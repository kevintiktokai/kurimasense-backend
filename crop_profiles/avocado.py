"""Avocado (Persea americana) — Subtropical perennial fruit tree with high export potential."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List


AVOCADO_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Phytophthora Root Rot",
        pathogen="Phytophthora cinnamomi",
        pathogen_type="oomycete",
        symptoms=[
            "Gradual canopy thinning and pale green to yellow small leaves",
            "Wilting despite adequate soil moisture",
            "Branch die-back from tips progressing inward",
            "Dark, brittle, blackened feeder roots (white and healthy when uninfected)",
            "Reduced fruit size and yield; eventual tree death over 1-3 years",
        ],
        identification_markers=[
            "Black, brittle feeder roots (contrast with white healthy roots — key diagnostic)",
            "Canopy decline from outer edges inward",
            "Small, sparse leaves with interveinal chlorosis",
            "Often one-sided canopy decline initially",
        ],
        favourable_conditions={
            "soil_moisture": "waterlogged or saturated soils",
            "temp_min_c": 20, "temp_max_c": 30,
            "note": "Zoospores require free water for motility and infection. Any period of "
                    "waterlogging, even brief, can initiate infection. Heavy soils, poor drainage, "
                    "and excessive irrigation are primary risk factors."
        },
        susceptible_stages=["Establishment", "All production stages"],
        resistant_varieties=["Duke 7 (rootstock)", "Dusa (rootstock)", "Latas (rootstock)"],
        susceptible_varieties=["Hass on seedling rootstock", "Fuerte"],
        chemical_control=[
            {"name": "Potassium phosphonate (Phyto-Fos)", "rate": "20 ml/L trunk injection or 5 ml/L foliar",
             "phi_days": "0", "notes": "Trunk injection 2-4 times/year; most effective management tool"},
            {"name": "Metalaxyl (Ridomil Gold)", "rate": "2.5 g a.i./m canopy diameter, soil drench",
             "phi_days": "60", "notes": "Soil drench around root zone; complement to phosphonate"},
        ],
        biological_control=[
            "Trichoderma harzianum soil applications (4-6 kg/ha) to colonise root zone",
            "Organic mulch (15-20 cm) to promote suppressive soil microbiology",
            "Maintain high calcium levels for root cell wall integrity",
        ],
        cultural_control=[
            "Plant on well-drained slopes or ridges; never in low-lying waterlogged areas",
            "Use tolerant rootstocks (Duke 7, Dusa) as the foundation of management",
            "Maintain thick organic mulch (15-20 cm) under canopy but away from trunk",
            "Avoid over-irrigation; use tensiometers to schedule irrigation",
            "Improve drainage with French drains if needed",
            "Avoid moving soil or water from infected to clean blocks",
        ],
        economic_threshold="Any root blackening on newly planted trees warrants immediate phosphonate treatment",
        severity_scale={
            "mild": "Slight canopy thinning, some feeder root blackening, tree recoverable",
            "moderate": "Significant canopy decline (30-50%), branch die-back, reduced yield",
            "severe": "> 50% canopy loss, extensive root death, tree unlikely to recover",
        },
    ),
    DiseaseProfile(
        name="Anthracnose",
        pathogen="Colletotrichum gloeosporioides",
        pathogen_type="fungal",
        symptoms=[
            "Dark brown to black circular lesions on ripe fruit",
            "Lesions expand rapidly during ripening, flesh beneath turns brown-black",
            "Pepper spot: tiny black spots on fruit skin (latent infection visible at harvest)",
            "Twig die-back with dark cankers on young shoots",
        ],
        identification_markers=[
            "Circular, sunken dark lesions on fruit that expand during ripening",
            "Salmon-pink spore masses on lesions under humid conditions",
            "Latent infection: fruit appears healthy at harvest, develops lesions during ripening",
            "Distinguish from stem-end rot by lesion position (anthracnose: anywhere on fruit surface)",
        ],
        favourable_conditions={
            "humidity_min": 80, "temp_min_c": 22, "temp_max_c": 30,
            "note": "Warm, wet conditions during fruit development. Latent infections established "
                    "on fruit from flowering onward remain quiescent until fruit ripens and "
                    "antifungal diene levels decline. Worse on stressed trees with Phytophthora."
        },
        susceptible_stages=["Flowering", "Fruit development", "Post-harvest"],
        resistant_varieties=["Hass (moderate tolerance)", "Reed"],
        susceptible_varieties=["Fuerte", "Ryan", "Pinkerton"],
        chemical_control=[
            {"name": "Copper oxychloride 85 WP", "rate": "3.0 kg/ha",
             "phi_days": "0", "notes": "Monthly from flowering through fruit set; protectant"},
            {"name": "Prochloraz 450 EC", "rate": "450 ml/1000L (post-harvest dip)",
             "phi_days": "N/A", "notes": "Post-harvest hot water + prochloraz dip (52 degC, 5 min)"},
            {"name": "Azoxystrobin 250 SC", "rate": "0.4 L/ha",
             "phi_days": "14", "notes": "Pre-harvest sprays during wet periods; max 3 per season"},
        ],
        biological_control=[
            "Bacillus subtilis foliar sprays during flowering",
            "Maintain tree health through Phytophthora management to boost natural antifungal compounds",
        ],
        cultural_control=[
            "Prune to open canopy for air circulation and light penetration",
            "Remove dead wood and mummified fruit (inoculum sources)",
            "Harvest fruit at correct maturity (21-24% dry matter for Hass)",
            "Cool fruit rapidly after harvest (5-7 degC within 6 hours)",
            "Post-harvest hot water treatment (48-52 degC, 5 minutes) reduces latent infections",
        ],
        economic_threshold="5% of fruit showing pepper spot at harvest indicates need for improved spray programme",
        severity_scale={
            "mild": "< 5% fruit with visible lesions at ripening",
            "moderate": "5-20% fruit affected; post-harvest losses significant",
            "severe": "> 20% fruit rejected at packhouse; brand reputation at risk",
        },
    ),
    DiseaseProfile(
        name="Cercospora Spot (Blotch)",
        pathogen="Cercospora purpurea (syn. Pseudocercospora purpurea)",
        pathogen_type="fungal",
        symptoms=[
            "Angular brown spots on leaves, often with yellow halo",
            "Small brown to dark purple spots on fruit skin",
            "Fruit spots remain superficial but cause cosmetic downgrading",
            "Severe leaf infection causes premature defoliation",
        ],
        identification_markers=[
            "Angular lesions on leaves bounded by minor veins (distinguishes from anthracnose)",
            "Lesions brown with dark margin and faint yellow halo",
            "Fruit spots dry, slightly raised, and do not expand during ripening",
            "Conidia produced on lower leaf surface under humid conditions",
        ],
        favourable_conditions={
            "humidity_min": 75, "temp_min_c": 18, "temp_max_c": 28,
            "note": "Frequent rainfall and high humidity. Old, senescent leaves most susceptible. "
                    "Worse on shaded, dense canopies with poor air movement."
        },
        susceptible_stages=["Vegetative flush", "Fruit development"],
        resistant_varieties=["Hass (moderate tolerance)"],
        susceptible_varieties=["Fuerte", "Pinkerton"],
        chemical_control=[
            {"name": "Copper oxychloride 85 WP", "rate": "3.0 kg/ha",
             "phi_days": "0", "notes": "Include in regular copper spray programme"},
            {"name": "Benomyl 50 WP", "rate": "0.5 kg/ha",
             "phi_days": "14", "notes": "Systemic; alternate with copper to manage resistance"},
        ],
        biological_control=[
            "Maintain vigorous tree health to accelerate leaf turnover",
            "Compost teas may suppress foliar pathogens",
        ],
        cultural_control=[
            "Prune to improve canopy light and air circulation",
            "Remove fallen leaves and debris from orchard floor",
            "Maintain balanced nutrition — avoid excessive nitrogen that produces soft, susceptible growth",
            "Avoid overhead irrigation",
        ],
        economic_threshold="15% of fruit with cosmetic lesions at harvest (export grade threshold)",
        severity_scale={
            "mild": "Scattered leaf spots, < 5% fruit with blemishes",
            "moderate": "Significant leaf spotting, 5-15% fruit downgraded",
            "severe": "Defoliation occurring, > 15% fruit unacceptable for export",
        },
    ),
]


AVOCADO_PESTS: List[PestProfile] = [
    PestProfile(
        name="Mediterranean Fruit Fly",
        scientific_name="Ceratitis capitata",
        pest_type="insect",
        identification=[
            "Adult: small fly (5-7mm), mottled brown wings with distinctive banding",
            "Larvae: white, legless maggots (8-10mm) inside fruit flesh",
            "Pupae: dark brown, barrel-shaped, found in soil under trees",
            "Males with iridescent wing patterns and feathery aristae",
        ],
        damage_symptoms=[
            "Oviposition punctures on fruit surface (tiny, often hard to see)",
            "Larvae tunnel through flesh causing internal breakdown",
            "Secondary fungal and bacterial infections in tunnels",
            "Premature fruit drop; fruit rots rapidly after infestation",
        ],
        life_cycle_notes=(
            "Complete lifecycle 21-30 days in warm conditions. Female punctures fruit skin "
            "with ovipositor and lays 1-10 eggs per puncture. Larvae feed inside fruit for "
            "7-10 days, drop to soil to pupate for 10-14 days. Multiple generations per year. "
            "Polyphagous — infests many fruit species."
        ),
        favourable_conditions={
            "temp_min_c": 20, "temp_max_c": 32,
            "note": "Warm, humid conditions. Population builds on early-maturing fruit hosts "
                    "(guava, mango, citrus) before moving to avocado. Worse in mixed-fruit orchards."
        },
        susceptible_stages=["Fruit development (mature)", "Pre-harvest"],
        economic_threshold="0.5 flies per McPhail trap per day or any larva found in fruit",
        chemical_control=[
            {"name": "GF-120 (Spinosad bait spray)", "rate": "1.0-1.5 L/ha in 20L water",
             "phi_days": "1", "notes": "Bait spray applied as coarse spots on every other tree; very targeted"},
            {"name": "Malathion bait spray", "rate": "Malathion 50 EC: 500 ml + 1 kg protein bait per 100L",
             "phi_days": "7", "notes": "Spot spray on trunk and lower canopy; avoid fruit contact"},
        ],
        biological_control=[
            "Sterile Insect Technique (SIT) in area-wide programmes",
            "Parasitoid wasps: Fopius arisanus, Diachasmimorpha longicaudata",
            "Ground-dwelling predators (ants, beetles) consume pupae in soil",
        ],
        cultural_control=[
            "Collect and destroy fallen fruit daily (bury 50cm deep or feed to livestock)",
            "Orchard sanitation: remove all unmarketable fruit from trees",
            "Mass trapping with McPhail or Lynfield traps (protein bait + DDVP strip)",
            "Maintain a weed-free strip under trees to expose pupae to sun and predators",
            "Coordinate with neighbours for area-wide management",
        ],
        scouting_protocol=(
            "Deploy McPhail or Chempac bucket traps at 1 per hectare from 8 weeks before expected "
            "harvest. Service weekly; count and identify flies. Record Flies per Trap per Day (FTD). "
            "If FTD > 0.5 for medfly, initiate bait spray programme immediately. Also check 50 fruit "
            "per block for oviposition stings."
        ),
    ),
    PestProfile(
        name="False Codling Moth",
        scientific_name="Thaumatotibia leucotreta",
        pest_type="insect",
        identification=[
            "Adult moth: small (15-20mm wingspan), mottled grey-brown with orange hindwings",
            "Larvae: pink-red with dark head, 15mm at maturity, inside fruit",
            "Pupae: brown, in silken cocoon in soil or leaf litter",
            "Eggs: flat, oval, laid singly on fruit surface (hard to see)",
        ],
        damage_symptoms=[
            "Entry hole with frass near fruit stem end or equator",
            "Internal tunnelling through flesh with frass-filled galleries",
            "Secondary rot (often Botrytis or Penicillium) in tunnels",
            "Premature fruit drop; quarantine pest for export markets",
        ],
        life_cycle_notes=(
            "Lifecycle 30-50 days depending on temperature. Female lays 100-200 eggs singly "
            "on fruit. Neonate larva bores into fruit within hours. Larval feeding 14-21 days "
            "inside fruit, then exits and drops to soil to pupate. 3-5 generations per year in "
            "subtropical Zimbabwe."
        ),
        favourable_conditions={
            "temp_min_c": 18, "temp_max_c": 30,
            "note": "Polyphagous; builds up on citrus, macadamia, and other hosts. "
                    "Higher populations in warm, low-altitude areas. Regulated quarantine pest "
                    "for EU, USA, and other markets."
        },
        susceptible_stages=["Fruit development", "Pre-harvest"],
        economic_threshold="Phytosanitary pest: zero tolerance for export; any detection requires action",
        chemical_control=[
            {"name": "Delegate (Spinetoram 250 WG)", "rate": "200 g/ha",
             "phi_days": "7", "notes": "Apply at egg hatch; monitor with pheromone traps for timing"},
            {"name": "Coragen (Chlorantraniliprole 200 SC)", "rate": "150-200 ml/ha",
             "phi_days": "7", "notes": "Diamide; ovicidal and larvicidal activity; soft on beneficials"},
        ],
        biological_control=[
            "Cryptophlebia leucotreta granulovirus (CrleGV) — specific, safe biological insecticide",
            "Trichogrammatoidea cryptophlebiae (egg parasitoid)",
            "Entomopathogenic nematodes (Heterorhabditis spp.) for soil pupae",
            "Mating disruption with pheromone dispensers in high-density orchards",
        ],
        cultural_control=[
            "Orchard sanitation: remove and destroy all fallen and unmarketable fruit",
            "Pheromone trapping for monitoring and partial population suppression",
            "Cold sterilisation treatment for export fruit (0.5 degC for 22 days)",
            "Encourage biodiversity for natural enemy conservation",
        ],
        scouting_protocol=(
            "Deploy delta pheromone traps at 2-4 per hectare from fruit set onward. Check weekly "
            "and record moth counts. Use trap data to time sprays at peak flight and egg hatch. "
            "Cut 50 fruit per block at harvest to check for internal larvae (a key compliance step "
            "for export). Report any detection to PPRI for export certification."
        ),
    ),
    PestProfile(
        name="Avocado Thrips",
        scientific_name="Scirtothrips perseae",
        pest_type="insect",
        identification=[
            "Tiny (0.7mm) pale yellow insects on young fruit and leaf surfaces",
            "Larvae even smaller, found on new flush and young fruit",
            "Adults move rapidly when disturbed",
            "Use magnification (10x) for reliable identification",
        ],
        damage_symptoms=[
            "Superficial scarring and russeting on young fruit skin",
            "Scabby, rough texture on fruit (cosmetic damage but downgrades grade)",
            "Leaf distortion and bronzing on new flush",
            "Brown corklike scarring makes Hass fruit unmarketable for export",
        ],
        life_cycle_notes=(
            "Complete lifecycle 14-20 days. Eggs inserted into young leaf or fruit tissue. "
            "Two larval instars feed on epidermis. Prepupa and pupa in soil or leaf litter. "
            "Multiple overlapping generations. Population peaks coincide with spring flush "
            "and fruit set."
        ),
        favourable_conditions={
            "temp_min_c": 20, "temp_max_c": 30,
            "note": "Warm, dry conditions with new flush growth. Spring and early summer peak. "
                    "Sheltered orchards with low wind have higher populations."
        },
        susceptible_stages=["Flowering", "Fruit set", "Young fruit (pea to marble size)"],
        economic_threshold="5-10 thrips per leaf or any scarring on 10% of young fruit",
        chemical_control=[
            {"name": "Abamectin 18 EC", "rate": "300-400 ml/ha",
             "phi_days": "7", "notes": "Translaminar; effective on larvae; time with fruit set"},
            {"name": "Spinosad 480 SC", "rate": "100-200 ml/ha",
             "phi_days": "3", "notes": "Soft option; rotate with abamectin to manage resistance"},
        ],
        biological_control=[
            "Predatory thrips (Franklinothrips spp.) and predatory mites",
            "Minute pirate bugs (Orius spp.)",
            "Conserve beneficials by using selective insecticides and ground covers",
        ],
        cultural_control=[
            "Avoid excessive nitrogen that promotes lush, susceptible flush",
            "Maintain ground covers between rows for beneficial insect habitat",
            "Mulch under canopy to support soil-dwelling thrips predators",
            "Kaolin clay (Surround WP) as particle film barrier on young fruit",
        ],
        scouting_protocol=(
            "Scout weekly from flowering through marble-size fruit stage. Examine 5 leaves and "
            "5 young fruit per tree on 20 trees per block. Use 10x hand lens. Record thrips per "
            "leaf and percent fruit with scarring. Treat when threshold reached. Yellow or blue "
            "sticky traps give additional population trend data."
        ),
    ),
]


AVOCADO_GROWTH_STAGES: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Winter Dormancy / Pre-Bloom",
        stage_code="GS1",
        day_range=(0, 45),
        water_kc=0.55,
        water_mm_per_week=15,
        critical_nutrients=["P", "B", "Zn"],
        key_activities=[
            "Light structural pruning and removal of dead wood",
            "Apply phosphonate trunk injection for Phytophthora management",
            "Soil and leaf analysis; apply corrections",
            "Replenish mulch layer to 15-20 cm under canopy",
            "Apply boron and zinc foliar sprays before bud swell",
        ],
        risks=["Frost damage in exposed sites", "Phytophthora if soils saturated from late rains"],
        scientific_notes=(
            "Avocado is evergreen but has reduced metabolic activity during cool dry months "
            "(June-August in Zimbabwe). Flower buds differentiate during this period in response "
            "to cooler temperatures (15-20 degC night). Phosphorus and boron are accumulated in "
            "buds for the coming flowering event. Root growth slows but never truly ceases in "
            "subtropical conditions."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Flowering (Bloom)",
        stage_code="GS2",
        day_range=(45, 90),
        water_kc=0.65,
        water_mm_per_week=18,
        critical_nutrients=["B", "Zn", "Ca"],
        key_activities=[
            "Boron foliar spray at 50% bloom for pollination support",
            "Deploy hives at 4-8 per hectare for cross-pollination",
            "Begin copper fungicide programme for anthracnose",
            "Avoid disruptive insecticide sprays during flowering",
        ],
        risks=["Cold snaps during flowering reducing set", "Rain washing pollen", "Boron deficiency"],
        scientific_notes=(
            "Avocado exhibits synchronous dichogamy (protogynous in type A, protandrous in type B). "
            "Hass (type A) opens female in the morning, male in the afternoon of the next day. "
            "Interplanting type A and type B cultivars (e.g., Hass + Fuerte) enhances cross-pollination. "
            "Only 0.001-0.1% of flowers set fruit to maturity. Boron deficiency causes 'monkey face' "
            "fruit deformation. Optimal pollination temperature: 20-25 degC."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Fruit Set and Cell Division",
        stage_code="GS3",
        day_range=(90, 150),
        water_kc=0.80,
        water_mm_per_week=22,
        critical_nutrients=["N", "K", "Ca"],
        key_activities=[
            "First nitrogen top-dress after fruit set confirmed",
            "Scout for thrips on young fruit (scarring risk highest now)",
            "Monitor fruit fly traps",
            "Maintain consistent irrigation — stress causes fruitlet drop",
        ],
        risks=["Thrips scarring", "Fruitlet abscission from water stress", "Wind damage"],
        scientific_notes=(
            "Two major fruit drop events occur: the first at 4-6 weeks post-set (June drop) and "
            "the second at 8-12 weeks. Surviving fruitlets undergo active cell division; final "
            "cell number largely determines potential fruit size. Calcium uptake into fruit is "
            "most active during this phase and critical for post-harvest quality (flesh firmness, "
            "reduced internal disorders). Water deficit during cell division permanently reduces "
            "fruit size potential."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Fruit Development (Cell Expansion)",
        stage_code="GS4",
        day_range=(150, 300),
        water_kc=0.75,
        water_mm_per_week=20,
        critical_nutrients=["K", "Ca", "Mg"],
        key_activities=[
            "Potassium application for oil accumulation and fruit quality",
            "Continue anthracnose spray programme during wet months",
            "Monitor fruit dry matter accumulation for harvest timing",
            "Second phosphonate trunk injection (mid-season)",
        ],
        risks=["Anthracnose latent infection", "Phytophthora root rot flare-up in wet season", "Sunburn on exposed fruit"],
        scientific_notes=(
            "Oil accumulation in avocado is the key maturity indicator. Hass fruit requires "
            "21-24% dry matter (approximately 10-12% oil) for acceptable eating quality. Oil "
            "accumulates steadily from 5 months post-set, reaching 15-30% at harvest maturity "
            "depending on cultivar and harvest date. Unlike most fruit, avocado does not ripen "
            "on the tree; ethylene-mediated ripening begins only after harvest. Potassium is "
            "essential for oil biosynthesis pathways."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Harvest",
        stage_code="GS5",
        day_range=(300, 365),
        water_kc=0.70,
        water_mm_per_week=18,
        critical_nutrients=["K"],
        key_activities=[
            "Test fruit dry matter with microwave method (target 21-24% for Hass)",
            "Harvest using clippers, leaving 5mm pedicel attached",
            "Cool fruit to 5-7 degC within 6 hours of picking",
            "Post-harvest hot water and fungicide treatment for export",
            "Orchard sanitation: remove fallen and reject fruit",
        ],
        risks=["Anthracnose expression during ripening", "Fruit fly infestation", "Over-maturity and flesh greying"],
        scientific_notes=(
            "Avocado harvest maturity is determined by dry matter content (inversely related to "
            "moisture content). South African / Zimbabwe standard: minimum 21% DM for Hass. "
            "Fruit can hang on tree for extended periods (storage on tree) gaining dry matter "
            "but risking alternate bearing in the following season. Post-harvest cold chain "
            "management is critical: controlled atmosphere (2-5% O2, 5-10% CO2) extends shelf "
            "life to 28-35 days at 5-7 degC for export by sea."
        ),
    ),
]


AVOCADO_FERTILIZER = FertilizerSchedule(
    basal={
        "product": "Single Superphosphate (SSP) + compost",
        "rate_per_tree": "SSP: 500 g + 20 kg compost per planting hole",
        "timing": "At planting; mix SSP and compost with topsoil in planting hole",
        "notes": "Planting holes: 60x60x60 cm minimum. Do not place fertiliser in direct contact with roots.",
    },
    top_dress_1={
        "product": "LAN (28% N) or CAN",
        "rate_per_tree": "Young (1-3 yr): 200-500 g; Bearing (4+ yr): 1-2 kg",
        "timing": "After fruit set (September-October), split into 2-3 applications",
        "notes": "Broadcast under canopy drip line, not against trunk. Irrigate after application.",
    },
    top_dress_2={
        "product": "Potassium chloride (KCl) or Sulphate of Potash (SOP)",
        "rate_per_tree": "Young: 200 g; Bearing: 500-1000 g KCl",
        "timing": "During fruit development (November-January)",
        "notes": "Potassium critical for oil accumulation and fruit quality. Split into 2 applications.",
    },
    foliar={
        "product": "Zinc sulphate + Boron (Solubor) + Calcium chloride",
        "rate": "Zn: 3 g/L, B: 1 g/L, CaCl2: 5 g/L",
        "timing": "3-5 foliar sprays: pre-bloom, at bloom, fruit set, mid-development, pre-harvest",
        "notes": "Boron at bloom essential. Calcium sprays improve fruit firmness and reduce grey pulp.",
    },
    liming={
        "target_ph": "5.5-6.5",
        "product": "Dolomitic lime",
        "rate": "As per soil test, typically 1-3 t/ha every 2-3 years",
        "timing": "Dry season; broadcast under canopy and incorporate lightly",
        "notes": "Avocado is acid-tolerant but performs best at pH 5.5-6.5. Dolomitic lime provides Mg.",
    },
    notes=(
        "Annual nutrient targets for mature bearing trees: 150-250 g N, 50-80 g P, 200-300 g K "
        "per tree (adjust based on tree size and yield). Organic matter management (thick mulch) "
        "is fundamental: apply 30-50 cm of coarse mulch under canopy annually. Avocado roots are "
        "shallow and sensitive; avoid deep cultivation. Micronutrients (Zn, B, Fe, Mn) are commonly "
        "deficient in Zimbabwe's acid fersiallitic soils."
    ),
)


AVOCADO_PLANTING_WINDOWS: List[PlantingWindow] = [
    PlantingWindow(
        region="NR I - Eastern Highlands (Chipinge, Chimanimani)",
        optimal_start="November 1",
        optimal_end="January 31",
        acceptable_start="October 15",
        acceptable_end="February 28",
        notes=(
            "Plant at onset of rains. Frost-free areas preferred. Excellent subtropical "
            "climate for Hass production. Altitude 600-1200m optimal."
        ),
    ),
    PlantingWindow(
        region="NR IIa - Highveld (Mazowe, Marondera)",
        optimal_start="November 1",
        optimal_end="December 31",
        acceptable_start="October 15",
        acceptable_end="February 15",
        notes=(
            "Frost is the main risk. Plant on north-facing slopes with frost drainage. "
            "Supplemental irrigation essential for establishment and dry season."
        ),
    ),
    PlantingWindow(
        region="NR III - Semi-intensive (Mutare lowveld margins)",
        optimal_start="November 15",
        optimal_end="January 15",
        acceptable_start="November 1",
        acceptable_end="February 28",
        notes=(
            "Marginal without irrigation. Hot summers can stress trees. Suitable for "
            "Fuerte and other heat-tolerant cultivars."
        ),
    ),
]


PROFILE = CropProfile(
    crop_name="Avocado",
    scientific_name="Persea americana",
    family="Lauraceae",

    optimal_ph=(5.5, 6.5),
    critical_ph_low=4.5,
    optimal_soil_types=["deep, well-drained red loam", "fersiallitic clay loam", "volcanic-origin soils"],
    avoid_soil_types=["waterlogged clay", "vertisol", "shallow lithosol", "heavy clay"],

    optimal_temp=(18.0, 28.0),
    critical_temp_low=0.0,
    critical_temp_high=35.0,
    base_temp_gdd=10.0,
    total_water_mm=1000.0,

    growth_stages=AVOCADO_GROWTH_STAGES,
    fertilizer_schedule=AVOCADO_FERTILIZER,
    diseases=AVOCADO_DISEASES,
    pests=AVOCADO_PESTS,
    planting_windows=AVOCADO_PLANTING_WINDOWS,

    harvest_moisture="70-76% moisture content (21-24% dry matter for Hass); fruit does not ripen on tree",
    storage_conditions="5-7 degC, 85-95% RH; controlled atmosphere (2-5% O2, 5-10% CO2) for sea export; shelf life 28-35 days",
    post_harvest_notes=(
        "Harvest with clippers leaving 5mm pedicel (stem button). Cool to 5-7 degC within 6 hours. "
        "Post-harvest hot water treatment (48-52 degC, 5 min) + prochloraz dip for anthracnose control. "
        "Grade by weight: count 10-28 per 4 kg tray (export). Ripen with ethylene (100 ppm, 24 hours at "
        "18-20 degC) for domestic market. First fruit from grafted trees in year 3-5; full production "
        "by year 7-8 at 10-15 tonnes/ha."
    ),

    natural_region_suitability={
        "I": "Excellent — ideal subtropical highland climate for Hass; primary production zone",
        "IIa": "Good — frost-free sites with irrigation; Mazowe and Marondera areas",
        "IIb": "Moderate — frost risk limits suitability; sheltered microclimates only",
        "III": "Marginal — possible under irrigation on suitable sites; heat stress risk",
        "IV": "Unsuitable — too hot and dry; excessive water stress",
        "V": "Unsuitable — extreme heat and aridity incompatible with avocado production",
    },
)

ALIASES: list = ["avocados"]
