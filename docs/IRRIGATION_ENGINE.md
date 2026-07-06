# AI Irrigation Recommendation Engine

`services/irrigation` turns weather, crop knowledge, soil data and planner
history into **actionable, explainable** irrigation decisions — millimetres,
minutes, confidence and the reasoning chain — not reminders.

## Decision model

FAO-56 style daily root-zone water balance:

```
TAW  = AWC (mm/m, Soil Intelligence) × root depth (stage-dependent)
RAW  = p × TAW                       (management-allowed depletion, p = 0.5)
Dr,t = clamp(Dr,t-1 + Kc·ET₀ − 0.8·rain − irrigation, 0, TAW)
```

* **Kc / stage** come from the existing `crop_profiles` knowledge base
  (`get_current_stage_for_crop`), so all 40+ crops work out of the box.
* **ET₀ + rainfall** (past 14 days + 7-day forecast with rain probabilities)
  come from one cached Open-Meteo call
  (`climate_service.get_water_balance_series`).
* **Soil capacity** comes from the field's Soil Intelligence profile
  (`water_holding_capacity`, mm/m); a loam default with an explicit
  reasoning note (and lower confidence) is used when no profile exists.
* **Applied water**: completed planner irrigation tasks reset the balance
  (assumed refill until amount capture lands).

Decision: compare depletion to the RAW stress trigger, **net of
probability-weighted forecast rain** — the engine explicitly answers "should I
wait for that storm?":

| Action | When |
| --- | --- |
| `irrigate_now` | depletion ≥ RAW and imminent rain won't fix it — includes mm + minutes |
| `delay_rain_expected` | ≥60%-probable rain within 2 days pulls depletion back under RAW |
| `irrigate_soon` | trigger will be crossed within ~2 days |
| `monitor` / `not_needed` | soil water adequate; includes next review date |

Confidence (`high`/`medium`/`low`) reflects data completeness: soil profile
present, ET₀ coverage, forecast probabilities, and whether a refill event
anchored the balance to a known state. A future soil-moisture probe reading
(`measured_soil_moisture_depletion_mm` on `IrrigationInputs`) overrides the
modelled depletion and pins confidence high — that is the sensor integration
point, already wired through.

## Architecture

* `engine.py` — pure decision core; deterministic; tested in
  `tests/test_irrigation_engine.py`. New data sources extend
  `IrrigationInputs` without touching consumers.
* `service.py` — assembles inputs from fields/soil/weather/planner;
  `ensure_planner_task` materialises actionable results as AI planner tasks
  (idempotent: one open AI irrigation task per field per day).
* `irrigation_routes.py` — REST surface.

## Surfaces

* `GET /fields/{id}/irrigation/recommendation` — field detail / planner card.
* `GET /irrigation/recommendations` — all planted fields, worst-first; powers
  the climatology decision-support dashboard.
* `POST /fields/{id}/irrigation/apply` — add to planner on demand.
* The notification generator (`generate_irrigation_recommendations`) runs the
  engine daily per field, auto-creates the planner task and notifies through
  the centralized notification service (category `irrigation`).

`/agro/irrigation/{field_id}` (the older Kc heuristic) remains for backward
compatibility; new consumers should use the endpoints above.
