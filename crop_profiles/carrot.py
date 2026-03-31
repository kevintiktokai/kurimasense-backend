"""Carrot (Daucus carota) — Cool-season root vegetable, important for smallholder nutrition and peri-urban markets in Zimbabwe."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List


CARROT_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Alternaria Leaf Blight",
        pathogen="Alternaria dauci",
        pathogen_type="fungal",
        symptoms=[
            "Dark brown to black lesions on leaf margins and tips",
            "V-shaped lesions that coalesce causing entire leaflet death",
            "Premature defoliation reducing root size and sugar content",
            "Petiole lesions causing leaf breakage during mechanical harvest",
        ],
        identification_markers=[
            "Lesions start at leaf margins (oldest leaves first)",
            "Distinct dark brown colour with chlorotic halo",
            "Conidia visible under hand lens on lesion surface in humid mornings",
            "Differs from Cercospora by larger, darker, margin-starting lesions",
        ],
        favourable_conditions={
            "humidity_min": 90, "temp_min_c": 20, "temp_max_c": 30,
            "leaf_wetness_hours": 8,
            "note": "Warm days with heavy dew or overhead irrigation. Seed-borne "
                    "inoculum initiates epidemics. Severity increases with crop age "
                    "as older leaves are more susceptible."
        },
        susceptible_stages=["Vegetative Growth", "Root Bulking", "Maturation"],
        resistant_varieties=["Kuroda (moderate tolerance)"],
        susceptible_varieties=["Nantes types", "Chantenay types"],
        chemical_control=[
            {"name": "Iprodione 50 WP", "rate": "1.5 kg/ha",
             "phi_days": "14", "notes": "Apply at first symptoms, 10-14 day intervals"},
            {"name": "Azoxystrobin 250 SC", "rate": "0.5 L/ha",
             "phi_days": "7", "notes": "Alternate with contact fungicide to manage resistance"},
            {"name": "Chlorothalonil 720 SC", "rate": "2.0 L/ha",
             "phi_days": "7", "notes": "Protectant; apply before infection periods"},
        ],
        biological_control=[
            "Trichoderma harzianum foliar spray reduces spore germination",
            "Bacillus subtilis-based products as preventive foliar applications",
        ],
        cultural_control=[
            "Use hot-water treated or thiram-treated seed to eliminate seed-borne inoculum",
            "2-3 year rotation away from all Apiaceae (carrot, parsley, celery)",
            "Avoid overhead irrigation; use drip where possible",
            "Remove crop residues promptly after harvest",
            "Plant during cooler months to reduce disease pressure",
        ],
        economic_threshold="First lesions visible on lower canopy; spray before spreading to upper leaves",
        severity_scale={
            "mild": "< 10% leaf area affected, confined to oldest leaves",
            "moderate": "10-30% canopy affected, upper leaves showing symptoms",
            "severe": "> 30% canopy destroyed, roots undersized, harvest quality compromised",
        },
    ),
    DiseaseProfile(
        name="Cavity Spot",
        pathogen="Pythium violae, Pythium sulcatum",
        pathogen_type="oomycete",
        symptoms=[
            "Small elliptical sunken lesions on root surface",
            "Lesions are dry, grey-brown, 1-10mm long",
            "Horizontal orientation across root surface",
            "No soft rot — lesions remain firm and dry",
        ],
        identification_markers=[
            "Elliptical horizontal cavities on root surface (diagnostic)",
            "Lesions often concentrated in lower third of root",
            "Roots otherwise appear healthy internally",
            "Distinct from forking (physical damage) or soft rots (bacterial)",
        ],
        favourable_conditions={
            "soil_moisture": "waterlogged or compacted soils",
            "temp_min_c": 15, "temp_max_c": 20,
            "note": "Cool, wet soils favour Pythium. Compacted soils with poor "
                    "drainage are highest risk. Worse in soils with low calcium."
        },
        susceptible_stages=["Root Bulking", "Maturation"],
        resistant_varieties=[],
        susceptible_varieties=["Most Nantes types"],
        chemical_control=[
            {"name": "Metalaxyl-M (Ridomil Gold) 480 SL", "rate": "2.5 L/ha soil drench",
             "phi_days": "21", "notes": "Apply at sowing in furrow; most effective pre-emptively"},
        ],
        biological_control=[
            "Trichoderma-enriched compost reduces Pythium populations",
            "Mycorrhizal inoculants improve root resistance to oomycete pathogens",
        ],
        cultural_control=[
            "Improve soil drainage — raised beds essential in heavy soils",
            "Avoid compaction; minimum tillage after bed preparation",
            "Maintain soil calcium with gypsum applications (1-2 t/ha)",
            "Rotate with cereals for 3+ years; avoid continuous Apiaceae",
            "Harvest promptly at maturity — cavity spot worsens with time in soil",
        ],
        economic_threshold="Any cavities on roots reduce market grade; preventive management required for fresh market",
        severity_scale={
            "mild": "< 5% roots with 1-2 small cavities, still marketable for processing",
            "moderate": "5-15% roots affected, downgraded from premium fresh market",
            "severe": "> 15% roots with multiple cavities, rejected by supermarket buyers",
        },
    ),
    DiseaseProfile(
        name="Sclerotinia White Mould",
        pathogen="Sclerotinia sclerotiorum",
        pathogen_type="fungal",
        symptoms=[
            "White cottony mycelial growth on crown and shoulders of root",
            "Soft, watery rot of root crown progressing downward",
            "Large black sclerotia (2-10mm) forming in and on mycelium",
            "Foliage collapse starting from crown when infection is advanced",
        ],
        identification_markers=[
            "White fluffy mycelium with large black sclerotia (diagnostic)",
            "Infection starts at crown where foliage meets root",
            "Distinct from bacterial soft rot by presence of mycelium and sclerotia",
            "Apothecia (small mushroom-like structures) may appear on soil surface",
        ],
        favourable_conditions={
            "humidity_min": 85, "temp_min_c": 15, "temp_max_c": 25,
            "note": "Cool, moist conditions during canopy closure. Dense canopy "
                    "creates microclimate ideal for ascospore infection. "
                    "Sclerotia survive 5-8 years in soil."
        },
        susceptible_stages=["Root Bulking", "Maturation"],
        resistant_varieties=[],
        susceptible_varieties=["All varieties susceptible"],
        chemical_control=[
            {"name": "Iprodione 50 WP", "rate": "1.5 kg/ha",
             "phi_days": "14", "notes": "Apply to crown area at canopy closure"},
            {"name": "Boscalid + Pyraclostrobin", "rate": "0.8 kg/ha",
             "phi_days": "14", "notes": "Excellent against Sclerotinia; one application at canopy closure"},
        ],
        biological_control=[
            "Coniothyrium minitans (Contans WG) — parasitises sclerotia in soil, apply pre-planting",
            "Trichoderma harzianum as soil amendment at bed preparation",
        ],
        cultural_control=[
            "Wide row spacing and adequate thinning to promote air circulation",
            "3-4 year rotation with cereals (avoid beans, lettuce, sunflower — also hosts)",
            "Avoid excessive nitrogen which creates dense, lush canopies",
            "Drip irrigation instead of overhead sprinklers",
            "Deep ploughing to bury sclerotia below germination depth",
        ],
        economic_threshold="First appearance of white mycelium on crowns; spray immediately",
        severity_scale={
            "mild": "Isolated plants with crown rot, < 5% stand",
            "moderate": "Patches of 5-20% affected, spreading along rows",
            "severe": "> 20% crown rot, significant storage losses expected",
        },
    ),
]

CARROT_PESTS: List[PestProfile] = [
    PestProfile(
        name="Carrot Rust Fly",
        scientific_name="Psila rosae",
        pest_type="insect",
        identification=[
            "Adult: small (4-5mm) shiny black fly with orange head and legs",
            "Larva: creamy-white, legless, 8-10mm, blunt-ended",
            "Pupa: brown, found in soil near damaged roots",
        ],
        damage_symptoms=[
            "Rusty-brown tunnels on root surface ('rust' appearance)",
            "Mining damage through root cortex",
            "Secondary soft rot bacteria enter feeding tunnels",
            "Stunted, forked roots in severe infestations",
        ],
        life_cycle_notes=(
            "Two generations per year in Zimbabwe's cool-season production. "
            "Adults emerge in autumn and spring, lay eggs at crown base. "
            "Larvae feed on roots for 3-4 weeks before pupating in soil. "
            "Attracted by volatile compounds released when thinning or weeding."
        ),
        favourable_conditions={
            "temp_min_c": 15, "temp_max_c": 25,
            "note": "Cool, moist conditions during autumn and spring. "
                    "Sheltered, low-wind sites with previous carrot history. "
                    "Thinning operations release attractant volatiles."
        },
        susceptible_stages=["Vegetative Growth", "Root Bulking", "Maturation"],
        economic_threshold="2-3 adults per yellow sticky trap per week during susceptible period",
        chemical_control=[
            {"name": "Chlorpyrifos 480 EC (soil drench)", "rate": "3.0 L/ha",
             "phi_days": "21", "notes": "Apply at sowing; diminishing availability due to regulatory pressure"},
            {"name": "Cypermethrin 200 EC", "rate": "0.25 L/ha",
             "phi_days": "7", "notes": "Foliar spray targeting adults at egg-laying period"},
        ],
        biological_control=[
            "Entomopathogenic nematodes (Steinernema feltiae) applied to soil target larvae",
            "Companion planting with onion or garlic masks carrot volatiles",
        ],
        cultural_control=[
            "Delay sowing until after first generation adult flight (late April-May)",
            "Avoid thinning operations during adult flight periods",
            "Thin in evening when flies are less active; firm soil after thinning",
            "Use fleece/insect netting barriers (1.2m height) around beds",
            "Rotate away from carrot for 3+ years; maintain 1km isolation if possible",
            "Harvest early varieties before second generation larvae cause damage",
        ],
        scouting_protocol=(
            "Deploy yellow sticky traps at 30cm height at field edges from March onwards. "
            "Check twice weekly. Adults fly low and close to field margins. "
            "Pull and examine sample roots at 60, 80, and 100 days for larval tunnelling."
        ),
    ),
    PestProfile(
        name="Root-Knot Nematode",
        scientific_name="Meloidogyne incognita, M. javanica",
        pest_type="nematode",
        identification=[
            "Microscopic worm-like organisms; only damage symptoms visible in field",
            "Females: pear-shaped, sedentary within root galls",
            "Second-stage juveniles (J2): infective stage, motile in soil",
        ],
        damage_symptoms=[
            "Forking and branching of tap root (most visible symptom)",
            "Galls and knots on feeder roots",
            "Stunted, uneven growth in patches across field",
            "Hairy root appearance with excessive lateral root proliferation",
            "Roots unmarketable due to forking and rough surface",
        ],
        life_cycle_notes=(
            "Complete cycle in 25-30 days at optimal soil temperatures (25-30°C). "
            "J2 larvae enter root tips, establish feeding sites, and form giant cells. "
            "Each female produces 200-500 eggs in a gelatinous matrix. "
            "Multiple generations per crop cycle. Survives between crops in soil and on weeds."
        ),
        favourable_conditions={
            "temp_min_c": 20, "temp_max_c": 35,
            "soil_type": "sandy, light-textured soils",
            "note": "Sandy soils with low organic matter are highest risk. "
                    "Warm soil temperatures accelerate reproduction. "
                    "Continuous vegetable cropping builds populations rapidly."
        },
        susceptible_stages=["Emergence", "Vegetative Growth", "Root Bulking"],
        economic_threshold="200+ J2 per 200ml soil sample pre-planting; any forking in fresh market crop",
        chemical_control=[
            {"name": "Oxamyl 24 SL", "rate": "5.0 L/ha soil application",
             "phi_days": "30", "notes": "Apply at sowing; systemic nematicide"},
            {"name": "Abamectin 18 EC (seed treatment)", "rate": "As per label",
             "phi_days": "N/A", "notes": "Protects seedling establishment; limited residual activity"},
        ],
        biological_control=[
            "Paecilomyces lilacinus — egg parasite, applied as soil amendment at planting",
            "Purpureocillium lilacinum-based products for pre-plant soil treatment",
            "Marigold (Tagetes spp.) as rotation/intercrop releases alpha-terthienyl nematicide",
        ],
        cultural_control=[
            "Pre-plant soil sampling and nematode analysis — essential for fresh market carrots",
            "Rotate with non-host cereals (maize, wheat, sorghum) for 2-3 years",
            "Solarise beds with clear plastic for 6-8 weeks before planting",
            "Incorporate organic matter (compost, cattle manure) to support antagonistic soil biota",
            "Plant mustard/rapeseed as biofumigant green manure before carrot crop",
            "Avoid fields with known nematode history for premium fresh market production",
        ],
        scouting_protocol=(
            "Pre-plant: collect 15-20 soil cores (0-30cm) per ha, composite, and submit "
            "for Meloidogyne analysis. During crop: pull sample roots at 45 and 70 days — "
            "forking or galling indicates problem. Post-harvest: assess root quality and "
            "submit soil for confirmation."
        ),
    ),
    PestProfile(
        name="Aphids (Carrot-Willow Aphid)",
        scientific_name="Cavariella aegopodii",
        pest_type="insect",
        identification=[
            "Small (2mm) pale green aphid on leaves and petioles",
            "Wingless forms cluster on young foliage",
            "Winged forms migrate between carrot and willow trees",
        ],
        damage_symptoms=[
            "Curling and yellowing of young leaves",
            "Honeydew and sooty mould on foliage",
            "Vector of Carrot Motley Dwarf virus complex",
            "Stunted root development in heavy infestations",
        ],
        life_cycle_notes=(
            "Holocyclic — alternates between willow (winter host) and carrot (summer host). "
            "Winged migrants colonise carrot crops from nearby willow trees. "
            "Rapid parthenogenetic reproduction; colonies build quickly in warm weather. "
            "Virus transmission occurs within minutes of feeding."
        ),
        favourable_conditions={
            "temp_min_c": 15, "temp_max_c": 25,
            "note": "Warm, dry conditions favour rapid colony build-up. "
                    "Proximity to willow trees increases immigration pressure."
        },
        susceptible_stages=["Vegetative Growth", "Root Bulking"],
        economic_threshold="10+ aphids per plant or first signs of virus symptoms",
        chemical_control=[
            {"name": "Pirimicarb 50 WG", "rate": "250 g/ha",
             "phi_days": "7", "notes": "Selective aphicide; preserves natural enemies"},
            {"name": "Acetamiprid 20 SP", "rate": "100 g/ha",
             "phi_days": "7", "notes": "Systemic; good for established colonies"},
        ],
        biological_control=[
            "Parasitic wasps (Aphidius spp.) — naturally abundant, conserve by avoiding broad-spectrum sprays",
            "Ladybirds (Coccinellidae) and lacewings (Chrysoperla spp.) as generalist predators",
            "Entomopathogenic fungi (Beauveria bassiana) foliar applications",
        ],
        cultural_control=[
            "Reflective mulch reduces winged aphid landing rates",
            "Avoid planting downwind of willow trees",
            "Remove volunteer Apiaceae weeds that serve as bridge hosts",
            "Adequate plant nutrition — stressed plants are more attractive",
        ],
        scouting_protocol=(
            "Weekly visual inspection of youngest leaves from emergence onwards. "
            "Check 20 plants per sampling point, 5 points per ha. Record aphid "
            "presence/absence and colony size category (light/moderate/heavy)."
        ),
    ),
]

CARROT_GROWTH_STAGES: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Germination & Emergence",
        stage_code="VE",
        day_range=(0, 21),
        water_kc=0.3,
        water_mm_per_week=12,
        critical_nutrients=["Phosphorus"],
        key_activities=[
            "Sow seed 10-15mm deep in fine, stone-free seedbed",
            "Ensure consistent moisture — carrot seed germinates slowly (10-21 days)",
            "Light irrigation (5mm) every 2 days to prevent surface crusting",
            "Apply pre-emergence herbicide (linuron) if weed pressure expected",
        ],
        risks=[
            "Surface crusting prevents emergence in heavy soils",
            "Erratic moisture causes uneven germination",
            "Ants carrying away seed",
            "Damping off (Pythium) in waterlogged conditions",
        ],
        scientific_notes=(
            "Carrot seed is slow to germinate (10-21 days) due to dormancy imposed by "
            "furanocoumarins in the seed coat. Optimal germination temperature is 20-25°C. "
            "Seed priming (hydropriming or osmopriming with PEG) can reduce field emergence "
            "time by 5-7 days. Fine seedbed preparation is critical as carrot seedlings "
            "are weak and cannot push through crusted soil."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Seedling Establishment",
        stage_code="V1",
        day_range=(21, 45),
        water_kc=0.5,
        water_mm_per_week=18,
        critical_nutrients=["Nitrogen", "Phosphorus"],
        key_activities=[
            "Thin to 3-5cm spacing when seedlings have 2-3 true leaves",
            "First hand weeding — carrot is very poor competitor when small",
            "Begin scouting for Alternaria on older leaves",
            "Monitor for aphid colonisation",
        ],
        risks=[
            "Weed competition — carrot canopy closes very slowly",
            "Thinning attracting carrot rust fly (thin in evening, firm soil)",
            "Damping off continuing in waterlogged beds",
        ],
        scientific_notes=(
            "Carrot seedlings are notoriously slow-growing and uncompetitive. "
            "The first 6 weeks are the critical weed-free period — yield losses of "
            "30-90% if weeds are not controlled during this window. "
            "Thinning releases volatile terpenes that attract Psila rosae adults."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Vegetative Growth & Canopy Development",
        stage_code="V2",
        day_range=(45, 75),
        water_kc=0.8,
        water_mm_per_week=25,
        critical_nutrients=["Nitrogen", "Potassium", "Calcium"],
        key_activities=[
            "Apply nitrogen top-dress (AN 150 kg/ha) at 6 weeks",
            "Maintain consistent irrigation — avoid wet-dry cycles",
            "Scout for Alternaria leaf blight weekly",
            "Second hand weeding before canopy closure",
        ],
        risks=[
            "Nitrogen excess causes excessive foliage at expense of root",
            "Alternaria establishing if overhead irrigation used",
            "Root-knot nematode damage becoming visible as forking",
        ],
        scientific_notes=(
            "Canopy development drives root yield through photosynthate supply. "
            "Carrot leaf area index peaks at 3-4 for optimal root bulking. "
            "Excessive nitrogen shifts partitioning to shoots; target N status that "
            "maintains deep green colour without lush, floppy foliage. "
            "Calcium is critical for cell wall integrity and cavity spot prevention."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Root Bulking",
        stage_code="RB",
        day_range=(75, 110),
        water_kc=0.9,
        water_mm_per_week=30,
        critical_nutrients=["Potassium", "Calcium", "Boron"],
        key_activities=[
            "Maintain even soil moisture — critical for root quality",
            "Apply potassium top-dress (MOP 100 kg/ha) if not in basal",
            "Foliar boron (Solubor 1 kg/ha) to prevent internal browning",
            "Continue Alternaria fungicide programme",
            "Sample roots for quality assessment at 90 days",
        ],
        risks=[
            "Cracking and splitting from uneven water supply",
            "Cavity spot (Pythium) in compacted, waterlogged soil",
            "Green shoulders from soil erosion exposing crown to light",
            "Bitter taste from terpenoid accumulation under heat stress",
        ],
        scientific_notes=(
            "Root bulking is driven by sucrose transport from leaves via phloem. "
            "Carrot roots accumulate carotenoids (alpha- and beta-carotene) during "
            "bulking, with content increasing as roots mature. Temperature above 30°C "
            "reduces carotene synthesis and increases terpenoid production (bitterness). "
            "Potassium is essential for sucrose translocation; boron prevents internal "
            "browning caused by calcium-boron imbalance in xylem."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Maturation & Harvest",
        stage_code="HV",
        day_range=(110, 140),
        water_kc=0.7,
        water_mm_per_week=20,
        critical_nutrients=["Potassium"],
        key_activities=[
            "Reduce irrigation 7-10 days before harvest to firm roots",
            "Test harvest sample: check size, colour, flavour, defects",
            "Irrigate lightly day before harvest to ease pulling/lifting",
            "Harvest in cool morning; minimise sun exposure of roots",
            "Top roots immediately; hydrocool if possible",
        ],
        risks=[
            "Over-maturity: roots become woody and crack",
            "Cavity spot worsening the longer roots remain in soil",
            "Post-harvest losses from mechanical damage during harvest",
            "Green shoulder devaluing fresh market grade",
        ],
        scientific_notes=(
            "Carrot roots reach harvestable maturity at 110-140 days depending on variety "
            "and temperature. Kuroda types mature faster (100-110 days) than Nantes (120-140). "
            "Sugar content peaks then declines if left too long. Fibre content increases "
            "with age, reducing eating quality. Post-harvest cooling to 0-1°C within 4 hours "
            "extends shelf life to 4-6 months in cold storage."
        ),
    ),
]

CARROT_FERTILIZER = FertilizerSchedule(
    basal={
        "product": "Compound S (7:21:8) or 2:3:4 (30)",
        "rate_kg_ha": 400,
        "timing": "Broadcast and incorporate before sowing",
        "notes": "High P for root development. Avoid fresh manure — causes forking. "
                 "Well-composted manure (20 t/ha) applied 3+ months before sowing is acceptable."
    },
    top_dress_1={
        "product": "Ammonium Nitrate (AN 34.5%)",
        "rate_kg_ha": 150,
        "timing": "6 weeks after emergence (V2 stage)",
        "notes": "Side-dress along rows. Do not exceed 80 kg N/ha total to avoid excessive foliage."
    },
    top_dress_2={
        "product": "Muriate of Potash (MOP 60% K₂O)",
        "rate_kg_ha": 100,
        "timing": "8-10 weeks after emergence (early root bulking)",
        "notes": "Potassium supports sugar accumulation and root colour development."
    },
    foliar={
        "product": "Solubor (20.5% B) + Calcium Chloride",
        "rate_kg_ha": 1.0,
        "timing": "At root bulking onset, repeat 14 days later",
        "notes": "Boron prevents internal browning; calcium reduces cavity spot risk."
    },
    liming={
        "product": "Agricultural lime (calcitic)",
        "rate_kg_ha": 1500,
        "timing": "4-6 weeks before planting if pH < 6.0",
        "notes": "Target pH 6.0-6.8. Calcium also helps prevent cavity spot. "
                 "Overliming above pH 7.0 may induce micronutrient deficiencies."
    },
    notes=(
        "Carrot is sensitive to direct contact with fertilizer granules — broadcast and "
        "incorporate rather than banding close to seed. Avoid fresh animal manure as it "
        "causes root forking, excessive hairiness, and off-flavours. Total N should not "
        "exceed 80-100 kg/ha to prevent excessive top growth at the expense of root yield."
    ),
)

CARROT_PLANTING_WINDOWS: List[PlantingWindow] = [
    PlantingWindow(
        region="NR I — Eastern Highlands",
        optimal_start="March 1",
        optimal_end="June 30",
        acceptable_start="February 15",
        acceptable_end="July 31",
        notes="Cool, moist conditions ideal. Can grow year-round at higher elevations (>1500m). "
              "Best quality carrots from this region due to cool temperatures enhancing sweetness.",
    ),
    PlantingWindow(
        region="NR IIa/IIb — Highveld (Harare, Marondera)",
        optimal_start="March 15",
        optimal_end="May 31",
        acceptable_start="March 1",
        acceptable_end="June 30",
        notes="Main commercial production zone. Winter crop under irrigation. "
              "Avoid planting after June — heat during root bulking (Sep-Oct) causes bitterness.",
    ),
    PlantingWindow(
        region="NR III — Middleveld",
        optimal_start="April 1",
        optimal_end="May 31",
        acceptable_start="March 15",
        acceptable_end="June 15",
        notes="Narrower window due to warmer temperatures. Irrigation essential. "
              "Harvest before onset of hot season in October.",
    ),
    PlantingWindow(
        region="NR IV-V — Lowveld (irrigated)",
        optimal_start="May 1",
        optimal_end="June 30",
        acceptable_start="April 15",
        acceptable_end="July 15",
        notes="Only during coolest months. Night temperatures must drop below 20°C for "
              "root colour development. Nematode pressure often high in sandy Lowveld soils.",
    ),
]


PROFILE = CropProfile(
    crop_name="Carrot",
    scientific_name="Daucus carota subsp. sativus",
    family="Apiaceae",

    optimal_ph=(6.0, 6.8),
    critical_ph_low=5.2,
    optimal_soil_types=[
        "Deep sandy loams — root development",
        "Loamy sands — easy harvest, good shape",
        "Alluvial soils — fertile and stone-free",
    ],
    avoid_soil_types=[
        "Heavy clay — causes forking and poor shape",
        "Rocky/stony soils — misshapen roots, mechanical damage",
        "Recently manured soils — forking from high N and organic acids",
        "Compacted soils — restricted root elongation and cavity spot risk",
    ],

    optimal_temp=(15.0, 22.0),
    critical_temp_low=2.0,
    critical_temp_high=30.0,
    base_temp_gdd=5.0,
    total_water_mm=400.0,

    growth_stages=CARROT_GROWTH_STAGES,
    fertilizer_schedule=CARROT_FERTILIZER,
    diseases=CARROT_DISEASES,
    pests=CARROT_PESTS,
    planting_windows=CARROT_PLANTING_WINDOWS,

    harvest_moisture="Roots: 86-88% moisture content at harvest (fresh weight basis)",
    storage_conditions=(
        "0-1°C and 95-98% RH for long-term storage (4-6 months). "
        "Remove tops immediately after harvest to prevent moisture loss. "
        "Hydrocooling within 2 hours of harvest extends shelf life. "
        "Do not store with ethylene-producing fruits (apples, bananas) — causes bitterness."
    ),
    post_harvest_notes=(
        "Kuroda variety dominant in Zimbabwe due to heat tolerance and deep orange colour. "
        "Carrots for fresh market must be washed, graded (baby 10-12cm, medium 15-18cm, "
        "large 18-22cm), and packed in 10kg bags. Reject roots with green shoulder >2cm, "
        "forking, cracking, cavity spot, or nematode damage. "
        "Processing carrots (for freezing/canning) have more relaxed shape standards."
    ),

    natural_region_suitability={
        "I": "Excellent — cool climate, year-round production possible at altitude",
        "IIa": "Good — main commercial zone, winter production under irrigation",
        "IIb": "Good — similar to IIa with slightly warmer microclimate",
        "III": "Moderate — restricted to cool season, irrigation essential",
        "IV": "Limited — only coolest months (May-Jul), nematode pressure",
        "V": "Poor — too hot for quality production except brief cool window",
    },
)

ALIASES = ["carrots"]
