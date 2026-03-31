"""Cassava (Manihot esculenta) — Zimbabwe's drought-tolerant food security root crop.

Cassava is a critical subsistence and commercial crop across Zimbabwe's NR III-V, prized
for its extraordinary drought tolerance, flexible harvest window (8-24+ months), and
nutritional density. It serves as both a staple food (processed into flour/meal) and a
famine reserve crop. Cyanogenic glycoside management is essential — bitter varieties
require thorough processing before consumption. Stake planting from October-December
aligns harvest with the dry season, enabling field storage on the plant.
"""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List


# ---------------------------------------------------------------------------
# DISEASES
# ---------------------------------------------------------------------------

CASSAVA_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Cassava Mosaic Disease (CMD)",
        pathogen="East African Cassava Mosaic Virus (EACMV) and related begomoviruses — Family Geminiviridae",
        pathogen_type="viral",
        symptoms=[
            "Yellow-green mosaic or chlorotic patches on leaves — classic 'mosaic' pattern",
            "Leaf distortion, curling, and puckering along the midrib",
            "Reduced leaf size (microphylly) on severely affected plants",
            "Stunted plant growth and reduced canopy in severe infections",
            "Swollen veins and chlorotic rings in some strains",
            "Root yield reduction of 20-90% depending on variety and infection timing",
        ],
        identification_markers=[
            "Yellow-green mosaic on leaves — distinct from nutrient deficiency which is uniform",
            "Symptoms most visible on young expanding leaves; older leaves may recover partially",
            "Whitefly (Bemisia tabaci) colonies on leaf undersides confirm vector presence",
            "Mosaic persists under all weather conditions — not environment-dependent",
            "Infected planting material (stakes) will show symptoms within 4-6 weeks",
            "Use PCR or ELISA test at Plant Protection Research Institute (PPRI) for confirmation",
        ],
        favourable_conditions={
            "humidity_min": 60,
            "temp_min_c": 24,
            "temp_max_c": 34,
            "note": (
                "CMD is transmitted by whitefly (Bemisia tabaci) in a persistent, circulative "
                "manner. Whitefly populations peak during warm, dry conditions (Sept-Nov) which "
                "coincide with planting windows. More critically, CMD spreads through infected "
                "planting material — vegetative propagation moves the virus directly into new "
                "fields. Fields replanted from farmer-saved stakes from infected crops are at "
                "highest risk regardless of whitefly pressure."
            ),
        },
        susceptible_stages=["Establishment", "Canopy Development", "Root Bulking"],
        resistant_varieties=[
            "IITA CMD-resistant lines: TME 14, TME 419",
            "CIMMYT/Zimbabwe releases screened for CMD tolerance",
            "Any variety derived from CMD-resistant parent lines with appropriate R-gene stacking",
        ],
        susceptible_varieties=[
            "Most unimproved local landraces",
            "Farmer-selected sweet varieties without formal disease screening",
        ],
        chemical_control=[
            {
                "name": "Imidacloprid 70 WS (stake dip / soil drench)",
                "rate": "1 g a.i./L water — soak stakes 5 min before planting",
                "phi_days": "Systemic, persists 6-8 weeks",
                "notes": "Suppresses whitefly populations in early establishment; does NOT cure CMD "
                         "but delays secondary spread. Use only as part of integrated strategy.",
            },
            {
                "name": "Thiamethoxam 25 WG (foliar, whitefly suppression)",
                "rate": "200 g/ha",
                "phi_days": "7",
                "notes": "Apply at first sign of whitefly colonies; rotate with different chemistry "
                         "to prevent resistance development.",
            },
        ],
        biological_control=[
            "Encarsia formosa (parasitoid wasp) for whitefly biocontrol in nurseries",
            "Beauveria bassiana spray against whitefly adults and nymphs",
            "Conservation of natural predators: Chrysopa spp. (lacewings), Coccinellidae (ladybirds)",
            "Remove and burn infected plants immediately to reduce virus reservoir",
        ],
        cultural_control=[
            "MOST IMPORTANT: Use only certified disease-free planting stakes from clean nurseries",
            "Roguing: remove and burn CMD-symptomatic plants within 2 weeks of detection",
            "Source stakes from plants that have been screened and found CMD-free",
            "Do not save stakes from infected crops for replanting",
            "Plant resistant or tolerant varieties — this is the single most effective strategy",
            "Synchronise planting in communities to reduce virus reservoir between plots",
            "Avoid planting near abandoned cassava fields which serve as inoculum reservoirs",
            "Maintain 1 m border rows of non-host crops to reduce whitefly migration",
        ],
        economic_threshold=(
            "Any CMD infection before 3 months after planting warrants rouging infected plants "
            "if they are < 20% of the stand. If > 40% of plants show CMD symptoms, consider "
            "replanting the entire field with clean, resistant material."
        ),
        severity_scale={
            "mild": "< 20% plants affected, mosaic limited to upper canopy, root yield loss < 15%",
            "moderate": "20-50% plants symptomatic, visible stunting, root yield loss 15-50%",
            "severe": "> 50% plants severely affected, widespread stunting, root yield loss 50-90%; "
                      "field may not be economically viable — consider emergency replanting",
        },
    ),
    DiseaseProfile(
        name="Cassava Brown Streak Disease (CBSD)",
        pathogen="Cassava Brown Streak Virus (CBSV) and Ugandan CBSV (UCBSV) — Family Potyviridae",
        pathogen_type="viral",
        symptoms=[
            "Yellow-green chlorotic patches along leaf veins — feathery or blotchy pattern",
            "Brown streaks and necrotic lesions on green stems (diagnostic feature)",
            "Root necrosis: brown corky rot inside roots — roots appear healthy externally",
            "Dry brown to black corky areas in root flesh when cut open",
            "Premature leaf drop in severe infections",
            "Root symptoms most severe and economically devastating — roots become inedible",
        ],
        identification_markers=[
            "KEY DIAGNOSTIC: Cut roots and look for internal brown/black corky necrosis",
            "Brown necrotic streaks on green stem tissue — distinct from normal stem coloration",
            "Chlorotic leaf symptoms less pronounced than CMD — often yellow-green blotches",
            "Whitefly (Bemisia tabaci) is also the vector for CBSD",
            "CBSD is confirmed by RT-PCR at PPRI Harare — visual diagnosis can be uncertain",
            "Root necrosis makes even visually mild infections economically serious",
        ],
        favourable_conditions={
            "humidity_min": 65,
            "temp_min_c": 20,
            "temp_max_c": 30,
            "note": (
                "CBSD is primarily a concern in East Africa (Tanzania, Uganda, Kenya) but has "
                "been recorded spreading southward. Risk to Zimbabwe increases with climate change "
                "and movement of planting material across borders. Like CMD, it spreads through "
                "infected stakes and via Bemisia tabaci whitefly. CBSD is arguably more dangerous "
                "than CMD because root necrosis can render harvests totally unmarketable while "
                "the plant looks nearly normal above ground — meaning losses go undetected."
            ),
        },
        susceptible_stages=["Establishment", "Root Bulking", "Maturation"],
        resistant_varieties=[
            "IITA CBSD-tolerant breeding lines: NASE 14, NASE 19",
            "CBSD resistance is being pyramid-bred into CMD-resistant backgrounds",
            "Consult CIMMYT Zimbabwe and ZARI (Harare Research Station) for current releases",
        ],
        susceptible_varieties=[
            "Most traditional landraces lack CBSD resistance",
            "Some CMD-resistant varieties remain CBSD-susceptible",
        ],
        chemical_control=[
            {
                "name": "Imidacloprid 70 WS (stake treatment)",
                "rate": "1 g a.i./L — as for CMD control",
                "phi_days": "Systemic, 6-8 weeks",
                "notes": "Suppresses whitefly vector but does not eliminate CBSD once established",
            },
        ],
        biological_control=[
            "Same whitefly biocontrol agents as CMD (Encarsia formosa, Beauveria bassiana)",
            "Remove and destroy infected plants and roots immediately",
        ],
        cultural_control=[
            "Use certified CBSD-free planting material — most critical management step",
            "Do not import stakes from high-risk areas (eastern Africa) without disease testing",
            "Harvest roots as soon as they reach marketable size — do not leave CBSD-infected "
            "crops in ground as root necrosis progresses with time",
            "At harvest, cut roots and inspect for necrosis before storage or sale",
            "Reject visually affected roots — do not process for food as necrotic tissue "
            "renders flour bitter and nutrient-poor",
            "Report suspected CBSD to AGRITEX for official diagnostic confirmation",
        ],
        economic_threshold=(
            "Given CBSD's quarantine status in Zimbabwe: zero-tolerance policy. "
            "Any suspected CBSD must be reported to plant protection authorities. "
            "Even 10% root necrosis at harvest can render a batch unmarketable."
        ),
        severity_scale={
            "mild": "Leaf symptoms only, root necrosis < 10% volume, roots partly usable",
            "moderate": "Stem streaking and 10-30% root necrosis, significant quality loss",
            "severe": "> 30% root necrosis, roots largely inedible, total commercial loss; "
                      "field must be destroyed and site rested for 2 seasons minimum",
        },
    ),
    DiseaseProfile(
        name="Cassava Bacterial Blight (CBB)",
        pathogen="Xanthomonas axonopodis pv. manihotis (Xam)",
        pathogen_type="bacterial",
        symptoms=[
            "Angular water-soaked leaf spots bounded by leaf veins — classic bacterial pattern",
            "Spots turn brown to black with yellow halo on surrounding tissue",
            "Leaf blight: large brown necrotic areas with wilting in severe cases",
            "Dieback of shoot tips — terminal bud dies, leaves hang and wither",
            "Bacterial exudate (gum/slime) on stem lesions in humid conditions",
            "Vascular discolouration: brownish streaks in stem cross-section",
            "Systemic infection can kill young plants; older plants show chronic dieback",
        ],
        identification_markers=[
            "Angular spots bounded by veins — distinguishes CBB from fungal leaf spots",
            "Yellow-brown water-soaked margins around lesions in early morning",
            "Gummy exudate on cut stems in humid weather",
            "Shoot tip dieback with brownish vascular streaking in stem",
            "Symptoms worsen after rain followed by hot dry winds (stomatal infection pathway)",
            "Bacterial streaming from cut stem in water drop under microscope confirms bacteria",
        ],
        favourable_conditions={
            "humidity_min": 80,
            "temp_min_c": 25,
            "temp_max_c": 35,
            "rainfall_note": "Rain-splash spreads bacteria; alternating wet-dry cycles worsen symptoms",
            "note": (
                "CBB thrives in warm, humid conditions with frequent rainfall. Infected planting "
                "material is the primary long-distance dispersal route. Rain-splash, insects, "
                "farm tools, and animal movement spread bacteria within and between fields. "
                "Wounds from nematodes, insects, or cultivation facilitate entry. NR II-III "
                "during peak rainy season (January-March) is highest risk period."
            ),
        },
        susceptible_stages=["Establishment", "Canopy Development", "Root Bulking"],
        resistant_varieties=[
            "TMS 30001 (moderate resistance)",
            "Some IITA improved varieties with partial CBB resistance",
            "Varieties screened at ZARI Harare Research Station",
        ],
        susceptible_varieties=[
            "Most local landraces",
            "Varieties propagated from infected stem material",
        ],
        chemical_control=[
            {
                "name": "Copper oxychloride 50 WP",
                "rate": "2.5 kg/ha",
                "phi_days": "14",
                "notes": "Apply as protective spray at onset of rainy season; "
                         "repeat every 14 days in wet conditions",
            },
            {
                "name": "Mancozeb + Copper (Curzate M8, Ridomil Gold Cu)",
                "rate": "2.0-2.5 kg/ha",
                "phi_days": "14",
                "notes": "More systemic coverage; useful when symptoms are establishing",
            },
        ],
        biological_control=[
            "Bacillus subtilis-based biofungicides (e.g. Serenade) with some bacteriostatic effect",
            "Trichoderma applications to soil to improve plant root vigour",
            "Avoid wounding during cultivation — use clean, disinfected tools",
        ],
        cultural_control=[
            "Use healthy, disease-free stakes sourced from clean material",
            "Treat stakes with Copper oxychloride solution (2.5%) before planting",
            "Avoid planting during the wet season when bacteria spread rapidly",
            "Remove and destroy affected plant parts immediately",
            "Disinfect pruning/harvesting tools between plants (bleach or 70% alcohol)",
            "Avoid overhead irrigation — use furrow or drip where possible",
            "Rotate cassava with non-host crops (maize, legumes) for at least 1 season",
            "Do not work in cassava fields when foliage is wet",
        ],
        economic_threshold="5% of plants showing shoot tip dieback warrants copper spray application",
        severity_scale={
            "mild": "Scattered leaf spots, no dieback, < 10% canopy affected",
            "moderate": "Leaf blight on 10-30% of canopy, some shoot tip dieback, 15-25% yield loss",
            "severe": "> 30% canopy blighted, widespread dieback and vascular streaking, "
                      "30-60% yield loss; replant with resistant variety after soil rest",
        },
    ),
    DiseaseProfile(
        name="Cassava Anthracnose Disease (CAD)",
        pathogen="Colletotrichum gloeosporioides (syn. Glomerella gloeosporioides)",
        pathogen_type="fungal",
        symptoms=[
            "Dieback of stem tips — young shoots wilt and brown from apex downward",
            "Dark brown to black lesions on stems with concentric rings",
            "Sunken, oval to irregular cankers on green stems",
            "Orange spore masses (acervuli) visible on lesions in humid conditions",
            "Leaf spots: circular brown lesions with darker margins",
            "Defoliation in severe cases reducing photosynthetic capacity",
            "Canker girdle can kill branches above the lesion",
        ],
        identification_markers=[
            "Orange-salmon spore masses (acervuli) on stem lesions — diagnostic feature",
            "Sunken stem cankers with concentric ring pattern",
            "Dieback progression from stem tips downward",
            "Distinct from CBB: CAD has fungal sporulation; CBB has bacterial gum",
            "Use hand lens to confirm acervuli in lesion centre",
        ],
        favourable_conditions={
            "humidity_min": 80,
            "temp_min_c": 22,
            "temp_max_c": 30,
            "leaf_wetness_hours": 10,
            "note": (
                "CAD is favoured by warm, humid conditions with prolonged leaf wetness. "
                "The fungus colonises stem wounds, insect damage, and growing points. "
                "Spreads by rain-splash and movement of infected planting material. "
                "Stress conditions (drought, nutrient deficiency) predispose plants to infection. "
                "Dense plantings that reduce air circulation increase CAD severity."
            ),
        },
        susceptible_stages=["Establishment", "Canopy Development"],
        resistant_varieties=[
            "Some improved IITA varieties show field tolerance",
            "Varieties with compact growth habit and fewer wound points are less affected",
        ],
        susceptible_varieties=[
            "Most local landraces under dense planting and poor nutrition",
        ],
        chemical_control=[
            {
                "name": "Thiram 80 WP (stake dip pre-planting)",
                "rate": "3 g/kg — dip stake bases in slurry for 5 min",
                "phi_days": "N/A",
                "notes": "Protects newly planted stakes during establishment",
            },
            {
                "name": "Mancozeb 80 WP",
                "rate": "2.0-2.5 kg/ha",
                "phi_days": "14",
                "notes": "Protectant foliar spray during wet season; target young stems",
            },
            {
                "name": "Azoxystrobin 25 SC",
                "rate": "1.0 L/ha",
                "phi_days": "14",
                "notes": "Systemic strobilurin; use when cankers are developing on stems",
            },
        ],
        biological_control=[
            "Trichoderma harzianum applied to planting holes reduces soil inoculum",
            "Pruning out infected stems during dry weather reduces spread",
        ],
        cultural_control=[
            "Select healthy planting stakes without lesions",
            "Treat stake bases with fungicide dip before planting",
            "Space plants to ensure good air circulation (1 m x 1 m minimum)",
            "Remove and burn infected stem tips promptly",
            "Avoid mechanical wounding during inter-row cultivation",
            "Apply balanced fertiliser — vigorous plants resist CAD better",
            "Prune lower branches to improve air movement under canopy",
        ],
        economic_threshold="Dieback on 15% of stems, or stem cankers reaching main trunk",
        severity_scale={
            "mild": "Tip dieback on < 15% of stems, leaf spots minor, minimal yield impact",
            "moderate": "Dieback on 15-40% of stems, cankers girdling some branches",
            "severe": "> 40% stems affected with cankers reaching main stems; "
                      "significant defoliation and 20-40% root yield loss",
        },
    ),
]


