"""Rape (Brassica napus) — Traditional Zimbabwean leafy vegetable, transplanted, year-round production."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List


RAPE_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Black Rot",
        pathogen="Xanthomonas campestris pv. campestris",
        pathogen_type="bacterial",
        symptoms=[
            "V-shaped yellow-to-brown lesions from leaf margins",
            "Blackening of vascular tissue in stems and petioles",
            "Progressive wilting and chlorosis from leaf edge inward",
            "Systemic infection leads to stunting and plant death",
        ],
        identification_markers=[
            "V-shaped lesions entering through hydathodes at leaf margins (diagnostic)",
            "Cross-section of petiole or stem reveals blackened vascular ring",
            "Bacterial exudate from cut stems under high humidity",
        ],
        favourable_conditions={
            "humidity_min": 80,
            "temp_min_c": 25,
            "temp_max_c": 35,
            "note": "Warm, wet conditions. Seed-borne pathogen is primary inoculum. "
                    "Overhead irrigation and rain splash spread bacteria.",
        },
        susceptible_stages=["Transplant establishment", "Vegetative growth", "Harvest period"],
        resistant_varieties=["Hobson — moderate tolerance"],
        susceptible_varieties=["Most local open-pollinated varieties"],
        chemical_control=[
            {"name": "Copper oxychloride 85 WP", "rate": "2.5 kg/ha",
             "phi_days": "7", "notes": "Preventive; apply 7-10 day intervals in wet weather"},
            {"name": "Copper hydroxide (Kocide) 61.4 WG", "rate": "1.5 kg/ha",
             "phi_days": "7", "notes": "Better rainfastness; use during rainy season"},
        ],
        biological_control=[
            "Hot-water seed treatment (50°C for 25 minutes) to eliminate seed-borne bacteria",
            "Bacillus subtilis seed and transplant drench",
        ],
        cultural_control=[
            "Use certified disease-free or hot-water treated seed",
            "Minimum 3-year rotation away from Brassica crops",
            "Remove and burn infected plants immediately",
            "Avoid overhead irrigation — use drip or furrow",
            "Sanitise tools between beds/blocks",
        ],
        economic_threshold="Any plants with V-shaped lesions and blackened veins require intervention",
        severity_scale={
            "mild": "<5% plants affected with isolated leaf lesions",
            "moderate": "5-20% plants showing symptoms, some systemic infection",
            "severe": ">20% plants affected, widespread vascular blackening — rogue out and rotate",
        },
    ),
    DiseaseProfile(
        name="Downy Mildew",
        pathogen="Hyaloperonospora parasitica",
        pathogen_type="fungal",
        symptoms=[
            "Angular yellow patches on upper leaf surface, bounded by veins",
            "White to grey-purple sporulation on corresponding lower leaf surface",
            "Older lesions dry out and become papery brown",
            "Premature leaf drop in severe infections",
        ],
        identification_markers=[
            "Angular chlorotic lesions on upper surface with downy sporulation beneath",
            "Check leaf undersides early morning for visible sporulation",
            "Angular shape distinguishes from other leaf spots",
        ],
        favourable_conditions={
            "humidity_min": 85,
            "temp_min_c": 10,
            "temp_max_c": 22,
            "note": "Cool, moist conditions — heavy dew, overcrowded plantings, poor ventilation.",
        },
        susceptible_stages=["Seedling/nursery", "Transplant establishment", "Vegetative growth"],
        resistant_varieties=[],
        susceptible_varieties=["Hobson and most rape varieties under cool, wet conditions"],
        chemical_control=[
            {"name": "Mancozeb 80 WP", "rate": "2.0 kg/ha", "phi_days": "7",
             "notes": "Protectant; apply at 7-10 day intervals in cool weather"},
            {"name": "Ridomil Gold MZ 68 WG", "rate": "2.5 kg/ha", "phi_days": "14",
             "notes": "Systemic + protectant; for high disease pressure situations"},
        ],
        biological_control=[
            "Potassium phosphonate foliar spray induces plant defence responses",
            "Improved air circulation through spacing reduces infection periods",
        ],
        cultural_control=[
            "Adequate plant spacing (30 x 40 cm for rape)",
            "Morning irrigation to allow leaves to dry",
            "Remove severely infected older leaves",
            "Rotate with non-Brassica crops for 2+ seasons",
        ],
        economic_threshold="10% of leaves with angular lesions on harvestable foliage",
        severity_scale={
            "mild": "Scattered lesions on lower/older leaves",
            "moderate": "10-25% of harvestable leaves affected",
            "severe": ">25% harvestable leaf area affected — unmarketable",
        },
    ),
    DiseaseProfile(
        name="Clubroot",
        pathogen="Plasmodiophora brassicae",
        pathogen_type="fungal",
        symptoms=[
            "Wilting during hot afternoons despite adequate soil moisture",
            "Stunted growth with yellowing and poor vigour",
            "Swollen, distorted roots forming club-shaped galls",
            "Plants pull up easily revealing malformed root system",
        ],
        identification_markers=[
            "Swollen, club-shaped roots (diagnostic — pull up suspected plants to check)",
            "Roots lack fine lateral roots; major roots are galled",
            "Distinguish from nematode galls: clubroot galls are larger and fused",
        ],
        favourable_conditions={
            "soil_ph_below": 6.5,
            "temp_min_c": 18,
            "temp_max_c": 25,
            "soil_moisture": "wet",
            "note": "Acid, wet soils strongly favour disease. Resting spores persist in soil for 15-20 years. "
                    "Once introduced, field is permanently contaminated.",
        },
        susceptible_stages=["Seedling/nursery", "Transplant establishment", "All vegetative stages"],
        resistant_varieties=[],
        susceptible_varieties=["All Brassica napus varieties susceptible to varying degree"],
        chemical_control=[
            {"name": "Fluazinam (Shirlan) 500 SC", "rate": "3 L/ha soil drench",
             "phi_days": "28", "notes": "Pre-plant soil treatment in known infested fields"},
            {"name": "Lime (agricultural)", "rate": "2-4 t/ha to raise pH above 7.2",
             "phi_days": "N/A", "notes": "Raising pH above 7.2 suppresses clubroot development significantly"},
        ],
        biological_control=[
            "Lime to raise soil pH above 7.2 is the most effective management tool",
            "Trichoderma harzianum soil inoculants may provide partial suppression",
        ],
        cultural_control=[
            "Raise soil pH to 7.0-7.2 with agricultural lime before planting",
            "Long rotation (5+ years) away from all Brassica crops",
            "Use raised beds for improved drainage",
            "Avoid movement of infested soil on boots, tools, and equipment",
            "Destroy infected plants — do not compost clubroot-affected roots",
            "Use transplants raised in sterile media to avoid nursery contamination",
        ],
        economic_threshold="Any clubroot-positive plants in a new field warrants immediate action",
        severity_scale={
            "mild": "<5% plants wilting, isolated clubbed roots",
            "moderate": "5-20% plants stunted with clubbed roots",
            "severe": ">20% plants affected — consider abandoning Brassica on this field for 5+ years",
        },
    ),
]

RAPE_PESTS: List[PestProfile] = [
    PestProfile(
        name="Aphids",
        scientific_name="Brevicoryne brassicae / Myzus persicae",
        pest_type="insect",
        identification=[
            "Cabbage aphid: grey-green with waxy bloom, dense colonies on leaf undersides",
            "Green peach aphid: shiny pale green, smaller, less waxy",
            "Winged aphids appear when colonies are crowded or plant quality declines",
            "White exuviae (shed skins) on leaf surfaces",
        ],
        damage_symptoms=[
            "Leaf curling and puckering from phloem feeding",
            "Honeydew production leading to sooty mould on leaves",
            "Stunted growth under heavy infestation",
            "Virus transmission (Turnip mosaic virus)",
        ],
        life_cycle_notes="Parthenogenetic reproduction; populations double every 3-5 days under warm conditions. "
                         "Natural enemies (ladybirds, lacewings, parasitoids) often provide adequate control "
                         "if broad-spectrum insecticides are avoided.",
        favourable_conditions={
            "temp_min_c": 18,
            "temp_max_c": 30,
            "note": "Warm, dry weather promotes rapid build-up. Excess nitrogen creates "
                    "soft growth attractive to aphids.",
        },
        susceptible_stages=["Transplant establishment", "Vegetative growth", "Harvest period"],
        economic_threshold="20% of plants with aphid colonies on marketable leaves",
        chemical_control=[
            {"name": "Malathion 500 EC", "rate": "1.5 L/ha", "phi_days": "7",
             "notes": "Target leaf undersides; short residual"},
            {"name": "Acetamiprid 20 SP", "rate": "0.2 kg/ha", "phi_days": "7",
             "notes": "Systemic; 14-21 day protection. Preferred for heavy infestations."},
        ],
        biological_control=[
            "Ladybird beetles (Coccinellidae) — both adults and larvae are efficient predators",
            "Aphid parasitoids (Aphidius spp.) — look for bronze aphid mummies",
            "Lacewing larvae (Chrysoperla spp.)",
            "Allow natural enemy build-up before resorting to chemicals",
        ],
        cultural_control=[
            "Reject infested transplants from nursery",
            "Intercrop with aromatic herbs (basil, coriander) to deter colonisation",
            "Remove oldest, most-infested leaves during harvest",
            "Avoid excessive nitrogen fertilisation",
        ],
        scouting_protocol="Sample 20 plants per block weekly. Check undersides of leaves and growing points. "
                          "Record percentage with active colonies. Note natural enemy presence.",
    ),
    PestProfile(
        name="Diamondback Moth",
        scientific_name="Plutella xylostella",
        pest_type="insect",
        identification=[
            "Adult: small grey-brown moth, diamond pattern visible when wings folded at rest",
            "Larva: pale green, cigar-shaped, 8-12 mm, tapered at both ends",
            "Larvae wriggle vigorously backward and drop on silk thread when disturbed",
            "Pupae in loose, open-mesh silk cocoons on leaf undersides",
        ],
        damage_symptoms=[
            "Windowpaning — larvae consume lower epidermis leaving translucent upper layer",
            "Shot-holes from larger larvae eating through full leaf thickness",
            "Growing point damage causing multi-headed or blind plants",
            "Larvae and frass contaminate marketable leaves",
        ],
        life_cycle_notes="Complete life cycle in 14-21 days at 25°C. Females lay 50-150 eggs singly "
                         "on leaf undersides. Multiple overlapping generations year-round in Zimbabwe. "
                         "Globally the most insecticide-resistant agricultural pest — "
                         "biological control (Bt, parasitoids) is essential strategy.",
        favourable_conditions={
            "temp_min_c": 20,
            "temp_max_c": 30,
            "note": "Warm, dry conditions. Continuous Brassica cropping sustains populations year-round.",
        },
        susceptible_stages=["Transplant establishment", "Vegetative growth", "Harvest period"],
        economic_threshold="5 larvae per plant or >15% leaves with windowpane damage",
        chemical_control=[
            {"name": "Bacillus thuringiensis (Bt) var. kurstaki", "rate": "0.5-1.0 kg/ha",
             "phi_days": "0", "notes": "Apply evening; safe for beneficials; 0-day PHI ideal for leafy veg"},
            {"name": "Spinosad 480 SC", "rate": "0.1 L/ha", "phi_days": "3",
             "notes": "Low toxicity to mammals; excellent on DBM. Max 3 sprays/cycle."},
        ],
        biological_control=[
            "Cotesia plutellae parasitic wasp — highly effective in Zimbabwe",
            "Diadegma insulare parasitoid",
            "Bt sprays act as biological insecticide",
            "Preserve natural enemies by avoiding pyrethroids and organophosphates",
        ],
        cultural_control=[
            "Enforce 4-6 week Brassica-free period between crops",
            "Remove and compost crop residues after final harvest",
            "Intercrop with tomatoes or onions",
            "Use yellow sticky traps for adult monitoring",
        ],
        scouting_protocol="Inspect 20 plants per block twice weekly. Examine leaf undersides for larvae, "
                          "eggs, and windowpane damage. Record average larvae per plant.",
    ),
    PestProfile(
        name="Cutworms",
        scientific_name="Agrotis spp.",
        pest_type="insect",
        identification=[
            "Larvae: dull grey-brown, smooth, C-shaped when disturbed, up to 40 mm",
            "Nocturnal — hide in soil during day, feed at night",
            "Adults are grey-brown moths (not commonly seen)",
            "Larvae found curled in soil within 5 cm of damaged seedlings",
        ],
        damage_symptoms=[
            "Transplants cut at soil level, toppling over (classic cutworm damage)",
            "Several plants cut in a row along planting line",
            "Wilted seedlings lying on soil surface with stem severed at base",
            "Occasionally feed on lower leaves from soil level",
        ],
        life_cycle_notes="Eggs laid in soil; larvae feed nocturnally for 3-5 weeks before pupating in soil. "
                         "Most damaging within first 2 weeks of transplanting when stems are tender. "
                         "One larva can destroy multiple transplants in a single night.",
        favourable_conditions={
            "temp_min_c": 15,
            "temp_max_c": 30,
            "note": "Weedy or recently cleared fields with high organic matter. "
                    "Previous grass or weed cover provides egg-laying sites.",
        },
        susceptible_stages=["Transplant establishment (first 2 weeks)"],
        economic_threshold="1 cut plant per 10 m of row (typically 1 larva is responsible for multiple cuts)",
        chemical_control=[
            {"name": "Cutworm bait (Carbaryl + bran)", "rate": "5-10 kg bait/ha broadcast in evening",
             "phi_days": "7", "notes": "Apply in evening before irrigation. Bait = 1 kg Carbaryl + 10 kg bran + water"},
            {"name": "Chlorpyrifos 480 EC", "rate": "2.0 L/ha drench at base of transplants",
             "phi_days": "21", "notes": "Soil drench around transplant stems; apply in evening"},
        ],
        biological_control=[
            "Steinernema feltiae entomopathogenic nematodes target soil-dwelling larvae",
            "Encourage ground beetles (Carabidae) which predate cutworm larvae",
            "Bt var. kurstaki applied as soil drench has partial activity",
        ],
        cultural_control=[
            "Clear and cultivate land 2-3 weeks before transplanting to starve existing larvae",
            "Flood irrigate before transplanting to expose larvae to predation",
            "Collar transplants with cardboard or plastic tubes at soil level",
            "Scout at dusk or night with torch to find and hand-pick larvae",
            "Avoid transplanting into recently cleared weedy or grassy land",
        ],
        scouting_protocol="Check transplants early morning for cut stems. Dig in soil within 5 cm radius of "
                          "cut plants to find larvae. One larva may cut 3-5 plants per night. Act immediately.",
    ),
]


PROFILE = CropProfile(
    crop_name="Rape",
    scientific_name="Brassica napus",
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
    base_temp_gdd=5.0,
    total_water_mm=350.0,

    # Growth stages
    growth_stages=[
        GrowthStageRequirements(
            stage_name="Nursery / Seedbed",
            stage_code="NURS",
            day_range=(1, 21),
            water_kc=0.4,
            water_mm_per_week=15.0,
            critical_nutrients=["P", "N"],
            key_activities=[
                "Sow seed thinly in nursery beds at 5 mm depth",
                "Maintain moist (not waterlogged) seedbed",
                "Provide 40% shade cloth in summer nurseries",
                "Thin seedlings to 5 cm spacing at 2-leaf stage",
                "Harden off transplants by reducing water 3 days before planting",
            ],
            risks=["Damping-off (Pythium, Rhizoctonia)", "Overcrowding leading to leggy seedlings"],
            scientific_notes="Rape seedlings ready for transplant at 4-6 true leaves (21-28 days from sowing). "
                             "Nursery period is critical — stress-free seedlings establish faster. "
                             "Phosphorus promotes root development for transplant resilience.",
        ),
        GrowthStageRequirements(
            stage_name="Transplant Establishment",
            stage_code="TRNS",
            day_range=(22, 35),
            water_kc=0.6,
            water_mm_per_week=20.0,
            critical_nutrients=["N", "P", "Ca"],
            key_activities=[
                "Transplant at 30 x 40 cm spacing in prepared beds",
                "Apply Compound C basal fertiliser in planting holes",
                "Water immediately and daily for first week",
                "Scout for cutworms — inspect at dusk for 2 weeks",
            ],
            risks=["Cutworm cutting stems at soil level", "Transplant shock and wilting",
                   "Bagrada bug on young transplants"],
            scientific_notes="Root re-establishment takes 5-7 days. Transplant in late afternoon to reduce "
                             "wilting stress. Wider spacing (30 x 40 cm) compared to tsunga allows larger leaf "
                             "production and better air circulation for disease management.",
        ),
        GrowthStageRequirements(
            stage_name="Vegetative Growth",
            stage_code="VGRO",
            day_range=(36, 55),
            water_kc=0.85,
            water_mm_per_week=25.0,
            critical_nutrients=["N", "K", "S"],
            key_activities=[
                "Top-dress with AN at 3-4 weeks after transplant",
                "Weed control — hand hoe or mulch between rows",
                "Monitor for aphids and diamondback moth",
                "Ensure consistent soil moisture",
            ],
            risks=["Aphid infestation", "Diamondback moth larvae", "Downy mildew under cool, wet conditions"],
            scientific_notes="Rapid canopy expansion phase. Nitrogen demand peaks at 150-200 kg N/ha equivalent "
                             "for commercial leaf production. Potassium improves leaf texture and shelf life. "
                             "Sulphur nutrition enhances the mild Brassica flavour preferred in rape leaves.",
        ),
        GrowthStageRequirements(
            stage_name="First Harvest",
            stage_code="HRV1",
            day_range=(56, 70),
            water_kc=0.9,
            water_mm_per_week=25.0,
            critical_nutrients=["N", "K"],
            key_activities=[
                "Harvest outer/lower leaves when 25-30 cm long",
                "Leave 5-6 inner leaves for continued growth",
                "Top-dress with AN or LAN after harvest",
                "Grade and bunch for market (10-12 leaves per bunch)",
            ],
            risks=["Over-harvesting reducing regrowth capacity", "Leaf damage from pests reducing marketability"],
            scientific_notes="First harvest at 40-60 days from transplanting. Rape produces broad, smooth leaves "
                             "preferred in Zimbabwean cuisine. Leaf removal stimulates axillary growth and "
                             "continued leaf production. Maintain LAI > 2 for adequate photosynthesis.",
        ),
        GrowthStageRequirements(
            stage_name="Multiple Harvest / Ratoon",
            stage_code="RATN",
            day_range=(71, 180),
            water_kc=0.85,
            water_mm_per_week=25.0,
            critical_nutrients=["N", "K", "Ca"],
            key_activities=[
                "Harvest every 2-3 weeks (outer leaves only)",
                "Top-dress with AN after every second harvest",
                "Monitor pest and disease pressure (increases with crop age)",
                "Replace plants after 4-6 harvests or when bolting",
            ],
            risks=["Nutrient exhaustion from repeated harvests", "Disease accumulation",
                   "Bolting under heat stress or long days"],
            scientific_notes="Rape supports 4-6 harvests over 3-4 months when well-managed. "
                             "Repeated nitrogen inputs are essential; each leaf harvest removes ~35 kg N/ha. "
                             "As plants age, susceptibility to black rot and aphids increases. "
                             "Bolting ends productive life — triggered by high temperature (>30°C) and day length.",
        ),
    ],

    # Fertilizer schedule
    fertilizer_schedule=FertilizerSchedule(
        basal={
            "product": "Compound C (6:15:12)",
            "rate": "400-500 kg/ha",
            "timing": "At transplanting, placed in planting holes or furrows",
            "notes": "Supplement with well-rotted manure at 20 t/ha for improved soil structure.",
        },
        top_dress_1={
            "product": "AN (34.5% N) or LAN (28% N)",
            "rate": "150-200 kg/ha AN",
            "timing": "3-4 weeks after transplanting",
            "notes": "Apply in band along rows and irrigate in",
        },
        top_dress_2={
            "product": "AN (34.5% N)",
            "rate": "100-150 kg/ha",
            "timing": "After first harvest and subsequent harvests",
            "notes": "Sustained N supply is critical for ratoon leaf quality and yield",
        },
        foliar={
            "product": "Calcium nitrate",
            "rate": "5 g/L",
            "timing": "Fortnightly during active harvest period",
            "notes": "Calcium prevents tip burn and improves leaf firmness and shelf life",
        },
        liming={
            "product": "Dolomitic lime",
            "rate": "2-4 t/ha when pH < 5.5; raise to pH 6.5-7.0 to suppress clubroot",
            "timing": "4-6 weeks before planting, incorporate into soil",
            "notes": "Clubroot risk increases dramatically below pH 6.5. "
                     "Dolomitic lime also supplies magnesium.",
        },
        notes="Rape is a heavy feeder. High nitrogen input drives leaf production but excess N increases "
              "aphid susceptibility and reduces leaf storage quality. Balance with K.",
    ),

    # Diseases and pests
    diseases=RAPE_DISEASES,
    pests=RAPE_PESTS,

    # Planting windows
    planting_windows=[
        PlantingWindow(
            region="I",
            optimal_start="August 1",
            optimal_end="April 30",
            acceptable_start="January 1",
            acceptable_end="December 31",
            notes="Year-round production with irrigation. Best quality in cool months.",
        ),
        PlantingWindow(
            region="IIa",
            optimal_start="August 1",
            optimal_end="April 30",
            acceptable_start="January 1",
            acceptable_end="December 31",
            notes="Year-round with irrigation. Rainfed October-March. "
                  "Major production area for Harare/Chitungwiza markets.",
        ),
        PlantingWindow(
            region="IIb",
            optimal_start="September 1",
            optimal_end="April 30",
            acceptable_start="January 1",
            acceptable_end="December 31",
            notes="Year-round with irrigation. Best quality March-September.",
        ),
        PlantingWindow(
            region="III",
            optimal_start="October 1",
            optimal_end="March 31",
            acceptable_start="September 1",
            acceptable_end="May 31",
            notes="Rainfed October-March. Year-round with irrigation. "
                  "Heat management needed October-November.",
        ),
        PlantingWindow(
            region="IV",
            optimal_start="October 15",
            optimal_end="February 28",
            acceptable_start="September 1",
            acceptable_end="April 30",
            notes="Rainfed season only without irrigation. Supplement irrigation extends to cool season.",
        ),
    ],

    # Post-harvest
    harvest_moisture="Leaves harvested fresh at full turgidity, preferably early morning",
    storage_conditions="Fresh leaves: store at 2-5°C and >95% RH for up to 5-7 days. "
                       "Bunch loosely to allow air circulation. Avoid compression damage.",
    post_harvest_notes="Harvest mature outer leaves at 25-30 cm. Bundle 10-12 leaves per bunch. "
                       "Pre-cool within 2 hours of harvest for maximum shelf life. "
                       "Rape has slightly better post-harvest life than covo due to thicker leaf tissue. "
                       "Avoid harvesting wet leaves — increases rot during transit.",

    # Zimbabwe natural regions
    natural_region_suitability={
        "I": "Excellent — ideal climate for year-round production.",
        "IIa": "Excellent — major commercial and smallholder production area.",
        "IIb": "Good — year-round with irrigation supplement.",
        "III": "Good — summer rainfed, year-round with irrigation.",
        "IV": "Moderate — irrigation required; heat stress limits quality October-November.",
        "V": "Marginal — only under full irrigation with shade management.",
    },
)

ALIASES = ["rape kale"]
