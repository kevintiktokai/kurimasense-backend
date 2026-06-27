# Sprint 2 Discovery & Design Notes — Financial / Exposure Layer

Produced: 2026-06-26. Builds on Sprint 1 (outcome loop). Backend-only.

## Goal (from CLAUDE.md)
Financial/contract layer + exposure engine producing **portfolio $ exposure, by week**.
- Tables: `grower_contracts`, `input_disbursements`, `deliveries`.
- Engine: per-grower `net_exposure = input_credit_value − (projected_volume × price × repayment_likelihood)`.
- Portfolio rollup to `$`, weekly.
- `GET /tenants/{id}/exposure`.
- `repayment_likelihood` v1 = f(KurimaScore + delivery history).

## Data sources (confirmed, reuse — never recompute)
- **KurimaScore + yield projection per field:** `services.field_state.aggregator.assemble_field_state(field_row, daily_logs=..., ...)` returns a `FieldState` with `kurima_score.score` (0–100) and `yield_projection.projected_tonnes_per_ha`. This is exactly how `services/portfolio/aggregate.py:254–284` already reads per-field score/projection. The exposure engine **reads** these (Hard Rule 1) — it never recomputes NDVI/score.
- **Projected volume (tonnes) per field** = `projected_tonnes_per_ha × size_hectares`. Summed across a grower's fields → grower projected volume.
- **Fields/growers/daily_logs load pattern:** copied from `aggregate.py` (load fields for tenant, batch-load `daily_logs` by `field_id = ANY(...)`).
- **Tenant scoping:** `get_authenticated_user` → `AuthenticatedUser` (`tenant_id`, `tenant_ids`, `role`). 403-vs-404 pattern as in Sprint 1 / `portfolio_routes.py`.

## Schema design (the three tables — `db/migrations/003_financial_exposure.sql`)
- `grower_contracts`: tenant_id, grower_id, season_year, crop_type, contracted_volume_tonnes, contract_price_per_tonne, input_credit_value, status, created_at.
- `input_disbursements`: tenant_id, grower_id, contract_id (FK), disbursement_date, input_type, quantity, unit, credit_value, created_at.
- `deliveries`: tenant_id, grower_id, contract_id (FK), field_id, delivery_date, volume_tonnes, price_per_tonne, quality_grade, value_usd, created_at.

All idempotent (`CREATE TABLE/INDEX IF NOT EXISTS`), UUID PKs via `gen_random_uuid()`, timestamptz, FKs to `tenants`/`growers`/`fields`/`grower_contracts`. No drops/renames.

## Exposure engine (pure, `services/exposure/compute.py`, no I/O)
- `input_credit_value` per grower = Σ `input_disbursements.credit_value` (actual credit extended), falling back to `grower_contracts.input_credit_value` when no disbursements logged.
- `repayment_likelihood(score, delivery_ratio) -> float ∈ [0,1]` v1:
  - `score_fraction = score/100`.
  - `delivery_ratio` = historical Σ delivered_volume / Σ contracted_volume (prior seasons). `None` if no history.
  - With history: `0.6*min(1, delivery_ratio) + 0.4*score_fraction`. Without: `score_fraction`. Clamp [0,1].
  - **v1 heuristic** — documented as such; learned later (Sprint 4).
- `grower_net_exposure(input_credit_value, projected_volume, price, repayment_likelihood) -> float`
  = `input_credit_value − projected_volume*price*repayment_likelihood`. Positive = capital at risk.
- `portfolio_weekly(grower_exposures) -> weekly buckets` keyed by the ISO-week of each grower's **expected harvest** (planting_date + days_to_maturity), summing net_exposure → `$ by week`.

## Decisions / assumptions (flagged)
1. `input_credit_value` taken from actual disbursements (most accurate exposure), contract value as fallback. 
2. Weekly rollup buckets by **expected harvest week** (when exposure resolves), not calendar-now. Trend-over-time storage is **out of scope** (Sprint 2 is the 3 tables above; no `exposure_snapshots` table) — the endpoint returns the current weekly distribution.
3. `repayment_likelihood` weights (0.6/0.4) are a deliberate v1 heuristic; flagged for replacement by a learned model in Sprint 4.
4. Price for projected (unsold) volume = the grower's contract `contract_price_per_tonne`; if multiple contracts, the season's contract for that crop.

## Non-goals respected
No farm accounting, e-commerce, payment processing. Contracts/disbursements/deliveries are exposure inputs, not a ledger product.
