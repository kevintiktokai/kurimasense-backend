"""
Season lifecycle and rotation analysis — pure, no I/O.

Two jobs:

1. **Lifecycle rules.** Which status transitions are legal, and what each one
   implies for the field's mirrored columns.
2. **Rotation analysis.** Turn a field's season history into the structured
   facts the agronomy needs — consecutive runs of the same crop, years since a
   crop was last grown, and the residue-borne disease risk that follows.

Why rotation analysis lives here
--------------------------------
The crop profiles already model residue inoculum in detail — maize Grey Leaf
Spot is *"worse under continuous maize or minimum tillage (residue inoculum)"*,
with cultural controls *"rotate with soybean, groundnut, or sunflower
(non-host)"* and *"bury crop residue by ploughing (reduces inoculum 60-80%)"*.
None of it could ever be applied, because nothing recorded what grew in the
field last year. This module is the missing half.

Pure by design: no DB, no network, fully unit-testable.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from datetime import date
from typing import Any, Dict, List, Optional, Sequence

# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------
STATUS_PLANNED = "planned"
STATUS_ACTIVE = "active"
STATUS_HARVESTED = "harvested"
STATUS_CLOSED = "closed"
STATUS_ABANDONED = "abandoned"

ALL_STATUSES = (
    STATUS_PLANNED, STATUS_ACTIVE, STATUS_HARVESTED, STATUS_CLOSED, STATUS_ABANDONED,
)

# planned → active → harvested → closed, with abandonment available until the
# crop is off the field. Nothing leaves `closed`: a finished season is a
# historical record, and rewriting history would silently corrupt every
# rotation and calibration conclusion drawn from it.
_TRANSITIONS: Dict[str, tuple] = {
    STATUS_PLANNED: (STATUS_ACTIVE, STATUS_ABANDONED),
    STATUS_ACTIVE: (STATUS_HARVESTED, STATUS_ABANDONED),
    STATUS_HARVESTED: (STATUS_CLOSED,),
    STATUS_CLOSED: (),
    STATUS_ABANDONED: (),
}


class InvalidTransition(ValueError):
    """Raised when a caller asks for a status change the lifecycle forbids."""


def can_transition(current: str, target: str) -> bool:
    return target in _TRANSITIONS.get(current, ())


def assert_transition(current: str, target: str) -> None:
    if current not in _TRANSITIONS:
        raise InvalidTransition(f"Unknown season status '{current}'")
    if target not in ALL_STATUSES:
        raise InvalidTransition(f"Unknown target status '{target}'")
    if not can_transition(current, target):
        allowed = _TRANSITIONS[current]
        allowed_text = ", ".join(allowed) if allowed else "nothing (terminal state)"
        raise InvalidTransition(
            f"A '{current}' season cannot become '{target}'. Allowed: {allowed_text}."
        )


def is_live(status: str) -> bool:
    """True while the crop is still in the ground (mirrors onto the field)."""
    return status == STATUS_ACTIVE


def derive_season_label(planting: Optional[date], hemisphere: str = "southern") -> Optional[str]:
    """``date(2026, 11, 15)`` → ``"2026/27 Summer"``.

    Southern-African summer cropping straddles the new year, so a single
    calendar year is the wrong label — a crop planted in November 2026 is
    harvested in 2027 and farmers call it the 2026/27 season.
    """
    if not planting:
        return None
    if hemisphere != "southern":
        return str(planting.year)
    # Summer season runs roughly Sep-Aug; winter crops sit inside one year.
    if planting.month >= 9:
        return f"{planting.year}/{str(planting.year + 1)[-2:]} Summer"
    if planting.month <= 3:
        return f"{planting.year - 1}/{str(planting.year)[-2:]} Summer"
    return f"{planting.year} Winter"


# ---------------------------------------------------------------------------
# Rotation analysis
# ---------------------------------------------------------------------------

# Crop → botanical/rotational family. Diseases and nematodes carry over within
# a family, so rotation must be judged on family, not crop name: maize followed
# by sorghum is not a break for a grass pathogen.
_CROP_FAMILY = {
    "maize": "cereal_grass", "corn": "cereal_grass", "sorghum": "cereal_grass",
    "wheat": "cereal_grass", "pearl_millet": "cereal_grass",
    "finger_millet": "cereal_grass", "barley": "cereal_grass",
    "soybean": "legume", "soybeans": "legume", "groundnuts": "legume",
    "groundnut": "legume", "cowpeas": "legume", "sugar_beans": "legume",
    "peas": "legume", "snow_peas": "legume", "green_beans": "legume",
    "bambara_nuts": "legume",
    "tobacco": "solanaceae", "tomato": "solanaceae", "potato": "solanaceae",
    "green_pepper": "solanaceae", "paprika": "solanaceae",
    "cabbage": "brassica", "rape": "brassica", "covo": "brassica",
    "mustard": "brassica",
    "cotton": "malvaceae",
    "sunflower": "asteraceae",
    "sweet_potato": "convolvulaceae",
    "onion": "allium", "garlic": "allium",
}

# Families that fix nitrogen for whatever follows them.
_N_FIXING_FAMILIES = {"legume"}


def crop_family(crop: Optional[str]) -> Optional[str]:
    if not crop:
        return None
    key = str(crop).strip().lower().replace(" ", "_").replace("-", "_")
    return _CROP_FAMILY.get(key)


def _norm(crop: Optional[str]) -> Optional[str]:
    if not crop:
        return None
    return str(crop).strip().lower().replace(" ", "_").replace("-", "_")


@dataclass
class RotationSummary:
    """What a field's cropping history implies for the next crop."""
    seasons_recorded: int
    history: List[Dict[str, Any]] = dc_field(default_factory=list)
    current_crop: Optional[str] = None
    consecutive_same_crop: int = 0
    consecutive_same_family: int = 0
    years_since: Dict[str, int] = dc_field(default_factory=dict)
    rotation_risk: str = "unknown"     # 'unknown' | 'low' | 'moderate' | 'high'
    risk_reasons: List[str] = dc_field(default_factory=list)
    last_n_fixing_crop: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seasons_recorded": self.seasons_recorded,
            "history": self.history,
            "current_crop": self.current_crop,
            "consecutive_same_crop": self.consecutive_same_crop,
            "consecutive_same_family": self.consecutive_same_family,
            "years_since": self.years_since,
            "rotation_risk": self.rotation_risk,
            "risk_reasons": self.risk_reasons,
            "last_n_fixing_crop": self.last_n_fixing_crop,
        }


