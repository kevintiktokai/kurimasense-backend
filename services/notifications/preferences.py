"""
Pure preference-resolution logic — no I/O, fully unit-testable.

Given a user's stored preference document and a category, decide which
channels to deliver on and whether non-in-app delivery must wait for quiet
hours to end. The stored document is a forward-compatible JSON blob: unknown
channel or group keys are preserved, missing keys fall back to defaults, so
adding channels/categories never requires a preference migration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - py<3.9 not supported in prod
    ZoneInfo = None  # type: ignore

from .models import CATEGORIES, CATEGORY_GROUPS, Severity

DEFAULT_TIMEZONE = "Africa/Harare"

# The factory default preference document. Email defaults ON for the channel
# but each category still needs email in its default_channels to actually use
# it (so task reminders stay in-app-only out of the box while frost warnings
# also email).
DEFAULT_PREFERENCES: Dict[str, Any] = {
    "enabled": True,                                  # global opt-out switch
    "timezone": DEFAULT_TIMEZONE,
    "channels": {"in_app": True, "email": True, "push": True, "sms": False, "whatsapp": False},
    "groups": {g: True for g in CATEGORY_GROUPS},     # category-group opt-in
    "quiet_hours": {"enabled": False, "start": 20, "end": 6},  # local hours [start, end)
    "summary_frequency": "weekly",                    # weekly | monthly | both | off
}


def merged_preferences(stored: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Overlay a stored preference document on the defaults (shallow per section)."""
    prefs = {k: (dict(v) if isinstance(v, dict) else v) for k, v in DEFAULT_PREFERENCES.items()}
    if not isinstance(stored, dict):
        return prefs
    for key, value in stored.items():
        if isinstance(value, dict) and isinstance(prefs.get(key), dict):
            prefs[key].update(value)
        else:
            prefs[key] = value
    return prefs


@dataclass
class DeliveryPlan:
    """Outcome of resolving an event against a user's preferences."""

    channels: List[str] = field(default_factory=list)
    suppressed: bool = False
    reason: str = ""
    # UTC time before which email/push must not go out (quiet hours). in_app is
    # never deferred — it is pull-based and respects no schedule.
    deferred_until: Optional[datetime] = None


def _local_now(prefs: Dict[str, Any], now_utc: datetime) -> datetime:
    tz_name = prefs.get("timezone") or DEFAULT_TIMEZONE
    if ZoneInfo is not None:
        try:
            return now_utc.astimezone(ZoneInfo(tz_name))
        except Exception:
            pass
    return now_utc.astimezone(timezone.utc)


def _in_quiet_hours(local_hour: int, start: int, end: int) -> bool:
    if start == end:
        return False
    if start < end:
        return start <= local_hour < end
    return local_hour >= start or local_hour < end  # window crosses midnight


def _quiet_hours_end_utc(prefs: Dict[str, Any], now_utc: datetime) -> datetime:
    """Next local time quiet hours end, converted back to UTC."""
    qh = prefs.get("quiet_hours") or {}
    end_hour = int(qh.get("end", 6)) % 24
    local = _local_now(prefs, now_utc)
    candidate = local.replace(hour=end_hour, minute=0, second=0, microsecond=0)
    if candidate <= local:
        candidate += timedelta(days=1)
    return candidate.astimezone(timezone.utc)


def resolve_delivery(
    category_key: str,
    severity: str,
    stored_prefs: Optional[Dict[str, Any]],
    now_utc: Optional[datetime] = None,
) -> DeliveryPlan:
    """Decide channels + timing for one event. Critical bypasses quiet hours."""
    now_utc = now_utc or datetime.now(timezone.utc)
    prefs = merged_preferences(stored_prefs)
    category = CATEGORIES.get(category_key)
    if category is None:
        return DeliveryPlan(suppressed=True, reason=f"unknown category '{category_key}'")

    if not prefs.get("enabled", True):
        return DeliveryPlan(suppressed=True, reason="notifications disabled by user")

    groups = prefs.get("groups") or {}
    if groups.get(category.group, True) is False:
        return DeliveryPlan(suppressed=True, reason=f"group '{category.group}' opted out")

    channel_prefs = prefs.get("channels") or {}
    channels = ["in_app"]  # in_app is the persistent record — always on
    for ch in category.default_channels:
        if ch == "in_app":
            continue
        if channel_prefs.get(ch, False):
            channels.append(ch)

    plan = DeliveryPlan(channels=channels)

    qh = prefs.get("quiet_hours") or {}
    if qh.get("enabled") and severity != Severity.CRITICAL:
        local = _local_now(prefs, now_utc)
        if _in_quiet_hours(local.hour, int(qh.get("start", 20)) % 24, int(qh.get("end", 6)) % 24):
            plan.deferred_until = _quiet_hours_end_utc(prefs, now_utc)
            plan.reason = "outbound channels deferred to quiet-hours end"

    return plan


def summary_enabled(stored_prefs: Optional[Dict[str, Any]], which: str) -> bool:
    """Whether the user wants the weekly/monthly summary (frequency setting)."""
    freq = merged_preferences(stored_prefs).get("summary_frequency", "weekly")
    if freq == "off":
        return False
    if freq == "both":
        return True
    return freq == which
