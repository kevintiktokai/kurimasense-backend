# Season accumulations — audit (Depth Sprint PR D backend, Step A)

## Weather provider & plumbing

- **`climate_service.py`** is the single weather module. Provider: **Open-Meteo**.
  - `HISTORICAL_URL = https://archive-api.open-meteo.com/v1/archive` — the
    historical archive used for past daily temps/precip (exactly what these
    season curves need; **historical only**, no forecast).
  - One shared `httpx.AsyncClient` via `_get_http()`; params built with
    `_join_params`. An in-process `_weather_cache` dict (TTL) exists for current
    weather. **Reuse decision:** add `get_daily_history(lat, lon, start, end)` to
    `climate_service` (reuses the client + a small module-level dict cache keyed
    by `lat:lon:start:end`, 6h TTL). **No caching table, no migration.**
- An existing **`calculate_gdd`** already hits the archive for
  `temperature_2m_max/min` — but it applies **no upper cap** and is entangled
  with progress/variety DB lookups, so it's not reused directly. We reuse its
  **fetch pattern**, not the function.

## GDD parameters (chosen + why)

- Bases come from the canonical lookup **`crop_constants.CROP_BASE_TEMPS`**
  (`get_base_temp`): tobacco 10 °C, maize 10 °C, soybean 10 °C, cotton 15.6 °C —
  these match the spec. No caps exist there, so this PR adds an **upper cap**.
- **Cap = 30 °C** for all crops (tobacco explicitly per spec; 30 °C is the
  standard upper threshold above which extra heat doesn't speed development for
  these warm-season crops). Documented in `services/season/accumulations.py`.
- Formula (with cap): `gdd = max(0, min((tmax+tmin)/2, cap) - base)`. Below base →
  0; mean above the cap → capped at `cap - base`. Matches the spec formula plus
  the "above cap → capped" behaviour.
- `gdd_params_for(crop_type)` normalizes the field's `crop_type` (e.g.
  `tobacco_flue_cured` → tobacco family) to `(base, cap)`, with a `(10, 30)`
  default for unknown crops.

## Field record / centroid

`resolve_access(field_id, requester_id, tenant_ids, is_admin)` (in
`services/field_state/aggregator.py`) loads the field **without** a tenant filter
then enforces access — **404** if absent (`FieldNotFound`), **403** otherwise
(`FieldAccessDenied`); grants access by admin / tenant membership / legacy
`user_id == requester_id`. Its SELECT already returns `planting_date`,
`crop_type`, `polygon_coordinates`. The endpoint reuses it verbatim, and the
existing `_centroid(polygon)` helper for the weather lat/lon (Harare fallback).

## Endpoint shape

`GET /field/{field_id}/season-accumulations` in a new light **`season_routes.py`**
(mirrors `portfolio_routes`/`grower_routes` so it's unit-testable in isolation;
its own self-contained principal dependency via `auth_roles.get_authenticated_user`,
same API-key-or-session pattern as `get_state_principal`). Pure series math lives
in **`services/season/accumulations.py`** (no network, no Pydantic-of-HTTP) and is
unit-tested against fixed daily fixtures.

## Latency

Measured live in the PR description (one archive call for the window, ~150-day
window for a tobacco field). The single archive request dominates; series math is
microseconds.
