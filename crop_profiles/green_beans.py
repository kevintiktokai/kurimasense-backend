"""Green Beans / French Beans (Phaseolus vulgaris) — Zimbabwe's premier export legume vegetable.

Major cash crop for smallholder and commercial farmers; exported mainly to the EU under
GlobalGAP certification protocols. Varieties Amy, Bronco, and Samantha dominate export production.
Known locally as 'bhinzi' in Shona-speaking regions.
"""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List


GREEN_BEAN_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Bean Rust",
        pathogen="Uromyces appendiculatus",
        pathogen_type="fungal",
        symptoms=[
            "Small, pale yellow spots (uredia) on upper leaf surface, corresponding to "
            "red-brown pustules (urediniospores) on the lower surface",
            "Pustules rupture to release reddish-brown powdery spore masses",
            "Severely infected leaves turn yellow and drop prematurely",
            "Stem and pod infections produce elongated, darker-brown pustules",
            "Late-season black telia (overwintering spores) replace rust pustules",
        ],
        identification_markers=[
            "Brick-red to orange-brown powdery pustules on UNDERSIDE of leaves — "
            "distinguishes rust from angular leaf spot (which has angular dry lesions)",
            "Yellow halo surrounding each pustule on the upper leaf surface",
            "Pustules surrounded by a white ring of torn leaf epidermis",
            "Spores easily rub off on a finger — confirmatory test in the field",
            "Unlike powdery mildew, pustules are on the lower surface and produce "
            "coloured (not white) spores",
        ],
        favourable_conditions={
            "humidity_min": 85,
            "temp_min_c": 17,
            "temp_max_c": 27,
            "leaf_wetness_hours": 6,
            "note": (
                "Warm humid nights with dew or light rain. Optimal infection temperature "
                "18-24°C with free water for 6+ hours. Spores are wind-dispersed over long "
                "distances. Zimbabwe's Oct-Feb rainy season is peak risk period."
            ),
        },
        susceptible_stages=["vegetative", "flowering", "pod_fill"],
        resistant_varieties=["Samantha (partial resistance)", "some determinate snap bean lines"],
        susceptible_varieties=["Amy", "Bronco", "Bobby"],
        chemical_control=[
            {
                "name": "Mancozeb 80 WP",
                "rate": "2.0-2.5 kg/ha",
                "phi_days": "14",
                "notes": (
                    "Protectant dithiocarbamate; apply preventively from 21 DAE. "
                    "Repeat every 10-14 days. Cover lower leaf surfaces thoroughly."
                ),
            },
            {
                "name": "Tebuconazole 250 EW",
                "rate": "0.5-0.75 L/ha",
                "phi_days": "14",
                "notes": (
                    "DMI (triazole) fungicide; curative activity within 48h of infection. "
                    "Rotate with non-triazoles to manage resistance."
                ),
            },
            {
                "name": "Azoxystrobin 250 SC + Difenoconazole 250 EC (Amistar Top)",
                "rate": "0.5 L/ha",
                "phi_days": "14",
                "notes": (
                    "Strobilurin + triazole premix; dual mode of action reduces resistance risk. "
                    "Excellent for export programmes — max 2 applications per season."
                ),
            },
            {
                "name": "Sulphur 80 WP",
                "rate": "3.0 kg/ha",
                "phi_days": "7",
                "notes": (
                    "Cheap protectant; do not apply when temperatures exceed 30°C "
                    "(phytotoxicity risk). Useful for organic programmes."
                ),
            },
        ],
        biological_control=[
            "Bacillus subtilis QST 713 (Serenade) as preventive foliar spray",
            "Copper-based products (copper hydroxide 77 WP at 2 kg/ha) as protectant",
            "Maintain adequate potassium nutrition — K-deficient plants are more susceptible",
        ],
        cultural_control=[
            "Use certified rust-tolerant varieties where available (Samantha, Safari)",
            "Rotate with non-legume crops for minimum 2-3 seasons to reduce soilborne inoculum",
            "Avoid overhead irrigation; use drip or furrow irrigation to reduce leaf wetness",
            "Remove and burn volunteer bean plants and debris that harbour rust spores",
            "Widen row spacing to improve air circulation and reduce leaf wetness duration",
            "Scout weekly from 3 weeks after emergence; early detection is critical",
            "Avoid planting downwind of infected fields during sporulation events",
        ],
        economic_threshold=(
            "5% leaf area affected (before flowering); any pustules on pods render crop "
            "unmarketable for export — zero tolerance on pods applies"
        ),
        severity_scale={
            "mild": "Scattered pustules on lower leaves, <5% leaf area, no pod infection",
            "moderate": "10-25% leaf area affected, multiple leaves, approaching upper canopy",
            "severe": (
                ">25% leaf area or pod infection — significant yield and quality loss; "
                "export rejection likely"
            ),
        },
    ),
    DiseaseProfile(
        name="Angular Leaf Spot",
        pathogen="Phaeoisariopsis griseola (teleomorph: Mycosphaerella griseola)",
        pathogen_type="fungal",
        symptoms=[
            "Angular, water-soaked lesions on leaves delimited by leaf veins — "
            "characteristic diagnostic shape",
            "Lesions turn grey-brown to dark brown with a yellow halo as they mature",
            "On pods: elongated, dark brown to black, slightly sunken lesions with "
            "water-soaked margins",
            "Pod lesions penetrate through to seeds causing seed discolouration",
            "Stems develop elongated dark brown streaks, especially at nodes",
            "Severe infections cause premature defoliation",
        ],
        identification_markers=[
            "Angular lesion shape confined by leaf veins — most reliable field diagnostic",
            "Grey sporulation (conidia) visible on lesion surface under humid conditions "
            "(use hand lens, 10×)",
            "Lesions turn grey-white on upper surface vs. darker on underside",
            "Angular spots differ from rust (round pustules) and common bacterial blight "
            "(water-soaked, no angular boundary in early stages)",
        ],
        favourable_conditions={
            "humidity_min": 80,
            "temp_min_c": 16,
            "temp_max_c": 28,
            "leaf_wetness_hours": 4,
            "note": (
                "Warm, wet conditions with high humidity. Seed-borne and residue-borne. "
                "High pathogen variability — over 300 pathotypes identified globally. "
                "Zimbabwe's rainy season creates ideal conditions Oct-March."
            ),
        },
        susceptible_stages=["vegetative", "flowering", "pod_fill"],
        resistant_varieties=["Some CIMMYT lines", "Samantha (moderate tolerance)"],
        susceptible_varieties=["Amy", "Bronco (highly susceptible in wet seasons)"],
        chemical_control=[
            {
                "name": "Chlorothalonil 500 SC",
                "rate": "2.0 L/ha",
                "phi_days": "14",
                "notes": (
                    "Broad-spectrum protectant; apply at first sign of disease and repeat "
                    "every 10-14 days. Key product in Zimbabwe export programmes."
                ),
            },
            {
                "name": "Mancozeb 80 WP",
                "rate": "2.0-2.5 kg/ha",
                "phi_days": "14",
                "notes": "Alternate with chlorothalonil to prevent resistance buildup.",
            },
            {
                "name": "Copper Oxychloride 50 WP",
                "rate": "2.5-3.0 kg/ha",
                "phi_days": "7",
                "notes": (
                    "Provides some curative activity; useful in wet periods. "
                    "Copper residues must be managed for EU MRL compliance."
                ),
            },
        ],
        biological_control=[
            "Use certified disease-free seed — primary management strategy",
            "Hot-water seed treatment (52°C for 30 minutes) to reduce seed-borne inoculum",
            "Trichoderma-based soil amendments to reduce residue-borne inoculum",
        ],
        cultural_control=[
            "Source certified disease-free seed — seed-borne transmission is primary inoculum source",
            "Treat seed with captan or thiram before planting (3 g/kg seed)",
            "Rotate with non-legumes for 2-3 years (residue-borne pathogen persists 1-2 seasons)",
            "Deep plough to bury infected crop residues after harvest",
            "Remove infected plant debris from field margins",
            "Avoid working in fields when plants are wet — mechanical spread on tools and clothing",
            "Adequate spacing (5-7 cm in-row, 60-75 cm between rows) improves canopy aeration",
        ],
        economic_threshold=(
            "10% plants with foliar symptoms at vegetative stage; "
            "any pod lesions in export crops — zero tolerance applies at grading"
        ),
        severity_scale={
            "mild": "Scattered angular spots on lower leaves, no pod infection, <10% leaf area",
            "moderate": "25-40% leaf area with symptoms, early pod lesions appearing",
            "severe": (
                ">40% leaf area affected, extensive pod lesions, premature defoliation — "
                "crop unsalvageable for export"
            ),
        },
    ),
    DiseaseProfile(
        name="Anthracnose",
        pathogen="Colletotrichum lindemuthianum",
        pathogen_type="fungal",
        symptoms=[
            "Dark brown to black sunken lesions on pods — most diagnostic symptom",
            "Lesions enlarge and produce salmon-pink to orange spore masses (acervuli) "
            "under humid conditions",
            "On leaves: dark brown lesions along veins (vein necrosis) on underside",
            "Seed infection: dark brown to black discolouration of seed coat",
            "Seedling blight from infected seed: dark streaks on cotyledons and hypocotyl",
            "Stem cankers at soil level in severe cases",
        ],
        identification_markers=[
            "Sunken, dark pod lesions with salmon-pink sporulation under humidity — "
            "the key field identifier",
            "Dark vein necrosis on leaf undersides (not upper surface)",
            "Acervuli (spore-bearing structures) appear as orange-pink pustules — "
            "different from rust (brown powdery) and bacterial blight (water-soaked)",
            "Seed coat discolouration and reduced germination from infected seed lots",
        ],
        favourable_conditions={
            "humidity_min": 92,
            "temp_min_c": 13,
            "temp_max_c": 26,
            "leaf_wetness_hours": 12,
            "note": (
                "Cool to warm, very wet conditions. Optimal 17°C with prolonged wetness. "
                "Primary inoculum from infected seed; secondary spread by rain splash and "
                "contact. Zimbabwe's high-humidity season (Nov-Feb) most risky."
            ),
        },
        susceptible_stages=["seedling", "flowering", "pod_fill"],
        resistant_varieties=["Jalo EEP558", "AND 277 (research lines)"],
        susceptible_varieties=["Amy", "Bronco", "Samantha (moderate susceptibility)"],
        chemical_control=[
            {
                "name": "Thiram 80 WP seed treatment",
                "rate": "3 g/kg seed",
                "phi_days": "N/A (seed treatment)",
                "notes": (
                    "Essential first line of defence — reduces seed-borne inoculum. "
                    "Apply 24h before planting and allow to dry."
                ),
            },
            {
                "name": "Carbendazim 500 SC",
                "rate": "0.5 L/ha",
                "phi_days": "14",
                "notes": (
                    "Systemic benzimidazole; apply at pod set and repeat 10-14 days later. "
                    "Note: resistance to benzimidazoles is widespread — monitor efficacy."
                ),
            },
            {
                "name": "Azoxystrobin 250 SC",
                "rate": "0.4 L/ha",
                "phi_days": "7",
                "notes": (
                    "Excellent pod protection; apply preventively from flowering. "
                    "Max 2 strobilurin applications per season."
                ),
            },
            {
                "name": "Iprodione 500 SC",
                "rate": "1.0-1.5 L/ha",
                "phi_days": "7",
                "notes": "Dicarboximide; effective against early pod lesions.",
            },
        ],
        biological_control=[
            "Hot-water seed treatment (52°C, 30 min) eliminates seed-borne inoculum",
            "Trichoderma harzianum seed treatment (biopriming) to protect seedlings",
            "Bacillus amyloliquefaciens foliar spray as preventive measure",
        ],
        cultural_control=[
            "Use certified disease-free or hot-water treated seed — CRITICAL first step",
            "Avoid overhead irrigation; direct water to soil not foliage",
            "Do not work in fields when plants are wet — human and equipment spread",
            "Remove and destroy infected plants immediately",
            "Rotate with cereals or brassicas for 2-3 years; avoid legume-legume rotation",
            "Incorporate crop residues deeply by ploughing after harvest",
            "Use raised beds to improve drainage and reduce splash dispersal",
        ],
        economic_threshold=(
            "5% pods with lesions — export programmes require zero pod lesion tolerance. "
            "Act at first foliar symptoms; do not wait for pod infection."
        ),
        severity_scale={
            "mild": "Vein lesions on lower leaves, no pod infection, <10% plants affected",
            "moderate": "Pod lesions on 5-20% pods, seed discolouration risk",
            "severe": (
                ">20% pods affected with salmon sporulation — entire crop rejected for export; "
                "seed crop completely unsalvageable"
            ),
        },
    ),
    DiseaseProfile(
        name="Common Bacterial Blight",
        pathogen="Xanthomonas axonopodis pv. phaseoli",
        pathogen_type="bacterial",
        symptoms=[
            "Irregular, water-soaked leaf lesions that enlarge to form large necrotic "
            "brown areas with narrow yellow margins",
            "Infected leaf tissue dries and turns papery brown — 'scorch' appearance",
            "Water-soaked, greasy pod lesions that turn red-brown to dark brown",
            "Bacterial ooze (dried yellow crust) on pod lesions under humid conditions",
            "Stem lesions produce cankers that can girdle the stem",
            "Seed infection: discoloured, shrunken seeds with yellow to brown blotches",
        ],
        identification_markers=[
            "Wide yellow border (halo) around necrotic leaf lesions — most distinguishing feature "
            "vs. angular leaf spot (angular boundary) and rust (pustules)",
            "Water-soaked greasy pod lesions that ooze bacterial exudate",
            "Symptoms spread rapidly from infected seed or following wet weather",
            "Lesions do not follow vein pattern (unlike angular leaf spot)",
            "Yellow exudate dries to form a crust on pod lesions",
        ],
        favourable_conditions={
            "humidity_min": 80,
            "temp_min_c": 28,
            "temp_max_c": 32,
            "note": (
                "Hot, humid conditions above 28°C are optimal — common in Zimbabwe's lowveld "
                "and during hot spells in the rainy season. Spread by rain splash, irrigation, "
                "insects, and contaminated tools. Survives in seed for 2+ years."
            ),
        },
        susceptible_stages=["vegetative", "flowering", "pod_fill"],
        resistant_varieties=["XAN 159", "ICN 103 (CIMMYT materials)"],
        susceptible_varieties=["Amy", "Bronco", "Samantha (moderate to highly susceptible)"],
        chemical_control=[
            {
                "name": "Copper Oxychloride 50 WP",
                "rate": "2.5-3.0 kg/ha",
                "phi_days": "7",
                "notes": (
                    "Bactericidal; preventive and early curative. Apply at first sign or when "
                    "wet weather forecast. Repeat every 7 days during high-risk periods. "
                    "Monitor copper MRL for EU market compliance."
                ),
            },
            {
                "name": "Streptomycin sulphate (where locally registered)",
                "rate": "100-200 g/ha",
                "phi_days": "14",
                "notes": (
                    "Antibiotic bactericide; restricted use in many markets. "
                    "NOT permitted on EU-destined crops. Use only for domestic market."
                ),
            },
            {
                "name": "Copper Hydroxide 77 WP (Kocide)",
                "rate": "2.0 kg/ha",
                "phi_days": "7",
                "notes": "Fixed copper; better redistribution than copper oxychloride in rain.",
            },
        ],
        biological_control=[
            "Hot-water seed treatment (55°C for 15 minutes) to eliminate seed-borne bacteria",
            "Bacillus subtilis-based products as preventive bactericide",
            "Plant extracts (neem, garlic) have limited but supporting bacteriostatic activity",
        ],
        cultural_control=[
            "Use certified, disease-free seed — MOST IMPORTANT management step",
            "Treat seed with copper-based product before planting",
            "Avoid overhead irrigation; bacteria spread prolifically via water splash",
            "Disinfect tools, stakes, and equipment with 10% bleach or 70% alcohol solution",
            "Remove and destroy infected plants to reduce inoculum build-up",
            "Avoid entering fields when plants are wet — boots and clothing spread bacteria",
            "Rotate with non-legume crops for minimum 3 years; bacteria survive in soil and debris",
            "Select well-drained fields with good air circulation",
        ],
        economic_threshold=(
            "Any bacterial blight on pods in export crops — zero tolerance. "
            "Foliar: act at first confirmed symptoms; do not wait for spread."
        ),
        severity_scale={
            "mild": "Scattered leaf lesions, yellow halo visible, no pod infection",
            "moderate": "10-30% leaf area, approaching upper canopy, early pod symptoms",
            "severe": (
                ">30% leaf area affected, pod lesions with exudate — export crop condemned; "
                "significant yield and seed quality loss"
            ),
        },
    ),
]


