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
- [x] `POST /fields/{id}/analyze` — coords + ownership read.
- [x] `GET /fields/{id}/insight` (deprecated) — field+NDVI read.
- [x] `GET /fields/{id}/history` — two field reads, one connection.
- [x] `DELETE /fields/{id}` — write; verified via throwaway create→delete. Also
  fixed a pre-existing bug: it called the non-existent `_cache_invalidate_prefix`,
  so every delete 500'd *after* removing the field.
- [x] `_fetch_fields_and_tasks` (feeds `/ai/insights`) — fields scoped;
  farm_tasks stays user-scoped.
- [x] `POST /fields/{id}/yield` — field + profiles read on one scoped connection.
- [x] `/agro/fertilizer|ipm|irrigation|harvest|crop-intelligence` — top field
  read scoped. Also fixed pre-existing tuple-cursor 500s (default cursor +
  by-key access) → RealDictCursor.
- [x] `/ai/growth-stage`, `/ai/disease-risk` — field reads scoped.
- [x] `GET /fields/{id}/yield-history` — ownership + history reads scoped.
- [x] `/ai/proactive-alerts/{id}` — field read scoped (scattered closes removed).
- [x] `POST /fields/{id}/yield-history` (`record_yield`) — ownership read +
  yield_history write wrapped in one tenant-scoped transaction.

**16 of 16 tenant-scoped sites wired in app.py.** All bound `field_scope_sql`
params until the drop; behavior-identical until FORCE flips.

### Straggler audit + full wiring (July 2 2026, second pass)

The "16/16 complete" above covered **app.py only**. A repo-wide audit (every
`get_db_connection()` call site cross-referenced against the RLS-target tables)
found ~30 more bare sites across 13 files — any of which would have returned
zero rows / hard-failed under FORCE. All are now wired via `tenancy.
arm_rls_gucs(conn, user_id, tenant_ids)` (the raw arming primitive, extracted
from `tenant_scoped_connection` for call sites that manage their own connection
lifecycle and already hold tenant ids from `AuthenticatedUser`):

- **Institutional route files**: `financial_routes` (7 sites), `reconciliation_routes`,
  `verification_routes` (2), `outcome_routes` (4), `scouting_routes` (2),
  `grower_routes` (6), `portfolio_routes`→`services/portfolio/aggregate`.
  Tenant-path routes union the already-authorized path tenant into the GUC so
  admins (who may not be members) keep access.
