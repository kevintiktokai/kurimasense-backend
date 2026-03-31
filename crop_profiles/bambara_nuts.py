"""Bambara Nuts (Vigna subterranea) — Indigenous legume with complete protein and exceptional drought tolerance."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List


BAMBARA_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Cercospora Leaf Spot",
        pathogen="Cercospora canescens / Cercospora cruenta",
        pathogen_type="fungal",
        symptoms=[
            "Small, circular to angular brown spots on leaves",
            "Spots enlarge with grey-tan centres and dark brown margins",
            "Severely affected leaves turn yellow and drop prematurely",
            "Defoliation reduces pod filling and yield",
        ],
        identification_markers=[
            "Circular spots (2-8mm) with tan centre and dark brown border",
            "Grey sporulation visible on lesion surface in humid conditions",
            "Lower and middle canopy affected first",
            "Distinct from bacterial spots which are more angular and water-soaked",
        ],
        favourable_conditions={
            "humidity_min": 80, "temp_min_c": 22, "temp_max_c": 30,
            "leaf_wetness_hours": 10,
            "note": "Warm, humid weather with prolonged leaf wetness. Worse in "
                    "dense plantings and continuous bambara cropping."
        },
        susceptible_stages=["Flowering", "Pod formation", "Pod fill"],
        resistant_varieties=["Local Cream (moderate tolerance)"],
        susceptible_varieties=["Local Red (moderate susceptibility)"],
        chemical_control=[
            {"name": "Mancozeb 80 WP", "rate": "2.0-2.5 kg/ha",
             "phi_days": "14", "notes": "Protectant; apply at first symptoms and repeat at 14-day intervals"},
            {"name": "Carbendazim 500 SC", "rate": "0.5 L/ha",
             "phi_days": "14", "notes": "Systemic; good curative activity on established lesions"},
        ],
        biological_control=[
            "Trichoderma-based products on crop residue decomposition",
            "No specific biocontrol agents registered for bambara Cercospora",
        ],
        cultural_control=[
            "Crop rotation with non-host crops (cereals) for 2-3 years",
            "Remove and destroy infected crop residue after harvest",
            "Wider spacing (45 x 20cm) for air circulation in humid areas",
            "Avoid overhead irrigation which prolongs leaf wetness",
            "Plant tolerant landraces where available",
        ],
        economic_threshold="15% leaf area infected before pod fill",
        severity_scale={
            "mild": "< 10% leaf area spotted, lower canopy only",
            "moderate": "10-25% leaf area, mid-canopy affected — some defoliation",
            "severe": "> 25% leaf area, premature defoliation — 20-35% yield loss",
        },
    ),
    DiseaseProfile(
        name="Fusarium Wilt",
        pathogen="Fusarium oxysporum",
        pathogen_type="fungal",
        symptoms=[
            "Wilting of individual branches or whole plant despite adequate soil moisture",
            "Yellowing (chlorosis) of lower leaves progressing upward",
            "Brown discolouration of vascular tissue visible in split stems",
            "Stunting and premature death of affected plants",
        ],
        identification_markers=[
            "Unilateral or complete wilting with brown vascular discolouration (key diagnostic)",
            "Cut stem shows brown-streaked xylem vessels",
            "Distinguished from drought stress by vascular browning and asymmetric wilting",
            "May be confused with waterlogging but persists after soil dries",
        ],
        favourable_conditions={
            "soil_temp_c": "25-30", "soil_pH": "acidic (< 5.5)",
            "note": "Warm, acidic soils favour Fusarium. Builds up under continuous "
                    "legume cropping. Root damage by nematodes or cultivation increases entry points."
        },
        susceptible_stages=["Seedling", "Flowering", "Pod formation"],
        resistant_varieties=["Local Cream (moderate tolerance)"],
        susceptible_varieties=["Local Red"],
        chemical_control=[
            {"name": "Thiram seed treatment", "rate": "2-3 g/kg seed",
             "phi_days": "N/A", "notes": "Reduces seedling infection from contaminated seed or soil"},
            {"name": "Carbendazim seed treatment", "rate": "2 g/kg seed",
             "phi_days": "N/A", "notes": "Systemic protection during seedling establishment"},
        ],
        biological_control=[
            "Trichoderma harzianum seed or soil treatment (10 g/kg seed)",
            "Pseudomonas fluorescens rhizosphere colonisation",
            "Mycorrhizal inoculants improve root health and Fusarium tolerance",
        ],
        cultural_control=[
            "Crop rotation with cereals for 3-4 years (non-host break)",
            "Lime acidic soils to pH 6.0-6.5 to reduce Fusarium survival",
            "Avoid mechanical damage to roots during cultivation",
            "Remove and destroy wilted plants to reduce soil inoculum",
            "Use clean, disease-free seed from healthy fields",
            "Improve soil drainage — waterlogged soils predispose roots to infection",
        ],
        economic_threshold="5% plants showing wilt symptoms during flowering",
        severity_scale={
            "mild": "< 5% plants wilted, scattered in field",
            "moderate": "5-15% plants wilted, patches forming",
            "severe": "> 15% plants wilted — significant stand loss and yield reduction",
        },
    ),
]


BAMBARA_PESTS: List[PestProfile] = [
    PestProfile(
        name="Aphids",
        scientific_name="Aphis craccivora",
        pest_type="insect",
        identification=[
            "Small (1-2mm) soft-bodied insects, black to dark green",
            "Colony-forming — dense clusters on growing tips, leaf undersides, and stems",
            "Winged and wingless forms present in colonies",
            "Sticky honeydew deposits and associated sooty mould",
        ],
        damage_symptoms=[
            "Curling and distortion of young leaves and growing points",
            "Stunted growth due to sap feeding",
            "Sooty mould on honeydew-covered surfaces",
            "Virus transmission (bean common mosaic and others)",
            "Flower and pod abortion in heavy infestations",
        ],
        life_cycle_notes=(
            "Aphis craccivora reproduces parthenogenetically — females produce live "
            "nymphs without mating. Populations can double in 3-4 days under warm "
            "conditions. Winged forms develop when colonies are crowded and migrate "
            "to new plants. Multiple overlapping generations per season."
        ),
        favourable_conditions={
            "temp_min_c": 20, "temp_max_c": 30,
            "note": "Warm, dry weather favours rapid population buildup. "
                    "Heavy rains wash aphids off plants and reduce populations."
        },
        susceptible_stages=["Seedling", "Vegetative growth", "Flowering"],
        economic_threshold="30% of plants with aphid colonies on growing tips",
        chemical_control=[
            {"name": "Dimethoate 40 EC", "rate": "0.5-0.75 L/ha",
             "phi_days": "14", "notes": "Systemic; effective against sucking pests"},
            {"name": "Imidacloprid 200 SL", "rate": "0.25 L/ha",
             "phi_days": "14", "notes": "Neonicotinoid; avoid during flowering to protect pollinators"},
        ],
        biological_control=[
            "Ladybird beetles (Hippodamia, Coccinella) — important predators",
            "Lacewing larvae (Chrysoperla) consume large numbers of aphids",
            "Parasitoid wasps (Aphidius spp.) lay eggs inside aphids",
            "Entomopathogenic fungi (Beauveria bassiana) in humid conditions",
        ],
        cultural_control=[
            "Early planting to establish crop before peak aphid populations",
            "Remove weedy hosts (especially other legumes) around field margins",
            "Intercrop with cereals to reduce aphid colonisation",
            "Avoid excessive nitrogen which promotes lush growth favoured by aphids",
        ],
        scouting_protocol=(
            "Scout weekly from emergence. Check 20 plants per field for aphid "
            "colonies on growing tips and leaf undersides. Note presence of "
            "natural enemies — if predator:prey ratio is favourable (1:30), "
            "biological control may suffice. Spray only if threshold exceeded "
            "and natural enemies are scarce."
        ),
    ),
    PestProfile(
        name="Pod Borers",
        scientific_name="Maruca vitrata / Helicoverpa armigera",
        pest_type="insect",
        identification=[
            "Maruca: brown moth, 20-25mm; larvae cream with dark spots",
            "Helicoverpa: medium moth; larvae green/brown/pink, up to 40mm",
            "Larvae found inside flowers, pods, and boring into developing seeds",
            "Frass and silk webbing on flowers and pods",
        ],
        damage_symptoms=[
            "Flowers webbed together and eaten from inside (Maruca)",
            "Bore holes in pods with frass extrusion",
            "Partially eaten or destroyed seeds inside pods",
            "Premature pod drop",
        ],
        life_cycle_notes=(
            "Maruca larvae web flowers and bore into pods. Helicoverpa larvae are "
            "more mobile and feed externally on pods before boring in. Both pupate "
            "in soil. Multiple generations per season overlap with the crop cycle."
        ),
        favourable_conditions={
            "temp_min_c": 22, "temp_max_c": 32,
            "note": "Warm wet season conditions. Maruca populations build on "
                    "flowering cowpea and bambara nearby."
        },
        susceptible_stages=["Flowering", "Pod formation", "Pod fill"],
        economic_threshold="10% flowers or pods damaged, or 2 larvae per plant",
        chemical_control=[
            {"name": "Cypermethrin 200 EC", "rate": "0.25-0.5 L/ha",
             "phi_days": "14", "notes": "Apply at peak flowering when larvae are exposed"},
            {"name": "Lambda-cyhalothrin 50 EC", "rate": "0.3 L/ha",
             "phi_days": "14", "notes": "Target small larvae on flowers before pod boring"},
        ],
        biological_control=[
            "Bacillus thuringiensis (Bt) sprays on young larvae",
            "Trichogramma egg parasitoids",
            "Conserve natural enemies: spiders, predatory bugs",
        ],
        cultural_control=[
            "Early planting to avoid peak Maruca populations",
            "Remove and destroy infested flower clusters",
            "Crop rotation to reduce soil-pupating populations",
            "Intercropping with cereals reduces pest colonisation",
        ],
        scouting_protocol=(
            "Scout at flowering onset and weekly thereafter. Open 10 flowers per "
            "point at 5 points and check for Maruca larvae. Inspect 20 pods per "
            "point for bore holes. Spray when 10% of flowers or pods are damaged."
        ),
    ),
    PestProfile(
        name="Bruchids (Storage Pest)",
        scientific_name="Callosobruchus maculatus",
        pest_type="insect",
        identification=[
            "Adult: small (3-4mm) brown beetle with mottled wing covers",
            "Eggs: white, glued to seed surface",
            "Larvae: legless grubs developing entirely inside the seed",
            "Characteristic round exit holes in infested seeds",
        ],
        damage_symptoms=[
            "Round emergence holes (2mm) in stored seed",
            "Weight loss and reduced nutritional value of grain",
            "Powdery frass inside and around seeds",
            "Infested seeds unfit for planting (poor germination)",
            "Heavy infestation renders entire stock inedible",
        ],
        life_cycle_notes=(
            "Females glue eggs to seed surface. Larvae bore into seed and develop "
            "entirely inside, consuming up to 25% of seed weight. Pupal and adult "
            "stages inside seed. Adults emerge through circular exit holes. Cycle "
            "takes 25-35 days at 25-30°C. Multiple generations in storage."
        ),
        favourable_conditions={
            "temp_min_c": 25, "temp_max_c": 35,
            "humidity_min_pct": 60,
            "note": "Warm, humid storage conditions. Infestation often begins in "
                    "the field on mature pods and continues in storage."
        },
        susceptible_stages=["Post-harvest storage"],
        economic_threshold="1-2% of seeds with emergence holes at intake",
        chemical_control=[
            {"name": "Actellic Super (pirimiphos-methyl + permethrin)", "rate": "50 g/50 kg bag",
             "phi_days": "N/A", "notes": "Admix dust at storage; do not treat seed for consumption"},
            {"name": "Phostoxin (aluminium phosphide)", "rate": "1-2 tablets/m3",
             "phi_days": "N/A", "notes": "Fumigation for large stocks; trained operators only"},
        ],
        biological_control=[
            "Neem leaf powder mixed with stored grain (20 g/kg) — traditional practice",
            "Diatomaceous earth (1-2 g/kg grain) desiccates insects",
            "Dinteranthus weevil parasitoids in natural storage ecosystems",
        ],
        cultural_control=[
            "Sun-dry seed to < 10% moisture before storage",
            "Store in airtight containers (PICS bags, metal drums)",
            "Hermetic storage kills bruchids through oxygen depletion",
            "Clean and disinfect storage containers before use",
            "Regular inspection of stored grain — early detection prevents spread",
            "Traditional: mix with wood ash or fine sand to fill inter-seed spaces",
        ],
        scouting_protocol=(
            "Inspect stored grain monthly. Take 500g samples from top, middle, and "
            "bottom of each container. Count seeds with exit holes. If > 5% of seeds "
            "have holes, re-treat or fumigate immediately."
        ),
    ),
]


BAMBARA_GROWTH_STAGES: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Germination and Emergence",
        stage_code="GE",
        day_range=(0, 10),
        water_kc=0.35,
        water_mm_per_week=12,
        critical_nutrients=["Phosphorus"],
        key_activities=[
            "Plant at 3-5cm depth in moist soil",
            "Apply basal Compound D or SSP at planting",
            "Target 100,000-130,000 plants/ha (45 x 15-20cm spacing)",
            "Inoculate with Bradyrhizobium if first-time bambara field",
        ],
        risks=["Poor emergence in cold, wet soils", "Seed rot in waterlogged conditions",
               "Bird and rodent damage on planted seed"],
        scientific_notes=(
            "Bambara nut has epigeal germination — cotyledons emerge above soil level. "
            "Germination requires soil temperature above 15°C (optimal 25-30°C). "
            "The radical emerges first, followed by the hypocotyl hook. Bambara seeds "
            "are relatively large (10-15g per 100 seeds) providing vigorous emergence. "
            "Phosphorus is critical for nodulation initiation with Bradyrhizobium."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Seedling Establishment",
        stage_code="SE",
        day_range=(10, 25),
        water_kc=0.40,
        water_mm_per_week=14,
        critical_nutrients=["Phosphorus", "Nitrogen (until nodulation)"],
        key_activities=[
            "First weeding at 14-21 DAE",
            "Scout for aphid colonies on growing tips",
            "Assess stand — gap-fill if needed using pre-soaked seed",
            "Check for nodulation starting on roots (pink = active)",
        ],
        risks=["Weed competition (bambara is slow-growing initially)",
               "Aphid infestation on young seedlings",
               "Fusarium wilt causing seedling damping-off"],
        scientific_notes=(
            "Bambara develops a strong taproot and initial lateral roots. Nodulation "
            "by Bradyrhizobium begins at 10-14 DAE — pink interior indicates active "
            "nitrogen fixation. Trifoliate leaves emerge from the compact, bunching "
            "growth habit. The prostrate to semi-erect architecture begins to establish, "
            "which will later facilitate geocarpic pod development."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Vegetative Growth and Branching",
        stage_code="VB",
        day_range=(25, 50),
        water_kc=0.65,
        water_mm_per_week=20,
        critical_nutrients=["Phosphorus", "Potassium"],
        key_activities=[
            "Second weeding — last opportunity before canopy closes",
            "Scout for Cercospora leaf spot",
            "Ensure adequate phosphorus for nodulation and pod initiation",
            "Light earthing up to cover developing pegs (in ridged systems)",
        ],
        risks=["Cercospora leaf spot establishing",
               "Weed competition if canopy closure delayed",
               "Poor nodulation on acid or compacted soils"],
        scientific_notes=(
            "Bambara develops a dense, low canopy through prolific branching. The "
            "indeterminate growth habit means vegetative and reproductive phases overlap. "
            "Nitrogen fixation reaches maximum rates (50-100 kg N/ha over the season). "
            "Phosphorus is critical for both nodulation efficiency and early flower "
            "initiation. The prostrate branches will bear flowers at nodes that "
            "subsequently peg into the soil (geocarpy, similar to groundnut)."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Flowering and Pegging",
        stage_code="FP",
        day_range=(50, 80),
        water_kc=0.80,
        water_mm_per_week=24,
        critical_nutrients=["Calcium", "Phosphorus", "Potassium"],
        key_activities=[
            "No further cultivation to avoid disturbing pegs",
            "Scout for pod borers on flowers",
            "Monitor aphid populations",
            "Ensure calcium availability in pod zone (top 10cm soil)",
        ],
        risks=["Pod borer damage on flowers", "Drought stress reducing flower set",
               "Calcium deficiency causing unfilled pods"],
        scientific_notes=(
            "Bambara has small, yellow, papilionaceous flowers borne on short pedicels "
            "at stem nodes. After fertilisation, the gynophore (peg) elongates and "
            "penetrates the soil — pods develop underground (geocarpy). This is an "
            "adaptation to protect developing seeds from desiccation and herbivory. "
            "Calcium uptake by the developing pod occurs directly from surrounding soil "
            "through the pod wall, similar to groundnut. Sandy or well-structured soils "
            "facilitate pegging."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Pod Fill",
        stage_code="PF",
        day_range=(80, 120),
        water_kc=0.65,
        water_mm_per_week=18,
        critical_nutrients=["Potassium", "Calcium"],
        key_activities=[
            "Monitor for Cercospora leaf spot — protect remaining leaf area",
            "Continue aphid monitoring",
            "Assess pod development by carefully digging test plants",
            "Begin harvest preparations",
        ],
        risks=["Cercospora defoliation reducing pod fill",
               "Drought stress causing shrivelled seeds",
               "Termite damage on underground pods"],
        scientific_notes=(
            "Pod filling involves accumulation of starch (50-60%), protein (18-24%), "
            "and fat (6-8%). Bambara nut is unique among legumes for providing a "
            "complete protein — all essential amino acids are present, with particularly "
            "high lysine and methionine. The underground pods are protected from above-ground "
            "pests but vulnerable to soil-dwelling organisms. Pod moisture declines "
            "from 70% to 30% during this phase."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Maturity and Harvest",
        stage_code="MH",
        day_range=(120, 150),
        water_kc=0.30,
        water_mm_per_week=8,
        critical_nutrients=[],
        key_activities=[
            "Harvest when leaves yellow and majority of pods are mature",
            "Lift plants with a hand hoe or plough to expose pods",
            "Separate pods from roots and vines",
            "Sun-dry pods for 5-7 days; shell when dry",
            "Sort by size and colour for market or seed retention",
        ],
        risks=["Pod loss in soil if harvesting delayed (pods detach from plant)",
               "Termite damage on over-mature pods",
               "Rain damage on lifted pods drying in field",
               "Bruchid infestation beginning in field on mature pods"],
        scientific_notes=(
            "Maturity is indicated by leaf yellowing and senescence. Due to indeterminate "
            "flowering, pods at various maturity stages are present — harvest is timed "
            "when 75-80% of pods are mature. The hard shell of mature pods aids storage "
            "but must be cracked for cooking. Bambara can be eaten fresh (green) or "
            "dried. Harvest index is typically 0.25-0.35, lower than other legumes "
            "due to the large underground pod mass."
        ),
    ),
]


BAMBARA_FERTILIZER = FertilizerSchedule(
    basal={
        "product": "Compound D (7:14:7) or SSP (Single Super Phosphate, 18% P2O5)",
        "rate_kg_ha": 200,
        "timing": "At planting",
        "method": "Band-placed 5cm to side and 5cm below seed",
        "nutrients_applied": {"N": 14, "P2O5": 28, "K2O": 14},
        "notes": "As a legume, bambara fixes its own nitrogen through Bradyrhizobium "
                 "nodulation. Phosphorus is the most limiting nutrient — it drives both "
                 "root growth and nodule function.",
    },
    top_dress_1={
        "product": "None required (nitrogen-fixing crop)",
        "rate_kg_ha": 0,
        "timing": "N/A",
        "method": "N/A",
        "nutrients_applied": {},
        "notes": "Bambara fixes 50-100 kg N/ha through biological nitrogen fixation. "
                 "No nitrogen top-dressing is needed. If plants appear yellow and nodules "
                 "are absent, check soil pH and consider lime application.",
    },
    top_dress_2=None,
    foliar=None,
    liming={
        "product": "Agricultural lime (dolomitic preferred for Mg supply)",
        "rate_kg_ha": "500-1500 based on soil test",
        "timing": "3-6 months before planting",
        "notes": "Target pH 5.5-6.5. Liming improves calcium availability for pod "
                 "development and enhances Bradyrhizobium activity. Dolomitic lime "
                 "also supplies magnesium.",
    },
    notes=(
        "Bambara nut has low external nitrogen requirements due to BNF. Focus "
        "fertilisation on phosphorus (20-30 kg P2O5/ha) and ensure adequate calcium "
        "in the pod zone. Farmyard manure (5-10 t/ha) is an excellent basal amendment. "
        "Inoculate seed with Bradyrhizobium (cowpea group) if planting in a field "
        "without recent bambara or cowpea history."
    ),
)


BAMBARA_PLANTING_WINDOWS: List[PlantingWindow] = [
    PlantingWindow(
        region="NR I (Eastern Highlands)",
        optimal_start="October 15",
        optimal_end="November 15",
        acceptable_start="October 1",
        acceptable_end="December 1",
        notes="Excessive moisture may increase disease pressure. Choose well-drained soils.",
    ),
    PlantingWindow(
        region="NR II (Highveld)",
        optimal_start="November 1",
        optimal_end="November 30",
        acceptable_start="October 15",
        acceptable_end="December 15",
        notes="Good production area. Often grown in mixtures with maize.",
    ),
    PlantingWindow(
        region="NR III (Midlands)",
        optimal_start="November 1",
        optimal_end="December 1",
        acceptable_start="October 20",
        acceptable_end="December 15",
        notes="Well-suited. Important food security and nutritional crop.",
    ),
    PlantingWindow(
        region="NR IV (Semi-arid)",
        optimal_start="November 15",
        optimal_end="December 15",
        acceptable_start="November 1",
        acceptable_end="December 31",
        notes="Excellent — bambara is one of the most drought-tolerant legumes. "
              "Plant on first effective rains.",
    ),
    PlantingWindow(
        region="NR V (Arid Lowveld)",
        optimal_start="December 1",
        optimal_end="January 5",
        acceptable_start="November 15",
        acceptable_end="January 15",
        notes="Bambara is one of the few legume options here. Sandy soils preferred for pegging.",
    ),
]


PROFILE = CropProfile(
    crop_name="Bambara Nuts",
    scientific_name="Vigna subterranea",
    family="Fabaceae",
    optimal_ph=(5.5, 6.5),
    critical_ph_low=4.5,
    optimal_soil_types=["kaolinitic (sandy)", "fersiallitic (well-drained)", "siallitic"],
    avoid_soil_types=["vertisol (heavy clay — impedes pegging)", "lithosol (shallow/rocky)"],
    optimal_temp=(22.0, 30.0),
    critical_temp_low=10.0,
    critical_temp_high=40.0,
    base_temp_gdd=12.0,
    total_water_mm=300.0,
    growth_stages=BAMBARA_GROWTH_STAGES,
    fertilizer_schedule=BAMBARA_FERTILIZER,
    diseases=BAMBARA_DISEASES,
    pests=BAMBARA_PESTS,
    planting_windows=BAMBARA_PLANTING_WINDOWS,
    harvest_moisture="10-12% seed moisture (after sun-drying shelled nuts)",
    storage_conditions=(
        "Store dried, shelled nuts at < 10% moisture in airtight containers. "
        "Bambara can be stored in-shell (pod) for added protection against bruchids. "
        "Use PICS bags or metal drums for hermetic storage. Actellic Super dust "
        "for conventional storage. In traditional systems, storage above the cooking "
        "fire (smoke deters insects) is effective."
    ),
    post_harvest_notes=(
        "Sun-dry pods for 5-7 days until shells crack when pressed. Shell by hand or "
        "simple mechanical sheller. Sort by size and colour for market. Bambara nuts "
        "are cooked as whole seeds (boiled for 2-4 hours), ground into flour, or roasted. "
        "The complete protein profile (18-24% protein with balanced amino acids) makes "
        "bambara an excellent meat substitute. Increasingly valued in health food markets. "
        "Bambara residues improve soil fertility through nitrogen fixation residues."
    ),
    natural_region_suitability={
        "NR I": "Possible but excess moisture increases disease risk",
        "NR II": "Good — intercrop with maize or standalone",
        "NR III": "Well suited — important smallholder crop",
        "NR IV": "Excellent — outstanding drought tolerance makes it a key crop",
        "NR V": "Very good — one of the few legume options for this zone",
    },
)


ALIASES = ["bambara groundnut", "nyimo", "bambara nut"]
