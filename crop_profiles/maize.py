"""Maize (Zea mays) — Zimbabwe's staple grain."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List


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


PROFILE = MAIZE_PROFILE
ALIASES = ["corn", "mealies"]
