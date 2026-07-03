"""
Role-aware authentication (Workstream 1)
========================================
Adds role context on top of the existing JWT auth WITHOUT changing
``deps.verify_token`` — which keeps returning a bare ``user_id`` string so the
48 endpoints using ``user_id: str = Depends(verify_token)`` behave identically
(the dominant backward-compatibility requirement).

Public surface:
    * get_authenticated_user(...)  -> AuthenticatedUser   (JWT + role lookup)
    * require_consumer / require_institutional / require_admin  (role guards)
    * require_admin_token(...)     -> True                (X-Admin-Token gate)

DESIGN NOTE (deviation from the literal spec): the prompt suggested having
``verify_token`` itself return ``AuthenticatedUser`` and the guards depend on it.
Doing so would change the value every existing endpoint receives from a ``str``
to a model and break all of them. We instead provide a *sibling* dependency
``get_authenticated_user`` that the guards use; ``verify_token`` is untouched.
``ai_brain`` is imported lazily so this module stays light and testable.
"""

from __future__ import annotations

import hmac
import logging
import os
from typing import Optional, Tuple

from fastapi import Depends, Header, HTTPException
from psycopg2.extras import RealDictCursor

from database import get_db_connection
from schemas import AuthenticatedUser

logger = logging.getLogger("kurimasense")

_VALID_ROLES = {"consumer", "institutional", "admin"}
_VALID_INSTITUTIONAL_TYPES = {"buyer", "lender", "insurer", "grower"}


# ---------------------------------------------------------------------------
# Role resolution from the profiles row
# ---------------------------------------------------------------------------
def _coerce_role(value: Optional[str]) -> str:
    """Map any stored role to the canonical vocabulary. Legacy/unknown values
    (e.g. pre-migration 'smallholder'/'farmer'/NULL) read as 'consumer' so an
    AuthenticatedUser can always be constructed."""
    return value if value in _VALID_ROLES else "consumer"


def _coerce_institutional_type(role: str, value: Optional[str]) -> Optional[str]:
    if role != "institutional":
        return None
    return value if value in _VALID_INSTITUTIONAL_TYPES else None


