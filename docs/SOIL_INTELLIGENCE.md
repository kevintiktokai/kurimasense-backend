# Soil Intelligence Subsystem — Design & Implementation Report

## Executive Summary

KurimaSense now builds and maintains a **persistent Soil Intelligence Profile**
for every field. The profile is assembled from multiple public data providers,
stored once, reused locally, and injected automatically into the AI Advisor so
that soil, terrain, and agro-ecological context inform every agronomic
recommendation — without the farmer ever re-entering soil facts the system
already knows.

The delivery is a **provider-agnostic architecture**, not a single-API
integration. Adding a new soil source (a national dataset, a user-uploaded lab
test, an IoT probe) is a ~40-line provider class and one line in a registry;
nothing else in the pipeline changes.

- **Backend**: new `services/soil_intelligence/` package, `soil_profiles` table
  (migration 012 + init self-heal), two API endpoints, lifecycle hook on field
  creation, and AI Advisor context injection.
- **Frontend**: `getFieldSoil`/`refreshFieldSoil` API client methods and a
  self-contained `SoilProfileCard` on the field detail page.
- **Tests**: 26 new hermetic unit tests; full backend suite stays green
  (327 passed, 2 skipped); frontend typechecks and lints clean.

## Architecture

```
Field created ──► centroid coordinates ──► get_or_build_profile()
                                               │
              ┌────────────────────────────────┼───────────────────────────┐
              ▼                                 ▼                            ▼
     SoilGridsProvider                 TerrainClimateProvider        (future providers)
     (pH, texture, SOC, N,             (elevation, rainfall,          e.g. lab tests,
      CEC, bulk density,                natural region)                national datasets)
      water content, WRB class)
              └────────────────┬───────────────┴────────────────────────────┘
                               ▼
                         merge_attributes()      ← priority, then confidence
                               ▼
                        enrich_with_derived()    ← texture class, AWC, drainage,
                               ▼                    erosion, organic matter, root depth
                         SoilProfile (JSONB)
                               ▼
                  soil_profiles table  ──►  reused locally  ──►  AI Advisor context
                               ▲                                        │
                               └──────── refresh only when stale ◄──────┘
```

**Why this shape.** The handoff explicitly warned against "integrating a single
soil API." The core abstraction is therefore the **`SoilAttribute`** — a single
value that carries its *own* provenance (source, confidence, acquired-at,
refresh policy). A `SoilProfile` is just a map of these, so a profile can mix
sources attribute-by-attribute and a higher-authority source (a lab test) can
override a global model for one attribute without special-casing.

Layers:

| Layer | Module | Responsibility |
|-------|--------|----------------|
| Model | `models.py` | `SoilAttribute`, `SoilProfile`, refresh policy, AI summary rendering. Stdlib-only. |
| Providers | `providers/` | One class per source; `fetch(lat, lon) → [SoilAttribute]`, never raises. |
| Merge | `merger.py` | Union provider outputs; resolve conflicts by priority then confidence. |
| Derive | `derive.py` | Compute agronomic attributes (texture class, AWC, drainage, erosion, OM, root depth) from primaries. |
| Persist | `repository.py` | RLS-armed read/write of `soil_profiles`. Best-effort. |
| Orchestrate | `service.py` | Lifecycle: reuse stored → else fetch/merge/derive/persist; refresh horizon. |

## Provider Evaluation

All providers were **verified against their live APIs (July 2026)** for
Zimbabwe coordinates — the handoff insisted "do not assume previous integrations
are still available; verify everything."

| Provider | Decision | Rationale |
|----------|----------|-----------|
| **ISRIC SoilGrids v2.0 REST** | **Adopted (primary)** | Free, keyless, versioned REST contract. Global 250 m coverage incl. Zimbabwe (verified pH 6.1–6.4 over farmland; WRB class *Lixisols/Acrisols*). Ships per-attribute **uncertainty** → honest confidence. CC-BY 4.0. Effectively static → multi-year reuse. Supplies pH, sand/silt/clay, SOC, nitrogen, CEC, bulk density, field-capacity & wilting-point water content, and WRB classification. |
| **Open-Meteo (archive)** | **Adopted (terrain/climate)** | Already KurimaSense's weather backend — no new vendor/key. Archive response returns **elevation** for free; a multi-year daily precipitation sum gives mean annual rainfall, which classifies the field into Zimbabwe's **Natural Regions**. |
| **OpenLandMap** | **Deferred** | Viable but redundant with SoilGrids and a heavier WCS/point API. Kept as a documented future provider slot. |
| **FAO / HWSD** | **Deferred** | Coarser resolution; useful as a cross-check, not a primary. Slots in as a future provider. |
| **Google Earth Engine** | **Rejected (for now)** | Requires authentication, quota, and a heavyweight client — disproportionate for point soil queries and adds an operational dependency. Revisit only for raster/zonal analytics. |
| **National Zimbabwe soil survey** | **Deferred** | No stable public API located; best future path is ingesting digitised survey sheets as a high-priority provider. |

