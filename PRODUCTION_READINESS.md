# Production Readiness — Audit & Launch Roadmap

*July 2026 audit covering both repos: `kurima-sense` (Next.js 16 / Vercel / Capacitor PWA) and
`kurimasense-backend` (FastAPI / Render) + Supabase (Postgres, Auth). The canonical copy lives in the
`kurima-sense` repo; this is a synced snapshot.*

The goal: launch, run paid ads, and acquire users **without flying blind or getting burned**.
Items are ordered by "what breaks first when real traffic arrives."

---

## 1. Verified baseline — what is already solid

Ran, not assumed (this audit re-verified everything locally):

| Area | Status |
|---|---|
| Backend test suite | ✅ 395 passed, 2 skipped |
| Frontend tests + typecheck | ✅ 239 passed, `tsc` clean |
| Production build (`next build`) | ✅ 28 routes compile |
| CI | ✅ Both repos run tests on push/PR to `main` |
| Backend observability | ✅ Structured JSON logs, `X-Request-ID` correlation, Sentry (dormant until `SENTRY_DSN` set) |
| Rate limiting | ✅ Per-user (token-hash) via slowapi on AI/write endpoints |
| Admin endpoints | ✅ `X-Admin-Token`, constant-time compare, deny-by-default |
| Tenant isolation | ✅ RLS policies applied; explicit scoping live; FORCE cutover gated behind `docs/rls_force_runbook.md` |
| Auth | ✅ Supabase JWT (HS256/ES256/RS256 + JWKS), cookie-based session (survives PWA boundary) |
| Funnel pages | ✅ Landing → `/auth` (signup w/ email confirm) → `/onboarding` (persona/institution) → role-routed app |
| Legal | ✅ `/privacy`, `/terms`, in-app disclaimer banners |
| Offline/PWA | ✅ Custom service worker, offline outbox, install prompts, Capacitor Android shell |

## 2. Fixed in this audit (branch `claude/production-readiness-audit-8mddxf`)

**Backend**
1. **Pinned `requirements.txt`** to the exact versions the suite passes against. Unpinned
   ranges meant every Render deploy could pull a breaking release and take prod down.
2. **CORS origin regex anchored.** `https://.*\.vercel\.app` matched *prefixes*, so
   `https://x.vercel.app.evil.com` was granted credentialed CORS. Now
   `https://[a-z0-9-]+(\.[a-z0-9-]+)*\.vercel\.app\Z`.
3. **`/health` no longer leaks config.** It previously returned the full CORS configuration and
   raw DB error strings to any unauthenticated caller. Now minimal (`status` + `database`);
   full diagnostics moved to admin-gated `GET /health/detail`.

**Frontend**
4. **Next.js 16.1.4 → 16.2.10** — clears four advisories including a high-severity RSC
   request-deserialization DoS (GHSA-h25m-26qc-wcjf) and HTTP smuggling in rewrites.
   `npm audit fix` applied for transitive deps. Typecheck/tests/build re-verified.
5. **Security headers** (HSTS, `X-Content-Type-Options`, `X-Frame-Options`,
   `Referrer-Policy`, `Permissions-Policy`) on every response via `next.config.ts`.
6. **`robots.txt` + `sitemap.xml`** (`app/robots.ts`, `app/sitemap.ts`) — marketing surface
   indexed, app shells excluded. Required for SEO and helps ad-platform site quality checks.
7. **Open Graph / Twitter metadata + `metadataBase`** — link previews for ads/social shares.
8. **Single API-base module** (`lib/api-base.ts`). The
   `process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'` fallback was copy-pasted in
   19 files; a missed env var silently sent production traffic to localhost. Now one import,
   with a loud console error if production runs unconfigured.