def fetch_or_create_role(user_id: str) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Return (role, institutional_type, tenant_name) for ``user_id``.

    Creates a default ``consumer`` profile row if the user has none yet
    (brand-new user). Degrades to a safe ``consumer`` default if the DB is
    unavailable, so authentication never 500s on role lookup.
    """
    conn = get_db_connection()
    if not conn:
        return "consumer", None, None
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT role, institutional_type, tenant_name FROM profiles WHERE id = %s::uuid",
            (user_id,),
        )
        row = cur.fetchone()
        if row is None:
            # Brand-new user: create a default consumer profile (idempotent).
            cur.execute(
                """
                INSERT INTO profiles (id, role) VALUES (%s::uuid, 'consumer')
                ON CONFLICT (id) DO NOTHING
                """,
                (user_id,),
            )
            conn.commit()
            cur.close()
            return "consumer", None, None
        cur.close()
        role = _coerce_role(row.get("role"))
        inst = _coerce_institutional_type(role, row.get("institutional_type"))
        tenant = row.get("tenant_name") if role == "institutional" else None
        return role, inst, tenant
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Role lookup failed for %s: %s", user_id, exc)
        return "consumer", None, None
    finally:
        try:
            conn.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Tenant context (Workstream 3)
# ---------------------------------------------------------------------------
def fetch_tenant_context(user_id: str):
    """
    Return (primary_tenant_id, tenant_ids, primary_member_role) for ``user_id``.

    Primary = earliest-joined membership. Degrades to (None, [], None) if the
    tenant tables don't exist yet (pre-migration) or the DB is unavailable, so
    authentication never breaks on the tenant lookup.
    """
    conn = get_db_connection()
    if not conn:
        return None, [], None
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # Suspended members (migration 013) keep their row for history but lose
        # tenant context platform-wide: excluding them here means every
        # tenant-scoped endpoint sees them as a user with no memberships.
        cur.execute(
            """
            SELECT tenant_id::text AS tenant_id, member_role
            FROM tenant_members
            WHERE user_id = %s::uuid
              AND COALESCE(status, 'active') = 'active'
            ORDER BY joined_at ASC, tenant_id ASC
            """,
            (user_id,),
        )
        rows = cur.fetchall()
        cur.close()
        if not rows:
            return None, [], None
        tenant_ids = [r["tenant_id"] for r in rows]
        return tenant_ids[0], tenant_ids, rows[0].get("member_role")
    except Exception as exc:  # pragma: no cover - defensive (e.g. table missing pre-migration)
        logger.warning("Tenant lookup failed for %s: %s", user_id, exc)
        return None, [], None
    finally:
        try:
            conn.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Role-aware dependency (sibling of verify_token)
# ---------------------------------------------------------------------------
def fetch_primary_institutional_tenant(user_id: str):
    """
    Return ``(institutional_type, tenant_name)`` for the user's earliest-joined
    **institutional** tenant membership, or ``None`` if they belong to no
    institutional tenant.

    Used as a downgrade guard: a member of an institutional tenant is an
    institutional user even if ``profiles.role`` was reset to ``consumer`` by a
    stray profile write — tenant membership wins, so an institutional owner/
    officer/viewer can never be silently downgraded. Degrades to ``None`` (no
    promotion) if the tenant tables are absent or the DB is unavailable.
    """
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT t.institutional_type, t.name
            FROM tenant_members tm
            JOIN tenants t ON t.id = tm.tenant_id
            WHERE tm.user_id = %s::uuid
              AND t.tenant_type = 'institutional'
              AND t.deleted_at IS NULL
            ORDER BY tm.joined_at ASC, tm.tenant_id ASC
            LIMIT 1
            """,
            (user_id,),
        )
        row = cur.fetchone()
        cur.close()
        if not row:
            return None
        # Tenants always carry a type, but coerce + default defensively so the
        # promoted AuthenticatedUser always has a valid institutional_type.
        inst_type = _coerce_institutional_type("institutional", row.get("institutional_type")) or "buyer"
        return inst_type, row.get("name")
    except Exception as exc:  # pragma: no cover - defensive (table missing pre-migration)
        logger.warning("Institutional-tenant lookup failed for %s: %s", user_id, exc)
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def get_authenticated_user(authorization: Optional[str] = Header(None)) -> AuthenticatedUser:
    """
    Verify the JWT (reusing ``deps.verify_token``) and attach role + tenant context.

    Returns an ``AuthenticatedUser``. ``verify_token`` is imported lazily so this
    module does not pull in the heavy AI stack at import time.
    """
    from deps import verify_token  # lazy: avoids importing ai_brain/openai here

    user_id = verify_token(authorization)
    role, institutional_type, tenant_name = fetch_or_create_role(user_id)
    tenant_id, tenant_ids, member_role = fetch_tenant_context(user_id)

    # Downgrade guard: membership in an institutional tenant makes the user
    # institutional regardless of profiles.role. Role resolution reads a single
    # mutable profiles.role column, so a stray profile write (onboarding/settings)
    # could otherwise silently downgrade an institutional owner to consumer and
    # hide their whole portfolio. Tenant membership wins. Only runs in that
    # downgrade case (non-admin, not already institutional, has a tenant) — so a
    # normal institutional user pays no extra query.
    if role not in ("admin", "institutional") and tenant_id is not None:
        promoted = fetch_primary_institutional_tenant(user_id)
        if promoted is not None:
            role = "institutional"
            institutional_type, tenant_name = promoted

    return AuthenticatedUser(
        user_id=user_id,
        role=role,
        institutional_type=institutional_type,
        tenant_name=tenant_name,
        tenant_id=tenant_id,
        tenant_ids=tenant_ids,
        member_role=member_role,
    )


