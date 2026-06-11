"""
Field State Aggregator — Pydantic response models
=================================================
The canonical shape of ``GET /field/{field_id}/state``.

Design rules baked into these models (see field_state_audit.md):

* **Units are explicit.** NDVI is dimensionless (-1..1), KurimaScore is 0..100,
  temperatures are Celsius, areas are hectares. Field names and docstrings say so.
* **Confidence is always a band + an integer percent.** Never a bare fraction.
  ``ConfidenceModel`` enforces ``pct`` as an ``int`` in [0, 100] and ``band`` as
  one of low/medium/high — this is what makes "Confidence: 0.6%" unrepresentable.
* Every section is optional-friendly: missing upstream data yields ``None`` plus a
  flag in ``data_completeness`` rather than a fabricated number or a 500.
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------
class ConfidenceModel(BaseModel):
    """Confidence is ALWAYS (band, integer pct). Fixes the 'Confidence: 0.6%' bug."""
    band: str = Field("medium", description="One of: low | medium | high")
    pct: int = Field(60, ge=0, le=100, description="Integer percent 0-100 (never fractional)")


# ---------------------------------------------------------------------------
# field
# ---------------------------------------------------------------------------
class FieldInfo(BaseModel):
    id: str
    name: str
    crop_type: Optional[str] = None
    variety_code: Optional[str] = None
    area_ha: Optional[float] = Field(None, description="Field area in hectares")
    natural_region: Optional[str] = None
    polygon_coordinates: Optional[List[Dict[str, float]]] = None
    tenant_id: Optional[str] = Field(None, description="Owning tenant (user_id today; see audit G1)")


# ---------------------------------------------------------------------------
# season
# ---------------------------------------------------------------------------
class SeasonInfo(BaseModel):
    planted_date: Optional[str] = None
    days_since_planted: Optional[int] = None
    expected_harvest_date: Optional[str] = None
    days_to_harvest: Optional[int] = None
    current_stage: Optional[str] = None
    season_progress_pct: Optional[int] = Field(None, ge=0, le=100)
    season_phase: Optional[str] = Field(
        None, description="Coarse phase: establishment|vegetative|reproductive|maturation|senescence"
    )


# ---------------------------------------------------------------------------
# kurima_score
# ---------------------------------------------------------------------------
class KurimaScoreComponents(BaseModel):
    satellite: Optional[float] = Field(None, ge=0, le=1)
    management: Optional[float] = Field(None, ge=0, le=1)
    environmental: Optional[float] = Field(None, ge=0, le=1)


class KurimaScore(BaseModel):
    score: int = Field(..., ge=0, le=100, description="KurimaScore, 0-100 (dimensionless)")
    label: str
    color: str = Field(..., description="Hex colour for the label band")
    components: KurimaScoreComponents = KurimaScoreComponents()
    primary_driver: Optional[str] = None
    likely_cause: Optional[str] = None
    recommended_action: Optional[str] = None
    yield_implication: Optional[str] = None
    confidence_band: str = "medium"
    confidence_pct: int = Field(60, ge=0, le=100)


# ---------------------------------------------------------------------------
# indices
# ---------------------------------------------------------------------------
class CurrentIndices(BaseModel):
    as_of_date: Optional[str] = None
    ndvi: Optional[float] = Field(None, ge=-1, le=1, description="NDVI, dimensionless -1..1")
    evi: Optional[float] = None
    ndre: Optional[float] = None
    ndmi: Optional[float] = None
    savi: Optional[float] = None
    sar_vv_db: Optional[float] = None
    observation_quality: str = Field("none", description="good | fair | stale | none")
    cloud_pct: Optional[float] = None
    # Interpretation of the raw NDVI given crop + stage — computed server-side so
    # the frontend never decides "0.21 < 0.3 = Critical".
    ndvi_label: Optional[str] = None
    ndvi_color: Optional[str] = None
    ndvi_expected_low: Optional[float] = None
    ndvi_expected_high: Optional[float] = None


class TrendPoint(BaseModel):
    date: str
    ndvi: Optional[float] = None
    kurima_score: Optional[int] = Field(None, ge=0, le=100)


class Indices(BaseModel):
    current: CurrentIndices = CurrentIndices()
    trend_30d: List[TrendPoint] = []


# ---------------------------------------------------------------------------
# yield_projection
# ---------------------------------------------------------------------------
class ConfidenceFactors(BaseModel):
    positive: List[str] = []
    negative: List[str] = []


class YieldProjection(BaseModel):
    projected_tonnes_per_ha: Optional[float] = None
    potential_tonnes_per_ha: Optional[float] = None
    yield_gap_pct: Optional[int] = Field(None, ge=0, le=100)
    confidence_band: str = "medium"
    confidence_pct: int = Field(60, ge=0, le=100)
    confidence_factors: ConfidenceFactors = ConfidenceFactors()
    confidence_interval_low: Optional[float] = None
    confidence_interval_high: Optional[float] = None
    unit: str = Field("tonnes_per_ha", description="All yields are tonnes/ha")


# ---------------------------------------------------------------------------
# weather
# ---------------------------------------------------------------------------
class CurrentWeather(BaseModel):
    temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    wind_kmh: Optional[float] = None
    uv_index: Optional[float] = None
    condition: Optional[str] = None
    as_of: Optional[str] = None


class TodayWeather(BaseModel):
    high: Optional[float] = None
    low: Optional[float] = None
    icon: Optional[str] = None


class ForecastDay(BaseModel):
    day: str
    high: Optional[float] = None
    low: Optional[float] = None
    icon: Optional[str] = None


class Weather(BaseModel):
    current: CurrentWeather = CurrentWeather()
    today: TodayWeather = TodayWeather()
    next_5_days: List[ForecastDay] = []


# ---------------------------------------------------------------------------
# water_balance
# ---------------------------------------------------------------------------
class WaterBalance(BaseModel):
    weekly_rainfall_mm: Optional[float] = None
    weekly_et_mm: Optional[float] = None
    balance_mm: Optional[float] = None
    balance_status: Optional[str] = Field(None, description="surplus | balanced | deficit")
    soil_moisture_pct: Optional[float] = None
    soil_moisture_label: Optional[str] = None
    irrigation_recommended: bool = False
    urgency: Optional[str] = Field(None, description="none | low | medium | high")


# ---------------------------------------------------------------------------
# growing_degree_days
# ---------------------------------------------------------------------------
class GrowingDegreeDays(BaseModel):
    accumulated_gdd: Optional[float] = None
    remaining_gdd: Optional[float] = None
    progress_to_maturity_pct: Optional[int] = Field(None, ge=0, le=100)
    estimated_maturity_days: Optional[int] = None
    current_phase: Optional[str] = None


# ---------------------------------------------------------------------------
# active_plan_items
# ---------------------------------------------------------------------------
class PlanItem(BaseModel):
    id: str
    date: Optional[str] = None
    category: Optional[str] = None
    title: str
    description: Optional[str] = None
    status: str = "pending"
    ai_recommended: bool = False
    contextualized_to_current_conditions: bool = True
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# alerts
# ---------------------------------------------------------------------------
class Alert(BaseModel):
    severity: str = Field(..., description="low | medium | high")
    category: Optional[str] = None
    headline: str
    detail: Optional[str] = None
    first_detected: Optional[str] = None
    recommended_action: Optional[str] = None


# ---------------------------------------------------------------------------
# scouting_observations
# ---------------------------------------------------------------------------
class ScoutingObservation(BaseModel):
    id: str
    date: Optional[str] = None
    type: Optional[str] = None
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# data_completeness
# ---------------------------------------------------------------------------
class DataCompleteness(BaseModel):
    has_variety_in_database: bool = False
    has_recent_satellite_pass: bool = False
    has_input_records: bool = False
    has_planting_date: bool = False
    has_field_polygon: bool = False
    overall_completeness_pct: int = Field(0, ge=0, le=100)
    missing_for_full_confidence: List[str] = []


# ---------------------------------------------------------------------------
# meta
# ---------------------------------------------------------------------------
class Meta(BaseModel):
    generated_at: str
    computation_time_ms: int = 0
    stale_data_warnings: List[str] = []
    as_of_satellite_pass: Optional[str] = None
    next_satellite_pass_estimate: Optional[str] = None


# ---------------------------------------------------------------------------
# Top-level FieldState
# ---------------------------------------------------------------------------
class FieldState(BaseModel):
    """The single canonical document describing a field. Every consumer screen
    reads from this; two screens reading it must reach identical conclusions."""
    field: FieldInfo
    season: SeasonInfo = SeasonInfo()
    kurima_score: KurimaScore
    indices: Indices = Indices()
    yield_projection: YieldProjection = YieldProjection()
    weather: Weather = Weather()
    water_balance: WaterBalance = WaterBalance()
    growing_degree_days: GrowingDegreeDays = GrowingDegreeDays()
    active_plan_items: List[PlanItem] = []
    alerts: List[Alert] = []
    scouting_observations: List[ScoutingObservation] = []
    data_completeness: DataCompleteness = DataCompleteness()
    meta: Meta
