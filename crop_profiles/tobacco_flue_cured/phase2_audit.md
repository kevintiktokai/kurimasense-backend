# Phase 2 Audit — Flue-Cured Tobacco Phase 1 Research

**Purpose:** Critically evaluate the Phase 1 research deliverables before any
Phase 2 math is written. Each criterion is marked **PASS**,
**GAPS_BUT_PROCEEDABLE**, or **BLOCKER**. Per the Phase 2 protocol, a single
BLOCKER halts Phase 2.

**Files audited (all present — no HALT):**
- `crop_profiles/tobacco_flue_cured/research.md` (43.7 KB, ~5,750 words)
- `crop_profiles/tobacco_flue_cured/sources.md` (11.7 KB)
- `crop_profiles/tobacco_flue_cured/variety_database.json` (12 varieties)
- `crop_profiles/tobacco_flue_cured/natural_region_baselines.json` (5 regions)

**Overall verdict: PROCEED.** No BLOCKER. Originally five PASS, two
GAPS_BUT_PROCEEDABLE.

**Phase 2 amendment (2026-06-05):** both GAPS items were subsequently addressed
(see "Amendments applied" at the foot of this document), upgrading criterion (b)
to **PASS** and substantially de-risking (a). Current standing: **six PASS, one
GAPS_BUT_PROCEEDABLE** (the residual being interpolated variety days-to-maturity /
topping-leaf counts, which require the full Kutsaga trial tables to close).

---

## (a) Variety coverage — **GAPS_BUT_PROCEEDABLE → improved (Phase 2)**

> Phase 2 amendment: plant-population ranges are now grounded in the documented
> Zimbabwe spacing standard (1.2 m × 0.50–0.56 m ⇒ ~14,800–16,700 plants/ha;
> Kutsaga spacing trials, Britannica Orinoco spacing). Residual interpolation is
> now limited to days-to-maturity and topping-leaf counts only.


- **Count:** 12 entries; 10 are current Zimbabwe commercial/recent Kutsaga lines
  (K RK1, K30R, K35, KRK29, KRK26R, KRK28, K RK66, K RK76, T75, KE1), plus KRK75
  (flagged for code reconciliation) and K326 (international benchmark). **≥6
  requirement met with margin.**
- **Required fields present for every entry:** `yield_potential_kg_ha_typical`
  **and** `_optimal`, `days_to_maturity_min/max`, `plant_population_min/max`,
  `disease_resistances`, `recommended_natural_regions`, `topping_height_*`,
  `sources`. **No entry has a null/missing critical field.**
- **Sources cited:** yes, per entry (Kutsaga 2023 brochure for the four
  fully-sourced lines; Newsday/CORESTA/internal profile for the rest).
- **Why not full PASS:** several numeric fields (days-to-maturity from transplant,
  plant population, topping-leaf counts) for KRK26R, KRK28, K RK66/76, T75, KE1
  are **interpolated from class norms**, not read from a primary trial table —
  this is disclosed in each entry's `notes` and in research.md §9. The values are
  agronomically defensible and complete, so design can proceed, but the model
  must (i) treat variety calibration as a *soft* multiplier with a confidence
  penalty for interpolated varieties, and (ii) never present interpolated
  maturities as hard data. **Handled in model_design §1 (variety_calibration) and
  §6 (confidence).**
- K326 is flagged benchmark-only (international norms, not Zimbabwe trial) — the
  model treats it as usable but tags it lower-confidence.

## (b) Natural Region baselines — **GAPS_BUT_PROCEEDABLE → PASS (Phase 2 amended)**

> Phase 2 amendment: `best_practice` values were lowered to operational
> best practice within the 2,500–3,500 sanity band (NR II = 3,300 kg/ha) and the
> former hybrid-ceiling figures moved to a new `genetic_ceiling_kg_ha` field
> (NR II = 4,500), which `tobacco_math.project_yield` now uses as the upper clamp.
> The sanity check now passes.


- **All 5 regions present** (I–V), each with
  `yield_baselines_kg_ha.{poor_management, average_management, best_practice}`,
  rainfall band, suitability, primary constraints, and sources.
- **Sources cited:** yes (Masvongo 2013 anchor for NR III; FAO; Kutsaga; the
  existing `yield_model.py` multipliers as cross-check).
