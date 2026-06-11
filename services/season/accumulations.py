"""
Season accumulation series — pure computation (Depth Sprint PR D).

Growing-degree-day (GDD) and cumulative-precipitation curves from a field's
planting date. **No network, no DB, no Pydantic-of-HTTP** — the HTTP/provider
code (climate_service) and the route (season_routes) are separate, so this math
is unit-testable against fixed daily-weather fixtures.

GDD with an upper cap:  ``gdd = max(0, min((tmax+tmin)/2, cap) - base)``
  - daily mean below ``base``           -> 0
  - daily mean at/above ``cap``          -> capped at ``cap - base``

Bases follow the canonical crop lookup (crop_constants); the cap is 30 °C — the
standard upper threshold above which extra heat no longer speeds development for
these warm-season crops (tobacco/maize/cotton/soybean). See
docs/season_accumulations_audit.md.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

# Per-crop GDD (base_c, cap_c). Bases mirror crop_constants.CROP_BASE_TEMPS;
# the cap is added here (none exists upstream). Keyed by crop family — the
# field's crop_type (e.g. "tobacco_flue_cured") is normalized before lookup.
GDD_PARAMS: dict[str, Tuple[float, float]] = {
    "tobacco": (10.0, 30.0),
    "maize": (10.0, 30.0),
    "cotton": (15.6, 30.0),
    "soybean": (10.0, 30.0),
    "soybeans": (10.0, 30.0),
    "sorghum": (10.0, 30.0),
    "groundnut": (13.0, 30.0),
    "groundnuts": (13.0, 30.0),
    "wheat": (4.0, 30.0),
}
DEFAULT_GDD_PARAMS: Tuple[float, float] = (10.0, 30.0)


def gdd_params_for(crop_type: Optional[str]) -> Tuple[float, float]:
    """Return ``(base_c, cap_c)`` for a field's ``crop_type``. Unknown -> default.

    Matches on crop *family* so variant strings like ``tobacco_flue_cured`` or
    ``tobacco_burley`` resolve to the tobacco params.
    """
    key = (crop_type or "").strip().lower()
    if not key:
        return DEFAULT_GDD_PARAMS
    if key in GDD_PARAMS:
        return GDD_PARAMS[key]
    for family, params in GDD_PARAMS.items():
        if key.startswith(family) or family in key:
            return params
    return DEFAULT_GDD_PARAMS


def compute_gdd(tmax: Optional[float], tmin: Optional[float], base: float, cap: float) -> float:
    """One day's GDD with the upper cap. Missing temps -> 0.0 (never raises)."""
    if tmax is None or tmin is None:
        return 0.0
    try:
        mean = (float(tmax) + float(tmin)) / 2.0
    except (TypeError, ValueError):
        return 0.0
    mean = min(mean, cap)
    return max(0.0, mean - base)


class DailyWeather:
    """A single day of provider weather (plain holder; no validation)."""
    __slots__ = ("date", "tmax", "tmin", "precip")

    def __init__(self, date: str, tmax: Optional[float], tmin: Optional[float], precip: Optional[float]):
        self.date = date
        self.tmax = tmax
        self.tmin = tmin
        self.precip = precip


def build_series(
    daily: List[DailyWeather], base: float, cap: float
) -> Tuple[List[dict], float, float]:
    """Build the per-day accumulation series from ordered daily weather.

    Returns ``(series, total_gdd, total_precip_mm)`` where each series item is a
    dict with ``date, gdd, gdd_cumulative, precip_mm, precip_cumulative``. Every
    provided day appears (date continuity preserved); missing temps contribute 0
    GDD and missing precip contributes 0 mm, so cumulatives are monotonic
    non-decreasing.
    """
    series: List[dict] = []
    cum_gdd = 0.0
    cum_precip = 0.0
    for d in daily:
        gdd = compute_gdd(d.tmax, d.tmin, base, cap)
        precip = float(d.precip) if d.precip is not None else 0.0
        if precip < 0:
            precip = 0.0
        cum_gdd += gdd
        cum_precip += precip
        series.append({
            "date": d.date,
            "gdd": round(gdd, 2),
            "gdd_cumulative": round(cum_gdd, 2),
            "precip_mm": round(precip, 2),
            "precip_cumulative": round(cum_precip, 2),
        })
    return series, round(cum_gdd, 2), round(cum_precip, 2)