**Remaining `npm audit` findings are accepted:** postcss (bundled inside Next) and
serialize-javascript (inside workbox's *build-time* tooling) never ship to users; the
suggested "fixes" are absurd downgrades. Revisit when next-pwa updates workbox.

---

## 3. P0 — do these BEFORE spending money on ads

1. **Conversion analytics.** There is currently **zero analytics** — no way to know if ads
   convert. Add PostHog (or GA4 + Meta Pixel) with events for: landing view, signup started,
   signup completed, onboarding completed, first field created, first analysis run. Ad spend
   without these events is unmeasurable. Add a lightweight cookie-consent banner at the same time.
2. **Frontend error tracking.** Backend has Sentry; the browser has nothing — user-side crashes
   are invisible today. Add `@sentry/nextjs` (free tier is fine) so "the app is broken on my
   phone" comes with a stack trace.
3. **Turn monitoring on.** Set `SENTRY_DSN` on Render (code is already wired), and point a free
   uptime monitor (UptimeRobot / Better Stack) at `GET /health` with alerting to your email/phone.
4. **Move Render off the free tier.** 512 MB + 15-min spin-down (the keep-warm cron is a crutch)
   will fall over under ad-driven traffic bursts; cold starts were measured at 90s+. The
   in-memory caches/rate-limits also reset on every restart.
5. **Supabase production settings** (dashboard, ~15 min): enable leaked-password protection
   (already flagged in `SECURITY_HARDENING_SPRINT4.md`), confirm redirect-URL allowlist,
   verify backup/PITR settings on a paid tier, and **set up custom SMTP** — default Supabase
   auth email has low deliverability, and every confirmation email that lands in spam is a
   paid signup lost at the last step.
6. **Custom domain.** Ads pointing at `*.vercel.app` convert worse and look untrustworthy;
   buying the domain later means re-doing OG URLs, CORS, Supabase redirects, and ad accounts.
   Set `NEXT_PUBLIC_SITE_URL` + `CORS_ORIGINS` when it lands (code already reads both).
7. **Kill mock-data fallbacks in production** (backend). ~17 code paths return `MOCK_FIELDS`
   -style demo data when the DB is unreachable — a real user during a DB blip sees *fake
   fields that look real*. Gate with an env var (e.g. `ALLOW_MOCK_FALLBACK=false` in prod →
   return 503) so failures are visible instead of fabricated.
8. **Real OG image.** A 1200×630 card (current placeholder: the 200px logo). Direct CTR impact
   on every shared link and some ad formats.

## 4. P1 — first two weeks after launch

- **RLS FORCE cutover** per `docs/rls_force_runbook.md` — the DB should enforce tenant
  isolation even if app code regresses. The prep work is done; execute the runbook.
- **Admin backoffice.** User/tenant management is curl-against-admin-endpoints today. Even a
  minimal internal page (list users, roles, tenants, recent signups, field counts) changes
  how fast you can support early users. Supabase Studio covers auth users in the interim.
- **Replace `print()` with the structured logger** in the backend (hundreds of prints bypass
  the JSON logging/request-id machinery that already exists — they're invisible to log search).
- **Dependency hygiene in CI**: add `pip-audit` / `npm audit --omit=dev` steps + enable
  Dependabot/Renovate on both repos, now that versions are pinned.
- **Remove the `DEBUG_MODE` auth bypass** from `deps.py` (it's guarded, but a prod-config
  footgun with zero production value), and migrate `@app.on_event("startup")` → lifespan.
- **Staging environment** (Vercel preview + a Render staging service + Supabase branch) so
  migrations and risky changes stop being tested in production.
- **OpenAI spend controls**: usage alerts + a monthly budget cap; an ad-driven traffic spike
  is also an LLM-bill spike. Rate limits exist, but set the billing-side backstop too.
- **Support channel**: a `support@` address + in-app "report a problem" link (even mailto).
  Required by app stores later anyway.
- **E2E smoke test** (Playwright): signup → onboarding → create field → dashboard renders.
  This is the money path; unit tests don't cover the seams between Supabase, backend, and UI.

## 5. P2 — hardening as you grow

- Strict Content-Security-Policy (needs an allowlist pass over map tiles/Supabase/Render + staging soak).
- Load testing on the AI endpoints; Redis for cache + rate limits when scaling past one instance.
- Dockerfile polish: non-root user, `HEALTHCHECK`, digest-pinned base image.
- Capacitor store submissions (Play Store checklist: privacy policy URL ✅, data-safety form,
  signed AAB, screenshots).
- i18n for farmer-facing surfaces (Shona/Ndebele) — `profiles.preferred_language` already exists.
- Accessibility pass (WCAG AA) on the marketing + auth funnel.

## 6. Accepted risks (documented so nobody "fixes" them accidentally)

- PostGIS/vector extensions in `public` schema (Supabase default; relocation is high-risk, low-reward).
- `subscribers` table allows anonymous INSERT — intentional (landing-page waitlist).
- workbox/postcss transitive advisories — build-time only, see §2.
- In-memory caches and rate limits — correct for a single instance; revisit at horizontal scale.
