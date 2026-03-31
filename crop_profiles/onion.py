"""Onion (Allium cepa) — Cool-season bulb crop, day-length sensitive, major vegetable in Zimbabwe."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List


ONION_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Purple Blotch",
        pathogen="Alternaria porri",
        pathogen_type="fungal",
        symptoms=[
            "Small, water-soaked, whitish lesions on leaves and seed stalks that rapidly enlarge",
            "Lesions turn purple to dark brown with a distinct yellow or water-soaked margin",
            "Concentric zonation (target-board pattern) develops within mature lesions",
            "Lesions girdle leaves or stalks causing tip-down dieback from infection point",
            "In humid conditions dark olive-brown sporulation (conidiophores and conidia) is visible on lesion surface",
            "Severely infected leaves collapse; bulb scales below infected necks may show surface discolouration",
        ],
        identification_markers=[
            "Purple to dark maroon lesion colour is diagnostic — distinguishes from Stemphylium leaf blight (straw-brown) and Botrytis (grey-brown)",
            "Concentric rings within lesion clearly visible under hand lens",
            "Yellow chlorotic halo surrounding lesion on living leaf tissue",
            "Lesions most abundant on older, lower leaves and at wound/thrips damage sites",
            "Dark olivaceous sporulation detectable under high humidity or in dew — confirms Alternaria vs. downy mildew (white/grey sporangia on abaxial surface)",
        ],
        favourable_conditions={
            "temp_min_c": 21,
            "temp_max_c": 30,
            "temp_opt_c": 25,
            "humidity_min_pct": 80,
            "leaf_wetness_hours": "6+ hours for infection",
            "note": (
                "Warm days (21-30 degC) with high humidity or prolonged leaf wetness (>6 h) "
                "create ideal infection conditions. Infection is greatly accelerated by thrips "
                "damage which breaches the waxy leaf cuticle and provides wound-entry points. "
                "Alternating wet and dry periods promote sporulation and dispersal. Disease is "
                "most destructive from bulb initiation through maturation when foliage must "
                "remain functional to drive carbohydrate partitioning into the bulb."
            ),
        },
        susceptible_stages=["Vegetative leaf growth", "Bulb initiation", "Bulb enlargement", "Maturation"],
        resistant_varieties=[],
        susceptible_varieties=["Texas Grano 502", "Red Creole C-5"],
        chemical_control=[
            {
                "name": "Mancozeb 80 WP",
                "rate": "2.0-2.5 kg/ha",
                "phi_days": "14",
                "notes": (
                    "Broad-spectrum dithiocarbamate protectant. Begin at first symptom appearance "
                    "or preventively from early bulb initiation. Repeat every 7-10 days. "
                    "Ensure good coverage of all leaf surfaces. Rotate with systemic fungicides."
                ),
            },
            {
                "name": "Iprodione 50 WP",
                "rate": "1.0-1.5 kg/ha",
                "phi_days": "21",
                "notes": (
                    "Dicarboximide fungicide with systemic activity against Alternaria. "
                    "Apply at first lesion stage and repeat at 10-14 day intervals. "
                    "Do not exceed 3 applications per season to manage resistance."
                ),
            },
            {
                "name": "Azoxystrobin 250 SC",
                "rate": "0.4-0.5 L/ha",
                "phi_days": "14",
                "notes": (
                    "QoI (strobilurin) fungicide with preventive and curative activity. "
                    "Alternate with mancozeb or iprodione to prevent resistance development. "
                    "Provides bonus activity against downy mildew in the same spray."
                ),
            },
            {
                "name": "Chlorothalonil 720 SC",
                "rate": "1.5-2.0 L/ha",
                "phi_days": "7",
                "notes": (
                    "Multi-site contact fungicide with broad-spectrum activity. "
                    "Good rainfastness once dried. Use in rotations with systemic products."
                ),
            },
        ],
        biological_control=[
            "Neem oil (Azadirachta indica) at 5-10 ml/L water — apply preventively every 7-10 days; moderate suppression",
            "Trichoderma asperellum foliar formulations showing promise in regional trials for Alternaria suppression",
            "Compost teas (aerated, 24 h) applied as foliar spray may reduce disease incidence by improving canopy microbiome",
            "Copper-based products (copper hydroxide, copper oxychloride) at 2-3 kg/ha as a protectant with broad spectrum activity",
        ],
        cultural_control=[
            "Increase between-row spacing to 30-35 cm to improve air circulation and reduce leaf wetness duration",
            "Avoid overhead irrigation; use drip tape or furrow irrigation to keep foliage dry",
            "Irrigate in early morning so foliage dries quickly — never irrigate in the evening",
            "Remove and deep-bury or burn all infected crop debris immediately after harvest",
            "Control thrips populations rigorously — thrips damage is the primary gateway for Alternaria infection",
            "Rotate with non-Allium crops for 2-3 seasons to reduce inoculum in soil and debris",
            "Avoid planting adjacent to or downwind of previous-season Allium fields",
        ],
        economic_threshold="10% of plants showing active lesions before bulb initiation; 20% during bulbing",
        severity_scale={
            "mild": "Isolated lesions on oldest leaves only; < 10% leaf area affected; no lesions on flag leaf",
            "moderate": "Lesions on multiple leaves including upper canopy; 10-30% leaf area affected; some girdling",
            "severe": "> 30% leaf area destroyed; flag leaf and seed stalks infected; significant early bulbing and yield loss",
        },
    ),
    DiseaseProfile(
        name="Downy Mildew",
        pathogen="Peronospora destructor",
        pathogen_type="fungal",
        symptoms=[
            "Pale oval or cylindrical patches on leaves, initially pale green then yellowing",
            "Violet-grey to purplish downy sporulation (sporangiophores) on infected patches in moist mornings",
            "Infected areas become pale straw-yellow, then collapse and dry off",
            "Systemic infection from bulb-borne mycelium causes entire plants to be pale and stunted from emergence",
            "Seed stalks can be infected, causing them to collapse before seed set",
            "Secondary Alternaria or Botrytis infection often colonises downy mildew lesions",
        ],
        identification_markers=[
            "Downy (not powdery) grey-purple sporulation on the outer (abaxial) leaf surface distinguishes from Alternaria",
            "Systemic plants uniformly pale green and shorter than healthy plants — visible from emergence",
            "In early morning dew, infected patches covered with distinctive grey-violet fuzz (branched sporangiophores)",
            "Lesions lack the distinct concentric rings of Alternaria porri",
            "Sporulation stops when foliage dries; patches then fade to straw yellow",
        ],
        favourable_conditions={
            "temp_min_c": 4,
            "temp_max_c": 25,
            "temp_opt_c": 13,
            "relative_humidity_min_pct": 95,
            "leaf_wetness_hours": "4+ hours at 10-15 degC triggers sporulation",
            "note": (
                "Cool, humid conditions are critical — optimum temperature for sporulation is 10-15 degC "
                "with RH above 95%. Infection requires 4+ hours of leaf wetness. In Zimbabwe, "
                "downy mildew is most severe during the cool winter months (June-August) when temperatures "
                "are cool at night and mornings are misty. The pathogen overwinters as oospores in soil "
                "and as systemic mycelium in infected bulb sets. Warm dry weather suppresses the disease."
            ),
        },
        susceptible_stages=["Seedling/nursery", "Transplant establishment", "Vegetative leaf growth", "Bulb initiation"],
        resistant_varieties=["Some newer F1 hybrids carry partial resistance"],
        susceptible_varieties=["Texas Grano 502", "Red Creole C-5", "Pukekohe Longkeeper"],
        chemical_control=[
            {
                "name": "Metalaxyl-M 4% + Mancozeb 64% WP (Ridomil Gold MZ)",
                "rate": "2.0-2.5 kg/ha",
                "phi_days": "14",
                "notes": (
                    "Systemic (metalaxyl-M) plus protectant (mancozeb) combination — first choice for "
                    "downy mildew. Metalaxyl-M penetrates leaf tissue and is active against established "
                    "infections. Do not use metalaxyl alone — resistance risk is very high. "
                    "Limit to 2-3 applications per season and rotate with non-phenylamide fungicides."
                ),
            },
            {
                "name": "Fosetyl-Al 80 WP (Aliette)",
                "rate": "2.5 kg/ha",
                "phi_days": "14",
                "notes": (
                    "Phosphonate systemic — moves upward and downward in the plant (ambimobile). "
                    "Good curative activity against established infections. Alternate with mancozeb."
                ),
            },
            {
                "name": "Dimethomorph 50 WP",
                "rate": "1.0 kg/ha",
                "phi_days": "7",
                "notes": "CAA fungicide with good activity against oomycetes. Alternate with metalaxyl.",
            },
            {
                "name": "Copper oxychloride 50 WP",
                "rate": "2.0-2.5 kg/ha",
                "phi_days": "7",
                "notes": "Protectant only; good as rotation partner and for organic programmes. Apply before infection.",
            },
        ],
        biological_control=[
            "Copper-based bioprotectants (copper hydroxide) as a first-line preventive spray in cool humid conditions",
            "Bacillus subtilis-based products (Serenade) show moderate suppressive activity in trials",
            "Phosphonate foliar sprays (potassium phosphonate) may stimulate systemic resistance",
        ],
        cultural_control=[
            "Use disease-free transplants raised from certified seed in pathogen-free nursery beds",
            "Inspect nursery beds for systemic downy mildew plants and remove immediately",
            "Avoid planting in low-lying areas prone to mist and overnight fog accumulation",
            "Optimise plant spacing to allow canopy ventilation and faster drying",
            "Use drip irrigation; avoid overhead sprinkler irrigation in cool seasons",
            "Maintain accurate weather records — schedule preventive sprays before predicted cool, humid nights",
            "Avoid volunteers (regrowth from previous crop) which are primary inoculum sources",
        ],
        economic_threshold="5% of plants showing sporulating lesions warrants immediate action; zero tolerance for systemic plants in nursery",
        severity_scale={
            "mild": "< 5% of plants showing isolated non-sporulating patches; cool-humid spell forecast",
            "moderate": "5-20% plants infected; sporulation visible in morning; disease progressing up canopy",
            "severe": "> 20% plants affected; sporulation on upper leaves; leaf collapse imminent; significant yield loss expected",
        },
    ),
    DiseaseProfile(
        name="Fusarium Basal Rot",
        pathogen="Fusarium oxysporum f. sp. cepae",
        pathogen_type="fungal",
        symptoms=[
            "Premature yellowing of leaf tips that progresses toward the leaf base and downward through the plant",
            "Brown to dark-brown dry rot advancing upward from the basal plate into bulb scales",
            "Pink to reddish-pink mycelium visible at the basal plate junction of pulled plants",
            "Roots brown, rotted and easily detached; the root-disc (basal plate) shows internal discolouration on cross-section",
            "Bulbs feel soft and spongy at the base; outer dry scales intact but inner tissue watery and discoloured",
            "In storage, infected bulbs develop secondary Penicillium (blue-green mould) and bacterial rot",
        ],
        identification_markers=[
            "Brown basal plate discolouration on cross-section is the most reliable field diagnostic",
            "Pink-tinged mycelium at the base (not white = not Sclerotium white rot; not grey = not Botrytis)",
            "Roots are decayed but no sclerotia are present (rules out white rot)",
            "Disease progresses from the bottom up — leaf tips die first, unlike downy mildew which starts on mid-canopy leaves",
            "Culture on PDA: cream to pink sporodochia producing banana-shaped macroconidia",
        ],
        favourable_conditions={
            "temp_min_c": 20,
            "temp_max_c": 35,
            "temp_opt_c": 28,
            "soil_moisture": "warm, moist to waterlogged soils",
            "note": (
                "Favoured by warm soil temperatures (optimum 25-30 degC) and wet soils. "
                "Any root damage from nematodes, insects (onion fly maggots), or cultivation "
                "dramatically increases infection risk. In Zimbabwe, the risk is highest "
                "during the October-November bulbing period when soils are warming. "
                "Pathogen persists as chlamydospores in soil for many years."
            ),
        },
        susceptible_stages=["Bulb initiation", "Bulb enlargement", "Maturation", "Post-harvest storage"],
        resistant_varieties=[],
        susceptible_varieties=["Texas Grano 502", "Red Creole C-5"],
        chemical_control=[
            {
                "name": "Thiram 80 WP (seed / transplant dip)",
                "rate": "3 g/L water; dip transplant roots 10-15 min before planting",
                "phi_days": "N/A",
                "notes": "Reduces seed- and soil-borne inoculum. Use as a preventive transplant treatment.",
            },
            {
                "name": "Carbendazim 50 WP",
                "rate": "1.0-1.5 g/L water, transplant root dip or early drench",
                "phi_days": "21",
                "notes": "MBC systemic fungicide. Soak transplant roots 20-30 minutes. Resistance risk — do not use repeatedly.",
            },
            {
                "name": "Tebuconazole 250 EW",
                "rate": "1.0 L/ha as soil drench",
                "phi_days": "30",
                "notes": "DMI systemic with partial curative activity. Apply as a drench at first symptoms.",
            },
        ],
        biological_control=[
            "Trichoderma harzianum soil incorporation at transplanting (2-4 kg product/ha) — well-documented suppression in trials",
            "Trichoderma viride applied in planting furrows",
            "Bacillus subtilis (e.g., Serenade) as a soil drench or transplant soak",
            "Mycorrhizal inoculants (Glomus intraradices) improve root health and tolerance to Fusarium stress",
        ],
        cultural_control=[
            "Avoid planting into waterlogged or poorly drained soils — raise beds if necessary",
            "Ensure good soil drainage by deep ripping or ridging before transplanting",
            "Minimise root damage from cultivations, nematodes, and onion fly — all create Fusarium entry points",
            "Rotate with non-Allium crops for minimum 3-4 years (cereal, legume rotations)",
            "Cure harvested bulbs properly: dry in shade with good ventilation for 3-4 weeks before storage",
            "Discard all soft or basal-rotted bulbs at harvest — do not store or use as planting sets",
            "Avoid excessive nitrogen late in the season which prolongs soft, lush growth susceptible to infection",
        ],
        economic_threshold="5% of plants showing basal plate discolouration symptoms during bulbing",
        severity_scale={
            "mild": "< 5% plants affected; basal plate slightly discoloured; roots partially intact",
            "moderate": "5-20% plants with significant root loss and basal plate rot; noticeable plant mortality",
            "severe": "> 20% plant mortality in field; storage losses projected above 30%; consider early harvest",
        },
    ),
    DiseaseProfile(
        name="Bacterial Soft Rot",
        pathogen="Erwinia carotovora subsp. carotovora (syn. Pectobacterium carotovorum)",
        pathogen_type="bacterial",
        symptoms=[
            "Water-soaked, slimy, translucent lesions on leaf bases and inner fleshy scales",
            "Rapid breakdown of internal bulb tissue into a foul-smelling, slimy, watery mass",
            "Outer dry scales remain intact while interior has completely rotted — 'hollow' feel when squeezed",
            "Brown to cream-coloured slimy exudate may ooze from the neck when the bulb is cut",
            "In the field: leaves wilt and collapse; pulling the plant reveals slimy, malodorous bulb base",
            "In storage: affected bulbs leak liquid, infecting adjacent bulbs in the storage pile rapidly",
        ],
        identification_markers=[
            "Foul ammonia-like or sulphurous smell is the most immediate diagnostic cue",
            "Outer scales intact but internal tissue completely liquefied — unique to soft rot bacteria",
            "Infection originates at wounds (neck damage at harvest, hail, insect feeding) or submerged plant bases",
            "No visible mycelium or sporulation (distinguishes from all fungal rots)",
            "Rapid spread in storage under warm humid conditions",
        ],
        favourable_conditions={
            "temp_min_c": 20,
            "temp_max_c": 35,
            "temp_opt_c": 28,
            "humidity": "high humidity, wet conditions, poor drainage",
            "note": (
                "Bacteria are ubiquitous in soil and water. Disease requires a wound entry point "
                "or stressed plant tissue. Warm, wet conditions accelerate bacterial multiplication "
                "and pectinase enzyme activity that degrades cell walls. In Zimbabwe, risk peaks "
                "during the hot, humid November-January period and when harvest is delayed during "
                "summer rains. Overcrowded storage with poor ventilation is a major risk factor. "
                "Insect damage (thrips, onion fly) creates infection courts in the field."
            ),
        },
        susceptible_stages=["Bulb enlargement", "Maturation", "Post-harvest storage"],
        resistant_varieties=[],
        susceptible_varieties=["Texas Grano 502 (thin-necked types more susceptible at harvest)", "Red Creole"],
        chemical_control=[
            {
                "name": "Copper oxychloride 50 WP",
                "rate": "2.0-2.5 kg/ha foliar",
                "phi_days": "7",
                "notes": "Protectant bactericide; limited curative activity against Erwinia. Spray after hail events or thrips damage.",
            },
            {
                "name": "Streptomycin sulphate 20% SP",
                "rate": "200 g/ha in high water volume",
                "phi_days": "14",
                "notes": (
                    "Antibiotic bactericide; use only when bacterial disease confirmed and with caution "
                    "to prevent resistance development. Check national registration status for food crops."
                ),
            },
        ],
        biological_control=[
            "Bacillus amyloliquefaciens or B. subtilis strains with documented antibacterial activity",
            "Bacteriophage-based products (where available) for post-harvest storage treatment",
        ],
        cultural_control=[
            "Harvest promptly when 70-80% of tops have fallen — do not delay into wet weather",
            "Handle bulbs gently at all times to minimise bruising and neck damage (primary infection courts)",
            "Cure bulbs thoroughly for 3-4 weeks before storage — ensures neck closure and skin drying",
            "Store bulbs in well-ventilated, dry conditions at < 25 degC; avoid humid storage sheds",
            "Sort and discard all damaged or suspect bulbs before placing in storage",
            "Do not harvest when soils are wet — bulb surfaces contaminated with soil bacteria",
            "Control insect pests (thrips, onion fly) that create wound sites for bacterial entry",
            "Avoid overhead irrigation in the final 4 weeks before harvest",
        ],
        economic_threshold="Any occurrence in storage warrants immediate removal of affected bulbs. In field: > 3% plants wilting without obvious cause — inspect for soft rot.",
        severity_scale={
            "mild": "Isolated bulbs soft; detected on harvest inspection; no spread to adjacent bulbs yet",
            "moderate": "Several bulbs affected; leaking in storage; spread beginning; > 5% storage losses projected",
            "severe": "Widespread liquefaction in storage; strong foul odour; > 20% losses; emergency ventilation and sorting required",
        },
    ),
]


ONION_PESTS: List[PestProfile] = [
    PestProfile(
        name="Onion Thrips",
        scientific_name="Thrips tabaci",
        pest_type="insect",
        identification=[
            "Adults 1.0-1.3 mm long, slender, pale yellow to light brown; fringed (feathery) wings folded along the abdomen",
            "Nymphs (instar 1 and 2) wingless, pale yellow-green to almost colourless, concentrated in the tight leaf sheath between inner leaves",
            "Adults and nymphs found deep inside the leaf sheaths where they are protected from sprays and from rain",
            "Frass (black specks) visible alongside feeding sites between leaf sheaths",
            "Use blue sticky traps (thrips prefer blue over yellow) at crop height for population monitoring",
            "Under a hand lens: two body segments visible before wings, and 7-8 abdominal segments",
        ],
        damage_symptoms=[
            "Characteristic silvery-white streaking, flecking, and stippling on leaves from feeding on epidermal cells",
            "Extensive whitish or silvery patches along upper leaf surface as feeding sites coalesce",
            "Leaf tips die back; in severe infestations entire leaves turn silvery-white then straw-brown",
            "Curling, twisting, and distortion of young leaves in the centre of the plant when growing points are attacked",
            "Reduced canopy photosynthetic area leads to small, undersized bulbs — the economically most damaging consequence",
            "Feeding wounds create multiple entry points for Alternaria porri (purple blotch) and Botrytis — a critical disease-linkage",
            "Thrips may also transmit Iris Yellow Spot Virus (IYSV) — look for straw-coloured spindle-shaped lesions on leaves as secondary symptom",
        ],
        life_cycle_notes=(
            "Highly prolific pest with a complete lifecycle of 13-30 days depending on temperature (faster at 25-30 degC). "
            "Females lay up to 80 eggs inserted individually into leaf tissue (endophytic). Eggs hatch in 5-7 days at 25 degC. "
            "Two nymphal instars feed actively; two pupal instars (propupa and pupa) do not feed and occur in the soil or leaf sheaths. "
            "Adults migrate rapidly within and between fields, especially in warm, dry, windy weather. "
            "Multiple (6-10+) overlapping generations per season in Zimbabwe's climate. "
            "Females can reproduce parthenogenetically, giving populations the capacity to rebuild very rapidly after partial control. "
            "Populations are naturally suppressed by rain which physically dislodges insects and creates conditions unfavourable for reproduction."
        ),
        favourable_conditions={
            "temp_min_c": 20,
            "temp_max_c": 35,
            "temp_opt_c": 28,
            "humidity": "low; hot and dry conditions strongly favour population explosions",
            "note": (
                "Thrips tabaci is the single most economically damaging pest of onions in Zimbabwe. "
                "Populations build explosively during hot, dry spells. In Zimbabwe's winter onion crop "
                "(June-September), thrips pressure is typically high because rains have ceased. "
                "In summer crops, populations may crash after heavy rain but recover quickly."
            ),
        },
        susceptible_stages=["Transplant establishment", "Vegetative leaf growth", "Bulb initiation", "Bulb enlargement"],
        economic_threshold="30 thrips per plant (average over 10-plant sample) or 5 thrips per leaf; lower threshold (20/plant) at bulb initiation when canopy loss is most costly",
        chemical_control=[
            {
                "name": "Spinosad 480 SC",
                "rate": "100-200 ml/ha in high water volume",
                "phi_days": "3",
                "notes": (
                    "Naturalyte (derived from Saccharopolyspora spinosa). Highly effective against "
                    "thrips nymphs and adults. Minimal impact on beneficial insects. "
                    "Use high water volume (400-600 L/ha) with good penetration into leaf sheaths. "
                    "Rotate with other modes of action to manage resistance."
                ),
            },
            {
                "name": "Lambda-cyhalothrin 50 EC",
                "rate": "150-200 ml/ha",
                "phi_days": "7",
                "notes": (
                    "Type II pyrethroid; fast knockdown. Significant resistance is developing in "
                    "Zimbabwe populations from overuse. Use only in rotation, not consecutively. "
                    "Harmful to beneficial insects."
                ),
            },
            {
                "name": "Abamectin 18 EC",
                "rate": "500-700 ml/ha",
                "phi_days": "3",
                "notes": (
                    "Macrocyclic lactone; good systemic and translaminar activity against thrips. "
                    "Effective against nymphs in leaf sheaths. Include adjuvant to improve penetration."
                ),
            },
            {
                "name": "Thiamethoxam 25 WG",
                "rate": "100 g/ha foliar or 300 g/ha soil drench at transplanting",
                "phi_days": "14",
                "notes": (
                    "Neonicotinoid; systemic. Soil drench at transplanting provides 3-4 weeks of "
                    "systemic protection during the vulnerable establishment phase. "
                    "Rotate with non-neonicotinoid insecticides."
                ),
            },
        ],
        biological_control=[
            "Minute pirate bugs (Orius spp.) are effective generalist predators of thrips — conserve by avoiding broad-spectrum insecticides",
            "Predatory mites (Amblyseius cucumeris, Amblyseius swirskii) for protected cultivation",
            "Entomopathogenic fungi (Beauveria bassiana, Metarhizium anisopliae) formulations applied as foliar sprays — most effective in humid conditions",
            "Conserving and enhancing natural enemy populations through reduced-impact insecticide programmes (spinosad, abamectin)",
        ],
        cultural_control=[
            "Overhead sprinkler irrigation or hand-spraying with plain water physically dislodges thrips from foliage — effective temporary knockdown",
            "Reflective silver/aluminium mulches deter adult thrips from landing on crop",
            "Remove grass and broad-leaf weed hosts from field margins which serve as thrips reservoirs",
            "Avoid planting adjacent to ageing Allium crops or grass seed crops which are thrips hotspots",
            "Plant at the recommended spacing — overcrowding creates warm, humid microclimate paradoxically unfavourable to thrips; overly sparse stands concentrate thrips on fewer plants",
            "Intercropping with carrot or celery has been shown to reduce thrips incidence by diversifying the canopy",
            "Monitor weekly from transplanting using blue sticky traps and direct plant inspection",
        ],
        scouting_protocol=(
            "Begin scouting at transplanting. Sample weekly: select 20 plants at 5 locations across the field (100 plants total per 5 ha). "
            "For each plant, peel apart inner leaf sheaths and count all thrips (adults and nymphs). Record separately. "
            "Calculate mean thrips per plant and mean per leaf. "
            "Set action threshold at 30/plant during vegetative growth; 20/plant at bulb initiation. "
            "Record blue sticky trap catches weekly (replace traps every 7 days). "
            "Note percentage of plants showing silver leaf damage (> 10% leaf area silvered = significant economic feeding)."
        ),
    ),
    PestProfile(
        name="Onion Fly (Onion Maggot)",
        scientific_name="Delia antiqua",
        pest_type="insect",
        identification=[
            "Adult: small grey-brown fly 6-8 mm long, resembling a small housefly but with narrower body and longer legs; thorax with dark longitudinal stripes",
            "Eggs: white, elongated, ribbed, 1 mm, laid individually or in clusters at the base of onion plants at soil level",
            "Larvae (maggots): white to cream, legless, tapered, 8-10 mm at maturity, found tunnelling in the bulb base and roots",
            "Puparia: brown, barrel-shaped, 5-6 mm, found in soil 5-10 cm below the plant or in infested bulb tissue",
            "Attracted strongly to decaying Allium tissue and freshly disturbed Allium-planted soil",
        ],
        damage_symptoms=[
            "Young transplants wilt and turn yellow within 1-2 weeks of damage — frequently mistaken for transplant failure",
            "Plants pull up easily from soil with roots and basal plate destroyed by larval feeding",
            "Larvae bore tunnels through the basal plate and into bulb tissue creating entry points for Fusarium and Erwinia rots",
            "In seedling stage: entire plant may be destroyed by a single larva consuming the roots",
            "On mature bulbs: irregular cavities and tunnels filled with larval frass; secondary rot infections cause complete bulb breakdown",
            "In the nursery: patches of dead or wilting seedlings indicate larval feeding below soil surface",
        ],
        life_cycle_notes=(
            "2-3 generations per year in Zimbabwe. Overwinters as pupa in the soil. "
            "First-generation adults emerge when soil temperatures reach approximately 13 degC (typically March-April in Zimbabwe). "
            "Females are strongly attracted to freshly transplanted or damaged Allium crops for oviposition. "
            "Eggs hatch in 3-7 days. Larval period is 15-25 days; larvae feed downward through roots into bulb tissue. "
            "Pupation occurs in soil at 5-15 cm depth. Pupal period 20-30 days. "
            "Second generation peaks around June-July and can be highly damaging to the winter onion crop. "
            "A third partial generation may occur September-October coinciding with summer crop transplanting."
        ),
        favourable_conditions={
            "temp_min_c": 13,
            "temp_max_c": 28,
            "temp_opt_c": 20,
            "soil_moisture": "cool, moist soils; wetter soils increase egg survival",
            "note": (
                "Cool to warm, moist conditions favour egg and larval development. "
                "Adult flies are most active in morning hours. "
                "Fresh crop residues and disturbed Allium soil at transplanting strongly attract females. "
                "In Zimbabwe, the March-June transplanting window coincides with first and second generation "
                "adult flight, making preventive soil treatments at planting critical."
            ),
        },
        susceptible_stages=["Seedling/nursery", "Transplant establishment", "Vegetative leaf growth"],
        economic_threshold="5-10% of transplants showing wilting; larvae found at basal plate on 2+ of 20 sampled plants",
        chemical_control=[
            {
                "name": "Chlorpyrifos 48 EC (soil drench/furrow treatment)",
                "rate": "2.5 L/ha applied as transplant furrow drench",
                "phi_days": "21",
                "notes": (
                    "Organophosphate applied as a drench at the base of transplants at planting. "
                    "Targets newly hatched larvae and reduces egg survival. Apply immediately after transplanting. "
                    "Observe pre-harvest interval strictly."
                ),
            },
            {
                "name": "Diazinon 14G (granular soil incorporation)",
                "rate": "30-40 kg/ha banded in planting furrow",
                "phi_days": "21",
                "notes": "Granular insecticide incorporated at planting. Provides residual soil protection during establishment.",
            },
            {
                "name": "Cyromazine 75 WP (Trigard)",
                "rate": "250-300 g/ha soil drench",
                "phi_days": "7",
                "notes": (
                    "Insect growth regulator (IGR) specifically targeting fly larvae (Delia spp.). "
                    "Lower environmental impact than organophosphates. Apply as drench at planting and repeat if necessary at 4 weeks."
                ),
            },
        ],
        biological_control=[
            "Entomopathogenic nematodes: Steinernema feltiae (700 million IJ/ha) applied as soil drench — targets larvae and pupae in soil; best in moist soils",
            "Entomopathogenic fungi: Metarhizium anisopliae soil applications for larval suppression",
            "Parasitic wasps: Trybliographa rapae (Figitidae) is a natural larval parasitoid; conserve through reduced insecticide use",
            "Ground beetles (Carabidae) and rove beetles (Staphylinidae) are important egg and larval predators in the soil surface layer",
        ],
        cultural_control=[
            "Delay transplanting by 2-3 weeks beyond peak first-generation adult flight to reduce oviposition on fresh transplants",
            "Use row covers (fine mesh, 0.8 mm aperture) over nursery beds and immediately after transplanting to physically exclude egg-laying females",
            "Remove all Allium crop debris promptly after harvest — decomposing tissue attracts flies to the field",
            "Avoid fresh uncomposted manure incorporation near onion plots (attracts flies)",
            "Rotate Allium crops to different fields each season — adults return to same location; 3-year rotation breaks cycle",
            "Compact soil around transplants firmly to deter egg-laying between loose soil and plant base",
            "Monitor adult flight with yellow sticky traps from March onward; record peak flight to time treatments",
        ],
        scouting_protocol=(
            "Place yellow sticky traps (15 cm x 25 cm) at canopy height, 1 per 2 ha from March/transplanting onward. "
            "Replace weekly and count Delia adults on each trap (note: other small flies also caught — identify Delia by narrow grey-striped thorax). "
            "In-field: weekly inspection of 20 plants at 5 locations — gently pull suspect wilting plants and examine roots and basal plate for larvae or tunnels. "
            "Action threshold: consistent adult catch of 10+ per trap per week, or larvae found on 2+ pulled plants out of 20 sampled."
        ),
    ),
    PestProfile(
        name="Cutworms",
        scientific_name="Agrotis spp. (primarily Agrotis ipsilon and Agrotis segetum)",
        pest_type="insect",
        identification=[
            "Larvae: stout, greasy-grey to dull brown caterpillars, 30-50 mm at maturity; curl tightly into a C-shape when disturbed (highly diagnostic)",
            "Head capsule brown; body with faint longitudinal pale stripe on dorsum; skin smooth and slightly oily in appearance",
            "Found in the top 5 cm of soil during the day; come to the surface to feed at night",
            "Adults: dull brown to grey moths (35-50 mm wingspan) with kidney-shaped forewing markings; rarely seen but can be attracted to light traps",
            "Pupae: mahogany-red, 18-22 mm, found in soil at 5-15 cm depth",
        ],
        damage_symptoms=[
            "Young onion transplants or seedlings cut off at or just below soil level overnight — the classic 'cutworm cut'",
            "Damaged stems have a clean, angled cut as if sliced with a knife (distinguishes from slug damage which is ragged and slimy)",
            "Small transplants disappear completely; larger plants with partially severed stems flop over and wilt",
            "Patchy stand loss: random gaps in the planting rows, not organised in lines (distinguishes from disease patchiness)",
            "Soil around damaged plants loose and crumbly from nocturnal larval activity",
            "In severe attacks on older plants, larvae may bore into the bulb base causing secondary rot",
        ],
        life_cycle_notes=(
            "Agrotis moths are migratory and multivoltine in Zimbabwe, with populations peaking at the onset of rains "
            "(October-November) when mass migration occurs from drying lowveld vegetation. "
            "Females lay batches of 200-2000 eggs on soil surface or on low plant material. "
            "Larvae feed aggressively from instars 3-6; early instars feed on leaves (minor damage) then shift to subterranean cutting at instar 3+. "
            "Full larval development takes 30-60 days. Pupation in soil for 2-4 weeks. "
            "Multiple generations per year; winter populations lower. Greatest risk to transplants in March-May and October-November. "
            "Newly transplanted fields into recently turned grassland or fallow land carry the highest risk."
        ),
        favourable_conditions={
            "temp_min_c": 15,
            "temp_max_c": 30,
            "soil_moisture": "moist, freshly cultivated soil; recently irrigated seedbeds",
            "note": (
                "Moist, freshly tilled soil with organic matter and crop debris is ideal for egg-laying. "
                "Risk is highest in March-May (autumn transplanting) and at the start of the rainy season. "
                "Fields planted after grassland fallow often have high resident larval populations. "
                "Heavy irrigation after transplanting creates ideal moist conditions for larval activity."
            ),
        },
        susceptible_stages=["Seedling/nursery", "Transplant establishment"],
        economic_threshold="5% stand loss (transplants cut or missing); or scouting finding 1 or more larvae per m2 in soil inspection before transplanting",
        chemical_control=[
            {
                "name": "Chlorpyrifos 48 EC (surface spray or soil incorporation)",
                "rate": "2.0-3.0 L/ha",
                "phi_days": "21",
                "notes": (
                    "Apply as a soil surface spray in the evening (when larvae are active) immediately after "
                    "transplanting. Or incorporate into the top 5 cm before transplanting in high-risk fields."
                ),
            },
            {
                "name": "Lambda-cyhalothrin 50 EC (evening spray)",
                "rate": "200 ml/ha as a directed surface spray at dusk",
                "phi_days": "7",
                "notes": "Fast-acting pyrethroid; apply in the evening when larvae emerge to feed. Good for immediate knockdown.",
            },
            {
                "name": "Carbaryl 85 WP (poison bait)",
                "rate": "Mix 1 kg Carbaryl + 10 kg bran + water to crumbly consistency; broadcast 10 kg bait/ha at dusk",
                "phi_days": "7",
                "notes": "Carbaryl-bran bait placed on soil surface at dusk attracts and kills cutworm larvae feeding at night. Effective and targeted.",
            },
        ],
        biological_control=[
            "Bacillus thuringiensis var. kurstaki (Bt-k) soil surface spray in evening; targets early instar larvae before they become subterranean",
            "Entomopathogenic nematodes (Steinernema carpocapsae, 1 billion IJ/ha) applied as soil drench — effective against larvae in the soil",
            "Metarhizium anisopliae soil incorporation targets larvae and pupae",
            "Trichogramma egg parasitoids can reduce egg hatch when applied at mass-mating period",
            "Nocturnal predators (ground beetles, centipedes, spiders) — conserve through minimum tillage and mulching practices",
        ],
        cultural_control=[
            "Soil cultivation and deep ploughing before transplanting exposes pupae and larvae to desiccation, birds, and frost",
            "Remove all crop debris, grass, and weeds from the seedbed 2-3 weeks before transplanting — reduces egg-laying sites",
            "Avoid planting directly after a grass fallow without thorough soil preparation",
            "Flood irrigation of the seedbed for 30 minutes the afternoon before transplanting brings larvae to the surface where birds feed on them",
            "Erect light traps above the canopy to attract and trap adult moths — reduces subsequent oviposition",
            "Use collar barriers (5 cm high paper or foil collar pressed 2 cm into soil) around transplant stems as a physical deterrent",
        ],
        scouting_protocol=(
            "Pre-planting soil inspection: dig 10 holes (30 cm x 30 cm x 15 cm deep) randomly across the field. "
            "Count and identify all caterpillars found. Action threshold: > 1 larva per hole average. "
            "Post-transplanting: walk the field at dawn and inspect each row for cut plants and freshly disturbed soil. "
            "Dig 5-10 cm into soil near cut plants to find the responsible larva (confirms cutworm vs. other causes). "
            "Use light traps from October to monitor adult moth flight and predict oviposition peaks."
        ),
    ),
]


ONION_GROWTH_STAGES: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Seedling / Nursery",
        stage_code="GS1",
        day_range=(0, 45),
        water_kc=0.40,
        water_mm_per_week=14,
        critical_nutrients=["P", "N"],
        key_activities=[
            "Sow seed thinly in well-prepared nursery beds (raised) at 5-10 g/m2",
            "Incorporate Compound S (7:21:7) at 50 g/m2 as basal dressing before sowing",
            "Cover seed lightly (0.5 cm) with fine soil or compost and tamp gently",
            "Irrigate gently twice daily with fine rose or mist system to avoid disturbing seedbed",
            "Apply pre-emergent herbicide or hand-weed carefully to eliminate weed competition",
            "Apply Thiram or Iprodione drench at 7 and 21 days to prevent damping-off",
            "Begin thinning at 3-4 leaf stage to final spacing of 2-3 cm between seedlings",
            "Harden off transplants by reducing irrigation frequency in the final 10 days before transplanting",
        ],
        risks=["Damping-off (Pythium, Rhizoctonia)", "Cutworm attack", "Overwatering", "Weed competition smothering seedlings"],
        scientific_notes=(
            "Onion seed germination is epigeal: the cotyledon emerges and forms a loop before straightening. "
            "Optimal germination temperature is 15-25 degC; germination is poor below 10 degC and above 35 degC. "
            "The seedling is vulnerable to damping-off fungi (Pythium aphanidermatum, Rhizoctonia solani) for the "
            "first 14-21 days until the hypocotyl lignifies. Phosphorus is critical in the nursery for root "
            "system development; deficiency causes purple leaf pigmentation and poor establishment. "
            "Nitrogen should be modest at this stage — lush growth increases disease susceptibility. "
            "Seedlings are ready for transplanting when they are pencil-thick (4-6 mm neck diameter) and "
            "have 4-6 true leaves, typically 35-45 days after sowing."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Transplant Establishment",
        stage_code="GS2",
        day_range=(45, 60),
        water_kc=0.50,
        water_mm_per_week=18,
        critical_nutrients=["P", "N", "K"],
        key_activities=[
            "Transplant seedlings at pencil-thick stage into prepared ridges or raised beds",
            "Spacing: 10-15 cm in-row, 25-30 cm between rows (100,000-130,000 plants/ha target)",
            "Dip transplant roots in Thiram slurry (3 g/L) or Trichoderma suspension before planting",
            "Water transplants in immediately after planting — critical for root-to-soil contact",
            "Apply Compound S 400 kg/ha as basal dressing incorporated 2-3 days before transplanting",
            "Irrigate lightly every 2-3 days for the first 2 weeks until new roots are established",
            "Scout for cutworm damage in the first week and apply soil surface spray if threshold exceeded",
            "Apply Thiamethoxam soil drench at transplanting for early thrips and aphid protection (systemic)",
        ],
        risks=["Transplant shock", "Cutworm", "Onion fly oviposition on fresh transplants", "Root-zone waterlogging"],
        scientific_notes=(
            "The transplant shock period (first 10-14 days) is characterised by a temporary wilting response "
            "as the damaged root system re-establishes. Root regeneration is rapid at 20-25 degC soil temperature; "
            "new roots emerge from the basal plate within 4-7 days in warm, moist soils. "
            "Phosphorus (P) availability in the root zone is critical during this phase — "
            "P moves by diffusion and must be in close proximity to the developing root system. "
            "The basal dressing of Compound S ensures adequate P for rapid root development. "
            "Transplanting during cooler parts of the day (early morning or late afternoon) and covering beds "
            "temporarily with shade netting reduces transpiration stress during establishment."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Vegetative Leaf Growth",
        stage_code="GS3",
        day_range=(60, 100),
        water_kc=0.75,
        water_mm_per_week=25,
        critical_nutrients=["N", "K", "S", "Mg"],
        key_activities=[
            "Apply first top-dress of Ammonium Nitrate (200 kg/ha) at 4 weeks after transplanting",
            "Irrigate every 5-7 days depending on soil type and weather (target 25-30 mm/application)",
            "Begin weekly thrips monitoring — action threshold 30/plant",
            "Scout for purple blotch and downy mildew; apply preventive fungicide if weather conditions are favourable",
            "Side-dress and irrigate in all fertilizer applications — never apply to wet foliage",
            "Shallow cultivation or inter-row weeding to maintain weed-free conditions",
            "Apply foliar zinc sulphate (2 g/L) and boron (Solubor, 1 g/L) at 6 and 10 weeks after transplanting",
        ],
        risks=["Thrips population build-up", "Nitrogen deficiency (pale yellow-green leaves)", "Purple blotch from thrips wounds + wet weather", "Weed smothering"],
        scientific_notes=(
            "The vegetative phase produces the leaf canopy that drives all subsequent dry matter accumulation. "
            "Each green leaf corresponds to a fleshy scale in the developing bulb — more leaves = more bulb scales = larger bulb. "
            "Onion leaves produce the photosynthate partitioned to the bulb during later stages; "
            "maximising green leaf area index (target 3.0-4.5 m2/m2) during this phase is critical. "
            "Nitrogen demand is at its peak: leaf elongation, chloroplast development, and rubisco enzyme synthesis "
            "all require abundant N. Sulphur is an important constituent of flavour-active thiosulphinate precursors "
            "(S-alk(en)yl cysteine sulphoxides) synthesised progressively throughout vegetative growth. "
            "Magnesium is the central atom of chlorophyll — deficiency appears as inter-veinal chlorosis on older leaves."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Bulb Initiation",
        stage_code="GS4",
        day_range=(100, 120),
        water_kc=0.95,
        water_mm_per_week=30,
        critical_nutrients=["N", "K", "Ca"],
        key_activities=[
            "Apply second top-dress of Ammonium Nitrate (200 kg/ha) at 8 weeks after transplanting",
            "This is the peak water demand period — maintain consistent soil moisture; water stress at bulb initiation severely reduces final bulb size",
            "Monitor thrips intensively — lower threshold (20/plant) during bulb initiation",
            "Spray preventive fungicide (Mancozeb or Azoxystrobin) if purple blotch or downy mildew risk conditions are present",
            "Avoid calcium deficiency: apply foliar calcium nitrate (5 g/L) if tip-burn symptoms appear",
            "Remove any bolting (flowering) plants immediately to prevent cross-pollination and yield loss in adjacent plants",
        ],
        risks=[
            "Bolting (premature flowering) from prolonged cold exposure of seedlings",
            "Water stress causing poor cell expansion in bulb scales",
            "Thrips damage reducing photosynthetic capacity exactly when bulb fill demands are highest",
            "Calcium deficiency causing tip-burn and poor scale integrity",
        ],
        scientific_notes=(
            "Bulb initiation is triggered by a critical photoperiod threshold. Allium cepa is a facultative "
            "long-day plant: most varieties used in Zimbabwe require day lengths exceeding 12-13 hours to "
            "initiate bulbing. Zimbabwe's latitude (15-22 degS) means day lengths are critical — "
            "this is why planting window timing is essential. Texas Grano types are short-day varieties "
            "(initiate at < 12-13 hours day length) making them suitable for Zimbabwe's winter crop at "
            "lower latitudes; Red Creole is also a short-day type. "
            "At bulb initiation, the leaf bases cease elongating and begin to swell as photosynthates "
            "are redirected from leaves to bulb scales. The bulbing ratio (bulb diameter / pseudo-stem diameter) "
            "exceeds 2.0, visible as a visible swelling at the base. "
            "Water is the primary driver of cell turgor expansion in bulb scales — "
            "deficit irrigation at this stage is the leading cause of undersized bulbs."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Bulb Enlargement",
        stage_code="GS5",
        day_range=(120, 150),
        water_kc=0.90,
        water_mm_per_week=28,
        critical_nutrients=["K", "Ca", "S"],
        key_activities=[
            "Maintain consistent irrigation — critical for bulb cell expansion and filling",
            "Continue fungicide programme (alternate Mancozeb, Azoxystrobin, Iprodione) every 10-14 days",
            "Cease all nitrogen applications — late nitrogen promotes leafy growth, delays maturity, and increases soft neck incidence",
            "Monitor for Fusarium basal rot symptoms; check pulled plants for basal plate discolouration",
            "Monitor for bacterial soft rot if any waterlogging events occur",
            "Begin reducing irrigation frequency in the final 10 days of this stage as maturation approaches",
        ],
        risks=[
            "Purple blotch, downy mildew — protect canopy photosynthesis during bulb fill",
            "Fusarium basal rot in warm soils",
            "Bacterial soft rot if waterlogged",
            "Late nitrogen application causing delayed maturity and thick necks",
        ],
        scientific_notes=(
            "During bulb enlargement, dry matter accumulates rapidly through cell division and expansion in the "
            "fleshy scale bases. Carbohydrates (primarily fructans — polymers of fructose) are the principal "
            "storage compounds, manufactured in green leaves and transported to bulb scales via the phloem. "
            "Potassium (K) plays a critical role in phloem loading and translocation of assimilates and "
            "in osmoregulation of expanding bulb cells through K+/H+ ATPase activity. "
            "Calcium is essential for cell wall integrity in rapidly expanding cells — deficiency leads to "
            "scale tip-burn and poor post-harvest quality. "
            "Sulphur compounds continue to be synthesised and stored: the ratio of S-alk(en)yl cysteine "
            "sulphoxides to pyruvate determines pungency — Zimbabwe markets generally favour pungent red types."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Maturation",
        stage_code="GS6",
        day_range=(150, 170),
        water_kc=0.55,
        water_mm_per_week=12,
        critical_nutrients=["K"],
        key_activities=[
            "Cease irrigation 2-3 weeks before planned harvest date to initiate neck drying",
            "Monitor the percentage of plants with 'tops-down' (bent or collapsed necks) — harvest when 70-80% have fallen",
            "Do not bend necks mechanically — this introduces bacterial soft rot entry points",
            "Spray final fungicide if wet weather threatens before harvest",
            "Prepare the curing area: ventilated shade structure with raised mesh or bamboo floor for air circulation under bulbs",
            "Plan and organise harvest labour, transport, and storage in advance",
        ],
        risks=[
            "Rain on mature, necked-down bulbs causes bacterial soft rot",
            "Delaying harvest beyond 80% tops-down causes skin cracking and bulb quality deterioration",
            "Premature harvest results in thin outer scales and poor storability",
        ],
        scientific_notes=(
            "Maturation is characterised by senescence of the leaf canopy and translocation of residual "
            "assimilates and nutrients from leaves to the bulb. The pseudo-stem neck collapses as "
            "vascular bundles desiccate — the progressive neck-fall (toppling) is the standard maturity "
            "indicator. Outer leaf sheaths dry to form the papery tunic layers that protect the bulb in "
            "storage. Alliinase enzyme activity, which catalyses the conversion of cysteine sulphoxides to "
            "pungent thiosulphinates on cell disruption (cutting), is maximal at full maturity. "
            "Withdrawal of irrigation accelerates the senescence process via ABA (abscisic acid) "
            "accumulation which promotes stomatal closure, chlorophyll degradation, and organic solute "
            "redistribution. Each day of delayed harvest beyond 80% tops-fall in wet conditions "
            "increases soft rot losses approximately 1-2% per day."
        ),
    ),
]


ONION_FERTILIZER = FertilizerSchedule(
    basal={
        "product": "Compound S (7:21:7) — or local equivalent high-phosphorus basal compound",
        "rate_kg_ha": 400,
        "n_kg_ha": 28,
        "p_kg_ha": 84,
        "k_kg_ha": 28,
        "timing": "Incorporated 2-3 days before transplanting; banded 5-7 cm below and to the side of planting rows",
        "notes": (
            "High phosphorus (P) at planting is critical for rapid root system establishment in transplants. "
            "If soil P is very low (Mehlich-3 P < 15 ppm), supplement with 150 kg/ha Single Superphosphate "
            "incorporated alongside the basal compound. Add 30 kg/ha sulphur (as single superphosphate or "
            "gypsum) to support flavour compound synthesis in the bulb. "
            "Carry out a soil test before the season and adjust compound rates accordingly."
        ),
    },
    top_dress_1={
        "product": "Ammonium Nitrate (34.5% N)",
        "rate_kg_ha": 200,
        "n_kg_ha": 69,
        "timing": "4 weeks after transplanting (approximately 60 days from sowing / GS3 start)",
        "notes": (
            "Side-dress in a band 5-7 cm to the side of the row and water in immediately. "
            "Do not apply on wet foliage — ammonium nitrate on leaves causes scorch. "
            "This application drives the main phase of leaf canopy development. "
            "Can substitute Calcium Ammonium Nitrate (CAN, 27% N) to simultaneously supply Ca — "
            "recommended where calcium deficiency has been noted (240 kg/ha CAN equivalent)."
        ),
    },
    top_dress_2={
        "product": "Ammonium Nitrate (34.5% N)",
        "rate_kg_ha": 200,
        "n_kg_ha": 69,
        "timing": "8 weeks after transplanting (approximately at bulb initiation / GS4 start)",
        "notes": (
            "Final nitrogen application. Applied at bulb initiation to support rapid cell expansion "
            "and scale development. Do NOT apply nitrogen after this point — late nitrogen delays "
            "maturity, produces thick necks, and reduces storability. "
            "At this application, consider supplementing with Potassium Chloride (KCl, 60% K2O) at "
            "100 kg/ha if soil potassium is below target (K > 150 ppm on Mehlich-3 test). "
            "Irrigate in immediately after application."
        ),
    },
    foliar={
        "product": "Zinc Sulphate (ZnSO4) + Solubor (boron) + Manganese Sulphate",
        "rate": "Zn: 2 g/L; B (Solubor): 1 g/L; Mn: 1 g/L water",
        "timing": (
            "Apply 2-3 times during vegetative growth: at 3, 6, and 9 weeks after transplanting. "
            "Can be tank-mixed with fungicide sprays if pH-compatible."
        ),
        "notes": (
            "Zinc deficiency is common on sandy, high-pH, and P-enriched soils in Zimbabwe. "
            "Symptoms: stunted growth, small leaves, mottled yellow older leaves. "
            "Boron is essential for cell wall formation and pollen viability. "
            "Apply foliar sprays in early morning or late afternoon to avoid leaf scorch. "
            "A dedicated calcium nitrate foliar (5 g/L) should be applied 2-3 times from "
            "GS4 onward to support bulb scale cell wall integrity and reduce post-harvest breakdown."
        ),
    },
    liming={
        "target_ph": "6.0-7.0 (optimal 6.5)",
        "product": "Agricultural lime (calcitic CaCO3 or dolomitic CaMg(CO3)2)",
        "rate": "As per soil test: typically 1.5-3.0 t/ha calcitic lime to raise pH 0.5-1.0 unit",
        "timing": "Apply 4-8 weeks before transplanting and incorporate thoroughly by disking or ripping",
        "notes": (
            "Onions are moderately sensitive to soil acidity. Below pH 5.5, aluminium toxicity "
            "damages roots and phosphorus becomes locked in soil. Above pH 7.0, micronutrients "
            "(Zn, Mn, B) become less available. Zimbabwe's granitic sandy soils (kaolinitic, NR IIa) "
            "are naturally acidic (pH 4.5-5.5) and require routine liming. "
            "Dolomitic lime is preferred on Mg-deficient soils (common on deep sandy soils in NR III-IV). "
            "Note: never apply lime and ammonium nitrogen fertilizers at the same time — wait at least 2 weeks."
        ),
    },
    notes=(
        "Total season nutrient targets for a 30 t/ha yield: 120-150 kg N/ha, 80-100 kg P2O5/ha, "
        "100-150 kg K2O/ha, 25-35 kg S/ha. "
        "Sulphur is particularly important for onion pungency and flavour; apply 30 kg S/ha total via "
        "single superphosphate in the basal dressing. "
        "Split nitrogen applications (basal P + 2x AN top-dress) reduce leaching losses on sandy soils "
        "and match crop demand timing — a proven practice for Zimbabwe highveld sandy loams. "
        "Always soil-test before the season and calibrate fertilizer rates to soil results. "
        "Compost or kraal manure (5-10 t/ha) incorporated before planting improves water retention, "
        "soil biology, and reduces fertilizer requirement on degraded soils."
    ),
)


ONION_PLANTING_WINDOWS: List[PlantingWindow] = [
    PlantingWindow(
        region="NR I - Eastern Highlands (Chimanimani, Nyanga, Vumba)",
        optimal_start="March 1",
        optimal_end="April 30",
        acceptable_start="February 15",
        acceptable_end="May 15",
        notes=(
            "Winter crop under irrigation. Cool highland climate (mean temp 12-18 degC) is "
            "ideal for producing high-quality, pungent red and brown onions. "
            "Sow seed in nursery February-March; transplant March-April into prepared ridges. "
            "Texas Grano and Red Creole perform well. Harvest July-October. "
            "Downy mildew risk is highest in this zone during the cool misty winter; "
            "preventive metalaxyl-mancozeb programmes are essential. "
            "Day length in March-April (12.0-11.5 hours at 19 degS) is suitable for short-day varieties."
        ),
    ),
    PlantingWindow(
        region="NR IIa / IIb - Highveld (Mashonaland Central, East, West)",
        optimal_start="March 15",
        optimal_end="May 31",
        acceptable_start="March 1",
        acceptable_end="June 15",
        notes=(
            "Main commercial onion production zone. Winter crop under irrigation on deep "
            "sandy loams following the summer maize crop. "
            "Sow nursery February-March; transplant March-May. Harvest August-October. "
            "Texas Grano 502 (white/brown) and Red Creole C-5 are the dominant commercial varieties. "
            "These are short-day types that initiate bulbing as day length drops below 12.5 hours "
            "(May-June, latitude 17-18 degS) — planting too late risks premature bulbing before "
            "adequate leaf mass is built, producing small bulbs. "
            "Thrips are the major pest constraint in the dry winter months; weekly monitoring essential. "
            "Target transplanting density: 100,000-130,000 plants/ha."
        ),
    ),
    PlantingWindow(
        region="NR III - Semi-intensive (parts of Midlands, Masvingo)",
        optimal_start="April 1",
        optimal_end="May 31",
        acceptable_start="March 15",
        acceptable_end="June 15",
        notes=(
            "Irrigation essential. Similar timing to NR IIa/IIb. Risk of warm mid-season "
            "temperatures (October-November maturation period) reduces storability of bulbs "
            "harvested late. Aim for September-October harvest. "
            "Red Creole tolerates slightly drier and warmer conditions and suits this zone. "
            "Late plantings (after June) risk bulbing triggered before adequate canopy is built "
            "due to declining day length — avoid transplanting after June 15."
        ),
    ),
    PlantingWindow(
        region="NR IIa/IIb/III - Summer Crop (August-September transplanting)",
        optimal_start="August 1",
        optimal_end="September 15",
        acceptable_start="July 20",
        acceptable_end="September 30",
        notes=(
            "A second, smaller summer production window exists for mid-season day-length-neutral "
            "or long-day variety types. Seed sown June-July in nursery; transplanted August-September. "
            "Harvested December-January. "
            "This window suits varieties such as Pukekohe Longkeeper (intermediate day) "
            "or newer hybrid types. NOT suitable for Texas Grano or Red Creole which will bulb "
            "prematurely on increasing day lengths if transplanted in August (days lengthening). "
            "Risk of harvest coinciding with early rains (December-January) increases bacterial "
            "soft rot and storage losses — plan rapid post-harvest curing accordingly. "
            "Primary use: fresh market supply during December lean season."
        ),
    ),
]


PROFILE = CropProfile(
    crop_name="Onion",
    scientific_name="Allium cepa",
    family="Amaryllidaceae",

    optimal_ph=(6.0, 7.0),
    critical_ph_low=5.5,
    optimal_soil_types=[
        "well-drained sandy loam",
        "silt loam",
        "light loam with good structure",
        "alluvial river-valley soils",
    ],
    avoid_soil_types=[
        "heavy clay (poor drainage, compaction risk)",
        "waterlogged or vlei soils",
        "highly acidic soils (pH < 5.5) without liming",
        "coarse sandy soils with very low water-holding capacity",
        "vertisol (cracking clay — difficult to manage irrigation)",
    ],

    optimal_temp=(13.0, 25.0),
    critical_temp_low=-2.0,
    critical_temp_high=35.0,
    base_temp_gdd=7.0,
    total_water_mm=450.0,

    growth_stages=ONION_GROWTH_STAGES,
    fertilizer_schedule=ONION_FERTILIZER,
    diseases=ONION_DISEASES,
    pests=ONION_PESTS,
    planting_windows=ONION_PLANTING_WINDOWS,

    harvest_moisture="Harvest when 70-80% of plants have fallen tops; outer scales beginning to papery-dry; bulbs firm",
    storage_conditions=(
        "Ideal: 0-2 degC, 65-70% RH for up to 6-8 months. "
        "Ambient Zimbabwe storage: well-ventilated shade structure, 18-25 degC, low humidity. "
        "Avoid storage above 28 degC or below 5 degC (sprouting zone is 5-18 degC — "
        "store either colder or warmer than this range). "
        "Stack bulbs in slatted wooden crates or hang in mesh bags — never in closed sacks."
    ),
    post_harvest_notes=(
        "Cure bulbs immediately after harvest in a well-ventilated shade structure for 3-4 weeks until "
        "outer skins are completely papery and the neck is fully dry and sealed. "
        "Curing at 28-32 degC with good airflow is ideal; avoid curing in direct sun (surface scorching). "
        "Trim dried roots to 1 cm and retain 2-3 cm of dry neck. "
        "Grade by size: premium large (> 65 mm diameter), standard (45-65 mm), small (< 45 mm). "
        "Reject all bulbs with soft necks, discolouration, or signs of disease. "
        "For seed stock selection: reserve the largest, best-shaped, most uniformly coloured bulbs "
        "from healthy plants for replanting (or save from a certified variety source). "
        "Texas Grano and Red Creole have moderate storage life (3-4 months at ambient); "
        "for longer storage life, consider pungent varieties (high pyruvate content) which store better. "
        "In Zimbabwe commercial context, onions are often sold direct from harvest or within 6-8 weeks "
        "at ambient temperature; for exports or longer marketing windows, cold chain is essential."
    ),

    natural_region_suitability={
        "I": (
            "Excellent — cool Eastern Highlands ideal for high-quality pungent onion production. "
            "Manage downy mildew rigorously. "
            "Premium niche for export-quality Red Creole."
        ),
        "IIa": (
            "Excellent — main commercial production zone. Irrigated winter crop after maize. "
            "Texas Grano 502 and Red Creole dominant. Thrips is the primary pest challenge."
        ),
        "IIb": (
            "Very good — similar to NR IIa under irrigation. "
            "Slightly higher temperatures toward end of season accelerate maturity."
        ),
        "III": (
            "Good under irrigation. Similar management to NR IIa/IIb. "
            "Harvest timing critical to avoid hot, early wet-season rains. Red Creole preferred."
        ),
        "IV": (
            "Marginal — possible under full irrigation in river-valley alluvials "
            "(Limpopo, Sabi, Mzingwane). High heat and water demand are constraints. "
            "Short-season varieties and careful timing required."
        ),
        "V": (
            "Generally unsuitable — excessive heat and water scarcity. "
            "Small-scale production possible in well-watered valley gardens during cooler months only."
        ),
    },
)

ALIASES: list = ["onions", "hanyanisi"]
