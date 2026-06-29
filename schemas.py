"""
KurimaSense Pydantic Request/Response Schemas
==============================================
Provides type-safe validation for all API endpoints,
replacing raw dict payloads with structured models.
"""

from datetime import date, datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, model_validator


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


# ========== Role Tagging (Workstream 1) ==========

Role = Literal["consumer", "institutional", "admin"]
InstitutionalType = Literal["buyer", "lender", "insurer", "grower"]
MemberRole = Literal["owner", "officer", "viewer"]


class AuthenticatedUser(BaseModel):
    """Role-aware identity for an authenticated request.

    Produced by ``auth_roles.get_authenticated_user`` (NOT by ``verify_token``,
    which is kept returning a bare ``user_id`` string for backward compatibility
    with the 48 existing endpoints). Carries the access tier and, for
    institutional users, their institution type/name.
    """
    user_id: str
    role: Role
    institutional_type: Optional[InstitutionalType] = None
    tenant_name: Optional[str] = None
    # Tenant context (Workstream 3). tenant_id is the *primary* tenant (earliest
    # joined). Optional because admins (and a degraded/pre-migration DB) have no
    # tenant membership — callers must handle None.
    tenant_id: Optional[str] = None
    tenant_ids: List[str] = []
    member_role: Optional[MemberRole] = None

    @model_validator(mode="after")
    def _institutional_requires_type(self) -> "AuthenticatedUser":
        # Pydantic-level mirror of the DB CHECK `institutional_users_have_type`.
        if self.role == "institutional" and self.institutional_type is None:
            raise ValueError("institutional users must have an institutional_type")
        return self


class SelfServeInstitutionalRequest(BaseModel):
    """Body for POST /me/institutional — a user upgrading their OWN account to an
    institution during onboarding (self-service, session-gated; distinct from the
    X-Admin-Token admin flow). ``institutional_type`` is validated by the Literal
    (422 on a bad value); ``organization_name`` becomes the tenant display name."""
    institutional_type: InstitutionalType
    organization_name: str = Field(..., min_length=1, max_length=200)


class UpdateUserRoleRequest(BaseModel):
    """Body for POST /admin/users/{user_id}/role.

    Note: the institutional-requires-type rule is enforced in the endpoint (so it
    can return HTTP 400, not a 422 validation error), NOT via a model validator.
    """
    role: Role
    institutional_type: Optional[InstitutionalType] = None
    tenant_name: Optional[str] = None


class UpdateUserRoleResponse(BaseModel):
    user_id: str
    role: str
    institutional_type: Optional[str] = None
    tenant_name: Optional[str] = None
    updated_at: str  # ISO timestamp


class UserProfile(BaseModel):
    """User profile shape including role context. Defined for a future GET /me
    (Workstream 2) — no endpoint returns it in this PR."""
    user_id: str
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    role: Role = "consumer"
    institutional_type: Optional[InstitutionalType] = None
    tenant_name: Optional[str] = None
    preferred_language: Optional[str] = None


class SelfServeInstitutionalRequest(BaseModel):
    """Body for POST /me/institutional — the authenticated user upgrades their
    OWN account to an institutional one (self-service signup).

    Unlike the admin role endpoint (which is gated by X-Admin-Token), this is
    gated by the user's own session: a user can only ever institutionalise
    themselves. The endpoint also provisions the tenant + owner membership so
    portfolio access works immediately — which the admin role-flip endpoint
    deliberately does not do.
    """
    institutional_type: InstitutionalType
    organization_name: str = Field(..., min_length=1, max_length=200)


class SelfServeInstitutionalResponse(BaseModel):
    user_id: str
    role: Role
    institutional_type: InstitutionalType
    tenant_name: str
    tenant_id: str
    member_role: MemberRole


# ========== Tenant model (Workstream 3) ==========

class Tenant(BaseModel):
    id: str
    name: str
    tenant_type: Literal["consumer", "institutional"]
    institutional_type: Optional[InstitutionalType] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class TenantMember(BaseModel):
    tenant_id: str
    user_id: str
    member_role: MemberRole
    joined_at: datetime


class CreateTenantRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    tenant_type: Literal["consumer", "institutional"] = "institutional"
    institutional_type: Optional[InstitutionalType] = None


class UpdateTenantRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    institutional_type: Optional[InstitutionalType] = None


class TenantDetail(Tenant):
    members: List[TenantMember] = []


class AddTenantMemberRequest(BaseModel):
    user_id: str
    member_role: MemberRole = "officer"


class UpdateTenantMemberRequest(BaseModel):
    member_role: MemberRole


# ========== Growers (Workstream 3) ==========

class Grower(BaseModel):
    id: str
    tenant_id: str
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    coordinates: Optional[dict] = None
    claimed_by_user_id: Optional[str] = None
    created_by_user_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CreateGrowerRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    phone: Optional[str] = None
    email: Optional[str] = None
    coordinates: Optional[dict] = None
    notes: Optional[str] = None


class UpdateGrowerRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    phone: Optional[str] = None
    email: Optional[str] = None
    coordinates: Optional[dict] = None
    notes: Optional[str] = None


