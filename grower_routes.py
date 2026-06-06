"""
Grower management endpoints (Workstream 3, institutional)
=========================================================
    POST   /tenants/me/growers
    GET    /tenants/me/growers        (?limit, ?offset)
    GET    /tenants/me/growers/{id}
    PATCH  /tenants/me/growers/{id}
    DELETE /tenants/me/growers/{id}   (soft delete)

Guarded by ``require_institutional`` (Workstream 1). Writes additionally require
member_role in (owner, officer) — viewers are read-only. Growers are scoped to
the caller's primary tenant (``user.tenant_id``). Light router (no AI-stack
imports) so it stays unit-testable.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from psycopg2.extras import RealDictCursor

from database import get_db_connection
from auth_roles import require_institutional
from schemas import AuthenticatedUser, Grower, CreateGrowerRequest, UpdateGrowerRequest

logger = logging.getLogger("kurimasense")

router = APIRouter(prefix="/tenants/me/growers", tags=["growers"])

_GROWER_COLS = (
    "id::text AS id, tenant_id::text AS tenant_id, name, phone, email, coordinates, "
    "claimed_by_user_id::text AS claimed_by_user_id, created_by_user_id::text AS created_by_user_id, "
    "notes, created_at, updated_at"
)


def _conn_or_503():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return conn


def _require_write(user: AuthenticatedUser) -> None:
    if user.member_role not in ("owner", "officer"):
        raise HTTPException(status_code=403, detail="Viewers cannot modify growers")


def _require_tenant(user: AuthenticatedUser) -> str:
    if not user.tenant_id:
        raise HTTPException(status_code=403, detail="No tenant context for this user")
    return user.tenant_id


@router.post("", response_model=Grower)
def create_grower(body: CreateGrowerRequest, user: AuthenticatedUser = Depends(require_institutional)):
    tenant_id = _require_tenant(user)
    _require_write(user)
    conn = _conn_or_503()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            f"""
            INSERT INTO growers (tenant_id, name, phone, email, coordinates, notes, created_by_user_id)
            VALUES (%s::uuid, %s, %s, %s, %s::jsonb, %s, %s::uuid)
            RETURNING {_GROWER_COLS}
            """,
            (tenant_id, body.name, body.phone, body.email,
             _json(body.coordinates), body.notes, user.user_id),
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
    finally:
        _close(conn)
    return Grower(**dict(row))


@router.get("", response_model=list[Grower])
def list_growers(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: AuthenticatedUser = Depends(require_institutional),
):
    tenant_id = _require_tenant(user)
    conn = _conn_or_503()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            f"SELECT {_GROWER_COLS} FROM growers "
            f"WHERE tenant_id = %s::uuid AND deleted_at IS NULL "
            f"ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (tenant_id, limit, offset),
        )
        rows = cur.fetchall()
        cur.close()
    finally:
        _close(conn)
    return [Grower(**dict(r)) for r in rows]


@router.get("/{grower_id}", response_model=Grower)
def get_grower(grower_id: str, user: AuthenticatedUser = Depends(require_institutional)):
    _require_tenant(user)
    row = _fetch_grower(grower_id)
    if not row:
        raise HTTPException(status_code=404, detail="Grower not found")
    if str(row["tenant_id"]) != str(user.tenant_id) and user.role != "admin":
        raise HTTPException(status_code=403, detail="Grower belongs to another tenant")
    return Grower(**row)


@router.patch("/{grower_id}", response_model=Grower)
def update_grower(grower_id: str, body: UpdateGrowerRequest, user: AuthenticatedUser = Depends(require_institutional)):
    _require_tenant(user)
    _require_write(user)
    existing = _fetch_grower(grower_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Grower not found")
    if str(existing["tenant_id"]) != str(user.tenant_id):
        raise HTTPException(status_code=403, detail="Grower belongs to another tenant")

    sets, params = [], []
    for field in ("name", "phone", "email", "notes"):
        val = getattr(body, field)
        if val is not None:
            sets.append(f"{field} = %s")
            params.append(val)
    if body.coordinates is not None:
        sets.append("coordinates = %s::jsonb")
        params.append(_json(body.coordinates))
    if not sets:
        raise HTTPException(status_code=400, detail="No fields to update")
    sets.append("updated_at = NOW()")
    params.extend([grower_id, user.tenant_id])

    conn = _conn_or_503()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            f"UPDATE growers SET {', '.join(sets)} "
            f"WHERE id = %s::uuid AND tenant_id = %s::uuid AND deleted_at IS NULL "
            f"RETURNING {_GROWER_COLS}",
            tuple(params),
        )
        row = cur.fetchone()
        if not row:
            conn.rollback()
            cur.close()
            raise HTTPException(status_code=404, detail="Grower not found")
        conn.commit()
        cur.close()
    except HTTPException:
        raise
    finally:
        _close(conn)
    return Grower(**dict(row))


@router.delete("/{grower_id}", status_code=204)
def delete_grower(grower_id: str, user: AuthenticatedUser = Depends(require_institutional)):
    _require_tenant(user)
    _require_write(user)
    conn = _conn_or_503()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE growers SET deleted_at = NOW(), updated_at = NOW() "
            "WHERE id = %s::uuid AND tenant_id = %s::uuid AND deleted_at IS NULL",
            (grower_id, user.tenant_id),
        )
        affected = cur.rowcount
        conn.commit()
        cur.close()
    finally:
        _close(conn)
    if affected == 0:
        raise HTTPException(status_code=404, detail="Grower not found")
    return Response(status_code=204)


# --- helpers ---------------------------------------------------------------
def _fetch_grower(grower_id: str):
    conn = _conn_or_503()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(f"SELECT {_GROWER_COLS} FROM growers WHERE id = %s::uuid AND deleted_at IS NULL", (grower_id,))
        row = cur.fetchone()
        cur.close()
        return dict(row) if row else None
    finally:
        _close(conn)


def _json(value):
    import json
    return json.dumps(value) if value is not None else None


def _close(conn):
    try:
        conn.close()
    except Exception:
        pass
