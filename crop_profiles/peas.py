"""Garden Peas (Pisum sativum) — cool-season legume grown for shelling; export and domestic crop in Zimbabwe."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List


PEAS_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Powdery Mildew",
        pathogen="Erysiphe pisi",
        pathogen_type="fungal",
        symptoms=[
            "White to grey powdery coating on leaves, stems, tendrils, and pods",
            "Yellowing and premature senescence of heavily colonised leaves",
            "Pod surface becomes rough and discoloured, unmarketable for export",
            "Severe infections lead to defoliation and early crop death",
            "Reduced photosynthesis causing poor seed fill and shrivelled peas",
        ],
        identification_markers=[
            "White talcum-powder-like growth on upper leaf surface first, progressing to stems and pods",
            "Distinctly different from downy mildew: grows on upper surface, not greyish-purple below",
            "Spreads rapidly during dry weather with cool nights and moderate day temperatures",
            "Cleistothecia (tiny dark chasmothecia) visible as black pinpricks in older powdery patches",
            "Characteristic musty smell from heavy infections in the field",
        ],
        favourable_conditions={
            "humidity_min": 50,
            "temp_min_c": 15,
            "temp_max_c": 26,
            "note": (
                "Dry days with cool, humid nights (15-26°C). Unlike most fungi, does NOT require "
                "free water — elevated relative humidity (>50% RH) alone is sufficient for spore "
                "germination. Most destructive when days are warm and nights cool, typical of "
                "Zimbabwe's dry-season pea production window (April-July)."
            ),
        },
        susceptible_stages=["vegetative", "flowering", "pod_fill"],
        resistant_varieties=["Greenfeast (moderate tolerance)", "Kelvedon Wonder (some tolerance)"],
        susceptible_varieties=["Onward (highly susceptible)", "Early Onward"],
        chemical_control=[
            {
                "name": "Sulphur 80 WP",
                "rate": "2.0-3.0 kg/ha",
                "phi_days": "7",
                "notes": (
                    "Protectant; apply before symptoms appear. Do NOT apply above 30°C — "
                    "phytotoxic in heat. Highly effective and low cost for commercial pea production."
                ),
            },
            {
                "name": "Myclobutanil 200 EW",
                "rate": "0.3 L/ha",
                "phi_days": "14",
                "notes": "Systemic triazole DMI fungicide; apply at first symptom. Gives 14-21 day protection.",
            },
            {
                "name": "Azoxystrobin 250 SC",
                "rate": "0.4 L/ha",
                "phi_days": "7",
                "notes": (
                    "Strobilurin (QoI) fungicide; preventive use recommended. Maximum 2 applications "
                    "per season to manage resistance risk. Excellent redistribution on waxy leaf surface."
                ),
            },
            {
                "name": "Tebuconazole 250 EW",
                "rate": "0.5 L/ha",
                "phi_days": "14",
                "notes": "Triazole; curative activity. Use in alternation with strobilurins.",
            },
        ],
        biological_control=[
            "Bacillus subtilis-based products (e.g., Serenade) as preventive foliar sprays",
            "Potassium bicarbonate (1-2%) disrupts fungal cell membranes — approved for organic production",
            "Reynoutria sachalinensis extract (Regalia) as a plant defence activator",
        ],
        cultural_control=[
            "Select tolerant varieties such as Greenfeast where available",
            "Ensure adequate plant spacing (8-10 cm in-row, rows 60-75 cm) for air movement",
            "Avoid excessive nitrogen application — lush vegetative growth is highly susceptible",
            "Remove and destroy all crop debris immediately after harvest",
            "Rotate with non-legume crops for minimum 2 seasons to break pathogen cycle",
            "Avoid late-season plantings that experience deteriorating conditions for mildew development",
        ],
        economic_threshold=(
            "15% of leaf area affected on vegetative plants; 5% on pods (export zero-tolerance on pods). "
            "Spray preventively once peas are at 50% flowering in areas with known mildew pressure."
        ),
        severity_scale={
            "mild": "Scattered white patches on lower leaves, <10% leaf area affected, no pod infection",
            "moderate": "20-40% leaf area affected, lesions reaching upper canopy and stems",
            "severe": ">40% leaf area with pod infection — major yield reduction and total export rejection",
        },
    ),

    DiseaseProfile(
        name="Downy Mildew",
        pathogen="Peronospora viciae",
        pathogen_type="fungal",
        symptoms=[
            "Pale yellow to pale green diffuse patches on upper leaf surface",
            "Grey to violet-grey fuzzy sporulation (sporangiophores) on leaf undersides",
            "Systemically infected seedlings are stunted, pale, and distorted",
            "Pod infection produces brown blotches and seed discolouration",
            "Severely infected plants may collapse at seedling stage",
        ],
        identification_markers=[
            "Grey-purple sporulation strictly on the UNDERSIDE of leaves — key distinction from powdery mildew",
            "Upper-surface yellow angular patches correspond directly to sporulation zone below",
            "Systemically infected plants are stunted with downward-curled leaves and yellow flush",
            "Infected seeds are small, brown, and wrinkled — important seed-borne inoculum source",
        ],
        favourable_conditions={
            "humidity_min": 85,
            "temp_min_c": 5,
            "temp_max_c": 18,
            "leaf_wetness_hours": 4,
            "note": (
                "Cool, wet weather with prolonged leaf wetness. Morning dews and light fog are ideal "
                "for sporulation. Infection most severe at 10-15°C. Warm dry weather (>24°C) arrests "
                "disease development. Eastern Highlands and Highveld in April-June are at moderate risk."
            ),
        },
        susceptible_stages=["seedling", "vegetative", "flowering"],
        resistant_varieties=[],
        susceptible_varieties=["Most commercial garden pea varieties show susceptibility"],
        chemical_control=[
            {
                "name": "Metalaxyl-M + Mancozeb (Ridomil Gold MZ)",
                "rate": "2.5 kg/ha",
                "phi_days": "14",
                "notes": (
                    "Apply preventively before infection. Metalaxyl-M is systemic (acropetal); "
                    "mancozeb is protectant contact component. Combination delays resistance development."
                ),
            },
            {
                "name": "Fosetyl-Al 80 WP (Aliette)",
                "rate": "2.0-3.0 kg/ha",
                "phi_days": "14",
                "notes": "Systemic; moves both up and down in plant. Stimulates plant phytoalexin production.",
            },
            {
                "name": "Cymoxanil + Mancozeb",
                "rate": "2.0-2.5 kg/ha",
                "phi_days": "14",
                "notes": "Curative + protectant combination. Cymoxanil has 1-3 day kickback activity.",
            },
        ],
        biological_control=[
            "Copper hydroxide (Kocide) at 1.5-2.0 kg/ha as a protectant copper fungicide",
            "Trichoderma harzianum soil drench at transplant/sowing to reduce soilborne inoculum",
            "Phosphorous acid (potassium phosphonate) foliar spray at 2-3 mL/L",
        ],
        cultural_control=[
            "Use certified disease-free seed from reputable suppliers or treat with metalaxyl seed dressing",
            "Avoid overhead irrigation; convert to drip where economically feasible",
            "Plant in well-drained soils — waterlogged conditions dramatically increase infection",
            "Rogue systemically infected plants immediately upon discovery",
            "Maintain 3+ year rotation away from peas, beans, and other legumes",
            "Plant in sites with good air movement to reduce prolonged leaf wetness duration",
        ],
        economic_threshold=(
            "5% incidence of systemically infected plants; any pod symptoms in export crops. "
            "In seedling stage, even 2-3% systemic infection justifies a preventive spray programme."
        ),
        severity_scale={
            "mild": "Scattered foliar lesions, <5% plants affected, no systemic symptoms",
            "moderate": "10-25% plants with foliar symptoms, some systemic plants present",
            "severe": ">25% plants affected or pod infection — significant yield and quality loss, crop may not recover",
        },
    ),

    DiseaseProfile(
        name="Ascochyta Blight",
        pathogen="Ascochyta pisi / Mycosphaerella pinodes",
        pathogen_type="fungal",
        symptoms=[
            "Dark brown to purple-black lesions on leaves, stems, and pods",
            "Stem base foot rot: dark discolouration causing plant lodging and death",
            "Leaf lesions are roughly circular with pale centres and dark margins",
            "Pod lesions are sunken, dark, and may penetrate to infect seeds",
            "Infected seeds develop brown to grey discolouration and shrivel at harvest",
        ],
        identification_markers=[
            "Concentric ring (target-spot) pattern within larger lesions",
            "Pycnidia (tiny raised dark specks) visible with hand lens within lesions",
            "Foot rot at stem base: characteristic purple-black discolouration at soil line",
            "M. pinodes causes a more diffuse blotch lesion than A. pisi (which is more discrete)",
            "Disease spreads from rain splash — worst near soil surface and in wet seasons",
        ],
        favourable_conditions={
            "humidity_min": 80,
            "temp_min_c": 15,
            "temp_max_c": 25,
            "rainfall": "Frequent rain, irrigation, or overhead watering",
            "note": (
                "Warm, wet weather with frequent wetting-drying cycles. Seed-borne and residue-borne. "
                "Eastern Highlands early-season plantings (March-April) with high rainfall are at risk. "
                "Splash dispersal extends the pathogen through the canopy rapidly once established."
            ),
        },
        susceptible_stages=["seedling", "vegetative", "flowering", "pod_fill"],
        resistant_varieties=[],
        susceptible_varieties=["Onward", "Greenfeast", "Kelvedon Wonder — all show susceptibility"],
        chemical_control=[
            {
                "name": "Chlorothalonil 500 SC",
                "rate": "2.0 L/ha",
                "phi_days": "14",
                "notes": (
                    "Broad-spectrum protectant. Apply before flowering and repeat at 10-14 day intervals. "
                    "Good contact coverage essential — use minimum 500 L water/ha."
                ),
            },
            {
                "name": "Mancozeb 80 WP",
                "rate": "2.0-2.5 kg/ha",
                "phi_days": "14",
                "notes": "Dithiocarbamate protectant; alternate with chlorothalonil to manage resistance.",
            },
            {
                "name": "Boscalid + Pyraclostrobin (Bellis)",
                "rate": "0.6-0.8 kg/ha",
                "phi_days": "7",
                "notes": "SDHI + strobilurin combination; excellent preventive and curative activity. Premium product.",
            },
        ],
        biological_control=[
            "Seed treatment with Trichoderma spp. (T. harzianum) to protect seedlings from soil phase",
            "Bacillus amyloliquefaciens (Serenade ASO) as foliar spray — reduces spore germination",
        ],
        cultural_control=[
            "Use certified disease-free seed — this is the primary inoculum source",
            "Treat seed with thiram or iprodione fungicide dressing before planting",
            "Rotate away from all legumes (peas, beans, lentils) for 3-4 years minimum",
            "Plough crop residue deeply to bury and accelerate decomposition of inoculum",
            "Avoid overhead irrigation during flowering and pod fill stages",
            "Select open, well-drained sites with good air circulation to reduce leaf wetness",
        ],
        economic_threshold=(
            "10% plants with stem base (foot rot) lesions; any pod lesions in export crops. "
            "Act early — once foot rot is established, plant recovery is unlikely."
        ),
        severity_scale={
            "mild": "Leaf lesions only, <10% leaf area affected, no stem or pod infection",
            "moderate": "Stem lesions present, 10-30% leaf area affected, some plants wilting",
            "severe": "Widespread foot rot causing plant death, pod infection confirmed — major losses",
        },
    ),

    DiseaseProfile(
        name="Fusarium Wilt",
        pathogen="Fusarium oxysporum f. sp. pisi",
        pathogen_type="fungal",
        symptoms=[
            "Sudden wilting of individual plants or patches in the field",
            "Yellowing progresses upward from lower leaves",
            "Brown to reddish-brown vascular discolouration visible when stem is cut lengthways",
            "Stunting and poor growth even before visible wilting",
            "Root system shows brown, rotted roots with reduced nodulation",
        ],
        identification_markers=[
            "Vascular discolouration (brown streaking) in stem xylem — cut stem to reveal",
            "One-sided wilting early in infection (asymmetric yellowing)",
            "Soil is often dry near affected plants — growers may wrongly attribute wilt to drought",
            "Fusarium produces salmon-pink sporodochia on dead stem tissue in humid conditions",
            "Disease is patchy in the field, often following soil drainage patterns or previous pea crop areas",
        ],
        favourable_conditions={
            "temp_min_c": 20,
            "temp_max_c": 30,
            "note": (
                "Warm soil temperatures (20-28°C optimal). Pathogen survives as chlamydospores in soil "
                "for many years. Exacerbated by drought stress, sandy soils, and acidic conditions. "
                "Fields with a history of peas are high risk. Monoculture dramatically increases inoculum."
            ),
        },
        susceptible_stages=["seedling", "vegetative", "flowering"],
        resistant_varieties=["Greenfeast (Race 1 resistance)", "Kelvedon Wonder (partial)"],
        susceptible_varieties=["Onward (susceptible to Race 1 and Race 2)"],
        chemical_control=[
            {
                "name": "Thiram 80 WP seed treatment",
                "rate": "3.0 g/kg seed",
                "phi_days": "N/A (seed treatment)",
                "notes": "Seed dressing only; protects young seedling roots at germination. No foliar efficacy.",
            },
            {
                "name": "Carbendazim 500 SC (seed treatment)",
                "rate": "2.0-3.0 mL/kg seed",
                "phi_days": "N/A (seed treatment)",
                "notes": "Systemic benzimidazole seed dressing; suppresses early Fusarium infection.",
            },
        ],
        biological_control=[
            "Trichoderma harzianum as soil drench or seed treatment — well-documented antagonist of Fusarium spp.",
            "Bacillus subtilis-based products as soil drench at planting",
            "Pseudomonas fluorescens soil inoculant — induces systemic resistance (ISR) in roots",
            "Mycorrhizal inoculant (Glomus intraradices) enhances root health and tolerance to vascular pathogens",
        ],
        cultural_control=[
            "Strict crop rotation: minimum 4-5 years between pea crops on infected land",
            "Select Fusarium-resistant varieties (Greenfeast for Race 1) wherever possible",
            "Avoid planting in poorly drained, compacted soil — creates stress that worsens wilt severity",
            "Maintain soil pH 6.0-7.0 to minimise pathogen virulence and promote plant vigour",
            "Remove and burn wilted plants promptly; do not compost them",
            "Deep ploughing to bury infested root debris and accelerate decomposition",
        ],
        economic_threshold=(
            "5% plant wilting warrants investigation of cause. Fusarium wilt has no curative treatment — "
            "once identified, rotation is the primary management tool for subsequent seasons."
        ),
        severity_scale={
            "mild": "Scattered wilted plants, <5% stand loss, field otherwise vigorous",
            "moderate": "5-20% plant death, yield reduction significant, patchy field appearance",
            "severe": ">20% plant death, major yield loss — replanting not economic; rotate field immediately",
        },
    ),
]


PEAS_PESTS: List[PestProfile] = [
    PestProfile(
        name="Pea Aphid",
        scientific_name="Acyrthosiphon pisum",
        pest_type="insect",
        identification=[
            "Large (3.0-4.5 mm) bright green to pale green aphid with long legs and antennae",
            "Colonies form densely on growing tips, tendrils, flower buds, and undersides of upper leaves",
            "Winged (alate) forms appear when colonies are overcrowded — spread disease to new fields",
            "White cast skins (exuviae) accumulate on leaves below feeding colonies",
            "Cornicles (tail pipes) are long and pale — diagnostic for A. pisum vs. other aphids",
        ],
        damage_symptoms=[
            "Curled and distorted growing tips reduce plant vigour and height",
            "Honeydew secretion promotes black sooty mould on pods — disqualifies export produce",
            "Reduced pod set and seed abortion due to phloem nutrient loss",
            "Vector of Pea Enation Mosaic Virus (PEMV), Bean Leaf Roll Virus (BLRV), and Pea Mosaic Virus",
            "Heavy infestations on young plants can be fatal — plants wilt and die",
        ],
        life_cycle_notes=(
            "Parthenogenetic (asexual) reproduction under warm conditions; one generation every 7-10 days "
            "at 20°C. Winged females migrate from other legume hosts (lucerne, clover, broad beans). "
            "Populations explode in cool dry weather (15-22°C); crash above 30°C or during heavy rain. "
            "In Zimbabwe's dry cool season (May-July), pea aphids are the highest-priority pest."
        ),
        favourable_conditions={
            "temp_min_c": 12,
            "temp_max_c": 25,
            "note": (
                "Cool to moderate temperatures with low rainfall. Zimbabwe's dry-season pea crop "
                "(April-July) faces highest aphid pressure. Natural enemies (parasitoid wasps, ladybirds) "
                "are often scarce early in the season."
            ),
        },
        susceptible_stages=["vegetative", "flowering", "pod_fill"],
        economic_threshold=(
            "30-50 aphids per plant on vegetative stage; 10 aphids per growing tip during flowering. "
            "Export crops: apply lower threshold of 15 aphids per plant due to virus risk and sooty mould."
        ),
        chemical_control=[
            {
                "name": "Pirimicarb 50 WG (Pirimor)",
                "rate": "250 g/ha",
                "phi_days": "7",
                "notes": (
                    "Selective aphicide; excellent choice as it spares beneficial insects "
                    "(parasitoid wasps, ladybirds, lacewings). First-choice product for IPM programmes."
                ),
            },
            {
                "name": "Acetamiprid 20 SP",
                "rate": "100-150 g/ha",
                "phi_days": "7",
                "notes": "Neonicotinoid; systemic uptake protects new growth. Avoid applying during flowering to protect pollinators.",
            },
            {
                "name": "Flonicamid 50 WG (Teppeki)",
                "rate": "140-200 g/ha",
                "phi_days": "7",
                "notes": "Selective aphicide with novel mode of action; disrupts feeding behaviour. Bee-safe.",
            },
        ],
        biological_control=[
            "Ladybirds (Coccinellidae) — Cheilomenes lunata is the common African species; adults and larvae consume 100+ aphids per day",
            "Parasitoid wasp Aphidius ervi (Braconidae) — mummified bronze aphids indicate successful parasitism",
            "Lacewing larvae Chrysoperla spp. — generalist predator of soft-bodied insects",
            "Entomopathogenic fungi Beauveria bassiana — effective under humid conditions (>80% RH)",
            "Hoverfly larvae (Syrphidae) — encourage by maintaining flowering plants on field margins",
        ],
        cultural_control=[
            "Monitor weekly from crop emergence; check growing tips and undersides of upper leaves",
            "Avoid excess nitrogen application — promotes lush succulent growth attractive to aphids",
            "Use reflective silver or aluminium mulches to deter winged alate aphids from landing",
            "Remove volunteer legumes and common weed hosts (e.g., wild lucerne) around field margins",
            "Early planting may reduce mid-season population peaks in consecutive cropping",
        ],
        scouting_protocol=(
            "Scout 20 plants in a W-pattern across the field twice per week from emergence. "
            "Count aphids on 3 growing tips per plant and note presence/absence of winged forms. "
            "Record natural enemy (ladybird, mummy, lacewing) presence. Do NOT spray if "
            "beneficial:pest ratio exceeds 1:30 — natural enemies will suppress colony. "
            "Check undersides of leaves for virus symptoms (yellowing, mosaic) indicating vector activity."
        ),
    ),

    PestProfile(
        name="Pea Weevil",
        scientific_name="Bruchus pisorum",
        pest_type="insect",
        identification=[
            "Adult is a stout (4-5 mm), mottled grey-brown weevil with white and black pattern on abdomen",
            "Characteristic white V-shaped marking visible on rear of abdomen when wings folded",
            "Adults become active when pea plants begin to flower — detected on flowers and pods",
            "Larvae are creamy-white, legless grubs found inside pea seeds at harvest",
            "Single larval entry hole visible on pod surface from egg hatching",
        ],
        damage_symptoms=[
            "Larvae develop inside individual pea seeds — internal damage not visible externally until adult emergence",
            "Exit hole (3-4 mm circular hole) in mature seeds at harvest or in storage — renders produce unsellable",
            "Infested seeds may show reduced germination if saved for planting",
            "Heavy seed infestation reduces protein content and seed weight significantly",
            "Export consignments contaminated with weevils or exit holes face total rejection",
        ],
        life_cycle_notes=(
            "Single generation per year. Adults overwinter in field debris, soil, or stored grain. "
            "Emerge when peas flower (triggered by pea flower volatile compounds). "
            "Female lays eggs on developing pods; each egg is glued to pod surface. "
            "Larva hatches and bores into developing seed within 1-2 weeks. "
            "Development inside seed: larva passes through 4 instars over 5-7 weeks. "
            "Adults emerge from dried seeds in storage — leaving the characteristic exit hole. "
            "Infestation is invisible until adult emergence, making post-harvest inspection critical."
        ),
        favourable_conditions={
            "temp_min_c": 18,
            "temp_max_c": 30,
            "note": (
                "Warm temperatures at flowering time. Adults most active on warm, sunny days. "
                "Cool cloudy weather suppresses adult flight and egg-laying activity. "
                "Zimbabwe's warm-season peas are more at risk than cool-season crops."
            ),
        },
        susceptible_stages=["flowering", "pod_fill"],
        economic_threshold=(
            "1 adult per plant during flowering in export crops — zero tolerance in packaged seed. "
            "For processing/dried peas: treat if adult numbers exceed 5 per 10 sweeps of net."
        ),
        chemical_control=[
            {
                "name": "Deltamethrin 25 EC",
                "rate": "0.2-0.3 L/ha",
                "phi_days": "7",
                "notes": (
                    "Pyrethroid; apply at onset of flowering and repeat 10-14 days later. "
                    "Targets adults before egg-laying — timing is critical. Apply in the morning."
                ),
            },
            {
                "name": "Lambda-cyhalothrin 50 EC (Karate)",
                "rate": "0.15-0.2 L/ha",
                "phi_days": "7",
                "notes": "Fast knockdown pyrethroid; highly effective against adults. Repeat at second flowering flush.",
            },
            {
                "name": "Chlorpyrifos 480 EC (seed storage treatment)",
                "rate": "5 mL/kg seed",
                "phi_days": "N/A (storage treatment)",
                "notes": "For stored seed treatment only; prevents adult emergence. Not for fresh market produce.",
            },
        ],
        biological_control=[
            "Parasitoid wasps Triaspis thoracicus attack larvae within seeds — natural regulation in organic systems",
            "Diatomaceous earth (silica dust) for storage protection at 1 g/kg seed — physical mode of action",
            "Neem oil seed treatment (20 mL/kg) deters adult egg-laying on pods",
        ],
        cultural_control=[
            "Harvest promptly at maturity — delays allow more adults to emerge in the field and re-infest",
            "Store harvested seed in sealed containers or cold storage (below 10°C) to prevent adult emergence",
            "Deep plough crop residues after harvest to destroy overwintering adults",
            "Avoid growing peas adjacent to fields with mature pea or bean crops — adult migration risk",
            "Monitor fields with sticky yellow traps baited with pea flower volatiles from early flowering",
        ],
        scouting_protocol=(
            "Walk field transects at 10% flowering and count adults per plant on 20 plants per hectare. "
            "Use sweep net (20 sweeps per monitoring point) in addition to plant inspection. "
            "Check pod surfaces for egg deposits (small yellow-orange eggs glued to surface). "
            "Examine cross-sections of older pods to detect early larval entry. "
            "Continue monitoring until pods are fully developed (seeds hard)."
        ),
    ),

    PestProfile(
        name="Pod Borer",
        scientific_name="Helicoverpa armigera",
        pest_type="insect",
        identification=[
            "Adult is a straw-yellow to brown moth (35-40 mm wingspan) with distinctive kidney-shaped spot on forewing",
            "Eggs are small (0.5 mm), white, ribbed spheres laid singly on young leaves and flower buds",
            "Young larvae are pale yellow-green; mature larvae (35-40 mm) variable: green, brown, or pink",
            "Larva has a pale lateral stripe and dark dorsal stripe — head capsule is brown with dark spots",
            "Feeding damage shows characteristic entry hole with fresh frass at pod surface",
        ],
        damage_symptoms=[
            "Pod entry holes (3-5 mm) with frass (insect droppings) at the point of entry",
            "Internal feeding destroys individual peas, often hollowing out developing seeds",
            "Wilting flower buds and tip dieback in early feeding phase",
            "Heavily infested crops show multiple exit-entry holes per pod — total yield loss possible",
            "Secondary fungal infection enters through larval feeding wounds on pods",
        ],
        life_cycle_notes=(
            "Highly polyphagous pest; attacks over 100 host crops including tomato, maize, sorghum, "
            "tobacco, and chickpea. Completes 3-5 generations per year in Zimbabwe. "
            "Pupal stage in soil (7-14 days). Adults are strong migrants — can travel 300+ km on wind currents. "
            "Moths are most active at night; eggs laid preferentially on the youngest, most tender tissue. "
            "Larval development takes 14-21 days. Fifth-instar larvae are voracious and highly mobile — "
            "may move between plants. Resistance to pyrethroids and organophosphates documented in Zimbabwe."
        ),
        favourable_conditions={
            "temp_min_c": 20,
            "temp_max_c": 32,
            "note": (
                "Warm temperatures accelerate development. Population peaks typically coincide with "
                "post-rainy season warm weather. Higher risk in irrigated dry-season crops where warm "
                "conditions prevail."
            ),
        },
        susceptible_stages=["flowering", "pod_fill"],
        economic_threshold=(
            "1 larva per metre row during pod fill; 5% pods with fresh damage (export crops: zero tolerance). "
            "For IPM: treat when egg hatch is confirmed and larvae are <3rd instar (most susceptible stage)."
        ),
        chemical_control=[
            {
                "name": "Emamectin benzoate 19 EC (Proclaim)",
                "rate": "0.4-0.6 L/ha",
                "phi_days": "3",
                "notes": (
                    "Excellent activity on young larvae. Translaminar movement into leaf tissue. "
                    "Short PHI makes it suitable for export programme. Low resistance risk."
                ),
            },
            {
                "name": "Chlorantraniliprole 200 SC (Coragen)",
                "rate": "0.15-0.2 L/ha",
                "phi_days": "1",
                "notes": (
                    "Diamide insecticide; targets ryanodine receptors — highly novel mode of action. "
                    "Excellent for resistance management. Very short PHI ideal for fresh market."
                ),
            },
            {
                "name": "Indoxacarb 150 EC (Avaunt)",
                "rate": "0.3-0.4 L/ha",
                "phi_days": "3",
                "notes": "Oxadiazine; pro-insecticide activated in insect gut. Effective against pyrethroid-resistant populations.",
            },
            {
                "name": "Spinosad 240 SC (Tracer)",
                "rate": "200-300 mL/ha",
                "phi_days": "3",
                "notes": "Naturalyte; excellent for early-instar larvae. Approved for some organic systems.",
            },
        ],
        biological_control=[
            "Bacillus thuringiensis var. kurstaki (Dipel) at 1.0-1.5 L/ha — effective on young larvae (<3rd instar)",
            "Nuclear Polyhedrosis Virus (HearNPV) — Helicoverpa-specific biopesticide registered in Zimbabwe",
            "Parasitoid wasps: Campoletis chlorideae, Cotesia kazak — conserve with selective insecticide use",
            "Trichogramma spp. egg parasitoids — augmentative release in high-value export crops",
            "Chrysoperla carnea (lacewing) larvae prey on eggs and young larvae",
        ],
        cultural_control=[
            "Use pheromone traps (Helicoverpa sex pheromone lure) to monitor adult flight activity",
            "Install one trap per 2 ha; replace lures every 4-6 weeks",
            "Deep ploughing after harvest destroys pupae in soil",
            "Intercrop with sorghum or sunflower to attract eggs away from peas (trap cropping)",
            "Remove crop residues promptly to eliminate pupation sites",
            "Time planting to avoid peak moth flight periods if scheduling allows",
        ],
        scouting_protocol=(
            "Check pheromone traps every 2-3 days; record catch numbers. "
            "Scout 25 plants in a Z-pattern across the field twice per week from flowering. "
            "Count eggs per leaf and fresh larval damage per pod. "
            "Examine growing tips and flower buds closely for young larvae using a 10x hand lens. "
            "Spray threshold: treat within 48 hours of exceeding 1 larva per metre row during pod fill."
        ),
    ),

    PestProfile(
        name="Thrips",
        scientific_name="Thrips tabaci / Frankliniella occidentalis",
        pest_type="insect",
        identification=[
            "Tiny (1.0-1.5 mm) slender insects, yellow to pale brown in colour (T. tabaci) or yellow-orange (F. occidentalis)",
            "Fringed wings (like tiny feathers) visible under 10x magnification",
            "Extremely fast-moving; shelter in flowers, leaf folds, and growing tips",
            "Tap plant material onto white paper to dislodge and count thrips",
            "Dark faecal droplets visible on leaves near feeding sites",
        ],
        damage_symptoms=[
            "Silver-grey feeding scars (stippling) on leaf surfaces — leaves appear shiny and bleached",
            "Distorted, misshapen flowers lead to poor pod set and reduced yield",
            "Brown-silver scarring on pod surfaces renders them unmarketable for fresh and export markets",
            "Heavy infestations on growing tips cause tip dieback and stunted growth",
            "F. occidentalis is a vector of Tomato Spotted Wilt Virus (TSWV) — yellowing, necrotic ringspots",
        ],
        life_cycle_notes=(
            "Complete generation in 14-20 days at 25°C. Eggs inserted into plant tissue (endophytic). "
            "Two larval instars feed on plant tissue; pre-pupa and pupa stages occur in soil or plant debris. "
            "F. occidentalis (Western Flower Thrips) is more damaging and insecticide-resistant than T. tabaci. "
            "Populations peak during warm, dry periods typical of Zimbabwe's irrigated dry season. "
            "Adults migrate into pea crops from drying weeds and senescent vegetation at field margins."
        ),
        favourable_conditions={
            "temp_min_c": 20,
            "temp_max_c": 32,
            "note": (
                "Warm, dry conditions accelerate development and migration. "
                "Populations decline rapidly during heavy rainfall which physically dislodges thrips. "
                "Irrigated crops in Zimbabwe's dry season (April-September) are at highest risk."
            ),
        },
        susceptible_stages=["flowering", "pod_fill"],
        economic_threshold=(
            "5-10 thrips per flower on vegetative/early flowering plants; "
            "any pod scarring in export crops constitutes a rejection risk (zero tolerance)."
        ),
        chemical_control=[
            {
                "name": "Spinosad 240 SC (Tracer)",
                "rate": "200-300 mL/ha",
                "phi_days": "3",
                "notes": "Excellent activity on F. occidentalis. Short PHI ideal for export. Rotate with other modes of action.",
            },
            {
                "name": "Abamectin 18 EC",
                "rate": "300-500 mL/ha",
                "phi_days": "7",
                "notes": "Translaminar activity; reaches larvae hidden inside flowers. Apply early morning for best penetration.",
            },
            {
                "name": "Thiamethoxam 250 WG (Actara)",
                "rate": "70-100 g/ha",
                "phi_days": "7",
                "notes": "Systemic neonicotinoid; effective on adults and larvae. Avoid during peak flowering for pollinator safety.",
            },
        ],
        biological_control=[
            "Predatory mite Amblyseius cucumeris — commercially available; effective against first-instar thrips in tunnels",
            "Orius spp. (minute pirate bugs) — aggressive generalist predator of thrips; occurs naturally in Zimbabwe",
            "Beauveria bassiana foliar spray under humid conditions — targets larvae in flowers",
            "Encourage diverse natural enemy community through reduced-spray IPM programme",
        ],
        cultural_control=[
            "Use blue sticky traps at canopy height for monitoring — blue is more attractive to thrips than yellow",
            "Deploy 2-4 traps per hectare; check twice per week during flowering",
            "Remove and slash weed hosts (especially Asteraceae/Compositae) from field margins before planting",
            "Avoid planting peas adjacent to senescent tobacco, onion, or broad bean crops — all thrips reservoirs",
            "Overhead irrigation can physically dislodge thrips from flowers and reduce population density",
        ],
        scouting_protocol=(
            "Inspect 20 flowers from throughout the field using a 10x hand lens. "
            "Tap flowers onto white paper and count all thrips present. "
            "Also inspect growing tips and young leaves for feeding scars. "
            "Monitor twice weekly from first flower bud appearance. "
            "Check pods for silver scarring at every inspection — any pod damage requires immediate action in export crops. "
            "Use blue sticky traps as a complementary early-warning monitoring tool."
        ),
    ),
]


PEAS_GROWTH_STAGES: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Germination & Emergence",
        stage_code="GE",
        day_range=(0, 14),
        water_kc=0.4,
        water_mm_per_week=12,
        critical_nutrients=["Phosphorus", "Molybdenum", "Zinc"],
        key_activities=[
            "Direct seed at 3-5 cm depth; spacing 5-8 cm within rows 60-75 cm apart",
            "Inoculate seed with Rhizobium leguminosarum bv. viciae before planting if no recent pea history",
            "Apply basal compound fertiliser banded 5 cm below and beside seed row",
            "Ensure soil is moist but not waterlogged at planting — check drainage",
            "Cover seed adequately and firm seedbed to ensure good soil-seed contact",
        ],
        risks=[
            "Damping-off caused by Pythium spp. and Rhizoctonia solani in wet, cool soils",
            "Bird damage to emerging seeds — place wire mesh or use bird scare devices",
            "Cold waterlogged soils delaying emergence and favouring Fusarium infection",
            "Seed rot if planted too deep in cold soil (<8°C)",
        ],
        scientific_notes=(
            "Garden peas (Pisum sativum) are hypogeal germinators — cotyledons remain below ground, "
            "protecting them from frost. Optimal germination soil temperature is 10-18°C (minimum 4°C). "
            "Rhizobium leguminosarum bv. viciae is the specific nodule-forming bacterium for peas — "
            "use the correct strain, not a generic legume inoculant. Molybdenum is a cofactor for "
            "nitrogenase enzyme in Rhizobium nodules; deficiency impairs N-fixation even when nodules form. "
            "Phosphorus stimulates early root development and is critical for nodule establishment."
        ),
    ),

    GrowthStageRequirements(
        stage_name="Vegetative Growth",
        stage_code="VG",
        day_range=(14, 35),
        water_kc=0.6,
        water_mm_per_week=22,
        critical_nutrients=["Phosphorus", "Potassium", "Sulphur", "Nitrogen (starter)"],
        key_activities=[
            "Erect or verify trellis/support structures — garden peas require support once 25-30 cm tall",
            "Weed control is critical — peas are poor competitors in early growth; hand-weed or apply pre-emergent herbicide",
            "Scout weekly for aphids on growing tips and undersides of upper leaves",
            "Begin fungicide programme if downy mildew or Ascochyta risk is elevated (wet/humid conditions)",
            "Check nodule development at 20-25 days — slice roots to confirm pink nodules (N-fixing)",
        ],
        risks=[
            "Weed competition reducing plant stand by 20-30% if uncontrolled",
            "Aphid population build-up on growing tips — can cause serious stunting",
            "Downy mildew in cool, wet conditions",
            "Rhizobium nodulation failure — plants will show nitrogen deficiency (pale yellow)",
        ],
        scientific_notes=(
            "The vegetative phase establishes leaf area index (LAI), which determines photosynthetic "
            "capacity and hence yield potential. Target LAI of 3.0-4.5 at flowering is associated with "
            "maximum yield. Nodulation begins 10-14 days after emergence; visible pink nodules indicate "
            "active N-fixation via leghaemoglobin. Until effective nodulation is established, small amounts "
            "of soil or starter N (20-30 kg N/ha) can support early growth without suppressing nodulation. "
            "Peas have a high Kc (crop coefficient) sensitivity to water stress — wilting even for 24 hours "
            "at vegetative stage can reduce final node number and yield."
        ),
    ),

    GrowthStageRequirements(
        stage_name="Flowering",
        stage_code="FL",
        day_range=(35, 55),
        water_kc=0.9,
        water_mm_per_week=35,
        critical_nutrients=["Phosphorus", "Potassium", "Boron", "Calcium", "Magnesium"],
        key_activities=[
            "Maintain consistent irrigation — water stress during flowering causes severe flower abortion",
            "Scout for thrips in flowers with 10x hand lens; check twice weekly",
            "Apply foliar boron (0.5-1.0 kg/ha Solubor) if flower drop suspected due to deficiency",
            "Begin powdery mildew fungicide programme — first spray at 50% flowering",
            "Scout for pea weevil adults emerging on flowers — apply pyrethroid if threshold exceeded",
        ],
        risks=[
            "Thrips damage to flowers reducing pod set",
            "Powdery mildew onset — particularly on varieties like Onward",
            "Heat stress above 26°C causing pollen sterility and flower abortion",
            "Water stress at flowering is the single most yield-limiting event",
            "Pea weevil egg-laying on young pods",
        ],
        scientific_notes=(
            "Garden peas are largely self-pollinating (cleistogamous) but insect pollination increases "
            "pod set by 10-20%. Flowers are borne at nodes on main stem and laterals; number of pods "
            "per plant is determined during this stage. Optimal flowering temperature is 13-20°C; above "
            "26°C pollen viability falls sharply and above 28°C pod abortion is extensive. "
            "Boron is essential for pollen tube growth through style tissue — deficiency causes blossom "
            "drop even when conditions are otherwise favourable. Calcium is critical for pod cell wall "
            "integrity. Water use is highest during this period (peak Kc ~0.9-1.05)."
        ),
    ),

    GrowthStageRequirements(
        stage_name="Pod Fill",
        stage_code="PF",
        day_range=(55, 70),
        water_kc=0.95,
        water_mm_per_week=38,
        critical_nutrients=["Potassium", "Nitrogen", "Calcium", "Magnesium"],
        key_activities=[
            "Maintain optimal soil moisture — seed fill is the primary yield-determining phase",
            "Monitor for pod borer (Helicoverpa) entry holes daily in export crops",
            "Continue powdery mildew and Ascochyta fungicide programme at 14-day intervals",
            "Begin harvest readiness assessment: check seed size, sweetness, and pod fill",
            "Plan labour and cold chain logistics for imminent harvest",
        ],
        risks=[
            "Pod borer larval feeding causing unmarketable pods",
            "Powdery mildew spreading to pods — export rejection risk",
            "Late-season heat stress from October onwards accelerating maturity and reducing seed size",
            "Insufficient irrigation causing wrinkled, underfilled peas",
        ],
        scientific_notes=(
            "Seed fill is the final determinant of garden pea yield and quality. Sucrose translocated "
            "from leaves is converted to starch in cotyledon cells — the rate of starch accumulation "
            "determines seed size (TSS, Tenderness Score). For fresh market/processing, peas are harvested "
            "at the 'green shelling' stage when seeds fill the pod but are still soft and sweet (sugar:starch "
            "ratio is highest). Delayed harvest triggers starch conversion from sucrose, reducing sweetness. "
            "Potassium drives phloem loading of sucrose into seeds; deficiency causes small, off-coloured seeds. "
            "The period from flowering to harvest is 20-35 days depending on temperature."
        ),
    ),

    GrowthStageRequirements(
        stage_name="Maturity & Harvest",
        stage_code="MH",
        day_range=(70, 85),
        water_kc=0.6,
        water_mm_per_week=20,
        critical_nutrients=[],
        key_activities=[
            "Harvest fresh garden peas when pods are fully filled, bright green, and seeds are tender",
            "Pick in the early morning to capture maximum sugar content and reduce field heat",
            "For fresh market/export: rapid pre-cooling to 1-4°C within 2 hours of harvest",
            "Allow pods to dry on plant if producing dried/split peas — harvest when pods turn yellow",
            "For seed production: allow pods to dry fully on plant before threshing",
        ],
        risks=[
            "Over-maturity: seeds become starchy and tough — very narrow harvest window (2-3 days) for fresh market",
            "Harvest damage from rough handling bruises peas under pod — discolouration on opening",
            "Post-harvest warming reverses sugars to starch within hours at ambient temperature",
        ],
        scientific_notes=(
            "The Tenderness Test (TT) or Tenderometer value is used commercially to determine harvest "
            "timing for processed peas — optimal TT value is 95-115. For fresh market peas in Zimbabwe, "
            "visual assessment (pod fill, seed size) combined with taste-testing is standard. "
            "Maturity index: pods fully swollen, seeds separated (not touching), bright green pod, "
            "sweet taste, TT < 120. At ambient tropical temperatures (25-30°C), quality declines "
            "within 4-6 hours of harvest without cooling. Export peas must be maintained at 1-4°C "
            "throughout the cold chain."
        ),
    ),

    GrowthStageRequirements(
        stage_name="Senescence & Field Preparation",
        stage_code="SE",
        day_range=(85, 95),
        water_kc=0.25,
        water_mm_per_week=5,
        critical_nutrients=[],
        key_activities=[
            "Remove all crop residues from the field — chop and incorporate or remove for compost",
            "Cut plants at soil level where possible — leave root system in soil for N-fixation benefit",
            "Deep plough to bury residues, destroy weed seeds, and break pest and disease cycles",
            "Record crop performance for rotation planning and variety selection",
            "Soil test before next crop to assess pH and nutrient status post-legume",
        ],
        risks=[
            "Volunteer pea seedlings from shattered pods may become a weed in the next crop",
            "Residue burn creates air quality issues and destroys beneficial soil organisms — avoid burning",
        ],
        scientific_notes=(
            "Pea root nodules at senescence contain 50-100 kg N/ha that is released through "
            "mineralisation as residues decompose. A follow-on brassica (cabbage, broccoli, cauliflower) "
            "or cereal crop benefits most from this residual nitrogen. Leaving root system in situ "
            "preserves soil structure improved by pea root channels and maximises N benefit. "
            "The C:N ratio of pea residue (approximately 20:1) means residues decompose rapidly, "
            "providing plant-available N within 4-6 weeks in warm, moist Zimbabwe conditions."
        ),
    ),
]


PEAS_FERTILIZER = FertilizerSchedule(
    basal={
        "product": "Compound L (5:18:10) or Single Super Phosphate + Muriate of Potash",
        "rate": "300 kg/ha Compound L (or 250 kg/ha SSP + 50 kg/ha KCl)",
        "timing": "At planting, banded 5 cm below and to the side of seed row",
        "nutrients": "15 kg N, 54 kg P₂O₅, 30 kg K₂O per ha from Compound L",
        "note": (
            "Peas are nitrogen-fixing legumes; basal N is kept low to avoid suppressing Rhizobium "
            "nodulation. Phosphorus is the most critical nutrient at establishment — promotes root "
            "development, nodule formation, and early vigour. Use Compound L (low N, high P) in "
            "preference to Compound D or AN which would deliver excessive nitrogen."
        ),
    },
    top_dress_1={
        "product": "Rhizobium leguminosarum inoculant (seed treatment at planting)",
        "rate": "Peat inoculant: 100-200 g per 25 kg seed; liquid: 5 mL per kg seed",
        "timing": "Applied to seed immediately before planting; do not expose to direct sunlight",
        "nutrients": "No direct NPK; provides 50-100 kg N/ha equivalent through biological N-fixation",
        "note": (
            "This is the most important 'fertiliser' input for peas. Use the correct strain for "
            "Pisum sativum (Rhizobium leguminosarum bv. viciae). If soil has grown peas within the "
            "last 4 years, indigenous strains may be adequate — but inoculation is always recommended "
            "for export crops. Do not use in same mixture with chemical seed treatments unless "
            "compatibility confirmed."
        ),
    },
    top_dress_2={
        "product": "Potassium Sulphate 50 WP (SOP) or Potassium Chloride",
        "rate": "60-80 kg/ha K₂SO₄ (or 50 kg/ha KCl)",
        "timing": "At early flowering (day 35-40)",
        "nutrients": "30-40 kg K₂O per ha",
        "note": (
            "Potassium drives pod and seed fill — deficiency causes small, wrinkled peas with "
            "poor sweetness. Use potassium sulphate in preference to KCl on light, sandy soils "
            "to also supply sulphur (15-18 kg S/ha). Avoid chloride excess on sensitive varieties. "
            "Apply as side-dressing to avoid foliar burn."
        ),
    },
    foliar={
        "product": "Solubor (sodium tetraborate) + Calcium Chloride + Magnesium Sulphate",
        "rate": "0.5-1.0 kg/ha Solubor + 2.0 kg/ha CaCl₂ + 2.0 kg/ha MgSO₄ in 500 L water",
        "timing": "At early flowering (day 35) and repeat 10-12 days later at pod set",
        "note": (
            "Boron is essential for pollen viability and pollen tube elongation — deficiency "
            "causes flower drop and poor pod set without visible leaf symptoms. Calcium strengthens "
            "pod cell walls and reduces pod tip-burn. Magnesium activates ribulose-1,5-bisphosphate "
            "carboxylase (RuBisCO) enzyme for photosynthesis — deficiency reduces sugar content in seeds."
        ),
    },
    liming={
        "ite": "Apply agricultural lime or dolomitic lime if soil pH < 5.8",
        "rate": "1.5-2.5 t/ha agricultural lime depending on buffer pH test result",
        "timing": "Minimum 6 weeks before planting; ideally applied the season prior",
        "note": (
            "Rhizobium leguminosarum is highly sensitive to acidic soil conditions — nodulation "
            "fails below pH 5.5. Target pH 6.0-7.0 for optimal N-fixation and phosphorus availability. "
            "Dolomitic lime is preferred on magnesium-deficient soils common on Zimbabwe's granite-derived "
            "sandy soils (kaolinitic/fersiallitic types). Do not over-lime above pH 7.2 — "
            "manganese and zinc deficiencies emerge above this threshold."
        ),
    },
    notes=(
        "Garden peas fix 60-120 kg N/ha through Rhizobium symbiosis under optimal conditions. "
        "The fertiliser programme deliberately emphasises P, K, and micronutrients over nitrogen. "
        "Excessive N application (>50 kg N/ha) suppresses Rhizobium nodulation, promotes excessive "
        "vegetative growth susceptible to disease and lodging, and reduces pod-to-leaf ratio. "
        "Follow garden peas with a nitrogen-demanding crop (brassicas, maize, wheat) to utilise "
        "residual fixed N from nodule decomposition. "
        "For organic systems, fish meal, bone meal, or compost tea can supply P and K requirements."
    ),
)


PEAS_PLANTING_WINDOWS: List[PlantingWindow] = [
    PlantingWindow(
        region="Highveld (NR IIa/IIb) — Harare, Marondera, Chinhoyi, Bindura",
        optimal_start="April 1",
        optimal_end="May 31",
        acceptable_start="March 15",
        acceptable_end="June 30",
        notes=(
            "Cool dry season under irrigation is the primary production window for garden peas. "
            "Temperatures of 15-22°C during this period are ideal for flowering and pod fill. "
            "Frost risk from late June onwards (especially July-August) — protect with frost cloth "
            "or avoid late-April plantings that will flower in July. "
            "March plantings may experience late rains increasing Ascochyta and downy mildew risk. "
            "Greenfeast and Onward varieties widely grown by commercial farmers around Harare."
        ),
    ),
    PlantingWindow(
        region="Eastern Highlands (NR I) — Nyanga, Juliasdale, Chimanimani, Honde Valley",
        optimal_start="March 1",
        optimal_end="July 31",
        acceptable_start="February 1",
        acceptable_end="August 31",
        notes=(
            "High altitude (1400-2400 m asl) provides cool conditions for extended pea production. "
            "Most productive region for both domestic consumption and export. Staggered plantings "
            "every 3-4 weeks enable continuous supply to export packhouses. "
            "Avoid December-February plantings when rainfall is heavy (>150 mm/month) and disease "
            "pressure from Ascochyta and downy mildew is extreme. "
            "Frost possible at high altitude (Nyanga) from May-September — monitor night temperatures. "
            "This region produces the bulk of Zimbabwe's exported garden peas and snow peas."
        ),
    ),
    PlantingWindow(
        region="Middleveld (NR III) — Mutare lowlands, Gweru, Kadoma",
        optimal_start="April 15",
        optimal_end="June 15",
        acceptable_start="April 1",
        acceptable_end="July 1",
        notes=(
            "Narrower planting window due to higher ambient temperatures. Must target cooler months "
            "(April-June) to avoid heat stress during flowering. Irrigation essential throughout. "
            "Powdery mildew pressure is higher in the Middleveld due to warmer, drier conditions — "
            "plan preventive fungicide programme from early flowering. "
            "July plantings risk heat stress at pod fill if September temperatures rise early."
        ),
    ),
    PlantingWindow(
        region="Irrigated Winter Crop — Lowveld Schemes (Hippo Valley, Triangle)",
        optimal_start="May 1",
        optimal_end="June 30",
        acceptable_start="April 15",
        acceptable_end="July 15",
        notes=(
            "Irrigated pea production is possible in the Lowveld during winter (May-July) when "
            "temperatures moderate sufficiently. Primarily for domestic supply rather than export due "
            "to logistical distance from packhouses. Heat stress management is critical — select "
            "short-season varieties (55-65 day) to complete pod fill before September heat arrives. "
            "Pea weevil and pod borer pressure is higher in Lowveld environments — intensive monitoring required."
        ),
    ),
]


PROFILE = CropProfile(
    crop_name="Garden Peas",
    scientific_name="Pisum sativum",
    family="Fabaceae",
    optimal_ph=(6.0, 7.0),
    critical_ph_low=5.5,
    optimal_soil_types=["fersiallitic", "siallitic"],
    avoid_soil_types=["vertisol", "lithosol"],
    optimal_temp=(12.0, 22.0),
    critical_temp_low=-2.0,
    critical_temp_high=26.0,
    base_temp_gdd=4.0,
    total_water_mm=350.0,
    growth_stages=PEAS_GROWTH_STAGES,
    fertilizer_schedule=PEAS_FERTILIZER,
    diseases=PEAS_DISEASES,
    pests=PEAS_PESTS,
    planting_windows=PEAS_PLANTING_WINDOWS,
    harvest_moisture=(
        "Fresh shelling (green) stage: seeds at 70-75% moisture, pods fully filled, bright green. "
        "For dried/split peas: harvest when pods are papery yellow and seeds hard (<14% moisture)."
    ),
    storage_conditions=(
        "Fresh peas: pre-cool to 1-4°C within 2 hours of harvest. Store at 1-2°C, 90-95% RH. "
        "Shelf life 7-10 days under optimal cold chain. Export in perforated polyethylene bags or "
        "modified atmosphere packaging (3-5% O₂, 5-8% CO₂). "
        "Dried peas: store at <14% moisture in sealed sacks or silos at ambient temperature; "
        "use hermetic bags (e.g., GrainPro) to prevent weevil infestation in storage."
    ),
    post_harvest_notes=(
        "Garden peas are highly perishable fresh — sugar to starch conversion begins within hours of harvest "
        "at ambient temperature. Maintain cold chain from field to packhouse without interruption. "
        "Grade fresh peas by pod size (minimum 60% fill) and colour (bright green, no yellowing). "
        "Remove any pods with insect entry holes, disease spots, or mechanical damage. "
        "Export grades for EU/UK markets require GLOBALG.A.P. certification and MRL compliance — "
        "observe all PHI (pre-harvest intervals) strictly. Primary export destinations from Zimbabwe "
        "include UK, Netherlands, and France. Greenfeast variety is preferred for sweet flavour; "
        "Onward for high yield and large pod size. Both are widely accepted by Zimbabwean exporters."
    ),
    natural_region_suitability={
        "I": (
            "Excellent — cool year-round temperatures ideal for extended cool-season production. "
            "Eastern Highlands is the premier pea-growing region; staggered plantings possible March-August."
        ),
        "IIa": (
            "Good — cool dry season (April-June) under irrigation. Harare plateau area well-suited. "
            "Main commercial production region for domestic supply and some export."
        ),
        "IIb": (
            "Good — cool season production under irrigation, April-June planting window. "
            "Slightly more heat stress risk than IIa; use short-season varieties."
        ),
        "III": (
            "Marginal — limited to May-June window only. Higher temperature variability increases "
            "risk of heat stress at flowering. Irrigation essential. Not recommended for export production."
        ),
        "IV": "Not suitable — too hot and dry for commercial pea production.",
        "V": "Not suitable — extreme heat and drought conditions incompatible with pea production.",
    },
)

ALIASES = ["garden peas", "shelling peas", "nyemba diki"]