- **Sanity check on NR II `best_practice`:** the audit criterion expects
  **2,500–3,500 kg/ha**; the JSON has **NR II best_practice = 4,500 kg/ha**. This
  is **outside (above) the sanity band** and is flagged. *Root cause:* the Phase 1
  figure deliberately encodes the **modern-hybrid genetic ceiling**
  (K RK66/K RK76, fully irrigated) rather than *operational* best practice.
  - **Resolution (not a blocker):** `model_design.md` distinguishes two anchors:
    `Y_ceiling` (genetic max, ~4,500 in NR II) used only as the hard upper clamp,
    and `Y_base` (operational best-practice anchor, **3,200 kg/ha in NR II**, the
    midpoint of the criterion's 2,500–3,500 band) used as `base_potential` in the
    yield formula. NR II `average_management` = 2,500 kg/ha (well-anchored to
    commercial reality) is the secondary calibration point. This keeps the model
    from systematically over-predicting while preserving the documented ceiling as
    a clamp. **The JSON is left unchanged in Phase 2** (no schema edits allowed);
    the reconciliation lives in the design + code constants.
- **Internal validation retained:** implied NR III/II ratio (~0.82) ≈
  `yield_model.py` multiplier (0.8) — good.

## (c) Phenological stages — **PASS**

- research.md §3 documents **6 stages** (Establishment, Vegetative/Rapid growth,
  Reproductive→topping, Topping & ripening, Reaping, Curing[post-field]) — ≥5 met.
- Each field stage has **days-from-transplant ranges** (0–21, 21–56, 56–70,
  70–100, 90–140).
- **Index sensitivity per stage is explicitly mapped** in the §3.2 table
  (SAVI at establishment; NDVI/NDRE/EVI at rapid growth; EVI/NDRE at
  reproductive; NDMI/NDRE at ripening; SAR + NDVI-integral at reaping). This is
  exactly the mapping the stage-weighted KurimaScore needs — directly portable to
  `INDEX_WEIGHTS` and `STAGE_WEIGHTS`.

## (d) Input requirements — **PASS**

- **Basal:** Compound C (6:15:12+6S+0.1B) ~700–800 kg/ha and Compound S
  (7:21:7+6S) 400–500 kg/ha alternative — documented with rates (§4b).
- **Topdressing:** AN 34.5% ~150 kg/ha split, first ~25 kg N/ha at ~3 weeks; total
  N ceiling ~80–100 kg/ha (§4b).
- **Plant population:** ~14,000–18,500/ha from 1.2 m × 0.45–0.56 m spacing (§4a).
- **Topping:** at ~50% button; each day late ≈ 50 kg/ha loss; 16–24 leaves (§4e).
- **Spray program:** key pests/diseases and weed control documented; **exact
  number/timing of applications flagged as estimated** (§4d, §9). Minor gap — the
  management component uses application *count vs a documented minimum band*, so
  the estimate is sufficient. Does not block.

## (e) Stress interpretation — **PASS**

- research.md §6 documents **15 stresses**, covering **all six required minimums**
  (nitrogen deficiency, water stress/drought, bacterial/Granville wilt, angular
  leaf spot, blue mould, late topping) plus N excess, K/B deficiency,
  waterlogging, black shank, hail, aphids, budworm, sucker breakthrough.
- Each entry has **satellite signature + visual symptoms + remediation + yield
  impact range**. Directly portable to the driver/cause/action decision tree
  (model_design §5).
- The §6 diagnostic key (uniform fade ⇒ nutrient/water; patchy clumps ⇒ wilt;
  sharp single-date ⇒ hail; failure-to-decline/re-greening ⇒ excess N / late
  topping / sucker) is the backbone of `interpret_primary_driver`.

## (f) Side-marketing — **PASS**

- research.md §7 explains the dynamic in Zimbabwe-specific terms (~95% contract;
  ~US$57m lost 2021; TIMB inspectorate; GIS field marking; grower-number fraud)
  with sourced figures.
- **Measurable detection signals identified:** satellite-estimated production vs
  delivered volume; stress-corroborated vs unexplained shortfall;
  reaping-signature timing; field-boundary/grower-number integrity. These map
  cleanly onto `detect_side_marketing_signal` (model_design §7).

## (g) Research gaps — **PASS**

- research.md §9 explicitly enumerates gaps (green→cured conversion basis;
  no Zimbabwe NDVI-integral→cured-yield calibration; interpolated variety/region
  cells; spray-calendar/subsoiling specifics; GDD base-temp 10 vs 13 °C).
- Estimates are **labelled as estimates** ("estimated; primary source needed")
  throughout, not presented as hard data.

---

## Blockers carried into design as explicit assumptions (none halt Phase 2)

| # | Item | Phase 2 handling |
|---|------|------------------|
| 1 | NR II `best_practice` 4,500 > sanity band | Split into `Y_base` (3,200 operational) + `Y_ceiling` (4,500 clamp); see model_design §1. |
| 2 | Interpolated variety numerics | `variety_calibration` soft multiplier + confidence penalty flag `interpolated=True`. |
| 3 | No empirical NDVI→cured-yield calibration | Satellite factor scores *relative health* vs stage baselines, not absolute kg; documented as the key Phase-3 calibration task. |
| 4 | Green→cured conversion ambiguity | Model works entirely in **cured kg/ha** (baselines already cured-leaf); conversion deferred to Phase 3 ingest. |
| 5 | Spray-count not precisely sourced | Scored vs a documented minimum band (≥6 typical), low weight. |

**Decision: all criteria PASS or GAPS_BUT_PROCEEDABLE → proceed to Step B.**

---

## Amendments applied (Phase 2, 2026-06-05)

Following the Step B/C/D build, the two GAPS items were addressed at the user's
request:

1. **Gap (b) — NR II ceiling above sanity band → RESOLVED (now PASS).**
   `natural_region_baselines.json` (schema 1.1): every region's `best_practice`
   lowered to operational best practice within band (I 3,000 / II 3,300 /
   III 2,800 / IV 2,200 / V 1,800) and a new `genetic_ceiling_kg_ha` field carries
   the former hybrid ceilings (I 4,000 / II 4,500 / III 3,800 / IV 3,000 /
   V 2,600). `tobacco_math.project_yield` now clamps to `genetic_ceiling_kg_ha`
   (with `best_practice` fallback for older files). NR II clamp unchanged at 4,500,
   so no model behaviour regressed; all 48 tests still pass.

2. **Gap (a) — variety interpolation → IMPROVED.** Plant-population ranges grounded
   in the sourced Zimbabwe spacing standard (1.2 m × 0.50–0.56 m ⇒
   ~14,800–16,700 plants/ha); `variety_database.json` `_meta` updated accordingly.
   Residual interpolation now limited to days-to-maturity and topping-leaf counts,
   which still require the full Kutsaga trial tables (carried as the one remaining
   GAPS_BUT_PROCEEDABLE item and noted in research.md §9).

New sources added to `sources.md`: Kutsaga spacing trial (1.2 × 0.56 m), Britannica
*common tobacco* (Orinoco flue-cured spacing).

