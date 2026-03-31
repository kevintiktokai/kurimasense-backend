"""Strawberries (Fragaria x ananassa) — high-value fruit crop, transplanted runners, needs cool conditions."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List


STRAWBERRY_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Botrytis Fruit Rot (Grey Mould)",
        pathogen="Botrytis cinerea",
        pathogen_type="fungal",
        symptoms=[
            "Soft, light brown rot on ripening fruit",
            "Dense grey fuzzy sporulation covering fruit surface",
            "Infected flowers turn brown and die (blossom blight)",
            "Fruit becomes watery and collapses, often remaining attached to plant",
        ],
        identification_markers=[
            "Grey-brown fluffy mould on fruit surface (diagnostic)",
            "Infection often starts at calyx or where fruit contacts soil/mulch",
            "Affected fruit feels soft and spongy before sporulation appears",
            "Under UV light, infected tissue fluoresces — useful for latent detection",
        ],
        favourable_conditions={
            "humidity_min": 85, "temp_min_c": 15, "temp_max_c": 25,
            "leaf_wetness_hours": 6,
            "note": "Cool, wet conditions during flowering and fruiting. Dense canopy, "
                    "fruit touching soil, and overhead irrigation greatly increase risk."
        },
        susceptible_stages=["flowering", "green_fruit", "fruit_ripening"],
        resistant_varieties=["Festival (moderate tolerance)"],
        susceptible_varieties=["Chandler (highly susceptible)"],
        chemical_control=[
            {"name": "Fenhexamid 500 SC (Teldor)", "rate": "1.0-1.5 L/ha",
             "phi_days": "1", "notes": "Hydroxyanilide; Botrytis-specific. Very short PHI for export."},
            {"name": "Iprodione 500 SC (Rovral)", "rate": "1.0-1.5 L/ha",
             "phi_days": "3", "notes": "Dicarboximide; broad-spectrum. Max 3 per season."},
            {"name": "Cyprodinil + Fludioxonil (Switch 62.5 WG)", "rate": "0.8-1.0 kg/ha",
             "phi_days": "3", "notes": "Two modes of action; excellent resistance management."},
        ],
        biological_control=[
            "Bacillus amyloliquefaciens (Amylo-X) applied during flowering",
            "Trichoderma harzianum (Eco-T) for canopy and soil application",
            "Gliocladium roseum competitive colonisation of flower tissue",
        ],
        cultural_control=[
            "Use plastic mulch or straw to prevent fruit-soil contact",
            "Drip irrigation only — avoid overhead watering during flowering/fruiting",
            "Remove infected fruit immediately (sanitation is critical)",
            "Plant at correct spacing (30-40 cm in-row) for air circulation",
            "Harvest in dry conditions; avoid handling wet fruit",
        ],
        economic_threshold="2% fruit infected at harvest; any blossom blight symptoms",
        severity_scale={
            "mild": "<5% fruit affected, scattered infections",
            "moderate": "5-15% fruit affected, significant quality loss",
            "severe": ">15% fruit affected — major economic impact, crop may be unmarketable",
        },
    ),
    DiseaseProfile(
        name="Powdery Mildew",
        pathogen="Podosphaera aphanis (syn. Sphaerotheca macularis f.sp. fragariae)",
        pathogen_type="fungal",
        symptoms=[
            "White powdery patches on leaf undersides, curling leaf edges upward",
            "Purple-red blotches on upper leaf surface corresponding to colonies below",
            "Infected fruit fails to colour properly, remains hard and pale",
            "Flower infection causes distorted, non-viable fruit",
        ],
        identification_markers=[
            "White mycelium primarily on UNDERSIDE of leaves (unlike most powdery mildews)",
            "Leaf edges curl upward exposing undersurface colonies",
            "Infected fruit has dry, seedy appearance with white powdery coating",
            "Purple-red upper surface discolouration is distinctive",
        ],
        favourable_conditions={
            "humidity_min": 60, "temp_min_c": 15, "temp_max_c": 27,
            "note": "Moderate temperatures with fluctuating humidity (dry days, humid nights). "
                    "Unlike most fungi, does NOT need free water for infection."
        },
        susceptible_stages=["vegetative", "flowering", "fruit_development"],
        resistant_varieties=["Festival (moderate resistance)"],
        susceptible_varieties=["Chandler (susceptible)"],
        chemical_control=[
            {"name": "Myclobutanil 200 EW", "rate": "0.3-0.4 L/ha",
             "phi_days": "7", "notes": "Systemic triazole; curative and protectant activity."},
            {"name": "Azoxystrobin 250 SC", "rate": "0.5 L/ha",
             "phi_days": "3", "notes": "Strobilurin; apply preventively. Max 3 per season."},
            {"name": "Sulphur 80 WP", "rate": "3.0-5.0 kg/ha",
             "phi_days": "1", "notes": "Protectant; do not apply above 30°C or with oil sprays."},
        ],
        biological_control=[
            "Potassium bicarbonate (Kaligreen) disrupts fungal cell membrane",
            "Bacillus subtilis (Serenade) preventive foliar sprays",
            "Ampelomyces quisqualis (hyperparasite of powdery mildew)",
        ],
        cultural_control=[
            "Select tolerant varieties for high-risk areas",
            "Maintain open plant architecture to improve air circulation",
            "Remove older, infected leaves from base of plant",
            "Avoid excessive nitrogen which promotes dense, susceptible foliage",
            "Overhead irrigation (brief) can wash off spores — but increases Botrytis risk",
        ],
        economic_threshold="5% of leaves infected or any fruit infection",
        severity_scale={
            "mild": "Scattered patches on lower leaves, <10% leaf area",
            "moderate": "10-30% leaf area, reaching flower trusses",
            "severe": ">30% leaf area, fruit infection — unmarketable crop",
        },
    ),
    DiseaseProfile(
        name="Verticillium Wilt",
        pathogen="Verticillium dahliae",
        pathogen_type="fungal",
        symptoms=[
            "Outer leaves wilt and turn brown while inner leaves remain green initially",
            "Stunted growth with reduced runner production",
            "Brownish discolouration of vascular tissue in crown (diagnostic — cut crown lengthwise)",
            "Whole plant collapse in severe cases, especially under heat stress",
        ],
        identification_markers=[
            "Asymmetric wilting — one side of plant may wilt before the other",
            "Brown vascular streaking visible in longitudinal crown section",
            "Chronic infection causes flattened, stunted plants with small leaves",
            "Distinguish from Phytophthora crown rot (which is water-soaked, not vascular)",
        ],
        favourable_conditions={
            "soil_temp_min_c": 18, "soil_temp_max_c": 25,
            "note": "Soilborne; persists as microsclerotia for 10+ years. Worse in cooler soils "
                    "and following susceptible crops (tomato, potato, eggplant, pepper)."
        },
        susceptible_stages=["all growth stages — especially transplant establishment"],
        resistant_varieties=["Festival (moderate tolerance)"],
        susceptible_varieties=["Chandler (moderately susceptible)"],
        chemical_control=[
            {"name": "Soil fumigation with metam sodium", "rate": "500-700 L/ha",
             "phi_days": "30", "notes": "Pre-plant only. Apply 4-6 weeks before planting. Seal with plastic."},
        ],
        biological_control=[
            "Trichoderma harzianum (Eco-T) root dip at transplanting",
            "Mycorrhizal inoculant (Glomus intraradices) improves plant resilience",
            "Brassica biofumigation — incorporate mustard green manure before planting",
        ],
        cultural_control=[
            "Use certified disease-free transplants from reputable nurseries",
            "Avoid fields previously cropped with Solanaceae (tomato, potato, pepper)",
            "Solarise soil before planting (clear plastic for 6-8 weeks in summer)",
            "Rotate with non-host crops: cereals, grasses for 4-5 years",
            "Remove and destroy infected plants promptly — do not compost",
        ],
        economic_threshold="5% plant mortality; vascular browning in sampled crowns",
        severity_scale={
            "mild": "Scattered wilting plants, <5% incidence",
            "moderate": "5-20% plant mortality, yield declining",
            "severe": ">20% plant mortality — consider field abandonment and soil treatment",
        },
    ),
]


STRAWBERRY_PESTS: List[PestProfile] = [
    PestProfile(
        name="Two-Spotted Spider Mite (Red Spider Mite)",
        scientific_name="Tetranychus urticae",
        pest_type="mite",
        identification=[
            "Tiny (0.5 mm) yellow-green mites with two dark spots on abdomen",
            "Fine webbing on leaf undersides in heavy infestations",
            "Eggs are spherical, translucent, on leaf undersides",
            "Use 10-20x hand lens for identification — barely visible to naked eye",
        ],
        damage_symptoms=[
            "Fine yellow stippling on upper leaf surface (feeding damage)",
            "Bronze discolouration of leaves in severe infestations",
            "Leaf desiccation and drop — reduced photosynthesis and yield",
            "Webbing covers fruit in extreme cases, rendering it unmarketable",
        ],
        life_cycle_notes=(
            "Egg to adult in 7-14 days depending on temperature. Populations can double "
            "every 3-5 days under hot, dry conditions. Females lay 100-200 eggs. Broad-spectrum "
            "insecticide use eliminates natural enemies and causes mite outbreaks (resurgence). "
            "Diapause (overwintering) females are orange-red, not green."
        ),
        favourable_conditions={
            "temp_min_c": 25, "temp_max_c": 35,
            "humidity_max": 50,
            "note": "Hot, dry, dusty conditions. Populations explode when natural enemies are killed "
                    "by insecticides. Water-stressed plants are more susceptible."
        },
        susceptible_stages=["vegetative", "flowering", "fruiting"],
        economic_threshold="5 mites per leaflet or >30% leaves with stippling",
        chemical_control=[
            {"name": "Abamectin 18 EC", "rate": "300-500 mL/ha",
             "phi_days": "3", "notes": "Translaminar; targets mites on leaf undersides. Rotate MOA."},
            {"name": "Bifenazate 240 SC (Acramite)", "rate": "0.6-1.0 L/ha",
             "phi_days": "3", "notes": "Selective miticide; safe to predatory mites."},
            {"name": "Spiromesifen 240 SC (Oberon)", "rate": "0.4-0.5 L/ha",
             "phi_days": "7", "notes": "Lipid synthesis inhibitor; kills eggs and juveniles."},
        ],
        biological_control=[
            "Phytoseiulus persimilis — specialist predatory mite, highly effective",
            "Neoseiulus californicus — more heat-tolerant predatory mite alternative",
            "Beauveria bassiana (under humid conditions)",
            "Avoid pyrethroids and organophosphates that kill predatory mites",
        ],
        cultural_control=[
            "Maintain adequate irrigation to avoid water stress",
            "Control dust on roads near fields (reduces mite dispersal and stress)",
            "Remove heavily infested leaves — bag and destroy, do not leave in field",
            "Overhead irrigation (brief) can dislodge mites and raise humidity",
            "Monitor with hand lens weekly — undersides of middle-canopy leaves",
        ],
        scouting_protocol=(
            "Inspect 30 leaflets from middle-aged leaves across the field using 10-20x hand lens. "
            "Count motile mites per leaflet. Record separately: mites, predatory mites, and eggs. "
            "If predatory mite:pest ratio >1:10, biological control may be sufficient. "
            "Scout twice weekly in hot weather."
        ),
    ),
    PestProfile(
        name="Aphids (Green Peach Aphid / Strawberry Aphid)",
        scientific_name="Myzus persicae / Chaetosiphon fragaefolii",
        pest_type="insect",
        identification=[
            "M. persicae: 1.5-2.5 mm, green to pink, on leaves and flowers",
            "C. fragaefolii: smaller, pale green-yellow, specific to strawberry",
            "Both form colonies on leaf undersides, growing tips, and flower trusses",
            "C. fragaefolii has characteristic capitate (club-shaped) body hairs",
        ],
        damage_symptoms=[
            "Curled and distorted leaves, especially young growth",
            "Honeydew deposits leading to sooty mould on fruit",
            "Reduced plant vigour and flower production",
            "C. fragaefolii vectors Strawberry Mild Yellow Edge Virus (SMYEV) and other viruses",
        ],
        life_cycle_notes=(
            "Parthenogenetic reproduction; one generation every 7-12 days. Populations build "
            "rapidly in mild, dry conditions. C. fragaefolii is the primary vector of several "
            "damaging strawberry viruses — even low populations can cause significant virus spread."
        ),
        favourable_conditions={
            "temp_min_c": 12, "temp_max_c": 25,
            "note": "Mild temperatures, sheltered conditions. Populations decline above 30°C "
                    "and during heavy rain. Tunnels and protective structures increase risk."
        },
        susceptible_stages=["vegetative", "flowering", "fruiting"],
        economic_threshold="10 aphids per leaf (virus-free area: 1 aphid per leaf — virus vector threshold)",
        chemical_control=[
            {"name": "Pirimicarb 50 WG (Pirimor)", "rate": "250-500 g/ha",
             "phi_days": "3", "notes": "Selective aphicide; preserves beneficial insects."},
            {"name": "Pymetrozine 250 WG (Chess)", "rate": "400 g/ha",
             "phi_days": "7", "notes": "Anti-feedant; stops aphid feeding but slow kill."},
        ],
        biological_control=[
            "Aphidius colemani parasitoid wasp (for M. persicae)",
            "Ladybirds (Hippodamia, Coccinella spp.) — adults and larvae",
            "Lacewing larvae (Chrysoperla carnea)",
            "Aphidoletes aphidimyza (predatory midge)",
        ],
        cultural_control=[
            "Use virus-tested planting material from certified nurseries",
            "Rogue (remove) virus-infected plants immediately",
            "Reflective mulch (silver-coloured plastic) deters winged aphid landing",
            "Monitor weekly with yellow sticky traps and direct plant inspection",
            "Avoid excessive nitrogen fertilisation",
        ],
        scouting_protocol=(
            "Inspect 25 plants across the field, examining youngest fully expanded leaf (underside) "
            "and flower trusses. Count aphid colonies (>5 aphids = colony). In virus-sensitive areas, "
            "any aphid presence triggers control action. Use yellow sticky traps for winged adults."
        ),
    ),
    PestProfile(
        name="Slugs and Snails",
        scientific_name="Deroceras reticulatum / Cornu aspersum",
        pest_type="mollusc",
        identification=[
            "Slugs: soft-bodied, grey-brown, 3-5 cm, leave slime trail",
            "Snails: similar but with coiled shell",
            "Active at night and in wet, overcast conditions",
            "Slime trails visible on leaves, fruit, and soil surface in morning",
        ],
        damage_symptoms=[
            "Irregular holes chewed in ripening fruit",
            "Slime contamination on fruit renders it unmarketable",
            "Feeding damage on leaves (irregular, ragged holes)",
            "Damage concentrated where fruit contacts mulch or soil",
        ],
        life_cycle_notes=(
            "Slugs lay 300-500 eggs in soil crevices; hatch in 2-4 weeks. "
            "Generation time 3-6 months. Most active at night when humidity is high. "
            "Populations highest in wet seasons and on heavy, poorly drained soils."
        ),
        favourable_conditions={
            "humidity_min": 80,
            "note": "Wet, mild conditions. Worst in rainy season, on heavy clay soils, "
                    "under organic mulches, and with dense canopy providing shelter."
        },
        susceptible_stages=["fruiting"],
        economic_threshold="5% fruit with slug/snail damage or slime trails",
        chemical_control=[
            {"name": "Iron phosphate pellets (Sluggo)", "rate": "25-50 kg/ha",
             "phi_days": "0", "notes": "Organic-approved; safe for wildlife. Scatter around plants."},
            {"name": "Metaldehyde 5% pellets", "rate": "5-7 kg/ha",
             "phi_days": "14", "notes": "Apply between rows. Toxic to pets and wildlife — use cautiously."},
        ],
        biological_control=[
            "Nematode Phasmarhabditis hermaphrodita (Nemaslug) — soil drench",
            "Ground beetles (Carabidae) are natural predators",
            "Encourage hedgehogs and frogs in orchard margins",
        ],
        cultural_control=[
            "Use plastic mulch rather than straw (less slug habitat)",
            "Raise fruit off ground with mulch ridge or tabletop growing systems",
            "Remove crop debris that provides daytime shelter",
            "Beer traps for monitoring and localised control",
            "Irrigate in the morning so foliage and soil surface dry by evening",
        ],
        scouting_protocol=(
            "Check field at dawn or use beer/bran traps for monitoring. Count traps twice weekly. "
            "Inspect 25 fruit per block for slime or feeding damage. Focus on field edges and "
            "areas near drainage channels or dense vegetation."
        ),
    ),
]


STRAWBERRY_GROWTH_STAGES: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Transplant Establishment",
        stage_code="TE",
        day_range=(0, 14),
        water_kc=0.4,
        water_mm_per_week=20,
        critical_nutrients=["Phosphorus", "Potassium"],
        key_activities=[
            "Transplant bare-root runners or plug plants into prepared beds",
            "Plant crown at soil surface level — not buried, not exposed",
            "Apply mulch (black plastic or straw) immediately after planting",
            "Irrigate immediately and daily for first 7-10 days",
            "Remove any flowers for first 4-6 weeks to promote vegetative establishment",
        ],
        risks=["Transplant shock in hot conditions", "Crown rot from deep planting",
               "Verticillium wilt from contaminated soil"],
        scientific_notes=(
            "Strawberry runners are clonally propagated; crown meristem integrity is critical. "
            "Planting depth must position the crown base at soil level — burial causes crown rot, "
            "exposure desiccates roots. Removing early flowers redirects assimilates to root and "
            "crown development, increasing subsequent yield by 20-40%. Roots are adventitious "
            "and shallow (80% in top 15 cm)."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Vegetative Growth & Crown Development",
        stage_code="VG",
        day_range=(15, 35),
        water_kc=0.6,
        water_mm_per_week=25,
        critical_nutrients=["Nitrogen", "Phosphorus", "Potassium"],
        key_activities=[
            "Begin fertigation programme with balanced NPK",
            "Remove runners to channel energy into crown development",
            "Scout for spider mites and aphids — early detection critical",
            "Maintain weed-free conditions around plants",
        ],
        risks=["Spider mite build-up in dry conditions", "Excessive runner production diverting energy",
               "Weed competition in establishment phase"],
        scientific_notes=(
            "Crown diameter is the strongest predictor of yield potential. Each crown branch "
            "produces a flower truss; multiple crowns per plant increase yield. Runner removal "
            "and adequate nutrition promote crown branching. Photoperiod sensitivity varies: "
            "June-bearing types initiate flowers under short days (<14 hours), while day-neutral "
            "types flower regardless of photoperiod."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Flower Initiation & Development",
        stage_code="FI",
        day_range=(36, 50),
        water_kc=0.7,
        water_mm_per_week=30,
        critical_nutrients=["Phosphorus", "Boron", "Calcium", "Potassium"],
        key_activities=[
            "Maintain consistent irrigation — stress reduces flower number",
            "Apply foliar boron (Solubor 1 kg/ha) for flower quality",
            "Begin Botrytis fungicide programme at first open flower",
            "Monitor for thrips in flowers",
        ],
        risks=["Frost damage to open flowers", "Botrytis blossom blight",
               "Poor pollination in cold or wet weather"],
        scientific_notes=(
            "Strawberry flowers are perfect (hermaphroditic) and largely self-fertile. "
            "However, insect pollination (bees) improves fruit shape and size by ensuring "
            "all achenes (true fruits) on the receptacle are fertilised. Unfertilised achenes "
            "result in misshapen fruit (buttoning). Boron is essential for pollen tube growth."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Fruit Development & Green Fruit",
        stage_code="FD",
        day_range=(51, 65),
        water_kc=0.85,
        water_mm_per_week=35,
        critical_nutrients=["Potassium", "Calcium", "Nitrogen"],
        key_activities=[
            "Maintain consistent irrigation for fruit sizing",
            "Apply calcium foliar sprays for fruit firmness",
            "Continue Botrytis/powdery mildew fungicide rotation",
            "Ensure fruit is lifted off ground by mulch or supports",
        ],
        risks=["Water stress causing small fruit", "Calcium deficiency causing soft fruit",
               "Slug/snail damage increasing as fruit develops"],
        scientific_notes=(
            "The strawberry 'fruit' is an accessory fruit — the fleshy part is the enlarged "
            "receptacle; the true fruits are the achenes (seeds) on the surface. Cell division "
            "in the receptacle occurs during the first 10-14 days after pollination; cell "
            "enlargement continues until harvest. Calcium is immobile in phloem — foliar "
            "applications directly to developing fruit are more effective than soil-applied Ca."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Fruit Ripening & Harvest",
        stage_code="HV",
        day_range=(66, 90),
        water_kc=0.9,
        water_mm_per_week=35,
        critical_nutrients=["Potassium"],
        key_activities=[
            "Harvest every 2-3 days when 75-100% of fruit surface is red",
            "Pick in cool morning hours; place in shade immediately",
            "Pre-cool to 2-4°C within 1-2 hours of harvest",
            "Grade by size, colour, firmness — remove blemished fruit",
            "Continue slug/snail control — iron phosphate bait around plants",
        ],
        risks=["Rain damage (cracking, Botrytis)", "Fruit fly (SWD) infestation",
               "Overripe fruit attracts pests and spreads disease"],
        scientific_notes=(
            "Strawberries are non-climacteric — sugar content does not increase after harvest. "
            "Harvest at 75-100% colour for maximum flavour (Brix 7-12). Anthocyanin (pelargonidin-"
            "3-glucoside) accumulates during ripening, driven by PAL enzyme activity. Respiration "
            "rate at 20°C is 3-4x higher than at 0°C, hence rapid cooling is essential. "
            "Shelf life is only 3-5 days at 4°C without modified atmosphere."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Post-Harvest Recovery & Runner Production",
        stage_code="PR",
        day_range=(91, 150),
        water_kc=0.5,
        water_mm_per_week=20,
        critical_nutrients=["Nitrogen", "Phosphorus"],
        key_activities=[
            "Reduce irrigation after final harvest",
            "Allow runner production for propagation if needed",
            "Remove old, diseased leaves (renovation)",
            "Apply post-harvest fertiliser for crown development",
            "Assess plant health — plan replanting if Verticillium or virus issues",
        ],
        risks=["Virus spread via aphids during runner growth", "Crown rot in waterlogged conditions"],
        scientific_notes=(
            "Runners are stolons produced from axillary buds under long-day conditions. "
            "Each runner produces daughter plants at nodes. In production systems, runners "
            "are typically removed to maintain plant vigour — only in propagation beds are "
            "they encouraged. Strawberry plantings are typically productive for 2-3 seasons "
            "before replanting due to yield decline from disease accumulation."
        ),
    ),
]


STRAWBERRY_FERTILIZER = FertilizerSchedule(
    basal={
        "product": "Compound D (7:14:7) or Compound S (7:21:7) + well-composted manure",
        "rate": "300-500 kg/ha Compound D + 20-30 t/ha compost (incorporate before bed forming)",
        "timing": "2-4 weeks before transplanting, incorporated into beds",
        "nutrients": "21-35 kg N, 42-105 kg P₂O₅, 21-35 kg K₂O per ha",
        "note": "Phosphorus and organic matter critical for root establishment. Avoid fresh manure.",
    },
    top_dress_1={
        "product": "Ammonium Nitrate (AN 34.5%) or Calcium Ammonium Nitrate (CAN)",
        "rate": "100-150 kg/ha AN, split into 2-3 applications via fertigation",
        "timing": "From 3 weeks after transplanting through to flowering",
        "nutrients": "35-50 kg N per ha",
        "note": "Apply via drip fertigation for efficiency. Avoid broadcast near crowns.",
    },
    top_dress_2={
        "product": "Potassium Sulphate (SOP) or Potassium Nitrate",
        "rate": "100-150 kg/ha SOP via fertigation during fruit development",
        "timing": "From green fruit stage through harvest",
        "nutrients": "50-75 kg K₂O per ha",
        "note": "Potassium critical for fruit colour, flavour, firmness, and shelf life.",
    },
    foliar={
        "product": "Calcium Chloride + Solubor",
        "rate": "3-5 kg/ha CaCl₂ + 1 kg/ha Solubor in 500 L water",
        "timing": "At flowering and every 10-14 days through fruit development",
        "note": "Calcium for fruit firmness; boron for pollination. Apply in cool conditions.",
    },
    liming={
        "product": "Agricultural lime (calcitic or dolomitic)",
        "rate": "1-3 t/ha based on soil analysis",
        "timing": "3-6 months before planting, incorporated",
        "note": "Target pH 5.8-6.5. Dolomitic lime preferred if Mg is low.",
    },
    notes=(
        "Strawberries respond well to fertigation through drip systems. Total season N demand "
        "is 80-120 kg/ha but must be split into frequent small doses to avoid salt damage to "
        "shallow roots. Excessive N causes soft, poorly coloured fruit with reduced shelf life. "
        "Potassium:Nitrogen ratio should increase during fruiting (shift from 1:1 to 2:1 K:N)."
    ),
)


STRAWBERRY_PLANTING_WINDOWS: List[PlantingWindow] = [
    PlantingWindow(
        region="Highveld (NR IIa/IIb) — Harare, Marondera, Norton",
        optimal_start="February 15",
        optimal_end="April 15",
        acceptable_start="February 1",
        acceptable_end="May 15",
        notes=(
            "Transplant at end of rains/early cool season for establishment before winter. "
            "First fruit from May-June onwards. Peak production July-September. "
            "Irrigation essential from April onwards."
        ),
    ),
    PlantingWindow(
        region="Eastern Highlands (NR I) — Nyanga, Chimanimani, Juliasdale",
        optimal_start="February 1",
        optimal_end="March 31",
        acceptable_start="January 15",
        acceptable_end="April 30",
        notes=(
            "Best quality fruit from high altitude plantings. Cool conditions extend "
            "harvest season. Day-neutral varieties can produce over extended period. "
            "Watch for excessive rain increasing Botrytis risk."
        ),
    ),
    PlantingWindow(
        region="Middleveld (NR III) — Mutare, Kadoma, Gweru",
        optimal_start="March 1",
        optimal_end="April 15",
        acceptable_start="February 15",
        acceptable_end="May 1",
        notes=(
            "Must plant to avoid hot summer fruiting. Production limited to cool dry season. "
            "Consider shade netting to reduce heat stress during establishment."
        ),
    ),
]


PROFILE = CropProfile(
    crop_name="Strawberries",
    scientific_name="Fragaria × ananassa",
    family="Rosaceae",
    optimal_ph=(5.8, 6.5),
    critical_ph_low=5.0,
    optimal_soil_types=["fersiallitic", "siallitic"],
    avoid_soil_types=["vertisol", "lithosol"],
    optimal_temp=(15.0, 25.0),
    critical_temp_low=-2.0,
    critical_temp_high=30.0,
    base_temp_gdd=7.0,
    total_water_mm=500.0,
    growth_stages=STRAWBERRY_GROWTH_STAGES,
    fertilizer_schedule=STRAWBERRY_FERTILIZER,
    diseases=STRAWBERRY_DISEASES,
    pests=STRAWBERRY_PESTS,
    planting_windows=STRAWBERRY_PLANTING_WINDOWS,
    harvest_moisture="Fruit harvested at 88-92% moisture; target Brix 7-12",
    storage_conditions=(
        "Pre-cool to 1-2°C within 1 hour of harvest using forced air cooling. "
        "Store at 0-2°C, 90-95% RH. Shelf life 3-5 days (7-10 days with MAP). "
        "Modified atmosphere: 5-10% CO₂, 5-10% O₂ for airfreight export."
    ),
    post_harvest_notes=(
        "Strawberries are extremely perishable. Maintain unbroken cold chain. "
        "Grade by size (>25 mm Class 1), colour uniformity, calyx freshness, and firmness. "
        "Pack in punnets (250 g or 500 g) with pad liners. Handle minimally — every touch "
        "causes bruising. Zimbabwe exports to regional (South Africa) and EU markets via airfreight."
    ),
    natural_region_suitability={
        "I": "Excellent — cool climate, ideal for premium quality fruit year-round",
        "IIa": "Good — cool season production (May-October) under irrigation",
        "IIb": "Good — as IIa, with slightly warmer conditions",
        "III": "Marginal — limited to cool dry season, heat stress limits production",
        "IV": "Not suitable — too hot for quality strawberry production",
        "V": "Not suitable — extreme heat, no viable production",
    },
)

ALIASES = ["strawberry"]
