"""
Season lifecycle + pre-plant planning API routes.

Two groups of endpoints:

**Season lifecycle** — CRUD over the ``seasons`` table plus the transitions
(``activate`` / ``harvest`` / ``close`` / ``abandon``) that carry side effects.

**Pre-plant planning** — the brief a farmer gets *before* the seed is bought:
rotation context, target plant population translated into row and in-row
spacing, and the crop's fertiliser schedule rendered as a dated, quantified
programme. Prices are out of scope by design; farmers price against their own
supplier quotes.

Access uses the canonical ``resolve_access`` gate, matching soil/scouting/season
routes, so consumer and institutional callers both get correct 403-vs-404
behaviour.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from auth_roles import get_authenticated_user
from schemas import AuthenticatedUser
from services.field_state.aggregator import (
    FieldAccessDenied,
    FieldNotFound,
    resolve_access,
)
from services.planning.establishment import (
    assess_stand,
    build_establishment_plan,
    stand_check_row_length_m,
)
from services.planning.fertiliser import build_fertiliser_programme
from services.planning.postharvest import build_post_harvest_plan
from services.seasons.retrospective import build_retrospective
from services.planning.windows import build_action_windows
from services.seasons import lifecycle
from services.seasons import service as seasons

router = APIRouter(tags=["seasons"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
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


def _resolve_season(season_id: str, user: AuthenticatedUser) -> dict:
    """Load a season, then re-check access through its parent field."""
    try:
        season = seasons.get(season_id, user.user_id, user.tenant_ids)
    except seasons.SeasonNotFound:
        raise HTTPException(status_code=404, detail="Season not found")
    _resolve(season["field_id"], user)
    return season


def _as_date(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _guard(fn, *args, **kwargs):
    """Map service-layer exceptions onto HTTP status codes."""
    try:
        return fn(*args, **kwargs)
    except seasons.SeasonNotFound:
        raise HTTPException(status_code=404, detail="Season not found")
    except lifecycle.InvalidTransition as e:
        raise HTTPException(status_code=409, detail=str(e))
    except seasons.SeasonConflict as e:
        raise HTTPException(status_code=409, detail=str(e))


def _variety_potential(crop: Optional[str], variety: Optional[str]) -> Optional[float]:
    """A realistic ceiling for this variety, from the crop_varieties catalogue.

    Uses the LOW end of the variety's published potential band, not the high
    end. Breeder maxima come from trial plots under ideal management; measuring
    a smallholder against one manufactures a gap that no management could have
    closed, and a benchmark a farmer cannot recognise is a benchmark they stop
    reading.
    """
    if not crop or not variety:
        return None
    try:
        from database import get_db_connection
        from psycopg2.extras import RealDictCursor

        conn = get_db_connection()
        if not conn:
            return None
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(
                "SELECT yield_potential_low, yield_potential_high FROM crop_varieties "
                "WHERE LOWER(crop_name) = LOWER(%s) AND LOWER(variety_name) = LOWER(%s) LIMIT 1",
                (crop, variety),
            )
            row = cur.fetchone()
            cur.close()
            if not row:
                return None
            low = row.get("yield_potential_low")
            return float(low) if low is not None else None
        finally:
            try:
                conn.close()
            except Exception:
                pass
    except Exception as e:
        print(f"[season_lifecycle_routes] variety potential lookup failed: {e}")
        return None


def _field_context(field: dict) -> Dict[str, Any]:
    """Planning inputs derivable from the field record itself."""
    return {
        "area_hectares": float(field["size_hectares"]) if field.get("size_hectares") else None,
        "natural_region": field.get("natural_region"),
    }


# ---------------------------------------------------------------------------
# Season lifecycle
# ---------------------------------------------------------------------------
@router.get("/fields/{field_id}/seasons")
def list_field_seasons(
    field_id: str,
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    """Every season for a field, newest first — the multi-season history spine."""
    _resolve(field_id, user)
    rows = seasons.list_for_field(field_id, user.user_id, user.tenant_ids)
    return {"field_id": field_id, "seasons": rows, "count": len(rows)}


@router.post("/fields/{field_id}/seasons", status_code=201)
def create_planned_season(
    field_id: str,
    body: Dict[str, Any] = Body(default_factory=dict),
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    """Create a **planned** season — the pre-plant record.

    A field may hold several planned seasons at once (a farmer comparing crop
    options); only one may ever be active.
    """
    field = _resolve(field_id, user)
    if not body.get("crop_type"):
        raise HTTPException(status_code=400, detail="crop_type is required")
    return _guard(
        seasons.plan_season,
        field_id, field.get("tenant_id"), user.user_id, body, user.tenant_ids,
    )


@router.get("/seasons/{season_id}")
def get_one_season(
    season_id: str,
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    return _resolve_season(season_id, user)


@router.patch("/seasons/{season_id}")
def patch_season(
    season_id: str,
    body: Dict[str, Any] = Body(default_factory=dict),
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    """Update a season. Status is not writable here — use the transitions."""
    _resolve_season(season_id, user)
    body.pop("status", None)
    return _guard(seasons.update, season_id, body, user.user_id, user.tenant_ids)


@router.post("/seasons/{season_id}/activate")
def activate_season(
    season_id: str,
    body: Dict[str, Any] = Body(default_factory=dict),
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    """planned → active: the crop is in the ground.

    Mirrors the crop onto ``fields`` (so every existing screen updates) and
    attributes observations from the planting date onward to this season.
    """
    _resolve_season(season_id, user)
    return _guard(
        seasons.activate,
        season_id, user.user_id, body.get("planting_date"), user.tenant_ids,
    )


@router.post("/seasons/{season_id}/harvest")
def harvest_season(
    season_id: str,
    body: Dict[str, Any] = Body(default_factory=dict),
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    """active → harvested. The crop is off the field; drying and storage follow."""
    _resolve_season(season_id, user)
    return _guard(
        seasons.record_harvest,
        season_id, user.user_id, body.get("harvest_date"),
        body.get("yield_tonnes_per_ha"), user.tenant_ids,
    )


@router.post("/seasons/{season_id}/close")
def close_season(
    season_id: str,
    body: Dict[str, Any] = Body(default_factory=dict),
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    """harvested → closed. Terminal — the season becomes history."""
    _resolve_season(season_id, user)
    return _guard(
        seasons.close,
        season_id, user.user_id, body.get("yield_tonnes_per_ha"), user.tenant_ids,
    )


@router.post("/seasons/{season_id}/abandon")
def abandon_season(
    season_id: str,
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    """Abandon a planned or active season (write-off, replant, change of plan)."""
    _resolve_season(season_id, user)
    return _guard(
        seasons.transition,
        season_id, lifecycle.STATUS_ABANDONED, user.user_id, user.tenant_ids,
    )


# ---------------------------------------------------------------------------
# Rotation context
# ---------------------------------------------------------------------------
@router.get("/fields/{field_id}/windows")
def get_action_windows(
    field_id: str,
    soil_texture: Optional[str] = Query(None),
    include_closed: bool = Query(False),
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    """The operations that are closing, ranked by cost per remaining day.

    A farmer with forty things to do does not need a longer list — they need to
    know which few are irreversible this week. Ranking by date alone puts a
    cheap task closing tomorrow above a costly one closing next week, which is
    exactly the prioritisation that loses a season.
    """
    _resolve(field_id, user)

    from services.seasons import repository as season_repo
    season = season_repo.get_active_season(field_id, user.user_id, user.tenant_ids)
    if not season:
        return {
            "field_id": field_id,
            "season_id": None,
            "windows": [],
            "reason": "No season is currently growing in this field.",
        }

    try:
        from crop_profiles import get_crop_profile_or_generic
        profile = get_crop_profile_or_generic(season.get("crop_type") or "")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Crop profile unavailable: {e}")

    windows = build_action_windows(
        profile,
        planting_date=season.get("planting_date"),
        emergence_date=season.get("emergence_date"),
        soil_texture=soil_texture,
        stand_already_checked=season.get("established_population_per_ha") is not None,
        include_closed=include_closed,
    )
    return {
        "field_id": field_id,
        "season_id": season.get("id"),
        "crop_type": season.get("crop_type"),
        "planting_date": season.get("planting_date"),
        "windows": windows,
    }


@router.get("/seasons/{season_id}/retrospective")
def get_season_retrospective(
    season_id: str,
    potential_yield_t_ha: Optional[float] = Query(
        None, gt=0, description="Realistic ceiling; derived from the variety if omitted"
    ),
    late_topdress_days: Optional[int] = Query(None, ge=0),
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    """Where this season's yield gap went.

    Attributes the shortfall only to factors there is a measurement for, and
    reports the remainder as unexplained. A decomposition that always sums to
    exactly 100% is one that has been fudged, and a farmer who spots one fudged
    line discounts the whole thing.
    """
    season = _resolve_season(season_id, user)

    potential = potential_yield_t_ha
    if potential is None:
        potential = _variety_potential(season.get("crop_type"), season.get("variety"))

    return build_retrospective(
        season,
        potential_yield_t_ha=potential,
        late_topdress_days=late_topdress_days,
    ).to_dict()


@router.get("/fields/{field_id}/post-harvest")
def get_post_harvest_plan(
    field_id: str,
    crop: Optional[str] = Query(None, description="Defaults to the field's current crop"),
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    """Drying, grading, storage and monitoring for a crop that is off the field.

    Harvest closes the loop for the model; for the farmer it opens the riskiest
    window of the year. Regional storage losses run 20-30%, so a flawless season
    can still lose a quarter of itself in the shed. Every crop profile has
    carried ``harvest_moisture``, ``storage_conditions`` and
    ``post_harvest_notes`` since the knowledge base was written; nothing has
    ever displayed them.
    """
    field = _resolve(field_id, user)

    crop_name = crop or field.get("crop_type")
    if not crop_name:
        raise HTTPException(
            status_code=400,
            detail="No crop set for this field, so no post-harvest plan can be built.",
        )

    try:
        from crop_profiles import get_crop_profile_or_generic
        profile = get_crop_profile_or_generic(crop_name)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Crop profile unavailable: {e}")

    return build_post_harvest_plan(profile).to_dict()


@router.get("/fields/{field_id}/season-history")
def get_field_season_history(
    field_id: str,
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    """Season-over-season history, aligned on days after planting.

    The alignment is the point: calendar dates compare a six-leaf crop with a
    tasselling one and call the difference performance. Crop age is the only
    axis on which two seasons are the same thing.
    """
    _resolve(field_id, user)
    return seasons.field_history(field_id, user.user_id, user.tenant_ids)


@router.get("/fields/{field_id}/rotation")
def get_rotation_context(
    field_id: str,
    candidate_crop: Optional[str] = Query(None),
    tillage_practice: Optional[str] = Query(None),
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    """What this field's cropping history implies for the next crop.

    Drives the residue-inoculum disease risk the crop profiles have always
    encoded but could never apply, because nothing recorded what grew here last.
    """
    _resolve(field_id, user)
    return seasons.rotation_context(
        field_id, user.user_id, candidate_crop, tillage_practice, user.tenant_ids
    )


# ---------------------------------------------------------------------------
# Pre-plant planning
# ---------------------------------------------------------------------------
@router.get("/fields/{field_id}/plan/establishment")
def get_establishment_plan(
    field_id: str,
    crop: str = Query(..., description="Crop to plan for"),
    natural_region: Optional[str] = Query(None),
    irrigated: bool = Query(False),
    rainfall_outlook: Optional[str] = Query(None),
    row_spacing_cm: Optional[float] = Query(None, gt=0),
    germination_pct: float = Query(90.0, gt=0, le=100),
    target_population: Optional[int] = Query(None, gt=0),
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    """Target population translated into spacing, seed quantity and a field check.

    The units matter: "44,000 plants/ha" is unactionable holding a hoe, so the
    response leads with row spacing, in-row spacing and a countable check.
    """
    field = _resolve(field_id, user)
    ctx = _field_context(field)

    plan = build_establishment_plan(
        crop,
        natural_region=natural_region or ctx["natural_region"],
        irrigated=irrigated,
        seasonal_rainfall_outlook=rainfall_outlook,
        area_hectares=ctx["area_hectares"],
        row_spacing_cm=row_spacing_cm,
        germination_pct=germination_pct,
        target_population_override=target_population,
    )
    if plan is None:
        raise HTTPException(
            status_code=422,
            detail=(
                f"No establishment agronomy is defined for '{crop}' yet. "
                f"A wrong plant population is worse than none, so no estimate is "
                f"offered rather than a guess."
            ),
        )
    return plan.to_dict()


@router.get("/fields/{field_id}/plan/fertiliser")
def get_fertiliser_plan(
    field_id: str,
    crop: str = Query(...),
    planting_date: Optional[str] = Query(None),
    soil_ph: Optional[float] = Query(None, gt=0, le=14),
    soil_texture: Optional[str] = Query(None),
    irrigated: bool = Query(False),
    target_yield_t_ha: Optional[float] = Query(None, gt=0),
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    """The crop's fertiliser schedule as a dated, quantified programme.

    Costs are deliberately absent — farmers price against their own quotes.
    """
    field = _resolve(field_id, user)
    ctx = _field_context(field)

    try:
        from crop_profiles import get_crop_profile_or_generic
        profile = get_crop_profile_or_generic(crop)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Crop profile unavailable: {e}")

    programme = build_fertiliser_programme(
        profile,
        planting_date=_as_date(planting_date),
        area_hectares=ctx["area_hectares"],
        soil_ph=soil_ph,
        soil_texture=soil_texture,
        irrigated=irrigated,
        target_yield_t_ha=target_yield_t_ha,
    )
    return programme.to_dict()


@router.get("/fields/{field_id}/plan/pre-plant")
def get_pre_plant_brief(
    field_id: str,
    crop: str = Query(...),
    planting_date: Optional[str] = Query(None),
    natural_region: Optional[str] = Query(None),
    irrigated: bool = Query(False),
    rainfall_outlook: Optional[str] = Query(None),
    soil_ph: Optional[float] = Query(None, gt=0, le=14),
    soil_texture: Optional[str] = Query(None),
    tillage_practice: Optional[str] = Query(None),
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    """The whole pre-plant brief in one call: rotation, establishment, fertiliser.

    One round trip because these three answers are read together and must agree
    with each other — the same reasoning behind the field-state aggregator.
    """
    field = _resolve(field_id, user)
    ctx = _field_context(field)

    rotation = seasons.rotation_context(
        field_id, user.user_id, crop, tillage_practice, user.tenant_ids
    )

    plan = build_establishment_plan(
        crop,
        natural_region=natural_region or ctx["natural_region"],
        irrigated=irrigated,
        seasonal_rainfall_outlook=rainfall_outlook,
        area_hectares=ctx["area_hectares"],
    )

    programme = None
    try:
        from crop_profiles import get_crop_profile_or_generic
        programme = build_fertiliser_programme(
            get_crop_profile_or_generic(crop),
            planting_date=_as_date(planting_date),
            area_hectares=ctx["area_hectares"],
            soil_ph=soil_ph,
            soil_texture=soil_texture,
            irrigated=irrigated,
        ).to_dict()
    except Exception as e:
        # Degrade rather than 500 — the rest of the brief is still useful.
        print(f"[season_lifecycle_routes] fertiliser programme failed: {e}")

    return {
        "field_id": field_id,
        "crop": crop,
        "area_hectares": ctx["area_hectares"],
        "planting_date": planting_date,
        "rotation": rotation,
        "establishment": plan.to_dict() if plan else None,
        "fertiliser": programme,
        "unsupported_crop": plan is None,
    }


# ---------------------------------------------------------------------------
# The Stand Check
# ---------------------------------------------------------------------------
@router.get("/seasons/{season_id}/stand-check")
def get_stand_check_instructions(
    season_id: str,
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    """How to run the Stand Check on this season's actual row spacing.

    Count the plants along the returned row length, multiply by 1000, and that
    is plants/ha — the method farmers already know, sized to their field.
    """
    season = _resolve_season(season_id, user)
    row_spacing = season.get("row_spacing_cm")
    if not row_spacing:
        raise HTTPException(
            status_code=400,
            detail=(
                "This season has no row spacing recorded, so the sample length "
                "cannot be worked out. Set row_spacing_cm on the season first."
            ),
        )
    length = stand_check_row_length_m(float(row_spacing))
    target = season.get("target_population_per_ha")
    return {
        "season_id": season_id,
        "row_spacing_cm": float(row_spacing),
        "row_length_m": length,
        "target_population_per_ha": target,
        "expected_count": round(target / 1000) if target else None,
        "instructions": (
            f"Measure {length:.1f} m along one row and count every plant in it. "
            f"Repeat in three or four spots across the field and average them — "
            f"one sample from a good patch tells you nothing about the field."
        ),
    }


@router.post("/seasons/{season_id}/stand-check")
def submit_stand_check(
    season_id: str,
    body: Dict[str, Any] = Body(...),
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    """Record a stand count and get the verdict, revised ceiling and decision.

    Persists the established population — the denominator the KurimaScore needs
    to tell a thin stand apart from a stressed one.
    """
    season = _resolve_season(season_id, user)

    counted = body.get("counted_plants")
    if counted is None:
        raise HTTPException(status_code=400, detail="counted_plants is required")

    row_spacing = body.get("row_spacing_cm") or season.get("row_spacing_cm")
    if not row_spacing:
        raise HTTPException(status_code=400, detail="row_spacing_cm is required")

    target = body.get("target_population_per_ha") or season.get("target_population_per_ha")
    if not target:
        raise HTTPException(
            status_code=400,
            detail="No target population is set for this season to compare against.",
        )

    row_length = body.get("row_length_m") or stand_check_row_length_m(float(row_spacing))

    try:
        assessment = assess_stand(
            int(counted),
            float(row_spacing),
            float(row_length),
            int(target),
            days_after_emergence=body.get("days_after_emergence"),
            emergence_uniformity=body.get("emergence_uniformity"),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    patch: Dict[str, Any] = {
        "established_population_per_ha": assessment.established_population_per_ha,
    }
    if body.get("emergence_uniformity"):
        patch["emergence_uniformity"] = body["emergence_uniformity"]
    if body.get("emergence_date"):
        patch["emergence_date"] = body["emergence_date"]

    updated = _guard(seasons.update, season_id, patch, user.user_id, user.tenant_ids)

    return {"assessment": assessment.to_dict(), "season": updated}
