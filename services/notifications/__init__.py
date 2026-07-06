"""
KurimaSense Notification Service
================================

Centralized, event-driven notification hub. Every subsystem (planner,
climatology, irrigation engine, accounts, future AI features) emits a
:class:`NotificationEvent` through :func:`notify` instead of embedding its own
delivery logic. The service decides:

  * **whether** to deliver (user category preferences, dedupe keys),
  * **where** to deliver (channel adapters: in-app, email today; push/SMS/
    WhatsApp plug in behind the same adapter interface),
  * **when** to deliver (quiet hours defer email/push; critical bypasses).

Scheduled *generators* (see ``generators.py``) turn platform state into events
on a cadence — planner reminders, overdue tasks, weather alerts, irrigation
recommendations, weekly/monthly summaries — and are idempotent via dedupe keys,
so the scheduler can run at any frequency without double-sending.

Public API:

    from services.notifications import notify, NotificationEvent
    notify(NotificationEvent(user_id=..., category="irrigation", title=..., body=...))
"""

from .models import (
    CATEGORIES,
    CATEGORY_GROUPS,
    CHANNELS,
    IMPLEMENTED_CHANNELS,
    Category,
    NotificationEvent,
    Severity,
)
from .service import dispatch_pending, notify, run_generation_cycle

__all__ = [
    "CATEGORIES",
    "CATEGORY_GROUPS",
    "CHANNELS",
    "IMPLEMENTED_CHANNELS",
    "Category",
    "NotificationEvent",
    "Severity",
    "notify",
    "dispatch_pending",
    "run_generation_cycle",
]
