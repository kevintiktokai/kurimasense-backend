"""Soybean (Glycine max) — key rotational legume."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List


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


PROFILE = SOYBEAN_PROFILE
ALIASES = ["soybeans", "soya", "soya beans"]
