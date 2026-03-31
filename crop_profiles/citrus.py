"""Citrus (Citrus spp.) — Perennial evergreen fruit trees, major export and domestic crop grown in Zimbabwe's Lowveld and Eastern Highlands."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List


CITRUS_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Citrus Greening (Huanglongbing / HLB)",
        pathogen="Candidatus Liberibacter africanus (African form)",
        pathogen_type="bacterial",
        symptoms=[
            "Blotchy mottle — asymmetric yellow patches on leaves (not vein-defined)",
            "Lopsided, small, bitter fruit with aborted seeds and green colour retained at stylar end",
            "Twig dieback and sparse canopy",
            "Zinc-deficiency-like symptoms but asymmetric across midrib (diagnostic)",
        ],
        identification_markers=[
            "Asymmetric chlorosis — unlike true zinc deficiency which is symmetric",
            "Lopsided fruit with colour inversion (green stylar end, orange stem end)",
            "Vascular staining in phloem when bark is peeled",
            "PCR confirmation from leaf midrib samples is definitive",
        ],
        favourable_conditions={
            "temp_min_c": 20, "temp_max_c": 30,
            "note": "African form (CLaf) is heat-sensitive; symptoms worsen in cool conditions "
                    "(below 25°C) unlike Asian form. Trioza erytreae psyllid vector prefers "
                    "cool, wet conditions at altitudes above 600m — Eastern Highlands is highest risk."
        },
        susceptible_stages=["Young trees", "Flushing periods"],
        resistant_varieties=[],
        susceptible_varieties=["All commercial cultivars susceptible; Valencia, Navel most severely affected"],
        chemical_control=[
            {"name": "Imidacloprid 200 SL (vector control)", "rate": "0.5 mL/tree soil drench",
             "phi_days": "60", "notes": "Systemic; targets psyllid nymphs during flush periods"},
            {"name": "Dimethoate 400 EC (vector control)", "rate": "1.0 L/ha",
             "phi_days": "28", "notes": "Foliar spray targeting adult psyllids on new flush"},
        ],
        biological_control=[
            "Tamarixia dryi — parasitoid wasp of Trioza erytreae, released as augmentative biocontrol",
            "Conservation of natural enemies by reducing broad-spectrum insecticide use",
        ],
        cultural_control=[
            "Use certified disease-free nursery trees from registered nurseries",
            "Remove and destroy infected trees (no cure exists)",
            "Suppress flush management to reduce psyllid breeding sites",
            "Regional area-wide psyllid management programmes",
            "Nutritional support (foliar micronutrients) to extend productive life of mildly affected trees",
        ],
        economic_threshold="Zero tolerance — any confirmed HLB tree should be removed to protect grove",
        severity_scale={
            "mild": "< 5% trees showing symptoms, prompt removal can contain spread",
            "moderate": "5-30% trees affected, grove productivity declining",
            "severe": "> 30% trees symptomatic, grove economics compromised, replanting required",
        },
    ),
    DiseaseProfile(
        name="Citrus Black Spot",
        pathogen="Phyllosticta citricarpa (syn. Guignardia citricarpa)",
        pathogen_type="fungal",
        symptoms=[
            "Hard spot: round, sunken lesions with grey centre and dark brown margin on fruit",
            "Freckle spot: raised red-brown flecks on rind",
            "Virulent spot: large, spreading dark lesions on mature fruit",
            "False melanose: small dark spots resembling melanose but caused by same pathogen",
        ],
        identification_markers=[
            "Hard spot with grey centre containing pycnidia (black dots) is diagnostic",
            "Symptoms appear only on fruit and rarely on leaves (except lemon)",
            "EU quarantine pathogen — any detection blocks export",
            "Laboratory isolation needed to distinguish from Phyllosticta capitalensis (non-pathogenic)",
        ],
        favourable_conditions={
            "humidity_min": 80, "temp_min_c": 20, "temp_max_c": 30,
            "rainfall_note": "Summer rainfall during fruit development",
            "note": "Ascospores released from leaf litter during warm, wet weather. "
                    "Infection period is 4-6 months before symptoms appear. "
                    "Late-maturing cultivars (Valencia) have longer fruit exposure."
        },
        susceptible_stages=["Fruit set", "Fruit development (first 5-6 months)"],
        resistant_varieties=["Satsuma mandarins (short fruit exposure)"],
        susceptible_varieties=["Valencia (most susceptible due to late maturity)", "Navel oranges", "Lemon"],
        chemical_control=[
            {"name": "Mancozeb 800 WP + mineral oil", "rate": "2.5 kg + 5 L/ha",
             "phi_days": "14", "notes": "Monthly from petal fall to February; backbone of programme"},
            {"name": "Azoxystrobin 250 SC", "rate": "0.4 L/ha",
             "phi_days": "21", "notes": "Alternate with mancozeb; strobilurin resistance management required"},
            {"name": "Copper oxychloride 850 WP", "rate": "3.0 kg/ha",
             "phi_days": "14", "notes": "Pre-harvest spray for late-season protection"},
        ],
        biological_control=[
            "Rapid decomposition of leaf litter with urea sprays (46 kg/ha on orchard floor) reduces ascospore inoculum",
            "Mulching over leaf litter to suppress ascospore release",
        ],
        cultural_control=[
            "Accelerate leaf litter decomposition — urea spray on fallen leaves, mulch heavily",
            "Prune to open canopy for better spray coverage and air circulation",
            "Remove fallen fruit which harbours inoculum",
            "Earlier-maturing cultivars have lower risk due to shorter exposure",
            "Wind-breaks reduce humidity in orchard microclimate",
        ],
        economic_threshold="Zero tolerance for export fruit (EU phytosanitary requirement). "
                           "Domestic market: cosmetic damage >25% of fruit surface affects saleability.",
        severity_scale={
            "mild": "< 5% fruit with 1-2 hard spots, acceptable for juice market",
            "moderate": "5-20% fruit with multiple spot types, downgraded from fresh export",
            "severe": "> 20% fruit affected, significant revenue loss; grove-wide intervention needed",
        },
    ),
    DiseaseProfile(
        name="Phytophthora Root Rot and Gummosis",
        pathogen="Phytophthora nicotianae, P. citrophthora",
        pathogen_type="oomycete",
        symptoms=[
            "Gum exudation from trunk and major limbs (gummosis)",
            "Dark, water-soaked bark lesions at soil line",
            "Root rot: brown, decayed feeder roots",
            "Canopy thinning, small fruit, and tree decline",
        ],
        identification_markers=[
            "Gum exudation with dark stained bark underneath (peel bark to check)",
            "Lesions at or near soil line extending upward",
            "Sour smell from affected bark tissue",
            "Root system: brown, sparse feeder roots vs healthy white roots",
        ],
        favourable_conditions={
            "soil_moisture": "waterlogged or poorly drained soils",
            "temp_min_c": 20, "temp_max_c": 30,
            "note": "Zoospores swim in free water — any waterlogging event is an infection risk. "
                    "Trees on susceptible rootstocks (rough lemon, sweet orange) most affected."
        },
        susceptible_stages=["All stages; young trees most vulnerable to decline"],
        resistant_varieties=["Troyer citrange rootstock (tolerant)", "Swingle citrumelo rootstock"],
        susceptible_varieties=["Rough lemon rootstock (highly susceptible)", "Sweet orange rootstock"],
        chemical_control=[
            {"name": "Fosetyl-Al 800 WP", "rate": "3.0 kg/ha foliar or 50g/tree trunk paint",
             "phi_days": "14", "notes": "Systemic; translocates to roots. Apply 2-3 times per year"},
            {"name": "Metalaxyl-M 480 SL", "rate": "2.5 mL/tree soil drench",
             "phi_days": "60", "notes": "Soil application in tree basin during active root growth"},
        ],
        biological_control=[
            "Trichoderma harzianum soil application around tree basin",
            "Mycorrhizal inoculants improve root health and resistance",
        ],
        cultural_control=[
            "Plant on Phytophthora-tolerant rootstocks (Troyer citrange, Carrizo citrange)",
            "Ensure excellent drainage — raised beds, drainage channels, avoid heavy soils",
            "Keep bud union 30cm above soil line; avoid soil build-up against trunk",
            "Avoid micro-sprinkler wetting of trunk; use drip irrigation",
            "Remove bark and treat gummosis lesions with copper paste",
        ],
        economic_threshold="Any gummosis lesion on trunk; declining feeder root health on rootstock assessment",
        severity_scale={
            "mild": "Isolated gummosis on 1-2 limbs, feeder roots still functional",
            "moderate": "Trunk gummosis affecting 25-50% circumference, canopy thinning",
            "severe": "Root rot advanced, canopy severely thin, tree non-productive",
        },
    ),
]

CITRUS_PESTS: List[PestProfile] = [
    PestProfile(
        name="African Citrus Psyllid",
        scientific_name="Trioza erytreae",
        pest_type="insect",
        identification=[
            "Adult: small (3-4mm) dark brown psyllid with clear wings",
            "Nymph: flat, green, found in characteristic 'pit galls' on leaf underside",
            "Pit galls on young leaves are diagnostic — unique to this species",
        ],
        damage_symptoms=[
            "Characteristic pit galls (depressions) on leaf underside",
            "Leaf distortion and curling of new flush",
            "Vector of Candidatus Liberibacter africanus (HLB/greening)",
            "Direct feeding damage minimal — disease transmission is the critical concern",
        ],
        life_cycle_notes=(
            "Adults colonise new flush growth to lay eggs on leaf margins. "
            "Nymphs develop in pit galls through 5 instars over 15-40 days depending on temperature. "
            "Adults are long-lived (several months) and highly mobile. "
            "Prefers cool, moist conditions — most damaging in Eastern Highlands."
        ),
        favourable_conditions={
            "temp_min_c": 15, "temp_max_c": 25,
            "altitude_note": "Most abundant above 600m altitude",
            "note": "Cool, moist conditions with regular flushing. "
                    "Populations peak during spring and autumn flush periods. "
                    "Eastern Highlands and Highveld orchards are highest risk."
        },
        susceptible_stages=["Flushing periods (spring, summer, autumn)"],
        economic_threshold="1 adult per yellow sticky trap per week; any nymphs on new flush in HLB-risk area",
        chemical_control=[
            {"name": "Imidacloprid 200 SL", "rate": "0.5 mL/tree soil drench",
             "phi_days": "60", "notes": "Systemic; protects during flush. Best for young trees."},
            {"name": "Dimethoate 400 EC", "rate": "1.0 L/ha",
             "phi_days": "28", "notes": "Foliar spray at flush break; targets adults and nymphs"},
            {"name": "Abamectin 18 EC", "rate": "0.5 L/ha",
             "phi_days": "7", "notes": "Low impact on beneficials; good IPM fit"},
        ],
        biological_control=[
            "Tamarixia dryi — specific ecto-parasitoid of T. erytreae nymphs; highly effective in biological control programmes",
            "Ladybird beetles and lacewings as generalist predators",
            "Conservation biological control by maintaining indigenous vegetation around orchards",
        ],
        cultural_control=[
            "Synchronise flush across orchard (pruning) to concentrate management",
            "Remove volunteer citrus seedlings that serve as psyllid reservoirs",
            "Manage irrigation to avoid continuous flush production",
            "Windbreaks to reduce psyllid movement between orchards",
        ],
        scouting_protocol=(
            "Deploy yellow sticky traps (1 per 2 ha) at canopy height. Check weekly. "
            "Visually inspect new flush shoots for pit galls and nymphs — check 5 trees "
            "per row, 5 rows per block. Record presence/absence and severity."
        ),
    ),
    PestProfile(
        name="Citrus Red Scale",
        scientific_name="Aonidiella aurantii",
        pest_type="insect",
        identification=[
            "Female: circular, 2mm, reddish-brown armoured scale on fruit, leaves, and bark",
            "Male: tiny winged insect; seldom seen",
            "Crawlers: minute, pale yellow, mobile first instar",
        ],
        damage_symptoms=[
            "Circular scale covers on fruit rind — cosmetic downgrading",
            "Yellow chlorotic halos around scale on leaves",
            "Heavy infestation causes leaf drop and twig dieback",
            "Fruit rejected for export with >3 live scales per fruit",
        ],
        life_cycle_notes=(
            "3-4 overlapping generations per year in Zimbabwe. "
            "Crawlers disperse by wind and settle on fruit, leaves, or bark. "
            "Development from crawler to adult takes 6-10 weeks. "
            "Females produce 100-150 crawlers over several weeks."
        ),
        favourable_conditions={
            "temp_min_c": 20, "temp_max_c": 35,
            "note": "Hot, dry conditions favour population build-up. "
                    "Dust on trees increases scale populations (inhibits natural enemies). "
                    "Interior canopy and shaded fruit are most heavily infested."
        },
        susceptible_stages=["Fruit development", "Throughout year on leaves and bark"],
        economic_threshold="5% of fruit with >3 live scales per fruit at monitoring",
        chemical_control=[
            {"name": "Mineral oil (petroleum spray oil)", "rate": "10-15 L/ha",
             "phi_days": "0", "notes": "Suffocates crawlers and settled scales; safe for beneficials; backbone of programme"},
            {"name": "Chlorpyrifos 480 EC", "rate": "1.5 L/ha",
             "phi_days": "28", "notes": "Crawler-targeted spray when peak crawler activity detected"},
            {"name": "Spirotetramat 240 SC", "rate": "0.5 L/ha",
             "phi_days": "14", "notes": "Ambimobile systemic; excellent scale control; IPM-compatible"},
        ],
        biological_control=[
            "Aphytis africanus and Aphytis melinus — parasitoid wasps specific to red scale (very effective)",
            "Chilocorus nigrita — ladybird beetle predator of armoured scales",
            "Comperiella bifasciata — internal parasitoid of red scale",
            "Conserve parasitoids by using selective insecticides and mineral oil",
        ],
        cultural_control=[
            "Prune to open canopy — reduces humidity and improves spray coverage",
            "Dust control on farm roads reduces scale populations",
            "Avoid broad-spectrum insecticides that destroy natural enemy complex",
            "Ants protect scales from parasitoids — control ants (sticky bands on trunks)",
        ],
        scouting_protocol=(
            "Monthly: examine 10 fruit per tree on 5 trees per block. "
            "Record live scale count per fruit. Use hand lens to check for parasitoid "
            "emergence holes (indicates biocontrol activity). "
            "Monitor crawler activity with double-sided tape wrapped around fruit."
        ),
    ),
    PestProfile(
        name="Fruit Fly (Mediterranean Fruit Fly)",
        scientific_name="Ceratitis capitata",
        pest_type="insect",
        identification=[
            "Adult: 5mm, yellowish-brown with iridescent wings (dark bands)",
            "Larva: white, legless maggot inside fruit",
            "Pupa: brown, barrel-shaped in soil",
        ],
        damage_symptoms=[
            "Oviposition puncture marks on fruit rind",
            "Internal larval feeding causing fruit rot",
            "Premature fruit drop",
            "Secondary fungal and bacterial decay in feeding tunnels",
        ],
        life_cycle_notes=(
            "Female punctures fruit rind with ovipositor, deposits 2-10 eggs per puncture. "
            "Larvae develop inside fruit in 7-14 days, then drop to soil to pupate. "
            "Adult emergence after 10-14 days in warm weather. "
            "Multiple overlapping generations; population peaks in warm, humid months."
        ),
        favourable_conditions={
            "temp_min_c": 18, "temp_max_c": 32,
            "note": "Warm, humid conditions during fruit ripening. "
                    "Presence of alternative hosts (guava, mango, peach) nearby increases pressure. "
                    "Populations build from October, peaking January-March."
        },
        susceptible_stages=["Fruit colouring and ripening"],
        economic_threshold="0.5 flies per McPhail trap per day; or first oviposition stings detected on fruit",
        chemical_control=[
            {"name": "GF-120 (spinosad bait)", "rate": "1.0-1.5 L/ha (spot spray)",
             "phi_days": "7", "notes": "Bait spray applied to 1m² patch on every other tree; highly selective"},
            {"name": "Malathion 500 EC + protein hydrolysate bait", "rate": "1.5 L + 1.0 L/ha",
             "phi_days": "7", "notes": "Traditional bait spray; less IPM-friendly than GF-120"},
        ],
        biological_control=[
            "Sterile Insect Technique (SIT) — release of irradiated sterile males",
            "Fopius arisanus and Diachasmimorpha longicaudata — egg and larval parasitoids",
            "Conservation of soil-dwelling pupal predators (ants, beetles)",
        ],
        cultural_control=[
            "Orchard sanitation — remove and destroy fallen fruit weekly",
            "Strip-pick ripe fruit promptly; do not leave overripe fruit on trees",
            "Remove alternative host plants (guava, feral peach) near orchard",
            "Mass trapping with McPhail or Lynfield traps (4-6 per ha)",
            "Post-harvest cold treatment (1°C for 16 days) for export compliance",
        ],
        scouting_protocol=(
            "McPhail traps baited with liquid protein hydrolysate or Torula yeast tablets: "
            "1 trap per 2 ha. Check and record weekly from colour break until harvest. "
            "Action threshold is 0.5 flies per trap per day. "
            "Also visually inspect ripening fruit for oviposition punctures."
        ),
    ),
]

CITRUS_GROWTH_STAGES: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Dormancy / Pre-Spring Flush",
        stage_code="D",
        day_range=(0, 30),
        water_kc=0.5,
        water_mm_per_week=15,
        critical_nutrients=["Zinc", "Manganese", "Boron"],
        key_activities=[
            "Winter pruning of dead wood, water sprouts, and crossing branches",
            "Apply dormant mineral oil spray for scale and mite control",
            "Foliar micronutrient spray (Zn, Mn, B) for spring flush support",
            "Soil sampling and pH adjustment if needed",
            "Pre-bloom phosphonate trunk injection for Phytophthora if history exists",
        ],
        risks=[
            "Frost damage in Eastern Highlands (July-August)",
            "Scale build-up under bark if dormant spray missed",
            "Root rot progressing in waterlogged winter soils",
        ],
        scientific_notes=(
            "Citrus in Zimbabwe's subtropical climate has a mild winter dormancy driven by "
            "cool temperatures and reduced daylength. Carbohydrate reserves accumulate during "
            "this period, supporting the coming spring flush and bloom. Zinc deficiency is "
            "common in Zimbabwean soils and must be corrected pre-bloom as it affects fruit set."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Spring Flush & Flowering",
        stage_code="FL",
        day_range=(30, 75),
        water_kc=0.6,
        water_mm_per_week=20,
        critical_nutrients=["Nitrogen", "Boron", "Calcium"],
        key_activities=[
            "Monitor psyllid activity on new flush — spray if threshold exceeded",
            "Bee-safe practices during bloom — avoid insecticides during flowering",
            "Foliar boron spray (Solubor 1 kg/ha) for fruit set",
            "Light nitrogen application (AN 300g/tree) post-petal fall",
            "Begin black spot fungicide programme at petal fall",
        ],
        risks=[
            "Poor fruit set from boron deficiency or cold stress",
            "Psyllid colonisation of new flush (HLB vector risk)",
            "Wind damage to flower clusters",
            "Thrips scarring flower buds and young fruitlets",
        ],
        scientific_notes=(
            "Citrus flowering is induced by winter stress (cold and/or drought) followed by "
            "return of warmth and moisture. Most Zimbabwe citrus blooms August-September. "
            "Effective pollination requires adequate boron (for pollen tube growth) and "
            "temperatures above 15°C. Natural fruit set in Valencia is typically 1-3% of flowers."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Fruit Set & June Drop",
        stage_code="FS",
        day_range=(75, 120),
        water_kc=0.65,
        water_mm_per_week=22,
        critical_nutrients=["Potassium", "Calcium", "Nitrogen"],
        key_activities=[
            "Maintain consistent irrigation to reduce physiological fruit drop",
            "Continue black spot and red scale monitoring",
            "Foliar potassium applications for fruit retention",
            "Apply GA (gibberellic acid) if needed to reduce alternate bearing",
        ],
        risks=[
            "Excessive June drop from water stress or nutrient imbalance",
            "Young fruit susceptible to black spot infection (latent)",
            "Mite build-up (red mite, rust mite) on leaves and fruitlets",
        ],
        scientific_notes=(
            "Physiological fruit drop occurs in 2-3 waves during the first 8-12 weeks after "
            "bloom. This is driven by competition among fruitlets for carbohydrate from leaves. "
            "Trees naturally adjust crop load through abscission regulated by auxin/ethylene balance. "
            "Potassium and consistent water supply reduce excessive drop."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Fruit Enlargement",
        stage_code="FE",
        day_range=(120, 270),
        water_kc=0.7,
        water_mm_per_week=28,
        critical_nutrients=["Potassium", "Calcium", "Magnesium"],
        key_activities=[
            "Continue fungicide programme for black spot (monthly mancozeb + oil)",
            "Monitor red scale — apply mineral oil if threshold exceeded",
            "Summer nitrogen application (AN 500g/tree) for canopy maintenance",
            "Potassium application (KCl 500g/tree) for fruit size and quality",
            "Monitor fruit fly from colour break (January onwards)",
        ],
        risks=[
            "Black spot infection continuing (latent for 4-6 months)",
            "Red scale and rust mite build-up in hot, dry weather",
            "Fruit splitting from erratic irrigation",
            "Sunburn on exposed fruit during October-January heat",
        ],
        scientific_notes=(
            "Fruit growth follows a sigmoidal curve with rapid cell division (first 6-8 weeks) "
            "then cell enlargement (remainder). Potassium is the primary driver of fruit size — "
            "it increases cell turgor and osmotic potential. Calcium is critical in first 8 weeks "
            "for rind quality and creasing prevention. Fruit colour develops when night temperatures "
            "drop below 13°C, breaking down chlorophyll and revealing carotenoids."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Fruit Maturation & Harvest",
        stage_code="HV",
        day_range=(270, 365),
        water_kc=0.65,
        water_mm_per_week=22,
        critical_nutrients=["Potassium"],
        key_activities=[
            "Fruit fly management intensifies — bait sprays weekly",
            "Maturity testing: Brix/acid ratio ≥8:1 for sweet orange",
            "Pre-harvest copper spray for black spot control on fruit",
            "Harvest using clippers (not pulling) to prevent rind injury",
            "Post-harvest fungicide dip (thiabendazole) and waxing",
        ],
        risks=[
            "Fruit fly damage as fruit ripens",
            "Alternaria brown spot on mandarins",
            "Over-maturity: rind puffing, re-greening, and granulation (Valencia)",
            "Post-harvest stem-end rot and green/blue mould",
        ],
        scientific_notes=(
            "Citrus is non-climacteric — fruit do not ripen further after harvest. "
            "Maturity is assessed by internal quality (Brix, acidity, juice content) not external colour. "
            "Valencia oranges in Zimbabwe reach legal maturity (Brix/acid ≥8, juice ≥35%) from "
            "June onwards. Late-hung fruit risks granulation (juice vesicle drying) and re-greening "
            "as temperatures warm again in September."
        ),
    ),
]

CITRUS_FERTILIZER = FertilizerSchedule(
    basal={
        "product": "Compound S (7:21:8) + Superphosphate",
        "rate_kg_ha": 0,
        "timing": "At planting in hole: 500g Compound S + 250g superphosphate per tree",
        "notes": "Young trees: fertilize 4 times per year in tree basin. "
                 "Mature trees: 3 main applications — post-harvest, pre-bloom, post-June drop."
    },
    top_dress_1={
        "product": "LAN 28% (post-harvest)",
        "rate_kg_ha": 0,
        "timing": "July-August (post-harvest for Valencia)",
        "notes": "250-500g LAN per tree depending on age. Replenishes nitrogen reserves for spring flush. "
                 "Young trees (1-3yr): 200g. Bearing trees (5yr+): 500-800g."
    },
    top_dress_2={
        "product": "KCl 60% K₂O (fruit enlargement)",
        "rate_kg_ha": 0,
        "timing": "December-January during fruit enlargement",
        "notes": "300-600g KCl per tree. Potassium is critical for fruit size and quality. "
                 "Split application with pre-bloom K gives best results."
    },
    foliar={
        "product": "Zinc Sulphate (36% Zn) + Manganese Sulphate + Solubor",
        "rate_kg_ha": 5,
        "timing": "Pre-bloom (August) and post-set (November)",
        "notes": "Foliar micronutrients essential in Zimbabwe's predominantly acid, leached soils. "
                 "Zn 5 kg/ha + Mn 3 kg/ha + Solubor 1 kg/ha. Add urea 5 kg/ha as carrier."
    },
    liming={
        "product": "Dolomitic lime (calcium + magnesium)",
        "rate_kg_ha": 2000,
        "timing": "Every 2-3 years based on soil analysis, apply in tree row",
        "notes": "Target pH 6.0-6.5 for optimal nutrient availability. "
                 "Dolomitic preferred to supply both Ca and Mg. "
                 "Gypsum (2 t/ha) if calcium needed without pH change."
    },
    notes=(
        "Citrus nutrition is complex — per-tree rates vary hugely by age, crop load, and rootstock. "
        "Annual leaf analysis (100 spring flush leaves per block) is essential for precise nutrition. "
        "Standard targets: N 2.3-2.7%, P 0.12-0.16%, K 0.7-1.1%, Ca 3.0-5.0%, Mg 0.26-0.60%. "
        "Zimbabwe soils are typically low in Zn, Mn, and B — foliar correction is standard practice."
    ),
)

CITRUS_PLANTING_WINDOWS: List[PlantingWindow] = [
    PlantingWindow(
        region="NR I — Eastern Highlands (Chipinge, Mutare)",
        optimal_start="October 1",
        optimal_end="December 31",
        acceptable_start="September 1",
        acceptable_end="February 28",
        notes="Citrus grown at 600-1000m. HLB/psyllid risk highest here — use certified nursery trees. "
              "Excellent for mandarins and grapefruit. Frost risk above 1200m — avoid.",
    ),
    PlantingWindow(
        region="NR IIa/IIb — Highveld (Mazoe, Marondera)",
        optimal_start="October 15",
        optimal_end="December 15",
        acceptable_start="September 15",
        acceptable_end="January 31",
        notes="Moderate citrus zone. Irrigation essential during dry season (May-October). "
              "Valencia and Navel oranges perform well. Mazoe historically significant citrus area.",
    ),
    PlantingWindow(
        region="NR III-V — Lowveld (Triangle, Chiredzi, Beitbridge)",
        optimal_start="August 1",
        optimal_end="October 31",
        acceptable_start="July 15",
        acceptable_end="November 30",
        notes="Prime citrus zone — hot, irrigated. Best fruit colour development due to warm days "
              "and cool winter nights. Valencia and lemon dominate. Irrigation from save/Runde rivers. "
              "Plant early to establish before hot season peak.",
    ),
]


PROFILE = CropProfile(
    crop_name="Citrus",
    scientific_name="Citrus sinensis (orange), C. reticulata (mandarin), C. limon (lemon)",
    family="Rutaceae",

    optimal_ph=(5.5, 6.5),
    critical_ph_low=4.5,
    optimal_soil_types=[
        "Deep, well-drained sandy loams — ideal root development",
        "Red fersiallitic clays (Highveld) — fertile with good structure",
        "Alluvial soils (river valleys) — deep and fertile",
    ],
    avoid_soil_types=[
        "Poorly drained clay — Phytophthora root rot risk",
        "Shallow soils over rock — restricted root zone",
        "Saline soils — citrus is salt-sensitive",
        "Waterlogged vertisols — root asphyxiation",
    ],

    optimal_temp=(20.0, 33.0),
    critical_temp_low=-2.0,
    critical_temp_high=40.0,
    base_temp_gdd=13.0,
    total_water_mm=900.0,

    growth_stages=CITRUS_GROWTH_STAGES,
    fertilizer_schedule=CITRUS_FERTILIZER,
    diseases=CITRUS_DISEASES,
    pests=CITRUS_PESTS,
    planting_windows=CITRUS_PLANTING_WINDOWS,

    harvest_moisture="Fruit juice content minimum 35% by weight for Valencia, 33% for Navel",
    storage_conditions=(
        "3-5°C and 90-95% RH for oranges (8-12 weeks storage). "
        "Lemons: 10-13°C (3-6 months). Mandarins: 5-8°C (2-4 weeks). "
        "Ethylene degreening (1-5 ppm, 20-25°C, 24-72 hours) for early season fruit with "
        "mature internal quality but green rind. Post-harvest fungicide (TBZ or imazalil) "
        "dip within 24 hours of harvest to prevent Penicillium green/blue mould."
    ),
    post_harvest_notes=(
        "Zimbabwe citrus is exported primarily to regional markets (South Africa, Mozambique, Zambia). "
        "EU market access is constrained by CBS (Citrus Black Spot) phytosanitary requirements. "
        "Valencia (Midnight selection) is the dominant cultivar for juice and fresh market. "
        "Mazoe Rough Lemon is used primarily as rootstock, not fruit. "
        "Packhouse operations: wash, fungicide dip, wax, grade, pack in 15kg cartons."
    ),

    natural_region_suitability={
        "I": "Good — mandarins, grapefruit; HLB risk from psyllid",
        "IIa": "Moderate — requires irrigation; Mazoe citrus estates",
        "IIb": "Moderate — similar to IIa",
        "III": "Good under irrigation — Lowveld margins, warm climate suits citrus",
        "IV": "Excellent with irrigation — prime citrus zone (Triangle, Chiredzi)",
        "V": "Good with irrigation — hot climate excellent for oranges and lemons",
    },
)

ALIASES = ["orange", "oranges", "lemon", "lemons", "mandarin", "mandarins", "grapefruit"]
