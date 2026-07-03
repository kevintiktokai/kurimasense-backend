# KurimaSense Engineering Audit & Production-Readiness Report — July 2026

Author: engineering pass, session `s252ch`. Scope: full-stack audit
(`kurimasense-backend`, `kurima-sense`) with evidence-driven fixes. This report
distinguishes **✅ implemented & validated this session** from **📋 recommended
next** so status is never ambiguous.

---

## Executive summary

KurimaSense is well-architected in its core (pure-function engines with unit
tests, tenant model with 403-vs-404, deny-by-default RLS, a canonical
field-state aggregator). The problems that made it *feel* broken in testing were
concentrated in a few high-traffic paths, and were **operational, not
structural**:

1. **Climate was fully down** — not a bug in parsing or rendering, but the
   backend hitting Open-Meteo's **429 rate limit** on the shared Render IP and
   having no resilience (cache-on-success-only, no retry, no stale-serve, raised
   500). One transient upstream limit became a permanent dead feature.
2. **The crop-variety picker looked "removed"** because its catalogue table was
   never seeded on prod, so the dropdown silently degraded to a text box.
3. **Field analysis rebuilt far more often than its data changes** (120 s blanket
   cache, no event-driven invalidation), wasting compute and upstream quota.
4. **Fields couldn't be edited** after creation — no update endpoint existed.

All four are addressed below; the first three are fixed and validated, the fourth
has its backend/API foundation shipped with tests.

---

## Method

Evidence first. Live probes were run against prod (`kurimasense-backend.onrender.com`)
with a real minted token, plus direct upstream probes, before any code changed.
Key measurements are quoted inline. Every backend change compiles; the suite runs
**284 passing** (9 pre-existing failures require a live `DATABASE_URL` and are
unrelated).

---

## Phase 6 — Climate module (root cause + fix) ✅

**Root cause (reproduced 3×).** With a real token:
```
GET /climate/current → HTTP 500
  "Failed to fetch weather data: Client error '429 Too Many Requests'
   for url 'https://api.open-meteo.com/v1/forecast?...'"
```
Meanwhile `/health` was 200 in 0.8 s and Open-Meteo answered a *direct* probe in
0.9 s — so the 429 is specific to the Render egress IP being over Open-Meteo's
free-tier limit. The service **only cached on success**, so during a rate-limit
spell the cache never populated → every call re-hit Open-Meteo → permanent 429 →
backend 500 → the frontend swallowed it to `null` → "Weather data unavailable".

**Contributing load.** A single field-state view fires 4 concurrent climate
calls; the weather page fires 6 (several fanning out to multiple Open-Meteo
endpoints). With no request coalescing, every view was a stampede.

**Fix — one shared resilience layer (`climate_service.py`).**
- `_get_json`: retry + exponential backoff w/ jitter on 429/5xx, honouring
  `Retry-After`; optional `OPENMETEO_API_KEY` + base-URL overrides (lifting the
  limit becomes a Render env change, not a deploy).
- `_cached`: TTL cache + **single-flight** (concurrent misses for one key collapse
  to one upstream call) + **serve-stale-on-error** (expired entries retained up
  to 24 h and served when upstream fails, instead of raising). Tiered TTLs
  (current 15 m, forecast 1 h, agri 3 h, history 6 h) replace the blanket 5 min.
- All primitive fetchers routed through it; historical-comparison reuses the
  cached history helper (one fewer raw call).
- Endpoints **soft-fail**: HTTP 200 `{available:false}` instead of 500, so the
  client shows "temporarily unavailable — retrying" and keeps polling.
- Frontend (`services/climate.ts`): bounded retry w/ backoff, and it no longer
  caches soft-unavailable payloads, so the page self-heals without user action.

**Validation.** Unit tests assert stale-on-error, single-flight (10 concurrent →
1 upstream call), and error-propagation when nothing is cached — all pass.

**Expected impact.** Upstream call volume drops by roughly the cache-hit ratio
(single-flight + long TTLs); a transient 429 now degrades to slightly-stale data
instead of a dead feature. **Durable capacity fix:** set `OPENMETEO_API_KEY`
(commercial tier) or move the instance off the shared free-tier IP.

