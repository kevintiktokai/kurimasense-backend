"""Pearl Millet (Pennisetum glaucum) — Most drought-tolerant cereal, vital for semi-arid Zimbabwe."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List


PEARL_MILLET_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Downy Mildew",
        pathogen="Sclerospora graminicola",
        pathogen_type="fungal",
        symptoms=[
            "Systemic chlorosis — yellow-green striping on leaves",
            "Leafy panicles (phyllody) — floral parts converted to leaf-like structures",
            "Green ear (witches' broom) — inflorescence remains vegetative",
            "Stunted plants with excessive tillering",
            "White downy sporulation on leaf undersides in early morning",
        ],
        identification_markers=[
            "Green ear / leafy panicle is pathognomonic (key diagnostic)",
            "White downy growth on abaxial leaf surface at dawn",
            "Systemic chlorotic striping (not patchy like nutrient deficiency)",
            "Stunted, excessively tillered plants with no grain",
        ],
        favourable_conditions={
            "humidity_min": 90, "temp_min_c": 20, "temp_max_c": 30,
            "soil_moisture": "saturated soils at seedling stage",
            "note": "Cool, wet nights and warm days. Oospores survive in soil 5-10 years. "
                    "Soil-borne primary infection at emergence, then aerial secondary spread."
        },
        susceptible_stages=["Emergence", "Seedling (1-14 DAE)", "Tillering"],
        resistant_varieties=["Okashana 1 (tolerant)", "PMH 1 (moderate)", "PMH 2 (moderate)"],
        susceptible_varieties=["PMV 2 (variable)", "local landraces (variable)"],
        chemical_control=[
            {"name": "Metalaxyl-M (Apron Star) seed treatment", "rate": "3-5 g/kg seed",
             "phi_days": "N/A", "notes": "Critical for high-risk fields. Protects seedling "
             "stage against soil-borne oospore infection."},
            {"name": "Mancozeb 80 WP (foliar)", "rate": "2.0 kg/ha",
             "phi_days": "14", "notes": "Protectant against secondary spread; apply at "
             "tillering if wet conditions persist."},
        ],
        biological_control=[
            "Pseudomonas fluorescens seed treatment (10 g/kg seed)",
            "Trichoderma viride seed treatment",
            "No effective field-level biocontrol — resistant varieties are the primary strategy",
        ],
        cultural_control=[
            "Plant resistant or tolerant hybrids/OPVs",
            "Seed treatment with Metalaxyl is essential in endemic areas",
            "Crop rotation with non-host crops (legumes, sunflower) for 3+ years",
            "Remove and destroy infected plants (green ear) before sporulation",
            "Avoid waterlogged planting conditions",
            "Do not save seed from infected fields",
        ],
        economic_threshold="5% systemically infected plants at seedling stage",
        severity_scale={
            "mild": "< 5% plants with systemic infection",
            "moderate": "5-15% infected, scattered green ears visible",
            "severe": "> 15% infected with green ear — 30-100% yield loss on affected plants",
        },
    ),
    DiseaseProfile(
        name="Ergot",
        pathogen="Claviceps fusiformis",
        pathogen_type="fungal",
        symptoms=[
            "Honeydew (sticky, sugary exudate) dripping from florets during flowering",
            "Pink to tan sclerotia replacing grain on the panicle",
            "Heavily infected panicles drip honeydew attracting insects",
            "Sclerotia are toxic — contaminated grain is unsafe for consumption",
        ],
        identification_markers=[
            "Sticky honeydew on florets at flowering (key early sign)",
            "Hard, dark sclerotia (ergot bodies) protruding from florets at maturity",
            "Sclerotia are larger than normal grain and dark-coloured",
            "Honeydew stage distinguishes ergot from smut",
        ],
        favourable_conditions={
            "humidity_min": 80, "temp_min_c": 20, "temp_max_c": 30,
            "note": "Wet weather during flowering promotes infection. Open-pollinated "
                    "varieties more susceptible due to protogyny (stigma exposed before "
                    "pollen shed). High humidity prevents pollen dispersal."
        },
        susceptible_stages=["Flowering (most critical)", "Early grain fill"],
        resistant_varieties=["PMH 1 (moderate — hybrid vigour reduces protogyny window)",
                             "PMH 2 (moderate)"],
        susceptible_varieties=["PMV 2 (open-pollinated, longer protogyny)",
                               "Local landraces"],
        chemical_control=[
            {"name": "Copper oxychloride 85 WP", "rate": "2.5-3.0 kg/ha",
             "phi_days": "14", "notes": "Protectant spray at early flowering; limited efficacy"},
            {"name": "Carbendazim 500 SC", "rate": "0.5 L/ha",
             "phi_days": "14", "notes": "Apply at 50% flowering if wet weather persists"},
        ],
        biological_control=[
            "No effective biological control agents registered",
            "Honeydew-feeding insects do not provide control but help reduce inoculum spread",
        ],
        cultural_control=[
            "Plant hybrids — shorter protogyny window reduces infection opportunity",
            "Avoid late planting which pushes flowering into peak wet season",
            "Remove and burn ergot-infected panicles before sclerotia drop to soil",
            "Deep plough to bury sclerotia below germination depth",
            "Do not feed ergot-contaminated grain to livestock (toxic alkaloids)",
            "Clean seed — soak in 2% salt solution; sclerotia float and can be removed",
        ],
        economic_threshold="5% of panicles showing honeydew at flowering",
        severity_scale={
            "mild": "< 5% panicles with honeydew, few sclerotia",
            "moderate": "5-20% panicles affected, significant sclerotia formation",
            "severe": "> 20% panicles with ergot — grain unmarketable due to contamination",
        },
    ),
    DiseaseProfile(
        name="Smut",
        pathogen="Moesziomyces penicillariae (syn. Tolyposporium penicillariae)",
        pathogen_type="fungal",
        symptoms=[
            "Individual grain replaced by green to dark brown smut sori (spore masses)",
            "Sori are covered by a membrane that ruptures to release black spores",
            "Panicle appears partially or fully blackened",
            "Black powdery spore mass on and between florets",
        ],
        identification_markers=[
            "Dark, membrane-covered sori replacing individual grains",
            "Black powdery spores released when sori rupture",
            "Unlike ergot, no honeydew stage and sori are soft/powdery, not hard sclerotia",
            "Individual florets affected (not systemic)",
        ],
        favourable_conditions={
            "humidity_min": 75, "temp_min_c": 25, "temp_max_c": 35,
            "note": "Warm, humid conditions during flowering. Airborne spore infection "
                    "of open florets. Worse in late-planted crops."
        },
        susceptible_stages=["Flowering"],
        resistant_varieties=["PMH 1", "PMH 2"],
        susceptible_varieties=["PMV 2 (moderate)", "Local landraces"],
        chemical_control=[
            {"name": "Thiram seed treatment", "rate": "2-3 g/kg seed",
             "phi_days": "N/A", "notes": "Reduces soil-borne inoculum; limited effect on "
             "airborne infection"},
            {"name": "Propiconazole 250 EC (foliar)", "rate": "0.5 L/ha",
             "phi_days": "21", "notes": "Apply at early flowering if smut history exists"},
        ],
        biological_control=[
            "No effective biocontrol agents currently available",
        ],
        cultural_control=[
            "Plant resistant hybrids",
            "Remove and destroy infected panicles before spore release",
            "Crop rotation to reduce soil inoculum",
            "Avoid late planting",
        ],
        economic_threshold="10% of panicles showing smut sori",
        severity_scale={
            "mild": "< 5% panicles affected",
            "moderate": "5-15% panicles with smut",
            "severe": "> 15% — significant yield and quality loss",
        },
    ),
]


PEARL_MILLET_PESTS: List[PestProfile] = [
    PestProfile(
        name="Birds (Quelea and others)",
        scientific_name="Quelea quelea / Ploceus spp.",
        pest_type="bird",
        identification=[
            "Quelea: small weaver, forms enormous flocks (millions)",
            "Various weavers, bishops, and sparrows also feed on pearl millet",
            "Flocks descend on fields at dawn and dusk",
            "Heavy perching bends and breaks panicles",
        ],
        damage_symptoms=[
            "Grain stripped from panicle, leaving bare rachis",
            "Broken panicle branches from bird weight",
            "Up to 100% loss in small fields near roosts",
            "Partially eaten grain attracts moulds",
        ],
        life_cycle_notes=(
            "Quelea populations peak during rainy season breeding. Flocks are "
            "nomadic, following rainfall and seed availability. Pearl millet "
            "is a highly preferred food source due to exposed grain on the panicle."
        ),
        favourable_conditions={
            "note": "Small isolated fields near water and roosting trees. "
                    "Late-maturing crops at highest risk."
        },
        susceptible_stages=["Grain fill (dough stage)", "Maturity"],
        economic_threshold="Any flock activity on maturing panicles",
        chemical_control=[
            {"name": "Queletox (fenthion 60% ULV)", "rate": "Aerial on roosts only",
             "phi_days": "N/A", "notes": "Government-controlled application only"},
        ],
        biological_control=[
            "Encourage raptors near fields",
            "Community-coordinated bird scaring",
        ],
        cultural_control=[
            "Synchronised planting for area-wide maturity",
            "Plant large contiguous blocks, not small isolated plots",
            "Use early-maturing varieties to shorten exposure window",
            "Physical scaring: drums, tins, reflective tape, children guarding",
            "Harvest early at dough stage and sun-dry if bird pressure extreme",
        ],
        scouting_protocol=(
            "Monitor daily from grain fill onwards. Coordinate with neighbours. "
            "Report quelea roost locations to Plant Protection department."
        ),
    ),
    PestProfile(
        name="Stem Borer",
        scientific_name="Chilo partellus",
        pest_type="insect",
        identification=[
            "Adult: straw-coloured moth, 20-25mm wingspan",
            "Larvae: cream to pinkish caterpillars with dark lateral spots",
            "Bore holes in stems with frass (sawdust-like excrement) pushed out",
            "Pupae inside stem tunnels",
        ],
        damage_symptoms=[
            "Dead hearts in seedlings — central leaf dries and pulls out",
            "Stem tunnelling causing lodging",
            "White head — panicle dies due to peduncle damage",
            "Frass extrusion from bore holes on stem",
        ],
        life_cycle_notes=(
            "Eggs laid in batches on leaf sheaths. Neonate larvae feed on leaves "
            "before boring into stems. Larval development takes 4-6 weeks. "
            "Pupation inside stems. Diapauses in crop stubble over dry season."
        ),
        favourable_conditions={
            "temp_min_c": 22, "temp_max_c": 32,
            "note": "Carries over in stubble of previous cereal crops. Worse in "
                    "continuous cereal monoculture areas."
        },
        susceptible_stages=["Seedling", "Tillering", "Stem elongation"],
        economic_threshold="5-10% plants with dead hearts or bore holes",
        chemical_control=[
            {"name": "Chlorpyrifos granules", "rate": "0.3 kg a.i./ha",
             "phi_days": "21", "notes": "Apply into leaf whorls at first signs"},
            {"name": "Lambda-cyhalothrin 50 EC", "rate": "0.3 L/ha",
             "phi_days": "14", "notes": "Target neonate larvae before stem entry"},
        ],
        biological_control=[
            "Cotesia sesamiae parasitoid wasp — important natural enemy",
            "Trichogramma egg parasitoids",
            "Conserve natural enemies by avoiding broad-spectrum sprays",
        ],
        cultural_control=[
            "Destroy crop stubble after harvest to kill diapausing larvae",
            "Rotate with legumes or sunflower (non-host crops)",
            "Early planting to escape peak moth flights",
            "Push-pull technology where feasible",
        ],
        scouting_protocol=(
            "Scout weekly from 14 DAE. Check for dead hearts, leaf feeding, and "
            "bore holes. Examine 20 plants at 5 points. Split suspect stems to "
            "confirm larvae presence."
        ),
    ),
    PestProfile(
        name="Head Caterpillar",
        scientific_name="Helicoverpa armigera / Mythimna spp.",
        pest_type="insect",
        identification=[
            "Helicoverpa larvae: variable green/brown/pink, up to 40mm",
            "Mythimna (armyworm) larvae: dark with pale lateral stripes",
            "Found feeding on developing grain inside panicle",
            "Frass and silk webbing in panicle",
        ],
        damage_symptoms=[
            "Larvae feed on developing grain in the panicle",
            "Hollowed-out seeds and frass between grains",
            "Reduced grain yield and quality",
            "Secondary fungal infection on damaged grain",
        ],
        life_cycle_notes=(
            "Helicoverpa is polyphagous — migrates from cotton, tomato, and other "
            "crops. Mythimna populations can build rapidly in outbreaks. Eggs laid "
            "singly (Helicoverpa) or in masses (Mythimna) on panicles and leaves."
        ),
        favourable_conditions={
            "temp_min_c": 20, "temp_max_c": 35,
            "note": "Populations build during wet season. Pearl millet flowering "
                    "coincides with peak moth activity."
        },
        susceptible_stages=["Flowering", "Grain fill"],
        economic_threshold="2-3 larvae per panicle",
        chemical_control=[
            {"name": "Lambda-cyhalothrin 50 EC", "rate": "0.3 L/ha",
             "phi_days": "14", "notes": "Target small larvae before they enter panicle"},
            {"name": "Indoxacarb 150 SC", "rate": "0.25 L/ha",
             "phi_days": "14", "notes": "Selective; safer for beneficial insects"},
        ],
        biological_control=[
            "Bacillus thuringiensis (Bt) sprays on young larvae",
            "HaNPV (nuclear polyhedrosis virus) for Helicoverpa",
            "Trichogramma egg parasitoids",
        ],
        cultural_control=[
            "Monitor moth flights with pheromone traps",
            "Destroy crop residue and pupae by ploughing",
            "Avoid proximity to cotton fields",
        ],
        scouting_protocol=(
            "Scout twice weekly from flowering. Open panicle and count larvae. "
            "Check 20 panicles per field. Spray when 2-3 larvae per panicle found."
        ),
    ),
]


PEARL_MILLET_GROWTH_STAGES: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Germination and Emergence",
        stage_code="GE",
        day_range=(0, 7),
        water_kc=0.30,
        water_mm_per_week=10,
        critical_nutrients=["Phosphorus"],
        key_activities=[
            "Plant at 2-3cm depth in moist soil",
            "Apply basal Compound D at planting",
            "Ensure soil temperature > 15°C for rapid germination",
            "Target 60,000-90,000 plants/ha (spacing 60-75cm x 15-20cm)",
        ],
        risks=["Poor emergence in cold soils", "Crusting of heavy soils",
               "Bird feeding on surface seed"],
        scientific_notes=(
            "Pearl millet has rapid germination (2-4 days at 25-30°C) and emergence "
            "by day 5-7. Epigeal germination. The coleoptile emerges first, followed "
            "by the first leaf. The mesocotyl elongates to push the crown node to "
            "1-2cm below soil surface. Faster establishment than finger millet due "
            "to larger seed size and more vigorous seedling growth."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Seedling Establishment",
        stage_code="SE",
        day_range=(7, 20),
        water_kc=0.40,
        water_mm_per_week=12,
        critical_nutrients=["Nitrogen", "Phosphorus"],
        key_activities=[
            "First weeding — critical as pearl millet is slow to shade weeds",
            "Thin to desired spacing if broadcast-planted",
            "Scout for shoot fly dead hearts",
            "Assess stand — gap-fill if < 60% establishment",
        ],
        risks=["Shoot fly damage", "Weed competition",
               "Downy mildew systemic infection from soil-borne oospores"],
        scientific_notes=(
            "Crown roots develop from day 7-10, establishing the permanent root "
            "system. Pearl millet's root system is extensive — eventually reaching "
            "2m depth, which explains its drought tolerance. Nodal roots provide "
            "anchorage and nutrient uptake from surface soil. This stage determines "
            "the foundation for tillering capacity."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Tillering",
        stage_code="TI",
        day_range=(20, 35),
        water_kc=0.55,
        water_mm_per_week=18,
        critical_nutrients=["Nitrogen", "Phosphorus"],
        key_activities=[
            "Top-dress with AN at 20-25 DAE",
            "Second weeding",
            "Scout for stem borers and downy mildew symptoms",
            "Remove systemically infected (green ear) plants",
        ],
        risks=["Stem borer establishment", "Downy mildew green ear expression",
               "Weed competition if not controlled"],
        scientific_notes=(
            "Pearl millet produces 1-5 productive tillers per plant, depending on "
            "variety, spacing, and fertility. Tillers are synchronous in hybrids "
            "and less so in OPVs. Nitrogen applied at tillering promotes tiller "
            "survival. The apical meristem transitions to reproductive phase around "
            "25-30 DAE in early varieties. Root depth reaches 60-90cm."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Stem Elongation and Booting",
        stage_code="EB",
        day_range=(35, 50),
        water_kc=0.80,
        water_mm_per_week=25,
        critical_nutrients=["Nitrogen", "Potassium"],
        key_activities=[
            "Final weeding if needed",
            "Monitor for stem borer bore holes",
            "Ensure adequate soil moisture — panicle primordia developing",
            "Scout for downy mildew green ear symptoms on tillers",
        ],
        risks=["Stem borer tunnelling causing white heads",
               "Drought stress reducing panicle size and spikelet number",
               "Downy mildew green ear becoming apparent"],
        scientific_notes=(
            "Rapid internode elongation — pearl millet can grow 5-10cm per day. "
            "The panicle (spike) primordium elongates within the flag leaf sheath. "
            "Spikelet number is determined during booting — drought stress at this "
            "stage irreversibly reduces yield potential. Pearl millet's C4 photosynthesis "
            "enables high growth rates even at temperatures above 35°C."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Heading and Flowering",
        stage_code="HF",
        day_range=(50, 60),
        water_kc=1.00,
        water_mm_per_week=30,
        critical_nutrients=["Potassium", "Boron"],
        key_activities=[
            "Monitor for ergot honeydew on florets",
            "Scout for head caterpillars",
            "Begin bird scaring preparations",
            "No further fertiliser application",
        ],
        risks=["Ergot infection (honeydew) during wet flowering weather",
               "Smut infection of open florets",
               "Head caterpillar damage"],
        scientific_notes=(
            "Pearl millet is protogynous — stigmas emerge 2-3 days before pollen shed "
            "on the same panicle. This promotes cross-pollination but creates a window "
            "for ergot infection (Claviceps spores infect receptive stigmas before "
            "pollen arrives). Hybrids have shorter protogyny windows and thus less "
            "ergot susceptibility. Anthesis progresses from top to base of the spike "
            "over 3-5 days."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Grain Fill",
        stage_code="GF",
        day_range=(60, 80),
        water_kc=0.65,
        water_mm_per_week=20,
        critical_nutrients=["Potassium"],
        key_activities=[
            "Intensify bird scaring — most critical period",
            "Monitor for head caterpillar damage",
            "Assess grain hardness for harvest timing",
            "Remove ergot-infected panicles (contaminated grain is toxic)",
        ],
        risks=["Severe bird damage — quelea can destroy entire fields",
               "Head caterpillar reducing grain quality",
               "Ergot sclerotia developing in infected panicles"],
        scientific_notes=(
            "Grain filling is rapid in pearl millet — starch accumulation proceeds "
            "over 20-25 days. Pearl millet grain is nutritionally rich: 11-12% protein, "
            "5% fat (higher than other cereals), and rich in iron (8 mg/100g) and "
            "zinc (3.1 mg/100g). Grain moisture declines from 60% at dough stage to "
            "20-25% at physiological maturity."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Maturity and Harvest",
        stage_code="MH",
        day_range=(80, 100),
        water_kc=0.25,
        water_mm_per_week=5,
        critical_nutrients=[],
        key_activities=[
            "Harvest when panicle turns grey-brown and grain is hard (12-14% moisture)",
            "Cut panicles by hand (sickle or knife)",
            "Dry on clean surface for 3-5 days",
            "Thresh by beating or mechanical thresher; winnow",
        ],
        risks=["Bird damage if harvest delayed",
               "Grain shattering in some varieties",
               "Rain on mature panicles causing sprouting or mould"],
        scientific_notes=(
            "Physiological maturity is reached when the panicle turns grey-brown and "
            "the grain cannot be dented by thumbnail. Pearl millet grain has a thin "
            "pericarp and is more susceptible to insect damage in storage than finger "
            "millet. Prompt drying to < 12% moisture is critical. The crop matures "
            "rapidly — only 75-100 days in most Zimbabwe varieties."
        ),
    ),
]


PEARL_MILLET_FERTILIZER = FertilizerSchedule(
    basal={
        "product": "Compound D (7:14:7)",
        "rate_kg_ha": 150,
        "timing": "At planting",
        "method": "Band-placed or broadcast and incorporated",
        "nutrients_applied": {"N": 10.5, "P2O5": 21, "K2O": 10.5},
        "notes": "Pearl millet is adapted to low-fertility soils but responds to "
                 "phosphorus. Modest fertilisation is more cost-effective than high inputs.",
    },
    top_dress_1={
        "product": "Ammonium Nitrate (AN 34.5%N)",
        "rate_kg_ha": 75,
        "timing": "At tillering (20-25 DAE)",
        "method": "Side-band or broadcast between rows",
        "nutrients_applied": {"N": 25.9},
        "notes": "Target total N: 30-40 kg/ha. Pearl millet is efficient at extracting "
                 "soil N — over-fertilisation increases lodging risk.",
    },
    top_dress_2=None,
    foliar=None,
    liming={
        "product": "Agricultural lime",
        "rate_kg_ha": "500-1000 based on soil test",
        "timing": "3-6 months before planting",
        "notes": "Pearl millet is relatively tolerant of acid soils (to pH 4.5) but "
                 "responds to liming on very acid soils.",
    },
    notes=(
        "Pearl millet has modest fertiliser requirements: 30-40 kg N/ha, 20 kg P2O5/ha, "
        "10 kg K2O/ha. It is one of the most nutrient-efficient cereals. Farmyard "
        "manure (3-5 t/ha) is an excellent basal amendment for smallholder systems. "
        "Excessive nitrogen promotes lodging and does not proportionally increase yield."
    ),
)


PEARL_MILLET_PLANTING_WINDOWS: List[PlantingWindow] = [
    PlantingWindow(
        region="NR I (Eastern Highlands)",
        optimal_start="October 15",
        optimal_end="November 15",
        acceptable_start="October 1",
        acceptable_end="December 1",
        notes="Not commonly grown here; too wet and cool for pearl millet.",
    ),
    PlantingWindow(
        region="NR II (Highveld)",
        optimal_start="November 1",
        optimal_end="November 30",
        acceptable_start="October 15",
        acceptable_end="December 15",
        notes="Possible but maize is usually preferred in this high-rainfall zone.",
    ),
    PlantingWindow(
        region="NR III (Midlands)",
        optimal_start="November 1",
        optimal_end="December 1",
        acceptable_start="October 20",
        acceptable_end="December 15",
        notes="Suitable as a drought insurance crop in drier parts of NR III.",
    ),
    PlantingWindow(
        region="NR IV (Semi-arid)",
        optimal_start="November 15",
        optimal_end="December 15",
        acceptable_start="November 1",
        acceptable_end="December 31",
        notes="Ideal zone for pearl millet. Plant on first effective rains.",
    ),
    PlantingWindow(
        region="NR V (Arid Lowveld)",
        optimal_start="December 1",
        optimal_end="January 5",
        acceptable_start="November 15",
        acceptable_end="January 15",
        notes="Pearl millet is the best cereal option here. Use earliest-maturing varieties.",
    ),
]


PROFILE = CropProfile(
    crop_name="Pearl Millet",
    scientific_name="Pennisetum glaucum",
    family="Poaceae",
    optimal_ph=(5.0, 7.5),
    critical_ph_low=4.5,
    optimal_soil_types=["kaolinitic (sandy)", "fersiallitic", "siallitic"],
    avoid_soil_types=["vertisol (waterlogged)", "saline soils"],
    optimal_temp=(25.0, 35.0),
    critical_temp_low=10.0,
    critical_temp_high=45.0,
    base_temp_gdd=12.0,
    total_water_mm=300.0,
    growth_stages=PEARL_MILLET_GROWTH_STAGES,
    fertilizer_schedule=PEARL_MILLET_FERTILIZER,
    diseases=PEARL_MILLET_DISEASES,
    pests=PEARL_MILLET_PESTS,
    planting_windows=PEARL_MILLET_PLANTING_WINDOWS,
    harvest_moisture="12-14% grain moisture",
    storage_conditions=(
        "Store at < 12% moisture in clean, dry, airtight containers. Pearl millet "
        "grain is more susceptible to storage pests than finger millet due to its "
        "thinner pericarp. Use Actellic Super dust or hermetic storage bags (PICS bags). "
        "Check regularly for grain weevil (Sitophilus) and flour beetle (Tribolium)."
    ),
    post_harvest_notes=(
        "Thresh by beating dried panicles. Winnow to remove chaff. Pearl millet "
        "is processed into sadza, porridge, mahewu, and traditional beer. The grain "
        "has higher fat content (5%) than other cereals, which contributes to flavour "
        "but can cause rancidity if stored improperly. Mill into flour within "
        "2-3 months for best quality. Pearl millet flour is naturally gluten-free."
    ),
    natural_region_suitability={
        "NR I": "Not recommended — too wet, high downy mildew risk",
        "NR II": "Possible but other cereals preferred in this zone",
        "NR III": "Suitable — useful drought insurance crop",
        "NR IV": "Excellent — primary recommendation for cereal production",
        "NR V": "Best cereal option — most drought-tolerant grain crop available",
    },
)


ALIASES = ["mhunga", "bulrush millet"]
