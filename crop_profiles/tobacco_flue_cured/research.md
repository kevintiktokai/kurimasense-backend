# Flue-Cured (Virginia) Tobacco — Zimbabwe Agronomic Research (Phase 1)

**Crop:** *Nicotiana tabacum* L. (flue-cured / Virginia type)
**Geography:** Zimbabwe (Natural Regions I–V)
**Purpose:** Ground a clinically accurate KurimaSense yield-prediction model and
KurimaScore translation layer for flue-cured tobacco.
**Status:** Phase 1 — RESEARCH ONLY. No application code, schema, or service
modules were modified.
**Companion files:** `sources.md`, `variety_database.json`,
`natural_region_baselines.json`.

> Citation convention: every quantitative claim carries an inline short key
> (e.g. `[Masvongo 2013]`) resolved in `sources.md`. Claims without a defensible
> primary source are marked **"estimated; primary source needed"** and repeated
> in Section 9.

---

## 0. Executive summary

Zimbabwe is Africa's largest flue-cured tobacco producer and the crop is the
country's top agricultural export earner. Production has shifted decisively from
a few hundred large-scale commercial estates to a smallholder/contract base —
roughly **95% of the crop is now grown under contract** [EquityAxis SideMkt
2023]. That structural fact is the commercial spine of KurimaSense's tobacco
proposition: contractors finance inputs, carry the default risk, and lose an
estimated **~US$57 million in a single season (2021) to side-marketing**
[Newsday US$57m 2022].

Agronomically, the crop is unusually quality-sensitive: yield and grade are
governed less by maximising biomass than by *precisely matched* nitrogen,
potassium as the quality element, disciplined topping/suckering, staged reaping,
and tightly controlled curing. Realistic yields run **~1,900–2,050 kg/ha for
smallholders** [Masvongo 2013; Newsday], **~2,500 kg/ha for well-run commercial
crops** [FAO Tobacco Zimbabwe], against a modern-hybrid genetic ceiling of
**~4,500 kg/ha** (K RK66/K RK76) [Newsday Kutsaga 2023].

Remote sensing of tobacco specifically is a thin but real literature —
dominated by Zimbabwean work (Svotwa and colleagues) showing NDVI tracks tobacco
biomass and nitrogen status, but with **no published season-integral-NDVI →
final-cured-yield calibration for Zimbabwe** that we could find. That gap is a
competitive opportunity, not a blocker.

This document audits what KurimaSense already encodes, then builds the external
evidence base for varieties, phenology, inputs, regional yield baselines, stress
interpretation, side-marketing intelligence, and satellite indices.

---

## 1. Existing Knowledge Audit (what the codebase already contains)

Before researching externally, the relevant KurimaSense modules were read
end-to-end. Tobacco is **already a first-class crop** in the system; the Phase 1
job is to deepen and reconcile, not to introduce from scratch.

### 1.1 What exists

- **`crop_constants.py`** — tobacco is registered with: base temp **10 °C** for
  GDD, default yield **2.0 t/ha**, season water requirement **450 mm**, and it is
  in `TRANSPLANTED_CROPS` (uses transplant date, not sowing date)
  [KurimaSense crop_constants.py]. These are sensible and broadly consistent with
  the external literature (see §4c, §5).
- **`crop_profiles/tobacco.py`** (duplicated as `TOBACCO_PROFILE` inside
  `crop_knowledge.py`, line ~1177) — a full `CropProfile`: pH 5.5–6.0 (critical
  low 5.0), light granite sands preferred, optimal temp 20–30 °C, four growth
  stages (Transplant/Establishment 0–21 d, Rapid Growth 21–56 d, Topping
  56–70 d, Ripening 70–100 d), a fertiliser schedule, one disease (Frog-eye /
  *Cercospora*), planting windows, grading notes, and NR suitability
  [KurimaSense tobacco.py].
- **`proactive_intelligence.py`** — `_calculate_tobacco_stage()` implements a
  parallel five-stage phenology (Establishment <21 d, Rapid Growth <56 d, Topping
  <70 d, Ripening to maturity−14 d, Harvest), and `get_variety_info()` reads
  varieties from a Postgres `crop_varieties` table.
- **`yield_model.py`** — the factor-based engine this research feeds:
  `projected = base_yield_mid × region × ndvi × water × input × variety`. It
  hard-codes tobacco `NATURAL_REGION_MULTIPLIERS` (I 1.15, II 1.0, IIa 1.0,
  IIb 0.95, III 0.8, IV 0.4, V 0.2) and a fallback tobacco yield band of
  **1.5–3.0 t/ha** [KurimaSense yield_model.py].
- **`db/migrations/001_create_crop_varieties.sql`** — the variety table schema
  (`crop_name`, `variety_name`, `breeder`, `days_to_maturity`,
  `yield_potential_low/high`, `characteristics` JSONB). The JSONB already
  anticipates tobacco with a `style` key ("Lemon", "Orange/Mahogany").
- **`knowledge_data/tobacco_manual_kutsaga.json`** — curated extract of the
  **Kutsaga 2023 variety brochure** (K RK1, K30R, K35, KRK29) with ripening rate,
  yield class, quality style, and disease-resistance codes
  [Kutsaga Brochure 2023].
- **`agronomic_engine.py`** and **`crop_knowledge.py`** — generic engines
  (planting window, fertiliser, IPM, irrigation, harvest readiness) that consume
  the profile; no tobacco-specific logic beyond the shared `TOBACCO_PROFILE`.

### 1.2 Contradictions and gaps flagged

