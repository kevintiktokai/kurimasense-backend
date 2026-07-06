"""
Hermetic tests for the notification service's pure logic: the category
registry, preference resolution (channels, groups, quiet hours), and the
summary frequency switch. No DB, no network.
"""

from datetime import datetime, timezone

from services.notifications.models import (
    CATEGORIES,
    CATEGORY_GROUPS,
    CHANNELS,
    NotificationEvent,
    Severity,
)
from services.notifications.preferences import (
    DEFAULT_PREFERENCES,
    merged_preferences,
    resolve_delivery,
    summary_enabled,
)


def utc(hour: int) -> datetime:
    # Harare is UTC+2 year-round: local hour = utc hour + 2.
    return datetime(2026, 7, 6, hour, 30, tzinfo=timezone.utc)


# ── registry sanity ──────────────────────────────────────────────────────────

def test_every_category_is_well_formed():
    assert CATEGORIES, "registry must not be empty"
    for key, cat in CATEGORIES.items():
        assert cat.key == key
        assert cat.group in CATEGORY_GROUPS
        assert cat.default_severity in Severity.ALL
        for ch in cat.default_channels:
            assert ch in CHANNELS


def test_event_resolves_category_default_severity():
    event = NotificationEvent(user_id="u1", category="weather_frost", title="t", body="b")
    assert event.resolved_severity() == Severity.CRITICAL
    event = NotificationEvent(user_id="u1", category="task_reminder", title="t", body="b")
    assert event.resolved_severity() == Severity.INFO


def test_event_explicit_severity_wins():
    event = NotificationEvent(user_id="u1", category="task_reminder", title="t", body="b",
                              severity=Severity.WARNING)
    assert event.resolved_severity() == Severity.WARNING


# ── preference merging ───────────────────────────────────────────────────────

def test_merged_preferences_defaults_when_nothing_stored():
    prefs = merged_preferences(None)
    assert prefs["enabled"] is True
    assert prefs["channels"]["in_app"] is True
    assert prefs["quiet_hours"]["enabled"] is False


def test_merged_preferences_overlays_sections_shallowly():
    prefs = merged_preferences({"channels": {"email": False}, "timezone": "Africa/Lusaka"})
    assert prefs["channels"]["email"] is False
    assert prefs["channels"]["push"] is DEFAULT_PREFERENCES["channels"]["push"]
    assert prefs["timezone"] == "Africa/Lusaka"


def test_merged_preferences_preserves_unknown_channel_keys():
    prefs = merged_preferences({"channels": {"telegram": True}})
    assert prefs["channels"]["telegram"] is True  # forward compatibility


# ── delivery resolution ──────────────────────────────────────────────────────

def test_defaults_email_category_gets_email_and_in_app():
    plan = resolve_delivery("weather_frost", Severity.CRITICAL, None, utc(10))
    assert plan.suppressed is False
    assert "in_app" in plan.channels
    assert "email" in plan.channels
    assert plan.deferred_until is None


def test_in_app_only_category_stays_in_app_even_with_email_enabled():
    plan = resolve_delivery("task_reminder", Severity.INFO, None, utc(10))
    assert plan.channels == ["in_app"]


def test_unknown_category_is_suppressed():
    plan = resolve_delivery("nonexistent", Severity.INFO, None, utc(10))
    assert plan.suppressed is True


def test_global_opt_out_suppresses():
    plan = resolve_delivery("weather_frost", Severity.CRITICAL, {"enabled": False}, utc(10))
    assert plan.suppressed is True


def test_group_opt_out_suppresses_only_that_group():
    stored = {"groups": {"weather": False}}
    assert resolve_delivery("weather_heat", Severity.WARNING, stored, utc(10)).suppressed is True
    assert resolve_delivery("task_reminder", Severity.INFO, stored, utc(10)).suppressed is False


def test_channel_opt_out_removes_email():
    stored = {"channels": {"email": False}}
    plan = resolve_delivery("weather_frost", Severity.CRITICAL, stored, utc(10))
    assert plan.channels == ["in_app"]


def test_quiet_hours_defer_outbound_channels():
    stored = {"quiet_hours": {"enabled": True, "start": 20, "end": 6}}
    # 22:30 local (20:30 UTC) — inside the window.
    plan = resolve_delivery("weather_heat", Severity.WARNING, stored, utc(20))
    assert plan.suppressed is False
    assert plan.deferred_until is not None
    assert plan.deferred_until > utc(20)


def test_quiet_hours_do_not_defer_during_day():
    stored = {"quiet_hours": {"enabled": True, "start": 20, "end": 6}}
    plan = resolve_delivery("weather_heat", Severity.WARNING, stored, utc(10))  # 12:30 local
    assert plan.deferred_until is None


def test_critical_bypasses_quiet_hours():
    stored = {"quiet_hours": {"enabled": True, "start": 20, "end": 6}}
    plan = resolve_delivery("weather_frost", Severity.CRITICAL, stored, utc(20))
    assert plan.deferred_until is None


# ── summary frequency ────────────────────────────────────────────────────────

def test_summary_frequency_switch():
    assert summary_enabled(None, "weekly") is True          # default weekly
    assert summary_enabled(None, "monthly") is False
    assert summary_enabled({"summary_frequency": "both"}, "monthly") is True
    assert summary_enabled({"summary_frequency": "off"}, "weekly") is False
    assert summary_enabled({"summary_frequency": "monthly"}, "monthly") is True
