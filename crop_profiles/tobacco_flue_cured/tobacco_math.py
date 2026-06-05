"""
KurimaSense — Flue-Cured Tobacco Math (Phase 2)
================================================
Pure-function implementation of the tobacco yield model and KurimaScore
translation layer specified in ``model_design.md``.

CONSTRAINTS (Phase 2):
    * No database calls, no HTTP, no file I/O except loading the two Phase 1
      JSON data files at module import time.
    * No imports from yield_model.py / ai_brain.py / proactive_intelligence.py
      or any other application module.
    * Every public function is type-hinted, documented with its formula, inputs
      and output range, and is deterministic for given inputs (no randomness,
      no wall-clock dependency beyond dates passed in).

All yields are CURED LEAF kg/ha. See model_design.md for the full specification;
section references (§n) below point into that document.
"""

from __future__ import annotations

import json
import os
from datetime import date
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class UnknownVarietyError(ValueError):
    """Raised when a variety code is not present in the variety database."""


class TobaccoDataError(RuntimeError):
    """Raised when the Phase 1 JSON data files cannot be loaded/parsed."""


# ---------------------------------------------------------------------------
# Load-time data (the ONLY I/O permitted in this module)
# ---------------------------------------------------------------------------

_HERE = os.path.dirname(os.path.abspath(__file__))
_VARIETY_DB_PATH = os.path.join(_HERE, "variety_database.json")
_NR_BASELINES_PATH = os.path.join(_HERE, "natural_region_baselines.json")


def _load_json(path: str) -> dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:  # pragma: no cover - defensive
        raise TobaccoDataError(f"Could not load tobacco data file {path}: {exc}") from exc


VARIETY_DATABASE: dict[str, Any] = _load_json(_VARIETY_DB_PATH)
NATURAL_REGION_BASELINES: dict[str, Any] = _load_json(_NR_BASELINES_PATH)


def _build_variety_index() -> dict[str, dict[str, Any]]:
    """Index varieties by a normalised code for tolerant lookup."""
    index: dict[str, dict[str, Any]] = {}
    for variety in VARIETY_DATABASE.get("varieties", []):
        code = str(variety.get("code", "")).strip()
        if not code:
            continue
        index[_normalise_code(code)] = variety
        # Also index the full_name token if present (e.g. "K326").
        full = str(variety.get("full_name", "")).strip()
        if full:
            index.setdefault(_normalise_code(full), variety)
    return index


def _normalise_code(code: str) -> str:
    """Normalise a variety code: uppercase, strip spaces/hyphens/parentheses head."""
    token = str(code).upper().strip()
    # Take the part before any parenthesis / comma (full_name may be descriptive).
    for sep in ("(", ",", " - "):
        if sep in token:
            token = token.split(sep)[0].strip()
    return token.replace(" ", "").replace("-", "")


_VARIETY_INDEX: dict[str, dict[str, Any]] = _build_variety_index()


def get_variety(variety_code: str) -> dict[str, Any]:
    """
    Return the variety record for ``variety_code`` (tolerant of spacing/case/hyphens).

    Raises UnknownVarietyError if not found.
    """
    if variety_code is None:
        raise UnknownVarietyError("Variety code is None")
    rec = _VARIETY_INDEX.get(_normalise_code(variety_code))
    if rec is None:
        raise UnknownVarietyError(
            f"Variety '{variety_code}' not found in variety_database.json"
        )
    return rec


# ---------------------------------------------------------------------------
# Module constants (mirror model_design.md tables)
# ---------------------------------------------------------------------------

STAGES: tuple[str, ...] = (
    "ESTABLISHMENT",
    "VEGETATIVE",
    "REPRODUCTIVE",
    "TOPPING_RIPENING",
    "REAPING",
)

# §2.1 — per-stage KurimaScore weights (each row sums to 1.0).
STAGE_WEIGHTS: dict[str, dict[str, float]] = {
    "ESTABLISHMENT":    {"W_SAT": 0.25, "W_MGT": 0.30, "W_ENV": 0.45},
    "VEGETATIVE":       {"W_SAT": 0.45, "W_MGT": 0.30, "W_ENV": 0.25},
    "REPRODUCTIVE":     {"W_SAT": 0.40, "W_MGT": 0.45, "W_ENV": 0.15},
    "TOPPING_RIPENING": {"W_SAT": 0.45, "W_MGT": 0.40, "W_ENV": 0.15},
    "REAPING":          {"W_SAT": 0.55, "W_MGT": 0.30, "W_ENV": 0.15},
}
_DEFAULT_STAGE_WEIGHT = {"W_SAT": 0.40, "W_MGT": 0.35, "W_ENV": 0.25}

# §3.1 — per-stage index weights (each row sums to 1.0).
INDEX_NAMES: tuple[str, ...] = ("NDVI", "EVI", "NDRE", "NDMI", "SAVI", "SAR")
INDEX_WEIGHTS: dict[str, dict[str, float]] = {
    "ESTABLISHMENT":    {"NDVI": 0.25, "EVI": 0.00, "NDRE": 0.00, "NDMI": 0.20, "SAVI": 0.45, "SAR": 0.10},
    "VEGETATIVE":       {"NDVI": 0.30, "EVI": 0.25, "NDRE": 0.30, "NDMI": 0.10, "SAVI": 0.05, "SAR": 0.00},
    "REPRODUCTIVE":     {"NDVI": 0.15, "EVI": 0.35, "NDRE": 0.35, "NDMI": 0.15, "SAVI": 0.00, "SAR": 0.00},
    "TOPPING_RIPENING": {"NDVI": 0.15, "EVI": 0.20, "NDRE": 0.30, "NDMI": 0.35, "SAVI": 0.00, "SAR": 0.00},
    "REAPING":          {"NDVI": 0.30, "EVI": 0.20, "NDRE": 0.00, "NDMI": 0.15, "SAVI": 0.00, "SAR": 0.35},
}

