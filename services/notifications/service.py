"""
Notification service orchestration: the ``notify()`` entrypoint every producer
calls, plus the dispatcher that drains the outbound delivery queue.

Flow of one event
-----------------
notify(event)
  → resolve user preferences (category group, channels, quiet hours)
  → insert notification row (dedupe on (user_id, dedupe_key)) + one delivery
    row per outbound channel, deferred past quiet hours when applicable
  → opportunistically dispatch what is already due (so interactive events —
    e.g. account emails — go out immediately; the scheduler is the safety net)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from . import repository
from .channels import CHANNEL_ADAPTERS
from .models import CATEGORIES, NotificationEvent
from .preferences import resolve_delivery

# Exponential-ish retry schedule for failed outbound sends (seconds), indexed
# by the attempt number already made. After the schedule runs out the delivery
# is marked failed for good (repository caps attempts at 5).
_RETRY_SCHEDULE = [60, 300, 1800, 7200]


def notify(event: NotificationEvent) -> Optional[Dict[str, Any]]:
    """Emit one notification. Returns the stored row, or None when suppressed
    by preferences, deduplicated, or the DB is unavailable."""
    if event.category not in CATEGORIES:
        print(f"[notifications] dropping event with unknown category '{event.category}'")
        return None

    severity = event.resolved_severity()
    stored_prefs = repository.get_preferences_row(event.user_id)
    plan = resolve_delivery(event.category, severity, stored_prefs)
    if plan.suppressed:
        return None

    row = repository.create_notification(
        event, severity, plan.channels, deferred_until=plan.deferred_until,
    )
    if row is None:
        return None

    # Fire-and-forget immediate dispatch for whatever is already due. Never
    # raises — producer call sites must not fail because SMTP hiccuped.
    try:
        if plan.deferred_until is None and len(plan.channels) > 1:
            dispatch_pending(limit=10)
    except Exception as e:
        print(f"[notifications] opportunistic dispatch failed: {e}")
    return row


def dispatch_pending(limit: int = 50) -> Dict[str, int]:
    """Send due outbound deliveries through their channel adapters.

    Called opportunistically from notify() and on every scheduler tick.
    Failures are retried on a backoff schedule; unconfigured channels are
    marked 'skipped' so the queue never wedges.
    """
    stats = {"sent": 0, "failed": 0, "skipped": 0, "retried": 0}
    for delivery in repository.due_deliveries(limit=limit):
        adapter = CHANNEL_ADAPTERS.get(delivery["channel"])
        if adapter is None:
            repository.update_delivery(delivery["delivery_id"], "skipped",
                                       f"no adapter for channel '{delivery['channel']}'")
            stats["skipped"] += 1
            continue
        try:
            result = adapter(delivery)
        except Exception as e:  # adapter bug — never kill the loop
            result = type("R", (), {"status": "failed", "error": str(e)[:400], "retriable": True})()

        if result.status == "sent":
            repository.update_delivery(delivery["delivery_id"], "sent")
            stats["sent"] += 1
        elif result.status == "skipped":
            repository.update_delivery(delivery["delivery_id"], "skipped", result.error)
            stats["skipped"] += 1
        elif getattr(result, "retriable", False):
            attempt = int(delivery.get("attempts") or 0)
            if attempt < len(_RETRY_SCHEDULE):
                repository.update_delivery(delivery["delivery_id"], "pending",
                                           result.error, retry_in_seconds=_RETRY_SCHEDULE[attempt])
                stats["retried"] += 1
            else:
                repository.update_delivery(delivery["delivery_id"], "failed", result.error)
                stats["failed"] += 1
        else:
            repository.update_delivery(delivery["delivery_id"], "failed", result.error)
            stats["failed"] += 1
    return stats


def run_generation_cycle(now: Optional[datetime] = None) -> Dict[str, Any]:
    """One full scheduler cycle: run every registered generator, then drain the
    delivery queue. Exposed for the in-process scheduler AND the admin/cron
    endpoint, so deployments without a long-lived worker can drive the system
    from an external cron."""
    from . import generators  # late import: generators pull in climate/irrigation

    now = now or datetime.now(timezone.utc)
    results: Dict[str, Any] = {"generated": {}, "dispatch": {}}
    for name, generator in generators.REGISTRY.items():
        try:
            results["generated"][name] = generator(now)
        except Exception as e:
            print(f"[notifications] generator '{name}' failed: {e}")
            results["generated"][name] = f"error: {e}"
    results["dispatch"] = dispatch_pending()
    return results
