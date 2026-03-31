"""Banana (Musa acuminata) — Tropical/subtropical perennial herbaceous fruit crop with high domestic and export value."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List


BANANA_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Panama Disease / Fusarium Wilt (Tropical Race 4)",
        pathogen="Fusarium oxysporum f. sp. cubense Tropical Race 4 (Foc TR4)",
        pathogen_type="fungal",
        symptoms=[
            "Yellowing of lower/outer leaves from the leaf margin inward, progressing upward through the crown",
            "Leaves collapse and hang down the pseudostem like a skirt before turning brown and drying",
            "Longitudinal splitting at the base of the pseudostem in advanced infections",
            "Internal vascular discolouration: yellow-to-reddish-brown streaks in pseudostem cross-section",
            "Dark brown-black staining of the central vascular cylinder in the rhizome (corm) — definitive sign",
            "Stunted plant growth; new suckers may also become infected through the shared corm",
            "Plants wilt and die before or soon after bunch emergence in severe cases",
        ],
        identification_markers=[
            "Vascular discolouration in pseudostem cross-section (brown/red streaks) — the primary diagnostic",
            "Rhizome/corm cut reveals dark brown to black central cylinder surrounded by cream-white outer tissue",
            "Symptom progression from outer leaves inward distinguishes from wind damage or drought",
            "Confirmed by laboratory plating on selective media (Nash-Snyder medium) or PCR diagnostic",
            "Presence of classic 'Panama wilt' appearance in Cavendish cultivars indicates TR4",
        ],
        favourable_conditions={
            "soil_temp_min_c": 24,
            "soil_temp_max_c": 32,
            "soil_moisture": "moderately moist; present in both wet and dry soils",
            "ph_range": "wide; worst in acidic, poorly drained, nutrient-deficient soils",
            "note": (
                "Foc TR4 produces chlamydospores that persist in soil for decades — effectively permanent "
                "once established. Spread occurs via infected planting material (suckers), contaminated "
                "soil on tools, vehicles, footwear, irrigation water, and run-off. There is NO effective "
                "chemical cure once soil is infested. Stress factors (drought, waterlogging, nematode "
                "damage to roots, compaction) dramatically accelerate disease expression."
            ),
        },
        susceptible_stages=["All stages — from establishment through maturity"],
        resistant_varieties=[
            "FHIA-01 (Goldfinger) — TR4 resistant, good yield but different flavour profile",
            "FHIA-17 — TR4 resistant dessert banana",
            "Gros Michel types — resistant to TR4 but susceptible to Race 1",
            "Pisang Jari Buaya — field tolerance reported",
        ],
        susceptible_varieties=[
            "Williams (Cavendish AAA) — highly susceptible; dominant Zimbabwe commercial variety",
            "Grand Nain (Cavendish AAA) — highly susceptible",
            "Dwarf Cavendish — highly susceptible",
            "All Cavendish subgroup cultivars",
        ],
        chemical_control=[
            {
                "name": "No registered curative chemical treatment",
                "rate": "N/A",
                "phi_days": "N/A",
                "notes": (
                    "Fungicides do not cure Foc TR4 infections. Preventive soil drenches with "
                    "Trichoderma-based biocontrol products may delay disease progression in "
                    "mildly infested soils but cannot eliminate the pathogen. Silicon (SiO2) "
                    "soil amendments and biochar may reduce disease pressure marginally."
                ),
            },
            {
                "name": "Carbendazim 500 SC (preventive/sucker treatment only)",
                "rate": "2 ml/L, sucker corm dip before planting",
                "phi_days": "60",
                "notes": (
                    "Corm dip of clean suckers before planting in potentially contaminated sites "
                    "— limited efficacy against TR4 but may reduce surface inoculum from Race 1. "
                    "NOT a substitute for clean planting material from tissue culture."
                ),
            },
        ],
        biological_control=[
            "Trichoderma harzianum + T. viride soil drench at planting (5 kg product/ha in irrigation water)",
            "Bacillus subtilis rhizosphere inoculant applied to planting holes",
            "Pseudomonas fluorescens soil drench as root coloniser",
            "Organic matter incorporation (compost, green manures) to stimulate suppressive soil microbiome",
            "Mycorrhizal inoculants (Glomus intraradices) to strengthen root system and competitive exclusion",
        ],
        cultural_control=[
            "USE ONLY CERTIFIED DISEASE-FREE TISSUE CULTURE (TC) PLANTLETS — this is the single most important preventive measure",
            "If using suckers, source only from blocks with no history of Panama disease; inspect corm before planting",
            "Strict biosecurity: dedicate tools, boots, and equipment to each block; disinfect with 10% bleach or Jik between blocks",
            "Quarantine: infected stools must be completely dug out, corm destroyed (burning or deep burial with lime) — do not compost",
            "Do not move soil, water, or equipment from infected to clean areas",
            "Maintain optimum soil health: balanced pH (6.0-6.5), adequate K and Ca, good drainage to reduce plant stress",
            "Nematode management is critical — nematode damage to roots provides entry points for Foc",
            "In heavily infested soils, fallowing with non-host Brachiaria/Panicum grasses for 3+ years reduces inoculum",
            "Establish windbreaks and manage drainage channels to limit water-borne spread",
            "Report suspected TR4 to Agritex / Plant Protection Research Institute immediately",
        ],
        economic_threshold=(
            "ZERO TOLERANCE — any confirmed Foc TR4 infection requires immediate quarantine of the block. "
            "A single infected mat can infest an entire plantation within 3-5 years. Economic impact is "
            "total crop loss on infected land. Phytosanitary pest of national significance."
        ),
        severity_scale={
            "mild": "1-3 infected mats per hectare; block viable if immediately quarantined; aggressive rouging may preserve rest of block",
            "moderate": "4-20 infected mats/ha; block viability in serious question; consider transition to resistant variety",
            "severe": "> 20 mats/ha or spreading rapidly; block must be abandoned for Cavendish; transition to FHIA or other host",
        },
    ),
    DiseaseProfile(
        name="Black Sigatoka (Black Leaf Streak Disease)",
        pathogen="Mycosphaerella fijiensis (anamorph: Pseudocercospora fijiensis)",
        pathogen_type="fungal",
        symptoms=[
            "Initial: tiny pale yellow streaks (1-2 mm) parallel to leaf veins on lower leaf surface (Stage 1-2)",
            "Streaks expand to brown rust-coloured lesions with yellow halos visible from above (Stage 3-4)",
            "Mature lesions: elliptical, dark brown to black with grey-white necrotic centres and yellow chlorotic halos (Stage 5)",
            "Leaf tissue between lesions turns yellow then collapses; leaves die prematurely from oldest to youngest",
            "Severe infection: entire leaf canopy destroyed; only youngest 1-2 leaves remain green",
            "Premature fruit ripening ('premature yellowing') on bunch; fingers ripen unevenly and smaller",
            "Significant yield loss: 30-50% in uncontrolled situations; up to 100% in susceptible blocks with no spraying",
        ],
        identification_markers=[
            "Yellow streaks on adaxial (upper) leaf surface parallel to midrib — earliest visible stage",
            "Black/dark brown oval lesions with distinctive yellow halo and grey necrotic centre",
            "Progression from leaf tip and margins inward; oldest leaves (outermost) most severely affected",
            "Lesion stages 1-6 on a single leaf indicate active epidemic (Fouré staging system)",
            "Distinguish from Yellow Sigatoka (M. musicola) by darker lesion colour and faster leaf destruction",
            "Microscopy: dark pseudothecia with bitunicate asci on mature lesions; conidia hyaline and curved",
        ],
        favourable_conditions={
            "temp_min_c": 22,
            "temp_max_c": 30,
            "humidity_min": 85,
            "rainfall_trigger": "frequent rainfall or heavy dew promoting leaf wetness > 8 hours",
            "note": (
                "Infection requires free moisture on leaf surface for ascospore germination (minimum 6-8 hours "
                "of leaf wetness). Optimal infection at 25-28 degC. Spores are wind-dispersed (ascospores) and "
                "water-splash dispersed (conidia). Zimbabwe's Eastern Highlands (Chipinge, Chimanimani) with "
                "high rainfall and humidity are extreme high-pressure zones. Lowveld irrigated schemes have "
                "reduced pressure but irrigation creates localised leaf wetness. Wet season (Nov-April) is "
                "peak epidemic period. Disease builds on untreated blocks in 6-8 weeks under favourable conditions."
            ),
        },
        susceptible_stages=["Vegetative (emerging leaves most susceptible)", "Bunch development"],
        resistant_varieties=[
            "FHIA-01, FHIA-17 — moderate field resistance",
            "SH-3436-9 — improved resistance",
            "Most cooking banana types (Plantain) have moderate tolerance",
        ],
        susceptible_varieties=[
            "Williams and all Cavendish cultivars — highly susceptible",
            "Gross Michel — highly susceptible",
        ],
        chemical_control=[
            {
                "name": "Propiconazole 250 EC (Tilt / Bumper)",
                "rate": "500 ml/ha in 200-400 L water",
                "phi_days": "28",
                "notes": (
                    "DMI (triazole) systemic fungicide; excellent curative and protectant activity. "
                    "Core fungicide in Black Sigatoka programmes. Spray on 21-day cycle or "
                    "Disease Warning System (DWS) timing. Rotate with non-DMI fungicides."
                ),
            },
            {
                "name": "Azoxystrobin 250 SC (Amistar)",
                "rate": "600-800 ml/ha in 400 L water",
                "phi_days": "14",
                "notes": (
                    "QoI (strobilurin) systemic; translaminar penetration. Use in rotation with DMIs "
                    "to manage resistance. Effective against both Black and Yellow Sigatoka. "
                    "Do not exceed 3 consecutive applications."
                ),
            },
            {
                "name": "Mancozeb 800 WP (Dithane M-45)",
                "rate": "2.0 kg/ha in 400-600 L water",
                "phi_days": "7",
                "notes": (
                    "Protectant (multi-site); low resistance risk. Used in dry season or as "
                    "part of a rotation programme. Best applied before rain events. "
                    "Tank-mix with mineral oil (2-4 L/ha) to improve leaf coverage and penetration."
                ),
            },
            {
                "name": "Mineral oil (250 cSt petroleum / Banole)",
                "rate": "4-8 L/ha in 400-600 L water",
                "phi_days": "0",
                "notes": (
                    "Adjuvant and fungicide with physical mode of action; smothers spores. "
                    "Tank-mix with systemics to improve efficacy. Used as sole treatment in "
                    "organic programmes. DO NOT apply in temperatures above 34 degC (phytotoxicity risk)."
                ),
            },
        ],
        biological_control=[
            "Bacillus subtilis foliar spray (Serenade / Rhapsody) — suppressive effect on ascospore germination",
            "Trichoderma-based foliar products — limited efficacy as primary control",
            "Deleaf removal of infected leaves to reduce inoculum load (mandatory cultural practice)",
        ],
        cultural_control=[
            "Deleafing: remove and destroy all leaves with > Stage 5 lesions (cut and bury or burn); reduces inoculum by 60-70%",
            "Deleaf frequency: weekly in wet season, fortnightly in dry season",
            "Maintain appropriate plant spacing (2.5 x 2.5 m or 3 x 2 m) for air circulation",
            "Drainage: waterlogged soils increase humidity, prolonging leaf wetness",
            "Remove dead and dying pseudostems promptly after harvest",
            "Minimise overhead irrigation where drip/micro-jet can substitute",
            "Maintain adequate nutrition, especially potassium, to improve leaf thickness and resistance",
            "Train to single follower system to reduce canopy density",
        ],
        economic_threshold=(
            "In commercial production, Black Sigatoka requires PREVENTIVE management — waiting for "
            "economic threshold results in severe crop loss. Leaf damage score > 30% (LeafArea Destroyed) "
            "or Dose-Response Interval (DRI) system reaching trigger point requires immediate fungicide "
            "application. Yield losses of 35-50% at DRI threshold in untreated blocks."
        ),
        severity_scale={
            "mild": "Stages 1-3 lesions only; < 10% LAD; protective programme maintaining control",
            "moderate": "Stage 4-5 lesions on leaves 3-5; 10-30% LAD; curative spray needed within 7 days",
            "severe": "> 30% LAD; multiple dead leaves; bunch fill compromised; emergency spray schedule required",
        },
    ),
    DiseaseProfile(
        name="Banana Bunchy Top Virus (BBTV)",
        pathogen="Banana bunchy top virus (genus Babuvirus, family Nanonviridae)",
        pathogen_type="viral",
        symptoms=[
            "Chlorotic (yellow-green) streaks on midrib, petiole, and pseudostem — often the first symptom",
            "'Dot-dash' or 'Morse code' pattern of dark-green streaks along veins of younger leaves",
            "Leaves become progressively smaller, narrower, and more erect — the 'bunchy top' appearance",
            "Leaf margins roll upward; leaves are stiff, brittle, with a waxy-grey-green discolouration",
            "Severely infected plants produce very small, crowded leaves at the apex (rosette/bunchy appearance)",
            "Infected plants rarely or never produce a bunch; if they do, fruit is malformed and unmarketable",
            "Plant growth stops; infected mats remain stunted indefinitely (cannot recover)",
        ],
        identification_markers=[
            "'Dot-dash' vein clearing on midrib and leaf lamina veins — pathognomonic for BBTV",
            "Dark green streaks on petiole and pseudostem (epidermal layer) visible in early infection",
            "Progressively smaller, bunched leaves at apex — very distinctive at advanced stage",
            "Confirm with ELISA or lateral flow immunoassay kits (available from PPRI Zimbabwe)",
            "Distinguish from Cucumber Mosaic Virus (CMV) by Morse code streaking and bunchy growth habit",
        ],
        favourable_conditions={
            "vector": "Pentalonia nigronervosa (banana aphid) — primary vector in a persistent circulative manner",
            "temp_range_c": "20-30 degC optimal for aphid population build-up",
            "note": (
                "BBTV is transmitted exclusively by the banana aphid (P. nigronervosa) in a persistent, "
                "circulative manner — once a aphid acquires the virus (12-hour acquisition feeding), it "
                "remains viruliferous for life and transmits to every plant it subsequently feeds on. "
                "No cure exists. Spread is entirely dependent on aphid movement. New plantings adjacent "
                "to infected blocks are at extreme risk. The virus is also transmitted through infected "
                "suckers. Zimbabwe has had BBTV outbreaks in Chipinge district and Lowveld irrigation schemes."
            ),
        },
        susceptible_stages=["All growth stages; most devastating in young plants (0-4 months)"],
        resistant_varieties=[
            "No truly BBTV-immune Cavendish varieties known",
            "Some Musa balbisiana types and cooking bananas show field tolerance",
        ],
        susceptible_varieties=[
            "Williams and all Cavendish — fully susceptible",
            "Lady Finger (Silk AAB) — susceptible",
        ],
        chemical_control=[
            {
                "name": "Imidacloprid 350 SC (Gaucho / Confidor)",
                "rate": "1 ml/L — soil drench around base of plant (200 ml solution per mat)",
                "phi_days": "21",
                "notes": (
                    "Systemic neonicotinoid; translocated into leaf tissue. Controls aphid vector "
                    "for 6-8 weeks per application. Apply at planting and again at 6 weeks. "
                    "Does not cure BBTV but prevents vector from spreading virus to healthy plants."
                ),
            },
            {
                "name": "Thiamethoxam 250 WG (Actara)",
                "rate": "0.2 g/L, foliar spray on aphid colonies",
                "phi_days": "14",
                "notes": "Foliar application for aphid knockdown; rotate with imidacloprid to manage resistance",
            },
            {
                "name": "Mineral oil spray",
                "rate": "5 ml/L",
                "phi_days": "0",
                "notes": "Physical control of aphid colonies; no resistance risk; safe around beneficials",
            },
        ],
        biological_control=[
            "Lacewings (Chrysoperla spp.) — predators of banana aphid colonies",
            "Parasitoid wasps: Lysiphlebus testaceipes parasitises banana aphid",
            "Ladybird beetles (Coccinellidae) — important aphid predators",
            "Conserve natural enemies by minimising broad-spectrum insecticide use",
        ],
        cultural_control=[
            "ROGUE AND DESTROY all infected plants IMMEDIATELY upon identification — do not delay",
            "Roguing protocol: inject infected pseudostem with paraquat/kerosene to kill before removing (prevents aphid dispersal during uprooting)",
            "Remove all suckers from rogued mat; pour diesel into corm cavity; cover with soil",
            "Establish BBTV-free buffer zones around clean plantations",
            "Use only certified TC plantlets or BBTV-tested suckers from disease-free blocks",
            "Inspect new plantings weekly for BBTV symptoms, especially in first 3 months",
            "Eliminate weed hosts of banana aphid around the plantation",
            "Coordinate with neighbouring growers for area-wide aphid management",
        ],
        economic_threshold=(
            "ZERO TOLERANCE — every infected plant must be rogued within 48 hours of confirmation. "
            "A single unrogued infected mat is a permanent inoculum source that can spread to the "
            "entire block via aphids within one season. BBTV can cause 100% yield loss on unmanaged "
            "plantations. Notifiable disease in Zimbabwe."
        ),
        severity_scale={
            "mild": "< 1% incidence; immediate roguing can protect remaining block; increase aphid monitoring",
            "moderate": "1-5% incidence; intensive roguing + aphid vector control; block at risk without aggressive management",
            "severe": "> 5% incidence; block severely compromised; consider replanting with clean TC material after buffer period",
        },
    ),
    DiseaseProfile(
        name="Banana Xanthomonas Wilt (BXW)",
        pathogen="Xanthomonas vasicola pv. musacearum (syn. X. campestris pv. musacearum)",
        pathogen_type="bacterial",
        symptoms=[
            "Wilting and yellowing of leaves, starting with inner/younger leaves (opposite pattern to Panama disease)",
            "Yellow ooze from cut pseudostem or inflorescence — bacterial exudate is yellow to orange-brown",
            "Premature yellowing and shrivelling of fingers before bunch matures",
            "Internal discolouration: yellow to brown streaks in vascular tissue of pseudostem and peduncle",
            "Collapse of male bud and peduncle; rotting of bunch stalk",
            "Unripe fruit collapses and shrivels; if cut, yellow ooze and internal rot visible",
            "Entire mat may collapse and die within weeks of bunch infection",
        ],
        identification_markers=[
            "Yellow bacterial ooze from cut vascular tissue — the key field diagnostic for BXW",
            "Yellowing beginning with youngest/inner leaves (distinguishes from Panama wilt)",
            "Malformed, shrivelled fingers with internal brown-yellow rot",
            "Cut pseudostem cross-section shows irregular yellow-brown vascular streaking with ooze",
            "Cut near male bud reveals yellow-brown discolouration and ooze",
            "Confirm with field lateral-flow immunoassay or laboratory isolation on YPGA medium",
        ],
        favourable_conditions={
            "transmission_routes": "insect visitors to male bud, infected cutting tools, infected suckers",
            "temp_min_c": 20,
            "temp_max_c": 30,
            "note": (
                "BXW spreads through: (1) insect vectors feeding on male bud inflorescences (bees, wasps, "
                "flies carrying exudate); (2) contaminated cutting tools shared between plants (machetes, "
                "pangas); (3) infected planting material (suckers). Removing the male bud at bunch emergence "
                "('de-budding') eliminates the main infection court. Present in East Africa and has been "
                "reported in Tanzania; growers in eastern Zimbabwe should be on high alert."
            ),
        },
        susceptible_stages=["Bunch emergence and development (highest risk)", "All stages via tool transmission"],
        resistant_varieties=[
            "No known fully resistant commercial varieties",
            "Enset (false banana) resistant",
        ],
        susceptible_varieties=[
            "Williams and all Cavendish — susceptible",
            "Most Musa species susceptible",
        ],
        chemical_control=[
            {
                "name": "No registered curative bactericide for BXW",
                "rate": "N/A",
                "phi_days": "N/A",
                "notes": (
                    "Copper-based bactericides (copper oxychloride 3 g/L) may suppress surface bacterial "
                    "populations on tools and cut surfaces but do not cure systemic infections. "
                    "Preventive copper sprays on male buds at emergence have been trialled with limited success."
                ),
            },
        ],
        biological_control=[
            "Bacillus subtilis soil applications may provide minor suppression",
            "Maintain healthy soil microbiome as indirect defence",
        ],
        cultural_control=[
            "DE-BUDDING: remove male bud with a forked stick (no hands) immediately after last hand of fingers emerges — eliminates primary infection court",
            "Tool sterilisation: disinfect machetes between every plant with 10% bleach solution or 10% formaldehyde",
            "Use only disease-free TC plantlets or confirmed-clean suckers from certified blocks",
            "Single-machete policy: do not share tools between blocks; use one tool per block",
            "Rogue infected mats immediately using 'mat injection' (systemic herbicide into pseudostem) before uprooting",
            "Remove and destroy all debris from rogued mats; do not compost",
            "Restrict movement of people and equipment between blocks",
        ],
        economic_threshold=(
            "ZERO TOLERANCE for BXW in Zimbabwe — rogue all infected mats within 48 hours. "
            "BXW can spread to 50-100% of a plantation within one season if uncontrolled. "
            "Primarily of high concern in blocks neighbouring East African imports."
        ),
        severity_scale={
            "mild": "1-2 infected mats; immediate roguing and de-budding protocol can contain outbreak",
            "moderate": "3-15% incidence; aggressive roguing, de-budding, and tool sterilisation essential",
            "severe": "> 15% incidence; risk of total block loss; replant only with clean material after 2-season fallow",
        },
    ),
]


BANANA_PESTS: List[PestProfile] = [
    PestProfile(
        name="Banana Weevil (Corm Weevil)",
        scientific_name="Cosmopolites sordidus",
        pest_type="insect",
        identification=[
            "Adult: hard-bodied black/dark brown snout weevil, 12-15 mm long, with characteristic curved rostrum",
            "Adults are nocturnal; found under leaf sheaths, in corm tunnels, or in leaf litter at base of plant",
            "Eggs: white, oval, laid singly in cavities chewed into pseudostem base or corm",
            "Larvae: white, legless, C-shaped grubs (up to 12 mm) with brown head capsule; found in corm tunnels",
            "Pupae: creamy white, found in corm galleries",
        ],
        damage_symptoms=[
            "Extensive tunnelling in the corm (rhizome) — larvae bore galleries through corm tissue",
            "Corm cross-section reveals networks of dark, frass-filled tunnels with decaying tissue",
            "Weakened pseudostem base leading to lodging (plants fall over, especially in wind)",
            "Stunted growth; poor sucker development; delayed bunch emergence",
            "Reduced root system due to corm destruction — plants susceptible to drought and nutritional stress",
            "Entry wounds in corm are infection courts for Foc and other soil pathogens",
            "Severe infestations: 'toppling disease' where pseudostems collapse at the base",
        ],
        life_cycle_notes=(
            "Complete lifecycle 5-8 months. Adults are long-lived (up to 3 years) and strongly attracted "
            "to fresh cut pseudostem tissue (host kairomones). Female lays 50-200 eggs over her lifetime. "
            "Larvae develop entirely within the corm (3-5 months depending on temperature). Pupation in "
            "corm cavities. Adults are flightless — spread is mainly through infected planting material "
            "(suckers with larvae/eggs in corm tissue). Population densities build steadily over plantation "
            "life; old plantations (5+ years) typically harbour highest populations."
        ),
        favourable_conditions={
            "temp_min_c": 20,
            "temp_max_c": 30,
            "note": (
                "Populations highest in old, ratoon-heavy plantations. Moist soils with abundant "
                "decomposing plant debris provide ideal habitat. Low light conditions (dense canopy) "
                "favour nocturnal adults. Worst damage in plantations with accumulated dead pseudostems "
                "providing breeding sites."
            ),
        },
        susceptible_stages=["All production stages; worst impact on ratoon crops and old plantations"],
        economic_threshold=(
            "5-10 adults per pseudostem trap per week, or > 30% of plants with corm tunnelling > 25% "
            "of corm cross-section area. In newly established blocks, even 1-2 weevils per trap justifies action."
        ),
        chemical_control=[
            {
                "name": "Chlorpyrifos 480 EC (Dursban)",
                "rate": "5 ml/L — drench around pseudostem base (1-2 L per mat)",
                "phi_days": "21",
                "notes": (
                    "Soil drench to contact adults and surface larvae. Apply every 3-4 months in high "
                    "pressure situations. Direct drench into leaf axils where adults shelter."
                ),
            },
            {
                "name": "Imidacloprid 350 SC (Confidor)",
                "rate": "1 ml/L, 200-300 ml per plant as soil drench",
                "phi_days": "21",
                "notes": (
                    "Systemic; translocated into pseudostem and corm tissues. Good residual effect "
                    "against both adults (feeding on treated tissue) and early instar larvae. "
                    "Preferred for low-toxicity profile relative to organophosphates."
                ),
            },
            {
                "name": "Carbofuran 5G (Furadan) granules",
                "rate": "10-15 g per plant placed in leaf axils at pseudostem base",
                "phi_days": "30",
                "notes": (
                    "Systemic granule; releases into plant on contact with moisture. Extremely effective "
                    "but high toxicity to birds and soil invertebrates. Use only where absolutely necessary; "
                    "follow safety protocols strictly."
                ),
            },
        ],
        biological_control=[
            "Entomopathogenic nematodes: Steinernema carpocapsae and Heterorhabditis bacteriophora — apply in irrigation water or as drench around pseudostem base (2.5 million IJs/m2)",
            "Beauveria bassiana: apply as pseudostem drench or in split pseudostem traps (5 x 10^12 conidia/ha)",
            "Metarhizium anisopliae: soil application for corm larvae; persists well in moist soils",
            "Predatory ants and ground beetles provide minor suppression of surface adults",
        ],
        cultural_control=[
            "Use only clean planting material — inspect sucker corms carefully before planting; pare and dip in insecticide solution",
            "Pseudostem trap monitoring: split pseudostems placed near mats attract adults; check every 2 weeks and kill adults found",
            "Remove and destroy dead pseudostems after harvest — eliminates breeding sites",
            "Paring (shaving) of planting material corms removes eggs and early larvae before planting",
            "Maintain clean, well-drained soil around the pseudostem base",
            "Avoid leaving cut pseudostem pieces in the plantation — they attract weevils",
            "Crop rotation with non-host crops (legumes, vegetables) in old heavily-infested areas before replanting",
        ],
        scouting_protocol=(
            "Place split pseudostem trap sections (60 cm lengths, split lengthwise, baited side down) at "
            "2-3 traps per hectare. Check every 7-14 days, count and kill adults. Record weevils per trap "
            "per week to track population trends. Also perform corm inspection: dig 10 random plants per "
            "hectare, cut corm transversely, estimate % area with tunnelling. Deploy pheromone traps "
            "(Cosmolure or Sordidin lure) at 5/ha for more sensitive monitoring — 1 pheromone trap per "
            "hectare in new plantations to detect early colonisation."
        ),
    ),
    PestProfile(
        name="Burrowing Nematode",
        scientific_name="Radopholus similis",
        pest_type="nematode",
        identification=[
            "Microscopic vermiform nematodes (0.5-0.7 mm long); not visible to naked eye in soil",
            "Laboratory identification: extract nematodes from soil and root samples; identify under compound microscope",
            "Females and juveniles found in root cortex tissue; males free-living in soil",
            "Diagnostic feature: typical migratory endoparasite burrows through cortical tissue",
            "Laboratory request: send 500 g soil + 20 g fresh roots to PPRI Harare for nematode extraction and ID",
        ],
        damage_symptoms=[
            "Dark brown to black necrotic lesions on outer surface of roots and rhizome (corm)",
            "Root cortex tunnelling: dark galleries in root cross-section; outer cortex separates from stele",
            "Reduced root mass — infected roots die and slough off, leaving plant with minimal functional root system",
            "'Toppling disease': heavily infected plants fall over because of severely weakened root-corm anchor",
            "Stunted growth, chlorotic leaves, and poor bunch development despite adequate nutrition and irrigation",
            "Reduced nutrient and water uptake — symptoms resemble drought or nutrient deficiency on surface",
            "Damaged roots provide entry points for Fusarium oxysporum (Panama disease synergism — critical interaction)",
        ],
        life_cycle_notes=(
            "Lifecycle 18-25 days in warm moist soil. Eggs laid in root cortex; juveniles develop within "
            "root tissue through 4 moults to adult stage. Adults continue to migrate through and between "
            "roots destroying cortical cells. Population densities build rapidly under favourable conditions. "
            "R. similis is an obligate endoparasite — cannot complete lifecycle outside plant tissue. "
            "In Zimbabwe soils at optimal temperature (25-28 degC), populations can exceed 1000 nematodes "
            "per 100 g soil under unmanaged conditions."
        ),
        favourable_conditions={
            "temp_min_c": 24,
            "temp_max_c": 30,
            "soil_moisture": "moist, well-aerated soils (not waterlogged)",
            "soil_type": "sandy loams and alluvial soils; poor clay soils with good structure",
            "note": (
                "Populations build fastest in irrigated sandy-loam soils at 25-28 degC. Spread occurs "
                "through infected planting material (suckers and TC plants from contaminated nurseries), "
                "soil on equipment and footwear, and irrigation water. Synergistic interaction with "
                "Foc: nematode root damage dramatically increases Panama disease severity."
            ),
        },
        susceptible_stages=["Establishment (severe impact on new plantings)", "All production stages"],
        economic_threshold=(
            "200 R. similis per 100 g fresh roots, or 500 per kg soil. In newly planted fields, any "
            "detectable population warrants treatment as establishment impact is disproportionately severe."
        ),
        chemical_control=[
            {
                "name": "Fenamiphos 400 SL (Nemacur)",
                "rate": "20 L/ha as soil drench in irrigation (5 ml/L at 4 L per plant)",
                "phi_days": "60",
                "notes": (
                    "Systemic nematicide; penetrates roots and kills endoparasitic stages. "
                    "Apply at planting and 3-4 monthly thereafter. Highly effective but toxic — "
                    "handle with full PPE; re-entry interval 48 hours. Restricted-use chemical."
                ),
            },
            {
                "name": "Oxamyl 240 SL (Vydate)",
                "rate": "4 L/ha, soil drench or chemigation",
                "phi_days": "14",
                "notes": "Carbamate nematicide/insecticide; shorter PHI than fenamiphos; controls both nematodes and weevil adults",
            },
            {
                "name": "Ethoprophos 20G (Mocap)",
                "rate": "30-40 kg/ha, incorporated into planting hole",
                "phi_days": "90",
                "notes": "Granular nematicide; apply at planting for establishment-phase protection",
            },
        ],
        biological_control=[
            "Paecilomyces lilacinus (Purple Rootlet Fungus) — soil drench of conidia suspension (5 x 10^6 cfu/g soil); parasitises nematode eggs",
            "Trichoderma harzianum — promotes root health and provides indirect protection",
            "Mucuna pruriens (velvet bean) cover crop — allelopathic to nematode populations; use as inter-season fallow crop",
            "Tagetes spp. (marigolds) inter-planted as border or fallow — nematicidal root exudates (alpha-terthienyl)",
            "Entomopathogenic nematodes (Steinernema feltiae) — minor effect on plant-parasitic nematodes",
        ],
        cultural_control=[
            "Use ONLY certified clean TC plantlets from accredited nurseries (tissue culture virtually eliminates nematode introduction)",
            "If using suckers: hot water treatment of corms at 52-55 degC for 20-25 minutes before planting kills nematodes without damaging planting material",
            "Pare sucker corms to remove outer root stubs (main site of nematode infestation) before hot water treatment",
            "Fallow with Brachiaria decumbens or Mucuna pruriens for 6-12 months before replanting to reduce soil populations",
            "Avoid moving soil between blocks on equipment; wash vehicles and tools",
            "Maintain optimal soil health: organic matter additions improve nematode-suppressive microbiome",
        ],
        scouting_protocol=(
            "Sample quarterly: collect 20 sub-samples of 200 g soil per hectare from 15-20 cm depth in "
            "the root zone of 10 representative mats. Also collect 5 g of fresh roots per sampled mat. "
            "Composite and submit to PPRI nematology laboratory. Request identification and counts of "
            "Radopholus similis, Pratylenchus spp., and Meloidogyne spp. as a routine panel. Inspect "
            "roots visually during de-suckering: dark cortical lesions and root sloughing are early "
            "indicators warranting laboratory confirmation."
        ),
    ),
    PestProfile(
        name="Banana Rust Thrips",
        scientific_name="Chaetanaphothrips signipennis",
        pest_type="insect",
        identification=[
            "Adults: tiny (1.5 mm), yellow-orange to brownish; characteristically found under the fruit hands on the bunch",
            "Nymphs: pale yellow-white, even smaller; gregarious colonies under bunch bracts",
            "Distinguished from flower thrips by feeding site (under bunch leaf bracts, between fingers)",
            "Identification with 10-20x hand lens on fresh bunch; dark frass specks accompany colonies",
        ],
        damage_symptoms=[
            "Characteristic 'rust' or 'corky scar tissue' on the fruit skin between fingers — the primary damage",
            "Reddish-brown to dark brown corky scarring on peel surface, especially in the inner curvature of fingers and where fingers contact each other",
            "Severe infestations: entire fruit surface covered in rusty-brown scarring — cosmetically unacceptable for export",
            "Grade A export requirements: zero visible scarring (< 2 cm2 lesion on one finger only acceptable)",
            "Does not penetrate peel; internal flesh quality unaffected — strictly a cosmetic/grade issue",
            "Premature yellow streaking on peel in areas of scarring",
        ],
        life_cycle_notes=(
            "Complete lifecycle 14-21 days in warm conditions. Eggs inserted into fruit peel tissue. "
            "Two nymphal instars feed on peel surface under bracts. Prepupa and pupa in soil under plant "
            "or in dry bract sheaths. Adults hide under bunch bracts during day; most active at dusk. "
            "Multiple generations per bunch cycle. Population peaks during bunch development at weeks 6-10. "
            "Populations higher in hot, dry conditions with dusty soil under plants."
        ),
        favourable_conditions={
            "temp_min_c": 22,
            "temp_max_c": 34,
            "note": (
                "Warm dry weather with low humidity favours population explosions. Dusty, dry soil conditions "
                "correlate with higher infestations. Dry season crops (June-September in Lowveld) are most "
                "affected. Poorly drained dusty track edges adjacent to blocks have higher populations."
            ),
        },
        susceptible_stages=["Bunch emergence", "Bunch development (weeks 1-10 after shooting)"],
        economic_threshold=(
            "For export production: 5 adults per hand counted by brushing fruit in 1st, 3rd, and "
            "5th hands; or 10% of fingers showing any scarring at week 6 of bunch development."
        ),
        chemical_control=[
            {
                "name": "Dimethoate 400 EC",
                "rate": "1.5 ml/L in 200-400 L/ha — directed at bunch",
                "phi_days": "21",
                "notes": (
                    "Apply as directional spray to emerging bunch and bracts. Repeat at 3-week intervals "
                    "during bunch development. Take care not to contaminate fruit flesh."
                ),
            },
            {
                "name": "Spinosad 480 SC (Tracer)",
                "rate": "0.5 ml/L directed at bunch",
                "phi_days": "3",
                "notes": "Soft chemistry; low PHI; safe for natural enemies. Excellent efficacy on thrips nymphs and adults.",
            },
            {
                "name": "Abamectin 18 EC",
                "rate": "0.4 ml/L directed at bunch",
                "phi_days": "7",
                "notes": "Translaminar action; effective on both adults and nymphs under bracts; rotate with spinosad",
            },
        ],
        biological_control=[
            "Predatory mites (Amblyseius cucumeris, Neoseiulus cucumeris) — apply to bunch at shooting",
            "Orius insidiosus (minute pirate bug) — predates thrips colonies",
            "Parasitoid wasp Ceranisus menes parasitises thrips larvae",
            "Conserve predatory mite populations by using selective insecticides",
        ],
        cultural_control=[
            "Bunch sleeving: sleeve bunch in perforated blue polyethylene bag at shooting — physically excludes thrips and reduces population 60-80%",
            "Bunch sleeving is standard practice for export-grade production in Zimbabwe's Lowveld schemes",
            "Petal/bract removal (bunch trimming): remove male bud bracts as they dry to eliminate thrips refugia",
            "Maintain moist, mulched soil under plants to deter dust-thriving populations",
            "Remove dry leaf sheaths and bracts which harbour resting adults",
            "Irrigate regularly — dust suppression reduces thrips habitat near plants",
        ],
        scouting_protocol=(
            "Scout weekly from bunch shooting onward. Examine 20 bunches per hectare (or 5% of plants "
            "with emerging bunches). Count thrips adults on 3 hands per bunch (1st, 3rd, 5th) by shaking "
            "fruit fingers over white paper and counting. Also visually score scarring on 5 fingers per "
            "hand. Record separately for export vs domestic grade tolerance. Check under bract sheath for "
            "hidden colonies. Population counts taken 2-3 weeks after shooting provide the best treatment "
            "timing guidance."
        ),
    ),
]


BANANA_GROWTH_STAGES: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Establishment",
        stage_code="GS1",
        day_range=(0, 60),
        water_kc=0.45,
        water_mm_per_week=20,
        critical_nutrients=["P", "N", "K"],
        key_activities=[
            "Plant TC plantlets or prepared suckers at spacing 2.5 x 2.5 m (1,600 plants/ha) or 3.0 x 2.0 m (1,667 plants/ha)",
            "Apply basal Compound S (500 g/plant) in planting hole mixed with topsoil and 10-20 L of kraal manure or compost",
            "Stake TC plantlets and protect from wind and direct afternoon sun for first 2 weeks",
            "Apply post-planting soil drench of Trichoderma + Beauveria to establish biocontrol agents",
            "Ensure consistent irrigation: TC plantlets require light, frequent irrigation (daily if hot and dry)",
            "Check for aphids (BBTV vector) weekly from week 1",
            "Apply foliar P at day 14 if soil P is marginal",
        ],
        risks=[
            "Transplant shock from poor TC hardening or sucker paring damage",
            "Aphid (Pentalonia) feeding and BBTV transmission in early establishment",
            "Waterlogging — roots need oxygen; avoid over-irrigation of clay soils",
            "Nematode pressure if planting into previously infested ground",
            "Weeds competing for moisture and nutrients in young plantation",
        ],
        scientific_notes=(
            "The establishment phase is critical for long-term plantation productivity. Banana rhizomes "
            "(corms) must develop a functional root system within the first 4-6 weeks to ensure the "
            "plant avoids transplant failure. TC plantlets have essentially no mycorrhizal colonisation "
            "and minimal root system on arrival — root development from corm primordia begins within "
            "days of planting if soil temperature is 22-28 degC and soil moisture is 60-80% field "
            "capacity. Phosphorus is limiting at this stage as new roots require high-P conditions for "
            "cell division and mycorrhizal establishment. Potassium uptake capacity is low in the first "
            "month; avoid excessive K application that can cause salt stress. The first sucker appears "
            "at approximately 6-8 weeks in TC plants under optimal conditions."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Vegetative Growth",
        stage_code="GS2",
        day_range=(60, 180),
        water_kc=0.85,
        water_mm_per_week=40,
        critical_nutrients=["N", "K", "Mg"],
        key_activities=[
            "First nitrogen top-dress at 6-8 weeks: Ammonium nitrate (AN 34.5%) 200 g per plant",
            "Second N top-dress at 12-14 weeks: AN 200 g/plant",
            "Begin K supplementation at week 10: Potassium chloride (KCl) or Muriate of Potash (MOP) 150 g/plant",
            "De-sucker: select ONE primary follower sucker (sword sucker preferred) per mat; remove all others",
            "Apply 100 g Compound S per plant at week 8 as general nutritional support",
            "First Black Sigatoka deleafing at week 8-10; remove all leaves with stage 4-5 lesions",
            "Commence Black Sigatoka spray programme if disease pressure observed (leaf streak > stage 3)",
            "Check for banana weevil using pseudostem traps; apply treatment if threshold reached",
            "Maintain weed control by slashing or hand weeding in plant base (avoid chemical near roots)",
        ],
        risks=[
            "Black Sigatoka rapid development in wet season — can defoliate fast-growing plants",
            "Potassium deficiency (leaf margin scorch, small leaf blade) — common on sandy soils",
            "Nitrogen deficiency (pale yellow leaves, small leaf size) on high-yield plantings",
            "Banana weevil establishment from planting material or adjacent old blocks",
            "Nematode population build-up — monitor roots during de-suckering",
        ],
        scientific_notes=(
            "Banana vegetative growth is exceptionally rapid — the pseudostem is botanically not a true "
            "stem but a tightly wrapped mass of leaf bases (petioles). Under optimal conditions in "
            "Zimbabwe's Lowveld, a new leaf emerges every 6-8 days. Total leaf production before "
            "flowering is approximately 40-44 leaves for Williams. The photosynthetically active leaf "
            "area index (LAI) determines bunch fill potential — Black Sigatoka destroying leaves during "
            "this phase directly reduces the number of active source leaves available for the developing "
            "bunch. Nitrogen drives leaf emergence rate (leaf initiation interval) while potassium "
            "determines leaf size, stomatal regulation, and drought tolerance. The corm grows rapidly "
            "from week 8 onward and stores starch reserves that fuel bunch development. Magnesium is "
            "essential for chlorophyll synthesis; Mg deficiency shows as interveinal chlorosis on older "
            "leaves and is common on Zimbabwe's leached granite-derived soils."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Flower Initiation and Shooting (Inflorescence Emergence)",
        stage_code="GS3",
        day_range=(180, 270),
        water_kc=0.95,
        water_mm_per_week=50,
        critical_nutrients=["K", "N", "B", "Zn"],
        key_activities=[
            "Third nitrogen top-dress at 6 months: AN 200 g/plant",
            "Potassium application at 6 months: KCl 200 g/plant — critical for bunch fill",
            "Apply foliar boron (Solubor 2 g/L) and zinc sulphate (3 g/L) at flag leaf stage",
            "Monitor daily for bunch shooting (inflorescence emergence through pseudostem apex)",
            "On shooting: immediately sleeve bunch in perforated blue polythene bag (export standard)",
            "Remove male bud (de-bud) after last hand of fingers has formed to prevent BXW entry and thrips habitat",
            "Apply thrips insecticide at shooting if thrips populations are at threshold",
            "Increase Black Sigatoka spray frequency to protect leaves supporting bunch fill",
            "Tag mats at shooting date for harvest timing management",
        ],
        risks=[
            "Potassium deficiency at shooting reduces bunch weight and finger length significantly",
            "Boron deficiency — malformed fingers, poor hand set",
            "Black Sigatoka destroying canopy leaves needed for bunch photosynthate supply",
            "BXW transmission at inflorescence emergence (insect vector via male bud)",
            "Thrips infestation on emerging bunch (cosmetic damage)",
            "Water stress at this stage directly reduces hand number and finger count",
        ],
        scientific_notes=(
            "Flower initiation in banana is determined by the number of leaves produced (leaf index) "
            "rather than photoperiod, unlike many crops. Williams typically initiates floral "
            "differentiation after producing 34-40 leaves under Zimbabwe conditions. The flag leaf "
            "(boat leaf) emerges 3-6 weeks before the bunch; its appearance is the signal for "
            "intensified management. The inflorescence (bunch) emerges through the pseudostem apex "
            "and develops acropetally (from base to tip): the first (lowest) hand emerges first, "
            "and hands continue to form until the male bud terminates development. Final hand number "
            "(typically 8-12 for Williams) is determined genetically and by nutritional status. "
            "Potassium is the most critical mineral at this stage: K deficiency at shooting reduces "
            "finger length by 15-25% and bunch weight by 20-30%. Bunch fill (days from shooting to "
            "harvest) is temperature-dependent: 80-100 days in Lowveld summer, up to 120-150 days in "
            "cooler Eastern Highlands conditions."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Bunch Development and Fill",
        stage_code="GS4",
        day_range=(270, 360),
        water_kc=0.90,
        water_mm_per_week=45,
        critical_nutrients=["K", "Ca", "N"],
        key_activities=[
            "Maintain consistent irrigation — water stress during bunch fill permanently reduces finger size and bunch weight",
            "Apply KCl 150 g/plant at week 4 post-shooting as final K top-up",
            "Continue Black Sigatoka spray programme and deleafing every 2 weeks",
            "Monitor thrips levels under bunch sleeve; apply directional spray if threshold exceeded",
            "Prop or support heavy bunches with wooden poles or twine to prevent pseudostem cracking",
            "Monitor bunch development stage (by caliper measurement of finger girth for harvest timing)",
            "Apply lime (dolomite) as foliar Ca/Mg supplement if leaf analysis indicates deficiency",
        ],
        risks=[
            "Water stress reducing finger girth and final bunch weight",
            "Black Sigatoka destroying canopy leaves needed as source for bunch fill",
            "Thrips scarring on fruit (cosmetic; export grade rejection)",
            "Bunch toppling due to weight on weakened pseudostem base (weevil damage)",
            "Delayed harvest leading to over-maturity and internal quality problems",
        ],
        scientific_notes=(
            "Bunch fill is driven almost entirely by current photosynthesis — bananas do not "
            "substantially mobilise stored starch from the corm to the bunch. This means that "
            "the leaf canopy condition at the time of shooting determines bunch fill potential. "
            "A minimum of 8-10 photosynthetically active leaves at shooting is required for "
            "adequate bunch fill in Williams. Each active green leaf contributes to approximately "
            "one hand of fingers. The proportion of dry matter in fingers increases from about "
            "18% at shooting to 22-25% at harvest maturity. Potassium accumulation in the fruit "
            "drives osmotic potential that draws water and sugars into the pulp during fill. "
            "Calcium in fruit pulp cell walls strengthens structure and reduces post-harvest bruising. "
            "Finger girth measurement is the primary indicator: Williams export standard requires "
            "minimum 38 mm girth (3-4 weeks before colour change) for Grade A."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Harvest and Ratoon Establishment",
        stage_code="GS5",
        day_range=(360, 420),
        water_kc=0.70,
        water_mm_per_week=35,
        critical_nutrients=["N", "K"],
        key_activities=[
            "Harvest at Days to Harvest from tagged shooting date (85-100 days in Lowveld summer; 100-120 days autumn/spring)",
            "Harvest criterion: finger girth 38 mm minimum (measured on outer fingers of 2nd-3rd hand)",
            "Harvest by cutting peduncle (bunch stalk) and easing bunch onto padded shoulder or cushioned cradle",
            "Immediately after harvest: prop cut pseudostem base to allow nutrient flow to ratoon sucker",
            "Select the ratoon follower: confirm the primary sword sucker is well-established at the mat base",
            "Apply post-harvest fertiliser to ratoon: AN 200 g + KCl 100 g per mat after cutting pseudostem",
            "Cut pseudostem back in stages (do not fell in one cut — allow nutrients to flow to sucker)",
            "Remove debris, old leaf sheaths, and fallen bracts (weevil breeding sites)",
            "Post-harvest deleaf: remove all leaves remaining on dying pseudostem to reduce Black Sigatoka inoculum",
        ],
        risks=[
            "Latex staining of fruit if bruised or cut — avoid rough handling",
            "Over-mature fruit (sugar breakdown, poor shelf-life) from delayed harvest",
            "Weevil population build-up in decaying pseudostem left in field",
            "Delayed ratoon development from over-aggressive pseudostem removal",
            "Nutrient stress on ratoon if post-harvest fertilisation delayed",
        ],
        scientific_notes=(
            "Harvest timing in banana is critical: unlike climacteric fruit such as avocado and mango, "
            "bananas must be harvested at the correct immature stage (three-quarter full, green) for "
            "commercial handling. The physiological maturity criterion is finger girth, not colour — "
            "colour change (yellowing) indicates over-maturity for export purposes. After harvest, the "
            "ethylene-mediated ripening climacteric is triggered by mechanical handling or exogenous "
            "ethylene application. The ratoon (follower) system is fundamental to Zimbabwean banana "
            "production economics: a well-managed mat cycles ratoons every 9-12 months in the Lowveld, "
            "giving continuous production from a single planted mat for 10-15+ years. However, each "
            "successive ratoon typically produces a slightly later bunch (increased cycle time) and "
            "potentially reduced yield if nematode, weevil, or Sigatoka pressure is not managed. "
            "Plantation productivity models suggest optimum mat size of 2-3 mats in production at any "
            "time, cycling every 10-12 months in Lowveld conditions."
        ),
    ),
]


BANANA_FERTILIZER = FertilizerSchedule(
    basal={
        "product": "Compound S (7:21:8 + Zn) + Dolomitic lime + kraal manure/compost",
        "rate_per_plant": (
            "Compound S: 500 g/plant; Dolomitic lime: 200 g/plant if pH < 5.5; "
            "Kraal manure or compost: 10-20 kg/plant (or 20 t/ha broadcast)"
        ),
        "timing": "At planting; mix thoroughly with topsoil in planting hole (do not place in direct root contact)",
        "notes": (
            "Planting holes: 50 x 50 x 50 cm. Compound S provides phosphorus for root establishment "
            "and early potassium. The high phosphorus of Compound S is particularly important for TC "
            "plantlets which lack established mycorrhizal networks at planting. Organic matter (kraal "
            "manure) is critical for water retention in Lowveld sands and microbial community establishment. "
            "Dolomitic lime corrects pH and provides Mg — both important as banana prefers pH 5.5-7.0. "
            "Do not use high-N fertilisers at planting — root burn risk and delayed establishment."
        ),
    },
    top_dress_1={
        "product": "Ammonium Nitrate (AN 34.5%)",
        "rate_per_plant": "200 g/plant per application; applied quarterly (at weeks 6-8, 14-16, 24-26, 36-38)",
        "timing": (
            "First application at 6-8 weeks after planting (establishment confirmed). "
            "Subsequent applications at approximately 8-10 week intervals through vegetative phase and shooting."
        ),
        "notes": (
            "Banana is a heavy nitrogen feeder — total annual N requirement for Williams at "
            "1,600 plants/ha is approximately 250-300 kg N/ha, equivalent to ~700 kg AN/ha total. "
            "Split into 4-6 applications to avoid leaching on sandy soils (common in Lowveld schemes). "
            "Broadcast in a ring 30-50 cm from pseudostem base; incorporate with irrigation. "
            "Avoid AN in direct contact with pseudostem base — burn risk. "
            "In cooler Eastern Highlands conditions, reduce N application frequency in winter (June-August)."
        ),
    },
    top_dress_2={
        "product": "Muriate of Potash (MOP / KCl 60%) or Sulphate of Potash (SOP 50%)",
        "rate_per_plant": (
            "150-200 g/plant per application; quarterly applications from week 10 onward. "
            "Increase to 250 g/plant at shooting (most critical K application)."
        ),
        "timing": (
            "Starting at week 10 post-planting and continuing at 8-10 week intervals. "
            "Critical application at flag leaf (shooting) stage. "
            "Final K application 4 weeks after bunch emergence for finger fill."
        ),
        "notes": (
            "Banana is THE heaviest potassium-consuming crop in Zimbabwe — a single bunch of 20 kg "
            "removes approximately 100 g K2O. Total annual K2O requirement at 1,600 plants/ha is "
            "350-450 kg K2O/ha (580-750 kg KCl/ha). K deficiency is the most common yield-limiting "
            "nutrient disorder in Zimbabwe banana production and presents as marginal leaf scorch "
            "(early), premature yellowing of fingers (moderate), and short, thin fingers with poor "
            "fill (severe). SOP is preferred over KCl in saline-sensitive soils or where Cl toxicity "
            "is suspected. KCl is more economical and widely available in Zimbabwe and is satisfactory "
            "on most Lowveld alluvial and sand soils."
        ),
    },
    foliar={
        "product": "Zinc sulphate (ZnSO4) + Solubor (Boron) + Manganese sulphate (MnSO4)",
        "rate": "Zn: 3 g/L; B (Solubor 20.5%): 1.5 g/L; Mn: 2 g/L in 400-600 L water/ha",
        "timing": (
            "3-4 applications per crop cycle: at 8 weeks (establishment), 4 months (rapid vegetative growth), "
            "flag leaf stage (pre-shooting), and 4 weeks post-shooting (bunch fill support). "
            "Apply in early morning or late afternoon; avoid midday heat application."
        ),
        "notes": (
            "Micronutrient deficiencies are common in Zimbabwe's Lowveld alluvial sandy soils and Eastern "
            "Highlands leached fersiallitic soils. Zinc deficiency causes 'bunchy top'-like symptoms "
            "in early growth and chlorotic mottling (not to be confused with BBTV). Boron deficiency "
            "at shooting causes malformed fingers and poor hand set. Manganese deficiency presents as "
            "interveinal chlorosis on young leaves in high-pH soils (> 7.0). Calcium (CaCl2 3 g/L) "
            "may be added to foliar programme where leaf analysis shows marginal Ca status. "
            "Spray when leaves are dry; re-apply if rain falls within 2 hours of spraying."
        ),
    },
    liming={
        "target_ph": "5.5-6.5 (optimal 6.0-6.5 for nutrient availability and Foc suppression)",
        "product": "Dolomitic lime (for Mg supplement) or Agricultural lime (where Mg is adequate)",
        "rate": "1-2 t/ha every 2-3 years; verify by soil test; target pH 6.0-6.5",
        "timing": (
            "Apply dolomitic lime in dry season (June-August); broadcast evenly under plant canopy. "
            "Allow 4-6 weeks before heavy N application to avoid ammonia volatilisation."
        ),
        "notes": (
            "Banana tolerates a wide pH range (5.0-7.5) but performs best at pH 6.0-6.5. "
            "Below pH 5.5: aluminium and manganese toxicity impair root function and dramatically "
            "worsen Panama disease (Foc TR4) expression — maintaining pH above 5.5 is a significant "
            "cultural tool for Foc management. Above pH 7.0: zinc, manganese, iron, and boron "
            "become unavailable. Dolomitic lime preferred as most Zimbabwe banana soils are also "
            "magnesium-deficient. Apply lime based on soil buffer pH test for accurate rate calculation."
        ),
    },
    notes=(
        "Annual nutrient programme summary per mature bearing mat (Williams, 1,600 plants/ha): "
        "N: 200-250 g/plant/year (applied as AN in 4-6 split doses); "
        "P: 50-80 g/plant/year (mainly basal Compound S + annual top-up); "
        "K: 350-450 g K2O/plant/year (KCl or SOP in 4-5 split doses — most critical nutrient); "
        "Mg: 30-50 g/plant/year (dolomitic lime + foliar MgSO4 if deficient); "
        "Micronutrients: Zn, B, Mn via foliar programme 3-4 times/year. "
        "Organic matter management: banana plantations benefit enormously from recycling "
        "pseudostem biomass (chop and mulch after harvest rather than removing from field). "
        "Each ton of pseudostem returned to the field contains approximately 9 kg K, 1.5 kg N, "
        "0.3 kg P — a significant nutrient contribution reducing fertiliser requirements. "
        "Leaf tissue analysis should be conducted annually (sample leaf 3 or leaf at shooting) "
        "to verify actual nutrient status against targets."
    ),
)


BANANA_PLANTING_WINDOWS: List[PlantingWindow] = [
    PlantingWindow(
        region="NR I — Eastern Highlands (Chipinge, Chimanimani, Mutare high-altitude)",
        optimal_start="October 1",
        optimal_end="November 30",
        acceptable_start="September 15",
        acceptable_end="January 31",
        notes=(
            "Plant at the break of the rains when soil temperatures rise above 22 degC. "
            "The Eastern Highlands (altitude 600-1200 m) is Zimbabwe's premier banana "
            "production zone — Chipinge district produces the majority of Zimbabwe's export-grade "
            "bananas. Rainfall 900-1400 mm/year with humidity enabling Black Sigatoka pressure "
            "year-round; rigorous spray programme essential. Williams is dominant. "
            "September-October sucker planting allows full establishment before peak wet season. "
            "Avoid planting in June-August (cold soils < 18 degC slow establishment and increase "
            "transplant losses). Tissue culture plantlets preferred; suckers must be inspected and "
            "pared before planting. Altitude limits: above 1200 m growth is too slow for profitable "
            "production."
        ),
    ),
    PlantingWindow(
        region="NR IV/V — Lowveld Irrigated Schemes (Triangle, Hippo Valley, Chiredzi, Save Valley)",
        optimal_start="September 1",
        optimal_end="October 31",
        acceptable_start="August 15",
        acceptable_end="November 30",
        notes=(
            "Zimbabwe's fastest-growing banana production zone under centre-pivot and drip irrigation. "
            "Hot, dry climate (rainfall 350-550 mm) means production is entirely irrigation-dependent. "
            "Year-round production is possible with irrigation; planting can occur any month but "
            "September-October is optimal to establish before peak summer heat (avoid planting in "
            "November-January when temperatures exceed 38 degC — transplant shock risk). "
            "Water requirement: 1200-1500 mm/year supplemental irrigation. "
            "Black Sigatoka pressure is lower than Eastern Highlands but nematode and weevil pressure "
            "is high in the alluvial sandy loam soils. Panama disease (Foc TR4) risk is high as "
            "these are intensively managed monoculture Cavendish plantings. "
            "Use ONLY TC plantlets from certified nurseries. "
            "Bunch fill is faster (85-100 days) due to higher temperatures — manage harvest calendar carefully."
        ),
    ),
    PlantingWindow(
        region="NR IIb/III — Midlands and Masvingo Smallholder Schemes (Murewa, Mutoko, Gutu)",
        optimal_start="October 15",
        optimal_end="December 15",
        acceptable_start="October 1",
        acceptable_end="January 31",
        notes=(
            "Smallholder banana production using suckers from established mats; limited TC plantlet "
            "adoption due to cost. Plant with onset of rains to reduce irrigation dependency during "
            "establishment. Williams and Dwarf Cavendish grown for domestic and local market supply. "
            "Sucker selection critical: use sword suckers (narrow, spear-shaped leaves) not water "
            "suckers (broad leaves). Pare corm, dip in insecticide, and plant within 24 hours. "
            "Supplemental irrigation required April-October to maintain production. "
            "Black Sigatoka management is often limited to deleafing in smallholder systems — "
            "advise growers on minimum 3-weekly deleaf plus 2 fungicide applications per season. "
            "Market access (proximity to urban centres) determines economic viability."
        ),
    ),
]


PROFILE = CropProfile(
    crop_name="Banana",
    scientific_name="Musa acuminata",
    family="Musaceae",

    optimal_ph=(5.5, 7.0),
    critical_ph_low=4.8,
    optimal_soil_types=[
        "deep alluvial sandy loam (Lowveld river terraces)",
        "well-drained red-brown fersiallitic loam (Eastern Highlands)",
        "friable volcanic-origin loam",
        "well-structured clay loam with good drainage",
    ],
    avoid_soil_types=[
        "waterlogged clay (anaerobic root zone fatal to banana)",
        "shallow lithosol over hardpan",
        "heavily compacted soils",
        "saline or sodic soils (EC > 1.5 dS/m)",
        "soils with known Foc TR4 history (permanent exclusion of Cavendish)",
    ],

    optimal_temp=(22.0, 30.0),
    critical_temp_low=10.0,
    critical_temp_high=38.0,
    base_temp_gdd=14.0,
    total_water_mm=1200.0,

    growth_stages=BANANA_GROWTH_STAGES,
    fertilizer_schedule=BANANA_FERTILIZER,
    diseases=BANANA_DISEASES,
    pests=BANANA_PESTS,
    planting_windows=BANANA_PLANTING_WINDOWS,

    harvest_moisture=(
        "Harvest at 'three-quarter full' maturity (green, immature) — finger girth 38 mm minimum "
        "on outer fingers of 2nd-3rd hand. Pulp moisture at harvest approximately 74-78%. "
        "DO NOT harvest by colour change — yellowing indicates over-maturity for commercial purposes."
    ),
    storage_conditions=(
        "13-14 degC (chilling injury below 12 degC); 90-95% relative humidity. "
        "Controlled ripening with ethylene (100-150 ppm at 14-16 degC for 24-48 hours) for market. "
        "Green shelf life at 13 degC: 14-21 days for export. "
        "Avoid ethylene-generating commodities (e.g., mangoes, tomatoes) in same cool room. "
        "Domestic market: room-temperature ripening takes 5-8 days depending on maturity at harvest."
    ),
    post_harvest_notes=(
        "Harvest protocol: cut bunch peduncle with sharp, clean knife; ease bunch onto padded shoulder cradle; "
        "carry in upright position to packhouse. Latex flow from cut peduncle stains fruit — apply sawdust "
        "or sawing motion to seal cut. "
        "Export grade standards (Zimbabwe): Grade A — finger length min 20 cm, girth min 38 mm, no scarring "
        "> 2 cm2, no bruising, no angular shape; Grade B — smaller fingers or minor cosmetic blemishes; "
        "Class C — domestic/local market. "
        "Packhouse operations: de-handing (separating hands from bunch crown), trim peduncle, wash in clean "
        "water + post-harvest fungicide (thiabendazole 1 g/L or imazalil 0.5 g/L) for crown rot control, "
        "dry, grade, and pack in 13 kg or 18 kg export cartons. "
        "Crown rot (Fusarium spp., Botryodiplodia theobromae, Colletotrichum musae) is the main post-harvest "
        "disease — sterilise all de-handing tools between bunches; use clean wash water with fungicide. "
        "First commercial harvest from TC plantlets: 9-12 months after planting in Lowveld; 12-18 months "
        "in Eastern Highlands. Subsequent ratoon cycles every 10-14 months. "
        "Productivity: well-managed Williams in Lowveld: 40-60 tonnes/ha/year; Eastern Highlands: 25-40 t/ha/year; "
        "smallholder with basic management: 8-15 t/ha/year."
    ),

    natural_region_suitability={
        "I": (
            "Excellent — Eastern Highlands (Chipinge, Chimanimani) is Zimbabwe's primary banana zone; "
            "optimal humidity and temperature; Williams dominant; year-round Black Sigatoka pressure "
            "requires full spray programme; main export production area"
        ),
        "IIa": (
            "Good — Mutare valley and low-altitude Manicaland; adequate rainfall with irrigation supplement; "
            "Sigatoka management essential; frost-free sites required; some commercial production exists"
        ),
        "IIb": (
            "Moderate — marginal without supplemental irrigation in dry season; frost risk on cold highveld "
            "nights limits suitability; suitable for smallholder home-garden production in sheltered valleys"
        ),
        "III": (
            "Moderate to Good under irrigation — Midlands irrigated schemes viable; Sigatoka pressure "
            "lower than Eastern Highlands; nematode and weevil management important; good market access needed"
        ),
        "IV": (
            "Good under full irrigation — Lowveld (Triangle/Hippo Valley) is the fastest-growing commercial "
            "production zone; entirely irrigation-dependent; high temperatures accelerate growth and bunch fill; "
            "nematode/Foc TR4 vigilance critical; second most important production zone after Eastern Highlands"
        ),
        "V": (
            "Marginal — extreme heat (> 40 degC) and very high irrigation demand limit profitability; "
            "possible in Zambezi Valley with reliable irrigation but Foc risk and water cost are constraints; "
            "not recommended for commercial investment"
        ),
    },
)

ALIASES: list = ["bananas", "bhanana"]
