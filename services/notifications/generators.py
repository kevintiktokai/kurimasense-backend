"""
Scheduled notification generators — the rules layer that turns platform state
into NotificationEvents on a cadence.

Design rules every generator follows:

* **Idempotent**: every event carries a dedupe key, so a generator can run on
  any schedule (15-min scheduler tick, external cron, manual admin trigger)
  without double-notifying.
* **Time-gated internally**: generators that should fire once a day/week check
  the user's local clock themselves (default Africa/Harare) instead of relying
  on scheduler timing.
* **Fail-soft**: one user's/field's failure never aborts the batch.

Registering a new generator = adding an entry to ``REGISTRY``. Future engines
(disease prediction, pest pressure, yield anomalies…) plug in the same way and
inherit preferences, channels, quiet hours and delivery for free.

Note on targeting: consumer notifications key off ``fields.user_id`` (every
personal-tenant field carries it). When institutional fan-out (notify all
tenant officers) lands, this is the single place that changes.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None  # type: ignore

from psycopg2.extras import RealDictCursor

from database import get_db_connection

from . import repository
from .models import NotificationEvent, Severity
from .preferences import DEFAULT_TIMEZONE, merged_preferences, summary_enabled
from .service import notify

# ── shared helpers ───────────────────────────────────────────────────────────

def _query(sql: str, params: Tuple = ()) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        cursor.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[notifications.generators] query failed: {e}")
        return []
    finally:
        conn.close()


def _local_now(user_prefs: Optional[Dict[str, Any]], now_utc: datetime) -> datetime:
    tz_name = merged_preferences(user_prefs).get("timezone") or DEFAULT_TIMEZONE
    if ZoneInfo is not None:
        try:
            return now_utc.astimezone(ZoneInfo(tz_name))
        except Exception:
            pass
    return now_utc


def _centroid(polygon: Any) -> Optional[Tuple[float, float]]:
    if isinstance(polygon, list) and polygon:
        try:
            lats = [p["lat"] for p in polygon]
            lons = [p["lon"] for p in polygon]
            return round(sum(lats) / len(lats), 2), round(sum(lons) / len(lons), 2)
        except Exception:
            return None
    return None


# ── planner: daily reminders ─────────────────────────────────────────────────

def generate_task_reminders(now_utc: datetime) -> int:
    """One morning digest per user listing today's planned tasks (≥06:00 local)."""
    rows = _query(
        """
        SELECT t.user_id, COUNT(*) AS n,
               ARRAY_AGG(t.title ORDER BY
                   CASE t.priority WHEN 'urgent' THEN 0 WHEN 'high' THEN 1
                                   WHEN 'normal' THEN 2 ELSE 3 END) AS titles
        FROM farm_tasks t
        WHERE t.task_date = CURRENT_DATE AND t.completed = FALSE
        GROUP BY t.user_id
        """
    )
    prefs_by_user = repository.all_preferences()
    emitted = 0
    for row in rows:
        local = _local_now(prefs_by_user.get(row["user_id"]), now_utc)
        if local.hour < 6:
            continue
        titles = [t for t in (row.get("titles") or []) if t][:3]
        preview = "; ".join(titles)
        more = int(row["n"]) - len(titles)
        if more > 0:
            preview += f" (+{more} more)"
        if notify(NotificationEvent(
            user_id=row["user_id"],
            category="task_reminder",
            title=f"You have {row['n']} task{'s' if int(row['n']) != 1 else ''} planned today",
            body=preview or "Open your planner to review today's work.",
            action_url="/dashboard/plan",
            data={"count": int(row["n"])},
            dedupe_key=f"task_reminder:{local.date().isoformat()}",
            source="planner",
        )):
            emitted += 1
    return emitted


def generate_overdue_alerts(now_utc: datetime) -> int:
    """Alert once per day when planned activities have slipped past their date."""
    rows = _query(
        """
        SELECT t.user_id, COUNT(*) AS n, MIN(t.task_date) AS oldest
        FROM farm_tasks t
        WHERE t.task_date < CURRENT_DATE AND t.completed = FALSE
          AND t.task_date > CURRENT_DATE - INTERVAL '30 days'
        GROUP BY t.user_id
        """
    )
    prefs_by_user = repository.all_preferences()
    emitted = 0
    for row in rows:
        local = _local_now(prefs_by_user.get(row["user_id"]), now_utc)
        if local.hour < 7:
            continue
        oldest = row.get("oldest")
        days = (local.date() - oldest).days if oldest else 1
        if notify(NotificationEvent(
            user_id=row["user_id"],
            category="task_overdue",
            title=f"{row['n']} overdue activit{'ies' if int(row['n']) != 1 else 'y'} on your plan",
            body=(f"The oldest has been waiting {days} day{'s' if days != 1 else ''}. "
                  "Mark them done or reschedule so your plan stays accurate."),
            action_url="/dashboard/plan",
            data={"count": int(row["n"]), "oldest_days": days},
            dedupe_key=f"task_overdue:{local.date().isoformat()}",
            source="planner",
        )):
            emitted += 1
    return emitted


