"""
Scouting observation routes (Sprint 3) — durable storage for field scouting
reports (pest/disease/etc.), optionally carrying an AI diagnosis snapshot.

Access uses the canonical resolve_access pattern (admin / tenant membership /
legacy user_id fallback) so it works for both consumer and institutional callers
with correct 403-vs-404 behaviour.
"""

import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from psycopg2.extras import RealDictCursor

from auth_roles import get_authenticated_user
from database import get_db_connection
from schemas import AuthenticatedUser, CreateScoutingRequest, ScoutingRecord
from services.field_state.aggregator import (
    FieldAccessDenied,
    FieldNotFound,
    resolve_access,
)

router = APIRouter(tags=["scouting"])

_COLS = (
    "id::text AS id, field_id::text AS field_id, tenant_id::text AS tenant_id, "
    "user_id::text AS user_id, category, severity, notes, lat, lon, photo_url, "
    "diagnosis, observed_at, source, created_at"
)


def _resolve(field_id: str, user: AuthenticatedUser) -> dict:
    try:
        return resolve_access(
            field_id,
            user.user_id,
            tenant_ids=user.tenant_ids,
            is_admin=user.role == "admin",
        )
    except FieldNotFound:
        raise HTTPException(status_code=404, detail="Field not found")
    except FieldAccessDenied:
        raise HTTPException(status_code=403, detail="Access denied")


@router.post("/fields/{field_id}/scouting", response_model=ScoutingRecord, status_code=201)
def create_scouting(
    field_id: str,
    body: CreateScoutingRequest,
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    field = _resolve(field_id, user)
    source = body.source if body.source in ("grower_logged", "ai_diagnosis", "institution_recorded") else "grower_logged"

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "INSERT INTO scouting_observations "
            "(field_id, tenant_id, user_id, category, severity, notes, lat, lon, "
            " photo_url, diagnosis, observed_at, source) "
            "VALUES (%s::uuid, %s::uuid, %s::uuid, %s, %s, %s, %s, %s, %s, %s, "
            "        COALESCE(%s, NOW()), %s) "
            "RETURNING " + _COLS,
            (
                field_id,
                field.get("tenant_id"),
                user.user_id,
                body.category,
                body.severity,
                body.notes,
                body.lat,
                body.lon,
                body.photo_url,
                json.dumps(body.diagnosis) if body.diagnosis is not None else None,
                body.observed_at,
                source,
            ),
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
    except HTTPException:
        raise
    except Exception as exc:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        conn.close()

    return ScoutingRecord(**dict(row))


@router.get("/fields/{field_id}/scouting", response_model=List[ScoutingRecord])
def list_scouting(
    field_id: str,
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    _resolve(field_id, user)

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database unavailable")
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT " + _COLS + " FROM scouting_observations "
            "WHERE field_id = %s::uuid ORDER BY observed_at DESC",
            (field_id,),
        )
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
    finally:
        conn.close()

    return [ScoutingRecord(**r) for r in rows]