# ---------------------------------------------------------------------------
# PESTS
# ---------------------------------------------------------------------------

CASSAVA_PESTS: List[PestProfile] = [
    PestProfile(
        name="Cassava Green Mite",
        scientific_name="Mononychellus tanajoa",
        pest_type="mite",
        identification=[
            "Extremely tiny (0.3-0.5 mm) — green to pale yellow colour, barely visible naked eye",
            "Females have two dark spots on the body (diagnostic with hand lens)",
            "Colonies form on undersides of young leaves and growing tips",
            "Fine webbing visible between leaf veins and on growing points in heavy infestations",
            "Eggs: round, pale, deposited on leaf undersides along veins",
            "Use 10x hand lens — look for moving specks under young leaves",
        ],
        damage_symptoms=[
            "Chlorotic stippling on upper leaf surface — yellow-green spots where mites have fed",
            "Distortion and stunting of young leaves — 'bunchy top' appearance",
            "Dying growing tips with characteristic angular, distorted young leaves",
            "Severe bronzing of leaves before shedding",
            "Reduced leaf size and abnormal leaf shape on newly expanding leaves",
            "Root yield losses of 30-80% in severe unmanaged infestations",
            "Drought conditions dramatically amplify damage — water-stressed plants most vulnerable",
        ],
        life_cycle_notes=(
            "Mononychellus tanajoa completes development from egg to adult in 7-10 days at 30°C. "
            "Females lay 3-5 eggs per day, living 15-20 days total. Populations can increase "
            "exponentially in 2-3 weeks under hot, dry conditions. Dispersal is primarily by "
            "wind on silk threads (ballooning) and through infested planting material. Populations "
            "crash when humidity rises above 85% or rainfall occurs — rain physically dislodges "
            "mites and promotes entomopathogenic fungi. Dry-season cassava (Oct-Dec planting) "
            "faces peak mite pressure during establishment before canopy closure."
        ),
        favourable_conditions={
            "temp_min_c": 28,
            "temp_max_c": 38,
            "humidity_max": 60,
            "note": (
                "Cassava green mite thrives in hot, dry conditions — exactly those of Zimbabwe's "
                "NR IV-V during establishment (Oct-Dec). Drought stress on host plants simultaneously "
                "increases plant susceptibility and accelerates mite population growth. Acaricide "
                "use that kills predatory mites causes resurgence. Conservation of natural enemies "
                "(Phytoseiidae predatory mites, Typhlodromalus aripo) is critical."
            ),
        },
        susceptible_stages=["Establishment", "Canopy Development"],
        economic_threshold="5 mites per young leaf, or visible chlorotic stippling on > 20% of young leaves",
        chemical_control=[
            {
                "name": "Abamectin 18 EC",
                "rate": "500-750 mL/ha",
                "phi_days": "7",
                "notes": "Most effective registered miticide; apply when populations exceed threshold. "
                         "Targets all motile stages. Avoid broad-spectrum insecticides that kill "
                         "predatory mites and cause secondary outbreak.",
            },
            {
                "name": "Bifenazate 240 SC",
                "rate": "400 mL/ha",
                "phi_days": "7",
                "notes": "Specific miticide with low impact on predatory mites; rotate with abamectin",
            },
            {
                "name": "Sulphur 80 WP (wettable sulphur)",
                "rate": "3 kg/ha",
                "phi_days": "3",
                "notes": "Contact miticide; effective and cheap. Avoid application above 30°C "
                         "(phytotoxicity risk). Good for early-season preventive sprays.",
            },
        ],
        biological_control=[
            "Typhlodromalus aripo (Phytoseiidae predatory mite) — commercially available from CABI; "
            "natural enemy released in Africa specifically for CGM control with excellent results",
            "Neoseiulus californicus and Phytoseiulus persimilis (predatory mites) conserved by "
            "avoiding broad-spectrum acaricides",
            "Beauveria bassiana wettable powder (entomopathogenic fungus) — apply in evening when "
            "humidity is higher; requires 5+ days of humid conditions to establish",
            "Intercropping with cowpea or other plants that harbour predatory mite refuges",
        ],
        cultural_control=[
            "Use pest-free planting stakes — inspect bases and upper nodes for mite colonies",
            "Dip stakes in water (45°C for 10 min) before planting to kill mites on stakes",
            "Irrigate during dry-season planting — mite populations crash when canopy closes",
            "Avoid planting during peak hot-dry season if alternatives exist",
            "Remove severely infested growing tips and burn",
            "Intercrop cassava with cowpea or soybean to increase biodiversity and predatory mite habitat",
            "Avoid pyrethroid and organophosphate sprays that eliminate predatory mites",
            "Maintain plant vigour through appropriate fertilisation — well-nourished plants "
            "tolerate mite feeding better",
        ],
        scouting_protocol=(
            "Scout weekly from 2 weeks after planting through canopy closure (0-12 weeks). "
            "Examine the 3 youngest fully expanded leaves on 20 plants across the field "
            "(W-pattern sampling). Use 10x hand lens on leaf undersides near growing tips. "
            "Count mites per leaf and note symptoms (stippling, distortion). "
            "Also examine growing points for 'bunchy top' symptoms. "
            "Record percentage of plants with mite colonies and severity score (1-5 scale). "
            "Spray if > 5 mites per young leaf on > 20% of sampled plants. "
            "After any spray, resample 5-7 days later to confirm efficacy."
        ),
    ),
    PestProfile(
        name="Cassava Mealybug",
        scientific_name="Phenacoccus manihoti",
        pest_type="insect",
        identification=[
            "White, cottony-waxy oval insects, 2-3 mm long, covered in mealy wax",
            "Female colonies form dense white masses at growing tips and leaf nodes",
            "Males: tiny winged flies, rarely seen; most reproduction is parthenogenetic",
            "Eggs: laid in white waxy ovisac attached to plant tissue",
            "Crawlers (mobile nymphs): pale yellow, 0.3 mm, disperse before waxing over",
            "Easily identified by white waxy coating and colonies clustered at stem nodes",
        ],
        damage_symptoms=[
            "Characteristic 'bunchy top' — growing tips form tight cluster of stunted, distorted leaves",
            "Severe stunting of the whole plant under heavy infestation",
            "Yellowing and distortion of leaves at growing tips",
            "Sooty mould growing on honeydew excreted by mealybugs",
            "Stem nodes covered in white waxy masses with associated ant activity",
            "Complete loss of growing tips in extreme infestations",
            "Root yield losses of 40-60% common in unmanaged outbreak years",
        ],
        life_cycle_notes=(
            "Phenacoccus manihoti is a major invasive pest of African cassava, introduced from "
            "South America (origin of cassava) in the 1970s. Females reproduce parthenogenetically, "
            "laying 400-500 eggs in a waxy ovisac. Crawlers hatch and move to new growing tips. "
            "Generation time is 30-40 days. Populations build most rapidly in hot, dry conditions "
            "(NR IV-V, September-November). Long-distance spread occurs through infested planting "
            "material. Ants protect mealybug colonies from predators by farming them for honeydew — "
            "controlling ants can significantly help biological control of mealybugs."
        ),
        favourable_conditions={
            "temp_min_c": 25,
            "temp_max_c": 35,
            "humidity_max": 65,
            "note": (
                "Dry, hot conditions strongly favour P. manihoti population build-up. "
                "Rain directly kills mealybugs (physical dislodgement and fungal infection). "
                "Ant mutualism is common — ant activity at nodes is an early warning sign. "
                "Stressed, under-fertilised plants are most severely damaged."
            ),
        },
        susceptible_stages=["Establishment", "Canopy Development", "Root Bulking"],
        economic_threshold="1 mealybug colony per growing tip on > 10% of scouted plants",
        chemical_control=[
            {
                "name": "Imidacloprid 200 SL (systemic)",
                "rate": "350 mL/ha",
                "phi_days": "7",
                "notes": "Systemic neonicotinoid; applied as soil drench at base of stem or "
                         "foliar spray to young plants. Good uptake into meristems where mealybugs feed.",
            },
            {
                "name": "Thiamethoxam 25 WG",
                "rate": "200 g/ha",
                "phi_days": "7",
                "notes": "Systemic; effective against mealybug crawlers and settled nymphs",
            },
            {
                "name": "Chlorpyrifos 48 EC",
                "rate": "1.5 L/ha",
                "phi_days": "14",
                "notes": "Contact organophosphate; must penetrate waxy coating — use with "
                         "spreader-sticker adjuvant. Less preferred as it kills natural enemies.",
            },
        ],
        biological_control=[
            "Anagyrus lopezi (Encyrtidae parasitic wasp) — the primary and most successful "
            "biocontrol agent for P. manihoti in Africa; introduced through IITA and now "
            "established across sub-Saharan Africa including Zimbabwe",
            "Epidinocarsis lopezi — parasitoid wasp established in East/Southern Africa",
            "Chrysoperla carnea (lacewing) predates on mealybug crawlers",
            "Entomopathogenic fungi: Beauveria bassiana and Isaria fumosorosea are effective "
            "when humidity is adequate — apply in late afternoon",
        ],
        cultural_control=[
            "Use clean, mealybug-free planting material — inspect stakes at all nodes",
            "Quarantine new planting material and observe for 2-3 weeks before field planting",
            "Control ants with banding (sticky bands around stems) or bait stations — "
            "ants protect mealybugs from parasitoids and predators",
            "Remove and destroy heavily infested growing tips during early infestations",
            "Maintain plant vigour through appropriate fertilisation and soil moisture",
            "Avoid monoculture cassava over large areas — diversified planting patterns "
            "reduce mealybug dispersal and build up of parasite populations",
            "Harvest and remove crop residue promptly after harvest to reduce carryover",
        ],
        scouting_protocol=(
            "Scout weekly from planting through 20 weeks after establishment. "
            "Walk a W-pattern, examining 30 plants at 5 stops (150 plants total). "
            "Inspect growing tips and upper 3 leaf nodes for white waxy colonies. "
            "Note ant activity — ants tending colonies at nodes is an early warning. "
            "Record: % plants with mealybug colonies, average colony size (1-5 scale), "
            "presence of parasitised (dark/mummified) mealybugs. "
            "If > 10% of plants have active colonies AND parasitoid activity is low, "
            "apply targeted spray to affected plants. If parasitoids are active "
            "(visible mummies), hold off chemical spray to conserve natural enemies."
        ),
    ),
    PestProfile(
        name="Silverleaf Whitefly (Cassava Whitefly)",
        scientific_name="Bemisia tabaci",
        pest_type="insect",
        identification=[
            "Adult: tiny white-winged insect, 1-1.5 mm, wings held tent-like over body",
            "When disturbed, adults fly up in a cloud from leaf undersides",
            "Nymphs (scales): flat, oval, pale green-yellow, 0.5-1 mm, sessile on leaf undersides",
            "Eggs: pale yellow, deposited in arcs on undersides of young leaves",
            "Pupae: white, slightly raised, oval, with fringe of wax filaments",
            "Sooty mould on honeydew deposits confirms active colony",
        ],
        damage_symptoms=[
            "Direct feeding damage: yellowing and silvering of leaves (from toxic saliva of B biotype)",
            "Sooty mould growth on honeydew reduces photosynthesis",
            "Wilting and premature leaf drop under severe colony pressure",
            "MOST IMPORTANTLY: Bemisia tabaci is the primary vector of CMD and CBSD viruses",
            "Even low whitefly populations can transmit CMD/CBSD to healthy plants",
            "Indirect virus transmission damage far exceeds direct feeding damage",
        ],
        life_cycle_notes=(
            "Bemisia tabaci has biotype B (= silverleaf whitefly) and many other biotypes "
            "present in Zimbabwe. Eggs hatch in 6-8 days; nymphs pass through 4 instars over "
            "14-21 days; adults live 30-40 days. Females lay 100-200 eggs. Multiple overlapping "
            "generations occur throughout the rainy season. High-temperature, low-humidity "
            "conditions favour population explosions. Insecticide resistance is widespread — "
            "resistance management through rotation of chemistry classes is essential."
        ),
        favourable_conditions={
            "temp_min_c": 24,
            "temp_max_c": 34,
            "humidity_max": 70,
            "note": (
                "Whitefly populations peak in the hot, dry pre-season (September-November) "
                "when cassava fields are being established. This is also the period when "
                "CMD/CBSD transmission risk is highest. Dry conditions inhibit entomopathogenic "
                "fungi that normally suppress whitefly populations."
            ),
        },
        susceptible_stages=["Establishment", "Canopy Development", "Root Bulking"],
        economic_threshold=(
            "For direct feeding: > 50 adults per leaf on > 30% of plants. "
            "For virus transmission: any whitefly in CMD/CBSD-endemic areas warrants preventive "
            "management — there is effectively no 'safe' threshold for virus vector populations."
        ),
        chemical_control=[
            {
                "name": "Imidacloprid 70 WS (stake drench pre-planting)",
                "rate": "1 g a.i./L — soak stake bases or drench planting holes",
                "phi_days": "Systemic, 6-8 weeks",
                "notes": "Best preventive treatment at planting; suppresses whitefly during "
                         "critical establishment period when CMD/CBSD transmission risk is highest",
            },
            {
                "name": "Spiromesifen 240 SC",
                "rate": "500 mL/ha",
                "phi_days": "7",
                "notes": "Inhibits lipid biosynthesis; effective on nymphs and eggs; "
                         "rotate with neonicotinoids to manage resistance",
            },
            {
                "name": "Pymetrozine 50 WG",
                "rate": "200 g/ha",
                "phi_days": "7",
                "notes": "Selective feeding inhibitor; low impact on beneficial insects; "
                         "good resistance management option",
            },
        ],
        biological_control=[
            "Encarsia formosa and Eretmocerus spp. (parasitoid wasps) — conserve by avoiding "
            "broad-spectrum pyrethroids",
            "Beauveria bassiana and Isaria fumosorosea sprays during humid weather",
            "Yellow sticky traps to monitor adult populations and provide mass trapping",
            "Reflective mulch (silver polyethylene) confuses and repels adult whiteflies "
            "during crop establishment — reduces CMD transmission significantly",
        ],
        cultural_control=[
            "Use CMD/CBSD-resistant varieties to reduce the consequence of whitefly feeding",
            "Use virus-free planting material — whitefly management alone is insufficient "
            "if infective virus sources are present",
            "Plant synchronously across a community to reduce the period of exposure",
            "Remove and destroy volunteer cassava and weed hosts near planting sites",
            "Intercropping with cowpea, okra, or maize physically disrupts whitefly dispersal",
            "Avoid planting near old infected cassava fields which serve as virus reservoirs",
            "Maintain field hygiene — remove plant debris after harvest",
        ],
        scouting_protocol=(
            "Scout weekly from 2 weeks after planting through canopy closure. "
            "Examine the 3 youngest fully expanded leaves on 20 plants per field. "
            "Count adult whiteflies per leaf (or estimate scale: 1=1-5, 2=6-20, 3=21-50, "
            "4=51-100, 5=>100). Inspect leaf undersides for nymphal colonies. "
            "Deploy yellow sticky traps (4 per ha) at 30 cm above canopy height — "
            "count adults caught per trap per week to track population trends. "
            "Record any CMD/CBSD symptoms on visited plants — correlate with whitefly counts. "
            "Prioritise management when: trapped >20 adults/trap/week OR nymphal colonies "
            "present on >20% of sampled leaves."
        ),
    ),
]


