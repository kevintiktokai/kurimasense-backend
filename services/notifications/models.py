"""
Notification domain model: categories, channels, severities, and the event
envelope every producer emits.

Extensibility contract
----------------------
* Adding a **notification type** = one ``Category`` entry in ``CATEGORIES``.
  Nothing else changes: preferences, storage, APIs and channel routing key off
  the registry.
* Adding a **channel** = one adapter in ``channels.py`` registered under a new
  key in ``CHANNELS``. Preference payloads carry unknown channel keys through
  untouched, so older clients keep working.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class Severity:
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

    ALL = (INFO, WARNING, CRITICAL)


# Delivery channel keys. in_app is always on (it is the notification row
# itself); the rest are opt-in per user. sms/whatsapp are reserved — they get
# adapters later without schema or API changes.
CHANNELS: List[str] = ["in_app", "email", "push", "sms", "whatsapp"]
IMPLEMENTED_CHANNELS: List[str] = ["in_app", "email", "push"]


# Preference groups — the granularity a farmer toggles in Settings. Individual
# categories map onto one group each so the preferences UI stays small even as
# the category list grows.
CATEGORY_GROUPS: List[str] = ["planner", "weather", "advisory", "summary", "account"]


@dataclass(frozen=True)
class Category:
    """A registered notification type."""

    key: str
    group: str                      # one of CATEGORY_GROUPS
    label: str                      # human name for the preferences UI
    default_severity: str = Severity.INFO
    # Channels used when the user has never customised anything. in_app is
    # implied and always included.
    default_channels: List[str] = field(default_factory=lambda: ["in_app"])
    description: str = ""


def _cat(key: str, group: str, label: str, severity: str = Severity.INFO,
         channels: Optional[List[str]] = None, description: str = "") -> Category:
    return Category(
        key=key, group=group, label=label, default_severity=severity,
        default_channels=channels or ["in_app"], description=description,
    )


CATEGORIES: Dict[str, Category] = {c.key: c for c in [
    # ── Planner ──────────────────────────────────────────────────────────
    _cat("task_reminder", "planner", "Daily planner reminders",
         description="Morning digest of today's planned farm tasks."),
    _cat("task_scheduled", "planner", "Scheduled farming tasks",
         description="A task you scheduled is due."),
    _cat("task_overdue", "planner", "Overdue activities", Severity.WARNING,
         description="Planned activities that were not completed on time."),
    _cat("harvest_reminder", "planner", "Harvest reminders", Severity.WARNING,
         ["in_app", "email"], "A field is approaching harvest readiness."),

    # ── Advisory (AI / decision engines) ────────────────────────────────
    _cat("irrigation", "advisory", "Irrigation recommendations", Severity.WARNING,
         description="The irrigation engine recommends action on a field."),
    _cat("fertilizer_reminder", "advisory", "Fertilizer reminders",
         description="Stage-based fertilizer application guidance."),
    _cat("spraying_reminder", "advisory", "Spraying reminders",
         description="Spray-window and application guidance."),
    _cat("ai_recommendation", "advisory", "AI recommendations",
         description="Recommendations from KurimaSense intelligence engines."),

    # ── Weather ──────────────────────────────────────────────────────────
    _cat("weather_alert", "weather", "General weather alerts", Severity.WARNING,
         ["in_app", "email"]),
    _cat("weather_heavy_rain", "weather", "Heavy rainfall alerts", Severity.WARNING,
         ["in_app", "email"]),
    _cat("weather_frost", "weather", "Frost warnings", Severity.CRITICAL,
         ["in_app", "email"]),
    _cat("weather_heat", "weather", "Heat stress warnings", Severity.WARNING,
         ["in_app", "email"]),
    _cat("weather_wind", "weather", "Wind warnings", Severity.WARNING,
         ["in_app", "email"]),
    _cat("weather_dry_spell", "weather", "Extended dry spell alerts", Severity.WARNING,
         ["in_app", "email"]),

    # ── Summaries ────────────────────────────────────────────────────────
    _cat("summary_weekly", "summary", "Weekly farm summary", Severity.INFO,
         ["in_app", "email"]),
    _cat("summary_monthly", "summary", "Monthly farm summary", Severity.INFO,
         ["in_app", "email"]),

    # ── Account ──────────────────────────────────────────────────────────
    _cat("account", "account", "Account notifications", Severity.INFO,
         ["in_app", "email"]),
    _cat("subscription", "account", "Subscription notifications", Severity.INFO,
         ["in_app", "email"]),
]}


@dataclass
class NotificationEvent:
    """The envelope a producer hands to :func:`services.notifications.notify`.

    ``dedupe_key`` makes emission idempotent: two events with the same
    ``(user_id, dedupe_key)`` collapse into one stored notification, which is
    what lets scheduled generators re-run safely. Producers choose the scheme,
    e.g. ``irrigation:{field_id}:{date}``.
    """

    user_id: str
    category: str
    title: str
    body: str
    severity: Optional[str] = None          # defaults to the category's severity
    field_id: Optional[str] = None
    action_url: Optional[str] = None        # frontend route to open on tap
    data: Dict[str, Any] = field(default_factory=dict)
    dedupe_key: Optional[str] = None
    source: str = "system"                  # producing subsystem, for observability

    def resolved_severity(self) -> str:
        if self.severity in Severity.ALL:
            return self.severity  # type: ignore[return-value]
        cat = CATEGORIES.get(self.category)
        return cat.default_severity if cat else Severity.INFO