# ========== Portfolio Aggregate (MVP PR 2) ==========

class PortfolioTenantInfo(BaseModel):
    id: str
    name: str
    institutional_type: Optional[InstitutionalType] = None


class PortfolioScoreDistribution(BaseModel):
    thriving: int = 0
    strong: int = 0
    adequate: int = 0
    stressed: int = 0
    distressed: int = 0
    critical: int = 0
    awaiting_data: int = 0


class PortfolioSummary(BaseModel):
    total_fields: int
    total_growers: int
    total_hectares: float
    score_distribution: PortfolioScoreDistribution
    alerts_critical: int
    alerts_high: int
    average_kurima_score: Optional[float] = None
    fields_with_data: int
    fields_awaiting_data: int


class PortfolioPriority(BaseModel):
    field_id: str
    field_name: str
    grower_id: Optional[str] = None
    grower_name: Optional[str] = None
    district: Optional[str] = None
    natural_region: Optional[str] = None
    crop_type: str
    variety: Optional[str] = None
    size_hectares: float
    kurima_score: Optional[int] = None
    kurima_label: Optional[str] = None
    kurima_color: Optional[str] = None
    primary_concern: Optional[str] = None
    recommended_action: Optional[str] = None
    urgency: Literal["critical", "high", "medium", "low", "awaiting_data"]
    days_since_observation: Optional[int] = None
    planting_date: Optional[str] = None
    days_since_planting: Optional[int] = None
    # Geometry + latest raw indices (Depth Sprint PR C) — additive, for the map
    # view. Passed through / derived from data already loaded; no extra queries.
    polygon_coordinates: Optional[list] = None
    centroid: Optional[dict] = None
    latest_ndvi: Optional[float] = None
    latest_soil_moisture: Optional[float] = None


class PortfolioAggregateResponse(BaseModel):
    tenant: PortfolioTenantInfo
    summary: PortfolioSummary
    priorities: List[PortfolioPriority]
    generated_at: datetime


# ========== Season accumulations (Depth Sprint PR D) ==========

class SeasonAccumulationDay(BaseModel):
    date: str            # YYYY-MM-DD
    gdd: float
    gdd_cumulative: float
    precip_mm: float
    precip_cumulative: float


class SeasonAccumulationsResponse(BaseModel):
    field_id: str
    crop_type: str
    planting_date: str
    days_elapsed: int
    gdd_base_c: float
    gdd_cap_c: float
    total_gdd: float
    total_precip_mm: float
    series: List[SeasonAccumulationDay]


# ========== Harvest Schemas ==========

class CreateHarvestRequest(BaseModel):
    season_year: int = Field(..., ge=2000, le=2100)
    area_harvested_ha: float = Field(..., gt=0)
    actual_yield_tonnes: float = Field(..., gt=0)
    harvest_date: Optional[date] = None
    quality_grade: Optional[str] = None
    moisture_at_harvest: Optional[float] = Field(default=None, ge=0, le=100)
    sale_price_per_tonne: Optional[float] = Field(default=None, ge=0)
    delivered_to_tenant: Optional[bool] = None
    notes: Optional[str] = None


class HarvestRecord(BaseModel):
    id: str
    field_id: str
    grower_id: Optional[str] = None
    tenant_id: Optional[str] = None
    season_year: int
    season_type: Optional[str] = None
    crop_type: Optional[str] = None
    variety: Optional[str] = None
    planting_date: Optional[date] = None
    harvest_date: Optional[date] = None
    area_harvested_ha: Optional[float] = None
    actual_yield_tonnes: Optional[float] = None
    quality_grade: Optional[str] = None
    moisture_at_harvest: Optional[float] = None
    sale_price_per_tonne: Optional[float] = None
    delivered_to_tenant: Optional[bool] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None


# ========== Calibration Schemas ==========

class CalibrationEntry(BaseModel):
    crop_type: Optional[str] = None
    natural_region: Optional[str] = None
    variety: Optional[str] = None
    season_progress_bucket: Optional[str] = None
    model_version: str
    n_observations: int
    mae_pct: float
    rmse: Optional[float] = None
    bias_pct: Optional[float] = None
    computed_at: Optional[datetime] = None


class CalibrationResponse(BaseModel):
    headline_mae_pct: Optional[float] = None
    headline_crop: Optional[str] = None
    headline_progress_bucket: Optional[str] = None
    is_validated: bool = False
    entries: List[CalibrationEntry] = []


# ========== Financial / Exposure Schemas (Sprint 2) ==========

class CreateContractRequest(BaseModel):
    grower_id: str
    season_year: int = Field(..., ge=2000, le=2100)
    crop_type: Optional[str] = None
    contracted_volume_tonnes: float = Field(..., gt=0)
    contract_price_per_tonne: float = Field(..., gt=0)
    input_credit_value: float = Field(..., ge=0)
    status: Optional[str] = Field(default="active")