1. **Base-temp inconsistency.** `crop_constants.py` uses tobacco base temp
   **10 °C**, while `tobacco.py`'s `CropProfile.base_temp_gdd` is also 10 °C —
   consistent. But the profile's `critical_temp_low` is 13 °C; literature
   commonly cites a tobacco base temperature nearer **13 °C** for thermal-time
   work. **Not an error to fix in Phase 1**, but Phase 2 should decide whether GDD
   uses 10 or 13 °C; flagged. **(estimated; expert confirmation needed)**
2. **Variety code drift.** The codebase mixes naming forms — `KRK26R`, `KRK75`,
   `T78`, `KRK26R`/`K RK26R`. The Kutsaga brochure uses `K RK1`, `K30R`, `K35`,
   `KRK29`. KRK75 appears only in the internal profile (as a frog-eye-resistant
   mahogany line) and may overlap with the modern `K RK7x` hybrid series. **The
   variety database (`variety_database.json`) normalises these and flags KRK75
   for reconciliation.**
3. **Duplication.** `TOBACCO_PROFILE` is defined identically in both
   `tobacco.py` and `crop_knowledge.py`. Not a research problem, but Phase 3
   should ensure a single source of truth to avoid divergence.
4. **Frog-eye is the only encoded disease.** The internal profile has no
   bacterial (Granville) wilt, angular leaf spot, black shank, or blue mould —
   all materially important in Zimbabwe (see §6). The variety database captures
   resistances for these; Phase 3 should add the disease profiles.
5. **Region multiplier vs. management.** `yield_model.py` collapses *region* and
   implicitly *management* into one multiplier. Our `natural_region_baselines.json`
   separates region from a poor/average/best-practice management axis and
   records the implied ratio back to the NR II anchor so the two can be
   reconciled in Phase 2 (the implied NR III ratio ~0.82 is close to the model's
   0.8).
6. **Fertiliser product mismatch.** The internal profile specifies **Compound S
   (7:21:7+6S)** basal; the Zimbabwe market and supplier guides predominantly cite
   **Compound C (6:15:12+6S+0.1B)** for tobacco basal (see §4b). Both are real
   tobacco compounds; Phase 2 should treat them as alternatives, not
   contradictions.

**Bottom line:** the existing tobacco profile is a solid skeleton. The high-value
additions from this research are (a) a real multi-variety database, (b) a
defensible per-region × management yield matrix, (c) the full disease/stress
catalogue, and (d) the side-marketing and remote-sensing intelligence that turn
the model into an institutional product.

---

## 2. Varieties (commercial flue-cured varieties in Zimbabwe)

Full structured data is in `variety_database.json` (12 entries; 10 of them
current Zimbabwe commercial/recent releases, plus KRK75 flagged for
reconciliation and K326 included as an international benchmark only). Variety
breeding in Zimbabwe is dominated by the **Tobacco Research Board (Kutsaga)**,
whose programme has lifted yield potential from roughly **600 kg/ha in the 1950s
to ~4,500 kg/ha** with the modern K RK66/K RK76 hybrids [Newsday Kutsaga 2023;
Kutsaga Breeding].

### 2.1 The Kutsaga naming system

- **K / Kutsaga** prefix denotes a Kutsaga release.
- **RK** lines (e.g. K RK1, KRK26R, KRK29, K RK66) are the main commercial
  series; an **R** suffix (e.g. KRK26R) historically denotes a root-knot-nematode
  resistant selection.
- **T** lines (e.g. T75) are newer named releases, several bred for drought
  tolerance.
- Quality/style is expressed as **lemon** (fast-ripening, bright) through
  **orange** to **mahogany** (slower-ripening, heavier-bodied).

### 2.2 Variety highlights (see JSON for full fields and sources)

| Code | Class | Ripening | Yield potential (opt/typ kg/ha) | Style | Notable resistance | Best NR |
|------|-------|----------|----------------------------------|-------|--------------------|---------|
| K RK1 | early | med-fast | 3200 / 2200 | deep orange | WM, ALT, RK; drought-tol | II–IV |
| K30R | late | slow | 3000 / 2100 | lemon–orange | WF-0, ALT, **GW**, RK, BS, TMV | II–III |
| K35 | late | slow | 3600 / 2400 | orange–lemon | WM, WF-0/1, ANG-1, ALT, BS | I–II |
| KRK29 | late | very slow | 3800 / 2500 | deep lemon–orange | RK | II–III |
| KRK26R | early | rapid (lemon) | 3300 / 2200 | lemon | RK | II–IV |
| KRK28 | medium | medium | 4000 / 2700 | — | RK, ALT | II–III |
| K RK66 (hybrid) | medium | medium | **4500** / 3000 | — | RK, ALT, WF-0 | I–III |
| K RK76 (hybrid) | medium | medium | **4500** / 3000 | — | RK, ALT, WF-0 | I–III |
| T75 | early | fast | 3200 / 2200 | — | RK; **drought tolerant** | III–V |
| KE1 | early | fast | 3000 / 2000 | — | WM (white-mould pioneer) | II–III |

Key agronomic reading of the set:

- **Fast/early lines (KRK26R, K RK1, T75, KE1)** are the dryland and
  late-planting insurance: rapid ripening lets the crop *escape* terminal drought
  and reach the early auction floors (price advantage). The codebase already
  encodes the KRK26R↔KRK75 style contrast (KRK26R cures fast/lemon but is
  frog-eye susceptible; KRK75 slow/mahogany but frog-eye resistant)
  [KurimaSense tobacco.py].
- **Slow/late, high-yield lines (KRK29, K35, K30R)** maximise leaf number and
  body under reliable rainfall/irrigation (NR I–II) but expose the crop to
  late-season risk in drier regions.
- **GW (Granville/bacterial wilt) resistance is rare and valuable** — K30R is the
  standout in the curated set, important for the wilt hotspots in §6.
