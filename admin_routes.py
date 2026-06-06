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

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from psycopg2.extras import RealDictCursor

from database import get_db_connection
from auth_roles import require_admin_token
from schemas import (
    UpdateUserRoleRequest, UpdateUserRoleResponse,
    Tenant, TenantDetail, TenantMember,
    CreateTenantRequest, UpdateTenantRequest,
    AddTenantMemberRequest, UpdateTenantMemberRequest,
)

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


# ===========================================================================
# Tenant management (Workstream 3) — all gated by X-Admin-Token
# ===========================================================================
_TENANT_COLS = (
    "id::text AS id, name, tenant_type, institutional_type, "
    "created_at, updated_at, deleted_at"
)


def _conn_or_503():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return conn


@router.post("/tenants", response_model=Tenant)
def create_tenant(body: CreateTenantRequest, _admin: bool = Depends(require_admin_token)):
    if body.tenant_type == "institutional" and not body.institutional_type:
        raise HTTPException(status_code=400, detail="institutional_type is required for institutional tenants")
    inst = body.institutional_type if body.tenant_type == "institutional" else None
    conn = _conn_or_503()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            f"INSERT INTO tenants (name, tenant_type, institutional_type) VALUES (%s, %s, %s) "
            f"RETURNING {_TENANT_COLS}",
            (body.name, body.tenant_type, inst),
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return Tenant(**dict(row))


@router.get("/tenants", response_model=list[Tenant])
def list_tenants(
    tenant_type: str | None = Query(None),
    _admin: bool = Depends(require_admin_token),
):
    conn = _conn_or_503()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        if tenant_type:
            cur.execute(
                f"SELECT {_TENANT_COLS} FROM tenants WHERE deleted_at IS NULL AND tenant_type = %s "
                f"ORDER BY created_at DESC",
                (tenant_type,),
            )
        else:
            cur.execute(
                f"SELECT {_TENANT_COLS} FROM tenants WHERE deleted_at IS NULL ORDER BY created_at DESC"
            )
        rows = cur.fetchall()
        cur.close()
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return [Tenant(**dict(r)) for r in rows]


@router.get("/tenants/{tenant_id}", response_model=TenantDetail)
def get_tenant(tenant_id: str, _admin: bool = Depends(require_admin_token)):
    conn = _conn_or_503()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(f"SELECT {_TENANT_COLS} FROM tenants WHERE id = %s::uuid", (tenant_id,))
        row = cur.fetchone()
        if not row:
            cur.close()
            raise HTTPException(status_code=404, detail="Tenant not found")
        cur.execute(
            "SELECT tenant_id::text AS tenant_id, user_id::text AS user_id, member_role, joined_at "
            "FROM tenant_members WHERE tenant_id = %s::uuid ORDER BY joined_at ASC",
            (tenant_id,),
        )
        members = [TenantMember(**dict(m)) for m in cur.fetchall()]
        cur.close()
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return TenantDetail(**dict(row), members=members)


@router.patch("/tenants/{tenant_id}", response_model=Tenant)
def update_tenant(tenant_id: str, body: UpdateTenantRequest, _admin: bool = Depends(require_admin_token)):
    sets, params = [], []
    if body.name is not None:
        sets.append("name = %s")
        params.append(body.name)
    if body.institutional_type is not None:
        sets.append("institutional_type = %s")
        params.append(body.institutional_type)
    if not sets:
        raise HTTPException(status_code=400, detail="No fields to update")
    sets.append("updated_at = NOW()")
    params.append(tenant_id)
    conn = _conn_or_503()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            f"UPDATE tenants SET {', '.join(sets)} WHERE id = %s::uuid RETURNING {_TENANT_COLS}",
            tuple(params),
        )
        row = cur.fetchone()
        if not row:
            conn.rollback()
            cur.close()
            raise HTTPException(status_code=404, detail="Tenant not found")
        conn.commit()
        cur.close()
    except HTTPException:
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return Tenant(**dict(row))


@router.delete("/tenants/{tenant_id}", status_code=204)
def delete_tenant(tenant_id: str, _admin: bool = Depends(require_admin_token)):
    conn = _conn_or_503()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE tenants SET deleted_at = NOW(), updated_at = NOW() "
            "WHERE id = %s::uuid AND deleted_at IS NULL",
            (tenant_id,),
        )
        affected = cur.rowcount
        conn.commit()
        cur.close()
    finally:
        try:
            conn.close()
        except Exception:
            pass
    if affected == 0:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return Response(status_code=204)


@router.post("/tenants/{tenant_id}/members", response_model=TenantMember)
def add_tenant_member(tenant_id: str, body: AddTenantMemberRequest, _admin: bool = Depends(require_admin_token)):
    conn = _conn_or_503()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "INSERT INTO tenant_members (tenant_id, user_id, member_role) VALUES (%s::uuid, %s::uuid, %s) "
            "ON CONFLICT (tenant_id, user_id) DO UPDATE SET member_role = EXCLUDED.member_role "
            "RETURNING tenant_id::text AS tenant_id, user_id::text AS user_id, member_role, joined_at",
            (tenant_id, body.user_id, body.member_role),
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
    except Exception as exc:
        try:
            conn.rollback()
        except Exception:
            pass
        # FK violation → tenant or user doesn't exist.
        raise HTTPException(status_code=404, detail="Tenant or user not found") from exc
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return TenantMember(**dict(row))


@router.patch("/tenants/{tenant_id}/members/{user_id}", response_model=TenantMember)
def update_tenant_member(tenant_id: str, user_id: str, body: UpdateTenantMemberRequest, _admin: bool = Depends(require_admin_token)):
    conn = _conn_or_503()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "UPDATE tenant_members SET member_role = %s WHERE tenant_id = %s::uuid AND user_id = %s::uuid "
            "RETURNING tenant_id::text AS tenant_id, user_id::text AS user_id, member_role, joined_at",
            (body.member_role, tenant_id, user_id),
        )
        row = cur.fetchone()
        if not row:
            conn.rollback()
            cur.close()
            raise HTTPException(status_code=404, detail="Membership not found")
        conn.commit()
        cur.close()
    except HTTPException:
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return TenantMember(**dict(row))


@router.delete("/tenants/{tenant_id}/members/{user_id}", status_code=204)
def remove_tenant_member(tenant_id: str, user_id: str, _admin: bool = Depends(require_admin_token)):
    conn = _conn_or_503()
    try:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM tenant_members WHERE tenant_id = %s::uuid AND user_id = %s::uuid",
            (tenant_id, user_id),
        )
        affected = cur.rowcount
        conn.commit()
        cur.close()
    finally:
        try:
            conn.close()
        except Exception:
            pass
    if affected == 0:
        raise HTTPException(status_code=404, detail="Membership not found")
    return Response(status_code=204)