---

## Phase 3 — Regression: crop-variety picker ✅

**Root cause (reproduced).** `GET /crops/Maize/varieties` → `HTTP 200 []` on prod.
The `crop_varieties` catalogue was empty because it was only ever populated by a
**manual** script (`scripts/seed_zimbabwe_crops.py`) that requires someone to run
it — nothing did on prod. With an empty catalogue the field-creation picker's
`availableVarieties.length > 0 ? <select> : <textbox>` branch fell to the text
box: the rich dropdown (SC 727, SC 513, …) "disappeared".

**Fix (proper, not a patch).** `init_db()` already self-heals tables and columns
on boot; extended it with an idempotent `seed_crop_varieties()` that loads the
canonical 87-variety list from that same script (single source of truth) and
upserts it (`ON CONFLICT DO NOTHING`), guarded by a COUNT so warm reboots pay one
query. The picker now works on every environment with no manual step. Frontend:
`getCropVarieties` no longer caches an empty result, so the picker reappears the
moment the catalogue is populated rather than after the 24 h TTL.

**Validation.** The 87-variety dataset loads cleanly via the same import path the
seeder uses (all required keys present, all 8 maize varieties). Seeder runs on
next deploy (`init_db` is the startup hook).

---

## Phase 7 — Field-analysis refresh strategy ✅

**Previous behaviour.** `/field/{id}/state` cached **120 s** per (user, field) and
was **never invalidated on writes**. So the whole aggregate — 4 climate fetches +
yield recompute + snapshot write — rebuilt every 2 minutes of browsing, even
though its slowest-changing inputs are satellite/NDVI (~5-day Sentinel revisit,
only updated by an explicit `/analyze`) and weather (now cached upstream 15 m–6 h).
Worse, a user's own edit could lag up to 2 min.

**Data-freshness tiers** (the categorisation the strategy is built on):

| Tier | Examples | Refresh policy |
|---|---|---|
| Real-time | auth, AI chat turns, user edits | never cached; edits invalidate derived caches |
| Frequently updated | weather, forecast, climate | upstream TTL 15 m–6 h + serve-stale |
| Periodically updated | NDVI, crop health, yield, recommendations | field-state cache 10 min + event-driven invalidation; satellite only on explicit `/analyze` |
| Static until changed | field metadata, planting/fertilizer history | cached; invalidated on edit |