# ── weather alerts ───────────────────────────────────────────────────────────

# climate_service alert type → (category, min-severity map)
_WEATHER_CATEGORY = {
    "frost": "weather_frost",
    "heat": "weather_heat",
    "wind": "weather_wind",
    "rain": "weather_heavy_rain",
    "uv": "weather_alert",
}


def generate_weather_alerts(now_utc: datetime) -> int:
    """Per distinct farm location: forecast-driven hazard alerts + dry spells.

    Locations are shared across a user's fields (centroids rounded to ~1km via
    2dp), and climate_service caches Open-Meteo calls, so this stays cheap even
    with many fields.
    """
    import climate_service

    fields = _query(
        """
        SELECT id, user_id, name, polygon_coordinates
        FROM fields
        WHERE user_id IS NOT NULL AND user_id <> ''
        """
    )
    # (user, lat, lon) → field names, so one alert covers all fields at a location
    locations: Dict[Tuple[str, float, float], List[str]] = defaultdict(list)
    for f in fields:
        c = _centroid(f.get("polygon_coordinates"))
        if not c:
            continue
        locations[(f["user_id"], c[0], c[1])].append(f.get("name") or "your field")

    emitted = 0
    for (user_id, lat, lon), field_names in list(locations.items())[:200]:
        try:
            alerts = asyncio.run(climate_service.get_weather_alerts(lat, lon))
            forecast = asyncio.run(climate_service.get_daily_forecast(lat, lon, days=7))
        except Exception as e:
            print(f"[notifications.generators] weather fetch failed ({lat},{lon}): {e}")
            continue

        where = field_names[0] if len(field_names) == 1 else f"{len(field_names)} of your fields"

        for alert in (alerts or {}).get("alerts", []):
            category = _WEATHER_CATEGORY.get(alert.get("type"))
            if not category:
                continue
            severity = Severity.CRITICAL if alert.get("severity") == "high" else Severity.WARNING
            recommendations = (alert.get("recommendations") or [])[:2]
            body = alert.get("message", "")
            if recommendations:
                body += "\n• " + "\n• ".join(recommendations)
            if notify(NotificationEvent(
                user_id=user_id,
                category=category,
                severity=severity,
                title=f"{alert.get('title', 'Weather alert')} — {where}",
                body=body,
                action_url="/dashboard/weather",
                data={"alert": {k: alert.get(k) for k in ("type", "severity", "date", "message")},
                      "lat": lat, "lon": lon},
                dedupe_key=f"weather:{alert.get('type')}:{alert.get('date')}:{lat}:{lon}",
                source="climatology",
            )):
                emitted += 1

        # Extended dry spell: negligible rain across the full 7-day horizon.
        daily = (forecast or {}).get("daily", [])
        if len(daily) >= 7:
            total_rain = sum(d.get("precipitation") or 0 for d in daily)
            max_prob = max((d.get("precipitation_probability") or 0) for d in daily)
            if total_rain < 5 and max_prob < 40:
                week = now_utc.isocalendar()
                if notify(NotificationEvent(
                    user_id=user_id,
                    category="weather_dry_spell",
                    title=f"Extended dry spell ahead — {where}",
                    body=(f"Less than {total_rain:.0f}mm of rain is forecast over the next 7 days "
                          f"(max rain chance {max_prob:.0f}%). Review irrigation plans and "
                          "prioritise moisture-sensitive crops."),
                    action_url="/dashboard/weather",
                    data={"total_rain_7d": round(total_rain, 1), "max_probability": max_prob},
                    dedupe_key=f"weather:dry_spell:{week.year}-W{week.week}:{lat}:{lon}",
                    source="climatology",
                )):
                    emitted += 1
    return emitted


# ── irrigation recommendations → planner + notification ─────────────────────

