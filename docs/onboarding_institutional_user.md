# Onboarding an institutional user

There are now **two** ways to onboard an institutional user:

1. **Self-service (preferred)** — the user picks "Institution" during signup
   onboarding. The frontend calls `POST /me/institutional` (session-gated, see
   below), which flips their `role` to `institutional`, records the
   `institutional_type` + organization name, and provisions a `tenant` +
   `owner` membership so portfolio access works immediately.
2. **Manual (admin)** — an operator flips a user's `role` via the
   `X-Admin-Token` admin endpoint. Use this for support/back-office changes.
   Note: the admin role-flip does **not** create a tenant/membership; pair it
   with the tenant + tenant-member admin endpoints if portfolio access is needed.

## Self-service endpoint

```
POST /me/institutional
Authorization: Bearer <user JWT>
Content-Type: application/json

{ "institutional_type": "buyer", "organization_name": "Northern Tobacco" }
```
`institutional_type` is one of `buyer | lender | insurer | grower`.
Re-submitting is idempotent: an institutional tenant the user already owns is
reused (renamed), never duplicated.

---

## Manual provisioning (admin)

Institutional users can also be provisioned manually by flipping a user's `role`
on the `profiles` table via the admin endpoint. This is the demo/back-office path.

## Prerequisites
- The `ADMIN_TOKEN` env var is set on the backend (Render). The admin endpoints
  reject all requests if it is unset or the `X-Admin-Token` header doesn't match.
- The role-tagging migration (`migrate_user_roles.py`) has been applied.

## 1. Find the user's `user_id`
The `user_id` is the user's Supabase `auth.users` UUID (= `profiles.id`).
- Supabase dashboard → **Authentication → Users** → find the user by email →
  copy their **UID**. (Equivalently, **Table editor → profiles → id**.)

## 2. Flip the user to institutional
```bash
curl -X POST https://<render-url>/admin/users/<USER_ID>/role \
  -H "X-Admin-Token: $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role": "institutional", "institutional_type": "buyer",
       "tenant_name": "Northern Tobacco"}'
```
`institutional_type` is one of `buyer | lender | insurer | grower` and is
**required** when `role` is `institutional` (the endpoint returns `400` otherwise).
`tenant_name` is free text (e.g. `"AFC"`, `"Old Mutual"`).

Response:
```json
{
  "user_id": "<USER_ID>",
  "role": "institutional",
  "institutional_type": "buyer",
  "tenant_name": "Northern Tobacco",
  "updated_at": "2026-06-06T12:00:00+00:00"
}
```

## 3. Read a user's current role
```bash
curl https://<render-url>/admin/users/<USER_ID>/role \
  -H "X-Admin-Token: $ADMIN_TOKEN"
```

## 4. Flip the user back to consumer
```bash
curl -X POST https://<render-url>/admin/users/<USER_ID>/role \
  -H "X-Admin-Token: $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role": "consumer"}'
```
Flipping to a non-institutional role **clears** `institutional_type` and
`tenant_name` automatically (and logs a warning if you passed them anyway).

## Notes
- This is a **manual** process until Workstream 5 (self-service institutional
  signup) is built.
- Roles: `consumer` (default for every existing/new user), `institutional`,
  `admin`. All existing users are `consumer` after the migration — no behaviour
  change for them.
- These admin endpoints use the `X-Admin-Token` header, **not** a user session —
  they are operator tools, not part of the consumer/institutional app surface.