**New strategy (implemented).** Longer, freshness-aligned TTL (120 s → **600 s**,
the fastest input's cadence) **plus event-driven invalidation**.
`_invalidate_field_caches(field_id, user_id)` drops the field-state view for *all*
viewers of a field (matches the `field_id` key suffix — tenant members have
distinct requester ids) plus the actor's insights/yield/dashboard rollups. Wired
into the events that actually change a field: **satellite analysis completion,
input logging, field deletion**. Satellite recomputation stays where it belongs —
behind the explicit `/analyze` action, never on load.

**Impact.** ~5× fewer aggregate rebuilds (and associated climate/DB load) during
normal browsing, while edits and fresh analyses appear immediately. **Trade-off:**
weather-derived bits inside a cached field-state can be up to 10 min old — bounded
and consistent with the upstream weather TTL, acceptable for agronomic decisions.
15 field-state/consumer tests still pass.

Complementary work already in this branch: **field-history prefetch on field
creation** (warms the archive/GDD cache so the first field open is ~2 s instead of
the measured ~26 s), and the climate caching above.

---

## Phase 4 — Field management (editing) — foundation shipped ✅ / UI 📋

**Gap (confirmed).** No `PATCH/PUT /fields/{id}` endpoint and no edit affordance in
`FieldManagement.tsx` (create + delete only). Users could not correct a field.

**Implemented.** `PATCH /fields/{id}` — owner/tenant-scoped partial update of
name, crop, variety, planting/transplant date, fertilizer history. Changing the
crop re-derives `is_transplanted` and clears a stale transplant date; blank dates
normalize to NULL; the field's cached state is invalidated on success. `api.updateField`
client shipped. **7 unit tests** cover validation + UPDATE construction.

**📋 Remaining (scoped).** Frontend edit UI: an "Edit" action opening the existing
create panel pre-filled, calling `api.updateField` (the create form already has
every input). Not shipped this session because the frontend can't be built/run in
this environment (`node_modules` absent) and shipping unvalidated UI would violate
the "validate every change" bar. Also worth adding: activity/record editing &
deletion (field_inputs, harvest_records) — same pattern (scoped PATCH/DELETE +
`_invalidate_field_caches`).

---

## Phase 5 — AI Advisor field-awareness — assessed 📋

**Finding (evidence).** The **backend is already field-aware**: `/chat/v2/*` accepts
`field_id`, and `ai_brain._build_context_prompt` injects `FieldContext` (crop,
variety, growth stage, NDVI, soil moisture, weather) plus the crop-knowledge
engine and RAG. General (no-field) chat also works. The gap is **frontend**:
`agronomist-chat.tsx` has no field selector, so users can't pick a field to make
the conversation field-specific.

**📋 Recommended (small, high-value).** Add a field dropdown to the chat composer
(reuse `useDashboardData().fields`), pass the selected `field_id` on send. The
context assembly is already extensible — `get_field_context` is the single place
to add future analytics (disease detections, historical analytics, previous
recommendations) so "add an analytic" is a one-function change. No backend work
needed beyond optionally widening `FieldContext`.

---

## Phases 1–2 & 8 — Architecture / performance / general

Investigated as part of the above. Notable confirmed items and status:

- ✅ **Climate stampede & upstream quota** — fixed (single-flight + TTLs).
- ✅ **Redundant field-state rebuilds** — fixed (event-driven cache).
- ✅ **First-field-open latency** (~26 s archive) — mitigated (prefetch + cache).
- 📋 **Render free-tier cold start (526 s measured)** — the dominant "app is slow"
  cause. Keep-warm workflow mitigates; the real fix is the $7/mo always-on plan.
  Strongly recommended before any pilot.
- 📋 **Frontend ships both Leaflet and MapLibre GL** — two map engines in one
  bundle; consolidate.
- 📋 **Observability** — 88 `print()` vs structured logging; adopt `logging` +
  Sentry. The climate/field-state paths now print clear stale/invalidation
  markers, but a real logger + request ids remain the top reliability rec.
- 📋 **Rate limiting** on AI/write endpoints (`slowapi`), and admin-gating
  `/db-schema` + `/jwt-config` — carried from the prior audit, still open.
- 📋 **RLS FORCE** — Steps A+B are code-complete (see `rls_force_runbook.md`);
  migrations 010/011 await application, then per-table FORCE.

---

## Validation summary

| Change | How validated |
|---|---|
| Climate resilience | unit tests: stale-on-error, single-flight 10→1, error-propagation |
| Climate root cause | reproduced live 3× (429) with real token; upstream+health probes |
| Variety regression | reproduced live (`/crops/Maize/varieties` → `[]`); data loads via seeder path |
| Field-state cache | 15 field-state/consumer tests pass; wiring grep-verified |
| PATCH /fields | 7 new unit tests; full suite 284 pass |

---

## Prioritised remaining recommendations

1. **Capacity for weather**: set `OPENMETEO_API_KEY` (or dedicated IP) — removes
   the 429 root cause entirely rather than only tolerating it.
2. **Render always-on plan** — kills the 526 s cold start (the biggest UX drag).
3. **Field edit UI + activity editing** (Phase 4 remainder) — backend/API ready.
4. **Chat field selector** (Phase 5) — backend already field-aware.
5. **Observability**: `logging` + Sentry + request ids.
6. **Rate limiting** on AI/write endpoints; admin-gate debug endpoints.
7. **RLS FORCE** cut-over per runbook (apply 010/011 → soak → per-table FORCE).
8. **Map engine consolidation** (Leaflet vs MapLibre) for bundle size.