# §3.1 — (floor, target) baselines per stage per index for index_score scaling.
INDEX_BASELINES: dict[str, dict[str, tuple[float, float]]] = {
    "ESTABLISHMENT":    {"NDVI": (0.15, 0.45), "EVI": (0.10, 0.40), "NDRE": (0.10, 0.35), "NDMI": (-0.10, 0.30), "SAVI": (0.10, 0.50), "SAR": (0.15, 0.40)},
    "VEGETATIVE":       {"NDVI": (0.45, 0.80), "EVI": (0.25, 0.65), "NDRE": (0.20, 0.50), "NDMI": (0.00, 0.40), "SAVI": (0.25, 0.60), "SAR": (0.18, 0.42)},
    "REPRODUCTIVE":     {"NDVI": (0.55, 0.85), "EVI": (0.30, 0.70), "NDRE": (0.25, 0.55), "NDMI": (0.05, 0.40), "SAVI": (0.30, 0.65), "SAR": (0.18, 0.42)},
    "TOPPING_RIPENING": {"NDVI": (0.45, 0.80), "EVI": (0.25, 0.65), "NDRE": (0.20, 0.50), "NDMI": (0.05, 0.40), "SAVI": (0.25, 0.60), "SAR": (0.18, 0.42)},
    "REAPING":          {"NDVI": (0.30, 0.65), "EVI": (0.18, 0.55), "NDRE": (0.15, 0.45), "NDMI": (-0.05, 0.35), "SAVI": (0.20, 0.55), "SAR": (0.15, 0.40)},
}

# §3.3 — stage water requirements (mm), Σ ≈ 450 (Phase 1 §4c).
STAGE_WATER_REQ_MM: dict[str, float] = {
    "ESTABLISHMENT": 40.0,
    "VEGETATIVE": 160.0,
    "REPRODUCTIVE": 90.0,
    "TOPPING_RIPENING": 110.0,
    "REAPING": 50.0,
}

# §3.3 — agro-ecological rainfall reliability ceiling per Natural Region.
REGION_RELIABILITY: dict[str, float] = {"I": 1.00, "II": 0.97, "III": 0.88, "IV": 0.72, "V": 0.58}

# §1.2 — natural region suitability factor (ceiling / NR II ceiling).
NATURAL_REGION_FACTOR: dict[str, float] = {"I": 0.89, "II": 1.00, "III": 0.84, "IV": 0.67, "V": 0.58}

# §1.2 — region-neutral genetic reference optimal (cured kg/ha).
BASE_POTENTIAL_REFERENCE_KG_HA: float = 3500.0

# §3.2 — management sub-score combination weights (Σ = 1.0).
MGMT_WEIGHTS: dict[str, float] = {"pop": 0.20, "fert": 0.35, "topping": 0.20, "spray": 0.10, "sucker": 0.15}

# §1.3 / §6 — confidence band → interval half-width fraction.
CONFIDENCE_WIDTH: dict[str, float] = {"high": 0.12, "medium": 0.20, "low": 0.30}

# §4 — KurimaScore label/colour bands (low, high inclusive, label, colour).
SCORE_BANDS: tuple[tuple[int, int, str, str], ...] = (
    (85, 100, "Thriving", "#2E7D32"),
    (70, 84, "Strong", "#66BB6A"),
    (55, 69, "Adequate", "#FBC02D"),
    (40, 54, "Stressed", "#F57C00"),
    (25, 39, "Distressed", "#D84315"),
    (0, 24, "Critical", "#B71C1C"),
)

