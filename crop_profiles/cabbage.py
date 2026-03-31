"""Cabbage (Brassica oleracea var. capitata) — important peri-urban vegetable in Zimbabwe, winter/cool-season crop grown year-round under irrigation."""

from crop_profiles._base import (
    CropProfile, DiseaseProfile, PestProfile,
    GrowthStageRequirements, FertilizerSchedule, PlantingWindow,
)
from typing import List, Dict, Any


# CABBAGE (Brassica oleracea var. capitata)
# ---------------------------------------------------------------------------

_diseases: List[DiseaseProfile] = [
    DiseaseProfile(
        name="Black Rot",
        pathogen="Xanthomonas campestris pv. campestris",
        pathogen_type="bacterial",
        symptoms=[
            "V-shaped, yellow to brown lesions starting from leaf margins, with the apex pointing toward the midrib",
            "Darkened, blackened veins (xylematic discolouration) running from the leaf margin inward",
            "Leaf lesions turn dry and papery as the disease advances",
            "Internal head discolouration: black vascular ring visible when head is cut cross-section",
            "Severely affected plants are stunted and produce small, unmarketable heads",
        ],
        identification_markers=[
            "V-shaped yellowing at leaf margins — diagnostic sign of black rot",
            "Black veins visible within the V-shaped lesion",
            "Vascular blackening in stem and head cross-section",
            "Symptoms begin on leaf margins and move inward — never as a leaf-spot in isolation",
        ],
        favourable_conditions={"temp_min_c": 25, "temp_max_c": 35, "humidity_min": 70},
        susceptible_stages=["Transplant Establishment", "Vegetative/Rosette", "Head Formation"],
        resistant_varieties=["Star 3311 (moderate tolerance)", "Conquistador (moderate)"],
        susceptible_varieties=["Copenhagen Market", "Drumhead"],
        chemical_control=[
            {"name": "Copper oxychloride 50 WP", "rate": "2.0-2.5 kg/ha",
             "phi_days": "14", "notes": "Protectant copper; apply at weekly intervals from transplanting. Do not spray in hot sun."},
            {"name": "Copper hydroxide 77 WP (Kocide)", "rate": "2.0 kg/ha",
             "phi_days": "7", "notes": "Broad-spectrum bactericide; good adhesion in rain. Rotate with mancozeb."},
            {"name": "Kasugamycin 2 SL", "rate": "1.5 L/ha",
             "phi_days": "7", "notes": "Antibiotic bactericide; use as curative when early symptoms appear. Limit to 2 applications per season."},
        ],
        biological_control=[
            "Bacillus subtilis-based products (e.g., Serenade) applied as foliar spray",
            "Avoid wounding during transplanting and cultivation — wounds are primary entry points",
        ],
        cultural_control=[
            "Use certified disease-free seed and transplants",
            "Treat seed with hot water (50°C for 30 minutes) before sowing to eliminate seed-borne inoculum",
            "Avoid overhead irrigation — spreads bacterial inoculum in water droplets",
            "Rotate with non-brassica crops for at least 2 years",
            "Remove and destroy infected plant debris at end of season",
            "Avoid working in field when plants are wet",
            "Control insects (especially flea beetles and aphids) that wound leaf tissue",
        ],
        economic_threshold="5% plants showing V-shaped lesions; spray immediately — disease spreads rapidly in warm wet weather",
        severity_scale={
            "mild": "< 5% plants with marginal lesions, no vascular blackening yet",
            "moderate": "5-25% plants affected with vascular blackening; head quality affected on some plants",
            "severe": "> 25% plants affected, widespread head discolouration, major yield and quality loss",
        },
    ),
    DiseaseProfile(
        name="Clubroot",
        pathogen="Plasmodiophora brassicae",
        pathogen_type="fungal",  # obligate soil-borne protist, classified here as fungal for system compatibility
        symptoms=[
            "Above-ground: wilting during warm afternoons (early sign), yellowing and stunting",
            "Leaves become pale green to yellow, plant fails to produce marketable head",
            "Below-ground (diagnostic): grotesque, club-shaped galls on roots and hypocotyl",
            "Galls are firm when young, become soft and rotten as they break down",
            "Severely infected plants may die before heading",
        ],
        identification_markers=[
            "PULL AND EXAMINE ROOTS: club-shaped, fused root galls are unmistakable",
            "Galls are smooth externally (unlike root-knot nematode galls which are beaded)",
            "Afternoon wilting of apparently healthy-looking top growth",
            "No recovery after irrigation — unlike drought stress",
        ],
        favourable_conditions={"temp_min_c": 18, "temp_max_c": 25, "soil_ph_max": 6.5, "humidity_min": 60},
        susceptible_stages=["Seedling/Nursery", "Transplant Establishment", "Vegetative/Rosette"],
        resistant_varieties=["Kilabu F1 (clubroot resistance)", "Kilaton F1"],
        susceptible_varieties=["Copenhagen Market", "Star 3311 (susceptible)"],
        chemical_control=[
            {"name": "Metalaxyl + Thiram seed treatment", "rate": "3 g/kg seed",
             "phi_days": "N/A", "notes": "Seed treatment; partial protection in nursery. Not curative once soil infested."},
            {"name": "Fluazinam (Shirlan 500 SC)", "rate": "0.5 L/ha",
             "phi_days": "N/A", "notes": "Soil drench at transplanting; reduces infection. Use in confirmed clubroot fields."},
        ],
        biological_control=[
            "Apply lime to raise soil pH above 7.0 — Plasmodiophora is suppressed at high pH",
            "Trichoderma-based soil inoculants to improve root health",
        ],
        cultural_control=[
            "Raise soil pH to 7.0-7.2 by liming — most effective management strategy",
            "Long rotation (3-4 years) away from all brassicas including weeds (wild mustard, shepherd's purse)",
            "Avoid moving soil from infected fields on boots, tools, or equipment",
            "Use clean nursery substrate — do not re-use soil from old nursery beds",
            "Improve soil drainage — clubroot thrives in wet, poorly drained soils",
            "Destroy infected plants including roots — do not compost",
        ],
        economic_threshold="Any confirmed clubroot in a field requires full rotation change. Once soil is infested, it remains infested for 15-20 years.",
        severity_scale={
            "mild": "< 5% plants with small galls; marginal yield impact in well-limed soil",
            "moderate": "5-20% plants with galls; noticeable stunting and yield reduction",
            "severe": "> 20% plants severely infected; unmarketable heads or total crop failure in badly infested soil",
        },
    ),
    DiseaseProfile(
        name="Downy Mildew",
        pathogen="Peronospora parasitica",
        pathogen_type="oomycete",
        symptoms=[
            "Yellow, irregular patches on upper leaf surface, often angular and bounded by leaf veins",
            "White to grey-purple, fluffy sporulation on corresponding underside of leaves",
            "Affected leaf tissue turns brown and dies as disease progresses",
            "On seedlings in nursery: rapid collapse ('damping off'-like appearance) under very humid conditions",
            "Head wrapper leaves affected, reducing marketability",
        ],
        identification_markers=[
            "White to pale grey cottony growth on UNDERSIDE of leaf — the most reliable sign",
            "Yellow patch on upper surface corresponds exactly to sporulation below",
            "Most severe in seedling nurseries and on young transplants",
            "Cooler temperatures and very high humidity favour explosive spread",
        ],
        favourable_conditions={"temp_min_c": 8, "temp_max_c": 20, "humidity_min": 85},
        susceptible_stages=["Seedling/Nursery", "Transplant Establishment", "Vegetative/Rosette"],
        resistant_varieties=["Star 3311 (moderate)", "Conquistador (moderate)"],
        susceptible_varieties=["Copenhagen Market"],
        chemical_control=[
            {"name": "Metalaxyl + Mancozeb (Ridomil Gold MZ 68 WG)", "rate": "2.5 kg/ha",
             "phi_days": "14", "notes": "Systemic + protectant; best option for oomycete control. Apply preventively in cool, humid conditions."},
            {"name": "Mancozeb 80 WP", "rate": "2.0-2.5 kg/ha",
             "phi_days": "7", "notes": "Protectant only; apply at 7-day intervals during high-risk periods"},
            {"name": "Cymoxanil + Mancozeb", "rate": "2.5 kg/ha",
             "phi_days": "7", "notes": "Translaminar activity; good for early curative action when symptoms first appear"},
            {"name": "Fosetyl-aluminium 80 WP (Aliette)", "rate": "2.0 kg/ha",
             "phi_days": "14", "notes": "Systemic oomyceticide; excellent curative and preventive activity"},
        ],
        biological_control=[
            "Bacillus subtilis foliar sprays in nurseries",
            "Copper-based products (copper hydroxide) for organic production",
        ],
        cultural_control=[
            "Avoid dense seeding in nurseries — space for good air circulation",
            "Water nurseries in the morning so foliage dries before nightfall",
            "Avoid overhead irrigation on mature plants",
            "Harden transplants progressively before field placement",
            "Remove and destroy affected lower leaves",
            "Ensure wide plant spacing to improve canopy airflow",
        ],
        economic_threshold="First confirmed sporulation on leaf undersides in nursery — spray immediately. In field, 10% of plants with symptoms.",
        severity_scale={
            "mild": "< 10% of leaf area affected; no wrapper leaf damage",
            "moderate": "10-30% of canopy affected; wrapper leaves showing lesions; reduced marketability",
            "severe": "> 30% canopy affected; severe defoliation; head development impaired",
        },
    ),
    DiseaseProfile(
        name="Alternaria Leaf Spot",
        pathogen="Alternaria brassicae / A. brassicicola",
        pathogen_type="fungal",
        symptoms=[
            "Small, dark brown to black circular spots on leaves, with or without concentric rings",
            "Spots may have a yellow halo in susceptible varieties",
            "Lesions coalesce under high disease pressure, causing large necrotic areas",
            "Spots on outer wrapper leaves reduce head quality and marketability",
            "Seed pods and stems can also be affected under heavy infection",
        ],
        identification_markers=[
            "Round to oval dark spots, typically 1-5 cm diameter",
            "Concentric ring pattern visible in older lesions under good light",
            "Sooty black spore mass visible in lesion centre under moist conditions",
            "Starts on older, lower leaves — progresses upward",
        ],
        favourable_conditions={"temp_min_c": 18, "temp_max_c": 30, "humidity_min": 75},
        susceptible_stages=["Vegetative/Rosette", "Head Formation", "Head Maturation"],
        resistant_varieties=["Star 3311 (moderate tolerance)"],
        susceptible_varieties=["Copenhagen Market"],
        chemical_control=[
            {"name": "Iprodione 500 SC (Rovral)", "rate": "1.0 L/ha",
             "phi_days": "7", "notes": "Dicarboximide; excellent for Alternaria. Apply at first sign of symptoms."},
            {"name": "Mancozeb 80 WP", "rate": "2.0-2.5 kg/ha",
             "phi_days": "7", "notes": "Broad-spectrum protectant; apply at 7-10 day intervals"},
            {"name": "Azoxystrobin 250 SC (Amistar)", "rate": "0.5 L/ha",
             "phi_days": "3", "notes": "Strobilurin; systemic, excellent curative and protectant. Max 3 apps/season to manage resistance."},
            {"name": "Boscalid + Pyraclostrobin (Bellis WG)", "rate": "0.8 kg/ha",
             "phi_days": "7", "notes": "Dual mode of action; excellent spectrum including Alternaria and downy mildew"},
        ],
        biological_control=[
            "Trichoderma harzianum foliar applications",
            "Remove infected lower leaves to reduce inoculum",
        ],
        cultural_control=[
            "Use disease-free seed — Alternaria is seed-borne",
            "Treat seed with Thiram or Iprodione before sowing",
            "Rotate with non-brassica crops for 2 years",
            "Avoid wetting foliage — use drip or furrow irrigation",
            "Remove and destroy infected crop residue at season end",
            "Maintain wide plant spacing to reduce humidity within canopy",
        ],
        economic_threshold="15% of wrapper leaves with spots, or first spots appearing on head leaves — spray to protect marketability",
        severity_scale={
            "mild": "< 15% of outer leaves with small spots; head unaffected",
            "moderate": "15-40% leaf area affected; wrapper leaves showing prominent spots; marketability reduced",
            "severe": "> 40% canopy affected; spots on head leaves; significant loss of marketable yield",
        },
    ),
]

