"""Tea (Camellia sinensis) — Perennial acid-loving crop grown in Zimbabwe's Eastern Highlands,
primarily the Honde Valley and Chipinge districts. Zimbabwe's commercial tea is centred on
Tanganda Tea Company, one of the largest tea estates in Africa."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List


TEA_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Blister Blight",
        pathogen="Exobasidium vexans",
        pathogen_type="fungal",
        symptoms=[
            "Pale, water-soaked translucent spots on young expanding leaves (first 2-3 days)",
            "Spots enlarge to form characteristic raised blisters (1-2 cm diameter) on the upper leaf surface",
            "Lower surface of blisters becomes covered in a white powdery mass of basidiospores",
            "Infected leaves curl, distort, and turn brown before dropping prematurely",
            "Affected shoots are stunted; severe infections eliminate the flush entirely",
            "Young stems and petioles may show elongated, irregular blister lesions",
        ],
        identification_markers=[
            "Translucent, light-green water-soaked patches on young unfurled leaves (early diagnostic)",
            "Raised blister on upper surface with white powdery spore mass on corresponding lower surface (definitive)",
            "Lesions confined strictly to young, actively expanding leaf tissue — mature leaves immune",
            "Basidiospores visible as white powder under hand lens in humid early morning conditions",
            "Affected leaves have wrinkled, distorted margins around lesion edges",
            "Never confused with grey blight — blister blight is raised, grey blight is flat with zonation",
        ],
        favourable_conditions={
            "temp_min_c": 16, "temp_max_c": 22,
            "humidity_min": 90,
            "leaf_wetness_hours": 4,
            "altitude": "above 900m — higher risk above 1200m",
            "note": "The most destructive tea disease in Zimbabwe's Eastern Highlands. Optimal "
                    "infection at 16-22 degC with >90% relative humidity and at least 4 hours of "
                    "leaf wetness. Basidiospores germinate in free water on leaf surface. Disease "
                    "is worst during the cool, misty rainy season (November-April) in highland "
                    "estates above 1000m. Honde Valley conditions (1000-1200m) are highly "
                    "conducive. Spore dispersal is primarily by wind and water splash. "
                    "Shade trees can worsen the disease by prolonging canopy wetness duration."
        },
        susceptible_stages=["Young flush", "First leaf", "Second leaf", "Nursery seedlings"],
        resistant_varieties=["PC 108 (moderately resistant)", "SFS 150 (moderate tolerance)"],
        susceptible_varieties=["Older seedling-derived clones", "Unselected seedling populations"],
        chemical_control=[
            {"name": "Copper oxychloride 85 WP", "rate": "3.0-4.0 kg/ha",
             "phi_days": "14", "notes": "Protectant fungicide; apply at 7-10 day intervals during high-risk "
                                         "periods; thorough coverage of young flush essential; mainstay of "
                                         "blister blight programmes in Zimbabwe"},
            {"name": "Hexaconazole 5 EC", "rate": "0.5-1.0 L/ha",
             "phi_days": "14", "notes": "Systemic triazole with curative and eradicant activity; use in "
                                         "rotation with copper to manage resistance; 2-3 applications per season"},
            {"name": "Propiconazole 250 EC", "rate": "0.5-0.75 L/ha",
             "phi_days": "14", "notes": "Ergosterol biosynthesis inhibitor; apply at first symptom detection "
                                         "for curative effect; limit to 2 applications per season"},
            {"name": "Triadimefon 250 WP", "rate": "0.5 kg/ha",
             "phi_days": "21", "notes": "Systemic triazole; effective preventive and curative; alternate "
                                         "with copper-based products to prevent resistance build-up"},
        ],
        biological_control=[
            "Trichoderma-based bioprotectants applied as drench or foliar — limited field efficacy on blister blight",
            "Maintain adequate plant spacing to improve air circulation and reduce canopy wetness duration",
            "Avoid over-use of nitrogen fertiliser which promotes soft, succulent and highly susceptible flush",
            "Strategic pruning (skiffing) to remove infected flush and stimulate clean regrowth",
        ],
        cultural_control=[
            "Plant resistant or tolerant clones (PC 108, SFS 150) as primary management strategy",
            "Avoid shade trees that cause prolonged canopy wetness — manage shade to <30% cover in high-risk blocks",
            "Pluck infected flush tissue promptly to reduce sporulation inoculum within the block",
            "Maintain balanced fertilisation — excess nitrogen produces soft, susceptible young leaves",
            "Improve air drainage by orienting rows along contour to allow cold air and mist to drain",
            "Spray programmes should commence at flush emergence and continue throughout the wet season",
            "Calibrate spray equipment for thorough under-leaf coverage where sporulation occurs",
        ],
        economic_threshold="5% of shoots showing blister blight lesions during the active flush period "
                           "warrants fungicide application; continuous monitoring required in high-altitude blocks",
        severity_scale={
            "mild": "< 5% of shoots affected, scattered lesions on occasional leaves — yield impact minimal",
            "moderate": "5-20% of shoots affected with multiple lesions per shoot — plucking round yield reduced 10-30%",
            "severe": "> 20% of shoots showing heavy blister blight; flush collapse and severe defoliation "
                      "— yield losses of 40-80% of the flush possible in epidemic conditions",
        },
    ),
    DiseaseProfile(
        name="Grey Blight",
        pathogen="Pestalotiopsis theae",
        pathogen_type="fungal",
        symptoms=[
            "Brown, water-soaked lesions beginning at leaf margins or tips (initial symptom)",
            "Lesions expand inward with distinct concentric zonation — alternating light and dark brown bands",
            "Characteristic grey centre develops as lesions age and sporulate",
            "Black pinhead-sized acervuli (fruiting bodies) visible within the grey zone under hand lens",
            "Severely affected leaves dry out and remain attached or fall prematurely",
            "Stems and petioles can be infected in severe cases, causing shoot die-back",
        ],
        identification_markers=[
            "Concentric zonation of brown and greyish-brown bands on lesions — distinguishes grey blight from blister blight",
            "Flat lesions (not raised) typically starting at leaf margins or wounds",
            "Black pinhead acervuli in concentric rings within the lesion (use hand lens)",
            "Lesions usually begin on mature-to-semi-mature leaves, unlike blister blight on young flush",
            "Acervuli exude creamy-white to pinkish spore tendrils (cirri) in wet conditions",
            "Strongly associated with leaf damage from hail, abrasion, or sun scorch",
        ],
        favourable_conditions={
            "temp_min_c": 20, "temp_max_c": 30,
            "humidity_min": 75,
            "note": "Pestalotiopsis theae is primarily a wound pathogen and weak saprophyte that "
                    "enters through mechanical damage (hail, abrasion, frost, sun scorch, insect "
                    "feeding wounds). Humid, warm conditions favour sporulation. Nutrient-stressed "
                    "and drought-stressed plants are significantly more susceptible. Common in "
                    "lower altitude tea blocks in Zimbabwe (Chipinge area, 600-900m). Spores "
                    "dispersed by rain splash and wind."
        },
        susceptible_stages=["Mature leaves", "Semi-mature flush", "Mechanically damaged tissue"],
        resistant_varieties=[],
        susceptible_varieties=["Stressed plants of any variety", "Nutrient-deficient bushes"],
        chemical_control=[
            {"name": "Copper oxychloride 85 WP", "rate": "3.0 kg/ha",
             "phi_days": "14", "notes": "Protectant; apply after hail events or mechanical damage to prevent infection"},
            {"name": "Mancozeb 80 WP", "rate": "2.0-2.5 kg/ha",
             "phi_days": "14", "notes": "Broad-spectrum protectant; particularly useful following hail damage"},
            {"name": "Carbendazim 500 SC", "rate": "0.5-1.0 L/ha",
             "phi_days": "14", "notes": "MBC fungicide; systemic activity; alternate with copper/mancozeb"},
        ],
        biological_control=[
            "Maintain vigorous plant nutrition to reduce physiological stress and susceptibility",
            "Trichoderma harzianum soil applications to improve root health and overall plant immunity",
        ],
        cultural_control=[
            "Avoid mechanical damage during plucking, pruning, and cultural operations",
            "Apply protectant fungicide immediately after hail events before Pestalotiopsis can colonise",
            "Ensure balanced NPK nutrition — deficiency of any major nutrient increases susceptibility",
            "Remove and destroy severely infected branches during pruning to reduce inoculum",
            "Maintain adequate soil moisture — drought-stressed plants are far more susceptible",
            "Reduce sun scorch damage by maintaining appropriate shade cover (20-30%)",
        ],
        economic_threshold="10-15% of leaves showing grey blight lesions, or following a hail event "
                           "in any block, preventive copper application is warranted",
        severity_scale={
            "mild": "< 10% leaves with lesions, confined to older leaf layer — negligible yield impact",
            "moderate": "10-30% leaves affected; some shoot die-back noted — quality and yield reduction",
            "severe": "> 30% leaves affected; shoot die-back; defoliation — major yield loss, replanting of "
                      "severely affected patches may be necessary",
        },
    ),
    DiseaseProfile(
        name="Root Rot (Armillaria / Wood Decay Complex)",
        pathogen="Armillaria mellea",
        pathogen_type="fungal",
        symptoms=[
            "Progressive yellowing and wilting of leaves starting in the upper canopy",
            "General decline in shoot vigour and flush production despite adequate nutrition and moisture",
            "Die-back of individual branches progressing to whole-bush death over months to years",
            "White fan-shaped mycelial mats (rhizomorphs) visible under bark at the collar level",
            "Dark, shoestring-like rhizomorphs found on root surfaces and in surrounding soil",
            "Mushroom fruiting bodies (honey-coloured, in clusters) at base of dying bushes (autumn)",
        ],
        identification_markers=[
            "White to cream mycelial fan under bark at collar and on upper root surfaces (definitive for Armillaria)",
            "Black bootlace-like rhizomorphs connecting affected bush to dead stumps or infected roots in soil",
            "Bitter almond / mushroom odour from infected wood tissue at collar level",
            "Honey-coloured Armillaria fruiting bodies at bush base following rainfall in March-May",
            "Progressive spread — adjacent bushes die in expanding patches over successive seasons",
            "Root cortex slips off the stele; brown discolouration of inner wood tissue",
        ],
        favourable_conditions={
            "soil_type": "previously forested or logged land with residual stumps",
            "moisture": "well-aerated soils — Armillaria not associated with waterlogging",
            "note": "Armillaria mellea spreads vegetatively via rhizomorphs from infected wood "
                    "substrates (old stumps, buried roots). Once established in a block it is "
                    "essentially impossible to eradicate. Expanding circular patches of dead "
                    "bushes are the hallmark. Risk is highest in areas cleared from indigenous "
                    "forest or old mature tea blocks with heavy stump populations. Secondary "
                    "root rot pathogens (Phytophthora spp., Fusarium spp.) may compound damage "
                    "in waterlogged sections."
        },
        susceptible_stages=["Establishment", "All production stages", "Post-prune recovery"],
        resistant_varieties=[],
        susceptible_varieties=["All Camellia sinensis varieties on infected sites"],
        chemical_control=[
            {"name": "Metalaxyl + Mancozeb (Ridomil Gold MZ)", "rate": "2.5 kg/ha soil drench",
             "phi_days": "60", "notes": "Limited efficacy against Armillaria; useful for Phytophthora component "
                                         "in waterlogged sections; drench around root zone of affected bushes"},
            {"name": "Fosetyl-aluminium 80 WP", "rate": "2.5 kg/ha soil drench",
             "phi_days": "60", "notes": "Systemic phosphonate; can suppress Phytophthora root rot as secondary "
                                         "pathogen; no efficacy against Armillaria itself"},
        ],
        biological_control=[
            "Trichoderma harzianum applied as high-volume soil drench around root zone — suppressive effects reported",
            "Bacillus subtilis soil drenches to colonise root zone and reduce secondary pathogen activity",
            "Maintain arbuscular mycorrhizal fungi communities — avoid fumigants that destroy mycorrhizas",
        ],
        cultural_control=[
            "Thorough stump removal and root-raking before establishing new tea or replanting sections",
            "Trench (1m deep) around infected patches to sever rhizomorph spread to healthy bushes",
            "Remove and burn all dead bushes and root fragments from affected patches — do not chip in situ",
            "Allow cleared patches to fallow for 2-3 years under sun-dried conditions to desiccate rhizomorphs",
            "Avoid poorly drained sites; install subsurface drainage if necessary before replanting",
            "Apply lime to raise pH slightly in replant holes — reduces secondary Fusarium activity",
        ],
        economic_threshold="Any expanding patch of dying or dead bushes — investigate collar and root immediately. "
                           "A single confirmed Armillaria patch requires immediate trenching to protect adjacent rows",
        severity_scale={
            "mild": "1-3 dead bushes in a block; single focus — investigate and trench immediately",
            "moderate": "Expanding patch of 5-20 dead bushes; rhizomorphs confirmed — trench and remove all stumps",
            "severe": "Large irregular patches of dead bushes across multiple rows — infill planting not viable "
                      "without full stump removal and extended fallow; long-term production compromised",
        },
    ),
    DiseaseProfile(
        name="Red Rust (Algal Leaf Spot)",
        pathogen="Cephaleuros virescens",
        pathogen_type="algal",
        symptoms=[
            "Orange-red to rusty-brown, roughly circular spots on the upper surface of older leaves",
            "Spots are slightly raised, velvety, and covered in orange-red sporangiophores and sporangia",
            "Heavily affected leaves develop multiple coalescing spots that cover large leaf areas",
            "Premature leaf drop of heavily infected mature leaves",
            "Stem lesions (less common) appear as orange-brown rough patches on green stems",
            "Severely affected bushes show general loss of older leaf layer and thin canopy",
        ],
        identification_markers=[
            "Rusty-orange velvety surface growth on upper leaf surface — unmistakable algal thallus",
            "Circular to irregular outline, 3-15 mm diameter, raised above leaf surface",
            "Orange-red colouration from carotenoid-rich sporangiophores (hand lens confirms filamentous structure)",
            "Affects mature, not young, leaves — opposite pattern to blister blight",
            "Lesions visible on stems as rough, orange-brown corky patches",
            "Common in lower-altitude, warmer, wetter sections of the estate",
        ],
        favourable_conditions={
            "temp_min_c": 20, "temp_max_c": 30,
            "humidity_min": 80,
            "note": "Cephaleuros virescens is a parasitic green alga requiring warm, humid conditions "
                    "for zoospore release and infection. Most problematic in lower-altitude sections "
                    "of Eastern Highlands estates (below 1000m). Weak, nutrient-deficient, or "
                    "drought-stressed bushes are more severely affected. Zoospores dispersed by "
                    "water splash. High iron in soils may predispose some blocks. Shade increases "
                    "humidity and can worsen algal disease. Typically a secondary problem but can "
                    "cause significant leaf loss in neglected or stressed plantations."
        },
        susceptible_stages=["Mature leaves", "Semi-mature leaves", "Stems"],
        resistant_varieties=[],
        susceptible_varieties=["Stressed, nutrient-deficient bushes of all varieties"],
        chemical_control=[
            {"name": "Copper oxychloride 85 WP", "rate": "3.0-4.0 kg/ha",
             "phi_days": "14", "notes": "Copper effectively suppresses algal growth; 2-3 applications at "
                                         "6-8 week intervals during warm, wet season; copper programmes "
                                         "for blister blight will simultaneously suppress red rust"},
            {"name": "Bordeaux mixture 1%", "rate": "Apply as per mixing instructions",
             "phi_days": "14", "notes": "Traditional copper-lime preparation; effective and low cost; "
                                         "prepare fresh; 2-3 seasonal applications"},
        ],
        biological_control=[
            "No commercially available biocontrol agents specific to Cephaleuros",
            "Optimise plant nutrition — vigorous well-nourished bushes tolerate algal infection far better",
        ],
        cultural_control=[
            "Ensure adequate and balanced NPK nutrition to maintain plant vigour",
            "Reduce shade density in affected blocks to lower canopy humidity",
            "Improve drainage to reduce standing water at bush base and soil splash",
            "Remove heavily infected older leaves during skiffing or tipping operations",
            "Annual copper applications as part of the blister blight spray programme provide simultaneous control",
            "Avoid waterlogging and improve air drainage in affected sections",
        ],
        economic_threshold="15-20% of mature leaves showing red rust symptoms; or following "
                           "previous season's defoliation from algal disease in a block",
        severity_scale={
            "mild": "< 10% of mature leaves with spots; isolated blocks — cosmetic damage only",
            "moderate": "10-30% of mature leaves affected; some defoliation; canopy thinning reducing yield",
            "severe": "> 30% of mature leaves lost; severe canopy thinning — increased bushiness required; "
                      "replant sections if combined with other stresses",
        },
    ),
]


TEA_PESTS: List[PestProfile] = [
    PestProfile(
        name="Tea Mosquito Bug",
        scientific_name="Helopeltis schoutedeni",
        pest_type="insect",
        identification=[
            "Slender, delicate hemipteran bug, 6-8 mm long; bright red-orange body with black head and legs",
            "Distinctive long, slender antennae (longer than body) with conspicuous club-shaped dorsal process on scutellum",
            "Nymphs red-orange, smaller, similar shape; early instars darker",
            "Adults and nymphs feed using piercing-sucking mouthparts on actively growing shoot tips",
            "Often visible in early morning on young flush before temperature rises and adults disperse",
        ],
        damage_symptoms=[
            "Dark brown to black necrotic lesions at feeding puncture sites on young shoots and leaves",
            "Lesions enlarge to irregular black patches that crack and fall out — characteristic 'shot hole' appearance",
            "Young shoots wilt, blacken, and die back — known as 'tip die-back' or 'bunchy top'",
            "Severely affected plucking tables show extensive dead shoot tips with few harvestable shoots",
            "Economic losses can be severe during flush periods, especially on highland estates November-March",
        ],
        life_cycle_notes=(
            "Incomplete metamorphosis (hemimetabolous). Female inserts eggs singly into soft plant tissue with a "
            "characteristic pair of filamentous respiratory horns protruding from the surface. Egg incubation "
            "7-10 days. Five nymphal instars over 20-30 days. Adult longevity 3-4 weeks. Multiple overlapping "
            "generations throughout the year in Zimbabwe. Peak populations coincide with periods of active flush "
            "growth (November-March during rainy season). Population build-up is rapid in warm, humid conditions. "
            "Adults disperse readily by flight; local spread by walking down shoots."
        ),
        favourable_conditions={
            "temp_min_c": 18, "temp_max_c": 28,
            "humidity_min": 70,
            "note": "Helopeltis schoutedeni thrives in warm, humid flush-growth periods. Populations "
                    "build rapidly when tea is actively growing (November-March in Honde Valley). "
                    "Shaded sections and forest margins harbour adults. Drought reduces both pest "
                    "and host activity. Older, dense tea with limited air circulation is worst affected. "
                    "Border rows adjacent to woodland are high-risk zones."
        },
        susceptible_stages=["Young flush", "First leaf", "Second leaf", "Nursery shoots"],
        economic_threshold="1-2 bugs per 10 shoots or > 5% of shoots showing active feeding damage",
        chemical_control=[
            {"name": "Dimethoate 40 EC", "rate": "1.0-1.5 L/ha",
             "phi_days": "7", "notes": "Systemic organophosphate; apply at threshold; thorough coverage "
                                        "of young flush essential; widely used in Zimbabwe tea"},
            {"name": "Lambda-cyhalothrin 5 EC", "rate": "300-400 ml/ha",
             "phi_days": "7", "notes": "Pyrethroid; fast knockdown; use as rotation partner with dimethoate; "
                                        "disrupts natural enemies — use judiciously"},
            {"name": "Imidacloprid 200 SL", "rate": "250-350 ml/ha",
             "phi_days": "14", "notes": "Systemic neonicotinoid; soil drench or foliar; caution on pollinators; "
                                         "use as part of resistance management rotation"},
            {"name": "Acetamiprid 20 SP", "rate": "150-200 g/ha",
             "phi_days": "7", "notes": "Neonicotinoid; good systemic activity; lower bee toxicity than imidacloprid; "
                                        "preferred option for managed bee areas"},
        ],
        biological_control=[
            "Egg parasitoids (Erythmelus kloppersi and related Mymaridae) provide natural suppression — conserve by "
            "avoiding broad-spectrum insecticides during non-threshold periods",
            "Nymphal predators including Reduviidae (assassin bugs) and spiders — important in unsprayed blocks",
            "Maintain semi-natural vegetation strips at field margins as refugia for natural enemy populations",
            "Beauveria bassiana formulations show moderate efficacy in humid, rainy conditions — apply in cool mornings",
        ],
        cultural_control=[
            "Regular and frequent plucking removes eggs laid in shoot tissue and reduces harbouring sites",
            "Pluck to a close, uniform plucking table level — tall, uneven tea harbours larger populations",
            "Control forest margins and undergrowth along block boundaries where adults shelter",
            "Avoid skipping plucking rounds during high-flush periods when populations build rapidly",
            "Shade management — reduce shade in heavily infested blocks to improve spray access and reduce humidity",
            "Weed control removes ground-level harbouring habitat and alternative host plants",
        ],
        scouting_protocol=(
            "Weekly during flush periods (November-April). Walk transects through each block, sampling 10 "
            "consecutive shoots at 10 sampling points per hectare (100 shoots total). Count live adults and "
            "nymphs per shoot and record percentage of shoots with fresh (dark, moist) feeding lesions. "
            "Note natural enemy presence. Treatment threshold: 1-2 live bugs per 10 shoots or >5% shoots with "
            "fresh lesions. Record by block and map to identify persistently infested areas. Inspect border "
            "rows adjacent to woodland more frequently."
        ),
    ),
    PestProfile(
        name="Red Spider Mite (Tea Red Mite)",
        scientific_name="Oligonychus coffeae",
        pest_type="mite",
        identification=[
            "Tiny (0.4-0.5 mm) brick-red to dark red mite, barely visible to naked eye",
            "Females oval-bodied, darker red; males smaller and more elongate",
            "Eight-legged adults and nymphs; six-legged larvae at hatching",
            "Pale, creamy-white spherical eggs laid on upper leaf surface along midrib and veins",
            "Characteristic bronzing of upper leaf surface from feeding — distinguishes from other mites",
            "Silk webbing absent or minimal (unlike Tetranychus spider mites which produce copious webbing)",
        ],
        damage_symptoms=[
            "Feeding on upper leaf surface causes fine stippling — individual puncture sites visible as tiny white dots",
            "Progressive bronzing of the upper leaf surface from green to bronze-brown",
            "Severely infested leaves have a dull, bronze-metallic sheen and feel rough to touch",
            "Heavy infestations cause premature leaf drop and defoliation of older leaf layer",
            "Quality of made tea from heavily mite-infested leaf is reduced — altered aroma and liquor colour",
            "Shoot growth and flush production suppressed under heavy mite pressure during drought periods",
        ],
        life_cycle_notes=(
            "Eggs hatch after 3-5 days; larval, protonymph, and deutonymph stages over 5-10 days total; "
            "adult female lives 10-15 days, laying 30-50 eggs individually on upper leaf surface. "
            "Complete generation time 10-20 days depending on temperature. Populations can double in "
            "less than one week in ideal conditions. Dispersal by walking, wind, and on harvested leaf. "
            "No sexual diapause — all year development in Zimbabwe's Eastern Highlands. Drought stress "
            "on bushes dramatically accelerates population growth by reducing plant defences and increasing "
            "amino acid content of leaf sap."
        ),
        favourable_conditions={
            "temp_min_c": 24, "temp_max_c": 35,
            "humidity_max": 60,
            "note": "Oligonychus coffeae populations explode during hot, dry conditions — particularly "
                    "the June-October dry season in Zimbabwe's Eastern Highlands. Drought-stressed "
                    "bushes are far more susceptible. Dusty conditions from unpaved roads coat leaves "
                    "and suppress natural enemies. Broad-spectrum insecticide use (especially pyrethroids) "
                    "eliminates predatory mites and triggers secondary outbreaks. Nutrient-deficient "
                    "or waterlogged bushes have elevated soluble amino acid content favouring mite "
                    "reproduction."
        },
        susceptible_stages=["Mature leaf", "Semi-mature leaf", "Post-prune regrowth"],
        economic_threshold="5-10 motile mites per mature leaf on average across sampled leaves, "
                           "or visible bronzing across > 10% of mature leaf surface in a block",
        chemical_control=[
            {"name": "Dicofol 18.5 EC", "rate": "1.5-2.0 L/ha",
             "phi_days": "7", "notes": "Specific acaricide (organochlorine derivative); "
                                        "no insecticide activity so natural enemies of insects conserved; "
                                        "primary miticide in Zimbabwe tea; 2 applications per season maximum"},
            {"name": "Abamectin 18 EC", "rate": "300-400 ml/ha",
             "phi_days": "7", "notes": "Macrocyclic lactone; excellent activity on all motile stages; "
                                        "some ovicidal action; use in alternation with dicofol"},
            {"name": "Hexythiazox 10 WP", "rate": "500-750 g/ha",
             "phi_days": "14", "notes": "Ovicide/larvicide; disrupts juvenile stages; no adult activity; "
                                         "use in combination with adulticide for rapid knockdown"},
            {"name": "Fenazaquin 200 SC", "rate": "500-700 ml/ha",
             "phi_days": "14", "notes": "Quinazoline acaricide; broad spectrum on all stages; "
                                         "useful third rotation partner; avoid use near water"},
        ],
        biological_control=[
            "Phytoseiid predatory mites (Amblyseius spp., Euseius spp.) are the primary natural control agents "
            "— protect by avoiding broad-spectrum insecticides, especially pyrethroids",
            "Stethorus spp. (small black coccinellid beetles) and Oligota spp. (staphylinid beetles) are "
            "specialist mite predators in tea — found in low-input blocks",
            "Beauveria bassiana and Metarhizium anisopliae formulations registered for mites in some countries — "
            "apply in cool, humid conditions for best efficacy",
            "Conserve biological control by using selective acaricides (dicofol, hexythiazox) rather than "
            "broad-spectrum organophosphates or pyrethroids where possible",
        ],
        cultural_control=[
            "Irrigate during dry season — mite populations on irrigated blocks are 60-80% lower than rain-fed blocks",
            "Suppress road dust with water spray or compaction to protect natural predator populations on border rows",
            "Avoid excessive nitrogen applications — high N increases mite fecundity via elevated leaf amino acid content",
            "Do not use pyrethroids in mite-prone blocks — use selective organophosphates (dimethoate) instead for insects",
            "Remove weed hosts (Bidens, Lantana) from block borders where Oligonychus may overwinter or bridge",
            "Monitor closely in July-September (peak dry season) as populations can increase 10-fold in 3-4 weeks",
        ],
        scouting_protocol=(
            "Bi-weekly from June through October (dry season); monthly during wet season. "
            "Sample 10 mature leaves from the second or third leaf position per plucking round from 20 "
            "sample bushes per hectare (200 leaves total). Examine each leaf under hand lens; count "
            "motile mites on a 4 cm2 area of upper leaf surface and extrapolate. Record egg numbers "
            "and natural predator presence separately. Alert threshold: 5 motile mites per leaf average "
            "across 30% of sampled leaves. Economic threshold: 10 motile mites per leaf. Also record "
            "bronzing percentage of leaf surface area."
        ),
    ),
    PestProfile(
        name="Soft Scales (Brown Soft Scale and related)",
        scientific_name="Coccus hesperidum / Pulvinaria psidii",
        pest_type="insect",
        identification=[
            "Coccus hesperidum: flat, oval, 2-3 mm, yellowish-brown to dark brown, waxy scale cover",
            "Pulvinaria psidii (mealybug scale): female surrounded by white cottony egg mass, 4-5 mm",
            "Found on stems, branch junctions, and undersides of mature leaves",
            "Immobile females firmly attached to bark; crawlers (first instars) disperse to new shoots",
            "Honeydew secretion promotes black sooty mould on leaves and stems below colonies",
            "Ant trails on trunk indicate active scale colonies (ant-scale mutualism)",
        ],
        damage_symptoms=[
            "Heavy black sooty mould on leaves and stems from honeydew produced by scale insects",
            "Wilting and yellowing of infested shoots — phloem sap removal weakens affected branches",
            "Stem tissue girdling under very heavy infestations — shoot die-back",
            "Photosynthesis severely impaired by sooty mould coating leaves — quality and yield reduction",
            "General loss of bush vigour and reduced flush production in heavily infested blocks",
            "Ant activity and honeydew on leaves attract attention to infested stems",
        ],
        life_cycle_notes=(
            "Coccus hesperidum reproduces parthenogenetically (no males needed). Females produce 500-2000 "
            "crawlers over several weeks. Crawlers settle and insert stylet to feed on phloem. First moult "
            "after 2-3 weeks; second moult produces adult female 6-8 weeks post-settling. Two to four "
            "generations per year in Zimbabwe's year-round tea production. Pulvinaria psidii similar; "
            "white cottony ovisac produced by mature female before death. "
            "Ant-scale mutualism critical: ants transport crawlers and deter natural enemies. "
            "Spread via movement of planting material and wind-dispersed crawlers."
        ),
        favourable_conditions={
            "temp_min_c": 18, "temp_max_c": 28,
            "note": "Scales build up in sheltered, shaded microhabitats with high humidity. Dense, "
                    "over-grown tea with closed canopy and poor air circulation is most at risk. "
                    "Ant mutualism dramatically amplifies scale populations by deterring parasitoids "
                    "and predators. Drought-stressed and nutrient-deficient plants are more susceptible. "
                    "Infested nursery material is a major source of scale introduction to new blocks."
        },
        susceptible_stages=["Established bushes", "Nursery plants", "Post-prune regrowth"],
        economic_threshold="20% of sampled stems showing active scale colonies with live crawlers, "
                           "or sooty mould covering > 15% of leaf area in a block",
        chemical_control=[
            {"name": "White mineral oil (horticultural oil) 97%", "rate": "10-15 L/ha in 500-1000 L water",
             "phi_days": "1", "notes": "Smothers all scale stages including eggs; extremely safe; excellent "
                                        "for use close to harvest; combine with water high-volume spray"},
            {"name": "Chlorpyrifos 48 EC", "rate": "1.5-2.0 L/ha",
             "phi_days": "14", "notes": "Organophosphate; targets crawlers (most susceptible stage); "
                                         "apply when crawlers detected under lens; disrupts natural enemies"},
            {"name": "Buprofezin 25 WP", "rate": "0.75-1.0 kg/ha",
             "phi_days": "14", "notes": "Chitin synthesis inhibitor; acts on crawlers/nymphs only — no adult "
                                         "activity; selective and safe to parasitoids; preferred IPM option"},
        ],
        biological_control=[
            "Parasitoid wasps (Metaphycus spp., Coccophagus spp.) are highly effective natural enemies — "
            "conserve by avoiding organophosphates and pyrethroids during natural enemy activity",
            "Cryptolaemus montrouzieri (mealybug destroyer) also preys on soft scale crawlers",
            "Control ant colonies with bait stations at bush bases to expose scales to parasitoids",
            "Entomopathogenic fungi (Lecanicillium lecanii) applied as foliar spray in humid conditions",
        ],
        cultural_control=[
            "Inspect all nursery material thoroughly before field planting — reject infested stock",
            "Prune to open canopy and improve air circulation — reduces humid microhabitats favoured by scales",
            "Band tree trunks and stems with sticky grease barriers to interrupt ant-scale mutualism",
            "Control ants at colony level using ant bait stations around infested blocks",
            "Remove heavily infested branches during pruning and destroy to reduce inoculum",
            "Maintain vigorous plant nutrition and irrigation — healthy plants tolerate scale pressure far better",
        ],
        scouting_protocol=(
            "Monthly inspection; increase to fortnightly when scale activity noted. Sample 20 bushes per "
            "hectare; examine 3 stems (5 cm section) and 10 leaves per bush for scale presence, live crawlers, "
            "honeydew, sooty mould, and natural enemy activity. Record presence of ants. Score 0-3 scale "
            "(0=absent, 1=low, 2=moderate, 3=heavy) per bush. Trigger spray when >20% of bushes score 2 or "
            "higher. Also examine nursery stock monthly."
        ),
    ),
    PestProfile(
        name="Tea Tortrix Moth (Tea Looper and related leaf-rollers)",
        scientific_name="Homona coffearia",
        pest_type="insect",
        identification=[
            "Adult: pale brown to ochreous moth, 12-16 mm wingspan; forewing with darker brown stripes and "
            "a characteristic costal fold in males",
            "Larvae: 15-20 mm, pale green to yellowish-green, with dark head capsule; wriggle vigorously "
            "and drop on silk thread when disturbed",
            "Eggs laid in overlapping flat clusters (egg masses) on upper leaf surface; pale green when fresh, "
            "darkening before hatching",
            "Silken retreat created by tying leaves together with webbing — characteristic 'leaf roll'",
            "Pupae: brown, in rolled leaf; adults emerge at dusk and are attracted to light traps",
        ],
        damage_symptoms=[
            "Characteristic rolled or tied leaves on young shoots — larvae shelter and feed within rolled leaf",
            "Skeletonisation of enclosed leaf tissue where larva feeds on lower epidermis and mesophyll",
            "Complete consumption of young leaf tissue in heavily infested shoots",
            "Webbing and frass (green pellets) visible in rolled leaf retreat when unrolled",
            "Shoot tip damage reduces pluckable shoot production in affected blocks",
            "Severe infestations in nurseries can completely destroy young rooted cuttings",
        ],
        life_cycle_notes=(
            "Female lays egg masses (50-100 eggs) on mature leaves. Eggs hatch after 5-8 days. Young larvae "
            "initially mine leaf tissue or feed gregariously, later each constructs individual rolled-leaf retreat. "
            "Larval development 25-35 days through 5-6 instars. Pupation in rolled leaf; adult emergence after "
            "7-10 days. Multiple overlapping generations throughout the year; 4-6 generations annually in Zimbabwe's "
            "warm Eastern Highlands climate. Peak populations occur during active flush periods (November-April). "
            "Adults are nocturnal and positively phototactic."
        ),
        favourable_conditions={
            "temp_min_c": 18, "temp_max_c": 30,
            "note": "Homona coffearia is present year-round in Zimbabwe's Eastern Highlands but population "
                    "peaks during November-April flush period when young leaf tissue is abundant. Shaded, "
                    "warm blocks with vigorous flush are most affected. Heavy nitrogen fertilisation producing "
                    "soft succulent flush increases larval survival. Natural enemies are generally effective "
                    "in maintaining populations below economic thresholds in unsprayed blocks."
        },
        susceptible_stages=["Young flush", "First leaf", "Second leaf", "Nursery cuttings", "Nursery seedlings"],
        economic_threshold="5% of sampled shoots containing live larvae or fresh leaf rolls, or > 3 fresh "
                           "leaf rolls per 10 shoots in nursery blocks",
        chemical_control=[
            {"name": "Bacillus thuringiensis var. kurstaki (Bt) 32 WP", "rate": "1.0-1.5 kg/ha",
             "phi_days": "0", "notes": "Biological insecticide; highly selective for Lepidoptera larvae; "
                                        "zero PHI — ideal for use close to plucking round; apply in late afternoon; "
                                        "preferred first-line option in IPM programmes"},
            {"name": "Chlorantraniliprole 200 SC (Coragen)", "rate": "150-200 ml/ha",
             "phi_days": "7", "notes": "Diamide insecticide; highly effective on all larval stages; very "
                                        "selective — safe to most beneficial insects and mites; use as IPM "
                                        "cornerstone when Bt not sufficient"},
            {"name": "Emamectin benzoate 19 EC", "rate": "300-400 ml/ha",
             "phi_days": "7", "notes": "Macrocyclic lactone; highly active on Lepidoptera larvae; systemic "
                                        "activity; use in alternation with Bt or diamides"},
            {"name": "Spinosad 480 SC", "rate": "200-250 ml/ha",
             "phi_days": "7", "notes": "Naturalyte (fermentation product); selective — low impact on parasitoids "
                                        "and predatory mites; good resistance management partner"},
        ],
        biological_control=[
            "Trichogramma spp. egg parasitoids — highly effective natural enemies conserved under selective "
            "insecticide programmes; mass release possible in high-pressure situations",
            "Larval parasitoids (Apanteles spp., Meteorus spp., ichneumonids) — present in unsprayed blocks; "
            "conserve by using Bt or diamides instead of broad-spectrum products",
            "Nuclear polyhedrosis viruses (NPV) naturally circulate in tortrix populations — conserve by "
            "avoiding disruptive chemistries",
            "Spiders, predatory beetles, and earwigs prey on larvae in exposed positions",
        ],
        cultural_control=[
            "Regular plucking every 7-10 days removes eggs and young larvae with harvested shoots before "
            "larvae can complete development",
            "Hand-pick leaf rolls during scouting visits to reduce local population density",
            "Light traps used for adult monitoring and mass capture (though limited suppressive effect alone)",
            "Maintain clean nursery practices — inspect all batches of cuttings for egg masses",
            "Balanced fertilisation — avoid excessive nitrogen that promotes succulent flush favouring larvae",
            "Shade management to reduce warm, sheltered microhabitats preferred by adults for egg-laying",
        ],
        scouting_protocol=(
            "Weekly during flush periods (November-April); fortnightly during dry season. "
            "Sample 10 consecutive shoots at 10 points per hectare (100 shoots). Count fresh leaf rolls "
            "and live larvae per shoot. Open 5 leaf rolls per sample point to confirm live larvae and "
            "parasitism rates. Record natural enemy activity. Use light traps (1 per 10 ha) for adult "
            "monitoring to predict population build-up 2-3 weeks ahead. Treatment threshold: 5% of shoots "
            "with live larvae. In nurseries, zero tolerance — treat at first detection of egg masses."
        ),
    ),
]


TEA_GROWTH_STAGES: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Establishment — Nursery and Field Planting",
        stage_code="GS0",
        day_range=(0, 365),
        water_kc=0.60,
        water_mm_per_week=20,
        critical_nutrients=["P", "N", "K"],
        key_activities=[
            "Prepare nursery beds: friable, acid soil (pH 4.5-5.0) with coarse sand for drainage",
            "Collect single-node stem cuttings from high-yielding mother bushes (PC 108, SFS 150 clones)",
            "Dip cutting bases in IBA rooting hormone (3000-5000 ppm) and insert in nursery medium",
            "Apply micro-drip or mist irrigation to maintain 80-90% RH around cuttings (fog houses ideal)",
            "Shade nursery to 50-60% (with shade cloth or slat frames) — reduce as plants establish",
            "Apply dilute NPK liquid fertiliser (e.g., 100:100:100 ppm) weekly from 8 weeks after striking",
            "Harden-off plants gradually over 4-6 weeks before field planting",
            "Prepare field: rip to 60 cm depth, apply rock phosphate + lime in planting line",
            "Plant at onset of reliable rains (November-January) at 1.1 m x 0.75 m spacing",
            "Install shade using Grevillea or Albizia trees planted 1-2 years prior",
            "Apply 5 cm mulch layer around each plant after planting to conserve moisture",
            "Peg and stake young plants against wind damage in exposed areas",
        ],
        risks=[
            "Cutting failure due to low humidity in fog house",
            "Nursery pathogens (Phytophthora damping-off) on cuttings",
            "Transplant shock — planting during dry period",
            "Weed competition in the first 6-12 months",
            "Mole cricket and cutworm damage to newly planted seedlings",
            "Frost during winter (June-August) if planted too early",
        ],
        scientific_notes=(
            "Tea propagation in Zimbabwe is exclusively vegetative (stem cuttings from proven clonal material) "
            "to preserve the agronomic and quality characteristics of elite clones such as PC 108 and SFS 150, "
            "selected by Tea Research Foundation of Central Africa (TRFCA). Single-node cuttings from "
            "semi-hardened tissue root within 8-12 weeks in humid fog houses (>85% RH) maintained at 22-26 degC. "
            "Auxin application (IBA) stimulates adventitious root initiation from callus at the cut base. "
            "Tea is ericaceous (acid-loving): optimal soil pH 4.5-5.5 for nutrient availability and "
            "suppression of soil-borne pathogens. Aluminium (Al3+), which is soluble and potentially toxic "
            "at pH below 4.2, is paradoxically beneficial at moderate concentrations in tea — stimulating "
            "root growth and P uptake via organic acid release. Field establishment during the rainy season "
            "is essential for survival. Young tea requires 18-24 months before first tipping (formative pruning)."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Young Tea — Formative Years",
        stage_code="GS1",
        day_range=(365, 1095),
        water_kc=0.70,
        water_mm_per_week=22,
        critical_nutrients=["N", "P", "K", "Mg"],
        key_activities=[
            "Year 2 (months 12-18): First tipping — cut back to uniform height (30-35 cm) to form frame",
            "Apply first full fertiliser dressing after first tipping: NPK 2:1:1 at 60% of mature rate",
            "Mulch renewal around each bush (5-10 cm) to suppress weeds and conserve moisture",
            "Weed management: 3-4 inter-row cultivations per year; hand-weed under bush canopy",
            "Year 3 (months 18-24): Second tipping to raise plucking table to 45-50 cm",
            "Shade management: progressively thin shade trees as tea canopy expands",
            "Scout for Helopeltis, blister blight, and red spider mite — apply controls at threshold",
            "Apply maintenance pruning (centre-opening cuts) to prevent bush from becoming too congested",
            "Monitor drainage — waterlogging at this stage is highly damaging to root establishment",
        ],
        risks=[
            "Blister blight on young flush during wet season",
            "Helopeltis tip die-back during flush periods",
            "Weed competition suppressing young bush growth",
            "Drought stress if rains fail in January-February",
            "Wind damage to young bushes on exposed slopes",
        ],
        scientific_notes=(
            "The formative period (years 1-3) is critical for establishing the permanent branching framework "
            "(frame) that will support productive plucking for 30-50 years. Formative pruning (tipping) "
            "forces lateral branch development and lowers the centre of gravity of the bush, improving stability "
            "and promoting a wide, flat plucking table. Nitrogen application drives vegetative growth but must "
            "be balanced against the risk of producing over-succulent flush susceptible to blister blight "
            "and Helopeltis. Phosphorus at establishment is critical for root system development; "
            "rock phosphate (slow-release) or SSP is applied at planting. The root system is concentrated "
            "in the top 30 cm but extends laterally 60-90 cm beyond the canopy edge. Young tea should "
            "not be harvested for leaf during the formative period — all biomass must be retained for "
            "frame establishment and root development."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Mature Tea — Dormancy (Dry Season Rest)",
        stage_code="GS2",
        day_range=(0, 60),
        water_kc=0.45,
        water_mm_per_week=14,
        critical_nutrients=["K", "Mg"],
        key_activities=[
            "Pruning cycle: prune every 3-4 years during dry season (June-August) to 55-65 cm height",
            "Apply lime to soil under canopy if pH has fallen below 4.0 (avoid over-liming above 5.5)",
            "Soil and leaf tissue sampling for nutrient analysis before the new season programme",
            "Repair drainage channels and terracing to prevent soil erosion in first rains",
            "Apply basal phosphate (rock phosphate or SSP) along the row during pruning",
            "Mulch replenishment: apply 10-15 t/ha of green mulch or pruning waste under canopy",
            "Pest and disease sanitation: destroy pruning waste containing scale, mite eggs, tortrix pupae",
            "Repair infrastructure: tracks, water supply lines, irrigation systems",
            "Shade tree management: thin or pollard shade trees to optimal 20-30% cover",
        ],
        risks=[
            "Frost damage to pruned stumps in elevated blocks (above 1400m) — do not prune immediately before frost season",
            "Armillaria root rot damage visible when pruning dead or dying bushes — investigate and trench",
            "Soil erosion on steep slopes in early rains after pruning exposes bare soil",
            "Drought stress on recently pruned bushes if dry season is extended",
        ],
        scientific_notes=(
            "Tea is pruned on a 3-4 year cycle (skeletonising prune to 55-65 cm) to rejuvenate the plucking "
            "table and prevent a large, woody collar forming that reduces flush production efficiency. "
            "Pruning is conducted during the dry season when vegetative growth is minimal. Following pruning, "
            "the bush relies entirely on carbohydrate reserves stored in stems and roots to produce the "
            "first post-prune flush (recovery flush). Adequate potassium levels in the bush are critical "
            "for this carbohydrate reserve capacity. The first post-prune flush is vigorous but susceptible "
            "to blister blight and Helopeltis as it is young and unprotected. Magnesium is critical for "
            "chlorophyll development in the expanding post-prune flush. In Zimbabwe, the pruning cycle is "
            "typically aligned with the June-August dry season to allow recovery before the November rains "
            "bring conditions for maximum flush production."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Mature Tea — Post-Prune Recovery Flush",
        stage_code="GS3",
        day_range=(60, 150),
        water_kc=0.75,
        water_mm_per_week=24,
        critical_nutrients=["N", "Mg", "Zn"],
        key_activities=[
            "Apply first post-prune nitrogen top-dress: CAN at 100-120 kg N/ha as new shoots emerge",
            "Apply foliar magnesium sulphate (MgSO4 5 g/L) to support chlorophyll development in new flush",
            "Apply foliar zinc sulphate (ZnSO4 3 g/L) for new shoot growth and enzyme activity",
            "Begin blister blight spray programme as first flush emerges (copper-based)",
            "Commence Helopeltis scouting — recovery flush is highly susceptible to tip die-back",
            "Skiffing at 8-10 cm above prune cut to stimulate branching before first tipping",
            "Maintain weed-free strip under canopy for first 4-6 months post-prune",
        ],
        risks=[
            "Blister blight epidemic on succulent post-prune flush during wet, cool weather",
            "Helopeltis tip die-back destroying recovery shoots and delaying table establishment",
            "Frost damage to newly emerged shoots if prune coincided with late cold season",
            "Red spider mite build-up if dry season persists",
        ],
        scientific_notes=(
            "The post-prune recovery flush is the most critical flush of the pruning cycle. The bush must "
            "regenerate its entire plucking table from pruning stubs over 8-12 weeks. During this phase, "
            "photosynthetic capacity is severely reduced and the plant depends on root and stem carbohydrate "
            "reserves. Nitrogen application at shoot emergence is timed to support rapid leaf area development "
            "without pre-loading the soil before the flush emerges (which would cause leaching). Magnesium "
            "is directly incorporated into chlorophyll molecules and is often deficient in Eastern Highlands "
            "soils that have been acidified over years of tea cultivation and nitrogen fertilisation. "
            "Zinc is a cofactor for over 300 enzymes and is critical for RNA polymerase activity in rapidly "
            "dividing meristematic cells. The new flush post-prune is physiologically young, thin-cuticled, "
            "and maximally susceptible to blister blight infection — fungicide programmes must begin immediately."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Mature Tea — Main Flush (Rainy Season Production)",
        stage_code="GS4",
        day_range=(150, 300),
        water_kc=1.00,
        water_mm_per_week=30,
        critical_nutrients=["N", "K", "S"],
        key_activities=[
            "Plucking every 7-10 days during peak flush (November-March): two leaves and a bud standard",
            "Apply second nitrogen top-dress: CAN 80-100 kg N/ha split across 2-3 applications during flush",
            "Apply potassium (KCl or SOP) 60-80 kg K2O/ha during active flush for quality improvement",
            "Continue blister blight spray programme (copper or systemic fungicide) at 10-14 day intervals",
            "Monitor Helopeltis — weekly scouting; treat at threshold (1-2 bugs per 10 shoots)",
            "Monitor red spider mite on lower canopy even during wet season (can build in dry spells)",
            "Weed management: 2-3 inter-row slashes; no cultivations to avoid root damage in peak season",
            "Maintain mulch cover under canopy to buffer soil moisture fluctuations between rains",
            "Apply foliar sulphur as ammonium sulphate or wettable sulphur for amino acid and quality",
        ],
        risks=[
            "Blister blight epidemic during prolonged cool, misty, wet weather at altitude",
            "Helopeltis tip die-back during warm-humid flush periods",
            "Waterlogging in heavy rainfall events — monitor drainage outlets",
            "Nutrient leaching in intensive rainfall — split N applications to reduce losses",
            "Overplucking (too frequent rounds) weakening bush reserves",
        ],
        scientific_notes=(
            "The main flush period (November-March) coincides with Zimbabwe's rainy season and warmest "
            "temperatures, driving maximum photosynthetic activity and hence maximum flush production. "
            "Tea yield is measured as kilograms of made tea per hectare per year; premium Eastern Highlands "
            "estates in Zimbabwe achieve 2000-3000 kg/ha/year. Shoot production follows a 'flush and dormancy' "
            "cycle related to growing degree accumulation. Nitrogen is the primary determinant of yield, "
            "but excess N at the expense of K and S quality parameters reduces the theaflavin:thearubigin ratio "
            "in black tea, lowering cup quality. Sulphur, present in the amino acids cysteine and methionine "
            "and in tea catechin precursors, is critical for aroma development. Potassium is the largest "
            "macronutrient requirement of tea by mass — it regulates stomatal opening, water use efficiency, "
            "and sugar loading into the phloem. Plucking interval (the number of days between rounds) "
            "directly determines the plucked shoot size and quality: shorter intervals (7 days) give finer, "
            "higher-quality leaf; longer intervals (14+ days) give higher weight but lower quality."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Mature Tea — Maintenance Flush (Dry Season)",
        stage_code="GS5",
        day_range=(300, 365),
        water_kc=0.55,
        water_mm_per_week=16,
        critical_nutrients=["K", "Mg"],
        key_activities=[
            "Plucking at extended intervals (14-21 days) as flush growth slows in dry season",
            "Apply potassium top-dress (KCl 40-60 kg K2O/ha) to replenish reserves before onset of rains",
            "Irrigation if available — even 15-20 mm/week maintains productivity in dry months (June-October)",
            "Skiffing of plucking table to even up any uneven growth before pruning (if prune year)",
            "Red spider mite intensive monitoring — July-September is peak risk period",
            "Scale insect inspection and control if populations exceed threshold",
            "Prepare pruning teams and equipment if pruning planned for July-August",
            "Apply foliar Mg and Zn if tissue analysis indicates deficiency",
        ],
        risks=[
            "Red spider mite explosion during dry season — can cause severe bronzing and defoliation",
            "Bush stress from drought reducing immune competence — secondary disease entry",
            "Scale insect population build-up under dry, hot conditions",
            "Overextended plucking intervals reducing plucking table cleanliness",
        ],
        scientific_notes=(
            "Camellia sinensis growth is temperature and water-sensitive — at temperatures below 13 degC or "
            "under significant water deficit, flush growth ceases. In Zimbabwe's Eastern Highlands the dry "
            "season (May-October) brings cooler nights (down to 8-10 degC at altitude) and strongly "
            "reduced rainfall, causing a natural growth depression. Irrigated estates (Honde Valley "
            "irrigation scheme) maintain productivity through the dry season by applying 15-20 mm/week. "
            "The maintenance flush period is important for replenishing the bush's carbohydrate and mineral "
            "reserves in preparation for the explosive November-March main flush. Potassium reserves in "
            "stem tissue act as a buffer for the first flush production when soil K availability may be "
            "temporarily low before the season's fertiliser applications. Magnesium deficiency symptoms "
            "(interveinal chlorosis on older leaves) are most visible in the dry season as nutrient "
            "mobility is reduced and older leaves become nutrient sources for the flush."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Mature Tea — Tipping (Pre-Season Plucking Table Reset)",
        stage_code="GS6",
        day_range=(300, 330),
        water_kc=0.60,
        water_mm_per_week=18,
        critical_nutrients=["N", "Zn"],
        key_activities=[
            "Tipping: light mechanical or hand cutting of plucking table to 2-3 cm below existing level",
            "Apply pre-season nitrogen (CAN 50-70 kg N/ha) 2-3 weeks before tipping to support flush emergence",
            "Apply foliar zinc (ZnSO4 3 g/L) on emerging flush after tipping",
            "Begin pre-season blister blight spray programme as first post-tipping flush emerges",
            "Inspect and service mechanical harvesting equipment before peak season",
            "Calibrate fertiliser spreaders and spray equipment for the new season",
        ],
        risks=[
            "Blister blight on first post-tipping flush",
            "Helopeltis activity increasing as new season flush emerges",
        ],
        scientific_notes=(
            "Tipping is a light form of pruning (2-3 cm cut) applied annually or bi-annually to keep the "
            "plucking table at the correct height and stimulate branching into productive new shoots. "
            "Unlike the full pruning cycle (every 3-4 years), tipping maintains the plucking table "
            "framework. Pre-season tipping is typically performed in October-November, just before the "
            "onset of the main rains, so the vigorous post-tipping flush coincides with optimal growing "
            "conditions. Zinc is applied at this stage because rapidly dividing meristematic cells in "
            "the newly forming shoots require zinc as a cofactor for RNA polymerase and zinc finger "
            "transcription factors that regulate cell differentiation."
        ),
    ),
]


TEA_FERTILIZER = FertilizerSchedule(
    basal={
        "product": "Rock Phosphate (35% P2O5) + Lime (if pH < 4.0)",
        "rate_kg_ha": "Rock Phosphate: 500 kg/ha; Lime: 500-1000 kg/ha only if pH < 4.0",
        "p_kg_ha": 87,
        "timing": "At field establishment; incorporate into planting row to 30 cm depth",
        "notes": "Tea thrives in acid soils (pH 4.5-5.5) — do NOT raise pH above 5.5. Rock phosphate "
                 "is the preferred P source in acid soils where SSP can cause localised P-Al reactions. "
                 "Liming is only required if pH falls below 4.0 where Al toxicity becomes a problem. "
                 "Apply dolomitic lime (for Mg supply) rather than calcitic lime where Mg is deficient. "
                 "For established tea: broadcast 200-300 kg/ha rock phosphate under canopy annually "
                 "or every 2 years as maintenance P application.",
    },
    top_dress_1={
        "product": "CAN (Calcium Ammonium Nitrate 28% N) + Ammonium Sulphate 21% N",
        "rate_kg_ha": "CAN: 300-400 kg/ha; OR Ammonium Sulphate: 350-450 kg/ha",
        "n_kg_ha": "84-126 kg N/ha per application; total annual N: 150-250 kg N/ha split into 3-4 applications",
        "timing": "First application: at flush emergence / post-tipping (October-November). "
                  "Second application: during peak flush (January). Third application: March-April.",
        "notes": "Tea is one of the heaviest N feeders of any perennial crop — 150-250 kg N/ha/year "
                 "is the standard for high-yielding Zimbabwe estates. Ammonium sulphate is preferred "
                 "on very acid soils as it maintains soil acidity (tea prefers acid) and supplies sulphur "
                 "for amino acid synthesis and flavour development. Do NOT use urea alone — it can cause "
                 "volatilisation losses and lacks the acidifying effect beneficial to tea. CAN is "
                 "acceptable on slightly less acid soils. Split applications into 3-4 doses to match "
                 "flush demand and reduce leaching losses in high-rainfall Eastern Highlands. "
                 "Post-prune year: apply 60% of standard rate until canopy re-establishes.",
    },
    top_dress_2={
        "product": "Muriate of Potash (KCl 60% K2O) or Sulphate of Potash (SOP 50% K2O)",
        "rate_kg_ha": "KCl: 250-350 kg/ha; OR SOP: 300-400 kg/ha",
        "k_kg_ha": "150-210 kg K2O/ha/year",
        "timing": "Apply in two splits: mid-season (January-February) and end-of-season (April-May)",
        "notes": "Potassium is the largest macronutrient requirement by mass for tea — essential for "
                 "stomatal regulation, osmoregulation, sugar loading, and maintenance of tea quality "
                 "parameters (theaflavin:thearubigin ratio). Potassium deficiency manifests as "
                 "marginal leaf scorch on older leaves. SOP is preferred in very high-yield, high-quality "
                 "blocks as it avoids potential chloride toxicity concerns (though tea is relatively "
                 "tolerant of Cl). KCl is used in most commercial Zimbabwe tea due to cost advantage. "
                 "NPK ratio for mature tea: approximately 2:0.5:1 (N:P:K) by elemental weight.",
    },
    foliar={
        "product": "Magnesium sulphate (MgSO4·7H2O) + Zinc sulphate (ZnSO4·7H2O) + "
                   "Manganese sulphate (MnSO4)",
        "rate": "MgSO4: 5-7 g/L; ZnSO4: 3-4 g/L; MnSO4: 2-3 g/L; spray to run-off",
        "timing": "3-4 applications per year: at post-prune flush emergence, mid-season, "
                  "post-tipping, and when deficiency symptoms observed",
        "notes": "Magnesium is frequently deficient in Eastern Highlands tea soils — intensive "
                 "nitrogen applications acidify soil and leach Mg from the cation exchange complex. "
                 "Interveinal chlorosis on mature leaves is the diagnostic symptom. Zinc deficiency "
                 "manifests as small, mottled leaves and reduced shoot length. Manganese deficiency "
                 "(grey speck) can occur if pH is raised above 5.5 by over-liming. Do not apply "
                 "foliar sprays in direct sunlight or when leaf wetness is high (risk of scorch). "
                 "Foliar application provides a rapid correction supplement to — not a replacement "
                 "for — soil applications. Copper from fungicide sprays (blister blight programme) "
                 "contributes incidentally to Cu nutrition.",
    },
    liming={
        "target_ph": "4.5-5.5 — tea is ACID LOVING; DO NOT EXCEED pH 5.5",
        "product": "Dolomitic lime (for both Ca and Mg supply)",
        "rate": "0.5-1.5 t/ha only when pH falls below 4.0; every 3-5 years only",
        "timing": "Apply during dry season; incorporate lightly under mulch; allow 3 months before "
                  "next soil test to assess pH response",
        "notes": "CRITICAL: Tea is unique among food crops in requiring a strongly acid soil (pH 4.5-5.5). "
                 "At pH > 5.5, manganese and iron become unavailable, iron chlorosis occurs, and the "
                 "characteristic acid-loving root mycorrhizal associations (ericoid mycorrhizas) are disrupted. "
                 "At pH < 4.0, aluminium (Al3+) becomes acutely toxic. The target is 4.5-5.0 for most "
                 "established blocks. Lime is only applied in Zimbabwe tea to CORRECT excessive acidity "
                 "(pH < 4.0) — NEVER routinely. Annual soil testing is essential to monitor pH drift. "
                 "Nitrogen fertilisers (especially ammonium sulphate) acidify soil over time — "
                 "monitor annually and correct at pH < 4.0.",
    },
    notes=(
        "Annual nutrient targets for mature bearing tea (Zimbabwe Eastern Highlands standard, "
        "high-yield blocks producing > 2000 kg made tea/ha/year): "
        "N: 180-250 kg/ha; P2O5: 40-60 kg/ha; K2O: 150-200 kg/ha; MgO: 20-30 kg/ha; S: 30-50 kg/ha. "
        "The NPK ratio is approximately 2:0.5:1.2 (elemental). Organic matter management is critical: "
        "10-20 t/ha of pruning waste and shade-tree litter returned under canopy annually builds "
        "soil organic matter and maintains the acid soil biology. Tanganda Tea Company in the Honde "
        "Valley uses integrated organic + mineral programmes. Sulphur is a key quality nutrient — "
        "sulphur-containing amino acids (cysteine, methionine) are precursors to the volatile "
        "aroma compounds and theaflavins that define Zimbabwe black tea quality. "
        "Chloride from KCl fertilisers increases drought tolerance by regulating osmotic potential "
        "but should not exceed 100 kg Cl/ha/year in sensitive high-quality blocks."
    ),
)


TEA_PLANTING_WINDOWS: List[PlantingWindow] = [
    PlantingWindow(
        region="NR I — Eastern Highlands: Honde Valley (Mutasa District, 600-1200m)",
        optimal_start="November 15",
        optimal_end="January 15",
        acceptable_start="November 1",
        acceptable_end="February 15",
        notes=(
            "The Honde Valley is the heartland of Zimbabwe's commercial tea industry and home to "
            "Tanganda Tea Company's largest estates. Annual rainfall 1400-2000 mm, distributed "
            "November-April with reliable onset. Temperatures 18-28 degC year-round. Deep, well-drained "
            "red-yellow fersiallitic soils derived from granite and greenschist, naturally acid (pH 4.5-5.5). "
            "Plant nursery-hardened cuttings (12-15 months old) at onset of rains. Establish shade trees "
            "(Grevillea robusta, Albizia chinensis) 1-2 years prior to tea planting. First economic harvest "
            "3-4 years after planting. Irrigation from Honde River allows year-round production on larger estates."
        ),
    ),
    PlantingWindow(
        region="NR I — Eastern Highlands: Chipinge District (600-1200m)",
        optimal_start="November 15",
        optimal_end="January 15",
        acceptable_start="November 1",
        acceptable_end="February 28",
        notes=(
            "Chipinge (Southern Eastern Highlands) has similar conditions to Honde Valley with slightly "
            "higher temperatures at lower altitudes. Annual rainfall 1200-1800 mm. Altitude range "
            "600-1200m; higher sites are suitable for premium tea. Tanganda Tea Company and smaller "
            "outgrower operations in this district. Soils are deep red-brown fersiallitic loams on "
            "the escarpment, transitioning to lighter sandy soils at lower elevations. Shade management "
            "more critical at lower altitudes where temperatures can exceed 30 degC. Good potential for "
            "outgrower tea development supported by Tanganda outgrower programme."
        ),
    ),
    PlantingWindow(
        region="NR I — Eastern Highlands: Vumba / Burma Valley (1000-1800m)",
        optimal_start="November 1",
        optimal_end="December 31",
        acceptable_start="October 15",
        acceptable_end="January 31",
        notes=(
            "Higher altitude sections (1000-1800m) of the Eastern Highlands including the Vumba "
            "escarpment and Burma Valley. Rainfall 1500-2200 mm annually with reliable early onset "
            "(October-November). Cooler temperatures (15-25 degC optimal) produce slower-growing but "
            "higher-quality leaf with elevated polyphenol and theaflavin content. Blister blight "
            "pressure is highest in these misty, cool blocks — fungicide programmes critical. "
            "Frost possible above 1500m in June-July: do not plant immediately before frost season. "
            "Premium specialty and orthodox-grade teas can be produced from these high sites. "
            "TRFCA clones PC 108 and SFS 150 perform well across this altitude range."
        ),
    ),
]


PROFILE = CropProfile(
    crop_name="Tea",
    scientific_name="Camellia sinensis",
    family="Theaceae",

    optimal_ph=(4.5, 5.5),
    critical_ph_low=4.0,
    optimal_soil_types=[
        "deep, well-drained red-yellow fersiallitic clay loam (Eastern Highlands primary soil type)",
        "acid, well-structured loamy soils derived from granite and greenschist parent material",
        "deep, friable loam with good organic matter content (> 3% OM)",
        "acid sandy loam soils on escarpment slopes with good internal drainage",
    ],
    avoid_soil_types=[
        "waterlogged or poorly drained soils — Armillaria and Phytophthora root rot risk",
        "heavy vertisol (black cotton) — shrink-swell dynamics damage roots",
        "shallow lithosol over granite — insufficient rooting depth",
        "calcareous or alkaline soils (pH > 6.0) — iron chlorosis and micronutrient lock-up",
        "duplex soils with impermeable clay pan at 30-50 cm depth",
    ],

    optimal_temp=(18.0, 28.0),
    critical_temp_low=2.0,
    critical_temp_high=35.0,
    base_temp_gdd=12.0,
    total_water_mm=1500.0,

    growth_stages=TEA_GROWTH_STAGES,
    fertilizer_schedule=TEA_FERTILIZER,
    diseases=TEA_DISEASES,
    pests=TEA_PESTS,
    planting_windows=TEA_PLANTING_WINDOWS,

    harvest_moisture="Green leaf: 75-80% moisture at plucking; processed black tea: 3-5% moisture for "
                     "storage; Orthodox manufacture: withering to 65-68% moisture content",
    storage_conditions=(
        "Made tea (black CTC or orthodox): moisture < 5%, stored in foil-lined multilayer paper sacks "
        "or chest/plywood tea chests lined with foil and tissue; cool (< 25 degC), dry, dark warehouse; "
        "humidity < 60% RH; off floor on pallets; strong-smelling chemicals must not be stored nearby "
        "as tea absorbs odours readily. Green leaf: transport to factory within 4 hours of plucking; "
        "spread in withering troughs at 1.5-2.0 kg/m2 for CTC; do not pile or heat."
    ),
    post_harvest_notes=(
        "Zimbabwe tea is primarily processed as black CTC (Cut-Tear-Curl) tea by Tanganda Tea Company "
        "and smaller processors. Orthodox black tea and green tea are produced in smaller volumes for "
        "specialty export. CTC manufacture process: (1) Withering: spread green leaf in troughs with "
        "air-flow for 12-16 hours at 25-30 degC, reducing moisture from 80% to 65-68%; "
        "(2) CTC cutting: pass withered leaf through CTC rotovane machines 2-3 times to break cell "
        "structure and release polyphenol oxidase; (3) Fermentation (oxidation): CTC dhool spread "
        "2-5 cm deep at 22-26 degC, 95% RH for 45-90 minutes until copper-brown colour develops — "
        "theaflavins and thearubigins form from polyphenol oxidase catalysis; (4) Drying (firing): "
        "pass through fluid-bed drier at 100-120 degC inlet, 3-5 minutes, reducing moisture to 3-5%; "
        "(5) Sorting: sieve into grades — BP (Broken Pekoe), PF (Pekoe Fannings), D (Dust); "
        "(6) Grading and packaging: bulk pack for auction or direct contract export. "
        "Zimbabwe tea is traded through Mombasa Tea Auction and direct sales to blenders in UK, "
        "Pakistan, Germany, and regional African markets. Tanganda is the dominant brand in the "
        "domestic Zimbabwean market. TRFCA (Tea Research Foundation of Central Africa) provides "
        "agronomic and manufacturing research support to the industry. "
        "Key quality parameters: theaflavin content (target > 1.5% on dry weight) determines brightness "
        "and briskness of cup; Thearubigin:Theaflavin ratio (target 9-12:1) determines colour depth; "
        "Total Colour (TC) and Brightness (B) measured spectrophotometrically at the factory."
    ),

    natural_region_suitability={
        "I": (
            "Excellent — the ONLY suitable natural region for commercial tea in Zimbabwe. "
            "Eastern Highlands (Honde Valley, Chipinge, Vumba) provide ideal temperature, "
            "rainfall (1200-2000 mm), humidity, and acid fersiallitic soils. "
            "Tanganda Tea Company, TRFCA, and smallholder outgrowers concentrated here. "
            "PC 108 and SFS 150 clones developed specifically for Eastern Highlands conditions."
        ),
        "IIa": "Unsuitable — insufficient annual rainfall (750-1000 mm vs 1200 mm minimum requirement); "
               "temperatures too variable; soils lack natural acidity required for tea; "
               "frost risk in some elevated areas",
        "IIb": "Unsuitable — too warm and dry for quality tea production; "
               "temperature extremes during summer exceed optimal range",
        "III": "Unsuitable — severely insufficient rainfall and high temperatures; "
               "soils typically non-acidic",
        "IV": "Unsuitable — semi-arid conditions completely incompatible with tea",
        "V": "Unsuitable — arid; far too hot and dry",
    },
)

ALIASES: list = ["tii", "chai"]
