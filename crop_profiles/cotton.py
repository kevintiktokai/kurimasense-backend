"""Cotton (Gossypium hirsutum) — Major cash crop for Gokwe, Muzarabani and Chiredzi."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List


COTTON_DISEASES: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Bacterial Blight",
        pathogen="Xanthomonas citri pv. malvacearum",
        pathogen_type="bacterial",
        symptoms=[
            "Angular, water-soaked lesions on leaves bounded by veins",
            "Lesions turn brown-black with age",
            "Black arm: dark lesions on stems and petioles causing wilting",
            "Boll rot: water-soaked spots on bolls, lint stained and discoloured",
        ],
        identification_markers=[
            "Angular leaf spots (bacterial, vein-limited) vs. circular (fungal)",
            "Bacterial ooze visible on lesions in early morning dew",
            "Black lesions on main stem = 'black arm' phase",
            "Seed-borne: fuzzy seed shows darkened chalazal end",
        ],
        favourable_conditions={
            "humidity_min": 80, "temp_min_c": 25, "temp_max_c": 35,
            "note": "Warm, humid weather with wind-driven rain spreads bacteria. "
                    "Seed-borne inoculum is the primary source. Hail damage "
                    "creates infection courts.",
        },
        susceptible_stages=["Squaring", "Flowering", "Boll Development"],
        resistant_varieties=["QM 302", "C 593", "SZ 9314"],
        susceptible_varieties=["Some older varieties"],
        chemical_control=[
            {"name": "Copper oxychloride 85 WP", "rate": "2.5-3.0 kg/ha",
             "phi_days": "14", "notes": "Protectant; apply before and after storms"},
            {"name": "Streptomycin sulphate", "rate": "100 g/ha",
             "phi_days": "7", "notes": "Use only if copper-tolerant strains are present"},
        ],
        biological_control=[
            "Use certified, acid-delinted seed treated with appropriate bactericides",
            "Bacillus-based biocontrol agents under research",
        ],
        cultural_control=[
            "Plant certified disease-free seed only",
            "Acid-delinting of seed removes surface bacteria",
            "Destroy crop residue immediately after harvest",
            "Rotate with non-host crops (cereals, legumes) for 2-3 years",
            "Avoid overhead irrigation which spreads bacteria",
        ],
        economic_threshold="10% of plants showing angular leaf spot before flowering",
        severity_scale={
            "mild": "Angular spots on <10% of leaves, no stem lesions",
            "moderate": "Leaf spots widespread, early black arm on stems",
            "severe": "Black arm girdling stems, boll rot — 30-70% yield loss",
        },
    ),
    DiseaseProfile(
        name="Fusarium Wilt",
        pathogen="Fusarium oxysporum f. sp. vasinfectum",
        pathogen_type="fungal",
        symptoms=[
            "Yellowing and wilting of leaves, often on one side of plant first",
            "Brown vascular discolouration visible when stem is cut",
            "Stunting and premature leaf drop",
            "Plant death in severe cases",
        ],
        identification_markers=[
            "One-sided wilting is characteristic",
            "Brown ring visible in cross-section of stem",
            "Distinguish from Verticillium by brown (not grey-green) vascular staining",
            "Often associated with root-knot nematode damage",
        ],
        favourable_conditions={
            "temp_min_c": 25, "temp_max_c": 33,
            "soil_ph": "acidic soils (<5.5) favour disease",
            "note": "Warm soils, sandy acidic soils, and nematode damage increase severity. "
                    "The pathogen persists in soil for many years.",
        },
        susceptible_stages=["Squaring", "Flowering", "Boll Development"],
        resistant_varieties=["QM 302", "SZ 9314"],
        susceptible_varieties=["C567", "Some older varieties"],
        chemical_control=[
            {"name": "Thiram 80 WP (seed treatment)", "rate": "3 g/kg seed",
             "phi_days": "N/A", "notes": "Reduces seed-borne inoculum; does not control soil-borne phase"},
            {"name": "Carbendazim 50 SC (seed treatment)", "rate": "2 mL/kg seed",
             "phi_days": "N/A", "notes": "Systemic seed treatment for Fusarium"},
        ],
        biological_control=[
            "Trichoderma harzianum seed treatment or soil drench",
            "Mycorrhizal inoculants improve root health and resistance",
        ],
        cultural_control=[
            "Plant resistant varieties (single most effective measure)",
            "Rotate with cereals for 3-4 years",
            "Lime acidic soils to pH 6.0-6.5",
            "Control root-knot nematodes which predispose plants to Fusarium",
            "Avoid planting in fields with known wilt history",
        ],
        economic_threshold="Any wilted plants should trigger variety change for next season",
        severity_scale={
            "mild": "< 5% plants wilted, scattered distribution",
            "moderate": "5-20% plants wilted, clustered in patches",
            "severe": "> 20% plants wilted — change variety and field",
        },
    ),
    DiseaseProfile(
        name="Verticillium Wilt",
        pathogen="Verticillium dahliae",
        pathogen_type="fungal",
        symptoms=[
            "Interveinal chlorosis and necrosis starting on lower leaves",
            "Leaf margins curl upward",
            "Premature defoliation from base upward",
            "Grey-green vascular discolouration in cross-section",
        ],
        identification_markers=[
            "Grey-green (not brown) vascular staining distinguishes from Fusarium",
            "V-shaped leaf necrosis from leaf margins",
            "Lower leaves affected first, disease moves upward",
            "Microsclerotia visible on dead stems",
        ],
        favourable_conditions={
            "temp_min_c": 20, "temp_max_c": 28,
            "note": "Cool to moderate temperatures favour Verticillium over Fusarium. "
                    "More common in irrigated cotton in cooler areas.",
        },
        susceptible_stages=["Flowering", "Boll Development"],
        resistant_varieties=["QM 302", "C 593"],
        susceptible_varieties=["Some older cultivars"],
        chemical_control=[
            {"name": "No effective chemical control once established", "rate": "N/A",
             "phi_days": "N/A", "notes": "Focus on prevention through resistant varieties and rotation"},
        ],
        biological_control=[
            "Trichoderma soil amendments",
            "Organic matter additions improve suppressive soil biology",
        ],
        cultural_control=[
            "Plant resistant varieties",
            "Long rotation (4+ years) with non-host crops (cereals)",
            "Avoid cotton after sunflower, potato, or tomato (also hosts)",
            "Destroy crop residue to reduce microsclerotia in soil",
        ],
        economic_threshold="Any symptomatic plants warrant variety review",
        severity_scale={
            "mild": "< 5% plants with symptoms, lower leaves only",
            "moderate": "5-20% plants defoliating",
            "severe": "> 20% plants severely defoliated — major lint yield loss",
        },
    ),
]


COTTON_PESTS: List[PestProfile] = [
    PestProfile(
        name="African Bollworm",
        scientific_name="Helicoverpa armigera",
        pest_type="insect",
        identification=[
            "Adult moth: 35-40 mm wingspan, buff-coloured with dark spot on forewing",
            "Larvae: variable colour (green, brown, pink), up to 40 mm, with lateral stripes",
            "Eggs: single, ribbed, dome-shaped, laid on tender growth",
            "Pupae: brown, in soil at 5-10 cm depth",
        ],
        damage_symptoms=[
            "Holes bored into squares (buds), flowers, and bolls",
            "Frass (pellet-like excrement) visible at entry holes",
            "Abscission (shedding) of damaged squares and young bolls",
            "Secondary boll rot from fungal entry through larval feeding holes",
        ],
        life_cycle_notes=(
            "Eggs hatch in 3-5 days. Larvae feed for 14-21 days, passing through "
            "6 instars. Pupation in soil for 10-14 days. Adults are strong fliers "
            "and migrate. Multiple overlapping generations per season. "
            "Resistance to pyrethroids is widespread in Zimbabwe."
        ),
        favourable_conditions={
            "temp_min_c": 20, "temp_max_c": 35,
            "note": "Warm conditions with available flowers/fruit. Peak flights "
                    "follow early-season rains. Polyphagous — moves from tomato, "
                    "maize, and legumes into cotton.",
        },
        susceptible_stages=["Squaring", "Flowering", "Boll Development"],
        economic_threshold="3-5 small larvae per 100 plants, or 20% squares with eggs/larvae",
        chemical_control=[
            {"name": "Indoxacarb 150 SC (Steward)", "rate": "250 mL/ha",
             "phi_days": "14", "notes": "Oxadiazine; effective on pyrethroid-resistant populations"},
            {"name": "Emamectin benzoate 5 SG", "rate": "300 g/ha",
             "phi_days": "14", "notes": "Low impact on beneficials; target small larvae"},
            {"name": "Lambda-cyhalothrin 50 EC", "rate": "200-300 mL/ha",
             "phi_days": "14", "notes": "Pyrethroid; check for resistance before relying on this"},
        ],
        biological_control=[
            "Trichogramma egg parasitoids (release at squaring)",
            "Bacillus thuringiensis (Bt) sprays target small larvae",
            "Encourage natural enemies: lacewings, ladybirds, spiders, parasitic wasps",
            "Nuclear polyhedrosis virus (HaNPV) specific to Helicoverpa",
        ],
        cultural_control=[
            "Scout twice weekly from squaring onward",
            "Hand-pick large larvae on small-scale farms",
            "Destroy crop residue and pupae by ploughing after harvest",
            "Trap crops: plant early sunflower or pigeon pea borders to attract moths",
            "Avoid broad-spectrum insecticides that kill natural enemies",
        ],
        scouting_protocol=(
            "Scout twice weekly from first square formation. Walk a W-pattern through "
            "the field. At each of 5 stops, examine 20 plants (100 total). Check terminal "
            "growth, squares, flowers, and small bolls for eggs and larvae. Record counts "
            "by instar (small <1cm, medium, large). Spray threshold: 3-5 small larvae or "
            "20% damaged squares per 100 plants. Prioritise small larvae — large larvae "
            "are harder to kill and have already caused damage."
        ),
    ),
    PestProfile(
        name="Red Spider Mite",
        scientific_name="Tetranychus urticae",
        pest_type="mite",
        identification=[
            "Tiny (0.5 mm), oval, yellowish-green to red mites",
            "Fine webbing on underside of leaves",
            "Visible with hand lens as moving dots on leaf underside",
            "Eggs: spherical, translucent, on leaf undersurface",
        ],
        damage_symptoms=[
            "Yellow-white stippling on leaf upper surface",
            "Reddening and bronzing of leaves in severe infestations",
            "Premature leaf drop reducing photosynthesis",
            "Fine silk webbing covering shoot tips and leaf surfaces",
        ],
        life_cycle_notes=(
            "Egg-to-adult cycle is 7-14 days depending on temperature. "
            "Rapid population build-up under hot, dry conditions. "
            "A single female can lay 100-200 eggs. Populations can explode "
            "after broad-spectrum insecticide applications kill natural enemies."
        ),
        favourable_conditions={
            "temp_min_c": 28, "temp_max_c": 40,
            "humidity_max": 50,
            "note": "Hot, dry, dusty conditions. Outbreaks often triggered by "
                    "pyrethroid sprays that eliminate predatory mites and ladybirds.",
        },
        susceptible_stages=["Squaring", "Flowering", "Boll Development"],
        economic_threshold="50% of plants with mite colonies and visible leaf damage",
        chemical_control=[
            {"name": "Abamectin 18 EC", "rate": "300-400 mL/ha",
             "phi_days": "14", "notes": "Specific acaricide; minimal impact on predators at low rates"},
            {"name": "Spiromesifen 240 SC", "rate": "400 mL/ha",
             "phi_days": "21", "notes": "Lipid synthesis inhibitor; good on eggs and nymphs"},
        ],
        biological_control=[
            "Predatory mites (Phytoseiidae) — conserve by avoiding broad-spectrum sprays",
            "Ladybird beetles (Stethorus spp.) feed on spider mites",
            "Lacewing larvae are generalist predators of mites",
        ],
        cultural_control=[
            "Avoid dusty field margins (suppress dust with grass strips)",
            "Irrigate during dry spells to increase humidity around plants",
            "Avoid unnecessary pyrethroid sprays that trigger mite outbreaks",
            "Destroy crop residue and alternate host weeds after harvest",
        ],
        scouting_protocol=(
            "Scout weekly from squaring, increasing to twice weekly in hot, dry weather. "
            "Examine the underside of leaves at the 5th node from the top on 20 plants "
            "at 5 points (W-pattern). Use a 10x hand lens. Record presence of mites, "
            "eggs, webbing, and predatory mites. If >50% of sampled leaves have colonies "
            "with minimal predators, consider acaricide application."
        ),
    ),
    PestProfile(
        name="Cotton Aphid",
        scientific_name="Aphis gossypii",
        pest_type="insect",
        identification=[
            "Small (1-2 mm), soft-bodied, dark green to black insects",
            "Cluster on growing tips and leaf undersides",
            "Winged forms appear when colonies are overcrowded",
            "Honeydew (sticky excrement) visible on leaves below colonies",
        ],
        damage_symptoms=[
            "Curling and distortion of young leaves",
            "Sticky honeydew on leaves promoting sooty mould growth",
            "Stunted growth in seedlings with heavy infestations",
            "Sticky lint at harvest (honeydew-contaminated) — grade downgrade",
        ],
        life_cycle_notes=(
            "Parthenogenetic reproduction — females produce live young without mating. "
            "Generation time is 5-7 days in warm weather. Populations can double every "
            "3 days under optimal conditions. Natural enemies usually provide adequate "
            "control if not disrupted by insecticides."
        ),
        favourable_conditions={
            "temp_min_c": 20, "temp_max_c": 30,
            "note": "Moderate temperatures. Outbreaks common after broad-spectrum "
                    "insecticide applications that kill natural enemies. "
                    "Excess nitrogen promotes succulent growth that attracts aphids.",
        },
        susceptible_stages=["Emergence", "Squaring", "Boll Opening"],
        economic_threshold="50% of plants with colonies of 50+ aphids on growing tips",
        chemical_control=[
            {"name": "Imidacloprid 200 SL", "rate": "250 mL/ha",
             "phi_days": "21", "notes": "Systemic; apply as a drench or foliar spray"},
            {"name": "Acetamiprid 20 SP", "rate": "100-150 g/ha",
             "phi_days": "14", "notes": "Neonicotinoid; good systemic activity"},
        ],
        biological_control=[
            "Ladybird beetles (Hippodamia, Coccinella spp.) — key natural enemies",
            "Lacewing larvae (Chrysoperla spp.)",
            "Parasitic wasps (Aphidius, Lysiphlebus spp.)",
            "Entomopathogenic fungi (Beauveria bassiana) in humid conditions",
        ],
        cultural_control=[
            "Avoid excessive nitrogen fertilisation",
            "Conserve natural enemies by using selective insecticides",
            "Remove weeds that serve as alternate hosts",
            "Monitor early season — aphids on seedlings are most damaging",
        ],
        scouting_protocol=(
            "Scout weekly from emergence. Check the underside of the 5th leaf from the "
            "top and the growing tip on 20 plants at 5 stops (100 plants). Record the "
            "average number of aphids per plant and presence of natural enemies. If "
            "ladybirds or parasitised 'mummies' are present, delay spraying. Treat only "
            "if >50% of plants have 50+ aphids and few natural enemies."
        ),
    ),
]


COTTON_GROWTH_STAGES: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Emergence",
        stage_code="GS1",
        day_range=(0, 14),
        water_kc=0.35,
        water_mm_per_week=15,
        critical_nutrients=["P", "K"],
        key_activities=[
            "Plant at 3-5 cm depth into warm, moist soil (>15°C)",
            "Apply basal Compound S at planting",
            "Target 40,000-55,000 plants/ha (90cm x 20-30cm)",
            "Scout for cutworms and aphids on seedlings",
        ],
        risks=["Cold-induced poor germination", "Seedling diseases (damping-off)", "Cutworm damage"],
        scientific_notes=(
            "Cotton requires soil temperatures above 15°C for germination and 18°C for "
            "vigorous emergence. The hypocotyl hook must push cotyledons through the soil — "
            "crusting is problematic. Phosphorus is critical for taproot development. "
            "Early-planted cotton (before soil warms) has higher seedling disease risk."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Squaring",
        stage_code="GS2",
        day_range=(35, 60),
        water_kc=0.60,
        water_mm_per_week=30,
        critical_nutrients=["N", "K", "B"],
        key_activities=[
            "Apply first top-dress AN at 5-6 weeks",
            "Begin bollworm scouting — check squares for eggs",
            "Cultivate or hand-weed between rows",
            "Scout for bacterial blight after rain events",
        ],
        risks=["Bollworm eggs on squares", "Bacterial blight after storms", "Aphid build-up"],
        scientific_notes=(
            "Squares (flower buds) initiate at the first fruiting node (usually node 5-7). "
            "The first fruiting position contributes disproportionately to yield. Square "
            "shedding above 40-50% indicates stress (water, nutrition, or pest). Boron "
            "deficiency causes square drop and malformed bolls. Cotton is an indeterminate "
            "plant — it flowers for 6-8 weeks."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Flowering",
        stage_code="GS3",
        day_range=(60, 90),
        water_kc=1.05,
        water_mm_per_week=50,
        critical_nutrients=["N", "K", "B", "Mg"],
        key_activities=[
            "Maximum water demand — irrigate if available",
            "Apply second top-dress (AN or urea)",
            "Intensify bollworm scouting to twice weekly",
            "Monitor for mite build-up in hot weather",
        ],
        risks=["Bollworm larvae boring into young bolls", "Water stress causing square/boll shedding",
               "Spider mite outbreaks"],
        scientific_notes=(
            "Cotton flowers open white, turn pink next day, and drop by day 3. Successful "
            "pollination and boll set depend on adequate moisture and potassium. Peak water "
            "use coincides with peak flowering. K deficiency causes premature senescence and "
            "fibre quality loss. The cutout point (when new fruiting nodes stop) occurs when "
            "the plant's assimilate demand from existing bolls exceeds supply."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Boll Development",
        stage_code="GS4",
        day_range=(90, 130),
        water_kc=0.90,
        water_mm_per_week=45,
        critical_nutrients=["K", "N"],
        key_activities=[
            "Continue bollworm and mite scouting",
            "No nitrogen after cutout (delays maturity)",
            "Monitor boll retention — aim for 60%+",
            "Apply potassium foliar if K deficiency visible",
        ],
        risks=["Boll rot from rain", "Spider mites (dry weather)", "Bollworm — late-season larvae"],
        scientific_notes=(
            "Boll maturation takes 45-65 days from flower to open boll. Fibre elongation "
            "occurs in the first 20 days; secondary wall thickening (cellulose deposition) "
            "follows. Potassium is critical for cellulose synthesis and fibre maturity. "
            "Water stress during boll fill reduces micronaire (fibre fineness) and strength. "
            "Late-season bolls on upper nodes have lower gin-out and grade."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Boll Opening",
        stage_code="GS5",
        day_range=(130, 160),
        water_kc=0.55,
        water_mm_per_week=20,
        critical_nutrients=[],
        key_activities=[
            "Apply defoliant when 60-70% bolls are open",
            "Scout for aphid honeydew contamination of lint",
            "Prepare for harvest — check picker equipment",
            "Avoid rain on open bolls (reduces lint quality)",
        ],
        risks=["Rain on open bolls (staining, grade loss)", "Aphid honeydew on lint",
               "Late bollworm damage to green bolls"],
        scientific_notes=(
            "Boll opening is driven by desiccation of the boll wall. Defoliation removes "
            "leaves to improve air circulation, reduce staining, and facilitate picking. "
            "Thidiazuron is the standard defoliant in Zimbabwe. Too-early defoliation "
            "reduces yield; too-late results in bark contamination of lint. Lint exposed "
            "to rain develops discolouration and microbial growth."
        ),
    ),
    GrowthStageRequirements(
        stage_name="Harvest",
        stage_code="GS6",
        day_range=(160, 200),
        water_kc=0.0,
        water_mm_per_week=0,
        critical_nutrients=[],
        key_activities=[
            "Hand-pick in 2-3 rounds as bolls open progressively",
            "Keep grades separate (first pick = best quality)",
            "Avoid picking wet cotton",
            "Deliver to buying points promptly for grading",
        ],
        risks=["Rain causing lint discolouration", "Contamination (leaves, bark, soil)",
               "Low prices if quality is poor"],
        scientific_notes=(
            "Zimbabwe cotton is predominantly hand-picked, which allows selective harvesting "
            "and generally produces higher-quality lint than machine picking. First-pick lint "
            "from lower bolls is typically the best quality. Grade depends on colour, staple "
            "length, strength, micronaire, and contamination level. Cotton grades in Zimbabwe: "
            "A, B, C, D with A commanding the highest price."
        ),
    ),
]


COTTON_FERT = FertilizerSchedule(
    basal={
        "product": "Compound S (7:21:7 +6S)",
        "rate_kg_ha": 250,
        "timing": "At planting",
        "placement": "Band 5-7 cm beside and below seed",
        "nutrients_supplied": {"N": 17.5, "P2O5": 52.5, "K2O": 17.5, "S": 15},
        "notes": "Compound S preferred over Compound D for cotton due to sulphur content. "
                 "Sulphur is essential for oil and protein in cotton seed.",
    },
    top_dress_1={
        "product": "Ammonium Nitrate (AN 34.5%N)",
        "rate_kg_ha": 150,
        "timing": "5-6 weeks after emergence (first squares visible)",
        "placement": "Side-dress 10-15 cm from plant row",
        "nutrients_supplied": {"N": 51.75},
        "notes": "Apply when soil is moist. Nitrogen drives vegetative growth and square production.",
    },
    top_dress_2={
        "product": "Ammonium Nitrate (AN 34.5%N)",
        "rate_kg_ha": 100,
        "timing": "At peak flowering (10-12 weeks)",
        "placement": "Side-dress or broadcast between rows",
        "nutrients_supplied": {"N": 34.5},
        "notes": "Final N application. Do NOT apply after cutout — delays maturity. "
                 "Total N should not exceed 120 kg/ha for dryland cotton.",
    },
    foliar={
        "product": "Solubor (boron) + KNO3",
        "rate_kg_ha": "Solubor 1 kg/ha + KNO3 5 kg/ha in 200L water",
        "timing": "At squaring and early flowering",
        "notes": "Boron deficiency causes square shedding and hollow-lock bolls. "
                 "Potassium nitrate supports K demand during boll fill.",
    },
    liming={
        "product": "Dolomitic lime",
        "rate_kg_ha": "As per soil test, typically 1000-2000 kg/ha",
        "timing": "Apply 2-3 months before planting, incorporate",
        "notes": "Cotton is sensitive to acidity. Target pH 6.0-6.5. "
                 "Dolomitic lime also supplies Mg needed for photosynthesis.",
    },
    notes=(
        "Cotton has high K demand — total K uptake is 150-200 kg K2O/ha for 2 t/ha lint. "
        "Potassium deficiency shows as premature senescence and poor fibre quality. "
        "Gypsum (CaSO4) at 200-300 kg/ha provides Ca and S on sodic soils in the lowveld."
    ),
)


COTTON_PLANTING_WINDOWS: List[PlantingWindow] = [
    PlantingWindow(
        region="NR I (Eastern Highlands)",
        optimal_start="N/A",
        optimal_end="N/A",
        acceptable_start="N/A",
        acceptable_end="N/A",
        notes="Too cool and wet for cotton. Not grown in NR I.",
    ),
    PlantingWindow(
        region="NR II (Mashonaland)",
        optimal_start="October 25",
        optimal_end="November 25",
        acceptable_start="October 15",
        acceptable_end="December 10",
        notes="Cotton grown in warmer parts of NR II (e.g., Muzarabani, Dande). "
              "Early planting critical for long season.",
    ),
    PlantingWindow(
        region="NR III (Semi-intensive)",
        optimal_start="October 20",
        optimal_end="November 20",
        acceptable_start="October 10",
        acceptable_end="December 5",
        notes="Suitable in warmer micro-climates. Gokwe district is key cotton zone.",
    ),
    PlantingWindow(
        region="NR IV (Semi-extensive)",
        optimal_start="November 1",
        optimal_end="December 5",
        acceptable_start="October 20",
        acceptable_end="December 15",
        notes="Major cotton belt (Gokwe South, Sanyati). Plant early on first rains — "
              "season length is limiting.",
    ),
    PlantingWindow(
        region="NR V (Lowveld)",
        optimal_start="October 15",
        optimal_end="November 15",
        acceptable_start="October 1",
        acceptable_end="November 30",
        notes="Chiredzi/Triangle irrigated cotton: plant early for full season. "
              "Dryland cotton is risky — consider short-season varieties.",
    ),
]


PROFILE = CropProfile(
    crop_name="Cotton",
    scientific_name="Gossypium hirsutum",
    family="Malvaceae",
    optimal_ph=(6.0, 7.0),
    critical_ph_low=5.2,
    optimal_soil_types=["fersiallitic", "siallitic", "vertisol"],
    avoid_soil_types=["waterlogged", "very sandy (rapid leaching)", "saline"],
    optimal_temp=(25.0, 35.0),
    critical_temp_low=15.0,
    critical_temp_high=40.0,
    base_temp_gdd=15.6,
    total_water_mm=700.0,
    growth_stages=COTTON_GROWTH_STAGES,
    fertilizer_schedule=COTTON_FERT,
    diseases=COTTON_DISEASES,
    pests=COTTON_PESTS,
    planting_windows=COTTON_PLANTING_WINDOWS,
    harvest_moisture="Lint should be dry (<10% moisture). Pick only dry, fully open bolls.",
    storage_conditions="Store seed cotton in dry, ventilated sheds. Keep off the ground on "
                       "platforms or pallets. Avoid contamination with soil, leaves, or "
                       "polypropylene fibres. Deliver to ginnery within 2 weeks of picking.",
    post_harvest_notes="Hand-pick in 2-3 rounds. Keep first-pick (best quality) separate. "
                       "Grade by colour and cleanliness. Remove any trash, bark, or green bolls. "
                       "Zimbabwe's hand-picked cotton commands a premium for fibre quality. "
                       "Contract farmers should deliver per the buyer's schedule.",
    natural_region_suitability={
        "NR I": "Not suitable — too cool and wet",
        "NR II": "Suitable in warm low-lying areas (Muzarabani, Dande, Rushinga)",
        "NR III": "Well suited — Gokwe is Zimbabwe's cotton capital",
        "NR IV": "Major cotton belt — good heat units, adequate rainfall",
        "NR V": "Under irrigation only (Chiredzi, Triangle). Dryland is very risky.",
    },
)

ALIASES: list = []
