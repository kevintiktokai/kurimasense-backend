# KurimaSense Deployment Guide 🚀

Follow these steps to deploy the KurimaSense platform. Each part of the system is hosted separately to ensure maximum performance and scalability.

## User roles

`profiles.role` tags each user as `consumer` (default — every farmer), `institutional`
(offtakers, lenders, insurers, growers — with an `institutional_type` + `tenant_name`),
or `admin`. Existing users default to `consumer` with no behaviour change. Roles are
provisioned manually via the `X-Admin-Token`-gated admin endpoint — see
[`docs/onboarding_institutional_user.md`](docs/onboarding_institutional_user.md).
Set the `ADMIN_TOKEN` env var to enable those endpoints. Run the migration with
`python migrate_user_roles.py`.

## Data model (tenants & growers)

Field ownership is by **tenant**, not user (Workstream 3). A `tenant` is a
`consumer` (one-member personal tenant) or `institutional` (many officers).
`tenant_members` maps users → tenants with a role (`owner`/`officer`/`viewer`);
`growers` are an institution's contracted growers; `fields` carry `tenant_id`
(+ optional `grower_id`). Every consumer gets a personal tenant on backfill, so
their experience is unchanged. See
[`docs/tenant_model_concepts.md`](docs/tenant_model_concepts.md) and
[`docs/grower_management_guide.md`](docs/grower_management_guide.md).

Migrations (run in order, idempotent):
```bash
python migrate_create_tenants.py            # tenants + tenant_members
python migrate_backfill_consumer_tenants.py # one owner-tenant per profile
python migrate_fields_to_tenants.py         # growers + fields.tenant_id/grower_id
```
`fields.user_id` is retained but **deprecated** (migration safety; dropped in a
future cleanup PR).

## Scripts

- `scripts/seed_demo_fields.py` — **demo-only**, manual seeder that creates ~40
  fields + growers (fictional names, real GPS polygons) in an institutional
  tenant for the portfolio dashboard demo. Not an API endpoint; safe to re-run
  (`DEMO_SEED:` marker) with a `--clear` that only removes demo data. See
  [`docs/demo_seeding_guide.md`](docs/demo_seeding_guide.md).
- `scripts/recompute_kurima_scores.py` — one-shot warm-up/validation of
  KurimaScores for a tenant's fields (scores are computed on-the-fly).


## 1. Frontend: Vercel Setup
**Repository**: [kevintiktokai/kurima-sense](https://github.com/kevintiktokai/kurima-sense)

### Configuration
- **Framework Preset**: Next.js
- **Root Directory**: `./` (The repo root)
- **Build Command**: `npm run build`
- **Output Directory**: `.next`

### Environment Variables
Click on "Settings" > "Environment Variables" and add:
- `NEXT_PUBLIC_API_URL`: The URL of your Render backend (e.g., `https://kurimasense-backend.onrender.com`)
- `NEXT_PUBLIC_MAPBOX_TOKEN`: (Optional) If you use Mapbox for high-res sat view.

---

## 2. Backend: Render / Railway Setup
**Repository**: [kevintiktokai/kurimasense-backend](https://github.com/kevintiktokai/kurimasense-backend)

### Configuration
- **Render**: create a Web Service · Runtime Python 3 · Build `pip install -r requirements.txt`
  · Start `uvicorn app:app --host 0.0.0.0 --port $PORT`.
- **Railway**: New Project → Deploy from GitHub repo. Railway auto-detects the
  `Dockerfile` (`railway.json` pins the healthcheck to `/health`). The Dockerfile
  binds to the injected `$PORT`, so no start command is needed. Pick the region
  **closest to your Supabase project** — every request makes several DB round
  trips, so backend↔DB latency dominates.

### Environment Variables
Add these in the platform's Environment/Variables tab:

**LLM provider** (choose one primary; keep an OpenAI key regardless — see note):
- `OPENROUTER_API_KEY`: routes the chat + vision tiers through OpenRouter
  (default text tier: DeepSeek, materially cheaper). When set, it is the primary
  provider and OpenAI is used only as an automatic fallback.
- `OPENAI_API_KEY`: **still required even with OpenRouter set** — RAG embeddings
  (`text-embedding-3-small`) and voice (`audio.speech`) have no OpenRouter
  equivalent, and it is the chat fallback if OpenRouter errors.
- Optional overrides: `OPENROUTER_CHAT_MODEL` (default `deepseek/deepseek-chat`),
  `OPENROUTER_DEEP_MODEL`, `OPENROUTER_VISION_MODEL` (default `openai/gpt-4o` —
  must be multimodal), `OPENROUTER_SITE_URL`/`OPENROUTER_APP_NAME` (attribution).

**Core:**
- `DATABASE_URL`: **Use the IPv4 Pooler URL** (Supabase → Connection Pooling,
  port 6543). The direct `db.xxxx.supabase.co` URL fails with "Network is
  unreachable" on Render (IPv6). Railway supports IPv6 but the pooler is still
  recommended for connection limits.
- `CORS_ORIGINS`: Your Vercel frontend URL (e.g., `https://kurima-sense.vercel.app`).
- `ADMIN_TOKEN`: enables the admin + `/health/detail` endpoints.
- `ALLOW_MOCK_FALLBACK`: leave **unset** in production. With `DATABASE_URL` set, a
  database outage returns an honest 503 instead of mock demo data.
- `DB_SELF_HEAL_SCHEMA`: leave unset (boot-time schema self-heal on) unless
  running the migration-managed NOBYPASSRLS role — see `docs/rls_force_runbook.md`.

---

## 3. Database: Supabase
Ensure your Postgres database is running and the `init_knowledge_base.sql` has been run. 

### Troubleshooting the "Network is unreachable" Error
If you see this error in Render logs, it means your `DATABASE_URL` is pointing to an IPv6 address.
1. Go to Supabase > Settings > Database.
2. Under **Connection Pooler**, toggle it to **Enabled**.
3. Copy the **Transaction Mode** connection string.
4. Update the `DATABASE_URL` on Render.

---

## ✅ Deployment Checklist
> [!IMPORTANT]
> - Ensure `NEXT_PUBLIC_API_URL` on Vercel matches your Render URL.
> - Ensure `CORS_ORIGINS` on Render includes your Vercel URL.
> - Verify that the OpenAI API key is active.

### Root Directory Clarification
For Vercel, since the repository `kurima-sense` was created directly from the `frontend` folder, you do **not** need to change the root directory setting. It should remain as **`./`**.
