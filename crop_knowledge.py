"""
KurimaSense Crop Knowledge Engine
===================================
PhD-level agronomic intelligence for every supported crop.

This module is the **single source of truth** for:
  - Crop-specific nutrient requirements by growth stage
  - Soil pH / EC / texture preferences
  - Pest & disease profiles with identification markers and IPM protocols
  - Fertilizer schedules (basal + top-dress) by natural region
  - Planting window calendars for Zimbabwe
  - Irrigation scheduling (Kc coefficients by growth stage)
  - Post-harvest handling guidelines

Design Principles:
  1. Every recommendation must be variety-aware (e.g. SC 727 vs SC 301)
  2. Every action must have a scientific "why" (physiological basis)
  3. All thresholds come from peer-reviewed or extension-verified data
  4. Zimbabwe Natural Region I-V adjustments built in
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


# ---------------------------------------------------------------------------
# MAIZE (Zea mays) — Zimbabwe's staple
# ---------------------------------------------------------------------------

MAIZE_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Grey Leaf Spot (GLS)",
        pathogen="Cercospora zeae-maydis",
        pathogen_type="fungal",
        symptoms=[
            "Rectangular, grey-tan lesions on lower leaves first",
            "Lesions restricted by leaf veins (gives rectangular shape)",
            "Coalescing lesions reduce photosynthetic area",
            "Premature leaf senescence in severe cases",
        ],
        identification_markers=[
            "Rectangular lesions bounded by veins (key diagnostic feature)",
            "Grey to tan colour with dark borders",
            "Starts on lower canopy and moves upward",
            "Lesions 2-7cm long, 2-4mm wide",
        ],
        favourable_conditions={
            "humidity_min": 80, "temp_min_c": 22, "temp_max_c": 30,
            "leaf_wetness_hours": 12,
            "note": "Humid, warm conditions with prolonged leaf wetness. "
                    "Worse under continuous maize or minimum tillage (residue inoculum)."
        },
        susceptible_stages=["V7-V10", "VT", "R1", "R2"],
        resistant_varieties=["SC 403", "PHB 30G19", "SC 727"],
        susceptible_varieties=["SC 637", "SC 513"],
        chemical_control=[
            {"name": "Amistar Xtra (Azoxystrobin + Cyproconazole)", "rate": "0.4-0.5 L/ha",
             "phi_days": "28", "notes": "Apply at first symptoms or V10-VT preventively"},
            {"name": "Nativo 75 WG (Trifloxystrobin + Tebuconazole)", "rate": "0.3-0.4 kg/ha",
             "phi_days": "28", "notes": "Broad-spectrum strobilurin + triazole"},
            {"name": "Mancozeb 80 WP (contact)", "rate": "2.0-2.5 kg/ha",
             "phi_days": "14", "notes": "Protectant; alternate with systemic fungicides"},
        ],
        biological_control=[
            "Trichoderma-based products on crop residue to accelerate decomposition",
            "Crop rotation (minimum 2-year break from maize)",
        ],
        cultural_control=[
            "Rotate with soybean, groundnut, or sunflower (non-host)",
            "Bury crop residue by ploughing (reduces inoculum 60-80%)",
            "Plant GLS-tolerant varieties in high-risk areas",
            "Avoid late planting which extends exposure during grain-fill",
            "Optimise plant population (don't overcrowd; improves air circulation)",
        ],
        economic_threshold="5% leaf area infected at or before tasseling",
        severity_scale={
            "mild": "< 5% leaf area, lower leaves only",
            "moderate": "5-25% leaf area, reaching ear leaf",
            "severe": "> 25% leaf area, above ear leaf — expect 30-50% yield loss",
        },
    ),
    DiseaseProfile(
        name="Common Rust",
        pathogen="Puccinia sorghi",
        pathogen_type="fungal",
        symptoms=[
            "Small, round to elongate orange-brown pustules on both leaf surfaces",
            "Pustules erupt through epidermis releasing powdery uredospores",
            "Severe infections cause premature drying and lodging",
        ],
        identification_markers=[
            "Orange-brown circular pustules (distinguish from Southern Rust which is smaller/lighter)",
            "Pustules on BOTH upper and lower leaf surfaces",
            "Rupture epidermis — feel rough when rubbed",
        ],
        favourable_conditions={
            "humidity_min": 75, "temp_min_c": 15, "temp_max_c": 25,
            "note": "Cool, humid nights with moderate daytime temps. "
                    "Worse in highlands and irrigated fields."
        },
        susceptible_stages=["V7-V10", "VT", "R1"],
        resistant_varieties=["SC 719", "PHB 30G19"],
        susceptible_varieties=["SC 301", "P2859W"],
        chemical_control=[
            {"name": "Amistar Xtra", "rate": "0.4-0.5 L/ha", "phi_days": "28",
             "notes": "Apply when pustules appear on 50% of lower leaves"},
            {"name": "Propiconazole 250 EC", "rate": "0.5 L/ha", "phi_days": "21",
             "notes": "Systemic triazole; good curative activity"},
        ],
        biological_control=["Resistant variety deployment is primary strategy"],
        cultural_control=[
            "Plant resistant or tolerant varieties",
            "Avoid very early planting in cool, humid regions",
            "Balanced nutrition (K improves resistance)",
        ],
        economic_threshold="Pustules reaching ear leaf before grain-fill",
        severity_scale={
            "mild": "Scattered pustules on lower leaves",
            "moderate": "50%+ leaves with pustules, approaching ear leaf",
            "severe": "Ear leaf and above heavily infected — 20-40% yield loss",
        },
    ),
    DiseaseProfile(
        name="Maize Streak Virus (MSV)",
        pathogen="Maize streak virus (Mastrevirus)",
        pathogen_type="viral",
        symptoms=[
            "Fine, broken yellow-green streaks along leaf veins",
            "Streaks run parallel to midrib",
            "Young plants: severe stunting, no cob formation",
            "Mature plants: reduced ear size",
        ],
        identification_markers=[
            "Discontinuous, fine chlorotic streaks parallel to veins",
            "Distinct from nutrient deficiency (streaks are broken/dotted)",
            "Symptoms appear 7-14 days after leafhopper feeding",
        ],
        favourable_conditions={
            "vector": "Cicadulina mbila (maize leafhopper)",
            "note": "Worse in warm, dry conditions that favour leafhoppers. "
                    "Late-planted crops at highest risk."
        },
        susceptible_stages=["VE", "V1-V3", "V4-V6"],
        resistant_varieties=["SC 403", "SC 637", "SC 727", "PHB 30G19"],
        susceptible_varieties=["Local OPV varieties", "SC 301 (moderate)"],
        chemical_control=[
            {"name": "Thiamethoxam seed treatment (Cruiser)", "rate": "As per seed treatment",
             "phi_days": "N/A", "notes": "Seed treatment; systemic neonicotinoid protects seedling stage"},
            {"name": "Imidacloprid 200 SL", "rate": "350 mL/ha",
             "phi_days": "21", "notes": "Foliar spray against leafhoppers in severe outbreaks"},
        ],
        biological_control=["Encourage natural predators (ladybirds, lacewings)"],
        cultural_control=[
            "Plant MSV-tolerant varieties (most important control)",
            "Plant within optimal window (avoid late planting)",
            "Remove grassy weeds that harbour leafhoppers",
            "Synchronise planting within community to reduce vector pressure",
        ],
        economic_threshold="10% plants showing streak symptoms before V6",
        severity_scale={
            "mild": "< 10% plants affected, symptoms on lower leaves only",
            "moderate": "10-30% plants, some stunting visible",
            "severe": "> 30% plants, significant stunting and yield loss",
        },
    ),
    DiseaseProfile(
        name="Diplodia Ear Rot",
        pathogen="Stenocarpella maydis (Diplodia maydis)",
        pathogen_type="fungal",
        symptoms=[
            "White mycelial growth starting from base of ear",
            "Husks tightly bound to ear, bleached appearance",
            "Kernels lightweight, chalky, and discoloured",
            "Black pycnidia (fruiting bodies) visible on husks and kernels",
        ],
        identification_markers=[
            "White mold starting at ear base (base rot pattern)",
            "Ear feels unusually light",
            "Husks bleached and adhering tightly",
        ],
        favourable_conditions={
            "humidity_min": 70, "temp_min_c": 20, "temp_max_c": 30,
            "note": "Rain or high humidity 2-3 weeks after silking is critical infection period. "
                    "Husk tightness and ear orientation affect susceptibility."
        },
        susceptible_stages=["R2", "R3", "R4"],
        resistant_varieties=["SC 719", "SC 727"],
        susceptible_varieties=["SC 301", "SC 513"],
        chemical_control=[
            {"name": "No effective post-infection fungicide", "rate": "N/A",
             "phi_days": "N/A", "notes": "Prevention through cultural practices is key"},
        ],
        biological_control=["Trichoderma residue treatments"],
        cultural_control=[
            "Rotate with non-host crops (2-year break minimum)",
            "Bury crop residue (primary inoculum source)",
            "Avoid drought stress during grain fill (predisposes ears)",
            "Harvest promptly at physiological maturity",
            "Ensure good ear coverage by husks",
        ],
        economic_threshold="5% ears showing symptoms at dough stage",
        severity_scale={
            "mild": "< 5% ears affected",
            "moderate": "5-20% ears, some mycotoxin risk",
            "severe": "> 20% ears — significant quality/safety concern (aflatoxin risk)",
        },
    ),
]

MAIZE_PESTS: List[PestProfile] = [
    PestProfile(
        name="Fall Armyworm (FAW)",
        scientific_name="Spodoptera frugiperda",
        pest_type="insect",
        identification=[
            "Larvae: green-brown caterpillar, 3-4cm, inverted Y on head capsule",
            "Four dark spots in square pattern on last abdominal segment",
            "Feeds inside whorl; frass (sawdust-like excrement) visible in whorl",
            "Adults: grey-brown moth, 30-38mm wingspan, pale hind wings",
        ],
        damage_symptoms=[
            "Windowpane feeding on young leaves (translucent patches)",
            "Ragged holes in leaves as larvae grow",
            "Whorl damage — deformed, tattered leaves on unfurling",
            "Ear damage — feeds on kernels, entry through silk channel or husk side",
        ],
        life_cycle_notes="Egg to adult: 30-40 days. Female lays 100-200 eggs in masses on leaf underside. "
                         "6 larval instars over 14-21 days. Pupates in soil. Multiple generations per season.",
        favourable_conditions={
            "temp_min_c": 20, "temp_max_c": 35,
            "note": "Warm, humid conditions. Migrates with weather fronts. "
                    "Worse in late-planted and irrigated fields."
        },
        susceptible_stages=["V1-V3", "V4-V6", "V7-V10", "R1"],
        economic_threshold="5% plants with live larvae in whorl (vegetative) or "
                           "2 larvae/ear (reproductive)",
        chemical_control=[
            {"name": "Emamectin benzoate 5 SG (e.g. Proclaim)", "rate": "200 g/ha",
             "phi_days": "14", "notes": "Low-toxicity, targets larvae in whorl. Apply with nozzle directed into whorl."},
            {"name": "Chlorantraniliprole 200 SC (Coragen)", "rate": "150 mL/ha",
             "phi_days": "14", "notes": "IRAC Group 28; excellent residual, low bee toxicity."},
            {"name": "Spinetoram 250 SC (Delegate)", "rate": "200 mL/ha",
             "phi_days": "7", "notes": "Spinosyn class; good efficacy, short PHI."},
            {"name": "Bacillus thuringiensis (Bt) kurstaki", "rate": "0.5-1.0 kg/ha",
             "phi_days": "0", "notes": "Biological option; must target L1-L3 larvae. UV-sensitive; apply late afternoon."},
        ],
        biological_control=[
            "Trichogramma egg parasitoids (preventive releases)",
            "Telenomus remus (egg parasitoid, highly effective)",
            "Bacillus thuringiensis (Bt) sprays for early-instar larvae",
            "Encourage natural enemies: ladybirds, earwigs, spiders, birds",
            "Nuclear polyhedrosis virus (NPV) — specific to Spodoptera",
        ],
        cultural_control=[
            "Early planting to avoid peak moth migration",
            "Push-pull technology (Desmodium + Brachiaria)",
            "Intercrop with legumes to disrupt host-finding",
            "Handpicking larvae in small-scale fields",
            "Destroy crop residue after harvest to reduce pupae",
            "Scout regularly from VE stage; focus on whorl inspection",
        ],
        scouting_protocol="Walk W-pattern through field. Check 20 plants per point (5 points = 100 plants). "
                          "Open whorl; count live larvae. Record % plants infested and larval instar (L1-L6).",
    ),
    PestProfile(
        name="Maize Stalk Borer",
        scientific_name="Busseola fusca",
        pest_type="insect",
        identification=[
            "Larvae: creamy-white with brown head, dark spots along body, up to 4cm",
            "Bore into stems causing 'dead heart' in young plants",
            "Adults: brown moths, 25-35mm wingspan, nocturnal",
        ],
        damage_symptoms=[
            "Dead heart (central whorl leaf dies and can be pulled out)",
            "Small round holes in stems where larvae entered",
            "Frass at entry holes",
            "Stem breakage (lodging) in severe infestations",
            "Tunnelling visible when stem is split",
        ],
        life_cycle_notes="1-2 generations per season. Larvae diapause in old stems "
                         "(overwinter). Spring emergence triggers first-generation attack on new crop.",
        favourable_conditions={
            "temp_min_c": 18, "temp_max_c": 30,
            "note": "Overwinters in crop residue. First-generation attack 3-6 weeks after crop emergence. "
                    "Worse where maize stubble is left standing."
        },
        susceptible_stages=["V1-V3", "V4-V6", "V7-V10"],
        economic_threshold="10% plants with dead heart or bore holes",
        chemical_control=[
            {"name": "Beta-cyfluthrin 2.5 EC + granules in whorl", "rate": "Per label",
             "phi_days": "21", "notes": "Granular application into whorl most effective for borers"},
            {"name": "Chlorantraniliprole 200 SC", "rate": "150 mL/ha",
             "phi_days": "14", "notes": "Systemic; reaches larvae inside stem"},
        ],
        biological_control=[
            "Cotesia sesamiae (larval parasitoid, indigenous to Zimbabwe)",
            "Destroy old maize stalks to eliminate overwintering larvae",
        ],
        cultural_control=[
            "Remove and burn or compost old maize stalks before planting season",
            "Early planting to reduce first-generation overlap",
            "Intercrop with non-host crops",
            "Push-pull technology (Desmodium repels moths)",
        ],
        scouting_protocol="From V2 onwards, check whorls for shothole leaf damage (rows of small holes "
                          "in unfurling leaves — larvae feeding before entering stem). Split suspect stems.",
    ),
    PestProfile(
        name="Grain Weevil (Storage Pest)",
        scientific_name="Sitophilus zeamais",
        pest_type="insect",
        identification=[
            "Small brown-black weevil, 2.5-5mm, with elongated snout",
            "Can fly (unlike S. granarius)",
            "Larvae develop entirely inside grain kernel",
        ],
        damage_symptoms=[
            "Round exit holes in stored grain",
            "Fine flour dust in stored grain",
            "Heating of grain bulk",
            "Weight loss (up to 30-40% in untreated stores)",
        ],
        life_cycle_notes="Female bores hole in kernel, deposits egg, seals with waxy plug. "
                         "Larva feeds inside kernel. 28-35 day cycle at 27°C. "
                         "Can infest grain in the field before harvest.",
        favourable_conditions={
            "temp_min_c": 15, "temp_max_c": 34,
            "humidity_min": 60,
            "note": "Warm, humid storage conditions accelerate reproduction. "
                    "Grain above 13% moisture highly vulnerable."
        },
        susceptible_stages=["R6", "Harvest Ready", "Post-harvest"],
        economic_threshold="1-2 weevils per kg of stored grain",
        chemical_control=[
            {"name": "Actellic Super (Pirimiphos-methyl + Permethrin)", "rate": "50 g/90 kg bag",
             "phi_days": "N/A", "notes": "Admixture dust for stored grain. Most widely used in Zimbabwe."},
            {"name": "Phosphine fumigation (Phostoxin tablets)", "rate": "Per volume",
             "phi_days": "3-5 days aeration", "notes": "Professional use only; sealed storage required."},
        ],
        biological_control=[
            "Diatomaceous earth (inert dust damages insect cuticle)",
            "Hermetic storage bags (PICS bags) — suffocates insects via O2 depletion",
        ],
        cultural_control=[
            "Dry grain to <13% moisture before storage",
            "Use hermetic (airtight) metal silos or PICS bags",
            "Clean stores thoroughly before loading new grain",
            "Harvest promptly at maturity to reduce field infestation",
            "Store in cool, dry place; avoid stacking against walls",
        ],
        scouting_protocol="Sample 10 points in stored grain bulk. Count insects per kg. "
                          "Check for heating (hand-feel or temperature probe).",
    ),
]

MAIZE_GROWTH_STAGES: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Germination & Emergence",
        stage_code="VE",
        day_range=(0, 14),
        water_kc=0.30,
        water_mm_per_week=15,
        critical_nutrients=["P", "Zn"],
        key_activities=[
            "Ensure uniform seed placement at 5-7 cm depth",
            "Scout for cutworms and soil-borne diseases",
            "Apply pre-emergence herbicide (Atrazine + Metolachlor)",
        ],
        risks=["Poor emergence from cold soil (<12°C)", "Cutworm damage", "Seed rot in waterlogged soil"],
        scientific_notes="Phosphorus is critical at germination for root primordia development. "
                         "Zinc activates enzymes for auxin synthesis (shoot elongation). "
                         "Soil temp >12°C required for consistent germination; below 10°C expect poor stands.",
    ),
    GrowthStageRequirements(
        stage_name="Early Vegetative (V1-V3)",
        stage_code="V1-V3",
        day_range=(14, 28),
        water_kc=0.40,
        water_mm_per_week=20,
        critical_nutrients=["N", "P", "Zn"],
        key_activities=[
            "First weeding — critical weed-free period begins",
            "Scout for Fall Armyworm (FAW) in whorls",
            "Scout for Maize Streak Virus (leaf symptoms)",
            "Check plant population; consider gap-filling if <75% stand",
        ],
        risks=["Fall Armyworm (whorl damage)", "Stalk borer (dead heart)", "Weed competition"],
        scientific_notes="Growing point is below soil surface until V5-V6 (protected from frost/hail). "
                         "This is the start of the CRITICAL WEED-FREE PERIOD: "
                         "weeds present V1-V6 cause 30-50% yield reduction (CIMMYT 2024). "
                         "NUE doubles from 19.3→38.7 kg grain/kg N with timely weeding.",
    ),
    GrowthStageRequirements(
        stage_name="Mid Vegetative (V4-V6)",
        stage_code="V4-V6",
        day_range=(28, 42),
        water_kc=0.60,
        water_mm_per_week=30,
        critical_nutrients=["N"],
        key_activities=[
            "TOP-DRESS NITROGEN: Apply AN or Urea (67 kg N/ha for smallholders, 120-150 for commercial)",
            "Complete second weeding before V6",
            "Scout for stalk borers (dead hearts, stem holes)",
            "Scout for FAW — last effective window for whorl applications",
        ],
        risks=["N deficiency (yellowing of lower leaves, V-pattern)", "Stalk borer entry", "GLS onset"],
        scientific_notes="V4-V6 is the TOP-DRESS WINDOW. Ear size determination begins at V5 "
                         "(number of kernel rows set). N demand accelerates sharply. "
                         "Side-dress N should be placed 10-15 cm from stem to avoid root pruning. "
                         "CIMMYT research shows economic optimum is 67 kg N/ha for smallholders "
                         "but NUE can be tripled with timely weeding + correct placement.",
    ),
    GrowthStageRequirements(
        stage_name="Late Vegetative (V7-V10)",
        stage_code="V7-V10",
        day_range=(42, 56),
        water_kc=0.80,
        water_mm_per_week=40,
        critical_nutrients=["N", "K"],
        key_activities=[
            "Scout for GLS (lower leaves — rectangular tan lesions)",
            "Scout for rust (orange-brown pustules)",
            "Consider preventive fungicide if GLS appears in susceptible variety",
            "Second top-dress N if planned (high-potential fields)",
        ],
        risks=["GLS onset in susceptible varieties", "Rust under cool humid conditions", "Drought stress"],
        scientific_notes="Ear length (kernel number per row) is being determined V7-V12. "
                         "Any stress now reduces potential kernel count. "
                         "GLS risk peaks when lower leaves have >12h wetness at 22-30°C. "
                         "Potassium strengthens cell walls and improves disease resistance.",
    ),
    GrowthStageRequirements(
        stage_name="Tasseling",
        stage_code="VT",
        day_range=(56, 70),
        water_kc=1.15,
        water_mm_per_week=55,
        critical_nutrients=["N", "K", "B"],
        key_activities=[
            "DO NOT spray herbicides (extreme sensitivity)",
            "Ensure adequate moisture — most drought-sensitive period",
            "Scout for silk-clipping insects (beetles, earworms)",
            "If GLS is >5% on ear leaf, apply fungicide NOW",
        ],
        risks=["Drought = 40-60% yield loss", "Barren ears from poor pollination", "GLS reaching ear leaf"],
        scientific_notes="VT-R1 is the MAXIMUM WATER DEMAND period. A single day of wilting at silking "
                         "can reduce yield 8%. Pollen viability drops above 35°C. "
                         "Boron is critical for pollen tube growth and kernel set. "
                         "Each silk must be pollinated individually (one silk per kernel).",
    ),
    GrowthStageRequirements(
        stage_name="Silking & Pollination",
        stage_code="R1",
        day_range=(70, 77),
        water_kc=1.15,
        water_mm_per_week=55,
        critical_nutrients=["N", "K", "B"],
        key_activities=[
            "Monitor pollination success (shake tassels; pollen should be visible)",
            "Protect silks from insect damage",
            "Maintain irrigation if available",
        ],
        risks=["Incomplete pollination → tip-back / missing kernels", "Silk clipping by beetles"],
        scientific_notes="ASI (Anthesis-Silking Interval) widens under drought stress. "
                         "If silks emerge >5 days after pollen shed, pollination fails. "
                         "Drought-tolerant varieties (SC 513, SC 403) have shorter ASI.",
    ),
    GrowthStageRequirements(
        stage_name="Grain Fill (R2-R4)",
        stage_code="R2-R4",
        day_range=(77, 115),
        water_kc=0.90,
        water_mm_per_week=45,
        critical_nutrients=["N", "K"],
        key_activities=[
            "Scout for ear rots (Diplodia — white mold at ear base)",
            "Scout for aflatoxin risk (Aspergillus — green-yellow mold on ears)",
            "Monitor for lodging (stalk rot weakening stems)",
            "Do not remove leaves or tillers",
        ],
        risks=["Diplodia ear rot", "Aflatoxin contamination", "Stalk rot and lodging"],
        scientific_notes="Active grain filling — photosynthate from leaves translocates to kernels. "
                         "Leaf loss from disease or hail directly reduces kernel weight. "
                         "Stalk cannibalization occurs if N is limiting (plant remobilises from stalk → lodging risk). "
                         "Black layer formation (R6) signals physiological maturity regardless of kernel moisture.",
    ),
    GrowthStageRequirements(
        stage_name="Maturity & Dry-down",
        stage_code="R5-R6",
        day_range=(115, 145),
        water_kc=0.50,
        water_mm_per_week=20,
        critical_nutrients=[],
        key_activities=[
            "Check for black layer formation (physiological maturity)",
            "Plan harvest logistics; secure storage",
            "Dry grain to <13% moisture to prevent storage pests",
            "Apply Actellic Super dust if using traditional storage",
        ],
        risks=["Field losses from lodging, birds, rodents", "Aflatoxin if delayed harvest in wet conditions"],
        scientific_notes="Kernel moisture at black layer is ~30-35%. Field dry-down rate depends on "
                         "temperature and humidity (typically 0.5-1.0% per day). "
                         "Harvest at 13-14% moisture for safe storage. "
                         "Every day of delay past maturity increases losses 1-2% (birds, rodents, ear drop).",
    ),
]

MAIZE_FERTILIZER = FertilizerSchedule(
    basal={
        "product": "Compound D (7:14:7) or Compound L (5:18:10)",
        "rate": "200-300 kg/ha",
        "timing": "At planting, placed 5 cm beside and 5 cm below seed",
        "nutrients_supplied": {"N": "10-15 kg", "P": "28-54 kg P2O5", "K": "7-10 kg K2O"},
        "scientific_basis": "Phosphorus must be placed near seed (immobile in soil); "
                            "band placement increases P uptake efficiency 3-5x vs broadcast.",
    },
    top_dress_1={
        "product": "Ammonium Nitrate (AN, 34.5% N) or Urea (46% N)",
        "rate": "150-200 kg AN/ha (52-69 kg N) or 100-150 kg Urea/ha (46-69 kg N)",
        "timing": "V4-V6 (28-42 days after planting); before knee height",
        "application": "Side-dress 10-15 cm from stem; cover with soil if using Urea",
        "scientific_basis": "N demand peaks at V8-VT. Early application at V4-V6 ensures N is "
                            "available during rapid vegetative growth and ear size determination. "
                            "CIMMYT economic optimum: 67 kg N/ha for smallholders in NR II-III.",
    },
    top_dress_2={
        "product": "AN or Urea",
        "rate": "100-150 kg AN/ha (35-52 kg N)",
        "timing": "V8-V10 (optional; for high-potential irrigated fields >8 t/ha target)",
        "application": "Side-dress between rows",
        "scientific_basis": "Split application reduces N loss from leaching and volatilisation. "
                            "Second top-dress only economical if yield target exceeds 8 t/ha.",
    },
    foliar={
        "product": "Zinc sulphate (ZnSO4) or Tradecorp Zn EDTA",
        "rate": "2 kg ZnSO4/ha in 200L water",
        "timing": "V3-V6 if Zn deficiency symptoms appear (white/yellow striping on young leaves)",
        "scientific_basis": "Zn deficiency common on high-pH soils (>7.0) and granite sands. "
                            "Zn is cofactor for carbonic anhydrase and tryptophan synthetase (auxin pathway).",
    },
    liming={
        "product": "Agricultural lime (CaCO3) or Dolomitic lime (CaMg(CO3)2)",
        "rate": "1-3 t/ha based on soil test",
        "timing": "Apply 3-6 months before planting; incorporate to 15 cm depth",
        "scientific_basis": "Target pH 5.5-6.5. Below pH 5.0: Al³⁺ toxicity inhibits root growth, "
                            "P becomes locked in Al/Fe phosphates, Mo unavailability affects N fixation in rotational legumes.",
    },
    notes="Total N budget for NR II-III: 100-150 kg N/ha for commercial, 60-80 kg N/ha for smallholder. "
          "P&K based on soil test; granite-derived soils are typically K-sufficient but P-deficient.",
)

MAIZE_PLANTING_WINDOWS: List[PlantingWindow] = [
    PlantingWindow(
        region="Natural Region I (Eastern Highlands)",
        optimal_start="October 15", optimal_end="November 15",
        acceptable_start="October 1", acceptable_end="December 15",
        notes="Reliable early rains; plant early to maximise growing season. "
              "Full-season varieties (SC 727, SC 719) perform best.",
    ),
    PlantingWindow(
        region="Natural Region II (Mashonaland)",
        optimal_start="November 1", optimal_end="November 30",
        acceptable_start="October 20", acceptable_end="December 20",
        notes="Wait for effective planting rains (>25mm in 3 days on moist soil). "
              "Full-season (SC 727) for early planting; medium (SC 637) for late.",
    ),
    PlantingWindow(
        region="Natural Region III (Central Plateau)",
        optimal_start="November 15", optimal_end="December 15",
        acceptable_start="November 1", acceptable_end="December 31",
        notes="Medium-season varieties (SC 637, SC 513) recommended. "
              "Late planting risk: may hit mid-season dry spell during grain fill.",
    ),
    PlantingWindow(
        region="Natural Region IV (Matabeleland)",
        optimal_start="November 20", optimal_end="December 20",
        acceptable_start="November 10", acceptable_end="January 10",
        notes="Short-season / drought-tolerant varieties essential (SC 301, SC 403). "
              "Consider sorghum or pearl millet as alternatives.",
    ),
    PlantingWindow(
        region="Natural Region V (Lowveld)",
        optimal_start="December 1", optimal_end="December 31",
        acceptable_start="November 15", acceptable_end="January 15",
        notes="Maize is MARGINAL here. Sorghum, millet, or irrigated maize only. "
              "If maize: ultra-early SC 301 with 90-100mm supplemental irrigation.",
    ),
]

MAIZE_PROFILE = CropProfile(
    crop_name="Maize",
    scientific_name="Zea mays L.",
    family="Poaceae (Gramineae)",
    optimal_ph=(5.5, 6.8),
    critical_ph_low=5.0,
    optimal_soil_types=["Well-drained loams", "Red clays (fersiallitic)", "Alluvial soils"],
    avoid_soil_types=["Waterlogged soils", "Pure sands (<5% clay)", "Saline soils (>4 dS/m)"],
    optimal_temp=(18.0, 32.0),
    critical_temp_low=10.0,
    critical_temp_high=38.0,
    base_temp_gdd=10.0,
    total_water_mm=500.0,
    growth_stages=MAIZE_GROWTH_STAGES,
    fertilizer_schedule=MAIZE_FERTILIZER,
    diseases=MAIZE_DISEASES,
    pests=MAIZE_PESTS,
    planting_windows=MAIZE_PLANTING_WINDOWS,
    harvest_moisture="Harvest at 20-25% kernel moisture for mechanical; shell-dry to <13% for storage.",
    storage_conditions="Cool (<25°C), dry (<13% moisture), ventilated. Treat with Actellic Super dust. "
                       "PICS bags or metal silos for hermetic storage (no chemical needed).",
    post_harvest_notes="Grade within 48h of shelling. Reject mouldy or discoloured kernels (aflatoxin risk). "
                       "For seed retention: select from best-performing cobs; dry to 12% before storage.",
    natural_region_suitability={
        "I": "Excellent — full-season varieties, 8-15+ t/ha potential",
        "IIa": "Excellent — primary maize belt, 6-12 t/ha",
        "IIb": "Good — 5-10 t/ha with good management",
        "III": "Moderate — medium-season varieties, 3-7 t/ha",
        "IV": "Marginal — short-season only, 2-4 t/ha, high risk",
        "V": "Not recommended without irrigation",
    },
)


# ---------------------------------------------------------------------------
# SOYBEAN (Glycine max)
# ---------------------------------------------------------------------------

SOYBEAN_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Soybean Rust (Asian Soybean Rust)",
        pathogen="Phakopsora pachyrhizi",
        pathogen_type="fungal",
        symptoms=[
            "Small, tan to dark-brown angular lesions on lower leaves",
            "Lesions with 1-2 uredinia (pustules) per lesion",
            "Premature defoliation from lower canopy upward",
            "Severe: complete defoliation and pod abortion",
        ],
        identification_markers=[
            "Tan to reddish-brown lesions with volcano-shaped uredinia on leaf underside",
            "Distinguished from bacterial pustule (no uredinia) and brown spot (circular, not angular)",
        ],
        favourable_conditions={
            "humidity_min": 75, "temp_min_c": 18, "temp_max_c": 28,
            "leaf_wetness_hours": 6,
            "note": "Wind-borne spores; can arrive from distant sources. Worst in warm, humid seasons.",
        },
        susceptible_stages=["R1-R2", "R3-R4", "R5-R6"],
        resistant_varieties=[],
        susceptible_varieties=["Most commercial varieties are susceptible"],
        chemical_control=[
            {"name": "Amistar Xtra", "rate": "0.4 L/ha", "phi_days": "30",
             "notes": "Apply preventively at R1-R2 or at first detection"},
            {"name": "Tebuconazole 250 EC", "rate": "0.5 L/ha", "phi_days": "21",
             "notes": "Good curative; alternate with strobilurin for resistance management"},
        ],
        biological_control=["No effective biological control currently available"],
        cultural_control=[
            "Plant early to escape late-season rust pressure",
            "Early-maturing varieties escape severe infection",
            "Monitor regional rust advisories",
        ],
        economic_threshold="Any rust detected before R5 stage warrants fungicide",
        severity_scale={
            "mild": "< 10% leaf area, lower canopy",
            "moderate": "10-30% leaf area, defoliation beginning",
            "severe": "> 30% — apply fungicide immediately if before R6",
        },
    ),
]

SOYBEAN_PESTS: List[PestProfile] = [
    PestProfile(
        name="Bean Fly (Stem Maggot)",
        scientific_name="Ophiomyia phaseoli",
        pest_type="insect",
        identification=[
            "Tiny (2mm) shiny black fly",
            "Larvae: white maggots mining in stems near soil level",
            "Swollen, cracked stems at base of plant",
        ],
        damage_symptoms=[
            "Wilting and yellowing of seedlings",
            "Swollen, cracked stem base",
            "Adventitious root formation above damage site",
            "Plant death in severe cases (young plants)",
        ],
        life_cycle_notes="Female punctures leaf to lay eggs. Larvae mine through petiole to stem. "
                         "Pupates inside stem. 21-day cycle in warm conditions.",
        favourable_conditions={
            "temp_min_c": 20, "temp_max_c": 30,
            "note": "Worse in late-planted, poorly fertilised crops. Early-planted vigorous crops tolerate better.",
        },
        susceptible_stages=["VE", "V1-V3"],
        economic_threshold="20% plants with stem damage symptoms",
        chemical_control=[
            {"name": "Thiamethoxam seed treatment", "rate": "Per seed label",
             "phi_days": "N/A", "notes": "Most effective; protects critical seedling phase"},
            {"name": "Dimethoate 400 EC", "rate": "500 mL/ha",
             "phi_days": "21", "notes": "Foliar spray at emergence if seed not treated"},
        ],
        biological_control=["Opius parasitoid wasps (natural enemy)"],
        cultural_control=[
            "Seed treatment is most effective control",
            "Early planting into moist soil for vigorous establishment",
            "Adequate phosphorus and potassium for strong roots",
            "Avoid late planting (higher fly pressure)",
        ],
        scouting_protocol="Check stem base of seedlings from VE-V3. Split stems to check for larvae if wilting.",
    ),
]

SOYBEAN_GROWTH_STAGES: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Germination & Emergence",
        stage_code="VE",
        day_range=(0, 10),
        water_kc=0.30,
        water_mm_per_week=15,
        critical_nutrients=["P", "Mo"],
        key_activities=[
            "Inoculate seed with Bradyrhizobium japonicum if field has no soybean history",
            "Plant at 3-5 cm depth in moist soil",
            "Apply pre-emergence herbicide (Metolachlor + Metribuzin)",
        ],
        risks=["Poor nodulation from low pH", "Bean fly damage", "Seed rot in cold/wet soil"],
        scientific_notes="Inoculation is ESSENTIAL for first-time soybean fields. "
                         "Rhizobium needs pH >5.2 and adequate Mo for nitrogenase enzyme. "
                         "At pH <5.0, Al toxicity kills rhizobia AND locks up P and Mo — "
                         "this causes 'pseudo-N deficiency' where plants yellow despite N in soil.",
    ),
    GrowthStageRequirements(
        stage_name="Vegetative (V1-V6)",
        stage_code="V1-V6",
        day_range=(10, 42),
        water_kc=0.50,
        water_mm_per_week=25,
        critical_nutrients=["P", "K", "Mo"],
        key_activities=[
            "Check nodulation at V2-V3: dig up 3-5 plants, slice nodules",
            "Pink/red nodules = ACTIVE N fixation (good)",
            "White/green nodules = INACTIVE (liming/Mo needed)",
            "First weeding critical by V2",
        ],
        risks=["Poor nodulation", "Bean fly", "Weed competition"],
        scientific_notes="Soybean can fix 200-300 kg N/ha with effective nodulation. "
                         "But this ONLY works if pH >5.2, Mo is available, and Bradyrhizobium is present. "
                         "If nodules are white/green at V3, apply 150 g/ha Na₂MoO₄ as foliar spray. "
                         "Do NOT apply N fertiliser to well-nodulated soybean — it suppresses fixation.",
    ),
    GrowthStageRequirements(
        stage_name="Flowering (R1-R2)",
        stage_code="R1-R2",
        day_range=(42, 65),
        water_kc=0.90,
        water_mm_per_week=40,
        critical_nutrients=["K", "B", "S"],
        key_activities=[
            "Maximum water demand begins — irrigate if dry",
            "Scout for soybean rust (lower leaves)",
            "Apply preventive fungicide if rust detected regionally",
        ],
        risks=["Drought = flower abortion", "Soybean rust onset", "Pod borer"],
        scientific_notes="R1-R2 is the CRITICAL PERIOD for water. Drought at flowering causes "
                         "50-80% flower abortion. Soybean flowers for 3-4 weeks (indeterminate types longer). "
                         "Potassium critical for pod retention and seed fill.",
    ),
    GrowthStageRequirements(
        stage_name="Pod Fill (R3-R6)",
        stage_code="R3-R6",
        day_range=(65, 100),
        water_kc=0.80,
        water_mm_per_week=35,
        critical_nutrients=["K", "S"],
        key_activities=[
            "Monitor for pod-sucking bugs (Nezara viridula — green stink bug)",
            "Continue rust monitoring and fungicide programme",
            "Do not cultivate (root disturbance reduces N fixation)",
        ],
        risks=["Stink bug damage (shrivelled beans)", "Rust defoliation", "Drought → small seeds"],
        scientific_notes="Seed oil and protein content determined during R5-R6. "
                         "K deficiency during pod fill reduces oil content. "
                         "S deficiency causes stunted plants with pale green upper leaves.",
    ),
    GrowthStageRequirements(
        stage_name="Maturity (R7-R8)",
        stage_code="R7-R8",
        day_range=(100, 130),
        water_kc=0.30,
        water_mm_per_week=10,
        critical_nutrients=[],
        key_activities=[
            "R7: leaves yellowing, one pod at mature colour",
            "R8: 95% pods at mature colour — ready to harvest",
            "Harvest at 13-14% moisture; avoid delays (shattering losses)",
        ],
        risks=["Shattering if harvest delayed", "Rain damage to drying pods"],
        scientific_notes="Soybean shatters if left beyond R8 in hot/dry conditions. "
                         "Harvest within 7-10 days of R8 to minimise losses.",
    ),
]

SOYBEAN_FERTILIZER = FertilizerSchedule(
    basal={
        "product": "Single Super Phosphate (SSP) or Compound S (7:21:7 +6S)",
        "rate": "200-300 kg/ha Compound S OR 200 kg/ha SSP + 100 kg/ha MOP",
        "timing": "At planting, banded 5 cm below and beside seed",
        "nutrients_supplied": {"P": "42-63 kg P2O5", "K": "7-14 kg K2O", "S": "12-18 kg"},
        "scientific_basis": "Soybean P demand is high for root development and nodulation. "
                            "Sulphur is critical for methionine/cysteine synthesis (protein crops). "
                            "Do NOT apply N to well-inoculated soybean — it suppresses biological N fixation.",
    },
    top_dress_1={
        "product": "Molybdenum (Na2MoO4) foliar spray",
        "rate": "150 g/ha Na2MoO4 in 200L water",
        "timing": "V2-V4 (only if pH <5.5 or nodules are white/green)",
        "application": "Foliar spray; ensure coverage of young leaves",
        "scientific_basis": "Mo is cofactor for nitrogenase enzyme in Rhizobium. "
                            "At pH <5.5, Mo availability drops drastically. "
                            "Foliar Mo is a cheap, highly effective fix for pseudo-N deficiency in acidic soils.",
    },
    top_dress_2=None,
    foliar=None,
    liming={
        "product": "Dolomitic lime (CaMg(CO3)2) preferred for soybean",
        "rate": "2-4 t/ha based on soil test to reach pH 5.8-6.2",
        "timing": "Apply 6+ months before planting; incorporate to 20 cm",
        "scientific_basis": "CRITICAL: pH <5.0 is the #1 yield-limiting factor for soybean in Zimbabwe. "
                            "Al toxicity kills rhizobia, locks up P and Mo. "
                            "Dolomitic lime supplies Mg (needed for chlorophyll). "
                            "UZ/CIMMYT research: liming from pH 4.8→5.8 increased yield 40-60%.",
    },
    notes="DO NOT apply N to well-nodulated soybean. If nodulation fails (white nodules at V3), "
          "apply 50 kg/ha Urea as emergency rescue — but investigate the root cause (pH, inoculant, waterlogging).",
)

SOYBEAN_PROFILE = CropProfile(
    crop_name="Soybean",
    scientific_name="Glycine max (L.) Merr.",
    family="Fabaceae (Leguminosae)",
    optimal_ph=(5.8, 6.5),
    critical_ph_low=5.0,
    optimal_soil_types=["Well-drained loams", "Red clays", "Sandy loams with good organic matter"],
    avoid_soil_types=["Waterlogged soils", "Acidic sands (pH <5.0)", "Saline soils"],
    optimal_temp=(20.0, 30.0),
    critical_temp_low=10.0,
    critical_temp_high=38.0,
    base_temp_gdd=10.0,
    total_water_mm=450.0,
    growth_stages=SOYBEAN_GROWTH_STAGES,
    fertilizer_schedule=SOYBEAN_FERTILIZER,
    diseases=SOYBEAN_DISEASES,
    pests=SOYBEAN_PESTS,
    planting_windows=[
        PlantingWindow(
            region="Natural Region I-II",
            optimal_start="November 15", optimal_end="December 15",
            acceptable_start="November 1", acceptable_end="December 31",
            notes="Soybean is photoperiod-sensitive. Planting after Dec 31 significantly reduces yield. "
                  "Inoculate seed on day of planting (UV kills rhizobia).",
        ),
        PlantingWindow(
            region="Natural Region III-IV",
            optimal_start="November 20", optimal_end="December 20",
            acceptable_start="November 10", acceptable_end="January 5",
            notes="Short-season varieties (SC Squire, SC Safari) for late planting. "
                  "Soybean is marginal in NR IV without supplemental irrigation.",
        ),
    ],
    harvest_moisture="Harvest at 13-14%. Combine at 14% to reduce shatter losses.",
    storage_conditions="Cool, dry, <12% moisture. Prone to moulding if stored wet.",
    post_harvest_notes="Market premium for food-grade (clean, unbroken, uniform colour). "
                       "Oil content typically 18-22%; protein 38-42%.",
    natural_region_suitability={
        "I": "Excellent — well-suited for rotation with maize",
        "IIa": "Excellent — primary soybean belt",
        "IIb": "Good",
        "III": "Moderate — short-season varieties recommended",
        "IV": "Marginal — needs irrigation or drought-tolerant varieties",
        "V": "Not recommended",
    },
)


# ---------------------------------------------------------------------------
# TOBACCO (Nicotiana tabacum) — Zimbabwe's top export crop
# ---------------------------------------------------------------------------

TOBACCO_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Frog-eye Leaf Spot (Cercospora)",
        pathogen="Cercospora nicotianae",
        pathogen_type="fungal",
        symptoms=[
            "Circular, brown spots with white/grey centre (frog-eye appearance)",
            "Dark brown margin around light centre",
            "Spots enlarge and coalesce in wet conditions",
            "Lower leaves affected first",
        ],
        identification_markers=[
            "Concentric ring pattern with light centre — the 'frog-eye'",
            "Distinct from Alternaria (which has target-board pattern with more rings)",
        ],
        favourable_conditions={
            "humidity_min": 80, "temp_min_c": 20, "temp_max_c": 30,
            "note": "Prolonged leaf wetness, dense canopy, poor air circulation.",
        },
        susceptible_stages=["Rapid Growth", "Topping Stage", "Ripening"],
        resistant_varieties=["KRK75"],
        susceptible_varieties=["KRK26R", "T78"],
        chemical_control=[
            {"name": "Mancozeb 80 WP", "rate": "2.0 kg/ha", "phi_days": "14",
             "notes": "Protectant; apply before infection period"},
            {"name": "Iprodione 50 WP (Rovral)", "rate": "1.0 kg/ha", "phi_days": "14",
             "notes": "Good for Cercospora; alternate with contact fungicide"},
        ],
        biological_control=["Adequate air circulation through proper spacing"],
        cultural_control=[
            "Maintain row spacing (1.2m between rows, 0.45m in-row)",
            "Remove infected lower leaves (priming)",
            "Avoid overhead irrigation",
            "Crop rotation (2-year break from tobacco)",
        ],
        economic_threshold="3-5% leaf area affected warrants fungicide",
        severity_scale={
            "mild": "Scattered spots on lower leaves",
            "moderate": "Spots reaching middle leaves, 5-15% area",
            "severe": "Upper leaves affected; quality downgrade certain",
        },
    ),
]

TOBACCO_GROWTH_STAGES: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Transplant & Establishment",
        stage_code="TRANSPLANT",
        day_range=(0, 21),
        water_kc=0.40,
        water_mm_per_week=20,
        critical_nutrients=["P", "N"],
        key_activities=[
            "Transplant 6-8 week-old seedlings",
            "Water in well; apply starter fertiliser (Compound S banded)",
            "Replant gaps within 7 days",
            "Scout for cutworms and aphids",
        ],
        risks=["Transplant shock", "Cutworm damage", "Root knot nematode"],
        scientific_notes="Phosphorus critical for root re-establishment. "
                         "Do not over-apply N at transplant — promotes rank growth and delayed ripening.",
    ),
    GrowthStageRequirements(
        stage_name="Rapid Growth",
        stage_code="RAPID",
        day_range=(21, 56),
        water_kc=0.80,
        water_mm_per_week=35,
        critical_nutrients=["N", "K"],
        key_activities=[
            "Top-dress N at 4 weeks post-transplant",
            "Weed control — tobacco is very sensitive to weed competition",
            "Begin suckering as auxiliary buds develop",
            "Scout for aphids, budworm, and leaf spot diseases",
        ],
        risks=["N deficiency (pale green leaves)", "Aphid-transmitted viruses", "Budworm"],
        scientific_notes="Rapid N uptake phase. Over-applying N creates thick, dark-green leaves that "
                         "cure poorly and reduce quality grade. Target: 80-100 kg N/ha total. "
                         "K is critical for leaf quality (body, texture, colour of cured leaf).",
    ),
    GrowthStageRequirements(
        stage_name="Topping",
        stage_code="TOPPING",
        day_range=(56, 70),
        water_kc=0.85,
        water_mm_per_week=38,
        critical_nutrients=["K"],
        key_activities=[
            "Top (remove flower head) when 50% of plants are at button/early flower",
            "Apply sucker control chemical (Fluprimidol / Off-Shoot T)",
            "Continue suckering manually as needed",
            "Reduce N irrigation/fertiliser — excess delays ripening",
        ],
        risks=["Late topping reduces leaf weight", "Sucker regrowth", "Frog-eye in humid conditions"],
        scientific_notes="Topping redirects photosynthate from seed production to leaf expansion. "
                         "Each day of delayed topping costs ~50 kg/ha leaf yield. "
                         "Suckers must be removed within 7 days of topping to prevent nutrient diversion.",
    ),
    GrowthStageRequirements(
        stage_name="Ripening",
        stage_code="RIPEN",
        day_range=(70, 100),
        water_kc=0.50,
        water_mm_per_week=20,
        critical_nutrients=[],
        key_activities=[
            "Monitor leaf ripeness (yellow-green, smooth surface, downward-curling tips)",
            "Harvest ripe leaves from bottom upward (priming)",
            "Cure: 3-5 days yellowing → 3-5 days colour-fixing → 5-7 days drying",
            "Maintain barn temperature 35-40°C (yellowing) → 55-60°C (killing out)",
        ],
        risks=["Over-ripe leaves (poor colour, quality downgrade)", "Barn rot in humid curing"],
        scientific_notes="Leaf ripening is marked by chlorophyll degradation and carotenoid accumulation. "
                         "Starch converts to sugars during curing (important for flavour). "
                         "KRK26R ripens faster (lemon style); KRK75 slower (mahogany style). "
                         "Curing temperature control is the #1 determinant of leaf grade.",
    ),
]

TOBACCO_PROFILE = CropProfile(
    crop_name="Tobacco",
    scientific_name="Nicotiana tabacum L.",
    family="Solanaceae",
    optimal_ph=(5.5, 6.0),
    critical_ph_low=5.0,
    optimal_soil_types=["Light sandy loams (granite sands)", "Well-drained soils with low N residue"],
    avoid_soil_types=["Heavy clays (poor drainage)", "High-N soils (ex-legume lands in first year)"],
    optimal_temp=(20.0, 30.0),
    critical_temp_low=13.0,
    critical_temp_high=35.0,
    base_temp_gdd=10.0,
    total_water_mm=450.0,
    growth_stages=TOBACCO_GROWTH_STAGES,
    fertilizer_schedule=FertilizerSchedule(
        basal={
            "product": "Compound S (7:21:7 +6S)",
            "rate": "400-500 kg/ha",
            "timing": "Banded at transplanting",
            "nutrients_supplied": {"N": "28-35 kg", "P": "84-105 kg P2O5", "K": "28-35 kg K2O", "S": "24-30 kg"},
            "scientific_basis": "Tobacco P requirement is very high for root establishment post-transplant.",
        },
        top_dress_1={
            "product": "Ammonium Nitrate (AN 34.5%)",
            "rate": "100-150 kg/ha (35-52 kg N)",
            "timing": "3-4 weeks post-transplant",
            "application": "Ring around plant base, 10 cm away from stem",
            "scientific_basis": "N promotes leaf area expansion. Total season N: 80-100 kg/ha. "
                                "Over-application degrades leaf quality and curing colour.",
        },
        top_dress_2={
            "product": "Muriate of Potash (MOP 60%)",
            "rate": "100-150 kg/ha (60-90 kg K2O)",
            "timing": "4-5 weeks post-transplant",
            "application": "Side-dress; do NOT mix with N application",
            "scientific_basis": "K is the QUALITY element in tobacco. Improves leaf body, burn quality, "
                                "and cured leaf colour. K-deficient leaves cure poorly (buff/brown instead of lemon/orange).",
        },
        foliar=None,
        liming={
            "product": "Calcitic lime (NOT dolomitic — excess Mg darkens cured leaf)",
            "rate": "1-2 t/ha based on soil test",
            "timing": "6 months before transplanting",
            "scientific_basis": "Target pH 5.5-6.0. Dolomitic lime should be avoided as excess Mg "
                                "causes undesirable dark-green cured leaf colour.",
        },
        notes="Chloride-sensitive crop: avoid KCl near transplanting. Use K2SO4 if available. "
              "Total N must not exceed 100 kg/ha for quality flue-cured leaf.",
    ),
    diseases=TOBACCO_DISEASES,
    pests=[],  # Can be expanded
    planting_windows=[
        PlantingWindow(
            region="All tobacco regions (NR I-III)",
            optimal_start="September 15", optimal_end="October 15",
            acceptable_start="September 1", acceptable_end="November 15",
            notes="Seedbed: sow June-July. Transplant after effective rains. "
                  "Early transplanting gives better prices (first floors auction early).",
        ),
    ],
    harvest_moisture="Harvest ripe leaves at full yellow colour. Cure to 11-12% moisture.",
    storage_conditions="Grade, tie in hands, bale. Store in cool, dry rooms. Avoid moisture reabsorption.",
    post_harvest_notes="Sort into grades: L (lemon), O (orange), M (mahogany), G (greenish), B (body). "
                       "Zimbabwe Tobacco Industry & Marketing Board (TIMB) grades determine price.",
    natural_region_suitability={
        "I": "Good — adequate rainfall but may be too cool for rapid growth",
        "IIa": "Excellent — primary tobacco belt (Mashonaland)",
        "IIb": "Good",
        "III": "Moderate — needs supplemental irrigation",
        "IV": "Marginal — only with full irrigation",
        "V": "Not suitable",
    },
)


# ---------------------------------------------------------------------------
# GROUNDNUTS (Arachis hypogaea)
# ---------------------------------------------------------------------------

GROUNDNUT_PROFILE = CropProfile(
    crop_name="Groundnuts",
    scientific_name="Arachis hypogaea L.",
    family="Fabaceae",
    optimal_ph=(5.5, 6.5),
    critical_ph_low=5.0,
    optimal_soil_types=["Light sandy loams (easy pegging/harvesting)", "Well-drained soils"],
    avoid_soil_types=["Heavy clays (difficult harvesting, pod staining)", "Waterlogged soils"],
    optimal_temp=(25.0, 32.0),
    critical_temp_low=15.0,
    critical_temp_high=38.0,
    base_temp_gdd=13.0,
    total_water_mm=400.0,
    growth_stages=[
        GrowthStageRequirements(
            stage_name="Germination & Emergence",
            stage_code="VE",
            day_range=(0, 14),
            water_kc=0.30,
            water_mm_per_week=15,
            critical_nutrients=["P", "Ca"],
            key_activities=["Plant at 5-7 cm depth", "Apply gypsum at planting if Ca is low",
                            "Scout for termites and cutworms"],
            risks=["Poor emergence in cold soil", "Termite damage to seed"],
            scientific_notes="Calcium is uniquely critical for groundnuts — the peg must absorb Ca "
                             "directly from soil for proper pod development. "
                             "Apply gypsum (CaSO4, 400-500 kg/ha) if soil Ca <400 ppm.",
        ),
        GrowthStageRequirements(
            stage_name="Vegetative Growth",
            stage_code="VEG",
            day_range=(14, 40),
            water_kc=0.60,
            water_mm_per_week=25,
            critical_nutrients=["P", "Mo"],
            key_activities=["Inoculate with Bradyrhizobium if new field", "Weed control — groundnut is slow to cover",
                            "Check nodulation at 30 days"],
            risks=["Weed competition (slow canopy closure)", "Rosette virus (aphid-transmitted)"],
            scientific_notes="Like soybean, groundnut fixes N via Rhizobium. "
                             "Effective nodulation requires pH >5.2 and Mo availability.",
        ),
        GrowthStageRequirements(
            stage_name="Flowering & Pegging",
            stage_code="R1-PEG",
            day_range=(40, 70),
            water_kc=0.85,
            water_mm_per_week=38,
            critical_nutrients=["Ca", "K", "B"],
            key_activities=["Apply gypsum in pod zone if not done at planting",
                            "Do NOT cultivate — damages pegs",
                            "Ensure adequate moisture for peg penetration"],
            risks=["Ca deficiency = empty pods (pops)", "Drought stops peg elongation",
                   "Leaf spot diseases (early leaf spot, late leaf spot)"],
            scientific_notes="The peg (gynophore) grows downward from the flower into soil. "
                             "Ca must be in the TOP 5 cm of soil — pegs absorb Ca directly (not via roots). "
                             "This is why gypsum is applied to the pod zone, not deep-banded.",
        ),
        GrowthStageRequirements(
            stage_name="Pod Fill",
            stage_code="R3-R6",
            day_range=(70, 100),
            water_kc=0.70,
            water_mm_per_week=30,
            critical_nutrients=["K"],
            key_activities=["Monitor for leaf spot and rust", "Avoid waterlogging (aflatoxin risk)",
                            "Begin planning harvest logistics"],
            risks=["Aflatoxin (Aspergillus) if drought stress followed by late rain",
                   "Leaf spot defoliation reducing pod fill"],
            scientific_notes="Aflatoxin risk is highest when drought stress cracks pods, "
                             "followed by late-season rains that favour Aspergillus colonisation.",
        ),
        GrowthStageRequirements(
            stage_name="Maturity & Harvest",
            stage_code="R7-R8",
            day_range=(100, 130),
            water_kc=0.30,
            water_mm_per_week=10,
            critical_nutrients=[],
            key_activities=["Test maturity: shell pods; dark inner pericarp = mature",
                            "Lift, windrow, and dry to <8% kernel moisture",
                            "Avoid soil contact during drying (aflatoxin)"],
            risks=["Over-maturity (in-shell sprouting)", "Aflatoxin from soil contact"],
            scientific_notes="Harvest when 75% of pods show dark inner pericarp. "
                             "Dry on raised racks, not on bare soil. Target <8% kernel moisture for safe storage.",
        ),
    ],
    fertilizer_schedule=FertilizerSchedule(
        basal={
            "product": "Single Super Phosphate (SSP) + Gypsum",
            "rate": "200 kg/ha SSP + 400-500 kg/ha Gypsum",
            "timing": "At planting",
            "nutrients_supplied": {"P": "36 kg P2O5", "Ca": "80-100 kg", "S": "40-50 kg"},
            "scientific_basis": "SSP supplies P+S+Ca. Gypsum supplies Ca to pod zone without raising pH excessively.",
        },
        top_dress_1={
            "product": "Gypsum (if not applied at planting)",
            "rate": "400-500 kg/ha",
            "timing": "At flowering/pegging",
            "application": "Broadcast over row; rain will wash into pod zone",
            "scientific_basis": "Ca in pod zone is NON-NEGOTIABLE for groundnut. "
                                "Peg absorbs Ca directly; root-absorbed Ca does not reach developing kernels.",
        },
        liming={
            "product": "Calcitic lime",
            "rate": "1-2 t/ha if pH <5.5",
            "timing": "6 months before planting",
            "scientific_basis": "Target pH 5.5-6.5. Gypsum does NOT raise pH; lime does.",
        },
        notes="Groundnuts do NOT need N fertiliser if well-inoculated. Over-liming (pH >7.0) "
              "causes micronutrient deficiencies (Mn, Fe, Zn).",
    ),
    diseases=[
        DiseaseProfile(
            name="Early Leaf Spot",
            pathogen="Cercospora arachidicola",
            pathogen_type="fungal",
            symptoms=["Brown spots with yellow halo on upper leaf surface",
                      "Spots circular, 1-10mm diameter"],
            identification_markers=["Spots predominantly on UPPER leaf surface (vs Late Leaf Spot on lower)"],
            favourable_conditions={"humidity_min": 80, "temp_min_c": 20, "temp_max_c": 28},
            susceptible_stages=["Vegetative Growth", "Flowering & Pegging", "Pod Fill"],
            resistant_varieties=["Nyanda"],
            susceptible_varieties=["Natal Common"],
            chemical_control=[
                {"name": "Chlorothalonil (Bravo) 500 SC", "rate": "2.0 L/ha", "phi_days": "14",
                 "notes": "Broad-spectrum protectant; apply at 14-day intervals from 40 DAP"},
            ],
            biological_control=["Crop rotation"],
            cultural_control=["Rotate with cereals (2-year break)", "Bury crop residue", "Avoid overhead irrigation"],
            economic_threshold="20% leaf area infected before R5",
            severity_scale={"mild": "< 10% leaf area", "moderate": "10-30%", "severe": "> 30% with defoliation"},
        ),
    ],
    pests=[],
    planting_windows=[
        PlantingWindow(
            region="Natural Region I-III",
            optimal_start="November 15", optimal_end="December 15",
            acceptable_start="November 1", acceptable_end="January 5",
            notes="Plant into moist soil. Ensure seed is treated with fungicide (Thiram) and inoculated.",
        ),
    ],
    harvest_moisture="Lift at 75% pod maturity. Dry kernels to <8% for safe storage.",
    storage_conditions="Store shelled or unshelled at <8% moisture, <25°C. Hermetic storage ideal.",
    post_harvest_notes="Sort and remove damaged/mouldy kernels (aflatoxin). "
                       "Confectionery grade (Makulu Red) commands premium prices.",
    natural_region_suitability={
        "I": "Good", "IIa": "Excellent", "IIb": "Good", "III": "Good",
        "IV": "Moderate — drought-tolerant varieties only", "V": "Not recommended",
    },
)


# ---------------------------------------------------------------------------
# Master crop registry — single lookup for the entire system
# ---------------------------------------------------------------------------

CROP_PROFILES: Dict[str, CropProfile] = {
    "maize": MAIZE_PROFILE,
    "soybean": SOYBEAN_PROFILE,
    "soybeans": SOYBEAN_PROFILE,
    "tobacco": TOBACCO_PROFILE,
    "groundnuts": GROUNDNUT_PROFILE,
    "groundnut": GROUNDNUT_PROFILE,
}


def get_crop_profile(crop_name: str) -> Optional[CropProfile]:
    """Look up the full agronomic profile for a crop."""
    return CROP_PROFILES.get(crop_name.lower().strip())


def get_all_crop_names() -> List[str]:
    """Return deduplicated list of supported crop names."""
    seen = set()
    names = []
    for profile in CROP_PROFILES.values():
        if profile.crop_name not in seen:
            seen.add(profile.crop_name)
            names.append(profile.crop_name)
    return names


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
    profile = get_crop_profile(crop_name)
    if not profile:
        return None
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
    profile = get_crop_profile(crop_name)
    if not profile:
        return f"No detailed profile available for '{crop_name}'. Provide general agronomic advice."

    stage = get_current_stage_for_crop(crop_name, days_since_planting)
    diseases = get_diseases_for_conditions(crop_name, temperature, humidity,
                                            stage.stage_code if stage else None)
    pests = get_pests_for_stage(crop_name, stage.stage_code if stage else "")

    parts = [f"## 🌱 Crop Intelligence: {profile.crop_name} ({profile.scientific_name})"]
    if variety_name:
        parts.append(f"**Variety**: {variety_name}")

    parts.append(f"**Optimal pH**: {profile.optimal_ph[0]}-{profile.optimal_ph[1]} "
                 f"(CRITICAL: below {profile.critical_ph_low} causes Al toxicity & P lockup)")
    parts.append(f"**Optimal Temp**: {profile.optimal_temp[0]}-{profile.optimal_temp[1]}°C | "
                 f"Frost risk below {profile.critical_temp_low}°C | Heat stress above {profile.critical_temp_high}°C")
    parts.append(f"**Total Water Need**: {profile.total_water_mm}mm over season")

    if stage:
        parts.append(f"\n### 📊 Current Stage: {stage.stage_name} ({stage.stage_code})")
        parts.append(f"**Day {days_since_planting}** (stage window: day {stage.day_range[0]}-{stage.day_range[1]})")
        parts.append(f"**Water Need Now**: Kc={stage.water_kc}, ~{stage.water_mm_per_week}mm/week")
        parts.append(f"**Critical Nutrients**: {', '.join(stage.critical_nutrients) if stage.critical_nutrients else 'None critical at this stage'}")
        parts.append(f"**Key Activities RIGHT NOW**:")
        for act in stage.key_activities:
            parts.append(f"  - {act}")
        parts.append(f"**Risks to Watch**:")
        for risk in stage.risks:
            parts.append(f"  - ⚠️ {risk}")
        parts.append(f"**Scientific Basis**: {stage.scientific_notes}")

    if diseases:
        parts.append(f"\n### 🦠 Disease Risk Assessment (live)")
        for d in diseases[:3]:
            emoji = "🔴" if d["risk_level"] == "high" else "🟡" if d["risk_level"] == "moderate" else "🟢"
            parts.append(f"{emoji} **{d['disease']}** — Risk: {d['risk_level'].upper()} ({d['risk_score']}/100)")
            for r in d["reasons"]:
                parts.append(f"  - {r}")
            parts.append(f"  - Look for: {d['scouting_tip']}")

    if pests:
        parts.append(f"\n### 🐛 Pest Watch (stage-specific)")
        for p in pests[:2]:
            parts.append(f"- **{p['pest']}** ({p['scientific_name']})")
            parts.append(f"  Scout for: {', '.join(p['damage_to_look_for'])}")
            parts.append(f"  Threshold: {p['economic_threshold']}")

    # Fertilizer guidance for current stage
    fert = profile.fertilizer_schedule
    if stage and stage.stage_code in ["VE", "V1-V3", "TRANSPLANT"]:
        parts.append(f"\n### 🧪 Fertilizer: Basal Application")
        parts.append(f"- Product: {fert.basal.get('product')}")
        parts.append(f"- Rate: {fert.basal.get('rate')}")
        parts.append(f"- Why: {fert.basal.get('scientific_basis', '')[:200]}")
    elif stage and stage.stage_code in ["V4-V6", "RAPID", "V1-V6"]:
        parts.append(f"\n### 🧪 Fertilizer: Top-Dress Window")
        parts.append(f"- Product: {fert.top_dress_1.get('product')}")
        parts.append(f"- Rate: {fert.top_dress_1.get('rate')}")
        parts.append(f"- Why: {fert.top_dress_1.get('scientific_basis', '')[:200]}")

    return "\n".join(parts)