GREEN_BEAN_PESTS: List[PestProfile] = [
    PestProfile(
        name="Bean Fly (Bean Stem Maggot)",
        scientific_name="Ophiomyia phaseoli",
        pest_type="insect",
        identification=[
            "Adult: small (2 mm), shiny black fly resembling a small housefly",
            "Larvae: white to cream-coloured maggots (up to 5 mm) mining inside stems",
            "Puparia: dark brown, barrel-shaped, found at the stem base just above or "
            "below the soil surface",
            "Adult feeding punctures: tiny white dots on young leaves (oviposition scars)",
            "Stem base swells and splits where larvae tunnel — characteristic gall-like lesion",
        ],
        damage_symptoms=[
            "SEEDLING STAGE: most critical — swollen, cracked, rotting stem base "
            "(hypocotyl); plant wilts and collapses ('damping-off-like' but with maggot present)",
            "Yellow patches on cotyledons from adult feeding punctures",
            "Mining damage visible as brown streaks in the hypocotyl when split open",
            "Older plants: yellow, stunted growth with root and stem base damage",
            "Secondary rot organisms (Fusarium, Pythium) enter through stem wounds",
            "Stand gaps from plant death are most visible symptom at field level",
        ],
        life_cycle_notes=(
            "Complete life cycle in 18-25 days at 25°C. Female lays 30-50 eggs singly into "
            "leaf tissue (epidermal mining). Larvae migrate from leaves down the petiole into "
            "the hypocotyl. Three larval instars; pupation at stem base in soil. Adults emerge "
            "and immediately mate. Polyvoltine: 10-12 generations per year in Zimbabwe. "
            "Most damaging from emergence to 14 days after planting — the critical window."
        ),
        favourable_conditions={
            "temp_min_c": 20,
            "temp_max_c": 30,
            "note": (
                "Warm, humid conditions. Populations are highest in the rainy season "
                "(Nov-Feb) in Zimbabwe. Early plantings (Oct) before natural enemy build-up "
                "are particularly vulnerable. Dry warm conditions between rains also favour "
                "adult activity."
            ),
        },
        susceptible_stages=["emergence", "vegetative"],
        economic_threshold=(
            "1-2 larvae per plant at emergence stage (seedlings highly sensitive); "
            "1 exit hole per 10 plants. Seedling stand loss >10% requires replanting."
        ),
        chemical_control=[
            {
                "name": "Thiamethoxam 35 FS seed treatment (Cruiser)",
                "rate": "7 mL/kg seed",
                "phi_days": "N/A (seed treatment)",
                "notes": (
                    "MOST EFFECTIVE management — systemic seed dressing protects seedlings "
                    "for 3-4 weeks post-emergence. Standard practice on all export bean "
                    "programmes in Zimbabwe. Check GlobalGAP compliance status."
                ),
            },
            {
                "name": "Imidacloprid 600 FS seed treatment (Gaucho)",
                "rate": "5-7 mL/kg seed",
                "phi_days": "N/A (seed treatment)",
                "notes": (
                    "Alternative neonicotinoid seed treatment; effective for 3 weeks. "
                    "Apply as slurry treatment 24h before planting."
                ),
            },
            {
                "name": "Chlorpyrifos 480 EC",
                "rate": "1.5-2.0 L/ha",
                "phi_days": "21",
                "notes": (
                    "Soil drench at planting or foliar spray at emergence; "
                    "targets adults on foliage. NOT suitable close to harvest — observe PHI. "
                    "EU market: check MRL status before applying."
                ),
            },
            {
                "name": "Dimethoate 400 EC",
                "rate": "0.75-1.0 L/ha",
                "phi_days": "14",
                "notes": (
                    "Systemic organophosphate; apply as foliar at first adult activity. "
                    "Limited residual activity — repeat weekly during high-pressure periods."
                ),
            },
        ],
        biological_control=[
            "Parasitoid wasp Gronotoma micromorpha parasitises larvae — preserve by avoiding "
            "broad-spectrum insecticides",
            "Entomopathogenic nematodes (Steinernema feltiae) applied as soil drench at "
            "planting target pupae in soil",
            "Beauveria bassiana foliar spray targets adults on leaves",
            "Avoid calendar spraying — use seed treatment + scouting-based interventions",
        ],
        cultural_control=[
            "SEED TREATMENT is the single most effective practice — insist on treated seed",
            "Plant at correct depth (3-4 cm) and ensure uniform germination to reduce "
            "vulnerable seedling period",
            "Early planting in the season to avoid peak fly populations",
            "Deep ploughing before planting exposes and kills pupae in the soil",
            "Remove and destroy previous bean crop residues — adults breed in debris",
            "Intercropping with maize or sorghum can reduce fly landing rates",
            "Avoid late planting which extends the vulnerable seedling window",
        ],
        scouting_protocol=(
            "Begin scouting at EMERGENCE (day 3-5). Scout 20 plants in a W-pattern. "
            "Check for adult feeding punctures (white dots on cotyledons) and wilting. "
            "If suspicious, uproot wilted plants and split stem at base — maggots confirm "
            "bean fly. Count stand gaps per 10 m row. Scout daily for first 14 days. "
            "Use yellow sticky traps at soil level to monitor adult emergence."
        ),
    ),
    PestProfile(
        name="Aphids (Black Bean Aphid)",
        scientific_name="Aphis fabae",
        pest_type="insect",
        identification=[
            "Small (2-3 mm), soft-bodied, shiny black to dark olive-green aphids",
            "Dense colonies on growing tips, underside of young leaves, and flower buds",
            "White cast skins (exuviae) visible on leaves and pods below colonies",
            "Winged (alate) forms appear when colonies become crowded — key dispersal stage",
            "Attend by ants which actively protect colonies from predators",
        ],
        damage_symptoms=[
            "Curled, distorted growing tips and young leaves — reduced plant vigour",
            "Sticky honeydew deposits on pods and leaves, leading to black sooty mould growth",
            "Sooty mould on pods renders them unmarketable for export",
            "Reduced pod set and smaller pods from feeding during flowering",
            "Vector of Bean Common Mosaic Virus (BCMV) and Bean Yellow Mosaic Virus (BYMV) — "
            "virus transmission in a non-persistent manner (brief feeding events)",
            "High populations during pod fill can cause direct pod distortion",
        ],
        life_cycle_notes=(
            "Parthenogenetic reproduction — females produce live young without mating "
            "in warm conditions. One generation completed in 7-10 days at 20-25°C. "
            "Overwinters as eggs on spindle/euonymus (primary host); migrates to beans "
            "(secondary host) from September onward in Zimbabwe. Populations can double "
            "in 3-4 days under optimal conditions. Peak infestations occur Oct-Jan in "
            "Zimbabwe during establishment of rainy season crops."
        ),
        favourable_conditions={
            "temp_min_c": 18,
            "temp_max_c": 26,
            "note": (
                "Moderate temperatures and low rainfall/humidity favour rapid population "
                "buildup. Populations are suppressed by heavy rain (physical knockdown) "
                "and temperatures above 30°C. Dry periods between rains create outbreak "
                "conditions. Excessive nitrogen promotes succulent growth attractive to aphids."
            ),
        },
        susceptible_stages=["vegetative", "flowering", "pod_fill"],
        economic_threshold=(
            "30-50 aphids per plant, or 10 per growing tip; "
            "any honeydew/sooty mould on pods — export zero-tolerance on pod contamination"
        ),
        chemical_control=[
            {
                "name": "Pirimicarb 50 WG (Pirimor)",
                "rate": "250 g/ha",
                "phi_days": "7",
                "notes": (
                    "Selective carbamate aphicide — does NOT affect most natural enemies. "
                    "Preferred product in export programmes for IPM compatibility. "
                    "Systemic and contact activity."
                ),
            },
            {
                "name": "Acetamiprid 20 SP",
                "rate": "100-150 g/ha",
                "phi_days": "7",
                "notes": (
                    "Neonicotinoid; very effective against aphids including resistant strains. "
                    "Avoid during flowering if bee activity present. "
                    "Check EU MRL status."
                ),
            },
            {
                "name": "Dimethoate 400 EC",
                "rate": "0.5-0.75 L/ha",
                "phi_days": "14",
                "notes": "Systemic organophosphate; observe PHI strictly for export.",
            },
            {
                "name": "Pymetrozine 50 WG (Chess)",
                "rate": "200 g/ha",
                "phi_days": "7",
                "notes": (
                    "Novel mode of action (feeding inhibitor); selective, safe to beneficials. "
                    "Excellent resistance management tool."
                ),
            },
        ],
        biological_control=[
            "Coccinellidae (ladybird beetles) — adults and larvae consume 20-50 aphids/day",
            "Parasitoid wasp Aphidius colemani (mummified aphids — swollen bronze bodies "
            "— indicate parasitism; do not spray when >15% aphids are mummified)",
            "Lacewing larvae (Chrysoperla spp.) — voracious aphid predators",
            "Syrphid fly larvae (hoverflies) — important natural enemies in bean fields",
            "Entomopathogenic fungi Beauveria bassiana and Lecanicillium lecanii under "
            "conditions of high humidity",
        ],
        cultural_control=[
            "Monitor weekly from crop emergence — detect colonies before they establish",
            "Avoid excessive nitrogen fertiliser — succulent growth attracts and sustains aphids",
            "Use reflective silver/aluminium mulches to deter alate aphids from landing",
            "Remove weed hosts (Chenopodiaceae, Asteraceae) from field margins",
            "Ant control around field perimeter reduces ant-aphid mutualism",
            "Avoid dense planting that reduces natural enemy access to colonies",
        ],
        scouting_protocol=(
            "Scout 20 plants in a W-pattern twice weekly from emergence. "
            "Check growing tip and 3 youngest leaves per plant. "
            "Count aphids per tip; record natural enemy presence (ladybirds, mummies, lacewings). "
            "Only spray if threshold exceeded AND beneficial:pest ratio is below 1:25. "
            "Use yellow sticky traps at crop canopy height for alate monitoring."
        ),
    ),
    PestProfile(
        name="American Bollworm (Tomato Fruit Worm)",
        scientific_name="Helicoverpa armigera",
        pest_type="insect",
        identification=[
            "Adult: medium-sized moth (35-40 mm wingspan), straw-yellow to olive-brown; "
            "hindwings pale with dark border",
            "Eggs: tiny (0.5 mm), dome-shaped, ribbed, creamy-white; laid singly on young "
            "leaves, flowers, and developing pods",
            "Larvae (caterpillars): variable colour — green, pink, brown, or striped; "
            "3-4 cm at maturity; pale lateral stripes; microspines on body (diagnostic feature "
            "under hand lens)",
            "Pupae: in soil, reddish-brown, 1.5-2 cm",
        ],
        damage_symptoms=[
            "Larvae bore into pods, feeding on developing seeds — most economically damaging stage",
            "Entry hole in pod often plugged with frass (excrement); internal cavity with "
            "seed damage",
            "Pod bore-holes render pods completely unmarketable — export zero tolerance",
            "Young larvae initially feed on flowers (bud drop) before moving to pods",
            "Window-frame feeding on young leaves by early instar larvae (minor)",
            "Pod entry holes allow secondary fungal and bacterial rot",
        ],
        life_cycle_notes=(
            "Complete life cycle in 30-40 days. Female lays 500-2000 eggs singly over "
            "10-14 days. Eggs hatch in 3-5 days. Six larval instars (18-25 days total). "
            "Pupation in soil 5-10 cm deep (14-20 days). Adults are migratory — long-distance "
            "movement is common, leading to sudden population increases. Polyphagous: attacks "
            "maize, tobacco, tomatoes, sorghum, cotton — all common in Zimbabwe. "
            "Multi-voltine: 4-6 generations per year in Zimbabwe."
        ),
        favourable_conditions={
            "temp_min_c": 20,
            "temp_max_c": 35,
            "note": (
                "Warm conditions; populations peak during flowering and pod fill of beans. "
                "Pest pressure highest Oct-Feb in Zimbabwe, coinciding with main bean season. "
                "Migration from senescing maize and tobacco crops brings adults into bean fields."
            ),
        },
        susceptible_stages=["flowering", "pod_fill"],
        economic_threshold=(
            "1-2 eggs per plant during flowering; any larvae on pods = action threshold "
            "for export (zero tolerance on pod damage at grading)"
        ),
        chemical_control=[
            {
                "name": "Emamectin Benzoate 1.9 EC (Proclaim)",
                "rate": "300-500 mL/ha",
                "phi_days": "3",
                "notes": (
                    "Macrolide; excellent larval activity, short PHI — preferred for "
                    "export bean programmes. Apply at egg hatch / early instar. "
                    "Alternation essential — resistance can develop rapidly."
                ),
            },
            {
                "name": "Spinosad 240 SC (Tracer)",
                "rate": "200-300 mL/ha",
                "phi_days": "3",
                "notes": (
                    "Naturalyte; excellent efficacy on young larvae; low mammalian toxicity. "
                    "Short PHI makes it ideal near harvest. Max 3 applications per season "
                    "to manage resistance."
                ),
            },
            {
                "name": "Chlorantraniliprole 200 SC (Coragen)",
                "rate": "150-200 mL/ha",
                "phi_days": "3",
                "notes": (
                    "Diamide insecticide; long residual activity (14-21 days). "
                    "Excellent for prevention and early control. Premium product suited "
                    "to export markets due to short PHI and favourable residue profile."
                ),
            },
            {
                "name": "Deltamethrin 25 EC",
                "rate": "0.3-0.5 L/ha",
                "phi_days": "7",
                "notes": (
                    "Pyrethroid; cost-effective but broad-spectrum — disrupts natural enemies. "
                    "Use only in severe outbreaks away from beneficial peaks."
                ),
            },
        ],
        biological_control=[
            "Helicoverpa NPV (Nuclear Polyhedrosis Virus) — apply at egg hatch, target "
            "early instar larvae; very selective, compatible with IPM",
            "Bacillus thuringiensis var. kurstaki (Bt) — apply at egg hatch; effective "
            "only on young larvae (1st-2nd instar)",
            "Trichogramma egg parasitoids — mass release at 200,000/ha at egg-laying period",
            "Chrysoperla carnea lacewing larvae — predator of eggs and young larvae",
            "Campoletis chlorideae and Microplitis mediator — larval parasitoids (preserve "
            "by avoiding broad-spectrum sprays)",
            "Pheromone traps (Helilure) for adult monitoring and mass trapping in large areas",
        ],
        cultural_control=[
            "Scout twice weekly from pre-flowering using pheromone traps and egg scouting",
            "Rotate with non-host crops to break bollworm breeding cycles",
            "Destroy crop residues immediately after harvest to prevent pupation",
            "Deep ploughing after harvest exposes pupae to desiccation and bird predation",
            "Avoid planting adjacent to maturing maize, tobacco, or tomato fields",
            "Use pheromone traps (Helilure) for monitoring: 2 traps per 5 ha field",
        ],
        scouting_protocol=(
            "Place pheromone traps before flowering — threshold 5 moths/trap/night indicates "
            "local population buildup. Scout 50 plants per ha twice weekly during flowering: "
            "check flowers, buds, and young pods for eggs and young larvae. "
            "Carefully inspect pod surface for entry holes and frass. "
            "Apply control measures within 48h of threshold being reached."
        ),
    ),
    PestProfile(
        name="Whitefly",
        scientific_name="Bemisia tabaci (Tobacco Whitefly / Silverleaf Whitefly)",
        pest_type="insect",
        identification=[
            "Adult: tiny (1-2 mm), white powdery wings, yellow-bodied; flies up in a cloud "
            "when plant is disturbed",
            "Eggs: pale yellow, oval, 0.2 mm; laid on leaf underside in circular or "
            "horseshoe patterns",
            "Nymphs: flat, scale-like, transparent to yellow-green on leaf underside "
            "(4 instars before adult)",
            "Puparium (4th instar/pseudo-pupa): pale yellow, oval, slightly raised — "
            "diagnostic shape varies by Bemisia vs. Trialeurodes",
            "Distinguish Bemisia (held wings flat, roof-like) from Trialeurodes (wings "
            "held at angle)",
        ],
        damage_symptoms=[
            "Direct sap-sucking causes yellowing, leaf curl, and premature senescence",
            "Honeydew excretion leads to black sooty mould on pods — key export-quality issue",
            "Vector of Bean Leaf Curl Virus and other begomoviruses — "
            "B. tabaci is the primary vector; virus transmission can cause severe stunting",
            "Silverleaf syndrome (physiological disorder) in some plant species",
            "Pod contamination with honeydew and sooty mould requires washing — "
            "adds packhouse cost and may still fail export inspection",
        ],
        life_cycle_notes=(
            "Complete cycle in 18-30 days at 25°C. Females lay 100-300 eggs over 2 weeks. "
            "Development highly temperature-dependent; rapid generations in warm conditions. "
            "B. tabaci is polyphagous across 600+ plant species. High insecticide resistance "
            "documented to neonicotinoids and pyrethroids in Zimbabwe populations. "
            "Populations peak during dry, hot periods (Aug-Oct in Zimbabwe) but can build "
            "rapidly under irrigation any time."
        ),
        favourable_conditions={
            "temp_min_c": 25,
            "temp_max_c": 38,
            "note": (
                "Hot, dry conditions strongly favour population buildup. Whiteflies are "
                "suppressed by heavy rain but thrive under irrigation in dry conditions. "
                "Common in export bean production areas (Karoi, Mazowe, Rusape) during "
                "dry season production."
            ),
        },
        susceptible_stages=["vegetative", "flowering", "pod_fill"],
        economic_threshold=(
            "10 adults per leaf or any nymphal colony on pods; sooty mould on pods "
            "= immediate action in export crops"
        ),
        chemical_control=[
            {
                "name": "Spiromesifen 240 SC (Oberon)",
                "rate": "0.75-1.0 L/ha",
                "phi_days": "3",
                "notes": (
                    "Ketoenol; targets eggs and nymphs (not adults). "
                    "Excellent resistance management tool. Short PHI suits export. "
                    "Apply to underside of leaves for contact with nymphs."
                ),
            },
            {
                "name": "Pyriproxyfen 100 EC (Sumitomo Admiral)",
                "rate": "0.75 L/ha",
                "phi_days": "7",
                "notes": (
                    "Insect Growth Regulator (juvenile hormone analogue); disrupts "
                    "nymph development and adult reproduction. Long residual effect."
                ),
            },
            {
                "name": "Buprofezin 25 WP",
                "rate": "1.0-1.5 kg/ha",
                "phi_days": "14",
                "notes": "Chitin synthesis inhibitor; suppresses nymphs over 2-3 weeks.",
            },
            {
                "name": "Flupyradifurone 200 SL (Sivanto)",
                "rate": "0.75 L/ha",
                "phi_days": "7",
                "notes": (
                    "Butenolide; novel neonicotinoid-like mode of action with improved "
                    "bee safety profile. Effective where neonicotinoid resistance is present."
                ),
            },
        ],
        biological_control=[
            "Encarsia formosa parasitoid wasp (primarily for protected/greenhouse production)",
            "Eretmocerus eremicus — effective in open field conditions at higher temperatures",
            "Beauveria bassiana and Isaria fumosorosea — entomopathogenic fungi effective "
            "under high humidity; spray undersides of leaves",
            "Paecilomyces lilacinus as preventive inoculant under dry-season pressure",
        ],
        cultural_control=[
            "Yellow sticky traps at crop canopy height for early warning (5 traps/ha minimum)",
            "Remove weed hosts (especially Solanaceae, Cucurbitaceae) from around fields",
            "Avoid planting adjacent to tobacco, tomato, or cucurbit crops",
            "Use reflective silver mulch to deter adult landing and reduce virus spread",
            "Apply foliar potassium silicate — increases leaf structural resistance",
            "Proper irrigation management — water-stressed plants are more susceptible",
        ],
        scouting_protocol=(
            "Inspect 25 plants across the field twice weekly. "
            "Count adults (disturb plant, count flying insects) and examine leaf undersides "
            "for nymph colonies and sooty mould. Yellow sticky traps at canopy height: "
            "record counts twice weekly — >20 adults per trap/day signals population buildup. "
            "Rotate spray modes of action every application to manage resistance."
        ),
    ),
]