_pests: List[PestProfile] = [
    PestProfile(
        name="Diamondback Moth",
        scientific_name="Plutella xylostella",
        pest_type="insect",
        identification=[
            "Adult: small grey-brown moth (8-9 mm wingspan); when wings folded, three cream diamond shapes visible along back — diagnostic",
            "Larva: small (< 10 mm), pale green, tapered at both ends, wriggles vigorously when disturbed",
            "Pupa: in transparent, loose, hammock-like silk cocoon on leaf underside",
            "Eggs: tiny (0.5 mm), oval, pale yellow-green, laid singly or in small groups on leaf surface near veins",
        ],
        damage_symptoms=[
            "Window-paning: larvae scrape lower leaf surface, leaving upper epidermis intact — translucent pale patches visible from above",
            "Holes through leaves where larvae have fed completely through",
            "Small green pellets of frass on leaves and in head",
            "Young larvae mine briefly inside leaf tissue before window-paning",
            "Severe infestations cause 'shot-hole' appearance and skeleton-like leaves",
            "Head boring by late-instar larvae reduces marketability severely",
        ],
        life_cycle_notes="Complete cycle 16-25 days at 25°C — fastest of all cabbage pests. Female lays 150-300 eggs. "
                         "4 larval instars; L1 mines leaf briefly, L2-L4 feed on leaf surface. "
                         "Up to 12 generations per year in Zimbabwe's climate. Highly prone to insecticide resistance "
                         "— resistance documented to organophosphates, pyrethroids, carbamates, and some Bt products. "
                         "Resistance management through rotation of chemical groups is CRITICAL. "
                         "Adults migrate long distances on wind currents, making population surges unpredictable.",
        favourable_conditions={"temp_min_c": 15, "temp_max_c": 30, "humidity_min": 40},
        susceptible_stages=["Transplant Establishment", "Vegetative/Rosette", "Head Formation"],
        economic_threshold="20 larvae per 10 plants (seedling to early rosette), or 5 larvae per plant during head formation",
        chemical_control=[
            {"name": "Emamectin benzoate 5 SG", "rate": "0.3 kg/ha",
             "phi_days": "7", "notes": "Avermectin; translaminar, reaches larvae feeding within leaves. Highly effective, low resistance. Key rotation partner."},
            {"name": "Spinosad 480 SC (Tracer)", "rate": "0.1 L/ha",
             "phi_days": "3", "notes": "Naturalyte; highly effective against young larvae. Rotate with other groups to protect activity."},
            {"name": "Chlorantraniliprole 200 SC (Coragen)", "rate": "0.15 L/ha",
             "phi_days": "1", "notes": "Diamide (Group 28); excellent efficacy, very low mammalian toxicity. Use as part of resistance rotation."},
            {"name": "Indoxacarb 150 SC (Steward)", "rate": "0.25 L/ha",
             "phi_days": "5", "notes": "Oxadiazine (Group 22); pro-insecticide activated in insect gut. Good against pyrethroid-resistant populations."},
            {"name": "Bacillus thuringiensis var. kurstaki (Btk)", "rate": "1.0-1.5 kg/ha",
             "phi_days": "0", "notes": "Biological insecticide; effective on young larvae. Must contact larvae — thorough coverage essential. Use in resistance management rotation."},
        ],
        biological_control=[
            "Cotesia plutellae — endoparasitoid wasp of DBM larvae; commonly found in Zimbabwe fields",
            "Diadegma semiclausum — larval parasitoid; important at cooler temperatures (above 1000 m elevation)",
            "Diadromus collaris — pupal parasitoid",
            "Bacillus thuringiensis subsp. kurstaki (Btk) — effective as biopesticide",
            "Chrysoperla lacewing larvae — generalist predator in nurseries",
            "Avoid broad-spectrum insecticides that destroy parasitoid populations",
        ],
        cultural_control=[
            "Avoid continuous brassica production — a 6-8 week brassica-free break drastically reduces DBM populations",
            "Remove and destroy old brassica crop residue immediately after final harvest",
            "Intercrop with non-host aromatic plants (e.g., coriander, dill) to attract parasitoids",
            "Insect-proof net covers on seedling nurseries prevent early colonisation",
            "Stagger planting dates to disrupt continuous DBM population build-up",
            "Overhead irrigation temporarily dislodges and drowns larvae — use strategically during peak infestations",
        ],
        scouting_protocol="From transplanting, inspect 20 plants twice weekly (5 from each field quadrant). "
                          "Examine both leaf surfaces — count live larvae per plant. Check youngest leaves and "
                          "head-forming stage for feeding damage. Hold leaves up to light to see window-paning. "
                          "At heading stage, open outer wrapper leaves to check for larvae inside. "
                          "Record larvae per plant. Resistance testing: if larvae survive at label rate after 3 days, "
                          "switch immediately to a different chemical mode-of-action group.",
    ),
    PestProfile(
        name="Cabbage Aphid",
        scientific_name="Brevicoryne brassicae",
        pest_type="insect",
        identification=[
            "Small (1.5-2.5 mm), blue-grey to greyish-green aphids with a waxy, mealy coating — distinctive grey powder",
            "Form dense, compact, powder-covered colonies on young leaves and developing heads",
            "Both winged (alatae) and wingless (apterae) forms occur; winged forms colonise new plants",
            "Eggs: shiny black, laid on stems and leaf bases in cool season",
        ],
        damage_symptoms=[
            "Dense grey colonies in growing points and head centres — severely distorts young leaves",
            "Affected leaves become curled, cupped, and stunted",
            "Heavy infestations can prevent head formation entirely",
            "Honeydew production leads to black sooty mould growth on leaves",
            "Plants become weak, stunted, and chlorotic under severe infestation",
            "Feeding inside forming heads makes them unmarketable even if aphids are not visible externally",
        ],
        life_cycle_notes="Parthenogenetic (asexual) reproduction for most of the season. A single female can produce "
                         "50-100 nymphs without mating. Generation time 7-14 days in warm weather. "
                         "Populations can double rapidly — early detection is critical. "
                         "Winged females colonise new plants; high-density colonies trigger winged morph production. "
                         "The waxy coat gives partial protection from contact insecticides — high-volume coverage essential.",
        favourable_conditions={"temp_min_c": 15, "temp_max_c": 28, "humidity_min": 40},
        susceptible_stages=["Transplant Establishment", "Vegetative/Rosette", "Head Formation"],
        economic_threshold="10% of plants with aphid colonies in the growing point, or any aphids inside forming heads",
        chemical_control=[
            {"name": "Imidacloprid 200 SL", "rate": "0.25 L/ha",
             "phi_days": "21", "notes": "Systemic neonicotinoid; apply as soil drench at transplanting for 3-4 weeks' systemic protection. Most effective approach."},
            {"name": "Pirimicarb 500 WG (Pirimor)", "rate": "0.25 kg/ha",
             "phi_days": "7", "notes": "Aphid-specific carbamate; spares most beneficial insects including parasitoid wasps. Excellent aphid control."},
            {"name": "Acetamiprid 200 SP", "rate": "0.25 kg/ha",
             "phi_days": "7", "notes": "Systemic neonicotinoid; good curative activity on dense colonies. Ensure thorough coverage."},
            {"name": "Lambda-cyhalothrin 5 EC", "rate": "0.4 L/ha",
             "phi_days": "7", "notes": "Broad-spectrum pyrethroid; use only if no other option — destroys beneficial insects"},
        ],
        biological_control=[
            "Diaeretiella rapae — specialist aphid parasitoid wasp; look for mummified (golden-brown) aphids as evidence",
            "Aphidius colemani — parasitoid wasp; effective at low temperatures",
            "Coccinellid beetles (ladybirds) — important generalist predators",
            "Lacewing (Chrysoperla) larvae — voracious aphid predators",
            "Preserve beneficial insect populations by avoiding broad-spectrum insecticides",
        ],
        cultural_control=[
            "Monitor plant growing points at transplanting — act early before colonies establish",
            "Remove heavily infested growing points by hand (smallholder scale)",
            "Use insect-proof nets on nurseries to prevent initial colonisation",
            "Reflective silver mulch disorients winged aphids and reduces landing rate",
            "Maintain plant vigour through balanced nutrition — over-fertilised (high N) plants are more susceptible",
            "Weed control — remove alternative brassicaceous hosts (wild mustard, shepherd's purse)",
        ],
        scouting_protocol="From transplanting, examine 20 plants twice weekly (5 per quadrant). "
                          "Inspect growing points and youngest leaves for grey powder-covered colonies. "
                          "Check inside head (wrapper leaves) at heading stage. Look for winged aphids trapped on "
                          "yellow sticky traps as early warning of colonisation waves. Record % plants infested "
                          "and colony density (light <20, medium 20-100, heavy >100 aphids per colony).",
    ),
    PestProfile(
        name="Cutworm",
        scientific_name="Agrotis spp. (A. segetum, A. ipsilon)",
        pest_type="insect",
        identification=[
            "Larva: stout, smooth, grey-brown to almost black, up to 50 mm; curls into a tight C when disturbed",
            "Found in soil at base of cut plants during the day — surface feeding only at night",
            "Adult: medium moth (35-45 mm wingspan), brown-grey with dark forewing markings; attracted to light",
            "Eggs: ribbed, dome-shaped, laid singly or in small batches on soil or low plant surfaces",
        ],
        damage_symptoms=[
            "Plants cut off cleanly at or just below soil level — plant collapses but remains green initially",
            "Seedling and transplant losses ('missing plants') — gaps in rows",
            "Stems of older plants partially severed, causing wilting",
            "Rarely, larvae climb stems to feed on leaves at night (surface feeding)",
        ],
        life_cycle_notes="Single generation per season for most Agrotis spp. in Zimbabwe. Larva passes through "
                         "6 instars; damage is caused mainly by L4-L6 larvae at night. Pupation in soil at 5-15 cm. "
                         "Adults are nocturnal and are attracted to light. "
                         "Infestations are worst in fields that follow grass or weedy fallows, or where "
                         "green manure has recently been incorporated. "
                         "Damage concentrated in patches — look for cut plants in sections of the field.",
        favourable_conditions={"temp_min_c": 15, "temp_max_c": 30, "humidity_min": 40},
        susceptible_stages=["Transplant Establishment", "Vegetative/Rosette"],
        economic_threshold="2-3% of plants cut in seedling stage; act immediately as population can cause rapid stand loss",
        chemical_control=[
            {"name": "Chlorpyrifos 48 EC", "rate": "2.0 L/ha",
             "phi_days": "14", "notes": "Soil and surface spray at dusk — apply around base of plants. Highly effective against larvae."},
            {"name": "Lambda-cyhalothrin 5 EC", "rate": "0.5 L/ha",
             "phi_days": "7", "notes": "Pyrethroid; spray soil surface at base of plants at dusk when larvae are active"},
            {"name": "Fipronil granules", "rate": "5-10 kg/ha",
             "phi_days": "N/A", "notes": "Apply to soil at planting in high-risk fields with known cutworm history"},
        ],
        biological_control=[
            "Metarhizium anisopliae soil application — entomopathogenic fungus infects soil-dwelling larvae",
            "Steinernema carpocapsae entomopathogenic nematodes — apply as soil drench to base of plants",
            "Parasitoid wasps (Meteorus spp.) and ground beetles are natural enemies",
        ],
        cultural_control=[
            "Deep ploughing before planting exposes larvae and pupae to birds and sun",
            "Cultivate between beds to disrupt larval habitat and expose pupae",
            "Remove weeds and grass from field borders — adult moths lay eggs on grassy vegetation",
            "Avoid transplanting into freshly turned weedy fields without a waiting period",
            "Bait traps: mix bran + molasses + poison (Carbaryl) — place in small heaps at dusk in affected areas",
            "Scout at dawn — dig at base of cut plants to find larvae",
        ],
        scouting_protocol="From transplanting, walk all field rows at dawn (when larvae return to soil). "
                          "Note any cut or wilted plants. Dig at base of cut plants to find larvae — "
                          "they are typically at 0-5 cm depth. Record number of cut plants per 100 plants. "
                          "Look for adult moths in light traps. Inspect field at night with a torch during high-risk "
                          "periods immediately after transplanting.",
    ),
]

