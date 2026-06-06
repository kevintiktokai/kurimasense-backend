"""
Admin role-management endpoints (Workstream 1)
==============================================
    GET  /admin/users/{user_id}/role  — inspect a user's current role
    POST /admin/users/{user_id}/role  — set a user's role

Both are gated by the ``X-Admin-Token`` header (see ``auth_roles.require_admin_token``).
Implemented as an ``APIRouter`` and included from ``app.py`` so it imports only
light deps (schemas, auth_roles, database) and stays unit-testable without the
AI stack. All SQL is psycopg2-parameterized (no string interpolation).
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from psycopg2.extras import RealDictCursor

from database import get_db_connection
from auth_roles import require_admin_token
from schemas import UpdateUserRoleRequest, UpdateUserRoleResponse

logger = logging.getLogger("kurimasense")

router = APIRouter(prefix="/admin", tags=["admin"])


def _row_to_response(user_id: str, row: dict) -> UpdateUserRoleResponse:
    updated = row.get("updated_at")
    return UpdateUserRoleResponse(
        user_id=user_id,
        role=row.get("role"),
        institutional_type=row.get("institutional_type"),
        tenant_name=row.get("tenant_name"),
        updated_at=updated.isoformat() if hasattr(updated, "isoformat") else (str(updated) if updated else ""),
    )


@router.get("/users/{user_id}/role", response_model=UpdateUserRoleResponse)
def get_user_role(user_id: str, _admin: bool = Depends(require_admin_token)):
    """Return a user's current role context. 404 if the user has no profile."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database unavailable")
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT role, institutional_type, tenant_name, updated_at
            FROM profiles WHERE id = %s::uuid
            """,
            (user_id,),
        )
        row = cur.fetchone()
        cur.close()
    finally:
        try:
            conn.close()
        except Exception:
            pass

    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return _row_to_response(user_id, dict(row))


@router.post("/users/{user_id}/role", response_model=UpdateUserRoleResponse)
def set_user_role(
    user_id: str,
    body: UpdateUserRoleRequest,
    _admin: bool = Depends(require_admin_token),
):
    """
    Set a user's role. Validation:
      * institutional role requires institutional_type (400 otherwise);
      * non-institutional roles clear institutional_type + tenant_name (a warning
        is logged if the caller tried to set them);
      * unknown user_id → 404.
    """
    if body.role == "institutional" and not body.institutional_type:
        raise HTTPException(
            status_code=400,
            detail="institutional_type is required when role is 'institutional'",
        )

    institutional_type = body.institutional_type
    tenant_name = body.tenant_name
    if body.role != "institutional":
        if institutional_type is not None or tenant_name is not None:
            logger.warning(
                "Clearing institutional_type/tenant_name: they were set with non-institutional role '%s' for user %s",
                body.role, user_id,
            )
        institutional_type = None
        tenant_name = None

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database unavailable")
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            UPDATE profiles
               SET role = %s,
                   institutional_type = %s,
                   tenant_name = %s,
                   updated_at = NOW()
             WHERE id = %s::uuid
            RETURNING role, institutional_type, tenant_name, updated_at
            """,
            (body.role, institutional_type, tenant_name, user_id),
        )
        row = cur.fetchone()
        if row is None:
            conn.rollback()
            cur.close()
            raise HTTPException(status_code=404, detail="User not found")
        conn.commit()
        cur.close()
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        try:
            conn.rollback()
        except Exception:
            pass
        logger.error("Failed to set role for %s: %s", user_id, exc)
        raise HTTPException(status_code=500, detail="Failed to update role")
    finally:
        try:
            conn.close()
        except Exception:
            pass

    return _row_to_response(user_id, dict(row))
