"""
KurimaSense Crop Profiles Package
===================================
Auto-discovers and registers all crop profiles from per-crop modules.

Usage:
    from crop_profiles import get_crop_profile, build_crop_context_for_ai
    profile = get_crop_profile("maize")
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Dict, List, Optional, Any

from crop_profiles._base import (
    CropProfile,
    DiseaseProfile,
    PestProfile,
    GrowthStageRequirements,
    FertilizerSchedule,
    PlantingWindow,
    NutrientRequirement,
    NaturalRegion,
    SoilType,
    NutrientStatus,
)

# Re-export all base types for backward compatibility
__all__ = [
    "CropProfile",
    "DiseaseProfile",
    "PestProfile",
    "GrowthStageRequirements",
    "FertilizerSchedule",
    "PlantingWindow",
    "NutrientRequirement",
    "NaturalRegion",
    "SoilType",
    "NutrientStatus",
    "CROP_PROFILES",
    "get_crop_profile",
    "get_all_crop_names",
    "get_stage_requirements",
    "get_current_stage_for_crop",
    "get_diseases_for_conditions",
    "get_pests_for_stage",
    "build_crop_context_for_ai",
]


# ---------------------------------------------------------------------------
# Auto-discover and register all crop profile modules
# ---------------------------------------------------------------------------

CROP_PROFILES: Dict[str, CropProfile] = {}


def _discover_profiles() -> None:
    """Import all sibling modules and collect their PROFILE exports."""
    package_path = __path__
    for importer, modname, ispkg in pkgutil.iter_modules(package_path):
        if modname.startswith("_"):
            continue  # skip _base.py and __init__
        try:
            module = importlib.import_module(f".{modname}", package=__name__)
            # Each crop module must export a PROFILE variable
            if hasattr(module, "PROFILE"):
                profile: CropProfile = module.PROFILE
                # Register under lowercase crop name
                key = profile.crop_name.lower().strip()
                CROP_PROFILES[key] = profile
                # Add common aliases
                aliases = getattr(module, "ALIASES", [])
                for alias in aliases:
                    CROP_PROFILES[alias.lower().strip()] = profile
        except Exception as e:
            print(f"⚠️ Failed to load crop profile module '{modname}': {e}")


_discover_profiles()


# ---------------------------------------------------------------------------
# Generic fallback profile for crops without full profiles
# ---------------------------------------------------------------------------

GENERIC_PROFILE = CropProfile(
    crop_name="Generic Crop",
    scientific_name="",
    family="",
    optimal_ph=(5.5, 7.0),
    critical_ph_low=4.5,
    optimal_soil_types=["Well-drained loams", "Sandy loams"],
    avoid_soil_types=["Waterlogged soils", "Saline soils"],
    optimal_temp=(18.0, 32.0),
    critical_temp_low=5.0,
    critical_temp_high=40.0,
    base_temp_gdd=10.0,
    total_water_mm=450.0,
    growth_stages=[
        GrowthStageRequirements(
            stage_name="Establishment",
            stage_code="EST",
            day_range=(0, 21),
            water_kc=0.35,
            water_mm_per_week=15,
            critical_nutrients=["P", "N"],
            key_activities=[
                "Ensure good seedbed preparation",
                "Scout for pests and diseases",
                "Apply basal fertiliser at planting",
            ],
            risks=["Poor emergence", "Seedling pests", "Weed competition"],
            scientific_notes="Establishment phase — root system developing, seedlings vulnerable.",
        ),
        GrowthStageRequirements(
            stage_name="Vegetative Growth",
            stage_code="VEG",
            day_range=(21, 60),
            water_kc=0.70,
            water_mm_per_week=30,
            critical_nutrients=["N", "K"],
            key_activities=[
                "Top-dress nitrogen",
                "Weed control critical",
                "Scout for pests and diseases regularly",
            ],
            risks=["Nutrient deficiency", "Weed competition", "Pest damage"],
            scientific_notes="Active vegetative growth — canopy development and biomass accumulation.",
        ),
        GrowthStageRequirements(
            stage_name="Reproductive / Fruiting",
            stage_code="REPRO",
            day_range=(60, 100),
            water_kc=0.95,
            water_mm_per_week=40,
            critical_nutrients=["K", "P"],
            key_activities=[
                "Ensure adequate moisture — most sensitive period",
                "Monitor for disease pressure",
                "Maintain nutrient supply",
            ],
            risks=["Drought stress", "Disease pressure", "Nutrient deficiency"],
            scientific_notes="Reproductive phase — flowering, fruit set, or grain fill. Maximum water demand.",
        ),
        GrowthStageRequirements(
            stage_name="Maturity & Harvest",
            stage_code="MAT",
            day_range=(100, 140),
            water_kc=0.40,
            water_mm_per_week=15,
            critical_nutrients=[],
            key_activities=[
                "Monitor crop maturity indicators",
                "Plan harvest logistics",
                "Dry to safe moisture content for storage",
            ],
            risks=["Delayed harvest losses", "Storage pest damage"],
            scientific_notes="Senescence and dry-down. Harvest at optimal moisture to minimise losses.",
        ),
    ],
    fertilizer_schedule=FertilizerSchedule(
        basal={
            "product": "Compound D (7:14:7) or crop-specific compound",
            "rate": "200-300 kg/ha",
            "timing": "At planting",
            "scientific_basis": "Phosphorus placement near seed for root development.",
        },
        top_dress_1={
            "product": "Ammonium Nitrate (AN 34.5%) or Urea (46%)",
            "rate": "150-200 kg/ha",
            "timing": "3-5 weeks after planting/transplanting",
            "scientific_basis": "Nitrogen for vegetative growth and canopy development.",
        },
        notes="Consult local Agritex officer for crop-specific fertiliser recommendations.",
    ),
    diseases=[],
    pests=[],
    planting_windows=[
        PlantingWindow(
            region="General Zimbabwe",
            optimal_start="November 1",
            optimal_end="December 15",
            acceptable_start="October 15",
            acceptable_end="January 15",
            notes="Timing varies by crop. Consult local extension for specific planting dates.",
        ),
    ],
    harvest_moisture="Harvest at crop-specific moisture. Consult extension guidelines.",
    storage_conditions="Cool, dry, ventilated. Protect from insects and rodents.",
    post_harvest_notes="Handle carefully to minimise damage. Grade and sort before storage or sale.",
    natural_region_suitability={
        "I": "Consult local extension",
        "IIa": "Consult local extension",
        "IIb": "Consult local extension",
        "III": "Consult local extension",
        "IV": "Consult local extension",
        "V": "Consult local extension",
    },
)


# ---------------------------------------------------------------------------
# Public API — backward-compatible with crop_knowledge.py
# ---------------------------------------------------------------------------

def get_crop_profile(crop_name: str) -> Optional[CropProfile]:
    """Look up the full agronomic profile for a crop.
    Returns the generic fallback if no specific profile exists."""
    profile = CROP_PROFILES.get(crop_name.lower().strip())
    if profile:
        return profile
    # Return a customised generic profile with the crop name
    return None


def get_crop_profile_or_generic(crop_name: str) -> CropProfile:
    """Like get_crop_profile but always returns a profile (generic fallback)."""
    profile = CROP_PROFILES.get(crop_name.lower().strip())
    if profile:
        return profile
    # Clone generic with the actual crop name
    from dataclasses import replace
    return replace(GENERIC_PROFILE, crop_name=crop_name)


def get_all_crop_names() -> List[str]:
    """Return deduplicated list of supported crop names."""
    seen = set()
    names = []
    for profile in CROP_PROFILES.values():
        if profile.crop_name not in seen:
            seen.add(profile.crop_name)
            names.append(profile.crop_name)
    return sorted(names)


def get_stage_requirements(crop_name: str, stage_code: str) -> Optional[GrowthStageRequirements]:
    """Look up requirements for a specific growth stage."""
    profile = get_crop_profile(crop_name)
    if not profile:
        return None
    for stage in profile.growth_stages:
        if stage.stage_code == stage_code:
            return stage
    return None


def get_current_stage_for_crop(crop_name: str, days_since_planting: int) -> Optional[GrowthStageRequirements]:
    """Determine the current growth stage based on days since planting."""
    profile = get_crop_profile_or_generic(crop_name)
    for stage in profile.growth_stages:
        if stage.day_range[0] <= days_since_planting <= stage.day_range[1]:
            return stage
    # Past all defined stages — return last stage
    if profile.growth_stages:
        return profile.growth_stages[-1]
    return None


def get_diseases_for_conditions(
    crop_name: str,
    temperature: Optional[float] = None,
    humidity: Optional[float] = None,
    current_stage: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Evaluate which diseases are currently at risk given weather + stage.
    Returns list of {disease, risk_level, reason, actions}.
    """
    profile = get_crop_profile(crop_name)
    if not profile:
        return []

    risks = []
    for disease in profile.diseases:
        risk_score = 0
        reasons = []

        conditions = disease.favourable_conditions
        # Temperature check
        if temperature is not None:
            t_min = conditions.get("temp_min_c", 0)
            t_max = conditions.get("temp_max_c", 50)
            if t_min <= temperature <= t_max:
                risk_score += 30
                reasons.append(f"Temperature {temperature}°C is in the favourable range ({t_min}-{t_max}°C)")

        # Humidity check
        if humidity is not None:
            h_min = conditions.get("humidity_min", 0)
            if humidity >= h_min:
                risk_score += 30
                reasons.append(f"Humidity {humidity}% exceeds threshold ({h_min}%)")

        # Stage check
        if current_stage:
            for sus_stage in disease.susceptible_stages:
                if sus_stage.lower() in current_stage.lower() or current_stage.lower() in sus_stage.lower():
                    risk_score += 25
                    reasons.append(f"Current stage '{current_stage}' is a susceptible period")
                    break

        # Both temp + humidity = compound risk
        if risk_score >= 60:
            risk_score = min(risk_score + 15, 100)

        if risk_score > 0:
            risk_level = "low" if risk_score < 30 else "moderate" if risk_score < 60 else "high"
            risks.append({
                "disease": disease.name,
                "pathogen": disease.pathogen,
                "risk_level": risk_level,
                "risk_score": risk_score,
                "reasons": reasons,
                "identification": disease.identification_markers[:2],
                "recommended_actions": (
                    disease.chemical_control[:1] if risk_level == "high"
                    else disease.cultural_control[:2]
                ),
                "scouting_tip": disease.symptoms[0] if disease.symptoms else "",
            })

    risks.sort(key=lambda x: x["risk_score"], reverse=True)
    return risks


