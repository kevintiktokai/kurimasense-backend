# FORCE RLS Rollout Runbook — Sprint 4, Slice 4 (provable tenant isolation)

Goal: constrain **even the backend owner role** to the caller's tenant(s), so a
bank/lender reviewer can be shown that cross-tenant data access is impossible at
the database layer — not just in application code.

This runbook covers the **gated** enforcement steps. The reversible groundwork is
already shipped:

- ✅ **Migration 008** — `app_tenant_ids()` GUC accessor + per-tenant `ts_*`
  policies on the 12 tenant-scoped tables. Applied **without** FORCE, so the
  running app is unaffected (owner bypasses non-forced RLS). Fully reversible
  (rollback block in the migration).
- ✅ **`tenancy.tenant_scoped_connection(user_id)`** — the enforcement primitive.
  Sets `app.tenant_ids` transaction-locally (`set_config(..., true)`), so it can
  never leak across pooled-connection checkouts. Inert until FORCE is on.

Everything below is **NOT yet done** and requires explicit approval + a soak.

---

## Security invariant (read first)

`app.tenant_ids` must **only ever** be settable server-side, by the backend, from
a value derived from a verified JWT (`fetch_tenant_context`). It must **never** be
settable by a client. Concretely:

- Do **not** expose `set_config` / a GUC-setting RPC to the `anon` or
  `authenticated` roles via PostgREST.
- The `ts_*` policies are permissive for `public`, but they gate on
  `app_tenant_ids()`, which returns `{}` for any connection that hasn't set the
  GUC — so anon/authenticated PostgREST clients continue to see **zero** rows.
  This safety collapses the moment a client can set the GUC. Guard that boundary.

---

## Step A — Wire the GUC into the request path (behind the primitive)

Migrate tenant-scoped DB reads/writes from bare `get_db_connection()` to
`with tenant_scoped_connection(user_id) as conn:`. Do it **incrementally** —
each endpoint is behavior-identical until FORCE flips, so this can land over
several PRs and soak in prod.

Priority order (highest-value / highest-risk isolation surfaces first):

1. `GET /fields`, `GET /dashboard/init`, single-field reads (already tenant-aware
   in SQL via `field_scope_sql`; wrapping them makes the DB enforce it too).
2. Reconciliation / verification / financial reads (`/tenants/{id}/...`).
3. Writes: `create_field`, input logging, harvest/delivery/disbursement inserts.

Leave **out of scope** (personal, no `tenant_id`): `farm_tasks`, `chat_logs`,
user-level `yield_history`. These need Step B before FORCE.

### Wiring inventory (app.py)

Each site is heterogeneous (early returns, HTTPException raises, mock fallbacks,
finally blocks), so they are wired **one at a time** with a compile check + a
prod smoke test — not as a bulk rewrite.

- [x] `GET /fields` (list) — wired + verified.
- [x] `get_dashboard_stats` (feeds `/dashboard/init`) — wired + verified; also
  fixed a latent connection leak on the success path.
- [ ] `POST /fields/{id}/analyze` (~663) — read for coords + ownership.
- [ ] `GET /fields/{id}/insight` (~728, deprecated) — field+NDVI read.
- [ ] field state / detail reads (~936, ~954, ~1497).
- [ ] `DELETE /fields/{id}` (~1217, ~1239) — **write**; verify commit path with a
  throwaway field, not a real one.
- [ ] tasks field-list (~2277) — list read.
- [ ] AI / agronomy field reads (~3189, ~3382, ~3461, ~3568, ~3684).
- [ ] crop-plan / yield field reads (~3920, ~3964, ~4021, ~4059, ~4120).

All bind `field_scope_sql` params today, so each is behavior-identical after
wrapping until FORCE flips. Line numbers drift as edits land — re-grep
`caller_tenant_ids(user_id)` for the live list.

### Verification for Step A
- Functionally unchanged in prod (FORCE still off). Watch error rates + p95 —
  each wrapped query now runs one extra `set_config` round trip inside its txn.
- Optional: temporarily `ALTER TABLE fields FORCE ROW LEVEL SECURITY` on a
  **staging** DB and run the suite to prove wrapped endpoints still return the
  right rows and un-wrapped ones fail loudly (that's how you find stragglers).

## Step B — Close the personal-data tables

Before FORCE, tables the backend touches that have **no** tenant policy will
deny the owner and break. Decide + add policies:

- `farm_tasks`, `chat_logs` (personal): add an `app.user_id` GUC + a
  `USING (user_id = app_user_id())` policy; set `app.user_id` in
  `tenant_scoped_connection` (already plumbed to set both is trivial).
- `model_calibration` (global model data, no tenant dimension): either keep a
  dedicated **owner-only** service path that is exempt from FORCE (connect as a
  role that isn't forced), or add a deliberate `USING (true)` policy after
  confirming it holds no tenant PII. **Do not** FORCE it until this is decided.
- Audit every table the backend writes to for a matching policy — a missing
  policy under FORCE is a hard failure, not a silent row-filter.

## Step C — Drop the `user_id` fallback (irreversible)

Only after Steps A–B are in prod and verified:

1. Remove the `OR user_id = %s::uuid` fallback from `field_scope_sql` and every
   migrated query (they now rely on `tenant_id` + the GUC).
2. `ALTER TABLE fields DROP COLUMN user_id;` (migration). Irreversible — take a
   backup / snapshot first.

## Step D — FORCE (the cut-over)

Per table, once its policy + wiring are proven:

```sql
ALTER TABLE public.fields FORCE ROW LEVEL SECURITY;
-- ... repeat per tenant-scoped table ...
```

Roll out **table by table**, not all at once, verifying after each. Keep the
`ALTER ... NO FORCE ROW LEVEL SECURITY` rollback one command away.

### Go / no-go
- All tenant-scoped reads/writes go through `tenant_scoped_connection`.
- Load test: p95 latency acceptable with the per-txn `set_config` overhead.
- Negative test: a request carrying tenant A's JWT cannot read tenant B's rows
  even with a crafted body/id (should 404/empty, never leak).

### Rollback
`ALTER TABLE <t> NO FORCE ROW LEVEL SECURITY;` immediately restores owner-bypass.
Policies + the GUC helper can stay (they're inert without FORCE).

---

## Status

- [x] Migration 008 (policies, no FORCE) — applied to prod, app unaffected.
- [x] `tenant_scoped_connection` primitive — shipped, inert until FORCE.
- [ ] Step A — incremental endpoint wiring (soak).
- [ ] Step B — personal-table + model_calibration policies.
- [ ] Step C — drop `fields.user_id` (irreversible, approval required).
- [ ] Step D — per-table FORCE cut-over (approval + load test required).
