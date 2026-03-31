"""Covo (Brassica carinata) — Traditional Zimbabwean leafy vegetable, Ethiopian kale."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List


COVO_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Black Rot",
        pathogen="Xanthomonas campestris pv. campestris",
        pathogen_type="bacterial",
        symptoms=[
            "V-shaped yellow lesions starting from leaf margins",
            "Veins within lesions turn black (diagnostic)",
            "Progressive wilting and necrosis from leaf edge inward",
            "Systemic infection causes stunting and premature leaf drop",
        ],
        identification_markers=[
            "V-shaped chlorotic to necrotic lesions originating from hydathodes at leaf margins",
            "Blackened vascular tissue visible in cross-section of petioles and stems",
            "Bacterial ooze may be visible on cut stems in humid conditions",
        ],
        favourable_conditions={
            "humidity_min": 80,
            "temp_min_c": 25,
            "temp_max_c": 35,
            "note": "Warm, wet conditions with overhead irrigation or rain splash. "
                    "Seed-borne pathogen; contaminated seed is primary inoculum source.",
        },
        susceptible_stages=["Transplant establishment", "Active vegetative growth", "Harvest period"],
        resistant_varieties=["Rugare — moderate tolerance"],
        susceptible_varieties=["Most open-pollinated local landraces"],
        chemical_control=[
            {"name": "Copper oxychloride 85 WP", "rate": "2.5 kg/ha",
             "phi_days": "7", "notes": "Protectant only; will not cure systemic infections. "
                                       "Apply preventively in wet weather."},
            {"name": "Copper hydroxide (Kocide) 61.4 WG", "rate": "1.5 kg/ha",
             "phi_days": "7", "notes": "Better rainfastness than copper oxychloride"},
        ],
        biological_control=[
            "Use certified, hot-water treated seed (50°C for 25 minutes)",
            "Bacillus subtilis seed treatment reduces seed-borne infection",
        ],
        cultural_control=[
            "Use disease-free seed or treat seed with hot water (50°C, 25 min)",
            "3-year rotation away from all Brassica crops",
            "Remove and destroy infected plants immediately",
            "Avoid overhead irrigation — use drip or furrow",
            "Control cruciferous weeds that harbour the pathogen",
        ],
        economic_threshold="Any V-shaped lesions with blackened veins warrants action",
        severity_scale={
            "mild": "<5% plants affected, isolated leaf lesions",
            "moderate": "5-20% plants with symptoms, some systemic infection",
            "severe": ">20% plants affected, widespread vascular infection — significant crop loss",
        },
    ),
    DiseaseProfile(
        name="Downy Mildew",
        pathogen="Hyaloperonospora parasitica",
        pathogen_type="fungal",
        symptoms=[
            "Yellow angular patches on upper leaf surface bounded by veins",
            "White to grey-purple fuzzy sporulation on lower leaf surface",
            "Older lesions turn brown and papery",
            "Severe infection causes leaf curling and premature drop",
        ],
        identification_markers=[
            "Angular chlorotic lesions on upper surface with corresponding downy growth beneath",
            "Sporulation best seen early morning when humidity is high",
            "Distinct from powdery mildew (downy mildew is on underside only)",
        ],
        favourable_conditions={
            "humidity_min": 85,
            "temp_min_c": 10,
            "temp_max_c": 22,
            "note": "Cool, moist nights followed by warm days. Dew formation critical for infection. "
                    "Worse in cool season plantings and irrigated gardens.",
        },
        susceptible_stages=["Seedling", "Transplant establishment", "Active vegetative growth"],
        resistant_varieties=[],
        susceptible_varieties=["Most Brassica carinata landraces"],
        chemical_control=[
            {"name": "Mancozeb 80 WP", "rate": "2.0 kg/ha", "phi_days": "7",
             "notes": "Protectant; apply before infection occurs, 7-10 day intervals"},
            {"name": "Ridomil Gold MZ (Metalaxyl-M + Mancozeb)", "rate": "2.5 kg/ha",
             "phi_days": "14", "notes": "Systemic + protectant; use when conditions highly favourable"},
        ],
        biological_control=[
            "Improve air circulation with adequate spacing (30 x 30 cm minimum)",
            "Potassium phosphonate foliar sprays stimulate plant defences",
        ],
        cultural_control=[
            "Ensure adequate plant spacing for air movement",
            "Avoid late afternoon irrigation — leaves must dry before nightfall",
            "Remove severely infected lower leaves",
            "Rotate with non-Brassica crops for at least 2 seasons",
        ],
        economic_threshold="10% of leaves showing angular lesions",
        severity_scale={
            "mild": "Scattered lesions on lower/older leaves only",
            "moderate": "Lesions spreading to mid-canopy, 10-25% leaf area affected",
            "severe": ">25% leaf area, premature defoliation — unmarketable leaves",
        },
    ),
    DiseaseProfile(
        name="Alternaria Leaf Spot",
        pathogen="Alternaria brassicicola",
        pathogen_type="fungal",
        symptoms=[
            "Dark brown to black circular spots with concentric rings (target spots)",
            "Spots often surrounded by yellow halo",
            "Older leaves affected first, progressing upward",
            "Severe infections cause shot-holing and leaf tatter",
        ],
        identification_markers=[
            "Concentric ring pattern within lesions (target-board appearance)",
            "Dark sporulation visible on lesion surface under hand lens",
            "Starts on oldest leaves and progresses to younger foliage",
        ],
        favourable_conditions={
            "humidity_min": 80,
            "temp_min_c": 20,
            "temp_max_c": 30,
            "note": "Warm, humid conditions with alternating wet/dry periods. "
                    "Infection requires free water on leaf surface for 9+ hours.",
        },
        susceptible_stages=["Active vegetative growth", "Harvest period"],
        resistant_varieties=[],
        susceptible_varieties=["All commonly grown varieties susceptible"],
        chemical_control=[
            {"name": "Mancozeb 80 WP", "rate": "2.0 kg/ha", "phi_days": "7",
             "notes": "Broad-spectrum protectant; 7-10 day spray intervals"},
            {"name": "Iprodione (Rovral) 50 WP", "rate": "1.0 kg/ha", "phi_days": "14",
             "notes": "Good activity against Alternaria; alternate with mancozeb"},
        ],
        biological_control=[
            "Trichoderma-based sprays as preventive treatment",
            "Compost teas may reduce inoculum build-up on leaf surfaces",
        ],
        cultural_control=[
            "Remove and destroy lower infected leaves during harvest",
            "Avoid overhead irrigation",
            "Crop rotation with non-Brassica species",
            "Adequate spacing for air circulation",
        ],
        economic_threshold="15% leaf area on harvestable leaves showing spots",
        severity_scale={
            "mild": "Spots on lower/oldest leaves only, <10% area",
            "moderate": "Spots on 10-25% of harvestable leaf area",
            "severe": ">25% leaf area spotted — leaves unmarketable",
        },
    ),
]

COVO_PESTS: List[PestProfile] = [
    PestProfile(
        name="Aphids",
        scientific_name="Brevicoryne brassicae (cabbage aphid) / Myzus persicae (green peach aphid)",
        pest_type="insect",
        identification=[
            "Cabbage aphid: grey-green, waxy, in dense colonies on leaf undersides",
            "Green peach aphid: pale green, shiny, less waxy than cabbage aphid",
            "Winged and wingless forms present; wings develop under crowding",
            "Cast white skins (exuviae) visible on leaves",
        ],
        damage_symptoms=[
            "Leaf curling and distortion from sap feeding",
            "Honeydew secretion leading to sooty mould growth",
            "Stunted growth and reduced leaf size under heavy infestation",
            "Virus transmission (Turnip mosaic virus, Cauliflower mosaic virus)",
        ],
        life_cycle_notes="Parthenogenetic reproduction; females produce live young without mating. "
                         "Generation time 7-10 days under warm conditions. Populations can explode rapidly "
                         "in warm, dry weather. Natural enemies often provide adequate control.",
        favourable_conditions={
            "temp_min_c": 18,
            "temp_max_c": 30,
            "humidity_note": "Warm, dry conditions favour rapid population build-up. "
                             "Heavy rain events physically remove aphids from plants.",
        },
        susceptible_stages=["Seedling", "Transplant establishment", "Active vegetative growth"],
        economic_threshold="20% of plants with colonies on growing points or harvestable leaves",
        chemical_control=[
            {"name": "Malathion 500 EC", "rate": "1.5 L/ha", "phi_days": "7",
             "notes": "Broad-spectrum; short residual. Apply to undersides of leaves."},
            {"name": "Acetamiprid 20 SP", "rate": "0.2 kg/ha", "phi_days": "7",
             "notes": "Systemic neonicotinoid; effective for 14-21 days"},
        ],
        biological_control=[
            "Lady beetles (Coccinellidae) — adults and larvae consume large numbers of aphids",
            "Lacewing larvae (Chrysoperla spp.) are voracious aphid predators",
            "Parasitic wasps (Aphidius spp.) cause aphid mummies",
            "Syrphid fly larvae feed on aphid colonies",
        ],
        cultural_control=[
            "Inspect transplants before planting — reject infested seedlings",
            "Intercrop with strong-scented herbs (coriander, dill) to deter colonisation",
            "Remove heavily infested lower leaves during harvest",
            "Avoid excessive nitrogen which promotes soft, aphid-attractive growth",
        ],
        scouting_protocol="Inspect 20 plants per bed weekly. Check undersides of leaves and growing points. "
                          "Record percentage of plants with colonies. Note presence of natural enemies.",
    ),
    PestProfile(
        name="Diamondback Moth",
        scientific_name="Plutella xylostella",
        pest_type="insect",
        identification=[
            "Adult: small (10 mm wingspan), grey-brown moth with diamond pattern when wings folded",
            "Larva: pale green, tapered at both ends, up to 12 mm",
            "Larvae wriggle vigorously and drop on silk thread when disturbed (diagnostic)",
            "Pupae in loose silk cocoons on leaf undersides",
        ],
        damage_symptoms=[
            "Windowpaning — larvae feed on lower leaf surface leaving upper epidermis intact",
            "Irregular holes in leaves as larvae grow larger",
            "Severe defoliation of growing points and young leaves",
            "Contamination of harvested leaves with larvae and frass",
        ],
        life_cycle_notes="Complete generation in 14-21 days under warm conditions. "
                         "Females lay 50-150 eggs singly on leaf undersides. "
                         "Highly resistant to many insecticides globally — "
                         "rotate chemical classes and emphasise biological control. "
                         "Year-round problem in Zimbabwe with continuous Brassica cultivation.",
        favourable_conditions={
            "temp_min_c": 20,
            "temp_max_c": 30,
            "note": "Warm, dry conditions favour rapid reproduction. "
                    "Continuous Brassica cropping maintains year-round populations.",
        },
        susceptible_stages=["Transplant establishment", "Active vegetative growth", "Harvest period"],
        economic_threshold="5 larvae per plant or 20% of leaves with windowpaning damage",
        chemical_control=[
            {"name": "Bacillus thuringiensis (Bt) var. kurstaki", "rate": "0.5-1.0 kg/ha",
             "phi_days": "0", "notes": "Biological insecticide; safe for beneficials. "
                                       "Apply in evening; UV degrades Bt protein."},
            {"name": "Spinosad 480 SC", "rate": "0.1 L/ha", "phi_days": "3",
             "notes": "Naturalyte insecticide; excellent DBM activity. Rotate with Bt."},
        ],
        biological_control=[
            "Cotesia plutellae — larval parasitoid wasp; very effective in Zimbabwe",
            "Diadegma insulare — ichneumonid larval parasitoid",
            "Bacillus thuringiensis (Bt) sprays are both biological and chemical control",
            "Encourage natural enemy populations by avoiding broad-spectrum insecticides",
        ],
        cultural_control=[
            "Break Brassica cropping cycle — include 4-6 week Brassica-free periods",
            "Destroy crop residues after final harvest",
            "Intercrop with tomato, onion, or garlic as repellent companions",
            "Use yellow sticky traps for monitoring adult flights",
        ],
        scouting_protocol="Inspect 20 plants per bed twice weekly. Check leaf undersides for eggs, larvae, "
                          "and windowpaning. Record larvae per plant and percentage damaged leaves.",
    ),
    PestProfile(
        name="Bagrada Bug",
        scientific_name="Bagrada hilaris",
        pest_type="insect",
        identification=[
            "Shield-shaped, 5-7 mm, black with white and orange markings",
            "Similar to harlequin bug but smaller",
            "Nymphs are smaller, rounder, without full colour pattern",
            "Often found in clusters on stems and leaf petioles",
        ],
        damage_symptoms=[
            "Stippled, chlorotic feeding marks on leaves from piercing-sucking mouthparts",
            "Wilting and collapse of seedlings under heavy infestation",
            "Star-shaped feeding scars around growing points",
            "Stunted, distorted growth when growing points are damaged",
        ],
        life_cycle_notes="Eggs laid in soil near host plants. Nymphs pass through 5 instars over 4-6 weeks. "
                         "Adults are strong fliers and can rapidly colonise new plantings. "
                         "Overwintering occurs in soil and crop debris.",
        favourable_conditions={
            "temp_min_c": 22,
            "temp_max_c": 35,
            "note": "Hot, dry conditions favour population build-up. "
                    "Major pest in warmer areas and during dry spells.",
        },
        susceptible_stages=["Seedling", "Transplant establishment", "Active vegetative growth"],
        economic_threshold="1 bug per seedling or 5 bugs per mature plant",
        chemical_control=[
            {"name": "Malathion 500 EC", "rate": "1.5 L/ha", "phi_days": "7",
             "notes": "Apply early morning when bugs are less active"},
            {"name": "Bifenthrin 100 EC", "rate": "0.4 L/ha", "phi_days": "7",
             "notes": "Pyrethroid; good knockdown activity against stink bugs"},
        ],
        biological_control=[
            "Egg parasitoids (Trissolcus spp.) provide natural population regulation",
            "Generalist predators (ground beetles, spiders) consume nymphs",
        ],
        cultural_control=[
            "Remove Brassica crop residues promptly after harvest",
            "Control cruciferous weeds (wild mustard, shepherd's purse) that harbour populations",
            "Use transplants rather than direct seeding to avoid vulnerable seedling stage",
            "Early planting before peak population build-up",
        ],
        scouting_protocol="Check 20 plants per bed early morning (bugs more visible and less mobile). "
                          "Look at stem bases, leaf petioles, and growing points. Count adults and large nymphs.",
    ),
]


PROFILE = CropProfile(
    crop_name="Covo",
    scientific_name="Brassica carinata",
    family="Brassicaceae",

    # Soil requirements
    optimal_ph=(6.0, 7.0),
    critical_ph_low=5.0,
    optimal_soil_types=["fersiallitic", "siallitic", "vertisol"],
    avoid_soil_types=["lithosol"],

    # Climate requirements
    optimal_temp=(15.0, 25.0),
    critical_temp_low=2.0,
    critical_temp_high=35.0,
    base_temp_gdd=4.4,
    total_water_mm=350.0,

    # Growth stages
    growth_stages=[
        GrowthStageRequirements(
            stage_name="Seedling / Nursery",
            stage_code="SEED",
            day_range=(1, 14),
            water_kc=0.4,
            water_mm_per_week=15.0,
            critical_nutrients=["N", "P"],
            key_activities=[
                "Sow seed in nursery beds or seed trays (5 mm depth)",
                "Keep seedbed moist but not waterlogged",
                "Provide shade cloth (40%) in hot weather",
                "Thin to 5 cm spacing in nursery if direct sown",
            ],
            risks=["Damping-off (Pythium/Rhizoctonia)", "Flea beetle damage to cotyledons"],
            scientific_notes="Brassica carinata germinates in 3-7 days at 20-25°C. "
                             "Phosphorus is critical for root establishment in the seedling phase. "
                             "Hypocotyl elongation is temperature-dependent; excessive heat causes leggy seedlings.",
        ),
        GrowthStageRequirements(
            stage_name="Transplant Establishment",
            stage_code="TRNS",
            day_range=(15, 28),
            water_kc=0.6,
            water_mm_per_week=20.0,
            critical_nutrients=["N", "P", "Ca"],
            key_activities=[
                "Transplant seedlings at 4-5 true leaf stage (30 x 30 cm spacing)",
                "Water immediately after transplanting",
                "Apply basal fertiliser (Compound C) at transplanting",
                "Scout for cutworms and Bagrada bug",
            ],
            risks=["Transplant shock", "Cutworm damage", "Bagrada bug on seedlings"],
            scientific_notes="Transplant at 4-5 true leaves for optimal survival. Root re-establishment "
                             "takes 5-7 days; during this period plants are vulnerable to wilting. "
                             "Calcium supports cell wall integrity during recovery.",
        ),
        GrowthStageRequirements(
            stage_name="Vegetative Growth (Leaf Expansion)",
            stage_code="VEGX",
            day_range=(29, 45),
            water_kc=0.85,
            water_mm_per_week=25.0,
            critical_nutrients=["N", "K", "S"],
            key_activities=[
                "Top-dress with AN or LAN at 3-4 weeks after transplant",
                "Weed control — hand hoe or mulch",
                "Monitor for aphids and diamondback moth",
                "Maintain consistent soil moisture",
            ],
            risks=["Aphid infestation", "Diamondback moth larvae", "Downy mildew in cool, wet weather"],
            scientific_notes="Rapid leaf area expansion driven by nitrogen. Brassica carinata has high N demand "
                             "(150-200 kg N/ha equivalent for commercial production). Sulphur is important for "
                             "glucosinolate synthesis which contributes to characteristic flavour and pest resistance.",
        ),
        GrowthStageRequirements(
            stage_name="First Harvest Ready",
            stage_code="HRV1",
            day_range=(46, 60),
            water_kc=0.9,
            water_mm_per_week=25.0,
            critical_nutrients=["N", "K"],
            key_activities=[
                "Begin harvesting outer/lower leaves when 25-30 cm long",
                "Leave 4-6 inner leaves for regrowth",
                "Top-dress with AN after each harvest cycle",
                "Continue pest and disease monitoring",
            ],
            risks=["Over-harvesting weakening regrowth", "Black rot in damaged leaves",
                   "Alternaria on stressed plants"],
            scientific_notes="First harvest at 45-60 days from sowing. Harvesting older outer leaves promotes "
                             "continued apical growth. Leave sufficient leaf area index (LAI > 2) for photosynthetic "
                             "capacity to drive regrowth. Nitrogen top-dressing after harvest replaces exported N.",
        ),
        GrowthStageRequirements(
            stage_name="Ratoon / Multiple Harvest Period",
            stage_code="RATN",
            day_range=(61, 150),
            water_kc=0.85,
            water_mm_per_week=25.0,
            critical_nutrients=["N", "K", "Ca"],
            key_activities=[
                "Harvest every 2-3 weeks (outer leaves only)",
                "Top-dress with LAN or AN after every second harvest",
                "Monitor for pest and disease build-up",
                "Replace exhausted plants after 4-6 harvests",
            ],
            risks=["Nutrient exhaustion", "Pest population build-up over time",
                   "Plant vigour decline and bolting"],
            scientific_notes="Covo supports 4-8 harvests over 3-5 months before plants lose vigour. "
                             "Repeated defoliation depletes carbohydrate reserves; adequate N and K inputs "
                             "maintain leaf quality and regrowth capacity. Plants eventually bolt "
                             "(transition to flowering) triggered by accumulated heat units or stress.",
        ),
    ],

    # Fertilizer schedule
    fertilizer_schedule=FertilizerSchedule(
        basal={
            "product": "Compound C (6:15:12)",
            "rate": "400-500 kg/ha",
            "timing": "At transplanting, incorporate into planting furrows",
            "notes": "Provides balanced NPK for establishment. "
                     "Alternatively apply well-rotted manure at 20 t/ha plus compound.",
        },
        top_dress_1={
            "product": "AN (34.5% N) or LAN (28% N)",
            "rate": "150-200 kg/ha AN or 200-250 kg/ha LAN",
            "timing": "3-4 weeks after transplanting",
            "notes": "Apply along rows and irrigate in. Split applications are more efficient.",
        },
        top_dress_2={
            "product": "AN (34.5% N)",
            "rate": "100-150 kg/ha",
            "timing": "After first harvest and every second harvest thereafter",
            "notes": "Essential for sustained regrowth and leaf quality. "
                     "Each leaf harvest removes approximately 30-40 kg N/ha.",
        },
        foliar={
            "product": "Calcium nitrate or Kelp extract",
            "rate": "5 g/L calcium nitrate",
            "timing": "Every 2-3 weeks during active harvest period",
            "notes": "Calcium strengthens cell walls and reduces tip burn. "
                     "Kelp provides micro-nutrients and growth stimulants.",
        },
        liming={
            "product": "Dolomitic lime",
            "rate": "1-2 t/ha",
            "timing": "4-6 weeks before planting if pH < 5.5",
            "notes": "Brassicas are sensitive to acid soils. Dolomitic lime also supplies Mg.",
        },
        notes="Covo is a heavy nitrogen feeder. Apply nitrogen after each harvest to sustain production. "
              "Manure (20 t/ha) provides excellent base fertility and improves moisture retention.",
    ),

    # Diseases and pests
    diseases=COVO_DISEASES,
    pests=COVO_PESTS,

    # Planting windows — year-round with irrigation
    planting_windows=[
        PlantingWindow(
            region="I",
            optimal_start="August 1",
            optimal_end="March 31",
            acceptable_start="January 1",
            acceptable_end="December 31",
            notes="Year-round production possible with irrigation. "
                  "Cool-season plantings produce best quality leaves.",
        ),
        PlantingWindow(
            region="IIa",
            optimal_start="August 1",
            optimal_end="April 30",
            acceptable_start="January 1",
            acceptable_end="December 31",
            notes="Year-round with irrigation. Rainfed October-March. "
                  "Best quality in cooler months.",
        ),
        PlantingWindow(
            region="IIb",
            optimal_start="September 1",
            optimal_end="April 30",
            acceptable_start="January 1",
            acceptable_end="December 31",
            notes="Year-round with irrigation. Rainfed planting October-February.",
        ),
        PlantingWindow(
            region="III",
            optimal_start="October 1",
            optimal_end="March 31",
            acceptable_start="September 1",
            acceptable_end="April 30",
            notes="Rainfed season October-March. Year-round with irrigation. "
                  "Hot-season plantings need shade net.",
        ),
        PlantingWindow(
            region="IV",
            optimal_start="October 15",
            optimal_end="February 28",
            acceptable_start="September 1",
            acceptable_end="April 30",
            notes="Rainfed only during summer rains. Irrigation essential for year-round. "
                  "Heat stress limits quality in October.",
        ),
    ],

    # Post-harvest
    harvest_moisture="Fresh leaves harvested at full turgidity, typically early morning",
    storage_conditions="Fresh leaves: store at 2-5°C and >95% RH for up to 5-7 days. "
                       "Bundle loosely to allow air circulation. Avoid compression.",
    post_harvest_notes="Harvest outer leaves when 25-30 cm long, snapping at leaf base. "
                       "Bundle in bunches of 8-12 leaves for market. "
                       "Pre-cool rapidly after harvest to extend shelf life. "
                       "Wilted or yellowed leaves are unmarketable.",

    # Zimbabwe natural regions
    natural_region_suitability={
        "I": "Excellent — abundant moisture, ideal temperatures for year-round production.",
        "IIa": "Excellent — major production area with good rainfall and market access.",
        "IIb": "Good — irrigation supplements extend growing season.",
        "III": "Good with irrigation — rainfed summer production viable.",
        "IV": "Moderate — requires irrigation; heat management in hot months.",
        "V": "Marginal — only under full irrigation with shade management.",
    },
)

ALIASES = ["ethiopian kale", "ethiopian mustard"]
