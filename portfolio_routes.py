"""
Portfolio aggregate endpoint (MVP PR 2)
=======================================
    GET /portfolio/aggregate  — institutional portfolio summary + priorities.

Read-only, institutional-only (admins may target any tenant via ?tenant_id).
Light router (no AI-stack imports) so it stays unit-testable.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from auth_roles import get_authenticated_user
from schemas import AuthenticatedUser, PortfolioAggregateResponse
from services.portfolio.aggregate import compute_portfolio_aggregate, TenantNotFound

router = APIRouter(tags=["portfolio"])


@router.get("/portfolio/aggregate", response_model=PortfolioAggregateResponse)
async def get_portfolio_aggregate(
    tenant_id: Optional[str] = Query(
        None,
        description="Admin override: which tenant to query. Non-admin callers "
                    "may only query their own tenant.",
    ),
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    """Return the institutional portfolio aggregate for the caller's tenant.

    * institutional → own tenant only (passing a different ``tenant_id`` → 403)
    * admin → any institutional tenant (via ``tenant_id``, default own)
    * everyone else → 403
    """
    if user.role == "admin":
        target = tenant_id or user.tenant_id
    elif user.role == "institutional":
        if tenant_id is not None and tenant_id != user.tenant_id:
            raise HTTPException(status_code=403, detail="Cannot query another tenant's portfolio")
        target = user.tenant_id
    else:
        raise HTTPException(status_code=403, detail="Institutional access only")

    if not target:
        raise HTTPException(status_code=400, detail="No tenant specified")

    try:
        return await compute_portfolio_aggregate(target)
    except TenantNotFound:
        raise HTTPException(status_code=404, detail="Tenant not found or not institutional")
