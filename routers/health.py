"""
Operational health checks.

GET /health/ingestion — surfaces freshness of the daily satellite ingestion
worker by inspecting the most recent daily_logs row plus a rolling count
of fields that failed to ingest in the last 24 hours.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from psycopg2.extras import RealDictCursor

from database import get_db_connection

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


# A run is "fresh" if there's a row newer than this many hours.
INGESTION_FRESH_HOURS = 36


def _is_fresh(last_ts: Optional[datetime], now: datetime) -> bool:
    if last_ts is None:
        return False
    if last_ts.tzinfo is None:
        # daily_logs.created_at TIMESTAMPTZ is timezone-aware in production,
        # but tolerate naive timestamps for older rows.
        last_ts = last_ts.replace(tzinfo=timezone.utc)
    return (now - last_ts) < timedelta(hours=INGESTION_FRESH_HOURS)


def _classify(payload: Dict[str, Any]) -> str:
    """ok / stale / unknown — used by uptime probes for green/yellow/red."""
    if payload.get("last_run_at") is None:
        return "unknown"
    return "ok" if payload.get("fresh") else "stale"


@router.get("/health/ingestion")
def ingestion_health() -> Dict[str, Any]:
    """
    Returns:
      - last_run_at: ISO-8601 timestamp of the newest daily_logs row, or null
      - fresh: whether last_run_at is within the freshness window
      - freshness_window_hours: the freshness threshold used
      - rows_last_24h: count of daily_logs rows written in the last 24h
      - fields_with_data_24h: distinct field count in the last 24h
      - rejected_observations_24h: rows ingested but flagged 'rejected'
      - status: ok | stale | unknown
    """
    now = datetime.now(timezone.utc)
    conn = get_db_connection()
    if conn is None:
        raise HTTPException(503, "Database unavailable")
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT
              MAX(created_at) AS last_run_at,
              COUNT(*) FILTER (WHERE created_at > (NOW() - INTERVAL '24 hours')) AS rows_last_24h,
              COUNT(DISTINCT field_id) FILTER (
                WHERE created_at > (NOW() - INTERVAL '24 hours')
              ) AS fields_with_data_24h,
              COUNT(*) FILTER (
                WHERE created_at > (NOW() - INTERVAL '24 hours')
                  AND observation_quality = 'rejected'
              ) AS rejected_observations_24h
            FROM daily_logs
            """
        )
        row = cursor.fetchone() or {}
        cursor.close()
    finally:
        conn.close()

    last_run_at = row.get("last_run_at")
    payload = {
        "last_run_at": last_run_at.isoformat() if last_run_at else None,
        "fresh": _is_fresh(last_run_at, now),
        "freshness_window_hours": INGESTION_FRESH_HOURS,
        "rows_last_24h": int(row.get("rows_last_24h") or 0),
        "fields_with_data_24h": int(row.get("fields_with_data_24h") or 0),
        "rejected_observations_24h": int(row.get("rejected_observations_24h") or 0),
        "checked_at": now.isoformat(),
    }
    payload["status"] = _classify(payload)
    return payload