class Contract(BaseModel):
    id: str
    tenant_id: Optional[str] = None
    grower_id: Optional[str] = None
    season_year: int
    crop_type: Optional[str] = None
    contracted_volume_tonnes: Optional[float] = None
    contract_price_per_tonne: Optional[float] = None
    input_credit_value: Optional[float] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None


class CreateDisbursementRequest(BaseModel):
    grower_id: str
    contract_id: Optional[str] = None
    input_type: Optional[str] = None
    quantity: Optional[float] = Field(default=None, ge=0)
    unit: Optional[str] = None
    credit_value: float = Field(..., gt=0)
    disbursement_date: Optional[date] = None


class Disbursement(BaseModel):
    id: str
    tenant_id: Optional[str] = None
    grower_id: Optional[str] = None
    contract_id: Optional[str] = None
    disbursement_date: Optional[date] = None
    input_type: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    credit_value: Optional[float] = None
    created_at: Optional[datetime] = None


class CreateDeliveryRequest(BaseModel):
    grower_id: str
    contract_id: Optional[str] = None
    field_id: Optional[str] = None
    volume_tonnes: float = Field(..., gt=0)
    price_per_tonne: Optional[float] = Field(default=None, ge=0)
    quality_grade: Optional[str] = None
    delivery_date: Optional[date] = None


class Delivery(BaseModel):
    id: str
    tenant_id: Optional[str] = None
    grower_id: Optional[str] = None
    contract_id: Optional[str] = None
    field_id: Optional[str] = None
    delivery_date: Optional[date] = None
    volume_tonnes: Optional[float] = None
    price_per_tonne: Optional[float] = None
    quality_grade: Optional[str] = None
    value_usd: Optional[float] = None
    created_at: Optional[datetime] = None


class GrowerExposureOut(BaseModel):
    grower_id: str
    grower_name: Optional[str] = None
    input_credit_value: float
    projected_volume_tonnes: float
    price_per_tonne: float
    repayment_likelihood: float
    net_exposure: float
    expected_harvest_date: Optional[date] = None
    kurima_score: Optional[float] = None
    field_count: int = 0


class WeeklyExposureOut(BaseModel):
    week_start: date
    total_net_exposure: float
    grower_count: int


class ExposureResponse(BaseModel):
    tenant_id: str
    total_net_exposure: float
    total_input_credit: float
    total_expected_recoverable: float
    grower_count: int
    model_version: str
    growers: List[GrowerExposureOut] = []
    weekly: List[WeeklyExposureOut] = []


# ========== Scouting Schemas (Sprint 3) ==========

ScoutingCategory = Literal['pest', 'disease', 'weed', 'water', 'nutrient', 'general']
ScoutingSeverity = Literal['low', 'medium', 'high', 'critical']


class CreateScoutingRequest(BaseModel):
    category: ScoutingCategory
    severity: ScoutingSeverity
    notes: Optional[str] = None
    lat: Optional[float] = Field(default=None, ge=-90, le=90)
    lon: Optional[float] = Field(default=None, ge=-180, le=180)
    photo_url: Optional[str] = None
    diagnosis: Optional[Dict[str, Any]] = None
    observed_at: Optional[datetime] = None
    source: Optional[str] = Field(default='grower_logged')


class ScoutingRecord(BaseModel):
    id: str
    field_id: str
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    notes: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    photo_url: Optional[str] = None
    diagnosis: Optional[Dict[str, Any]] = None
    observed_at: Optional[datetime] = None
    source: Optional[str] = None
    created_at: Optional[datetime] = None


# ========== Reconciliation Schemas (Sprint 4) ==========

class GrowerReconciliationOut(BaseModel):
    grower_id: str
    grower_name: Optional[str] = None
    contracted_volume_tonnes: float
    projected_volume_tonnes: float
    delivered_volume_tonnes: float
    expected_volume_tonnes: float
    delivery_gap_pct: float
    side_marketing_volume_tonnes: float
    flag: str
    reasons: List[str] = []


class ReconciliationResponse(BaseModel):
    tenant_id: str
    grower_count: int
    flagged_count: int
    watch_count: int
    total_side_marketing_tonnes: float
    growers: List[GrowerReconciliationOut] = []


# ========== Verification Schemas (Sprint 4) ==========

class InputVerificationOut(BaseModel):
    input_date: date
    input_type: Optional[str] = None
    ndvi_before: Optional[float] = None
    ndvi_after: Optional[float] = None
    response_delta: Optional[float] = None
    status: str
    reason: str


class FieldVerificationResponse(BaseModel):
    field_id: str
    n_inputs: int
    n_verified: int
    n_flagged: int
    n_unknown: int
    verification_pct: Optional[float] = None
    inputs: List[InputVerificationOut] = []


class FieldVerificationSummary(BaseModel):
    field_id: str
    field_name: Optional[str] = None
    grower_name: Optional[str] = None
    n_inputs: int
    n_verified: int
    n_flagged: int
    n_unknown: int
    verification_pct: Optional[float] = None


class PortfolioVerificationResponse(BaseModel):
    tenant_id: str
    field_count: int
    fields_with_flagged: int
    total_flagged_inputs: int
    total_inputs: int
    fields: List[FieldVerificationSummary] = []

