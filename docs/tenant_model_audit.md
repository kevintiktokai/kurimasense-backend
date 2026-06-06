# Tenant Model Audit — Workstream 3 (Block 1)

The load-bearing document for the tenant migration. Today field ownership is
`fields.user_id`; this works for consumers but cannot express the institutional
case (e.g. Northern Tobacco's 30 officers all needing to see the same 3000
contracted growers' fields). Workstream 3 introduces `tenants` + `tenant_members`
and re-scopes field data from *user* to *tenant*.

**Hard constraint:** existing consumer users must see ZERO behaviour change across
the whole workstream. Every consumer gets a 1-member `consumer` tenant (they are
the `owner`), so `tenant_id`-scoped queries return exactly what `user_id`-scoped
queries returned.

**Scope of Block 1:** audit + schema migrations only. No query/endpoint changes
(Block 2) and no tests beyond migration idempotency (Block 3).

---

## 1. Live schema (Supabase `kurimasense`, read-only)

| table | ownership cols | notes |
|---|---|---|
| `fields` | `user_id` | + `id, name, crop_type, crop, planting_date, transplant_date, is_transplanted, variety, size_hectares, polygon_coordinates, lat, lon, location, health_score, fertilizer_history`. **No `tenant_id`/`grower_id` yet.** |
| `daily_logs` | `field_id`, `user_id` | satellite indices; `user_id` = who triggered ingestion |
| `field_inputs` | `field_id`, `user_id` | fertiliser/input records |
| `farm_tasks` | `user_id`, `field_id` | tasks; `is_ai_generated` |
| `chat_logs` | `user_id`, `field_context_id` | **personal** chat history |
| `user_events` | `user_id` | **personal** analytics |
| `profiles` | `id`, `role`, `institutional_type`, `tenant_name` | (Workstream 1) |

`tenants`, `tenant_members`, `growers` — **do not exist yet** (created by this block).

## 2. `user_id` references (non-test): 168 in `app.py`, plus `database.py` (20),
`deps.py` (15), `ai_brain.py` (15), `admin_routes.py` (15), `auth_roles.py` (10),
`services/field_state/aggregator.py` (7), `schemas.py` (6), `router.py` (3),
`me_routes.py` (1), `tools/generate_advice.py` (1). Categorised below.

`FROM` counts: `fields` ×20, `daily_logs` ×4, `farm_tasks` ×4, `chat_logs` ×3,
`field_inputs` ×1, `profiles` ×2. The dominant field-ownership filter
(`... AND f.user_id = %s::uuid`) appears ~25 times.

---

## 3. Categorisation

### 🟢 MIGRATE TO TENANT — field data
Field ownership and everything hanging off a field must be tenant-scoped so all
members of an institutional tenant share visibility.

**`fields`** — every `WHERE user_id = %s` / `WHERE f.id = %s AND f.user_id = %s`.
- Current: `SELECT ... FROM fields WHERE id = %s::uuid AND user_id = %s::uuid`
- Proposed (Block 2): `SELECT ... FROM fields WHERE id = %s::uuid AND tenant_id = ANY(%s)`
  where the parameter is the caller's tenant id(s) resolved from `tenant_members`
  (a consumer has exactly one). Plus a 403-vs-404 access check identical to the
  aggregator's pattern.
- Backfill makes this transparent for consumers (their tenant owns their fields).

**`daily_logs`, `field_inputs`** — currently filtered/joined via `field_id` + the
field's `user_id`.
- Current: `JOIN fields f ON dl.field_id = f.id WHERE f.user_id = %s`
- Proposed (Block 2): scope by `f.tenant_id` instead of `f.user_id`. The row's own
  `user_id` is retained purely for **attribution** (who ingested/logged it), not
  for access control. No schema change needed on these tables in Block 1 — they
  inherit tenant scope through `fields.tenant_id`.

**`farm_tasks`** — see AMBIGUOUS (leaning tenant).

**Writes** (`INSERT INTO fields/daily_logs/field_inputs/farm_tasks`) — Block 2 will
also stamp `tenant_id` on new `fields` rows (and `grower_id` where applicable);
child tables keep `user_id` for attribution and derive tenant via the field.

### 🔵 KEEP USER-SPECIFIC — personal data (NO tenant scoping)
Scoping these to a tenant would leak personal data between institutional officers.

- **`chat_logs`** (×3 `FROM`, ×2 `INSERT`) — chat history is personal. An officer
  must not read a colleague's conversations. **Keep `WHERE user_id = %s`.**
- **`user_events`** — per-user analytics. Keep user-scoped.
- **`profiles`** + `get_user_language` / preferences / `GET /user` / `GET /me/role`
  — inherently per-user. Keep.
- **`tenant_members`** lookups themselves key on `user_id` (resolving the caller's
  tenant) — correct and required.

### 🟠 AMBIGUOUS
- **`farm_tasks`** — tasks are created by a user against a field. For consumers,
  user == tenant owner, so behaviour is unchanged either way. For institutional
  tenants, a task on a shared field is arguably shared work.
  **Decision (to confirm in Block 2):** scope task *reads* by the field's
  `tenant_id` (so officers see tasks on shared fields), keep `user_id` for
  "assigned/created by" attribution. Tasks with `field_id IS NULL` (farm-wide
  personal tasks) stay user-scoped. Flagged here; the query change lands in Block 2.
- **`ai_brain.py` / `tools/generate_advice.py` `user_id`** — used to build AI
  context (recent activity). These read field data; once field reads are
  tenant-scoped the context naturally follows. No access-control role — safe.

---

## 4. Endpoint categorisation (no changes in Block 1)

All 50 session endpoints are **consumer-only today**. After Workstream 3:

- **Both roles, tenant-scoped (different access rules):** `GET/POST /fields`,
  `DELETE /fields/{id}`, `POST /fields/{id}/analyze`, `GET /fields/{id}/history`,
  `GET /fields/{id}/insight`, `GET /field/{id}/state`, `POST /fields/{id}/yield`,
  `GET/POST /fields/{id}/yield-history`, `GET /dashboard`, `GET /dashboard/init`,
  `GET /yield-analytics`, `POST /inputs`, the `GET /agro/*` and
  `GET /ai/*`/`GET /climate/*` field-scoped endpoints. → scope by tenant.
- **Both roles, KEEP user-specific:** `GET /chat/history`, `POST /chat/send`,
  `POST /chat/v2/*`, `POST /proactive`, `POST /vision/analyze`, `GET /user`,
  `GET /me/role`. → stay user-scoped.
- **Institutional-only (new in Block 2/3):** grower CRUD, portfolio aggregates.
- **Admin-only:** existing `X-Admin-Token` endpoints (no tenant needed).

## 5. daily_logs / field_inputs / farm_tasks — explicit finding (Step A.4)
All three carry a `user_id`. **None of them should be access-controlled by their
own `user_id` after Workstream 3** — they must be reached through their parent
`fields.tenant_id`, otherwise an institutional officer would be blocked from a
colleague's ingestion/inputs on a shared field. Their `user_id` is downgraded to
*attribution only*. `chat_logs.user_id` and `user_events.user_id` are the
exception — those stay access-controlling because the data is personal.

## 6. Migration plan (this block)
1. `migrate_create_tenants.py` — `tenants` + `tenant_members`.
2. `migrate_backfill_consumer_tenants.py` — one owner tenant per non-admin profile.
3. `migrate_fields_to_tenants.py` — `growers` table; add `fields.tenant_id` +
   `fields.grower_id` (nullable), backfill `tenant_id` from `tenant_members`, set
   NOT NULL once clean. **`fields.user_id` is retained** (deprecated, for safety).

All idempotent. No endpoint/query code changes in Block 1 — those are Block 2.
