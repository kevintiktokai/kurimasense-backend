"""Macadamia (Macadamia integrifolia) — Premium export nut tree, Chipinge/Vumba area."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List


MACADAMIA_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Phytophthora Trunk Canker",
        pathogen="Phytophthora cinnamomi",
        pathogen_type="fungal",
        symptoms=[
            "Dark, water-soaked lesions on trunk and major limbs",
            "Reddish-brown exudate oozing from bark cracks",
            "Progressive canopy dieback starting from affected limbs",
            "Crown thinning with yellowing and wilting of leaves",
        ],
        identification_markers=[
            "Dark staining visible when bark is removed (diagnostic)",
            "Canker margins clearly defined between healthy and diseased tissue",
            "Gum exudation from trunk, often near soil line or graft union",
            "Reddish-brown inner bark discolouration",
        ],
        favourable_conditions={
            "humidity_min": 85,
            "temp_min_c": 20,
            "temp_max_c": 30,
            "note": "Waterlogged, poorly drained soils favour root infection. "
                    "Spread by contaminated water and soil movement on equipment.",
        },
        susceptible_stages=["Young trees (1-5 years)", "Post-stress recovery", "Bearing trees under waterlogging"],
        resistant_varieties=["Beaumont (695) — moderate tolerance"],
        susceptible_varieties=["Nelmak 2", "HAES 344"],
        chemical_control=[
            {"name": "Ridomil Gold MZ (Metalaxyl-M + Mancozeb)", "rate": "2.5 kg/ha drench",
             "phi_days": "60", "notes": "Soil drench around root zone; apply preventively in wet season"},
            {"name": "Phosphorous acid (Phosguard)", "rate": "5 mL/L trunk injection or foliar spray",
             "phi_days": "28", "notes": "Trunk injection most effective for established cankers"},
        ],
        biological_control=[
            "Trichoderma harzianum soil inoculants to suppress Phytophthora in root zone",
            "Improve soil biology with compost applications to encourage antagonistic microbes",
        ],
        cultural_control=[
            "Ensure excellent drainage — raised beds or ridges for orchard establishment",
            "Avoid wounding trunks during mechanical operations",
            "Clean equipment between orchards to prevent soil-borne spread",
            "Remove and burn severely affected trees to reduce inoculum",
            "Mulch under canopy to moderate soil temperature and moisture",
        ],
        economic_threshold="Any trunk canker on young trees warrants immediate intervention",
        severity_scale={
            "mild": "Small isolated cankers on lower trunk, <10% canopy affected",
            "moderate": "Multiple cankers, 10-30% canopy dieback, reduced nut set",
            "severe": ">30% canopy dieback, girdling trunk cankers — tree removal may be necessary",
        },
    ),
    DiseaseProfile(
        name="Anthracnose",
        pathogen="Colletotrichum gloeosporioides",
        pathogen_type="fungal",
        symptoms=[
            "Dark brown to black spots on husks during nut development",
            "Premature nut drop with incomplete kernel fill",
            "Sunken, dark lesions on racemes causing flower blight",
            "Leaf spots with concentric rings on mature foliage",
        ],
        identification_markers=[
            "Dark, sunken husk lesions often with salmon-pink spore masses in humid conditions",
            "Concentric ring pattern on leaf lesions (diagnostic)",
            "Black raceme dieback from tip progressing downward",
        ],
        favourable_conditions={
            "humidity_min": 80,
            "temp_min_c": 20,
            "temp_max_c": 28,
            "rainfall_note": "Frequent rain during flowering and nut set dramatically increases severity",
        },
        susceptible_stages=["Flowering", "Nut set", "Nut development"],
        resistant_varieties=["Beaumont (695)"],
        susceptible_varieties=["Nelmak 2", "HAES 246"],
        chemical_control=[
            {"name": "Mancozeb 80 WP", "rate": "2.5 kg/ha", "phi_days": "14",
             "notes": "Protectant; apply pre-flowering and at nut set"},
            {"name": "Carbendazim 500 SC", "rate": "0.5 L/ha", "phi_days": "28",
             "notes": "Systemic; alternate with protectants to avoid resistance"},
        ],
        biological_control=[
            "Bacillus subtilis sprays during flowering to colonise floral surfaces competitively",
            "Trichoderma foliar sprays as protectant during low-pressure periods",
        ],
        cultural_control=[
            "Prune to open canopy and improve air circulation",
            "Remove fallen nuts and debris from orchard floor",
            "Maintain adequate spacing (9 x 9 m or 10 x 5 m hedgerow)",
            "Avoid overhead irrigation during flowering",
        ],
        economic_threshold="5% flower racemes or husks showing symptoms",
        severity_scale={
            "mild": "<5% nut drop, scattered husk lesions",
            "moderate": "5-20% premature nut drop, significant raceme blight",
            "severe": ">20% nut drop, widespread flower blight — 30-60% crop loss",
        },
    ),
    DiseaseProfile(
        name="Botrytis Blight",
        pathogen="Botrytis cinerea",
        pathogen_type="fungal",
        symptoms=[
            "Grey fuzzy mould on flower racemes during cool, wet weather",
            "Raceme blight with brown, water-soaked flower clusters",
            "Premature flower drop reducing nut set",
            "Grey mould on nuts under prolonged humid conditions",
        ],
        identification_markers=[
            "Grey-brown fuzzy sporulation visible on racemes (diagnostic)",
            "Water-soaked browning of flowers and immature nut clusters",
            "Petal blight progressing to entire raceme collapse",
        ],
        favourable_conditions={
            "humidity_min": 90,
            "temp_min_c": 12,
            "temp_max_c": 22,
            "note": "Cool, wet conditions during flowering. Common in Eastern Highlands (Chipinge/Vumba).",
        },
        susceptible_stages=["Flowering", "Early nut set"],
        resistant_varieties=[],
        susceptible_varieties=["All varieties susceptible under favourable conditions"],
        chemical_control=[
            {"name": "Iprodione (Rovral) 50 WP", "rate": "1.0 kg/ha", "phi_days": "21",
             "notes": "Apply at early flowering if wet conditions forecast"},
            {"name": "Switch (Cyprodinil + Fludioxonil)", "rate": "0.8 kg/ha", "phi_days": "14",
             "notes": "Excellent botrytis activity; alternate with other modes of action"},
        ],
        biological_control=[
            "Bacillus amyloliquefaciens foliar sprays during flowering",
            "Trichoderma harzianum preventive sprays before wet periods",
        ],
        cultural_control=[
            "Prune to improve ventilation through canopy",
            "Avoid excessive nitrogen fertilisation which promotes soft growth",
            "Time irrigation to allow foliage drying before nightfall",
            "Remove blighted racemes to reduce inoculum",
        ],
        economic_threshold="Any grey mould on racemes during flowering warrants spray",
        severity_scale={
            "mild": "Scattered raceme infection, <5% racemes affected",
            "moderate": "10-25% raceme blight, noticeable reduction in nut set",
            "severe": ">25% racemes blighted — significant crop loss expected",
        },
    ),
]

MACADAMIA_PESTS: List[PestProfile] = [
    PestProfile(
        name="Macadamia Nut Borer",
        scientific_name="Cryptophlebia ombrodelta",
        pest_type="insect",
        identification=[
            "Adult moth: brownish-grey, 15-20 mm wingspan with kidney-shaped marking on forewing",
            "Larva: pinkish-white caterpillar, up to 15 mm, found inside nut husk and shell",
            "Frass and entry holes visible on husk surface",
        ],
        damage_symptoms=[
            "Circular entry holes in husk and shell of developing nuts",
            "Larvae bore through shell and feed on kernel",
            "Premature nut drop with partially eaten kernels",
            "Frass at entry point on husk",
        ],
        life_cycle_notes="Eggs laid on husk surface; larvae bore through husk into shell over 3-4 weeks. "
                         "Pupation in soil or under bark. Multiple overlapping generations per year in warm areas. "
                         "Most damaging from January to April during kernel filling.",
        favourable_conditions={
            "temp_min_c": 20,
            "temp_max_c": 30,
            "note": "Warm, humid conditions favour population build-up. Peak activity coincides with nut maturation.",
        },
        susceptible_stages=["Nut development", "Shell hardening", "Kernel fill"],
        economic_threshold="2% of nuts with entry holes on sampled trees",
        chemical_control=[
            {"name": "Delegate (Spinetoram) 250 WG", "rate": "0.2 kg/ha", "phi_days": "14",
             "notes": "Apply when monitoring traps show moth flight peaks"},
            {"name": "Cypermethrin 200 EC", "rate": "0.5 L/ha", "phi_days": "21",
             "notes": "Contact pyrethroid; apply to husk surface before larval entry"},
        ],
        biological_control=[
            "Trichogrammatoidea cryptophlebiae egg parasitoid releases",
            "Beauveria bassiana fungal sprays targeting larvae",
            "Conserve natural enemies by avoiding broad-spectrum insecticides",
        ],
        cultural_control=[
            "Collect and destroy fallen nuts regularly (break pest life cycle)",
            "Maintain orchard floor hygiene to expose pupae to predators",
            "Use pheromone traps for monitoring flight peaks",
            "Timely harvest reduces exposure period",
        ],
        scouting_protocol="Install pheromone traps at 1 per 2 ha from December. Sample 50 nuts per block weekly, "
                          "checking for entry holes and frass. Record percentage damaged nuts.",
    ),
    PestProfile(
        name="Two-spotted Stink Bug",
        scientific_name="Bathycoelia distincta",
        pest_type="insect",
        identification=[
            "Shield-shaped green-brown bug, 12-15 mm long",
            "Two distinct dark spots on scutellum (diagnostic)",
            "Nymphs are smaller, rounded, and more brightly coloured",
            "Characteristic stink bug odour when disturbed",
        ],
        damage_symptoms=[
            "Feeding punctures on developing nuts causing kernel damage",
            "Dark spots on kernel (stylet sheaths visible in cross-section)",
            "Premature nut drop from severe feeding",
            "Kernel discolouration and off-flavours reducing grade quality",
        ],
        life_cycle_notes="Adults overwinter in surrounding vegetation and colonise orchards from September. "
                         "Eggs laid in clusters on leaves; 5 nymphal instars over 6-8 weeks. "
                         "Adults can fly between trees; 2-3 generations per season.",
        favourable_conditions={
            "temp_min_c": 18,
            "temp_max_c": 30,
            "note": "Warm conditions favour population build-up. "
                    "Adjacent indigenous bush and litchi orchards harbour overwintering adults.",
        },
        susceptible_stages=["Nut development", "Shell hardening", "Kernel fill"],
        economic_threshold="0.5 bugs per tree when shaking branches over a beating sheet",
        chemical_control=[
            {"name": "Mercaptothion (Malathion) 500 EC", "rate": "1.5 L/ha", "phi_days": "7",
             "notes": "Apply when threshold exceeded; good knockdown but short residual"},
            {"name": "Endosulfan 350 EC", "rate": "2.0 L/ha", "phi_days": "21",
             "notes": "Effective but being phased out; check current registration status"},
        ],
        biological_control=[
            "Anastatus spp. egg parasitoids provide significant natural control",
            "Encourage insectivorous birds with nesting boxes in orchards",
            "Maintain biodiversity strips to harbour beneficial predators",
        ],
        cultural_control=[
            "Remove weed hosts and surrounding bush harbourage within 50 m of orchard",
            "Trap cropping with preferred host plants on orchard margins",
            "Regular beating-sheet sampling to detect early colonisation",
            "Border sprays rather than whole-orchard treatment to preserve beneficials",
        ],
        scouting_protocol="From September, sample 10 trees per block using beating sheet (3 branches per tree). "
                          "Count adults and large nymphs. Record weekly; action threshold is 0.5 bugs per tree.",
    ),
    PestProfile(
        name="Macadamia Thrips",
        scientific_name="Scirtothrips aurantii",
        pest_type="insect",
        identification=[
            "Tiny (1-1.5 mm) slender yellow-orange insects",
            "Found in flowers, new flush, and under husks",
            "Adults have fringed wings typical of Thysanoptera",
        ],
        damage_symptoms=[
            "Scarring and russeting of young nuts and husks",
            "Distortion of new leaf flush with silvery feeding scars",
            "Flower damage leading to poor pollination and reduced nut set",
            "Cosmetic damage to husk surface",
        ],
        life_cycle_notes="Rapid reproduction; eggs inserted into plant tissue. Life cycle 14-21 days under warm "
                         "conditions. Multiple generations per year. Populations peak during flowering and new flush.",
        favourable_conditions={
            "temp_min_c": 20,
            "temp_max_c": 32,
            "humidity_note": "Hot, dry conditions favour population explosions. "
                             "Rain events can wash thrips off foliage temporarily.",
        },
        susceptible_stages=["Flowering", "New flush", "Early nut set"],
        economic_threshold="10 thrips per flower raceme or visible scarring on >5% of young nuts",
        chemical_control=[
            {"name": "Abamectin 18 EC", "rate": "0.5 L/ha", "phi_days": "14",
             "notes": "Translaminar activity; effective on larvae in protected feeding sites"},
            {"name": "Imidacloprid 200 SL", "rate": "0.25 L/ha", "phi_days": "28",
             "notes": "Systemic; soil drench or foliar. Avoid during bee-active flowering"},
        ],
        biological_control=[
            "Predatory mites (Amblyseius spp.) provide ongoing biological control",
            "Minute pirate bugs (Orius spp.) are effective thrips predators",
            "Beauveria bassiana biopesticide sprays under humid conditions",
        ],
        cultural_control=[
            "Maintain ground cover to harbour thrips predators",
            "Avoid excessive nitrogen that promotes soft flush growth",
            "Irrigate adequately — water stress exacerbates thrips damage",
            "Monitor during flowering with blue sticky traps",
        ],
        scouting_protocol="Use blue sticky traps (1 per 4 trees) during flowering. Inspect 10 racemes per block "
                          "weekly, shaking over white paper. Count adults and larvae.",
    ),
]


PROFILE = CropProfile(
    crop_name="Macadamia",
    scientific_name="Macadamia integrifolia",
    family="Proteaceae",

    # Soil requirements
    optimal_ph=(5.0, 6.5),
    critical_ph_low=4.5,
    optimal_soil_types=["fersiallitic", "siallitic"],
    avoid_soil_types=["vertisol", "lithosol"],

    # Climate requirements
    optimal_temp=(18.0, 28.0),
    critical_temp_low=3.0,
    critical_temp_high=38.0,
    base_temp_gdd=10.0,
    total_water_mm=1000.0,

    # Growth stages — annual cycle for bearing tree
    growth_stages=[
        GrowthStageRequirements(
            stage_name="Dormancy / Root Flush",
            stage_code="DORM",
            day_range=(1, 60),
            water_kc=0.5,
            water_mm_per_week=15.0,
            critical_nutrients=["P", "Ca", "B"],
            key_activities=[
                "Post-harvest pruning and canopy management",
                "Apply lime if pH below 5.0",
                "Repair irrigation systems",
                "Soil sampling and analysis",
            ],
            risks=["Frost damage to young trees", "Phytophthora in waterlogged soils"],
            scientific_notes="Winter dormancy period (June-August). Root flush occurs in late winter. "
                             "Carbohydrate reserves accumulated during this phase drive subsequent flowering. "
                             "Proteoid root clusters form, enhancing P uptake in low-P soils.",
        ),
        GrowthStageRequirements(
            stage_name="Flowering",
            stage_code="FLOW",
            day_range=(61, 120),
            water_kc=0.7,
            water_mm_per_week=20.0,
            critical_nutrients=["B", "Zn", "K"],
            key_activities=[
                "Monitor for Botrytis on racemes during wet weather",
                "Bee hive placement for pollination (2-4 hives/ha)",
                "Foliar boron application (Solubor 1 g/L)",
                "Thrips monitoring with blue sticky traps",
            ],
            risks=["Botrytis raceme blight", "Thrips damage", "Cold snaps reducing pollination"],
            scientific_notes="Macadamia racemes bear 100-300 flowers but only 0.3-0.5% set fruit. "
                             "Cross-pollination by bees significantly improves nut set. Boron is critical "
                             "for pollen tube growth; deficiency causes poor fertilisation. Flowering occurs "
                             "August-October in Eastern Highlands.",
        ),
        GrowthStageRequirements(
            stage_name="Nut Set and Development",
            stage_code="NSET",
            day_range=(121, 210),
            water_kc=0.85,
            water_mm_per_week=25.0,
            critical_nutrients=["N", "K", "Ca"],
            key_activities=[
                "First top-dress nitrogen application",
                "Monitor for nut borer (pheromone traps)",
                "Stink bug scouting with beating sheets",
                "Maintain irrigation schedule — water stress causes nut drop",
            ],
            risks=["Premature nut drop", "Nut borer entry", "Stink bug feeding damage"],
            scientific_notes="After fertilisation, nuts undergo rapid husk and shell expansion (October-January). "
                             "Shell hardening occurs progressively. Calcium is critical for shell integrity. "
                             "Oil accumulation in kernel begins after shell hardening. "
                             "70% of initial nut set is shed naturally (physiological drop).",
        ),
        GrowthStageRequirements(
            stage_name="Kernel Fill and Oil Accumulation",
            stage_code="KFIL",
            day_range=(211, 300),
            water_kc=0.9,
            water_mm_per_week=28.0,
            critical_nutrients=["K", "N", "Mg"],
            key_activities=[
                "Second top-dress nitrogen application",
                "Continue nut borer and stink bug monitoring",
                "Potassium foliar sprays to support oil accumulation",
                "Prepare for harvest — check dehusking equipment",
            ],
            risks=["Nut borer damage to kernel", "Stink bug feeding reduces quality grade",
                   "Water stress reduces kernel recovery"],
            scientific_notes="Kernel fill occurs January-April. Oil accumulation drives kernel quality — "
                             "target 72%+ oil content for premium grade. Potassium enhances oil synthesis "
                             "and kernel size. Water stress during this phase directly reduces kernel recovery "
                             "percentage (KR%) which determines commercial value.",
        ),
        GrowthStageRequirements(
            stage_name="Harvest and Maturation",
            stage_code="HARV",
            day_range=(301, 365),
            water_kc=0.6,
            water_mm_per_week=15.0,
            critical_nutrients=["K"],
            key_activities=[
                "Collect fallen nuts every 2-3 weeks",
                "Dehusk within 24 hours of collection",
                "Dry to 1.5-3.5% kernel moisture content",
                "Sort and grade — reject insect-damaged kernels",
            ],
            risks=["Rain damage to fallen nuts", "Mould development on unharvested nuts",
                   "Rodent and bird losses"],
            scientific_notes="Mature nuts fall naturally from tree March-July. Prompt collection is critical — "
                             "nuts left on wet ground develop aflatoxin and quality deteriorates. Kernel moisture "
                             "must be reduced from ~25% to 1.5-3.5% through staged drying (initial air dry "
                             "then kiln at 38-48°C) to achieve shelf-stable product.",
        ),
    ],

    # Fertilizer schedule (per tree, bearing orchard)
    fertilizer_schedule=FertilizerSchedule(
        basal={
            "product": "Compound D (7:14:7) or superphosphate",
            "rate": "500 g/tree in planting hole; bearing trees 1-2 kg/tree/year",
            "timing": "At planting or July-August for bearing trees",
            "notes": "Macadamia is Proteaceae — sensitive to high P. Avoid excessive phosphorus.",
        },
        top_dress_1={
            "product": "LAN (28% N)",
            "rate": "300-500 g/tree",
            "timing": "October-November (nut set)",
            "notes": "Apply in ring around drip line; irrigate in",
        },
        top_dress_2={
            "product": "LAN (28% N) + Potassium chloride (KCl)",
            "rate": "300 g LAN + 200 g KCl per tree",
            "timing": "January-February (kernel fill)",
            "notes": "Potassium is critical for oil accumulation and kernel quality",
        },
        foliar={
            "product": "Solubor (boron) + Zinc sulphate",
            "rate": "1 g/L Solubor + 3 g/L ZnSO4",
            "timing": "Pre-flowering (August) and at nut set",
            "notes": "Boron critical for pollination; zinc for enzyme systems",
        },
        liming={
            "ite": "Calcitic lime",
            "rate": "2-3 t/ha when pH < 5.0",
            "timing": "Every 3-4 years based on soil analysis",
            "notes": "Macadamia tolerates moderately acid soils but Al toxicity below pH 4.5 limits roots",
        },
        notes="Macadamia is P-sensitive (Proteaceae family). Avoid high-P fertilisers on bearing trees. "
              "Foliar micronutrients more effective than soil-applied due to proteoid root system.",
    ),

    # Diseases and pests
    diseases=MACADAMIA_DISEASES,
    pests=MACADAMIA_PESTS,

    # Planting windows
    planting_windows=[
        PlantingWindow(
            region="I",
            optimal_start="October 15",
            optimal_end="December 15",
            acceptable_start="September 1",
            acceptable_end="February 28",
            notes="Eastern Highlands ideal for macadamia. Plant at onset of rains. "
                  "Frost-free sites with >1000 mm rainfall. First harvest year 5-7.",
        ),
        PlantingWindow(
            region="IIa",
            optimal_start="November 1",
            optimal_end="December 31",
            acceptable_start="October 1",
            acceptable_end="January 31",
            notes="Suitable with irrigation supplement. Select frost-free sites. "
                  "Chipinge, Chimanimani districts well suited.",
        ),
        PlantingWindow(
            region="IIb",
            optimal_start="November 1",
            optimal_end="December 31",
            acceptable_start="October 1",
            acceptable_end="January 31",
            notes="Marginal without supplementary irrigation. Select deep, well-drained soils.",
        ),
        PlantingWindow(
            region="III",
            optimal_start="November 15",
            optimal_end="December 31",
            acceptable_start="October 15",
            acceptable_end="January 31",
            notes="Only with full irrigation. Heat stress risk in Lowveld margins.",
        ),
        PlantingWindow(
            region="IV",
            optimal_start="November 15",
            optimal_end="December 15",
            acceptable_start="November 1",
            acceptable_end="January 15",
            notes="Not recommended without full irrigation. Marginal rainfall and heat stress.",
        ),
    ],

    # Post-harvest
    harvest_moisture="1.5-3.5% kernel moisture content (nut-in-shell ~10% at harvest, dried down)",
    storage_conditions="Dried nut-in-shell at <3.5% kernel moisture, cool (15-20°C), dry (<60% RH), "
                       "well-ventilated storage. Kernel: vacuum-packed or nitrogen-flushed, -18 to 4°C.",
    post_harvest_notes="Dehusk within 24 hours of collection. Stage drying: initial air dry to 8% shell moisture "
                       "then kiln at 38-48°C to 1.5-3.5% kernel moisture. Avoid exceeding 50°C (oil degradation). "
                       "Grade by flotation (specific gravity) and visual inspection. "
                       "First harvest typically year 5-7; full bearing from year 10-12.",

    # Zimbabwe natural regions
    natural_region_suitability={
        "I": "Excellent — Chipinge, Vumba, Honde Valley. Optimal rainfall, altitude, and temperatures.",
        "IIa": "Good with irrigation — Mutare surrounds, some Mashonaland East sites.",
        "IIb": "Moderate — requires irrigation; select sheltered, frost-free sites.",
        "III": "Marginal — only with full irrigation and frost-free microclimate.",
        "IV": "Not recommended — insufficient rainfall, heat stress.",
        "V": "Not suitable — too hot and dry.",
    },
)

ALIASES = ["macadamia nuts"]
