"""
Generic crop math — crop-agnostic KurimaScore
=============================================
A minimal, crop-agnostic mirror of the flue-cured tobacco math
(``crop_profiles/tobacco_flue_cured/tobacco_math.py``) so that *every* crop gets
a KurimaScore until it grows its own Phase 1+2 model (per prompt Step C.2).

It deliberately mirrors the tobacco output contract:
``compute_generic_kurima_score(...) -> dict`` with keys
``score, label, color, components{satellite,management,environmental},
primary_driver, likely_cause, recommended_action, yield_implication,
confidence_band, confidence_pct, stage`` — so the aggregator can treat tobacco
and non-tobacco fields through one normalised shape.

The satellite component is computed from how the *recent* NDVI sits inside the
stage-expected band (see ``classifiers.ndvi_health_fraction``). This is what makes
a low NDVI at a high-expectation stage drive the score down — the contradiction
resolution required by the prompt. Pure functions, no I/O.
"""

from __future__ import annotations

from typing import List, Dict, Optional, Tuple

from . import classifiers


# Per-phase component weights (each row sums to 1.0). Satellite-dominant once the
# canopy is established, so an NDVI/expected gap moves the score decisively.
PHASE_WEIGHTS: Dict[str, Dict[str, float]] = {
    "establishment": {"sat": 0.30, "mgt": 0.35, "env": 0.35},
    "vegetative":    {"sat": 0.50, "mgt": 0.30, "env": 0.20},
    "reproductive":  {"sat": 0.50, "mgt": 0.30, "env": 0.20},
    "maturation":    {"sat": 0.50, "mgt": 0.30, "env": 0.20},
    "senescence":    {"sat": 0.55, "mgt": 0.30, "env": 0.15},
}
_DEFAULT_WEIGHTS = {"sat": 0.45, "mgt": 0.30, "env": 0.25}


def detect_phase(days_since_planting: Optional[int], maturity_days: Optional[int]) -> str:
    """Map progress fraction to a coarse phase (crop-agnostic)."""
    if days_since_planting is None or not maturity_days or maturity_days <= 0:
        return "vegetative"
    frac = days_since_planting / float(maturity_days)
    if frac < 0.15:
        return "establishment"
    if frac < 0.45:
        return "vegetative"
    if frac < 0.70:
        return "reproductive"
    if frac < 0.92:
        return "maturation"
    return "senescence"


def _recent_values(indices_history: List[dict], key: str, window: int = 3) -> List[float]:
    vals: List[float] = []
    for obs in reversed(indices_history or []):
        if not isinstance(obs, dict):
            continue
        v = obs.get(key)
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
    indices_history: List[dict],
    crop_type: Optional[str],
    phase: str,
) -> Optional[float]:
    """
    Satellite health component in [0,1] from recent NDVI (and EVI when present),
    each scaled against the stage-expected band. ``None`` when no usable indices.
    """
    ndvi_vals = _recent_values(indices_history, "ndvi") or _recent_values(indices_history, "NDVI")
    if not ndvi_vals:
        return None
    ndvi_mean = sum(ndvi_vals) / len(ndvi_vals)
    frac = classifiers.ndvi_health_fraction(crop_type, phase, ndvi_mean)
    return frac


def _ndvi_trend(indices_history: List[dict]) -> float:
    vals = _recent_values(indices_history, "ndvi", window=3) or _recent_values(indices_history, "NDVI", window=3)
    if len(vals) >= 2:
        return round(vals[-1] - vals[0], 4)
    return 0.0


