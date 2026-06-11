"""
Field State Aggregator — classifiers (interpretation logic)
===========================================================
This module is the *single* home for every threshold decision that used to live
in the frontend or be duplicated across screens (see field_state_audit.md F2):

    * what makes an NDVI "Critical" vs "Adequate" for a crop at a stage
    * what makes a water balance a deficit, and how urgent
    * what soil-moisture percentage counts as "dry" for a crop
    * how a 0-1 confidence score becomes a (band, integer pct) pair
    * how recent/cloudy a satellite pass must be to be "good"

Change a threshold here once and it propagates to every screen, because every
screen reads the aggregator. Pure functions, no I/O.
"""

from __future__ import annotations

from typing import List, Optional, Tuple, Dict


# ---------------------------------------------------------------------------
# KurimaScore label bands (shared with tobacco_math so labels are identical)
# ---------------------------------------------------------------------------
SCORE_BANDS: Tuple[Tuple[int, int, str, str], ...] = (
    (85, 100, "Thriving", "#2E7D32"),
    (70, 84, "Strong", "#66BB6A"),
    (55, 69, "Adequate", "#FBC02D"),
    (40, 54, "Stressed", "#F57C00"),
    (25, 39, "Distressed", "#D84315"),
    (0, 24, "Critical", "#B71C1C"),
)


def label_for_score(score: int) -> Tuple[str, str]:
    """Map a 0-100 KurimaScore to (label, hex_colour)."""
    s = max(0, min(100, int(round(score))))
    for low, high, label, color in SCORE_BANDS:
        if low <= s <= high:
            return label, color
    return "Critical", "#B71C1C"


# ---------------------------------------------------------------------------
# Season phase model (crop-agnostic) and per-phase expected NDVI baselines
# ---------------------------------------------------------------------------
# Coarse phases used everywhere in the aggregator. Stage detection in
# generic_crop_math maps day-since-planting fractions onto these.
PHASES: Tuple[str, ...] = (
    "establishment",
    "vegetative",
    "reproductive",
    "maturation",
    "senescence",
)

# Generic expected (floor, ceiling) NDVI per phase — the band a *healthy* crop
# should sit in. Below floor => stress signal. These mirror the tobacco
# INDEX_BASELINES philosophy but crop-agnostic (audit G5).
_PHASE_NDVI: Dict[str, Tuple[float, float]] = {
    "establishment": (0.15, 0.40),
    "vegetative": (0.45, 0.78),
    "reproductive": (0.55, 0.85),
    "maturation": (0.40, 0.72),
    "senescence": (0.25, 0.55),
}

# Per-crop scaling of the generic band. Some canopies (onion, garlic) never
# reach high NDVI; others (tea, maize) do. Multiplier applied to floor+ceiling.
_CROP_NDVI_SCALE: Dict[str, float] = {
    "onion": 0.72, "garlic": 0.72, "cassava": 0.9, "sesame": 0.9,
    "cowpeas": 0.9, "bambara nuts": 0.85, "tea": 1.08, "maize": 1.05,
    "sugarcane": 1.08, "banana": 1.08, "coffee": 1.05,
}


def expected_ndvi_range(crop_type: Optional[str], phase: Optional[str]) -> Tuple[float, float]:
    """Return the (floor, ceiling) NDVI a healthy ``crop_type`` should show in ``phase``."""
    floor, ceil = _PHASE_NDVI.get((phase or "vegetative"), _PHASE_NDVI["vegetative"])
    scale = _CROP_NDVI_SCALE.get((crop_type or "").strip().lower(), 1.0)
    lo = max(0.0, round(floor * scale, 3))
    hi = min(1.0, round(ceil * scale, 3))
    return lo, hi


def ndvi_health_fraction(crop_type: Optional[str], phase: Optional[str], ndvi: Optional[float]) -> Optional[float]:
    """
    Scale a raw NDVI to a [0,1] health fraction vs the stage-expected band.
    Below the floor -> 0.0, at/above the ceiling -> 1.0, linear in between.
    This is the bridge that makes "NDVI 0.21 at reproductive" read as ~0.0
    (i.e. Critical) rather than as an absolute value the frontend guesses at.
    """
    if ndvi is None:
        return None
    lo, hi = expected_ndvi_range(crop_type, phase)
    if hi <= lo:
        return 0.0
    frac = (float(ndvi) - lo) / (hi - lo)
    return max(0.0, min(1.0, frac))


def classify_ndvi(crop_type: Optional[str], phase: Optional[str], ndvi: Optional[float]) -> dict:
    """
    Classify a raw NDVI for a crop at a phase into a label/colour the whole app
    shares. The label is derived from how the NDVI sits inside the *expected*
    band, so it stays consistent with the KurimaScore.
    """
    lo, hi = expected_ndvi_range(crop_type, phase)
    if ndvi is None:
        return {"label": None, "color": None, "expected_low": lo, "expected_high": hi}
    frac = ndvi_health_fraction(crop_type, phase, ndvi)
    # Map the fraction onto the same 6-band vocabulary as the KurimaScore.
    label, color = label_for_score(int(round((frac or 0.0) * 100)))
    return {
        "label": label,
        "color": color,
        "expected_low": lo,
        "expected_high": hi,
    }