_growth_stages: List[GrowthStageRequirements] = [
    GrowthStageRequirements(
        stage_name="Seedling/Nursery",
        stage_code="SN",
        day_range=(0, 30),
        water_kc=0.35,
        water_mm_per_week=12,
        critical_nutrients=["P", "N"],
        key_activities=[
            "Sow seed in raised nursery beds or trays with well-drained substrate (2:1 river sand:compost)",
            "Sowing rate: 2-3 g seed per m2 of nursery bed, covering ~1 ha transplant demand",
            "Apply thin layer of compost or fine soil over seeds, then mulch with grass until germination",
            "Water twice daily (morning and evening) until emergence; once daily thereafter",
            "Apply balanced starter fertiliser (e.g., Compound C) at low rate once first true leaf appears",
            "Begin hardening off from day 25: reduce watering and expose to direct sun progressively",
        ],
        risks=[
            "Damping-off (Pythium, Rhizoctonia) — overcrowding and overwatering in nursery",
            "Downy mildew (Peronospora parasitica) in humid nurseries",
            "Aphid colonies in growing points — monitor closely",
            "Harsh sun or frost on unprotected seedlings",
        ],
        scientific_notes="Cabbage is transplanted as a plug or bare-root seedling at 4-6 true leaf stage. "
                         "Nursery duration is 28-35 days. A well-established root system with short, sturdy stem "
                         "('stocky' transplant) is essential for rapid field establishment. "
                         "Phosphorus in the nursery substrate promotes strong root development. "
                         "Hardening off (reducing water and increasing sun exposure 5-7 days before transplanting) "
                         "acclimatises seedlings to field conditions and reduces transplant shock significantly.",
    ),
    GrowthStageRequirements(
        stage_name="Transplant Establishment",
        stage_code="TE",
        day_range=(30, 45),
        water_kc=0.45,
        water_mm_per_week=18,
        critical_nutrients=["P", "N"],
        key_activities=[
            "Transplant at 4-6 true leaf stage (30-35 days from sowing) in late afternoon",
            "Spacing: 60 cm between rows x 45 cm within row (37,000 plants/ha) for large head varieties",
            "Water transplants thoroughly immediately after planting — ensure root-soil contact",
            "Apply starter drench: dilute P fertiliser (DAP solution) or Compound C at transplanting",
            "Monitor for cutworm damage at dawn for first 2 weeks — check for cut plants",
            "Weed thoroughly 7-10 days after transplanting",
        ],
        risks=[
            "Transplant shock — roots damaged or dry during transplanting",
            "Cutworm severing stems at soil level during first 2 weeks",
            "Aphid colonisation of growing points",
            "Strong wind or hail damage on newly transplanted seedlings",
        ],
        scientific_notes="Transplanting in the late afternoon reduces water stress on seedlings. "
                         "The establishment phase (first 15 days) is critical — plants need adequate moisture to "
                         "establish contact between root tips and soil aggregates. Phosphorus promotes lateral root "
                         "development. Transplant shock can be reduced by using well-hardened seedlings, "
                         "avoiding root damage, and maintaining soil moisture. "
                         "Spacing affects head size, uniformity, and air circulation — wider spacing reduces "
                         "disease pressure but reduces plant density per hectare.",
    ),
    GrowthStageRequirements(
        stage_name="Vegetative/Rosette",
        stage_code="VEG",
        day_range=(45, 75),
        water_kc=0.75,
        water_mm_per_week=30,
        critical_nutrients=["N", "K", "S"],
        key_activities=[
            "Apply first nitrogen top-dressing (LAN 200 kg/ha) at 3 weeks after transplanting (WAT)",
            "Hoe weed thoroughly — cabbage is poor at competing with weeds during this stage",
            "Begin diamondback moth scouting programme — check leaf undersides for larvae",
            "Start fungicide programme with mancozeb as base protectant",
            "Scout for black rot V-shaped lesions from leaf margins",
        ],
        risks=[
            "Diamondback moth window-paning on young leaves",
            "Cabbage aphid colonies in growing points",
            "Black rot entering through leaf margin wounds",
            "Downy mildew in cool, humid weather",
            "Nitrogen deficiency — outer leaves pale green, growth slow",
        ],
        scientific_notes="The rosette stage builds the photosynthetic leaf area that determines final head size. "
                         "Adequate nitrogen is essential — cabbage is a high N-demanding crop. "
                         "Sulphur is a critical nutrient for brassicas: it is needed for glucosinolate synthesis "
                         "and protein production. Sulphur deficiency shows as yellowing of young leaves (similar "
                         "to N deficiency but starting on YOUNGER leaves). "
                         "Weed competition during this stage can reduce yields by 30-50% — a weed-free period "
                         "to 6 weeks after transplanting is critical.",
    ),
    GrowthStageRequirements(
        stage_name="Head Formation",
        stage_code="HF",
        day_range=(75, 100),
        water_kc=1.05,
        water_mm_per_week=42,
        critical_nutrients=["K", "Ca", "N"],
        key_activities=[
            "Apply second nitrogen top-dressing (LAN 100-150 kg/ha) at 6 weeks after transplanting",
            "Increase irrigation frequency — head formation demands maximum water",
            "Intensify DBM scouting — larvae found inside forming head are very damaging",
            "Check wrapper leaves for Alternaria leaf spots and downy mildew",
            "Apply foliar calcium (0.5% CaCl2 solution) if soil calcium is marginal — reduces internal tip burn",
        ],
        risks=[
            "Tip burn (calcium deficiency inside head) — caused by poor Ca translocation in hot weather",
            "Diamondback moth larvae feeding inside head — renders head unmarketable",
            "Bolting (premature stem elongation) if prolonged cold period precedes warm spell",
            "Head splitting in early varieties or from uneven irrigation after dry spell",
            "Black rot spreading into head through wrapper leaf veins",
        ],
        scientific_notes="Head formation (cupping) occurs when the terminal growing point begins to produce leaves "
                         "that curve inward instead of outward. This is triggered by sufficient leaf area and "
                         "favourable temperatures (12-20°C optimal). "
                         "Tip burn is a calcium deficiency disorder of inner head leaves caused by high transpiration "
                         "demand exceeding Ca supply to poorly transpiring inner leaves. It is exacerbated by "
                         "rapid growth, high N, low Ca, and moisture stress. Regular Ca foliar sprays help. "
                         "Water demand is at its peak during head filling — deficit irrigation at this stage "
                         "directly reduces head weight and marketable yield.",
    ),
    GrowthStageRequirements(
        stage_name="Head Maturation",
        stage_code="HM",
        day_range=(100, 120),
        water_kc=0.90,
        water_mm_per_week=32,
        critical_nutrients=["K"],
        key_activities=[
            "Monitor head firmness — harvest when heads are firm and well-filled but before splitting",
            "Reduce irrigation 7-10 days before intended harvest to firm heads and improve storage quality",
            "Continue DBM and aphid monitoring — infestation at this stage reduces marketability",
            "Grade fields — mark sections that are ready for first, second, and third picks",
            "Do not apply high-N fertiliser at this stage — excess N delays maturation and softens heads",
        ],
        risks=[
            "Head splitting from rain or re-irrigation after moisture stress at late maturity",
            "Over-mature heads — become loose, bitter, and susceptible to disease",
            "Caterpillar infestation inside heads discovered at harvest",
            "Post-harvest losses from rough handling",
        ],
        scientific_notes="Cabbage maturity is assessed by head firmness — a mature head resists gentle thumb pressure. "
                         "Heads are non-climacteric and do not continue to develop significantly after harvest, "
                         "unlike tomato or banana. Days to maturity vary by variety: early varieties mature in "
                         "85-95 days from transplant, main-season varieties 100-120 days. "
                         "Prolonged cold (vernalisation) followed by warm conditions can trigger bolting before "
                         "head formation — an issue at high elevations or in unusually cold seasons. "
                         "Staggered planting at 10-14 day intervals allows spread of harvest over several weeks, "
                         "reducing market glut and labour peaks.",
    ),
]