def get_pests_for_stage(crop_name: str, current_stage: str) -> List[Dict[str, Any]]:
    """Return pests relevant to the current growth stage."""
    profile = get_crop_profile(crop_name)
    if not profile:
        return []

    relevant = []
    for pest in profile.pests:
        for sus_stage in pest.susceptible_stages:
            if sus_stage.lower() in current_stage.lower() or current_stage.lower() in sus_stage.lower():
                relevant.append({
                    "pest": pest.name,
                    "scientific_name": pest.scientific_name,
                    "damage_to_look_for": pest.damage_symptoms[:2],
                    "scouting_protocol": pest.scouting_protocol,
                    "economic_threshold": pest.economic_threshold,
                    "top_control": pest.chemical_control[0]["name"] if pest.chemical_control else "Cultural control",
                })
                break

    return relevant


def build_crop_context_for_ai(
    crop_name: str,
    days_since_planting: int,
    temperature: Optional[float] = None,
    humidity: Optional[float] = None,
    variety_name: Optional[str] = None,
) -> str:
    """
    Build a rich, crop-specific context string to inject into the AI Brain's
    system prompt. This gives the LLM PhD-level knowledge about what the
    farmer's crop needs RIGHT NOW.
    """
    profile = get_crop_profile_or_generic(crop_name)

    stage = get_current_stage_for_crop(crop_name, days_since_planting)
    diseases = get_diseases_for_conditions(crop_name, temperature, humidity,
                                            stage.stage_code if stage else None)
    pests = get_pests_for_stage(crop_name, stage.stage_code if stage else "")

    parts = [f"## Crop Intelligence: {profile.crop_name} ({profile.scientific_name})"]
    if variety_name:
        parts.append(f"**Variety**: {variety_name}")

    parts.append(f"**Optimal pH**: {profile.optimal_ph[0]}-{profile.optimal_ph[1]} "
                 f"(CRITICAL: below {profile.critical_ph_low} causes Al toxicity & P lockup)")
    parts.append(f"**Optimal Temp**: {profile.optimal_temp[0]}-{profile.optimal_temp[1]}°C | "
                 f"Frost risk below {profile.critical_temp_low}°C | Heat stress above {profile.critical_temp_high}°C")
    parts.append(f"**Total Water Need**: {profile.total_water_mm}mm over season")

    if stage:
        parts.append(f"\n### Current Stage: {stage.stage_name} ({stage.stage_code})")
        parts.append(f"**Day {days_since_planting}** (stage window: day {stage.day_range[0]}-{stage.day_range[1]})")
        parts.append(f"**Water Need Now**: Kc={stage.water_kc}, ~{stage.water_mm_per_week}mm/week")
        parts.append(f"**Critical Nutrients**: {', '.join(stage.critical_nutrients) if stage.critical_nutrients else 'None critical at this stage'}")
        parts.append("**Key Activities RIGHT NOW**:")
        for act in stage.key_activities:
            parts.append(f"  - {act}")
        parts.append("**Risks to Watch**:")
        for risk in stage.risks:
            parts.append(f"  - {risk}")
        parts.append(f"**Scientific Basis**: {stage.scientific_notes}")

    if diseases:
        parts.append("\n### Disease Risk Assessment (live)")
        for d in diseases[:3]:
            level_indicator = "HIGH" if d["risk_level"] == "high" else "MODERATE" if d["risk_level"] == "moderate" else "LOW"
            parts.append(f"**{d['disease']}** — Risk: {level_indicator} ({d['risk_score']}/100)")
            for r in d["reasons"]:
                parts.append(f"  - {r}")
            parts.append(f"  - Look for: {d['scouting_tip']}")

    if pests:
        parts.append("\n### Pest Watch (stage-specific)")
        for p in pests[:2]:
            parts.append(f"- **{p['pest']}** ({p['scientific_name']})")
            parts.append(f"  Scout for: {', '.join(p['damage_to_look_for'])}")
            parts.append(f"  Threshold: {p['economic_threshold']}")

    # Fertilizer guidance for current stage
    fert = profile.fertilizer_schedule
    if stage and stage.stage_code in ["VE", "V1-V3", "TRANSPLANT", "EST"]:
        parts.append("\n### Fertilizer: Basal Application")
        parts.append(f"- Product: {fert.basal.get('product')}")
        parts.append(f"- Rate: {fert.basal.get('rate')}")
        parts.append(f"- Why: {fert.basal.get('scientific_basis', '')[:200]}")
    elif stage and stage.stage_code in ["V4-V6", "RAPID", "V1-V6", "VEG"]:
        parts.append("\n### Fertilizer: Top-Dress Window")
        parts.append(f"- Product: {fert.top_dress_1.get('product')}")
        parts.append(f"- Rate: {fert.top_dress_1.get('rate')}")
        parts.append(f"- Why: {fert.top_dress_1.get('scientific_basis', '')[:200]}")

    return "\n".join(parts)
