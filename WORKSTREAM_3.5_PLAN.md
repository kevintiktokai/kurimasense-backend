# Workstream 3.5 — uniform tenant scoping → provable RLS

Prerequisite for Sprint 4's RLS isolation (per CLAUDE.md). Migrates the consumer
`fields` endpoints from `user_id` filtering to **tenant-aware** filtering, then
(gated, last) drops `fields.user_id` and adds `FORCE ROW LEVEL SECURITY` +
per-tenant policies.

This touches **live consumer endpoints**, so it is staged and
**behavior-preserving**, with the `user_id` fallback retained until the final
drop. Each batch ships with the helper and review; endpoint-level assertions need
a full env (app.py imports cryptography, broken in the sandbox — see
`tests/test_tenancy.py`).

## Helper (shipped) — `tenancy.py`
- `caller_tenant_ids(user_id)` → tenant ids via `fetch_tenant_context` ([] safe).
- `field_scope_sql(alias)` → `"(alias.tenant_id = ANY(%s::uuid[]) OR alias.user_id = %s::uuid)"`,
  bound with `(tenant_ids, user_id)`. For a consumer (personal tenant,
  `fields.user_id` set) results are identical; officers gain tenant access; the
  fallback prevents any regression if a row lacks `tenant_id`.

## Scope
**In scope** — `fields`-table access (and field-scoped reads via the field FK).
Dropping `fields.user_id` depends only on these.
**Out of scope** — `farm_tasks`, `chat_logs`: **no `tenant_id` column**; they are
inherently personal data and stay `user_id`-scoped (a separate decision/migration
if ever shared across a tenant). The ~5 `farm_tasks` and ~3 `chat_logs` sites in
the grep are therefore NOT part of Workstream 3.5.

## `fields` access inventory (app.py)
| Line(s) | Endpoint / purpose | Pattern |
|---|---|---|
| 437 `GET /fields` | list fields | `WHERE f.user_id` → **migrated (batch 1)** |
| ~645,710,918,934 | field detail / state / analyze reads | `id = %s AND user_id = %s` |
| ~1199,1222 | delete field | `id = %s AND user_id = %s` |
| ~1375,2258 | dashboard/init + tasks field list | `WHERE f.user_id` |
| ~1478 | field by id | `id = %s AND user_id = %s` |
| ~3170,3363,3442,3549,3665 | AI/agronomy field reads | `id = %s AND user_id = %s` |
| ~3901,3945,4002,4040,4101 | crop-plan/yield field reads | `WHERE id = %s AND user_id = %s` |
| ~3569 | field_inputs by field+user | scope via field |

(~16 single-field checks + 3 list sites.)

## Batches
1. **`GET /fields` list** — ✅ done (proof-of-pattern; `field_scope_sql`).
2. **Single-field ownership reads** (~16 `id = %s AND user_id = %s` sites) — ✅ done.
   All migrated to `id = %s::uuid AND (tenant_id = ANY(%s::uuid[]) OR user_id = %s::uuid)`
   with `caller_tenant_ids(user_id)`. Covers field detail/state/analyze, delete,
   AI/agronomy reads, crop-plan/yield reads.
3. **Remaining list sites** (dashboard-init, tasks-field list) — ✅ done. Plus the
   field-scoped `yield_history` read is now scoped by `field_id` after the
   (tenant-aware) field access check, so officers see a grower's history instead
   of an empty list.
4. **Soak** — deploy, verify consumers + institutional officers in prod. (pending)

### Intentionally NOT migrated
- `farm_tasks`, `chat_logs`, user-level `yield_history` aggregates — personal data,
  **no `tenant_id` column**; stay `user_id`-scoped.
- `SELECT variety FROM fields WHERE id = %s` (one internal read) — has no `user_id`
  filter today; unscoped internal lookup, left as-is (not a user_id→tenant site).

## Gated final steps (irreversible — explicit approval + live verification)
5. **Drop the `user_id` fallback** from all migrated `fields` queries, then
   `ALTER TABLE fields DROP COLUMN user_id` (migration). Only after batches 1–4
   are in prod and verified.
6. **`FORCE ROW LEVEL SECURITY` + per-tenant policies** on `fields` (and
   field-scoped tables). Design note: the backend connects as the `postgres`
   **owner**, which bypasses RLS even with policies — so provable enforcement
   needs one of: (a) the backend sets a per-transaction GUC
   (`SET LOCAL app.tenant_ids = …`) and policies read `current_setting(...)`, with
   `FORCE RLS` on the owner; or (b) the backend connects as a dedicated non-owner
   role. (a) is lower-churn but requires wiring `SET LOCAL` into the per-request
   connection. This is the largest change and must be load-tested.

## Status
Batches 1–3 shipped: **all consumer `fields` access is tenant-aware** (with the
`user_id` fallback). Next is soak/verification in prod, then the gated
irreversible steps (5–6). The app-layer change is reversible (fallback retained);
nothing is dropped yet.
