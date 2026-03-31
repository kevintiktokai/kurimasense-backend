"""Sunflower (Helianthus annuus) — Oilseed crop, drought tolerant, excellent rotation crop."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List


SUNFLOWER_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Sclerotinia Head Rot",
        pathogen="Sclerotinia sclerotiorum",
        pathogen_type="fungal",
        symptoms=[
            "Water-soaked, soft rot on the back of the head",
            "White cottony mycelial growth on head surface",
            "Black sclerotia (2-10mm) embedded in rotting tissue",
            "Premature head drooping and seed shattering",
            "Stem infections cause wilting and basal rot",
        ],
        identification_markers=[
            "White fluffy mycelium on head back (key diagnostic)",
            "Hard black sclerotia visible in decayed tissue",
            "Shredded, papery head tissue in advanced stages",
            "Mushy, watery rot distinct from Botrytis grey mould",
        ],
        favourable_conditions={
            "humidity_min": 80, "temp_min_c": 15, "temp_max_c": 25,
            "rainfall": "prolonged wet weather during flowering and grain fill",
            "note": "Cool, wet conditions during R5-R8 stages. "
                    "Inoculum persists as sclerotia in soil for 5-8 years."
        },
        susceptible_stages=["R5 (flowering)", "R6 (grain fill)", "R7-R8 (maturity)"],
        resistant_varieties=["Agsun 8251 (moderate tolerance)", "NK Adagio CL"],
        susceptible_varieties=["PAN 7057", "open-pollinated locals"],
        chemical_control=[
            {"name": "Amistar Xtra (Azoxystrobin + Cyproconazole)", "rate": "0.5 L/ha",
             "phi_days": "28", "notes": "Apply at R5 (early flowering) preventively"},
            {"name": "Carbendazim 500 SC", "rate": "0.5-1.0 L/ha",
             "phi_days": "21", "notes": "Systemic; good curative action on head rot"},
        ],
        biological_control=[
            "Trichoderma harzianum soil applications reduce sclerotia viability",
            "Coniothyrium minitans parasitises sclerotia in soil",
            "Crop rotation (minimum 3-year break) to deplete soil sclerotia bank",
        ],
        cultural_control=[
            "Rotate with cereals (maize, sorghum, millet) — minimum 3-year break",
            "Avoid excessive nitrogen which promotes dense canopy and humidity",
            "Wider row spacing (90cm) for air circulation",
            "Deep ploughing to bury sclerotia below germination depth",
            "Remove and destroy infected heads to reduce inoculum",
        ],
        economic_threshold="5% of heads showing symptoms at R5-R6",
        severity_scale={
            "mild": "< 5% heads affected, limited rot on head back",
            "moderate": "5-20% heads affected, mycelium visible, some seed loss",
            "severe": "> 20% heads affected, extensive rot — expect 30-60% yield loss",
        },
    ),
    DiseaseProfile(
        name="Downy Mildew",
        pathogen="Plasmopara halstedii",
        pathogen_type="fungal",
        symptoms=[
            "Systemic chlorosis — pale green to yellow leaves",
            "White downy sporulation on leaf undersides",
            "Stunted plants with thickened, brittle stems",
            "Dwarfed heads with poor seed set",
            "Infected seedlings may die before flowering",
        ],
        identification_markers=[
            "Systemic yellowing (not patchy) from seedling stage",
            "White cottony growth on abaxial leaf surface",
            "Stunted internodes giving rosette-like appearance",
            "Distinguished from nutrient deficiency by white sporulation",
        ],
        favourable_conditions={
            "humidity_min": 90, "temp_min_c": 15, "temp_max_c": 22,
            "soil_moisture": "saturated or waterlogged",
            "note": "Cool, wet soils at emergence. Oospores persist in soil for 10+ years. "
                    "Worse in poorly drained fields."
        },
        susceptible_stages=["VE (emergence)", "V2-V4 (seedling)", "V6-V8 (vegetative)"],
        resistant_varieties=["NK Adagio CL", "Agsun 8251"],
        susceptible_varieties=["older open-pollinated lines"],
        chemical_control=[
            {"name": "Metalaxyl-M (Apron XL) seed treatment", "rate": "3 mL/kg seed",
             "phi_days": "N/A", "notes": "Systemic seed treatment; critical for infected fields"},
            {"name": "Mancozeb 80 WP (foliar)", "rate": "2.0-2.5 kg/ha",
             "phi_days": "14", "notes": "Protectant; apply at V2-V4 if wet conditions persist"},
        ],
        biological_control=[
            "Use certified disease-free seed",
            "No effective biological control agents currently registered",
        ],
        cultural_control=[
            "Plant resistant hybrids (race-specific resistance available)",
            "Ensure good field drainage to reduce soil saturation",
            "Crop rotation with non-host crops for 4+ years",
            "Remove volunteer sunflower plants which harbour the pathogen",
            "Avoid planting into cold, waterlogged soils",
        ],
        economic_threshold="2% of plants showing systemic infection at seedling stage",
        severity_scale={
            "mild": "< 5% plants systemically infected",
            "moderate": "5-15% plants infected, patchy stand reduction",
            "severe": "> 15% plants infected — replanting may be necessary",
        },
    ),
    DiseaseProfile(
        name="Rust",
        pathogen="Puccinia helianthi",
        pathogen_type="fungal",
        symptoms=[
            "Small, round, cinnamon-brown pustules on leaves",
            "Pustules primarily on leaf undersides, also on stems and petioles",
            "Premature defoliation in severe infections",
            "Reduced seed fill and oil content",
        ],
        identification_markers=[
            "Round to oval brown uredinia (pustules) on leaves",
            "Powdery brown spores released when pustules rupture",
            "Dark brown-black telia form late in season",
            "Starts on lower leaves and progresses upward",
        ],
        favourable_conditions={
            "humidity_min": 75, "temp_min_c": 20, "temp_max_c": 30,
            "dew_hours": 6,
            "note": "Warm, humid conditions with heavy dew. "
                    "Wind-dispersed uredospores can travel long distances."
        },
        susceptible_stages=["V10-V12 (late vegetative)", "R1-R3 (budding)", "R5 (flowering)"],
        resistant_varieties=["Agsun 8251", "NK Adagio CL"],
        susceptible_varieties=["PAN 7057", "older cultivars"],
        chemical_control=[
            {"name": "Amistar (Azoxystrobin 250 SC)", "rate": "0.4 L/ha",
             "phi_days": "28", "notes": "Apply at first pustule appearance"},
            {"name": "Propiconazole 250 EC", "rate": "0.5 L/ha",
             "phi_days": "21", "notes": "Triazole; curative and protective activity"},
        ],
        biological_control=[
            "Deploy resistant hybrids as primary strategy",
            "No effective biocontrol agents registered for sunflower rust",
        ],
        cultural_control=[
            "Plant rust-resistant hybrids",
            "Destroy volunteer sunflower plants and crop residue",
            "Avoid late planting which increases exposure during grain fill",
            "Balanced potassium nutrition improves plant resistance",
        ],
        economic_threshold="Pustules on 50% of lower leaves before R5",
        severity_scale={
            "mild": "Scattered pustules on lower 3-4 leaves",
            "moderate": "Pustules reaching middle canopy, 25-50% leaves affected",
            "severe": "Pustules on upper leaves including head bracts — 25-40% yield loss",
        },
    ),
]


SUNFLOWER_PESTS: List[PestProfile] = [
    PestProfile(
        name="Sunflower Moth",
        scientific_name="Homoeosoma electellum",
        pest_type="insect",
        identification=[
            "Adult: small grey-brown moth, 10-12mm wingspan",
            "Larvae: cream to pinkish caterpillar with dark head capsule, up to 15mm",
            "Larvae spin silk webbing across florets on head face",
            "Frass (excrement) visible between florets",
        ],
        damage_symptoms=[
            "Larvae feed on developing seeds and florets",
            "Webbing and frass between seeds on head surface",
            "Hollowed-out seeds with entry holes",
            "Secondary fungal infection of damaged tissue",
            "Yield losses of 10-30% in severe infestations",
        ],
        life_cycle_notes=(
            "Adults emerge from soil pupae in early summer. Females lay eggs on "
            "florets during flowering. Larvae feed for 2-3 weeks before dropping "
            "to soil to pupate. One to two generations per season in Zimbabwe."
        ),
        favourable_conditions={
            "temp_min_c": 25, "temp_max_c": 35,
            "note": "Warm, dry conditions favour moth activity. "
                    "Early-flowering fields attract moths first."
        },
        susceptible_stages=["R5 (flowering)", "R6 (grain fill)"],
        economic_threshold="1-2 larvae per head at R5.1-R5.5",
        chemical_control=[
            {"name": "Cypermethrin 200 EC", "rate": "0.25-0.5 L/ha",
             "phi_days": "14", "notes": "Apply at early flowering (R5.1) when moths active"},
            {"name": "Chlorpyrifos 480 EC", "rate": "0.75-1.0 L/ha",
             "phi_days": "21", "notes": "Broad-spectrum; consider pollinator safety"},
        ],
        biological_control=[
            "Trichogramma parasitoid wasps on moth eggs",
            "Bacillus thuringiensis (Bt) sprays on young larvae",
            "Encourage natural predators (lacewings, ladybirds)",
        ],
        cultural_control=[
            "Synchronised planting to reduce staggered flowering targets",
            "Early planting so flowering avoids peak moth populations",
            "Deep tillage to destroy overwintering pupae in soil",
            "Trap cropping with early-flowering varieties",
        ],
        scouting_protocol=(
            "Scout at R5 flowering stage. Inspect 20 heads across the field. "
            "Count larvae per head. Treatment justified at 1-2 larvae per head. "
            "Scout at dusk when adults are most active."
        ),
    ),
    PestProfile(
        name="Birds (Quelea, Doves)",
        scientific_name="Quelea quelea / Streptopelia spp.",
        pest_type="bird",
        identification=[
            "Quelea: small weaver bird, brownish with variable face markings",
            "Doves: grey or brown columbids, ring-necked dove common",
            "Flocks of hundreds to millions descend on fields",
            "Feed on exposed seed in mature heads",
        ],
        damage_symptoms=[
            "Seeds stripped from head face, leaving empty receptacles",
            "Damaged heads with scattered seed loss from edges inward",
            "Faecal contamination of remaining seed",
            "Can cause 50-100% loss in small fields near roost sites",
        ],
        life_cycle_notes=(
            "Quelea breed in vast colonies during the rainy season. Flocks are "
            "highly mobile and can devastate fields in hours. Movements are "
            "correlated with rainfall patterns and seed availability."
        ),
        favourable_conditions={
            "note": "Late-maturing crops near water sources and roosting sites. "
                    "Small isolated fields more vulnerable than large blocks."
        },
        susceptible_stages=["R7-R8 (seed fill)", "R9 (physiological maturity)"],
        economic_threshold="Any flock activity on maturing heads warrants action",
        chemical_control=[
            {"name": "Bird repellent (Methiocarb-based)", "rate": "As per label",
             "phi_days": "14", "notes": "Registered avian repellents; limited effectiveness"},
        ],
        biological_control=[
            "Encourage raptors (hawks, kestrels) near fields",
            "Falconry-based bird scaring in high-value fields",
        ],
        cultural_control=[
            "Plant large blocks rather than isolated small fields",
            "Synchronised planting with neighbours for area-wide dilution",
            "Early harvest at 12-15% moisture to reduce exposure time",
            "Physical bird scaring: reflective tape, gas cannons, scarecrows",
            "Choose varieties with head-down posture at maturity for partial deterrence",
        ],
        scouting_protocol=(
            "Monitor from R7 onwards. Watch for flock arrival at dawn and dusk. "
            "Assess damage by counting stripped seeds per head on 20 heads. "
            "Coordinate with neighbours for area-wide bird management."
        ),
    ),
    PestProfile(
        name="African Bollworm",
        scientific_name="Helicoverpa armigera",
        pest_type="insect",
        identification=[
            "Adult: medium moth (35-40mm wingspan), pale brown forewings with dark spots",
            "Larvae: variable colour (green, brown, pink), up to 40mm",
            "Distinctive light and dark lateral stripes on larvae",
            "Eggs: small, round, white to brown, laid singly on florets",
        ],
        damage_symptoms=[
            "Larvae bore into developing seeds",
            "Frass visible on head surface and between seeds",
            "Hollow seeds and direct yield loss",
            "Secondary Aspergillus infection in damaged seeds",
        ],
        life_cycle_notes=(
            "Polyphagous pest — also attacks cotton, tomato, maize. Adults are "
            "strong fliers and migrate between host crops. Females lay 500-1000 "
            "eggs. Larvae develop through 6 instars over 14-21 days. Pupation "
            "occurs in soil."
        ),
        favourable_conditions={
            "temp_min_c": 20, "temp_max_c": 35,
            "note": "Warm, dry spells during flowering. Populations build on "
                    "preceding cotton and tomato crops nearby."
        },
        susceptible_stages=["R5 (flowering)", "R6 (grain fill)"],
        economic_threshold="2-3 larvae per head at R5-R6",
        chemical_control=[
            {"name": "Lambda-cyhalothrin 50 EC", "rate": "0.3 L/ha",
             "phi_days": "14", "notes": "Apply when threshold exceeded; target small larvae"},
            {"name": "Indoxacarb 150 SC", "rate": "0.25 L/ha",
             "phi_days": "14", "notes": "Selective; safer for beneficials than pyrethroids"},
        ],
        biological_control=[
            "Bacillus thuringiensis (Bt) on young larvae",
            "Nuclear polyhedrosis virus (HaNPV) specific to Helicoverpa",
            "Trichogramma egg parasitoids",
            "Conserve natural enemies: ladybirds, lacewings, spiders",
        ],
        cultural_control=[
            "Monitor moth flights with pheromone traps from budding stage",
            "Avoid proximity to cotton fields which amplify populations",
            "Destroy crop residue and pupae by deep ploughing after harvest",
            "Trap cropping with pigeon pea or early-flowering sunflower rows",
        ],
        scouting_protocol=(
            "Scout twice weekly from R4 (budding) through R7. Inspect 20 heads "
            "per field. Shake heads over a tray to dislodge small larvae. "
            "Count eggs and larvae. Spray when 2-3 larvae per head are found."
        ),
    ),
]


SUNFLOWER_GROWTH_STAGES: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Germination and Emergence",
        stage_code="VE",
        day_range=(0, 10),
        water_kc=0.35,
        water_mm_per_week=15,
        critical_nutrients=["Phosphorus", "Zinc"],
        key_activities=[
            "Plant at 5-7cm depth in moist soil",
            "Apply basal Compound S at planting",
            "Ensure soil temperature > 10°C for germination",
            "Target 40,000-55,000 plants/ha",
        ],
        risks=["Poor emergence in cold, wet soils", "Bird damage on emerging seedlings",
               "Cutworm damage at soil line"],
        scientific_notes=(
            "Sunflower requires soil temperature above 10°C for germination, with "
            "optimal at 20-25°C. Hypogeal germination — cotyledons remain below "
            "soil surface. Radical emergence in 3-4 days, epicotyl hook pushes "
            "through soil by day 7-10. Phosphorus critical for root establishment."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Seedling Establishment",
        stage_code="V2-V6",
        day_range=(10, 30),
        water_kc=0.45,
        water_mm_per_week=20,
        critical_nutrients=["Nitrogen", "Phosphorus", "Boron"],
        key_activities=[
            "First weeding at V2-V4 (critical weed-free period begins)",
            "Scout for cutworm and downy mildew",
            "Apply pre-emergence herbicides if not done at planting",
            "Assess plant population and consider replanting if < 30,000/ha",
        ],
        risks=["Downy mildew systemic infection", "Cutworm damage",
               "Weed competition establishing"],
        scientific_notes=(
            "Sunflower develops a strong taproot system during this phase, reaching "
            "30-60cm depth by V6. Lateral roots expand horizontally. The apical "
            "meristem transitions from vegetative to reproductive around V6 — the "
            "microscopic head primordium is being initiated. Boron demand begins "
            "rising as vascular tissue differentiates."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Rapid Vegetative Growth",
        stage_code="V8-V14",
        day_range=(30, 55),
        water_kc=0.75,
        water_mm_per_week=35,
        critical_nutrients=["Nitrogen", "Potassium", "Boron"],
        key_activities=[
            "Top-dress with AN at V8-V10",
            "Second weeding or inter-row cultivation",
            "Scout for rust and Sclerotinia stem infection",
            "Assess moisture status — drought stress reduces head size",
        ],
        risks=["Nitrogen deficiency reducing head size", "Rust establishment",
               "Drought stress during head primordium development"],
        scientific_notes=(
            "Maximum vegetative growth rate — plants gain 5-8cm per day. The "
            "developing head (capitulum) at the shoot apex enlarges rapidly. Ray "
            "and disc floret primordia differentiate. Number of potential seeds "
            "is determined during this phase. Nitrogen demand peaks as leaf area "
            "expands exponentially. Boron is critical for pollen tube development "
            "in forming florets."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Budding (Star Bud)",
        stage_code="R1-R4",
        day_range=(55, 70),
        water_kc=0.95,
        water_mm_per_week=45,
        critical_nutrients=["Boron", "Potassium", "Nitrogen"],
        key_activities=[
            "Foliar boron application (Solubor) at R1-R2",
            "Scout for head moth and bollworm eggs",
            "Monitor soil moisture — most drought-sensitive phase approaching",
            "Ensure adequate potassium for oil synthesis initiation",
        ],
        risks=["Boron deficiency causing poor seed set", "Drought stress reducing floret fertility",
               "Early moth and bollworm oviposition"],
        scientific_notes=(
            "The immature bud (capitulum) becomes visible and enlarges. The star "
            "bud stage (R1) transitions to full bud (R4) as ray florets elongate. "
            "Boron is essential for pollen viability and pollen tube growth — "
            "deficiency at this stage causes hollow seeds and poor fertilisation. "
            "The developing head acts as a strong sink for assimilates and boron."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Flowering",
        stage_code="R5",
        day_range=(70, 85),
        water_kc=1.10,
        water_mm_per_week=55,
        critical_nutrients=["Boron", "Potassium"],
        key_activities=[
            "Monitor for Sclerotinia head rot (preventive fungicide if wet)",
            "Scout for sunflower moth larvae on head face",
            "Avoid pesticide application during peak bee activity (pollination)",
            "Ensure adequate moisture — yield potential set during this stage",
        ],
        risks=["Sclerotinia head rot in wet weather", "Sunflower moth larvae",
               "Heat stress (>35°C) reducing pollen viability",
               "Rain damage on open florets"],
        scientific_notes=(
            "Anthesis proceeds centripetally — outer ring of disc florets opens "
            "first, progressing inward over 5-10 days. Cross-pollination by bees "
            "improves seed set by 15-30% even in self-fertile hybrids. Pollen "
            "viability declines above 35°C. Oil synthesis begins in fertilised "
            "ovules. Sclerotinia ascospore infection occurs through senescing "
            "ray florets and petal tissue on the head back."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Grain Fill",
        stage_code="R6-R8",
        day_range=(85, 110),
        water_kc=0.80,
        water_mm_per_week=35,
        critical_nutrients=["Potassium", "Sulphur"],
        key_activities=[
            "Monitor for head rot and bollworm damage",
            "Assess bird damage — begin scaring if flocks appear",
            "Prepare harvesting equipment",
            "Monitor seed moisture for harvest timing",
        ],
        risks=["Sclerotinia head rot in prolonged wet weather", "Bird damage (quelea)",
               "Bollworm boring into seeds", "Lodging in strong winds"],
        scientific_notes=(
            "Oil accumulation is rapid during R6-R7 — oil content increases from "
            "25% to 45% of seed dry weight. Oleic and linoleic acid ratios are "
            "determined by temperature during this phase (higher temp = more oleic). "
            "The head back turns yellow then brown as physiological maturity "
            "approaches. Potassium supports oil synthesis and translocation."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Maturity and Harvest",
        stage_code="R9",
        day_range=(110, 130),
        water_kc=0.35,
        water_mm_per_week=10,
        critical_nutrients=[],
        key_activities=[
            "Harvest when seed moisture is 10-12% (back of head is brown/dry)",
            "Combine harvest: adjust cylinder speed to reduce seed cracking",
            "Desiccation with Paraquat if uneven maturity (10-14 days before harvest)",
            "Begin post-harvest soil preparation for next crop",
        ],
        risks=["Bird damage intensifies", "Seed shattering if harvest delayed",
               "Rain causing head mould on mature heads",
               "Over-drying increasing seed cracking during harvest"],
        scientific_notes=(
            "Physiological maturity (R9) is reached when the back of the head turns "
            "brown and seed moisture is 25-30%. Field drying to 10-12% follows. "
            "Delayed harvest risks Rhizopus head rot and bird losses. Seed oil "
            "content and quality are fixed at R9. The bracts dry and the head "
            "assumes a nodding posture, reducing bird access somewhat."
        ),
    ),
]


SUNFLOWER_FERTILIZER = FertilizerSchedule(
    basal={
        "product": "Compound S (7:21:7 + 6S + 1Zn)",
        "rate_kg_ha": 250,
        "timing": "At planting",
        "method": "Band-placed 5cm to side and 5cm below seed",
        "nutrients_applied": {"N": 17.5, "P2O5": 52.5, "K2O": 17.5, "S": 15, "Zn": 2.5},
        "notes": "Sunflower has high phosphorus demand for root establishment",
    },
    top_dress_1={
        "product": "Ammonium Nitrate (AN 34.5%N)",
        "rate_kg_ha": 150,
        "timing": "V8-V10 (30-40 days after emergence)",
        "method": "Side-band 10cm from plant row",
        "nutrients_applied": {"N": 51.75},
        "notes": "Total N target: 60-80 kg/ha. Avoid excessive N which promotes "
                 "vegetative growth, lodging, and Sclerotinia susceptibility.",
    },
    top_dress_2=None,
    foliar={
        "product": "Solubor (20.5% B)",
        "rate_kg_ha": 1.5,
        "timing": "R1-R2 (star bud stage)",
        "method": "Foliar spray in 200-300 L water/ha",
        "nutrients_applied": {"B": 0.31},
        "notes": "Critical for seed set. Apply in morning or evening to avoid leaf scorch.",
    },
    liming={
        "product": "Agricultural lime (calcitic or dolomitic)",
        "rate_kg_ha": "1000-2000 based on soil test",
        "timing": "3-6 months before planting",
        "notes": "Target pH 6.0-7.0. Sunflower is moderately sensitive to aluminium toxicity.",
    },
    notes=(
        "Sunflower is efficient at extracting deep soil nutrients but responds well "
        "to balanced fertilisation. Avoid excessive nitrogen (>80 kg N/ha) which "
        "promotes vegetative growth at the expense of oil content. Phosphorus and "
        "boron are the most commonly deficient nutrients for sunflower in Zimbabwe."
    ),
)


SUNFLOWER_PLANTING_WINDOWS: List[PlantingWindow] = [
    PlantingWindow(
        region="NR I (Eastern Highlands)",
        optimal_start="October 15",
        optimal_end="November 15",
        acceptable_start="October 1",
        acceptable_end="December 15",
        notes="High rainfall areas; watch for Sclerotinia in wet seasons.",
    ),
    PlantingWindow(
        region="NR II (Highveld)",
        optimal_start="November 1",
        optimal_end="November 30",
        acceptable_start="October 15",
        acceptable_end="December 15",
        notes="Primary sunflower production zone. Avoid late planting past mid-December.",
    ),
    PlantingWindow(
        region="NR III (Midlands)",
        optimal_start="November 1",
        optimal_end="December 1",
        acceptable_start="October 20",
        acceptable_end="December 15",
        notes="Good region for sunflower. Drought tolerance is advantageous here.",
    ),
    PlantingWindow(
        region="NR IV (Low rainfall)",
        optimal_start="November 15",
        optimal_end="December 15",
        acceptable_start="November 1",
        acceptable_end="December 31",
        notes="Sunflower well-suited due to drought tolerance. Plant on first effective rains.",
    ),
    PlantingWindow(
        region="NR V (Lowveld)",
        optimal_start="December 1",
        optimal_end="December 31",
        acceptable_start="November 15",
        acceptable_end="January 15",
        notes="Marginal for dryland sunflower. Irrigation improves reliability.",
    ),
]


PROFILE = CropProfile(
    crop_name="Sunflower",
    scientific_name="Helianthus annuus",
    family="Asteraceae",
    optimal_ph=(6.0, 7.5),
    critical_ph_low=5.0,
    optimal_soil_types=["fersiallitic", "siallitic", "kaolinitic (with fertility amendments)"],
    avoid_soil_types=["vertisol (waterlogged)", "lithosol (shallow)"],
    optimal_temp=(20.0, 30.0),
    critical_temp_low=5.0,
    critical_temp_high=40.0,
    base_temp_gdd=6.0,
    total_water_mm=500.0,
    growth_stages=SUNFLOWER_GROWTH_STAGES,
    fertilizer_schedule=SUNFLOWER_FERTILIZER,
    diseases=SUNFLOWER_DISEASES,
    pests=SUNFLOWER_PESTS,
    planting_windows=SUNFLOWER_PLANTING_WINDOWS,
    harvest_moisture="10-12% seed moisture",
    storage_conditions=(
        "Store at < 9% moisture for long-term storage. Cool, dry, ventilated warehouse. "
        "Sunflower seed is prone to rancidity — monitor temperature and moisture. "
        "Aeration is critical to prevent hot spots."
    ),
    post_harvest_notes=(
        "Sunflower seed must be dried promptly to < 9% moisture to prevent fungal "
        "deterioration and rancidity. Clean seed to remove broken seeds and foreign "
        "material. Oil content is typically 38-45% for oilseed types. Confectionery "
        "types are larger-seeded with lower oil content. Sunflower meal is a valuable "
        "livestock feed byproduct after oil extraction."
    ),
    natural_region_suitability={
        "NR I": "Suitable but watch for Sclerotinia in wet conditions",
        "NR II": "Excellent — primary production zone with reliable yields",
        "NR III": "Well suited — drought tolerance valuable here",
        "NR IV": "Good — one of the best oilseed options for drier areas",
        "NR V": "Marginal under dryland; possible under irrigation",
    },
)


ALIASES = ["sunflowers"]
