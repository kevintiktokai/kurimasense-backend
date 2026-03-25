# Agronomist Flow SOP

## Purpose
Define deterministic steps for producing advice from user input and context data.

## Inputs
- Unified Agronomist Input ("Seed") from `gemini.md`
- Satellite & Weather Context ("Soil") from `architecture/data_ingestion.md`

## Output
- Delivery Payload ("Harvest") from `gemini.md`

## Steps
1. Validate the incoming Seed object has `user_id`, `session_id`, `timestamp`, `location`, `context`, `intent_classification`, and `raw_message`.
2. Route by `intent_classification`:
   - `weather_check`: require weather context only.
   - `general_advice`: require weather + satellite context.
   - `disease_id`: require weather + satellite context and request photo if missing.
3. Determine response language:
   - Use `seed.language` if provided.
   - Otherwise detect language from `raw_message`.
3. Call `tools/get_weather_forecast.py` and/or `tools/get_crop_health.py` as required by the intent.
4. Merge results into a single "Soil" object with source metadata and tool status.
5. Call `tools/generate_advice.py` with the Seed + Soil objects and target language.
6. Validate the advice output adheres to the Delivery Payload schema.
7. Ensure behavioral laws are respected:
   - If confidence < 0.80, return a clarifying question instead of a prescription.
   - If any tool fails, degrade to best-practice advice and explain the missing context.

## Error Handling
- Missing or invalid input: return a structured error payload with `confidence_score: 0.0`.
- Tool error: include `reasoning_trace` indicating the failing tool and fallback path used.