def _season_sort_key(s: Dict[str, Any]):
    """Newest first, by whichever date the season actually has."""
    return (
        s.get("planting_date")
        or s.get("planned_planting_date")
        or s.get("created_at")
        or ""
    )


def summarise_rotation(
    seasons: Sequence[Dict[str, Any]],
    *,
    candidate_crop: Optional[str] = None,
    tillage_practice: Optional[str] = None,
) -> RotationSummary:
    """Analyse a field's season history.

    ``seasons`` are dicts as stored (any order). Planned seasons are ignored —
    a crop that has not been planted has left no residue and carries no
    inoculum. ``candidate_crop`` asks "what if I plant this next?" and drives
    the risk assessment; without it the summary describes history only.
    """
    grown = [
        s for s in seasons
        if s.get("status") in (STATUS_ACTIVE, STATUS_HARVESTED, STATUS_CLOSED)
        and s.get("crop_type")
    ]
    grown.sort(key=_season_sort_key, reverse=True)

    history = [
        {
            "season_id": s.get("id"),
            "crop_type": s.get("crop_type"),
            "family": crop_family(s.get("crop_type")),
            "variety": s.get("variety"),
            "season_label": s.get("season_label"),
            "planting_date": s.get("planting_date"),
            "yield_tonnes_per_ha": s.get("yield_tonnes_per_ha"),
            "status": s.get("status"),
        }
        for s in grown
    ]

    summary = RotationSummary(seasons_recorded=len(grown), history=history)
    if not grown:
        summary.risk_reasons.append(
            "No cropping history recorded for this field yet, so rotation risk "
            "cannot be assessed. Adding past seasons unlocks it."
        )
        return summary

    summary.current_crop = grown[0].get("crop_type")

    # Years since each crop/family was last grown (0 = most recent season).
    for idx, s in enumerate(grown):
        key = _norm(s.get("crop_type"))
        if key and key not in summary.years_since:
            summary.years_since[key] = idx

    for s in grown:
        if crop_family(s.get("crop_type")) in _N_FIXING_FAMILIES:
            summary.last_n_fixing_crop = s.get("crop_type")
            break

    target = _norm(candidate_crop) or _norm(summary.current_crop)
    target_family = crop_family(target)

    # Count the unbroken run of the candidate crop (and its family) immediately
    # preceding the next planting.
    run_crop = 0
    for s in grown:
        if _norm(s.get("crop_type")) == target:
            run_crop += 1
        else:
            break
    run_family = 0
    if target_family:
        for s in grown:
            if crop_family(s.get("crop_type")) == target_family:
                run_family += 1
            else:
                break

    summary.consecutive_same_crop = run_crop
    summary.consecutive_same_family = run_family

    reasons: List[str] = []
    if run_crop >= 3:
        risk = "high"
        reasons.append(
            f"{candidate_crop or summary.current_crop} has been grown here "
            f"{run_crop} seasons running. Residue-borne pathogens build up with "
            f"each repeat — for maize that means Grey Leaf Spot and Diplodia ear "
            f"rot carrying over in the trash."
        )
    elif run_crop == 2:
        risk = "moderate"
        reasons.append(
            f"This would be a third consecutive {candidate_crop or summary.current_crop} "
            f"crop. Inoculum is building; a break crop next season would reset it."
        )
    elif run_family >= 3:
        risk = "moderate"
        reasons.append(
            f"Different crops, but {run_family} seasons in the same "
            f"{target_family.replace('_', ' ')} family — many pathogens do not "
            f"distinguish between them, so this is a weaker break than it looks."
        )
    else:
        risk = "low"
        if run_crop <= 1:
            reasons.append("The rotation gives a genuine break from last season's residue.")

    # Minimum tillage leaves residue on the surface, where inoculum survives.
    if tillage_practice and str(tillage_practice).lower().replace("-", "_") in (
        "minimum", "minimum_till", "min_till", "no_till", "no_tillage", "conservation"
    ):
        if risk == "high":
            reasons.append(
                "Minimum tillage leaves that residue on the surface rather than "
                "burying it, so the inoculum load is at its worst. Ploughing residue "
                "in cuts it by 60-80%."
            )
        elif risk == "moderate":
            risk = "high"
            reasons.append(
                "Minimum tillage keeps last season's residue — and its inoculum — "
                "on the surface, which raises the risk a step."
            )

    summary.rotation_risk = risk
    summary.risk_reasons = reasons
    return summary


def is_break_crop(candidate: Optional[str], previous: Optional[str]) -> bool:
    """True if ``candidate`` is a genuine rotational break from ``previous``.

    Family-level, not name-level: maize → sorghum is not a break.
    """
    cf, pf = crop_family(candidate), crop_family(previous)
    if _norm(candidate) == _norm(previous):
        return False
    if cf and pf:
        return cf != pf
    return True