def generate_irrigation_recommendations(now_utc: datetime) -> int:
    """Run the irrigation engine over active fields; for actionable results,
    create an intelligent planner task and notify the farmer.

    The irrigation service owns planner-task creation/dedupe; this generator
    owns targeting + notification, keeping engine and delivery decoupled.
    """
    from services.irrigation import service as irrigation_service

    fields = _query(
        """
        SELECT id, user_id, name, crop_type, planting_date, polygon_coordinates
        FROM fields
        WHERE user_id IS NOT NULL AND user_id <> ''
          AND planting_date IS NOT NULL
        """
    )
    prefs_by_user = repository.all_preferences()
    emitted = 0
    for field in fields[:200]:
        user_id = field["user_id"]
        local = _local_now(prefs_by_user.get(user_id), now_utc)
        if local.hour < 6:  # recommendations land with the morning review
            continue
        try:
            rec = asyncio.run(irrigation_service.recommendation_for_field_row(field))
        except Exception as e:
            print(f"[notifications.generators] irrigation failed for field {field.get('id')}: {e}")
            continue
        if rec is None or rec.action not in ("irrigate_now", "irrigate_soon"):
            continue

        task = irrigation_service.ensure_planner_task(field, rec)
        urgency = "today" if rec.action == "irrigate_now" else "within 2 days"
        if notify(NotificationEvent(
            user_id=user_id,
            category="irrigation",
            severity=Severity.WARNING if rec.action == "irrigate_now" else Severity.INFO,
            title=f"Irrigate {field.get('name') or 'your field'} {urgency} (~{rec.recommended_mm:.0f}mm)",
            body=rec.summary(),
            field_id=str(field["id"]),
            action_url="/dashboard/plan",
            data={"recommendation": rec.to_dict(), "planner_task_id": task.get("id") if task else None},
            dedupe_key=f"irrigation:{field['id']}:{local.date().isoformat()}",
            source="irrigation_engine",
        )):
            emitted += 1
    return emitted


# ── summaries ────────────────────────────────────────────────────────────────

def _summary_stats(user_id: str, since_days: int) -> Dict[str, int]:
    rows = _query(
        """
        SELECT
          COUNT(*) FILTER (WHERE t.completed AND t.completed_at >= NOW() - (%s || ' days')::interval) AS done,
          COUNT(*) FILTER (WHERE NOT t.completed AND t.task_date >= CURRENT_DATE
                             AND t.task_date < CURRENT_DATE + 7) AS upcoming,
          COUNT(*) FILTER (WHERE NOT t.completed AND t.task_date < CURRENT_DATE) AS overdue
        FROM farm_tasks t WHERE t.user_id = %s
        """,
        (str(since_days), user_id),
    )
    return {k: int(v or 0) for k, v in (rows[0] if rows else {}).items()}


def _generate_summaries(now_utc: datetime, which: str) -> int:
    users = _query("SELECT DISTINCT user_id FROM farm_tasks WHERE user_id IS NOT NULL")
    prefs_by_user = repository.all_preferences()
    emitted = 0
    for row in users:
        user_id = row["user_id"]
        prefs = prefs_by_user.get(user_id)
        if not summary_enabled(prefs, which):
            continue
        local = _local_now(prefs, now_utc)
        if which == "weekly":
            if not (local.weekday() == 6 and local.hour >= 16):  # Sunday evening
                continue
            week = local.isocalendar()
            dedupe = f"summary_weekly:{week.year}-W{week.week}"
            period_days, period_label = 7, "this week"
            category = "summary_weekly"
            title = "Your weekly farm summary"
        else:
            if not (local.day == 1 and local.hour >= 7):  # 1st of the month
                continue
            dedupe = f"summary_monthly:{local.year}-{local.month:02d}"
            period_days, period_label = 30, "last month"
            category = "summary_monthly"
            title = "Your monthly farm summary"

        stats = _summary_stats(user_id, period_days)
        body = (f"Completed {period_label}: {stats.get('done', 0)} activities. "
                f"Planned for the next 7 days: {stats.get('upcoming', 0)}.")
        if stats.get("overdue"):
            body += f" Overdue: {stats['overdue']} — worth a review."
        if notify(NotificationEvent(
            user_id=user_id, category=category, title=title, body=body,
            action_url="/dashboard/plan", data=stats, dedupe_key=dedupe,
            source="planner",
        )):
            emitted += 1
    return emitted


def generate_weekly_summaries(now_utc: datetime) -> int:
    return _generate_summaries(now_utc, "weekly")


def generate_monthly_summaries(now_utc: datetime) -> int:
    return _generate_summaries(now_utc, "monthly")


# ── registry ─────────────────────────────────────────────────────────────────

REGISTRY: Dict[str, Callable[[datetime], int]] = {
    "task_reminders": generate_task_reminders,
    "overdue_alerts": generate_overdue_alerts,
    "weather_alerts": generate_weather_alerts,
    "irrigation_recommendations": generate_irrigation_recommendations,
    "weekly_summaries": generate_weekly_summaries,
    "monthly_summaries": generate_monthly_summaries,
}
