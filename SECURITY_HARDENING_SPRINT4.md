# Security Hardening Checklist — Sprint 4

Living checklist of database/auth security findings to address during Sprint 4
("Verification + reconciliation, Sentinel-1 SAR, **RLS hardening**"). Sourced
from the Supabase advisor run on the live `kurimasense` project
(`cqyxcpbdpvsrksilczmv`) on 2026-06-26, plus CLAUDE.md Appendix C.

Severity legend: 🔴 critical · 🟠 do in Sprint 4 · 🟡 review/accept · ⚪ manual/dashboard

---

## Already done (interim posture, pre-Sprint-4)
- [x] **Deny-by-default RLS** on 15 sensitive backend-only tables (migrations 004, 005).
      Anon/authenticated keys denied; backend (postgres owner / service_role) bypasses
      RLS (no `FORCE`). Closes the public REST/GraphQL data-exposure hole.
- [x] **`match_documents` search_path pinned** (migration 006) — fixes the mutable
      search_path WARN on the RAG vector-search function.

---

## Sprint 4 — provable tenant isolation (the real RLS work)
- [x] 🟠 **Prerequisite (Workstream 3.5):** migrated the consumer `fields`
      endpoints from `fields.user_id` to tenant-aware scoping (`field_scope_sql`,
      `user_id` fallback retained). Soak verified in prod. Dropping `fields.user_id`
      is the gated Step C below.
- [x] 🟠 **Per-tenant RLS policies added (migration 008), `FORCE` deferred.**
      `app_tenant_ids()` GUC accessor + `ts_*` policies on the 12 tenant-scoped
      tables (`tenants`, `tenant_members`, `growers`, `fields`, `daily_logs`,
      `field_inputs`, `harvest_records`, `yield_projections`, `grower_contracts`,
      `input_disbursements`, `deliveries`, `scouting_observations`). Applied
      **without** FORCE → owner still bypasses → **zero behavior change**, fully
      reversible. Anon/authenticated still see zero rows (`app_tenant_ids()` = `{}`
      when the GUC is unset). Enforcement primitive shipped:
      `tenancy.tenant_scoped_connection(user_id)` (transaction-local GUC, leak-safe).
- [ ] 🟠 **`FORCE ROW LEVEL SECURITY` cut-over** — gated. Requires incremental
      endpoint wiring to `tenant_scoped_connection`, policies for the personal
      tables (`farm_tasks`/`chat_logs`) + `model_calibration`, dropping
      `fields.user_id`, a load test, and explicit approval. **Full runbook:**
      `docs/rls_force_runbook.md`.
      - Security invariant: `app.tenant_ids` must only ever be set server-side by
        the backend; never expose a GUC-setting path to clients (see runbook).

## Auth configuration (manual, Supabase dashboard)
- [ ] ⚪ **Enable leaked-password protection** (HaveIBeenPwned check).
      Dashboard → Authentication → Policies/Password. One toggle, no migration.
      Ref: https://supabase.com/docs/guides/auth/password-security
- [ ] 🟡 Review password strength / MFA options while in that screen.

## PostGIS / extensions (low priority, accept-or-relocate)
- [ ] 🟡 **`st_estimatedextent` SECURITY DEFINER executable by anon/authenticated**
      (3 overloads). These are **PostGIS built-ins** exposed via PostgREST RPC, a
      side effect of PostGIS living in `public`. Do NOT revoke/alter them directly
      (extension-managed; reverts on upgrade, risks breaking spatial features).
      Addressed properly only by relocating the extension (below) or accepting.
- [ ] 🟡 **`extension_in_public`: `postgis`, `vector`** installed in `public`.
      Relocating is disruptive (type/operator resolution, references) and Supabase
      installs them in `public` by default. **Recommendation: accept** unless a
      reviewer requires otherwise; if required, move to a dedicated `extensions`
      schema in a carefully tested migration.

## Intentional / no-action (documented so they aren't "fixed" by mistake)
- [ ] 🟡 **`rls_policy_always_true` on `subscribers` (`Allow public inserts`)** —
      INTENTIONAL: the landing-page waitlist needs anonymous INSERT. The policy only
      permits INSERT (no SELECT of others' rows), so it is not a data-exposure risk.
      *Do not remove* (breaks signups). Optional: add lightweight abuse protection
      (e.g. a `CHECK` on email format, or rate limiting at the edge).
- [x] **`spatial_ref_sys` RLS disabled** (the lone remaining `rls_disabled_in_public`
      ERROR) — PostGIS public reference data (SRID/EPSG), extension-managed.
      Intentionally left: enabling RLS risks breaking spatial queries for no gain.

## GraphQL exposure (resolved by RLS, monitor)
- [ ] 🟡 `pg_graphql_*_table_exposed` WARNs (26 tables): mooted by RLS — with RLS on
      and no permissive policy, anon/authenticated read zero rows via GraphQL too.
      Revisit if pg_graphql is not used (could disable the GraphQL endpoint entirely).

---

### How to apply the prepared migrations to the live DB
```bash
DATABASE_URL="<render db url>" python migrate_enable_rls.py        # 004 + 005 (done)
DATABASE_URL="<render db url>" python migrate_pin_search_path.py   # 006
```
Or via the Supabase MCP `apply_migration` (idempotent; safe to re-run).