- **T75** is the strategic climate-adaptation variety: documented as
  highest-yielding with least drought-stress symptoms and high cross-season
  stability [Magama 2016].

### 2.3 Research note on varieties

The four brochure varieties (K RK1, K30R, K35, KRK29) are fully sourced. The
remaining entries (KRK26R, KRK28, K RK66/76, T75, KE1) are confirmed as real
Kutsaga lines but several of their *numeric* fields (days-to-maturity from
transplant, plant population, topping-leaf count) are **interpolated from
Zimbabwe flue-cured norms** — flagged per-entry in the JSON and in §9. We meet
the "≥8 commercially relevant varieties" bar with margin (10 Zimbabwe lines).

---

## 3. Phenological stages (transplant → curing)

Flue-cured tobacco in Zimbabwe is **transplanted** (8-week float/seedbed
seedlings) after effective rains, typically September–October for the main crop,
with irrigated crops starting earlier [KurimaSense tobacco.py]. The codebase's
own staging (§1.1) aligns closely with standard agronomy nomenclature below.
Total transplant-to-final-reaping span is ~**90–140 days** depending on variety
class, then 1–2 weeks of curing per barn-load running concurrently with reaping.

### 3.1 Stage narrative

1. **Establishment (transplant → anchorage, ~0–21 days).** Root re-establishment
   dominates. Phosphorus is critical; nitrogen must be modest (excess N here
   drives rank growth and delays ripening) [KurimaSense tobacco.py]. The plant is
   small with low ground cover, so canopy reflectance is dominated by soil.
   Highly sensitive to transplant shock, cutworm, damping-off, and moisture
   extremes.

2. **Vegetative / rapid growth (anchorage → button, ~21–56 days).** Exponential
   leaf-area expansion and rapid N and K uptake. This is the single most
   information-rich window for satellite monitoring because canopy closes and
   greenness scales with biomass and nitrogen. Stress here (N deficiency, water
   deficit, aphid-vectored virus) directly reduces leaf number and size.

3. **Reproductive (button → topping, ~56–70 days).** Flower bud ("button")
   appears; left unchecked the plant diverts photosynthate to seed. Management
   pivots to **topping** (removing the flower head) to redirect assimilate into
   the leaves. Canopy is at or near maximum greenness/biomass.

4. **Topping & ripening (~56–100 days).** After topping, leaves thicken and
   mature; chlorophyll degrades and carotenoids accumulate (the visible
   yellowing/ripening). Sucker control is critical (see §4e). NDVI/greenness now
   *should* plateau and then decline from the bottom up — a healthy, expected
   senescence signal, not stress.

5. **Reaping (multiple primings, bottom → top).** Leaves are harvested in
   successive primings as they ripen — typically **5–7 reapings**, two (max three)
   ripe leaves per plant per reaping, from the lugs/primings up to the tips
   [Curing/Reaping snippet]. Canopy progressively thins; SAR backscatter and a
   declining NDVI integral track defoliation.

6. **Curing (post-field).** Reaped green leaf is flue-cured in barns over
   ~1–2 weeks: yellowing → leaf (lamina) drying → midrib drying. Handled
   separately from the field model but central to grade and to the green→cured
   mass conversion (§4f).

### 3.2 Stage × satellite-index relevance

| Stage | Days (transplant) | Key process | Most informative index | What it should signal | Primary risks |
|-------|-------------------|-------------|--------------------------|------------------------|----------------|
| Establishment | 0–21 | Rooting, anchorage | **SAVI** (soil-adjusted; low cover) | Low/rising vegetation over bare soil; SAVI > NDVI here | Transplant shock, cutworm, damping-off, dry/waterlogged soil |
| Rapid growth | 21–56 | Leaf-area & N/K uptake | **NDVI, NDRE, EVI** | Steep greenness climb; NDRE tracks N status; EVI avoids saturation | N deficiency, water stress, aphid/virus, weeds |
| Reproductive (to topping) | 56–70 | Button → topping | **EVI, NDRE** (NDVI saturates) | Greenness plateau at canopy max | Late topping, boron deficiency, hail |
| Topping & ripening | 70–100 | Leaf thickening, ripening | **NDMI, NDRE** | Controlled decline; NDMI tracks leaf moisture/ripening | Over-ripening, sucker breakthrough, drought |
| Reaping | 90–140 | Sequential defoliation | **SAR backscatter, NDVI integral** | Progressive canopy thinning bottom→top | Over-ripe loss, weather damage, barn capacity |
| Curing | post-field | Yellowing→drying | (non-field; thermal/smoke only) | n/a optical field signal | Barn rot, scorch, fuel shortage |

NDVI saturates at high leaf-area index (LAI 3–6), so **EVI and NDRE are
preferred once the canopy closes**; NDRE (red-edge) is the most physiologically
direct nitrogen proxy, which matters enormously for a crop where *excess* N is as
damaging as deficiency (§6) [general RS literature; Svotwa 2013b].

---

## 4. Input requirements (commercial regime, by region where it differs)

> Supplier guides (Agricura, Farmitagro, Superfert) are used **only for product
> specifications and rates**, never for yield claims, per the citation standard.

### 4a. Land preparation

- **Subsoiling** to break plough pans, commonly to **~45–60 cm** to allow the
  deep tobacco taproot to exploit subsoil moisture — critical for dryland crops
  in NR III–IV. **(estimated; primary source needed for exact depth)**
- **Ridging:** crop grown on ridges/rows at **~1.2 m between rows** with **~0.45 m
  (lemon/fast) up to ~0.56 m in-row** spacing [KurimaSense tobacco.py;
  Svotwa trials 120 × 56 cm], giving plant populations of roughly
  **~15,000–18,500 plants/ha** (1.2 × 0.45) down to **~14,800/ha** (1.2 × 0.56).
