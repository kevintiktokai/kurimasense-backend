# Onboarding an institutional user (manual)

Until self-service institutional signup exists (Workstream 5), institutional
users are provisioned manually by flipping a user's `role` on the `profiles`
table via the admin endpoint. This is the demo path.

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
