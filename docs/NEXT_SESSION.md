# Next-session handoff (written July 2 2026)

Read this first, then `docs/production_audit_2026-07.md` and
`docs/rls_force_runbook.md`. Both repos (`kurimasense-backend`, `kurima-sense`)
deploy from `main` (Render auto-deploys backend; Vercel the frontend).

## Queued work, in priority order

1. **AI/agronomy brain deep-pass** (the big one). Models already upgraded to
   gpt-4.1-mini / gpt-4.1 via `llm_models.py` (env-overridable). Now review
   CONTENT quality to expert/doctorate level: system prompts in `ai_brain.py`
   (~line 400+), `crop_knowledge.py` (1,627 lines), `crop_profiles/*`,
   `proactive_intelligence.py`. Goals: agronomically rigorous for Zimbabwe
   (varieties, natural regions, pH/Al toxicity, disease-weather interactions),
   yet conveyed in language smallholder farmers understand. Also review every
   AI feature end-to-end (chat, vision diagnosis, insights, crop plan, yield).
2. **RLS FORCE cut-over** — fully staged; execute per `docs/rls_force_runbook.md`
   Steps B–D: apply `migrations/010_rls_personal_policies.sql`, decide
   `model_calibration`, drop `fields.user_id` (irreversible — snapshot first),
   per-table FORCE with negative tests. All 16 endpoints already wired to
   `tenant_scoped_connection`. Needs Kevin's explicit go at the FORCE step.
3. **Field-history background prefetch** — first-ever field-state view still
   pays ~15-30s Open-Meteo archive latency (GDD). Prefetch
   `climate_service.get_daily_history` after field creation + a warm-up pass;
   repeats are already ~2s (6h cache).
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
  `.claude/settings.json` (`mcp__Supabase`) — should apply from session start.
- Cleanup owed: delete the `__RLS_SMOKE__` row in `yield_history` (test
  artifact); recommend Render paid plan to Kevin (cold start measured 526s;
  keep-warm workflow mitigates).
- Verification habit that caught 4 real bugs: after each backend push, wait
  ~2-3 min for the deploy to actually flip, then smoke-test live endpoints
  with a real token. Don't trust the first 110s.
