# Data Ingestion SOP

## Purpose
Fetch and normalize satellite and weather context into the "Soil" schema.

## Inputs
- `location.lat`, `location.lon` from the Seed schema
- Optional `context.crop_type`, `context.sowing_date`, `context.growth_stage`

## Output
- Satellite & Weather Context ("Soil") schema from `gemini.md`

## Weather Retrieval (OpenWeatherMap)
1. Call `tools/get_weather_forecast.py` with `lat`, `lon`.
2. Normalize fields into:
   - `current_temp`
   - `precip_chance_24h`
   - `humidity`
   - `forecast_summary`

## Satellite Retrieval (Sentinel Hub)
1. Call `tools/get_crop_health.py` with `lat`, `lon`, optional crop metadata.
2. Normalize fields into:
   - `ndvi_mean`
   - `ndvi_anomaly`
   - `evi_mean`
   - `evi_anomaly`
   - `cloud_cover_pct`
   - `last_pass_date`
3. Anomaly baseline is computed from a historical window (baseline: 60-30 days before now).

## Validation
- If any required field is missing, mark the tool result as `status: "error"` and provide `error_message`.
- If satellite data is unavailable, proceed with weather-only context and set `satellite` fields to `null`.

## Error Handling
- All tool failures must be surfaced to the Router with a deterministic error code.
