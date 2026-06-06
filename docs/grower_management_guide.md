# Grower management — API guide (institutional)

Institutional users (role `institutional`) manage their tenant's contracted
growers via `/tenants/me/growers`. All requests use the normal Supabase session
(`Authorization: Bearer <token>`). Growers are automatically scoped to the
caller's primary tenant. **Owners and officers** can create/edit/delete;
**viewers are read-only**.

Base URL below is the deployed backend, e.g.
`https://kurimasense-backend.onrender.com`.

## Create a grower
```bash
curl -X POST $BASE/tenants/me/growers \
  -H "Authorization: Bearer $JWT" -H "Content-Type: application/json" \
  -d '{"name":"Tafadzwa Moyo","phone":"+263...","email":"t@example.com",
       "coordinates":{"lat":-17.8,"lon":31.0},"notes":"Ward 12"}'
```
`tenant_id` and `created_by_user_id` are set server-side. Returns the `Grower`.

## List growers (active only, paginated)
```bash
curl "$BASE/tenants/me/growers?limit=50&offset=0" -H "Authorization: Bearer $JWT"
```
Soft-deleted growers are excluded.

## Get / update / delete
```bash
curl "$BASE/tenants/me/growers/$GROWER_ID" -H "Authorization: Bearer $JWT"

curl -X PATCH "$BASE/tenants/me/growers/$GROWER_ID" \
  -H "Authorization: Bearer $JWT" -H "Content-Type: application/json" \
  -d '{"phone":"+263 77 000 0000","notes":"Updated"}'

curl -X DELETE "$BASE/tenants/me/growers/$GROWER_ID" -H "Authorization: Bearer $JWT"
# 204; the grower is soft-deleted (deleted_at set) and drops out of the list.
```

## Linking a field to a grower
Field create/update accepts an optional `grower_id`, validated against the
caller's tenant (a grower from another tenant is rejected with 400). Setting
`grower_id` to null unlinks. *(This wiring on the `/fields` endpoints is the
app.py long-tail tracked in `tenant_model_audit.md`; the grower records and
`fields.grower_id` column already exist.)*

## Responses & errors
- `403` — viewer attempting a write, or a grower from another tenant.
- `404` — grower not found in your tenant (or already soft-deleted).
- `401` — missing/invalid session.

## Notes
- A grower may later be `claimed_by_user_id` (a consumer farmer who also uses the
  app) — that linkage is set in a future workstream.
- All SQL is parameterized; growers are never visible across tenants.
