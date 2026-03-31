"""Sweet Potato (Ipomoea batatas) — critical food security and nutrition crop for Zimbabwe NR III-V."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List


SWEET_POTATO_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Sweet Potato Virus Disease (SPVD)",
        pathogen="Sweet Potato Feathery Mottle Virus (SPFMV) + Sweet Potato Chlorotic Stunt Virus (SPCSV)",
        pathogen_type="viral",
        symptoms=[
            "Severe stunting — plants remain dwarf compared to healthy neighbours",
            "Leaf chlorosis: yellow or pale green mottling and mosaic patterns",
            "Leaf distortion, cupping, and feathery appearance on young leaves",
            "Purple or necrotic streaking along leaf veins in some varieties",
            "Drastically reduced vine length and internode shortening",
            "Severely misshapen and undersized storage roots — up to 90% yield loss in susceptible varieties",
            "Symptoms worsen as the season progresses; early infection is most damaging",
        ],
        identification_markers=[
            "Stunted plants with mottle/mosaic contrast sharply with adjacent healthy plants",
            "Feathery leaf margins (characteristic of SPFMV component)",
            "Whitefly (Bemisia tabaci) populations usually evident on affected plants",
            "Symptoms most severe when both SPFMV and SPCSV are present together (synergism)",
            "SPVD is NOT caused by either virus alone — synergistic interaction multiplies severity 10-100x",
            "Distinguish from nutrient deficiency by: presence of whitefly vectors, mosaic pattern, stunting",
            "Use ELISA or lateral flow assay kits (available from CIMMYT/CIP offices) for confirmation",
        ],
        favourable_conditions={
            "humidity_min": 60,
            "temp_min_c": 20,
            "temp_max_c": 35,
            "note": "Warm, dry conditions favour Bemisia tabaci whitefly vectors. "
                    "Disease spreads rapidly when whitefly populations are high. "
                    "Infected planting material is the primary long-distance spread route. "
                    "Volunteer sweet potato plants and wild Ipomoea spp. serve as virus reservoirs. "
                    "Drought stress compromises plant immunity and increases susceptibility.",
        },
        susceptible_stages=["Establishment", "Vine Development", "Root Bulking"],
        resistant_varieties=["Irene (OFSP)", "Chingovha (OFSP)", "Brondal", "Kemb 10"],
        susceptible_varieties=["Many local white- and cream-fleshed landraces", "Unselected farmer-saved material"],
        chemical_control=[
            {"name": "Imidacloprid 70 WS (cutting dip)", "rate": "1-2 g/L water — dip cuttings 30 min before planting",
             "phi_days": "N/A", "notes": "Systemic neonicotinoid; protects establishing vines from early whitefly feeding. "
                                         "Provides 3-4 weeks systemic protection"},
            {"name": "Acetamiprid 20 SP", "rate": "150-200 g/ha",
             "phi_days": "21", "notes": "Foliar spray targeting whitefly adults and nymphs; rotate chemistry to avoid resistance"},
            {"name": "Spiromesifen 240 SC", "rate": "0.75 L/ha",
             "phi_days": "7", "notes": "Targets whitefly nymphs and eggs; good resistance management partner"},
        ],
        biological_control=[
            "Encarsia formosa (parasitic wasp) — a naturally occurring whitefly parasitoid, encourage by reducing broad-spectrum insecticides",
            "Beauveria bassiana 1.15% WP (e.g. BotaniGard) — spray on whitefly colonies",
            "Reflective mulch (aluminium foil or silver PE mulch) confuses and repels whitefly, reducing virus spread by up to 60%",
            "Intercropping with maize or sorghum creates a barrier reducing windborne whitefly dispersal",
        ],
        cultural_control=[
            "ONLY use certified virus-tested planting material from reputable sources (e.g. CIP, AGRITEX vine multiplication sites)",
            "Rogue and destroy infected plants immediately — do NOT compost; burn or bury deeply",
            "Plant resistant/tolerant OFSP varieties (Irene, Chingovha) — primary defence against SPVD",
            "Establish vine multiplication plots isolated (>100 m) from commercial fields",
            "Destroy volunteer sweet potato and wild Ipomoea spp. around field boundaries",
            "Synchronise community planting to break whitefly cycle (fallow period)",
            "Avoid planting during peak whitefly seasons (dry late-season conditions)",
            "Inspect incoming planting material and quarantine new sources for 2 weeks",
        ],
        economic_threshold="Any confirmed SPVD plants warrant roguing; >5% incidence indicates poor planting material — do not save vines for replanting",
        severity_scale={
            "mild": "< 5% plants infected, usually early season; rogue and replant with clean material",
            "moderate": "5-20% plants affected with stunting; significant yield loss expected; rogue and improve vector control",
            "severe": "> 20% plants showing SPVD symptoms — 50-90% yield loss; abandon for replanting with certified material next season",
        },
    ),
    DiseaseProfile(
        name="Alternaria Blight",
        pathogen="Alternaria batatas",
        pathogen_type="fungal",
        symptoms=[
            "Circular to irregular brown spots on leaves, 2-10 mm diameter",
            "Target-board appearance: concentric rings of brown and tan within spots",
            "Yellow halo surrounding lesions on susceptible varieties",
            "Lesions coalesce causing large necrotic patches and premature defoliation",
            "Stem lesions: dark brown elliptical cankers that girdle stems causing die-back",
            "Severe defoliation reduces photosynthesis and stunts storage root development",
        ],
        identification_markers=[
            "Concentric ring pattern within brown leaf spots (targetboard symptom)",
            "Dark olivaceous sporulation (Alternaria chains) visible on spot surface with hand lens",
            "Spots begin on older lower leaves and progress upward",
            "Distinguished from Cercospora leaf spot by larger lesion size and concentric rings",
            "Stem girdling with dark sunken cankers distinguishes from vine borer injury",
        ],
        favourable_conditions={
            "humidity_min": 80,
            "temp_min_c": 22,
            "temp_max_c": 30,
            "leaf_wetness_hours": 6,
            "note": "Warm, wet conditions with frequent rain or heavy dew. "
                    "Stressful conditions (drought, poor nutrition) predispose plants. "
                    "Survives on infected crop debris and weedy Ipomoea hosts. "
                    "Common in NR I-II and in irrigation schemes during summer.",
        },
        susceptible_stages=["Vine Development", "Root Bulking", "Maturation"],
        resistant_varieties=["Irene", "Jewel", "Hernandez"],
        susceptible_varieties=["Local white-fleshed landraces", "Beauregard under high disease pressure"],
        chemical_control=[
            {"name": "Mancozeb 80 WP", "rate": "2.0-2.5 kg/ha",
             "phi_days": "14", "notes": "Protectant fungicide; apply at 10-14 day intervals in wet weather"},
            {"name": "Chlorothalonil 720 SC", "rate": "1.5-2.0 L/ha",
             "phi_days": "14", "notes": "Broad-spectrum protectant; good in humid highland conditions"},
            {"name": "Azoxystrobin 250 SC", "rate": "0.6-0.8 L/ha",
             "phi_days": "14", "notes": "Systemic strobilurin; use in rotation to manage resistance risk"},
        ],
        biological_control=[
            "Trichoderma harzianum soil treatment reduces soilborne inoculum",
            "Remove and destroy infected crop debris after harvest",
            "Balanced K nutrition improves canopy resistance to fungal infection",
        ],
        cultural_control=[
            "Rotate with non-Ipomoea crops for 2+ seasons to reduce soilborne inoculum",
            "Use disease-free, healthy planting material",
            "Improve drainage and avoid overhead irrigation in high-humidity conditions",
            "Remove infected lower leaves and debris from field",
            "Apply potassium fertiliser adequately — K deficiency increases blight severity",
            "Avoid mechanical injury during crop management operations",
        ],
        economic_threshold="Lesions on 15% or more of leaf area warrants fungicide application",
        severity_scale={
            "mild": "Scattered spots on older leaves only; little impact on yield",
            "moderate": "15-40% leaf area blighted, reaching middle canopy; 10-20% yield reduction",
            "severe": "> 40% defoliation with stem girdling — 30-50% yield reduction; urgent fungicide and cultural action needed",
        },
    ),
    DiseaseProfile(
        name="Black Rot",
        pathogen="Ceratocystis fimbriata",
        pathogen_type="fungal",
        symptoms=[
            "Dark brown to black, circular to irregular lesions on storage roots",
            "Lesions are firm (not soft/watery) and penetrate deep into root tissue",
            "Bitter taste in affected root tissue — renders roots inedible even if partially affected",
            "Greenish-black discolouration of root flesh extending from the lesion",
            "Seedling damping-off and stem rot at or below soil level",
            "Dark cankers on stems at soil line, causing wilt of above-ground vines",
            "Infected roots in storage turn entirely black and mummify",
        ],
        identification_markers=[
            "Black, firm, circular lesions (NOT soft and mushy like Rhizopus soft rot)",
            "Bitter flavour is diagnostic — even a small lesion makes the whole root inedible",
            "Green-black zone extends 2-3 cm into healthy-looking tissue around lesion",
            "Flask-shaped perithecia (fungal fruiting bodies) visible with hand lens on lesion edges",
            "Stem cankers are dark and sunken at soil line, distinguished from Fusarium by black (not pink) colouration",
        ],
        favourable_conditions={
            "humidity_min": 75,
            "temp_min_c": 15,
            "temp_max_c": 30,
            "note": "Fungus survives indefinitely in soil and on infected debris. "
                    "Spread by infected planting material, contaminated soil on tools and implements. "
                    "Enters through wounds — harvest injuries are major infection courts. "
                    "Cool, moist storage conditions favour rot development post-harvest. "
                    "Common along irrigation canals and in poorly drained soils.",
        },
        susceptible_stages=["Establishment", "Root Bulking", "Maturation", "Storage"],
        resistant_varieties=["Jewel", "Rojo Blanco"],
        susceptible_varieties=["Beauregard", "Most local landraces", "Resisto under high inoculum"],
        chemical_control=[
            {"name": "Thiabendazole 450 SC (cutting dip)", "rate": "1.0 g a.i./L water — dip cuttings 10 min",
             "phi_days": "N/A", "notes": "Pre-plant cutting dip; systemic fungicide penetrates vine tissue to kill latent infection"},
            {"name": "Captan 50 WP (root dip at harvest)", "rate": "2.0 g/L water — dip roots briefly",
             "phi_days": "0", "notes": "Post-harvest root dip before curing; reduces storage rot incidence"},
        ],
        biological_control=[
            "Trichoderma viride antagonises Ceratocystis in soil when applied as root zone drench",
            "Bacillus subtilis (e.g. Serenade) applied to soil and as cutting dip",
            "Avoid insect vectors (sweet potato weevil creates wounds that are primary infection courts)",
        ],
        cultural_control=[
            "Use only healthy, certified vine cuttings from disease-free source fields",
            "Never plant on fields with known black rot history without 3-year rotation",
            "Cure harvested roots: hold at 29-33°C, 90-95% RH for 4-7 days to form wound periderm",
            "Handle roots gently at harvest to minimise wounds — black rot enters through injuries",
            "Remove infected roots from storage immediately to prevent spread",
            "Disinfect storage structures with lime-wash between seasons",
            "Control sweet potato weevil — weevil wounds are primary black rot entry points",
            "Plough deeply after harvest to bury infected debris",
        ],
        economic_threshold="Any confirmed black rot in field or storage requires action; post-harvest, >2% root infection warrants improved storage hygiene",
        severity_scale={
            "mild": "< 3% roots with lesions; small surface spots; rogue affected and improve storage",
            "moderate": "3-15% roots affected; significant storage loss; implement curing and fungicide dip",
            "severe": "> 15% roots with black rot — major economic loss; review entire production chain from planting material to storage",
        },
    ),
]


SWEET_POTATO_PESTS: List[PestProfile] = [
    PestProfile(
        name="Sweet Potato Weevil",
        scientific_name="Cylas puncticollis",
        pest_type="insect",
        identification=[
            "Adult: shiny, elongated beetle 5-8 mm long; characteristic narrow 'waist' between thorax and abdomen",
            "Head, thorax and legs are reddish-brown to orange; abdomen is dark blue-black with metallic sheen",
            "Antennae are long and elbowed — typical of curculionid weevils",
            "Eggs: white, oval, 0.7 mm long, laid singly in cavities chewed into roots or stems near soil",
            "Larvae: creamy-white, legless, curved grubs 5-8 mm, found inside tunnels in roots and stems",
            "Pupae: white, inside pupal chambers within roots",
        ],
        damage_symptoms=[
            "Irregular tunnels and galleries inside storage roots — roots appear intact externally",
            "Dark brown-black staining and resinous odour from root tissue around tunnels (terpenoid defence response)",
            "Bitter, acrid taste of affected roots renders them inedible even with minor infestation",
            "Stem damage at soil line: tunnel entry holes with frass at surface",
            "Above-ground vines wilt and collapse when larval tunnelling girdles stem base",
            "Emergence holes (2-3 mm) on root surface where adults exit",
            "Severe infestation: entire root converted to frass-filled tunnels",
        ],
        life_cycle_notes=(
            "Cylas puncticollis is the most damaging sweet potato pest in sub-Saharan Africa. "
            "Adults are long-lived (up to 6 months) and can fly short distances. "
            "Females lay 100-200 eggs individually in roots or stems. "
            "Egg incubation 6-9 days. Larval period 3-4 weeks. Pupal period 7-10 days. "
            "Total egg-to-adult takes 5-6 weeks under warm conditions. "
            "Weevils breed continuously throughout the year; multiple overlapping generations. "
            "Adults are nocturnal; hide in soil cracks and under debris during day. "
            "Soil cracking during dry periods exposes roots, dramatically increasing infestation. "
            "Pheromone traps using cis-3,3-dimethylcyclohexaneethanol are available for monitoring."
        ),
        favourable_conditions={
            "temp_min_c": 20,
            "temp_max_c": 35,
            "note": "Hot, dry conditions create soil cracks that expose roots to adult weevils. "
                    "Drought stress increases damage severity by reducing vine coverage. "
                    "Worst in NR IV-V where dry seasons are prolonged. "
                    "Soils with high clay content crack more severely, increasing exposure. "
                    "Continuous sweet potato production without rotation maintains high populations.",
        },
        susceptible_stages=["Root Bulking", "Maturation"],
        economic_threshold="5% of roots showing weevil damage on inspection; or 1 adult per pheromone trap per week",
        chemical_control=[
            {"name": "Chlorpyrifos 480 EC (soil drench)", "rate": "1.5 L/ha in 400-600 L water",
             "phi_days": "28", "notes": "Apply to soil around base of plants when roots begin bulking; water in well"},
            {"name": "Thiamethoxam 25 WG", "rate": "200 g/ha",
             "phi_days": "14", "notes": "Systemic; apply as soil drench; provides systemic activity against adults and emerging larvae"},
            {"name": "Lambda-cyhalothrin 50 EC", "rate": "300 mL/ha",
             "phi_days": "14", "notes": "Foliar/soil surface spray targeting adults; apply in the evening when weevils are active"},
        ],
        biological_control=[
            "Beauveria bassiana — entomopathogenic fungus; apply to soil as granules or drench (e.g. BioAct WG)",
            "Steinernema carpocapsae nematodes — apply as soil drench when roots begin forming; must keep soil moist",
            "Pheromone traps (cis-3,3-dimethylcyclohexaneethanol) for mass trapping — used in combination with other methods",
            "Encourage ground beetles (Carabidae) which are natural predators of weevil eggs",
        ],
        cultural_control=[
            "Hill or ridge soil over roots to prevent cracking and exposure — critical management step",
            "Irrigate during dry spells to prevent soil cracking and maintain vine cover",
            "Harvest promptly at maturity — do not leave roots in soil after they are ready",
            "Rotate sweet potato with non-host crops for at least 2 seasons to reduce soil populations",
            "Use clean, weevil-free planting material — inspect stem bases for entry holes before planting",
            "Destroy crop residue (roots and vines) thoroughly after harvest — do not leave old roots in soil",
            "Avoid moving infested soil on equipment between fields",
            "Plant at start of rains to maximise vine coverage before dry season",
        ],
        scouting_protocol=(
            "Deploy pheromone traps at 5-10 per hectare from 6 weeks after planting. "
            "Check traps weekly; record adult numbers. Threshold: 1+ adult per trap per week. "
            "In-field: excavate 10-20 roots at random across the field at 60 and 90 days. "
            "Cut each root longitudinally and inspect for tunnels, larvae, and dark staining. "
            "Record percentage of infested roots. Also check stem bases for adult weevils under debris. "
            "Scout at dawn or dusk when adults are active. "
            "If >5% of roots infested, implement chemical and cultural controls immediately."
        ),
    ),
    PestProfile(
        name="Whitefly (SPVD Vector)",
        scientific_name="Bemisia tabaci",
        pest_type="insect",
        identification=[
            "Adult: tiny white moth-like insect, 1-2 mm long; wings held flat over body (distinguishes from greenhouse whitefly)",
            "Covered in white waxy powder; adults fly up in clouds when plant is disturbed",
            "Eggs: pale yellow, oval, 0.2 mm, laid individually on underside of young leaves",
            "Nymphs: flat, oval, scale-like; pale yellow-green; 4 instars on leaf underside",
            "Pupal case (4th instar): flattened, oval, yellow-white with upright wax filaments",
        ],
        damage_symptoms=[
            "Transmission of Sweet Potato Virus Disease (SPVD) — primary and most damaging role",
            "Honeydew secretion covering leaves, leading to black sooty mould growth",
            "Yellow stippling and chlorosis of leaves from direct sap sucking",
            "Leaf curl and distortion on heavily infested young shoots",
            "Premature leaf drop and reduced vine vigour under heavy infestation",
            "Sooty mould interferes with photosynthesis",
        ],
        life_cycle_notes=(
            "Bemisia tabaci (Biotype B = 'silverleaf whitefly') is a primary vector of geminiviruses "
            "and is also an efficient vector of SPCSV component of SPVD. "
            "Female lays 100-300 eggs over her lifetime (3-4 weeks). "
            "Egg incubation 5-7 days. Nymphal development 12-20 days. "
            "Generation time 20-30 days at 25°C; up to 12 generations per year in warm climates. "
            "Adults acquire SPFMV in as little as 30 minutes of feeding; transmit in 30 minutes. "
            "SPCSV (the more damaging component) requires longer acquisition. "
            "Populations peak in dry, hot conditions (March-October in Zimbabwe lowveld). "
            "Sooty mould indicates past or ongoing infestation."
        ),
        favourable_conditions={
            "temp_min_c": 24,
            "temp_max_c": 38,
            "humidity_note": "Populations are highest during hot, dry periods",
            "note": "Hot, dry conditions dramatically accelerate whitefly development and reproduction. "
                    "Heavily fertilised plants with lush growth attract higher populations. "
                    "Worst in NR IV-V lowveld during warm dry spells. "
                    "Crop diversity in landscape reduces long-distance migration.",
        },
        susceptible_stages=["Establishment", "Vine Development"],
        economic_threshold="5+ adults per leaf on more than 20% of plants warrants control; any whiteflies in SPVD-hotspot areas warrant preventive action",
        chemical_control=[
            {"name": "Imidacloprid 200 SL", "rate": "0.5 mL/L water (foliar) or 1.0 L/ha soil drench",
             "phi_days": "21", "notes": "Highly effective; systemic; use as soil drench at establishment for preventive protection"},
            {"name": "Spirotetramat 150 OD", "rate": "0.75 L/ha",
             "phi_days": "14", "notes": "Excellent for nymph control; systemic; rotate with other modes of action"},
            {"name": "Pymetrozine 50 WG", "rate": "300 g/ha",
             "phi_days": "14", "notes": "Feeding disruptor; kills adults and nymphs without direct contact; good resistance management partner"},
        ],
        biological_control=[
            "Encarsia formosa — naturally occurring parasitoid wasp; conserve by avoiding broad-spectrum insecticides",
            "Eretmocerus mundus — another important parasitoid, common in Zimbabwe",
            "Reflective silver mulch: reduces whitefly landing by up to 70% and significantly slows SPVD spread",
            "Neem-based formulations (Azadirachtin 0.03%) repel adults and affect nymph development",
            "Soap sprays (potassium soap 2%) as a contact spray on nymph colonies",
        ],
        cultural_control=[
            "Plant SPVD-resistant varieties to reduce the impact even when whitefly vectors are present",
            "Reflective aluminium or silver mulch on beds confuses and repels whiteflies",
            "Maintain good vine cover — dense canopy is less accessible to whiteflies than sparse vines",
            "Remove and destroy infested plant material; never compost SPVD-affected material",
            "Establish border rows of maize or sorghum as a physical barrier to whitefly immigration",
            "Avoid planting near known virus reservoirs (wild Ipomoea spp., tobacco, tomato)",
            "Time planting to avoid peak dry-season whitefly pressure where possible",
        ],
        scouting_protocol=(
            "Begin scouting at 2 weeks after planting. Select 20 plants at random across the field. "
            "For each plant, examine the 3 youngest fully expanded leaves on the main vine. "
            "Turn leaf over and count adults and nymph colonies on leaf underside. "
            "Record average adults per leaf and percentage of leaves with nymph colonies. "
            "Also observe for SPVD symptoms (stunting, mosaic) — any SPVD plants indicate "
            "active virus transmission and require immediate roguing + vector control. "
            "Scout weekly during establishment phase; fortnightly thereafter."
        ),
    ),
    PestProfile(
        name="Aphids",
        scientific_name="Aphis gossypii / Myzus persicae",
        pest_type="insect",
        identification=[
            "Aphis gossypii: small (1-2 mm), greenish to dark olive or black soft-bodied insects in colonies",
            "Myzus persicae: pale green to yellow-green, slightly larger (1.5-2.5 mm)",
            "Both species: pear-shaped body, pair of cornicles (tail-pipe structures) on abdomen",
            "Winged and wingless forms occur; winged forms disperse to new fields",
            "Eggs are shiny black, laid on bark of wild hosts during cool season",
            "Dense colonies on growing tips and young leaves",
        ],
        damage_symptoms=[
            "Transmission of Sweet Potato Feathery Mottle Virus (SPFMV) — primary concern",
            "Curling and distortion of young leaves where colonies feed",
            "Chlorotic stippling and yellowing of leaves at feeding sites",
            "Honeydew deposits leading to sooty mould on leaves below colonies",
            "Stunted growing tips from heavy aphid feeding",
            "Reduced vine vigour and root development under severe sustained attack",
        ],
        life_cycle_notes=(
            "Both Aphis gossypii (cotton/melon aphid) and Myzus persicae (green peach aphid) "
            "vector SPFMV in a non-persistent manner — meaning acquisition and inoculation are "
            "rapid (seconds to minutes of probing). This makes non-persistent viruses very "
            "difficult to control with insecticides alone, as aphids inoculate while briefly "
            "probing even before insecticide takes effect. "
            "Aphids reproduce parthenogenetically in summer; a single female can produce 50-100 "
            "offspring per week. Populations can double in 3-5 days under warm conditions. "
            "Winged alates are produced when colonies become crowded or plant quality declines; "
            "these disperse and found new colonies on fresh plants. "
            "Natural enemies (ladybirds, lacewings, parasitic wasps) can suppress populations rapidly."
        ),
        favourable_conditions={
            "temp_min_c": 15,
            "temp_max_c": 30,
            "note": "Moderate temperatures favour rapid reproduction. "
                    "Dense, lush vegetation from excess nitrogen supports high populations. "
                    "Drought stress increases plant susceptibility. "
                    "Natural enemy populations are suppressed by broad-spectrum insecticide use.",
        },
        susceptible_stages=["Establishment", "Vine Development"],
        economic_threshold="Colonies on 20% or more of growing tips; or any aphid activity in fields at high SPVD risk",
        chemical_control=[
            {"name": "Pirimicarb 50 WG (aphid-selective)", "rate": "200-300 g/ha",
             "phi_days": "14", "notes": "Selective aphicide — spares beneficial insects; preferred option for IPM"},
            {"name": "Flonicamid 50 WG", "rate": "200 g/ha",
             "phi_days": "14", "notes": "Feeding disruptor; does not kill immediately but stops virus transmission quickly"},
            {"name": "Mineral oil (Sunspray Ultra-Fine 97% EC)", "rate": "5-10 L/ha in 400 L water",
             "phi_days": "0", "notes": "Mineral oil interferes with non-persistent virus transmission; use as preventive spray in high-risk fields"},
        ],
        biological_control=[
            "Coccinellidae (ladybirds) — major predators; a single adult consumes 50-100 aphids/day; conserve by avoiding pyrethroids",
            "Chrysoperla carnea (green lacewing) larvae are voracious aphid predators",
            "Aphidius spp. and Lysiphlebus spp. — parasitic wasps that mummify aphids",
            "Entomopathogenic fungi: Lecanicillium muscarium applied as spray in humid conditions",
            "Neem oil (1-2%) reduces aphid reproduction and partially repels alates",
        ],
        cultural_control=[
            "Avoid excess nitrogen fertilisation — lush growth attracts and supports aphid populations",
            "Intercrop with strongly-scented plants (onions, marigolds) to confuse aphid host-finding",
            "Yellow sticky traps at 10-15/ha monitor alate (winged) aphid arrivals",
            "Mineral oil spray disrupts non-persistent virus transmission more effectively than insecticides alone",
            "Maintain beneficial insect habitat (flower strips, minimal bare soil) to support natural enemies",
            "Remove and destroy heavily infested terminal shoots",
        ],
        scouting_protocol=(
            "Scout weekly from 2 weeks after planting through vine development. "
            "Examine growing tips and young leaves of 20 randomly selected plants. "
            "Count aphid colonies and estimate infestation density (none / light <5 / moderate 5-20 / heavy >20 aphids per leaf). "
            "Check for presence of winged aphids (alates) which indicate active dispersal. "
            "Record natural enemy presence: ladybird adults and larvae, parasitised (mummified) aphids. "
            "If >20% of plants have colonies AND natural enemies are scarce, consider targeted aphicide. "
            "In known SPVD-hotspot areas, use mineral oil preventively regardless of aphid counts."
        ),
    ),
]


SWEET_POTATO_GROWTH_STAGES: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Establishment",
        stage_code="GS1",
        day_range=(0, 30),
        water_kc=0.40,
        water_mm_per_week=18,
        critical_nutrients=["P", "K", "N"],
        key_activities=[
            "Plant 30-40 cm vine cuttings with 3-4 nodes; bury 2-3 nodes, leave 1-2 with leaves",
            "Plant on ridges or mounds 75-100 cm apart, 30-40 cm between plants in the row",
            "Apply basal Compound D at planting: 300 kg/ha banded beside the ridge",
            "Ensure soil moisture for cutting establishment — plant into moist ridges or irrigate immediately",
            "Scout for whitefly and begin SPVD monitoring from 2 weeks",
            "Control weeds by hand or shallow hoe — do not damage shallow roots",
            "Dip cuttings in imidacloprid solution to protect against early whitefly and weevil",
        ],
        risks=[
            "Cutting death from lack of moisture at planting",
            "Whitefly-transmitted SPVD infection in early, vulnerable phase",
            "Poor rooting on compacted or waterlogged soils",
            "Cutworm damage at base of cuttings",
            "Transplant shock in dry or hot conditions",
        ],
        scientific_notes=(
            "Sweet potato is propagated vegetatively from stem cuttings (typically 25-40 cm long). "
            "Rooting occurs from nodes; at least 2 nodes should be below soil. "
            "The cutting uses reserve carbohydrates and nutrients from vine tissue while adventitious "
            "roots establish — typically 7-14 days to visible rooting. "
            "Phosphorus is critical for rapid adventitious root development and early vine growth. "
            "Plants established from cuttings have no true primary root; the storage roots develop "
            "from adventitious roots that thicken into tuberous roots during the bulking phase. "
            "Soil temperature of 20-30°C is optimal; below 15°C severely retards establishment. "
            "Early SPVD infection (first 4 weeks) is most damaging as plants lack the vine mass "
            "to compensate — SPVD-infected plants may produce 80-90% fewer roots."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Vine Development",
        stage_code="GS2",
        day_range=(30, 60),
        water_kc=0.70,
        water_mm_per_week=30,
        critical_nutrients=["N", "K", "S"],
        key_activities=[
            "Apply top dress: AN at 100 kg/ha at 4-6 weeks when vines actively growing",
            "Weed control — complete by 6 weeks; sweet potato will suppress weeds once canopy closes",
            "Scout for weevil adults and whitefly; implement control if above threshold",
            "Check vine density — full canopy should develop; bare soil exposes roots to weevil",
            "Hill soil over emerging root initiations to prevent greening and weevil access",
            "Identify and rogue any SPVD-infected plants (stunted, mosaic) before 45 days",
        ],
        risks=[
            "SPVD infection spreading via whitefly — scout and rogue infected plants urgently",
            "Weevil colonisation of early-forming roots",
            "Drought stress reducing vine vigour and canopy development",
            "Nitrogen deficiency causing pale, slow-growing vines",
            "Excess nitrogen causing excessive vine growth at expense of root formation",
        ],
        scientific_notes=(
            "Vine development is characterised by rapid elongation of main vine and branching. "
            "A full canopy by 45-60 days is important for weed suppression and to shade the soil, "
            "preventing it from cracking (which would expose roots to weevils). "
            "Nitrogen application at this stage stimulates vine growth and leaf area development. "
            "However, excess nitrogen (>120 kg N/ha total) shifts assimilate partitioning away from "
            "storage roots toward above-ground biomass — a common cause of poor root yield. "
            "Potassium plays a key role in photoassimilate loading into phloem and translocation to roots. "
            "The transition from vine growth to root bulking is triggered by shorter photoperiods and "
            "changes in assimilate source-sink balance — critical environmental cue for root initiation. "
            "SPVD roguing must be completed before 45 days to prevent spread to clean plants."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Root Bulking",
        stage_code="GS3",
        day_range=(60, 120),
        water_kc=0.85,
        water_mm_per_week=35,
        critical_nutrients=["K", "P", "B"],
        key_activities=[
            "Maintain soil moisture — irrigation during dry periods prevents cracking and weevil entry",
            "Hill up ridges to cover exposed roots — critical against weevil and black rot",
            "Scout weekly for weevil damage: excavate sample roots and inspect for tunnels",
            "Monitor for Alternaria blight — apply fungicide if lesions reach 15% leaf area",
            "Avoid any further nitrogen application — promotes vines at expense of root fill",
            "Pheromone trap checks twice weekly in weevil-risk areas",
        ],
        risks=[
            "Sweet potato weevil damage — most economically damaging risk at this stage",
            "Soil cracking from drought exposing roots",
            "Alternaria blight defoliating plants and reducing photosynthetic area",
            "Black rot entering through weevil wounds",
            "Waterlogging causing root rots (Phytophthora, Pythium)",
        ],
        scientific_notes=(
            "Root bulking is the primary yield-determining phase in sweet potato. "
            "Starch synthesis and deposition in storage roots accelerates from 60 days, with "
            "maximum bulking rate typically between 70-100 days after planting. "
            "The storage root is an enlarged, starchy adventitious root — morphologically "
            "distinct from a tuber (which is a modified stem). "
            "Beta-carotene (vitamin A precursor) concentration in OFSP (orange-fleshed) varieties "
            "increases during root bulking and is highest at physiological maturity. "
            "Potassium is the most critical macronutrient during bulking — K deficiency directly "
            "reduces starch synthesis and root expansion. "
            "Boron deficiency causes 'internal cork' (necrotic internal tissue) which is common "
            "in boron-depleted sandy soils of NR III-V. "
            "Maintaining continuous soil moisture prevents cracking — each soil crack is a potential "
            "weevil access point. Furrow irrigation or drip is preferable to overhead."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Maturation",
        stage_code="GS4",
        day_range=(120, 150),
        water_kc=0.60,
        water_mm_per_week=20,
        critical_nutrients=[],
        key_activities=[
            "Reduce irrigation 2-3 weeks before harvest to improve root quality and skin-set",
            "Check root maturity: scratch skin with thumbnail — mature roots resist peeling; immature skin peels easily",
            "Plan harvest logistics — sweet potato must be harvested carefully to avoid wound damage",
            "Prepare curing facility: warm, humid room (29-33°C, 85-95% RH) for 4-7 days post-harvest",
            "Harvest when 70-80% of roots have reached commercial size (typically 150-400 g for market)",
            "Grade at harvest: separate Grade 1 (market), Grade 2 (local consumption), damaged (animal feed)",
        ],
        risks=[
            "Delayed harvest allowing weevil populations to increase and damage more roots",
            "Skin cracking if soil becomes too dry before harvest",
            "Black rot infection through harvest wounds if curing is skipped",
            "Vine regrowth concealing mature roots in late-season rains",
            "Over-maturity causes roots to become woody or to hollow",
        ],
        scientific_notes=(
            "Sweet potato reaches physiological maturity when root starch content peaks, "
            "generally 120-150 days after planting depending on variety and temperature. "
            "Unlike grain crops, sweet potato does not have a discrete physiological maturity "
            "event — harvest timing is determined by root size, skin set, and market readiness. "
            "Skin set (development of a tough outer periderm) improves after reducing irrigation. "
            "Curing post-harvest is essential: at 29-33°C, 90-95% RH for 4-7 days, the cut "
            "surfaces form a wound periderm (2-5 cell layers) that prevents desiccation and "
            "fungal entry. Uncured roots lose 10-15% weight in 2 weeks and have 3-4x higher "
            "storage rot rates. OFSP varieties (Irene, Chingovha) should be harvested at "
            "optimal maturity to maximise beta-carotene content for nutrition programmes."
        ),
    ),
]


SWEET_POTATO_FERT = FertilizerSchedule(
    basal={
        "product": "Compound D (7:14:7)",
        "rate_kg_ha": 300,
        "timing": "At planting — incorporate into ridges before planting cuttings",
        "placement": "Band 5-7 cm beneath and beside the cutting in the ridge",
        "nutrients_supplied": {"N": 21, "P2O5": 42, "K2O": 21},
        "notes": "Sweet potato has a high potassium demand for root starch synthesis. "
                 "Compound D provides balanced starter nutrition. "
                 "On low-P soils (common in sandy NR IV-V), increase to 350 kg/ha or supplement "
                 "with single superphosphate (100 kg/ha). "
                 "Do NOT apply fertiliser directly in contact with stem cuttings — burns emerging roots. "
                 "On irrigated sandy soils, split basal application: 200 kg/ha at planting + 100 kg/ha at 3 weeks.",
    },
    top_dress_1={
        "product": "Ammonium Nitrate (AN 34.5%N)",
        "rate_kg_ha": 100,
        "timing": "4-6 weeks after planting when vines are actively growing (30-40 cm long)",
        "placement": "Side-dress 10 cm from vine row, lightly incorporated or watered in",
        "nutrients_supplied": {"N": 34.5},
        "notes": "Stimulates vine and leaf development to build photosynthetic capacity for root fill. "
                 "Apply when soil is moist — do NOT apply in dry conditions or onto dry foliage. "
                 "In NR IV-V with uncertain rainfall, reduce to 75 kg/ha to avoid promoting excessive "
                 "vine growth at expense of root formation. "
                 "Alternatively, use urea (46%N) at 72 kg/ha for equivalent N supply. "
                 "CRITICAL: Do NOT apply nitrogen after 8 weeks — excess late N shifts "
                 "assimilate partitioning from roots to shoots, directly reducing root yield.",
    },
    top_dress_2=None,
    foliar={
        "product": "Potassium Schoenite / Polysulphate or K-foliar (potassium sulphate 50% K2O)",
        "rate_kg_ha": "2-3 kg/ha in 400 L water",
        "timing": "At 8-10 weeks (onset of root bulking) if potassium deficiency symptoms appear",
        "notes": "Apply as foliar spray only if soil K is inadequate (shown by marginal leaf scorch). "
                 "Potassium sulphate preferred over KCl — sulphate form improves root quality. "
                 "Boron deficiency (internal cork) is addressed by: Solubor 0.1-0.2% foliar spray "
                 "at 8 and 12 weeks; important on sandy, low-organic-matter soils of NR IV-V. "
                 "Zinc deficiency (small, distorted leaves) — ZnSO4 0.3% foliar or 10 kg/ha to soil.",
    },
    liming={
        "product": "Agricultural lime (CaCO3) or dolomitic lime",
        "rate_kg_ha": "500-1000 kg/ha based on soil pH test",
        "timing": "Apply 4-6 weeks before planting and incorporate into ridges",
        "notes": "Sweet potato performs best at pH 5.5-6.5. "
                 "Below pH 5.0: aluminium toxicity restricts root elongation; phosphorus is locked up. "
                 "Above pH 7.0: manganese and zinc deficiencies occur. "
                 "Dolomitic lime is preferred on Mg-deficient sandy soils. "
                 "Many NR IV-V sandy soils have natural pH 5.0-5.5 — moderate liming is beneficial.",
    },
    notes=(
        "Total N requirement for sweet potato is modest (40-60 kg N/ha total) compared to cereals. "
        "Excess nitrogen is counterproductive — it promotes vine growth and reduces root yield. "
        "The crop has high potassium demand (~100-120 kg K2O/ha for a 15-20 t/ha crop). "
        "Compound D at 300 kg/ha provides 21 kg K2O; this may be supplemented with muriate of potash "
        "(KCl) at 50-75 kg/ha on K-deficient soils. "
        "For OFSP varieties grown in nutrition programmes, balanced K and B nutrition is critical "
        "for maximising beta-carotene content (beta-carotene synthesis requires adequate potassium). "
        "Manure (cattle or compost at 5-10 t/ha) is highly beneficial — improves soil structure, "
        "water retention in sandy soils, and provides micronutrients including boron and zinc."
    ),
)


SWEET_POTATO_PLANTING_WINDOWS: List[PlantingWindow] = [
    PlantingWindow(
        region="NR I (Eastern Highlands, >1000 mm/year)",
        optimal_start="October 15",
        optimal_end="November 30",
        acceptable_start="October 1",
        acceptable_end="December 31",
        notes="Sweet potato performs well in the warm lowveld fringes of NR I. "
              "In the highlands proper (>1500 m), growing season is cool; use early-maturing varieties. "
              "Excellent irrigation potential supports year-round production in valley floors. "
              "Secondary season planting (February-March) possible under irrigation. "
              "SPVD risk is lower at altitude due to reduced whitefly pressure.",
    ),
    PlantingWindow(
        region="NR II (Mashonaland, 750-1000 mm/year)",
        optimal_start="October 15",
        optimal_end="December 1",
        acceptable_start="October 1",
        acceptable_end="December 31",
        notes="Main season planting with first October-November rains. "
              "Plant into ridges once soil has received 30+ mm of rain and is reliably moist. "
              "Secondary (vlei) season: February-March planting on residual moisture along river banks and dambos. "
              "Whitefly and SPVD risk is moderate — use certified planting material and reflective mulch. "
              "Both OFSP (Irene, Chingovha) and white-fleshed varieties grow well here.",
    ),
    PlantingWindow(
        region="NR III (Semi-intensive, 650-800 mm/year)",
        optimal_start="October 15",
        optimal_end="November 30",
        acceptable_start="October 1",
        acceptable_end="December 15",
        notes="Main season aligns with November-December rain establishment. "
              "Sweet potato is an excellent dryland crop here — drought tolerance during mid-season dry spells. "
              "Residual moisture planting in February-March along water courses provides a valuable second crop. "
              "Weevil pressure increases in mid-season dry spells — irrigation or ridging is essential. "
              "OFSP varieties recommended for food and nutrition security programmes in NR III.",
    ),
    PlantingWindow(
        region="NR IV (Semi-extensive, 450-650 mm/year)",
        optimal_start="November 1",
        optimal_end="December 15",
        acceptable_start="October 20",
        acceptable_end="January 7",
        notes="CRITICAL food security zone — sweet potato is often the primary starchy staple after sorghum. "
              "Plant with season-establishing rains (40+ mm in a week). "
              "Early planting maximises canopy cover before January dry spells reduce soil moisture. "
              "Irrigation (where available) supports season extension into March-April. "
              "Weevil management is critical — soil cracking during dry periods is severe. "
              "OFSP varieties (Irene, Chingovha) priority for nutrition benefits in food-insecure households. "
              "Residual moisture planting (February-March) along rivers and dambos is traditional practice.",
    ),
    PlantingWindow(
        region="NR V (Lowveld, <450 mm/year)",
        optimal_start="November 15",
        optimal_end="December 31",
        acceptable_start="November 1",
        acceptable_end="January 15",
        notes="Most important food security zone for sweet potato in Zimbabwe. "
              "Season is short and unreliable — use shortest-maturing varieties (100-120 day types). "
              "Sweet potato's drought tolerance makes it more reliable than maize or cowpea in poor years. "
              "Plant on stored soil moisture after first rains, on the highest available ground to avoid waterlogging. "
              "Weevil pressure is extreme in NR V — harvesting promptly at maturity is essential. "
              "Vine multiplication during the growing season is the survival strategy for planting material. "
              "Winter garden production (May-August) possible near rivers and with simple bucket irrigation — "
              "this is a critical household nutrition window for OFSP production.",
    ),
]


PROFILE = CropProfile(
    crop_name="Sweet Potato",
    scientific_name="Ipomoea batatas",
    family="Convolvulaceae",
    optimal_ph=(5.5, 6.5),
    critical_ph_low=4.8,
    optimal_soil_types=["kaolinitic", "fersiallitic", "siallitic"],
    avoid_soil_types=["waterlogged", "heavy vertisol with poor drainage", "pure rock-derived lithosol"],
    optimal_temp=(24.0, 30.0),
    critical_temp_low=12.0,
    critical_temp_high=40.0,
    base_temp_gdd=15.0,
    total_water_mm=500.0,
    growth_stages=SWEET_POTATO_GROWTH_STAGES,
    fertilizer_schedule=SWEET_POTATO_FERT,
    diseases=SWEET_POTATO_DISEASES,
    pests=SWEET_POTATO_PESTS,
    planting_windows=SWEET_POTATO_PLANTING_WINDOWS,
    harvest_moisture="Harvested fresh at 70-80% water content; "
                     "target for storage: cure to develop wound periderm, then store at 13-16°C, 85-90% RH. "
                     "Fresh roots are 65-75% water — no 'dry' moisture standard as with grain crops.",
    storage_conditions="Cure immediately after harvest at 29-33°C, 85-95% RH for 4-7 days to form wound periderm. "
                       "Store cured roots at 13-16°C (cool cellar/rondavel in shade) at 85-90% RH. "
                       "DO NOT refrigerate below 10°C — chilling injury causes internal blackening. "
                       "Inspect stored roots weekly; remove and use any with soft spots or rot immediately. "
                       "Properly cured and stored sweet potato can last 4-6 months. "
                       "At smallholder level without temperature control: store in cool, well-ventilated shade "
                       "and consume within 4-8 weeks of harvest.",
    post_harvest_notes="Handle roots gently at harvest — skin damage and bruising are primary entry points for "
                       "black rot (Ceratocystis fimbriata) and Rhizopus soft rot. "
                       "Use hand-digging with a fork or sharp hoe; avoid dragging roots along soil. "
                       "Grade immediately: Grade 1 (200-400 g, smooth, no defects) for fresh market; "
                       "Grade 2 (small or minor defects) for home consumption; damaged for animal feed. "
                       "OFSP roots for nutrition programmes: harvest at optimal maturity (120-140 days) "
                       "to maximise beta-carotene content. "
                       "Vine utilisation: sweet potato leaves and vines are highly nutritious vegetables "
                       "(rich in protein, iron, and beta-carotene) — communicate this to farmers as an "
                       "important dual-use benefit, especially during the hungry period (October-December). "
                       "Vine multiplication: retain 2-3 healthy plants per 10 m row as a permanent vine bank "
                       "to supply planting material for the next season. "
                       "Processing: surplus roots can be processed into dried chips (slice 5 mm, dry in sun "
                       "2-3 days) or sweet potato flour for porridge — key food security strategy in NR IV-V.",
    natural_region_suitability={
        "NR I": "Good in valley floors and lower-altitude areas; cool highlands limit growth; "
                "high rainfall increases disease risk (Alternaria, black rot) — drainage critical",
        "NR II": "Well suited; high productivity with adequate moisture; "
                 "OFSP varieties recommended for food and nutrition security programmes",
        "NR III": "Highly recommended — drought tolerance and food security value; "
                  "dual-purpose crop (roots + leaves); OFSP for nutrition programmes; "
                  "second crop on residual moisture highly viable",
        "NR IV": "Critical food security crop — one of the most reliable starchy staples available; "
                 "OFSP varieties (Irene, Chingovha) prioritised for nutrition; "
                 "weevil management is the primary production constraint; "
                 "vine multiplication skills are essential survival knowledge",
        "NR V": "Essential food and nutrition security crop — drought tolerance and vine multiplication "
                "make it uniquely valuable in the most water-limited zone; "
                "short-season varieties + winter garden production (near rivers) is a critical strategy; "
                "OFSP beta-carotene provides vitamin A in contexts of highly limited dietary diversity",
    },
)

ALIASES = ["sweet potatoes", "mbambaira"]