- **Pre-plant:** clean fallow / rotation away from solanaceous crops; avoid
  high-N residue lands (ex-legume first-year lands raise leaf N and harm grade)
  [KurimaSense tobacco.py].

### 4b. Nutrition

Tobacco nutrition is a *quality* exercise: the target is **~80–100 kg N/ha total
— and not more** for quality flue-cured leaf [KurimaSense tobacco.py], with
**potassium as the quality element** governing leaf body, burn and cured colour.

- **Basal (at/just before transplant):**
  - Market-standard: **Compound C (6:15:12 +6S +0.1B)** at **~700–800 kg/ha**
    [Superfert Tobacco; Esaja Compound C listing]. At 800 kg/ha this supplies
    ~48 kg N, ~120 kg P₂O₅, ~96 kg K₂O, ~48 kg S, ~0.8 kg B.
  - Internal-profile alternative: **Compound S (7:21:7 +6S)** at 400–500 kg/ha
    (higher P, lower K) [KurimaSense tobacco.py]. Treat C and S as
    region/soil-dependent alternatives, not a contradiction (§1.2).
- **Top-dressing:** **Ammonium Nitrate (AN, 34.5% N)** at **~150 kg/ha**, applied
  as a split, with the first AN side-dressing at **~3 weeks after transplant at
  ~25 kg N/ha** [Agricura 1ha Tobacco; SQM Nutrition]. Kutsaga advocates AN
  directly after planting and **does not advocate potassium-nitrate topdressing**
  [SQM Nutrition]. Total season N stays within the ~80–100 kg/ha ceiling.
- **Potassium:** supplied largely in the basal compound; the internal profile
  adds **Muriate of Potash only with caution** because tobacco is
  **chloride-sensitive** — `K₂SO₄` (sulphate of potash) is preferred near
  transplanting [KurimaSense tobacco.py].
- **Calcium / magnesium:** use **calcitic lime, not dolomitic** — excess Mg
  darkens cured leaf [KurimaSense tobacco.py].
- **Boron:** specifically important (built into Compound C at 0.1% B); boron
  deficiency causes growing-point death and distorted top leaves (§6).
- **pH & lime:** target **pH 5.5–6.0** (critical low 5.0); **calcitic lime
  ~1–2 t/ha** on soil test, applied ~6 months before transplant
  [KurimaSense tobacco.py]. Acidity below ~5.0 risks Al toxicity and P lock-up.
- **Foliar:** no universal standard foliar; boron/micronutrient correction foliars
  used reactively. **(estimated; standard foliar program not established)**

*Regional nuance:* drier NR III–IV crops lean on slightly lower N (to avoid rank
growth under moisture limitation and to protect grade) and rely more on basal P
for early vigour; high-rainfall NR I–II can carry the upper N range with greater
leaching risk (split AN more finely).

### 4c. Water management

- Season requirement **~450 mm** [KurimaSense crop_constants.py], consistent with
  flue-cured norms. Management mode by region: **NR I–II largely dryland with
  supplementary irrigation in dry spells; NR III supplementary irrigation
  effectively required; NR IV–V full irrigation mandatory** (see §5).
- **Critical water windows:** the **rapid-growth/leaf-expansion** phase
  (~3–8 weeks) is most yield-sensitive to deficit; moderate stress *after*
  topping can actually aid ripening, but severe terminal drought caps leaf
  filling.
- Irrigation timing/depth: schedule to replace ET (Kc rises ~0.4 establishment →
  ~0.8–0.85 rapid/topping → ~0.5 ripening, per the internal stage Kc values)
  [KurimaSense tobacco.py]; deficit at rapid growth is the costliest error.

### 4d. Pest & disease management

- **Spray program:** a typical commercial crop runs a scheduled program from
  seedbed through to late field stage; exact counts vary by season and pressure.
  **(estimated number of applications; primary spray-calendar source needed.)**
- **Key pests:** cutworm (establishment), aphids (virus vectors — rapid growth),
  budworm, tobacco leaf miner, tobacco hornworm. The internal stage model already
  schedules cutworm scouting at establishment and aphid/budworm scouting in rapid
  growth [proactive_intelligence.py].