**Coverage nuance handled in code.** SoilGrids returns nulls on urban/water-masked
pixels (e.g. central Harare). The provider retries a handful of small (~1–3 km)
coordinate offsets before giving up, so a field centroid on a masked pixel still
resolves.

## Soil Intelligence Model

Canonical attributes (see `CANONICAL_ATTRIBUTES` in `models.py`):

- **Classification/texture**: `soil_classification` (WRB), `texture_class` (USDA,
  derived), `sand_pct`, `silt_pct`, `clay_pct`.
- **Chemistry**: `ph`, `organic_carbon`, `organic_matter` (derived, SOC×1.724),
  `nitrogen`, `cec`.
- **Physical/water**: `bulk_density`, `field_capacity`, `wilting_point`,
  `available_water` (derived), `water_holding_capacity` (derived, mm/m),
  `root_depth` (derived), `drainage` (derived), `erosion_risk` (derived).
- **Terrain/climate**: `elevation`, `slope`, `terrain`, `climate_zone`
  (Zimbabwe Natural Region), `historical_rainfall`.

Every attribute records **source, confidence (0–1), acquired-at, and refresh
policy**. Confidence is derived honestly: SoilGrids' own uncertainty band drives
soil-property confidence; classification uses the WRB class probability.

**Data lifecycle.** `RefreshPolicy` encodes how often each attribute may be
re-fetched (soil properties = multi-year, terrain = static, climate = annual).
`get_or_build_profile` returns a stored, fresh profile with **zero external
calls** on the common path, and only rebuilds when the profile is absent, stale,
or explicitly refreshed. `refresh_after` is persisted so the horizon survives
restarts. This directly implements the handoff's "store permanently → reuse
locally → refresh only when necessary."

## AI Integration

`deps.get_field_context` now loads the stored profile (DB-only, no network on the
chat path) and sets `FieldContext.soil_summary`. `to_prompt_section` appends the
formatted soil block, so **any field-scoped conversation** (chat v2 + streaming)
automatically receives the field's soil intelligence. The system prompt gained a
**"Soil-Aware"** mandate instructing the advisor to ground soil/fertiliser/
liming/irrigation advice in the profile, weight figures by confidence, and never
ask the farmer for soil facts already on file. The advisor now reasons over the
full context set: soil, crop, variety, planting/fertilizer history, weather,
climate, satellite analytics, growth stage, activities, and prior recommendations.

## Performance & Engineering Review

- **Common path is DB-only.** A built profile is reused with no external calls;
  the AI context read is a single indexed lookup on `soil_profiles(field_id)`.
- **Off-request-path build.** The baseline profile is fetched in a background
  task at field creation (alongside the existing history/GDD prefetch), so field
  creation latency is unchanged.
- **Concurrent, fault-isolated providers.** `asyncio.gather(return_exceptions=True)`
  runs providers in parallel; one slow/failed source never blocks the others or
  the caller. Providers are contractually non-raising.
- **Self-healing schema.** `soil_profiles` is created both by migration 012 and
  by `init_db` (same pattern as the SAR columns), so it exists on every
  environment without a manual step.
- **Incidental fix.** `FieldContext.to_prompt_section` previously emitted a
  literal `\\n` (escaped) between field lines; corrected to real newlines while
  adding the soil block.

## Future Expansion

The provider registry makes each of these an additive change:

- **User-uploaded lab soil tests** — a high-priority provider that overrides
  modelled values per attribute (the priority/confidence merge already supports
  this).
- **Soil sampling workflows** & **IoT sensor integration** — providers keyed on
  time-series probe data with `SEASONAL`/live refresh policies.
- **Precision & variable-rate fertilizer**, **nutrient budgeting** — consume
  `cec`, `ph`, `organic_matter`, `nitrogen` for rate calculations.
- **Yield-prediction improvements** — feed `water_holding_capacity`, `texture_class`,
  and `climate_zone` into the yield model.
- **Carbon accounting** & **soil-health scoring** — derived indices layered on
  `organic_carbon` trends over successive refreshes.

## Files

Backend: `services/soil_intelligence/**`, `soil_routes.py`,
`migrations/012_soil_profiles.sql`, `tests/test_soil_intelligence.py`; edits to
`app.py`, `database.py`, `deps.py`, `ai_brain.py`.
Frontend: `components/field/SoilProfileCard.tsx`; edits to `services/api.ts` and
`app/fields/[id]/page.tsx`.
