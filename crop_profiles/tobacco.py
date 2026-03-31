"""Tobacco (Nicotiana tabacum) — Zimbabwe's top export crop."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List, Optional, Dict, Any


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


PROFILE = TOBACCO_PROFILE
ALIASES = []
