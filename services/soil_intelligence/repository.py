"""
Soil profile persistence
========================
Read/write access to the ``soil_profiles`` table. One row per field holds the
merged :class:`SoilProfile` as JSONB. RLS GUCs are armed on every connection
(FORCE-ready) so the table behaves exactly like its sibling ``daily_logs`` under
the tenant policy from migration 012.

All functions are best-effort: a DB outage degrades to ``None`` / no-op rather
than raising, so the soil subsystem never takes down a field request.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List, Optional

from database import get_db_connection
from .models import SoilProfile


def _arm(conn, user_id: Optional[str], tenant_ids: Optional[List[str]]) -> None:
    if not user_id:
        return
    try:
        from tenancy import arm_rls_gucs, caller_tenant_ids
        tids = tenant_ids if tenant_ids is not None else caller_tenant_ids(user_id)
        arm_rls_gucs(conn, user_id, [str(t) for t in (tids or [])])
    except Exception as e:
        print(f"[soil.repository] GUC arm failed (continuing): {e}")


def load_profile(
    field_id: str,
    user_id: Optional[str] = None,
    tenant_ids: Optional[List[str]] = None,
) -> Optional[SoilProfile]:
    """Return the stored profile for a field, or None if absent/unavailable."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        _arm(conn, user_id, tenant_ids)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT profile FROM soil_profiles WHERE field_id = %s::uuid LIMIT 1",
            (field_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        if not row:
            return None
        raw = row["profile"] if isinstance(row, dict) else row[0]
        if isinstance(raw, str):
            raw = json.loads(raw)
        if not raw:
            return None
        profile = SoilProfile.from_dict(raw)
        profile.field_id = profile.field_id or field_id
        return profile
    except Exception as e:
        print(f"[soil.repository] load_profile failed: {e}")
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def save_profile(
    profile: SoilProfile,
    refresh_after: Optional[datetime],
    user_id: Optional[str] = None,
    tenant_ids: Optional[List[str]] = None,
) -> bool:
    """Upsert a profile (one row per field). Returns True on success."""
    if not profile.field_id:
        return False
    conn = get_db_connection()
    if not conn:
        return False
    try:
        _arm(conn, user_id, tenant_ids)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO soil_profiles
                (field_id, lat, lon, profile, provider_status, schema_version,
                 built_at, refresh_after, updated_at)
            VALUES (%s::uuid, %s, %s, %s::jsonb, %s::jsonb, %s, NOW(), %s, NOW())
            ON CONFLICT (field_id) DO UPDATE SET
                lat = EXCLUDED.lat,
                lon = EXCLUDED.lon,
                profile = EXCLUDED.profile,
                provider_status = EXCLUDED.provider_status,
                schema_version = EXCLUDED.schema_version,
                built_at = EXCLUDED.built_at,
                refresh_after = EXCLUDED.refresh_after,
                updated_at = NOW()
            """,
            (
                profile.field_id,
                profile.lat,
                profile.lon,
                json.dumps(profile.to_dict()),
                json.dumps(profile.provider_status),
                profile.schema_version,
                refresh_after,
            ),
        )
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"[soil.repository] save_profile failed: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass
