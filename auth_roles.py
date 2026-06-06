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
# Role-aware dependency (sibling of verify_token)
# ---------------------------------------------------------------------------
def get_authenticated_user(authorization: Optional[str] = Header(None)) -> AuthenticatedUser:
    """
    Verify the JWT (reusing ``deps.verify_token``) and attach role context.

    Returns an ``AuthenticatedUser``. ``verify_token`` is imported lazily so this
    module does not pull in the heavy AI stack at import time.
    """
    from deps import verify_token  # lazy: avoids importing ai_brain/openai here

    user_id = verify_token(authorization)
    role, institutional_type, tenant_name = fetch_or_create_role(user_id)
    return AuthenticatedUser(
        user_id=user_id,
        role=role,
        institutional_type=institutional_type,
        tenant_name=tenant_name,
    )


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
