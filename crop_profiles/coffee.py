"""Coffee (Coffea arabica) — Perennial highland crop grown in Zimbabwe's Eastern Highlands, shade-grown possible."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List


COFFEE_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Coffee Berry Disease (CBD)",
        pathogen="Colletotrichum kahawae",
        pathogen_type="fungal",
        symptoms=[
            "Dark, sunken lesions on green developing berries",
            "Berries turn black and mummify on the branch",
            "Premature fruit drop, especially during wet weather",
            "Sporulation appears as salmon-pink spore masses on lesions in humid conditions",
        ],
        identification_markers=[
            "Dark, sunken, round to irregular lesions on green berries (key diagnostic)",
            "Berries shrivel and mummify, remaining attached or falling",
            "Distinct from berry blotch by rapid progression and berry mummification",
            "Acervuli with salmon-pink spore masses under humid conditions",
        ],
        favourable_conditions={
            "temp_min_c": 15, "temp_max_c": 25,
            "humidity_min": 80,
            "rainfall": "frequent rain during berry expansion",
            "note": "Most destructive at 15-25 degC with prolonged wetness during "
                    "berry expansion (weeks 8-16 post-flowering). Endemic to Africa. "
                    "Conidia spread by rain splash."
        },
        susceptible_stages=["Flowering", "Berry expansion", "Green berry"],
        resistant_varieties=["Catimor 129", "Ruiru 11"],
        susceptible_varieties=["SL28", "SL34", "K7"],
        chemical_control=[
            {"name": "Copper oxychloride 85 WP", "rate": "3.0-4.0 kg/ha",
             "phi_days": "14", "notes": "Protectant; apply at petal fall and repeat 3-4 weekly during wet season"},
            {"name": "Chlorothalonil 500 SC", "rate": "2.5-3.0 L/ha",
             "phi_days": "21", "notes": "Broad-spectrum protectant; alternate with copper"},
            {"name": "Azoxystrobin 250 SC", "rate": "0.5 L/ha",
             "phi_days": "28", "notes": "Systemic strobilurin; limit to 2-3 applications per season"},
        ],
        biological_control=[
            "Bacillus subtilis-based biofungicides show moderate efficacy",
            "Shade management reduces berry wetness duration",
            "Maintain balanced nutrition for plant defence compounds",
        ],
        cultural_control=[
            "Plant resistant varieties (Catimor 129) in high-CBD-risk areas",
            "Prune to open canopy and improve air circulation",
            "Remove mummified berries (sanitation) to reduce inoculum carryover",
            "Maintain shade trees at 40-50% cover to moderate microclimate",
            "Harvest ripe berries promptly to remove sporulation substrate",
        ],
        economic_threshold="2-5% berry infection at green berry stage warrants fungicide application",
        severity_scale={
            "mild": "< 5% berries affected, scattered lesions",
            "moderate": "5-25% berries infected, mummification beginning",
            "severe": "> 25% berries lost to mummification — 50-80% crop loss possible",
        },
    ),
    DiseaseProfile(
        name="Coffee Leaf Rust (CLR)",
        pathogen="Hemileia vastatrix",
        pathogen_type="fungal",
        symptoms=[
            "Yellow-orange powdery pustules on the underside of leaves",
            "Corresponding pale yellow spots visible on the upper leaf surface",
            "Severe defoliation leading to die-back of bearing branches",
            "Reduced berry set and smaller beans in subsequent seasons",
        ],
        identification_markers=[
            "Bright orange uredospores on leaf undersurface (diagnostic)",
            "Round to irregular yellow patches on upper leaf surface",
            "Lower and inner canopy affected first where humidity is highest",
            "No pustules on stems or berries (leaf-specific pathogen)",
        ],
        favourable_conditions={
            "temp_min_c": 20, "temp_max_c": 28,
            "humidity_min": 80,
            "leaf_wetness_hours": 6,
            "note": "Optimal infection at 21-25 degC with 6+ hours of leaf wetness. "
                    "Worst during warm, wet months (January-April in Zimbabwe). "
                    "High crop load increases susceptibility due to carbohydrate drain."
        },
        susceptible_stages=["Post-harvest flush", "Vegetative growth", "Berry development"],
        resistant_varieties=["Catimor 129", "Colombia variety", "Ruiru 11"],
        susceptible_varieties=["SL28", "SL34", "Blue Mountain"],
        chemical_control=[
            {"name": "Copper oxychloride 85 WP", "rate": "3.0-4.0 kg/ha",
             "phi_days": "14", "notes": "Preventive; apply 3-4 times during wet season"},
            {"name": "Triadimefon 250 WP", "rate": "0.5 kg/ha",
             "phi_days": "21", "notes": "Systemic triazole; curative and preventive activity"},
            {"name": "Cyproconazole 100 SL", "rate": "0.5 L/ha",
             "phi_days": "28", "notes": "Systemic; tank mix with copper for broader protection"},
        ],
        biological_control=[
            "Lecanicillium lecanii hyperparasite of rust pustules (limited commercial availability)",
            "Maintain shade trees to reduce temperature extremes and leaf wetness cycling",
        ],
        cultural_control=[
            "Plant resistant varieties as the primary CLR management strategy",
            "Prune to maintain open canopy for air movement and rapid leaf drying",
            "Balanced fertilisation (especially K) improves leaf resistance",
            "Reduce overbearing through selective harvest and pruning",
            "Remove heavily infected branches during dry season",
        ],
        economic_threshold="5% leaf area infected or 20% of leaves showing symptoms",
        severity_scale={
            "mild": "< 5% leaves with pustules, lower canopy only",
            "moderate": "5-20% leaves infected, defoliation beginning",
            "severe": "> 20% leaves infected, heavy defoliation — crop loss next season",
        },
    ),
    DiseaseProfile(
        name="Root Rot",
        pathogen="Armillaria mellea / Fusarium spp.",
        pathogen_type="fungal",
        symptoms=[
            "Progressive yellowing and wilting of leaves despite adequate moisture",
            "Die-back of branches starting from tips",
            "White mycelial fans under bark at collar level (Armillaria)",
            "Entire tree death over months to years",
        ],
        identification_markers=[
            "White fan-shaped mycelium under bark at the collar (Armillaria diagnostic)",
            "Black rhizomorphs (bootlace structures) on root surfaces and in soil",
            "Brown, water-soaked root cortex that slips off the stele",
            "Mushroom fruiting bodies at base of dead trees (Armillaria)",
        ],
        favourable_conditions={
            "soil_moisture": "waterlogged or poorly drained soils",
            "note": "Armillaria spreads via rhizomorphs from infected stumps. "
                    "Common on previously forested land. Fusarium root rot favoured by "
                    "nematode damage and poor drainage."
        },
        susceptible_stages=["Establishment", "All production stages"],
        resistant_varieties=[],
        susceptible_varieties=["SL28", "SL34"],
        chemical_control=[
            {"name": "Metalaxyl + Mancozeb (Ridomil Gold MZ)", "rate": "2.5 kg/ha soil drench",
             "phi_days": "60", "notes": "For Fusarium/Phytophthora component; limited efficacy on Armillaria"},
        ],
        biological_control=[
            "Trichoderma harzianum soil applications around root zone",
            "Maintain mycorrhizal associations through minimal soil disturbance",
        ],
        cultural_control=[
            "Remove and destroy all old tree stumps before establishing new coffee",
            "Ensure excellent drainage; plant on ridges or raised beds if needed",
            "Avoid planting on recently cleared indigenous forest land",
            "Trench around infected trees to sever rhizomorph connections",
            "Replant with Catimor or other vigorous rootstock types",
        ],
        economic_threshold="Any tree showing collar rot symptoms — isolate and investigate immediately",
        severity_scale={
            "mild": "1-2 trees showing yellowing in a block",
            "moderate": "Expanding patch of affected trees (5-10%), rhizomorphs found",
            "severe": "Large patches of dead trees, replanting required",
        },
    ),
]


COFFEE_PESTS: List[PestProfile] = [
    PestProfile(
        name="Coffee Berry Borer",
        scientific_name="Hypothenemus hampei",
        pest_type="insect",
        identification=[
            "Tiny (1.5-2mm) dark brown to black beetle",
            "Female bores into the berry through the disc (navel) end",
            "Single round entry hole (1mm) at berry tip is diagnostic",
            "Male smaller, flightless, remains inside the berry",
        ],
        damage_symptoms=[
            "Single round borehole at the tip (disc) of the berry",
            "Internal tunnelling and destruction of one or both coffee beans",
            "Frass (fine powder) at entry hole",
            "Premature berry drop; beans with tunnels rejected at grading",
        ],
        life_cycle_notes=(
            "Female bores into berry and lays 35-50 eggs inside. Complete lifecycle 25-35 days. "
            "Multiple overlapping generations. Males are haploid and do not fly. Females disperse "
            "to new berries after emergence. Overwinters in dried berries on tree or ground."
        ),
        favourable_conditions={
            "temp_min_c": 20, "temp_max_c": 30,
            "humidity_min": 75,
            "note": "Warm, humid conditions at low-mid altitudes. Worse with poor sanitation "
                    "(berries left on ground). Shade can increase or decrease depending on microclimate."
        },
        susceptible_stages=["Berry expansion", "Green berry", "Ripe berry"],
        economic_threshold="2-5% berries with borer entry holes",
        chemical_control=[
            {"name": "Chlorpyrifos 48 EC", "rate": "1.5-2.0 L/ha",
             "phi_days": "21", "notes": "Apply at 2% infestation; target berry disc with fine nozzle"},
            {"name": "Endosulfan 35 EC", "rate": "2.5 L/ha",
             "phi_days": "30", "notes": "Where still registered; being phased out globally"},
        ],
        biological_control=[
            "Beauveria bassiana (entomopathogenic fungus) — 1-2 x 10^9 spores/ha; best in humid conditions",
            "Parasitoid wasps: Cephalonomia stephanoderis and Prorops nasuta (classical biocontrol agents)",
            "Trap berries: leave small proportion of ripe berries as traps, then remove and destroy",
        ],
        cultural_control=[
            "Strip-pick all remaining berries at end of harvest (sanitation harvest critical)",
            "Collect and destroy fallen berries from the ground",
            "Maintain shade at 40-50% to reduce berry borer flight activity",
            "Prune to open canopy and facilitate spray coverage",
            "Alcohol-methanol traps (ethanol:methanol 1:1) to monitor and mass-trap adults",
        ],
        scouting_protocol=(
            "From 8 weeks after main flowering, sample 30 berries from 30 trees per hectare. "
            "Examine berry disc for entry holes. Calculate percent infestation. Treat if >2%. "
            "Re-scout every 2 weeks during berry development. Use Brocap traps for adult monitoring."
        ),
    ),
    PestProfile(
        name="Coffee Mealybug",
        scientific_name="Planococcus kenyensis",
        pest_type="insect",
        identification=[
            "Soft-bodied, oval, 3-4mm, covered in white waxy filaments",
            "Found in clusters at leaf axils, branch junctions, and berry clusters",
            "Waxy secretion and honeydew with sooty mould on leaves and berries",
            "Attended by ants (mutualistic relationship)",
        ],
        damage_symptoms=[
            "Sooty mould on leaves and berries from honeydew secretion",
            "Wilting of shoot tips and berry clusters",
            "Berry drop and reduced berry size",
            "Ant trails on trunk and branches indicate mealybug colonies",
        ],
        life_cycle_notes=(
            "Females produce 200-400 eggs in waxy ovisac. Crawlers (first instars) disperse "
            "by walking or wind. 3 nymphal instars for females, 4 for males. Complete lifecycle "
            "30-50 days. Males are winged. Ant-mealybug mutualism is critical for colony protection."
        ),
        favourable_conditions={
            "temp_min_c": 20, "temp_max_c": 30,
            "note": "Shaded, sheltered microhabitats within canopy. Ant attendance protects colonies "
                    "from natural enemies. Drought stress on trees increases susceptibility."
        },
        susceptible_stages=["Flowering", "Berry expansion", "Green berry", "Ripe berry"],
        economic_threshold="10% of berry clusters infested with mealybugs",
        chemical_control=[
            {"name": "Diazinon 60 EC", "rate": "1.5 L/ha",
             "phi_days": "14", "notes": "Target colonies at branch junctions with high-volume spray"},
            {"name": "Imidacloprid 200 SL (soil drench)", "rate": "350 ml/ha",
             "phi_days": "60", "notes": "Systemic; soil drench for long-term suppression. Use cautiously."},
        ],
        biological_control=[
            "Anagyrus pseudococci (parasitoid wasp) for classical biocontrol",
            "Cryptolaemus montrouzieri (mealybug destroyer beetle)",
            "Lacewings (Chrysoperla spp.) prey on crawlers",
            "Control ants to expose mealybugs to natural enemies",
        ],
        cultural_control=[
            "Band tree trunks with sticky barriers to prevent ant access",
            "Prune to open canopy and reduce sheltered microhabitats",
            "Remove heavily infested shoots and destroy",
            "Maintain plant vigour through balanced fertilisation and irrigation",
            "Control ant colonies at base of trees with bait stations",
        ],
        scouting_protocol=(
            "Monthly inspection of 20 trees per hectare. Examine 5 berry clusters and 5 branch "
            "junctions per tree. Record presence of mealybugs, ants, and sooty mould. "
            "Note natural enemy activity. Treat when >10% clusters infested."
        ),
    ),
    PestProfile(
        name="Antestia Bug",
        scientific_name="Antestiopsis thunbergii",
        pest_type="insect",
        identification=[
            "Shield-shaped bug, 6-8mm, variable colour (orange, black, white patterns)",
            "Bright orange and black markings on pronotum and scutellum",
            "Eggs laid in clusters of 12 on underside of leaves",
            "Nymphs gregarious, round-bodied, dark with orange markings",
        ],
        damage_symptoms=[
            "Feeding punctures on developing berries causing localised hard spots",
            "Potato taste defect in cupped coffee (due to bacterial transmission)",
            "Berry discolouration and premature ripening",
            "Black, sunken feeding lesions on green berries",
        ],
        life_cycle_notes=(
            "1-2 generations per year. Females lay 50-100 eggs in clusters. Nymphal development "
            "takes 35-50 days through 5 instars. Adults long-lived (several months). Overwinter "
            "as adults in leaf litter. Both adults and nymphs feed on berries."
        ),
        favourable_conditions={
            "temp_min_c": 15, "temp_max_c": 22,
            "altitude": "above 1200m",
            "note": "Highland pest; more severe above 1200m altitude. Populations build "
                    "during cool, wet season. Shade increases habitat suitability."
        },
        susceptible_stages=["Flowering", "Berry expansion", "Green berry"],
        economic_threshold="1-2 bugs per tree at berry expansion stage",
        chemical_control=[
            {"name": "Fenitrothion 50 EC", "rate": "1.5 L/ha",
             "phi_days": "14", "notes": "Apply when threshold reached; ensure thorough coverage of berry clusters"},
            {"name": "Deltamethrin 25 EC", "rate": "250-400 ml/ha",
             "phi_days": "7", "notes": "Pyrethroid; fast knockdown; may disrupt natural enemies"},
        ],
        biological_control=[
            "Egg parasitoids (Trissolcus spp.) provide natural suppression",
            "Birds are important predators; maintain shade trees with nesting habitat",
            "Predatory pentatomids feed on antestia nymphs",
        ],
        cultural_control=[
            "Hand-pick adults and nymphs during scouting visits",
            "Manage shade to balance pest pressure and beneficial habitat",
            "Remove alternative host plants (Solanaceae) near coffee",
            "Maintain clean orchard floor to reduce adult overwintering sites",
        ],
        scouting_protocol=(
            "Weekly from flowering through berry development. Beat branches over a cloth or tray. "
            "Examine 20 trees per hectare, 4 branches per tree (N/S/E/W). Count adults and nymphs. "
            "Treat when average exceeds 1-2 bugs per tree."
        ),
    ),
]


COFFEE_GROWTH_STAGES: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Dormancy / Dry Season Rest",
        stage_code="GS1",
        day_range=(0, 60),
        water_kc=0.50,
        water_mm_per_week=18,
        critical_nutrients=["K"],
        key_activities=[
            "Pruning: remove dead wood, suckers, and unproductive branches",
            "Apply lime if soil pH below 5.0",
            "Mulch replenishment under canopy (5-10 cm thick)",
            "Conduct soil and leaf tissue analysis",
            "Repair and maintain shade trees",
        ],
        risks=["Drought stress if dry season extended", "Fire damage to mulch"],
        scientific_notes=(
            "Arabica coffee requires a dry rest period (6-8 weeks with minimal rainfall) "
            "to synchronise flowering. Water stress induces flower bud dormancy which breaks "
            "upon re-wetting (rain or irrigation). Endogenous abscisic acid (ABA) levels rise "
            "during water stress and drop upon rehydration, triggering bud break. Pruning "
            "during dormancy minimises sap loss and disease entry."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Flowering",
        stage_code="GS2",
        day_range=(60, 75),
        water_kc=0.80,
        water_mm_per_week=25,
        critical_nutrients=["P", "B", "Zn"],
        key_activities=[
            "Irrigate to break dormancy if rains delayed (blossom shower)",
            "Apply boron foliar spray (Solubor 1 g/L) for fruit set",
            "Begin CBD fungicide programme at petal fall",
            "Avoid pesticide sprays during peak flowering (protect pollinators)",
        ],
        risks=["Rain during flowering reducing set", "CBD infection at petal fall", "Boron deficiency causing star flowers"],
        scientific_notes=(
            "Coffee flowers open 8-12 days after the breaking rain (blossom shower). "
            "Arabica is largely self-pollinating but cross-pollination by bees increases "
            "fruit set by 10-20%. Boron is critical for pollen tube growth and ovule "
            "fertilisation. Flowers are borne on nodes of the previous season's wood, "
            "so pruning strategy directly affects yield potential."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Berry Expansion (Pinhead to Green)",
        stage_code="GS3",
        day_range=(75, 180),
        water_kc=0.95,
        water_mm_per_week=30,
        critical_nutrients=["N", "K", "Ca"],
        key_activities=[
            "Apply first top-dress nitrogen (after fruit set confirmed)",
            "Continue CBD fungicide programme every 3-4 weeks",
            "Scout for coffee berry borer (entry holes at berry disc)",
            "Weed control: maintain weed-free strip under canopy, mow inter-rows",
        ],
        risks=["CBD peak risk", "Berry borer infestation", "Drought causing berry drop"],
        scientific_notes=(
            "Berry development follows a double sigmoid growth curve. Initial rapid expansion "
            "(cell division phase) occurs weeks 6-12 post-flowering. Endosperm development "
            "(bean fill) dominates weeks 12-24. Nitrogen demand peaks during this phase as "
            "the tree supports both vegetative growth and berry development. Water deficit "
            "during bean fill leads to small, light beans (peaberries and floaters)."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Berry Maturation and Ripening",
        stage_code="GS4",
        day_range=(180, 270),
        water_kc=0.85,
        water_mm_per_week=25,
        critical_nutrients=["K", "Mg"],
        key_activities=[
            "Second top-dress with potassium for bean quality and density",
            "Scout for antestia bug (potato taste defect risk)",
            "Monitor berry colour change from green to yellow to red",
            "Plan harvest logistics: pickers, wet mill, drying infrastructure",
        ],
        risks=["Antestia bug damage", "Over-ripe berries falling", "Mealybug colonies"],
        scientific_notes=(
            "Mucilage (sugary pulp) develops and sugar content rises as berries ripen. "
            "Chlorophyll degrades and anthocyanins accumulate (green to red). The parchment "
            "(endocarp) hardens. Bean moisture decreases from 60% to 50%. Potassium is "
            "critical for sugar and organic acid balance in the bean, influencing cup quality. "
            "Optimal harvest is at full cherry red stage for washed Arabica."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Harvest",
        stage_code="GS5",
        day_range=(270, 330),
        water_kc=0.70,
        water_mm_per_week=20,
        critical_nutrients=["K"],
        key_activities=[
            "Selective hand-picking of ripe red cherries only",
            "Multiple picking rounds (3-5) at 10-14 day intervals",
            "Wet processing within 12 hours of picking for quality",
            "Sanitation harvest: strip remaining berries to control berry borer",
        ],
        risks=["Over-ripe berries (fermentation on tree)", "Rain damage to drying coffee", "Berry borer carryover"],
        scientific_notes=(
            "Arabica in Zimbabwe typically matures 8-9 months after flowering. The Eastern "
            "Highlands main crop harvest is May-August. Selective picking ensures uniform "
            "ripeness which is critical for specialty-grade washed coffee. Each selective round "
            "removes 20-30% of the crop. The final strip-pick is essential for phytosanitary "
            "management of CBD and berry borer."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Post-Harvest Vegetative Flush",
        stage_code="GS6",
        day_range=(330, 365),
        water_kc=0.65,
        water_mm_per_week=20,
        critical_nutrients=["N", "P", "Zn"],
        key_activities=[
            "Apply post-harvest nitrogen to support new growth",
            "Foliar zinc application for new leaf development",
            "Begin leaf rust monitoring as new flush is susceptible",
            "Repair mulch and begin dry-season water management",
        ],
        risks=["Leaf rust on new flush", "Drought stress", "Stem borer damage"],
        scientific_notes=(
            "After harvest and with late-season rains, trees produce new vegetative growth "
            "(primaries and laterals) on which next season's flower buds will differentiate. "
            "Flower bud initiation occurs on new nodes during short days (April-June in Zimbabwe). "
            "Adequate nitrogen and zinc at this stage directly determine next season's yield "
            "potential. The tree must rebuild carbohydrate reserves depleted by fruiting."
        ),
    ),
]


COFFEE_FERTILIZER = FertilizerSchedule(
    basal={
        "product": "Single Superphosphate (SSP) + agricultural lime",
        "rate_kg_ha": "SSP: 250 kg/ha; Lime as per soil test",
        "p_kg_ha": 50,
        "timing": "At establishment (planting hole preparation) or annually during pruning",
        "notes": "Place SSP in planting hole mixed with topsoil and compost. Mature trees: "
                 "broadcast under canopy and mulch over.",
    },
    top_dress_1={
        "product": "CAN (Calcium Ammonium Nitrate 28% N) or LAN",
        "rate_kg_ha": 300,
        "n_kg_ha": 84,
        "timing": "After fruit set confirmed (approximately 8-10 weeks after flowering)",
        "notes": "Split application: broadcast under canopy, 1m radius from trunk. Follow with irrigation or rain.",
    },
    top_dress_2={
        "product": "Muriate of Potash (KCl 60% K2O) or Sulphate of Potash",
        "rate_kg_ha": 200,
        "k_kg_ha": 120,
        "timing": "During berry expansion to early ripening (approximately 5-6 months after flowering)",
        "notes": "Potassium critical for bean density and cup quality. Use SOP on acid soils.",
    },
    foliar={
        "product": "Zinc sulphate + Boron (Solubor) + Magnesium sulphate",
        "rate": "Zn: 3 g/L, B: 1 g/L, MgSO4: 5 g/L",
        "timing": "3-4 sprays per year: at flowering, berry set, mid-season, and post-harvest flush",
        "notes": "Apply in early morning. Zinc and boron deficiency common in Zimbabwe coffee soils.",
    },
    liming={
        "target_ph": "5.5-6.5",
        "product": "Dolomitic lime (preferred for Mg supply)",
        "rate": "1-3 t/ha based on soil test; every 2-3 years",
        "timing": "Apply during dry season and incorporate lightly under mulch",
        "notes": "Coffee soils in Eastern Highlands naturally acidify. Dolomitic lime supplies "
                 "both Ca and Mg. Avoid over-liming above pH 6.5 (micronutrient lockup).",
    },
    notes=(
        "Annual nutrient targets for mature bearing trees (>5 years): 80-120 kg N/ha, "
        "30-50 kg P2O5/ha, 100-150 kg K2O/ha. Young trees (years 1-3) receive 30-50% of "
        "bearing-tree rates. Organic matter management (mulch, compost, shade tree litter) "
        "is fundamental to Zimbabwe coffee nutrition. The industry standard is 10-15 t/ha "
        "mulch per year."
    ),
)


COFFEE_PLANTING_WINDOWS: List[PlantingWindow] = [
    PlantingWindow(
        region="NR I - Eastern Highlands (Chipinge, Honde Valley, Vumba)",
        optimal_start="November 15",
        optimal_end="January 15",
        acceptable_start="November 1",
        acceptable_end="February 28",
        notes=(
            "Plant at onset of reliable rains. Establish shade trees 1-2 years prior to coffee. "
            "Altitude 900-1800m. This is the primary coffee-growing region in Zimbabwe. "
            "Allow 3-4 years to first economic harvest."
        ),
    ),
    PlantingWindow(
        region="NR IIa - Highveld (limited, irrigated estates)",
        optimal_start="November 15",
        optimal_end="December 31",
        acceptable_start="November 1",
        acceptable_end="January 31",
        notes=(
            "Marginal for coffee without shade and supplemental irrigation. Only suitable "
            "on sheltered, frost-free sites with reliable water supply. Higher temperatures "
            "may reduce cup quality compared to highlands."
        ),
    ),
]


PROFILE = CropProfile(
    crop_name="Coffee",
    scientific_name="Coffea arabica",
    family="Rubiaceae",

    optimal_ph=(5.5, 6.5),
    critical_ph_low=4.5,
    optimal_soil_types=["deep, well-drained red loam", "fersiallitic clay loam", "volcanic-origin soils"],
    avoid_soil_types=["waterlogged soils", "shallow lithosol", "heavy vertisol"],

    optimal_temp=(15.0, 25.0),
    critical_temp_low=4.0,
    critical_temp_high=30.0,
    base_temp_gdd=10.0,
    total_water_mm=1500.0,

    growth_stages=COFFEE_GROWTH_STAGES,
    fertilizer_schedule=COFFEE_FERTILIZER,
    diseases=COFFEE_DISEASES,
    pests=COFFEE_PESTS,
    planting_windows=COFFEE_PLANTING_WINDOWS,

    harvest_moisture="50-55% cherry moisture at harvest; dry parchment to 10-12% for storage",
    storage_conditions="Dry parchment coffee: 10-12% moisture, cool dry warehouse, off-floor on pallets, 20-25 degC",
    post_harvest_notes=(
        "Wet processing (washed coffee): pulp within 12 hours, ferment 12-36 hours to remove mucilage, "
        "wash with clean water, dry on raised beds or concrete patio to 10-12% moisture (7-14 days). "
        "Zimbabwe's specialty coffee reputation depends on meticulous wet processing. Parchment rests "
        "6-8 weeks before dry milling. Grade by screen size (AA >18, AB 15-18) and cup quality."
    ),

    natural_region_suitability={
        "I": "Excellent — primary coffee zone; Eastern Highlands 900-1800m; ideal climate and soils",
        "IIa": "Marginal — only on sheltered, frost-free irrigated sites; lower cup quality",
        "IIb": "Unsuitable — too warm and dry; frost risk in some areas",
        "III": "Unsuitable — insufficient rainfall and too warm for quality Arabica",
        "IV": "Unsuitable — too hot and dry",
        "V": "Unsuitable — far too hot and arid",
    },
)

ALIASES: list = []
