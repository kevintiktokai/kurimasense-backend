"""
Persistence for the notification service.

Schema self-heals on boot (``ensure_schema`` is called from app startup) the
same way ``farm_tasks``/``soil_profiles`` do, so every environment works
without a manual migration step; ``migrations/014_notifications.sql`` is the
canonical DDL + RLS policies for production.

Tables
------
notifications             one row per delivered-to-user notification (this *is*
                          the in-app inbox; other channels reference it)
notification_deliveries   one row per (notification, outbound channel) with
                          status/attempts — the dispatch queue
notification_preferences  one JSONB preference document per user
notification_devices      registered push tokens (mobile app), per platform
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from psycopg2.extras import RealDictCursor

from database import get_db_connection

from .models import NotificationEvent

_SCHEMA_READY = False

_DDL = """
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    category TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'info',
    title TEXT NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    field_id UUID,
    action_url TEXT,
    data JSONB NOT NULL DEFAULT '{}'::jsonb,
    dedupe_key TEXT,
    source TEXT NOT NULL DEFAULT 'system',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    read_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_notifications_user_dedupe
    ON notifications(user_id, dedupe_key) WHERE dedupe_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_notifications_user_created
    ON notifications(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_user_unread
    ON notifications(user_id) WHERE read_at IS NULL;

CREATE TABLE IF NOT EXISTS notification_deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notification_id UUID NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
    channel TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',   -- pending | sent | failed | skipped
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    deliver_after TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_notification_deliveries_due
    ON notification_deliveries(deliver_after) WHERE status = 'pending';

CREATE TABLE IF NOT EXISTS notification_preferences (
    user_id TEXT PRIMARY KEY,
    preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS notification_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    platform TEXT NOT NULL DEFAULT 'android',  -- android | ios | web
    token TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_notification_devices_user ON notification_devices(user_id);
"""


def ensure_schema() -> bool:
    """Idempotently create notification tables. Safe to call on every boot."""
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return True
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(_DDL)
        conn.commit()
        cursor.close()
        _SCHEMA_READY = True
        return True
    except Exception as e:
        print(f"[notifications] ensure_schema failed: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return False
    finally:
        conn.close()


def _row_to_dict(row: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(row)
    for key in ("id", "notification_id", "field_id"):
        if out.get(key) is not None:
            out[key] = str(out[key])
    for key in ("created_at", "read_at", "expires_at", "sent_at", "deliver_after", "updated_at"):
        if isinstance(out.get(key), datetime):
            out[key] = out[key].isoformat()
    return out


# ── notifications ────────────────────────────────────────────────────────────

def create_notification(
    event: NotificationEvent,
    severity: str,
    channels: List[str],
    deferred_until: Optional[datetime] = None,
) -> Optional[Dict[str, Any]]:
    """Insert a notification + its outbound delivery rows.

    Returns the stored notification, or ``None`` when the dedupe key already
    exists (event already emitted) or the DB is unavailable.
    """
    if not ensure_schema():
        return None
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            INSERT INTO notifications
                (user_id, category, severity, title, body, field_id, action_url,
                 data, dedupe_key, source)
            VALUES (%s, %s, %s, %s, %s, %s::uuid, %s, %s::jsonb, %s, %s)
            ON CONFLICT (user_id, dedupe_key) WHERE dedupe_key IS NOT NULL
            DO NOTHING
            RETURNING *
            """,
            (
                event.user_id, event.category, severity, event.title, event.body,
                event.field_id, event.action_url, json.dumps(event.data or {}),
                event.dedupe_key, event.source,
            ),
        )
        row = cursor.fetchone()
        if row is None:  # dedupe hit
            conn.rollback()
            return None
        outbound = [ch for ch in channels if ch != "in_app"]
        for channel in outbound:
            cursor.execute(
                """
                INSERT INTO notification_deliveries (notification_id, channel, deliver_after)
                VALUES (%s, %s, COALESCE(%s, NOW()))
                """,
                (row["id"], channel, deferred_until),
            )
        conn.commit()
        cursor.close()
        return _row_to_dict(row)
    except Exception as e:
        print(f"[notifications] create_notification failed: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return None
    finally:
        conn.close()


def list_notifications(
    user_id: str,
    limit: int = 30,
    unread_only: bool = False,
    before: Optional[str] = None,
) -> List[Dict[str, Any]]:
    if not ensure_schema():
        return []
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT * FROM notifications
            WHERE user_id = %s
              AND (expires_at IS NULL OR expires_at > NOW())
        """
        params: List[Any] = [user_id]
        if unread_only:
            query += " AND read_at IS NULL"
        if before:
            query += " AND created_at < %s"
            params.append(before)
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(max(1, min(int(limit), 100)))
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        cursor.close()
        return [_row_to_dict(r) for r in rows]
    except Exception as e:
        print(f"[notifications] list failed: {e}")
        return []
    finally:
        conn.close()


def unread_count(user_id: str) -> int:
    if not ensure_schema():
        return 0
    conn = get_db_connection()
    if not conn:
        return 0
    try:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT COUNT(*) FROM notifications
               WHERE user_id = %s AND read_at IS NULL
                 AND (expires_at IS NULL OR expires_at > NOW())""",
            (user_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        count = row[0] if not isinstance(row, dict) else list(row.values())[0]
        return int(count or 0)
    except Exception as e:
        print(f"[notifications] unread_count failed: {e}")
        return 0
    finally:
        conn.close()


def mark_read(user_id: str, notification_id: str) -> bool:
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE notifications SET read_at = NOW()
               WHERE id = %s::uuid AND user_id = %s AND read_at IS NULL""",
            (notification_id, user_id),
        )
        updated = cursor.rowcount
        conn.commit()
        cursor.close()
        return updated > 0
    except Exception as e:
        print(f"[notifications] mark_read failed: {e}")
        return False
    finally:
        conn.close()


def mark_all_read(user_id: str) -> int:
    conn = get_db_connection()
    if not conn:
        return 0
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE notifications SET read_at = NOW() WHERE user_id = %s AND read_at IS NULL",
            (user_id,),
        )
        updated = cursor.rowcount
        conn.commit()
        cursor.close()
        return updated
    except Exception as e:
        print(f"[notifications] mark_all_read failed: {e}")
        return 0
    finally:
        conn.close()


# ── preferences ──────────────────────────────────────────────────────────────

def get_preferences_row(user_id: str) -> Optional[Dict[str, Any]]:
    if not ensure_schema():
        return None
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "SELECT preferences FROM notification_preferences WHERE user_id = %s",
            (user_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        if not row:
            return None
        prefs = row["preferences"]
        return json.loads(prefs) if isinstance(prefs, str) else prefs
    except Exception as e:
        print(f"[notifications] get_preferences failed: {e}")
        return None
    finally:
        conn.close()


def upsert_preferences(user_id: str, prefs: Dict[str, Any]) -> bool:
    if not ensure_schema():
        return False
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO notification_preferences (user_id, preferences, updated_at)
            VALUES (%s, %s::jsonb, NOW())
            ON CONFLICT (user_id)
            DO UPDATE SET preferences = EXCLUDED.preferences, updated_at = NOW()
            """,
            (user_id, json.dumps(prefs)),
        )
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"[notifications] upsert_preferences failed: {e}")
        return False
    finally:
        conn.close()


def all_preferences() -> Dict[str, Dict[str, Any]]:
    """user_id → stored preference doc, for the batch generators."""
    if not ensure_schema():
        return {}
    conn = get_db_connection()
    if not conn:
        return {}
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT user_id, preferences FROM notification_preferences")
        rows = cursor.fetchall()
        cursor.close()
        out: Dict[str, Dict[str, Any]] = {}
        for r in rows:
            prefs = r["preferences"]
            out[r["user_id"]] = json.loads(prefs) if isinstance(prefs, str) else (prefs or {})
        return out
    except Exception as e:
        print(f"[notifications] all_preferences failed: {e}")
        return {}
    finally:
        conn.close()


# ── devices (push tokens) ────────────────────────────────────────────────────

def register_device(user_id: str, platform: str, token: str) -> bool:
    if not ensure_schema():
        return False
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO notification_devices (user_id, platform, token, last_seen_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (token)
            DO UPDATE SET user_id = EXCLUDED.user_id,
                          platform = EXCLUDED.platform,
                          last_seen_at = NOW()
            """,
            (user_id, platform, token),
        )
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"[notifications] register_device failed: {e}")
        return False
    finally:
        conn.close()


def delete_device(user_id: str, token: str) -> bool:
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM notification_devices WHERE user_id = %s AND token = %s",
            (user_id, token),
        )
        deleted = cursor.rowcount
        conn.commit()
        cursor.close()
        return deleted > 0
    except Exception as e:
        print(f"[notifications] delete_device failed: {e}")
        return False
    finally:
        conn.close()


def list_devices(user_id: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "SELECT id, platform, token, last_seen_at FROM notification_devices WHERE user_id = %s",
            (user_id,),
        )
        rows = cursor.fetchall()
        cursor.close()
        return [_row_to_dict(r) for r in rows]
    except Exception as e:
        print(f"[notifications] list_devices failed: {e}")
        return []
    finally:
        conn.close()


# ── delivery queue ───────────────────────────────────────────────────────────

def due_deliveries(limit: int = 50) -> List[Dict[str, Any]]:
    """Pending deliveries whose deliver_after has passed, oldest first,
    joined with their notification payload."""
    if not ensure_schema():
        return []
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT d.id AS delivery_id, d.channel, d.attempts,
                   n.id, n.user_id, n.category, n.severity, n.title, n.body,
                   n.field_id, n.action_url, n.data, n.created_at
            FROM notification_deliveries d
            JOIN notifications n ON n.id = d.notification_id
            WHERE d.status = 'pending' AND d.deliver_after <= NOW()
              AND d.attempts < 5
            ORDER BY d.deliver_after ASC
            LIMIT %s
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        cursor.close()
        out = []
        for r in rows:
            d = _row_to_dict(r)
            d["delivery_id"] = str(r["delivery_id"])
            out.append(d)
        return out
    except Exception as e:
        print(f"[notifications] due_deliveries failed: {e}")
        return []
    finally:
        conn.close()


def update_delivery(delivery_id: str, status: str, error: Optional[str] = None,
                    retry_in_seconds: Optional[int] = None) -> None:
    conn = get_db_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        if status == "sent":
            cursor.execute(
                """UPDATE notification_deliveries
                   SET status = 'sent', attempts = attempts + 1, sent_at = NOW(), last_error = NULL
                   WHERE id = %s::uuid""",
                (delivery_id,),
            )
        elif status == "pending" and retry_in_seconds:
            cursor.execute(
                """UPDATE notification_deliveries
                   SET attempts = attempts + 1, last_error = %s,
                       deliver_after = NOW() + (%s || ' seconds')::interval
                   WHERE id = %s::uuid""",
                (error, str(int(retry_in_seconds)), delivery_id),
            )
        else:
            cursor.execute(
                """UPDATE notification_deliveries
                   SET status = %s, attempts = attempts + 1, last_error = %s
                   WHERE id = %s::uuid""",
                (status, error, delivery_id),
            )
        conn.commit()
        cursor.close()
    except Exception as e:
        print(f"[notifications] update_delivery failed: {e}")
    finally:
        conn.close()


# ── shared lookups for channels/generators ───────────────────────────────────

def get_user_email(user_id: str) -> Optional[str]:
    """Best-effort email lookup from Supabase's auth schema. Returns None when
    the backend role cannot read auth.users (email channel then skips)."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM auth.users WHERE id = %s::uuid", (user_id,))
        row = cursor.fetchone()
        cursor.close()
        if not row:
            return None
        email = row[0] if not isinstance(row, dict) else row.get("email")
        return email or None
    except Exception:
        return None
    finally:
        conn.close()
