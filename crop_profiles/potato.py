"""Potato (Solanum tuberosum) — high-value irrigated crop with two seasons possible in Zimbabwe."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List, Dict, Any


# POTATO (Solanum tuberosum)
# ---------------------------------------------------------------------------

_diseases: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Late Blight",
        pathogen="Phytophthora infestans",
        pathogen_type="oomycete",
        symptoms=[
            "Water-soaked, dark green to brown lesions on leaf tips and margins",
            "White sporulation on underside of leaves in humid conditions",
            "Rapid collapse of foliage ('blight') within days",
            "Brown, firm rot on tubers extending inward from skin",
        ],
        identification_markers=[
            "White cottony growth on leaf undersides (sporangiophores) — diagnostic",
            "Lesions expand rapidly in cool, wet weather",
            "Characteristic musty smell from infected foliage",
            "Tuber blight: reddish-brown granular rot beneath skin",
        ],
        favourable_conditions={"temp_min_c": 10, "temp_max_c": 20, "humidity_min": 90},
        susceptible_stages=["Vegetative", "Tuber Initiation", "Tuber Bulking"],
        resistant_varieties=["BP1 (moderate)", "Mnandi (moderate)"],
        susceptible_varieties=["Mondial", "Hermes"],
        chemical_control=[
            {"name": "Metalaxyl + Mancozeb (Ridomil Gold MZ 68 WG)", "rate": "2.5 kg/ha",
             "phi_days": "14", "notes": "Systemic + protectant. Apply preventively; alternate with contact fungicides."},
            {"name": "Mancozeb 80 WP", "rate": "2.0-2.5 kg/ha",
             "phi_days": "7", "notes": "Protectant only. Apply 7-day intervals in high-risk weather."},
            {"name": "Chlorothalonil 500 SC", "rate": "2.0 L/ha",
             "phi_days": "7", "notes": "Protectant. Good rotation partner for metalaxyl."},
        ],
        biological_control=[
            "Copper-based products (Bordeaux mixture) for organic systems",
            "Trichoderma soil inoculants to suppress soil-borne inoculum",
        ],
        cultural_control=[
            "Plant certified disease-free seed tubers",
            "Destroy volunteer potatoes and cull piles (inoculum sources)",
            "Ensure good hilling to protect tubers from rain-splashed spores",
            "Destroy haulms 2-3 weeks before harvest if blight is present",
            "Do not irrigate by overhead sprinkler during high-risk periods",
        ],
        economic_threshold="First lesion found — spray immediately. Late blight is explosive; "
                           "delay of 2-3 days can result in total crop loss.",
        severity_scale={
            "mild": "< 5% leaf area, scattered lesions on a few plants",
            "moderate": "5-25% leaf area, multiple plants affected, spreading",
            "severe": "> 25% leaf area, rapid canopy collapse, tuber infection likely",
        },
    ),
    DiseaseProfile(
        name="Early Blight",
        pathogen="Alternaria solani",
        pathogen_type="fungal",
        symptoms=[
            "Dark brown concentric-ringed spots on older leaves (target-board appearance)",
            "Lesions start on lower, older leaves and progress upward",
            "Yellowing and premature senescence of affected leaves",
            "Stem lesions: dark, elongated cankers near soil line",
        ],
        identification_markers=[
            "Concentric rings within lesions — classic 'target spot' appearance",
            "Starts on LOWER leaves (unlike late blight which often starts at top)",
            "Lesions dry and papery, not water-soaked",
        ],
        favourable_conditions={"temp_min_c": 20, "temp_max_c": 30, "humidity_min": 70},
        susceptible_stages=["Tuber Initiation", "Tuber Bulking", "Maturity"],
        resistant_varieties=["BP1 (moderate tolerance)"],
        susceptible_varieties=["Mondial", "Hermes"],
        chemical_control=[
            {"name": "Azoxystrobin 250 SC", "rate": "0.5 L/ha",
             "phi_days": "7", "notes": "Strobilurin; excellent for early blight. Max 3 applications per season."},
            {"name": "Mancozeb 80 WP", "rate": "2.0 kg/ha",
             "phi_days": "7", "notes": "Protectant; apply preventively from tuber initiation."},
        ],
        biological_control=[
            "Trichoderma harzianum soil applications",
            "Bacillus subtilis foliar sprays",
        ],
        cultural_control=[
            "Remove and destroy crop residue after harvest",
            "Rotate potatoes with non-solanaceous crops for 3 years",
            "Ensure adequate plant nutrition — stressed plants are more susceptible",
            "Avoid overhead irrigation in the evening",
        ],
        economic_threshold="10% leaf area on lower canopy affected at tuber initiation stage",
        severity_scale={
            "mild": "< 10% lower leaves affected, no yield impact",
            "moderate": "10-30% leaf area, premature senescence beginning",
            "severe": "> 30% leaf area, significant canopy loss, tuber yield reduced 20-40%",
        },
    ),
    DiseaseProfile(
        name="Bacterial Wilt",
        pathogen="Ralstonia solanacearum",
        pathogen_type="bacterial",
        symptoms=[
            "Sudden wilting of one or more stems, initially recovers overnight",
            "Wilting becomes permanent within days",
            "Brown discolouration of vascular tissue when stem is cut",
            "Bacterial ooze: milky white streaming from cut stem placed in water",
        ],
        identification_markers=[
            "CUT STEM TEST: place freshly cut stem in clear water — milky white bacterial streaming "
            "within 1-2 minutes is DIAGNOSTIC for Ralstonia",
            "Unilateral wilting (one side of plant wilts first)",
            "Eyes of infected tubers may exude bacterial ooze",
        ],
        favourable_conditions={"temp_min_c": 25, "temp_max_c": 37, "humidity_min": 70},
        susceptible_stages=["Vegetative", "Tuber Initiation", "Tuber Bulking"],
        resistant_varieties=["No fully resistant commercial varieties in Zimbabwe"],
        susceptible_varieties=["All commercial varieties are susceptible"],
        chemical_control=[
            {"name": "No effective chemical control", "rate": "N/A",
             "phi_days": "N/A", "notes": "Ralstonia is a soil-borne pathogen; chemicals are not effective."},
        ],
        biological_control=[
            "Bacillus amyloliquefaciens soil drench (suppressive, not curative)",
            "Trichoderma soil inoculant to build suppressive soil microbiome",
        ],
        cultural_control=[
            "Plant ONLY certified disease-free seed tubers — most important measure",
            "Rotate out of potatoes for 5+ years (pathogen persists in soil)",
            "Do not plant in fields with Ralstonia history",
            "Remove and destroy infected plants immediately — do NOT compost",
            "Avoid irrigating from water sources that may carry Ralstonia",
            "Disinfect tools and equipment between fields",
        ],
        economic_threshold="First wilted plant — rogue immediately. One infected plant can contaminate an entire field.",
        severity_scale={
            "mild": "1-5% plants wilted, rogued promptly",
            "moderate": "5-15% plants wilted, significant inoculum in soil",
            "severe": "> 15% plants wilted, field should be removed from potato rotation for 5+ years",
        },
    ),
]

_pests: List[PestProfile] = [
    PestProfile(
        name="Potato Tuber Moth",
        scientific_name="Phthorimaea operculella",
        pest_type="insect",
        identification=[
            "Adult: small grey-brown moth, 12-15 mm wingspan",
            "Larva: white to pinkish, up to 12 mm, with dark head",
            "Mines in leaves, petioles, and tubers",
            "Tuber damage: galleries under skin filled with frass",
        ],
        damage_symptoms=[
            "Leaf mining — transparent blotch mines visible from above",
            "Galleries in tubers — dark tunnels with frass under skin",
            "Tubers become unmarketable due to tunnelling damage",
            "Secondary rots enter through moth tunnels",
        ],
        life_cycle_notes="Complete cycle 25-35 days. Female lays eggs on leaves, soil near stems, "
                         "or exposed tubers. Larva mines leaves then moves to tubers via cracks in soil. "
                         "In storage, moths continue breeding on stored tubers if not controlled.",
        favourable_conditions={"temp_min_c": 20, "temp_max_c": 35, "humidity_min": 40},
        susceptible_stages=["Tuber Bulking", "Maturity", "Storage"],
        economic_threshold="5 moths per pheromone trap per night, or 10% of tubers with galleries at harvest",
        chemical_control=[
            {"name": "Cypermethrin 20 EC", "rate": "0.5 L/ha",
             "phi_days": "14", "notes": "Foliar spray targeting moths and exposed larvae"},
            {"name": "Chlorpyrifos 48 EC", "rate": "1.5 L/ha",
             "phi_days": "21", "notes": "Soil drench around stems to kill larvae migrating to tubers"},
        ],
        biological_control=[
            "Granulosis virus (Phthorimaea operculella GV) — effective in storage",
            "Bacillus thuringiensis var. kurstaki for leaf-mining larvae",
            "Parasitoid wasp Copidosoma koehleri",
        ],
        cultural_control=[
            "HILL UP soil to at least 15 cm over tubers — prevents moth access",
            "Irrigate to prevent soil cracking (cracks allow moth access to tubers)",
            "Harvest promptly at maturity — do not leave tubers in ground",
            "In storage, use PICS bags or treat with approved grain protectant",
            "Remove and destroy volunteer potato plants",
        ],
        scouting_protocol="Install pheromone traps at planting (1 per 0.5 ha). "
                          "Check traps twice weekly and record moth counts. "
                          "Also inspect 20 plants for leaf mines and check soil cracks near stems. "
                          "At harvest, cut 20 tubers open to check for galleries.",
    ),
    PestProfile(
        name="Aphids (Green Peach Aphid / Potato Aphid)",
        scientific_name="Myzus persicae / Macrosiphum euphorbiae",
        pest_type="insect",
        identification=[
            "Myzus persicae: small (1.5-2.5 mm), pale green to yellowish-green",
            "Macrosiphum euphorbiae: larger (3-4 mm), green or pink",
            "Colonies on leaf undersides, stems, and growing tips",
            "Winged forms migrate between fields transmitting viruses",
        ],
        damage_symptoms=[
            "Leaf curling and distortion",
            "Honeydew and sooty mould on lower leaves",
            "Virus transmission (PVY, PLRV) — most economically important damage",
            "Stunted growth under heavy infestation",
        ],
        life_cycle_notes="Parthenogenetic reproduction. Population doubles every 5-7 days in warm weather. "
                         "Winged forms colonise new fields and transmit viruses non-persistently (PVY) "
                         "or persistently (PLRV). Even low aphid numbers can transmit viruses.",
        favourable_conditions={"temp_min_c": 15, "temp_max_c": 28, "humidity_min": 40},
        susceptible_stages=["Vegetative", "Tuber Initiation"],
        economic_threshold="5 aphids per compound leaf (for ware potatoes); "
                           "ZERO tolerance in seed potato production",
        chemical_control=[
            {"name": "Imidacloprid 200 SL", "rate": "0.25 L/ha",
             "phi_days": "21", "notes": "Systemic; effective but use judiciously to protect pollinators"},
            {"name": "Pirimicarb 50 WG", "rate": "0.3 kg/ha",
             "phi_days": "7", "notes": "Selective aphicide — does not harm most beneficial insects"},
        ],
        biological_control=[
            "Ladybird beetles (Hippodamia, Coccinella spp.)",
            "Hoverfly larvae (Syrphidae)",
            "Parasitic wasp Aphidius matricariae",
            "Lacewings (Chrysoperla carnea)",
        ],
        cultural_control=[
            "Use certified virus-free seed tubers",
            "Destroy volunteer potatoes (virus reservoirs)",
            "Plant early to avoid peak aphid flights",
            "Mineral oil sprays to reduce virus transmission in seed crops",
            "Remove weed hosts (Solanaceae, Brassicaceae)",
        ],
        scouting_protocol="From emergence, inspect 20 plants weekly (5 per quadrant). "
                          "Turn over compound leaves and count aphids. "
                          "Record winged vs wingless forms — winged aphids indicate immigration. "
                          "In seed crops, use yellow water traps to monitor flying aphid populations. "
                          "Scout twice weekly from tuber initiation onward.",
    ),
    PestProfile(
        name="Root-Knot Nematode",
        scientific_name="Meloidogyne incognita / M. javanica",
        pest_type="nematode",
        identification=[
            "Not visible without magnification — microscopic worms in soil/roots",
            "Females form characteristic 'knots' (galls) on roots",
            "Galls are swellings on roots, 2-10 mm diameter",
            "Tubers may show bumpy, warty surface in severe cases",
        ],
        damage_symptoms=[
            "Stunted, chlorotic plants in patches",
            "Root galling — characteristic swellings on root system",
            "Reduced tuber size and number",
            "Warty, bumpy tuber surface (reduces market value)",
            "Plants wilt easily even when soil is moist",
        ],
        life_cycle_notes="Egg to adult in 25-30 days at 25-30°C. Females sedentary; "
                         "lay 200-500 eggs in gelatinous mass on root surface. "
                         "Juveniles (J2) are the infective stage — invade roots and establish feeding sites. "
                         "Build up over successive susceptible crops.",
        favourable_conditions={"temp_min_c": 20, "temp_max_c": 35, "humidity_min": 50},
        susceptible_stages=["Vegetative", "Tuber Initiation", "Tuber Bulking"],
        economic_threshold="200 J2 per 200 cc soil (pre-plant soil test); galling index > 2 on 0-5 scale",
        chemical_control=[
            {"name": "Oxamyl 24 SL (Vydate)", "rate": "5.0 L/ha",
             "phi_days": "28", "notes": "Apply at planting; soil drench in furrow"},
            {"name": "Fenamiphos 40 EC (Nemacur)", "rate": "5.0 L/ha",
             "phi_days": "60", "notes": "Soil application at planting; highly toxic — use with caution"},
        ],
        biological_control=[
            "Paecilomyces lilacinus — fungal egg parasite",
            "Purpureocillium lilacinum soil inoculant",
            "Plant nematode-suppressive cover crops (Crotalaria, Tagetes)",
        ],
        cultural_control=[
            "Rotate with non-host crops (cereals, alliums) for 2-3 years",
            "Plant marigolds (Tagetes) as trap/antagonist crop",
            "Solarise soil with clear plastic for 4-6 weeks before planting",
            "Add organic matter to build suppressive soil biology",
            "Avoid moving infested soil on equipment between fields",
        ],
        scouting_protocol="Pre-plant: collect soil samples (20 cores per field, 0-30 cm depth) and "
                          "submit for nematode analysis. During season, dig up 5 plants from poor patches "
                          "and examine roots for galling. Rate galling on 0-5 scale. "
                          "At harvest, inspect tuber surfaces for warty symptoms.",
    ),
]

_growth_stages: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Sprouting & Emergence",
        stage_code="S-VE",
        day_range=(0, 20),
        water_kc=0.35,
        water_mm_per_week=15,
        critical_nutrients=["P", "K"],
        key_activities=[
            "Plant pre-sprouted (chitted) seed tubers at 10-15 cm depth",
            "Spacing: 75-90 cm between rows, 25-30 cm in-row",
            "Apply basal fertiliser in furrow and cover before placing seed",
            "Light irrigation to settle soil around seed pieces",
        ],
        risks=["Seed piece decay in cold/wet soil", "Rhizoctonia damping-off",
               "Delayed emergence in un-chitted seed"],
        scientific_notes="Pre-sprouting (chitting) seed tubers at 15-20°C in diffused light for 2-3 weeks "
                         "before planting accelerates emergence by 7-10 days and improves stand uniformity. "
                         "Apical dominance means the 'rose end' sprouts first; seed pieces should have "
                         "2-3 strong sprouts. Soil temperature >8°C required for planting.",
    ),
    GrowthStageRequirements(
        stage_name="Vegetative Growth",
        stage_code="V1-VN",
        day_range=(20, 40),
        water_kc=0.65,
        water_mm_per_week=30,
        critical_nutrients=["N", "P", "Mg"],
        key_activities=[
            "First hilling (earthing up) when plants are 15-20 cm tall",
            "Apply first N top-dressing at hilling",
            "Scout for aphids and early blight",
            "Weed control — potatoes compete poorly with weeds",
        ],
        risks=["Excessive N delays tuberisation", "Aphid virus transmission",
               "Late blight under cool, wet conditions"],
        scientific_notes="Vegetative growth establishes the photosynthetic canopy that will drive tuber bulking. "
                         "Excessive N at this stage promotes haulm growth at the expense of early tuberisation. "
                         "Hilling (earthing up) is essential to prevent tuber greening (solanine accumulation) "
                         "and provides physical barrier against tuber moth.",
    ),
    GrowthStageRequirements(
        stage_name="Tuber Initiation",
        stage_code="TI",
        day_range=(40, 55),
        water_kc=0.85,
        water_mm_per_week=40,
        critical_nutrients=["K", "Ca", "B"],
        key_activities=[
            "Second hilling to cover developing stolons",
            "Apply second N top-dressing (split application)",
            "Maintain consistent soil moisture — critical period",
            "Begin intensive late blight scouting",
        ],
        risks=["Moisture stress reduces tuber number permanently",
               "Heat stress (>30°C soil) inhibits tuberisation",
               "Late blight onset under cool, wet conditions"],
        scientific_notes="Tuber initiation is triggered by short days and cool temperatures in Solanum tuberosum. "
                         "Stolon tips swell to form tuber primordia. The NUMBER of tubers is determined at this stage "
                         "and cannot be increased later. Consistent soil moisture and soil temperature <20°C at "
                         "tuber level are critical. K is essential for starch synthesis in developing tubers.",
    ),
    GrowthStageRequirements(
        stage_name="Tuber Bulking",
        stage_code="TB",
        day_range=(55, 90),
        water_kc=1.00,
        water_mm_per_week=45,
        critical_nutrients=["K", "N", "Ca"],
        key_activities=[
            "Maintain steady irrigation — avoid wet/dry cycles",
            "Continue fungicide programme for late blight",
            "Scout for tuber moth — ensure adequate hilling",
            "Monitor for early blight on lower leaves",
        ],
        risks=["Irregular watering causes growth cracks and hollow heart",
               "Late blight can destroy canopy in 7-10 days",
               "Tuber moth damage if soil cracks expose tubers"],
        scientific_notes="Tuber bulking is the period of maximum dry matter accumulation. "
                         "Tubers gain 500-1000 kg/ha/day under optimal conditions. "
                         "The linear growth phase requires maximum water (Kc = 1.0) and K for starch synthesis. "
                         "Irregular irrigation causes second-growth abnormalities (knobby tubers, hollow heart). "
                         "Ca is critical for tuber skin quality and resistance to soft rot bacteria.",
    ),
    GrowthStageRequirements(
        stage_name="Maturation & Skin Set",
        stage_code="MAT",
        day_range=(90, 110),
        water_kc=0.60,
        water_mm_per_week=20,
        critical_nutrients=["K"],
        key_activities=[
            "Reduce irrigation gradually to promote skin set",
            "Desiccate haulms (mechanical or chemical) 2-3 weeks before harvest",
            "Allow skin to 'set' — rub test: skin should not peel easily",
            "If blight is present, destroy haulms to prevent tuber infection",
        ],
        risks=["Harvesting before skin set causes skinning injury and storage losses",
               "Late blight zoospores washed down to tubers by rain",
               "Over-watering delays skin set"],
        scientific_notes="Skin set involves suberisation of the periderm — formation of a tough, "
                         "corky skin layer that protects tubers during harvest and storage. "
                         "Haulm desiccation (Diquat or mechanical flailing) promotes skin set "
                         "and prevents late blight spores from reaching tubers via rain splash. "
                         "Allow 14-21 days between haulm kill and harvest for proper skin set.",
    ),
    GrowthStageRequirements(
        stage_name="Harvest",
        stage_code="H",
        day_range=(110, 120),
        water_kc=0.0,
        water_mm_per_week=0,
        critical_nutrients=[],
        key_activities=[
            "Skin set test: rub tuber firmly — skin should NOT peel",
            "Harvest in dry conditions to reduce disease entry",
            "Avoid mechanical damage — set digger depth correctly",
            "Grade, cure, and store at 10-15°C with good ventilation",
        ],
        risks=["Skinning and bruising if harvested too early or roughly",
               "Tuber moth infestation if tubers left in field overnight",
               "Bacterial soft rot if tubers harvested wet"],
        scientific_notes="Harvest at >80% skin set. Cure tubers at 15°C, 85-90% RH for 10-14 days "
                         "to heal harvest wounds (suberisation). Then store at 3-5°C for table stock "
                         "or 10-15°C for seed tubers. Avoid light exposure during curing/storage "
                         "to prevent solanine (glycoalkaloid) accumulation.",
    ),
]

_fertilizer = FertilizerSchedule(
    basal={
        "product": "Compound S (7:21:8) or Compound C (5:15:12)",
        "rate": "800-1000 kg/ha Compound S (high-yield target)",
        "timing": "At planting, banded in furrow 5 cm below seed piece",
        "nutrients_supplied": {"N": "56-70 kg", "P": "168-210 kg P2O5", "K": "64-80 kg K2O"},
        "scientific_basis": "Potato is a heavy feeder. High P promotes root and stolon development. "
                            "K is critical for tuber starch content and skin quality. "
                            "Compound S preferred for potato due to high P ratio.",
    },
    top_dress_1={
        "product": "Ammonium Nitrate (AN) 34.5% N",
        "rate": "200-250 kg/ha",
        "timing": "At first hilling (20-25 DAP)",
        "application": "Side-dress in furrow and hill up over the band",
        "scientific_basis": "Split N application — first top-dressing provides N for canopy growth "
                            "while avoiding excessive early N that delays tuberisation.",
    },
    top_dress_2={
        "product": "Ammonium Nitrate (AN) 34.5% N + Potassium Chloride (KCl)",
        "rate": "150 kg/ha AN + 100 kg/ha KCl",
        "timing": "At second hilling / tuber initiation (40-45 DAP)",
        "application": "Side-dress and hill up. Last N application.",
        "scientific_basis": "Final N split supports canopy maintenance during bulking. "
                            "Extra K at tuber initiation enhances starch deposition and skin quality. "
                            "Total N for the season: 180-250 kg/ha depending on target yield.",
    },
    foliar={
        "product": "Calcium Nitrate + Boron (Solubor)",
        "rate": "5 kg/ha Ca(NO3)2 + 1 kg/ha Solubor in 200 L water",
        "timing": "Two applications at tuber initiation and mid-bulking",
        "scientific_basis": "Ca improves tuber skin quality and resistance to bacterial soft rot. "
                            "B supports cell wall integrity in rapidly expanding tuber tissue.",
    },
    liming={
        "product": "Dolomitic lime (supplies Ca + Mg)",
        "rate": "2-3 t/ha if pH < 5.5",
        "timing": "3-6 months before planting",
        "scientific_basis": "Target pH 5.5-6.5. Above pH 6.5, common scab (Streptomyces) is favoured. "
                            "Dolomitic lime preferred as potato is sensitive to Mg deficiency.",
    },
    notes="Potato is a heavy feeder requiring 180-250 kg N, 150-210 kg P2O5, and 150-250 kg K2O per ha "
          "for yields of 30-50 t/ha. Split N into 3 applications. Do NOT apply N after tuber initiation "
          "is well advanced as it delays maturity and reduces dry matter content.",
)

_planting_windows: List[PlantingWindow] = [
    PlantingWindow(
        region="Natural Region I (Eastern Highlands)",
        optimal_start="February 1", optimal_end="March 15",
        acceptable_start="January 15", acceptable_end="April 1",
        notes="Cool-season crop. Main season Feb-Mar (autumn planting). "
              "Second crop possible Aug-Sep (spring planting). Irrigated production.",
    ),
    PlantingWindow(
        region="Natural Region II (Highveld)",
        optimal_start="February 15", optimal_end="March 31",
        acceptable_start="February 1", acceptable_end="April 15",
        notes="Main season: autumn planting (Feb-Mar) under residual moisture + irrigation. "
              "Spring planting Aug-Sep possible with full irrigation. "
              "Avoid mid-summer planting — too hot for tuberisation.",
    ),
    PlantingWindow(
        region="Natural Region III",
        optimal_start="February 15", optimal_end="March 31",
        acceptable_start="February 1", acceptable_end="April 15",
        notes="Irrigated production only. Cool winter period ideal. "
              "Frost risk in June-July must be managed with irrigation timing.",
    ),
    PlantingWindow(
        region="Natural Region IV",
        optimal_start="March 1", optimal_end="April 15",
        acceptable_start="February 15", acceptable_end="April 30",
        notes="Only viable under full irrigation. Heat stress limits summer production. "
              "Winter/cool season planting preferred. Limited area planted.",
    ),
    PlantingWindow(
        region="Natural Region V",
        optimal_start="March 15", optimal_end="May 1",
        acceptable_start="March 1", acceptable_end="May 15",
        notes="Only viable under full irrigation in cool season. Limited commercial potential. "
              "Night temperatures must be <20°C for tuber initiation.",
    ),
]

PROFILE = CropProfile(
    crop_name="Potato",
    scientific_name="Solanum tuberosum L.",
    family="Solanaceae",
    optimal_ph=(5.5, 6.5),
    critical_ph_low=4.8,
    optimal_soil_types=["Well-drained sandy loams", "Red volcanic soils", "Deep loams"],
    avoid_soil_types=["Waterlogged soils", "Heavy clays (poor tuber shape)", "Recently limed to pH >6.5 (scab risk)"],
    optimal_temp=(15.0, 22.0),
    critical_temp_low=2.0,
    critical_temp_high=30.0,
    base_temp_gdd=7.0,
    total_water_mm=500.0,
    growth_stages=_growth_stages,
    fertilizer_schedule=_fertilizer,
    diseases=_diseases,
    pests=_pests,
    planting_windows=_planting_windows,
    harvest_moisture="Harvest after skin set (14-21 days post haulm desiccation). "
                     "Tuber DM content 18-22% for table stock.",
    storage_conditions="Cure at 15°C, 85-90% RH for 10-14 days. "
                       "Store table stock at 3-5°C, 85-90% RH. "
                       "Seed potatoes at 10-15°C in diffused light. Ventilate to remove CO2.",
    post_harvest_notes="Grade by size: seed (28-55 mm), table (>55 mm), chat (<28 mm). "
                       "Avoid light exposure to prevent greening (solanine). "
                       "Zimbabwe's potato market prefers large, smooth, white-fleshed tubers.",
    natural_region_suitability={
        "I": "Excellent — cool temperatures ideal, two seasons possible",
        "IIa": "Good — irrigated cool-season production",
        "IIb": "Good — irrigated cool-season production",
        "III": "Moderate — irrigation essential, cool season only",
        "IV": "Limited — only under full irrigation in winter",
        "V": "Not recommended — heat stress and water limitations",
    },
)

ALIASES = ["potatoes", "irish potato"]