_fertilizer = FertilizerSchedule(
    basal={
        "product": "Compound 2:3:2 (28) or equivalent NPK compound",
        "rate": "800 kg/ha",
        "timing": "At transplanting, banded into planting furrow or broadcast and incorporated 2 weeks before transplanting",
        "nutrients_supplied": {"N": "~56 kg N", "P": "~84 kg P2O5", "K": "~56 kg K2O"},
        "scientific_basis": "Compound 2:3:2 (ratio) at 800 kg/ha provides a balanced NPK base for the season. "
                            "The higher phosphorus ratio supports root establishment, which is critical in the "
                            "transplant establishment phase. Cabbage requires 200-250 kg N, 80-120 kg P2O5, "
                            "and 200-300 kg K2O per hectare for a 40-60 t/ha head yield. "
                            "Basal fertiliser should not contact transplant roots directly — band 5 cm below "
                            "and beside the planting hole to avoid root burn.",
    },
    top_dress_1={
        "product": "Limestone Ammonium Nitrate (LAN 28% N)",
        "rate": "200 kg/ha",
        "timing": "3 weeks after transplanting (WAT) — when transplant is established and growing vigorously",
        "application": "Side-dress 7-10 cm from plant stem; irrigate in",
        "scientific_basis": "First N top-dressing drives rapid vegetative leaf area development during the rosette stage. "
                            "LAN is preferred over straight ammonium nitrate or urea because it contains calcium carbonate "
                            "(30%) which helps maintain soil pH, and the calcium fraction is available to the plant. "
                            "200 kg LAN/ha at 3 WAT supplies approximately 56 kg N/ha, sufficient to support "
                            "rapid leaf area expansion to the rosette phase.",
    },
    top_dress_2={
        "product": "Limestone Ammonium Nitrate (LAN 28% N)",
        "rate": "200 kg/ha",
        "timing": "6 weeks after transplanting (WAT) — at onset of head formation (cupping stage)",
        "application": "Side-dress 10 cm from stem; do not place against stem of heading plants; water in",
        "scientific_basis": "Second N top-dressing at head formation sustains the nitrogen supply for head filling. "
                            "At this stage the plant transitions from leaf area expansion to head biomass accumulation. "
                            "Nitrogen supports chlorophyll and protein synthesis in the expanding head leaves. "
                            "Do NOT apply additional N after head formation is well underway (beyond 8 WAT) as it "
                            "delays maturity, softens head texture, and increases susceptibility to black rot and tip burn.",
    },
    foliar={
        "product": "Calcium chloride (CaCl2) 0.5% solution",
        "rate": "0.5 kg CaCl2 per 100 L water, applied to wet the inner head leaves",
        "timing": "From head cupping stage (approx. 8 WAT) — apply weekly for 3-4 applications",
        "scientific_basis": "Tip burn in cabbage is caused by calcium deficiency in rapidly growing inner head leaves "
                            "that have low transpiration and therefore receive inadequate Ca via the xylem stream. "
                            "Unlike older leaves, inner head leaves cannot draw Ca by transpiration. "
                            "Foliar CaCl2 applied directly into the head supplements Ca supply to these tissues. "
                            "Boron at 0.2 kg/ha (as Solubor) can be co-applied to support Ca uptake and cell wall integrity.",
    },
    liming={
        "product": "Agricultural lime (calcium carbonate) or dolomitic lime",
        "rate": "2-4 t/ha if soil pH < 5.5; 1-2 t/ha if pH 5.5-6.0",
        "timing": "3-6 months before planting; incorporated by ploughing",
        "scientific_basis": "Target soil pH 6.0-7.0 for cabbage. Below pH 5.5, phosphorus becomes unavailable "
                            "and aluminium and manganese toxicity develop. Critically, pH below 6.5 also favours "
                            "Plasmodiophora brassicae (clubroot) — liming to pH 7.0 or above effectively suppresses "
                            "clubroot by reducing spore viability and hyphal penetration. Dolomitic lime is preferred "
                            "where magnesium deficiency is suspected as brassicas have moderate Mg demand.",
    },
    notes="Total nutrient programme: Basal Compound 2:3:2 at 800 kg/ha + LAN 200 kg/ha at 3 WAT + "
          "LAN 200 kg/ha at 6 WAT + foliar CaCl2 weekly from cupping. "
          "For high-yielding crops (>60 t/ha), consider additional K as muriate of potash (KCl) "
          "at 100 kg/ha at 6 WAT alongside the LAN. "
          "Sulphur is important for all brassicas — if using non-S-containing fertilisers, "
          "apply gypsum (CaSO4) at 200-300 kg/ha as basal to supply sulphur for glucosinolate and protein synthesis.",
)

