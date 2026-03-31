"""
Base dataclass definitions for the crop profile system.
All crop profile modules import these structures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


# ---------------------------------------------------------------------------
# Core enums
# ---------------------------------------------------------------------------

class NaturalRegion(Enum):
    """Zimbabwe Natural Farming Regions (agro-ecological zones)."""
    I = "I"       # Eastern Highlands, >1000mm rain, specialised farming
    II_A = "IIa"  # 750-1000mm, intensive farming (Mashonaland)
    II_B = "IIb"  # 750-1000mm, intensive farming
    III = "III"   # 650-800mm, semi-intensive
    IV = "IV"     # 450-650mm, semi-extensive (Matabeleland)
    V = "V"       # <450mm, extensive (Lowveld)


class SoilType(Enum):
    """Common Zimbabwe soil types."""
    FERSIALLITIC = "fersiallitic"        # Red / reddish-brown clays (Highveld)
    KAOLINITIC = "kaolinitic"            # Sandy, leached (granite sands)
    VERTISOL = "vertisol"                # Black cotton soils (Lowveld)
    SIALLITIC = "siallitic"              # Fertile alluvial soils
    LITHOSOL = "lithosol"                # Thin, rocky soils


class NutrientStatus(Enum):
    DEFICIENT = "deficient"
    LOW = "low"
    ADEQUATE = "adequate"
    HIGH = "high"
    TOXIC = "toxic"


# ---------------------------------------------------------------------------
# Data classes for structured crop knowledge
# ---------------------------------------------------------------------------

@dataclass
class NutrientRequirement:
    """Nutrient needs for a crop at a specific growth stage."""
    nitrogen_kg_ha: float
    phosphorus_kg_ha: float
    potassium_kg_ha: float
    sulphur_kg_ha: float = 0.0
    zinc_kg_ha: float = 0.0
    boron_kg_ha: float = 0.0
    molybdenum_note: str = ""
    calcium_note: str = ""
    timing: str = ""
    scientific_basis: str = ""


@dataclass
class FertilizerSchedule:
    """Complete fertilizer programme for a crop."""
    basal: Dict[str, Any]         # At planting
    top_dress_1: Dict[str, Any]   # First top-dress
    top_dress_2: Optional[Dict[str, Any]] = None  # Second top-dress (if applicable)
    foliar: Optional[Dict[str, Any]] = None  # Foliar feeds
    liming: Optional[Dict[str, Any]] = None  # Lime requirements
    notes: str = ""


@dataclass
class DiseaseProfile:
    """Complete disease identification and management profile."""
    name: str
    pathogen: str
    pathogen_type: str   # fungal, bacterial, viral, nematode
    symptoms: List[str]
    identification_markers: List[str]  # Key visual diagnostic features
    favourable_conditions: Dict[str, Any]  # temp, humidity, etc.
    susceptible_stages: List[str]
    resistant_varieties: List[str]
    susceptible_varieties: List[str]
    chemical_control: List[Dict[str, str]]  # [{name, rate, phi_days, notes}]
    biological_control: List[str]
    cultural_control: List[str]
    economic_threshold: str
    severity_scale: Dict[str, str]  # {mild: desc, moderate: desc, severe: desc}


@dataclass
class PestProfile:
    """Complete pest identification and IPM profile."""
    name: str
    scientific_name: str
    pest_type: str  # insect, mite, rodent, bird, nematode
    identification: List[str]
    damage_symptoms: List[str]
    life_cycle_notes: str
    favourable_conditions: Dict[str, Any]
    susceptible_stages: List[str]
    economic_threshold: str
    chemical_control: List[Dict[str, str]]
    biological_control: List[str]
    cultural_control: List[str]
    scouting_protocol: str


@dataclass
class GrowthStageRequirements:
    """What a crop needs at a specific growth stage."""
    stage_name: str
    stage_code: str
    day_range: Tuple[int, int]     # (start_day, end_day) from planting
    water_kc: float                 # Crop coefficient for ET calculation
    water_mm_per_week: float        # Simplified weekly requirement
    critical_nutrients: List[str]   # Which nutrients are most important now
    key_activities: List[str]       # What farmer should do
    risks: List[str]                # What to watch out for
    scientific_notes: str           # PhD-level explanation of why


@dataclass
class PlantingWindow:
    """Optimal planting window for a region."""
    region: str
    optimal_start: str  # "October 15"
    optimal_end: str    # "November 30"
    acceptable_start: str
    acceptable_end: str
    notes: str


@dataclass
class CropProfile:
    """Complete agronomic profile for a crop."""
    crop_name: str
    scientific_name: str
    family: str

    # Soil requirements
    optimal_ph: Tuple[float, float]  # (min, max)
    critical_ph_low: float           # Below this = Al toxicity / P lockup
    optimal_soil_types: List[str]
    avoid_soil_types: List[str]

    # Climate requirements
    optimal_temp: Tuple[float, float]   # (min_optimal, max_optimal) °C
    critical_temp_low: float             # Frost / cold damage threshold
    critical_temp_high: float            # Heat stress threshold
    base_temp_gdd: float                 # Base temp for GDD calculation
    total_water_mm: float                # Total season water requirement

    # Growth stages with detailed requirements
    growth_stages: List[GrowthStageRequirements]

    # Fertilizer programme
    fertilizer_schedule: FertilizerSchedule

    # Pest & disease knowledge
    diseases: List[DiseaseProfile]
    pests: List[PestProfile]

    # Planting windows
    planting_windows: List[PlantingWindow]

    # Post-harvest
    harvest_moisture: str          # Target moisture for harvest
    storage_conditions: str
    post_harvest_notes: str

    # Zimbabwe-specific
    natural_region_suitability: Dict[str, str]  # {region: suitability_note}
