"""Sesame (Sesamum indicum) — Drought-tolerant oilseed crop, emerging cash crop for smallholders in Zimbabwe's drier regions."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List


SESAME_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Cercospora Leaf Spot",
        pathogen="Cercospora sesami",
        pathogen_type="fungal",
        symptoms=[
            "Angular to irregular brown spots on leaves with grey-brown centres",
            "Dark brown to purplish margins around lesions",
            "Premature defoliation starting from lower leaves",
            "Reduced photosynthetic area affecting seed fill",
        ],
        identification_markers=[
            "Angular lesions bounded by leaf veins (diagnostic)",
            "Grey-brown centre with darker margin",
            "Starts on older lower leaves and progresses upward",
            "Conidia visible under hand lens on lesion surface in humid conditions",
        ],
        favourable_conditions={
            "humidity_min": 80, "temp_min_c": 25, "temp_max_c": 32,
            "note": "Warm, humid conditions with frequent dew. Seed-borne inoculum "
                    "and crop residue from previous sesame crops are primary sources. "
                    "Severity increases with dense planting and poor air circulation."
        },
        susceptible_stages=["Flowering", "Capsule Fill"],
        resistant_varieties=["IETC 32 (moderate tolerance)"],
        susceptible_varieties=["Local unimproved landraces"],
        chemical_control=[
            {"name": "Mancozeb 800 WP", "rate": "2.0 kg/ha",
             "phi_days": "14", "notes": "Protectant; apply at first symptoms, 10-14 day intervals"},
            {"name": "Carbendazim 500 SC", "rate": "0.5 L/ha",
             "phi_days": "14", "notes": "Systemic; alternate with mancozeb for resistance management"},
        ],
        biological_control=[
            "Trichoderma-based seed treatment reduces seed-borne inoculum",
            "Bacillus subtilis foliar applications as preventive measure",
        ],
        cultural_control=[
            "Rotate with cereals for 2-3 years to break disease cycle",
            "Use certified or hot-water treated seed",
            "Adequate plant spacing (30-45 cm between rows) for air circulation",
            "Remove and destroy crop residues after harvest",
            "Avoid excessive nitrogen which promotes dense, susceptible canopy",
        ],
        economic_threshold="10% of leaf area affected on middle canopy leaves",
        severity_scale={
            "mild": "< 10% leaf area on lower leaves only",
            "moderate": "10-25% leaf area affected, reaching middle canopy",
            "severe": "> 25% leaf area affected, premature defoliation, seed fill compromised",
        },
    ),
    DiseaseProfile(
        name="Bacterial Leaf Spot",
        pathogen="Pseudomonas syringae pv. sesami",
        pathogen_type="bacterial",
        symptoms=[
            "Small, angular, water-soaked spots on leaves",
            "Lesions turn brown-black and may merge into large necrotic patches",
            "Spots may be surrounded by yellow halo",
            "In severe cases, leaf distortion and petiole lesions",
        ],
        identification_markers=[
            "Water-soaked appearance of fresh lesions (best seen in morning)",
            "Angular shape following vein boundaries",
            "No fungal sporulation on lesion surface (distinguishes from Cercospora)",
            "Bacterial streaming visible under microscope from fresh lesion in water drop",
        ],
        favourable_conditions={
            "humidity_min": 85, "temp_min_c": 25, "temp_max_c": 35,
            "note": "Warm, rainy weather with wind-driven rain spreading bacteria. "
                    "Seed-borne pathogen; primary infection from contaminated seed."
        },
        susceptible_stages=["Vegetative", "Flowering"],
        resistant_varieties=[],
        susceptible_varieties=["Most varieties susceptible; severity varies"],
        chemical_control=[
            {"name": "Copper hydroxide 770 WP", "rate": "2.0 kg/ha",
             "phi_days": "7", "notes": "Bactericide; preventive application before wet weather"},
        ],
        biological_control=[
            "Bacillus subtilis seed treatment",
            "Pseudomonas fluorescens as antagonist on leaf surfaces",
        ],
        cultural_control=[
            "Use disease-free seed from reputable sources",
            "Hot-water seed treatment (52°C for 30 minutes) kills seed-borne bacteria",
            "Avoid working in crop when foliage is wet",
            "Rotate away from sesame for 2+ years",
            "Remove volunteer sesame plants that harbour inoculum",
        ],
        economic_threshold="First appearance of water-soaked lesions during wet periods",
        severity_scale={
            "mild": "Scattered lesions on < 10% of plants",
            "moderate": "Lesions on 10-30% of plants, some leaf necrosis",
            "severe": "> 30% plants affected with significant defoliation",
        },
    ),
    DiseaseProfile(
        name="Charcoal Rot",
        pathogen="Macrophomina phaseolina",
        pathogen_type="fungal",
        symptoms=[
            "Premature wilting of plants, often one-sided initially",
            "Grey-black discolouration of stem base and roots",
            "Stem tissue shredded with visible microsclerotia (tiny black dots) in pith",
            "Capsules fail to fill; premature drying of plants",
        ],
        identification_markers=[
            "Dark stem base with shredded cortex tissue",
            "Microsclerotia (< 0.5mm black dots) visible in stem pith (use hand lens)",
            "Plants pull out easily — root system partially decayed",
            "Distinct from Fusarium wilt by microsclerotia and shredded tissue",
        ],
        favourable_conditions={
            "temp_min_c": 28, "temp_max_c": 40,
            "soil_moisture": "drought-stressed plants most susceptible",
            "note": "Hot, dry conditions during flowering and capsule fill. "
                    "Soil-borne — microsclerotia survive for years. "
                    "Wide host range including maize, sorghum, soybean, groundnut."
        },
        susceptible_stages=["Flowering", "Capsule Fill", "Maturation"],
        resistant_varieties=[],
        susceptible_varieties=["All varieties susceptible under stress conditions"],
        chemical_control=[
            {"name": "Thiram 80 WP (seed treatment)", "rate": "3 g/kg seed",
             "phi_days": "N/A", "notes": "Protects seedling establishment; does not prevent later stem infection"},
        ],
        biological_control=[
            "Trichoderma viride soil application reduces soil inoculum",
            "Bacillus subtilis seed treatment provides early protection",
        ],
        cultural_control=[
            "Avoid planting sesame after sesame, soybean, or groundnut in sequence",
            "Maintain adequate soil moisture — supplemental irrigation during dry spells at flowering",
            "Increase organic matter to improve soil water-holding capacity",
            "Optimum plant population — avoid overcrowding that increases competition for moisture",
            "Crop residue removal and deep ploughing to bury microsclerotia",
        ],
        economic_threshold="5% of plants showing stem base discolouration during flowering",
        severity_scale={
            "mild": "< 5% plants wilting, scattered in field",
            "moderate": "5-20% plants affected, often in patches on lighter soils",
            "severe": "> 20% plant mortality, significant yield loss, consider early harvest",
        },
    ),
]

SESAME_PESTS: List[PestProfile] = [
    PestProfile(
        name="Sesame Webworm",
        scientific_name="Antigastra catalaunalis",
        pest_type="insect",
        identification=[
            "Adult: small moth (15-20mm wingspan) with pale brownish wings",
            "Larva: pale green with dark head, 15-20mm, webbing leaves and capsules",
            "Pupa: in soil or webbed leaf debris",
        ],
        damage_symptoms=[
            "Larvae web together terminal leaves and flower buds",
            "Bore into capsules and feed on developing seeds",
            "Webbed growing points causing stunting and branching distortion",
            "Frass and webbing visible on terminals and capsules",
        ],
        life_cycle_notes=(
            "Adults are nocturnal, attracted to light. Female lays eggs on young leaves "
            "and flower buds. Larvae feed for 10-15 days through 5 instars, webbing "
            "leaves together as they grow. Pupation in soil for 7-10 days. "
            "Multiple generations overlap throughout the growing season."
        ),
        favourable_conditions={
            "temp_min_c": 25, "temp_max_c": 35,
            "note": "Warm, dry weather during flowering and capsule development. "
                    "Populations build through the season; late plantings often more affected."
        },
        susceptible_stages=["Flowering", "Capsule Development"],
        economic_threshold="1-2 larvae per plant or 10% of terminals with webbing",
        chemical_control=[
            {"name": "Lambda-cyhalothrin 50 EC", "rate": "0.3 L/ha",
             "phi_days": "14", "notes": "Effective against larvae; apply when threshold reached"},
            {"name": "Emamectin benzoate 50 SG", "rate": "0.2 kg/ha",
             "phi_days": "7", "notes": "Selective; less disruptive to beneficial insects"},
        ],
        biological_control=[
            "Trichogramma egg parasitoids — release at flowering onset",
            "Bacillus thuringiensis (Bt) spray against young larvae",
            "Natural enemies: braconid wasps, predatory spiders",
        ],
        cultural_control=[
            "Early planting to escape peak moth populations",
            "Avoid very late planting which coincides with high webworm pressure",
            "Intercropping with cereals reduces oviposition on sesame",
            "Light traps to monitor and mass-trap adults (1 per ha)",
            "Destruction of crop residues after harvest to reduce carry-over",
        ],
        scouting_protocol=(
            "Weekly from flowering onset: examine 20 terminals per sampling point, "
            "5 points per ha. Record percentage of terminals with webbing and count "
            "larvae per plant. Also check capsules for bore holes and frass."
        ),
    ),
    PestProfile(
        name="Aphids",
        scientific_name="Aphis gossypii, Myzus persicae",
        pest_type="insect",
        identification=[
            "Small (1-2mm) soft-bodied insects clustering on growing points",
            "Green (A. gossypii) or pink-green (M. persicae) colour",
            "Wingless forms dominate; winged forms appear when colonies are crowded",
        ],
        damage_symptoms=[
            "Curling and distortion of young leaves and shoot tips",
            "Honeydew excretion leading to sooty mould on leaves",
            "Reduced vigour and delayed flowering under heavy infestation",
            "Vector of sesame phyllody phytoplasma (where present)",
        ],
        life_cycle_notes=(
            "Parthenogenetic reproduction — all-female colonies in warm weather. "
            "Generation time as short as 7 days at 25°C. "
            "Winged forms migrate to new hosts when crowded. "
            "Natural enemy complex usually controls populations by mid-season."
        ),
        favourable_conditions={
            "temp_min_c": 20, "temp_max_c": 30,
            "note": "Warm, dry conditions. Populations build rapidly in early season "
                    "before natural enemies establish. Excessive nitrogen fertilizer "
                    "promotes soft growth attractive to aphids."
        },
        susceptible_stages=["Vegetative", "Early Flowering"],
        economic_threshold="20+ aphids per growing point or 50% of terminals colonised",
        chemical_control=[
            {"name": "Pirimicarb 50 WG", "rate": "250 g/ha",
             "phi_days": "7", "notes": "Selective aphicide; preserves natural enemies — preferred option"},
            {"name": "Acetamiprid 20 SP", "rate": "100 g/ha",
             "phi_days": "14", "notes": "Systemic neonicotinoid; effective but disrupts beneficials"},
        ],
        biological_control=[
            "Ladybirds (Coccinellidae) — both adults and larvae are voracious aphid predators",
            "Parasitic wasps (Aphidius colemani, Lysiphlebus) — mummified aphids indicate activity",
            "Lacewings (Chrysoperla spp.) — larvae consume 200+ aphids each",
            "Entomopathogenic fungi (Beauveria bassiana) effective in humid conditions",
        ],
        cultural_control=[
            "Avoid excessive nitrogen which creates lush, aphid-attractive growth",
            "Reflective mulch confuses winged colonisers",
            "Conserve natural enemies — avoid broad-spectrum insecticides early in season",
            "Early planting — established plants tolerate aphids better",
        ],
        scouting_protocol=(
            "Weekly: examine 10 growing points per sampling area, 5 areas per ha. "
            "Record average aphids per tip and presence of natural enemies. "
            "If parasitised (mummified) aphids are abundant, delay spraying."
        ),
    ),
    PestProfile(
        name="Gall Midge",
        scientific_name="Asphondylia sesami",
        pest_type="insect",
        identification=[
            "Adult: tiny (2-3mm) delicate fly with long legs and antennae",
            "Larva: orange-yellow, found inside galled flower buds or capsules",
            "Galled flowers/capsules are swollen and distorted (diagnostic)",
        ],
        damage_symptoms=[
            "Flower buds swell into abnormal galls instead of opening",
            "Capsules distorted, remain green, and fail to produce seed",
            "Galled capsules often contain single orange larva in internal chamber",
            "Yield loss from converted flowers/capsules — can exceed 30% in bad years",
        ],
        life_cycle_notes=(
            "Adult midges lay eggs in flower buds. Larvae develop inside gall tissue, "
            "feeding on plant cells modified by larval secretions. Pupation occurs inside "
            "gall or in soil. Multiple generations overlap during the flowering period. "
            "Adults are weak fliers — infestations are often localised."
        ),
        favourable_conditions={
            "temp_min_c": 22, "temp_max_c": 30,
            "humidity_min": 70,
            "note": "Warm, humid conditions during flowering. "
                    "Continuous sesame cropping in an area builds populations. "
                    "Wild Sesamum spp. can serve as alternative hosts."
        },
        susceptible_stages=["Flowering", "Early Capsule Development"],
        economic_threshold="5% of flower buds or capsules showing gall symptoms",
        chemical_control=[
            {"name": "Dimethoate 400 EC", "rate": "0.8 L/ha",
             "phi_days": "21", "notes": "Systemic; targets adults and early-stage larvae in buds"},
            {"name": "Lambda-cyhalothrin 50 EC", "rate": "0.3 L/ha",
             "phi_days": "14", "notes": "Contact spray targeting adults at dusk when active"},
        ],
        biological_control=[
            "Parasitoid wasps (Eupelmus spp.) — attack larvae inside galls",
            "Predatory thrips feed on midge eggs on flower surfaces",
        ],
        cultural_control=[
            "Early and uniform planting to reduce extended flowering window exposure",
            "Remove and destroy galled buds/capsules to reduce within-field population",
            "Do not grow sesame in same field in consecutive years",
            "Remove wild Sesamum spp. within 500m of field",
            "Adjust planting date to avoid peak midge flight (if known locally)",
        ],
        scouting_protocol=(
            "During flowering: examine 20 flower buds per observation point, "
            "5 points per ha. Record percentage of buds showing swelling/gall formation. "
            "Cut open suspect buds to confirm orange larvae inside."
        ),
    ),
]

SESAME_GROWTH_STAGES: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Germination & Emergence",
        stage_code="VE",
        day_range=(0, 14),
        water_kc=0.3,
        water_mm_per_week=10,
        critical_nutrients=["Phosphorus"],
        key_activities=[
            "Sow at 1-2cm depth in warm soil (>25°C) — sesame will not germinate in cold soil",
            "Seed rate 3-5 kg/ha broadcast or 2-3 kg/ha drilled in rows 30-45cm apart",
            "Ensure good seed-soil contact on fine seedbed",
            "Pre-emergence weed control critical — sesame is slow to establish",
        ],
        risks=[
            "Poor emergence in cold or crusted soils",
            "Damping off (Rhizoctonia) in waterlogged seedbed",
            "Ants removing seed before germination",
            "Weed competition — sesame seedlings are tiny and uncompetitive",
        ],
        scientific_notes=(
            "Sesame is a thermophilic crop requiring soil temperatures above 25°C for germination "
            "(optimum 28-32°C). Seeds are very small (3-4mg each) and planted shallow. "
            "Photoblastic response: some varieties germinate better with light exposure. "
            "Radical emergence in 2-3 days under optimal conditions; first true leaves at 7-10 days."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Vegetative Growth",
        stage_code="V1",
        day_range=(14, 45),
        water_kc=0.5,
        water_mm_per_week=15,
        critical_nutrients=["Nitrogen", "Phosphorus"],
        key_activities=[
            "Thin to 10-15cm within rows at 3-4 leaf stage",
            "First hand weeding at 2-3 weeks (critical weed-free period)",
            "Second weeding at 4-5 weeks before canopy closure",
            "Scout for aphids on growing points",
        ],
        risks=[
            "Weed competition during critical first 5 weeks",
            "Aphid colonisation of tender growing points",
            "Excessive nitrogen causing lodging-prone vegetative growth",
        ],
        scientific_notes=(
            "Sesame establishes a deep taproot during vegetative phase, enabling drought "
            "tolerance later. Indeterminate growth habit means vegetative and reproductive "
            "phases overlap. Branching pattern varies by variety — single-stem types are preferred "
            "for mechanical harvest. Plant population of 250,000-400,000 plants/ha is optimal."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Flowering",
        stage_code="FL",
        day_range=(45, 75),
        water_kc=0.7,
        water_mm_per_week=20,
        critical_nutrients=["Potassium", "Phosphorus", "Boron"],
        key_activities=[
            "Monitor for sesame webworm on terminals and flower buds",
            "Scout for gall midge — check for swollen buds",
            "Maintain adequate moisture — water stress reduces capsule set",
            "Foliar boron (Solubor 0.5 kg/ha) improves seed set",
        ],
        risks=[
            "Webworm boring into capsules",
            "Gall midge converting buds to galls",
            "Cercospora leaf spot accelerating if humid",
            "Water stress causing flower/capsule abortion",
        ],
        scientific_notes=(
            "Sesame is self-pollinating but cross-pollination by bees occurs (5-60% depending on variety). "
            "Flowers open at dawn and close by midday. Each node produces 1-3 capsules depending "
            "on variety. Flowering proceeds acropetally — lower capsules mature while upper flowers "
            "still opening. This indeterminate pattern means optimal harvest timing is a compromise "
            "between mature lower and immature upper capsules."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Capsule Fill & Seed Development",
        stage_code="SF",
        day_range=(75, 105),
        water_kc=0.6,
        water_mm_per_week=15,
        critical_nutrients=["Potassium", "Sulphur"],
        key_activities=[
            "Continue webworm monitoring and control if threshold exceeded",
            "Reduce irrigation frequency — excess moisture increases disease and delays maturity",
            "Monitor for charcoal rot symptoms (wilting, dark stem base)",
            "Begin planning harvest timing — lower capsules turning brown",
        ],
        risks=[
            "Charcoal rot under drought stress",
            "Cercospora defoliation reducing seed fill",
            "Bird damage on ripening capsules",
            "Capsule shattering if harvest delayed (in shattering varieties)",
        ],
        scientific_notes=(
            "Oil accumulation in sesame seed peaks at 48-55% of seed weight during capsule fill. "
            "Oil is primarily composed of oleic (35-50%) and linoleic (35-50%) fatty acids, "
            "plus sesamin and sesamolin (unique lignans with antioxidant properties). "
            "Potassium is critical for oil synthesis; sulphur for amino acid (methionine) production. "
            "Seed colour develops late — white, brown, or black depending on variety."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Maturation & Harvest",
        stage_code="HV",
        day_range=(105, 130),
        water_kc=0.3,
        water_mm_per_week=8,
        critical_nutrients=[],
        key_activities=[
            "Cease irrigation 2-3 weeks before harvest",
            "Harvest when 75% of capsules have turned brown and lower leaves have dropped",
            "Cut plants at base and stack upright in shocks to dry for 7-14 days",
            "Thresh by inverting shocks over tarpaulin — capsules open and seeds fall out",
            "Clean seed and dry to < 8% moisture for storage",
        ],
        risks=[
            "Shattering losses if harvest delayed beyond optimal window",
            "Rain during field drying causes seed discolouration and mould",
            "Bird and rodent damage during shock drying",
            "Over-drying causing seed cracking",
        ],
        scientific_notes=(
            "Sesame capsules dehisce (open) when mature — this is both the natural seed "
            "dispersal mechanism and the traditional harvesting method. Non-shattering varieties "
            "(developed for combine harvest) are emerging but not yet common in Zimbabwe. "
            "Traditional harvest involves cutting when 75% of capsules are brown, stacking "
            "in shocks for 1-2 weeks, then inverting to shake out seeds. Seed moisture must "
            "reach < 8% for safe storage. Sesame oil is remarkably stable due to sesamol "
            "antioxidant — properly stored seed maintains quality for 1-2 years."
        ),
    ),
]

SESAME_FERTILIZER = FertilizerSchedule(
    basal={
        "product": "Compound L (5:18:10) or Single Superphosphate",
        "rate_kg_ha": 200,
        "timing": "At planting, banded or broadcast and incorporated",
        "notes": "Sesame has modest fertility needs. Responds primarily to P on deficient soils. "
                 "On fertile soils after a well-fertilised maize crop, basal fertilizer may be reduced."
    },
    top_dress_1={
        "product": "Ammonium Nitrate (AN 34.5%)",
        "rate_kg_ha": 75,
        "timing": "3-4 weeks after emergence at thinning",
        "notes": "Light nitrogen top dress. Do not exceed 40 kg N/ha total — excess N causes "
                 "tall, lodging-prone plants with delayed maturity and reduced oil content."
    },
    top_dress_2=None,
    foliar={
        "product": "Solubor (20.5% B) + Zinc Sulphate",
        "rate_kg_ha": 0.5,
        "timing": "At onset of flowering",
        "notes": "Boron improves capsule set and seed number. Zinc supports oil synthesis. "
                 "Mix Solubor 0.5 kg/ha + ZnSO₄ 2 kg/ha in 200 L water."
    },
    liming={
        "product": "Agricultural lime",
        "rate_kg_ha": 1000,
        "timing": "4-6 weeks before planting if pH < 5.5",
        "notes": "Sesame tolerates mildly acid soils (pH 5.5-7.0) but responds to liming "
                 "on strongly acid soils. Do not over-lime above pH 7.5."
    },
    notes=(
        "Sesame is a low-input crop — this is part of its appeal for smallholders. "
        "Excessive fertilisation (especially nitrogen) is counterproductive, causing "
        "vegetative excess, lodging, delayed maturity, and reduced oil percentage. "
        "Best yields come from residual fertility after a well-fertilised cereal crop in rotation."
    ),
)

SESAME_PLANTING_WINDOWS: List[PlantingWindow] = [
    PlantingWindow(
        region="NR III — Middleveld (Gokwe, Hurungwe)",
        optimal_start="November 15",
        optimal_end="December 31",
        acceptable_start="November 1",
        acceptable_end="January 15",
        notes="Primary sesame production zone. Plant after first reliable rains. "
              "Avoid very late planting — maturity must fall in dry period (April-May).",
    ),
    PlantingWindow(
        region="NR IV — Semi-arid (Muzarabani, Mt Darwin, Binga)",
        optimal_start="December 1",
        optimal_end="January 15",
        acceptable_start="November 15",
        acceptable_end="January 31",
        notes="Excellent sesame zone — hot climate suits the crop. Lower rainfall reduces "
              "disease pressure. Time harvest to fall in dry May-June period.",
    ),
    PlantingWindow(
        region="NR V — Lowveld (Chiredzi, Beitbridge)",
        optimal_start="December 1",
        optimal_end="January 15",
        acceptable_start="November 15",
        acceptable_end="January 31",
        notes="Marginal rainfall but sesame's drought tolerance is an advantage. "
              "Supplemental irrigation at flowering significantly increases yield. "
              "Very hot conditions — monitor for charcoal rot.",
    ),
    PlantingWindow(
        region="NR IIa/IIb — Highveld (limited)",
        optimal_start="November 15",
        optimal_end="December 15",
        acceptable_start="November 1",
        acceptable_end="December 31",
        notes="Cooler Highveld temperatures are suboptimal — sesame prefers heat. "
              "Better suited as niche crop in warm microsites. "
              "Higher humidity increases Cercospora risk.",
    ),
]


PROFILE = CropProfile(
    crop_name="Sesame",
    scientific_name="Sesamum indicum",
    family="Pedaliaceae",

    optimal_ph=(5.5, 7.0),
    critical_ph_low=5.0,
    optimal_soil_types=[
        "Well-drained sandy loams — good root development and drainage",
        "Light clay loams — fertile with adequate drainage",
        "Alluvial soils — fertile river valley soils",
    ],
    avoid_soil_types=[
        "Heavy, waterlogged clays — sesame is very sensitive to waterlogging",
        "Saline soils — reduces germination and growth",
        "Compacted hardpan soils — restricts deep taproot development",
    ],

    optimal_temp=(25.0, 35.0),
    critical_temp_low=15.0,
    critical_temp_high=40.0,
    base_temp_gdd=15.0,
    total_water_mm=400.0,

    growth_stages=SESAME_GROWTH_STAGES,
    fertilizer_schedule=SESAME_FERTILIZER,
    diseases=SESAME_DISEASES,
    pests=SESAME_PESTS,
    planting_windows=SESAME_PLANTING_WINDOWS,

    harvest_moisture="Seed: < 8% moisture content for safe storage; harvest plants at 12-15% and field-dry",
    storage_conditions=(
        "Store clean, dry seed (< 8% moisture) in airtight containers or woven bags in cool, "
        "dry conditions. Sesame seed oil is naturally stable due to sesamol and sesamin antioxidants — "
        "properly stored seed maintains quality for 12-24 months. "
        "Protect from rodents and weevils; hermetic storage bags (PICS bags) are effective."
    ),
    post_harvest_notes=(
        "Zimbabwe sesame is primarily white-seeded (Lindi White variety) for export market. "
        "Export grades require: white colour, < 2% impurity, < 2% damaged seed, < 8% moisture, "
        "oil content > 48%. Hulled sesame commands premium prices. "
        "Major buyers: Japan, South Korea, Turkey, EU confectionery market. "
        "Smallholder aggregation through cooperatives or contract farming is common for export. "
        "Organic certification adds significant premium and is feasible given low-input production."
    ),

    natural_region_suitability={
        "I": "Poor — too cool and wet for sesame",
        "IIa": "Marginal — cooler temperatures suboptimal, high disease pressure",
        "IIb": "Marginal — similar to IIa",
        "III": "Good — primary production zone (Gokwe, Hurungwe)",
        "IV": "Excellent — hot climate ideal, low disease pressure",
        "V": "Good — heat suits crop, but rainfall limiting without supplemental irrigation",
    },
)

ALIASES = ["simsim", "ufuta", "runinga"]