- **Key diseases:** angular leaf spot (bacterial), frog-eye/*Cercospora* (the one
  encoded disease), Alternaria/brown spot, blue mould/*Peronospora* (downy
  mildew), **Granville/bacterial wilt** (*Ralstonia solanacearum* race 1 biovar 1)
  and **black shank** (*Phytophthora nicotianae*); an emerging **black
  shank–Fusarium wilt complex** is flagged as a new threat [Granville Wilt
  Zimbabwe; Black Shank-Fusarium complex]. Management leans heavily on
  **resistant cultivars** plus rotation and sanitation.
- **Weed control:** tobacco is very sensitive to early weed competition; the
  internal model emphasises weed control in rapid growth
  [proactive_intelligence.py].

### 4e. Husbandry (topping, suckering, reaping)

- **Topping:** top when **~50% of plants reach button/early flower**; **each day
  of delayed topping costs ~50 kg/ha** of leaf yield [KurimaSense tobacco.py].
  Topping height (leaves left) ranges roughly **16–24 leaves** depending on
  variety and target style (fewer leaves = heavier, riper leaf).
- **Sucker control:** after topping, axillary buds (suckers) must be suppressed
  within ~7 days — chemically (**maleic hydrazide**, fluprimidol/Off-Shoot-T
  contact/local-systemics) and/or manually [KurimaSense tobacco.py]. **Sucker
  breakthrough** is a classic failure mode that diverts assimilate and slashes
  grade (§6).
- **Reaping:** harvest ripe leaves **bottom-up in 5–7 primings**, ~2 (max 3) ripe
  leaves per plant per reaping [Curing/Reaping snippet; KurimaSense tobacco.py].

### 4f. Curing

- **Methods in Zimbabwe:** conventional flue barns; the **rocket barn**
  (Malawi-origin; ~**50% wood saving** vs conventional) widely promoted for
  smallholders; the **Kutsaga Counter-Current** barn (**3.5 kg wood/kg cured** vs
  ~4.25 rocket / ~5.32 conventional); and emerging electric/biomass options where
  power allows [Rocket/Counter-Current Barn]. Venturi-style barns also feature in
  the market.
- **Curing schedule:** **yellowing (~35–40 °C)** → colour-fixing/leaf (lamina)
  drying (~rising to ~55 °C) → **midrib drying / killing-out (~55–60 °C+)**, over
  roughly 1–2 weeks per barn-load; curing temperature control is the **#1
  determinant of leaf grade** [KurimaSense tobacco.py].
- **Green-to-cured ratio:** field models predicting cured leaf must apply the
  green→cured mass loss. Industry rule-of-thumb loss is **~8–12%**... however the
  *conventional* agronomic figure is closer to ~85–90% water loss by mass (i.e.
  cured ≈ 12–16% of green); the **8–12%** in the prompt is interpreted as the
  *additional* curing/handling shrink applied to graded leaf rather than the raw
  green→dry water loss. **FLAGGED — the green→cured conversion basis must be
  pinned down with a primary source before Phase 2** (it directly scales every
  yield number). **(estimated; primary source needed.)**

---

## 5. Yield baselines by Natural Region

Full structured data in `natural_region_baselines.json`. Methodology and
uncertainty are stated explicitly because this section most directly drives the
model.

### 5.1 National anchor points (well-sourced)

- **Smallholder/communal average ~1,900–2,050 kg/ha:** Mount Darwin (NR III)
  smallholders averaged **2,052 kg/ha** (2010/11) [Masvongo 2013]; Mazowe's
  10,000+ growers averaged **~1,915 kg/ha** (2017) [Newsday].
- **Large-scale commercial ~2,500 kg/ha** [FAO Tobacco Zimbabwe].
- **Modern-hybrid best-practice ceiling ~4,500 kg/ha** (K RK66/K RK76, irrigated,
  fully resourced) [Newsday Kutsaga 2023].
- **Historical volatility:** national productivity fell from ~2,200 kg/ha (1998)
  to ~700 kg/ha (2001) through the land-reform disruption [FAO; trade press],
  illustrating how management/structure — not genetics — dominates realised
  yield.

### 5.2 Per-region × management matrix (anchors + interpolation)

TIMB does not publish a clean per-region × management yield table, so the matrix
below interpolates from the §5.1 anchors along the agro-ecological
rainfall/reliability gradient, cross-checked against the multipliers already in
`yield_model.py`. **Per-region figures carry estimation uncertainty (§9).**

| NR | Suitability | Rainfall (mm/yr) | Poor | Average | Best-practice | Implied ratio vs NR II avg |
|----|-------------|------------------|------|---------|---------------|-----------------------------|
| I | good | 1000–1400+ | 1500 | 2400 | 4000 | 0.96 |
| II | **excellent** | 750–1000 | 1800 | **2500** | **4500** | 1.00 (anchor) |
| III | good | 650–800 | 1400 | 2050 | 3800 | 0.82 |
| IV | marginal | 450–650 | 800 | 1400 | 3000 | 0.56 |
| V | marginal | <450 | 500 | 1000 | 2600 | 0.40 |

Notes:
- **NR II** is the core belt (Mvurwi, Bindura, Marondera, Karoi, Mazowe); its
  "average" 2,500 kg/ha and "best-practice" 4,500 kg/ha are directly anchored.
- **NR III** "average" 2,050 kg/ha is directly anchored to Mount Darwin/Mazowe;
  the implied 0.82 ratio matches the model's 0.8 multiplier closely — a useful
  internal validation.
- **NR I** is climatically capable (best-practice ~4,000 kg/ha) but cooler
  temperatures can slow ripening and land competes with horticulture/plantation
  crops; the model's 1.15 multiplier may be *optimistic* for tobacco specifically
  (cool-season ripening drag) and is flagged for Phase 2 review.
- **NR IV–V** figures lean on the model multipliers (0.4 / 0.2) plus the reality
  that viable crops there are essentially irrigated; the "poor management"
  dryland numbers are low and uncertain. Recent NCV/irrigated initiatives in
  Matabeleland (NR IV) are expanding the footprint [Newsday NCV Matabeleland].

The poor/average/best-practice spread (roughly a **2.5–5× range within a single
region**) is the core agronomic justification for KurimaSense: the dominant
yield driver is management, which is exactly what satellite + input monitoring
can observe.

---

## 6. Stress & anomaly interpretation (KurimaScore building blocks)

Each entry gives the satellite signature, the most-damaging stages, farmer-visible
symptoms, remediation, and an uncorrected yield-impact range. These are the raw
material for the KurimaScore "primary driver / likely cause / recommended action"
output. Impact ranges are **agronomic estimates** unless cited.

1. **Nitrogen deficiency.** *Satellite:* low/declining NDVI & especially **low
   NDRE** during rapid growth; pale, uniform canopy. *Stages:* rapid growth.
   *Visual:* general pale-green/yellow lower leaves, stunted, thin leaves.
   *Action:* bring forward/raise AN topdress within the ~80–100 kg N/ha ceiling;
   check pH (acidity mimics N deficiency). *Impact:* ~10–25%.
2. **Nitrogen excess (over-fertilisation — common in tobacco).** *Satellite:*
   abnormally high, *persistently non-declining* NDVI/NDRE late into ripening
   (canopy "won't ripen"). *Stages:* topping–ripening. *Visual:* thick, dark,
   coarse "rank" leaf; delayed yellowing; poor cure to dull/green grades.
   *Action:* stop N, top/sucker decisively, manage water down to push ripening.
   *Impact:* grade downgrade rather than tonnage loss — can cut *value* 15–30%.
3. **Potassium deficiency.** *Satellite:* subtle — marginal/interveinal decline,
   weak NDVI gain despite adequate N. *Stages:* rapid growth–ripening. *Visual:*
   leaf-margin scorch/necrosis, mottling; cured leaf cures buff/brown not
   lemon/orange [KurimaSense tobacco.py]. *Action:* ensure K in basal; SOP
   (K₂SO₄) side-dress (avoid chloride). *Impact:* mainly grade/quality; 5–20%
   value.
4. **Boron deficiency.** *Satellite:* hard to see; localised top-canopy
   distortion. *Stages:* rapid growth–topping. *Visual:* death of growing point,
   brittle/distorted young top leaves, "top sickness". *Action:* boron foliar;
   ensure B in basal (Compound C carries 0.1% B). *Impact:* 5–15%, can be severe
   locally.
5. **Water stress (drought).** *Satellite:* falling **NDMI** (leaf moisture) then
   NDVI/EVI; wilting signature; SAR roughness change. *Stages:* rapid growth most
   damaging. *Visual:* midday wilting, leaf rolling, premature/forced ripening.
   *Action:* irrigate the rapid-growth window; choose fast/drought-tolerant
   varieties (T75, KRK26R) in marginal regions. *Impact:* 15–50%+ in severe
   terminal drought (cf. NR III/IV baselines, §5).
6. **Waterlogging.** *Satellite:* patchy NDVI collapse in low-lying field zones;
   high soil-moisture SAR. *Stages:* any, worst at establishment. *Visual:*
   yellowing, stunting, root death, black-shank risk spike. *Action:* drainage,
   ridging; avoid heavy clays [KurimaSense tobacco.py]. *Impact:* 10–40% in
   affected zones.
7. **Bacterial / Granville wilt (*Ralstonia solanacearum* race 1 biovar 1).**
   *Satellite:* sudden, patchy NDVI collapse in discrete clumps that expands;
   distinct from uniform deficiency. *Stages:* rapid growth–ripening, worse in hot
   wet soils. *Visual:* one-sided then whole-plant wilting, vascular browning,
   bacterial ooze; persistent in Mvurwi-Concession, Macheke/Headlands/Marondera,
   Burma Valley [Granville Wilt Zimbabwe]. *Action:* resistant varieties (e.g.
   K30R), rotation, sanitation — no effective in-season chemical cure. *Impact:*
   localised total loss; field-level 5–30%.
8. **Black shank (*Phytophthora nicotianae*), incl. emerging Fusarium complex.**
   *Satellite:* patch wilt similar to Granville. *Stages:* establishment–rapid
   growth in wet soils. *Visual:* stem black lesion at soil line, "shank"
   blackening, sudden wilt; emerging black-shank–Fusarium complex flagged as new
   threat [Black Shank-Fusarium complex]. *Action:* resistant varieties (K30R,
   K35), drainage, rotation, metalaxyl-type protection. *Impact:* 5–30% localised.
9. **Angular leaf spot (bacterial).** *Satellite:* diffuse NDVI/grade decline
   under prolonged leaf wetness; hard to isolate spectrally. *Stages:* rapid
   growth–ripening in wet, humid (NR I/high-rainfall) conditions. *Visual:*
   angular, vein-delimited water-soaked lesions. *Action:* resistant varieties
   (K35, K30R), copper sprays, spacing/air-flow. *Impact:* mainly grade; 5–15%.
10. **Blue mould / downy mildew (*Peronospora* spp.).** *Satellite:* rapid
    seedbed/early-field canopy decline in cool, humid spells. *Stages:* seedbed &
    establishment. *Visual:* grey-violet sporulation underside, yellow blotches,
    rapid leaf death. *Action:* seedbed fungicides, ventilation, avoid
    overcrowding. *Impact:* seedbed wipe-out risk; field 5–20%.
11. **Hail damage.** *Satellite:* abrupt, sharply bounded NDVI/EVI drop on a
    single date over an irregular footprint (weather-correlated). *Stages:* any —
    worst near topping/ripening (mature leaf is the product). *Visual:* shredded,
    torn, bruised leaf. *Action:* salvage-reap usable leaf, manage rot, insurance.
    *Impact:* 10–80% depending on severity/timing.
12. **Aphid infestation.** *Satellite:* slow NDVI stagnation/decline plus virus
    symptoms; sooty-mould can depress reflectance. *Stages:* rapid growth (also
    virus vector). *Visual:* colonies on undersides of young leaves, curling,
    honeydew/sooty mould. *Action:* scout (model already schedules this),
    selective aphicides, beneficials. *Impact:* 5–20% (more if virus
    transmitted).
13. **Budworm damage.** *Satellite:* minor NDVI texture/holes; mostly
    sub-pixel. *Stages:* rapid growth–budding. *Visual:* chewed bud and young
    top leaves, frass. *Action:* scout and spot-spray at threshold. *Impact:*
    5–15%.
14. **Late topping.** *Satellite:* greenness keeps climbing past expected
    plateau; ripening delayed (NDVI/NDRE stays high too long). *Stages:* the
    button→topping window. *Visual:* flowering/seed set, lighter top leaves.
    *Action:* top promptly at ~50% button — **each day late ≈ 50 kg/ha lost**
    [KurimaSense tobacco.py]. *Impact:* cumulative; multiple days late =
    several %.
15. **Sucker breakthrough (failed sucker control).** *Satellite:* unexpected
    *re-greening*/NDVI rebound after topping (suckers re-foliating the canopy).
    *Stages:* post-topping ripening. *Visual:* leafy axillary shoots, delayed
    ripening, smaller primary leaves. *Action:* re-apply maleic hydrazide /
    manual desuckering within ~7 days of topping. *Impact:* 5–20% yield + grade.

