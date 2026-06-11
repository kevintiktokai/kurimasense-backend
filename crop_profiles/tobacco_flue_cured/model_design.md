# Flue-Cured Tobacco — Yield Model & KurimaScore Design Specification (Phase 2)

**Status:** Design + isolated math ONLY. This document specifies the math
implemented in `tobacco_math.py`. It does **not** modify `yield_model.py`,
`crop_constants.py`, the database, or any API. Phase 3 will integrate.

**Grounding:** every factor cites Phase 1 (`research.md` §n, `phase2_audit.md`,
`variety_database.json`, `natural_region_baselines.json`). All yields are in
**cured leaf kg/ha** (the unit of the Phase 1 baselines), sidestepping the
unresolved green→cured conversion (audit gap #4).

**Units convention:** components and factor-internal scores are dimensionless in
`[0,1]`; the six yield factors are in `[0.0, 1.5]`; yields are kg/ha cured leaf;
KurimaScore is an integer `0–100`.

---

## 1. Yield Projection Formula

### 1.1 Master formula

```
projected_yield_kg_ha =
      base_potential
    × variety_calibration       # [0.85, 1.15]
    × natural_region_factor     # [0.40, 1.00]
    × management_quality_factor # [0.55, 1.05]
    × satellite_health_factor   # [0.60, 1.10]
    × stress_event_factor       # [0.30, 1.00]
```

Result is then **clamped** to `[200, Y_ceiling[region]]` where `Y_ceiling` is the
`genetic_ceiling_kg_ha` field of `natural_region_baselines.json` (the documented
hybrid genetic ceiling; falls back to `best_practice` for older data files). This
field was introduced in the Phase 2 amendment that resolved audit gap (b) — see
`phase2_audit.md`; NR II ceiling = 4,500 kg/ha, operational `best_practice` = 3,300.
Every factor is individually clamped to the Phase-2 mandated `[0.0, 1.5]` window
before multiplication; the tighter sub-ranges above are the *design* ranges.

### 1.2 Factor definitions

**`base_potential` — region-neutral genetic reference = 3,500 kg/ha.**
This is the flue-cured reference optimal (≈ K326/modern-line optimal,
`variety_database.json`). It is deliberately region-neutral; region scaling is
applied separately. Rationale for not using NR II `best_practice` 4,500 directly:
`phase2_audit.md` (b) — 4,500 encodes the hybrid ceiling and would systematically
over-predict; 3,500 is the cross-variety optimal and 4,500 is retained only as
the NR II clamp.

**`variety_calibration` ∈ [0.85, 1.15]** — relative genetic merit of the chosen
variety:
```
variety_calibration = clip( variety.yield_potential_kg_ha_optimal / 3500, 0.85, 1.15 )
```
For interpolated-numeric varieties (audit (a)) the value is still usable but the
variety is tagged `interpolated=True`, which docks confidence (§6). Unknown
variety → raises `UnknownVarietyError` (§8); callers must handle.

**`natural_region_factor` ∈ [0.40, 1.00]** — agro-ecological suitability relative
to NR II, derived from the Phase 1 `best_practice` ceilings
(`natural_region_baselines.json`) normalised to NR II:
| NR | ceiling (kg/ha) | factor = ceiling / 4500 |
|----|-----------------|--------------------------|
| I | 4000 | 0.89 |
| II | 4500 | 1.00 |
| III | 3800 | 0.84 |
| IV | 3000 | 0.67 |
| V | 2600 | 0.58 |

(The "ceiling" column above is the `genetic_ceiling_kg_ha` field added in the
Phase 2 gap-(b) amendment; factors are unchanged.)
This is intentionally more generous than `yield_model.py`'s legacy tobacco
multipliers (IV 0.4 / V 0.2) because `base_potential` is already a single
reference and management/stress factors carry the rest; the divergence is
flagged for Phase-3 reconciliation (§10).

**`management_quality_factor` ∈ [0.55, 1.05]** — linear map of the management
component (§3.2):
```
management_quality_factor = 0.55 + 0.50 × management_component
```

**`satellite_health_factor` ∈ [0.60, 1.10]** — linear map of the satellite
component (§3.1):
```
satellite_health_factor = 0.60 + 0.50 × satellite_component
```

**`stress_event_factor` ∈ [0.30, 1.00]** — combines chronic environmental stress
with acute catastrophic events:
```
stress_event_factor = (0.50 + 0.50 × environmental_component)
                     × Π (1 − acute_penalty_e)
```
`acute_penalty_e` per discrete event (from `environmental_data`): hail 0.0–0.6,
confirmed bacterial/Granville wilt patch 0.1–0.3, severe waterlogging 0.1–0.3
(Phase 1 §6 impact ranges). Product clamped so the factor floors at 0.30.

### 1.3 Point estimate + confidence interval

The point estimate is the clamped product. The interval is **multiplicative**,
widening with uncertainty:
```
frac = WIDTH[confidence_band]          # high 0.12, medium 0.20, low 0.30
interval_low  = max(150, point × (1 − frac))
interval_high = min(Y_ceiling, point × (1 + frac)) ; and ≥ point × (1 + 0.5×frac)
```
`confidence_band` comes from §6. Early-season, sparse-observation, missing-input
forecasts get `low`/`medium` bands → wider intervals; late-season data-rich
forecasts get `high` → tight intervals. Invariant: `low < point < high` always
(enforced; if clamps collide, point is nudged to strict interior).

---

## 2. KurimaScore Composition

```
kurima_score = round( 100 × ( W_SAT × satellite_component
                            + W_MGT × management_component
                            + W_ENV × environmental_component ) )
```
Each component ∈ `[0,1]`; weights sum to 1.0 per stage. Defaults
`W_SAT=0.40, W_MGT=0.35, W_ENV=0.25`.

### 2.1 Per-stage weight overrides (`STAGE_WEIGHTS`)

| Stage | W_SAT | W_MGT | W_ENV | Justification (Phase 1) |
|-------|-------|-------|-------|--------------------------|
| `ESTABLISHMENT` | 0.25 | 0.30 | 0.45 | Canopy too sparse for reliable optical signal; rainfall/anchorage dominate survival (§3.1, §4c). |
| `VEGETATIVE` | 0.45 | 0.30 | 0.25 | Canopy closure makes NDVI/NDRE most informative; rapid N/K uptake (§3.2). |
| `REPRODUCTIVE` | 0.40 | 0.45 | 0.15 | Topping & N-management decisions dominate outcome; weather less pivotal once established (§4e, §6 N-excess). |
| `TOPPING_RIPENING` | 0.45 | 0.40 | 0.15 | Ripening (NDMI/NDRE) + sucker/topping discipline drive grade & weight (§3.2, §6 sucker/late-topping). |
| `REAPING` | 0.55 | 0.30 | 0.15 | Defoliation signature / NDVI integral dominate; little management left to change outcome (§3.2). |

All rows sum to 1.00. Weights are module constants and tunable.

---

## 3. Component Calculations

### 3.1 Satellite component (0–1)

```
satellite_component = Σ_i  w_index[stage][i] × index_score[i]      (Σ w = 1.0)
```
over the index set `{NDVI, EVI, NDRE, NDMI, SAVI, SAR}` where `SAR` is the
VH/VV backscatter ratio. If some indices are absent from `indices_history`, their
weights are dropped and the remainder **renormalised to sum 1.0**. Empty history
→ neutral `0.5` (cannot assess; confidence handles the penalty).

**Per-stage index weights (`INDEX_WEIGHTS`, each row sums to 1.0):**

| Stage | NDVI | EVI | NDRE | NDMI | SAVI | SAR |
|-------|------|-----|------|------|------|-----|
| ESTABLISHMENT | 0.25 | 0.00 | 0.00 | 0.20 | 0.45 | 0.10 |
| VEGETATIVE | 0.30 | 0.25 | 0.30 | 0.10 | 0.05 | 0.00 |
| REPRODUCTIVE | 0.15 | 0.35 | 0.35 | 0.15 | 0.00 | 0.00 |
| TOPPING_RIPENING | 0.15 | 0.20 | 0.30 | 0.35 | 0.00 | 0.00 |
| REAPING | 0.30 | 0.20 | 0.00 | 0.15 | 0.00 | 0.35 |

(SAVI-heavy at establishment for soil background; NDRE/EVI at canopy closure to
avoid NDVI saturation; NDMI at ripening for leaf moisture; SAR at reaping for
canopy structure — Phase 1 §3.2.)

**Raw value → `index_score` ∈ [0,1]:** linear interpolation against a
stage-specific `(floor, target)` baseline (`INDEX_BASELINES`), all indices framed
so *more vegetation/moisture = healthier* (keeps the score monotone):
```
index_score = clip( (value − floor) / (target − floor), 0.0, 1.0 )
```
The most recent up-to-3 valid observations per index are **averaged** for
stability; the same window feeds the trend used by the driver logic (§5).

Representative `INDEX_BASELINES` `(floor, target)` (full table in code):
NDVI: estab (0.15,0.45), veg (0.45,0.80), repro (0.55,0.85), ripen (0.45,0.80),
reap (0.30,0.65). NDRE: ~(0.15,0.45). NDMI: ~(−0.05,0.35). EVI: ~(0.20,0.65).
SAVI: ~(0.10,0.50). SAR(VH/VV): ~(0.15,0.40).

### 3.2 Management component (0–1)

Five sub-scores, each ∈ [0,1]:

- **`pop_score`** — actual vs the variety's `plant_population_min/max`
  (`variety_database.json`). Inside range → 1.0; below min → linear to 0 at 0
  plants; above max → mild over-density penalty, linear to 0.70 at 2×max.
- **`fert_score = 0.5 × basal_score + 0.5 × topdress_score`.**
  `basal_score`: recognised tobacco compound (Compound C/S) **and** rate in band
  (C: 600–900 kg/ha, S: 350–550 kg/ha → 1.0; partial credit for low/no rate or
  unrecognised product). `topdress_score = topdressing_schedule_completion` (0–1).
  (Phase 1 §4b; N-ceiling discipline.)
- **`topping_score`** — days-after-transplant vs optimal window 55–75 d. In window
  → 1.0; later → `max(0, 1 − 0.03 × (t − 75))` (each late day ≈ 50 kg/ha,
  §4e); much earlier than 50 d → mild penalty. `None` → neutral 0.70.
- **`spray_score = clip(spray_applications_count / 6, 0, 1)`** (6 ≈ typical full
  season program; §4d, count-based because exact calendar is an audit gap).
  `None` → 0.60.
- **`sucker_score`** — `True`→1.0, `False`→0.40 (breakthrough risk, §6), `None`→0.70.

Combination (weighted average + a worst-link guard so one catastrophic failure
still bites — tobacco is unforgiving of a single missed operation):
```
weights = {pop:0.20, fert:0.35, topping:0.20, spray:0.10, sucker:0.15}   (Σ=1.0)
wavg = Σ weight_k × subscore_k
management_component = clip( 0.85 × wavg + 0.15 × min(subscores), 0, 1 )
```
Monotone non-decreasing in every sub-score (both terms are). Sub-scores that are
not yet meaningful for the current stage (e.g., topping pre-topping) use their
neutral `None` defaults.

### 3.3 Environmental component (0–1)

```
base_env = clip( mean_over_elapsed_stages(rain_score_s) − drought_pen − heat_pen, 0, 1 )
environmental_component = clip( base_env × region_reliability[region], 0, 1 )
```
- **`rain_score_s`** per elapsed stage `s`: `adequacy = rainfall_s / WATER_REQ_s`
  with stage requirements `{ESTABLISHMENT:40, VEGETATIVE:160, REPRODUCTIVE:90,
  TOPPING_RIPENING:110, REAPING:50}` mm (Σ≈450, Phase 1 §4c). Mapped
  `rain_score = clip(0.30 + 0.70 × min(adequacy,1.1)/0.9, 0, 1)` (0.9 adequacy
  → 1.0; monotone increasing in rainfall).
- **`drought_pen = clip(0.01 × Σ drought_days, 0, 0.40)`.**
- **`heat_pen = clip(0.05 × heat_stress_events, 0, 0.30)`** (heat during sensitive
  stages; §6 water/heat stress).
- **`region_reliability`**: I 1.00, II 0.97, III 0.88, IV 0.72, V 0.58 — encodes
  agro-ecological rainfall reliability so that a *marginal region caps the
  environmental ceiling even under good local weather* (this is what pulls an
  "optimal-everything" Region V crop down to the Adequate band; §4, §5).

---

## 4. KurimaScore Labels and Output Structure

| Score | Label | Color |
|-------|-------|-------|
| 85–100 | Thriving | #2E7D32 |
| 70–84 | Strong | #66BB6A |
| 55–69 | Adequate | #FBC02D |
| 40–54 | Stressed | #F57C00 |
| 25–39 | Distressed | #D84315 |
| 0–24 | Critical | #B71C1C |

`compute_kurima_score(...) -> dict` returns:
```
{
  "score": int,                       # 0–100
  "label": str,                       # one of the six
  "color": str,                       # hex
  "component_breakdown": {"satellite": float, "management": float, "environmental": float},
  "primary_driver": str,              # §5
  "likely_cause": str,                # §5
  "recommended_action": str,          # §5
  "yield_implication": str,           # qualitative impact statement
  "confidence_band": str,             # "high" | "medium" | "low" (passed in / default "medium")
  "stage": str,
  "as_of_date": str | None            # ISO date echo if provided
}
```
`yield_implication` is derived from the score band (e.g., Stressed → "Projected
yield tracking 15–30% below regional best-practice unless corrected").

---

## 5. Primary Driver / Likely Cause / Recommended Action Logic

`interpret_primary_driver(component_breakdown, indices_trend, stage)
-> (primary_driver, likely_cause, recommended_action)`.

`component_breakdown` carries the three components plus **optional** sub-signals
when available (`fert_score`, `topping_score`, `sucker_score`, `pop_score`,
`input_quality_score`, `disease_type`, `waterlogging`). `indices_trend` carries
recent deltas (`ndvi_trend`, `ndre_trend`, `ndmi_trend`) and optional flags
(`ndvi_abrupt_drop`, `spatial_patchiness`). Rules are evaluated **in priority
order; first match wins** (acute/diagnostic before generic). Each cites Phase 1
§6.

1. **Hail** — `ndvi_abrupt_drop ≥ 0.20` (single-date crash): driver "Acute canopy
   loss (hail/storm)"; action salvage-reap + insurance (§6 hail).
2. **Bacterial / Granville wilt** — `spatial_patchiness == "high"` & `satellite<0.5`
   & `environmental>0.55` & stage ∈ {VEGETATIVE,REPRODUCTIVE,TOPPING_RIPENING}:
   driver "Soil-borne wilt (patchy collapse)"; action confirm Ralstonia, rogue,
   no chemical cure, resistant variety next season (§6 #7).
3. **Waterlogging** — `waterlogging == True` or (`ndmi_trend>0.05` & `satellite<0.5`):
   driver "Waterlogging / poor drainage"; action drainage, ridging (§6 #6).
4. **Water stress (drought)** — `ndmi_trend ≤ −0.03` & `environmental<0.55` &
   `management≥0.5`: driver "Water stress (drought)"; action irrigate rapid-growth
   window; drought-tolerant variety (§6 #5).
5. **Nitrogen deficiency** — stage ∈ {VEGETATIVE,REPRODUCTIVE} & `ndre_trend<0`
   (or `ndre`-driven low satellite) & `fert_score<0.5`: driver "Nitrogen
   deficiency"; action bring forward/raise AN within ≤100 kg N/ha ceiling; check
   pH (§6 #1).
6. **Nitrogen excess / late topping** — stage ∈ {REPRODUCTIVE,TOPPING_RIPENING} &
   `ndvi_trend ≥ 0` (canopy won't decline) & `topping_score<0.5`: driver "Delayed
   ripening — late topping / excess N"; action verify topping, stop N, push
   ripening (§6 #2, #14).
7. **Sucker breakthrough** — stage ∈ {TOPPING_RIPENING,REAPING} & `sucker_score<0.5`
   & `ndvi_trend>0.02` (re-greening): driver "Sucker breakthrough"; action
   re-apply maleic hydrazide / desucker within 7 d of topping (§6 #15).
8. **Plant population below spec** — stage ∈ {ESTABLISHMENT,VEGETATIVE} &
   `pop_score<0.5`: driver "Sub-optimal plant stand"; action gap-fill / record for
   yield-cap; review transplanting (§4a).
9. **Late / poor establishment** — stage == ESTABLISHMENT & `satellite<0.45` &
   `environmental>0.5`: driver "Poor establishment"; action scout cutworm/
   damping-off, replant gaps (§3.1, §6).
10. **Leaf-disease outbreak (angular leaf spot / blue mould)** — stage ∈
    {VEGETATIVE,REPRODUCTIVE} & `satellite<0.55` & `environmental>0.6`
    (wet/humid) & `ndvi_trend<0`: driver names the disease from `disease_type`
    ("angular_leaf_spot"→warm-wet; "blue_mould"→cool-wet seedbed/early); action
    copper/fungicide, spacing, resistant variety (§6 #9, #10).
11. **General disease / pest pressure** — `satellite<0.55` & `ndvi_trend<−0.01`
    not otherwise classified: driver "Canopy decline — disease/pest pressure";
    action scout aphid/budworm/leaf-spot, spray at threshold (§6 #12,#13).
12. **Management execution gap** — `management<0.40` & `environmental>0.60`:
    driver "Management execution gap"; action review fertiliser/topping/spray
    records with grower (§5 example).
13. **Environmental / regional limitation** — `environmental<0.40` &
    `management>0.60`: driver "Environmental constraint"; action weather-driven,
    limited intervention; consider irrigation/region fit (§5).
14. **On track (default)** — none triggered: driver "On track"; cause "Crop
    tracking to regional expectation"; action maintain program.

(≥12 substantive branches; the tests exercise each.)

---

## 6. Confidence Scoring

`confidence_band ∈ {high, medium, low}` from a `confidence_score ∈ [0.05,0.95]`:
```
score = 0.50
  + (obs≥5: +0.20 ; 3≤obs<5: +0.10 ; 1≤obs<3: −0.10 ; obs==0: −0.25)
  + (progress≥0.60: +0.15 ; 0.35≤progress<0.60: +0.05 ; progress<0.35: −0.05)
  − 0.10 × (recent_index_variance > 0.04)        # inconsistent signals
  − 0.03 × n_missing_core_inputs                  # variety/transplant/region/pop/fert
  − 0.10 × (unstable_recent_stress)               # stress detected, not yet stable
score = clip(score, 0.05, 0.95)
band  = high if score ≥ 0.70 else medium if score ≥ 0.45 else low
```
`progress = days_since_transplant / days_to_maturity`. Empty `indices_history`
forces `obs==0` → band cannot exceed `low` unless other factors strongly
positive (by construction it lands `low`/`medium`). Thresholds are module
constants.

---

## 7. Side-Marketing Detection Signal

`detect_side_marketing_signal(delivered_yield_kg_ha, predicted_yield_kg_ha,
std_dev, confidence_band) -> dict`.
```
deviation_std_devs = (predicted − delivered) / std_dev      # >0 ⇒ under-delivery
if confidence_band == "low":
    severity = "MEDIUM" if deviation_std_devs ≥ 1.0 else "LOW"   # cannot be HIGH
elif deviation_std_devs ≥ 2.0:
    severity = "HIGH"
elif deviation_std_devs ≥ 1.0:
    severity = "MEDIUM"
else:
    severity = "LOW"
```
- **`std_dev`** is supplied by `project_yield` as `point × WIDTH[band]` (so it
  **grows with data sparsity** via the band, §1.3/§6); guarded to a floor (≥150)
  to avoid divide-by-zero / absurd sensitivity.
- **HIGH requires `confidence_band ∈ {medium, high}`** — a low-confidence forecast
  can never raise a HIGH flag (offtaker protection against false accusation).
- **Offtaker-facing messages:**
  - HIGH: "Delivered yield is >2σ below KurimaSense's prediction with no
    corroborating field-loss event. Recommend reconciliation / field audit."
  - MEDIUM: "Delivered yield is 1–2σ below prediction. Monitor; cross-check
    against stress history before action."
  - LOW: "Delivered yield is within expected variance of prediction. No flag."

The flag is advisory; §10 notes it must always be paired with the stress history
so a genuine drought/hail shortfall is not mistaken for diversion (Phase 1 §7).

---

## 8. Phenological Stage Detection

`detect_stage(variety_code, transplant_date, current_date) -> str`.
```
d = (current_date − transplant_date).days
M = variety.days_to_maturity_max
if variety unknown:            raise UnknownVarietyError
if d < 0:                      return "PRE_TRANSPLANT"
if d < 21:                     return "ESTABLISHMENT"
if d < 56:                     return "VEGETATIVE"
if d < 70:                     return "REPRODUCTIVE"
t_reap = max(80, M − 30)
if d < t_reap:                 return "TOPPING_RIPENING"
if d < M:                      return "REAPING"
return "POST_HARVEST"
```
Stage boundaries 0/21/56/70 are fixed early-phenology anchors (Phase 1 §3);
the reaping window is variety-relative (last ~30 d to `M`). `PRE_TRANSPLANT` and
`POST_HARVEST` are valid sentinels (scored as edge cases, not errors); only an
unknown variety raises.

---

## 9. Data Requirements per Field

| Tier | Field | In `schemas.py` today? |
|------|-------|------------------------|
| **Required** | variety code | ✅ `CreateFieldRequest.variety` |
| **Required** | transplant date | ✅ `CreateFieldRequest.transplantDate` / `isTransplanted` |
| **Required** | Natural Region (from coords) | ⚠️ derivable from `coordinates`; not stored explicitly |
| **Required** | field polygon | ✅ `CreateFieldRequest.coordinates` |
| **Recommended** | plant population/ha | ❌ not captured — **Phase 3 add** |
| **Recommended** | basal product + rate | ⚠️ partial via free-text `fertilizerHistory`; not structured |
| **Recommended** | topdressing schedule + rates | ⚠️ partial via `LogInputRequest` (`input_type/quantity/unit`); no schedule completion field |
| **Recommended** | irrigation regime (categorical) | ❌ not captured — **Phase 3 add** |
| **Optional** | spray applications log | ⚠️ via `LogInputRequest` (unstructured) |
| **Optional** | topping date | ❌ not captured — **Phase 3 add** |
| **Optional** | disease/pest observations | ⚠️ via vision/chat, not structured for scoring |

**Phase 3 schema additions to propose (not done in Phase 2):**
`plant_population_per_ha:int`, `irrigation_regime:Literal["dryland","supplementary","full"]`,
`topping_date:date`, and a structured `topdressing_schedule_completion:float`
plus `basal_product`/`basal_rate_kg_ha`. None are added now.

---

## 10. Open Questions / Phase 3 Implementation Notes

**Review before Phase 3:**
- **`base_potential` 3,500 vs region ceilings** — confirm the genetic-reference
  approach vs per-region `Y_base`; affects absolute calibration.
- **`natural_region_factor` (this design: IV 0.67 / V 0.58) vs legacy
  `yield_model.py` (IV 0.40 / V 0.20)** — these disagree; Phase 3 must pick one
  source of truth. Recommendation: reconcile against real TIMB regional delivery
  data when available.
- **`region_reliability` pulling Region V KurimaScore into the Adequate band** —
  is capping the *health* score by region desired, or should KurimaScore reflect
  only realized health and let yield carry the region penalty? Product decision.
- **Green→cured conversion** (audit #4) — model is in cured kg/ha; the Phase 3
  ingest layer must convert green reap weights before comparison.

**Agronomist questions:** validate stage day-boundaries per maturity class;
confirm the 6-spray "typical season" minimum; confirm topping optimal window
55–75 d; sanity-check `INDEX_BASELINES` floors/targets against Kutsaga canopy
data.

**Integration points (Phase 3, handle carefully):**
- `yield_model.py` — `project_yield` here parallels `generate_yield_projection`;
  decide whether tobacco routes through this module or merges factor logic. Do
  **not** duplicate `NATURAL_REGION_MULTIPLIERS` divergently.
- `proactive_intelligence.py` — `detect_stage` overlaps `_calculate_tobacco_stage`
  and `get_variety_info` (DB-backed). Reconcile stage names (this spec's
  `TOPPING_RIPENING`/`REAPING` vs existing `TOPPING`/`RIPENING`/`HARVEST`).
- `ai_brain.py` — the driver/cause/action strings are designed to feed the
  narrative layer; ensure no double-interpretation.
- **Data migration:** new structured input fields imply a `crop_varieties` read
  path + field-level columns; `variety_database.json` should seed `crop_varieties`
  rather than diverge.

**Determinism / safety:** all functions are pure, type-hinted, no I/O beyond
load-time JSON, no time/randomness beyond passed-in dates — see `tobacco_math.py`.
