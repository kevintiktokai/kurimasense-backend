"""Mustard greens / Tsunga (Brassica juncea) — Traditional Zimbabwean leafy vegetable, important in Shona diet."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List


MUSTARD_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Black Rot",
        pathogen="Xanthomonas campestris pv. campestris",
        pathogen_type="bacterial",
        symptoms=[
            "V-shaped yellowing from leaf margins progressing inward",
            "Blackened vascular tissue in petioles and stems",
            "Wilting of affected leaves, eventually entire plant",
            "Bacterial ooze from cut stems in humid weather",
        ],
        identification_markers=[
            "V-shaped chlorotic lesions originating at leaf margins (hydathode entry)",
            "Cross-section of stem or petiole shows blackened vascular bundles",
            "Distinct from nutrient deficiency — lesions are asymmetric and margin-originated",
        ],
        favourable_conditions={
            "humidity_min": 80,
            "temp_min_c": 25,
            "temp_max_c": 35,
            "note": "Warm, wet conditions. Spread by rain splash, overhead irrigation, "
                    "contaminated tools, and infected seed.",
        },
        susceptible_stages=["Seedling", "Vegetative growth", "Harvest period"],
        resistant_varieties=[],
        susceptible_varieties=["Tsunga (Giant) — susceptible under high disease pressure"],
        chemical_control=[
            {"name": "Copper oxychloride 85 WP", "rate": "2.5 kg/ha",
             "phi_days": "7", "notes": "Protectant only; apply preventively at 7-10 day intervals"},
            {"name": "Copper hydroxide (Kocide) 61.4 WG", "rate": "1.5 kg/ha",
             "phi_days": "7", "notes": "Better rainfastness; use during wet season"},
        ],
        biological_control=[
            "Hot-water seed treatment (50°C for 25 minutes) eliminates seed-borne bacteria",
            "Bacillus subtilis seed treatment for transplant production",
        ],
        cultural_control=[
            "Use disease-free or hot-water treated seed",
            "3-year minimum rotation away from all Brassica crops",
            "Remove infected plant debris and compost at high temperature",
            "Avoid overhead irrigation; use drip or furrow methods",
            "Sanitise tools between beds with 10% bleach solution",
        ],
        economic_threshold="Any plants showing V-shaped lesions with black veins warrants action",
        severity_scale={
            "mild": "<5% plants affected, isolated lesions on older leaves",
            "moderate": "5-20% plants with symptoms, systemic infection in some plants",
            "severe": ">20% plants affected — remove and destroy; break rotation cycle",
        },
    ),
    DiseaseProfile(
        name="Downy Mildew",
        pathogen="Hyaloperonospora parasitica",
        pathogen_type="fungal",
        symptoms=[
            "Angular yellow-green patches on upper leaf surface",
            "White to greyish-purple sporulation on lower leaf surface",
            "Lesions eventually turn brown and necrotic",
            "Leaf curling and premature defoliation in severe cases",
        ],
        identification_markers=[
            "Angular lesions bounded by veins on upper surface",
            "Downy sporulation visible on underside (check early morning)",
            "Distinguish from powdery mildew: downy mildew on underside, powdery on both sides",
        ],
        favourable_conditions={
            "humidity_min": 85,
            "temp_min_c": 10,
            "temp_max_c": 22,
            "note": "Cool, moist conditions with heavy dew. Worse in winter and cool-season crops.",
        },
        susceptible_stages=["Seedling", "Vegetative growth"],
        resistant_varieties=[],
        susceptible_varieties=["Most tsunga varieties"],
        chemical_control=[
            {"name": "Mancozeb 80 WP", "rate": "2.0 kg/ha", "phi_days": "7",
             "notes": "Protectant; apply preventively at 7-10 day intervals"},
            {"name": "Ridomil Gold MZ 68 WG", "rate": "2.5 kg/ha", "phi_days": "14",
             "notes": "Systemic; use when disease pressure is high. Limit to 3 applications/season"},
        ],
        biological_control=[
            "Adequate spacing improves air circulation and reduces leaf wetness duration",
            "Potassium silicate foliar sprays strengthen leaf cuticle",
        ],
        cultural_control=[
            "Plant spacing of 20-30 cm within rows for air circulation",
            "Avoid late afternoon irrigation",
            "Remove and destroy severely infected leaves",
            "Rotate with non-Brassica crops",
        ],
        economic_threshold="10% of harvestable leaves with angular lesions",
        severity_scale={
            "mild": "Lesions on lower/older leaves, <10% leaf area",
            "moderate": "10-25% of harvestable leaf area affected",
            "severe": ">25% leaf area — leaves unmarketable, heavy defoliation",
        },
    ),
    DiseaseProfile(
        name="Alternaria Leaf Spot",
        pathogen="Alternaria brassicae",
        pathogen_type="fungal",
        symptoms=[
            "Dark brown to black circular spots with concentric rings",
            "Yellow halo surrounding spots",
            "Spots coalesce and cause leaf blight under severe infection",
            "Starts on older leaves and progresses upward",
        ],
        identification_markers=[
            "Target-board pattern with concentric rings within lesions",
            "Dark sporulation on lesion surface visible with hand lens",
            "Shot-hole effect as dead tissue drops out of older lesions",
        ],
        favourable_conditions={
            "humidity_min": 80,
            "temp_min_c": 18,
            "temp_max_c": 30,
            "note": "Warm, wet conditions. Alternating wetting-drying promotes spore release. "
                    "Splash dispersal from soil-borne inoculum.",
        },
        susceptible_stages=["Vegetative growth", "Harvest period"],
        resistant_varieties=[],
        susceptible_varieties=["All commonly grown tsunga varieties"],
        chemical_control=[
            {"name": "Mancozeb 80 WP", "rate": "2.0 kg/ha", "phi_days": "7",
             "notes": "Protectant; 7-10 day intervals during wet weather"},
            {"name": "Score (Difenoconazole) 250 EC", "rate": "0.3 L/ha", "phi_days": "14",
             "notes": "Systemic triazole; curative and protectant activity"},
        ],
        biological_control=[
            "Trichoderma harzianum-based sprays as preventive measure",
            "Crop residue incorporation to accelerate decomposition of inoculum",
        ],
        cultural_control=[
            "Remove oldest infected leaves during harvest",
            "Crop rotation (2-3 years away from Brassicaceae)",
            "Avoid overhead irrigation",
            "Destroy crop residues after final harvest",
        ],
        economic_threshold="15% harvestable leaf area with lesions",
        severity_scale={
            "mild": "Scattered spots on older leaves only",
            "moderate": "Spots on 10-25% harvestable leaf area, some leaf blight",
            "severe": ">25% leaf area blighted — unmarketable leaves",
        },
    ),
]

MUSTARD_PESTS: List[PestProfile] = [
    PestProfile(
        name="Aphids",
        scientific_name="Brevicoryne brassicae / Myzus persicae",
        pest_type="insect",
        identification=[
            "Cabbage aphid: grey-green, mealy, waxy coating, dense colonies",
            "Green peach aphid: shiny pale green without waxy coating",
            "Winged forms develop when colonies are overcrowded",
            "White cast skins on leaf surfaces indicate colony activity",
        ],
        damage_symptoms=[
            "Leaf curling and distortion from phloem feeding",
            "Honeydew deposits with black sooty mould",
            "Stunted growth, reduced leaf size and quality",
            "Virus transmission reducing plant vigour",
        ],
        life_cycle_notes="Viviparous (live birth) reproduction; no males needed. "
                         "Populations can double every 3-4 days under optimal conditions (20-25°C). "
                         "Heavy rain physically removes aphids; dry spells promote build-up.",
        favourable_conditions={
            "temp_min_c": 18,
            "temp_max_c": 30,
            "note": "Warm, dry conditions. Excess nitrogen produces soft, succulent "
                    "growth that attracts aphid colonisation.",
        },
        susceptible_stages=["Seedling", "Vegetative growth", "Harvest period"],
        economic_threshold="20% of plants with colonies on harvestable leaves",
        chemical_control=[
            {"name": "Malathion 500 EC", "rate": "1.5 L/ha", "phi_days": "7",
             "notes": "Apply to leaf undersides; short residual"},
            {"name": "Acetamiprid 20 SP", "rate": "0.2 kg/ha", "phi_days": "7",
             "notes": "Systemic neonicotinoid; 14-21 day residual activity"},
        ],
        biological_control=[
            "Lady beetles (Hippodamia, Coccinella spp.) consume 50-100 aphids/day",
            "Parasitic wasps (Aphidius spp.) parasitise aphids creating characteristic mummies",
            "Lacewing larvae (Chrysoperla spp.) are generalist predators of aphids",
            "Syrphid fly larvae feed within aphid colonies",
        ],
        cultural_control=[
            "Intercrop with onion, garlic, or coriander to deter aphid colonisation",
            "Remove heavily infested leaves during harvest",
            "Avoid excessive nitrogen fertilisation",
            "Use reflective mulch to disorient winged aphids",
        ],
        scouting_protocol="Inspect 20 plants per bed weekly. Examine undersides of young and mid-canopy leaves. "
                          "Record percentage of plants with active colonies and note presence of natural enemies.",
    ),
    PestProfile(
        name="Diamondback Moth",
        scientific_name="Plutella xylostella",
        pest_type="insect",
        identification=[
            "Adult moth: 8-10 mm wingspan, grey-brown, diamond pattern along back when at rest",
            "Larva: pale green, cigar-shaped, 10-12 mm, very active",
            "Characteristic wriggling and dropping on silk thread when disturbed",
            "Loose silk cocoons on leaf undersides contain pupae",
        ],
        damage_symptoms=[
            "Windowpaning — larvae eat lower epidermis leaving translucent upper layer",
            "Irregular holes in older larvae feeding",
            "Severe defoliation of young leaves and growing points",
            "Frass and larvae contaminate harvestable leaves",
        ],
        life_cycle_notes="Rapid development: egg to adult in 14-21 days at 25°C. "
                         "Female lays up to 160 eggs over 10-day lifespan. "
                         "Notorious for insecticide resistance — rotate modes of action. "
                         "Continuous Brassica cropping enables year-round populations.",
        favourable_conditions={
            "temp_min_c": 20,
            "temp_max_c": 32,
            "note": "Warm, dry conditions favour population build-up. "
                    "Year-round problem where Brassica crops are grown continuously.",
        },
        susceptible_stages=["Seedling", "Vegetative growth", "Harvest period"],
        economic_threshold="5 larvae per plant or >15% leaves with windowpaning",
        chemical_control=[
            {"name": "Bacillus thuringiensis (Bt) var. kurstaki", "rate": "0.5-1.0 kg/ha",
             "phi_days": "0", "notes": "Apply in evening; UV degrades Bt. Safe for beneficials."},
            {"name": "Spinosad 480 SC", "rate": "0.1 L/ha", "phi_days": "3",
             "notes": "Naturalyte; excellent DBM activity. Maximum 3 sprays per crop cycle."},
        ],
        biological_control=[
            "Cotesia plutellae — parasitic wasp, very effective in Zimbabwe",
            "Diadegma insulare — ichneumonid parasitoid",
            "Bt sprays serve as biological control agent",
            "Avoid broad-spectrum insecticides to conserve natural enemies",
        ],
        cultural_control=[
            "Break Brassica cycle with 4-6 week fallow between crops",
            "Destroy crop residues after final harvest",
            "Intercrop with tomato or strong-smelling herbs",
            "Trap cropping with preferred host plants on field margins",
        ],
        scouting_protocol="Inspect 20 plants per bed twice weekly. Check leaf undersides for larvae, "
                          "eggs, and windowpaning damage. Record larvae count per plant.",
    ),
    PestProfile(
        name="Flea Beetles",
        scientific_name="Phyllotreta spp.",
        pest_type="insect",
        identification=[
            "Small (2-3 mm) dark metallic beetles that jump when disturbed (diagnostic)",
            "Shiny black, blue-black, or with yellow stripes depending on species",
            "Very active on leaf surfaces in warm sunshine",
            "Larvae are soil-dwelling, white with dark heads",
        ],
        damage_symptoms=[
            "Characteristic small round 'shot-holes' in leaves",
            "Pitting of cotyledons and young leaves",
            "Seedling death under severe attack",
            "Older plants tolerate moderate feeding but leaves become unmarketable",
        ],
        life_cycle_notes="Adults overwinter in soil and emerge in spring. Eggs laid in soil near plant roots. "
                         "Larvae feed on roots (minor damage). Adults cause most damage on foliage. "
                         "1-2 generations per season. Most damaging to seedlings and young transplants.",
        favourable_conditions={
            "temp_min_c": 20,
            "temp_max_c": 30,
            "note": "Warm, sunny, dry conditions — beetles are most active and damaging. "
                    "Less active in cool, wet weather.",
        },
        susceptible_stages=["Seedling", "Transplant establishment"],
        economic_threshold="5 beetles per plant on seedlings or 10% leaf area with shot-holes",
        chemical_control=[
            {"name": "Carbaryl 85 WP", "rate": "2.0 kg/ha", "phi_days": "7",
             "notes": "Apply when threshold exceeded; effective on adults"},
            {"name": "Cypermethrin 200 EC", "rate": "0.3 L/ha", "phi_days": "7",
             "notes": "Pyrethroid; good knockdown but short residual"},
        ],
        biological_control=[
            "Ground beetles (Carabidae) predate flea beetle larvae in soil",
            "Entomopathogenic nematodes (Steinernema spp.) target soil-dwelling larvae",
            "Encourage diverse ground cover to harbour predators",
        ],
        cultural_control=[
            "Use transplants rather than direct seeding to avoid cotyledon stage vulnerability",
            "Crop debris removal eliminates overwintering sites",
            "Floating row covers protect seedling beds",
            "Intercrop with non-Brassica crops to reduce beetle concentration",
        ],
        scouting_protocol="Check seedlings and young transplants daily in warm weather. Count beetles per plant "
                          "and assess percentage of leaf area with shot-holes. Act quickly on seedlings.",
    ),
]


PROFILE = CropProfile(
    crop_name="Mustard greens",
    scientific_name="Brassica juncea",
    family="Brassicaceae",

    # Soil requirements
    optimal_ph=(6.0, 7.0),
    critical_ph_low=5.0,
    optimal_soil_types=["fersiallitic", "siallitic", "vertisol"],
    avoid_soil_types=["lithosol"],

    # Climate requirements
    optimal_temp=(12.0, 25.0),
    critical_temp_low=0.0,
    critical_temp_high=35.0,
    base_temp_gdd=4.4,
    total_water_mm=300.0,

    # Growth stages
    growth_stages=[
        GrowthStageRequirements(
            stage_name="Germination / Seedling",
            stage_code="GERM",
            day_range=(1, 10),
            water_kc=0.4,
            water_mm_per_week=15.0,
            critical_nutrients=["P"],
            key_activities=[
                "Direct sow at 1-2 cm depth in prepared beds",
                "Keep soil moist for uniform germination",
                "Thin to 15-20 cm spacing at 2-leaf stage",
                "Apply light shade in hot weather",
            ],
            risks=["Poor germination in hot soil (>35°C)", "Damping-off", "Flea beetle on cotyledons"],
            scientific_notes="Brassica juncea germinates rapidly (2-5 days at 20-25°C). Small seeds require "
                             "shallow sowing and firm seed-soil contact. Phosphorus promotes radicle elongation "
                             "and early root development.",
        ),
        GrowthStageRequirements(
            stage_name="Seedling Establishment",
            stage_code="ESTB",
            day_range=(11, 20),
            water_kc=0.5,
            water_mm_per_week=18.0,
            critical_nutrients=["N", "P"],
            key_activities=[
                "Thin to final spacing (15-20 cm between plants)",
                "Apply basal fertiliser (Compound C) if not pre-applied",
                "Weed control — hand hoe or mulch",
                "Scout for flea beetles and aphids",
            ],
            risks=["Flea beetle damage to young leaves", "Cutworm severing seedlings"],
            scientific_notes="True leaf development begins; shift from cotyledon dependence to photosynthetic "
                             "self-sufficiency. Root system establishes in top 15 cm of soil. "
                             "Adequate moisture critical for cell expansion in young leaves.",
        ),
        GrowthStageRequirements(
            stage_name="Rapid Vegetative Growth",
            stage_code="VGRO",
            day_range=(21, 35),
            water_kc=0.85,
            water_mm_per_week=25.0,
            critical_nutrients=["N", "K", "S"],
            key_activities=[
                "Top-dress with AN or LAN",
                "Monitor for diamondback moth and aphids",
                "Maintain consistent irrigation schedule",
                "Interrow cultivation for weed control",
            ],
            risks=["Diamondback moth defoliation", "Aphid colonies", "Downy mildew in cool weather"],
            scientific_notes="Peak growth rate and nitrogen demand. Brassica juncea accumulates biomass rapidly "
                             "with adequate N (120-150 kg N/ha equivalent). Glucosinolate concentration "
                             "(responsible for characteristic pungent taste of tsunga) increases under moderate "
                             "sulphur nutrition and mild water stress.",
        ),
        GrowthStageRequirements(
            stage_name="First Harvest Ready",
            stage_code="HRV1",
            day_range=(30, 45),
            water_kc=0.85,
            water_mm_per_week=25.0,
            critical_nutrients=["N", "K"],
            key_activities=[
                "Begin harvesting outer leaves at 20-25 cm length",
                "Leave 4-5 inner leaves for regrowth",
                "Top-dress with AN after harvest",
                "Continue pest monitoring",
            ],
            risks=["Over-harvesting reduces regrowth vigour", "Leaf quality decline in heat"],
            scientific_notes="Tsunga reaches harvestable size 30-45 days from sowing under optimal conditions. "
                             "Younger leaves are less pungent; older leaves have higher glucosinolate content "
                             "preferred in traditional Shona cooking. Harvest in early morning for best turgidity.",
        ),
        GrowthStageRequirements(
            stage_name="Multiple Harvest / Ratoon",
            stage_code="RATN",
            day_range=(46, 120),
            water_kc=0.8,
            water_mm_per_week=22.0,
            critical_nutrients=["N", "K", "Ca"],
            key_activities=[
                "Harvest every 2 weeks (outer leaves)",
                "Top-dress with AN/LAN after every second harvest",
                "Monitor for disease build-up and pest accumulation",
                "Replace plants showing bolting or exhaustion",
            ],
            risks=["Bolting under heat or water stress", "Nutrient depletion", "Pest accumulation"],
            scientific_notes="Tsunga supports 3-5 harvests over 2-3 months before vigour declines. "
                             "Bolting is hastened by long days, high temperatures (>30°C), "
                             "and water stress. Once flower buds appear, leaf quality declines rapidly "
                             "and plants should be replaced.",
        ),
    ],

    # Fertilizer schedule
    fertilizer_schedule=FertilizerSchedule(
        basal={
            "product": "Compound C (6:15:12)",
            "rate": "300-400 kg/ha",
            "timing": "At planting or immediately before sowing, incorporate into soil",
            "notes": "Well-rotted cattle manure at 15-20 t/ha is an excellent complement or substitute.",
        },
        top_dress_1={
            "product": "AN (34.5% N) or LAN (28% N)",
            "rate": "100-150 kg/ha AN",
            "timing": "3 weeks after sowing when plants are actively growing",
            "notes": "Apply along rows and water in immediately",
        },
        top_dress_2={
            "product": "AN (34.5% N)",
            "rate": "100 kg/ha",
            "timing": "After first harvest",
            "notes": "Repeat after each major harvest to sustain leaf regrowth",
        },
        foliar=None,
        liming={
            "product": "Dolomitic lime",
            "rate": "1-2 t/ha",
            "timing": "4-6 weeks before planting when pH < 5.5",
            "notes": "Brassicas need pH > 5.5 to avoid clubroot and nutrient lockup",
        },
        notes="Tsunga is fast-growing and requires consistent nitrogen supply. "
              "Organic matter (manure, compost) improves both nutrition and soil moisture retention.",
    ),

    # Diseases and pests
    diseases=MUSTARD_DISEASES,
    pests=MUSTARD_PESTS,

    # Planting windows
    planting_windows=[
        PlantingWindow(
            region="I",
            optimal_start="February 1",
            optimal_end="August 31",
            acceptable_start="January 1",
            acceptable_end="December 31",
            notes="Year-round production possible. Best quality in cooler months (Feb-Aug).",
        ),
        PlantingWindow(
            region="IIa",
            optimal_start="February 1",
            optimal_end="August 31",
            acceptable_start="January 1",
            acceptable_end="December 31",
            notes="Year-round with irrigation. Cooler months give best leaf quality and less pest pressure.",
        ),
        PlantingWindow(
            region="IIb",
            optimal_start="March 1",
            optimal_end="August 31",
            acceptable_start="January 1",
            acceptable_end="December 31",
            notes="Year-round with irrigation. Avoid hot-season sowing without shade.",
        ),
        PlantingWindow(
            region="III",
            optimal_start="March 1",
            optimal_end="August 31",
            acceptable_start="February 1",
            acceptable_end="October 31",
            notes="Cool season preferred. Hot-season production requires irrigation and shade.",
        ),
        PlantingWindow(
            region="IV",
            optimal_start="April 1",
            optimal_end="August 31",
            acceptable_start="March 1",
            acceptable_end="September 30",
            notes="Cool season only under irrigation. Heat stress limits summer production.",
        ),
    ],

    # Post-harvest
    harvest_moisture="Leaves harvested fresh at full turgidity, early morning",
    storage_conditions="Fresh leaves: 2-5°C at >95% RH for 3-5 days. "
                       "Bundle loosely; do not compress. Keep out of direct sun.",
    post_harvest_notes="Harvest outer leaves when 20-25 cm long. Bundle 10-15 leaves for market. "
                       "Pre-cool within 2 hours of harvest. Wilted leaves lose market value rapidly. "
                       "Tsunga can also be sun-dried for storage (mufushwa) — traditional preservation method.",

    # Zimbabwe natural regions
    natural_region_suitability={
        "I": "Excellent — ideal temperatures and moisture for year-round production.",
        "IIa": "Excellent — major production area, good market access in Harare corridor.",
        "IIb": "Good — year-round with irrigation supplement.",
        "III": "Good — cool season production excellent; summer needs irrigation.",
        "IV": "Moderate — cool season under irrigation only.",
        "V": "Marginal — hot and dry; only possible under full irrigation with shade.",
    },
)

ALIASES = ["tsunga", "mustard greens"]
