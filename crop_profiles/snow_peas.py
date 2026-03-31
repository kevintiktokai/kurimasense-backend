"""Snow Peas (Pisum sativum var. saccharatum) — export vegetable with flat edible pods, cool-season legume."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List


SNOW_PEA_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Powdery Mildew",
        pathogen="Erysiphe pisi",
        pathogen_type="fungal",
        symptoms=[
            "White powdery coating on leaves, stems, and pods",
            "Yellowing and premature senescence of affected leaves",
            "Pod surface becomes rough and unmarketable",
            "Severe infections cause plant defoliation",
        ],
        identification_markers=[
            "White talcum-powder-like growth on upper leaf surface first",
            "Distinct from downy mildew (which is on underside and grey-purple)",
            "Spreads rapidly in dry weather with cool nights",
            "Cleistothecia (tiny dark dots) visible in late infections",
        ],
        favourable_conditions={
            "humidity_min": 50, "temp_min_c": 15, "temp_max_c": 25,
            "note": "Dry days with cool, humid nights. Unlike most fungi, does "
                    "NOT require free water — high RH alone is sufficient."
        },
        susceptible_stages=["flowering", "pod_fill"],
        resistant_varieties=["Oregon Sugar Pod II"],
        susceptible_varieties=["Sugar Snap (moderate)"],
        chemical_control=[
            {"name": "Sulphur 80 WP", "rate": "2.0-3.0 kg/ha",
             "phi_days": "7", "notes": "Protectant; apply before symptoms. Do not apply above 30°C."},
            {"name": "Myclobutanil 200 EW", "rate": "0.3 L/ha",
             "phi_days": "14", "notes": "Systemic triazole; apply at first sign of disease."},
            {"name": "Azoxystrobin 250 SC", "rate": "0.4 L/ha",
             "phi_days": "7", "notes": "Strobilurin; preventive use, max 2 applications per season."},
        ],
        biological_control=[
            "Bacillus subtilis-based products (e.g., Serenade) as preventive sprays",
            "Potassium bicarbonate foliar sprays (disrupts fungal cell walls)",
        ],
        cultural_control=[
            "Select resistant varieties such as Oregon Sugar Pod II",
            "Ensure good air circulation with appropriate plant spacing (15-20 cm in-row)",
            "Avoid excessive nitrogen which promotes succulent growth susceptible to mildew",
            "Remove and destroy crop debris after harvest",
            "Rotate with non-legume crops for at least 2 seasons",
        ],
        economic_threshold="10% of leaf area affected or any pod infection (export zero-tolerance on pods)",
        severity_scale={
            "mild": "Scattered patches on lower leaves, <10% leaf area",
            "moderate": "20-40% leaf area, beginning to reach pods",
            "severe": ">40% leaf area, pod infection — crop unmarketable for export",
        },
    ),
    DiseaseProfile(
        name="Downy Mildew",
        pathogen="Peronospora viciae",
        pathogen_type="fungal",
        symptoms=[
            "Yellow to pale green patches on upper leaf surface",
            "Grey-purple fuzzy sporulation on leaf undersides",
            "Systemic infection causes stunted, distorted plants",
            "Pod infection results in brown discolouration",
        ],
        identification_markers=[
            "Grey-purple sporulation on UNDERSIDE of leaves (distinguishes from powdery mildew)",
            "Yellow angular patches on upper surface correspond to sporulation below",
            "Systemically infected plants are stunted with downward-curled leaves",
        ],
        favourable_conditions={
            "humidity_min": 85, "temp_min_c": 5, "temp_max_c": 18,
            "leaf_wetness_hours": 6,
            "note": "Cool, wet weather with prolonged leaf wetness. Morning dews and fog ideal."
        },
        susceptible_stages=["seedling", "vegetative", "flowering"],
        resistant_varieties=[],
        susceptible_varieties=["Most commercial varieties show some susceptibility"],
        chemical_control=[
            {"name": "Metalaxyl-M + Mancozeb (Ridomil Gold MZ)", "rate": "2.5 kg/ha",
             "phi_days": "14", "notes": "Apply preventively; systemic + contact combination."},
            {"name": "Fosetyl-Al 80 WP", "rate": "2.0-3.0 kg/ha",
             "phi_days": "14", "notes": "Systemic; stimulates plant defence (phytoalexins)."},
        ],
        biological_control=[
            "Copper hydroxide at low rates as protectant",
            "Trichoderma harzianum soil drench to reduce soilborne inoculum",
        ],
        cultural_control=[
            "Use certified disease-free seed",
            "Avoid overhead irrigation; use drip where possible",
            "Plant in well-drained soils with good air movement",
            "Remove infected plants immediately (roguing)",
            "Rotate away from peas and beans for 3+ years",
        ],
        economic_threshold="5% incidence of systemically infected plants; any pod symptoms",
        severity_scale={
            "mild": "Scattered leaf lesions, <5% plants affected",
            "moderate": "10-25% plants showing foliar symptoms",
            "severe": ">25% plants affected or pod infection — major yield and quality loss",
        },
    ),
    DiseaseProfile(
        name="Ascochyta Blight",
        pathogen="Ascochyta pisi / Mycosphaerella pinodes",
        pathogen_type="fungal",
        symptoms=[
            "Dark brown to purple-black lesions on stems, leaves, and pods",
            "Stem base lesions cause foot rot and plant collapse",
            "Pod lesions are sunken with dark margins",
            "Seed infection causes brown discolouration and shrivelling",
        ],
        identification_markers=[
            "Concentric ring pattern within lesions (target-spot appearance)",
            "Pycnidia (tiny dark dots) visible within older lesions",
            "Foot rot at stem base with dark purple-black discolouration",
        ],
        favourable_conditions={
            "humidity_min": 80, "temp_min_c": 15, "temp_max_c": 25,
            "rainfall": "Frequent rain or overhead irrigation",
            "note": "Warm, wet weather. Seed-borne and residue-borne pathogen."
        },
        susceptible_stages=["seedling", "flowering", "pod_fill"],
        resistant_varieties=[],
        susceptible_varieties=["Most pea varieties susceptible to M. pinodes complex"],
        chemical_control=[
            {"name": "Chlorothalonil 500 SC", "rate": "2.0 L/ha",
             "phi_days": "14", "notes": "Protectant; apply before flowering and repeat at 10-14 day intervals."},
            {"name": "Mancozeb 80 WP", "rate": "2.0-2.5 kg/ha",
             "phi_days": "14", "notes": "Protectant; alternate with chlorothalonil."},
        ],
        biological_control=[
            "Seed treatment with Trichoderma spp. to protect seedlings",
            "Bacillus amyloliquefaciens foliar spray",
        ],
        cultural_control=[
            "Use certified disease-free seed or treat seed with fungicide",
            "Rotate away from all legumes for 3-4 years",
            "Bury crop residue by ploughing to reduce inoculum",
            "Avoid overhead irrigation during flowering and pod fill",
            "Plant in well-drained, open sites with good air circulation",
        ],
        economic_threshold="10% plants with stem base lesions or any pod lesions in export crops",
        severity_scale={
            "mild": "Leaf lesions only, <10% leaf area",
            "moderate": "Stem lesions present, 10-30% leaf area affected",
            "severe": "Foot rot causing plant death, pod infection — major losses",
        },
    ),
]


SNOW_PEA_PESTS: List[PestProfile] = [
    PestProfile(
        name="Pea Aphid",
        scientific_name="Acyrthosiphon pisum",
        pest_type="insect",
        identification=[
            "Large (3-4 mm) bright green aphid with long legs and antennae",
            "Colonies on growing tips, tendrils, and flower buds",
            "Winged forms appear when colonies are crowded",
            "Cast skins (white exuviae) on leaves indicate infestation",
        ],
        damage_symptoms=[
            "Curled and distorted growing tips",
            "Honeydew deposits leading to sooty mould on pods",
            "Reduced pod set and misshapen pods",
            "Vector of Pea Enation Mosaic Virus and Bean Leaf Roll Virus",
        ],
        life_cycle_notes=(
            "Parthenogenetic reproduction in warm conditions; one generation every "
            "7-10 days. Winged females migrate from other legume hosts. Populations "
            "explode rapidly in cool, dry weather (15-25°C)."
        ),
        favourable_conditions={
            "temp_min_c": 15, "temp_max_c": 25,
            "note": "Cool to moderate temperatures, low rainfall. Populations crash above 30°C "
                    "or during heavy rain."
        },
        susceptible_stages=["vegetative", "flowering", "pod_fill"],
        economic_threshold="30-50 aphids per plant or 10 aphids per growing tip (export: lower thresholds apply)",
        chemical_control=[
            {"name": "Pirimicarb 50 WG (Pirimor)", "rate": "250 g/ha",
             "phi_days": "7", "notes": "Selective aphicide; safe to beneficials."},
            {"name": "Acetamiprid 20 SP", "rate": "100-150 g/ha",
             "phi_days": "7", "notes": "Neonicotinoid; avoid during flowering if pollinators present."},
        ],
        biological_control=[
            "Ladybirds (Coccinellidae) — both adults and larvae are voracious aphid predators",
            "Parasitoid wasp Aphidius ervi (mummified aphids indicate parasitism)",
            "Lacewing larvae (Chrysoperla spp.)",
            "Entomopathogenic fungi (Beauveria bassiana) under humid conditions",
        ],
        cultural_control=[
            "Monitor weekly from emergence; scout growing tips and undersides of leaves",
            "Avoid excessive nitrogen fertilisation which promotes aphid population growth",
            "Use reflective mulches to deter alate (winged) aphid landing",
            "Remove volunteer legumes and weeds that harbour aphids",
        ],
        scouting_protocol=(
            "Scout 20 plants in a W-pattern across the field twice per week. "
            "Count aphids on 3 growing tips per plant. Record presence of natural enemies. "
            "Spray only if threshold exceeded AND beneficial:pest ratio is below 1:30."
        ),
    ),
    PestProfile(
        name="Thrips",
        scientific_name="Thrips tabaci / Frankliniella occidentalis",
        pest_type="insect",
        identification=[
            "Tiny (1-2 mm) slender insects, pale yellow to brown",
            "Fringed wings visible under magnification",
            "Fast-moving; hide in flowers and leaf folds",
            "Tap plant over white paper to dislodge and count",
        ],
        damage_symptoms=[
            "Silver-white feeding scars (stippling) on leaves and pods",
            "Distorted flowers leading to poor pod set",
            "Brown scarring on pods renders them unmarketable for export",
            "Vector of Tomato Spotted Wilt Virus (TSWV)",
        ],
        life_cycle_notes=(
            "Complete generation in 14-20 days. Pupation occurs in soil. "
            "F. occidentalis (Western Flower Thrips) is more damaging and insecticide-resistant "
            "than T. tabaci. Populations peak during warm, dry periods."
        ),
        favourable_conditions={
            "temp_min_c": 20, "temp_max_c": 30,
            "note": "Warm, dry conditions. Populations decline during heavy rains."
        },
        susceptible_stages=["flowering", "pod_fill"],
        economic_threshold="5-10 thrips per flower; any pod scarring in export crops",
        chemical_control=[
            {"name": "Spinosad 240 SC (Tracer)", "rate": "200-300 mL/ha",
             "phi_days": "3", "notes": "Naturalyte; excellent for WFT. Short PHI suits export."},
            {"name": "Abamectin 18 EC", "rate": "300-500 mL/ha",
             "phi_days": "7", "notes": "Translaminar; targets larvae in flowers."},
        ],
        biological_control=[
            "Predatory mites (Amblyseius swirskii) in protected production",
            "Orius spp. (minute pirate bugs) are effective thrips predators",
            "Beauveria bassiana sprays under humid conditions",
        ],
        cultural_control=[
            "Blue or yellow sticky traps for monitoring (blue more attractive to thrips)",
            "Remove weed hosts (especially Compositae) around field margins",
            "Avoid planting near onion or tobacco fields (thrips reservoirs)",
            "Overhead irrigation can physically dislodge thrips and raise humidity",
        ],
        scouting_protocol=(
            "Inspect 20 flowers across the field using a 10x hand lens. "
            "Tap flowers onto white paper and count thrips. Check twice weekly "
            "during flowering. Use blue sticky traps at canopy height for early warning."
        ),
    ),
    PestProfile(
        name="Leaf Miner",
        scientific_name="Liriomyza huidobrensis",
        pest_type="insect",
        identification=[
            "Adult is a small (2 mm) black and yellow fly",
            "Larvae are pale yellow maggots mining inside leaf tissue",
            "Mines appear as winding white-grey trails on leaves",
            "Puncture marks from adult feeding visible as small white dots",
        ],
        damage_symptoms=[
            "Serpentine mines reduce photosynthetic area",
            "Heavy mining causes leaf drop and plant stress",
            "Aesthetic damage makes pods unmarketable if mines on pods",
            "Entry wounds allow secondary infection by bacterial pathogens",
        ],
        life_cycle_notes=(
            "Egg to adult in 15-25 days depending on temperature. Females insert eggs "
            "into leaf tissue with ovipositor. Pupation occurs in soil. Polyphagous pest "
            "with wide host range including beans, lettuce, and ornamentals."
        ),
        favourable_conditions={
            "temp_min_c": 18, "temp_max_c": 30,
            "note": "Warm, dry conditions. Protected cropping (tunnels) particularly vulnerable."
        },
        susceptible_stages=["vegetative", "flowering", "pod_fill"],
        economic_threshold="5 active mines per leaf or >20% leaves with mines",
        chemical_control=[
            {"name": "Cyromazine 75 WP (Trigard)", "rate": "150-200 g/ha",
             "phi_days": "7", "notes": "IGR; disrupts larval moulting. Very selective."},
            {"name": "Abamectin 18 EC", "rate": "300-500 mL/ha",
             "phi_days": "7", "notes": "Translaminar activity reaches larvae in mines."},
        ],
        biological_control=[
            "Parasitoid wasps Diglyphus isaea and Dacnusa sibirica (in tunnels)",
            "Encourage natural parasitism by avoiding broad-spectrum insecticides",
        ],
        cultural_control=[
            "Use yellow sticky traps to monitor adult fly populations",
            "Remove and destroy heavily mined leaves",
            "Destroy crop residues promptly after harvest to kill pupae",
            "Rotate with non-host crops (cereals, alliums)",
        ],
        scouting_protocol=(
            "Inspect 25 leaves from middle canopy across the field twice weekly. "
            "Count active mines (with live larvae — hold leaf to light). "
            "Use yellow sticky traps at canopy height to detect adult emergence peaks."
        ),
    ),
]


SNOW_PEA_GROWTH_STAGES: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Germination & Emergence",
        stage_code="GE",
        day_range=(0, 8),
        water_kc=0.4,
        water_mm_per_week=15,
        critical_nutrients=["Phosphorus", "Molybdenum"],
        key_activities=[
            "Direct seed at 3-4 cm depth, 5-8 cm apart in rows 60-75 cm apart",
            "Inoculate seed with Rhizobium leguminosarum if field not previously cropped to peas",
            "Apply basal fertiliser at planting",
            "Erect trellis/support netting at planting (1.5-1.8 m height)",
        ],
        risks=["Damping-off (Pythium, Rhizoctonia)", "Bird damage to seed", "Cold waterlogged soils"],
        scientific_notes=(
            "Peas germinate at soil temperatures as low as 4°C but optimal is 10-18°C. "
            "Rhizobium inoculation is critical for N-fixation; compatible strain required. "
            "Hypogeal germination — cotyledons remain below ground."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Vegetative Growth & Vine Development",
        stage_code="VG",
        day_range=(9, 25),
        water_kc=0.6,
        water_mm_per_week=25,
        critical_nutrients=["Nitrogen (early)", "Phosphorus", "Potassium"],
        key_activities=[
            "Train vines onto trellis as tendrils develop",
            "Weed control — peas are poor competitors early on",
            "Scout for aphids on growing tips",
            "Begin fungicide programme if downy mildew risk is high",
        ],
        risks=["Weed competition", "Aphid colonisation", "Downy mildew in wet conditions"],
        scientific_notes=(
            "Indeterminate growth habit means vegetative and reproductive growth overlap. "
            "Nodulation begins 10-14 days after emergence — N-fixation contribution increases "
            "from this point. Photoperiod-sensitive: long days accelerate flowering."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Flowering",
        stage_code="FL",
        day_range=(26, 40),
        water_kc=0.85,
        water_mm_per_week=35,
        critical_nutrients=["Phosphorus", "Potassium", "Boron", "Calcium"],
        key_activities=[
            "Maintain consistent irrigation — water stress causes flower drop",
            "Scout for thrips in flowers (use 10x hand lens)",
            "Apply foliar boron if deficiency suspected (poor pod set)",
            "Begin powdery mildew fungicide programme",
        ],
        risks=["Thrips damage to flowers", "Powdery mildew onset", "Heat stress (>27°C) causing flower abortion"],
        scientific_notes=(
            "Snow peas are largely self-pollinating but insect visitation improves pod set. "
            "Flowers are borne at nodes on main stem and laterals. Optimal flowering "
            "temperature is 15-20°C; above 27°C pollen viability drops sharply. "
            "Boron is critical for pollen tube growth and fertilisation."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Pod Development (Flat Pod Stage)",
        stage_code="PD",
        day_range=(41, 55),
        water_kc=0.95,
        water_mm_per_week=40,
        critical_nutrients=["Potassium", "Calcium", "Nitrogen"],
        key_activities=[
            "Begin harvesting when pods are flat, bright green, with barely visible seeds",
            "Harvest every 2-3 days to maintain quality and stimulate continued production",
            "Maintain cold chain immediately after harvest (hydrocool or shade)",
            "Continue pest and disease monitoring",
        ],
        risks=["Over-mature pods (seeds swelling) become unmarketable", "Pod scarring from thrips/leaf miner",
               "Powdery mildew on pods"],
        scientific_notes=(
            "Snow peas are harvested at the flat pod stage before seeds develop — the entire pod "
            "is edible due to reduced parchment layer (recessive p and v genes). "
            "Sugar content is highest at this stage. Delayed harvest by even 1-2 days "
            "causes seed swell, reducing export grade."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Continued Harvest & Production",
        stage_code="CH",
        day_range=(56, 70),
        water_kc=0.85,
        water_mm_per_week=35,
        critical_nutrients=["Potassium", "Nitrogen (maintenance)"],
        key_activities=[
            "Continue regular picking every 2-3 days",
            "Apply foliar potassium to support continued pod production",
            "Monitor plant vigour — reduce irrigation as production declines",
            "Plan crop termination when quality drops",
        ],
        risks=["Plant exhaustion", "Increased disease pressure on ageing canopy",
               "Market oversupply if harvest window is long"],
        scientific_notes=(
            "Indeterminate peas continue flowering and podding as long as pods are removed. "
            "Regular picking prevents seed development which signals the plant to senesce "
            "(source-sink regulation). Total harvest period may extend to 4-6 weeks under "
            "optimal conditions."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Senescence & Crop Termination",
        stage_code="SE",
        day_range=(71, 85),
        water_kc=0.4,
        water_mm_per_week=15,
        critical_nutrients=[],
        key_activities=[
            "Final harvest of remaining marketable pods",
            "Cut plants at soil level (leave roots for N-fixation residual)",
            "Incorporate residues for green manure benefit",
            "Plan rotation — follow with nitrogen-demanding crop (e.g., brassicas)",
        ],
        risks=["Disease build-up on old tissue", "Volunteer pea seedlings in next crop"],
        scientific_notes=(
            "Senescing pea plants release approximately 30-50 kg N/ha through root nodule "
            "decomposition and residue mineralisation, benefiting subsequent crops. "
            "Leaving roots intact preserves soil structure and maximises N contribution."
        ),
    ),
]


SNOW_PEA_FERTILIZER = FertilizerSchedule(
    basal={
        "product": "Compound S (7:21:7) or Single Super Phosphate",
        "rate": "200-300 kg/ha Compound S",
        "timing": "At planting, banded 5 cm below and to the side of seed",
        "nutrients": "14-63 kg N, 42-63 kg P₂O₅, 14-21 kg K₂O per ha",
        "note": "Peas fix their own N via Rhizobium; P is most critical at establishment.",
    },
    top_dress_1={
        "product": "Potassium Chloride (Muriate of Potash) or Potassium Sulphate",
        "rate": "50-100 kg/ha KCl",
        "timing": "At onset of flowering (day 25-30)",
        "nutrients": "30-60 kg K₂O per ha",
        "note": "K supports pod quality and sugar content. Use K₂SO₄ if soil S is low.",
    },
    top_dress_2=None,
    foliar={
        "product": "Solubor (boron) + Calcium Chloride",
        "rate": "1 kg/ha Solubor + 3 kg/ha CaCl₂ in 500 L water",
        "timing": "At early flowering and repeat 10 days later",
        "note": "Boron for pollen viability; calcium for pod wall integrity.",
    },
    liming={
        "ite": "Apply agricultural lime if pH < 5.8",
        "rate": "1-2 t/ha depending on buffer pH",
        "timing": "At least 3 months before planting",
        "note": "Rhizobium activity optimal at pH 6.0-7.0; liming critical for N-fixation.",
    },
    notes=(
        "Snow peas are legumes and fix 50-100 kg N/ha via Rhizobium symbiosis. "
        "Excessive N fertiliser suppresses nodulation and promotes vegetative growth at the "
        "expense of pod production. Focus fertiliser inputs on P, K, and micronutrients."
    ),
)


SNOW_PEA_PLANTING_WINDOWS: List[PlantingWindow] = [
    PlantingWindow(
        region="Highveld (NR II) — Harare, Marondera, Chinhoyi",
        optimal_start="April 15",
        optimal_end="June 15",
        acceptable_start="March 15",
        acceptable_end="July 15",
        notes=(
            "Cool dry season planting under irrigation. Frost risk June-August: "
            "use frost cloth on very cold nights. Avoid planting into hot wet season."
        ),
    ),
    PlantingWindow(
        region="Eastern Highlands (NR I) — Nyanga, Juliasdale, Chimanimani",
        optimal_start="March 1",
        optimal_end="August 31",
        acceptable_start="February 15",
        acceptable_end="September 15",
        notes=(
            "High altitude provides cool conditions year-round; most productive area. "
            "Can grow almost continuously with staggered plantings. Watch for excessive "
            "rain in Dec-Feb increasing disease pressure."
        ),
    ),
    PlantingWindow(
        region="Middleveld (NR III) — Mutare lowlands, Kadoma",
        optimal_start="May 1",
        optimal_end="June 30",
        acceptable_start="April 15",
        acceptable_end="July 15",
        notes=(
            "Narrower window due to higher temperatures. Must plant in cooler months. "
            "Irrigation essential. Heat stress limits summer production."
        ),
    ),
]


PROFILE = CropProfile(
    crop_name="Snow Peas",
    scientific_name="Pisum sativum var. saccharatum",
    family="Fabaceae",
    optimal_ph=(6.0, 7.0),
    critical_ph_low=5.5,
    optimal_soil_types=["fersiallitic", "siallitic"],
    avoid_soil_types=["vertisol", "lithosol"],
    optimal_temp=(12.0, 22.0),
    critical_temp_low=-2.0,
    critical_temp_high=27.0,
    base_temp_gdd=4.4,
    total_water_mm=350.0,
    growth_stages=SNOW_PEA_GROWTH_STAGES,
    fertilizer_schedule=SNOW_PEA_FERTILIZER,
    diseases=SNOW_PEA_DISEASES,
    pests=SNOW_PEA_PESTS,
    planting_windows=SNOW_PEA_PLANTING_WINDOWS,
    harvest_moisture="Pods harvested fresh; target 90%+ moisture at harvest for crispness",
    storage_conditions=(
        "Pre-cool to 0-2°C within 1 hour of harvest. Store at 0-1°C, 95% RH. "
        "Shelf life 7-10 days. Use perforated poly bags or modified atmosphere packaging "
        "for export (2-5% O₂, 3-5% CO₂)."
    ),
    post_harvest_notes=(
        "Snow peas are highly perishable. Maintain cold chain from field to packhouse. "
        "Grade by pod size (6-9 cm preferred for export), flatness, and absence of blemishes. "
        "String removal may be required for premium markets. "
        "Export mainly to EU and UK markets from Zimbabwe."
    ),
    natural_region_suitability={
        "I": "Excellent — cool temperatures, high altitude ideal for year-round production",
        "IIa": "Good — cool season production (April-August) under irrigation",
        "IIb": "Good — cool season production under irrigation",
        "III": "Marginal — limited to May-June only, heat stress risk",
        "IV": "Not suitable — too hot and dry",
        "V": "Not suitable — too hot",
    },
)

ALIASES = ["mange tout"]
