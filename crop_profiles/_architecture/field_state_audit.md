# Field State Audit — Input to the Field State Aggregator

**Status:** Step A deliverable for the Field State Aggregator refactor.
**Date:** 2026-06-05
**Scope:** Every consumer screen in `kurima-sense` (frontend) and the backend
endpoints/modules in `kurimasense-backend` they depend on.

The purpose of this document is to capture *what data each screen actually
consumes*, *where it interprets that data locally*, and *where screens
contradict each other* — so that the aggregator (`GET /field/{field_id}/state`)
is built against the screens' real needs rather than a guess.

---

## 0. Cross-cutting findings (the "why" behind this refactor)

| # | Finding | Impact |
|---|---------|--------|
| F1 | **Health status has two sources.** Backend returns `field.healthStatus` (derived from `health_score` via `deps.get_health_status`), *and* the Field Detail screen recomputes a label from raw NDVI against a local crop-threshold table. The two disagree → "EXCELLENT HEALTH" badge over a "Critical" NDVI. | The contradiction screenshotted in the prompt. |
| F2 | **Threshold/interpretation logic lives in the frontend.** `app/fields/[id]/page.tsx` carries a ~25-crop `cropThresholds` table and `getNdviLabel`/`getMoistureLabel`/`getNdviColor` functions. A near-identical table *also* exists in the backend (`app.py` `get_field_insight`, lines ~742–799). Two copies, drift guaranteed. | Changing a threshold requires editing both repos. |
| F3 | **Confidence is rendered as a raw number.** `CropPlan.tsx` renders `Confidence: {plan.confidence_score}%` directly. The backend yield model emits `confidence_score` as a 0–1 float → `0.6` rendered as `0.6%`. Chat and YieldConfidenceChart *do* multiply by 100, so formatting is inconsistent across screens. | The "Confidence: 0.6%" bug. |
| F4 | **"Field not found" from the insight path.** `GET /fields/{id}/insight` queries `WHERE f.id = %s AND f.user_id = %s`. When the requesting session's `user_id` does not match the row's `user_id` (tenant/scope mismatch), the query returns no row and the endpoint emits `{"insight": "Field not found..."}` — even though the field exists and has satellite data. | The Agronomist Insight panel bug. |
| F5 | **Crop Health Trends chart plots raw NDVI (0–1) and soil moisture (0–100) on dual axes with no single labelled unit.** With NDVI scaled and moisture overlaid, the visible axis reads as an unlabelled ~0–32+ range. | The "what unit is this 0–32 axis?" confusion. |
| F6 | **Same data fetched many times with different shapes.** A user crossing Dashboard → Field Detail → Plan → Weather triggers 5–7 round-trips for overlapping field state, with no shared cache and different field shapes (`field.ndvi` snapshot vs `history[].ndvi` series vs yield-embedded `current_stage`). | Latency + divergence. |
| F7 | **Growth stage has two sources.** Plan reads `current_stage` from `/fields/{id}/yield`; Weather reads GDD `progress_percent` from `/climate/agricultural`. Nothing reconciles them. | Two "how far along is this crop?" answers. |

**Conclusion:** there is no canonical "state of this field". Each screen computes
its own. The aggregator resolves F1–F7 by becoming the single source of truth and
moving *all* interpretation server-side.

---

## 1. Frontend data layer (shared)

- **Base URL:** `services/api.ts` → `API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'`.
- **Auth:** `lib/api-cache.ts` → `getAuthHeaders()` attaches `Authorization: Bearer <supabase access_token>`.
- **Data layer:** **SWR is installed (`swr@^2.3.8`) but the app primarily uses manual `fetch` + an in-memory `Map` cache** (`lib/api-cache.ts`, `CACHE_TTL`). **No React Query.**
  - → *The aggregator hook (`useFieldState`) is implemented with SWR to match the dependency already present, falling back to the same fetch+cache idiom.*
- **Charts:** `recharts@^3.7.0` everywhere.

---

## 2. Screen-by-screen audit