- **Field-state pipeline**: `resolve_access` + the `_q` best-effort fetchers in
  `services/field_state/aggregator` (scope = caller tenants ∪ resolved field's
  tenant); `services/calibration/snapshot` (background write, armed with the
  field's tenant as `service:yield_snapshot`).
- **app.py second wave**: `create_field` (arm after owner-tenant resolution;
  re-arm after the mid-handler commit for the daily_logs insert),
  `trigger_sentinel_analysis` (tenant threaded from the authorized caller),
  `log_input`, 4 chat closures (`chat_logs`, user-GUC only), 5 farm_tasks
  handlers, `get_agricultural_metrics`, `get_yield_analytics`.
- **Personal-data paths**: `chat_session_routes` (5 sites) and
  `ai_brain.ConversationMemory` (3 methods) arm the user GUC only (no tenant
  lookup needed); `deps.get_field_context` / `deps.resolve_coordinates` use
  `tenant_scoped_connection`; `database.get_recent_field_activity` and
  `yield_model.get_field_ndvi_history` take optional caller identity, threaded
  from their endpoints.

Verified: compile clean + 277 unit tests pass (9 failures are pre-existing
env-dependent tests needing DATABASE_URL).

### Bootstrap exemption (design decision — read before FORCE)

`tenants`, `tenant_members` (and `profiles`) must **NEVER be FORCEd**:

1. `auth_roles.fetch_tenant_context` reads `tenant_members` to *derive* the
   GUC value — forcing it is a chicken-and-egg that locks every user out.
2. `_resolve_or_create_owner_tenant_id` (create_field) INSERTs a brand-new
   tenant + membership; a WITH CHECK keyed on the GUC can never contain a
   tenant id that doesn't exist yet.
3. `me_routes` / `admin_routes` read/manage these tables cross-tenant by
   design (admin console is admin-token-gated).

These tables hold membership/identity rows, not farm data; the deny-by-default
posture for PostgREST clients (anon/authenticated see zero rows) is preserved
by the existing non-forced policies. `auth_roles.py`, `me_routes.py` and
`admin_routes.py` therefore intentionally stay on bare connections.

### Known FORCE consequences (accepted)

- **403-vs-404 tightening**: `resolve_access`-style unfiltered lookups can't
  see cross-tenant rows under FORCE, so probes resolve 404 instead of 403.
  Arguably better (no existence oracle).
- **Admin cross-tenant field reads** return 404 under FORCE unless the admin is
  a member (or the path tenant is unioned in, which tenant-path routes do). A
  SECURITY DEFINER resolver would be needed for unrestricted admin field
  access — deferred until actually required.
- **Global service paths** (`/admin/calibration/recompute`,
  `trigger_sentinel_analysis` fallback) use `arm_rls_gucs_all_tenants` — a
  deliberate all-tenant grant, only reachable from admin-gated/internal code.
  It reads `tenants` to enumerate ids, which works precisely because of the
  bootstrap exemption.

Step B groundwork also shipped:
- `tenant_scoped_connection` now sets **both** `app.tenant_ids` and `app.user_id`
  (transaction-local).
- `migrations/010_rls_personal_policies.sql` drafted: `app_user_id()` +
  type-robust `us_*` policies on `farm_tasks` / `chat_logs` / `yield_history`.
  Apply during the FORCE step (safe/no-op until FORCE). `model_calibration`
  decision still open.

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
- `model_calibration` — **DECIDED (July 2 2026)**: it holds only aggregate
  model-error statistics per segment (no ids/names/volumes/prices → no tenant
  PII), and is read cross-tenant by design. `migrations/
  011_rls_model_calibration_policy.sql` adds the deliberate `USING (true)`
  policy; apply it alongside 010. Migration 010 was also extended to cover
  `chat_sessions` (post-dates the original draft).
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
- [x] Step A — app.py wiring (16 sites) + repo-wide straggler audit and full
      wiring (~30 more sites across 13 files, July 2 2026). Needs a prod soak
      after deploy.
- [x] Step B (code/migrations staged) — 010 extended (`chat_sessions`), 011
      drafted (`model_calibration` USING(true)); bootstrap exemption decided
      and documented. **Migrations not yet applied** (blocked on Supabase MCP
      approval in the July 2 session — apply 010 + 011 first thing next
      session; both are inert until FORCE).
- [ ] Step C — drop `fields.user_id` (irreversible). ORDER MATTERS: the
      `field_scope_sql` fallback-removal code change must be merged to main
      AND deployed on Render BEFORE the column drop, or every fields query
      500s on the missing column. Snapshot first:
      `CREATE TABLE _backup_fields_user_id AS SELECT id, user_id FROM fields;`
- [ ] Step D — per-table FORCE cut-over. Checklist per table:
      `ALTER TABLE public.<t> FORCE ROW LEVEL SECURITY;` → hit the live
      endpoints that read/write it with a real token (expect identical
      results) → negative test (tenant A token must NOT see tenant B rows) →
      next table. NEVER force `tenants` / `tenant_members` / `profiles`
      (bootstrap exemption above). Rollback is one command:
      `ALTER TABLE <t> NO FORCE ROW LEVEL SECURITY;`
      Suggested order: `scouting_observations` (lowest traffic) →
      `grower_contracts` / `input_disbursements` / `deliveries` /
      `harvest_records` / `yield_projections` → `growers` → `field_inputs` /
      `daily_logs` → `fields` (highest blast radius) → personal tables
      (`farm_tasks`, `chat_logs`, `chat_sessions`, `yield_history`) →
      `model_calibration`.