# ---------------------------------------------------------------------------
# GROWTH STAGES
# ---------------------------------------------------------------------------

CASSAVA_GROWTH_STAGES: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Establishment",
        stage_code="GS1",
        day_range=(0, 60),
        water_kc=0.30,
        water_mm_per_week=18,
        critical_nutrients=["P", "K", "N"],
        key_activities=[
            "Plant stakes horizontally (5-8 cm deep) or at 45-degree angle in prepared ridges",
            "Use stakes 20-30 cm long with 3-5 nodes from mid-portion of 8-12 month-old stems",
            "Apply basal Compound D (250 kg/ha) in band or spot placement 5-10 cm from stake",
            "Target planting density: 10,000 plants/ha (1 m x 1 m) for sole crop",
            "Scout for green mite and mealybug weekly — populations build fast on young tips",
            "Weed control critical — cassava is slow to establish canopy",
            "If dry-season planting, irrigate at planting and weekly until first rain",
        ],
        risks=[
            "Poor stake sprouting from old, dried, or diseased material",
            "Cassava green mite colonies on growing tips before canopy closure",
            "Mealybug infestation causing bunchy top on young plants",
            "Whitefly CMD transmission from nearby infected fields",
            "Weed competition — cassava is not competitive until 8-10 weeks old",
            "Stake rotting in waterlogged or very heavy soils",
        ],
        scientific_notes=(
            "Cassava propagation is vegetative — stems (stakes) develop adventitious roots from "
            "nodes within 7-14 days of planting. The cuttings rely entirely on carbohydrate and "
            "nutrient reserves stored in the stem tissue for initial sprouting. Shoot growth "
            "emerges from axillary buds at stem nodes. Root development proceeds simultaneously, "
            "forming a fibrous root system that later develops swollen storage roots. The first "
            "8 weeks are critical: the plant has minimal photosynthetic capacity and is highly "
            "vulnerable to environmental stress, pests, and diseases. Phosphorus stimulates "
            "early root development; potassium is important for overall vigour from the outset. "
            "Soil temperature of 20-30°C is optimal for root initiation. Cassava's C3 "
            "photosynthesis means it does not achieve the water-use efficiency of C4 crops "
            "like maize, but its deep roots and osmotic adjustment enable remarkable drought "
            "tolerance once fully established."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Canopy Development",
        stage_code="GS2",
        day_range=(60, 120),
        water_kc=0.60,
        water_mm_per_week=30,
        critical_nutrients=["N", "K", "Mg"],
        key_activities=[
            "Apply top-dress Ammonium Nitrate at 60-70 DAP if growth is slow (optional — see notes)",
            "First mechanical or hand-hoe weeding at 8-10 weeks",
            "Second weeding at 12-14 weeks if canopy not yet closed",
            "Scout for CMD, CBB, green mite, and mealybug — apply controls if thresholds exceeded",
            "Monitor for cassava bacterial blight during wet weather (angular leaf spots)",
            "Remove and burn any CMD-symptomatic plants if < 20% of stand affected",
        ],
        risks=[
            "CMD and CBSD infection spreading from infected stakes or whiteflies",
            "Cassava bacterial blight in wet season NR II-III",
            "Cassava anthracnose tip dieback in humid conditions",
            "Late-season nitrogen application luxury consumption without yield benefit",
            "Allelopathic weed species (Striga not a problem in cassava but Commelina spp.)",
        ],
        scientific_notes=(
            "During canopy development, cassava undergoes rapid leaf area expansion. Each branching "
            "node produces 3 branches (trichotomous branching pattern). The crop switches from "
            "relying on stem reserves to active photosynthesis. Nitrogen is critical during this "
            "phase for chlorophyll synthesis and protein production. However, cassava is notably "
            "more efficient in nitrogen use than cereals — excessive nitrogen leads to 'top heavy' "
            "plants with abundant foliage but reduced root-to-shoot ratio, directly reducing "
            "storage root yield. Potassium is critical throughout for assimilate partitioning "
            "and drought adaptation. Magnesium is important for chlorophyll function and "
            "assimilate loading into the phloem. Canopy closure at 10-14 weeks suppresses weeds "
            "and creates its own microclimate that moderates extremes."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Root Bulking",
        stage_code="GS3",
        day_range=(120, 270),
        water_kc=0.75,
        water_mm_per_week=35,
        critical_nutrients=["K", "P"],
        key_activities=[
            "Maintain weed-free conditions if canopy has not fully closed",
            "Continue disease and pest scouting — CBB and CMD monitoring remains important",
            "Scout for cassava scale insects and new mealybug infestations",
            "Apply potassium top-dress (Muriate of Potash, 50 kg/ha) at 120 DAP if soil test low",
            "Mark plants with superior canopy and root development for stake selection at harvest",
            "Avoid deep cultivation near plants — storage roots radiate to 1 m from stem base",
        ],
        risks=[
            "Drought stress during root bulking reducing final root yield significantly",
            "CMD/CBSD root necrosis (CBSD) making roots inedible",
            "Excessive soil nitrogen from previous applications reducing root starch content",
            "Rodent damage to developing roots (Mastomys natalensis, Arvicanthis spp.)",
            "Root-knot nematode (Meloidogyne spp.) causing galled, misshapen roots",
        ],
        scientific_notes=(
            "Root bulking is the defining phase of cassava production. Storage roots are "
            "modified lateral roots that undergo secondary thickening through lignification of "
            "the pericycle and accumulation of starch in the root parenchyma. Up to 80% of "
            "final root dry matter is accumulated during this phase. Sucrose is loaded from "
            "leaves into the phloem and unloaded into storage root cells, where it is converted "
            "to starch by ADP-glucose pyrophosphorylase and starch synthase. Potassium plays a "
            "central role in this process — it is the primary ion driving sucrose loading and "
            "phloem turgor. Drought stress activates abscisic acid signalling, which triggers "
            "stomatal closure and can redirect assimilates to roots (drought escape response), "
            "partially explaining cassava's tolerance. Cyanogenic glycosides (linamarin and "
            "lotaustralin) accumulate differentially in roots depending on variety: bitter "
            "varieties contain > 100 mg HCN equivalent/kg fresh weight, sweet varieties < 50 "
            "mg HCN/kg. Nitrogen deficiency increases HCN content; adequate K nutrition "
            "moderates it. Long-season (12-18 month) cassava accumulates 3-5x more starch "
            "per ha than 8-month crops."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Maturation",
        stage_code="GS4",
        day_range=(270, 365),
        water_kc=0.50,
        water_mm_per_week=20,
        critical_nutrients=[],
        key_activities=[
            "Assess roots for harvest readiness: dig test roots from 3-5 sample plants",
            "Assess starch content by specific gravity (float test) — denser roots = more starch",
            "Select and label best plants for stake/cutting material for next season",
            "Cut back stems to 30-40 cm above ground if retaining plants for second season",
            "Begin staged harvest — cassava is highly flexible: harvest from 8-24+ months",
            "For flour production: harvest at 12-18 months for maximum starch concentration",
            "Fresh market: harvest earlier (8-10 months) before roots become woody",
        ],
        risks=[
            "Root deterioration post-physiological maturity (roots become woody and fibrous)",
            "CBSD necrosis progression with delayed harvest — inspect roots early",
            "Stem borers (Sesamia spp.) may attack old stems",
            "Rodent damage increases with time in ground",
            "Regrowth after rain causing roots to crack and lose quality",
        ],
        scientific_notes=(
            "Cassava has an exceptionally flexible harvest window — a key food security attribute. "
            "Unlike cereals that have a fixed physiological maturity, cassava can remain in the "
            "ground for 8-24+ months, acting as a 'food bank' during famine periods. Root starch "
            "concentration peaks at 12-18 months after planting; beyond 24 months, roots become "
            "increasingly lignified and HCN concentration rises. Roots do not store well "
            "post-harvest: physiological post-harvest deterioration (PPD) begins within 24-48 "
            "hours of harvest due to reactive oxygen species accumulation in root tissues, causing "
            "blue-black vascular streaking (scopoletin polymerisation). PPD is the primary "
            "constraint to cassava commercialisation. Cyanogenic glycoside content must be "
            "reduced below safe levels (< 10 mg HCN/kg dry weight) through processing before "
            "human consumption of bitter varieties."
        ),
    ),
]


# ---------------------------------------------------------------------------
# FERTILIZER SCHEDULE
# ---------------------------------------------------------------------------

CASSAVA_FERT = FertilizerSchedule(
    basal={
        "product": "Compound D (7:14:7)",
        "rate_kg_ha": 250,
        "timing": "At planting — incorporated into planting hole or band 5-10 cm from stake",
        "placement": "Band or spot-place 5-10 cm from planting stake, 10 cm deep",
        "nutrients_supplied": {"N": 17.5, "P2O5": 35, "K2O": 17.5},
        "notes": (
            "Compound D provides balanced NPK for establishment. The phosphorus component is "
            "most critical — cassava has high P demand for root initiation. On very sandy, "
            "P-deficient soils (NR IV-V granitic sands), increase to 300 kg/ha or use "
            "Compound S (7:21:7). On heavy clay vertisols, reduce to 200 kg/ha and focus "
            "on potassium management. Do NOT place fertiliser in direct contact with stakes "
            "as salt damage inhibits root sprouting."
        ),
    },
    top_dress_1={
        "product": "Ammonium Nitrate (AN 34.5%N) — optional, season-dependent",
        "rate_kg_ha": 75,
        "timing": "60-70 days after planting (canopy development stage)",
        "placement": "Side-dress 15 cm from stem base, do NOT mound over fertiliser",
        "nutrients_supplied": {"N": 25.9},
        "notes": (
            "Cassava is efficient with nitrogen and excess N promotes vegetative growth at the "
            "expense of root yield. Top-dressing is only recommended if: (a) plants show "
            "yellowing and slow growth at 60 DAP, (b) soil organic matter is very low, "
            "(c) the season has been good (> 400 mm rain to date). In NR IV-V dryland cassava, "
            "skip nitrogen top-dressing unless irrigation is available. Where compost (5 t/ha) "
            "was applied at planting, nitrogen top-dressing is rarely needed."
        ),
    },
    top_dress_2={
        "product": "Muriate of Potash (MOP, 60% K2O)",
        "rate_kg_ha": 50,
        "timing": "120-130 days after planting (root bulking stage begins)",
        "placement": "Broadcast and incorporate lightly, or side-dress 20 cm from stem",
        "nutrients_supplied": {"K2O": 30},
        "notes": (
            "Potassium is the most critical nutrient during root bulking — it drives sucrose "
            "loading from leaves into phloem and assimilate partitioning to storage roots. "
            "Zimbabwe's granite-derived sandy soils (NR III-V) are inherently low in K. "
            "This application significantly increases both root yield and starch content. "
            "Apply only if soil K is below 120 ppm on soil test. On heavier soils with "
            "higher cation exchange capacity, the Compound D basal may supply adequate K."
        ),
    },
    foliar={
        "product": "Multifeed or Kristalon (foliar NPK + micronutrients)",
        "rate": "2-3 kg/ha in 200-300 L water",
        "timing": "Optional: at 8 and 14 weeks if deficiency symptoms appear",
        "notes": (
            "Foliar feeding is a corrective measure, not a substitute for adequate soil nutrition. "
            "Apply if leaf yellowing (N), purple colouration of leaf undersides (P), "
            "or marginal leaf scorch (K) is observed. Include zinc (ZnSO4, 0.5 kg/ha) if "
            "reddish-brown leaf margins and stunted young leaves appear — zinc deficiency "
            "is common on limestone-derived soils. Boron at 0.1 kg/ha corrects poor branching."
        ),
    },
    liming={
        "product": "Calcitic or dolomitic agricultural lime",
        "rate_kg_ha": "As per soil test — typically 500-1500 kg/ha for pH below 5.2",
        "timing": "Apply 2-3 months before planting, incorporate to 15 cm depth",
        "notes": (
            "Cassava tolerates slightly acid soils better than maize (survives to pH 4.5) "
            "but optimal production requires pH 5.5-6.5. Below pH 5.0, aluminium toxicity "
            "inhibits root elongation and P uptake. Dolomitic lime supplies both Ca and Mg — "
            "preferred where Mg deficiency (interveinal yellowing of older leaves) is present. "
            "Heavy-textured soils may require 2000+ kg/ha to raise pH by one unit."
        ),
    },
    notes=(
        "Cassava has relatively modest nutrient requirements compared to cereals for equivalent "
        "caloric output — a key advantage for smallholder food security. Total N removal at "
        "harvest is ~40-60 kg/ha, P2O5 ~20-30 kg/ha, K2O ~80-120 kg/ha (K is the most "
        "limiting nutrient for cassava). The most common Zimbabwe smallholder error is "
        "excessive nitrogen and inadequate potassium. Compost or farmyard manure (5-10 t/ha "
        "at planting) substantially improves water retention and nutrient availability in "
        "sandy soils. In NR IV-V, organic matter additions can be more important than "
        "inorganic fertiliser for sustainable cassava production."
    ),
)


# ---------------------------------------------------------------------------
# PLANTING WINDOWS
# ---------------------------------------------------------------------------

CASSAVA_PLANTING_WINDOWS: List[PlantingWindow] = [
    PlantingWindow(
        region="NR I (Eastern Highlands)",
        optimal_start="October 15",
        optimal_end="November 30",
        acceptable_start="October 1",
        acceptable_end="December 31",
        notes=(
            "Not a primary cassava zone — too cold at altitude (> 1500 m) for optimal root "
            "development. Cassava grown only in lower-elevation valleys within NR I. "
            "Frost risk limits the production season. Prefer sweet varieties for reduced "
            "processing burden. Harvest at 10-12 months before cold season damages roots."
        ),
    ),
    PlantingWindow(
        region="NR II (Mashonaland)",
        optimal_start="October 15",
        optimal_end="December 1",
        acceptable_start="October 1",
        acceptable_end="December 31",
        notes=(
            "Good production zone with reliable rainfall (750-1000 mm). Stake planting "
            "with onset of October rains. Both sweet and bitter varieties suit this zone. "
            "Harvest at 12-18 months for maximum starch yield. CBD and CMD pressure are "
            "higher in this wetter zone — prioritise disease-free planting material. "
            "Irrigation potential in Mashonaland plateau allows year-round planting."
        ),
    ),
    PlantingWindow(
        region="NR III (Semi-intensive Farming)",
        optimal_start="October 20",
        optimal_end="December 1",
        acceptable_start="October 1",
        acceptable_end="December 31",
        notes=(
            "Very suitable cassava zone (650-800 mm rainfall). Planting with early rains "
            "in October ensures root development before dry season. A 12-month crop planted "
            "in October-November is harvested the following October-November at start of "
            "next rains — avoiding competition with land preparation. Cassava provides "
            "an excellent food security buffer in this zone where rainfall variability "
            "makes cereal farming unpredictable."
        ),
    ),
    PlantingWindow(
        region="NR IV (Semi-extensive Farming, Matabeleland)",
        optimal_start="November 1",
        optimal_end="December 15",
        acceptable_start="October 15",
        acceptable_end="January 7",
        notes=(
            "Cassava is highly suited to NR IV's 450-650 mm rainfall and its variability. "
            "Plant with first establishing rains (40+ mm in one week) in November. "
            "Cassava's drought tolerance allows it to bridge dry spells that would kill "
            "maize. Use drought-tolerant varieties and plant on ridges for water retention. "
            "Typical harvest at 12-18 months. Cassava is increasingly promoted here as "
            "a food security crop and income earner (flour processing). Green mite and "
            "mealybug pressure is highest in this dry zone — prioritise IPM."
        ),
    ),
    PlantingWindow(
        region="NR V (Lowveld, Extensive Farming)",
        optimal_start="November 15",
        optimal_end="December 31",
        acceptable_start="November 1",
        acceptable_end="January 15",
        notes=(
            "Challenging but possible cassava production zone (< 450 mm rainfall). "
            "Success depends on irrigation or planting in low-lying areas with access "
            "to moisture from seepage zones, riverbanks, or dambo margins. "
            "Dryland cassava in NR V is only viable in above-average rainfall years "
            "or on deep sandy soils with high water retention. Recommend 2-year "
            "crop cycle planted at first rains in November-December — leave in ground "
            "through second dry season, harvest at 18-24 months. Cassava serves as the "
            "ultimate famine reserve crop in this drought-prone zone."
        ),
    ),
]


# ---------------------------------------------------------------------------
# CYANOGENIC GLYCOSIDE MANAGEMENT NOTE
# (Included as a module-level constant for access by advisory systems)
# ---------------------------------------------------------------------------

CYANOGENIC_MANAGEMENT = {
    "overview": (
        "Cassava contains cyanogenic glycosides — primarily linamarin (~93%) and "
        "lotaustralin (~7%) — concentrated in the leaf blades, leaf petioles, stem bark, "
        "and to varying degrees in storage roots. When plant tissue is damaged (crushing, "
        "grating, peeling), the glycosides contact the endogenous enzyme linamarase, releasing "
        "hydrogen cyanide (HCN). HCN concentrations above 50 mg/kg fresh weight pose "
        "health risks; chronic low-level exposure causes Konzo (paralytic disease) and "
        "tropical ataxic neuropathy — documented in Zimbabwe and Mozambique."
    ),
    "bitter_vs_sweet": {
        "sweet_varieties": {
            "hcn_range_mg_per_kg_fresh": "< 50",
            "examples": "Most improved IITA varieties, some traditional sweet landraces",
            "processing_required": "Peeling and cooking sufficient for most preparations",
            "notes": "Sweet varieties can be eaten as cooked vegetable (muchachanda/garwe). "
                     "Safe for direct consumption after boiling. Lower risk but NOT zero risk.",
        },
        "bitter_varieties": {
            "hcn_range_mg_per_kg_fresh": "> 100, up to 400+",
            "examples": "Most traditional Zimbabwe landraces (mhanga, some mufarinya types)",
            "processing_required": "Multi-step processing MANDATORY before safe consumption",
            "notes": (
                "Bitter varieties are commonly grown for high yield and pest/pest resistance "
                "but require thorough traditional processing. NEVER feed bitter cassava to "
                "children or livestock without full processing."
            ),
        },
    },
    "processing_methods": {
        "fermentation_and_sun_drying": {
            "description": "Traditional Zimbabwean method producing mahewu base or cassava flour",
            "steps": [
                "1. Peel roots and discard peels (highest HCN concentration)",
                "2. Grate or chip roots (cell rupture activates linamarase — volatilisation begins)",
                "3. Ferment in water for 3-5 days (lactic acid bacteria lower pH, "
                   "accelerating HCN volatilisation)",
                "4. Drain fermented pulp thoroughly",
                "5. Sun-dry until moisture < 12% (HCN volatile — evaporates with drying)",
                "6. Pound or mill to flour",
            ],
            "hcn_reduction": "Reduces HCN by 90-97% in bitter varieties",
            "safety_note": "Critical: All steps must be completed. Incomplete processing "
                           "is the primary cause of cassava-related illness.",
        },
        "heap_fermentation": {
            "description": "Whole roots left in heaps under leaves for 3-5 days",
            "hcn_reduction": "Reduces HCN by 70-85%",
            "notes": "Less reliable than water fermentation; use only for sweet varieties "
                     "or follow with sun-drying",
        },
        "wetting_and_sun_drying": {
            "description": "Peeled chips soaked in water 4+ hours, then sun-dried",
            "hcn_reduction": "Reduces HCN by 50-70% — insufficient for bitter varieties alone",
            "notes": "Adequate for sweet varieties; must combine with fermentation for bitter",
        },
        "boiling": {
            "description": "Boiling peeled roots in large volume of water with lid off",
            "hcn_reduction": "Reduces HCN by 70-90% depending on time and volume of water",
            "notes": (
                "Most reliable quick method for fresh consumption. "
                "Key: boil in OPEN pot, large volume of water, discard cooking water. "
                "Do NOT steam or pressure-cook bitter cassava — HCN trapped in steam "
                "is reabsorbed. Boiling for 25+ minutes in open water is safest."
            ),
        },
    },
    "leaves_processing": {
        "note": (
            "Cassava leaves (muriwo wemhanga) are an important vegetable and protein source "
            "in Zimbabwe. HCN content in leaves is very high (500-2000 mg HCN equiv./kg). "
            "MANDATORY processing: crush/grind leaves, allow 30-60 min rest (HCN volatilises), "
            "then boil in large volume of open water for 20+ minutes, discarding water. "
            "Repeat boiling with fresh water for bitter varieties. Properly processed "
            "cassava leaves are nutritious and safe."
        ),
    },
    "field_identification": {
        "bitter_indicators": [
            "Very strong, pungent smell when leaves or stems are crushed",
            "Extremely bitter taste (CAUTION: do not taste raw roots from unknown varieties)",
            "Leaves and petioles often dark green to purplish — though unreliable alone",
            "Traditional knowledge: ask the farmer or seed source about variety bitterness",
        ],
        "sweet_indicators": [
            "Mild or no smell when leaves crushed",
            "Petioles often pale green to cream-coloured (not definitive)",
            "Named sweet varieties: confirm with AGRITEX variety list",
        ],
    },
}


# ---------------------------------------------------------------------------
# PROFILE
# ---------------------------------------------------------------------------

PROFILE = CropProfile(
    crop_name="Cassava",
    scientific_name="Manihot esculenta",
    family="Euphorbiaceae",
    optimal_ph=(5.5, 6.5),
    critical_ph_low=4.5,
    optimal_soil_types=["fersiallitic", "kaolinitic", "siallitic"],
    avoid_soil_types=[
        "waterlogged or poorly drained soils (root rot and anaerobic conditions)",
        "pure sand with no clay or organic matter (excessive drying, no nutrient retention)",
        "heavy montmorillonite clays (cracking damages roots, harvest difficult)",
    ],
    optimal_temp=(25.0, 35.0),
    critical_temp_low=12.0,
    critical_temp_high=40.0,
    base_temp_gdd=15.0,
    total_water_mm=600.0,
    growth_stages=CASSAVA_GROWTH_STAGES,
    fertilizer_schedule=CASSAVA_FERT,
    diseases=CASSAVA_DISEASES,
    pests=CASSAVA_PESTS,
    planting_windows=CASSAVA_PLANTING_WINDOWS,
    harvest_moisture=(
        "Cassava roots do not have a grain moisture target. Harvest when roots reach "
        "desired size and starch concentration (typically 12-18 months after planting). "
        "For flour processing: target 35-40% dry matter content. Roots deteriorate rapidly "
        "after harvest (post-harvest physiological deterioration begins within 24-48 hours). "
        "Fresh roots must be processed or sold within 24-48 hours of harvest. "
        "For field storage: leave roots in ground — cassava is its own best storage container."
    ),
    storage_conditions=(
        "Fresh roots: process within 24-48 hours of harvest. Waxing roots (paraffin dip) "
        "extends shelf life to 1-2 weeks for commercial fresh market. "
        "Dried chips/flour: store at < 12% moisture in sealed sacks or containers in "
        "cool, dry, well-ventilated stores. Apply Actellic Super dust (pirimiphos-methyl "
        "+ pyrethrins) to dried chips at 50 g/100 kg product. Flour stores 3-6 months "
        "under good conditions. Dried chips can store 12+ months. "
        "CYANIDE WARNING: never store unprocessed bitter cassava in enclosed spaces "
        "where HCN vapour can accumulate."
    ),
    post_harvest_notes=(
        "Cassava processing chain: fresh roots -> peeling (remove HCN-rich bark) -> "
        "grating or chipping -> fermentation (3-5 days in water for bitter varieties) -> "
        "sun-drying or oven-drying -> milling to flour. "
        "Zimbabwe end-products: sadza ya mhanga (cassava stiff porridge), cassava-maize "
        "composite flour, mahewu base, starch (industrial), dried chips (livestock feed). "
        "Value addition: cassava flour for composite bread (up to 20% cassava flour + 80% "
        "wheat flour is acceptable for bread-making). Cassava starch for industrial uses "
        "(paper, textile, adhesives). "
        "IMPORTANT: Always test unknown varieties for bitterness before consuming without "
        "full processing. When in doubt, apply full fermentation + boiling protocol."
    ),
    natural_region_suitability={
        "NR I": (
            "Marginal — too cold at high altitude for optimal cassava. "
            "Limited to valley floors below 1400 m. Not a priority zone for cassava promotion."
        ),
        "NR II": (
            "Well suited — reliable rainfall supports good yields (15-25 t/ha fresh roots). "
            "Disease pressure (CMD, CBB) higher due to humidity. "
            "Both commercial and smallholder production viable."
        ),
        "NR III": (
            "Highly recommended — cassava's drought tolerance makes it ideal complement "
            "to maize. Yields of 12-20 t/ha fresh roots achievable. "
            "Important food security backup when maize fails."
        ),
        "NR IV": (
            "Strongly recommended — cassava is the most drought-tolerant food crop for "
            "this semi-arid zone. Yields variable (8-18 t/ha) depending on rainfall. "
            "Green mite and mealybug management critical. Key food security crop."
        ),
        "NR V": (
            "Important famine reserve crop — only viable with irrigation, in dambo margins, "
            "or in above-average rainfall years. Dryland yields low (5-10 t/ha) but "
            "the ability to leave roots in ground as food bank is invaluable. "
            "Essential for household food security in drought years."
        ),
    },
)

ALIASES = ["mhanga", "mufarinya"]
