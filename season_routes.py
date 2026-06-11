"""
Season accumulations endpoint (Depth Sprint PR D).

    GET /field/{field_id}/season-accumulations

Read-only. Serves two season-long curves for a field — accumulated GDD and
accumulated precipitation since planting — for the field-detail charts.

Light router (mirrors portfolio_routes/grower_routes): a self-contained
principal dependency (API-key or session, same shape as app.get_state_principal)
so it's unit-testable in isolation. Access is enforced by reusing the field
aggregator's ``resolve_access`` (admin / tenant membership / legacy user_id):
404 for an unknown field, 403 for no access. Pure series math lives in
``services.season.accumulations``; the provider call is ``climate_service``.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException

import climate_service
from schemas import SeasonAccumulationsResponse, SeasonAccumulationDay
from services.field_state.aggregator import resolve_access, FieldNotFound, FieldAccessDenied, _centroid
from services.season.accumulations import gdd_params_for, build_series, DailyWeather

router = APIRouter(tags=["season"])

MAX_WINDOW_DAYS = 240


def get_principal(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None),
) -> dict:
    """Resolve the caller to {requester_id, tenant_ids, is_admin}. Mirrors
    app.get_state_principal: an institutional API key scoped by X-Tenant-Id, or
    the role-aware session user."""
    if x_api_key:
        expected = os.environ.get("INSTITUTIONAL_API_KEY")
        if expected and x_api_key == expected and x_tenant_id:
            return {"requester_id": x_tenant_id, "tenant_ids": [x_tenant_id], "is_admin": False}
        raise HTTPException(status_code=401, detail="Invalid API key or missing X-Tenant-Id scope")
    from auth_roles import get_authenticated_user
    user = get_authenticated_user(authorization)
    return {"requester_id": user.user_id, "tenant_ids": user.tenant_ids, "is_admin": user.role == "admin"}


def _as_date(value) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


@router.get("/field/{field_id}/season-accumulations", response_model=SeasonAccumulationsResponse)
async def get_season_accumulations(field_id: str, principal: dict = Depends(get_principal)):
    # Access + field row (404 absent, 403 no access) — reuse the aggregator path.
    try:
        field = resolve_access(
            field_id, principal["requester_id"],
            tenant_ids=principal.get("tenant_ids"), is_admin=principal.get("is_admin", False),
        )
    except FieldNotFound:
        raise HTTPException(status_code=404, detail="Field not found")
    except FieldAccessDenied:
        raise HTTPException(status_code=403, detail="You do not have access to this field")

    planted = _as_date(field.get("planting_date"))
    if planted is None:
        raise HTTPException(status_code=422, detail="Field has no planting_date; season accumulations require one.")

    crop_type = field.get("crop_type") or "unknown"
    base, cap = gdd_params_for(crop_type)

    # Window: planting_date through yesterday (UTC), capped at MAX_WINDOW_DAYS.
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).replace(tzinfo=None)
    start = planted
    end = min(yesterday, planted + timedelta(days=MAX_WINDOW_DAYS))

    series_models = []
    total_gdd = 0.0
    total_precip = 0.0
    if start.date() <= end.date():
        lat, lon = _centroid(field.get("polygon_coordinates"))
        raw = await climate_service.get_daily_history(
            lat, lon, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"),
        )
        daily = [DailyWeather(d.get("date"), d.get("tmax"), d.get("tmin"), d.get("precip")) for d in raw]
        series, total_gdd, total_precip = build_series(daily, base, cap)
        series_models = [SeasonAccumulationDay(**d) for d in series]

    days_elapsed = max(0, (end.date() - start.date()).days)

    return SeasonAccumulationsResponse(
        field_id=str(field.get("id") or field_id),
        crop_type=crop_type,
        planting_date=planted.strftime("%Y-%m-%d"),
        days_elapsed=days_elapsed,
        gdd_base_c=base,
        gdd_cap_c=cap,
        total_gdd=total_gdd,
        total_precip_mm=total_precip,
        series=series_models,
    )
