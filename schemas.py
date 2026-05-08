"""
KurimaSense Pydantic Request/Response Schemas
==============================================
Provides type-safe validation for all API endpoints,
replacing raw dict payloads with structured models.
"""

from datetime import date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ========== Common Models ==========

class Coordinate(BaseModel):
    lat: float
    lon: float


# ========== Field Schemas ==========

class CreateFieldRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    crop: str = Field(default="Maize", max_length=50)
    coordinates: List[Coordinate] = []
    area: Optional[float] = Field(default=15.0, ge=0)
    plantingDate: Optional[str] = None
    transplantDate: Optional[str] = None
    isTransplanted: Optional[bool] = False
    variety: Optional[str] = None
    fertilizerHistory: Optional[str] = None


class FieldResponse(BaseModel):
    status: str
    id: str


# ========== Chat Schemas ==========

class ChatContext(BaseModel):
    user_id: Optional[str] = None
    field_id: Optional[str] = None
    location: Optional[Coordinate] = None
    language: Optional[str] = "en"
    voice_enabled: Optional[bool] = False


class ChatSendRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    context: Optional[ChatContext] = None
    image: Optional[str] = None  # base64 encoded


class ChatV2SendRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    field_id: Optional[str] = None
    session_id: Optional[str] = None
    language: Optional[str] = "en"
    image: Optional[str] = None  # base64 encoded


# ========== Input Logging ==========

class LogInputRequest(BaseModel):
    field_id: str
    input_type: str = Field(..., min_length=1)
    quantity: float = Field(..., ge=0)
    unit: str = Field(default="units")
    date: Optional[str] = "now"


# ========== Yield Schemas ==========

class YieldRecordRequest(BaseModel):
    season_year: int = Field(..., ge=2000, le=2100)
    season_type: str = Field(default="summer")
    crop_type: Optional[str] = None
    variety: Optional[str] = None
    planting_date: Optional[str] = None
    harvest_date: Optional[str] = None
    area_harvested_ha: float = Field(..., gt=0)
    actual_yield_tonnes: float = Field(..., ge=0)
    quality_grade: Optional[str] = None
    moisture_at_harvest: Optional[float] = None
    projected_yield_tonnes: Optional[float] = None
    sale_price_per_tonne: Optional[float] = None
    notes: Optional[str] = None


# ========== Vision Schemas ==========

class VisionAnalyzeRequest(BaseModel):
    image: str = Field(..., min_length=1)  # base64 image data
    crop_type: Optional[str] = None
    additional_context: Optional[str] = None


# ========== Farm Tasks ==========

class CreateFarmTaskRequest(BaseModel):
    field_id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    activity_type: str = Field(default="custom")
    priority: str = Field(default="normal")
    task_date: Optional[str] = None


class UpdateFarmTaskRequest(BaseModel):
    completed: Optional[bool] = None
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None


# ========== Portfolio (B2B) Schemas ==========

class ConfidenceBand(BaseModel):
    low: float
    mid: float
    high: float


class DistrictForecast(BaseModel):
    district_name: str
    n_fields: int
    total_area_ha: float
    projected_yield_tonnes_per_ha: float
    confidence_score: float
    confidence_band: ConfidenceBand


class PortfolioYieldForecastResponse(BaseModel):
    tenant_id: str
    crop: str
    districts: List[DistrictForecast]


class RiskDistribution(BaseModel):
    low: int
    medium: int
    high: int
    critical: int


class FieldAlert(BaseModel):
    field_id: str
    risk_level: str
    primary_concern: str


class PortfolioRiskSummaryResponse(BaseModel):
    tenant_id: str
    total_fields: int
    risk_distribution: RiskDistribution
    fields_with_alerts: List[FieldAlert]


class FieldAnomaly(BaseModel):
    field_id: str
    index: str
    days_back: int
    earlier_mean: float
    recent_mean: float
    drop: float


class PortfolioAnomaliesResponse(BaseModel):
    tenant_id: str
    threshold: float
    days_back: int
    anomalies: List[FieldAnomaly]


class IndicesHistoryPoint(BaseModel):
    log_date: date
    ndvi: Optional[float] = None
    evi: Optional[float] = None
    ndre: Optional[float] = None
    ndmi: Optional[float] = None
    savi: Optional[float] = None
    vv_db: Optional[float] = None
    vh_db: Optional[float] = None
    cloud_pct: Optional[float] = None
    observation_quality: Optional[str] = None


class IndicesHistoryResponse(BaseModel):
    field_id: str
    start_date: date
    end_date: date
    points: List[IndicesHistoryPoint]


class RiskScoreRequest(BaseModel):
    field_ids: List[str] = Field(..., min_length=1, max_length=500)


class FieldRiskScore(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    primary_factors: List[str]


class RiskScoreResponse(BaseModel):
    tenant_id: str
    scores: Dict[str, FieldRiskScore]


# ========== Admin: API key management ==========

class CreateApiKeyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    expires_days: Optional[int] = Field(default=None, gt=0, le=3650)
    rate_limit_per_minute: Optional[int] = Field(default=None, gt=0, le=100_000)
    rate_limit_per_day: Optional[int] = Field(default=None, gt=0, le=10_000_000)


class CreateApiKeyResponse(BaseModel):
    key_id: str
    tenant_id: str
    name: str
    raw_key: str  # shown ONCE; never reproducible after this response
    expires_at: Optional[str] = None


class ApiKeyMetadata(BaseModel):
    id: str
    tenant_id: str
    name: str
    created_at: Optional[str] = None
    expires_at: Optional[str] = None
    last_used_at: Optional[str] = None
    is_active: bool
    rate_limit_override: Optional[Dict[str, Any]] = None
    key_id_hex: Optional[str] = None


class ListApiKeysResponse(BaseModel):
    tenant_id: str
    keys: List[ApiKeyMetadata]


class RevokeApiKeyResponse(BaseModel):
    key_id: str
    revoked: bool
