# Next-session handoff (written July 2 2026)

Read this first, then `docs/production_audit_2026-07.md` and
`docs/rls_force_runbook.md`. Both repos (`kurimasense-backend`, `kurima-sense`)
deploy from `main` (Render auto-deploys backend; Vercel the frontend).

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
2. **RLS FORCE cut-over** — Steps A + B now code-complete (see
   `docs/rls_force_runbook.md` Status). This session did the repo-wide straggler
   audit and wired ALL ~30 remaining bare DB sites (not just the original 16
   app.py ones) via `tenancy.arm_rls_gucs`, extended migration 010
   (`chat_sessions`), added migration 011 (`model_calibration` USING(true)), and
   documented the bootstrap exemption + Step C/D checklists.
   **Still to do next session:**
   (a) APPLY migrations 010 + 011 (blocked this session on a Supabase MCP
   approval prompt — they're inert until FORCE, safe to apply anytime);
   (b) prod soak of the wiring (watch error rates / p95 — each wrapped query
   adds one `set_config` round trip);
   (c) Step C drop `fields.user_id` — CODE FIRST: remove the `field_scope_sql`
   fallback and deploy to Render BEFORE the column drop, snapshot first;
   (d) Step D per-table FORCE with negative tests. Needs Kevin's go at FORCE.
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
  `.claude/settings.json` (`mcp__Supabase`) — should apply from session start.
- Cleanup owed: ~~delete the `__RLS_SMOKE__` row in `yield_history`~~ (done);
  recommend Render paid plan to Kevin (cold start measured 526s; keep-warm
  workflow mitigates).
- Verification habit that caught 4 real bugs: after each backend push, wait
  ~2-3 min for the deploy to actually flip, then smoke-test live endpoints
  with a real token. Don't trust the first 110s.
