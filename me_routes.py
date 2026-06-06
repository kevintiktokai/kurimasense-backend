"""
Current-user role endpoint (Workstream 2)
=========================================
    GET /me/role  — the authenticated user's role context.

The ONLY backend change in Workstream 2. Thin wrapper over Workstream 1's
``get_authenticated_user`` dependency so the frontend can route by role. Kept in
a light router module (no AI-stack imports) so it stays unit-testable.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from auth_roles import get_authenticated_user
from schemas import AuthenticatedUser

router = APIRouter(tags=["me"])


@router.get("/me/role", response_model=AuthenticatedUser)
def get_me_role(user: AuthenticatedUser = Depends(get_authenticated_user)) -> AuthenticatedUser:
    """Return ``{user_id, role, institutional_type, tenant_name}`` for the caller.

    Role context comes from ``get_authenticated_user`` (JWT verify + profiles
    lookup; brand-new users are auto-created as ``consumer``).
    """
    return user