# ---------------------------------------------------------------------------
# Field access helpers (Workstream 3)
# ---------------------------------------------------------------------------
def user_can_access_field(user: AuthenticatedUser, field_tenant_id) -> bool:
    """True if ``user`` may READ fields in ``field_tenant_id`` (admin: always)."""
    if user.role == "admin":
        return True
    if field_tenant_id is None:
        return False
    return str(field_tenant_id) in user.tenant_ids


# Member-role permission tiers (migration 013). Legacy roles map into the new
# vocabulary: officer ≈ manager (can write + assign), viewer/analyst read-only.
# Keep these as module-level sets so the tiers stay in one place and future
# roles slot in by editing a set, not call sites.
MANAGE_TEAM_ROLES = frozenset({"owner", "admin"})
ASSIGN_FIELD_ROLES = frozenset({"owner", "admin", "manager", "officer"})
WRITE_FIELD_ROLES = frozenset({"owner", "admin", "manager", "agronomist",
                               "field_officer", "officer"})


def user_can_modify_field(user: AuthenticatedUser, field_tenant_id) -> bool:
    """True if ``user`` may WRITE fields in ``field_tenant_id``. Writing roles
    (owner/admin/manager/agronomist/field_officer + legacy officer) can modify;
    analysts and viewers cannot; platform admin always can."""
    if user.role == "admin":
        return True
    if field_tenant_id is None or str(field_tenant_id) not in user.tenant_ids:
        return False
    return user.member_role in WRITE_FIELD_ROLES


def user_can_manage_team(user: AuthenticatedUser) -> bool:
    """True if ``user`` may manage tenant membership (invite/suspend/remove/
    change roles). Platform admin or tenant owner/admin."""
    return user.role == "admin" or user.member_role in MANAGE_TEAM_ROLES


def user_can_assign_fields(user: AuthenticatedUser) -> bool:
    """True if ``user`` may assign fields to team members."""
    return user.role == "admin" or user.member_role in ASSIGN_FIELD_ROLES


# ---------------------------------------------------------------------------
# Role guards — DEFINED but NOT attached to any endpoint in this PR.
# (Workstream 2+ will apply them as institutional endpoints get built.)
# ---------------------------------------------------------------------------
def require_consumer(user: AuthenticatedUser = Depends(get_authenticated_user)) -> AuthenticatedUser:
    """Endpoint guard: only consumer users may access."""
    if user.role != "consumer":
        raise HTTPException(status_code=403, detail="Consumer access only")
    return user


def require_institutional(user: AuthenticatedUser = Depends(get_authenticated_user)) -> AuthenticatedUser:
    """Endpoint guard: only institutional users may access."""
    if user.role != "institutional":
        raise HTTPException(status_code=403, detail="Institutional access only")
    return user


def require_admin(user: AuthenticatedUser = Depends(get_authenticated_user)) -> AuthenticatedUser:
    """Endpoint guard: only admin users may access.

    Decision: admin is a *distinct* tier and does NOT implicitly satisfy the
    consumer/institutional guards — those check role equality. Admins manage
    roles via the X-Admin-Token admin endpoints, not via session role guards.
    """
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access only")
    return user


# ---------------------------------------------------------------------------
# X-Admin-Token gate (for the admin role-management endpoints)
# ---------------------------------------------------------------------------
def require_admin_token(x_admin_token: Optional[str] = Header(None)) -> bool:
    """
    Gate admin endpoints on the ``X-Admin-Token`` header matching the
    ``ADMIN_TOKEN`` env var (constant-time compare). If ``ADMIN_TOKEN`` is unset,
    all access is denied (safe default). Establishes the convention referenced by
    the spec (no pre-existing admin endpoint existed — see audit finding F2).
    """
    expected = os.environ.get("ADMIN_TOKEN")
    if not expected or not x_admin_token or not hmac.compare_digest(x_admin_token, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing admin token")
    return True