_planting_windows: List[PlantingWindow] = [
    PlantingWindow(
        region="Natural Region I (Eastern Highlands, >1000 m)",
        optimal_start="February 1", optimal_end="April 30",
        acceptable_start="January 1", acceptable_end="June 30",
        notes="Cool temperatures in this region favour cabbage year-round. Main season is autumn-winter "
              "(Feb-Apr sowing in nursery, transplant Mar-May). Frost risk limits production in June-July "
              "at highest elevations. Downy mildew pressure is higher due to humidity. "
              "Avoid transplanting in October-November — too warm for good head formation.",
    ),
    PlantingWindow(
        region="Natural Region II (Highveld — Mashonaland, Harare peri-urban belt)",
        optimal_start="February 15", optimal_end="May 31",
        acceptable_start="January 15", acceptable_end="July 31",
        notes="Primary cabbage production zone for Harare peri-urban markets. Sow in nursery Feb-May, "
              "transplant to field Mar-Jun. Harvest May-Aug (winter/cool season). Irrigation essential. "
              "Frost can occur June-July in some areas — plant timing to avoid heads maturing during frost risk. "
              "Summer (Oct-Dec) production is possible with irrigation but DBM pressure is very high and "
              "head quality is poor in high temperatures. Star 3311 is the predominant variety in this zone.",
    ),
    PlantingWindow(
        region="Natural Region III (Semi-intensive, intermediate altitude)",
        optimal_start="March 1", optimal_end="June 30",
        acceptable_start="February 1", acceptable_end="July 31",
        notes="Winter season production with irrigation. Avoid wet summer season for cabbage. "
              "DBM pressure during warm months requires intensive IPM programme. "
              "Head quality is best at the cooler winter months.",
    ),
    PlantingWindow(
        region="Natural Region IV (Semi-extensive, Matabeleland)",
        optimal_start="March 15", optimal_end="May 31",
        acceptable_start="March 1", acceptable_end="June 30",
        notes="Irrigated winter production. Hot summers are unsuitable for cabbage head formation. "
              "Drip irrigation preferred — conserves water in this drier agro-ecological zone. "
              "Earlier planting (March) targets the best cool season window before June-July minimum temperatures.",
    ),
    PlantingWindow(
        region="Natural Region V (Lowveld — Limpopo Basin, Triangle, Chiredzi)",
        optimal_start="April 1", optimal_end="May 31",
        acceptable_start="March 15", acceptable_end="June 15",
        notes="Short window of suitable temperatures in the cool season. "
              "Summer is too hot for acceptable head formation. Frost risk is minimal but temperatures "
              "can rise quickly in September, terminating the season. "
              "Irrigation from rivers or dams is essential. Vigilance for cutworms after first rains.",
    ),
]

