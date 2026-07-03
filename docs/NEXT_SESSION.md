# Next-session handoff (written July 2 2026)

Read this first, then `docs/production_audit_2026-07.md` and
`docs/rls_force_runbook.md`. Both repos (`kurimasense-backend`, `kurima-sense`)
deploy from `main` (Render auto-deploys backend; Vercel the frontend).

## Engineering audit pass (see docs/ENGINEERING_AUDIT_2026-07.md)

Full evidence-driven audit + fixes this session. Headlines:
- **Climate outage ROOT-CAUSED + FIXED**: Open-Meteo 429 on the shared Render IP;
  service had no resilience so a transient limit was a permanent outage. Added a
  shared retry/backoff + cache + single-flight + serve-stale layer; endpoints
  soft-fail (200 `{available:false}`) instead of 500; frontend self-heals.
  **Durable fix owed by Kevin**: set `OPENMETEO_API_KEY` env on Render (commercial
  tier) or move off the free-tier shared IP.
- **Variety picker regression FIXED**: `crop_varieties` was never seeded on prod →
  picker fell back to a text box. `init_db()` now self-seeds it idempotently.
- **Field-analysis refresh FIXED**: field-state cache 120s→600s + event-driven
  invalidation (analyze/log_input/delete) instead of blanket rebuild every 2 min.
- **Field editing (Phase 4)**: `PATCH /fields/{id}` + `api.updateField` shipped
  with 7 tests. **Remaining**: the edit *UI* (couldn't build frontend here) and
  activity/record editing.
- **AI advisor (Phase 5)**: backend already field-aware (`/chat/v2` takes
  field_id, injects FieldContext). **Remaining**: a field selector in the chat
  frontend (`agronomist-chat.tsx`).

## Done since this handoff was written

- **AI plumbing fixes** (branch `claude/handoff-continuation-s252ch`): the model
  upgrade wasn't actually reaching the main chat endpoint — `AgronomistBrain.
  process()` picks its model via `LLMRouter.select_model`, which was hardcoded to
  `gpt-4o-mini`/`gpt-4o` and overrode the central tiers. Now routes through
  `CHAT/DEEP/VISION_MODEL` from `llm_models.py`. Separately, the `/field/{id}/
  state` insight path imported crop lookups from legacy `crop_knowledge.py`
  (only 4 crops), so 35 of 39 crops got no growth-stage context or temp-threshold
  fallback — repointed to the `crop_profiles` package. Deleted the now-dead
  `crop_knowledge.py` (1,627 lines, superseded and divergent), removed the unused
  `LLMProvider` enum, and made the vision endpoint report the real model.
- Deleted the `__RLS_SMOKE__` test row from `yield_history` (owed cleanup).

## Queued work, in priority order

1. **AI/agronomy brain content review** (the big one). Model tiers now correctly
   wired (see above). Remaining: deepen CONTENT quality to expert/doctorate
   level — system prompts in `ai_brain.py` (~line 400+), `crop_profiles/*` (39
   crops, all already carry full disease/pest/growth-stage data; maize is the
   gold-standard reference), `proactive_intelligence.py`. Goals: agronomically
   rigorous for Zimbabwe (varieties, natural regions, pH/Al toxicity,
   disease-weather interactions), yet conveyed in language smallholder farmers
   understand. Review every AI feature end-to-end (chat, vision diagnosis,
   insights, crop plan, yield) — ideally with a live token once `openai` deps are
   installed, since the sandbox can't import `ai_brain`.
2. **RLS FORCE cut-over** — Steps A–C DONE; Step D BLOCKED by architecture (see
   `docs/rls_force_runbook.md`). This session: wired all ~30 DB sites
   (`tenancy.arm_rls_gucs`); **applied migrations 010 + 011 to prod** (July 3 —
   `us_*` personal policies + `mc_global`); shipped Step C code prep behind the
   `RLS_TENANT_ONLY` flag (all `fields.user_id` refs gated, guard-tested).
   **⚠️ KEY FINDING:** the backend connects as `postgres`, which has `BYPASSRLS`,
   so **`FORCE` is a no-op against it** — running it gives no isolation while
   looking like it does. FORCE was deliberately NOT applied. Real
   backend-isolation needs a dedicated `NOBYPASSRLS` role + moving `init_db()`
   runtime DDL to a migration + rotating `DATABASE_URL` (scoped project; only
   for a lender-audit requirement). External access is already safe (PostgREST
   anon/authenticated hit deny-by-default policies). **Remaining, optional:**
   Step C operational drop of `fields.user_id` (flip `RLS_TENANT_ONLY=true` on
   Render → soak → snapshot → `DROP COLUMN`).
3. ~~**Field-history background prefetch**~~ — DONE. `POST /fields` now schedules
   `app._prefetch_field_history` as a background task: warms both
   `climate_service.get_daily_history` and the derived `calculate_gdd` for the
   field's centroid + planting/transplant window, so the first field-state view
   is served from the 6h cache (~2s) instead of paying ~15-30s archive latency.
   Best-effort; offline/mock create path skips it.
4. **Smaller audit items**: slowapi rate limiting on AI endpoints; structured
   logging + Sentry; restrict `/db-schema` + `/jwt-config` to admin; keep
   splitting app.py; consolidate Leaflet vs MapLibre on the frontend.

## Environment facts the next session needs

- Supabase project `cqyxcpbdpvsrksilczmv`; backend
  https://kurimasense-backend.onrender.com; frontend
  https://kurima-sense.vercel.app.
- Test account: kevin@test123.com / password Chisango1234 (user id
  05807a41-4362-48f3-b134-346a51de9bfd, 22 fields). Mint a token via Supabase
  password grant with the anon key to smoke-test authenticated endpoints.
- Supabase MCP approval prompts: allowlist committed in
  `.claude/settings.json` (`mcp__Supabase`) — BUT in the July 2 remote session
  the server re-registered under a UUID name (`mcp__a131210d-…`), so the
  allowlist didn't match and every call after the early-session window hit an
  un-answerable approval gate. This is what blocked applying migrations 010/011.
  Next session: verify the Supabase MCP server's registered name first; if it's
  a UUID again, the allowlist entry needs to match it (or Kevin approves the
  prompts interactively). First DB actions once unblocked: apply
  `migrations/010_rls_personal_policies.sql` + `011_rls_model_calibration_policy.sql`
  (both inert until FORCE).
- Cleanup owed: ~~delete the `__RLS_SMOKE__` row in `yield_history`~~ (done);
  recommend Render paid plan to Kevin (cold start measured 526s; keep-warm
  workflow mitigates).
- Verification habit that caught 4 real bugs: after each backend push, wait
  ~2-3 min for the deploy to actually flip, then smoke-test live endpoints
  with a real token. Don't trust the first 110s.
