"""Sugar Beans (Phaseolus vulgaris) — Zimbabwe's most popular food legume."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List


SUGAR_BEAN_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Angular Leaf Spot",
        pathogen="Pseudocercospora griseola (syn. Phaeoisariopsis griseola)",
        pathogen_type="fungal",
        symptoms=[
            "Angular, grey-brown lesions on leaves bounded by veins",
            "Lesions on pods appear as circular to oval reddish-brown spots",
            "Severe infection causes premature defoliation",
            "Seed discolouration in heavily infected pods",
        ],
        identification_markers=[
            "Angular shape of leaf lesions (vein-limited) is diagnostic",
            "Grey sporulation on underside of lesions in humid weather",
            "Lesions often surrounded by yellow halo",
            "Distinguished from common bacterial blight by angular shape and fungal sporulation",
        ],
        favourable_conditions={
            "humidity_min": 80, "temp_min_c": 18, "temp_max_c": 25,
            "note": "Moderate temperatures with high humidity and rain. Seed-borne "
                    "and survives in crop residue for up to 2 years.",
        },
        susceptible_stages=["Flowering (R1-R3)", "Pod Fill (R5-R7)"],
        resistant_varieties=["Gloria", "PAN 148"],
        susceptible_varieties=["Some local landraces"],
        chemical_control=[
            {"name": "Amistar Xtra (Azoxystrobin + Cyproconazole)", "rate": "0.4-0.5 L/ha",
             "phi_days": "21", "notes": "Apply at first symptoms or preventively at flowering"},
            {"name": "Mancozeb 80 WP", "rate": "2.0-2.5 kg/ha",
             "phi_days": "14", "notes": "Protectant; apply before rain in wet seasons"},
            {"name": "Carbendazim 50 SC", "rate": "0.5 L/ha",
             "phi_days": "14", "notes": "Systemic; alternate with contact fungicides"},
        ],
        biological_control=[
            "Trichoderma-based seed treatments",
            "Crop residue decomposition using Trichoderma soil applications",
        ],
        cultural_control=[
            "Use certified disease-free seed",
            "Rotate with cereals for at least 2 years",
            "Bury crop residue by ploughing",
            "Avoid overhead irrigation during flowering",
            "Plant resistant varieties (Gloria, PAN 148)",
        ],
        economic_threshold="10% leaf area with angular lesions at or before flowering",
        severity_scale={
            "mild": "Scattered lesions on lower leaves, <5% leaf area",
            "moderate": "10-25% leaf area affected, pod lesions beginning",
            "severe": "> 25% leaf area, premature defoliation, seed discoloured — 30-60% yield loss",
        },
    ),
    DiseaseProfile(
        name="Anthracnose",
        pathogen="Colletotrichum lindemuthianum",
        pathogen_type="fungal",
        symptoms=[
            "Dark brown to black sunken lesions on pods, stems, and leaves",
            "Lesions on pods follow veins and produce pink spore masses in wet weather",
            "Seed-coat discolouration (dark brown speckling)",
            "Wilting and death of seedlings from stem cankers",
        ],
        identification_markers=[
            "Sunken, dark lesions with pink spore masses (acervuli) — diagnostic",
            "Pod lesions are deeply sunken with dark margins",
            "Stem lesions are elongated and dark brown",
            "Seed infection shows brown-black spots on seed coat",
        ],
        favourable_conditions={
            "humidity_min": 85, "temp_min_c": 13, "temp_max_c": 26,
            "note": "Cool to moderate temperatures with rain and high humidity. "
                    "Splash-dispersed by rain. Seed-borne — primary source of new-field inoculum.",
        },
        susceptible_stages=["Vegetative (V1-V4)", "Flowering (R1-R3)", "Pod Fill (R5-R7)"],
        resistant_varieties=["PAN 148"],
        susceptible_varieties=["Some local varieties without Co resistance genes"],
        chemical_control=[
            {"name": "Mancozeb 80 WP", "rate": "2.0-2.5 kg/ha",
             "phi_days": "14", "notes": "Protectant; apply before and after rain events"},
            {"name": "Carbendazim 50 SC", "rate": "0.5 L/ha",
             "phi_days": "14", "notes": "Systemic; effective on established infections"},
        ],
        biological_control=[
            "Trichoderma harzianum seed treatment",
            "Bacillus subtilis-based products under research",
        ],
        cultural_control=[
            "Use certified disease-free seed — most critical control measure",
            "Rotate with non-legume crops for 3 years",
            "Do not save seed from infected fields",
            "Avoid working in wet fields (spreads spores on clothing/tools)",
            "Destroy crop residue after harvest",
        ],
        economic_threshold="Any pod lesions warrant fungicide application if still in pod fill",
        severity_scale={
            "mild": "Leaf lesions only, no pod symptoms",
            "moderate": "Pod lesions present, some seed infection",
            "severe": "Widespread pod cankers, seed severely discoloured — crop may be unmarketable",
        },
    ),
    DiseaseProfile(
        name="Halo Blight",
        pathogen="Pseudomonas savastanoi pv. phaseolicola",
        pathogen_type="bacterial",
        symptoms=[
            "Small water-soaked spots on leaves surrounded by broad yellow-green halo",
            "Lesions may coalesce causing large areas of chlorosis",
            "Greasy, water-soaked lesions on pods",
            "Systemic infection causes stunting and wilting",
        ],
        identification_markers=[
            "Distinctive large yellow-green halo around small necrotic centre — key diagnostic",
            "Halo is caused by a phytotoxin (phaseolotoxin) that inhibits ornithine metabolism",
            "Distinguished from common blight by larger halo and smaller necrotic centre",
            "Bacterial ooze visible on lesions in early morning dew",
        ],
        favourable_conditions={
            "humidity_min": 80, "temp_min_c": 16, "temp_max_c": 24,
            "note": "Cool, wet conditions. More common in cooler highlands. "
                    "Seed-borne and spread by rain splash.",
        },
        susceptible_stages=["Vegetative (V1-V4)", "Flowering (R1-R3)"],
        resistant_varieties=["PAN 148"],
        susceptible_varieties=["Some local landraces"],
        chemical_control=[
            {"name": "Copper oxychloride 85 WP", "rate": "2.5-3.0 kg/ha",
             "phi_days": "7", "notes": "Protectant; apply before and after storms"},
            {"name": "Streptomycin sulphate", "rate": "100 g/ha",
             "phi_days": "7", "notes": "Antibiotic; use only when copper is insufficient"},
        ],
        biological_control=[
            "Certified seed is the primary prevention measure",
            "Bacillus-based biocontrol agents under research",
        ],
        cultural_control=[
            "Use certified disease-free seed",
            "Rotate with non-legume crops for 2-3 years",
            "Do not work in wet fields",
            "Avoid overhead irrigation",
            "Rogue out severely infected plants early",
        ],
        economic_threshold="5% of plants showing halo blight symptoms before flowering",
        severity_scale={
            "mild": "Scattered leaf spots with halos, <5% of plants",
            "moderate": "10-30% of plants with symptoms, some pod lesions",
            "severe": "Widespread infection, systemic wilting — 40-80% yield loss",
        },
    ),
]


SUGAR_BEAN_PESTS: List[PestProfile] = [
    PestProfile(
        name="Bean Fly (Bean Stem Maggot)",
        scientific_name="Ophiomyia phaseoli",
        pest_type="insect",
        identification=[
            "Adult: tiny (2-3 mm) shiny black fly",
            "Larvae: white-yellow maggots inside stems near soil line",
            "Puparia: brown, barrel-shaped, found in stem pith",
            "Oviposition punctures visible on cotyledons and first leaves",
        ],
        damage_symptoms=[
            "Yellowing and wilting of seedlings (often mistaken for drought stress)",
            "Swollen, cracked stem base from larval feeding",
            "Death of growing point in severe cases",
            "Reduced root development and stunting",
        ],
        life_cycle_notes=(
            "Females puncture leaves to feed and lay eggs. Larvae mine through leaf "
            "tissue into the stem and feed on pith near the base. Pupation occurs inside "
            "the stem or in soil. Life cycle is 21-28 days. Multiple generations per season. "
            "Most damaging to seedlings in the first 3 weeks."
        ),
        favourable_conditions={
            "temp_min_c": 20, "temp_max_c": 30,
            "note": "Warm conditions. Worse when beans are planted into bare soil "
                    "without mulch. Continuous bean cropping increases populations.",
        },
        susceptible_stages=["Emergence", "Vegetative (V1-V4)"],
        economic_threshold="10% of seedlings showing stem swelling and yellowing",
        chemical_control=[
            {"name": "Imidacloprid 70 WS (seed treatment)", "rate": "2 g/kg seed",
             "phi_days": "N/A", "notes": "Systemic seed treatment; protects seedlings for 3-4 weeks"},
            {"name": "Dimethoate 40 EC", "rate": "500 mL/ha",
             "phi_days": "14", "notes": "Foliar spray at first leaf stage if seed was untreated"},
        ],
        biological_control=[
            "Parasitoid wasps (Opius phaseoli) attack larvae inside stems",
            "Predatory ground beetles feed on pupae in soil",
            "Mulching provides habitat for natural enemies",
        ],
        cultural_control=[
            "Treat seed with systemic insecticide (most effective single measure)",
            "Apply mulch around seedlings to deter oviposition",
            "Plant into well-fertilised soil for vigorous seedlings that tolerate attack",
            "Earth up (hill) around stems to encourage adventitious root development",
            "Rotate with cereals to break the cycle",
        ],
        scouting_protocol=(
            "Scout from 7 days after emergence until V3 stage. Pull up 10 seedlings "
            "at each of 5 points (50 total). Check stem base for swelling, cracking, "
            "and larval tunnels. Gently split stems with a blade to see larvae. If >10% "
            "of seedlings show stem damage and are wilting, apply foliar systemic insecticide. "
            "Seed treatment is preferred over foliar rescue."
        ),
    ),
    PestProfile(
        name="Aphids",
        scientific_name="Aphis fabae (black bean aphid)",
        pest_type="insect",
        identification=[
            "Small (2 mm), soft-bodied, black to dark green insects",
            "Dense colonies on growing tips, stems, and leaf undersides",
            "Winged adults appear when colonies are crowded",
            "Honeydew and sooty mould on infested plants",
        ],
        damage_symptoms=[
            "Curling and distortion of growing tips and young leaves",
            "Stunting and reduced pod set from heavy infestations",
            "Sooty mould on honeydew reduces photosynthesis",
            "Vector for Bean Common Mosaic Virus (BCMV)",
        ],
        life_cycle_notes=(
            "Parthenogenetic reproduction — females produce live young without mating. "
            "Generation time 7-10 days. Populations can explode under warm, dry conditions. "
            "Natural enemies usually keep populations below economic threshold unless "
            "disrupted by broad-spectrum insecticides."
        ),
        favourable_conditions={
            "temp_min_c": 18, "temp_max_c": 28,
            "note": "Warm, dry weather favours rapid multiplication. Populations "
                    "collapse in heavy rain and high humidity.",
        },
        susceptible_stages=["Vegetative (V1-V4)", "Flowering (R1-R3)"],
        economic_threshold="50% of plants with colonies of 20+ aphids on growing tips",
        chemical_control=[
            {"name": "Imidacloprid 200 SL", "rate": "250 mL/ha",
             "phi_days": "21", "notes": "Systemic; effective against virus vectors"},
            {"name": "Acetamiprid 20 SP", "rate": "100 g/ha",
             "phi_days": "14", "notes": "Neonicotinoid with quick knockdown"},
        ],
        biological_control=[
            "Ladybird beetles (Hippodamia, Coccinella spp.) — key predators",
            "Parasitic wasps (Aphidius, Lysiphlebus spp.)",
            "Hoverfly larvae (Syrphidae)",
            "Entomopathogenic fungi (Beauveria bassiana) in humid weather",
        ],
        cultural_control=[
            "Conserve natural enemies by avoiding unnecessary insecticide sprays",
            "Intercrop with maize or sorghum (reduces aphid landing rates)",
            "Remove weed hosts around field margins",
            "Healthy, well-fertilised plants tolerate moderate aphid pressure",
        ],
        scouting_protocol=(
            "Scout weekly from V1 to R3. Examine the growing tip and underside of the "
            "youngest fully expanded leaf on 20 plants at 5 stops (100 plants). Record "
            "presence of aphid colonies and natural enemies (ladybirds, parasitised mummies). "
            "If >50% of plants have colonies of 20+ aphids and few predators/parasitoids, "
            "consider insecticide application. Prioritise action if BCMV-susceptible variety."
        ),
    ),
    PestProfile(
        name="Bruchid Beetle (Storage)",
        scientific_name="Acanthoscelides obtectus",
        pest_type="insect",
        identification=[
            "Adult: small (3-4 mm), greyish-brown beetle with mottled wing covers",
            "Larvae: white, C-shaped grubs found inside beans",
            "Exit holes: perfectly round 2mm holes in bean surface",
            "Frass (powder) accumulating around stored beans",
        ],
        damage_symptoms=[
            "Round exit holes in stored beans",
            "Weight loss (up to 40% in severe infestations)",
            "Reduced germination of seed beans",
            "Beans become unpalatable and unmarketable",
        ],
        life_cycle_notes=(
            "Adults lay eggs on bean surface or in cracks. Larvae bore into the bean "
            "and feed internally, completing development inside the seed. Life cycle is "
            "25-35 days. Adults can infest beans in the field before harvest. Up to "
            "5 generations can develop in stored beans over 6 months."
        ),
        favourable_conditions={
            "temp_min_c": 20, "temp_max_c": 32,
            "humidity_min": 40,
            "note": "Warm storage conditions. Higher moisture content of stored beans "
                    "accelerates development. Unprotected beans can be completely "
                    "destroyed within 3-6 months.",
        },
        susceptible_stages=["Maturity (R8-R9)", "Storage"],
        economic_threshold="Any adult bruchids or exit holes in stored beans",
        chemical_control=[
            {"name": "Actellic Super Dust (pirimiphos-methyl + permethrin)", "rate": "50 g/90 kg bag",
             "phi_days": "N/A", "notes": "Mix into beans at storage. Standard grain protectant in Zimbabwe"},
            {"name": "Phosphine tablets (Phostoxin)", "rate": "1-2 tablets per m3 of sealed space",
             "phi_days": "7", "notes": "Fumigation for large quantities. Must be gas-tight."},
        ],
        biological_control=[
            "Hermetic storage (PICS bags, metal silos) — suffocates insects without chemicals",
            "Diatomaceous earth (Fossil Shield) as non-toxic grain protectant",
        ],
        cultural_control=[
            "Harvest promptly at maturity — do not leave dry pods in the field",
            "Clean store thoroughly before loading new harvest",
            "Dry beans to <12% moisture before storage",
            "Use hermetic (airtight) storage bags (PICS, GrainPro)",
            "Inspect stored beans monthly for exit holes and live insects",
        ],
        scouting_protocol=(
            "Inspect stored beans monthly. Take 1 kg samples from top, middle, and "
            "bottom of the store. Sieve out adults and frass. Cut open 100 beans and "
            "check for internal larvae. If any bruchids or exit holes are found, treat "
            "immediately with Actellic Super or move to hermetic storage."
        ),
    ),
]


SUGAR_BEAN_GROWTH_STAGES: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Emergence",
        stage_code="VE",
        day_range=(0, 10),
        water_kc=0.35,
        water_mm_per_week=15,
        critical_nutrients=["P"],
        key_activities=[
            "Plant at 4-5 cm depth into warm, moist soil",
            "Apply basal Compound D at planting",
            "Target 250,000-300,000 plants/ha (45-50cm x 7-10cm)",
            "Inoculate seed with Rhizobium phaseoli if field is new to beans",
            "Scout for bean fly from 7 days after emergence",
        ],
        risks=["Bean fly attack on seedlings", "Damping-off in cold, wet soils",
               "Poor germination from old or cracked seed"],
        scientific_notes=(
            "Phaseolus vulgaris is an epigeal germinator — cotyledons emerge above ground "
            "and serve as first photosynthetic organs. Hypocotyl elongation is sensitive to "
            "soil crusting. Rhizobium inoculation is essential in fields with no recent bean "
            "history. Effective nodulation requires pH >5.5, adequate P and Mo, and specific "
            "Rhizobium strains. Seed treatment with fungicide and insecticide (imidacloprid) "
            "is recommended in bean fly-prone areas."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Vegetative (V1-V4)",
        stage_code="V1-V4",
        day_range=(10, 30),
        water_kc=0.55,
        water_mm_per_week=25,
        critical_nutrients=["N (until nodulation)", "P", "K"],
        key_activities=[
            "Weed control — beans are poor competitors",
            "Scout for bean fly and aphids",
            "Check for Rhizobium nodulation (pink nodules = active)",
            "Do NOT apply nitrogen if nodules are active (inhibits fixation)",
        ],
        risks=["Bean fly damage to stems", "Weed competition", "Aphid colonisation and BCMV transmission"],
        scientific_notes=(
            "Trifoliate leaves expand sequentially. Each node on the main stem produces "
            "a trifoliate leaf and potentially a branch. Root nodules become visible by V2 "
            "and active (pink interior from leghaemoglobin) by V3. Beans fix 40-80 kg N/ha "
            "through biological nitrogen fixation when effectively nodulated. Phosphorus is "
            "critical for both root growth and nodule function. Molybdenum is essential for "
            "nitrogenase enzyme activity."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Flowering (R1-R3)",
        stage_code="R1-R3",
        day_range=(30, 45),
        water_kc=0.85,
        water_mm_per_week=40,
        critical_nutrients=["P", "K", "Ca", "B"],
        key_activities=[
            "Ensure adequate moisture — flowering is very sensitive to drought",
            "Scout for angular leaf spot and anthracnose",
            "Apply fungicide if disease symptoms appear",
            "Do not cultivate — shallow roots are easily damaged",
        ],
        risks=["Drought causing flower abortion", "Angular leaf spot and anthracnose",
               "Halo blight after storms"],
        scientific_notes=(
            "Beans are self-pollinating. Flowering begins at lower nodes and progresses "
            "upward. Water stress during R1-R2 causes 50-80% flower abortion. Calcium and "
            "boron are critical for pollen tube growth and fertilisation. Beans have a "
            "determinate (bush type) or indeterminate growth habit — most Zimbabwe commercial "
            "varieties are determinate Type I or II. Flower abortion is the primary yield "
            "component affected by stress."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Pod Fill (R5-R7)",
        stage_code="R5-R7",
        day_range=(45, 65),
        water_kc=0.80,
        water_mm_per_week=35,
        critical_nutrients=["N (remobilisation)", "K", "S"],
        key_activities=[
            "Maintain moisture — pod fill requires consistent water supply",
            "Scout for pod diseases (anthracnose, angular leaf spot on pods)",
            "Monitor for bruchid beetle adults in the field",
            "Begin planning harvest logistics",
        ],
        risks=["Pod rot from excess rain", "Anthracnose on pods (seed infection)",
               "Bruchid infestation beginning in the field"],
        scientific_notes=(
            "Seed development passes through 3 phases: cell division, cell enlargement "
            "(rapid dry matter accumulation), and maturation (desiccation). Nitrogen is "
            "remobilised from leaves and nodules to developing seed — leaf senescence begins. "
            "Protein content (22-25% for sugar beans) is determined by N remobilisation "
            "efficiency. Potassium supports assimilate transport to pods. Sulphur is needed "
            "for sulphur-containing amino acids (methionine, cysteine) in seed protein."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Maturity (R8-R9)",
        stage_code="R8-R9",
        day_range=(65, 85),
        water_kc=0.30,
        water_mm_per_week=10,
        critical_nutrients=[],
        key_activities=[
            "Reduce irrigation and allow plants to dry down",
            "Harvest when 90% of pods are dry and brown",
            "Pull or cut plants and dry in stooks if weather is wet",
            "Thresh when pods shatter easily — avoid seed cracking",
        ],
        risks=["Rain causing seed discolouration and sprouting", "Shattering losses from delayed harvest",
               "Bruchid beetle infestation of dry pods in the field"],
        scientific_notes=(
            "Physiological maturity (R7) is when maximum seed dry weight is reached. "
            "Harvest maturity (R9) is when pods and seed have dried to <15% moisture. "
            "Excessive drying in the field causes pod shattering. Harvesting at high moisture "
            "followed by controlled drying reduces shattering losses. Seed coat colour and "
            "pattern (important for marketability of sugar beans) is determined genetically "
            "but can be altered by weathering and disease."
        ),
    ),
]


SUGAR_BEAN_FERT = FertilizerSchedule(
    basal={
        "product": "Compound D (7:14:7)",
        "rate_kg_ha": 200,
        "timing": "At planting",
        "placement": "Band 5 cm beside and below seed",
        "nutrients_supplied": {"N": 14, "P2O5": 28, "K2O": 14},
        "notes": "Provides starter N and P. P is critical for nodulation and root growth. "
                 "On very acidic soils, consider SSP (Single Super Phosphate) for extra P.",
    },
    top_dress_1={
        "product": "None if effectively nodulated",
        "rate_kg_ha": 0,
        "timing": "N/A — beans fix their own nitrogen",
        "placement": "N/A",
        "nutrients_supplied": {},
        "notes": "If nodulation has failed (check roots at V3 — white or green nodules indicate failure), "
                 "apply 50 kg/ha AN as rescue nitrogen. Do NOT apply N if pink nodules are present.",
    },
    top_dress_2=None,
    foliar={
        "product": "Molybdenum (sodium molybdate) + Boron (Solubor)",
        "rate_kg_ha": "Na-molybdate 100 g/ha + Solubor 500 g/ha in 200L water",
        "timing": "V2-V3 (2-3 trifoliate leaves)",
        "notes": "Molybdenum is essential for nitrogenase activity in Rhizobium. "
                 "Often deficient on acid soils. Boron supports flowering and pod set.",
    },
    liming={
        "product": "Dolomitic lime",
        "rate_kg_ha": "As per soil test, typically 500-1500 kg/ha",
        "timing": "Apply 2-3 months before planting, incorporate",
        "notes": "Beans require pH >5.5 for effective nodulation. "
                 "Liming also improves P availability and provides Ca and Mg.",
    },
    notes=(
        "Beans are a low-input crop when Rhizobium inoculation is successful. "
        "Total N fixation is 40-80 kg/ha. Residual N benefits the following cereal crop. "
        "Avoid excessive N fertiliser — it suppresses nodulation and promotes vegetative "
        "growth at the expense of pods. P is the most yield-limiting nutrient for beans."
    ),
)


SUGAR_BEAN_PLANTING_WINDOWS: List[PlantingWindow] = [
    PlantingWindow(
        region="NR I (Eastern Highlands)",
        optimal_start="November 1",
        optimal_end="December 15",
        acceptable_start="October 15",
        acceptable_end="January 15",
        notes="Can also be grown as a late summer crop (Feb-Apr) in warm parts. "
              "Watch for halo blight in cool, wet conditions.",
    ),
    PlantingWindow(
        region="NR II (Mashonaland)",
        optimal_start="November 15",
        optimal_end="December 31",
        acceptable_start="November 1",
        acceptable_end="January 15",
        notes="Main bean production zone. Plant with first reliable rains. "
              "Can also be relay-planted into maize at tasseling.",
    ),
    PlantingWindow(
        region="NR III (Semi-intensive)",
        optimal_start="December 1",
        optimal_end="January 7",
        acceptable_start="November 15",
        acceptable_end="January 31",
        notes="Shorter rainy season — use early-maturing varieties (Gloria, 75 days). "
              "Ensure maturity before rains end.",
    ),
    PlantingWindow(
        region="NR IV (Semi-extensive)",
        optimal_start="December 15",
        optimal_end="January 15",
        acceptable_start="December 1",
        acceptable_end="January 31",
        notes="Marginal for beans — moisture often insufficient. "
              "Plant on vlei margins or with supplemental irrigation.",
    ),
    PlantingWindow(
        region="NR V (Lowveld)",
        optimal_start="N/A",
        optimal_end="N/A",
        acceptable_start="N/A",
        acceptable_end="N/A",
        notes="Too hot and dry for dryland beans. Only under irrigation (e.g., winter crop).",
    ),
]


PROFILE = CropProfile(
    crop_name="Sugar Beans",
    scientific_name="Phaseolus vulgaris",
    family="Fabaceae",
    optimal_ph=(5.8, 7.0),
    critical_ph_low=5.0,
    optimal_soil_types=["fersiallitic", "siallitic"],
    avoid_soil_types=["waterlogged", "heavy vertisol (poor drainage)", "very acidic (pH <5.0)"],
    optimal_temp=(18.0, 28.0),
    critical_temp_low=10.0,
    critical_temp_high=32.0,
    base_temp_gdd=10.0,
    total_water_mm=350.0,
    growth_stages=SUGAR_BEAN_GROWTH_STAGES,
    fertilizer_schedule=SUGAR_BEAN_FERT,
    diseases=SUGAR_BEAN_DISEASES,
    pests=SUGAR_BEAN_PESTS,
    planting_windows=SUGAR_BEAN_PLANTING_WINDOWS,
    harvest_moisture="Pull or cut plants when 90% of pods are dry. Thresh at 12-14% seed moisture.",
    storage_conditions="Dry to <12% moisture. Store in hermetic bags (PICS) or treat with "
                       "Actellic Super Dust for bruchid protection. Keep in cool, dry store. "
                       "Beans maintain viability for 2-3 years if stored dry.",
    post_harvest_notes="Thresh by hand or small thresher — avoid cracking seed coats. "
                       "Grade by size and colour (sugar beans must have characteristic "
                       "red-speckled pattern). Remove discoloured, broken, and insect-damaged beans. "
                       "Pack in clean bags for market.",
    natural_region_suitability={
        "NR I": "Well suited — cool, moist conditions ideal",
        "NR II": "Primary production zone — excellent for beans",
        "NR III": "Good with early-maturing varieties",
        "NR IV": "Marginal — only on bottomlands or with irrigation",
        "NR V": "Not recommended for dryland; irrigated winter crop possible",
    },
)

ALIASES = ["beans", "dry beans", "common beans"]
