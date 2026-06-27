# Sprint 4 Notes — Verification, Reconciliation, Resilience

Sprint 4 has four workstreams of differing risk. Sequencing (lowest-risk,
highest-value first; matches CLAUDE.md ordering):

1. **Reconciliation engine** — side-marketing flags. ✅ *this slice*
2. **Verification engine** — self-report × disbursement × NDVI response. (next)
3. **Sentinel-1 SAR ingestion** — close data-gap G2 (persist
   `sar_vv_db`/`ndre`/`ndmi`/`savi`; wet-season floor). (infra)
4. **Postgres RLS provable isolation** — must follow **Workstream 3.5** (migrate
   the ~25 `fields.user_id` endpoints, then drop `fields.user_id`). See
   `SECURITY_HARDENING_SPRINT4.md`. (largest/riskiest — last)

---

## Slice 1 — Reconciliation engine (done)
The institutional "killer capability": detect growers the satellite says produced
the crop but who under-delivered to the contracting buyer (side-marketing) — the
evidence base for delivery-risk accountability and premium pricing.

### Pure engine — `services/reconciliation/compute.py` (no I/O, Hard Rule 1)
Per grower-season, compares:
- **contracted** (obligation, `grower_contracts`)
- **satellite-implied / projected** (Sprint 1 model output — *read*, never recomputed)
- **delivered** (`deliveries`)

`reconcile_grower()` →
- `expected` = contracted (else projected when no contract)
- `delivery_gap_pct` = (expected − delivered)/expected
- **corroboration**: projected ≥ expected×0.8 ⇒ satellite says they grew it
- flag: gap ≥ 40% **and** corroborated → `flag` (side-marketing), with
  `side_marketing_volume_tonnes` = produced − delivered; gap ≥ 40% but **not**
  corroborated → `watch` ("production shortfall, not diversion"); gap ≥ 20% →
  `watch`; else `none`. Side-marketing volume is only counted at watch/flag.

`summarize()` rolls up flagged/watch counts + total side-marketing tonnes.
Tunables: `WATCH_GAP_PCT=20`, `FLAG_GAP_PCT=40`, `PRODUCTION_CORROBORATION=0.8`.

### Read API — `reconciliation_routes.py`
`GET /tenants/{tenant_id}/reconciliation` — tenant-scoped (admin / tenant_ids),
403 on cross-tenant. Loads contracted (latest season per grower), delivered
(sum), and satellite-implied (latest live `yield_projections` × `size_hectares`
per field, summed per grower via a LATERAL join), runs the engine, returns
growers sorted most-concerning first + a portfolio summary.

### Tests
`tests/test_reconciliation.py` (9, hand-computed) + `tests/test_reconciliation_route.py`
(4, tenant access). No migration required (reuses existing tables). Full suite
254 pass; no regressions.

### Notes / follow-ups
- Deliveries are summed across all of a grower's deliveries (v1); season-scoping
  via `contract_id`/season is a refinement once multi-season books exist.
- Satellite-implied volume relies on `yield_projections` being populated (the
  field-state snapshot hook + backtest). Sparse projections ⇒ projected=0 ⇒ the
  grower reads as "production shortfall" rather than side-marketing (conservative,
  avoids false accusations).

## Slice 2 — Verification engine (planned)
For each field: did a logged/disbursed input produce an NDVI response? Compare
`input_disbursements`/`field_inputs` dates against the `daily_logs` NDVI
trajectory in the following window; flag "input not reflected in canopy" (possible
non-application/diversion). Pure function over (input events, NDVI series) +
read API. No migration.

## Slice 3 — Sentinel-1 SAR (planned, infra)
Persist `sar_vv_db`/`ndre`/`ndmi`/`savi` (currently computed-not-stored, G2).
Needs a `daily_logs` column migration + a CDSE Sentinel-1 fetch path; gives a
wet-season floor when optical NDVI is cloud-blocked.

## Slice 4 — RLS provable isolation (planned, last)
Per CLAUDE.md: finish Workstream 3.5 first (migrate ~25 `fields.user_id`
endpoints to `tenant_id`, then drop `fields.user_id`), then `FORCE ROW LEVEL
SECURITY` + per-tenant policies. Tracked in `SECURITY_HARDENING_SPRINT4.md`.
