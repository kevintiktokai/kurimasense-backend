# Production-Readiness Audit — July 2026

Full-stack audit of KurimaSense (backend `kurimasense-backend`, frontend
`kurima-sense`) against production engineering practice. Each finding is marked
✅ fixed-in-this-pass, 🔧 recommended-next, or 📋 accepted/tracked.

## Verdict in one paragraph

The app is much closer to "engineered" than "vibe-coded" in the areas that
matter most: the auth surface is tight (only 4 unauthenticated endpoints, all
harmless public data), CORS is a strict allowlist+regex with correct preflight
handling, the database has deny-by-default RLS plus per-tenant policies, there
are no hardcoded secrets, TypeScript is in strict mode, and there are 24 backend
+ 16 frontend test files covering the pure engines. The real gaps were
operational: no error boundaries (a single render bug white-screened the app),
no observability (88 `print()` calls, zero structured logging, no error
tracking), a 4,177-line `app.py` monolith, no rate limiting, no CI, and — the
single biggest UX killer — Render free-tier cold starts measured at **90–240+
seconds** on first hit.

## 1. Security

| Finding | Status |
|---|---|
| Auth surface: only `/health`, `/market/prices`, `/ai/capabilities`, `/agro/supported-crops` unauthenticated — all public data | ✅ good as-is |
| CORS: strict origin allowlist + regex, custom middleware guarantees headers on error paths | ✅ good as-is |
| RLS: deny-by-default (mig 004/005) + per-tenant `ts_*` policies (mig 008) + personal policies drafted (mig 010); FORCE gated per runbook | ✅ shipped this sprint |
| No hardcoded secrets anywhere (all `os.getenv`) | ✅ good as-is |
| No rate limiting on any endpoint. AI endpoints (`/chat/*`, `/vision/analyze`, `/fields/{id}/yield`) spend OpenAI tokens per call → cost/abuse exposure | 🔧 add `slowapi` per-user limits on AI + write endpoints |
| `/db-schema` + `/jwt-config` debug endpoints readable by ANY authenticated user (schema/config disclosure) | 🔧 restrict to admin role or remove |
| Supabase leaked-password protection still off (one dashboard toggle) | 🔧 manual toggle |

## 2. Reliability & observability

| Finding | Status |
|---|---|
| No React error boundaries — any component crash white-screened the app | ✅ fixed: `app/error.tsx` + `app/global-error.tsx` |
| 88 `print()` vs 0 `logger` calls in `app.py`; no request IDs, no timings, no error tracker | 🔧 adopt `logging` + Sentry (free tier) — top recommendation |
| 3 bare `except:` clauses in `app.py` | 🔧 narrow them |
| Connection leak in `get_dashboard_stats` (pool exhaustion cliff) | ✅ fixed during RLS wiring |
| `DELETE /fields` 500'd after success; `/agro/*` all 500'd (tuple cursor) | ✅ fixed during RLS wiring |
| No CI — tests exist but nothing runs them on push | 🔧 frontend CI added (typecheck+tests); backend CI recommended once env-dependent tests are markable |

## 3. Performance (measured live, July 2 2026)

| Path | Measured | Notes |
|---|---|---|
| Supabase login | ~1.7s | acceptable (includes TLS setup) |
| **Backend cold start** | **90–240+ s** | Render free tier spins down after ~15 min idle. THE dominant "app feels slow" cause |
| Warm `/dashboard/init` | see below | consolidated 1-request loader + 120s cache already in place (good design) |

Actions:
- ✅ `.github/workflows/keep-warm.yml` — pings `/health` every 10 min so the
  instance stays resident (fits in Render's 750 free hours/month).
- 🔧 The *real* fix is Render's $7/mo starter plan (always-on). Strongly
  recommended before any pilot with real farmers.
- 🔧 Frontend ships BOTH Leaflet (consumer maps) and MapLibre GL (portfolio map)
  — two full map engines in one bundle. Consolidate on one.
- 📋 Warm-path numbers to be re-measured after keep-warm merges; recorded in
  this doc's next revision.

## 4. Code structure

| Finding | Status |
|---|---|
| `app.py` = 4,177 lines mixing ~60 routes + services. Newer code (outcome/financial/verification/reconciliation routes, services/) is properly modular | 🔧 keep extracting: field routes → `field_routes.py`, chat/AI routes → `chat_routes.py`, one file per sprint touched |
| 12 one-shot `migrate_*.py` scripts in repo root + `migrations/*.sql` | 🔧 move applied one-shots to `migrations/applied/` for a cleaner root |
| Frontend: 3 stray `console.log`s, strict TS, no dead pages found | ✅ healthy |
| Legacy duplicate tables in DB (`daily_log` vs `daily_logs`, `documents`, `alerts`) flagged by advisor | 🔧 verify unused → drop in a cleanup migration |

## 5. AI / agronomy brain (summary — full audit in AI workstream)

| Finding | Status |
|---|---|
| All AI features pinned to mid-2024 models (`gpt-4o-mini` ×6 sites, `gpt-4o` ×2), hardcoded per call site | ✅ fixed: `llm_models.py` central tiers (chat `gpt-4.1-mini`, deep+vision `gpt-4.1`), env-overridable, forward-compatible with gpt-5/o-series param semantics |
| Chat has NO session concept — `session_id` hacked onto `chat_logs.field_context_id`; one endless conversation | 🔧 in progress: `chat_sessions` table + LLM-style chat UI (history sidebar, new/resume chats) |
| Vision replies render as text tag in chat UI instead of image preview | 🔧 in progress (UI workstream) |
| Agronomy system prompt is substantive (variety portfolio, pH/Al-toxicity chains, disease-risk wiring) | 📋 deep content-quality pass in AI workstream |

## 6. What was already right (credit where due)

- Pure-function service engines with hand-computed unit tests (calibration,
  exposure, reconciliation, verification) — genuinely good architecture.
- Tenant model + 403-vs-404 access resolution done properly.
- PWA/offline outbox for field capture; gzip; SWR caching with sane TTLs;
  consolidated `/dashboard/init` loader.
- Migrations are idempotent with rollback notes.
