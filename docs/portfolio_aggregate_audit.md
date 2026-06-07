# Portfolio Aggregate Endpoint — audit (MVP PR 2)

One-page input for `GET /portfolio/aggregate` (read-only, institutional-only,
reuses the field-state aggregator). No migrations, no writes.

## 1. Aggregator reuse
- **`services/field_state/aggregator.assemble_field_state(*, field_row, requester_id,
  daily_logs, …, enforce_owner=True)` → `FieldState`** is the **pure, no-I/O**
  path. Given a field row + its `daily_logs` it computes the KurimaScore and
  derived alerts with **no network calls**. This is what the portfolio uses
  (one batched DB read for all fields, then assemble per field) — fast and
  reuses the canonical scoring. We do **not** use `build_field_state` here (it
  does per-field climate/yield/alert network calls — too slow for 40 fields).
- Relevant `FieldState` fields consumed:
  - `kurima_score.{score:int, label, color, recommended_action, primary_driver}`
  - `alerts: List[Alert]` where `Alert.{severity('low'|'medium'|'high'), category, headline, recommended_action}`
  - `indices.current.{observation_quality('good'|'fair'|'stale'|'none'), as_of_date}`
  - `season.{days_since_planted, planted_date}`

## 2. "Awaiting data" detection (important)
`assemble_field_state` **always** returns an integer `kurima_score` (with no
observations the satellite component defaults to neutral). So a non-null score is
*not* a reliable "has data" signal. The reliable signal is
**`indices.current.observation_quality == 'none'`** (⟺ the field has zero
`daily_logs`). The portfolio treats that as `kurima_score = None` /
`urgency = 'awaiting_data'`. (The live demo tenant currently has 0 `daily_logs`
until the Render backfill runs, so today every field is `awaiting_data`.)

## 3. Tenant context / access
- `AuthenticatedUser` (Workstream 3) carries `role`, `tenant_id`, `tenant_ids`.
- `auth_roles.get_authenticated_user` resolves these; `user_can_access_field` /
  `resolve_access` already grant institutional users via tenant membership.
- Endpoint authz: institutional → own tenant only; admin → any (via `?tenant_id`);
  others → 403.

## 4. Schema realities the endpoint must handle
- `fields` has **no `district` column** — district is embedded in demo field
  names (`DEMO_SEED: <first> - <District> - <crop>`); parsed best-effort, else null.
- `fields.natural_region` exists (added in the seeding PR).
- `fields.size_hectares` (double), `grower_id` (uuid, nullable).
- A field whose `grower_id` points to a **soft-deleted** grower must still appear,
  with `grower_name = null` → use `LEFT JOIN growers g ON g.id=f.grower_id AND
  g.deleted_at IS NULL` (do **not** drop the field).

## 5. Decisions
- **Band label/colour:** reuse the aggregator's values straight off
  `FieldState.kurima_score` (single source of truth) rather than re-defining a
  colour table. Summary distribution uses the score thresholds 85/70/55/40/25.
- **`primary_concern`:** prefer the top `alert.headline` + `alert.recommended_action`;
  else the score-based fallback; else the awaiting-data message. (Note our `Alert`
  field is `headline`, not `title` as the prompt sketch assumed.)
- Performance: one `tenants` read + one `fields` (LEFT JOIN growers) read + one
  batched `daily_logs` read + one batched `field_inputs` count, then pure assemble
  per field. No per-field network → well under 3s for 40 fields.
