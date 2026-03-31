"""Paprika (Capsicum annuum) — Export cash crop grown for dried red pods in Zimbabwe."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List


PAPRIKA_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Bacterial Wilt",
        pathogen="Ralstonia solanacearum",
        pathogen_type="bacterial",
        symptoms=[
            "Rapid, permanent wilting of entire plant without prior yellowing",
            "Leaves remain green on wilted plants (distinguishes from Fusarium)",
            "Brown discolouration of vascular tissue in lower stem",
            "Bacterial ooze streams from cut stem when placed in water",
        ],
        identification_markers=[
            "Cut stem placed in clear water produces milky bacterial streaming within 2-3 minutes",
            "Green wilting (no leaf yellowing) is key differentiator from fungal wilts",
            "Brown vascular ring visible in stem cross-section",
            "Plants wilt during heat of day, may partially recover at night initially",
        ],
        favourable_conditions={
            "soil_temp_min_c": 25, "soil_temp_max_c": 37,
            "soil_moisture": "Waterlogged or poorly drained",
            "note": "Hot, wet conditions. Pathogen enters through root wounds. "
                    "Survives in soil for years without host. Spread by contaminated water and tools."
        },
        susceptible_stages=["Transplant establishment", "Vegetative growth", "Flowering"],
        resistant_varieties=[],
        susceptible_varieties=["PRI Paprika", "Serrano Hot Chilli"],
        chemical_control=[
            {"name": "No effective chemical control", "rate": "N/A",
             "phi_days": "N/A", "notes": "No registered bactericides are effective against R. solanacearum in soil"},
        ],
        biological_control=[
            "Bacillus amyloliquefaciens soil drenches reduce inoculum levels",
            "Trichoderma harzianum in planting holes enhances root defence",
            "Bacteriophage-based products under research for Zimbabwe conditions",
        ],
        cultural_control=[
            "Rotate with non-solanaceous crops for minimum 3-4 years",
            "Plant on raised beds to improve drainage and reduce waterlogging",
            "Sterilise pruning tools between plants (10% bleach solution)",
            "Remove and burn infected plants immediately with surrounding soil",
            "Avoid fields with known bacterial wilt history",
            "Use clean transplants from certified nurseries",
        ],
        economic_threshold="Any confirmed plant — remove immediately, quarantine surrounding 2 m radius",
        severity_scale={
            "mild": "< 5% plants wilted, isolated cases",
            "moderate": "5-20% plants lost, spreading in patches",
            "severe": "> 20% plant mortality — consider replanting to alternative crop",
        },
    ),
    DiseaseProfile(
        name="Phytophthora Blight",
        pathogen="Phytophthora capsici",
        pathogen_type="oomycete",
        symptoms=[
            "Dark, water-soaked lesions at stem base (collar rot)",
            "Rapid plant collapse — whole plant turns brown and dies within days",
            "Fruit develop dark, sunken, water-soaked lesions with white mould",
            "Root rot causes plant to pull out easily from soil",
        ],
        identification_markers=[
            "Dark brown to black collar rot at soil line",
            "White sporulation on fruit lesions under humid conditions",
            "Rapid plant death distinguishes from slower bacterial wilt",
            "Entire sections of rows affected following water flow patterns",
        ],
        favourable_conditions={
            "humidity_min": 90, "temp_min_c": 20, "temp_max_c": 30,
            "note": "Saturated soils after heavy rain. Spreads via zoospores in surface water. "
                    "Worse in low-lying areas and furrow-irrigated fields."
        },
        susceptible_stages=["Transplant establishment", "Vegetative growth", "Fruiting"],
        resistant_varieties=[],
        susceptible_varieties=["PRI Paprika"],
        chemical_control=[
            {"name": "Metalaxyl + Mancozeb (Ridomil Gold MZ 68 WG)", "rate": "2.5 kg/ha",
             "phi_days": "14", "notes": "Soil drench at planting and after heavy rains"},
            {"name": "Fosetyl-aluminium (Aliette 80 WG)", "rate": "2.5 kg/ha",
             "phi_days": "14", "notes": "Systemic; stimulates plant defence response"},
            {"name": "Copper hydroxide 77 WP", "rate": "2.0-2.5 kg/ha",
             "phi_days": "7", "notes": "Protectant on fruit and foliage; apply before rains"},
        ],
        biological_control=[
            "Trichoderma harzianum soil incorporation before transplanting",
            "Bacillus subtilis (Serenade) as preventative soil drench",
        ],
        cultural_control=[
            "Plant on raised beds (20-30 cm) for drainage",
            "Avoid furrow irrigation; use drip irrigation",
            "Do not plant in low-lying or waterlogged areas",
            "Rotate with non-solanaceous crops for 3+ years",
            "Incorporate organic matter to improve soil structure and drainage",
            "Remove and destroy infected plants with surrounding soil",
        ],
        economic_threshold="First confirmed collar rot symptoms — treat immediately",
        severity_scale={
            "mild": "Isolated collar rot, < 5% plants affected",
            "moderate": "10-30% plants lost in patches, especially low areas",
            "severe": "> 30% field loss — economic production unlikely",
        },
    ),
    DiseaseProfile(
        name="Powdery Mildew",
        pathogen="Leveillula taurica",
        pathogen_type="fungal",
        symptoms=[
            "Diffuse, pale yellow spots on upper leaf surface",
            "White powdery sporulation on lower leaf surface (unlike typical powdery mildews)",
            "Leaves become chlorotic and drop prematurely",
            "Defoliation exposes fruit to sunscald",
        ],
        identification_markers=[
            "Sporulation predominantly on abaxial (lower) leaf surface — unusual for powdery mildew",
            "Yellow blotches on upper surface correspond to sporulation below",
            "Distinct from Podosphaera which sporulates on upper surface",
        ],
        favourable_conditions={
            "humidity_min": 40, "humidity_max": 70,
            "temp_min_c": 20, "temp_max_c": 30,
            "note": "Warm, dry conditions with moderate humidity. Common in NR III-V. "
                    "Endophytic pathogen — infection occurs inside leaf tissue."
        },
        susceptible_stages=["Flowering", "Fruiting", "Late vegetative"],
        resistant_varieties=[],
        susceptible_varieties=["PRI Paprika", "Serrano Hot Chilli"],
        chemical_control=[
            {"name": "Sulphur 80 WP", "rate": "3.0 kg/ha",
             "phi_days": "1", "notes": "Protectant; do not apply above 35°C"},
            {"name": "Myclobutanil 200 EW", "rate": "0.3 L/ha",
             "phi_days": "7", "notes": "Systemic triazole with curative activity"},
        ],
        biological_control=[
            "Potassium bicarbonate (3-5 g/L) disrupts fungal spore germination",
            "Neem oil (0.5-1%) has some inhibitory effect",
        ],
        cultural_control=[
            "Adequate plant spacing for air circulation",
            "Avoid water stress which predisposes plants",
            "Remove and destroy heavily infected lower leaves",
            "Balanced nutrition — avoid excess nitrogen",
        ],
        economic_threshold="15% leaf area affected before peak fruiting",
        severity_scale={
            "mild": "< 15% leaf area, lower canopy",
            "moderate": "15-40% defoliation, some sunscald risk",
            "severe": "> 40% defoliation, significant sunscald — 30-50% quality loss",
        },
    ),
]

PAPRIKA_PESTS: List[PestProfile] = [
    PestProfile(
        name="Aphids",
        scientific_name="Myzus persicae",
        pest_type="insect",
        identification=[
            "Small (1.5-2 mm), green to yellow-green, soft-bodied insects",
            "Found on undersides of young leaves and growing tips",
            "Winged and wingless forms; cornicles (tail pipes) visible under magnification",
            "Often attended by ants which farm them for honeydew",
        ],
        damage_symptoms=[
            "Leaf curling and distortion, especially on young growth",
            "Honeydew excretion leads to sooty mould on leaves and pods",
            "Vector for Tobacco Mosaic Virus (TMV) and Potato Virus Y (PVY)",
            "Stunted growth and reduced pod production",
        ],
        life_cycle_notes=(
            "Continuous parthenogenetic reproduction in Zimbabwe's warm climate. "
            "One female produces 50-100 nymphs over 3-4 weeks. Generation time 7-10 days "
            "at 25°C. Winged forms migrate to new fields, especially in spring. "
            "Natural enemies can suppress populations if broad-spectrum insecticides are avoided."
        ),
        favourable_conditions={
            "temp_min_c": 18, "temp_max_c": 28,
            "note": "Warm, dry conditions. Excessive nitrogen creates lush growth attractive to aphids. "
                    "Populations crash during heavy rains."
        },
        susceptible_stages=["Seedling (nursery)", "Transplant establishment", "Vegetative growth", "Flowering"],
        economic_threshold="25% of plants with > 20 aphids on youngest leaves; or virus symptoms on 2% of plants",
        chemical_control=[
            {"name": "Pirimicarb 50 WG (Pirimor)", "rate": "0.5 g/L",
             "phi_days": "3", "notes": "Selective aphicide; preserves natural enemies"},
            {"name": "Acetamiprid 20 SP", "rate": "0.2 g/L",
             "phi_days": "7", "notes": "Systemic neonicotinoid; translaminar activity"},
            {"name": "Thiamethoxam 25 WG (Actara)", "rate": "0.2 g/L",
             "phi_days": "14", "notes": "Drench at transplanting for 4-6 weeks protection"},
        ],
        biological_control=[
            "Ladybird beetles (Cheilomenes spp.) — each larva eats 200+ aphids before pupation",
            "Lacewing larvae (Chrysoperla spp.) are effective generalist predators",
            "Parasitoid wasp Aphidius colemani — mummified aphids indicate parasitism",
            "Beauveria bassiana sprays under humid conditions",
        ],
        cultural_control=[
            "Use reflective silver mulch to repel winged aphids",
            "Establish nursery seedbeds under fine netting (0.3 mm mesh)",
            "Avoid excessive nitrogen fertilisation",
            "Remove weed hosts (especially solanaceous weeds) around fields",
            "Interplant with basil or marigold as repellent trap crops",
        ],
        scouting_protocol=(
            "Scout twice weekly. Examine 10 plants at each of 5 points per field. "
            "Check undersides of 3 youngest fully expanded leaves per plant. "
            "Record number per leaf and presence of natural enemies. "
            "Note any virus symptoms (mosaic, stunting, leaf curl) which indicate aphid-borne viruses."
        ),
    ),
    PestProfile(
        name="Fruit Borer (African Bollworm)",
        scientific_name="Helicoverpa armigera",
        pest_type="insect",
        identification=[
            "Eggs: spherical, ribbed, 0.5 mm, laid singly on flowers and young pods",
            "Larvae: variable colour (green, brown, pink), up to 40 mm, dark lateral stripes",
            "Adults: stout, brown moths, 35-40 mm wingspan, fly at dusk",
            "Pupae: brown, 15-20 mm, found in soil at 5-10 cm depth",
        ],
        damage_symptoms=[
            "Larvae bore into developing pods, feeding on seeds and placenta",
            "Entry holes with dark frass (excrement) visible on pod surface",
            "Pods rot secondarily from pathogen entry through borer holes",
            "Single larva can destroy 5-10 pods before pupation",
        ],
        life_cycle_notes=(
            "Moths lay 500-1500 eggs over 2-3 weeks, singly on reproductive structures. "
            "Eggs hatch in 3-5 days. Larval development: 14-21 days through 6 instars. "
            "Pupation in soil for 10-14 days (longer in cool conditions). "
            "3-4 generations per season in Zimbabwe. Highly polyphagous — also attacks tomato, "
            "cotton, maize. Peak moth flights October-December and February-March."
        ),
        favourable_conditions={
            "temp_min_c": 20, "temp_max_c": 35,
            "note": "Warm nights favour moth flight and oviposition. Irrigated fields attract moths. "
                    "Previous host crops (cotton, tomato) nearby increase pressure."
        },
        susceptible_stages=["Flowering", "Fruit development", "Pod maturation"],
        economic_threshold="1 egg or larva per 5 plants, or 5% pods with bore holes",
        chemical_control=[
            {"name": "Indoxacarb 150 SC (Steward)", "rate": "0.4-0.5 mL/L",
             "phi_days": "7", "notes": "Targets young larvae; low impact on natural enemies"},
            {"name": "Emamectin benzoate 5 SG", "rate": "0.4 g/L",
             "phi_days": "7", "notes": "Highly effective; apply in evening when larvae are active"},
            {"name": "Lambda-cyhalothrin 50 EC", "rate": "0.3 mL/L",
             "phi_days": "14", "notes": "Broad-spectrum pyrethroid; may flare aphids and mites"},
        ],
        biological_control=[
            "Bacillus thuringiensis var. kurstaki (Bt) at 1.0-1.5 kg/ha — targets young larvae only",
            "Nuclear polyhedrosis virus (HaNPV) specific to Helicoverpa",
            "Trichogramma egg parasitoids — release at 50,000 per hectare at flowering",
            "Encourage predatory wasps, lacewings, and birds",
        ],
        cultural_control=[
            "Monitor moth activity with pheromone traps (1 per 2 ha)",
            "Intercrop with sorghum or maize as trap crop for oviposition",
            "Deep ploughing after harvest to destroy pupae",
            "Hand-pick and destroy large larvae during scouting (small fields)",
            "Remove alternate hosts (weeds) around field borders",
        ],
        scouting_protocol=(
            "Deploy Helicoverpa pheromone traps at 1 per 2 ha from pre-flowering. "
            "When trap catches exceed 10 moths per trap per night, begin field scouting. "
            "Examine 20 plants at 5 points per field. Check flowers and young pods for "
            "eggs (use hand lens) and small larvae. Scout early morning when larvae are "
            "on plant surface. Record eggs, larvae (by size), and damaged pods separately."
        ),
    ),
    PestProfile(
        name="Red Spider Mite",
        scientific_name="Tetranychus urticae",
        pest_type="mite",
        identification=[
            "Very small (< 0.5 mm), oval, yellowish-green to red with two dark spots",
            "Fine webbing visible on leaf undersides in heavy infestations",
            "Eggs: spherical, translucent, laid in clusters on leaf undersides",
            "Use 10x hand lens for reliable identification",
        ],
        damage_symptoms=[
            "Fine white/yellow stippling on upper leaf surface from cell puncturing",
            "Leaves become bronzed and dry; severe cases cause defoliation",
            "Webbing covers leaf surface, interfering with photosynthesis",
            "Pods may show russeting and reduced colour development",
        ],
        life_cycle_notes=(
            "Eggs hatch in 3-5 days. Nymphal stages: 5-7 days. "
            "Generation time as short as 8-12 days at 30°C. "
            "Populations can explode from 10 to 10,000 per plant in 3 weeks. "
            "Broad-spectrum insecticides kill natural enemies and cause mite resurgence."
        ),
        favourable_conditions={
            "temp_min_c": 25, "temp_max_c": 38,
            "humidity_max": 60,
            "note": "Hot, dry, dusty conditions. Often flares after pyrethroid applications "
                    "which kill predatory mites. Water stress increases plant susceptibility."
        },
        susceptible_stages=["Vegetative growth", "Flowering", "Fruiting"],
        economic_threshold="30% of leaves with stippling, or 5 mites per leaf (use hand lens)",
        chemical_control=[
            {"name": "Abamectin 18 EC", "rate": "0.3-0.5 mL/L",
             "phi_days": "7", "notes": "Specific acaricide; low impact on predatory mites"},
            {"name": "Spiromesifen 240 SC (Oberon)", "rate": "0.5 mL/L",
             "phi_days": "7", "notes": "Inhibits lipid biosynthesis; effective on all stages"},
        ],
        biological_control=[
            "Predatory mite Phytoseiulus persimilis — 1:10 predator:prey ratio",
            "Stethorus beetle (ladybird) — specialist mite feeder",
            "Avoid broad-spectrum insecticides that kill predatory mites",
        ],
        cultural_control=[
            "Overhead irrigation or misting raises humidity and suppresses mites",
            "Reduce dust by vegetating field borders and access roads",
            "Avoid water stress — irrigate consistently",
            "Remove heavily infested plants to reduce source population",
            "Avoid pyrethroid insecticides that cause mite outbreaks",
        ],
        scouting_protocol=(
            "Check leaf undersides of lower and mid-canopy leaves with a 10x hand lens. "
            "Sample 5 leaves from each of 10 plants per monitoring point. "
            "Look for stippling, webbing, and live mites. Scout weekly in cool weather, "
            "twice weekly when temperatures exceed 30°C. "
            "Note presence of predatory mites (move faster, pear-shaped)."
        ),
    ),
]

PAPRIKA_GROWTH_STAGES: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Nursery & Seedling",
        stage_code="NS",
        day_range=(0, 35),
        water_kc=0.35,
        water_mm_per_week=12,
        critical_nutrients=["Phosphorus", "Nitrogen"],
        key_activities=[
            "Sow seed in raised seedbeds or seedling trays (200-cell)",
            "Use sterilised growing media to prevent damping-off",
            "Provide 50% shade for first 14 days, then harden off",
            "Apply starter fertiliser (liquid 2:3:2 at 2 mL/L weekly)",
            "Transplant at 6-8 true leaf stage (35-42 days)",
        ],
        risks=[
            "Damping-off (Pythium, Rhizoctonia) in overwatered seedbeds",
            "Aphid infestation and virus transmission in nursery",
            "Leggy, weak transplants from insufficient light or overcrowding",
            "Root-bound seedlings from delayed transplanting",
        ],
        scientific_notes=(
            "Capsicum annuum seed germinates optimally at 25-30°C soil temperature. "
            "Germination is epigeal; cotyledons emerge in 7-14 days. Seedling phase is "
            "characterised by slow growth and high sensitivity to environmental stress. "
            "Phosphorus is critical for root development in the confined seedling tray environment. "
            "Hardening off for 7-10 days before transplanting reduces transplant shock mortality."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Transplanting & Establishment",
        stage_code="TE",
        day_range=(35, 55),
        water_kc=0.45,
        water_mm_per_week=18,
        critical_nutrients=["Phosphorus", "Nitrogen", "Calcium"],
        key_activities=[
            "Transplant into well-prepared beds at 0.9-1.0 m x 0.4-0.5 m spacing",
            "Apply basal fertiliser in planting holes before transplanting",
            "Water immediately after transplanting and for 3 consecutive days",
            "Mulch around plants to conserve moisture and suppress weeds",
            "Apply Metalaxyl drench for Phytophthora protection",
        ],
        risks=[
            "Transplant shock and mortality in hot, windy conditions",
            "Cutworm damage to newly transplanted seedlings",
            "Bacterial wilt infection through root wounds",
            "Waterlogging in poorly drained soils",
        ],
        scientific_notes=(
            "Transplant shock involves disruption of root-shoot hydraulic continuity. "
            "Recovery depends on rapid adventitious root regeneration, which requires "
            "adequate soil moisture, phosphorus, and calcium for cell wall formation. "
            "Transplanting in late afternoon reduces evapotranspiration stress. "
            "Establishment is confirmed when new leaves unfurl (typically 7-14 days post-transplant)."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Vegetative Growth",
        stage_code="VG",
        day_range=(55, 90),
        water_kc=0.70,
        water_mm_per_week=28,
        critical_nutrients=["Nitrogen", "Potassium", "Magnesium"],
        key_activities=[
            "Apply first top-dress of AN at 200 kg/ha (side-dress)",
            "Cultivate or mulch for weed control",
            "Scout for aphids and spider mites weekly",
            "Stake or trellis plants if variety is tall",
            "Begin powdery mildew preventive programme",
        ],
        risks=[
            "Excessive vegetative growth from too much nitrogen delays flowering",
            "Aphid build-up and virus transmission",
            "Bacterial wilt incidence increases in warm, wet soils",
            "Red spider mite flare in hot, dry weather",
        ],
        scientific_notes=(
            "Capsicum annuum exhibits dichotomous branching at each node after the first "
            "fork (crown). Canopy architecture determines light interception and ultimately "
            "yield potential. Nitrogen drives leaf area expansion but excess promotes apical "
            "dominance over reproductive initiation. Potassium is essential for stomatal "
            "regulation and the osmotic adjustment needed in Zimbabwe's hot climate."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Flowering & Fruit Set",
        stage_code="FL",
        day_range=(90, 120),
        water_kc=0.95,
        water_mm_per_week=35,
        critical_nutrients=["Potassium", "Boron", "Calcium"],
        key_activities=[
            "Reduce nitrogen; increase potassium for fruit quality",
            "Apply foliar boron (Solubor 1 g/L) at first flowering",
            "Deploy Helicoverpa pheromone traps",
            "Maintain consistent irrigation — water stress causes flower drop",
            "Continue fungicide programme for powdery mildew",
        ],
        risks=[
            "Flower drop from temperatures above 35°C or below 15°C",
            "Blossom end rot from calcium deficiency or irregular irrigation",
            "Bollworm (Helicoverpa) oviposition on flowers",
            "Excessive fruit set exhausts plant — may need thinning",
        ],
        scientific_notes=(
            "Paprika is self-pollinating; flowers are complete with both androecium and "
            "gynoecium. Pollen viability drops above 35°C (heat-induced pollen sterility). "
            "Fruit set requires successful fertilisation and adequate auxin-gibberellin "
            "signalling for ovary expansion. Boron deficiency causes thick, cracked fruit walls "
            "and hollow pods. The capsaicin biosynthesis pathway activates during early fruit "
            "development — environmental stress at this stage affects pungency and colour."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Fruit Development & Ripening",
        stage_code="FD",
        day_range=(120, 160),
        water_kc=0.85,
        water_mm_per_week=32,
        critical_nutrients=["Potassium", "Calcium"],
        key_activities=[
            "Apply second top-dress of KCl or AN+KCl blend",
            "Intensify bollworm scouting and management",
            "Maintain fungicide programme to protect canopy",
            "Begin phased harvesting of ripe red pods",
            "Prepare drying racks or tunnels for post-harvest",
        ],
        risks=[
            "Bollworm boring into ripening pods",
            "Fruit rot from rain splash and soil contact",
            "Sunscald on exposed pods after defoliation",
            "Colour degradation from excessive rain during ripening",
        ],
        scientific_notes=(
            "Capsanthin and capsorubin (ketocarotenoids) are responsible for the red colour "
            "valued in export paprika. Their biosynthesis peaks at full ripeness via the "
            "carotenoid pathway. ASTA colour value (target > 120 for export grade) correlates "
            "with carotenoid concentration. Potassium enhances colour intensity and dry matter "
            "accumulation. Rain during ripening leaches pigments and promotes Botrytis pod rot."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Harvest & Drying",
        stage_code="HD",
        day_range=(160, 180),
        water_kc=0.55,
        water_mm_per_week=18,
        critical_nutrients=["Potassium"],
        key_activities=[
            "Harvest fully red, ripe pods at regular 7-10 day intervals",
            "Remove entire pod with calyx attached",
            "Dry on raised racks in solar tunnels or mechanical dryers at 55-65°C",
            "Target moisture content < 12% for safe storage",
            "Grade by colour (ASTA value), size, and defects",
        ],
        risks=[
            "Over-drying degrades colour pigments",
            "Mould development if dried too slowly or stored damp",
            "Aflatoxin contamination in improperly dried pods",
            "Loss of ASTA colour value from UV exposure during sun-drying",
        ],
        scientific_notes=(
            "Optimal drying temperature is 55-65°C; above 70°C, capsanthin degrades "
            "irreversibly. Sun-drying on ground mats causes 20-30% ASTA loss compared to "
            "solar tunnel drying. Target moisture < 12% ensures safe storage without mould. "
            "Export-grade paprika requires ASTA > 120, moisture < 11%, and aflatoxin < 10 ppb. "
            "Zimbabwe paprika competes with Spanish and Hungarian grades on world markets."
        ),
    ),
]

PAPRIKA_FERTILIZER = FertilizerSchedule(
    basal={
        "product": "Compound C (5-15-12) or Compound S (7-21-8)",
        "rate_kg_ha": 400,
        "timing": "Incorporated into planting holes/beds 3-5 days before transplanting",
        "nutrients_supplied": {"N": 20, "P": 60, "K": 48},
        "notes": "High P and K for root establishment and early fruit quality. "
                 "Mix with well-composted manure at 10-15 t/ha if available.",
    },
    top_dress_1={
        "product": "Ammonium Nitrate (AN 34.5%)",
        "rate_kg_ha": 250,
        "timing": "3-4 weeks after transplanting (start of active vegetative growth)",
        "nutrients_supplied": {"N": 86},
        "notes": "Side-dress 10 cm from stem. Irrigate immediately. "
                 "Avoid contact with foliage to prevent scorch.",
    },
    top_dress_2={
        "product": "Ammonium Nitrate (AN 34.5%) + Muriate of Potash (KCl 60%)",
        "rate_kg_ha": "AN 150 + KCl 100",
        "timing": "At first fruit set (90-100 days)",
        "nutrients_supplied": {"N": 52, "K": 60},
        "notes": "Potassium critical for pod colour development and dry matter. "
                 "Excessive nitrogen at this stage reduces ASTA colour value.",
    },
    foliar={
        "product": "Solubor + Calcium Nitrate",
        "rate": "Solubor 1 g/L + CaNO3 5 g/L",
        "timing": "At flowering and every 14 days during fruit development",
        "notes": "Boron for fruit set, calcium for blossom end rot prevention. "
                 "Spray in early morning or late afternoon.",
    },
    liming={
        "product": "Dolomitic lime",
        "rate_kg_ha": "1000-2000 based on soil test",
        "timing": "6-8 weeks before transplanting",
        "target_ph": "6.0-7.0",
        "notes": "Paprika is very sensitive to acidity. Dolomitic lime also supplies Mg "
                 "needed for chlorophyll and capsanthin biosynthesis.",
    },
    notes=(
        "Total seasonal target: 150-170 kg N/ha, 60 kg P/ha, 100-120 kg K/ha. "
        "Paprika has high potassium demand for colour development. "
        "Micronutrients (Zn, B, Mn) often deficient on Zimbabwe granite sands — "
        "include in foliar programme. Fertigation is ideal for drip-irrigated crops."
    ),
)

PAPRIKA_PLANTING_WINDOWS: List[PlantingWindow] = [
    PlantingWindow(
        region="NR I (Eastern Highlands)",
        optimal_start="August 15",
        optimal_end="September 30",
        acceptable_start="August 1",
        acceptable_end="October 31",
        notes="Nursery sow July. Transplant to field Aug-Sept. Cool conditions favour colour development.",
    ),
    PlantingWindow(
        region="NR II (Highveld)",
        optimal_start="September 1",
        optimal_end="October 31",
        acceptable_start="August 15",
        acceptable_end="November 30",
        notes="Main paprika belt (Mashonaland). Nursery sow August. Transplant with early rains or irrigation.",
    ),
    PlantingWindow(
        region="NR III (Midlands)",
        optimal_start="September 15",
        optimal_end="November 15",
        acceptable_start="September 1",
        acceptable_end="December 15",
        notes="Irrigation essential. Dry spell risk during establishment. Lower yields than NR II.",
    ),
    PlantingWindow(
        region="NR IV (Semi-arid)",
        optimal_start="October 1",
        optimal_end="November 30",
        acceptable_start="September 15",
        acceptable_end="December 15",
        notes="Full irrigation required. High heat may reduce colour; shade nets beneficial.",
    ),
    PlantingWindow(
        region="NR V (Arid Lowveld)",
        optimal_start="October 15",
        optimal_end="November 30",
        acceptable_start="October 1",
        acceptable_end="December 31",
        notes="Only under full irrigation with shade management. Extreme heat reduces ASTA colour.",
    ),
]

PROFILE = CropProfile(
    crop_name="Paprika",
    scientific_name="Capsicum annuum",
    family="Solanaceae",
    optimal_ph=(6.0, 7.0),
    critical_ph_low=5.0,
    optimal_soil_types=["Fersiallitic red clays", "Siallitic alluvial soils", "Well-drained loams"],
    avoid_soil_types=["Waterlogged vertisols", "Acidic granite sands (unlimed)", "Saline soils"],
    optimal_temp=(20.0, 30.0),
    critical_temp_low=10.0,
    critical_temp_high=38.0,
    base_temp_gdd=12.0,
    total_water_mm=600.0,
    growth_stages=PAPRIKA_GROWTH_STAGES,
    fertilizer_schedule=PAPRIKA_FERTILIZER,
    diseases=PAPRIKA_DISEASES,
    pests=PAPRIKA_PESTS,
    planting_windows=PAPRIKA_PLANTING_WINDOWS,
    harvest_moisture="Harvest fully red pods; dry to < 12% moisture for storage (< 11% for export)",
    storage_conditions=(
        "Store dried pods in clean, dry, dark conditions at 15-20°C and < 65% RH. "
        "Use breathable polypropylene bags. Protect from light to preserve ASTA colour. "
        "Fumigate with phosphine if insect pests detected. Shelf life 12-18 months if properly dried."
    ),
    post_harvest_notes=(
        "Grade pods by ASTA colour value: Grade A (>160), Grade B (120-160), Grade C (<120). "
        "Remove damaged, mouldy, or discoloured pods. Export markets require aflatoxin < 10 ppb, "
        "pesticide residue compliance, and traceability. "
        "Mechanical grinding reduces value vs. whole pod export."
    ),
    natural_region_suitability={
        "NR I": "Good for colour development due to cool conditions; frost risk at higher elevations",
        "NR II": "Excellent — main commercial paprika zone in Zimbabwe (Mashonaland)",
        "NR III": "Suitable under irrigation; moderate yields",
        "NR IV": "Marginal — requires full irrigation and heat management",
        "NR V": "Not recommended without intensive irrigation and shade infrastructure",
    },
)

ALIASES: list = []