The diagnostic key for KurimaScore is **shape and locality of the NDVI/NDRE
anomaly**: *uniform* fade ⇒ nutrient/water; *patchy/expanding clumps* ⇒
soil-borne wilt; *sharp single-date irregular* ⇒ hail; *failure-to-decline or
re-greening late* ⇒ excess N / late topping / sucker breakthrough.

---

## 7. Side-marketing context (institutional value proposition)

**What it is.** Side-marketing is when a *contracted* grower — whose inputs were
financed by a contracting company — sells some or all of the crop to a third
party (another contractor, an auction floor under a different grower number, or
across the border) instead of delivering to the financier, defaulting on the
input loan [Newsday Contract Fuelling; allAfrica 2009].

**Scale of loss.** TIMB estimated **~US$57 million lost to side-marketing in
2021 alone**, while cautioning that the true annual figure cannot be precisely
ascertained [Newsday US$57m 2022]. With **~95% of Zimbabwe's crop grown under
contract** [EquityAxis SideMkt 2023], even single-digit-percent leakage is large
in absolute terms; this is a structural, recurring loss, not a one-off.

**Why it happens (grower incentives).** Contract prices/grades can lag spot or
informal-buyer offers; growers carry input debt and immediate cash needs; and
enforcement has historically been weak. Debt pressure among smallholders is
well-documented and sharpens the incentive to divert [Manicaland Debt 2021;
Land Reform Tobacco 2022].

