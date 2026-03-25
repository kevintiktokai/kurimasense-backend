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