GREEN_BEAN_GROWTH_STAGES: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Germination & Emergence",
        stage_code="GE",
        day_range=(0, 14),
        water_kc=0.4,
        water_mm_per_week=18,
        critical_nutrients=["Phosphorus", "Molybdenum", "Zinc"],
        key_activities=[
            "Direct seed at 3-4 cm depth; 5-7 cm in-row spacing, 60-75 cm between rows",
            "Apply Rhizobium phaseoli inoculant to seed immediately before planting "
            "(slurry method using diluted sugar solution as sticker)",
            "Apply basal Compound L fertiliser at planting in a band 5 cm below and "
            "5 cm to the side of the seed row to avoid seed burn",
            "Thiamethoxam or imidacloprid seed dressing for bean fly protection — non-negotiable",
            "Fungicide seed treatment (thiram or captan) to protect against seedling diseases",
            "Ensure good seedbed tilth: fine, firm seedbed for uniform germination",
            "Irrigate to bring soil to field capacity before planting on drip systems",
        ],
        risks=[
            "Bean fly (Ophiomyia phaseoli) — #1 risk in Zimbabwe during this stage",
            "Damping-off from Pythium and Rhizoctonia in wet, cold soils",
            "Poor germination from seed placed too deep or in dry soil",
            "Seed rot from excess moisture combined with pathogen pressure",
            "Bird damage (doves, queleas) on germinating seeds",
        ],
        scientific_notes=(
            "Phaseolus vulgaris has epigeal germination — cotyledons emerge above ground "
            "and are green and photosynthetically active. Optimal soil temperature for "
            "germination is 20-30°C; emergence is rapid (5-7 days) at 25°C. Phosphorus is "
            "critical for early root and nodule development. Rhizobium inoculation provides "
            "the foundation for biological nitrogen fixation — the inoculant must contain "
            "the correct strain (Rhizobium leguminosarum bv. phaseoli or Rhizobium tropici). "
            "Nodule formation begins within 7-10 days of emergence in inoculated soils."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Vegetative Growth",
        stage_code="VG",
        day_range=(14, 35),
        water_kc=0.7,
        water_mm_per_week=30,
        critical_nutrients=["Nitrogen (early, before nodules active)", "Phosphorus", "Potassium", "Iron"],
        key_activities=[
            "Weed control at 14-21 days — beans are poor competitors; hand-weed or "
            "apply pre-emergence herbicide (metolachlor) at planting",
            "Scout for bean fly damage on stem base; check for swelling, cracks, or "
            "wilting — immediate replacement planting if >10% stand loss",
            "Scout for aphid colonies on growing tips twice weekly",
            "Check nodule development on roots at 21 days: pink/red nodules = active N-fixation; "
            "white/green nodules = inactive (may need supplementary N)",
            "Apply light Ammonium Nitrate top dress if nodules appear inactive",
            "Begin disease monitoring programme (angular leaf spot, rust)",
        ],
        risks=[
            "Weed competition (Galinsoga, Digitaria, Cyperus species in Zimbabwe)",
            "Aphid population buildup on succulent young growth",
            "Iron chlorosis on alkaline soils (pH >7)",
            "Late bean fly emergence from soil pupae",
        ],
        scientific_notes=(
            "Primary trifoliate leaves unfold 14-18 days after planting; compound trifoliate "
            "nodes continue to develop. The first true trifoliate marks the shift from "
            "heterotrophic (seed-fed) to autotrophic (photosynthesis-based) nutrition. "
            "Nitrogen fixation accelerates from day 20-25 when nodules become fully functional. "
            "Critical to maintain adequate soil moisture during root penetration phase "
            "(soil compaction or waterlogging at this stage significantly reduces final yield). "
            "Phosphorus uptake is highest during this period — P must be available in the "
            "rhizosphere."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Flowering",
        stage_code="FL",
        day_range=(35, 50),
        water_kc=0.85,
        water_mm_per_week=38,
        critical_nutrients=["Potassium", "Boron", "Calcium", "Phosphorus"],
        key_activities=[
            "Maintain consistent, uniform irrigation — water stress during flowering "
            "causes flower abortion (French beans are highly sensitive)",
            "Apply foliar boron (Solubor 1 kg/ha) at first flower open — critical for "
            "pollen tube growth and fertilisation",
            "Scout for thrips in flowers (tap flowers over white paper; use hand lens)",
            "Scout for American bollworm eggs on leaves and flower buds",
            "Inspect flowers for signs of grey mould (Botrytis) in wet, cool conditions",
            "Begin full pest and disease spray programme as per export protocol",
            "Apply foliar calcium if blossom-end rot risk is present",
        ],
        risks=[
            "Water stress causing flower drop — most critical risk to pod set",
            "American bollworm (Helicoverpa armigera) egg-laying and larval damage to flowers",
            "Thrips scarring on petals leading to pod distortion",
            "Boron deficiency causing poor pod set (common on sandy soils in Zimbabwe)",
            "High temperature (>30°C) reducing pollen viability",
        ],
        scientific_notes=(
            "Phaseolus vulgaris is self-pollinating (cleistogamous) but insect visitation "
            "increases pod set by 15-30%. Flowers are borne in racemes at leaf axils. "
            "Each inflorescence bears 2-8 flowers; only 1-3 typically set pods. "
            "Flower initiation and pod set are the most water-sensitive stages in the crop "
            "calendar — a 3-day water deficit during early flowering can reduce pod set by "
            "40-60%. Boron is essential for pollen tube elongation and pollen germination on "
            "the stigma. Temperature above 30°C during anthesis reduces pollen viability and "
            "causes abscission. Potassium is critical for osmoregulation and sugar transport "
            "to developing pods."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Pod Development (Pod Fill)",
        stage_code="PD",
        day_range=(50, 65),
        water_kc=0.95,
        water_mm_per_week=42,
        critical_nutrients=["Potassium", "Calcium", "Nitrogen (maintenance)"],
        key_activities=[
            "Begin scouting for first harvestable pods at day 50-55 (export variety dependent)",
            "Maintain full irrigation — pod fill is the second highest water demand stage",
            "Scout intensively for bollworm larvae and pod entry damage",
            "Inspect pods for disease lesions (angular leaf spot, anthracnose, bacterial blight)",
            "Maintain cold chain planning: pre-book packhouse and refrigerated transport",
            "Apply potassium foliar feed (0-0-50 SOP at 2 kg/ha) to improve pod quality",
            "Check pod straightness and colour — key export grade parameters",
        ],
        risks=[
            "American bollworm pod boring — economic damage can be severe if uncontrolled",
            "Angular leaf spot pod lesions — zero export tolerance",
            "Anthracnose pod lesions — most visible at grading",
            "Water deficit causing pod puckering and reduced pod size",
            "Excessive rainfall causing waterlogging and root stress",
        ],
        scientific_notes=(
            "Pod fill in P. vulgaris involves two phases: rapid pod elongation (cell division, "
            "day 50-58) followed by seed development (cell enlargement, day 58-65). For export "
            "green beans, harvest must occur during or just after the pod elongation phase — "
            "before seeds become visible through the pod wall. Delay in harvest by 2-3 days "
            "causes seed swell and pod stringiness, immediately downgrading export quality. "
            "Pod dry weight accumulates mainly in the final 10 days; potassium loading to the "
            "pod is critical for maintaining turgor and crisp texture. "
            "Calcium is required for cell wall integrity in the pod wall."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Harvest",
        stage_code="HA",
        day_range=(65, 75),
        water_kc=0.7,
        water_mm_per_week=28,
        critical_nutrients=["Potassium (maintenance)"],
        key_activities=[
            "Harvest in early morning to minimise field heat and maximise shelf life",
            "Snap pods cleanly from plant; do not pull or damage vine",
            "Place harvested pods immediately in shade or ventilated containers",
            "Transport to packhouse within 2-3 hours of harvest — cold chain starts here",
            "Hydro-cool or forced-air cool pods to 4-6°C within 4 hours of harvest",
            "Continue harvesting every 2-3 days to maintain plant production and quality",
            "Sort and grade: A-grade (16-60 cm long, straight, uniform green, blemish-free)",
            "Reject pods with any disease lesions, insect damage, or yellowing",
        ],
        risks=[
            "Post-harvest heat damage reducing shelf life (critical risk in Zimbabwe climate)",
            "Mechanical damage during picking reducing grade",
            "Delayed cold chain leading to yellowing and softening",
            "Over-ripe pods (seed swell) reducing export acceptance",
            "Residue non-compliance — observe all PHIs strictly",
        ],
        scientific_notes=(
            "Green beans for export are harvested at the immature pod stage (BBCH 79: "
            "pod elongated, seeds just barely visible as bumps). Respiration rate is high "
            "immediately after harvest (climacteric-like behaviour in response to picking). "
            "Temperature is the primary driver of post-harvest quality loss — for every 10°C "
            "increase above 0°C, respiration approximately doubles (Q10 effect), accelerating "
            "senescence, yellowing, and tissue softening. Target pod temperature of 4-6°C "
            "within 4 hours of harvest maintains marketable quality for 7-12 days. "
            "Modified atmosphere packaging (5% O₂ + 5% CO₂) extends shelf life to 14-18 days "
            "for airfreight to EU markets."
        ),
    ),
]


GREEN_BEAN_FERTILIZER = FertilizerSchedule(
    basal={
        "product": "Compound L (5:18:12 + trace elements)",
        "rate": "400 kg/ha",
        "timing": "At planting, banded 5 cm below and 5 cm to the side of the seed row",
        "nutrients": (
            "20 kg N, 72 kg P₂O₅, 48 kg K₂O per ha from Compound L. "
            "Trace elements (Zn, B, Mo, Mn) included in Compound L formulation."
        ),
        "note": (
            "Compound L is the preferred basal fertiliser for legumes in Zimbabwe — "
            "its lower N and higher P:K ratio supports nodulation over vegetative growth. "
            "Do NOT use Compound D (high-N) as basal — excess N suppresses Rhizobium "
            "nodule formation. Band placement improves P availability in P-fixing soils "
            "(Highveld kaolinitic sands)."
        ),
    },
    top_dress_1={
        "product": "Ammonium Nitrate 34.5% N (AN)",
        "rate": "50-75 kg/ha",
        "timing": (
            "At 25-30 DAE (days after emergence), only if nodules are not actively fixing "
            "(confirmed by uprooting 3-5 plants and examining nodule colour: white/green "
            "= inactive; apply AN). Omit if nodules are pink/red."
        ),
        "nutrients": "17-26 kg N per ha",
        "note": (
            "A light 'starter' nitrogen application bridges the gap between seed N reserves "
            "and full nodule activation (nodules become effective at 20-28 DAE in Zimbabwe "
            "conditions). Excess N at this stage suppresses nodulation and increases cost. "
            "Apply as side-dress 10 cm from plant row; incorporate lightly."
        ),
    },
    top_dress_2={
        "product": "Potassium Sulphate (SOP, 0-0-50 + 17% S)",
        "rate": "50-75 kg/ha",
        "timing": "At early flowering (day 33-38)",
        "nutrients": "25-37 kg K₂O + 8-12 kg S per ha",
        "note": (
            "Potassium is critical for pod quality, sugar transport, and export grade. "
            "Use sulphate of potash (SOP) rather than muriate (KCl) for export beans — "
            "chloride in MOP can reduce pod crispness at high rates. "
            "Sulphur in SOP is beneficial on Highveld soils which are typically S-deficient."
        ),
    },
    foliar={
        "product": "Solubor (boron 17%) + Calcium Chloride 77%",
        "rate": "1.0 kg/ha Solubor + 2.0 kg/ha CaCl₂ in 500 L water",
        "timing": "At first flower open and repeat 10-14 days later (2 applications total)",
        "note": (
            "Boron is essential for pollen tube growth, pollen germination, and cell wall "
            "synthesis in developing pods. Deficiency is common on sandy Highveld soils "
            "and highly leached Eastern Highlands soils. Calcium maintains pod cell wall "
            "integrity and reduces pod tip burn. Do not tank-mix with copper products "
            "(precipitation). Apply in early morning or late afternoon."
        ),
    },
    liming={
        "ite": "Apply agricultural lime (CaCO₃) or dolomitic lime if pH < 5.8",
        "rate": "1.5-2.5 t/ha agricultural lime, depending on buffer pH and soil type",
        "timing": "Minimum 3 months before planting; ideally at land preparation",
        "note": (
            "Rhizobium phaseoli activity is optimal at pH 6.0-6.8. Below pH 5.5, "
            "aluminium toxicity severely inhibits root growth and nodule formation. "
            "Most Zimbabwe Highveld soils require regular liming (every 2-3 years) "
            "due to natural acidity and acidifying effect of ammonium-based fertilisers. "
            "Dolomitic lime (CaMg(CO₃)₂) preferred where Mg deficiency is suspected."
        ),
    },
    notes=(
        "Green beans fix 40-80 kg N/ha via Rhizobium symbiosis under optimal conditions. "
        "Key principles for Zimbabwe export bean fertiliser management: (1) prioritise P "
        "at establishment for root and nodule development; (2) only apply N if nodulation "
        "is confirmed poor; (3) build K and Ca for pod quality at flowering; (4) always "
        "apply Rhizobium inoculant even in previously-cropped fields (inoculant populations "
        "decline over 2-3 years). Excess N produces over-vegetative plants with reduced "
        "pod set and darker-than-optimal pod colour that can affect export grade."
    ),
)


GREEN_BEAN_PLANTING_WINDOWS: List[PlantingWindow] = [
    PlantingWindow(
        region="Highveld (NR IIa/IIb) — Harare, Marondera, Mazowe, Chinhoyi",
        optimal_start="October 15",
        optimal_end="January 31",
        acceptable_start="October 1",
        acceptable_end="February 15",
        notes=(
            "Main rainy season production coincides with the EU summer bean gap — "
            "optimal market timing. Two crops possible: Oct-Dec and Jan-Feb plantings. "
            "Rainfall 750-1000 mm supplements irrigation. Rust and angular leaf spot "
            "pressure peaks in Jan-Feb wet season. Stagger plantings by 2-3 weeks for "
            "continuous supply to packhouse. Under full irrigation: year-round production "
            "possible with dry-season planting (Apr-Jul) for off-season EU premium pricing."
        ),
    ),
    PlantingWindow(
        region="Eastern Highlands (NR I) — Nyanga, Juliasdale, Chipinge",
        optimal_start="September 15",
        optimal_end="December 31",
        acceptable_start="September 1",
        acceptable_end="January 31",
        notes=(
            "High altitude (1500-2000 m) produces premium quality beans with natural "
            "coolness reducing disease pressure in the dry months. September-November "
            "plantings take advantage of lower disease risk before peak rains. "
            "Disease pressure high from December onwards — fungicide programme essential. "
            "Frost risk minimal compared to Highveld but cool nights can slow growth. "
            "Under irrigation, extended production season possible. Chipinge lower-altitude "
            "areas allow earlier planting from August under irrigation."
        ),
    ),
    PlantingWindow(
        region="Midlands Irrigation Schemes — Kwekwe, Gweru, Mvuma",
        optimal_start="October 1",
        optimal_end="December 31",
        acceptable_start="September 15",
        acceptable_end="January 31",
        notes=(
            "Lower elevation and hotter temperatures require careful timing. "
            "Oct-Nov plantings before peak heat (Dec-Jan) are preferred. "
            "Full irrigation essential throughout. Bean fly and whitefly pressure "
            "is higher here than on the Highveld — seed treatment non-negotiable. "
            "Dry-season irrigation production (Apr-Jun) possible for premium markets "
            "but requires careful water management."
        ),
    ),
    PlantingWindow(
        region="Year-Round Irrigated Export Production — All Suitable Regions",
        optimal_start="Year-round",
        optimal_end="Year-round (staggered)",
        acceptable_start="Any month",
        acceptable_end="Any month",
        notes=(
            "Zimbabwe's EU export window is primarily Oct-March (northern hemisphere "
            "winter/spring). Commercial export programmes under centre-pivot or drip "
            "irrigation plant on a continuous cycle: 10-14 day staggered plantings to "
            "ensure steady weekly packhouse throughput of 5-15 tonnes per ha per week. "
            "April-September dry-season production targets premium 'off-season' EU pricing. "
            "GlobalGAP certification is mandatory for all EU-destined produce. "
            "Cold chain must be in place before planting commences."
        ),
    ),
]


PROFILE = CropProfile(
    crop_name="Green Beans (French Beans)",
    scientific_name="Phaseolus vulgaris",
    family="Fabaceae",
    optimal_ph=(6.0, 6.8),
    critical_ph_low=5.5,
    optimal_soil_types=["fersiallitic", "siallitic", "kaolinitic"],
    avoid_soil_types=["vertisol", "lithosol"],
    optimal_temp=(18.0, 28.0),
    critical_temp_low=5.0,
    critical_temp_high=35.0,
    base_temp_gdd=10.0,
    total_water_mm=350.0,
    growth_stages=GREEN_BEAN_GROWTH_STAGES,
    fertilizer_schedule=GREEN_BEAN_FERTILIZER,
    diseases=GREEN_BEAN_DISEASES,
    pests=GREEN_BEAN_PESTS,
    planting_windows=GREEN_BEAN_PLANTING_WINDOWS,
    harvest_moisture=(
        "Harvest at immature pod stage: pods 14-18 cm long, straight, deep green, "
        "seeds barely visible through pod wall. Pod moisture ~88-92% at correct harvest maturity."
    ),
    storage_conditions=(
        "Pre-cool to 4-6°C within 2-4 hours of harvest using hydro-cooling or "
        "forced-air cooling. Store at 4-6°C, 95% relative humidity. "
        "Do NOT store below 4°C — chilling injury causes pitting and discolouration. "
        "Shelf life: 7-12 days at 4-6°C. Use perforated polyethylene bags or modified "
        "atmosphere packaging (5% O₂ + 5% CO₂) for airfreight — extends shelf life to "
        "14-18 days. Ethylene sensitivity is low — safe to store with other produce."
    ),
    post_harvest_notes=(
        "Green beans are Zimbabwe's most important export horticulture crop to the EU, "
        "generating significant foreign currency. GlobalGAP (formerly EurepGAP) "
        "certification is mandatory for all EU-destined produce — this covers pesticide "
        "management, worker welfare, traceability, and food safety. "
        "Key export varieties grown in Zimbabwe: AMY (fine bean, 14-16 cm, round pod, "
        "most widely grown), BRONCO (flat bean, robust, high yield, suits Highveld), "
        "SAMANTHA (fine bean, partial rust tolerance, good for wet seasons). "
        "Grading standards: Grade A = 14-18 cm length, straight (max 15mm curve), "
        "fresh green colour, turgid, blemish-free; Grade B = 10-14 cm or slight curve. "
        "Post-harvest operations: field reception > wash and sanitise > grade by size "
        "> pack in 200 g consumer packs > palletise > cold store > airfreight. "
        "Maximum residue levels (MRLs) for EU market are strictly enforced — "
        "maintain pesticide application records (spray diary) for all applications. "
        "Typical export yield: 8-12 tonnes/ha marketable beans; top producers achieve "
        "15+ tonnes/ha under optimal irrigation and agronomic management."
    ),
    natural_region_suitability={
        "I": (
            "Excellent — high altitude, cool temperatures, low disease pressure in dry months. "
            "Year-round production possible under irrigation. Premium quality."
        ),
        "IIa": (
            "Excellent — Harare, Marondera, Mazowe belt is Zimbabwe's primary export bean "
            "production zone. Rainy season Oct-Feb production; dry-season under irrigation."
        ),
        "IIb": (
            "Good — suitable for rainy season production. Slightly higher disease risk "
            "than NR IIa. Full irrigation package and fungicide programme essential."
        ),
        "III": (
            "Moderate — suitable under full irrigation. Heat stress risk increases in "
            "Dec-Feb. Bean fly pressure higher. Dry-season production Apr-Jun preferred."
        ),
        "IV": (
            "Marginal — too hot and dry for reliable production without intensive irrigation. "
            "Not recommended for commercial export programmes."
        ),
        "V": (
            "Not suitable — excessive heat and water scarcity preclude commercial production."
        ),
    },
)

ALIASES = ["green bean", "french beans", "snap beans", "bhinzi"]
