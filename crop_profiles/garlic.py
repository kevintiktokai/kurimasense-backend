"""Garlic (Allium sativum) — Cool-season bulb crop planted from cloves, high-value spice and medicinal plant."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List


GARLIC_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="White Rot",
        pathogen="Sclerotium cepivorum",
        pathogen_type="fungal",
        symptoms=[
            "Yellowing and wilting of older leaves progressing to younger leaves",
            "White fluffy mycelial growth around the basal plate and roots",
            "Black sclerotia (0.5-2mm) embedded in mycelium on bulb surface",
            "Soft, watery decay of roots and basal plate leading to plant collapse",
        ],
        identification_markers=[
            "White fluffy mycelium at the base of bulbs (diagnostic)",
            "Tiny black spherical sclerotia visible with hand lens",
            "Roots completely destroyed; plants pull out easily",
            "Distinct from Fusarium by presence of sclerotia and white (not pink) mycelium",
        ],
        favourable_conditions={
            "temp_min_c": 10, "temp_max_c": 20,
            "soil_moisture": "cool, moist soils",
            "note": "Most active at 14-18 degC soil temperature. Sclerotia persist in soil "
                    "for 20+ years. Stimulated to germinate by allyl sulphide root exudates "
                    "of Allium species."
        },
        susceptible_stages=["Establishment", "Active growth", "Bulbing"],
        resistant_varieties=[],
        susceptible_varieties=["Egyptian White", "Purple Stripe"],
        chemical_control=[
            {"name": "Tebuconazole 250 EW", "rate": "1.0 L/ha drench",
             "phi_days": "30", "notes": "Soil drench at planting; partial suppression only"},
            {"name": "Iprodione 50 WP", "rate": "1.5 kg/ha",
             "phi_days": "21", "notes": "Pre-plant soil incorporation; reduces but does not eliminate"},
        ],
        biological_control=[
            "Trichoderma harzianum soil application at planting (2-4 kg/ha product)",
            "Coniothyrium minitans as sclerotia parasitiser in rotation",
        ],
        cultural_control=[
            "Minimum 15-year rotation away from all Allium crops once infested",
            "Use certified disease-free planting cloves",
            "Solarise soil with clear plastic mulch for 6-8 weeks before planting",
            "Avoid moving soil or equipment from infested to clean fields",
            "Raise soil pH above 7.0 to reduce severity",
        ],
        economic_threshold="Any occurrence warrants action; zero tolerance in clean fields",
        severity_scale={
            "mild": "< 5% plants showing yellowing, no visible mycelium yet",
            "moderate": "5-20% plants affected, white mycelium visible on pulled plants",
            "severe": "> 20% plants dead or dying, field abandonment may be necessary",
        },
    ),
    DiseaseProfile(
        name="Basal Rot",
        pathogen="Fusarium oxysporum f. sp. cepae",
        pathogen_type="fungal",
        symptoms=[
            "Premature yellowing and dieback of leaf tips",
            "Brown, dry rot progressing upward from the basal plate",
            "Pink-white mycelium at the base of infected cloves",
            "Bulbs feel soft and spongy at the base when squeezed",
        ],
        identification_markers=[
            "Brown discolouration of basal plate tissue on cross-section",
            "Pink-tinged mycelium (distinguishes from white rot)",
            "Roots brown and decayed but sclerotia absent",
            "Often secondary infections by Penicillium (blue-green mould) in storage",
        ],
        favourable_conditions={
            "temp_min_c": 25, "temp_max_c": 32,
            "soil_moisture": "warm, wet soils",
            "note": "Favoured by warm soil temperatures above 25 degC and waterlogging. "
                    "Worse when bulbs are damaged during harvest."
        },
        susceptible_stages=["Bulbing", "Maturation", "Post-harvest storage"],
        resistant_varieties=[],
        susceptible_varieties=["Egyptian White"],
        chemical_control=[
            {"name": "Thiram 80 WP (clove dip)", "rate": "3 g/L water, dip 15 min",
             "phi_days": "N/A", "notes": "Pre-plant clove treatment to reduce seed-borne inoculum"},
            {"name": "Carbendazim 50 WP", "rate": "1.0 g/L clove dip",
             "phi_days": "N/A", "notes": "Systemic; soak cloves for 30 minutes before planting"},
        ],
        biological_control=[
            "Trichoderma viride applied to planting furrows",
            "Bacillus subtilis seed treatments showing promise in trials",
        ],
        cultural_control=[
            "Avoid planting in warm, waterlogged soils",
            "Cure bulbs properly at harvest (dry in shade for 2-3 weeks)",
            "Handle bulbs carefully to prevent wounding",
            "Rotate with non-Allium crops for minimum 3 years",
            "Ensure good drainage at planting site",
        ],
        economic_threshold="5% bulbs showing basal rot symptoms during growing season",
        severity_scale={
            "mild": "< 5% plants affected, basal plate slightly discoloured",
            "moderate": "5-15% plants affected, significant root loss",
            "severe": "> 15% plant mortality, storage losses exceeding 30%",
        },
    ),
    DiseaseProfile(
        name="Purple Blotch",
        pathogen="Alternaria porri",
        pathogen_type="fungal",
        symptoms=[
            "Small water-soaked lesions on leaves that enlarge into purple-brown patches",
            "Concentric zonation patterns within lesions",
            "Lesions girdle leaves causing tip dieback",
            "Infected seed stalks break at lesion points",
        ],
        identification_markers=[
            "Purple to dark brown lesions with distinct concentric rings",
            "Yellow halo surrounding lesions",
            "Lesions often start at leaf tips and wound sites",
            "Dark olivaceous sporulation visible in humid conditions",
        ],
        favourable_conditions={
            "temp_min_c": 21, "temp_max_c": 30,
            "humidity_min": 80,
            "note": "Warm, humid conditions with alternating wet and dry periods. "
                    "Thrips damage creates entry points for infection."
        },
        susceptible_stages=["Active growth", "Bulbing", "Maturation"],
        resistant_varieties=[],
        susceptible_varieties=["Egyptian White", "Purple Stripe"],
        chemical_control=[
            {"name": "Mancozeb 80 WP", "rate": "2.0-2.5 kg/ha",
             "phi_days": "14", "notes": "Protectant; begin applications at first symptom"},
            {"name": "Azoxystrobin 250 SC", "rate": "0.4 L/ha",
             "phi_days": "14", "notes": "Systemic strobilurin; alternate with contact fungicides"},
        ],
        biological_control=[
            "Neem oil sprays (5 ml/L) as a preventive measure",
            "Compost teas may reduce foliar disease pressure",
        ],
        cultural_control=[
            "Wider spacing to improve air circulation",
            "Avoid overhead irrigation; use drip or furrow irrigation",
            "Remove and destroy crop debris after harvest",
            "Control thrips to reduce wound-entry points for the pathogen",
        ],
        economic_threshold="10% of leaves showing lesions before bulbing",
        severity_scale={
            "mild": "Scattered lesions on older leaves, < 10% leaf area",
            "moderate": "Multiple leaves affected, 10-30% leaf area destroyed",
            "severe": "> 30% leaf area destroyed, significant bulb size reduction",
        },
    ),
]


GARLIC_PESTS: List[PestProfile] = [
    PestProfile(
        name="Onion Thrips",
        scientific_name="Thrips tabaci",
        pest_type="insect",
        identification=[
            "Tiny (1-1.5mm) slender insects, pale yellow to brown",
            "Fringed wings; adults and nymphs found between leaf sheaths",
            "Nymphs wingless, pale yellow-green",
            "Use white or blue sticky traps for monitoring",
        ],
        damage_symptoms=[
            "Silvery-white streaking and stippling on leaves",
            "Leaf distortion and curling in severe infestations",
            "Reduced photosynthesis leading to undersized bulbs",
            "Feeding damage creates entry points for purple blotch and other diseases",
        ],
        life_cycle_notes=(
            "Complete lifecycle 15-30 days depending on temperature. Females lay eggs "
            "within leaf tissue. Multiple overlapping generations per season. Pupal stage "
            "occurs in soil. Populations build rapidly in hot, dry weather."
        ),
        favourable_conditions={
            "temp_min_c": 25, "temp_max_c": 35,
            "humidity": "low; dry conditions favour population build-up",
            "note": "Hot, dry conditions accelerate reproduction. Rainfall suppresses populations."
        },
        susceptible_stages=["Active growth", "Bulbing"],
        economic_threshold="30 thrips per plant or 5 thrips per leaf",
        chemical_control=[
            {"name": "Lambda-cyhalothrin 50 EC", "rate": "200 ml/ha",
             "phi_days": "7", "notes": "Pyrethroid; resistance risk with repeated use"},
            {"name": "Spinosad 480 SC", "rate": "100-200 ml/ha",
             "phi_days": "3", "notes": "Naturalyte; safer for beneficials; rotate with other modes"},
        ],
        biological_control=[
            "Predatory mites (Amblyseius swirskii) in protected cultivation",
            "Minute pirate bugs (Orius spp.) are effective natural predators",
            "Conserve natural enemies by avoiding broad-spectrum insecticides",
        ],
        cultural_control=[
            "Overhead irrigation or sprinkler to wash thrips off plants",
            "Reflective mulches deter thrips landing",
            "Remove weed hosts (grasses harbour thrips)",
            "Intercropping with non-host crops to reduce colonisation",
        ],
        scouting_protocol=(
            "Weekly monitoring from emergence. Pull apart leaf sheaths to count thrips. "
            "Sample 10 plants per 5 locations in the field. Record adults and nymphs separately. "
            "Treat when threshold of 30 per plant is reached."
        ),
    ),
    PestProfile(
        name="Onion Maggot",
        scientific_name="Delia antiqua",
        pest_type="insect",
        identification=[
            "Adult: small grey fly (6-7mm), resembles housefly but slender",
            "Larvae: white, legless maggots (8mm) found in bulb tissue",
            "Pupae: brown, barrel-shaped, found in soil near host",
            "Adults attracted to decaying Allium tissue for oviposition",
        ],
        damage_symptoms=[
            "Wilting, yellowing plants that pull up easily (roots destroyed)",
            "Brown tunnels and cavities in cloves and basal plate",
            "Soft, mushy rot with foul smell from secondary bacterial infection",
            "Seedlings killed outright; mature plants stunted with misshapen bulbs",
        ],
        life_cycle_notes=(
            "2-3 generations per year. Overwinters as pupa in soil. Adults emerge in spring "
            "and lay eggs at the base of plants. Larvae feed on roots and bulb tissue for "
            "2-3 weeks before pupating in soil. Attracted to damaged or decomposing Allium tissue."
        ),
        favourable_conditions={
            "temp_min_c": 15, "temp_max_c": 25,
            "soil_moisture": "cool, moist soils",
            "note": "Cool, moist conditions favour egg survival and larval development. "
                    "First generation coincides with planting season in Zimbabwe."
        },
        susceptible_stages=["Establishment", "Active growth"],
        economic_threshold="5-10% plants showing wilting symptoms; larvae found on pulled plants",
        chemical_control=[
            {"name": "Chlorpyrifos 48 EC (soil drench)", "rate": "2.5 L/ha",
             "phi_days": "21", "notes": "Apply at planting as a preventive soil treatment"},
            {"name": "Diazinon 14G (granular)", "rate": "30 kg/ha banded",
             "phi_days": "21", "notes": "Incorporate into furrow at planting"},
        ],
        biological_control=[
            "Entomopathogenic nematodes (Steinernema feltiae) applied to soil",
            "Parasitic wasps (Trybliographa rapae) attack larvae naturally",
            "Predatory ground beetles (Carabidae) feed on eggs and pupae",
        ],
        cultural_control=[
            "Delay planting to avoid peak first-generation adult flight",
            "Remove and destroy all Allium crop residues promptly",
            "Rotate away from Allium crops for 3+ years",
            "Use row covers / fleece over beds to prevent egg-laying",
            "Avoid using fresh manure near Allium crops (attracts flies)",
        ],
        scouting_protocol=(
            "Place yellow sticky traps at crop level to monitor adult flies from March onward. "
            "Scout weekly for wilting plants and pull suspect plants to check for larvae at base. "
            "Check 20 plants across 5 locations in the field."
        ),
    ),
    PestProfile(
        name="Root-Knot Nematodes",
        scientific_name="Meloidogyne spp.",
        pest_type="nematode",
        identification=[
            "Microscopic worms; adults not visible to the naked eye",
            "Root galls (knots) 1-5mm diameter on roots are the diagnostic sign",
            "Females pear-shaped, sedentary within root tissue",
            "Egg masses gelatinous, brown, found on root surface",
        ],
        damage_symptoms=[
            "Stunted, unthrifty plants with yellowing leaves",
            "Root galling reduces water and nutrient uptake",
            "Plants wilt during hot afternoons despite adequate soil moisture",
            "Bulbs undersized and malformed; secondary rot infections common",
        ],
        life_cycle_notes=(
            "Complete lifecycle 25-40 days depending on soil temperature. Juveniles (J2) "
            "penetrate root tips and establish feeding sites (giant cells). Females produce "
            "300-500 eggs per egg mass. Multiple generations per crop cycle in warm soils."
        ),
        favourable_conditions={
            "temp_min_c": 20, "temp_max_c": 30,
            "soil_type": "light, sandy soils",
            "note": "Sandy soils with warm temperatures favour nematode movement and reproduction. "
                    "Worse with monoculture and poor rotation."
        },
        susceptible_stages=["Establishment", "Active growth", "Bulbing"],
        economic_threshold="200 J2 per 200g soil at planting (pre-plant soil analysis)",
        chemical_control=[
            {"name": "Fenamiphos 400 EC", "rate": "5 L/ha pre-plant",
             "phi_days": "60", "notes": "Apply 2 weeks before planting and incorporate"},
            {"name": "Oxamyl 24 SL", "rate": "5 L/ha drench",
             "phi_days": "30", "notes": "Post-plant drench at first sign of damage"},
        ],
        biological_control=[
            "Paecilomyces lilacinus for egg parasitism",
            "Purpureocillium lilacinum soil treatments",
            "Incorporate nematode-suppressive crops (marigolds, mustard) as green manure before planting",
        ],
        cultural_control=[
            "Rotate with non-host crops: maize, sorghum, wheat for 2-3 seasons",
            "Solarise soil with clear plastic for 6-8 weeks in hot season",
            "Incorporate organic matter (compost, chicken manure) to promote antagonistic soil microflora",
            "Plant trap crops (Crotalaria spp.) in rotation",
            "Use raised beds with well-drained soils",
        ],
        scouting_protocol=(
            "Conduct pre-plant nematode soil analysis: collect 20 soil cores (0-30cm depth) "
            "per hectare, mix, and submit 200g sub-sample to nematology lab. During the season, "
            "pull stunted plants and examine roots for galling. Rating: 0 = clean, 5 = severely galled."
        ),
    ),
]


GARLIC_GROWTH_STAGES: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Establishment / Sprouting",
        stage_code="GS1",
        day_range=(0, 21),
        water_kc=0.40,
        water_mm_per_week=12,
        critical_nutrients=["P", "K"],
        key_activities=[
            "Plant cloves 5-7 cm deep, pointed end up, 10 cm in-row, 20-25 cm between rows",
            "Apply basal fertiliser and incorporate",
            "Irrigate immediately after planting to settle soil around cloves",
            "Apply pre-emergent herbicide or mulch for weed suppression",
        ],
        risks=["Waterlogging causing clove rot", "Bird damage", "Poor clove quality"],
        scientific_notes=(
            "Root initiation occurs at 10-15 degC soil temperature. Cloves break dormancy "
            "via vernalisation exposure (4-10 degC for 2-6 weeks depending on cultivar). "
            "Phosphorus is critical for root primordia development. The apical meristem "
            "elongates to produce the first true leaf within 10-14 days."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Vegetative Growth",
        stage_code="GS2",
        day_range=(21, 70),
        water_kc=0.70,
        water_mm_per_week=20,
        critical_nutrients=["N", "P", "K", "S"],
        key_activities=[
            "First top-dress with nitrogen at 4-5 leaf stage",
            "Hand-weed or cultivate shallowly to avoid root damage",
            "Monitor for thrips and purple blotch",
            "Maintain consistent soil moisture",
        ],
        risks=["Thrips infestation", "Nitrogen deficiency", "Weed competition"],
        scientific_notes=(
            "Each leaf corresponds to a clove wrapper. Final leaf number (8-12) determines "
            "bulb wrapper quality and storability. Sulphur uptake during vegetative growth "
            "directly influences allicin content (flavour and medicinal compounds). "
            "Photoperiod sensitivity begins to develop; short days maintain vegetative growth."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Bulb Initiation",
        stage_code="GS3",
        day_range=(70, 100),
        water_kc=0.90,
        water_mm_per_week=25,
        critical_nutrients=["N", "K", "S"],
        key_activities=[
            "Second top-dress with nitrogen and potassium",
            "Ensure adequate sulphur supply for flavour development",
            "Scout for white rot symptoms (cool-season peak risk)",
            "Remove any flower scapes (hardneck types) to redirect energy to bulb",
        ],
        risks=["White rot", "Premature bulbing from temperature stress", "Under-fertilisation"],
        scientific_notes=(
            "Bulb initiation is triggered by a combination of day length (>13 hours for "
            "long-day types) and accumulated temperature. The lateral buds in leaf axils "
            "differentiate into clove primordia. Bulbing ratio (bulb diameter / neck diameter) "
            "exceeds 2.0, marking onset of bulbing. Potassium demand increases sharply as "
            "bulb cells expand through vacuole enlargement and osmotic adjustment."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Bulb Development",
        stage_code="GS4",
        day_range=(100, 140),
        water_kc=0.85,
        water_mm_per_week=22,
        critical_nutrients=["K", "S", "Ca"],
        key_activities=[
            "Maintain irrigation but begin reducing frequency toward end of stage",
            "Monitor for basal rot in warm soils",
            "Cease nitrogen applications to prevent secondary growth",
            "Watch for nematode damage symptoms (stunting, yellowing)",
        ],
        risks=["Secondary growth from late nitrogen", "Basal rot", "Bulb splitting"],
        scientific_notes=(
            "Dry matter accumulation peaks during this phase with partitioning of "
            "photosynthates from leaves to bulb storage tissue. Fructans (storage "
            "carbohydrates) accumulate in developing cloves. Organosulphur compounds "
            "(alliin) are synthesised and stored in clove mesophyll. Calcium is essential "
            "for cell wall integrity and reduces post-harvest breakdown."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Maturation and Curing",
        stage_code="GS5",
        day_range=(140, 165),
        water_kc=0.50,
        water_mm_per_week=10,
        critical_nutrients=["K"],
        key_activities=[
            "Stop irrigation 2-3 weeks before harvest",
            "Monitor neck softness as maturity indicator (50-75% tops down)",
            "Prepare curing area (shade structure with good ventilation)",
            "Plan harvest timing to avoid rain",
        ],
        risks=["Rain damage to mature bulbs", "Delayed harvest causing skin cracking"],
        scientific_notes=(
            "Leaf senescence mobilises remaining nutrients to the bulb. The pseudostem "
            "neck softens as vascular tissue collapses, a reliable maturity indicator. "
            "Outer wrapper leaves dry to form protective skin. Alliinase enzyme activity "
            "and allicin potential are highest at full physiological maturity. Delaying "
            "harvest beyond 75% top fall increases skin splitting and disease entry."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Harvest and Post-Harvest",
        stage_code="GS6",
        day_range=(165, 180),
        water_kc=0.0,
        water_mm_per_week=0,
        critical_nutrients=[],
        key_activities=[
            "Lift bulbs carefully with fork to avoid bruising",
            "Cure in shade with good airflow for 2-3 weeks",
            "Trim roots and tops after curing (leave 2-3 cm neck)",
            "Grade and store in mesh bags or braids",
        ],
        risks=["Bruising during harvest", "Fusarium storage rot", "Sprouting in storage"],
        scientific_notes=(
            "Proper curing involves drying outer skins at 25-30 degC with 60-70% RH for "
            "14-21 days. This forms a protective barrier of desiccated outer scales that "
            "reduces water loss and pathogen entry during storage. Post-harvest weight loss "
            "is 5-10% during curing. Well-cured garlic stores 6-8 months at 0-2 degC and "
            "60-70% RH, or at ambient temperature (15-20 degC) for 3-4 months."
        ),
    ),
]


GARLIC_FERTILIZER = FertilizerSchedule(
    basal={
        "product": "Compound S (7:21:7) or similar high-P compound",
        "rate_kg_ha": 400,
        "n_kg_ha": 28,
        "p_kg_ha": 84,
        "k_kg_ha": 28,
        "timing": "At planting, banded 5 cm below and to the side of cloves",
        "notes": "Incorporate well. Add 200 kg/ha single superphosphate on P-deficient soils.",
    },
    top_dress_1={
        "product": "Ammonium Nitrate (34.5% N) or CAN",
        "rate_kg_ha": 150,
        "n_kg_ha": 52,
        "timing": "4-5 leaf stage (approximately 30-35 days after planting)",
        "notes": "Side-dress and irrigate in. Do not apply to wet foliage.",
    },
    top_dress_2={
        "product": "Potassium Nitrate (13:0:46) or KCl + AN blend",
        "rate_kg_ha": 100,
        "n_kg_ha": 13,
        "k_kg_ha": 46,
        "timing": "At bulb initiation (approximately 70-80 days after planting)",
        "notes": "Final N application. Potassium critical for bulb quality and storability.",
    },
    foliar={
        "product": "Zinc sulphate + Boron (Solubor)",
        "rate": "Zn: 2 g/L, B: 1 g/L",
        "timing": "2-3 foliar sprays during vegetative phase",
        "notes": "Apply in early morning or late afternoon to avoid scorch.",
    },
    liming={
        "target_ph": "6.0-7.0",
        "product": "Agricultural lime (calcitic or dolomitic)",
        "rate": "As per soil test, typically 1-3 t/ha",
        "timing": "Apply 4-6 weeks before planting and incorporate",
        "notes": "Garlic prefers near-neutral pH. Dolomitic lime provides Mg on deficient soils.",
    },
    notes=(
        "Total nutrient targets: 90-120 kg N/ha, 80-100 kg P2O5/ha, 80-120 kg K2O/ha. "
        "Sulphur is important for flavour; apply 20-30 kg S/ha via single superphosphate or gypsum. "
        "Avoid excessive nitrogen which promotes lush foliage at the expense of bulb development."
    ),
)


GARLIC_PLANTING_WINDOWS: List[PlantingWindow] = [
    PlantingWindow(
        region="NR I - Eastern Highlands",
        optimal_start="March 15",
        optimal_end="April 30",
        acceptable_start="March 1",
        acceptable_end="May 15",
        notes=(
            "Cool highland temperatures provide ideal vernalisation. Garlic benefits from "
            "the cool dry winter period. Harvest August-October."
        ),
    ),
    PlantingWindow(
        region="NR IIa/IIb - Highveld (Mashonaland)",
        optimal_start="April 1",
        optimal_end="May 15",
        acceptable_start="March 15",
        acceptable_end="May 31",
        notes=(
            "Main garlic production zone under irrigation. Plant after maize harvest "
            "as a winter rotation crop. Harvest September-November."
        ),
    ),
    PlantingWindow(
        region="NR III - Semi-intensive",
        optimal_start="April 1",
        optimal_end="May 15",
        acceptable_start="March 20",
        acceptable_end="May 31",
        notes=(
            "Irrigation essential. Similar timing to NR II. Risk of warm late-season "
            "temperatures affecting bulb quality. Harvest September-October."
        ),
    ),
]


PROFILE = CropProfile(
    crop_name="Garlic",
    scientific_name="Allium sativum",
    family="Amaryllidaceae",

    optimal_ph=(6.0, 7.0),
    critical_ph_low=5.2,
    optimal_soil_types=["well-drained loam", "sandy loam", "silt loam"],
    avoid_soil_types=["heavy clay", "waterlogged soils", "vertisol"],

    optimal_temp=(12.0, 24.0),
    critical_temp_low=-5.0,
    critical_temp_high=35.0,
    base_temp_gdd=0.0,
    total_water_mm=350.0,

    growth_stages=GARLIC_GROWTH_STAGES,
    fertilizer_schedule=GARLIC_FERTILIZER,
    diseases=GARLIC_DISEASES,
    pests=GARLIC_PESTS,
    planting_windows=GARLIC_PLANTING_WINDOWS,

    harvest_moisture="65-70% moisture content at harvest; cure to < 40% for storage",
    storage_conditions="0-2 degC, 60-70% RH for long-term (6-8 months); or ambient 15-20 degC for 3-4 months",
    post_harvest_notes=(
        "Cure bulbs in shade with good ventilation for 2-3 weeks until outer skins are papery. "
        "Trim roots to 1 cm and tops to 2-3 cm. Grade by size: large (> 45mm diameter), "
        "medium (35-45mm), small (< 35mm). Store in mesh bags or braid for air circulation. "
        "Reserve best bulbs for seed stock (plant the largest cloves from largest bulbs)."
    ),

    natural_region_suitability={
        "I": "Excellent — cool highlands ideal for high-quality garlic production",
        "IIa": "Good — irrigated winter production on Highveld; main commercial zone",
        "IIb": "Good — similar to IIa under irrigation",
        "III": "Moderate — possible under irrigation but warm temperatures reduce bulb quality",
        "IV": "Marginal — too warm and dry without irrigation; poor vernalisation",
        "V": "Unsuitable — excessive heat, insufficient cold for proper bulbing",
    },
)

ALIASES: list = []
