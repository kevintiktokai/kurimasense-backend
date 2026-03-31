"""Green Pepper (Capsicum annuum) — High-value vegetable crop harvested at the immature green stage."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List


GREEN_PEPPER_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Bacterial Wilt",
        pathogen="Ralstonia solanacearum",
        pathogen_type="bacterial",
        symptoms=[
            "Rapid, permanent wilting of entire plant without leaf yellowing",
            "Leaves remain green while plant collapses",
            "Brown vascular discolouration in stem cross-section",
            "Bacterial ooze visible when cut stem is immersed in clear water",
        ],
        identification_markers=[
            "Bacterial streaming test: cut stem in water shows milky ooze within 2-3 minutes",
            "Green wilt (no yellowing) distinguishes from Fusarium",
            "Rapid wilt on hot days with partial recovery at night in early stages",
        ],
        favourable_conditions={
            "soil_temp_min_c": 25, "soil_temp_max_c": 37,
            "soil_moisture": "Saturated or poorly drained",
            "note": "Warm, wet soils. Enters through root wounds from nematodes, cultivation, "
                    "or transplanting. Survives in soil indefinitely in the absence of host."
        },
        susceptible_stages=["Transplant establishment", "Vegetative growth", "Flowering"],
        resistant_varieties=[],
        susceptible_varieties=["California Wonder", "Star 9011"],
        chemical_control=[
            {"name": "No effective chemical control", "rate": "N/A",
             "phi_days": "N/A", "notes": "Systemic bactericides are not effective against soil-borne R. solanacearum"},
        ],
        biological_control=[
            "Bacillus amyloliquefaciens soil application at transplanting",
            "Trichoderma harzianum (5 g/planting hole) for competitive rhizosphere colonisation",
            "Non-pathogenic Pseudomonas fluorescens as antagonist",
        ],
        cultural_control=[
            "Rotate with non-solanaceous crops for at least 4 years",
            "Plant on raised beds (25-30 cm) for improved drainage",
            "Use pathogen-free transplants from certified nurseries",
            "Sterilise all tools with 10% sodium hypochlorite between rows",
            "Remove and burn infected plants immediately; avoid composting",
            "Amend soil with lime to raise pH above 6.5 (suppresses pathogen)",
        ],
        economic_threshold="Any confirmed bacterial wilt — immediate removal and quarantine",
        severity_scale={
            "mild": "< 3% scattered plants, isolated patches",
            "moderate": "3-15% plants lost, spreading along irrigation lines",
            "severe": "> 15% mortality — consider replanting to non-solanaceous crop",
        },
    ),
    DiseaseProfile(
        name="Phytophthora Blight",
        pathogen="Phytophthora capsici",
        pathogen_type="oomycete",
        symptoms=[
            "Dark, water-soaked lesions at stem base (collar rot)",
            "Sudden plant collapse and death",
            "Dark, oily lesions on fruit with white sporulation",
            "Roots turn brown and mushy; plants pull out easily",
        ],
        identification_markers=[
            "Dark collar rot at soil line is diagnostic",
            "White cottony mycelium on fruit lesions in high humidity",
            "Follows water drainage patterns in field — low spots worst",
            "More rapid than bacterial wilt — plant dead within 24-48 hours",
        ],
        favourable_conditions={
            "humidity_min": 90, "temp_min_c": 22, "temp_max_c": 32,
            "note": "Heavy rain, flooding, and waterlogged soils. Zoospores spread in "
                    "surface water. Furrow irrigation greatly increases risk."
        },
        susceptible_stages=["Transplant establishment", "Vegetative growth", "Fruiting"],
        resistant_varieties=[],
        susceptible_varieties=["California Wonder"],
        chemical_control=[
            {"name": "Metalaxyl + Mancozeb (Ridomil Gold MZ 68 WG)", "rate": "2.5 kg/ha",
             "phi_days": "14", "notes": "Soil drench at transplanting; repeat after heavy rains"},
            {"name": "Fosetyl-aluminium (Aliette 80 WG)", "rate": "2.5-3.0 kg/ha",
             "phi_days": "14", "notes": "Foliar + root absorbed; activates plant defence (phytoalexins)"},
            {"name": "Dimethomorph 50 WP (Forum)", "rate": "0.5 kg/ha",
             "phi_days": "7", "notes": "Oomycete-specific; alternate with metalaxyl"},
        ],
        biological_control=[
            "Trichoderma harzianum incorporated into planting beds at 5 kg/ha",
            "Bacillus subtilis (Serenade) soil drench at transplanting",
        ],
        cultural_control=[
            "Raised beds (25-30 cm) with drip irrigation mandatory in high-risk areas",
            "Never use furrow irrigation on pepper",
            "Rotate with non-solanaceous, non-cucurbit crops for 3+ years",
            "Ensure surface drainage away from field",
            "Incorporate organic matter (compost, crop residue) to improve soil structure",
        ],
        economic_threshold="First confirmed collar rot — drench surrounding area immediately",
        severity_scale={
            "mild": "< 5% plants with collar rot, isolated spots",
            "moderate": "5-20% mortality, spreading along water channels",
            "severe": "> 20% lost — economic harvest unlikely",
        },
    ),
    DiseaseProfile(
        name="Bacterial Spot",
        pathogen="Xanthomonas euvesicatoria",
        pathogen_type="bacterial",
        symptoms=[
            "Small, dark, water-soaked spots on leaves, becoming necrotic with yellow halo",
            "Leaf spots enlarge and coalesce, causing defoliation",
            "Raised, scabby lesions on fruit reduce market quality",
            "Stem cankers in severe cases",
        ],
        identification_markers=[
            "Angular, dark lesions with yellow halo (leaf)",
            "Raised, corky, scab-like spots on fruit",
            "Lesions coalesce causing tattered, shot-hole appearance in leaves",
            "Worse on lower canopy exposed to rain splash",
        ],
        favourable_conditions={
            "humidity_min": 80, "temp_min_c": 24, "temp_max_c": 30,
            "note": "Warm, wet weather with rain splash. Seed-borne and spread by "
                    "overhead irrigation. Enters through stomata and wounds."
        },
        susceptible_stages=["Vegetative growth", "Flowering", "Fruiting"],
        resistant_varieties=["Star 9011"],
        susceptible_varieties=["California Wonder"],
        chemical_control=[
            {"name": "Copper hydroxide 77 WP", "rate": "2.0-2.5 kg/ha",
             "phi_days": "7", "notes": "Protectant; apply before rain. Mix with mancozeb to reduce copper resistance"},
            {"name": "Copper hydroxide + Mancozeb tank mix", "rate": "1.5 + 2.0 kg/ha",
             "phi_days": "7", "notes": "Combination reduces bacterial resistance to copper"},
        ],
        biological_control=[
            "Bacillus subtilis sprays as preventive protectant",
            "Acibenzolar-S-methyl (Bion) for systemic acquired resistance induction",
        ],
        cultural_control=[
            "Use certified, disease-free seed treated with hot water (52°C for 25 minutes)",
            "Avoid overhead irrigation; use drip",
            "Do not work in fields when foliage is wet",
            "Rotate with non-solanaceous crops for 2-3 years",
            "Remove and destroy crop debris promptly after harvest",
        ],
        economic_threshold="5% of fruit with spot lesions, or 20% of leaves with symptoms",
        severity_scale={
            "mild": "Scattered leaf spots, < 10% leaves affected",
            "moderate": "20-40% leaves spotted, some fruit lesions, early defoliation",
            "severe": "> 50% defoliation, significant fruit damage — 40-60% unmarketable",
        },
    ),
]

GREEN_PEPPER_PESTS: List[PestProfile] = [
    PestProfile(
        name="Aphids",
        scientific_name="Myzus persicae",
        pest_type="insect",
        identification=[
            "Small (1.5-2 mm), green to yellow-green, soft-bodied insects",
            "Dense colonies on growing tips and leaf undersides",
            "Cornicles (tube-like structures) on abdomen distinguish from other small insects",
            "Winged morphs appear when populations are high",
        ],
        damage_symptoms=[
            "Leaf curling and distortion of growing points",
            "Honeydew and sooty mould reduce photosynthesis",
            "Vector for Pepper Mottle Virus, CMV, and PVY",
            "Stunted growth and reduced fruit set",
        ],
        life_cycle_notes=(
            "Parthenogenetic reproduction; one female produces 50-80 nymphs. "
            "Generation time 7-10 days at 25°C. Populations can double every 3-4 days. "
            "Winged forms disperse to colonise new fields. Natural enemies normally keep "
            "populations below economic threshold unless disrupted by broad-spectrum insecticides."
        ),
        favourable_conditions={
            "temp_min_c": 18, "temp_max_c": 28,
            "note": "Warm, dry conditions. Lush, over-fertilised crops (excess N) are highly attractive."
        },
        susceptible_stages=["Nursery seedling", "Transplant establishment", "Vegetative growth"],
        economic_threshold="20% of plants with colonies on growing tips, or virus symptoms on 2% of plants",
        chemical_control=[
            {"name": "Pirimicarb 50 WG (Pirimor)", "rate": "0.5 g/L",
             "phi_days": "3", "notes": "Selective aphicide; does not harm natural enemies"},
            {"name": "Acetamiprid 20 SP", "rate": "0.2 g/L",
             "phi_days": "7", "notes": "Systemic; effective against resistant populations"},
            {"name": "Imidacloprid 200 SL (soil drench)", "rate": "0.5 mL/L drench at transplanting",
             "phi_days": "21", "notes": "Provides 4-6 weeks systemic protection; one application only"},
        ],
        biological_control=[
            "Ladybird beetles (Hippodamia, Cheilomenes spp.) — conserve by avoiding pyrethroids",
            "Lacewing larvae (Chrysoperla carnea) — voracious generalist predator",
            "Parasitoid wasps (Aphidius colemani) cause aphid mummification",
            "Beauveria bassiana spray under humid conditions",
        ],
        cultural_control=[
            "Reflective silver mulch repels winged aphid immigrants",
            "Fine mesh netting (0.3 mm) over nursery seedbeds",
            "Avoid excessive nitrogen; maintain balanced NPK",
            "Remove solanaceous weed hosts from field margins",
            "Border rows of tall crops (maize, sorghum) as windbreak reduce winged immigration",
        ],
        scouting_protocol=(
            "Scout twice weekly from transplanting to mid-vegetative stage. "
            "Examine undersides of 3 youngest leaves on 10 plants at each of 5 points. "
            "Record aphid numbers, presence of natural enemies (mummies, ladybirds), "
            "and any virus symptoms. Use yellow pan traps to detect early winged immigrants."
        ),
    ),
    PestProfile(
        name="Fruit Borer (African Bollworm)",
        scientific_name="Helicoverpa armigera",
        pest_type="insect",
        identification=[
            "Eggs: small (0.5 mm), spherical, ribbed, laid singly on flowers and fruit",
            "Larvae: highly variable colour (green, brown, yellowish) with lateral stripes, up to 40 mm",
            "Adults: dull brown moths, 35 mm wingspan, active at dusk",
            "Pupae: brown, barrel-shaped, in soil at 5-10 cm depth",
        ],
        damage_symptoms=[
            "Larvae bore into fruit near calyx, feeding internally",
            "Entry hole with dark frass visible on fruit surface",
            "Secondary rot develops inside bored fruit",
            "Single larva can damage 3-5 fruit before pupation",
        ],
        life_cycle_notes=(
            "Polyphagous: attacks tomato, cotton, maize, beans, and peppers. "
            "Moths lay 500-1500 eggs over lifespan, preferring flowers and young fruit. "
            "Eggs hatch in 3-5 days. 6 larval instars over 14-21 days. "
            "Pupation in soil 10-14 days. 3-4 generations per Zimbabwe summer season."
        ),
        favourable_conditions={
            "temp_min_c": 20, "temp_max_c": 35,
            "note": "Warm nights with >20°C encourage moth activity. "
                    "Peak flights Oct-Dec and Feb-Mar. Adjacent tomato/cotton fields increase risk."
        },
        susceptible_stages=["Flowering", "Fruit development"],
        economic_threshold="1 larva per 10 plants, or 2% fruit with bore damage",
        chemical_control=[
            {"name": "Indoxacarb 150 SC", "rate": "0.4 mL/L",
             "phi_days": "5", "notes": "Targets young larvae; IPM-compatible"},
            {"name": "Emamectin benzoate 5 SG", "rate": "0.4 g/L",
             "phi_days": "7", "notes": "Effective on all larval instars; apply in evening"},
            {"name": "Bacillus thuringiensis (Bt) var. kurstaki", "rate": "1.0-1.5 kg/ha",
             "phi_days": "0", "notes": "Biological insecticide; only effective on L1-L3 larvae"},
        ],
        biological_control=[
            "Bt sprays targeting young larvae (L1-L3 only)",
            "Trichogramma egg parasitoids — release at flowering onset",
            "Helicoverpa NPV (nuclear polyhedrosis virus) — species-specific biopesticide",
            "Encourage insectivorous birds and predatory wasps",
        ],
        cultural_control=[
            "Install pheromone traps (1 per 2 ha) at flowering for monitoring",
            "Deep ploughing after harvest exposes pupae to predation and desiccation",
            "Avoid planting adjacent to cotton, tomato, or maize",
            "Hand-pick visible larvae on small-scale plots",
            "Remove crop residues promptly to reduce pupal survival",
        ],
        scouting_protocol=(
            "Deploy pheromone traps from pre-flowering. When moths > 10 per trap per night, "
            "begin intensive field scouting. Examine 20 plants per point at 5 locations. "
            "Check flowers for eggs and small fruit (near calyx) for entry holes and frass. "
            "Scout early morning. Record eggs, small larvae (<10 mm), large larvae, and "
            "damaged fruit separately for threshold assessment."
        ),
    ),
    PestProfile(
        name="Cutworms",
        scientific_name="Agrotis spp.",
        pest_type="insect",
        identification=[
            "Larvae: fat, smooth, grey-brown caterpillars, 30-45 mm, curl into C-shape when disturbed",
            "Adults: dull brown moths with kidney-shaped wing markings",
            "Larvae hide in soil during day, feed at night",
            "Dig around base of cut plant to find larvae",
        ],
        damage_symptoms=[
            "Seedlings and transplants cleanly severed at soil surface",
            "Plants topple over; stem cut is smooth, not chewed",
            "Damage appears in patches, worse near field margins",
            "One larva can cut 3-5 seedlings per night",
        ],
        life_cycle_notes=(
            "Moths lay eggs on soil surface or low-growing weeds. Larvae develop through "
            "6 instars over 3-4 weeks, feeding at night and hiding in soil during the day. "
            "Pupation in soil. More common in fields with recent grass or weed cover. "
            "Peak damage during first 2-3 weeks after transplanting."
        ),
        favourable_conditions={
            "temp_min_c": 15, "temp_max_c": 25,
            "note": "Cool nights. Worse in fields recently cleared of weeds or grass. "
                    "Moist soil keeps larvae near surface where they can reach stems."
        },
        susceptible_stages=["Transplant establishment", "Early vegetative growth"],
        economic_threshold="5% of transplants cut within first 2 weeks",
        chemical_control=[
            {"name": "Carbaryl 85 WP bait (bran + carbaryl)", "rate": "50 g Carbaryl per 5 kg bran, wetted",
             "phi_days": "14", "notes": "Apply bait in evening along rows; cutworms feed on bait at night"},
            {"name": "Chlorpyrifos 48 EC (soil drench)", "rate": "2.0 mL/L around transplant base",
             "phi_days": "21", "notes": "Drench planting hole at transplanting; kills larvae on contact"},
        ],
        biological_control=[
            "Entomopathogenic nematodes (Steinernema carpocapsae) — soil application",
            "Encourage natural predators: ground beetles (Carabidae), parasitic wasps",
            "Bacillus thuringiensis bait (bran + Bt suspension) — organic alternative",
        ],
        cultural_control=[
            "Clear weeds and grass 2-3 weeks before transplanting to starve larvae",
            "Flood-irrigate field before planting to expose larvae",
            "Place cardboard collars around transplant stems (3 cm into soil, 3 cm above)",
            "Dig around damaged plants to find and destroy larvae",
            "Late afternoon transplanting reduces first-night damage exposure",
        ],
        scouting_protocol=(
            "Scout transplants every morning for the first 14 days after planting. "
            "Walk rows counting cut plants. Dig around freshly cut stems to locate larvae "
            "(usually within 5-10 cm). Mark affected areas for targeted bait application. "
            "Night scouting with a torch (8-10 PM) reveals active larvae on soil surface."
        ),
    ),
]

GREEN_PEPPER_GROWTH_STAGES: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Nursery & Seedling",
        stage_code="NS",
        day_range=(0, 30),
        water_kc=0.35,
        water_mm_per_week=12,
        critical_nutrients=["Phosphorus", "Nitrogen"],
        key_activities=[
            "Sow seed in 200-cell trays with sterilised growing medium",
            "Maintain 25-30°C for germination (7-14 days emergence)",
            "Provide 50% shade cloth for first 10 days then reduce",
            "Apply liquid starter fertiliser (2:3:2 at 2 mL/L) weekly",
            "Harden off for 7-10 days before transplanting",
        ],
        risks=[
            "Damping-off (Pythium, Rhizoctonia) from overwatering",
            "Aphid colonisation and virus transmission",
            "Etiolated seedlings from insufficient light",
            "Root-bound plants from delayed transplanting",
        ],
        scientific_notes=(
            "Capsicum annuum seed requires alternating temperatures (25°C day/20°C night) "
            "for optimal germination uniformity. Photoblastic response is neutral — light "
            "is not required for germination but is critical post-emergence. Root architecture "
            "established in the seedling stage determines field establishment success. "
            "Phosphorus availability in growing media directly affects root:shoot ratio."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Transplanting & Establishment",
        stage_code="TE",
        day_range=(30, 50),
        water_kc=0.50,
        water_mm_per_week=20,
        critical_nutrients=["Phosphorus", "Calcium", "Nitrogen"],
        key_activities=[
            "Transplant at 6-8 true leaf stage",
            "Spacing: 0.9-1.0 m between rows, 0.35-0.45 m in-row",
            "Apply basal fertiliser and Metalaxyl drench at transplanting",
            "Irrigate daily for 5-7 days after transplanting",
            "Monitor and manage cutworms immediately",
        ],
        risks=[
            "Transplant shock mortality in hot, windy conditions",
            "Cutworm damage (peak risk period)",
            "Bacterial wilt introduction through root wounds",
            "Waterlogging if drainage is poor",
        ],
        scientific_notes=(
            "Transplant shock results from severed root-to-shoot hydraulic connections "
            "and temporary stomatal dysfunction. New adventitious root formation is calcium-dependent "
            "and begins 3-5 days post-transplant in warm soils. Transplanting in late afternoon "
            "minimises evapotranspiration demand during the critical first 24 hours. "
            "Establishment is defined as resumption of new leaf production (7-14 days)."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Vegetative Growth",
        stage_code="VG",
        day_range=(50, 75),
        water_kc=0.70,
        water_mm_per_week=28,
        critical_nutrients=["Nitrogen", "Potassium", "Magnesium"],
        key_activities=[
            "Apply first top-dress of AN at 200 kg/ha",
            "Cultivate for weed control or apply mulch",
            "Begin regular scouting for aphids and mites",
            "Stake or support plants if needed",
            "Initiate fungicide programme if conditions are wet",
        ],
        risks=[
            "Excessive nitrogen delays flowering",
            "Aphid build-up and virus infection",
            "Phytophthora collar rot in wet soils",
            "Weed competition reduces canopy development",
        ],
        scientific_notes=(
            "Green pepper plants exhibit sympodial (dichotomous) branching after the first "
            "fork. Each branch terminates in a flower, with two vegetative shoots continuing "
            "growth. The number of branch forks before first flower determines early vs. late "
            "maturity. Nitrogen drives leaf area index to the optimum of 3.0-4.0 for maximum "
            "light interception. Excessive N pushes vegetative growth at the expense of "
            "reproductive partitioning."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Flowering & Fruit Set",
        stage_code="FL",
        day_range=(75, 95),
        water_kc=0.95,
        water_mm_per_week=35,
        critical_nutrients=["Potassium", "Boron", "Calcium"],
        key_activities=[
            "Apply foliar calcium and boron at first flowering",
            "Maintain consistent irrigation — stress causes flower drop",
            "Deploy Helicoverpa pheromone traps",
            "Reduce nitrogen; maintain potassium for fruit quality",
            "Continue aphid and disease management",
        ],
        risks=[
            "Flower abortion from heat > 35°C or cold < 15°C",
            "Blossom end rot from calcium deficiency or water stress",
            "Bollworm oviposition on flowers and young fruit",
            "Poor pollination from rain or extreme temperatures",
        ],
        scientific_notes=(
            "Green pepper flowers are self-pollinating (cleistogamous tendency). "
            "Pollen viability is optimal at 20-25°C and declines sharply above 33°C. "
            "Fruit set requires adequate cytokinin and auxin for ovary expansion. "
            "Calcium demand peaks during rapid cell division phase (first 14 days after "
            "pollination). Boron is essential for pollen tube growth; deficiency causes "
            "flower drop and misshapen fruit."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Fruit Development",
        stage_code="FD",
        day_range=(95, 115),
        water_kc=0.90,
        water_mm_per_week=34,
        critical_nutrients=["Potassium", "Calcium", "Nitrogen"],
        key_activities=[
            "Apply second top-dress (AN 150 kg/ha + KCl 50 kg/ha)",
            "Intensify bollworm scouting and control",
            "Maintain disease management for bacterial spot",
            "Ensure consistent irrigation for uniform fruit development",
            "Begin harvesting mature green fruit at glossy-green stage",
        ],
        risks=[
            "Blossom end rot from inconsistent watering",
            "Fruit borer damage intensifies",
            "Sunscald on exposed fruit after defoliation",
            "Cracking from irregular water supply",
        ],
        scientific_notes=(
            "Green pepper fruit grows by cell division (first 14-21 days) then cell expansion. "
            "Harvest at the mature green stage captures maximum weight before colour break. "
            "Chlorophyll content is highest at this stage; ethylene-induced ripening to red "
            "is unwanted for green pepper marketing. Potassium accumulation in fruit drives "
            "sugar and acid balance. Calcium is xylem-transported to fruit via transpiration — "
            "consistent soil moisture is essential to prevent blossom end rot."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Continuous Harvest",
        stage_code="CH",
        day_range=(115, 150),
        water_kc=0.80,
        water_mm_per_week=30,
        critical_nutrients=["Potassium", "Nitrogen"],
        key_activities=[
            "Harvest every 5-7 days when fruit reaches marketable size (> 150 g)",
            "Cut fruit with short stem stub using secateurs",
            "Apply light nitrogen top-dress to maintain plant vigour",
            "Continue disease and pest management throughout harvest",
            "Grade by size and quality for market",
        ],
        risks=[
            "Harvest delay causes fruit to colour-break (reduce green pepper value)",
            "Plant exhaustion from heavy fruit load without adequate nutrition",
            "Late-season Phytophthora and bacterial spot increase",
            "Declining fruit quality as plant ages",
        ],
        scientific_notes=(
            "Capsicum annuum is indeterminate; vegetative and reproductive growth overlap. "
            "Regular harvesting stimulates new flower production through release of apical "
            "dominance and hormonal balance shift (reduced auxin from fruit, increased "
            "cytokinin from roots). A well-managed plant can produce 30-50 fruit over "
            "8-12 weeks of harvest. Maintaining leaf area index above 2.0 through balanced "
            "nutrition ensures continued photosynthate supply for new fruit."
        ),
    ),
]

GREEN_PEPPER_FERTILIZER = FertilizerSchedule(
    basal={
        "product": "Compound S (7-21-8)",
        "rate_kg_ha": 400,
        "timing": "Incorporated into beds or planting holes 3-5 days before transplanting",
        "nutrients_supplied": {"N": 28, "P": 84, "K": 32},
        "notes": "Band-place in rows. Supplement with 5-10 t/ha well-decomposed cattle manure.",
    },
    top_dress_1={
        "product": "Ammonium Nitrate (AN 34.5%)",
        "rate_kg_ha": 200,
        "timing": "3-4 weeks after transplanting (active vegetative growth)",
        "nutrients_supplied": {"N": 69},
        "notes": "Side-dress 10 cm from stem. Irrigate immediately. "
                 "Split into 2 applications on sandy soils.",
    },
    top_dress_2={
        "product": "Ammonium Nitrate (AN 34.5%) + Muriate of Potash (KCl 60%)",
        "rate_kg_ha": "AN 150 + KCl 50",
        "timing": "At first fruit set (75-80 days from transplant)",
        "nutrients_supplied": {"N": 52, "K": 30},
        "notes": "Potassium for fruit development, firmness, and shelf life.",
    },
    foliar={
        "product": "Calcium Nitrate + Solubor",
        "rate": "CaNO3 5 g/L + Solubor 1 g/L",
        "timing": "At flowering, repeated every 10-14 days through fruit development",
        "notes": "Prevents blossom end rot and improves fruit set. Apply early morning.",
    },
    liming={
        "product": "Dolomitic lime",
        "rate_kg_ha": "1000-1500 based on soil test",
        "timing": "6-8 weeks before transplanting",
        "target_ph": "6.0-6.8",
        "notes": "Critical for pH-sensitive peppers. Dolomitic lime supplies Mg for chlorophyll.",
    },
    notes=(
        "Total seasonal target: 150-180 kg N/ha, 80 kg P/ha, 60-80 kg K/ha. "
        "Green peppers have a long harvest period requiring sustained nutrition. "
        "Fertigation through drip systems is ideal for split applications. "
        "On granite sands, include Zn (ZnSO4 10 kg/ha basal) and B (Solubor foliar)."
    ),
)

GREEN_PEPPER_PLANTING_WINDOWS: List[PlantingWindow] = [
    PlantingWindow(
        region="NR I (Eastern Highlands)",
        optimal_start="August 15",
        optimal_end="October 15",
        acceptable_start="August 1",
        acceptable_end="November 30",
        notes="Nursery sow July. Frost risk limits early transplanting. Cool conditions extend harvest.",
    ),
    PlantingWindow(
        region="NR II (Highveld)",
        optimal_start="August 1",
        optimal_end="October 31",
        acceptable_start="July 15",
        acceptable_end="December 31",
        notes="Year-round production possible under irrigation. Main season Aug-Oct transplanting.",
    ),
    PlantingWindow(
        region="NR III (Midlands)",
        optimal_start="September 1",
        optimal_end="November 15",
        acceptable_start="August 15",
        acceptable_end="December 15",
        notes="Irrigation essential. Supplementary shade cloth may be needed in hot months.",
    ),
    PlantingWindow(
        region="NR IV (Semi-arid)",
        optimal_start="September 15",
        optimal_end="November 30",
        acceptable_start="September 1",
        acceptable_end="December 31",
        notes="Full irrigation mandatory. Use shade netting (30-40%) to reduce heat stress.",
    ),
    PlantingWindow(
        region="NR V (Arid Lowveld)",
        optimal_start="March 1",
        optimal_end="April 30",
        acceptable_start="February 15",
        acceptable_end="May 31",
        notes="Winter production under irrigation avoids extreme summer heat. Greenhouse/shade house preferred.",
    ),
]

PROFILE = CropProfile(
    crop_name="Green Pepper",
    scientific_name="Capsicum annuum",
    family="Solanaceae",
    optimal_ph=(6.0, 6.8),
    critical_ph_low=5.2,
    optimal_soil_types=["Fersiallitic red clays", "Siallitic alluvial soils", "Well-drained sandy loams"],
    avoid_soil_types=["Waterlogged vertisols", "Saline soils", "Acidic granite sands (unlimed)"],
    optimal_temp=(18.0, 28.0),
    critical_temp_low=10.0,
    critical_temp_high=35.0,
    base_temp_gdd=12.0,
    total_water_mm=550.0,
    growth_stages=GREEN_PEPPER_GROWTH_STAGES,
    fertilizer_schedule=GREEN_PEPPER_FERTILIZER,
    diseases=GREEN_PEPPER_DISEASES,
    pests=GREEN_PEPPER_PESTS,
    planting_windows=GREEN_PEPPER_PLANTING_WINDOWS,
    harvest_moisture=(
        "Harvest at mature green stage (glossy, firm, full size). "
        "Fruit should snap cleanly from plant. Target > 90% green colour for premium market."
    ),
    storage_conditions=(
        "Store at 7-10°C and 90-95% RH. Do not store below 7°C (chilling injury causes pitting). "
        "Shelf life 2-3 weeks under optimal conditions. Keep away from ethylene-producing fruit "
        "(bananas, tomatoes) to prevent premature ripening."
    ),
    post_harvest_notes=(
        "Grade by size: Extra Large (>200 g), Large (150-200 g), Medium (100-150 g). "
        "Pack in ventilated cartons, 5-10 kg. Remove damaged, misshapen, or blemished fruit. "
        "Pre-cool to 10°C within 2 hours of harvest for optimal shelf life. "
        "Export markets require GlobalGAP certification and MRL compliance."
    ),
    natural_region_suitability={
        "NR I": "Good; cool conditions extend harvest but limit early planting (frost risk)",
        "NR II": "Excellent — main green pepper production zone, year-round under irrigation",
        "NR III": "Good with irrigation; moderate to high yields",
        "NR IV": "Feasible under irrigation with shade management",
        "NR V": "Winter production only; requires full infrastructure (irrigation, shade)",
    },
)

ALIASES = ["bell pepper", "sweet pepper"]