### 2.1 Dashboard — `app/dashboard/page.tsx` → `components/dashboard/Overview.tsx`
- **Endpoints:** `GET /dashboard/init` (combined `fields[] + stats + market`); deferred `POST /proactive`, `GET /ai/insights`, `POST /fields/{id}/yield`.
- **Data consumed:** `fields[].ndvi`, `fields[].soilMoisture`, `fields[].healthStatus`, `stats`, yield `projected_yield`/`yield_potential`, proactive `insight`, `risks[]`, `actions[]`.
- **Local interpretation:**
  - `avgNdvi = mean(fields.ndvi)`, `avgMoisture = mean(fields.soilMoisture)` — the **"AVG NDVI" card**.
  - `yieldEfficiency = min(98, round(projected/potential*100))`.
  - "Low vigour — check field" copy is hard-coded.
  - Confidence badge: `Math.round(confidence*100)%` with 0.8/0.5 colour cutoffs.
- **Aggregator mapping:** AVG NDVI → **AVG KurimaScore** (`kurima_score.score`); copy → `kurima_score.recommended_action`; "No active risks" → `alerts`.

### 2.2 Fields list — `app/dashboard/fields/page.tsx` → `components/dashboard/FieldManagement.tsx`
- **Endpoints:** uses cached `fields[]` from the provider; `POST /fields`, `DELETE /fields/{id}`, `GET /crops/{crop}/varieties`.
- **Data consumed:** `field.healthStatus` → `healthConfig` map (Excellent/Good/Critical → colour+label).
- **Local interpretation:** maps backend `healthStatus` to colour/label only (no NDVI thresholds here).
- **Aggregator mapping:** `kurima_score.label`/`kurima_score.color` directly.

### 2.3 Field detail — `app/fields/[id]/page.tsx` (the "Analyze Insights" screen)
- **Endpoints:** `GET /fields` (find by id), `GET /fields/{id}/history`, `GET /fields/{id}/insight`, `POST /fields/{id}/yield`, `POST /fields/{id}/analyze`.
- **Data consumed:** `field.ndvi`, `field.soilMoisture`, `field.healthStatus`, `history[]`, `insight`, yield projection.
- **Local interpretation (THE contradiction source):**
  - `cropThresholds` table (~25 crops) + `getNdviLabel`/`getNdviColor`/`getMoistureLabel` (lines ~217–254). **This is where "0.21 < 0.3 = Critical" is decided client-side.**
  - Health badge styled off `field.healthStatus` (lines ~361–368) — *independent* of the NDVI label above ⇒ "EXCELLENT HEALTH" + "Critical NDVI".
  - `yieldEfficiency` recomputed locally.
  - **Crop Health Trends chart** (Recharts AreaChart, lines ~515–561): plots `ndvi` and `soilMoisture` on dual axes, reference lines at `ct.ndvi.good`/`ct.ndvi.moderate`. **No single labelled unit (F5).**
  - Scouting pins are **localStorage-only** (`scouting_pins_{fieldId}`) — not yet persisted server-side.
- **Aggregator mapping:** remove local thresholds; render `kurima_score.label`/`.color` as the single badge; chart switches to `indices.trend_30d[].kurima_score` with a "KurimaScore (0–100)" axis and Stressed/Adequate/Strong band regions.

### 2.4 Plan tab — `app/dashboard/plan/page.tsx` → `CropPlan.tsx` + `ActivityLog.tsx`
- **Endpoints:** `POST /fields/{id}/yield` (plan + stage), `GET /ai/tasks?date&field_id`, `POST /ai/tasks/from-plan`, `GET /ai/tasks/history`.
- **Data consumed:** `current_stage`, `days_to_harvest`, `progress_percent`, `next_actions[]`, `full_plan[]`, `confidence_score`, `pest_alert`, tasks.
- **Local interpretation:** `Confidence: {confidence_score}%` rendered raw → **the 0.6% bug (F3)**. Plan items not cross-checked against current alerts.
- **Aggregator mapping:** `active_plan_items[]` (with `contextualized_to_current_conditions` + `notes`); a "Review against current conditions" note when a plan item conflicts with a high-severity alert.

### 2.5 AI Advisory chat — `app/dashboard/chat/page.tsx` → `AIAgronomistChat.tsx`
- **Endpoints:** `GET /chat/history`, `POST /chat/v2/stream` (SSE), `POST /chat/v2/send` (with image).
- **Data consumed:** message stream, `confidence_score`, `detected_intent`, `proactive_insights[]`, `actions[]`.
- **Local interpretation:** confidence badge `Math.round(confidence*100)%`.
- **Aggregator mapping:** chat is *not* re-platformed in this refactor; it may optionally hydrate field context from the aggregator, but its endpoints stay. Listed for completeness.