# Recognised tobacco basal compounds and their accepted rate bands (kg/ha) §3.2.
_BASAL_RATE_BANDS: dict[str, tuple[float, float]] = {
    "compound c": (600.0, 900.0),
    "compound s": (350.0, 550.0),
}


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def _clip(value: float, low: float, high: float) -> float:
    """Clamp ``value`` into [low, high]."""
    return low if value < low else high if value > high else value


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _variance(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = _mean(values)
    return sum((v - m) ** 2 for v in values) / len(values)


def _normalise_region(natural_region: str) -> str:
    """Normalise a region label ('IIa'/'IIb' → 'II'); default 'II' if unknown."""
    if not natural_region:
        return "II"
    token = str(natural_region).upper().strip()
    if token.startswith("II"):
        return "II"
    for cand in ("I", "III", "IV", "V"):
        pass
    # Direct membership check against canonical set.
    if token in ("I", "II", "III", "IV", "V"):
        return token
    # Handle 'IIA'/'IIB' already covered; fall back to leading roman parse.
    for cand in ("V", "IV", "III", "II", "I"):
        if token == cand:
            return cand
    return "II"


# ---------------------------------------------------------------------------
# §8 — Phenological stage detection
# ---------------------------------------------------------------------------


def detect_stage(variety_code: str, transplant_date: date, current_date: date) -> str:
    """
    Determine the phenological stage from transplant/current dates and variety.

    Formula (§8): d = (current - transplant).days, M = variety days_to_maturity_max
        d < 0            -> "PRE_TRANSPLANT"
        d < 21           -> "ESTABLISHMENT"
        d < 56           -> "VEGETATIVE"
        d < 70           -> "REPRODUCTIVE"
        d < max(80,M-30) -> "TOPPING_RIPENING"
        d < M            -> "REAPING"
        else             -> "POST_HARVEST"

    Inputs:
        variety_code: code present in variety_database.json (else UnknownVarietyError).
        transplant_date, current_date: datetime.date.
    Returns:
        Stage string (one of STAGES, or "PRE_TRANSPLANT"/"POST_HARVEST").
    """
    variety = get_variety(variety_code)  # raises UnknownVarietyError
    maturity = int(variety.get("days_to_maturity_max") or 120)
    d = (current_date - transplant_date).days
    if d < 0:
        return "PRE_TRANSPLANT"
    if d < 21:
        return "ESTABLISHMENT"
    if d < 56:
        return "VEGETATIVE"
    if d < 70:
        return "REPRODUCTIVE"
    t_reap = max(80, maturity - 30)
    if d < t_reap:
        return "TOPPING_RIPENING"
    if d < maturity:
        return "REAPING"
    return "POST_HARVEST"


def _scoring_stage(stage: str) -> str:
    """Map edge sentinels onto the nearest scoring stage for component math."""
    if stage in STAGE_WEIGHTS:
        return stage
    if stage == "PRE_TRANSPLANT":
        return "ESTABLISHMENT"
    if stage == "POST_HARVEST":
        return "REAPING"
    return "VEGETATIVE"


def _elapsed_stages(stage: str) -> list[str]:
    """Stages up to and including the current scoring stage (for env averaging)."""
    cur = _scoring_stage(stage)
    out: list[str] = []
    for s in STAGES:
        out.append(s)
        if s == cur:
            break
    return out


# ---------------------------------------------------------------------------
# §3.1 — Satellite component
# ---------------------------------------------------------------------------


def _index_score(index: str, value: float, stage: str) -> float:
    """Scale a raw index value to [0,1] vs the stage (floor,target) baseline."""
    floor, target = INDEX_BASELINES[stage][index]
    if target <= floor:  # pragma: no cover - guarded by data
        return 0.0
    return _clip((value - floor) / (target - floor), 0.0, 1.0)


def _recent_index_values(indices_history: list[dict], index: str, window: int = 3) -> list[float]:
    """Most recent up-to-``window`` valid (non-None, numeric) values for an index."""
    vals: list[float] = []
    for obs in reversed(indices_history or []):
        if not isinstance(obs, dict):
            continue
        v = obs.get(index)
        if v is None:
            continue
        try:
            vals.append(float(v))
        except (TypeError, ValueError):
            continue
        if len(vals) >= window:
            break
    return list(reversed(vals))


def compute_satellite_component(
    indices_history: list[dict],
    stage: str,
    variety_code: str,
    natural_region: str,
) -> float:
    """
    Satellite health component in [0.0, 1.0] (§3.1).

    Formula:
        satellite = Σ_i w[stage][i] * index_score(i)   (weights renormalised over
        indices actually present; empty history -> neutral 0.5).

    Inputs:
        indices_history: list of {"NDVI":.., "EVI":.., ...} observations, oldest→newest.
        stage: phenological stage (STAGES or edge sentinel).
        variety_code / natural_region: accepted for signature parity / future
            variety- or region-relative baselines (validated, not yet differentiated).
    Returns:
        float in [0.0, 1.0].
    """
    get_variety(variety_code)  # validate (raises UnknownVarietyError)
    sstage = _scoring_stage(stage)
    weights = INDEX_WEIGHTS[sstage]

    present: dict[str, float] = {}
    for index in INDEX_NAMES:
        if weights.get(index, 0.0) <= 0.0:
            continue
        vals = _recent_index_values(indices_history, index)
        if vals:
            present[index] = _index_score(index, _mean(vals), sstage)

    if not present:
        return 0.5  # cannot assess; confidence layer penalises (§6)

    total_w = sum(weights[i] for i in present)
    if total_w <= 0.0:  # pragma: no cover - defensive
        return 0.5
    score = sum(weights[i] * present[i] for i in present) / total_w
    return _clip(score, 0.0, 1.0)


# ---------------------------------------------------------------------------
# §3.2 — Management component
# ---------------------------------------------------------------------------


def _population_score(plant_population_per_ha: Optional[int], variety: dict[str, Any]) -> float:
    """Triangular score vs variety recommended population range."""
    if plant_population_per_ha is None:
        return 0.70  # neutral when unknown
    pop = float(plant_population_per_ha)
    if pop <= 0:
        return 0.0
    pmin = float(variety.get("plant_population_min") or 14000)
    pmax = float(variety.get("plant_population_max") or 18000)
    if pmin <= pop <= pmax:
        return 1.0
    if pop < pmin:
        return _clip(pop / pmin, 0.0, 1.0)
    # Over-dense: linear penalty to 0.70 at 2x pmax, floor 0.5.
    over = (pop - pmax) / max(pmax, 1.0)
    return _clip(1.0 - 0.30 * over, 0.5, 1.0)


def _basal_score(product: Optional[str], rate_kg_ha: Optional[float]) -> float:
    """Score the basal fertiliser application (product recognised + rate in band)."""
    if not product and rate_kg_ha is None:
        return 0.35  # nothing recorded
    prod = (product or "").strip().lower()
    band = None
    for key, rng in _BASAL_RATE_BANDS.items():
        if key in prod:
            band = rng
            break
    if rate_kg_ha is None:
        return 0.6 if band else 0.45  # recognised product but no rate
    rate = float(rate_kg_ha)
    if band is None:
        # Unrecognised product but some rate applied — partial credit scaled to a
        # generic tobacco basal target of ~700 kg/ha.
        return _clip(0.45 + 0.35 * min(rate, 700.0) / 700.0, 0.0, 0.85)
    low, high = band
    if low <= rate <= high:
        return 1.0
    if rate < low:
        return _clip(0.4 + 0.6 * rate / low, 0.0, 1.0)
    # Above band — mild over-application penalty.
    return _clip(1.0 - 0.20 * (rate - high) / high, 0.6, 1.0)


def _topping_score(topping_days_after_transplant: Optional[int]) -> float:
    """Score topping timing vs optimal 55–75 d window (§4e; each late day ~50 kg/ha)."""
    if topping_days_after_transplant is None:
        return 0.70  # neutral when unknown / not yet topped
    t = float(topping_days_after_transplant)
    if t < 0:
        return 0.70
    if 55 <= t <= 75:
        return 1.0
    if t < 55:
        # Slightly early topping: mild penalty, never below 0.8.
        return _clip(1.0 - 0.01 * (55 - t), 0.8, 1.0)
    # Late topping: 0.03/day beyond 75.
    return _clip(1.0 - 0.03 * (t - 75), 0.0, 1.0)


def _spray_score(spray_applications_count: Optional[int]) -> float:
    """Score spray program adherence vs a ~6-application typical season (§4d)."""
    if spray_applications_count is None:
        return 0.60
    return _clip(float(spray_applications_count) / 6.0, 0.0, 1.0)


def _sucker_score(sucker_control_applied: Optional[bool]) -> float:
    """Binary-ish sucker control score (§6 sucker breakthrough)."""
    if sucker_control_applied is None:
        return 0.70
    return 1.0 if sucker_control_applied else 0.40


def compute_management_component(
    plant_population_per_ha: Optional[int],
    basal_fertilizer_rate_kg_ha: Optional[float],
    basal_fertilizer_product: Optional[str],
    topdressing_schedule_completion: Optional[float],
    topping_days_after_transplant: Optional[int],
    spray_applications_count: Optional[int],
    sucker_control_applied: Optional[bool],
    variety_code: str,
    stage: str,
) -> float:
    """
    Management quality component in [0.0, 1.0] (§3.2).

    Sub-scores (each [0,1]): population, fertiliser (0.5 basal + 0.5 topdressing),
    topping timing, spray adherence, sucker control. Combined as:
        component = clip(0.85 * weighted_avg + 0.15 * min(subscores), 0, 1)
    which is monotone non-decreasing in every sub-score.

    Inputs: see model_design.md §3.2; None values fall back to documented neutral
    defaults. variety_code validates and supplies the population range.
    Returns: float in [0.0, 1.0].
    """
    variety = get_variety(variety_code)  # raises UnknownVarietyError

    pop = _population_score(plant_population_per_ha, variety)
    topdress = _clip(float(topdressing_schedule_completion), 0.0, 1.0) if topdressing_schedule_completion is not None else 0.5
    fert = 0.5 * _basal_score(basal_fertilizer_product, basal_fertilizer_rate_kg_ha) + 0.5 * topdress
    topping = _topping_score(topping_days_after_transplant)
    spray = _spray_score(spray_applications_count)
    sucker = _sucker_score(sucker_control_applied)

    subscores = {"pop": pop, "fert": fert, "topping": topping, "spray": spray, "sucker": sucker}
    wavg = sum(MGMT_WEIGHTS[k] * subscores[k] for k in MGMT_WEIGHTS)
    component = 0.85 * wavg + 0.15 * min(subscores.values())
    return _clip(component, 0.0, 1.0)


def _management_subscores(
    plant_population_per_ha: Optional[int],
    basal_fertilizer_rate_kg_ha: Optional[float],
    basal_fertilizer_product: Optional[str],
    topdressing_schedule_completion: Optional[float],
    topping_days_after_transplant: Optional[int],
    spray_applications_count: Optional[int],
    sucker_control_applied: Optional[bool],
    variety: dict[str, Any],
) -> dict[str, float]:
    """Expose individual management sub-scores for the driver logic (§5)."""
    topdress = _clip(float(topdressing_schedule_completion), 0.0, 1.0) if topdressing_schedule_completion is not None else 0.5
    basal = _basal_score(basal_fertilizer_product, basal_fertilizer_rate_kg_ha)
    return {
        "pop_score": _population_score(plant_population_per_ha, variety),
        "fert_score": 0.5 * basal + 0.5 * topdress,
        "input_quality_score": 0.5 * basal + 0.5 * topdress,
        "topping_score": _topping_score(topping_days_after_transplant),
        "spray_score": _spray_score(spray_applications_count),
        "sucker_score": _sucker_score(sucker_control_applied),
    }


# ---------------------------------------------------------------------------
# §3.3 — Environmental component
# ---------------------------------------------------------------------------


def _rain_score(rainfall_mm: float, requirement_mm: float) -> float:
    """Stage rainfall adequacy → [0,1] (0.9 adequacy ≈ 1.0; monotone increasing)."""
    if requirement_mm <= 0:
        return 1.0
    adequacy = rainfall_mm / requirement_mm
    return _clip(0.30 + 0.70 * min(adequacy, 1.1) / 0.9, 0.0, 1.0)


def compute_environmental_component(
    rainfall_mm_per_stage: dict[str, float],
    drought_days_per_stage: dict[str, int],
    heat_stress_events: int,
    natural_region: str,
    stage: str,
) -> float:
    """
    Environmental context component in [0.0, 1.0] (§3.3).

    Formula:
        base = mean(rain_score over elapsed stages) - drought_pen - heat_pen
        environmental = clip(base, 0, 1) * region_reliability[region]
    where drought_pen = clip(0.01*Σdrought_days, 0, 0.40),
          heat_pen    = clip(0.05*heat_events, 0, 0.30).

    Region reliability caps the ceiling so a marginal region limits the score even
    under good local weather (§3.3, §5).
    Returns: float in [0.0, 1.0].
    """
    region = _normalise_region(natural_region)
    elapsed = _elapsed_stages(stage)

    rain_scores: list[float] = []
    for s in elapsed:
        rain = float((rainfall_mm_per_stage or {}).get(s, 0.0))
        rain_scores.append(_rain_score(rain, STAGE_WATER_REQ_MM[s]))
    base = _mean(rain_scores) if rain_scores else 0.5

    total_drought = sum(int(v) for v in (drought_days_per_stage or {}).values())
    drought_pen = _clip(0.01 * total_drought, 0.0, 0.40)
    heat_pen = _clip(0.05 * max(0, int(heat_stress_events or 0)), 0.0, 0.30)

    base = _clip(base - drought_pen - heat_pen, 0.0, 1.0)
    reliability = REGION_RELIABILITY.get(region, 0.97)
    return _clip(base * reliability, 0.0, 1.0)


# ---------------------------------------------------------------------------
# §4 — KurimaScore label + assembly
# ---------------------------------------------------------------------------


def _label_for_score(score: int) -> tuple[str, str]:
    for low, high, label, color in SCORE_BANDS:
        if low <= score <= high:
            return label, color
    return "Critical", "#B71C1C"  # pragma: no cover - score always clamped 0..100


def _yield_implication(label: str) -> str:
    return {
        "Thriving": "Projected yield tracking at or above regional best-practice.",
        "Strong": "Projected yield tracking near regional best-practice.",
        "Adequate": "Projected yield around regional average; upside available with tighter management.",
        "Stressed": "Projected yield tracking ~15–30% below regional best-practice unless corrected.",
        "Distressed": "Projected yield tracking ~30–50% below potential; intervention needed.",
        "Critical": "Projected yield severely compromised; crop-loss risk.",
    }.get(label, "Yield implication unavailable.")


def compute_kurima_score(
    satellite_component: float,
    management_component: float,
    environmental_component: float,
    stage: str,
    confidence_band: str = "medium",
    indices_trend: Optional[dict] = None,
    as_of_date: Optional[str] = None,
    driver_breakdown: Optional[dict] = None,
) -> dict:
    """
    Assemble the 0–100 KurimaScore and its interpretation (§2, §4, §5).

    Formula:
        score = round(100 * (W_SAT*sat + W_MGT*mgt + W_ENV*env))   (stage weights §2.1)

    Inputs:
        satellite_component, management_component, environmental_component: each [0,1].
        stage: phenological stage (selects the weight row).
        confidence_band: "high"|"medium"|"low" (echoed; default "medium").
        indices_trend / driver_breakdown: optional signals for driver logic (§5).
        as_of_date: optional ISO date echoed into the output.
    Returns:
        dict per model_design.md §4 (score, label, color, component_breakdown,
        primary_driver, likely_cause, recommended_action, yield_implication,
        confidence_band, stage, as_of_date).
    """
    sat = _clip(float(satellite_component), 0.0, 1.0)
    mgt = _clip(float(management_component), 0.0, 1.0)
    env = _clip(float(environmental_component), 0.0, 1.0)

    weights = STAGE_WEIGHTS.get(_scoring_stage(stage), _DEFAULT_STAGE_WEIGHT)
    raw = weights["W_SAT"] * sat + weights["W_MGT"] * mgt + weights["W_ENV"] * env
    score = int(round(_clip(raw, 0.0, 1.0) * 100))
    label, color = _label_for_score(score)

    breakdown = {"satellite": round(sat, 4), "management": round(mgt, 4), "environmental": round(env, 4)}
    driver_input = dict(breakdown)
    if driver_breakdown:
        driver_input.update(driver_breakdown)
    primary_driver, likely_cause, recommended_action = interpret_primary_driver(
        driver_input, indices_trend or {}, _scoring_stage(stage)
    )

    return {
        "score": score,
        "label": label,
        "color": color,
        "component_breakdown": breakdown,
        "primary_driver": primary_driver,
        "likely_cause": likely_cause,
        "recommended_action": recommended_action,
        "yield_implication": _yield_implication(label),
        "confidence_band": confidence_band if confidence_band in CONFIDENCE_WIDTH else "medium",
        "stage": stage,
        "as_of_date": as_of_date,
    }


# ---------------------------------------------------------------------------
# §5 — Primary driver / likely cause / recommended action
# ---------------------------------------------------------------------------


def interpret_primary_driver(
    component_breakdown: dict,
    indices_trend: dict,
    stage: str,
) -> tuple[str, str, str]:
    """
    Map component values + index trends + stage to a human-readable
    (primary_driver, likely_cause, recommended_action) triple (§5).

    Rules are evaluated in priority order; first match wins (acute/diagnostic
    before generic). ``component_breakdown`` must contain satellite/management/
    environmental and may carry optional sub-signals (fert_score, topping_score,
    sucker_score, pop_score, disease_type, waterlogging). ``indices_trend`` may
    carry ndvi_trend, ndre_trend, ndmi_trend and flags ndvi_abrupt_drop,
    spatial_patchiness.
    """
    sat = float(component_breakdown.get("satellite", 0.5))
    mgt = float(component_breakdown.get("management", 0.5))
    env = float(component_breakdown.get("environmental", 0.5))
    fert = float(component_breakdown.get("fert_score", 1.0))
    topping = float(component_breakdown.get("topping_score", 1.0))
    sucker = float(component_breakdown.get("sucker_score", 1.0))
    pop = float(component_breakdown.get("pop_score", 1.0))
    disease_type = str(component_breakdown.get("disease_type", "") or "")
    waterlogging = bool(component_breakdown.get("waterlogging", False))

    ndvi_trend = float(indices_trend.get("ndvi_trend", 0.0))
    ndre_trend = float(indices_trend.get("ndre_trend", 0.0))
    ndmi_trend = float(indices_trend.get("ndmi_trend", 0.0))
    ndvi_abrupt_drop = float(indices_trend.get("ndvi_abrupt_drop", 0.0))
    patchiness = str(indices_trend.get("spatial_patchiness", "") or "")

    veg_repro = {"VEGETATIVE", "REPRODUCTIVE"}
    ripen_reap = {"TOPPING_RIPENING", "REAPING"}

    # 1. Hail / storm — abrupt single-date canopy crash.
    if ndvi_abrupt_drop >= 0.20:
        return (
            "Acute canopy loss (hail/storm)",
            "Abrupt single-date NDVI/EVI collapse consistent with hail or storm damage (research.md §6 #11).",
            "Inspect field; salvage-reap usable leaf, manage rot, and lodge an insurance/loss claim.",
        )

    # 2. Bacterial / Granville wilt — patchy expanding collapse with healthy weather.
    if patchiness == "high" and sat < 0.5 and env > 0.55 and stage in (veg_repro | {"TOPPING_RIPENING"}):
        return (
            "Soil-borne wilt (patchy collapse)",
            "Clumped, expanding NDVI collapse under non-stress weather suggests bacterial/Granville wilt (Ralstonia) (research.md §6 #7).",
            "Confirm wilt, rogue affected plants, avoid waterlogging; plan a GW-resistant variety (e.g. K30R) next season — no in-season chemical cure.",
        )

    # 3. Waterlogging.
    if waterlogging or (ndmi_trend > 0.05 and sat < 0.5 and env < 0.6):
        return (
            "Waterlogging / poor drainage",
            "Rising leaf-moisture signal with declining canopy in low-lying zones indicates waterlogging and root stress (research.md §6 #6).",
            "Open drainage, re-ridge; avoid heavy clays in future; watch for black-shank follow-on.",
        )

    # 4. Water stress (drought).
    if ndmi_trend <= -0.03 and env < 0.55 and mgt >= 0.5:
        return (
            "Water stress (drought)",
            "Falling NDMI then NDVI with adequate management points to soil-moisture deficit (research.md §6 #5).",
            "Irrigate the rapid-growth window if possible; for marginal regions prefer drought-tolerant varieties (T75, KRK26R).",
        )

    # 5. Nitrogen deficiency.
    if stage in veg_repro and (ndre_trend < 0.0 or sat < 0.55) and fert < 0.5:
        return (
            "Nitrogen deficiency",
            "Weak/declining red-edge (NDRE) with below-target fertiliser records indicates nitrogen shortfall (research.md §6 #1).",
            "Bring forward/raise AN top-dressing within the ≤100 kg N/ha ceiling; check soil pH (acidity mimics N deficiency).",
        )

    # 6. Late topping / nitrogen excess — canopy refuses to ripen.
    if stage in ripen_reap | {"REPRODUCTIVE"} and ndvi_trend >= 0.0 and topping < 0.5:
        return (
            "Delayed ripening (late topping / excess N)",
            "Canopy greenness not declining into ripening with late/low topping score (research.md §6 #2, #14).",
            "Verify topping completion; stop nitrogen and manage water down to push ripening; assess yield-loss risk (~50 kg/ha per late day).",
        )

    # 7. Sucker breakthrough — re-greening after topping.
    if stage in ripen_reap and sucker < 0.5 and ndvi_trend > 0.02:
        return (
            "Sucker breakthrough",
            "Unexpected canopy re-greening after topping indicates failed sucker control (research.md §6 #15).",
            "Re-apply maleic hydrazide or hand-desucker within ~7 days of topping; record for grade-loss risk.",
        )

    # 8. Plant population below spec.
    if stage in {"ESTABLISHMENT", "VEGETATIVE"} and pop < 0.5:
        return (
            "Sub-optimal plant stand",
            "Actual plant population well below the variety's recommended range caps achievable yield (research.md §4a).",
            "Gap-fill where still viable; record reduced stand for yield expectation; review transplanting practice.",
        )

    # 9. Poor / late establishment.
    if stage == "ESTABLISHMENT" and sat < 0.45 and env > 0.5:
        return (
            "Poor establishment",
            "Low canopy signal early with adequate moisture suggests transplant shock, cutworm or damping-off (research.md §3.1, §6).",
            "Scout for cutworm/damping-off, replant gaps within ~7 days, ensure starter P is banded.",
        )

    # 10. Leaf-disease outbreak (angular leaf spot / blue mould).
    if stage in veg_repro and sat < 0.55 and env > 0.6 and ndvi_trend < 0.0:
        if disease_type == "blue_mould":
            return (
                "Blue mould (downy mildew) outbreak",
                "Rapid canopy decline in cool, humid conditions consistent with Peronospora (research.md §6 #10).",
                "Apply seedbed/early fungicide, improve ventilation and spacing; protect adjacent seedbeds.",
            )
        if disease_type == "angular_leaf_spot":
            return (
                "Angular leaf spot outbreak",
                "Canopy/grade decline under prolonged leaf wetness consistent with angular leaf spot (research.md §6 #9).",
                "Apply copper sprays, improve air-flow/spacing; favour resistant varieties (K35, K30R) next season.",
            )
        return (
            "Leaf-disease pressure (wet canopy)",
            "Declining canopy under wet, humid conditions suggests a foliar bacterial/fungal outbreak (research.md §6 #9–10).",
            "Scout to identify the pathogen; apply appropriate copper/fungicide and improve canopy air-flow.",
        )

    # 11. General disease / pest pressure.
    if sat < 0.55 and ndvi_trend < -0.01:
        return (
            "Canopy decline (disease/pest pressure)",
            "Gradual canopy decline not otherwise classified — likely aphid/budworm or leaf-spot pressure (research.md §6 #12–13).",
            "Scout for aphids/budworm and leaf-spot; spray selectively at economic threshold.",
        )

    # 12. Management execution gap.
    if mgt < 0.40 and env > 0.60:
        return (
            "Management execution gap",
            "Good environmental conditions but weak management inputs are limiting the crop (research.md §5).",
            "Review fertiliser, topping and spray records with the grower; close the most-lagging operation first.",
        )

    # 13. Environmental / regional limitation.
    if env < 0.40 and mgt > 0.60:
        return (
            "Environmental constraint",
            "Sound management but limiting weather/region context is capping performance (research.md §5, §6 #5).",
            "Largely weather-driven; consider supplementary irrigation and region-appropriate variety selection.",
        )

    # 14. On track (default).
    return (
        "On track",
        "Crop is tracking to regional expectations with no dominant limiting factor (research.md §5).",
        "Maintain the current program; continue routine scouting and scheduled inputs.",
    )


# ---------------------------------------------------------------------------
# §6 — Confidence scoring
# ---------------------------------------------------------------------------


def compute_confidence(
    indices_history: list[dict],
    progress: float,
    n_missing_core_inputs: int = 0,
    unstable_recent_stress: bool = False,
) -> tuple[float, str]:
    """
    Compute (confidence_score in [0.05,0.95], confidence_band) per §6.

    Reduces confidence for sparse observations, early season, inconsistent index
    signals (high recent NDVI variance), missing core inputs, and freshly-detected
    unstable stress. Returns the score and band ("high"|"medium"|"low").
    """
    obs = sum(
        1
        for o in (indices_history or [])
        if isinstance(o, dict) and any(o.get(i) is not None for i in INDEX_NAMES)
    )
    score = 0.50
    if obs >= 5:
        score += 0.20
    elif obs >= 3:
        score += 0.10
    elif obs >= 1:
        score -= 0.10
    else:
        score -= 0.25

    if progress >= 0.60:
        score += 0.15
    elif progress >= 0.35:
        score += 0.05
    else:
        score -= 0.05

    ndvi_recent = _recent_index_values(indices_history, "NDVI", window=5)
    if _variance(ndvi_recent) > 0.04:
        score -= 0.10

    score -= 0.03 * max(0, int(n_missing_core_inputs))
    if unstable_recent_stress:
        score -= 0.10

    score = _clip(score, 0.05, 0.95)
    band = "high" if score >= 0.70 else "medium" if score >= 0.45 else "low"
    return score, band


# ---------------------------------------------------------------------------
# §1 — Yield projection
# ---------------------------------------------------------------------------


def _indices_trend(indices_history: list[dict]) -> dict:
    """Derive simple recent trends + acute-drop flag from the index history."""
    trend: dict[str, float] = {}
    for index, key in (("NDVI", "ndvi_trend"), ("NDRE", "ndre_trend"), ("NDMI", "ndmi_trend")):
        vals = _recent_index_values(indices_history, index, window=3)
        trend[key] = round(vals[-1] - vals[0], 4) if len(vals) >= 2 else 0.0
    # Acute drop: largest single-step NDVI fall across the last few observations.
    ndvi = _recent_index_values(indices_history, "NDVI", window=5)
    drop = 0.0
    for a, b in zip(ndvi, ndvi[1:]):
        drop = max(drop, a - b)
    trend["ndvi_abrupt_drop"] = round(drop, 4)
    return trend


def project_yield(
    variety_code: str,
    natural_region: str,
    transplant_date: date,
    current_date: date,
    plant_population_per_ha: int,
    indices_history: list[dict],
    management_inputs: dict,
    environmental_data: dict,
) -> dict:
    """
    Project season-end cured yield (kg/ha) with a confidence interval (§1).

    projected = base_potential(3500) * variety_calibration * natural_region_factor
              * management_quality_factor * satellite_health_factor * stress_event_factor
    then clamped to [200, Y_ceiling[region]].

    management_inputs keys (all optional): basal_fertilizer_rate_kg_ha,
        basal_fertilizer_product, topdressing_schedule_completion,
        topping_days_after_transplant, spray_applications_count,
        sucker_control_applied.
    environmental_data keys: rainfall_mm_per_stage:dict, drought_days_per_stage:dict,
        heat_stress_events:int, acute_events:list[{"type","penalty"}] (optional).

    Returns dict: projected_yield_kg_ha, confidence_interval{low,high},
        confidence_band, contributing_factors{...}, stage, kurima_score.
    """
    variety = get_variety(variety_code)  # raises UnknownVarietyError
    region = _normalise_region(natural_region)
    stage = detect_stage(variety_code, transplant_date, current_date)
    sstage = _scoring_stage(stage)

    # Components.
    satellite = compute_satellite_component(indices_history, stage, variety_code, region)
    mi = management_inputs or {}
    management = compute_management_component(
        plant_population_per_ha,
        mi.get("basal_fertilizer_rate_kg_ha"),
        mi.get("basal_fertilizer_product"),
        mi.get("topdressing_schedule_completion"),
        mi.get("topping_days_after_transplant"),
        mi.get("spray_applications_count"),
        mi.get("sucker_control_applied"),
        variety_code,
        stage,
    )
    ed = environmental_data or {}
    environmental = compute_environmental_component(
        ed.get("rainfall_mm_per_stage", {}),
        ed.get("drought_days_per_stage", {}),
        int(ed.get("heat_stress_events", 0) or 0),
        region,
        stage,
    )

    # Factors (§1.2).
    variety_calibration = _clip(
        float(variety.get("yield_potential_kg_ha_optimal") or 3000) / BASE_POTENTIAL_REFERENCE_KG_HA,
        0.85,
        1.15,
    )
    nr_factor = NATURAL_REGION_FACTOR.get(region, 1.0)
    mgmt_factor = 0.55 + 0.50 * management
    sat_factor = 0.60 + 0.50 * satellite

    acute_mult = 1.0
    for ev in ed.get("acute_events", []) or []:
        try:
            acute_mult *= (1.0 - _clip(float(ev.get("penalty", 0.0)), 0.0, 0.9))
        except (TypeError, ValueError):
            continue
    stress_factor = _clip((0.50 + 0.50 * environmental) * acute_mult, 0.30, 1.0)

    # Enforce mandated [0.0, 1.5] window on every factor before multiplying.
    factors = {
        "variety_calibration": _clip(variety_calibration, 0.0, 1.5),
        "natural_region_factor": _clip(nr_factor, 0.0, 1.5),
        "management_quality_factor": _clip(mgmt_factor, 0.0, 1.5),
        "satellite_health_factor": _clip(sat_factor, 0.0, 1.5),
        "stress_event_factor": _clip(stress_factor, 0.0, 1.5),
    }

    point = BASE_POTENTIAL_REFERENCE_KG_HA
    for f in factors.values():
        point *= f

    y_ceiling = float(
        NATURAL_REGION_BASELINES["natural_regions"][region]["yield_baselines_kg_ha"]["best_practice"]
    )
    point = _clip(point, 200.0, y_ceiling)

    # Confidence + interval (§1.3, §6).
    maturity = int(variety.get("days_to_maturity_max") or 120)
    days = max(0, (current_date - transplant_date).days)
    progress = _clip(days / maturity, 0.0, 1.2) if maturity else 0.0
    n_missing = sum(
        1
        for v in (
            mi.get("basal_fertilizer_product"),
            mi.get("topdressing_schedule_completion"),
            plant_population_per_ha,
        )
        if v in (None, 0)
    )
    _, band = compute_confidence(indices_history, progress, n_missing_core_inputs=n_missing)

    frac = CONFIDENCE_WIDTH[band]
    low = max(150.0, point * (1.0 - frac))
    high = min(y_ceiling, point * (1.0 + frac))
    # Guarantee strict ordering low < point < high.
    if not (low < point < high):
        low = max(150.0, min(low, point * 0.98))
        high = max(point * 1.02, high)

    kscore = compute_kurima_score(
        satellite, management, environmental, stage,
        confidence_band=band,
        indices_trend=_indices_trend(indices_history),
        as_of_date=current_date.isoformat(),
        driver_breakdown=_management_subscores(
            plant_population_per_ha,
            mi.get("basal_fertilizer_rate_kg_ha"),
            mi.get("basal_fertilizer_product"),
            mi.get("topdressing_schedule_completion"),
            mi.get("topping_days_after_transplant"),
            mi.get("spray_applications_count"),
            mi.get("sucker_control_applied"),
            variety,
        ),
    )

    return {
        "projected_yield_kg_ha": round(point, 1),
        "confidence_interval": {"low": round(low, 1), "high": round(high, 1)},
        "confidence_band": band,
        "contributing_factors": {
            "base_potential_kg_ha": BASE_POTENTIAL_REFERENCE_KG_HA,
            **{k: round(v, 4) for k, v in factors.items()},
            "satellite_component": round(satellite, 4),
            "management_component": round(management, 4),
            "environmental_component": round(environmental, 4),
        },
        "stage": stage,
        "kurima_score": kscore["score"],
    }


# ---------------------------------------------------------------------------
# §7 — Side-marketing detection
# ---------------------------------------------------------------------------


def detect_side_marketing_signal(
    delivered_yield_kg_ha: float,
    predicted_yield_kg_ha: float,
    std_dev: float,
    confidence_band: str,
) -> dict:
    """
    Flag side-marketing risk from a delivery-vs-prediction shortfall (§7).

        deviation = (predicted - delivered) / std_dev      (>0 => under-delivery)
        low confidence  -> MEDIUM if deviation>=1 else LOW  (never HIGH)
        deviation >= 2  -> HIGH
        deviation >= 1  -> MEDIUM
        else            -> LOW

    A HIGH flag requires confidence_band in {medium, high} so a low-confidence
    forecast can never accuse a grower. std_dev is floored at 150 to avoid
    divide-by-zero / hypersensitivity.

    Returns: {flag_severity, deviation_std_devs, message}.
    """
    safe_std = max(float(std_dev), 150.0)
    deviation = (float(predicted_yield_kg_ha) - float(delivered_yield_kg_ha)) / safe_std
    band = confidence_band if confidence_band in CONFIDENCE_WIDTH else "medium"

    if band == "low":
        severity = "MEDIUM" if deviation >= 1.0 else "LOW"
    elif deviation >= 2.0:
        severity = "HIGH"
    elif deviation >= 1.0:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    messages = {
        "HIGH": (
            "Delivered yield is more than 2 standard deviations below KurimaSense's "
            "predicted yield with no corroborating field-loss event. Recommend "
            "reconciliation / field audit before settlement."
        ),
        "MEDIUM": (
            "Delivered yield is 1–2 standard deviations below the predicted yield. "
            "Monitor and cross-check against the field's stress history before any action."
        ),
        "LOW": (
            "Delivered yield is within the expected variance of the prediction. No flag."
        ),
    }
    return {
        "flag_severity": severity,
        "deviation_std_devs": round(deviation, 2),
        "message": messages[severity],
    }


__all__ = [
    "UnknownVarietyError",
    "TobaccoDataError",
    "VARIETY_DATABASE",
    "NATURAL_REGION_BASELINES",
    "STAGE_WEIGHTS",
    "INDEX_WEIGHTS",
    "INDEX_BASELINES",
    "get_variety",
    "detect_stage",
    "compute_satellite_component",
    "compute_management_component",
    "compute_environmental_component",
    "compute_kurima_score",
    "compute_confidence",
    "interpret_primary_driver",
    "project_yield",
    "detect_side_marketing_signal",
]
