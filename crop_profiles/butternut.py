"""Butternut (Cucurbita moschata) — Popular cucurbit for smallholder and commercial farming in Zimbabwe."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List


BUTTERNUT_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Powdery Mildew",
        pathogen="Podosphaera xanthii",
        pathogen_type="fungal",
        symptoms=[
            "White, powdery fungal colonies on upper leaf surfaces",
            "Progresses to cover entire leaf, petioles, and stems",
            "Severely infected leaves become chlorotic and senesce prematurely",
            "Reduced fruit size and sugar content due to loss of photosynthetic area",
        ],
        identification_markers=[
            "White talcum-powder-like patches on adaxial leaf surface",
            "Colonies spread radially; older centres may turn grey-brown",
            "Unlike downy mildew, appears on upper leaf surface first",
            "No free water required for infection (conidia germinate at low humidity)",
        ],
        favourable_conditions={
            "humidity_min": 50, "humidity_max": 90,
            "temp_min_c": 20, "temp_max_c": 30,
            "note": "Dry foliage with moderate humidity favours conidial germination. "
                    "Shaded, dense canopies increase severity. Free water actually inhibits spore germination."
        },
        susceptible_stages=["Vine elongation", "Flowering", "Fruit development"],
        resistant_varieties=["Star 6001"],
        susceptible_varieties=["Waltham"],
        chemical_control=[
            {"name": "Difenoconazole 250 EC (Score)", "rate": "0.3-0.5 L/ha",
             "phi_days": "7", "notes": "Systemic triazole; apply at first signs"},
            {"name": "Sulphur 80 WP", "rate": "2.5-3.0 kg/ha",
             "phi_days": "1", "notes": "Protectant; avoid application above 35°C (phytotoxic)"},
            {"name": "Azoxystrobin 250 SC (Amistar)", "rate": "0.4-0.5 L/ha",
             "phi_days": "3", "notes": "Strobilurin; alternate with triazoles to manage resistance"},
        ],
        biological_control=[
            "Bacillus subtilis-based products (Serenade) applied preventatively",
            "Potassium bicarbonate sprays (3-5 g/L) disrupt fungal cell walls",
            "Ampelomyces quisqualis hyperparasite available in some bio-control programmes",
        ],
        cultural_control=[
            "Select tolerant varieties such as Star 6001",
            "Ensure adequate spacing (2 m x 0.6 m) for air circulation",
            "Avoid excessive nitrogen which promotes dense, susceptible canopy",
            "Remove and destroy severely infected lower leaves",
            "Drip irrigation preferred over overhead to keep foliage dry",
        ],
        economic_threshold="10% leaf area affected before fruit set",
        severity_scale={
            "mild": "< 10% leaf area, lower canopy only",
            "moderate": "10-40% leaf area, spreading to upper canopy",
            "severe": "> 40% leaf area, premature defoliation — 30-50% yield loss",
        },
    ),
    DiseaseProfile(
        name="Downy Mildew",
        pathogen="Pseudoperonospora cubensis",
        pathogen_type="fungal",
        symptoms=[
            "Angular, yellow-green lesions bounded by leaf veins on upper surface",
            "Purple-grey sporangiophore growth on corresponding lower leaf surface",
            "Lesions become necrotic and coalesce, causing rapid defoliation",
            "Fruit exposed to sun develops sunscald after defoliation",
        ],
        identification_markers=[
            "Angular lesions restricted by veins (unlike powdery mildew round patches)",
            "Greyish-purple sporulation visible on lower leaf surface in morning dew",
            "Rapid spread during wet weather — entire fields can defoliate in 7-10 days",
        ],
        favourable_conditions={
            "humidity_min": 85, "temp_min_c": 15, "temp_max_c": 22,
            "leaf_wetness_hours": 6,
            "note": "Cool, wet conditions with prolonged leaf wetness. "
                    "Morning dews and overhead irrigation greatly increase risk."
        },
        susceptible_stages=["Vine elongation", "Flowering", "Fruit development"],
        resistant_varieties=[],
        susceptible_varieties=["Waltham", "Star 6001"],
        chemical_control=[
            {"name": "Mancozeb 80 WP", "rate": "2.0-2.5 kg/ha",
             "phi_days": "14", "notes": "Protectant; apply before infection or on 7-day schedule"},
            {"name": "Metalaxyl + Mancozeb (Ridomil Gold MZ 68 WG)", "rate": "2.5 kg/ha",
             "phi_days": "14", "notes": "Systemic + protectant; limit to 3 applications per season"},
        ],
        biological_control=[
            "Copper hydroxide 77 WP at 2.0 kg/ha as organic-approved protectant",
            "Trichoderma harzianum soil drenches to boost plant systemic resistance",
        ],
        cultural_control=[
            "Avoid overhead irrigation; use drip or furrow",
            "Plant on raised beds for drainage in heavy soils",
            "Ensure adequate plant spacing for air movement",
            "Remove volunteer cucurbits and weed hosts",
            "Rotate with non-cucurbit crops for at least 2 seasons",
        ],
        economic_threshold="First angular lesions detected on 5% of plants",
        severity_scale={
            "mild": "Scattered angular lesions on lower leaves",
            "moderate": "Lesions coalescing, 20-40% leaf area lost",
            "severe": "> 50% defoliation, fruit sunscald evident — 40-70% yield loss",
        },
    ),
    DiseaseProfile(
        name="Fusarium Wilt",
        pathogen="Fusarium oxysporum f. sp. cucurbitacearum",
        pathogen_type="fungal",
        symptoms=[
            "Unilateral wilting — one side of vine wilts while other remains turgid",
            "Yellowing and browning of older leaves progressing upward",
            "Brown vascular discolouration visible when stem is cut longitudinally",
            "Entire plant collapse in advanced stages",
        ],
        identification_markers=[
            "Vascular browning in stem cross-section is diagnostic",
            "Wilting that does not recover with irrigation (distinguish from water stress)",
            "Unilateral symptoms are characteristic of vascular pathogens",
        ],
        favourable_conditions={
            "soil_temp_min_c": 20, "soil_temp_max_c": 30,
            "note": "Warm soils, acidic pH, sandy soils. Pathogen persists in soil "
                    "for many years as chlamydospores. Worse after root damage by nematodes."
        },
        susceptible_stages=["Seedling", "Vine elongation", "Flowering"],
        resistant_varieties=[],
        susceptible_varieties=["Waltham"],
        chemical_control=[
            {"name": "Benomyl 50 WP (soil drench)", "rate": "1.0 g/L seedling drench",
             "phi_days": "21", "notes": "Drench transplant holes; limited curative effect"},
        ],
        biological_control=[
            "Trichoderma harzianum seed treatment and soil incorporation",
            "Non-pathogenic Fusarium oxysporum as competitive exclusion agent",
            "Mycorrhizal inoculants enhance root defence",
        ],
        cultural_control=[
            "Rotate with non-cucurbit crops for minimum 4-5 years",
            "Maintain soil pH above 6.0 with agricultural lime",
            "Graft onto resistant rootstocks (Cucurbita maxima x C. moschata)",
            "Solarise soil with clear plastic for 4-6 weeks before planting",
            "Avoid root damage during cultivation; control root-knot nematodes",
        ],
        economic_threshold="Any confirmed wilt — remove and destroy affected plants immediately",
        severity_scale={
            "mild": "1-5% plants showing unilateral wilt",
            "moderate": "5-20% plant mortality in patches",
            "severe": "> 20% plant mortality, field abandonment may be considered",
        },
    ),
]

BUTTERNUT_PESTS: List[PestProfile] = [
    PestProfile(
        name="Fruit Fly",
        scientific_name="Bactrocera cucurbitae",
        pest_type="insect",
        identification=[
            "Adult: 6-8 mm long, yellowish-brown with clear wings and dark markings",
            "Larvae: white maggots 8-10 mm found inside fruit",
            "Pupae: brown, barrel-shaped, found in soil beneath plants",
        ],
        damage_symptoms=[
            "Oviposition punctures visible as small, dark spots on fruit skin",
            "Internal tunnelling by larvae causes fruit rot and collapse",
            "Secondary bacterial and fungal infections follow larval damage",
            "Fruit drops prematurely; unmarketable fruit",
        ],
        life_cycle_notes=(
            "Female lays eggs just beneath fruit skin. Larvae develop inside fruit "
            "over 7-10 days, then drop to soil to pupate. Adults emerge after 7-14 days. "
            "Multiple overlapping generations per season. Peak activity in warm, humid weather."
        ),
        favourable_conditions={
            "temp_min_c": 25, "temp_max_c": 35,
            "humidity_min": 60,
            "note": "Warm, humid conditions. Activity peaks during fruiting stage."
        },
        susceptible_stages=["Flowering", "Fruit development", "Maturation"],
        economic_threshold="5 flies per trap per week, or 2% fruit with oviposition marks",
        chemical_control=[
            {"name": "Malathion 50 EC + protein bait", "rate": "1.5 mL/L + 10 mL bait/L",
             "phi_days": "7", "notes": "Bait spray on border rows; attract-and-kill strategy"},
            {"name": "Lambda-cyhalothrin 50 EC", "rate": "0.3-0.5 mL/L",
             "phi_days": "7", "notes": "Cover spray during peak flight; rotate chemistry"},
        ],
        biological_control=[
            "Release of parasitoid wasps (Fopius arisanus, Diachasmimorpha longicaudata)",
            "Entomopathogenic fungi (Metarhizium anisopliae) soil application targets pupae",
            "Encourage natural predators: ants, ground beetles",
        ],
        cultural_control=[
            "Field sanitation: collect and destroy fallen, infested fruit daily",
            "Bury infested fruit at least 50 cm deep or feed to livestock",
            "Use yellow sticky traps and cue-lure traps for monitoring and mass trapping",
            "Early harvesting reduces exposure window",
            "Plough fields after harvest to expose pupae to desiccation and predation",
        ],
        scouting_protocol=(
            "Install cue-lure traps (1 per hectare) at flowering onset. Check traps weekly. "
            "Inspect 20 fruit per monitoring point for oviposition punctures. "
            "Record and map hotspots to target bait sprays."
        ),
    ),
    PestProfile(
        name="Aphids",
        scientific_name="Aphis gossypii",
        pest_type="insect",
        identification=[
            "Small (1-2 mm), soft-bodied, pear-shaped insects",
            "Colour varies: green, yellow, or dark brown-black",
            "Found in dense colonies on growing tips and leaf undersides",
            "Winged forms appear when colonies become overcrowded",
        ],
        damage_symptoms=[
            "Leaf curling and distortion of growing points",
            "Sticky honeydew excretion on leaves, leading to sooty mould",
            "Virus transmission (Cucumber Mosaic Virus, Zucchini Yellow Mosaic Virus)",
            "Stunted growth and reduced fruit set in severe infestations",
        ],
        life_cycle_notes=(
            "Parthenogenetic reproduction in warm conditions — population can double "
            "in 3-4 days. Winged morphs disperse to new plants. No sexual stage in "
            "tropical/subtropical Zimbabwe. Continuous generations year-round under irrigation."
        ),
        favourable_conditions={
            "temp_min_c": 20, "temp_max_c": 30,
            "note": "Warm, dry conditions favour rapid reproduction. "
                    "Excessive nitrogen fertilisation produces succulent growth attractive to aphids."
        },
        susceptible_stages=["Seedling", "Vine elongation", "Flowering"],
        economic_threshold="20% of plants with colonies on growing tips, or 50 aphids per leaf",
        chemical_control=[
            {"name": "Imidacloprid 200 SL (Confidor)", "rate": "0.3-0.5 mL/L",
             "phi_days": "14", "notes": "Systemic neonicotinoid; avoid during flowering (pollinator risk)"},
            {"name": "Acetamiprid 20 SP", "rate": "0.2 g/L",
             "phi_days": "7", "notes": "Safer neonicotinoid for use near flowering"},
            {"name": "Pirimicarb 50 WG (Pirimor)", "rate": "0.5 g/L",
             "phi_days": "3", "notes": "Selective aphicide; spares natural enemies"},
        ],
        biological_control=[
            "Encourage ladybird beetles (Hippodamia convergens) — each adult eats 50+ aphids/day",
            "Lacewing larvae (Chrysoperla carnea) are voracious aphid predators",
            "Parasitoid wasps (Aphidius colemani) cause aphid mummification",
            "Beauveria bassiana sprays effective under humid conditions",
        ],
        cultural_control=[
            "Avoid excessive nitrogen — promotes soft, aphid-attractive growth",
            "Reflective mulches (silver or aluminium) disorient winged aphids",
            "Strong water jets dislodge colonies from plants",
            "Remove weed hosts around field borders",
            "Intercrop with repellent plants (basil, marigold)",
        ],
        scouting_protocol=(
            "Check 5 plants per 10 m of row at 4 monitoring points per hectare. "
            "Examine undersides of youngest fully expanded leaves and growing tips. "
            "Use yellow pan traps to detect winged immigrant aphids early. "
            "Scout twice weekly during warm, dry spells."
        ),
    ),
    PestProfile(
        name="Pumpkin Fly",
        scientific_name="Dacus bivittatus",
        pest_type="insect",
        identification=[
            "Adult: larger than fruit fly (10-12 mm), dark brown with two distinctive yellow dorsal stripes",
            "Larvae: cream-white maggots up to 12 mm in mature fruit",
            "Pupae: dark brown, found in soil at 2-5 cm depth",
        ],
        damage_symptoms=[
            "Soft, water-soaked areas on fruit where eggs are laid",
            "Internal tunnelling causes fruit to become watery and collapse",
            "Heavy secondary rotting with foul smell",
            "Fruit completely destroyed; yield losses can reach 80-100% without control",
        ],
        life_cycle_notes=(
            "Females oviposit into young, developing fruit. Larvae feed for 10-14 days, "
            "exit fruit, and pupate in soil for 10-21 days. Adults live 2-4 months. "
            "Peak emergence coincides with onset of rains in Zimbabwe (November-December)."
        ),
        favourable_conditions={
            "temp_min_c": 22, "temp_max_c": 32,
            "humidity_min": 65,
            "note": "Warm, moist conditions during fruiting. Highest pressure "
                    "in NR I and II where rainfall is abundant."
        },
        susceptible_stages=["Fruit development", "Maturation"],
        economic_threshold="3 flies per protein bait trap per week",
        chemical_control=[
            {"name": "GF-120 NF Naturalyte Bait (Spinosad)", "rate": "1.0-1.5 L/ha",
             "phi_days": "3", "notes": "Spot application on foliage; reduced environmental impact"},
            {"name": "Fenthion 50 EC + protein hydrolysate bait", "rate": "1.0 mL/L + bait",
             "phi_days": "14", "notes": "Attract-and-kill; apply to border vegetation"},
        ],
        biological_control=[
            "Parasitoid wasps (Psyttalia cosyrae) attack larvae",
            "Entomopathogenic nematodes (Steinernema feltiae) applied to soil target pupae",
            "Maintain natural enemy habitat with flowering borders",
        ],
        cultural_control=[
            "Collect and destroy all fallen and infested fruit daily",
            "Deep ploughing after harvest to expose and desiccate pupae",
            "Harvest fruit promptly at maturity; do not leave in field",
            "Protein bait traps deployed at 10-15 per hectare for mass trapping",
            "Crop rotation and field isolation from other cucurbit fields",
        ],
        scouting_protocol=(
            "Deploy protein bait traps at flowering onset, 1 per 0.5 ha. "
            "Check traps every 3 days, recording species and count. "
            "Walk field diagonals inspecting developing fruit for oviposition stings. "
            "Map affected areas for targeted bait application."
        ),
    ),
]

BUTTERNUT_GROWTH_STAGES: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Germination & Emergence",
        stage_code="GE",
        day_range=(0, 10),
        water_kc=0.40,
        water_mm_per_week=15,
        critical_nutrients=["Phosphorus", "Zinc"],
        key_activities=[
            "Direct seed at 2-3 cm depth, 2 seeds per station",
            "Spacing: 2.0 m between rows, 0.6-0.8 m in-row",
            "Apply basal fertilizer in planting furrow 5 cm below seed",
            "Ensure adequate soil moisture for uniform germination",
        ],
        risks=[
            "Soil crusting in heavy clay soils prevents emergence",
            "Cutworm damage to emerging seedlings",
            "Bird damage to cotyledons",
            "Poor germination if soil temp below 15°C",
        ],
        scientific_notes=(
            "Cucurbita moschata requires soil temperatures above 15°C for germination, "
            "with an optimum of 25-30°C. Hypogeal germination; cotyledons emerge within "
            "5-7 days at optimal temperature. Phosphorus is critical for radicle development "
            "and early root establishment in the low-P soils common across Zimbabwe's granite sands."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Seedling & Establishment",
        stage_code="SE",
        day_range=(10, 25),
        water_kc=0.50,
        water_mm_per_week=20,
        critical_nutrients=["Nitrogen", "Phosphorus"],
        key_activities=[
            "Thin to 1 plant per station at 2-leaf stage",
            "Shallow cultivation for weed control",
            "Monitor for cutworms and aphids",
            "Apply first top-dress nitrogen if plants appear pale",
        ],
        risks=[
            "Cutworm attack at soil level",
            "Aphid colonisation and virus transmission",
            "Damping-off (Pythium, Rhizoctonia) in waterlogged soils",
            "Competition from weeds during slow early growth",
        ],
        scientific_notes=(
            "The juvenile phase is characterised by development of the first 4-5 true leaves "
            "and establishment of the primary root system. Leaf area index is very low (<0.5), "
            "so weed competition for light is critical. Cucurbit seedlings are particularly "
            "sensitive to root disturbance, hence minimal tillage around plants is advised."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Vine Elongation",
        stage_code="VE",
        day_range=(25, 50),
        water_kc=0.70,
        water_mm_per_week=30,
        critical_nutrients=["Nitrogen", "Potassium"],
        key_activities=[
            "Apply first top-dress of AN at 200-250 kg/ha",
            "Train vines away from inter-row paths",
            "Last opportunity for mechanical weed control",
            "Monitor for powdery mildew onset",
        ],
        risks=[
            "Powdery mildew establishment during rapid canopy growth",
            "Nitrogen deficiency limits vine extension",
            "Vine damage from strong winds",
            "Waterlogging in heavy rains reduces root function",
        ],
        scientific_notes=(
            "Vine elongation represents exponential vegetative growth with high nitrogen demand. "
            "Indeterminate growth habit means vines can extend 3-5 metres. Source-sink dynamics "
            "shift as the plant builds carbohydrate reserves for subsequent fruit loading. "
            "Potassium uptake increases sharply, supporting cell expansion and osmotic regulation."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Flowering & Pollination",
        stage_code="FL",
        day_range=(50, 70),
        water_kc=0.90,
        water_mm_per_week=35,
        critical_nutrients=["Potassium", "Boron", "Calcium"],
        key_activities=[
            "Ensure adequate bee activity for pollination",
            "Avoid insecticide applications during morning flowering hours",
            "Apply foliar boron (Solubor 1 g/L) to improve fruit set",
            "Monitor for fruit fly and pumpkin fly with traps",
        ],
        risks=[
            "Poor pollination leads to misshapen or aborted fruit",
            "Rain during flowering reduces bee activity",
            "Fruit fly oviposition begins on young fruit",
            "Water stress causes flower abortion",
        ],
        scientific_notes=(
            "C. moschata is monoecious with separate male and female flowers. Male flowers "
            "open first (protandry), followed by female flowers 5-7 days later. Pollination "
            "requires insect vectors, primarily Apis mellifera and Bombus spp. Each female "
            "flower is receptive for only one morning. Boron is essential for pollen tube "
            "growth; deficiency on Zimbabwe's leached granite soils is common."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Fruit Development",
        stage_code="FD",
        day_range=(70, 100),
        water_kc=0.85,
        water_mm_per_week=35,
        critical_nutrients=["Potassium", "Calcium", "Nitrogen"],
        key_activities=[
            "Maintain consistent irrigation — avoid wet-dry cycles",
            "Apply second top-dress if needed (AN at 100 kg/ha)",
            "Intensify fruit fly and pumpkin fly management",
            "Scout for powdery mildew and apply fungicides if needed",
        ],
        risks=[
            "Fruit cracking from irregular watering",
            "Blossom end rot from calcium deficiency",
            "Fruit fly and pumpkin fly damage intensifies",
            "Powdery mildew reduces leaf area, limiting photosynthate supply to fruit",
        ],
        scientific_notes=(
            "Fruit development involves rapid cell division (first 14 days post-pollination) "
            "followed by cell expansion. Potassium demand peaks as fruit acts as a strong "
            "carbohydrate sink. Brix content and dry matter accumulation depend on adequate "
            "leaf area and photosynthetic capacity. Calcium translocation to fruit is xylem-dependent "
            "and requires consistent transpiration — interrupted water supply causes blossom end rot."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Maturation & Harvest",
        stage_code="MH",
        day_range=(100, 120),
        water_kc=0.60,
        water_mm_per_week=20,
        critical_nutrients=["Potassium"],
        key_activities=[
            "Reduce irrigation 7-10 days before harvest to concentrate sugars",
            "Harvest when skin is uniformly tan and hard (thumbnail test)",
            "Cut fruit with 5 cm stem stub to prevent rot entry",
            "Cure fruit in shade at 25-30°C for 7-10 days to harden skin",
        ],
        risks=[
            "Overwatering delays maturity and reduces storage life",
            "Mechanical damage during harvest opens infection sites",
            "Sunscald on exposed fruit if vines have defoliated",
            "Post-harvest rots if curing is skipped",
        ],
        scientific_notes=(
            "Maturation is marked by peduncle lignification, skin hardening (increased suberin "
            "and wax deposition), and carotenoid accumulation giving the characteristic tan colour. "
            "Starch-to-sugar conversion continues post-harvest during curing. Properly cured fruit "
            "can store for 3-6 months at 12-15°C due to intact cuticle barrier. The stem stub "
            "dries and seals, preventing pathogen ingress through the peduncle wound."
        ),
    ),
]

BUTTERNUT_FERTILIZER = FertilizerSchedule(
    basal={
        "product": "Compound S (7-21-8)",
        "rate_kg_ha": 300,
        "timing": "At planting, banded 5 cm below and to the side of seed",
        "nutrients_supplied": {"N": 21, "P": 63, "K": 24},
        "notes": "High P for root establishment. Place below seed, never in contact with seed.",
    },
    top_dress_1={
        "product": "Ammonium Nitrate (AN 34.5%)",
        "rate_kg_ha": 200,
        "timing": "25-30 days after emergence, at start of vine elongation",
        "nutrients_supplied": {"N": 69},
        "notes": "Side-dress 10 cm from plant base. Irrigate immediately after application.",
    },
    top_dress_2={
        "product": "Ammonium Nitrate (AN 34.5%)",
        "rate_kg_ha": 100,
        "timing": "At early fruit set (70-75 days)",
        "nutrients_supplied": {"N": 34.5},
        "notes": "Support fruit development. Reduce rate if vine growth is excessive.",
    },
    foliar={
        "product": "Solubor (Boron) + Calcium chloride",
        "rate": "Solubor 1 g/L + CaCl2 3 g/L",
        "timing": "At flowering and early fruit set",
        "notes": "Boron for pollination and fruit set; calcium for blossom end rot prevention.",
    },
    liming={
        "ite": "Agricultural lime (ite calcitic or dolomitic)",
        "rate_kg_ha": "500-1000 based on soil test",
        "timing": "4-6 weeks before planting, incorporated into topsoil",
        "target_ph": "6.0-6.8",
        "notes": "Dolomitic lime preferred on Mg-deficient granite sands.",
    },
    notes=(
        "Total seasonal NPK target: approximately 120-130 kg N/ha, 60 kg P/ha, 24 kg K/ha. "
        "Butternut has moderate fertility needs. Excessive nitrogen promotes vine growth "
        "at the expense of fruit. On sandy soils, split nitrogen into 3 applications."
    ),
)

BUTTERNUT_PLANTING_WINDOWS: List[PlantingWindow] = [
    PlantingWindow(
        region="NR I (Eastern Highlands)",
        optimal_start="September 15",
        optimal_end="November 15",
        acceptable_start="September 1",
        acceptable_end="December 15",
        notes="Cool highlands; earlier planting for frost-free period. Second crop possible Feb-Mar.",
    ),
    PlantingWindow(
        region="NR II (Highveld)",
        optimal_start="October 1",
        optimal_end="November 30",
        acceptable_start="September 15",
        acceptable_end="December 31",
        notes="Main summer planting with onset of rains. Irrigated crops can plant earlier.",
    ),
    PlantingWindow(
        region="NR III (Midlands)",
        optimal_start="October 15",
        optimal_end="November 30",
        acceptable_start="October 1",
        acceptable_end="December 15",
        notes="Plant with first reliable rains. Supplementary irrigation beneficial.",
    ),
    PlantingWindow(
        region="NR IV (Lowveld drier)",
        optimal_start="November 1",
        optimal_end="December 15",
        acceptable_start="October 15",
        acceptable_end="January 15",
        notes="Requires irrigation. Hot conditions accelerate maturity. Watch for fruit fly pressure.",
    ),
    PlantingWindow(
        region="NR V (Lowveld arid)",
        optimal_start="November 15",
        optimal_end="December 31",
        acceptable_start="November 1",
        acceptable_end="January 31",
        notes="Only viable under full irrigation. Very high pest pressure from fruit flies.",
    ),
]

PROFILE = CropProfile(
    crop_name="Butternut",
    scientific_name="Cucurbita moschata",
    family="Cucurbitaceae",
    optimal_ph=(6.0, 6.8),
    critical_ph_low=5.0,
    optimal_soil_types=["Fersiallitic red clays", "Siallitic alluvial soils", "Well-drained sandy loams"],
    avoid_soil_types=["Waterlogged vertisols", "Lithosols (shallow, rocky)", "Heavy clays with poor drainage"],
    optimal_temp=(20.0, 30.0),
    critical_temp_low=10.0,
    critical_temp_high=38.0,
    base_temp_gdd=10.0,
    total_water_mm=400.0,
    growth_stages=BUTTERNUT_GROWTH_STAGES,
    fertilizer_schedule=BUTTERNUT_FERTILIZER,
    diseases=BUTTERNUT_DISEASES,
    pests=BUTTERNUT_PESTS,
    planting_windows=BUTTERNUT_PLANTING_WINDOWS,
    harvest_moisture="Harvest when fruit skin is hard and uniformly tan; dry matter > 20%",
    storage_conditions=(
        "Cure at 25-30°C and 80% RH for 7-10 days. Store at 12-15°C and 50-70% RH. "
        "Well-cured fruit stores for 3-6 months. Avoid temperatures below 10°C (chilling injury)."
    ),
    post_harvest_notes=(
        "Handle carefully to avoid skin damage. Leave 5 cm stem stub. Do not wash before storage. "
        "Grade by size: Small (<1 kg), Medium (1-2 kg), Large (>2 kg). "
        "For market, uniform shape and tan colour command premium prices."
    ),
    natural_region_suitability={
        "NR I": "Suitable; cool conditions extend season but lower pest pressure",
        "NR II": "Excellent; ideal temperature and rainfall for dryland production",
        "NR III": "Good with supplementary irrigation; main smallholder production zone",
        "NR IV": "Feasible under irrigation; high fruit fly pressure",
        "NR V": "Only under full irrigation; heat stress and pest management critical",
    },
)

ALIASES = ["butternut squash"]