### 2.6 Climate / Weather — `app/dashboard/weather/page.tsx`
- **Endpoints:** `GET /climate/current`, `/climate/forecast`, `/climate/alerts`, `/climate/agricultural`, `/climate/spray-window`, `/climate/historical` (all `?field_id=`).
- **Data consumed:** `current` (temp/humidity/wind/uv), `daily[]`, `hourly[]`, `growing_degree_days`, `water_balance`, `moisture`, alerts, spray windows.
- **Local interpretation:** water-balance colour by `status` (surplus/deficit/balanced); GDD progress bar from `progress_percent`.
- **Aggregator mapping:** re-wire to `weather`, `water_balance`, `growing_degree_days` sections of the aggregator so it shares the same source. (This screen is already strong; only the data source changes.)

---

## 3. Backend modules the aggregator composes

| Concern | Module / entry point | Notes |
|---------|----------------------|-------|
| Auth + scope | `deps.verify_token() -> user_id` | **No `tenant_id` column today.** Tenancy == `user_id`. (See gap G1.) |
| DB | `database.get_db_connection()` (psycopg2 pool, `RealDictCursor`) | Tables: `fields`, `daily_logs`, `field_inputs`, `farm_tasks`, `crop_varieties`, `profiles`. |
| KurimaScore (tobacco) | `crop_profiles/tobacco_flue_cured/tobacco_math.py` | `compute_satellite_component`, `compute_management_component`, `compute_environmental_component`, `compute_kurima_score`, `compute_confidence`, `detect_stage`. **Not modified.** |
| KurimaScore (other crops) | **NEW** `services/field_state/generic_crop_math.py` | Mirrors the tobacco interface with crop-agnostic defaults (per prompt Step C.2). |
| Yield | `yield_model.generate_yield_projection(...)` / `tools.generate_yield` | Emits `confidence_score` (0–1) — must be banded in the aggregator. **Not modified.** |
| Weather / GDD / water balance | `climate_service.get_current_weather / get_daily_forecast / get_agricultural_metrics / calculate_gdd` (async) | Open-Meteo backed; cached 5 min. |
| Plan / recommendations | `agronomic_engine.*` | Deterministic helpers. |
| Alerts | `proactive_intelligence.generate_proactive_alerts(...)` (async), `calculate_growth_stage(...)` | Growth stage + alerts. |
| Crop profiles | `crop_profiles.get_crop_profile_or_generic(crop)` | Stage ranges, temps, GDD base. |

---

## 4. GAPS the audit surfaced (data the aggregator needs but the backend doesn't fully provide)

> Per the prompt: *if the audit shows the aggregator needs data the backend doesn't currently provide, surface that as a finding — do not silently build on missing data.*

- **G1 — No `tenant_id`.** Isolation today is by `fields.user_id`. The contract asks for `tenant_id` and X-API-Key institutional access with tenant scoping. **Decision:** the aggregator treats `user_id` as the tenant boundary and surfaces it as `field.tenant_id`. The 403-vs-404 security rule is implemented (field looked up by id first; ownership mismatch ⇒ 403). A true `tenant_id` column / API-key table is out of scope for this refactor and is noted for a follow-up migration.
- **G2 — `daily_logs` only stores `ndvi`, `evi`, `soil_moisture`, `cloud_cover`.** The contract's `indices.current` also lists `ndre`, `ndmi`, `savi`, `sar_vv_db`. **Decision:** the aggregator returns the columns that exist and marks the rest `null` with an `observation_quality`/completeness flag; KurimaScore uses whatever indices are present (the tobacco/generic math already renormalise over present indices).
- **G3 — No `variety_code` column.** `fields.variety` is free text. Tobacco math needs a code present in `variety_database.json`. **Decision:** attempt a tolerant lookup; on `UnknownVarietyError`, fall back to generic crop math and set `data_completeness.has_variety_in_database = false`.
- **G4 — Scouting observations are localStorage-only.** No server table. **Decision:** `scouting_observations` returns `[]` with a completeness flag until a table exists (noted for follow-up). Field-input records (`field_inputs`) *do* exist and feed `has_input_records`.
- **G5 — `expected_harvest_date` / per-stage expected NDVI** are not stored. **Decision:** derived in the aggregator from planting date + crop profile maturity and the per-phase NDVI baselines in `classifiers.py`.

These gaps are handled gracefully (nulls + completeness flags), never fabricated.