def _interpret(
    crop_type: Optional[str],
    phase: str,
    sat: float,
    mgt: float,
    env: float,
    ndvi_trend: float,
    ndvi: Optional[float],
    expected_low: float,
) -> Tuple[str, str, str]:
    """Crop-agnostic (primary_driver, likely_cause, recommended_action)."""
    crop = (crop_type or "crop").lower()
    # Acute canopy gap vs expectation dominates.
    if sat < 0.35 and ndvi is not None and ndvi < expected_low:
        return (
            "Canopy below stage expectation",
            f"NDVI {ndvi:.2f} is well below the {expected_low:.2f}+ expected for {crop} at {phase} stage, "
            "indicating significant crop stress (water, nutrient, disease or establishment).",
            "Scout the field within 48 hours to identify the stressor; check soil moisture and recent inputs first.",
        )
    if env < 0.45 and mgt >= 0.5:
        return (
            "Environmental stress",
            "Weather/water context is limiting the crop despite adequate management.",
            "Irrigate if possible and protect the crop through the stress window.",
        )
    if mgt < 0.45 and env >= 0.55:
        return (
            "Management execution gap",
            "Conditions are favourable but logged inputs are below expectation.",
            "Review fertiliser and spray records; close the most-lagging operation first.",
        )
    if ndvi_trend < -0.03:
        return (
            "Declining canopy",
            "NDVI is trending down over recent passes — early sign of emerging stress.",
            "Scout for pests, disease and moisture deficit before the decline accelerates.",
        )
    if sat >= 0.7 and mgt >= 0.6:
        return (
            "On track",
            f"{crop.capitalize()} is tracking to expectation with no dominant limiting factor.",
            "Maintain the current programme; continue routine scouting and scheduled inputs.",
        )
    return (
        "Adequate, room to improve",
        "No single limiting factor dominates, but the crop is below its best-practice ceiling.",
        "Tighten management — confirm nutrition and irrigation are on schedule for the stage.",
    )


def _yield_implication(label: str) -> str:
    return {
        "Thriving": "Projected yield tracking at or above regional best-practice.",
        "Strong": "Projected yield tracking near regional best-practice.",
        "Adequate": "Projected yield around regional average; upside available with tighter management.",
        "Stressed": "Projected yield tracking ~15-30% below best-practice unless corrected.",
        "Distressed": "Projected yield tracking ~30-50% below potential; intervention needed.",
        "Critical": "Projected yield severely compromised; crop-loss risk.",
    }.get(label, "Yield implication unavailable.")


def compute_generic_kurima_score(
    crop_type: Optional[str],
    phase: str,
    indices_history: List[dict],
    *,
    management_component: Optional[float] = None,
    environmental_component: Optional[float] = None,
    confidence_band: str = "medium",
    confidence_pct: int = 60,
    current_ndvi: Optional[float] = None,
) -> dict:
    """
    Assemble a 0-100 KurimaScore for a non-tobacco crop.

    ``management_component`` / ``environmental_component`` are [0,1] signals the
    aggregator supplies (from input records and water balance). When ``None`` they
    fall back to documented neutral defaults so a sparse field still scores.
    Returns the normalised score dict described in the module docstring.
    """
    weights = PHASE_WEIGHTS.get(phase, _DEFAULT_WEIGHTS)

    sat = compute_satellite_component(indices_history, crop_type, phase)
    sat_eff = 0.5 if sat is None else sat            # neutral when unknown
    mgt = 0.55 if management_component is None else max(0.0, min(1.0, management_component))
    env = 0.55 if environmental_component is None else max(0.0, min(1.0, environmental_component))

    raw = weights["sat"] * sat_eff + weights["mgt"] * mgt + weights["env"] * env
    score = int(round(max(0.0, min(1.0, raw)) * 100))
    label, color = classifiers.label_for_score(score)

    lo, _hi = classifiers.expected_ndvi_range(crop_type, phase)
    primary, cause, action = _interpret(
        crop_type, phase, sat_eff, mgt, env, _ndvi_trend(indices_history), current_ndvi, lo
    )

    return {
        "score": score,
        "label": label,
        "color": color,
        "components": {
            "satellite": None if sat is None else round(sat, 4),
            "management": round(mgt, 4),
            "environmental": round(env, 4),
        },
        "primary_driver": primary,
        "likely_cause": cause,
        "recommended_action": action,
        "yield_implication": _yield_implication(label),
        "confidence_band": confidence_band,
        "confidence_pct": confidence_pct,
        "stage": phase,
    }
