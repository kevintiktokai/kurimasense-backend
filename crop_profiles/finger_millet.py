"""Finger Millet (Eleusine coracana) — Drought-tolerant small grain with exceptional nutrition."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List


FINGER_MILLET_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Finger Millet Blast",
        pathogen="Magnaporthe grisea (anamorph: Pyricularia grisea)",
        pathogen_type="fungal",
        symptoms=[
            "Leaf blast: elliptical grey-green lesions with dark brown margins on leaves",
            "Neck blast: infection at peduncle causing head breakage and grain loss",
            "Finger blast: dark brown to black discolouration of individual fingers",
            "Node blast: dark lesions at stem nodes causing lodging",
            "Severe infections kill entire panicle before grain fill",
        ],
        identification_markers=[
            "Diamond-shaped leaf lesions with grey centre and brown border (key diagnostic)",
            "Neck region turns dark brown and shrivels (neck blast)",
            "Fingers appear blighted with chalky, unfilled grains",
            "Distinct from Helminthosporium which produces more elongate, uniform lesions",
        ],
        favourable_conditions={
            "humidity_min": 85, "temp_min_c": 22, "temp_max_c": 30,
            "leaf_wetness_hours": 10,
            "note": "Warm, humid weather with prolonged leaf wetness. Excessive nitrogen "
                    "increases susceptibility. Worse in high-density plantings."
        },
        susceptible_stages=["Tillering", "Booting", "Heading (most critical)", "Grain fill"],
        resistant_varieties=["FMV 1 (moderate resistance)"],
        susceptible_varieties=["Local landrace selections", "ICIAP-SM 1 (moderate)"],
        chemical_control=[
            {"name": "Tricyclazole 75 WP", "rate": "0.3-0.5 kg/ha",
             "phi_days": "21", "notes": "Systemic; apply at booting and heading stages"},
            {"name": "Carbendazim 500 SC", "rate": "0.5 L/ha",
             "phi_days": "14", "notes": "Apply at first symptoms; repeat after 14 days if wet"},
            {"name": "Mancozeb 80 WP", "rate": "2.0 kg/ha",
             "phi_days": "14", "notes": "Protectant; tank-mix with systemic for better efficacy"},
        ],
        biological_control=[
            "Trichoderma viride seed treatment reduces seedling blast",
            "Pseudomonas fluorescens seed treatment (10 g/kg seed)",
            "Crop rotation to reduce soil and residue inoculum",
        ],
        cultural_control=[
            "Plant resistant or tolerant varieties",
            "Avoid excessive nitrogen fertilisation (< 40 kg N/ha for blast-prone areas)",
            "Optimise plant spacing (25 x 10cm) for air circulation",
            "Remove and destroy infected crop residue after harvest",
            "Avoid late planting which pushes heading into peak wet season",
            "Seed treatment with Thiram or Carbendazim (2 g/kg seed)",
        ],
        economic_threshold="10% leaf area infected at booting, or any neck blast at heading",
        severity_scale={
            "mild": "< 10% leaf area with lesions, no neck or finger blast",
            "moderate": "10-25% leaf area, scattered neck blast — 20-30% yield loss",
            "severe": "> 25% leaf area, widespread neck blast — 50-100% yield loss",
        },
    ),
    DiseaseProfile(
        name="Helminthosporium Leaf Blight",
        pathogen="Exserohilum turcicum (syn. Helminthosporium turcicum)",
        pathogen_type="fungal",
        symptoms=[
            "Long, elliptical tan-brown lesions on leaves",
            "Lesions enlarge and coalesce causing extensive blighting",
            "Premature drying of leaves from tip downward",
            "Reduced grain filling due to loss of photosynthetic area",
        ],
        identification_markers=[
            "Elongate (3-15cm) spindle-shaped lesions, tan centre with dark borders",
            "Lesions more uniform than blast (not diamond-shaped)",
            "Dark grey-brown sporulation on lesion surface in humid conditions",
            "Lower leaves affected first, progressing upward",
        ],
        favourable_conditions={
            "humidity_min": 80, "temp_min_c": 20, "temp_max_c": 28,
            "note": "Warm, humid conditions with prolonged leaf wetness. "
                    "Worse under continuous millet cropping and heavy dew."
        },
        susceptible_stages=["Tillering", "Booting", "Heading", "Grain fill"],
        resistant_varieties=["FMV 1 (moderate tolerance)"],
        susceptible_varieties=["Local landraces", "ICIAP-SM 1"],
        chemical_control=[
            {"name": "Mancozeb 80 WP", "rate": "2.0-2.5 kg/ha",
             "phi_days": "14", "notes": "Protectant; apply at first symptoms"},
            {"name": "Propiconazole 250 EC", "rate": "0.5 L/ha",
             "phi_days": "21", "notes": "Systemic; curative activity on established lesions"},
        ],
        biological_control=[
            "Trichoderma-based products on crop residue decomposition",
            "No specific biocontrol agents registered",
        ],
        cultural_control=[
            "Crop rotation with non-host crops (legumes, sunflower)",
            "Destroy infected crop residue by ploughing or burning",
            "Plant tolerant varieties where available",
            "Avoid excessive plant density",
            "Balanced fertilisation — well-nourished plants resist better",
        ],
        economic_threshold="25% leaf area blighted before grain fill",
        severity_scale={
            "mild": "< 10% leaf area blighted, lower leaves only",
            "moderate": "10-25% leaf area, reaching flag leaf",
            "severe": "> 25% leaf area, flag leaf blighted — 20-40% yield loss",
        },
    ),
]


FINGER_MILLET_PESTS: List[PestProfile] = [
    PestProfile(
        name="Birds (Quelea and others)",
        scientific_name="Quelea quelea / Ploceus spp.",
        pest_type="bird",
        identification=[
            "Quelea: small weaver bird forming enormous flocks",
            "Various weavers and bishops also feed on finger millet",
            "Flocks arrive at dawn and dusk to feed on maturing grain",
            "Perching damage — stems bent or broken by bird weight",
        ],
        damage_symptoms=[
            "Grain stripped from fingers, leaving empty husks",
            "Broken fingers and scattered grain on ground",
            "Can destroy entire fields in 2-3 days near roost sites",
            "Partial damage leads to secondary fungal infection on damaged ears",
        ],
        life_cycle_notes=(
            "Quelea populations peak during the rainy season when breeding "
            "colonies form. Flocks of up to millions of birds move between "
            "feeding sites. Small grains (millet, sorghum) are preferred foods."
        ),
        favourable_conditions={
            "note": "Small isolated fields near water and tree roosts. "
                    "Late-maturing crops are at highest risk."
        },
        susceptible_stages=["Heading", "Grain fill", "Maturity"],
        economic_threshold="Any flock activity on maturing heads",
        chemical_control=[
            {"name": "Queletox (fenthion 60% ULV)", "rate": "Aerial application on roosts",
             "phi_days": "N/A", "notes": "Controlled by government pest agencies only"},
        ],
        biological_control=[
            "Encourage raptors near fields",
            "Community-based scaring using traditional methods",
        ],
        cultural_control=[
            "Synchronised planting with neighbours for area-wide maturity",
            "Early-maturing varieties to shorten exposure window",
            "Physical bird scaring: drums, tins, reflective tape, children guarding",
            "Plant large contiguous blocks rather than small isolated plots",
            "Early harvest when grain is at dough stage (dry in sun later)",
        ],
        scouting_protocol=(
            "Monitor daily from heading onwards. Watch for bird flocks at dawn and "
            "dusk. If quelea roosts are nearby, coordinate with Plant Protection "
            "department. Harvest as soon as grain is hard enough to thresh."
        ),
    ),
    PestProfile(
        name="Shoot Fly",
        scientific_name="Atherigona spp.",
        pest_type="insect",
        identification=[
            "Adult: small grey fly, 3-5mm long, resembling a house fly",
            "Eggs: white, elongate, laid on underside of young leaves",
            "Larvae: white maggots found inside shoot at growing point",
            "Pupae: brown puparium in soil near plant base",
        ],
        damage_symptoms=[
            "Dead heart symptom — central shoot dries and can be pulled out",
            "Rotting growing point with foul smell",
            "Tillers may compensate but are delayed and less productive",
            "Seedling stand reduced; gaps in field",
        ],
        life_cycle_notes=(
            "Female flies lay eggs on seedlings 7-21 days after emergence. "
            "Larvae bore into the central shoot and feed on the growing point. "
            "Pupation in soil lasts 7-10 days. Multiple generations per season."
        ),
        favourable_conditions={
            "temp_min_c": 25, "temp_max_c": 35,
            "note": "Late-planted crops more affected as fly populations build. "
                    "Drought-stressed seedlings more susceptible."
        },
        susceptible_stages=["Emergence", "Seedling (7-21 DAE)"],
        economic_threshold="10% dead hearts at seedling stage",
        chemical_control=[
            {"name": "Imidacloprid seed treatment", "rate": "5-10 g/kg seed",
             "phi_days": "N/A", "notes": "Seed treatment provides 14-21 days protection"},
            {"name": "Cypermethrin 200 EC (foliar)", "rate": "0.25 L/ha",
             "phi_days": "14", "notes": "Spray at 7 DAE and 14 DAE if dead hearts appear"},
        ],
        biological_control=[
            "Parasitoid wasps (Opius spp.) naturally regulate shoot fly",
            "Conserve natural enemies by avoiding calendar spraying",
        ],
        cultural_control=[
            "Plant early within the recommended window to avoid peak fly populations",
            "Increase seeding rate by 25% to compensate for expected losses",
            "Remove dead heart tillers to reduce in-field breeding",
            "Inter-crop with taller crops for partial fly deterrence",
        ],
        scouting_protocol=(
            "Scout at 7, 14, and 21 days after emergence. Pull out central "
            "leaf of suspected dead hearts — if it pulls out easily with a "
            "rotting base, shoot fly damage is confirmed. Count dead hearts "
            "per 10-metre row length across 5 points in the field."
        ),
    ),
    PestProfile(
        name="Stem Borer",
        scientific_name="Chilo partellus / Busseola fusca",
        pest_type="insect",
        identification=[
            "Chilo partellus: straw-coloured moth, 20-25mm wingspan",
            "Busseola fusca: brown nocturnal moth, 25-35mm wingspan",
            "Larvae: cream to pinkish caterpillars with dark spots, found inside stems",
            "Characteristic bore holes in stems with frass extrusion",
        ],
        damage_symptoms=[
            "Dead hearts in young plants (similar to shoot fly but larger bore holes)",
            "Stem tunnelling causing lodging and nutrient disruption",
            "White heads (panicle dies prematurely due to stem damage)",
            "Frass extrusion at bore holes on stems",
        ],
        life_cycle_notes=(
            "Moths lay egg batches on leaf sheaths. Neonates initially feed on leaves "
            "before boring into stems. Larvae develop over 4-6 weeks, pupating inside "
            "stems. Two to three generations per season. Diapauses in stubble."
        ),
        favourable_conditions={
            "temp_min_c": 20, "temp_max_c": 30,
            "note": "Carries over in crop stubble. Worse in continuous cereal cropping "
                    "areas. First generation attacks 3-4 weeks after planting."
        },
        susceptible_stages=["Seedling", "Tillering", "Booting", "Heading"],
        economic_threshold="5-10% plants with dead hearts or bore holes",
        chemical_control=[
            {"name": "Chlorpyrifos granules (stem application)", "rate": "0.3 kg a.i./ha",
             "phi_days": "21", "notes": "Apply into leaf whorls at first bore hole signs"},
            {"name": "Lambda-cyhalothrin 50 EC", "rate": "0.3 L/ha",
             "phi_days": "14", "notes": "Foliar spray targeting neonate larvae on leaves"},
        ],
        biological_control=[
            "Cotesia sesamiae — larval parasitoid wasp (important natural enemy)",
            "Trichogramma egg parasitoids",
            "Conserve natural enemies by minimising broad-spectrum insecticide use",
        ],
        cultural_control=[
            "Destroy stubble and crop residue after harvest to kill diapausing larvae",
            "Rotate with non-cereal crops (legumes, sunflower)",
            "Early planting to avoid peak moth flights",
            "Push-pull technology: Napier grass (trap) and Desmodium (repellent)",
        ],
        scouting_protocol=(
            "Scout weekly from 14 DAE. Check for dead hearts, leaf feeding windows, "
            "and bore holes with frass. Examine 20 plants per point at 5 points. "
            "Split stems of suspicious plants to confirm larvae presence."
        ),
    ),
]


FINGER_MILLET_GROWTH_STAGES: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Germination and Emergence",
        stage_code="GE",
        day_range=(0, 10),
        water_kc=0.30,
        water_mm_per_week=12,
        critical_nutrients=["Phosphorus"],
        key_activities=[
            "Prepare fine, firm seedbed (tiny seeds need good soil-seed contact)",
            "Mix seed with sand for even broadcast (1:3 ratio) or use row planting",
            "Apply basal Compound D at planting",
            "Roll or firm seedbed after sowing",
        ],
        risks=["Poor emergence due to deep sowing (max 1-2cm depth)",
               "Crusting of heavy soils preventing emergence",
               "Bird feeding on surface-sown seed"],
        scientific_notes=(
            "Finger millet seed is extremely small (1.5-2.0mm, 2.5g per 1000 seeds). "
            "Epigeal germination requires shallow sowing and good soil-seed contact. "
            "Light promotes germination — do not bury deeper than 2cm. Emergence "
            "occurs in 5-7 days at optimal temperature (25-30°C). Phosphorus is "
            "critical for radical elongation in the small seedling."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Seedling Establishment",
        stage_code="SE",
        day_range=(10, 25),
        water_kc=0.40,
        water_mm_per_week=15,
        critical_nutrients=["Nitrogen", "Phosphorus"],
        key_activities=[
            "Thin to 10-15cm between plants in rows (if row-planted)",
            "First weeding — critical as finger millet is slow-growing initially",
            "Scout for shoot fly (dead hearts in central shoot)",
            "Assess stand and consider gap-filling if < 50% emergence",
        ],
        risks=["Weed competition (finger millet is very slow initially)",
               "Shoot fly causing dead hearts",
               "Drought stress on shallow-rooted seedlings"],
        scientific_notes=(
            "Finger millet seedlings grow very slowly for the first 3 weeks — slower "
            "than most weeds, making early weeding essential. The seminal root system "
            "is shallow (10-15cm). Crown root initiation begins around 14 DAE. The "
            "plant produces 2-4 leaves in this phase. Tillering capacity is determined "
            "by early vigour and nutrient availability."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Tillering",
        stage_code="TI",
        day_range=(25, 45),
        water_kc=0.60,
        water_mm_per_week=20,
        critical_nutrients=["Nitrogen", "Phosphorus"],
        key_activities=[
            "Top-dress with AN (first application)",
            "Second weeding",
            "Scout for stem borers and blast lesions on leaves",
            "Thin excess tillers if stand is too dense",
        ],
        risks=["Blast infection on leaves (leaf blast phase)",
               "Stem borer dead hearts",
               "Weed competition if weeding delayed"],
        scientific_notes=(
            "Finger millet produces 3-8 productive tillers per plant. Tiller number "
            "is genetically determined but modified by spacing, nitrogen, and moisture. "
            "Crown roots establish the permanent root system to 30-60cm depth. "
            "Nitrogen application at tillering promotes tiller survival and ear-bearing "
            "capacity. The apical meristem remains below soil level, protected from "
            "damage until stem elongation begins."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Stem Elongation and Booting",
        stage_code="EB",
        day_range=(45, 65),
        water_kc=0.80,
        water_mm_per_week=25,
        critical_nutrients=["Nitrogen", "Potassium"],
        key_activities=[
            "Monitor for blast — leaf and neck blast risk increasing",
            "Final weeding if needed",
            "Scout for stem borers (bore holes, frass)",
            "Ensure adequate moisture — panicle primordia developing",
        ],
        risks=["Neck blast if humid conditions persist at booting",
               "Stem borer tunnelling causing white heads",
               "Drought stress reducing panicle size"],
        scientific_notes=(
            "Rapid internode elongation pushes the flag leaf and developing panicle "
            "upward. The panicle (ear) primordium differentiates within the boot — "
            "finger number and spikelet number per finger are determined. Boron "
            "and calcium are needed for pollen development. The boot stage is the "
            "most critical period for neck blast infection — the emerging peduncle "
            "is highly susceptible."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Heading and Flowering",
        stage_code="HF",
        day_range=(65, 80),
        water_kc=0.95,
        water_mm_per_week=30,
        critical_nutrients=["Potassium", "Boron"],
        key_activities=[
            "Preventive fungicide if blast risk is high",
            "Monitor bird activity — early arrivals indicate problems ahead",
            "Assess crop uniformity and expected yield",
            "No top-dressing after this stage",
        ],
        risks=["Neck blast — most devastating disease phase",
               "Bird damage beginning on early-maturing tillers",
               "Drought stress reducing seed set"],
        scientific_notes=(
            "The ear (panicle) emerges from the boot and the characteristic 'fingers' "
            "spread open. Finger millet is primarily self-pollinated (cleistogamous "
            "flowers). Anthesis progresses from tip to base of each finger over 3-5 "
            "days. Pollination efficiency is high (>95%) but drought stress reduces "
            "pollen viability. The neck region (peduncle junction) is extremely "
            "susceptible to Magnaporthe infection during this stage."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Grain Fill",
        stage_code="GF",
        day_range=(80, 100),
        water_kc=0.70,
        water_mm_per_week=22,
        critical_nutrients=["Potassium"],
        key_activities=[
            "Intensify bird scaring — most critical period for bird damage",
            "Monitor for finger blast and grain mould",
            "Begin harvest preparations",
            "Assess grain hardness for harvest timing",
        ],
        risks=["Bird damage — peak feeding on dough-stage grain",
               "Finger blast causing grain shrivelling",
               "Grain mould in prolonged wet weather"],
        scientific_notes=(
            "Grain filling in finger millet involves starch and protein accumulation. "
            "Finger millet grain is exceptionally high in calcium (344 mg/100g), iron "
            "(3.9 mg/100g), and methionine compared to other cereals. The calcium "
            "accumulation occurs primarily during mid to late grain fill. Grain "
            "moisture declines from 65% at early dough to 25-30% at physiological "
            "maturity. The fingers close inward as grain matures."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Maturity and Harvest",
        stage_code="MH",
        day_range=(100, 120),
        water_kc=0.30,
        water_mm_per_week=8,
        critical_nutrients=[],
        key_activities=[
            "Harvest when fingers turn brown and grain is hard (12-14% moisture)",
            "Cut panicles by hand or sickle",
            "Dry on clean surface or threshing floor",
            "Thresh by beating or foot-trampling; winnow to clean grain",
        ],
        risks=["Bird damage if harvest delayed",
               "Grain shattering in some varieties if over-mature",
               "Rain damage causing sprouting on mature heads",
               "Grain mould reducing quality"],
        scientific_notes=(
            "Physiological maturity is reached when the fingers turn brown and the "
            "grain is hard and cannot be dented by thumbnail. Grain moisture at "
            "harvest should be 12-14% for safe storage. Finger millet grain has "
            "excellent storage characteristics — the small, hard grain resists "
            "insect damage better than maize or sorghum. Traditional granary "
            "storage of unthreshed heads in the husk provides additional protection."
        ),
    ),
]


FINGER_MILLET_FERTILIZER = FertilizerSchedule(
    basal={
        "product": "Compound D (7:14:7)",
        "rate_kg_ha": 200,
        "timing": "At planting",
        "method": "Broadcast and incorporate before sowing, or band-place in rows",
        "nutrients_applied": {"N": 14, "P2O5": 28, "K2O": 14},
        "notes": "Finger millet is less responsive to fertiliser than maize but "
                 "phosphorus is critical for root development in small-seeded crops.",
    },
    top_dress_1={
        "product": "Ammonium Nitrate (AN 34.5%N)",
        "rate_kg_ha": 75,
        "timing": "At tillering (25-35 DAE)",
        "method": "Broadcast or side-band between rows",
        "nutrients_applied": {"N": 25.9},
        "notes": "Target total N: 40-50 kg/ha. Excessive N increases blast susceptibility "
                 "and lodging risk in finger millet.",
    },
    top_dress_2=None,
    foliar=None,
    liming={
        "product": "Agricultural lime",
        "rate_kg_ha": "500-1000 based on soil test",
        "timing": "3-6 months before planting",
        "notes": "Finger millet tolerates mildly acidic soils but responds to liming on "
                 "very acid soils (pH < 5.0).",
    },
    notes=(
        "Finger millet is adapted to low-fertility soils but responds to modest "
        "fertilisation. Total nutrient targets: 40-50 kg N/ha, 25-30 kg P2O5/ha, "
        "15 kg K2O/ha. Over-fertilisation with nitrogen increases blast disease "
        "risk and lodging. Farmyard manure (5-10 t/ha) is an excellent basal amendment."
    ),
)


FINGER_MILLET_PLANTING_WINDOWS: List[PlantingWindow] = [
    PlantingWindow(
        region="NR I (Eastern Highlands)",
        optimal_start="October 15",
        optimal_end="November 15",
        acceptable_start="October 1",
        acceptable_end="December 1",
        notes="Not commonly grown here; maize and wheat preferred.",
    ),
    PlantingWindow(
        region="NR II (Highveld)",
        optimal_start="November 1",
        optimal_end="November 30",
        acceptable_start="October 15",
        acceptable_end="December 15",
        notes="Suitable but other crops often preferred commercially.",
    ),
    PlantingWindow(
        region="NR III (Midlands)",
        optimal_start="November 1",
        optimal_end="December 1",
        acceptable_start="October 20",
        acceptable_end="December 15",
        notes="Good area for finger millet. Important food security crop here.",
    ),
    PlantingWindow(
        region="NR IV (Semi-arid)",
        optimal_start="November 15",
        optimal_end="December 15",
        acceptable_start="November 1",
        acceptable_end="December 31",
        notes="Well-suited due to drought tolerance. Plant on first effective rains.",
    ),
    PlantingWindow(
        region="NR V (Arid Lowveld)",
        optimal_start="December 1",
        optimal_end="December 31",
        acceptable_start="November 15",
        acceptable_end="January 15",
        notes="Finger millet is a key food security crop in this zone. Early varieties preferred.",
    ),
]


PROFILE = CropProfile(
    crop_name="Finger Millet",
    scientific_name="Eleusine coracana",
    family="Poaceae",
    optimal_ph=(5.0, 7.0),
    critical_ph_low=4.5,
    optimal_soil_types=["fersiallitic", "kaolinitic", "siallitic"],
    avoid_soil_types=["vertisol (waterlogged)", "saline soils"],
    optimal_temp=(22.0, 30.0),
    critical_temp_low=10.0,
    critical_temp_high=38.0,
    base_temp_gdd=12.0,
    total_water_mm=350.0,
    growth_stages=FINGER_MILLET_GROWTH_STAGES,
    fertilizer_schedule=FINGER_MILLET_FERTILIZER,
    diseases=FINGER_MILLET_DISEASES,
    pests=FINGER_MILLET_PESTS,
    planting_windows=FINGER_MILLET_PLANTING_WINDOWS,
    harvest_moisture="12-14% grain moisture",
    storage_conditions=(
        "Store threshed grain at < 12% moisture in clean, dry containers. "
        "Finger millet grain stores exceptionally well — 5+ years in traditional "
        "granaries when stored unthreshed in heads. The hard seed coat resists "
        "insect penetration. Store in airtight containers or bags treated with "
        "Actellic Super dust."
    ),
    post_harvest_notes=(
        "Thresh by beating dried heads or using mechanical thresher. Winnow to "
        "remove chaff and broken rachis. Finger millet is processed into flour "
        "for sadza (thick porridge), mahewu (fermented drink), and traditional "
        "beer (kachasu). The grain is gluten-free and exceptionally rich in "
        "calcium, iron, and essential amino acids, making it a valuable "
        "nutritional crop."
    ),
    natural_region_suitability={
        "NR I": "Possible but not commonly grown; too wet increases blast risk",
        "NR II": "Suitable — moderate production",
        "NR III": "Well suited — important smallholder crop",
        "NR IV": "Excellent — key drought-tolerant food security crop",
        "NR V": "Good — one of the few reliable cereal options",
    },
)


ALIASES = ["rapoko", "rukweza"]
