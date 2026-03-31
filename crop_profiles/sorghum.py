"""Sorghum (Sorghum bicolor) — Zimbabwe's #2 grain, critical dryland crop for NR IV-V."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List


SORGHUM_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Grain Mold Complex",
        pathogen="Fusarium spp., Aspergillus flavus, Curvularia lunata",
        pathogen_type="fungal",
        symptoms=[
            "Pink, white, grey or black discolouration of grain surface",
            "Mouldy smell from panicles at maturity",
            "Soft, chalky grain with reduced test weight",
            "Mycotoxin contamination (aflatoxin from Aspergillus)",
        ],
        identification_markers=[
            "Pink or salmon colour = Fusarium; black-green = Aspergillus",
            "Mould visible on grain within the glumes",
            "Affected grain crumbles easily when pressed",
            "Often worst in compact panicle types that trap moisture",
        ],
        favourable_conditions={
            "humidity_min": 85, "temp_min_c": 25, "temp_max_c": 35,
            "rainfall_note": "Rain during grain fill and maturity",
            "note": "High humidity and warm temperatures during grain fill. "
                    "Compact panicle types and bird-damaged grain are most susceptible. "
                    "Delayed harvest dramatically increases mould severity.",
        },
        susceptible_stages=["Grain Fill", "Maturity"],
        resistant_varieties=["Macia", "SC Sila"],
        susceptible_varieties=["White-grained open-pollinated local landraces"],
        chemical_control=[
            {"name": "Thiram 80 WP (seed treatment)", "rate": "3 g/kg seed",
             "phi_days": "N/A", "notes": "Protects seedling establishment, not grain mould directly"},
            {"name": "Mancozeb 80 WP", "rate": "2.0-2.5 kg/ha",
             "phi_days": "14", "notes": "Foliar spray at flowering if wet conditions forecast"},
        ],
        biological_control=[
            "Aflasafe (atoxigenic Aspergillus strains) applied to soil to displace toxigenic strains",
            "Trichoderma-based seed treatments reduce Fusarium inoculum",
        ],
        cultural_control=[
            "Plant open-panicle varieties that dry quickly (e.g. Macia)",
            "Time planting so maturity avoids late rains",
            "Harvest promptly at physiological maturity (black layer)",
            "Dry grain to <12.5% moisture within 48 hours of harvest",
            "Remove bird-damaged heads separately — they harbour more mould",
        ],
        economic_threshold="More than 10% of grains showing visible mould at soft dough stage",
        severity_scale={
            "mild": "< 5% grains affected, grain still marketable",
            "moderate": "5-25% grains with visible mould, test weight reduced",
            "severe": "> 25% grains mouldy, mycotoxin risk high — not safe for food without testing",
        },
    ),
    DiseaseProfile(
        name="Anthracnose",
        pathogen="Colletotrichum sublineolum",
        pathogen_type="fungal",
        symptoms=[
            "Small, circular to elliptical spots on leaves with red or tan centres",
            "Acervuli (dark fungal fruiting bodies) visible in lesion centres",
            "Leaf midrib and stalk rots in severe cases",
            "Premature leaf senescence reducing grain fill",
        ],
        identification_markers=[
            "Leaf spots with concentric rings and dark acervuli in centre",
            "Red-purple discolouration on susceptible varieties",
            "Stalk rot: internal pith discolouration when split open",
            "Distinct from other leaf spots by acervuli presence (use hand lens)",
        ],
        favourable_conditions={
            "humidity_min": 80, "temp_min_c": 25, "temp_max_c": 30,
            "leaf_wetness_hours": 12,
            "note": "Warm, humid conditions with frequent rain. Survives in crop residue. "
                    "Worse under continuous sorghum cropping.",
        },
        susceptible_stages=["Vegetative/Tillering", "Booting/Heading", "Flowering", "Grain Fill"],
        resistant_varieties=["SC Sila", "SC Smile"],
        susceptible_varieties=["Some local landraces"],
        chemical_control=[
            {"name": "Amistar Xtra (Azoxystrobin + Cyproconazole)", "rate": "0.4-0.5 L/ha",
             "phi_days": "28", "notes": "Apply at first symptoms on lower leaves"},
            {"name": "Mancozeb 80 WP", "rate": "2.0-2.5 kg/ha",
             "phi_days": "14", "notes": "Protectant; apply before heading in wet seasons"},
        ],
        biological_control=[
            "Trichoderma harzianum applied to crop residue to accelerate decomposition",
            "Crop rotation breaks the disease cycle",
        ],
        cultural_control=[
            "Rotate with non-host crops (legumes, cotton) for at least 2 seasons",
            "Plough under crop residue to reduce inoculum",
            "Use certified disease-free seed",
            "Plant resistant varieties (SC Sila, SC Smile)",
            "Avoid excessive nitrogen which promotes lush, susceptible growth",
        ],
        economic_threshold="Lesions on 10% of leaf area before heading",
        severity_scale={
            "mild": "Scattered lesions on lower leaves only",
            "moderate": "Lesions on 10-30% of leaf area, reaching flag leaf",
            "severe": "> 30% leaf area blighted plus stalk rot — 30-50% yield loss",
        },
    ),
    DiseaseProfile(
        name="Leaf Blight",
        pathogen="Exserohilum turcicum",
        pathogen_type="fungal",
        symptoms=[
            "Long, elliptical grey-green lesions on leaves",
            "Lesions may reach 15 cm in length",
            "Lesions coalesce causing extensive leaf death",
            "Severe cases lead to premature drying of entire canopy",
        ],
        identification_markers=[
            "Elliptical lesions (not rectangular like GLS in maize)",
            "Grey-green initially, turning tan-brown with age",
            "Starts on lower leaves and progresses upward",
            "Dark sporulation on underside of lesions in humid weather",
        ],
        favourable_conditions={
            "humidity_min": 75, "temp_min_c": 18, "temp_max_c": 27,
            "note": "Moderate temperatures with high humidity and frequent dew. "
                    "Common in NR II-III during mid-season wet spells.",
        },
        susceptible_stages=["Vegetative/Tillering", "Booting/Heading", "Flowering"],
        resistant_varieties=["Macia", "SC Smile"],
        susceptible_varieties=["Some local landraces"],
        chemical_control=[
            {"name": "Propiconazole 250 EC", "rate": "0.5 L/ha",
             "phi_days": "21", "notes": "Systemic triazole; apply at early symptoms"},
            {"name": "Mancozeb 80 WP", "rate": "2.0-2.5 kg/ha",
             "phi_days": "14", "notes": "Protectant spray in wet weather"},
        ],
        biological_control=[
            "Crop residue management reduces carry-over inoculum",
            "Balanced nutrition improves plant resistance",
        ],
        cultural_control=[
            "Crop rotation with legumes or cotton",
            "Bury infected residue by ploughing",
            "Plant tolerant varieties",
            "Avoid late planting in high-rainfall zones",
        ],
        economic_threshold="Lesions reaching flag leaf before grain fill",
        severity_scale={
            "mild": "Scattered lesions on lower leaves",
            "moderate": "Lesions on 20-40% of leaf area",
            "severe": "> 40% leaf area blighted — significant yield loss expected",
        },
    ),
]


SORGHUM_PESTS: List[PestProfile] = [
    PestProfile(
        name="Stem Borer (Chilo partellus)",
        scientific_name="Chilo partellus",
        pest_type="insect",
        identification=[
            "Adult moth: straw-coloured, 20-25 mm wingspan",
            "Larvae: creamy-white with brown head capsule, up to 25 mm",
            "Pupae found inside stem tunnels",
            "Egg masses laid on underside of leaves near midrib",
        ],
        damage_symptoms=[
            "Dead heart in young plants (central shoot dies and pulls out easily)",
            "Stem tunnelling visible when stalk is split",
            "Chaffy or partially filled panicles from peduncle damage",
            "Frass (sawdust-like excrement) at stem borer entry points",
        ],
        life_cycle_notes=(
            "Eggs hatch in 5-7 days. Larvae initially feed on leaf whorls, "
            "then bore into stems. Larval period 25-35 days. Pupation inside "
            "stem for 7-10 days. 2-3 generations per season in Zimbabwe lowveld. "
            "Diapauses in dry crop stalks over winter."
        ),
        favourable_conditions={
            "temp_min_c": 25, "temp_max_c": 35,
            "note": "Warm conditions accelerate development. Carry-over in uncleared "
                    "maize and sorghum stubble is main inoculum source.",
        },
        susceptible_stages=["Emergence", "Vegetative/Tillering", "Booting/Heading"],
        economic_threshold="5-10% plants showing dead hearts or fresh frass at stem base",
        chemical_control=[
            {"name": "Bulldock 0.05 GR (Beta-cyfluthrin granules)", "rate": "5-8 kg/ha into whorl",
             "phi_days": "21", "notes": "Apply into leaf whorl at 3-4 weeks after emergence"},
            {"name": "Chlorpyrifos 48 EC", "rate": "1.0 L/ha",
             "phi_days": "21", "notes": "Foliar spray targeting young larvae before stem entry"},
        ],
        biological_control=[
            "Cotesia flavipes (parasitic wasp) — released in push-pull systems",
            "Trichogramma egg parasitoids",
            "Encourage natural enemies: ants, earwigs, spiders",
        ],
        cultural_control=[
            "Destroy crop residues after harvest (remove or burn stalks)",
            "Early planting to escape peak moth flights",
            "Push-pull system: intercrop with Desmodium, border with Napier grass",
            "Plant stem borer-tolerant varieties",
        ],
        scouting_protocol=(
            "Scout weekly from 2 weeks after emergence. Walk a W-pattern, examine "
            "20 plants at 5 stops (100 plants total). Check for dead hearts, leaf "
            "feeding damage in whorls, and frass at stem base. Record percentage "
            "of affected plants. Spray if >5% dead hearts detected."
        ),
    ),
    PestProfile(
        name="Grain Midge",
        scientific_name="Contarinia sorghicola",
        pest_type="insect",
        identification=[
            "Adult: tiny orange fly, 1.5-2 mm long",
            "Larvae: orange-red maggots inside developing grain",
            "Adults seen swarming around panicles at flowering",
            "Puparia in soil beneath sorghum fields",
        ],
        damage_symptoms=[
            "Blasted (empty) spikelets — grain fails to develop",
            "Orange larvae visible inside glumes when opened",
            "Panicles appear normal but grains are shrivelled or absent",
            "Yield loss can reach 70-100% in severe unsprayed fields",
        ],
        life_cycle_notes=(
            "Adults emerge from soil puparia and lay eggs in spikelets at flowering. "
            "Egg-to-adult cycle is 14-18 days. Larvae feed on developing grain, "
            "drop to soil to pupate. Can have multiple generations per season. "
            "Main damage occurs when flowering overlaps with peak midge emergence. "
            "Staggered planting dates increase exposure risk."
        ),
        favourable_conditions={
            "temp_min_c": 20, "temp_max_c": 35,
            "note": "Warm conditions with staggered flowering dates in an area "
                    "allow midge populations to build. Fields flowering after "
                    "the main flush are at highest risk.",
        },
        susceptible_stages=["Flowering"],
        economic_threshold="1-2 midges per panicle at 50% flowering",
        chemical_control=[
            {"name": "Lambda-cyhalothrin 50 EC", "rate": "200 mL/ha",
             "phi_days": "14", "notes": "Spray at 50% panicle emergence, repeat at full flowering"},
            {"name": "Carbaryl 85 WP", "rate": "1.5 kg/ha",
             "phi_days": "14", "notes": "Contact insecticide; best applied in early morning"},
        ],
        biological_control=[
            "Parasitoid wasps (Tetrastichus spp., Aprostocetus spp.)",
            "Predatory beetles and spiders feed on adults",
        ],
        cultural_control=[
            "Synchronise planting in the community (uniform flowering reduces risk)",
            "Avoid late planting which exposes flowering to peak midge populations",
            "Plant midge-resistant varieties where available",
            "Destroy crop residue and volunteer sorghum to reduce carryover",
        ],
        scouting_protocol=(
            "Begin scouting at panicle emergence (booting). At dawn or dusk, "
            "observe panicles for tiny orange flies hovering around spikelets. "
            "Sample 20 panicles across the field. Open 5-10 spikelets per panicle "
            "and look for orange eggs/larvae. If >1 midge per panicle at 50% "
            "flowering, apply insecticide immediately."
        ),
    ),
    PestProfile(
        name="Quelea Birds",
        scientific_name="Quelea quelea",
        pest_type="bird",
        identification=[
            "Small weaver bird, 12-13 cm, brownish plumage",
            "Males develop red/black face mask in breeding season",
            "Travel in massive flocks (thousands to millions)",
            "Nesting colonies in reed beds and thorn trees",
        ],
        damage_symptoms=[
            "Grain stripped from panicles leaving bare rachis",
            "Partial panicle damage — irregular grain loss pattern",
            "Lodging of stems from bird weight on panicles",
            "Can destroy an entire small-scale field in hours",
        ],
        life_cycle_notes=(
            "Quelea quelea is the world's most abundant wild bird. Breeds in "
            "enormous colonies. Flocks migrate following rain fronts and food "
            "availability. Peak damage occurs during sorghum grain fill and "
            "maturity, especially in NR IV-V where sorghum is the main crop."
        ),
        favourable_conditions={
            "note": "Large colonies near water sources. Fields close to roost sites "
                    "at highest risk. Worse when wild grass seed is scarce (drought years). "
                    "Early-maturing or late-planted fields preferentially attacked.",
        },
        susceptible_stages=["Grain Fill", "Maturity"],
        economic_threshold="Any flock activity in or near the field warrants immediate action",
        chemical_control=[
            {"name": "Fenthion 60 ULV (aerial application)", "rate": "As directed by Dept. of Agriculture",
             "phi_days": "N/A", "notes": "Quelea control is a government operation in Zimbabwe; "
                                         "report roosts to AGRITEX or Plant Protection Research Institute"},
        ],
        biological_control=[
            "Encourage raptors (hawks, falcons) by preserving nesting habitat near fields",
        ],
        cultural_control=[
            "Plant bird-resistant varieties with long, tight glumes (e.g. brown-grained types)",
            "Synchronise community planting to dilute damage",
            "Bird scaring: children/adults in field during grain fill (traditional method)",
            "Use reflective tape, scarecrows, or noise-makers",
            "Harvest as early as possible at physiological maturity",
        ],
        scouting_protocol=(
            "Watch for quelea flocks from soft dough stage onward. Monitor "
            "at dawn and dusk when birds are most active. Check nearby water "
            "sources and trees for roost sites. If flocks are spotted, begin "
            "bird scaring immediately and report large roosts (>10,000 birds) "
            "to AGRITEX for possible control operations."
        ),
    ),
]


SORGHUM_GROWTH_STAGES: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Emergence",
        stage_code="GS1",
        day_range=(0, 10),
        water_kc=0.35,
        water_mm_per_week=15,
        critical_nutrients=["P", "Zn"],
        key_activities=[
            "Plant at 5-7 cm depth into moist soil",
            "Apply basal fertiliser (Compound D) at planting",
            "Target 90,000-120,000 plants/ha (75cm x 10-15cm)",
            "Scout for cutworms and shoot fly",
        ],
        risks=["Crusting on heavy soils preventing emergence", "Shoot fly attack", "Poor germination from cold soils"],
        scientific_notes=(
            "Sorghum requires soil temperatures above 12°C for germination, optimum 25-30°C. "
            "Mesocotyl elongation pushes coleoptile to surface. Phosphorus is critical for "
            "seminal root development. Sorghum has a smaller seed reserve than maize, making "
            "it more sensitive to deep planting and soil crusting."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Vegetative/Tillering",
        stage_code="GS2",
        day_range=(10, 35),
        water_kc=0.50,
        water_mm_per_week=25,
        critical_nutrients=["N", "P", "K"],
        key_activities=[
            "Apply first top-dress AN at 4-5 weeks",
            "Weed control — sorghum is slow to establish canopy",
            "Scout for stem borer (dead hearts) and leaf diseases",
            "Thin to desired plant population if over-planted",
        ],
        risks=["Stem borer damage (dead hearts)", "Weed competition", "Drought stress delaying tillering"],
        scientific_notes=(
            "Sorghum produces tillers from basal nodes, contributing 10-30% of total yield. "
            "Tiller production is stimulated by adequate moisture and nitrogen, and suppressed "
            "by high plant density. The growing point remains below ground until ~30 days, "
            "conferring some drought tolerance — the crop can 'wait' for rain. Nitrogen uptake "
            "accelerates rapidly during this phase."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Booting/Heading",
        stage_code="GS3",
        day_range=(35, 55),
        water_kc=0.80,
        water_mm_per_week=40,
        critical_nutrients=["N", "K", "B"],
        key_activities=[
            "Apply second top-dress if needed (AN or Urea)",
            "Scout for anthracnose and leaf blight",
            "Monitor soil moisture — critical period begins",
            "Prepare for bird scaring if in quelea area",
        ],
        risks=["Drought stress causing poor panicle exsertion", "Anthracnose on leaves", "Lodging from wind"],
        scientific_notes=(
            "The panicle differentiates inside the boot and is highly sensitive to drought "
            "and heat stress. Flag leaf is the main photosynthetic source for grain fill. "
            "Boron deficiency can cause poor panicle exsertion and sterility. Water stress "
            "at this stage causes 'blast' — partial or complete panicle sterility."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Flowering",
        stage_code="GS4",
        day_range=(55, 65),
        water_kc=1.00,
        water_mm_per_week=50,
        critical_nutrients=["N", "K", "Zn"],
        key_activities=[
            "Maximum water demand — irrigate if possible",
            "Scout for grain midge at dawn/dusk",
            "Begin bird scaring in quelea-risk areas",
            "Monitor for head smut and ergot",
        ],
        risks=["Grain midge oviposition", "Drought causing floret sterility", "Ergot in cool wet weather"],
        scientific_notes=(
            "Sorghum flowers from the apex of the panicle downward over 4-7 days. "
            "Each floret is receptive for only a few hours. Pollen viability drops "
            "above 38°C. Grain midge females lay eggs in open florets, so tight-glumed "
            "varieties offer physical resistance. This is the most water-sensitive "
            "stage — a single week of severe stress can halve yields."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Grain Fill",
        stage_code="GS5",
        day_range=(65, 95),
        water_kc=0.85,
        water_mm_per_week=40,
        critical_nutrients=["N", "K"],
        key_activities=[
            "Maintain bird scaring continuously",
            "Scout for grain mould (especially if wet)",
            "Monitor stalk strength for lodging risk",
            "Avoid any nitrogen application (delays maturity)",
        ],
        risks=["Bird damage", "Grain mould from rain", "Charcoal rot (stalk) under drought stress"],
        scientific_notes=(
            "Grain fill in sorghum lasts 25-35 days. Starch is deposited in the endosperm "
            "in a vitreous (hard) or floury pattern depending on genetics. Stay-green trait "
            "maintains leaf function during grain fill and confers drought tolerance — "
            "photosynthates continue flowing to grain. Black layer formation at the hilum "
            "indicates physiological maturity."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Maturity",
        stage_code="GS6",
        day_range=(95, 120),
        water_kc=0.40,
        water_mm_per_week=15,
        critical_nutrients=[],
        key_activities=[
            "Check for black layer (physiological maturity)",
            "Continue bird scaring until harvest",
            "Harvest when grain moisture is 12-14%",
            "Dry grain rapidly to <12.5% for safe storage",
        ],
        risks=["Bird damage to mature grain", "Grain mould if rain delays harvest", "Lodging"],
        scientific_notes=(
            "Physiological maturity is marked by black layer formation at the hilum. "
            "Grain moisture at black layer is typically 25-30%. Field drying to 12-14% "
            "takes 2-4 weeks depending on weather. Delayed harvest increases grain mould "
            "risk and bird damage. Sorghum grain has a waxy cuticle that provides some "
            "weathering resistance compared to maize."
        ),
    ),
]


SORGHUM_FERT = FertilizerSchedule(
    basal={
        "product": "Compound D (7:14:7)",
        "rate_kg_ha": 200,
        "timing": "At planting",
        "placement": "Band 5 cm beside and below seed",
        "nutrients_supplied": {"N": 14, "P2O5": 28, "K2O": 14},
        "notes": "Compound D provides starter P for root development. "
                 "On very sandy soils, consider Compound S (7:21:7) for extra P.",
    },
    top_dress_1={
        "product": "Ammonium Nitrate (AN 34.5%N)",
        "rate_kg_ha": 100,
        "timing": "4-5 weeks after emergence (knee height)",
        "placement": "Side-dress 10 cm from plant row",
        "nutrients_supplied": {"N": 34.5},
        "notes": "Apply when soil is moist for rapid uptake. "
                 "In NR IV-V, reduce to 75 kg/ha if rainfall is poor.",
    },
    top_dress_2={
        "product": "Ammonium Nitrate (AN 34.5%N)",
        "rate_kg_ha": 50,
        "timing": "At booting (flag leaf visible)",
        "placement": "Side-dress or broadcast",
        "nutrients_supplied": {"N": 17.25},
        "notes": "Only apply if the season is good (adequate rainfall). "
                 "Skip in drought years — excess N delays maturity.",
    },
    foliar=None,
    liming={
        "ite": "Calcitic or dolomitic lime",
        "rate_kg_ha": "As per soil test, typically 500-1000 kg/ha",
        "timing": "Apply 2-3 months before planting, incorporate",
        "notes": "Sorghum tolerates slightly acidic soils better than maize, "
                 "but lime if pH < 5.0. Dolomitic lime also supplies Mg.",
    },
    notes=(
        "Sorghum is more nutrient-efficient than maize. Total N requirement is "
        "about 60-80 kg/ha for 2-3 t/ha yield. Excess N promotes lodging and "
        "delays maturity, increasing bird and mould damage risk. In NR IV-V, "
        "use conservative fertiliser rates matched to expected rainfall."
    ),
)


SORGHUM_PLANTING_WINDOWS: List[PlantingWindow] = [
    PlantingWindow(
        region="NR I (Eastern Highlands)",
        optimal_start="November 1",
        optimal_end="November 30",
        acceptable_start="October 15",
        acceptable_end="December 15",
        notes="Not a primary sorghum zone; maize preferred. Sorghum grown only on marginal land.",
    ),
    PlantingWindow(
        region="NR II (Mashonaland)",
        optimal_start="November 15",
        optimal_end="December 15",
        acceptable_start="November 1",
        acceptable_end="December 31",
        notes="Sorghum as rotation or drought hedge. Plant after maize window if rains are late.",
    ),
    PlantingWindow(
        region="NR III (Semi-intensive)",
        optimal_start="November 15",
        optimal_end="December 15",
        acceptable_start="November 1",
        acceptable_end="January 7",
        notes="Sorghum is a sound choice here. Plant with first reliable rains (>30 mm).",
    ),
    PlantingWindow(
        region="NR IV (Semi-extensive/Matabeleland)",
        optimal_start="December 1",
        optimal_end="December 31",
        acceptable_start="November 15",
        acceptable_end="January 15",
        notes="Primary sorghum zone. Wait for season-establishing rains (>40 mm in a week). "
              "Use short-season varieties (Macia, 90-100 days).",
    ),
    PlantingWindow(
        region="NR V (Lowveld)",
        optimal_start="December 1",
        optimal_end="January 15",
        acceptable_start="November 15",
        acceptable_end="January 31",
        notes="Dryland sorghum is the staple. Plant on stored soil moisture after first rains. "
              "Ultra-short varieties essential. Bird pressure is extreme.",
    ),
]


PROFILE = CropProfile(
    crop_name="Sorghum",
    scientific_name="Sorghum bicolor",
    family="Poaceae",
    optimal_ph=(5.5, 7.5),
    critical_ph_low=4.5,
    optimal_soil_types=["fersiallitic", "vertisol", "siallitic"],
    avoid_soil_types=["waterlogged", "pure sand with no clay"],
    optimal_temp=(25.0, 35.0),
    critical_temp_low=10.0,
    critical_temp_high=42.0,
    base_temp_gdd=10.0,
    total_water_mm=400.0,
    growth_stages=SORGHUM_GROWTH_STAGES,
    fertilizer_schedule=SORGHUM_FERT,
    diseases=SORGHUM_DISEASES,
    pests=SORGHUM_PESTS,
    planting_windows=SORGHUM_PLANTING_WINDOWS,
    harvest_moisture="12-14% grain moisture (black layer at 25-30%, field dry to target)",
    storage_conditions="Store at <12.5% moisture in sealed containers or bags. "
                       "Treat with Actellic Super or diatomaceous earth for weevil protection. "
                       "Keep in cool, dry, well-ventilated store.",
    post_harvest_notes="Thresh panicles by hand or small mechanical thresher. "
                       "Winnow to remove chaff. Grade for grain mould — reject heavily "
                       "mouldy grain for human consumption. Sorghum stores well due to "
                       "tannin content in coloured-grain types.",
    natural_region_suitability={
        "NR I": "Marginal — too wet, prefer maize or specialty crops",
        "NR II": "Suitable as rotation or drought hedge crop",
        "NR III": "Well suited — reliable yields with moderate inputs",
        "NR IV": "Highly recommended — primary grain crop for this zone",
        "NR V": "Essential food security crop — drought tolerance critical here",
    },
)

ALIASES = ["grain sorghum"]
