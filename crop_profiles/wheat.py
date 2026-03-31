"""Wheat (Triticum aestivum) — Winter irrigated crop grown May-October."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List


WHEAT_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Stem Rust",
        pathogen="Puccinia graminis f. sp. tritici",
        pathogen_type="fungal",
        symptoms=[
            "Red-brown, elongated pustules on stems, leaf sheaths, and leaves",
            "Pustules rupture epidermis releasing masses of uredospores",
            "Severe infections weaken stems causing lodging",
            "Black teliospores form at end of season (black stem stage)",
        ],
        identification_markers=[
            "Pustules are brick-red and elongated (distinguish from yellow rust which is smaller/orange)",
            "Mainly on stems and leaf sheaths (not predominantly on leaf blades)",
            "Pustules rupture epidermis raggedly — feel very rough when rubbed",
            "Teliospores (black) appear late in the season under the epidermis",
        ],
        favourable_conditions={
            "humidity_min": 70, "temp_min_c": 15, "temp_max_c": 30,
            "leaf_wetness_hours": 6,
            "note": "Warmer than yellow rust. Most aggressive in late season as "
                    "temperatures rise (August-September in Zimbabwe). Ug99 race "
                    "group is a global threat with broad virulence.",
        },
        susceptible_stages=["Stem Extension", "Heading", "Grain Fill"],
        resistant_varieties=["SC Nduna", "Pan 3120"],
        susceptible_varieties=["Older varieties lacking Sr31/Sr38 resistance"],
        chemical_control=[
            {"name": "Amistar Xtra (Azoxystrobin + Cyproconazole)", "rate": "0.5 L/ha",
             "phi_days": "28", "notes": "Apply at first pustules or preventively at flag leaf"},
            {"name": "Propiconazole 250 EC", "rate": "0.5 L/ha",
             "phi_days": "21", "notes": "Systemic triazole; good curative activity"},
            {"name": "Tebuconazole 250 EW", "rate": "0.5 L/ha",
             "phi_days": "21", "notes": "Alternative triazole; rotate chemistries"},
        ],
        biological_control=[
            "Plant resistant varieties — the single most effective strategy",
            "Eradicate barberry (alternate host) — not present in Zimbabwe, but biosecurity matters",
        ],
        cultural_control=[
            "Plant resistant varieties (resistance is the backbone of rust management)",
            "Avoid very late planting (exposes heading to warmer temps that favour rust)",
            "Eliminate volunteer wheat and grass hosts between seasons",
            "Balanced nutrition — N excess promotes lush growth vulnerable to rust",
        ],
        economic_threshold="Any pustules on flag leaf or stem during heading-grain fill",
        severity_scale={
            "mild": "Scattered pustules on lower leaves and stems only",
            "moderate": "Pustules reaching flag leaf, moderate sporulation",
            "severe": "Stem and flag leaf heavily pustulated — 40-100% yield loss possible",
        },
    ),
    DiseaseProfile(
        name="Yellow (Stripe) Rust",
        pathogen="Puccinia striiformis f. sp. tritici",
        pathogen_type="fungal",
        symptoms=[
            "Yellow-orange pustules arranged in stripes along leaf veins",
            "Distinct linear pattern distinguishes from other rusts",
            "Leaf yellowing and premature senescence",
            "Severe infections reduce grain fill and test weight",
        ],
        identification_markers=[
            "Pustules in lines/stripes along veins (key diagnostic)",
            "Yellow-orange colour (lighter than stem rust)",
            "Mainly on leaf blades (not stems)",
            "Appears earlier in season than stem rust (cooler temps needed)",
        ],
        favourable_conditions={
            "humidity_min": 70, "temp_min_c": 7, "temp_max_c": 20,
            "dew_hours": 4,
            "note": "Cool, moist conditions. In Zimbabwe, appears mainly June-August "
                    "during cold season. High-altitude areas at greatest risk.",
        },
        susceptible_stages=["Tillering", "Stem Extension", "Heading"],
        resistant_varieties=["SC Nduna", "SC Select"],
        susceptible_varieties=["Some older cultivars without Yr genes"],
        chemical_control=[
            {"name": "Amistar Xtra", "rate": "0.5 L/ha",
             "phi_days": "28", "notes": "Apply at first stripes or at GS31-39 preventively"},
            {"name": "Propiconazole 250 EC", "rate": "0.5 L/ha",
             "phi_days": "21", "notes": "Good curative and protectant activity"},
        ],
        biological_control=[
            "Resistant variety deployment is the primary strategy",
            "Diversify varieties grown in a region to reduce epidemic risk",
        ],
        cultural_control=[
            "Plant resistant varieties",
            "Avoid excessively early planting in cold, high-altitude areas",
            "Destroy volunteer wheat between seasons",
            "Optimise plant population to improve air circulation",
        ],
        economic_threshold="Stripes reaching flag leaf in any proportion during heading",
        severity_scale={
            "mild": "Stripes on lower leaves only",
            "moderate": "Stripes approaching flag leaf, 10-30% leaf area affected",
            "severe": "Flag leaf and ear heavily infected — 30-60% yield loss",
        },
    ),
    DiseaseProfile(
        name="Septoria Leaf Blotch",
        pathogen="Zymoseptoria tritici (syn. Mycosphaerella graminicola)",
        pathogen_type="fungal",
        symptoms=[
            "Irregular, light tan lesions with dark brown margins on leaves",
            "Small black pycnidia (fruiting bodies) visible within lesions",
            "Premature senescence of lower leaves progressing upward",
            "Reduced green leaf area for grain fill",
        ],
        identification_markers=[
            "Tan blotches with tiny black dots (pycnidia) visible with hand lens",
            "Lesions not restricted by veins (irregular shape)",
            "Lower leaves affected first; slow upward progression",
            "Distinguished from tan spot by pycnidia presence",
        ],
        favourable_conditions={
            "humidity_min": 85, "temp_min_c": 15, "temp_max_c": 25,
            "rainfall_note": "Splash-dispersed by rain",
            "note": "Warm, wet weather with frequent rain. Survives in stubble. "
                    "Latent period is 14-21 days from infection to symptoms.",
        },
        susceptible_stages=["Tillering", "Stem Extension", "Heading"],
        resistant_varieties=["SC Nduna"],
        susceptible_varieties=["Some older cultivars"],
        chemical_control=[
            {"name": "Amistar Xtra", "rate": "0.5 L/ha",
             "phi_days": "28", "notes": "Apply preventively at GS31-39"},
            {"name": "Mancozeb 80 WP", "rate": "2.0-2.5 kg/ha",
             "phi_days": "14", "notes": "Protectant; apply in rainy spells"},
        ],
        biological_control=[
            "Trichoderma on stubble to accelerate residue decomposition",
        ],
        cultural_control=[
            "Rotate with non-cereal crops (at least 1-year break from wheat)",
            "Bury infected stubble by ploughing",
            "Plant resistant or tolerant varieties",
            "Avoid overhead irrigation during susceptible stages",
        ],
        economic_threshold="Lesions with pycnidia on leaf 3 (third from top) before heading",
        severity_scale={
            "mild": "Lower leaves affected, flag leaf clean",
            "moderate": "Leaf 2-3 affected, approaching flag leaf",
            "severe": "Flag leaf blotched — 20-40% yield loss",
        },
    ),
]


WHEAT_PESTS: List[PestProfile] = [
    PestProfile(
        name="Russian Wheat Aphid",
        scientific_name="Diuraphis noxia",
        pest_type="insect",
        identification=[
            "Small (1.5-2 mm), elongated, pale green aphid",
            "Short antennae; appears 'spindle-shaped' compared to other aphids",
            "No prominent cornicles (siphunculi) — distinguishes from other aphids",
            "Often found inside rolled leaves",
        ],
        damage_symptoms=[
            "Longitudinal rolling and tight curling of leaves (trapping aphids inside)",
            "White-yellow-purple streaking along leaf blades",
            "Stunting and prostrate growth in seedlings",
            "Awns trapped in rolled flag leaf — 'onion leaf' symptom",
            "Reduced grain fill and test weight",
        ],
        life_cycle_notes=(
            "Parthenogenetic reproduction. Generation time 10-14 days in cool "
            "weather. Injects a toxin during feeding that causes leaf rolling and "
            "chlorosis. Rolled leaves protect colonies from sprays and natural enemies. "
            "Migrates on wind over long distances."
        ),
        favourable_conditions={
            "temp_min_c": 5, "temp_max_c": 22,
            "note": "Cool, dry conditions. Most damaging during the cool winter "
                    "season (May-August in Zimbabwe). Stressed plants under "
                    "drought or nutrient deficiency are more susceptible.",
        },
        susceptible_stages=["Emergence", "Tillering", "Stem Extension", "Heading"],
        economic_threshold="10% of tillers infested with >5 aphids in rolled leaves",
        chemical_control=[
            {"name": "Imidacloprid 200 SL", "rate": "250 mL/ha",
             "phi_days": "21", "notes": "Systemic; penetrates rolled leaves to reach colonies"},
            {"name": "Dimethoate 40 EC", "rate": "500 mL/ha",
             "phi_days": "14", "notes": "Contact-systemic; good for heavy infestations"},
            {"name": "Acetamiprid 20 SP", "rate": "100 g/ha",
             "phi_days": "14", "notes": "Neonicotinoid alternative"},
        ],
        biological_control=[
            "Parasitic wasps (Diaeretiella rapae, Aphelinus spp.)",
            "Ladybird beetles (Hippodamia, Coccinella spp.)",
            "Hoverfly larvae (Syrphidae)",
            "Lacewing larvae (Chrysoperla spp.)",
        ],
        cultural_control=[
            "Plant RWA-resistant varieties where available",
            "Avoid water stress — irrigate on schedule",
            "Early planting reduces exposure to peak aphid populations",
            "Volunteer wheat control between seasons",
        ],
        scouting_protocol=(
            "Scout weekly from emergence through heading. Walk a W-pattern, examining "
            "20 tillers at 5 stops (100 tillers total). Unroll curled leaves to check "
            "for colonies inside. Record % tillers with RWA and presence of natural "
            "enemies. If >10% tillers infested and few parasitoids/predators, apply "
            "systemic insecticide. Pay special attention during cool, dry spells."
        ),
    ),
    PestProfile(
        name="Quelea Birds",
        scientific_name="Quelea quelea",
        pest_type="bird",
        identification=[
            "Small weaver bird (12-13 cm), drab brown plumage",
            "Males develop variable red/black face mask in breeding season",
            "Enormous flocks, often numbering thousands",
            "Roost in reed beds and trees near water",
        ],
        damage_symptoms=[
            "Grain stripped from heads, leaving bare rachis",
            "Entire small fields can be destroyed in a day",
            "Lodging from bird weight on mature heads",
            "Yield loss 30-100% in unprotected fields near roosts",
        ],
        life_cycle_notes=(
            "Quelea quelea is Africa's most destructive pest bird. They breed in "
            "massive colonies. Flocks target ripening cereals within flight range "
            "of roost sites. In Zimbabwe, wheat ripening in September-October may "
            "coincide with quelea movements."
        ),
        favourable_conditions={
            "note": "Fields near water and roost sites are at highest risk. "
                    "Isolated fields surrounded by bush attract less attention "
                    "than fields near large-scale cereals. Late-maturing fields "
                    "are preferentially attacked.",
        },
        susceptible_stages=["Grain Fill", "Maturity"],
        economic_threshold="Any flock presence warrants immediate bird scaring",
        chemical_control=[
            {"name": "Quelea control is a government operation", "rate": "N/A",
             "phi_days": "N/A", "notes": "Report roosts to AGRITEX or Plant Protection "
                                         "Research Institute for aerial Fenthion application"},
        ],
        biological_control=[
            "Encourage raptors near fields (preserve large trees for nesting)",
        ],
        cultural_control=[
            "Time planting so maturity avoids peak quelea activity",
            "Bird scaring (personnel, noise, reflective tape)",
            "Harvest as soon as grain reaches target moisture",
            "Coordinate with neighbours for community bird scaring",
        ],
        scouting_protocol=(
            "Monitor from soft dough stage. Watch for flock movements at dawn and "
            "dusk. Check trees and reed beds within 10 km for roost sites. If flocks "
            "are sighted, station bird-scarers in the field continuously during daylight. "
            "Report roosts of >10,000 birds to AGRITEX."
        ),
    ),
]


WHEAT_GROWTH_STAGES: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Emergence",
        stage_code="Z10-Z13",
        day_range=(0, 14),
        water_kc=0.30,
        water_mm_per_week=15,
        critical_nutrients=["P", "Zn"],
        key_activities=[
            "Plant at 3-5 cm depth into well-prepared seedbed",
            "Apply basal Compound D at planting",
            "Target 250-350 plants/m2",
            "First irrigation at planting to ensure germination",
        ],
        risks=["Poor stand establishment from uneven seedbed", "Damping-off in waterlogged conditions",
               "Bird damage to emerging seedlings"],
        scientific_notes=(
            "Wheat requires vernalisation (cold period) for floral initiation in true winter types, "
            "but most Zimbabwe varieties are spring/facultative types that do not need vernalisation. "
            "Seminal roots emerge first, followed by coleoptile emergence. Phosphorus is critical for "
            "root establishment. Optimal germination temperature is 12-20°C. Crown depth is "
            "determined by planting depth."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Tillering",
        stage_code="Z20-Z29",
        day_range=(14, 42),
        water_kc=0.45,
        water_mm_per_week=20,
        critical_nutrients=["N", "P", "K"],
        key_activities=[
            "Apply first top-dress AN at GS21-23 (3-4 tillers)",
            "Irrigate every 10-14 days depending on ET",
            "Weed control — wheat is a poor competitor at this stage",
            "Scout for aphids and early rust symptoms",
        ],
        risks=["RWA infestation during cool weather", "Weed competition", "Waterlogging from over-irrigation"],
        scientific_notes=(
            "Tillers emerge from basal nodes. Tiller number determines potential ear "
            "number and thus yield potential. Nitrogen stimulates tillering. Over-population "
            "(>400 plants/m2) reduces individual tiller vigour. The target is 500-600 ears/m2 "
            "at maturity. Phyllochron (leaf appearance rate) is driven by temperature — "
            "about 100°C-days per leaf."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Stem Extension",
        stage_code="Z30-Z39",
        day_range=(42, 65),
        water_kc=0.75,
        water_mm_per_week=30,
        critical_nutrients=["N", "K", "S"],
        key_activities=[
            "Apply second top-dress AN at GS30-32 (first node detectable)",
            "Irrigate regularly — water demand increasing",
            "Scout for rusts (yellow rust favoured by cool weather)",
            "Assess tiller survival — weakest tillers die off",
        ],
        risks=["Yellow rust epidemic", "Lodging from excess N", "Frost damage to developing ear (rare at this stage)"],
        scientific_notes=(
            "Stem extension (jointing) is rapid internode elongation driven by gibberellins. "
            "The ear is developing inside the boot (floret initiation and meiosis). Any stress "
            "during meiosis (GS33-39) reduces grain number per ear. This is the most N-responsive "
            "stage — the split application (GS21 + GS30) maximises N use efficiency and minimises "
            "lodging risk."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Heading",
        stage_code="Z50-Z59",
        day_range=(65, 80),
        water_kc=1.05,
        water_mm_per_week=45,
        critical_nutrients=["N", "K", "B"],
        key_activities=[
            "Maximum water demand — do not miss irrigation",
            "Apply fungicide if rust is present on flag leaf",
            "Scout for stem rust pustules on stems and sheaths",
            "Do NOT apply nitrogen after this stage",
        ],
        risks=["Stem rust epidemic", "Heat stress causing floret sterility",
               "Water stress reducing grain number"],
        scientific_notes=(
            "Heading is ear emergence from the boot (flag leaf sheath). Anthesis (pollination) "
            "occurs 3-5 days after heading. Wheat is self-pollinating. Temperatures >30°C during "
            "anthesis reduce pollen viability and grain set. The flag leaf contributes ~50% of "
            "photosynthate for grain fill — protecting it from disease is critical. Fungicide "
            "at flag leaf (GS39-55) is the single most yield-responsive spray timing."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Grain Fill",
        stage_code="Z60-Z79",
        day_range=(80, 105),
        water_kc=0.85,
        water_mm_per_week=40,
        critical_nutrients=["N (remobilisation)", "K"],
        key_activities=[
            "Maintain irrigation schedule through mid-grain fill",
            "Last irrigation at soft dough stage (GS75-77)",
            "Scout for stem rust (warmer temperatures now)",
            "Prepare harvesting equipment",
        ],
        risks=["Stem rust (temperatures rising in Sept-Oct)", "Heat stress shortening grain fill",
               "Bird damage from quelea"],
        scientific_notes=(
            "Grain fill consists of lag phase (cell division in endosperm), linear fill "
            "(starch deposition), and maturation (desiccation). Thousand-grain weight is "
            "determined during this phase. Heat stress (>30°C) shortens the fill period, "
            "reducing individual grain weight. Nitrogen remobilisation from leaves and stems "
            "to grain contributes 60-80% of grain protein. Final irrigation should be at "
            "soft-medium dough to allow field drying."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Maturity",
        stage_code="Z80-Z92",
        day_range=(105, 130),
        water_kc=0.25,
        water_mm_per_week=0,
        critical_nutrients=[],
        key_activities=[
            "Stop irrigation at hard dough (GS87)",
            "Harvest when grain moisture is 12-13%",
            "Combine harvester settings: minimise cracking",
            "Deliver to GMB or millers promptly",
        ],
        risks=["Shattering losses from delayed harvest", "Rain on mature crop (sprouting risk)",
               "Quality downgrade from weathering"],
        scientific_notes=(
            "Physiological maturity is reached when maximum dry weight is achieved and "
            "the peduncle turns golden. Grain moisture at PM is ~35%. Field drying to "
            "12-13% for safe storage takes 1-2 weeks in Zimbabwe's dry winter conditions. "
            "Pre-harvest sprouting (from late rains) degrades milling quality by activating "
            "alpha-amylase. Falling number test measures sprout damage."
        ),
    ),
]


WHEAT_FERT = FertilizerSchedule(
    basal={
        "product": "Compound D (7:14:7)",
        "rate_kg_ha": 300,
        "timing": "At planting",
        "placement": "Drill with seed or band 5 cm below seed row",
        "nutrients_supplied": {"N": 21, "P2O5": 42, "K2O": 21},
        "notes": "Phosphorus is the most critical basal nutrient for wheat root establishment. "
                 "On very P-deficient soils, supplement with SSP (Single Super Phosphate) at 100 kg/ha.",
    },
    top_dress_1={
        "product": "Ammonium Nitrate (AN 34.5%N)",
        "rate_kg_ha": 150,
        "timing": "GS21-23 (3-4 tillers, ~3 weeks after emergence)",
        "placement": "Broadcast and irrigate in",
        "nutrients_supplied": {"N": 51.75},
        "notes": "First N split drives tillering. Apply before irrigation for soil incorporation.",
    },
    top_dress_2={
        "product": "Ammonium Nitrate (AN 34.5%N)",
        "rate_kg_ha": 150,
        "timing": "GS30-32 (first node detectable, ~6-7 weeks)",
        "placement": "Broadcast and irrigate in",
        "nutrients_supplied": {"N": 51.75},
        "notes": "Second N split supports stem extension and ear development. "
                 "Total N target: 120-180 kg/ha depending on yield target. "
                 "Do NOT apply N after heading.",
    },
    foliar={
        "product": "Urea (46%N) foliar",
        "rate_kg_ha": "10 kg urea in 200L water/ha",
        "timing": "GS39-55 (flag leaf to heading)",
        "notes": "Optional foliar N to boost grain protein for bread wheat grade. "
                 "Apply in cool conditions (late afternoon) to avoid leaf scorch.",
    },
    liming={
        "product": "Calcitic or dolomitic lime",
        "rate_kg_ha": "As per soil test, typically 1000-2000 kg/ha",
        "timing": "Apply in summer before winter wheat planting",
        "notes": "Wheat requires pH 6.0-7.0. Most Highveld soils need liming for wheat. "
                 "Lime also supplies Ca needed for grain quality.",
    },
    notes=(
        "Total N should be 120-180 kg/ha for 5-7 t/ha yield target under irrigation. "
        "Split application (basal + 2 top-dresses) is standard. Sulphur deficiency is "
        "common on sandy Highveld soils — supplement with gypsum 200 kg/ha or use AN "
        "with S (e.g., Ammonium Sulphate Nitrate). Zinc deficiency may occur on alkaline soils."
    ),
)


WHEAT_PLANTING_WINDOWS: List[PlantingWindow] = [
    PlantingWindow(
        region="NR I (Eastern Highlands)",
        optimal_start="May 10",
        optimal_end="June 10",
        acceptable_start="May 1",
        acceptable_end="June 20",
        notes="Cool temperatures favour wheat. Irrigation usually available from dams. "
              "Risk of frost during tillering — avoid very early planting.",
    ),
    PlantingWindow(
        region="NR II (Mashonaland/Highveld)",
        optimal_start="May 15",
        optimal_end="June 15",
        acceptable_start="May 1",
        acceptable_end="June 30",
        notes="Main wheat production zone. Irrigated from dams and boreholes. "
              "Late planting risks heat stress during grain fill (October).",
    ),
    PlantingWindow(
        region="NR III (Semi-intensive)",
        optimal_start="May 15",
        optimal_end="June 10",
        acceptable_start="May 5",
        acceptable_end="June 20",
        notes="Wheat under irrigation only. Water availability may limit area planted.",
    ),
    PlantingWindow(
        region="NR IV (Semi-extensive)",
        optimal_start="May 10",
        optimal_end="June 5",
        acceptable_start="May 1",
        acceptable_end="June 15",
        notes="Only under irrigation. Limited area — water is scarce. "
              "Early planting preferred to avoid October heat.",
    ),
    PlantingWindow(
        region="NR V (Lowveld)",
        optimal_start="May 1",
        optimal_end="May 30",
        acceptable_start="April 25",
        acceptable_end="June 10",
        notes="Irrigated wheat at Triangle, Hippo Valley. Plant early — "
              "lowveld heat accelerates development and shortens grain fill. "
              "Harvest before October heat peaks.",
    ),
]


PROFILE = CropProfile(
    crop_name="Wheat",
    scientific_name="Triticum aestivum",
    family="Poaceae",
    optimal_ph=(6.0, 7.0),
    critical_ph_low=5.0,
    optimal_soil_types=["fersiallitic", "siallitic", "vertisol"],
    avoid_soil_types=["waterlogged", "very sandy (low water holding capacity)", "saline"],
    optimal_temp=(15.0, 25.0),
    critical_temp_low=2.0,
    critical_temp_high=32.0,
    base_temp_gdd=4.0,
    total_water_mm=400.0,
    growth_stages=WHEAT_GROWTH_STAGES,
    fertilizer_schedule=WHEAT_FERT,
    diseases=WHEAT_DISEASES,
    pests=WHEAT_PESTS,
    planting_windows=WHEAT_PLANTING_WINDOWS,
    harvest_moisture="12-13% grain moisture. Test with moisture meter before combining.",
    storage_conditions="Store at <13% moisture in clean, dry silos or bags. "
                       "Fumigate with phosphine if weevils detected. "
                       "Monitor temperature — heating indicates insect activity or mould.",
    post_harvest_notes="Combine at 12-13% moisture. Minimise cracking by adjusting cylinder speed. "
                       "Grade by hectolitre weight, protein content, falling number, and moisture. "
                       "Zimbabwe bread wheat should have >11.5% protein for baking quality. "
                       "Deliver to Grain Marketing Board or private millers.",
    natural_region_suitability={
        "NR I": "Well suited under irrigation — cool temperatures ideal",
        "NR II": "Primary production zone — irrigated Highveld farms",
        "NR III": "Suitable under irrigation where water is available",
        "NR IV": "Limited by water availability — irrigation essential",
        "NR V": "Irrigated estates (Triangle, Hippo Valley) — plant early to avoid heat",
    },
)

ALIASES: list = []