# ---------------------------------------------------------------------------
# Water balance + soil moisture
# ---------------------------------------------------------------------------
def classify_water_balance(balance_mm: Optional[float]) -> Tuple[Optional[str], bool, str]:
    """
    Classify a weekly water balance (rainfall - ET, in mm) into
    (status, irrigation_recommended, urgency).
    """
    if balance_mm is None:
        return None, False, "none"
    b = float(balance_mm)
    if b >= 5:
        return "surplus", False, "none"
    if b >= -5:
        return "balanced", False, "low"
    if b >= -20:
        return "deficit", True, "medium"
    return "deficit", True, "high"


# Crop soil-moisture thresholds (adequate, low, critical) — lifted from the
# backend insight fallback so the *same* numbers drive every screen (F2).
_MOISTURE_T: Dict[str, Tuple[float, float, float]] = {
    "maize": (50, 30, 20), "wheat": (45, 25, 15), "sorghum": (35, 20, 10),
    "finger millet": (30, 18, 10), "pearl millet": (30, 18, 10),
    "tobacco": (45, 30, 20), "cotton": (40, 25, 15), "sunflower": (35, 20, 12),
    "paprika": (45, 30, 18), "sesame": (30, 18, 10), "tea": (55, 40, 30),
    "soybean": (40, 25, 15), "soybeans": (40, 25, 15), "groundnuts": (35, 20, 12),
    "sugar beans": (40, 25, 15), "cowpeas": (30, 18, 10), "bambara nuts": (25, 15, 8),
    "peas": (45, 28, 15), "green beans": (45, 30, 18), "potato": (55, 35, 22),
    "sweet potato": (40, 25, 15), "cassava": (30, 18, 10), "tomato": (55, 35, 22),
    "onion": (50, 30, 18), "cabbage": (55, 35, 22), "butternut": (40, 25, 15),
    "green pepper": (50, 32, 20), "garlic": (45, 28, 15), "strawberries": (55, 35, 22),
    "blueberries": (50, 32, 20), "snow peas": (45, 28, 15),
}


def classify_soil_moisture(crop_type: Optional[str], moisture_pct: Optional[float]) -> Optional[str]:
    """Classify soil-moisture % into wet/adequate/moderate/low/dry for a crop."""
    if moisture_pct is None:
        return None
    adeq, low, crit = _MOISTURE_T.get((crop_type or "").strip().lower(), (40, 25, 15))
    m = float(moisture_pct)
    if m < crit:
        return "dry"
    if m < low:
        return "low"
    if m < adeq:
        return "moderate"
    return "adequate"


# ---------------------------------------------------------------------------
# Confidence — ALWAYS band + integer pct (fixes the 0.6% bug, F3)
# ---------------------------------------------------------------------------
def confidence_from_fraction(score_0_1: Optional[float]) -> Tuple[str, int]:
    """
    Convert a 0-1 confidence fraction into (band, integer_pct).

        >>> confidence_from_fraction(0.6)
        ('medium', 60)

    Never returns a fractional percent. ``None`` -> a conservative medium/50.
    Values >1 are treated as already-percentages and clamped (defensive).
    """
    if score_0_1 is None:
        return "medium", 50
    v = float(score_0_1)
    if v > 1.0:  # caller already multiplied by 100; clamp into fraction
        v = v / 100.0 if v <= 100.0 else 1.0
    v = max(0.0, min(1.0, v))
    pct = int(round(v * 100))
    band = "high" if v >= 0.70 else "medium" if v >= 0.45 else "low"
    return band, pct


def confidence_from_band(band: Optional[str]) -> Tuple[str, int]:
    """Map a band string to a representative integer pct (for band-only sources)."""
    b = (band or "medium").strip().lower()
    return {
        "high": ("high", 80),
        "medium": ("medium", 60),
        "low": ("low", 35),
    }.get(b, ("medium", 60))


# ---------------------------------------------------------------------------
# Satellite observation quality
# ---------------------------------------------------------------------------
def observation_quality(days_since_pass: Optional[int], cloud_pct: Optional[float]) -> str:
    """Grade a satellite observation: good | fair | stale | none."""
    if days_since_pass is None:
        return "none"
    if days_since_pass > 14:
        return "stale"
    cloud = cloud_pct if cloud_pct is not None else 0.0
    if days_since_pass <= 7 and cloud <= 20:
        return "good"
    if days_since_pass <= 10 and cloud <= 40:
        return "fair"
    return "stale"


# ---------------------------------------------------------------------------
# Data completeness
# ---------------------------------------------------------------------------
def compute_completeness(
    has_variety_in_database: bool,
    has_recent_satellite_pass: bool,
    has_input_records: bool,
    has_planting_date: bool,
    has_field_polygon: bool,
) -> Tuple[int, List[str]]:
    """
    Weighted completeness 0-100 plus a human list of what's missing for full
    confidence. Weights reflect how much each input moves the KurimaScore.
    """
    weights = {
        "satellite": (has_recent_satellite_pass, 30, "No recent satellite pass — indices may be stale"),
        "polygon": (has_field_polygon, 20, "No field polygon — weather/satellite localisation is approximate"),
        "planting": (has_planting_date, 20, "No planting date — growth stage and GDD are estimated"),
        "variety": (has_variety_in_database, 15, "Variety not in our database (using crop-type defaults)"),
        "inputs": (has_input_records, 15, "No fertiliser or input applications logged"),
    }
    total = sum(w for _, (_, w, _) in weights.items())
    got = sum(w for _, (present, w, _) in weights.items() if present)
    pct = int(round(100 * got / total)) if total else 0
    missing = [msg for _, (present, _, msg) in weights.items() if not present]
    return pct, missing
