"""Tomato (Solanum lycopersicum) — most widely grown vegetable in Zimbabwe, year-round production with irrigation."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List, Dict, Any


# TOMATO (Solanum lycopersicum)
# ---------------------------------------------------------------------------

_diseases: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Early Blight",
        pathogen="Alternaria solani",
        pathogen_type="fungal",
        symptoms=[
            "Dark brown spots with concentric rings (target-board pattern) on older leaves",
            "Spots enlarge and coalesce, causing defoliation from base upward",
            "Stem lesions: dark, sunken, elongated cankers at or above soil line",
            "Fruit lesions: dark, leathery, concentric-ringed spots near calyx end",
        ],
        identification_markers=[
            "Concentric ring pattern within spots — diagnostic 'target spot'",
            "Starts on OLDEST (lowest) leaves",
            "Yellowing (chlorotic halo) around lesions",
        ],
        favourable_conditions={"temp_min_c": 20, "temp_max_c": 30, "humidity_min": 70},
        susceptible_stages=["Vegetative", "Flowering", "Fruit Set", "Fruit Ripening"],
        resistant_varieties=["Tengeru 97 (moderate tolerance)"],
        susceptible_varieties=["Heinz 1370", "Rodade"],
        chemical_control=[
            {"name": "Mancozeb 80 WP", "rate": "2.0-2.5 kg/ha",
             "phi_days": "7", "notes": "Protectant; apply from transplant at 7-10 day intervals"},
            {"name": "Azoxystrobin 250 SC (Amistar)", "rate": "0.5 L/ha",
             "phi_days": "3", "notes": "Strobilurin; excellent curative and protectant activity. Max 3 apps/season."},
            {"name": "Chlorothalonil 500 SC", "rate": "2.0 L/ha",
             "phi_days": "7", "notes": "Broad-spectrum protectant; good rotation partner for systemics"},
        ],
        biological_control=[
            "Trichoderma harzianum soil applications to suppress soil-borne inoculum",
            "Bacillus subtilis foliar sprays",
        ],
        cultural_control=[
            "Stake and prune plants to improve air circulation",
            "Remove lower leaves touching soil (splash zone)",
            "Rotate with non-solanaceous crops for 3 years",
            "Use drip irrigation — avoid wetting foliage",
            "Mulch to prevent soil splash onto lower leaves",
        ],
        economic_threshold="5% leaf area affected on lower canopy at early fruiting stage",
        severity_scale={
            "mild": "< 10% lower leaves affected, no fruit symptoms",
            "moderate": "10-30% leaf area, defoliation advancing, scattered fruit lesions",
            "severe": "> 30% canopy lost, fruit exposed to sunscald, significant yield loss",
        },
    ),
    DiseaseProfile(
        name="Late Blight",
        pathogen="Phytophthora infestans",
        pathogen_type="oomycete",
        symptoms=[
            "Water-soaked grey-green lesions on leaves, expanding rapidly",
            "White sporulation on leaf undersides in humid conditions",
            "Stems develop dark brown lesions and collapse",
            "Fruit develops firm, brown, greasy-looking rot",
        ],
        identification_markers=[
            "White cottony growth on leaf undersides — diagnostic",
            "Lesions spread extremely rapidly in cool, wet weather",
            "Affected tissue has a musty, distinctive smell",
        ],
        favourable_conditions={"temp_min_c": 10, "temp_max_c": 22, "humidity_min": 90},
        susceptible_stages=["Vegetative", "Flowering", "Fruit Set", "Fruit Ripening"],
        resistant_varieties=["Star 9009 (moderate)"],
        susceptible_varieties=["Heinz 1370", "Rodade"],
        chemical_control=[
            {"name": "Metalaxyl + Mancozeb (Ridomil Gold MZ 68 WG)", "rate": "2.5 kg/ha",
             "phi_days": "14", "notes": "Systemic + protectant; apply preventively. Max 3 apps/season."},
            {"name": "Cymoxanil + Mancozeb", "rate": "2.5 kg/ha",
             "phi_days": "7", "notes": "Translaminar; good kickback activity if early symptoms found"},
            {"name": "Mancozeb 80 WP", "rate": "2.5 kg/ha",
             "phi_days": "7", "notes": "Protectant; apply at 5-7 day intervals during high-risk periods"},
        ],
        biological_control=[
            "Copper hydroxide (organic-approved) as protectant",
            "Bacillus subtilis and Trichoderma-based products",
        ],
        cultural_control=[
            "Avoid planting near potato fields (shared pathogen)",
            "Ensure good air circulation — wide spacing, staking",
            "Remove and destroy infected plants immediately",
            "Avoid overhead irrigation",
            "Plant during warm, dry season when disease pressure is lower",
        ],
        economic_threshold="First lesion found — spray immediately. Late blight is explosive.",
        severity_scale={
            "mild": "Scattered lesions on < 5% of plants",
            "moderate": "5-20% of canopy affected, spreading",
            "severe": "> 20% canopy destroyed, fruit rot appearing, crop loss imminent",
        },
    ),
    DiseaseProfile(
        name="Bacterial Wilt",
        pathogen="Ralstonia solanacearum",
        pathogen_type="bacterial",
        symptoms=[
            "Sudden, permanent wilting of entire plant or individual stems",
            "Brown discolouration of vascular tissue in stem cross-section",
            "Milky white bacterial ooze from cut stems placed in water",
            "Plants may initially wilt during hot afternoons and recover at night",
        ],
        identification_markers=[
            "STEM CUT TEST: cut stem at base, place in clear water — milky white streaming confirms Ralstonia",
            "Vascular browning visible in stem cross-section",
            "No leaf spots — just sudden wilt",
        ],
        favourable_conditions={"temp_min_c": 25, "temp_max_c": 37, "humidity_min": 70},
        susceptible_stages=["Vegetative", "Flowering", "Fruit Set"],
        resistant_varieties=["Tengeru 97 (partial resistance)", "Star 9009 (moderate tolerance)"],
        susceptible_varieties=["Heinz 1370", "Rodade"],
        chemical_control=[
            {"name": "No effective chemical control", "rate": "N/A",
             "phi_days": "N/A", "notes": "Soil-borne pathogen; no chemical cure. Prevention is key."},
        ],
        biological_control=[
            "Trichoderma and Bacillus soil inoculants to build suppressive microbiome",
            "Grafting onto resistant rootstock (Solanum torvum) — commercial operations",
        ],
        cultural_control=[
            "Plant in fields with no history of bacterial wilt",
            "Rotate with non-solanaceous crops for 5+ years",
            "Use certified disease-free transplants",
            "Rogue and destroy infected plants immediately (burn, do not compost)",
            "Avoid moving infested soil between fields on tools/boots",
            "Use drip irrigation (overhead systems can spread pathogen)",
        ],
        economic_threshold="First wilted plant — rogue immediately. Field is compromised for Solanaceae.",
        severity_scale={
            "mild": "1-5% plants wilted, rogued promptly",
            "moderate": "5-15% plants wilted, inoculum building in soil",
            "severe": "> 15% plants wilted, field unsuitable for tomatoes/potatoes for 5+ years",
        },
    ),
    DiseaseProfile(
        name="Tomato Leaf Curl Virus (ToLCV)",
        pathogen="Tomato leaf curl virus (Begomovirus)",
        pathogen_type="viral",
        symptoms=[
            "Upward leaf curling and cupping",
            "Leaf thickening and yellowing (chlorosis)",
            "Severe stunting of plant growth",
            "Flower drop and drastically reduced fruit set",
        ],
        identification_markers=[
            "Leaves curl UPWARD (distinguishes from physiological curling)",
            "Whiteflies always present on undersides of leaves",
            "Stunting more severe in young plants",
            "Interveinal yellowing on affected leaves",
        ],
        favourable_conditions={"temp_min_c": 25, "temp_max_c": 35, "humidity_min": 50},
        susceptible_stages=["Transplant", "Vegetative", "Flowering"],
        resistant_varieties=["Star 9009 (Ty-gene resistance)", "Tengeru 97"],
        susceptible_varieties=["Heinz 1370", "Rodade", "Star 9006"],
        chemical_control=[
            {"name": "Imidacloprid 200 SL (vector control)", "rate": "0.25 L/ha",
             "phi_days": "21", "notes": "Systemic; controls whitefly vectors. Apply as soil drench at transplanting."},
            {"name": "Pyriproxyfen 10 EC", "rate": "0.5 L/ha",
             "phi_days": "14", "notes": "IGR; disrupts whitefly development. Use in rotation with adulticides."},
        ],
        biological_control=[
            "Encarsia formosa — parasitoid wasp for whitefly biocontrol",
            "Yellow sticky traps for mass-trapping whitefly adults",
            "Neem-based sprays to deter whitefly feeding",
        ],
        cultural_control=[
            "Plant ToLCV-resistant varieties (most important measure)",
            "Use insect-proof netting in seedling nurseries",
            "Rogue out infected plants early — they become virus reservoirs",
            "Avoid planting new tomato crops adjacent to old, infected crops",
            "Weed control — remove alternate whitefly hosts",
            "Reflective mulch (silver/aluminium) deters whitefly landing",
        ],
        economic_threshold="5% plants showing leaf curl symptoms; focus on whitefly control",
        severity_scale={
            "mild": "< 5% plants infected, vigorous growth continues",
            "moderate": "5-20% plants infected, yield reduction 20-40%",
            "severe": "> 20% plants infected, crop may be uneconomic to maintain",
        },
    ),
]

_pests: List[PestProfile] = [
    PestProfile(
        name="Whitefly",
        scientific_name="Bemisia tabaci",
        pest_type="insect",
        identification=[
            "Tiny (1-1.5 mm) white-winged insects on leaf undersides",
            "Fly up in a 'cloud' when plants are disturbed",
            "Nymphs: flat, oval, translucent scales on leaf undersides",
            "Eggs: tiny, elongated, laid in circular patterns on young leaves",
        ],
        damage_symptoms=[
            "Honeydew production leading to sooty mould",
            "Virus transmission: ToLCV (most damaging), TYLCV, ToMV",
            "Leaf chlorosis and reduced vigour under heavy infestations",
            "Uneven ripening of fruit (whitefly toxin injection)",
        ],
        life_cycle_notes="Egg to adult 21-28 days at 25°C. Female lays 150-300 eggs on leaf undersides. "
                         "Nymphal stages are sedentary (scale-like) and feed on phloem sap. "
                         "Adults are highly mobile and can migrate long distances. "
                         "Bemisia tabaci B-biotype is the most efficient ToLCV vector.",
        favourable_conditions={"temp_min_c": 20, "temp_max_c": 35, "humidity_min": 40},
        susceptible_stages=["Transplant", "Vegetative", "Flowering", "Fruit Set"],
        economic_threshold="3-5 adults per leaf (check 3rd leaf from top); any virus symptoms warrant action",
        chemical_control=[
            {"name": "Imidacloprid 200 SL", "rate": "0.25 L/ha",
             "phi_days": "21", "notes": "Systemic; apply as drench at transplanting for 3-4 week protection"},
            {"name": "Spiromesifen 240 SC", "rate": "0.5 L/ha",
             "phi_days": "3", "notes": "Lipid synthesis inhibitor; effective against nymphs and eggs"},
            {"name": "Pyriproxyfen 10 EC", "rate": "0.5 L/ha",
             "phi_days": "14", "notes": "IGR; prevents nymph development. Rotate with adulticides."},
        ],
        biological_control=[
            "Encarsia formosa parasitoid wasp (greenhouse/tunnel production)",
            "Eretmocerus eremicus parasitoid",
            "Yellow sticky traps for monitoring and mass-trapping",
            "Neem oil/extract (Azadirachtin) as feeding deterrent",
        ],
        cultural_control=[
            "Use insect-proof net covers on seedling nurseries",
            "Reflective mulch (silver plastic) deters whitefly landing",
            "Maintain crop-free period (2-3 months) between tomato cycles",
            "Remove weed hosts and old crop residue",
            "Do not plant new tomato crops downwind of infected fields",
        ],
        scouting_protocol="From transplanting, inspect 20 plants twice weekly (5 per quadrant). "
                          "Turn over the 3rd fully expanded leaf from the growing tip and count adults. "
                          "Check for nymphs on older leaves with hand lens. "
                          "Install yellow sticky traps (1 per 500 m2) at canopy height. "
                          "Record trap counts weekly. Check for virus symptoms on every visit.",
    ),
    PestProfile(
        name="Tomato Leaf Miner (Tuta absoluta)",
        scientific_name="Tuta absoluta",
        pest_type="insect",
        identification=[
            "Adult: small (5-7 mm) grey-brown moth, narrow wings",
            "Larva: cream to green, up to 8 mm, with dark head",
            "Leaf mines: irregular, blotch-shaped, often near midrib",
            "Frass visible inside leaf mines",
        ],
        damage_symptoms=[
            "Serpentine and blotch mines in leaves (transparent from above)",
            "Larvae bore into fruit — entry holes with frass near calyx",
            "Stems mined, causing wilting of upper portions",
            "Severe defoliation under heavy infestation",
            "Fruit losses of 50-100% if uncontrolled",
        ],
        life_cycle_notes="Complete cycle 26-38 days. Female lays 250-300 eggs singly on leaves, stems, "
                         "and fruit calyces. 4 larval instars; larvae mine leaves and bore into stems/fruit. "
                         "Pupation in soil, leaf litter, or within mines. Multiple overlapping generations. "
                         "Arrived in Zimbabwe ~2016 and is now a key pest of tomato.",
        favourable_conditions={"temp_min_c": 18, "temp_max_c": 32, "humidity_min": 50},
        susceptible_stages=["Vegetative", "Flowering", "Fruit Set", "Fruit Ripening"],
        economic_threshold="20 moths per pheromone trap per week, or 30% of leaves with active mines",
        chemical_control=[
            {"name": "Emamectin benzoate 5 SG", "rate": "0.3 kg/ha",
             "phi_days": "7", "notes": "Translaminar; penetrates mines to reach larvae. Most effective option."},
            {"name": "Spinosad 480 SC", "rate": "0.1 L/ha",
             "phi_days": "3", "notes": "Natural product; effective against young larvae. Rotate to prevent resistance."},
            {"name": "Chlorantraniliprole 200 SC (Coragen)", "rate": "0.15 L/ha",
             "phi_days": "1", "notes": "Diamide; very effective, low toxicity to beneficials"},
        ],
        biological_control=[
            "Trichogramma pretiosum egg parasitoid",
            "Nesidiocoris tenuis — predatory mirid bug (eats eggs and young larvae)",
            "Bacillus thuringiensis var. kurstaki for young larvae",
            "Pheromone traps for mass-trapping (20-40 traps/ha)",
        ],
        cultural_control=[
            "Install pheromone traps at transplanting to detect first arrival",
            "Use insect-proof net tunnels where economically feasible",
            "Remove and destroy infested leaves and fruit",
            "Plough crop residue immediately after final harvest",
            "Maintain a 2-month crop-free period for tomato",
            "Do not plant new crop adjacent to old infested crop",
        ],
        scouting_protocol="Install delta pheromone traps at transplanting (1 per 0.25 ha). "
                          "Check traps twice weekly. Inspect 20 plants for leaf mines — "
                          "hold leaves up to light to see active mines with larvae inside. "
                          "Check fruit for entry holes, especially near calyx. "
                          "Record percentage of leaves with active mines. Scout twice weekly minimum.",
    ),
    PestProfile(
        name="African Bollworm / Tomato Fruitworm",
        scientific_name="Helicoverpa armigera",
        pest_type="insect",
        identification=[
            "Adult: medium moth (35-40 mm wingspan), straw-coloured to brown",
            "Larva: variable colour (green, brown, pink), up to 40 mm, with lateral stripes",
            "Eggs: small, spherical, ribbed, laid singly on flowers and young fruit",
            "Larva bores into fruit leaving large entry holes",
        ],
        damage_symptoms=[
            "Large (5-10 mm) entry holes in fruit, usually near calyx",
            "Internal feeding — larvae consume fruit flesh and seeds",
            "Secondary rot enters through larval feeding holes",
            "Fruit drops prematurely",
        ],
        life_cycle_notes="Complete cycle 30-40 days. Highly polyphagous — also attacks cotton, maize, sorghum. "
                         "Female lays 500-1000 eggs; single eggs on flowers and fruit. "
                         "Late instars are difficult to control chemically due to boring habit. "
                         "Pupation in soil at 5-10 cm depth.",
        favourable_conditions={"temp_min_c": 20, "temp_max_c": 35, "humidity_min": 50},
        susceptible_stages=["Flowering", "Fruit Set", "Fruit Ripening"],
        economic_threshold="1 larva per 20 plants, or 5% of fruit with entry holes",
        chemical_control=[
            {"name": "Emamectin benzoate 5 SG", "rate": "0.3 kg/ha",
             "phi_days": "7", "notes": "Effective against young larvae before they bore in"},
            {"name": "Indoxacarb 150 SC", "rate": "0.25 L/ha",
             "phi_days": "5", "notes": "Oxadiazine; excellent for Helicoverpa, reduced risk to beneficials"},
            {"name": "Lambda-cyhalothrin 5 EC", "rate": "0.4 L/ha",
             "phi_days": "7", "notes": "Broad-spectrum; use only if infestation is severe"},
        ],
        biological_control=[
            "Trichogramma egg parasitoids (release at 50,000-100,000 per ha)",
            "Nuclear polyhedrosis virus (HaNPV) specific to Helicoverpa",
            "Bacillus thuringiensis var. kurstaki (Bt) for young larvae",
        ],
        cultural_control=[
            "Handpick and destroy larvae and infested fruit (smallholder level)",
            "Intercrop with basil or marigold to deter oviposition",
            "Destroy crop residue and plough to expose pupae",
            "Avoid planting tomato adjacent to cotton or maize (alternate hosts)",
        ],
        scouting_protocol="From first flowering, inspect 20 plants twice weekly. "
                          "Check flowers for eggs (tiny, ribbed spheres). "
                          "Examine developing fruit near calyx for entry holes and frass. "
                          "Shake plants gently over a white sheet to dislodge larvae. "
                          "Record larvae per plant and % fruit damaged.",
    ),
    PestProfile(
        name="Red Spider Mite",
        scientific_name="Tetranychus urticae / T. evansi",
        pest_type="mite",
        identification=[
            "Tiny (0.5 mm), reddish to greenish-yellow mites on leaf undersides",
            "Fine silk webbing visible between leaves in heavy infestations",
            "Use hand lens (10x) to confirm — mites have 8 legs (not insects)",
            "T. evansi: red, more damaging than T. urticae in warm climates",
        ],
        damage_symptoms=[
            "Fine yellow stippling on upper leaf surface",
            "Leaves become bronze/brown and crispy in severe infestations",
            "Webbing covers leaves and growing points",
            "Premature defoliation — fruit exposed to sunscald",
            "Stunted growth and reduced fruit size",
        ],
        life_cycle_notes="Egg to adult 7-14 days depending on temperature. Populations explode in hot, "
                         "dry weather. Female lays 100+ eggs on leaf undersides. Thrives when humidity is low "
                         "and natural enemies are killed by broad-spectrum insecticides.",
        favourable_conditions={"temp_min_c": 25, "temp_max_c": 40, "humidity_min": 20},
        susceptible_stages=["Vegetative", "Flowering", "Fruit Set", "Fruit Ripening"],
        economic_threshold="5 mites per leaf with stippling symptoms, or first sign of webbing",
        chemical_control=[
            {"name": "Abamectin 18 EC", "rate": "0.5 L/ha",
             "phi_days": "7", "notes": "Translaminar; excellent miticide. Apply with good coverage to leaf undersides."},
            {"name": "Spiromesifen 240 SC", "rate": "0.5 L/ha",
             "phi_days": "3", "notes": "Lipid biosynthesis inhibitor; effective against all stages including eggs"},
        ],
        biological_control=[
            "Phytoseiulus persimilis — predatory mite, voracious feeder on spider mites",
            "Amblyseius californicus — predatory mite, tolerant of hot conditions",
            "Avoid broad-spectrum insecticides that kill mite predators",
        ],
        cultural_control=[
            "Maintain adequate irrigation — drought-stressed plants are more susceptible",
            "Avoid dusty conditions near fields (dust suppresses mite predators)",
            "Overhead irrigation temporarily knocks mite populations down",
            "Destroy old crop residue promptly after harvest",
        ],
        scouting_protocol="From 3 weeks after transplanting, inspect 20 plants weekly. "
                          "Use 10x hand lens to examine undersides of middle-canopy leaves. "
                          "Count mites per leaf on 3 leaves per plant. Look for stippling, "
                          "bronzing, and webbing. Mites increase rapidly — scout more frequently "
                          "in hot, dry weather (twice weekly). Check for predatory mites too.",
    ),
]

_growth_stages: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Transplant Establishment",
        stage_code="T",
        day_range=(0, 14),
        water_kc=0.40,
        water_mm_per_week=20,
        critical_nutrients=["P"],
        key_activities=[
            "Transplant 4-6 week old seedlings (4-5 true leaves)",
            "Water immediately after transplanting — settle root zone",
            "Apply Imidacloprid drench at transplanting for whitefly protection",
            "Install stakes or trellising within 2 weeks",
            "Spacing: 1.0-1.2 m between rows, 0.4-0.5 m in-row",
        ],
        risks=["Transplant shock if roots are damaged", "Cutworm damage at soil line",
               "Whitefly colonisation from nearby crops"],
        scientific_notes="Transplanting is preferred over direct seeding in Zimbabwe for earlier harvest "
                         "and better stand establishment. Harden seedlings for 5-7 days before transplanting "
                         "by reducing irrigation. Transplant in the late afternoon to reduce transplant shock. "
                         "Phosphorus at transplanting promotes rapid root establishment.",
    ),
    GrowthStageRequirements(
        stage_name="Vegetative Growth",
        stage_code="VEG",
        day_range=(14, 35),
        water_kc=0.60,
        water_mm_per_week=30,
        critical_nutrients=["N", "P", "Mg"],
        key_activities=[
            "First top-dressing of N (LAN/AN)",
            "Train plants onto stakes — remove side shoots below first flower truss",
            "Begin fungicide programme (Mancozeb alternating with systemics)",
            "Weed control — hand hoe or mulch between rows",
        ],
        risks=["Excessive N produces lush growth but delays flowering",
               "Early blight starting on lower leaves",
               "Whitefly and Tuta absoluta colonisation"],
        scientific_notes="Vegetative growth builds the photosynthetic canopy that will support fruit production. "
                         "Indeterminate varieties require staking and pruning to single or double stem "
                         "for optimal fruit size and air circulation. Determinate (bush) types for processing "
                         "are grown unsupported. N management is critical — excess promotes vegetative growth "
                         "at the expense of fruit set.",
    ),
    GrowthStageRequirements(
        stage_name="Flowering",
        stage_code="FL",
        day_range=(35, 50),
        water_kc=0.80,
        water_mm_per_week=38,
        critical_nutrients=["K", "Ca", "B"],
        key_activities=[
            "Apply second N top-dressing",
            "Begin K supplementation for fruit quality",
            "Scout for Tuta absoluta — check leaf mines and pheromone traps",
            "Monitor whitefly pressure for virus management",
            "Ensure pollination — tap stakes to aid pollen release",
        ],
        risks=["High temperature (>35°C) causes poor fruit set and blossom drop",
               "Tuta absoluta leaf mining reduces photosynthesis",
               "Bacterial wilt symptoms may first appear at this stage"],
        scientific_notes="Tomato is self-pollinating but wind or mechanical vibration improves pollen release. "
                         "Optimum temperature for fruit set is 21-29°C. Above 35°C day / 21°C night, "
                         "pollen viability drops dramatically (parthenocarpic fruit or blossom drop). "
                         "Calcium begins to be important for preventing blossom end rot in developing fruit.",
    ),
    GrowthStageRequirements(
        stage_name="Fruit Set & Development",
        stage_code="FS",
        day_range=(50, 70),
        water_kc=0.95,
        water_mm_per_week=45,
        critical_nutrients=["K", "Ca", "B"],
        key_activities=[
            "Increase K applications — K drives sugar and lycopene accumulation",
            "Apply calcium nitrate foliar spray to prevent blossom end rot",
            "Continue Tuta and bollworm scouting — fruit now at risk",
            "Maintain consistent irrigation — irregular watering causes BER and cracking",
        ],
        risks=["Blossom end rot (Ca deficiency / irregular watering)",
               "Fruit cracking from uneven irrigation",
               "Bollworm and Tuta boring into developing fruit",
               "Late blight in cool, wet conditions"],
        scientific_notes="Blossom end rot (BER) is a Ca-deficiency disorder caused by poor Ca translocation "
                         "to the distal end of the fruit, exacerbated by moisture stress and high transpiration. "
                         "It is a physiological disorder, not a pathogen. Consistent irrigation is more important "
                         "than Ca application alone. K is the most important nutrient during fruit development — "
                         "it drives acid/sugar balance, colour, and firmness.",
    ),
    GrowthStageRequirements(
        stage_name="Fruit Ripening",
        stage_code="FR",
        day_range=(70, 90),
        water_kc=0.85,
        water_mm_per_week=38,
        critical_nutrients=["K"],
        key_activities=[
            "Begin harvesting at breaker stage (first colour change) for distant markets",
            "Harvest at table-ripe stage for local markets",
            "Continue pest management — fruit is most valuable now",
            "Reduce N application — excess N delays ripening",
        ],
        risks=["Sunscald on fruit exposed by defoliation",
               "Fruit fly damage on ripe/overripe fruit",
               "Rain damage — splitting and rot on ripe fruit"],
        scientific_notes="Tomato is a climacteric fruit — it continues to ripen after harvest if picked at "
                         "mature green or breaker stage. Ethylene triggers ripening: chlorophyll degrades, "
                         "lycopene and beta-carotene accumulate. Optimum ripening temperature is 20-25°C. "
                         "Below 13°C, ripening is inhibited (chilling injury). Harvesting at breaker stage "
                         "extends shelf life from 4-5 days (vine-ripe) to 10-14 days.",
    ),
    GrowthStageRequirements(
        stage_name="Extended Harvest (Indeterminate types)",
        stage_code="EH",
        day_range=(90, 120),
        water_kc=0.75,
        water_mm_per_week=30,
        critical_nutrients=["K", "Ca"],
        key_activities=[
            "Continue harvesting every 3-5 days",
            "Remove old, exhausted trusses and yellowing leaves",
            "Maintain fungicide and pest management programme",
            "Gradually reduce irrigation as final trusses ripen",
        ],
        risks=["Plant exhaustion — declining fruit size and quality",
               "Disease pressure accumulates on ageing canopy",
               "Economic decision: when to terminate crop"],
        scientific_notes="Indeterminate tomato varieties can produce for 4-6 months with good management. "
                         "Fruit size and quality decline as the plant ages and pest/disease pressure accumulates. "
                         "The economic decision to terminate depends on market price vs. management costs. "
                         "Determinate varieties are harvested in 2-3 concentrated picks.",
    ),
]

_fertilizer = FertilizerSchedule(
    basal={
        "product": "Compound S (7:21:8) or Compound C (5:15:12)",
        "rate": "600-800 kg/ha Compound S",
        "timing": "At transplanting, banded 10 cm beside and below transplant hole",
        "nutrients_supplied": {"N": "42-56 kg", "P": "126-168 kg P2O5", "K": "48-64 kg K2O"},
        "scientific_basis": "High P at transplanting promotes rapid root establishment. "
                            "Compound S or C preferred for balanced NPK. "
                            "Do not place fertiliser directly against roots — burn risk.",
    },
    top_dress_1={
        "product": "Ammonium Nitrate (AN) 34.5% N",
        "rate": "200 kg/ha",
        "timing": "21-28 DAT (days after transplanting)",
        "application": "Side-dress 10 cm from stem, irrigate in",
        "scientific_basis": "First N top-dressing supports vegetative canopy development. "
                            "Avoid excessive rates that promote rank growth at expense of fruiting.",
    },
    top_dress_2={
        "product": "Potassium Nitrate (KNO3) or AN + KCl",
        "rate": "150 kg/ha KNO3 or 100 kg/ha AN + 100 kg/ha KCl",
        "timing": "At first fruit set (45-50 DAT)",
        "application": "Side-dress or fertigation",
        "scientific_basis": "K demand increases sharply at fruit set. K drives sugar accumulation, "
                            "lycopene development, and fruit firmness. Shift fertiliser programme from "
                            "N-heavy to K-heavy at this stage.",
    },
    foliar={
        "product": "Calcium Nitrate + Boron (Solubor)",
        "rate": "5 kg/ha Ca(NO3)2 + 0.5 kg/ha Solubor in 200 L water",
        "timing": "Weekly from first fruit set to mid-harvest",
        "scientific_basis": "Foliar Ca helps prevent blossom end rot. B supports pollination and fruit set. "
                            "Foliar application supplements soil-applied Ca during peak demand.",
    },
    liming={
        "product": "Dolomitic lime",
        "rate": "2-3 t/ha if pH < 5.5",
        "timing": "3-6 months before transplanting",
        "scientific_basis": "Target pH 6.0-6.5 for optimal nutrient availability. "
                            "Dolomitic lime supplies Mg which tomato requires in moderate amounts.",
    },
    notes="Total nutrient requirement for 60-80 t/ha yield: 200-250 kg N, 150-200 kg P2O5, "
          "250-350 kg K2O per ha. Use fertigation for precise nutrient delivery in drip-irrigated systems. "
          "Shift N:K ratio from 1:1 during vegetative stage to 1:2 during fruiting.",
)

_planting_windows: List[PlantingWindow] = [
    PlantingWindow(
        region="Natural Region I (Eastern Highlands)",
        optimal_start="August 1", optimal_end="September 30",
        acceptable_start="July 1", acceptable_end="March 31",
        notes="Year-round production possible with irrigation. Main season: Aug-Sep transplanting "
              "for summer harvest. Frost-free areas only.",
    ),
    PlantingWindow(
        region="Natural Region II (Highveld)",
        optimal_start="August 15", optimal_end="October 15",
        acceptable_start="February 1", acceptable_end="November 30",
        notes="Main season: spring transplanting (Aug-Oct) for summer/autumn harvest. "
              "Winter production only in frost-free areas with irrigation. "
              "Avoid transplanting in June-July (frost risk).",
    ),
    PlantingWindow(
        region="Natural Region III",
        optimal_start="August 1", optimal_end="October 31",
        acceptable_start="February 1", acceptable_end="November 30",
        notes="Irrigation essential. Spring/summer planting preferred. "
              "Hot-season production requires heat-tolerant varieties.",
    ),
    PlantingWindow(
        region="Natural Region IV",
        optimal_start="February 1", optimal_end="April 30",
        acceptable_start="January 15", acceptable_end="May 31",
        notes="Irrigated production only. Avoid hottest months (Oct-Dec) — poor fruit set above 35°C. "
              "Autumn/winter production ideal if frost-free.",
    ),
    PlantingWindow(
        region="Natural Region V (Lowveld)",
        optimal_start="March 1", optimal_end="May 31",
        acceptable_start="February 15", acceptable_end="June 30",
        notes="Winter/cool season production with irrigation. Summer is too hot for fruit set. "
              "Major commercial production area (Lowveld estates).",
    ),
]

PROFILE = CropProfile(
    crop_name="Tomato",
    scientific_name="Solanum lycopersicum L.",
    family="Solanaceae",
    optimal_ph=(6.0, 6.8),
    critical_ph_low=5.0,
    optimal_soil_types=["Well-drained sandy loams", "Red loams", "Deep fertile soils"],
    avoid_soil_types=["Waterlogged soils", "Fields with Ralstonia history",
                      "Heavy clays with poor drainage"],
    optimal_temp=(21.0, 29.0),
    critical_temp_low=5.0,
    critical_temp_high=35.0,
    base_temp_gdd=10.0,
    total_water_mm=600.0,
    growth_stages=_growth_stages,
    fertilizer_schedule=_fertilizer,
    diseases=_diseases,
    pests=_pests,
    planting_windows=_planting_windows,
    harvest_moisture="Harvest at breaker stage for distant markets (10-14 day shelf life) "
                     "or table-ripe for local sale (3-5 day shelf life).",
    storage_conditions="Store green/breaker fruit at 15-20°C for ripening. "
                       "DO NOT refrigerate below 13°C — chilling injury. "
                       "Ripe fruit: 7-10°C, 85-90% RH for 1-2 weeks maximum.",
    post_harvest_notes="Handle carefully — tomato bruises easily. "
                       "Grade by size, colour, and freedom from defects. "
                       "Zimbabwe fresh market prefers large, round, firm red fruit. "
                       "Processing varieties (Heinz 1370, Rodade) for paste/sauce.",
    natural_region_suitability={
        "I": "Excellent — year-round production possible",
        "IIa": "Excellent — main production zone, spring/summer season",
        "IIb": "Good — irrigated production",
        "III": "Good — irrigated, heat-tolerant varieties for hot season",
        "IV": "Moderate — irrigation essential, winter/cool season only",
        "V": "Good — Lowveld winter production is major commercial zone",
    },
)

ALIASES = ["tomatoes"]
