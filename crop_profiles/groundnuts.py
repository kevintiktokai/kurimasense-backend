"""Groundnuts (Arachis hypogaea) — key legume crop."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List, Dict, Any


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


PROFILE = GROUNDNUT_PROFILE
ALIASES = ["groundnut"]
