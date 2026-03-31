"""Cowpeas (Vigna unguiculata) — drought-tolerant legume, critical for smallholder food security and fodder."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List, Dict, Any


# COWPEAS (Vigna unguiculata)
# ---------------------------------------------------------------------------

_diseases: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Cowpea Aphid-Borne Mosaic Virus (CABMV)",
        pathogen="Cowpea aphid-borne mosaic virus (Potyvirus)",
        pathogen_type="viral",
        symptoms=[
            "Green and yellow mosaic mottling on leaves",
            "Leaf distortion and curling",
            "Stunted growth and reduced vigour",
            "Pod distortion and reduced seed size",
        ],
        identification_markers=[
            "Mosaic pattern follows leaf venation",
            "Young leaves show symptoms first",
            "Aphid colonies usually present on growing tips",
        ],
        favourable_conditions={"temp_min_c": 20, "temp_max_c": 30, "humidity_min": 50},
        susceptible_stages=["Emergence", "Vegetative", "Flowering"],
        resistant_varieties=["IT 18", "CBC5 (Solar)"],
        susceptible_varieties=["Local landrace selections"],
        chemical_control=[
            {"name": "Dimethoate 40% EC (vector control)", "rate": "0.5 L/ha",
             "phi_days": "14", "notes": "Controls aphid vectors; does NOT cure infected plants"},
            {"name": "Imidacloprid 200 SL (seed treatment)", "rate": "5 mL/kg seed",
             "phi_days": "N/A", "notes": "Systemic seed treatment protects seedlings for 3-4 weeks"},
        ],
        biological_control=[
            "Encourage ladybird beetles (Coccinellidae) — aphid predators",
            "Parasitic wasps (Aphidius spp.) for aphid biocontrol",
        ],
        cultural_control=[
            "Plant resistant varieties (IT 18, CBC5)",
            "Rogue out infected plants early to reduce inoculum",
            "Avoid planting near old cowpea fields or alternative hosts",
            "Intercrop with cereals (barrier effect reduces aphid landing)",
        ],
        economic_threshold="5% plants showing mosaic symptoms before flowering; rogue immediately",
        severity_scale={
            "mild": "< 5% plants infected, no yield impact",
            "moderate": "5-20% plants infected, 10-30% yield loss",
            "severe": "> 20% plants infected, > 30% yield loss with pod distortion",
        },
    ),
    DiseaseProfile(
        name="Cercospora Leaf Spot",
        pathogen="Cercospora canescens / Cercospora cruenta",
        pathogen_type="fungal",
        symptoms=[
            "Circular to irregular reddish-brown spots on leaves",
            "Spots 2-8 mm diameter with grey centre and dark margin",
            "Premature defoliation in severe cases",
            "Reduced pod fill due to loss of photosynthetic area",
        ],
        identification_markers=[
            "Grey-centred spots with reddish-brown border",
            "Spots visible on both leaf surfaces",
            "Defoliation starts from lower canopy",
        ],
        favourable_conditions={"temp_min_c": 22, "temp_max_c": 30, "humidity_min": 80},
        susceptible_stages=["Vegetative", "Flowering", "Pod Fill"],
        resistant_varieties=["CBC2", "IT 18"],
        susceptible_varieties=["CBC1"],
        chemical_control=[
            {"name": "Mancozeb 80 WP", "rate": "2.0-2.5 kg/ha",
             "phi_days": "14", "notes": "Protectant; apply at first symptoms, repeat 10-14 day intervals"},
            {"name": "Carbendazim 50 WP", "rate": "0.5 kg/ha",
             "phi_days": "14", "notes": "Systemic; alternate with protectant to delay resistance"},
        ],
        biological_control=[
            "Trichoderma-based bio-fungicides as soil drench",
        ],
        cultural_control=[
            "Rotate with non-legume crops for 2 seasons",
            "Remove and burn crop residue after harvest",
            "Avoid dense plant populations that restrict air flow",
            "Plant improved varieties with partial resistance",
        ],
        economic_threshold="15% leaf area affected before pod fill stage",
        severity_scale={
            "mild": "< 10% leaf area, cosmetic damage only",
            "moderate": "10-25% leaf area, partial defoliation",
            "severe": "> 25% leaf area, premature defoliation and significant yield loss",
        },
    ),
    DiseaseProfile(
        name="Bacterial Blight",
        pathogen="Xanthomonas axonopodis pv. vignicola",
        pathogen_type="bacterial",
        symptoms=[
            "Water-soaked spots on leaves that dry to brown necrotic lesions",
            "Lesions may coalesce causing large dead areas",
            "Pod lesions appear as dark sunken spots",
            "Seed discolouration in severe infections",
        ],
        identification_markers=[
            "Water-soaked margins around leaf lesions (hold leaf to light)",
            "Bacterial ooze on leaf surface under humid conditions",
            "Lesions follow angular leaf vein pattern",
        ],
        favourable_conditions={"temp_min_c": 25, "temp_max_c": 35, "humidity_min": 85},
        susceptible_stages=["Vegetative", "Flowering", "Pod Fill"],
        resistant_varieties=["IT 18"],
        susceptible_varieties=["Local landraces"],
        chemical_control=[
            {"name": "Copper oxychloride 85 WP", "rate": "2.5-3.0 kg/ha",
             "phi_days": "7", "notes": "Protectant; apply before rain events when symptoms first appear"},
        ],
        biological_control=[
            "Bacillus subtilis-based biocontrol agents",
        ],
        cultural_control=[
            "Use certified disease-free seed",
            "Avoid overhead irrigation — use drip or furrow",
            "Rotate with non-legume crops for 2-3 seasons",
            "Do not work in fields when foliage is wet",
        ],
        economic_threshold="10% of plants showing leaf and pod lesions",
        severity_scale={
            "mild": "Scattered leaf spots, < 10% plants affected",
            "moderate": "10-30% plants with leaf and some pod lesions",
            "severe": "> 30% plants affected, pods infected, seed quality compromised",
        },
    ),
]

_pests: List[PestProfile] = [
    PestProfile(
        name="Legume Pod Borer",
        scientific_name="Maruca vitrata",
        pest_type="insect",
        identification=[
            "Adult moth: pale brown, 20-25 mm wingspan, dark markings on forewings",
            "Larva: greenish with dark head, up to 18 mm long",
            "Larva bores into flower buds, flowers, and pods",
            "Silk webbing around flowers and pod clusters",
        ],
        damage_symptoms=[
            "Webbing of flowers and young pods",
            "Holes bored into pods with frass visible",
            "Flower abortion and pod shedding",
            "Larvae feeding inside pods consuming developing seeds",
        ],
        life_cycle_notes="Complete cycle 25-30 days. Female lays 200-400 eggs on flower buds. "
                         "Larva feeds inside flowers then moves to pods. Pupation in soil. "
                         "Multiple overlapping generations per season in Zimbabwe.",
        favourable_conditions={"temp_min_c": 25, "temp_max_c": 35, "humidity_min": 60},
        susceptible_stages=["Flowering", "Pod Fill"],
        economic_threshold="1-2 larvae per plant at flowering, or 10% pods damaged",
        chemical_control=[
            {"name": "Lambda-cyhalothrin 5 EC", "rate": "0.3-0.4 L/ha",
             "phi_days": "14", "notes": "Apply at first flower bud formation; target larvae before they bore in"},
            {"name": "Emamectin benzoate 5 SG", "rate": "0.3 kg/ha",
             "phi_days": "7", "notes": "Effective against larvae inside flowers; low impact on beneficials"},
        ],
        biological_control=[
            "Trichogramma egg parasitoids",
            "Bacillus thuringiensis (Bt) sprays for young larvae",
            "Encourage natural enemies — spiders, ground beetles",
        ],
        cultural_control=[
            "Early planting to avoid peak moth populations in late season",
            "Remove and destroy webbed flower clusters",
            "Intercrop with sorghum or maize to disrupt host-finding",
            "Plough in crop residue to destroy pupae",
        ],
        scouting_protocol="From first flower appearance, inspect 20 plants per field (5 plants at "
                          "4 locations). Shake flowers over white paper and count larvae. "
                          "Also check for webbed flower clusters. Scout twice per week during flowering.",
    ),
    PestProfile(
        name="Cowpea Aphid",
        scientific_name="Aphis craccivora",
        pest_type="insect",
        identification=[
            "Small (1.5-2 mm), shiny black aphid",
            "Dense colonies on growing tips, flower buds, and young pods",
            "Winged forms develop when colonies become crowded",
            "Honeydew and sooty mould on lower leaves",
        ],
        damage_symptoms=[
            "Wilting and curling of young leaves and growing points",
            "Stunted plant growth",
            "Sooty mould development on honeydew deposits",
            "Virus transmission (CABMV) — most important damage",
            "Flower and young pod abortion under heavy infestation",
        ],
        life_cycle_notes="Parthenogenetic reproduction; females give birth to live nymphs (no egg stage). "
                         "Population can double every 3-4 days under warm conditions. "
                         "Winged migrants colonise new fields, transmitting viruses.",
        favourable_conditions={"temp_min_c": 20, "temp_max_c": 30, "humidity_min": 40},
        susceptible_stages=["Emergence", "Vegetative", "Flowering"],
        economic_threshold="20 aphids per growing tip on 50% of plants, or first virus symptoms",
        chemical_control=[
            {"name": "Dimethoate 40 EC", "rate": "0.5 L/ha",
             "phi_days": "14", "notes": "Systemic; effective but kills beneficial insects"},
            {"name": "Acetamiprid 20 SP", "rate": "0.1 kg/ha",
             "phi_days": "7", "notes": "Lower toxicity to pollinators than older neonicotinoids"},
        ],
        biological_control=[
            "Ladybird beetles (Coccinellidae) — key predators",
            "Hoverfly larvae (Syrphidae) — each larva eats 400+ aphids",
            "Lacewing larvae (Chrysoperla spp.)",
            "Parasitic wasp Aphidius colemani",
        ],
        cultural_control=[
            "Early planting to establish crop before aphid peak",
            "Remove volunteer cowpea plants (green bridge)",
            "Intercropping with cereals reduces aphid colonisation",
            "Avoid excessive N fertiliser which promotes succulent growth",
        ],
        scouting_protocol="From emergence, inspect 20 plants weekly (5 per quadrant). "
                          "Count aphids on terminal 10 cm of main stem. "
                          "Check for winged aphids which indicate immigration events. "
                          "Monitor for virus symptoms on young leaves. Scout twice weekly in warm weather.",
    ),
    PestProfile(
        name="Bruchid Beetle (Storage Pest)",
        scientific_name="Callosobruchus maculatus",
        pest_type="insect",
        identification=[
            "Adult: small beetle 2-3.5 mm, reddish-brown with dark mottling on wing covers",
            "Eggs: white, glued to seed surface",
            "Larva develops entirely inside the seed — internal feeder",
            "Round exit holes in seeds with powder residue",
        ],
        damage_symptoms=[
            "Circular exit holes in stored seed",
            "Weight loss of 20-50% in severe infestations",
            "Fine powder (frass) accumulating in grain bulk",
            "Reduced germination and nutritional quality",
            "Seeds become hollow and unmarketable",
        ],
        life_cycle_notes="Female lays 60-80 eggs on seed surface. Larva bores into seed and completes "
                         "entire development inside (25-30 days at 30°C). Adult emerges through round exit hole. "
                         "Infestation begins in the field on mature pods and continues in storage.",
        favourable_conditions={"temp_min_c": 25, "temp_max_c": 35, "humidity_min": 60},
        susceptible_stages=["Maturity", "Post-harvest storage"],
        economic_threshold="1-2 exit holes per 100 seeds in stored grain",
        chemical_control=[
            {"name": "Actellic Super (pirimiphos-methyl + permethrin)", "rate": "50 g/90 kg bag",
             "phi_days": "N/A", "notes": "Admix with grain before storage. Do NOT use on seed for planting."},
        ],
        biological_control=[
            "Hermetic storage (PICS bags, metal silos) — deprives insects of oxygen",
            "Neem leaf powder mixed with stored grain (50 g/kg)",
            "Diatomaceous earth (100 g/100 kg grain)",
        ],
        cultural_control=[
            "Harvest promptly at maturity — do not leave dry pods in field",
            "Sun-dry grain to <10% moisture before storage",
            "Use hermetic (PICS/GrainPro) bags — most effective for smallholders",
            "Clean store thoroughly before new harvest",
            "Triple-bag in polythene for oxygen deprivation",
        ],
        scouting_protocol="At harvest: inspect sample of 200 seeds for eggs or exit holes. "
                          "In storage: monthly inspection — pour 1 kg sample onto white surface and "
                          "count live adults and seeds with exit holes. If > 2 adults per kg, "
                          "re-treat or transfer to hermetic storage immediately.",
    ),
]

_growth_stages: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Emergence",
        stage_code="VE",
        day_range=(0, 10),
        water_kc=0.30,
        water_mm_per_week=12,
        critical_nutrients=["P"],
        key_activities=[
            "Plant at 3-5 cm depth in moist soil",
            "Apply Rhizobium inoculant if field has no cowpea history",
            "Scout for cutworms and ants",
            "Gap-fill by day 10 if emergence is poor",
        ],
        risks=["Poor emergence in crusted soils", "Cutworm damage to emerging seedlings",
               "Ants carrying away seed"],
        scientific_notes="Cowpea is an epigeal germinator — cotyledons emerge above soil. "
                         "Soil crusting after heavy rain can trap cotyledons. "
                         "Vigna unguiculata fixes N via Bradyrhizobium spp.; inoculation is critical "
                         "in fields without prior cowpea/compatible legume history.",
    ),
    GrowthStageRequirements(
        stage_name="Vegetative Growth",
        stage_code="V1-V5",
        day_range=(10, 30),
        water_kc=0.50,
        water_mm_per_week=20,
        critical_nutrients=["P", "Mo"],
        key_activities=[
            "First weeding at 2-3 weeks after emergence",
            "Check nodulation at 21 days — cut roots, look for pink active nodules",
            "Scout for aphids on growing tips",
            "Second weeding before canopy closure",
        ],
        risks=["Weed competition (critical weed-free period: first 30 days)",
               "Aphid infestation and virus transmission"],
        scientific_notes="Cowpea canopy closes relatively quickly in indeterminate types. "
                         "The critical weed-free period is the first 3-4 weeks. "
                         "Effective N-fixation begins ~14 DAP when nodules turn pink internally "
                         "(indicating active leghemoglobin). Mo is essential as a cofactor for "
                         "nitrogenase enzyme.",
    ),
    GrowthStageRequirements(
        stage_name="Flowering",
        stage_code="R1-R2",
        day_range=(30, 45),
        water_kc=0.80,
        water_mm_per_week=35,
        critical_nutrients=["K", "Ca", "B"],
        key_activities=[
            "Scout for Maruca pod borer on flower buds",
            "Monitor aphid pressure — virus transmission most damaging at this stage",
            "Ensure adequate moisture — drought causes flower abortion",
            "Do NOT apply broad-spectrum insecticides during peak pollination",
        ],
        risks=["Maruca pod borer — larvae in flower buds",
               "Drought-induced flower abortion", "Thrips damage to flowers"],
        scientific_notes="Cowpea is predominantly self-pollinating, but bee visits increase pod set "
                         "by 10-20%. Flower opening is in early morning (0600-0900). "
                         "Drought stress during flowering can reduce yield by 50-70%. "
                         "Indeterminate types continue flowering over 2-3 weeks, providing yield insurance.",
    ),
    GrowthStageRequirements(
        stage_name="Pod Development",
        stage_code="R3-R5",
        day_range=(45, 60),
        water_kc=0.75,
        water_mm_per_week=30,
        critical_nutrients=["K", "N (from fixation)"],
        key_activities=[
            "Scout pods for pod borer damage — check for entry holes and frass",
            "Monitor for pod-sucking bugs (Clavigralla, Riptortus)",
            "Maintain moisture — pod fill is sensitive to drought",
            "Spray if pod borer threshold exceeded",
        ],
        risks=["Pod borer (Maruca) boring into developing pods",
               "Pod-sucking bugs causing shrivelled seeds",
               "Late-season drought reducing seed size"],
        scientific_notes="During pod fill, photosynthate is translocated to developing seeds. "
                         "The plant remobilises N from leaves and nodules to seeds — this causes "
                         "natural lower-leaf senescence. K is critical for assimilate translocation. "
                         "Seeds accumulate 22-25% protein, one of the highest among grain legumes.",
    ),
    GrowthStageRequirements(
        stage_name="Pod Maturation",
        stage_code="R6-R7",
        day_range=(60, 75),
        water_kc=0.40,
        water_mm_per_week=15,
        critical_nutrients=[],
        key_activities=[
            "First harvest of dry pods (indeterminate types produce pods sequentially)",
            "Check pod moisture — harvest individual pods as they dry",
            "Scout for storage pests (bruchids) — infestation begins in field",
            "Prepare drying and storage facilities",
        ],
        risks=["Pod shattering if over-mature in hot sun",
               "Bruchid infestation starting in dry field pods",
               "Rain damage to mature pods (discolouration, sprouting)"],
        scientific_notes="Indeterminate cowpea varieties allow 2-3 harvests of dry pods as they "
                         "mature progressively from bottom to top. Determinate types mature uniformly. "
                         "Harvest at physiological maturity when pods turn brown/tan and rattle when shaken. "
                         "Seed moisture should be 14-16% at harvest, dried to <10% for storage.",
    ),
    GrowthStageRequirements(
        stage_name="Final Harvest & Fodder",
        stage_code="R8",
        day_range=(75, 90),
        water_kc=0.20,
        water_mm_per_week=5,
        critical_nutrients=[],
        key_activities=[
            "Complete pod harvest — strip remaining pods",
            "Cut haulms for livestock fodder (high protein: 14-18% CP)",
            "Dry seeds to <10% moisture for safe storage",
            "Store in hermetic bags (PICS) to prevent bruchid damage",
        ],
        risks=["Bruchid infestation if storage is delayed",
               "Aflatoxin if grain stored wet"],
        scientific_notes="Cowpea haulms (leaves and stems) are highly valued livestock fodder, "
                         "especially in semi-arid regions. Haulm dry matter yield is 1-3 t/ha with "
                         "14-18% crude protein — comparable to commercial cattle feed. "
                         "The dual-purpose nature (grain + fodder) makes cowpea uniquely valuable "
                         "for mixed crop-livestock smallholder systems in NR III-V.",
    ),
]

_fertilizer = FertilizerSchedule(
    basal={
        "product": "Compound D (7:14:7) or Single Super Phosphate (SSP)",
        "rate": "150-200 kg/ha Compound D, or 150 kg/ha SSP",
        "timing": "At planting, banded 5 cm beside and below seed",
        "nutrients_supplied": {"N": "10-14 kg (starter only)", "P": "21-28 kg P2O5", "K": "10-14 kg K2O"},
        "scientific_basis": "Cowpea fixes its own N but needs a small starter N dose. "
                            "P is critical for nodulation and root development. "
                            "SSP is preferred as it also supplies S and Ca.",
    },
    top_dress_1={
        "product": "Not normally required for cowpea",
        "rate": "Only if crop looks pale/stunted and nodulation has failed",
        "timing": "25-30 DAP if visual deficiency symptoms",
        "application": "AN at 50 kg/ha only as rescue treatment",
        "scientific_basis": "Applying N top-dressing to cowpea SUPPRESSES nodulation. "
                            "Only apply if nodulation check at 21 DAP shows no active (pink) nodules.",
    },
    liming={
        "product": "Calcitic or dolomitic lime",
        "rate": "1-2 t/ha if pH < 5.0",
        "timing": "3-6 months before planting",
        "scientific_basis": "Bradyrhizobium is sensitive to Al toxicity below pH 5.0. "
                            "Liming to pH 5.5-6.5 improves nodulation and P availability.",
    },
    notes="Cowpea is a N-fixing legume — DO NOT apply N top-dressing unless nodulation has failed. "
          "Excessive N application suppresses biological N fixation and wastes money. "
          "Inoculate seed with Bradyrhizobium spp. if planting in a new field. "
          "Residual soil fertility from previous maize crop is usually adequate for cowpea.",
)

_planting_windows: List[PlantingWindow] = [
    PlantingWindow(
        region="Natural Region I",
        optimal_start="November 15", optimal_end="December 15",
        acceptable_start="November 1", acceptable_end="January 15",
        notes="Ample rainfall; all varieties suitable. Can follow early potato crop.",
    ),
    PlantingWindow(
        region="Natural Region II",
        optimal_start="November 15", optimal_end="December 15",
        acceptable_start="November 1", acceptable_end="January 10",
        notes="Good rainfall zone. Intercrop with maize common. Plant after effective planting rains.",
    ),
    PlantingWindow(
        region="Natural Region III",
        optimal_start="December 1", optimal_end="December 31",
        acceptable_start="November 15", acceptable_end="January 15",
        notes="Semi-intensive zone. Use early-maturing varieties (CBC1, CBC2). "
              "Cowpea is well-suited to this region due to drought tolerance.",
    ),
    PlantingWindow(
        region="Natural Region IV",
        optimal_start="December 1", optimal_end="January 5",
        acceptable_start="November 20", acceptable_end="January 20",
        notes="Semi-arid zone — cowpea is ideal crop. Use drought-tolerant varieties (IT 18, CBC5). "
              "Intercrop with sorghum or pearl millet. Plant on moisture.",
    ),
    PlantingWindow(
        region="Natural Region V",
        optimal_start="December 15", optimal_end="January 15",
        acceptable_start="December 1", acceptable_end="January 31",
        notes="Marginal rainfall. Cowpea is one of few viable grain crops. "
              "Use extra-early varieties. Harvest haulms for dry-season livestock feed.",
    ),
]

PROFILE = CropProfile(
    crop_name="Cowpeas",
    scientific_name="Vigna unguiculata (L.) Walp.",
    family="Fabaceae",
    optimal_ph=(5.5, 7.0),
    critical_ph_low=5.0,
    optimal_soil_types=["Sandy loams", "Well-drained loams", "Red fersiallitic soils"],
    avoid_soil_types=["Waterlogged soils", "Heavy cracking clays", "Saline soils"],
    optimal_temp=(25.0, 35.0),
    critical_temp_low=15.0,
    critical_temp_high=40.0,
    base_temp_gdd=10.0,
    total_water_mm=300.0,
    growth_stages=_growth_stages,
    fertilizer_schedule=_fertilizer,
    diseases=_diseases,
    pests=_pests,
    planting_windows=_planting_windows,
    harvest_moisture="Harvest dry pods at 14-16% seed moisture. Dry to <10% for safe storage.",
    storage_conditions="Store in hermetic bags (PICS) at <10% moisture. "
                       "Bruchid beetles are the #1 storage threat — hermetic storage is essential.",
    post_harvest_notes="Cowpea grain provides 22-25% protein, critical for household nutrition. "
                       "Haulms are valuable livestock fodder (14-18% CP). "
                       "Premium prices for large-seeded, unblemished white grain.",
    natural_region_suitability={
        "I": "Suitable — but higher-value crops usually preferred",
        "IIa": "Good — common as intercrop with maize",
        "IIb": "Good — common as intercrop with maize",
        "III": "Excellent — well-suited, reliable production",
        "IV": "Excellent — one of the best crops for this zone",
        "V": "Good — drought tolerance makes it viable where most crops fail",
    },
)

ALIASES = ["cowpea", "nyemba"]
