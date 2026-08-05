"""
Season orchestration — lifecycle transitions, rotation context, and the
``fields`` mirror.

Thin by design: the rules live in :mod:`.lifecycle` (pure, unit-tested) and the
SQL lives in :mod:`.repository`. This module wires them together and owns the
side effects a transition implies.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from . import repository as repo
from .lifecycle import (
    STATUS_ACTIVE,
    STATUS_CLOSED,
    STATUS_HARVESTED,
    STATUS_PLANNED,
    InvalidTransition,
    assert_transition,
    derive_season_label,
    summarise_rotation,
)


class SeasonNotFound(Exception):
    """No season with that id (→ 404)."""


class SeasonConflict(Exception):
    """The request conflicts with the field's current state (→ 409)."""


def _as_date(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def list_for_field(field_id: str, user_id: str, tenant_ids: Optional[List[str]] = None):
    return repo.list_seasons(field_id, user_id, tenant_ids)


def get(season_id: str, user_id: str, tenant_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    season = repo.get_season(season_id, user_id, tenant_ids)
    if not season:
        raise SeasonNotFound(season_id)
    return season


def plan_season(
    field_id: str,
    tenant_id: Optional[str],
    user_id: str,
    payload: Dict[str, Any],
    tenant_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Create a **planned** season — the pre-plant record.

    A field may hold any number of planned seasons (a farmer comparing options)
    but only one active one, so no conflict check is needed here.
    """
    body = dict(payload)
    if not body.get("season_label"):
        anchor = _as_date(body.get("planned_planting_date")) or _as_date(body.get("planting_date"))
        label = derive_season_label(anchor)
        if label:
            body["season_label"] = label

    created = repo.create_season(
        field_id, tenant_id, user_id, body, status=STATUS_PLANNED, tenant_ids=tenant_ids
    )
    if not created:
        raise SeasonConflict("Could not create the season")
    return created


def update(
    season_id: str,
    payload: Dict[str, Any],
    user_id: str,
    tenant_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    existing = repo.get_season(season_id, user_id, tenant_ids)
    if not existing:
        raise SeasonNotFound(season_id)
    if existing.get("status") == STATUS_CLOSED:
        raise SeasonConflict(
            "This season is closed. Closed seasons are historical records and "
            "cannot be edited — every rotation and calibration conclusion drawn "
            "from them depends on that."
        )

    updated = repo.update_season(season_id, payload, user_id, tenant_ids)
    if not updated:
        raise SeasonConflict("Could not update the season")

    # Keep the field mirror in step when the live season's crop details change.
    if updated.get("status") == STATUS_ACTIVE:
        repo.mirror_to_field(updated["field_id"], updated, user_id, tenant_ids)
    return updated


def activate(
    season_id: str,
    user_id: str,
    planting_date: Optional[str] = None,
    tenant_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """planned → active. The moment the crop actually goes in the ground.

    Side effects, in order: confirm the planting date, flip the status, mirror
    onto ``fields`` so every existing screen sees the new crop, and attribute
    observations from the planting date onward to this season.
    """
    season = repo.get_season(season_id, user_id, tenant_ids)
    if not season:
        raise SeasonNotFound(season_id)
    assert_transition(season.get("status", ""), STATUS_ACTIVE)

    field_id = season["field_id"]
    live = repo.get_active_season(field_id, user_id, tenant_ids)
    if live and live["id"] != season_id:
        raise SeasonConflict(
            "This field already has an active season. Harvest or abandon it "
            "before starting another."
        )

    effective = (
        planting_date
        or season.get("planting_date")
        or season.get("planned_planting_date")
        or date.today().isoformat()
    )

    patch: Dict[str, Any] = {"planting_date": effective}
    if not season.get("season_label"):
        label = derive_season_label(_as_date(effective))
        if label:
            patch["season_label"] = label

    updated = repo.update_season(season_id, patch, user_id, tenant_ids, status=STATUS_ACTIVE)
    if not updated:
        raise SeasonConflict("Could not activate the season")

    repo.mirror_to_field(field_id, updated, user_id, tenant_ids)
    repo.attribute_observations(field_id, season_id, effective, user_id, tenant_ids)
    return updated


def record_harvest(
    season_id: str,
    user_id: str,
    harvest_date: Optional[str] = None,
    yield_tonnes_per_ha: Optional[float] = None,
    tenant_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """active → harvested. The crop is off the field; drying/storage follow.

    Deliberately *not* the end of the season: 20-30% of a crop can still be
    lost in storage, so the season stays open through the post-harvest phase.
    """
    season = repo.get_season(season_id, user_id, tenant_ids)
    if not season:
        raise SeasonNotFound(season_id)
    assert_transition(season.get("status", ""), STATUS_HARVESTED)

    patch: Dict[str, Any] = {"harvest_date": harvest_date or date.today().isoformat()}
    if yield_tonnes_per_ha is not None:
        patch["yield_tonnes_per_ha"] = yield_tonnes_per_ha

    updated = repo.update_season(season_id, patch, user_id, tenant_ids, status=STATUS_HARVESTED)
    if not updated:
        raise SeasonConflict("Could not record the harvest")
    return updated


def close(
    season_id: str,
    user_id: str,
    yield_tonnes_per_ha: Optional[float] = None,
    tenant_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """harvested → closed. Terminal; the season becomes history."""
    season = repo.get_season(season_id, user_id, tenant_ids)
    if not season:
        raise SeasonNotFound(season_id)
    assert_transition(season.get("status", ""), STATUS_CLOSED)

    patch: Dict[str, Any] = {}
    if yield_tonnes_per_ha is not None:
        patch["yield_tonnes_per_ha"] = yield_tonnes_per_ha

    updated = repo.update_season(season_id, patch, user_id, tenant_ids, status=STATUS_CLOSED)
    if not updated:
        raise SeasonConflict("Could not close the season")
    return updated


def transition(
    season_id: str,
    target_status: str,
    user_id: str,
    tenant_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Generic transition for states with no side effects (e.g. abandonment)."""
    season = repo.get_season(season_id, user_id, tenant_ids)
    if not season:
        raise SeasonNotFound(season_id)
    assert_transition(season.get("status", ""), target_status)
    updated = repo.update_season(season_id, {}, user_id, tenant_ids, status=target_status)
    if not updated:
        raise SeasonConflict(f"Could not move the season to '{target_status}'")
    return updated


def field_history(
    field_id: str,
    user_id: str,
    tenant_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Season-over-season history for a field, aligned on days after planting.

    Calendar dates make seasons incomparable — a crop planted 15 November and
    one planted 2 December are at different growth stages on any given day.
    Re-indexing to crop age is what makes "this season is ahead of last" a
    statement about the crop rather than about the calendar.
    """
    from .history import build_field_history, group_observations_by_season

    seasons = repo.list_seasons(field_id, user_id, tenant_ids)
    observations = repo.load_observations(field_id, user_id, tenant_ids)
    grouped = group_observations_by_season(seasons, observations)
    return build_field_history(field_id, seasons, grouped).to_dict()


def rotation_context(
    field_id: str,
    user_id: str,
    candidate_crop: Optional[str] = None,
    tillage_practice: Optional[str] = None,
    tenant_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Rotation summary for a field, optionally for a candidate next crop.

    This is the input the crop advisor and residue-inoculum disease risk both
    need — the thing that was impossible before seasons existed.
    """
    seasons = repo.list_seasons(field_id, user_id, tenant_ids)
    if tillage_practice is None:
        for s in seasons:
            if s.get("tillage_practice"):
                tillage_practice = s["tillage_practice"]
                break
    return summarise_rotation(
        seasons, candidate_crop=candidate_crop, tillage_practice=tillage_practice
    ).to_dict()
