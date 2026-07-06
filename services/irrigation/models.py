"""
Irrigation engine domain model.

``IrrigationInputs`` is the engine's entire world — service.py assembles it
from fields/soil/weather/planner, tests construct it directly, and future data
sources (soil-moisture probes, satellite ET, IoT valves) become new optional
fields here without touching the decision core's consumers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional


@dataclass
class DayWeather:
    """One day of the water-balance weather series."""

    date: str                                   # ISO date
    et0: Optional[float] = None                 # FAO reference ET, mm
    precip: Optional[float] = None              # rainfall, mm
    precip_probability: Optional[float] = None  # %, forecast rows only
    tmax: Optional[float] = None
    tmin: Optional[float] = None


# Application rates (mm/hour) used to translate a recommended depth into a
# runtime. Deliberately conservative field-scale defaults; a per-field
# irrigation-system profile can override them later.
IRRIGATION_METHOD_RATES_MM_PER_HOUR: Dict[str, float] = {
    "drip": 6.0,
    "sprinkler": 10.0,
    "center_pivot": 12.0,
    "flood": 40.0,
    "furrow": 30.0,
    "manual": 8.0,   # bucket/hose watering
}
DEFAULT_IRRIGATION_METHOD = "sprinkler"

# Fallback plant-available water capacity when no soil profile exists yet
# (loam-ish mid-range; the reasoning notes when this default is used).
DEFAULT_AWC_MM_PER_M = 140.0

# Stage-dependent effective rooting depth bounds (m). Simple two-point model:
# roots grow from MIN at emergence to the crop's max over the season.
MIN_ROOT_DEPTH_M = 0.15
DEFAULT_MAX_ROOT_DEPTH_M = 0.6
MAX_ROOT_DEPTH_BY_CROP_M: Dict[str, float] = {
    "maize": 1.0, "sorghum": 1.0, "wheat": 1.0, "sunflower": 1.1,
    "soybean": 0.8, "groundnuts": 0.6, "tobacco": 0.8, "cotton": 1.0,
    "potato": 0.5, "tomato": 0.7, "cabbage": 0.5, "onion": 0.4,
    "banana": 0.7, "citrus": 1.1, "avocado": 0.9, "macadamia": 1.0,
    "coffee": 1.0, "tea": 0.9,
}

# Management-allowed depletion fraction p (share of TAW that can deplete before
# stress). FAO-56 table 22 varies 0.3–0.6 by crop; 0.5 is the standard default.
DEFAULT_DEPLETION_FRACTION = 0.5

# Share of gross rainfall that actually recharges the root zone (runoff /
# interception / deep-percolation losses).
EFFECTIVE_RAIN_FACTOR = 0.8


@dataclass
class IrrigationInputs:
    """Everything the pure decision core needs, pre-resolved."""

    field_id: str
    field_name: str
    crop: str
    stage_name: str
    kc: float
    days_since_planting: int
    awc_mm_per_m: float = DEFAULT_AWC_MM_PER_M
    awc_source: str = "default"                 # "soil_profile" | "default"
    root_depth_m: float = 0.4
    depletion_fraction: float = DEFAULT_DEPLETION_FRACTION
    past: List[DayWeather] = field(default_factory=list)      # oldest → newest
    forecast: List[DayWeather] = field(default_factory=list)  # today → future
    # ISO dates on which irrigation was recorded in the planner (assumed refill
    # to field capacity — amounts aren't captured yet).
    irrigation_dates: List[str] = field(default_factory=list)
    method: str = DEFAULT_IRRIGATION_METHOD
    # Future integrations override the modeled depletion when present:
    measured_soil_moisture_depletion_mm: Optional[float] = None


@dataclass
class IrrigationRecommendation:
    """An explainable, actionable recommendation."""

    field_id: str
    field_name: str
    crop: str
    stage: str
    # irrigate_now | irrigate_soon | delay_rain_expected | monitor | not_needed
    action: str
    headline: str                    # one-line farmer-facing verdict
    reasoning: List[str]             # the full explanation chain
    water_deficit_mm: float          # estimated current root-zone depletion
    raw_trigger_mm: float            # readily-available-water threshold
    taw_mm: float                    # total available water in root zone
    recommended_mm: float            # suggested application depth (0 if none)
    duration_minutes: Optional[int]  # runtime for the chosen method
    method: str
    expected_rain_mm_3d: float       # probability-weighted forecast, next 3 days
    etc_mm_per_day: float            # current crop water use
    confidence: float                # 0..1
    confidence_label: str            # high | medium | low
    next_review_date: Optional[str] = None
    valid_until: Optional[str] = None
    generated_at: Optional[str] = None
    data_sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_id": self.field_id,
            "field_name": self.field_name,
            "crop": self.crop,
            "stage": self.stage,
            "action": self.action,
            "headline": self.headline,
            "reasoning": self.reasoning,
            "water_deficit_mm": round(self.water_deficit_mm, 1),
            "raw_trigger_mm": round(self.raw_trigger_mm, 1),
            "taw_mm": round(self.taw_mm, 1),
            "recommended_mm": round(self.recommended_mm, 1),
            "duration_minutes": self.duration_minutes,
            "method": self.method,
            "expected_rain_mm_3d": round(self.expected_rain_mm_3d, 1),
            "etc_mm_per_day": round(self.etc_mm_per_day, 2),
            "confidence": round(self.confidence, 2),
            "confidence_label": self.confidence_label,
            "next_review_date": self.next_review_date,
            "valid_until": self.valid_until,
            "generated_at": self.generated_at,
            "data_sources": self.data_sources,
        }

    def summary(self) -> str:
        """Compact multi-line text for notifications/emails."""
        lines = [self.headline]
        lines += [f"• {r}" for r in self.reasoning[:4]]
        return "\n".join(lines)
