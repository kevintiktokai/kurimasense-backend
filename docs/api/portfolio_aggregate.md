# `GET /portfolio/aggregate`

Single round-trip payload for the institutional **Portfolio › Today** screen:
tenant info, portfolio summary stats, and a worst-first priority list of every
field in the tenant. **Read-only.** Reuses the field-state aggregator.

## Auth
Supabase session (`Authorization: Bearer <jwt>`).
- **institutional** → own tenant only.
- **admin** → any institutional tenant via `?tenant_id=<uuid>` (defaults to own).
- anyone else → `403`.

## Query params
| param | type | notes |
|---|---|---|
| `tenant_id` | uuid (optional) | Admin override. Institutional callers passing a *different* tenant → `403`. |

## Responses
- `200` → `PortfolioAggregateResponse` (below)
- `400` — no tenant in scope (institutional user without a tenant)
- `403` — non-institutional, or cross-tenant attempt
- `404` — tenant missing or not institutional

## Urgency taxonomy (sort: worst actionable first)
Derived from the field's KurimaScore:

| urgency | score | sort rank |
|---|---|---|
| `critical` | < 25 | 0 |
| `high` | 25–39 | 1 |
| `medium` | 40–54 | 2 |
| `low` | ≥ 55 | 3 |
| `awaiting_data` | no observations yet | 4 (**last** — not actionable) |

Within a bucket: KurimaScore ascending, then `size_hectares` descending (bigger
exposure first), then `field_id` (deterministic).

## KurimaScore bands
Reused from the aggregator's `classifiers.label_for_score` (single source of
truth) — `Thriving`/`Strong`/`Adequate`/`Stressed`/`Distressed`/`Critical` at
85/70/55/40/25 thresholds, each with its canonical hex colour. `kurima_label` /
`kurima_color` are taken straight off the field's computed state.

## "Awaiting data"
`assemble_field_state` always returns an integer score, so the reliable
no-data signal is `indices.current.observation_quality == 'none'` (zero
`daily_logs`). Such fields report `kurima_score = null`, `urgency =
'awaiting_data'`, and are counted in `summary.fields_awaiting_data` and excluded
from `average_kurima_score`.

## Performance
One `tenants` read + one `fields` (LEFT JOIN growers) read + one batched
`daily_logs` read + one batched `field_inputs` count, then pure per-field
assembly (no network). **Measured: ~29 ms for 40 fields** (assembly only).

## Example (representative)
> The live demo tenant currently has 0 `daily_logs` (Sentinel backfill not yet
> run), so today every field is `awaiting_data`. Below is a mixed example.

```json
{
  "tenant": { "id": "6fd723f4-…", "name": "Test Institution", "institutional_type": "buyer" },
  "summary": {
    "total_fields": 40, "total_growers": 26, "total_hectares": 156.0,
    "score_distribution": { "thriving": 0, "strong": 1, "adequate": 0,
      "stressed": 0, "distressed": 2, "critical": 0, "awaiting_data": 37 },
    "alerts_critical": 0, "alerts_high": 1,
    "average_kurima_score": 45.7, "fields_with_data": 3, "fields_awaiting_data": 37
  },
  "priorities": [
    {
      "field_id": "…", "field_name": "DEMO_SEED: G1 - Bindura - Flue-Cured",
      "grower_id": "…", "grower_name": "Tafadzwa Moyo",
      "district": "Bindura", "natural_region": "II",
      "crop_type": "tobacco_flue_cured", "variety": "KRK26", "size_hectares": 2.5,
      "kurima_score": 35, "kurima_label": "Distressed", "kurima_color": "#D84315",
      "primary_concern": "Significant stress symptoms",
      "recommended_action": "Field officer visit recommended within 72 hours",
      "urgency": "high", "days_since_observation": 3,
      "planting_date": "2026-02-01", "days_since_planting": 126
    }
    /* … awaiting_data fields sort last with kurima_score: null … */
  ],
  "generated_at": "2026-06-…T…Z"
}
```

`primary_concern` prefers the field's top alert (`headline` + its
`recommended_action`); otherwise a score-based message; the awaiting-data message
when there are no observations.
