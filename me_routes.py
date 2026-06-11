"""
Current-user endpoints
======================
    GET  /me/role          — the authenticated user's role context (Workstream 2).
    POST /me/institutional — self-service institutional signup (Workstream 5).

Kept in a light router module (no AI-stack imports) so it stays unit-testable.
All SQL is psycopg2-parameterized (no string interpolation).
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from psycopg2.extras import RealDictCursor

from auth_roles import get_authenticated_user
from database import get_db_connection
from schemas import (
    AuthenticatedUser,
    SelfServeInstitutionalRequest,
    SelfServeInstitutionalResponse,
)

logger = logging.getLogger("kurimasense")

router = APIRouter(tags=["me"])


@router.get("/me/role", response_model=AuthenticatedUser)
def get_me_role(user: AuthenticatedUser = Depends(get_authenticated_user)) -> AuthenticatedUser:
    """Return ``{user_id, role, institutional_type, tenant_name}`` for the caller.

    Role context comes from ``get_authenticated_user`` (JWT verify + profiles
    lookup; brand-new users are auto-created as ``consumer``).
    """
    return user


@router.post("/me/institutional", response_model=SelfServeInstitutionalResponse)
def upgrade_me_to_institutional(
    body: SelfServeInstitutionalRequest,
    user: AuthenticatedUser = Depends(get_authenticated_user),
) -> SelfServeInstitutionalResponse:
    """Self-service institutional signup for the *authenticated* user.

    The user can only institutionalise themselves (the target is always
    ``user.user_id`` from the verified JWT — never a path/body param). In one
    transaction this:

      1. flips ``profiles.role`` → ``institutional`` and records
         ``institutional_type`` + ``tenant_name``;
      2. provisions an institutional ``tenant`` (reusing one the user already
         owns, so re-submitting is idempotent and never creates duplicates); and
      3. adds the user to that tenant as ``owner``,

    so the portfolio shell and field/grower management work immediately. The
    profiles row is guaranteed to exist here because ``get_authenticated_user``
    auto-creates a default consumer row for brand-new users.
    """
    user_id = user.user_id
    institutional_type = body.institutional_type
    tenant_name = body.organization_name.strip()
    if not tenant_name:
        raise HTTPException(status_code=400, detail="organization_name is required")

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database unavailable")
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # 1. Promote the caller's profile to institutional. This row exists
        #    because get_authenticated_user created it (consumer) if absent.
        cur.execute(
            """
            UPDATE profiles
               SET role = 'institutional',
                   institutional_type = %s,
                   tenant_name = %s,
                   updated_at = NOW()
             WHERE id = %s::uuid
            RETURNING id
            """,
            (institutional_type, tenant_name, user_id),
        )
        if cur.fetchone() is None:
            # Defensive: should not happen (dependency creates the row first).
            cur.execute(
                """
                INSERT INTO profiles (id, role, institutional_type, tenant_name)
                VALUES (%s::uuid, 'institutional', %s, %s)
                ON CONFLICT (id) DO UPDATE
                    SET role = 'institutional',
                        institutional_type = EXCLUDED.institutional_type,
                        tenant_name = EXCLUDED.tenant_name,
                        updated_at = NOW()
                """,
                (user_id, institutional_type, tenant_name),
            )

        # 2. Reuse an institutional tenant the user already owns (idempotent
        #    re-submit) rather than creating a duplicate.
        cur.execute(
            """
            SELECT t.id::text AS id
              FROM tenants t
              JOIN tenant_members tm ON tm.tenant_id = t.id
             WHERE tm.user_id = %s::uuid
               AND t.tenant_type = 'institutional'
               AND t.deleted_at IS NULL
             ORDER BY t.created_at ASC
             LIMIT 1
            """,
            (user_id,),
        )
        existing = cur.fetchone()

        if existing:
            tenant_id = existing["id"]
            cur.execute(
                """
                UPDATE tenants
                   SET name = %s,
                       institutional_type = %s,
                       updated_at = NOW()
                 WHERE id = %s::uuid
                """,
                (tenant_name, institutional_type, tenant_id),
            )
        else:
            cur.execute(
                """
                INSERT INTO tenants (name, tenant_type, institutional_type)
                VALUES (%s, 'institutional', %s)
                RETURNING id::text AS id
                """,
                (tenant_name, institutional_type),
            )
            tenant_id = cur.fetchone()["id"]

        # 3. Ensure the user is an owner of the tenant.
        cur.execute(
            """
            INSERT INTO tenant_members (tenant_id, user_id, member_role)
            VALUES (%s::uuid, %s::uuid, 'owner')
            ON CONFLICT (tenant_id, user_id) DO UPDATE
                SET member_role = 'owner'
            """,
            (tenant_id, user_id),
        )

        conn.commit()
        cur.close()
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        try:
            conn.rollback()
        except Exception:
            pass
        logger.error("Self-serve institutional signup failed for %s: %s", user_id, exc)
        raise HTTPException(status_code=500, detail="Failed to set up institutional account")
    finally:
        try:
            conn.close()
        except Exception:
            pass

    return SelfServeInstitutionalResponse(
        user_id=user_id,
        role="institutional",
        institutional_type=institutional_type,
        tenant_name=tenant_name,
        tenant_id=tenant_id,
        member_role="owner",
    )
