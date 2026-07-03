"""
Soil Intelligence API routes
============================
Read + refresh endpoints for a field's Soil Intelligence Profile.

  * ``GET  /fields/{id}/soil``          — return the stored profile (building it
    on first access if absent). Cheap on the common path (DB read only).
  * ``POST /fields/{id}/soil/refresh``  — force a rebuild from providers.

Access uses the canonical ``resolve_access`` gate (admin / tenant membership /
legacy user_id) so consumer and institutional callers both get correct
403-vs-404 behaviour, identical to the scouting/season routes.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from auth_roles import get_authenticated_user
from schemas import AuthenticatedUser
from services.field_state.aggregator import (
    FieldAccessDenied,
    FieldNotFound,
    resolve_access,
)
from services.soil_intelligence import get_or_build_profile, get_stored_profile

router = APIRouter(tags=["soil"])


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


def _centroid(field_row: dict) -> tuple[Optional[float], Optional[float]]:
    """Best-effort polygon centroid → (lat, lon)."""
    coords = field_row.get("polygon_coordinates")
    if not coords:
        return (None, None)
    try:
        pts = coords if isinstance(coords, list) else []
        lats = [p["lat"] for p in pts if isinstance(p, dict) and "lat" in p]
        lons = [p["lon"] for p in pts if isinstance(p, dict) and "lon" in p]
        if lats and lons:
            return (sum(lats) / len(lats), sum(lons) / len(lons))
    except Exception:
        pass
    return (None, None)


def _serialise(profile) -> Dict[str, Any]:
    """Frontend-friendly shape: flat attribute map + provider status + meta."""
    if profile is None:
        return {"available": False, "attributes": {}, "provider_status": {}}
    return {
        "available": not profile.is_empty(),
        "field_id": profile.field_id,
        "lat": profile.lat,
        "lon": profile.lon,
        "built_at": profile.built_at,
        "provider_status": profile.provider_status,
        "attributes": {k: a.to_dict() for k, a in profile.attributes.items()},
        "summary": profile.to_ai_summary(),
    }


@router.get("/fields/{field_id}/soil")
async def get_field_soil(
    field_id: str,
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    """Return the field's soil profile, building it on first access if needed."""
    field = _resolve(field_id, user)
    lat, lon = _centroid(field)
    try:
        profile = await get_or_build_profile(
            field_id, lat, lon,
            user_id=user.user_id, tenant_ids=user.tenant_ids,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Soil profile unavailable: {e}")
    return _serialise(profile)


@router.post("/fields/{field_id}/soil/refresh")
async def refresh_field_soil(
    field_id: str,
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    """Force a rebuild of the soil profile from all providers."""
    field = _resolve(field_id, user)
    lat, lon = _centroid(field)
    if lat is None or lon is None:
        raise HTTPException(status_code=400, detail="Field has no coordinates to sample")
    try:
        profile = await get_or_build_profile(
            field_id, lat, lon,
            user_id=user.user_id, tenant_ids=user.tenant_ids,
            force_refresh=True,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Soil refresh failed: {e}")
    return _serialise(profile)
