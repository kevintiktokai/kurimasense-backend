"""Blueberries (Vaccinium corymbosum) — perennial export fruit crop requiring acidic soil."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List


BLUEBERRY_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Botrytis Blight (Grey Mould)",
        pathogen="Botrytis cinerea",
        pathogen_type="fungal",
        symptoms=[
            "Grey fuzzy mould on flowers, causing blossom blight",
            "Infected flowers turn brown and collapse",
            "Fruit develops soft, watery rot covered in grey sporulation",
            "Twig dieback from infected flower clusters",
        ],
        identification_markers=[
            "Distinctive grey-brown fluffy sporulation on infected tissue",
            "Infected blossoms remain attached ('mummies') serving as inoculum",
            "Fruit infection often starts at calyx end (stem scar)",
            "Sporulation visible in humid conditions, especially early morning",
        ],
        favourable_conditions={
            "humidity_min": 85, "temp_min_c": 15, "temp_max_c": 25,
            "leaf_wetness_hours": 8,
            "note": "Cool, wet, overcast weather during flowering is ideal. "
                    "Dense canopy with poor air circulation greatly increases risk."
        },
        susceptible_stages=["flowering", "fruit_ripening"],
        resistant_varieties=["Legacy (moderate tolerance)"],
        susceptible_varieties=["Most highbush varieties susceptible during flowering"],
        chemical_control=[
            {"name": "Iprodione 500 SC (Rovral)", "rate": "1.0-1.5 L/ha",
             "phi_days": "7", "notes": "Dicarboximide; apply at early bloom. Max 2 applications."},
            {"name": "Fenhexamid 500 SC (Teldor)", "rate": "1.0-1.5 L/ha",
             "phi_days": "1", "notes": "Hydroxyanilide; specific to Botrytis. Very short PHI ideal for export."},
            {"name": "Pyrimethanil 400 SC (Scala)", "rate": "1.5-2.0 L/ha",
             "phi_days": "7", "notes": "Anilinopyrimidine; different mode of action for resistance management."},
        ],
        biological_control=[
            "Bacillus amyloliquefaciens (Amylo-X) applied during flowering",
            "Trichoderma harzianum (Eco-T) for canopy colonisation to outcompete Botrytis",
            "Aureobasidium pullulans (Boni Protect) as a competitive yeast on flowers",
        ],
        cultural_control=[
            "Prune to open centre to maximise air circulation through canopy",
            "Remove mummified fruit and dead flower clusters (sanitation)",
            "Avoid overhead irrigation during flowering — use drip",
            "Harvest promptly at correct maturity to reduce post-harvest Botrytis",
            "Ensure rapid cooling post-harvest to below 2°C within 4 hours",
        ],
        economic_threshold="5% blossom blight incidence; any grey mould on fruit at harvest",
        severity_scale={
            "mild": "<5% flowers infected, no fruit symptoms",
            "moderate": "5-15% blossom blight, scattered fruit infections",
            "severe": ">15% blossom blight, significant fruit losses — expect 20-50% crop loss",
        },
    ),
    DiseaseProfile(
        name="Anthracnose Fruit Rot",
        pathogen="Colletotrichum gloeosporioides / C. acutatum",
        pathogen_type="fungal",
        symptoms=[
            "Ripe fruit develops soft, sunken lesions",
            "Orange spore masses (acervuli) in humid conditions",
            "Fruit shrivels and mummifies on bush",
            "Post-harvest fruit collapse during shipping (latent infection)",
        ],
        identification_markers=[
            "Orange to salmon-pink spore masses on infected fruit (diagnostic)",
            "Sunken lesions on ripe or near-ripe fruit",
            "Latent infections not visible until fruit ripens or during cold storage",
            "Distinguished from Botrytis by orange (not grey) sporulation",
        ],
        favourable_conditions={
            "humidity_min": 80, "temp_min_c": 22, "temp_max_c": 32,
            "note": "Warm, humid conditions during ripening. Rain splash spreads spores. "
                    "Infections initiated during green fruit stage but remain latent."
        },
        susceptible_stages=["green_fruit", "fruit_ripening", "post_harvest"],
        resistant_varieties=["Eureka Sunrise (moderate)"],
        susceptible_varieties=["Ventura", "Most southern highbush types"],
        chemical_control=[
            {"name": "Azoxystrobin 250 SC (Amistar)", "rate": "0.5-0.8 L/ha",
             "phi_days": "7", "notes": "Strobilurin; apply from petal fall. Max 3 per season."},
            {"name": "Prochloraz 450 EC", "rate": "0.5-0.75 L/ha",
             "phi_days": "7", "notes": "Imidazole; good curative activity on Colletotrichum."},
        ],
        biological_control=[
            "Bacillus subtilis (Serenade) applied from green fruit stage",
            "Trichoderma-based products for canopy application",
        ],
        cultural_control=[
            "Remove mummified fruit from bushes and ground (sanitation critical)",
            "Prune for open canopy to reduce humidity within bush",
            "Harvest frequently — don't leave overripe fruit on bush",
            "Rapid post-harvest cooling to suppress latent infections",
            "Use clean, sanitised harvest containers",
        ],
        economic_threshold="2% fruit showing symptoms at harvest (latent infections may be much higher)",
        severity_scale={
            "mild": "Occasional fruit affected, <2% at harvest",
            "moderate": "2-10% fruit loss at harvest and in cold storage",
            "severe": ">10% fruit loss, major post-harvest rots — consignment rejections",
        },
    ),
    DiseaseProfile(
        name="Phomopsis Twig Blight and Canker",
        pathogen="Phomopsis vaccinii",
        pathogen_type="fungal",
        symptoms=[
            "Flagging (wilting) of shoot tips with brown discolouration",
            "Cankers at base of infected shoots with dark brown lesion margins",
            "Infected flowers turn brown and remain attached",
            "Fruit may develop small brown spots near harvest",
        ],
        identification_markers=[
            "One-sided flagging of shoots — distinctive wilting of current season growth",
            "Dark brown cankers with sharp margin at base of wilted shoot",
            "Pycnidia (tiny black dots) on cankered bark in wet weather",
        ],
        favourable_conditions={
            "humidity_min": 80, "temp_min_c": 20, "temp_max_c": 30,
            "note": "Warm, wet spring conditions. Infection occurs through wounds and "
                    "lenticels during active growth."
        },
        susceptible_stages=["bud_break", "flowering", "shoot_growth"],
        resistant_varieties=["Legacy (moderate tolerance)"],
        susceptible_varieties=["Most highbush varieties if pruning hygiene is poor"],
        chemical_control=[
            {"name": "Captan 500 WP", "rate": "2.0-3.0 kg/ha",
             "phi_days": "14", "notes": "Protectant; apply at bud break and repeat at 14-day intervals."},
            {"name": "Copper hydroxide 500 WP", "rate": "2.0-3.0 kg/ha",
             "phi_days": "21", "notes": "Apply at leaf fall and bud break. Avoid during flowering."},
        ],
        biological_control=[
            "Trichoderma harzianum applied to pruning wounds",
            "Good overall plant nutrition to support wound healing",
        ],
        cultural_control=[
            "Prune out and burn infected shoots (cut 10 cm below visible canker)",
            "Sterilise pruning tools between cuts (70% ethanol or 10% bleach)",
            "Improve air circulation through correct pruning (open-vase system)",
            "Avoid excessive nitrogen which promotes succulent, susceptible growth",
        ],
        economic_threshold="5% of shoots showing flagging; increasing incidence of cankers",
        severity_scale={
            "mild": "Scattered flagged shoots, <5% canopy affected",
            "moderate": "5-15% canopy affected, multiple cankers per bush",
            "severe": ">15% canopy affected, significant framework damage — replanting may be needed",
        },
    ),
]


BLUEBERRY_PESTS: List[PestProfile] = [
    PestProfile(
        name="Fruit Fly (Spotted Wing Drosophila / Mediterranean Fruit Fly)",
        scientific_name="Drosophila suzukii / Ceratitis capitata",
        pest_type="insect",
        identification=[
            "D. suzukii: small (2-3 mm) vinegar fly; males have dark wing spots",
            "C. capitata: slightly larger (4-5 mm), mottled brown wings, bright colours",
            "D. suzukii females have serrated ovipositor to pierce intact fruit",
            "Larvae are small white maggots inside fruit",
        ],
        damage_symptoms=[
            "Small puncture marks on ripening fruit (oviposition sites)",
            "Fruit becomes soft, collapses, and leaks juice",
            "Secondary fungal and bacterial infections at oviposition wounds",
            "Larvae found inside fruit at harvest — phytosanitary rejection for export",
        ],
        life_cycle_notes=(
            "D. suzukii completes a generation in 8-14 days in warm conditions. "
            "Unlike other Drosophila, it attacks intact ripening fruit. C. capitata "
            "has a longer cycle (21-30 days) but wider host range. Both are quarantine "
            "pests for many export markets."
        ),
        favourable_conditions={
            "temp_min_c": 18, "temp_max_c": 28,
            "note": "Moderate temperatures, high humidity. Populations crash above 32°C. "
                    "D. suzukii prefers shaded, humid microhabitats within canopy."
        },
        susceptible_stages=["fruit_colouring", "fruit_ripening"],
        economic_threshold="Zero tolerance for export — any larvae in fruit = consignment rejection",
        chemical_control=[
            {"name": "Spinosad 240 SC (GF-120 bait)", "rate": "1.0-1.5 L/ha as bait spray",
             "phi_days": "3", "notes": "Bait formulation preferred. Very short PHI."},
            {"name": "Malathion 500 EC (bait spray)", "rate": "1.0 L/ha + protein bait",
             "phi_days": "7", "notes": "Apply as spot spray to trunk and lower canopy. Not on fruit."},
        ],
        biological_control=[
            "Mass trapping with apple cider vinegar + red wine traps",
            "Parasitoid wasps (Trichopria drosophilae, Ganaspis brasiliensis) — emerging biocontrol",
            "Entomopathogenic fungi (Beauveria bassiana) under humid conditions",
        ],
        cultural_control=[
            "Harvest promptly at correct ripeness — do not leave ripe fruit on bush",
            "Remove and destroy all fallen and overripe fruit",
            "Use exclusion netting (80-mesh) in high-value plantings",
            "Maintain open canopy to reduce humidity favoured by D. suzukii",
            "Cold treatment post-harvest (1°C for 14 days) kills larvae",
        ],
        scouting_protocol=(
            "Deploy apple cider vinegar traps at bush height from first colour change. "
            "Monitor traps twice weekly. Cut open 50 ripe fruit per block weekly to check "
            "for internal larvae. Maintain trap records for phytosanitary compliance."
        ),
    ),
    PestProfile(
        name="Scale Insects",
        scientific_name="Hemiberlesia lataniae / Aspidiotus nerii",
        pest_type="insect",
        identification=[
            "Small (1-3 mm) circular to oval, armoured scales on bark and stems",
            "Tan to grey waxy covering over insect body",
            "Crawlers (nymphs) are tiny, pale, and mobile — settle and form scale",
            "Often found on older wood, particularly in branch crotches",
        ],
        damage_symptoms=[
            "Bark encrustation reducing plant vigour",
            "Dieback of heavily infested branches",
            "Honeydew and sooty mould (soft scales only)",
            "Fruit contamination with scale — phytosanitary issue for export",
        ],
        life_cycle_notes=(
            "2-3 generations per year. Crawlers emerge from under female scale, "
            "disperse, and settle to feed. Armoured scales do not produce honeydew. "
            "Populations build up slowly on neglected bushes."
        ),
        favourable_conditions={
            "temp_min_c": 18, "temp_max_c": 30,
            "note": "Warm conditions accelerate development. Dusty conditions and "
                    "ant activity (which protect soft scales) favour build-up."
        },
        susceptible_stages=["all stages of perennial bush"],
        economic_threshold="10% of shoots with scale; any fruit contamination",
        chemical_control=[
            {"name": "Mineral oil (Budbreak / summer oil) 2%", "rate": "20 L/1000 L water",
             "phi_days": "0", "notes": "Apply at crawler emergence. Good coverage essential."},
            {"name": "Spirotetramat 240 SC (Movento)", "rate": "0.5-0.75 L/ha",
             "phi_days": "7", "notes": "Systemic; moves in phloem to reach feeding scales."},
        ],
        biological_control=[
            "Parasitoid wasps (Aphytis spp., Encarsia spp.) attack scale crawlers",
            "Ladybirds (Chilocorus spp.) feed on scale insects",
            "Avoid broad-spectrum insecticides that kill natural enemies",
        ],
        cultural_control=[
            "Prune out heavily infested branches during winter",
            "Improve air circulation to reduce favourable microclimate",
            "Control ants that protect scale from natural enemies",
            "Monitor for crawlers using double-sided sticky tape on branches",
        ],
        scouting_protocol=(
            "Inspect 20 bushes monthly, examining older wood and branch crotches. "
            "Use double-sided sticky tape on branches to detect crawler emergence. "
            "Record scale density per 10 cm of branch. Treat at crawler stage for best efficacy."
        ),
    ),
    PestProfile(
        name="Birds",
        scientific_name="Various — Pycnonotus spp. (bulbuls), Zosterops spp. (white-eyes), Quelea quelea",
        pest_type="bird",
        identification=[
            "Dark-capped bulbul: brown with dark head, yellow under-tail",
            "Cape white-eye: small, green-olive with distinctive white eye-ring",
            "Red-billed quelea: small, brown, massive flocks",
            "Damage visible as pecked, partially eaten fruit",
        ],
        damage_symptoms=[
            "Fruit pecked open and partially consumed",
            "Increased secondary rot from wounds",
            "Significant crop loss — 20-60% in unprotected plantings",
            "Droppings on remaining fruit reduce quality",
        ],
        life_cycle_notes=(
            "Bird damage is most severe as fruit turns blue (colour attraction). "
            "Frugivorous species learn quickly and return daily once a food source "
            "is identified. Quelea form flocks of thousands."
        ),
        favourable_conditions={
            "note": "Worst during ripening season when wild fruit is scarce. "
                    "Isolated plantings surrounded by bush are more vulnerable."
        },
        susceptible_stages=["fruit_colouring", "fruit_ripening"],
        economic_threshold="Any bird damage — prevention is essential",
        chemical_control=[],
        biological_control=[
            "Birds of prey (raptors) as deterrents — raptor kites or trained hawks",
        ],
        cultural_control=[
            "Bird netting is the only reliable protection (20-25 mm mesh)",
            "Install netting before fruit begins to colour",
            "Reflective tape and flash tape as temporary deterrents",
            "Auditory deterrents (gas cannons, distress calls) — birds habituate quickly",
            "Harvest promptly to reduce exposure time",
        ],
        scouting_protocol=(
            "Daily assessment of bird activity from pre-dawn. Record species and flock size. "
            "Assess damage on 50 fruit per block. Net installation should be triggered by "
            "first sighting of fruit-eating birds in orchard."
        ),
    ),
]


BLUEBERRY_GROWTH_STAGES: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Winter Dormancy & Chill Accumulation",
        stage_code="DM",
        day_range=(0, 60),
        water_kc=0.2,
        water_mm_per_week=10,
        critical_nutrients=[],
        key_activities=[
            "Winter pruning — remove dead, crossing, and unproductive wood",
            "Open centre to allow light penetration and air flow",
            "Apply dormant spray (copper + mineral oil) for disease/scale control",
            "Soil amendment with elemental sulphur if pH > 5.5",
            "Mulch with pine bark or sawdust (10-15 cm layer)",
        ],
        risks=["Insufficient chill hours (<400 for low-chill types)", "Winter drought stress on young bushes"],
        scientific_notes=(
            "Blueberries require 200-800 chill hours (below 7.2°C) depending on cultivar. "
            "Low-chill Southern Highbush types (e.g., Ventura, Eureka Sunrise) need 200-400 hours "
            "and are more suited to Zimbabwe's Eastern Highlands. Chill accumulation below 7.2°C "
            "releases dormancy-breaking hormones (gibberellins). Insufficient chill causes erratic "
            "bud break, extended flowering, and reduced yield."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Bud Break & Flowering",
        stage_code="BF",
        day_range=(61, 100),
        water_kc=0.5,
        water_mm_per_week=20,
        critical_nutrients=["Nitrogen (light)", "Boron", "Calcium"],
        key_activities=[
            "Begin irrigation as buds swell",
            "Apply first nitrogen dose — ammonium sulphate (NOT nitrate forms)",
            "Scout for Botrytis blossom blight — apply fungicide if conditions favour",
            "Ensure pollinator access (honeybees or indigenous bees)",
            "Apply foliar boron at 10% bloom for improved fruit set",
        ],
        risks=["Late frost damage to flowers", "Botrytis blossom blight", "Poor pollination in cold/wet weather"],
        scientific_notes=(
            "Blueberry flowers are urceolate (urn-shaped), requiring buzz pollination by "
            "bees that sonicate (vibrate) the flower. Honeybees are less efficient than "
            "indigenous carpenter bees or bumblebees. Cross-pollination between cultivars "
            "improves fruit size by 15-30%. Blueberries are calcifuge — use ammonium-N only "
            "as nitrate-N raises rhizosphere pH and disrupts iron uptake."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Fruit Set & Green Fruit Development",
        stage_code="GF",
        day_range=(101, 140),
        water_kc=0.7,
        water_mm_per_week=25,
        critical_nutrients=["Nitrogen", "Potassium", "Calcium"],
        key_activities=[
            "Maintain consistent irrigation — fruit sizing depends on water supply",
            "Apply second nitrogen dose",
            "Begin anthracnose fungicide programme (protect green fruit)",
            "Thin excessive fruit clusters if bush is overloaded",
            "Monitor for scale insects and fruit fly traps",
        ],
        risks=["Fruit drop from water stress", "Anthracnose latent infection", "Excessive fruit load causing small berries"],
        scientific_notes=(
            "Cell division in blueberry fruit occurs during the first 4-6 weeks after "
            "pollination; fruit size is largely determined during this phase. Calcium "
            "uptake is critical now — it cannot be remobilised later. Xylem-mobile calcium "
            "moves with transpiration stream; consistent irrigation aids uptake. "
            "Anthracnose (Colletotrichum) infections initiated now remain latent until ripening."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Fruit Colouring & Ripening",
        stage_code="FR",
        day_range=(141, 175),
        water_kc=0.85,
        water_mm_per_week=30,
        critical_nutrients=["Potassium", "Calcium"],
        key_activities=[
            "Deploy fruit fly traps and begin monitoring intensively",
            "Install bird netting before first colour change",
            "Reduce nitrogen to avoid soft fruit and poor colour",
            "Begin harvest when berries are fully blue with waxy bloom",
            "Harvest into shallow containers; avoid compression damage",
        ],
        risks=["Fruit fly infestation (quarantine pest)", "Bird damage", "Botrytis fruit rot",
               "Rain splitting"],
        scientific_notes=(
            "Anthocyanin accumulation drives the colour change from green to red to blue. "
            "This is triggered by ethylene and ABA signalling as sugar content rises (Brix 10-14). "
            "The waxy bloom (epicuticular wax) is a quality indicator — handling removes it. "
            "Potassium enhances sugar accumulation and colour development."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Harvest Period",
        stage_code="HV",
        day_range=(176, 220),
        water_kc=0.75,
        water_mm_per_week=25,
        critical_nutrients=["Potassium"],
        key_activities=[
            "Harvest every 5-7 days as berries ripen sequentially within clusters",
            "Maintain cold chain: field → pre-cooler (forced air cooling to 1°C) within 2 hours",
            "Grade and pack for export: remove soft, damaged, or overripe fruit",
            "Continue fruit fly monitoring and phytosanitary compliance",
            "Begin post-harvest potassium application for next season's bud initiation",
        ],
        risks=["Post-harvest fruit rot if cold chain breaks", "Fruit fly larvae in export consignments",
               "Over-mature fruit with poor shelf life"],
        scientific_notes=(
            "Blueberries are non-climacteric — they do not ripen further after harvest. "
            "Harvest at full blue with waxy bloom for maximum shelf life. Respiration rate "
            "drops 5-fold from 25°C to 0°C, hence the critical need for rapid cooling. "
            "Forced air cooling is preferred over hydrocooling to maintain bloom."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Post-Harvest & Vegetative Recovery",
        stage_code="PH",
        day_range=(221, 365),
        water_kc=0.5,
        water_mm_per_week=15,
        critical_nutrients=["Phosphorus", "Potassium"],
        key_activities=[
            "Apply post-harvest fertiliser (P and K focus)",
            "Maintain mulch layer — top up pine bark/sawdust",
            "Monitor soil pH — apply elemental sulphur if above 5.5",
            "Control weeds around bush base (avoid cultivation — shallow roots)",
            "Prepare for dormancy as temperatures drop",
        ],
        risks=["Insufficient reserves for next season", "Root rot in waterlogged soils"],
        scientific_notes=(
            "Flower bud initiation for the following season occurs during late summer and "
            "autumn while the bush is still in leaf. Adequate reserves of carbohydrate and "
            "nutrients at this stage directly influence next year's crop. Blueberry roots are "
            "fibrous with no root hairs — they depend on ericoid mycorrhizal fungi for nutrient "
            "uptake, particularly phosphorus. Mycorrhizal activity is favoured by acidic, "
            "organic-rich soil (hence pine bark mulch)."
        ),
    ),
]


BLUEBERRY_FERTILIZER = FertilizerSchedule(
    basal={
        "product": "Ammonium Sulphate (LAN NOT recommended — raises pH)",
        "rate": "50-100 g per bush (young) / 200-400 g per bush (mature)",
        "timing": "At bud break, split into 2-3 applications",
        "nutrients": "21% N + 24% S — acidifying effect maintains low pH",
        "note": "Never use nitrate-based fertilisers or lime near blueberries.",
    },
    top_dress_1={
        "product": "Potassium Sulphate (Sulphate of Potash)",
        "rate": "100-150 g per bush",
        "timing": "At fruit set (green fruit stage)",
        "nutrients": "50% K₂O + 18% S",
        "note": "Avoid KCl (Muriate of Potash) — blueberries are chloride-sensitive.",
    },
    top_dress_2={
        "product": "Ammonium Sulphate (second split)",
        "rate": "50-100 g per bush",
        "timing": "Post-harvest for bud initiation support",
        "nutrients": "21% N + 24% S",
        "note": "Final N application of season — do not apply after mid-autumn.",
    },
    foliar={
        "product": "Iron chelate (Fe-EDDHA) + Manganese sulphate + Zinc sulphate",
        "rate": "2 g/L Fe-EDDHA + 1 g/L MnSO₄ + 0.5 g/L ZnSO₄",
        "timing": "Monthly during active growth (spring through summer)",
        "note": "Micronutrient deficiency common in blueberries due to low pH interaction. "
                "Fe-EDDHA is the only Fe chelate stable below pH 5.",
    },
    liming=None,  # NEVER lime blueberries
    notes=(
        "Blueberries require ACIDIC soil (pH 4.5-5.5). DO NOT LIME. If pH is too high, "
        "apply elemental sulphur (200-500 kg/ha) or ferrous sulphate. Ammonium sulphate "
        "as N source helps maintain acidity. Incorporate pine bark or composted sawdust "
        "into planting holes. Ericoid mycorrhizal inoculant highly recommended at planting."
    ),
)


BLUEBERRY_PLANTING_WINDOWS: List[PlantingWindow] = [
    PlantingWindow(
        region="Eastern Highlands (NR I) — Chimanimani, Nyanga, Honde Valley edge",
        optimal_start="June 1",
        optimal_end="August 31",
        acceptable_start="May 1",
        acceptable_end="September 30",
        notes=(
            "Plant during winter dormancy for bare-root plants. Container-grown plants can be "
            "planted year-round but establish best in cool season. First crop expected year 3. "
            "Full production from year 5-6. This is the primary blueberry region in Zimbabwe."
        ),
    ),
    PlantingWindow(
        region="Highveld (NR IIa) — Harare, Marondera (substrate culture only)",
        optimal_start="June 1",
        optimal_end="August 15",
        acceptable_start="May 15",
        acceptable_end="September 15",
        notes=(
            "Marginal for soil-grown blueberries due to high soil pH. Substrate culture "
            "(coco peat + pine bark in bags/pots) allows pH control. Requires shade netting "
            "in summer. Chill accumulation may be insufficient for high-chill varieties."
        ),
    ),
]


PROFILE = CropProfile(
    crop_name="Blueberries",
    scientific_name="Vaccinium corymbosum",
    family="Ericaceae",
    optimal_ph=(4.5, 5.5),
    critical_ph_low=4.0,
    optimal_soil_types=["kaolinitic"],
    avoid_soil_types=["vertisol", "siallitic"],
    optimal_temp=(15.0, 25.0),
    critical_temp_low=-2.0,
    critical_temp_high=35.0,
    base_temp_gdd=7.0,
    total_water_mm=600.0,
    growth_stages=BLUEBERRY_GROWTH_STAGES,
    fertilizer_schedule=BLUEBERRY_FERTILIZER,
    diseases=BLUEBERRY_DISEASES,
    pests=BLUEBERRY_PESTS,
    planting_windows=BLUEBERRY_PLANTING_WINDOWS,
    harvest_moisture="Fruit harvested at 80-85% moisture; target Brix 10-14",
    storage_conditions=(
        "Forced-air cool to 0-1°C within 2 hours of harvest. Store at 0°C, 90-95% RH. "
        "Shelf life 14-21 days in optimal conditions. Modified atmosphere packaging "
        "(10-15% CO₂, 1-5% O₂) extends shelf life for sea freight export."
    ),
    post_harvest_notes=(
        "Blueberries are non-climacteric — harvest at full colour with intact bloom. "
        "Avoid wet harvesting (increases Botrytis). Grade by size (>12 mm premium), colour "
        "uniformity, and firmness. Phytosanitary inspection required for fruit fly compliance. "
        "Zimbabwe exports primarily via airfreight to EU and UK markets."
    ),
    natural_region_suitability={
        "I": "Suitable — sufficient chill, acidic soils possible, adequate rainfall",
        "IIa": "Marginal — substrate culture only, insufficient chill for high-chill types",
        "IIb": "Marginal — as IIa, with additional heat stress risk",
        "III": "Not suitable — too hot, soils too alkaline",
        "IV": "Not suitable — too hot and dry",
        "V": "Not suitable — extreme heat, no chill accumulation",
    },
)

ALIASES = ["blueberry"]
