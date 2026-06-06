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