PROFILE = CropProfile(
    crop_name="Cabbage",
    scientific_name="Brassica oleracea var. capitata L.",
    family="Brassicaceae",
    optimal_ph=(6.0, 7.0),
    critical_ph_low=5.0,
    optimal_soil_types=[
        "Deep, well-drained sandy loams",
        "Red loam soils (fersiallitic) — common on Highveld",
        "Fertile alluvial soils near rivers",
        "Clay loams with good structure and drainage",
    ],
    avoid_soil_types=[
        "Waterlogged or poorly drained soils (promotes clubroot and Pythium)",
        "Very sandy, infertile soils with low water retention",
        "Fields with history of clubroot (Plasmodiophora) in any brassica crop",
        "Soils with pH < 5.0 — severe P unavailability and Al toxicity",
    ],
    optimal_temp=(12.0, 20.0),
    critical_temp_low=2.0,
    critical_temp_high=28.0,
    base_temp_gdd=5.0,
    total_water_mm=400.0,
    growth_stages=_growth_stages,
    fertilizer_schedule=_fertilizer,
    diseases=_diseases,
    pests=_pests,
    planting_windows=_planting_windows,
    harvest_moisture="Harvest at full head firmness. Press head gently with thumb — a mature head gives "
                     "little or no yield. Days to maturity from transplant: early varieties 85-95 days, "
                     "main season varieties 100-120 days. Harvest in the morning for best shelf life.",
    storage_conditions="Store at 0-4°C, 90-95% RH for up to 3 months (commercial cold storage). "
                       "At ambient Zimbabwe temperatures (15-25°C in winter), shelf life is 7-14 days "
                       "if heads are kept cool and dry. "
                       "Remove damaged or diseased outer leaves before storage. "
                       "Do not store cabbage with ethylene-producing fruit (bananas, apples) — accelerates yellowing.",
    post_harvest_notes="Handle carefully — cabbage heads bruise and crack easily if dropped. "
                       "Grade by head weight (small <1 kg, medium 1-2 kg, large >2 kg) for market. "
                       "Zimbabwe fresh markets (Mbare musika, peri-urban markets) prefer large, "
                       "firm, green heads. Remove outer leaves damaged by insects or disease before packing. "
                       "Star 3311 is the most widely grown and recognised variety in Zimbabwe peri-urban areas — "
                       "produces dense, round to slightly oval heads of 1.5-3 kg. "
                       "Cabbage is a critical peri-urban vegetable supplying Harare, Bulawayo, and "
                       "secondary cities year-round, predominantly from smallholder and A1 scheme farmers.",
    natural_region_suitability={
        "I": "Excellent — cool temperatures favour head formation; year-round potential; humidity increases disease pressure",
        "IIa": "Excellent — primary production zone for Harare peri-urban belt; winter season irrigated production",
        "IIb": "Good — winter season with irrigation; adequate temperature range for heading",
        "III": "Good — winter/cool season with irrigation; DBM pressure higher in warm months",
        "IV": "Moderate — narrow cool season window; irrigation essential; water availability limits production",
        "V": "Marginal — very short cool season window; high heat limits production; only Apr-Jun suitable",
    },
)

ALIASES = ["cabbages", "kabichi"]