**Enforcement mechanisms tried.**
- **TIMB inspectorate (est. 2021):** a dedicated department to prevent, detect,
  investigate and address illegal activity including side-marketing, with
  inspectors deployed across tobacco regions [EquityAxis SideMkt 2023].
- **Grower-number controls:** suspension of **~550 grower numbers** tied to
  fictitious/duplicate registrations used to launder side-marketed leaf
  [EquityAxis SideMkt 2023].
- **GIS field registration:** marking cardinal points of every tobacco field and
  collating against the crop-assessment report so that self-financed leaf goes to
  auction and contract leaf goes to the rightful contractor [EquityAxis SideMkt
  2023].
- **Contractor-level:** input tagging, delivery quotas vs estimated yield, and
  buying-floor cross-checks.

**TIMB's role.** TIMB is the statutory regulator: it registers contracts and
grower numbers, runs the marketing system (auction + contract floors), operates
the inspectorate, and adjudicates disputes [TIMB; Tobacco Reporter 2022].

**Measurable signals distinguishing genuine shortfall from side-marketing — the
KurimaSense angle.** A legitimate yield shortfall leaves a *consistent biophysical
trail*; side-marketing leaves a *discrepancy*. KurimaSense can quantify the gap:
- **Satellite-estimated production vs delivered volume.** A field whose
  season-long NDVI/EVI integral, canopy area, and reaping signature indicate a
  healthy ~2,500 kg/ha crop, but which delivers far less, is a **red flag** — the
  biomass was grown but not delivered.
- **Stress-corroborated shortfall.** Where low delivery *is* matched by observed
  drought (falling NDMI), disease patches (clumped NDVI collapse), or hail (sharp
  single-date drop), the shortfall is corroborated as genuine.
- **Reaping-signature timing.** Normal sequential bottom-up defoliation vs an
  abrupt whole-field canopy disappearance (possible early bulk removal).
- **Field-boundary integrity.** GIS field marking (already a TIMB initiative)
  combined with per-field area × yield estimates closes the "extra grower number"
  loophole.

This is the **accountability feature** that makes KurimaSense a contractor/
institutional product rather than only a grower tool: it converts "we think
they side-marketed" into "the field grew an estimated X kg with no biophysical
loss event; delivery was Y; the unexplained gap is Z." That is the Phase 3
killer offer, and it is grounded in real, sourced industry dynamics above.

---

## 8. Satellite-index research for tobacco

**Headline: tobacco is under-studied in remote sensing relative to maize/wheat,
and the Zimbabwe-specific work is small but directly relevant — and it
explicitly calls out the gap.** That is a moat for KurimaSense.

**What is validated for tobacco specifically.**
- **NDVI tracks tobacco biomass and nitrogen.** Zimbabwean work (Svotwa et al.)
  found a clear relationship between **NDVI and both biomass and total nitrogen**
  across tobacco varieties, with NDVI rising as N fertilisation rises
  [Svotwa 2013b; Svotwa 2017]. This validates NDVI/NDRE as N-status proxies — the
  exact lever the yield and KurimaScore models need.
- **Seedling/float stage.** For float seedlings, a **Simple Ratio Index (SRI)
  related better (r²≈0.905) than NDVI (r²≈0.819)** to fertiliser response
  [Svotwa 2012] — suggesting SRI/red-edge variants may outperform plain NDVI for
  tobacco at certain stages.
- **Planting-date effect.** Maximum NDVI **and** the NDVI–mass r² both **decline
  with later planting** [Svotwa 2013b] — operationally important for Zimbabwe,
  where late-transplanted crops are both lower-yielding and *harder to monitor*.
