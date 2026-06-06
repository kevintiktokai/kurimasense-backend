# Role Migration Audit — Workstream 1 foundation

**Scope:** backend-only role-tagging foundation. Input to Workstream 2
(frontend role-based routing) and Workstream 3 (institutional fields / tenant
data model). This document captures the *current* auth + `profiles` reality so
the migration is backward-compatible.

**Live DB inspected:** Supabase project `kurimasense` (`cqyxcpbdpvsrksilczmv`),
read-only, on 2026-06-06.

---

## 1. How authentication works today

- **JWT verification:** `deps.verify_token(authorization: Header) -> str`
  (`deps.py`). It parses `Authorization: Bearer <jwt>`, verifies the Supabase JWT
  (HS256 via `SUPABASE_JWT_SECRET`, or ES256/RS256 via configured key / JWKS),
  and returns the `sub` claim as `user_id` (a UUID string). A short-lived token
  cache avoids re-verifying every request.
- **Where `user_id` flows:** every authenticated route declares
  `user_id: str = Depends(verify_token)` and uses it to scope DB queries
  (`WHERE user_id = %s::uuid` / `WHERE id = %s`).
- **Where `profiles` is read today:**
  - `deps.get_user_language(user_id)` → `SELECT preferred_language FROM profiles WHERE id = %s`.
  - `app.get_user` / settings → returns profile fields.
  - The frontend `api.getUser` does `profiles.select('full_name, phone_number, role')`
    and **displays `role` as the user's label** (default `'Farmer'`).
- **Tenant model today:** there is no `tenant_id`; isolation is by `user_id`. The
  `X-API-Key`/`INSTITUTIONAL_API_KEY` principal added for `GET /field/{id}/state`
  is the only non-session auth path.

## 2. `profiles` table — actual columns (live)

| column | type | nullable | default |
|---|---|---|---|
| id | uuid | NO | — (FK to auth.users) |
| full_name | text | YES | — |
| phone_number | text | YES | — |
| **role** | **text** | **YES** | **— (no default, no CHECK)** |
| avatar_url | text | YES | — |
| updated_at | timestamptz | YES | — |
| created_at | timestamptz | NO | `now()` |
| preferred_language | text | YES | `'English'` |
| whatsapp_notifications | boolean | YES | `true` |
| has_seen_tutorial | boolean | YES | `false` |
| tutorial_progress | jsonb | YES | `'{}'` |

### ⚠️ Finding F1 — `role` already exists with legacy values
The prompt assumed `role` did not exist. It does, as **free text** the frontend
displays. Current distribution (6 rows):

| role | count |
|---|---|
| `smallholder` | 5 |
| `farmer` | 1 |

**Consequence for the migration:** a naïve `ADD COLUMN role ...` is wrong (it
would be skipped by the idempotency guard, leaving the column without
default/NOT NULL/CHECK). The migration instead **repurposes the existing
column** as the access tier: backfill any value not in
`('consumer','institutional','admin')` (i.e. `smallholder`/`farmer`/NULL) to
`'consumer'`, then add DEFAULT/NOT NULL/CHECK. All 6 existing users are
consumer-tier farmers, so the access behaviour is unchanged. The visible side
effect is that the settings "role" label becomes `consumer` — this is the
intended repurpose; Workstream 2 owns role display.

### Finding F2 — no pre-existing admin endpoint / `ADMIN_TOKEN`
The prompt references "the existing ADMIN_TOKEN pattern used by satellite
ingestion admin endpoints". No such endpoint or env var exists in this repo
today (`grep` for `ADMIN_TOKEN`/`X-Admin-Token` → none). This PR therefore
*establishes* the `X-Admin-Token` header + `ADMIN_TOKEN` env convention for
`POST /admin/users/{id}/role`, mirroring the existing `X-API-Key` header style.

## 3. Authenticated endpoints (future role-aware surface)

All of the following require `Depends(verify_token)` today. **None are modified
in this PR** — listed so Workstream 2/3 know what may become role-gated. (48
session-authenticated routes.)

- Fields: `GET/POST /fields`, `DELETE /fields/{id}`, `POST /fields/{id}/analyze`,
  `GET /fields/{id}/history`, `GET /fields/{id}/insight`, `GET /field/{id}/state`,
  `POST /fields/{id}/yield`, `GET/POST /fields/{id}/yield-history`.
- Dashboard / yield: `GET /dashboard`, `GET /dashboard/init`, `GET /yield-analytics`.
- AI / tasks: `GET /ai/insights`, `GET /ai/proactive-alerts/{id}`,
  `GET /ai/growth-stage/{id}`, `GET /ai/disease-risk/{id}`, `GET /ai/capabilities`,
  `GET /ai/tasks`, `GET /ai/tasks/history`, `POST /ai/tasks`,
  `PATCH /ai/tasks/{id}`, `POST /ai/tasks/from-plan`.
- Agronomy: `GET /agro/*` (planting-window, fertilizer, ipm, irrigation, harvest,
  crop-intelligence, supported-crops).
- Climate: `GET /climate/*` (current, forecast, agricultural, alerts,
  spray-window, historical, full).
- Chat: `GET /chat/history`, `POST /chat/send`, `POST /chat/v2/send`,
  `POST /chat/v2/stream`, `POST /proactive`, `POST /vision/analyze`,
  `POST /router`.
- Misc: `GET /user`, `GET /crops`, `GET /crops/{crop}/varieties`,
  `GET /market/prices`, `POST /inputs`.

## 4. What this PR adds (foundation only)

1. `migrate_user_roles.py` — repurpose `role`; add `institutional_type`,
   `tenant_name`; CHECKs; backfill; index. Idempotent.
2. `schemas.AuthenticatedUser` model + `auth_roles.get_authenticated_user`
   dependency (additive — see Finding F3 below).
3. Role-guard dependency factories (`auth_roles.require_consumer`,
   `require_institutional`, `require_admin`) — **defined but not attached to any
   endpoint**.
4. `GET`/`POST /admin/users/{user_id}/role` (`admin_routes.py`) guarded by
   `auth_roles.require_admin_token` (`X-Admin-Token` / `ADMIN_TOKEN`).
5. `tests/test_user_roles.py` for the auth boundaries.

### ⚠️ Finding F3 — `verify_token` deliberately NOT changed to return a model
The spec suggested `verify_token` return an `AuthenticatedUser`. Doing so would
change the value all 48 existing `user_id: str = Depends(verify_token)` endpoints
receive from a `str` to a Pydantic model and break every one of them — directly
violating the dominant backward-compat mandate (SUCCESS #6). We therefore keep
`verify_token() -> str` **unchanged** and add a sibling
`auth_roles.get_authenticated_user() -> AuthenticatedUser` (JWT verify + role
lookup + auto-create default `consumer` profile). The role guards depend on the
sibling, not on `verify_token`. This satisfies the role-context requirement
without touching the existing surface.

> Backward-compat guarantee: existing users default to `consumer` and see no
> behaviour change. `verify_token`'s signature/return is untouched; no existing
> endpoint is modified.
