"""
In-process notification scheduler.

A single asyncio task started on FastAPI startup runs the generation cycle
every ``NOTIFICATIONS_INTERVAL_SECONDS`` (default 15 min). A Postgres advisory
lock makes the cycle single-flight across replicas, so horizontal scaling of
the API never double-sends — whichever instance wins the lock runs the cycle,
the rest skip the tick.

Deployments that prefer an external scheduler (Render cron, GitHub Actions,
Supabase cron) can set ``NOTIFICATIONS_SCHEDULER_ENABLED=false`` and hit
``POST /notifications/admin/run-cycle`` (X-Admin-Token) instead — both paths
call the same ``run_generation_cycle``.
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone

from starlette.concurrency import run_in_threadpool

from database import get_db_connection

# Stable app-wide advisory lock id for the notification cycle (arbitrary but
# fixed; do not reuse for other subsystems).
_ADVISORY_LOCK_ID = 762031


def _enabled() -> bool:
    return os.environ.get("NOTIFICATIONS_SCHEDULER_ENABLED", "true").strip().lower() in ("1", "true", "yes")


def _interval_seconds() -> int:
    try:
        return max(60, int(os.environ.get("NOTIFICATIONS_INTERVAL_SECONDS", "900")))
    except ValueError:
        return 900


def run_cycle_with_lock() -> dict:
    """Run one generation+dispatch cycle under the advisory lock (sync;
    callers run it in a threadpool). Returns cycle stats, or a skip marker
    when another instance holds the lock."""
    from .service import run_generation_cycle

    conn = get_db_connection()
    if not conn:
        return {"skipped": "no database connection"}
    try:
        # Transaction-scoped lock: released on the rollback below no matter how
        # the cycle exits, so a pooled connection can never strand the lock.
        cursor = conn.cursor()
        cursor.execute("SELECT pg_try_advisory_xact_lock(%s)", (_ADVISORY_LOCK_ID,))
        row = cursor.fetchone()
        got_lock = bool(row[0] if not isinstance(row, dict) else list(row.values())[0])
        cursor.close()
        if not got_lock:
            return {"skipped": "another instance is running the cycle"}
        return run_generation_cycle(datetime.now(timezone.utc))
    finally:
        try:
            conn.rollback()
        except Exception:
            pass
        conn.close()


async def _loop() -> None:
    interval = _interval_seconds()
    # Let the app finish booting (and init_db/ensure_schema run) first.
    await asyncio.sleep(20)
    print(f"[notifications] scheduler started (every {interval}s)")
    while True:
        try:
            stats = await run_in_threadpool(run_cycle_with_lock)
            generated = stats.get("generated")
            if generated and any(isinstance(v, int) and v > 0 for v in generated.values()):
                print(f"[notifications] cycle: {stats}")
        except Exception as e:
            print(f"[notifications] scheduler cycle error: {e}")
        await asyncio.sleep(interval)


def start_scheduler() -> None:
    """Called from app startup. No-ops when disabled or DB is unconfigured."""
    if not _enabled():
        print("[notifications] scheduler disabled via NOTIFICATIONS_SCHEDULER_ENABLED")
        return
    if not os.environ.get("DATABASE_URL"):
        print("[notifications] scheduler not started (no DATABASE_URL)")
        return
    asyncio.get_event_loop().create_task(_loop())