- **Operational area+yield estimation** for Zimbabwe tobacco has been
  demonstrated with RS + statistical methods [Tobacco Crop Area RS 2018].

**Crop-specific spectral signatures.**
- **Ripening/curing signature:** the agronomic ripening process (chlorophyll
  loss, carotenoid gain) is a *predictable* spectral senescence — a feature, not
  a stress, and separable from drought by its bottom-up progression and stable
  NDMI early in ripening.
- **Curing-barn smoke detection** (thermal/aerosol signatures of active flue
  curing) is conceptually possible and would be a novel side-marketing/activity
  signal, but we found **no published validation** — flagged as a research idea,
  not a capability. **(research gap.)**

**Temporal NDVI/EVI/NDRE pattern across the cycle.** A characteristic curve: low
(soil-dominated) at establishment → steep rise through rapid growth → plateau
around topping (NDVI saturating, EVI/NDRE more discriminating) → controlled
decline through ripening and reaping. Departures from this curve are the basis
for the §6 diagnostics.

**Spatial resolution / within-field heterogeneity.** Sentinel-2 (10 m optical)
resolves within-field zones for typical Zimbabwe field sizes; smallholder fields
(<1 ha) approach the resolution limit and benefit from red-edge bands and, where
affordable, higher-resolution tasking. **(estimated; tobacco-specific minimum
detectable patch size not established in literature — research gap.)**

**Season-end NDVI integral ↔ final cured yield correlation.** This is the single
most important number for the model, and **we found no published
season-integral-NDVI → final-cured-flue-yield calibration for Zimbabwe**. Analogue
crops give a strong prior (cotton EVI/NDVI at flowering r²≈0.56–0.89; soybean
r²≈0.69–0.70) [general RS literature], and the tobacco NDVI–biomass link is
established [Svotwa], but the specific cured-leaf calibration is **a gap we must
fill with our own data** — and doing so is a defensible competitive advantage.

---

## 9. Research gaps and assumptions

Stated plainly so the model knows where it is strong and where to be humble.

**Where the public literature is thin / snippet-level only.**
- Several primary PDFs (Kutsaga brochure, Superfert/Agricura/Farmitagro guides,
  FAO chapter, Svotwa 2017, RS-area 2018) returned **HTTP 403 to automated
  fetching** and were used at curated-extract or abstract/snippet level. They are
  flagged in `sources.md` and should be re-read in full before Phase 2 sign-off.
- No single public **per-Natural-Region × management yield matrix** from TIMB;
  §5.2 is interpolation from solid national anchors.
- No public **season-integral-NDVI → cured-yield calibration** for Zimbabwe
  tobacco (§8) — the key model parameter is ours to measure.
- No validated **tobacco-specific minimum detectable within-field patch size**
  or **curing-barn smoke detection** literature (§8).
- **Standard spray-calendar** (number/timing of applications) and **subsoiling
  depth** not pinned to a primary source (§4a, §4d).

**Where we used interpolation / estimation (carried as flags, not facts).**
- Variety numeric fields (days-to-maturity from transplant, plant population,
  topping-leaf counts) for KRK26R, KRK28, K RK66/76, T75, KE1 — interpolated from
  class norms (`variety_database.json` per-entry notes).
- Per-region poor/best-practice yields for NR IV–V (low-density, irrigation-
  dependent) — highest uncertainty cells in the matrix.
- **Green→cured conversion basis** (§4f) — the prompt's "8–12% loss" vs the
  conventional ~85% water-loss figure must be reconciled; this scales *every*
  yield output and is the highest-priority quantitative gap.
- Variety-code reconciliation: **KRK75** (internal profile) vs the K RK7x hybrid
  series; **K326** included as international benchmark only, not Zimbabwe trial
  data.
- GDD base temperature: 10 °C (constants) vs ~13 °C critical-low (profile) —
  Phase 2 modelling decision (§1.2).

**Data sources that would strengthen the model.**
- Direct **TIMB/contractor delivery datasets** (per-field volumes + grower
  numbers + GIS boundaries) for the side-marketing feature and for ground-truth
  yield calibration.
- **Kutsaga full variety brochure + trial yield tables** (regional, irrigated vs
  dryland) to replace interpolated variety fields.
- **Multi-season Sentinel-2 + ground-yield pairs** from Zimbabwe tobacco fields
  to build the NDVI-integral → cured-yield calibration ourselves.
- A **curing/grading dataset** to anchor the green→cured conversion and link
  spectral ripening to final grade (grade = value, not just tonnage).

**Expert validation that would be valuable.**
- A **Kutsaga agronomist** reviewing `variety_database.json` (codes, maturities,
  resistances, populations, topping heights) and the §6 stress catalogue.
- A **TIMB/contractor commercial reviewer** validating the side-marketing loss
  framing and the satellite-vs-delivery accountability logic (§7).
- A **remote-sensing scientist** (ideally Svotwa-lineage UZ work) sanity-checking
  the stage×index table (§3.2) and the NDVI-integral calibration plan (§8).

**Overall confidence.** Variety identities, phenology, the input regime, the
national yield anchors, and the side-marketing dynamics are **well-grounded
(medium-high confidence)**. The per-region × management yield cells, the
green→cured conversion, and the NDVI-integral→cured-yield calibration are
**estimates/gaps (low-medium confidence)** and are the explicit Phase 2 work
program. Honesty here is the point: it tells us the model's clinical accuracy is
strongest on *relative* management/stress detection and weakest on *absolute*
cured-kg conversion until we calibrate against real delivery data.

---

*End of Phase 1 research. No application code, constants, schema, or service
modules were modified in producing this document (deliverables are confined to
`crop_profiles/tobacco_flue_cured/`).*
