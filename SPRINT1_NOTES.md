# Sprint 1 Discovery Notes

**Task 0 — Discovery & Confirmation**
Produced: 2026-06-26

---

## 1. The Contract: Field-State Aggregator

### Pydantic model
**Class:** `FieldState` in `services/field_state/models.py:255–271`

The top-level document returned by `GET /field/{field_id}/state`. Contains `yield_projection: YieldProjection` (line 262).

### Yield projection model
**Class:** `YieldProjection` in `services/field_state/models.py:123–133`

| Field | Type | Notes |
|---|---|---|
| `projected_tonnes_per_ha` | `Optional[float]` | **The projected yield value** |
| `potential_tonnes_per_ha` | `Optional[float]` | Variety potential |
| `yield_gap_pct` | `Optional[int]` | 0–100 |
| `confidence_band` | `str` | `"low"` / `"medium"` / `"high"` |
| `confidence_pct` | `int` | 0–100 |
| `confidence_factors` | `ConfidenceFactors` | Nested (positive/negative lists) |
| `confidence_interval_low` | `Optional[float]` | Lower bound |
| `confidence_interval_high` | `Optional[float]` | Upper bound |
| `unit` | `str` | Always `"tonnes_per_ha"` |

**CLAUDE.md correction:** The spec guessed `FieldState.yield_projection` as the field name — that is correct at the top level. Within the model, the yield value is `projected_tonnes_per_ha` (not `yield_projection`).

### Snapshot hook site
**Function:** `_fetch_yield()` in `services/field_state/aggregator.py:872–898`

Signature: `def _fetch_yield(field_row: Dict, daily_logs: List[Dict]) -> Optional[Dict]`

Called at **line 759** inside `build_field_state()`. Returns a raw dict with keys: `projected_yield`, `yield_potential`, `confidence_bands`, `confidence_score`, `confidence_factors`.

The raw dict is then passed to `_build_yield()` (line 376 in `assemble_field_state`) which constructs the Pydantic `YieldProjection`.

**Task 2 hook strategy:** After `_fetch_yield()` returns at line 759, we have both `field_row` (with `field_id`, `tenant_id`) and `yield_raw` (with the projection). This is the hook site — persist a `yield_projections` row from this data, fail-safe on its own connection.

---

## 2. The Satellite-History Fetch

### Primary callable
**File:** `tools/get_crop_health.py`

- `_build_stats_request(bbox, start_date: str, end_date: str) -> dict` (lines 89–132) — builds Sentinel Hub Statistics API payload for NDVI+EVI, daily aggregation, arbitrary date window.
- `_fetch_ndvi_stats(token: str, payload: dict) -> dict` (lines 135–153) — POSTs to Statistics API, retries 3x.
- `_get_access_token(client_id, client_secret) -> str` — CDSE OAuth.
- `_build_bbox(lat, lon) -> list` — builds bounding box from centroid.
- `_isoformat_z(dt) -> str` — formats datetime to ISO-Z.

### Backfill script
**File:** `scripts/backfill_demo_fields.py` (lines 116–129) demonstrates arbitrary-window usage:
```python
token = gch._get_access_token(cid, secret)
start = end - timedelta(days=args.days)  # configurable via --days
req = gch._build_stats_request(gch._build_bbox(lat, lon), _iso_z(start), _iso_z(end))
stats = gch._fetch_ndvi_stats(token, req)
```

### Confirmation
**YES** — the fetch functions accept any ISO-Z date pair. The backtest harness can call them for an arbitrary historical window (e.g., planting_date to as-of checkpoint date).

---

## 3. The Yield Model

### Entry point
**Function:** `generate_yield_projection()` in `yield_model.py:350–510`

Signature:
```python
def generate_yield_projection(
    field_id: str, crop: str, variety: Optional[str],
    planting_date: date, area_ha: float,
    coordinates: Optional[List[Dict[str, float]]] = None,
    fertilizer_history: Optional[str] = None,
    ndvi_history: Optional[List[float]] = None,
    weather_data: Optional[Dict[str, Any]] = None,
    cumulative_rainfall_mm: float = 0.0,
    transplant_date: Optional[date] = None,
    is_transplanted: bool = False
) -> YieldProjection  # dataclass from yield_model.py
```

Returns a `YieldProjection` dataclass (line 26) with: `projected_yield`, `yield_potential`, `confidence_bands`, `confidence_score`, `confidence_factors`, `yield_gap_analysis`, `methodology`, `adjustment_factors`, `disclaimer`.

### Truncated-series feasibility
**YES** — the model works on partial data:
- NDVI factor uses `ndvi_history[-7:]` (recent 7) or all if fewer (lines 109–160)
- Water factor normalizes by `growth_stage.progress_percent` (lines 163–200)
- Growth stage is days-since-planting to "now", not full season
- No assumption of completed crop cycle

For backtest: pass `ndvi_history` truncated to the as-of date, and the model will compute using only that data.

---

## 4. Tenant Enforcement

### `get_authenticated_user`
**File:** `auth_roles.py:194–228`

Returns `AuthenticatedUser` (defined in `schemas.py:124–148`):
```python
class AuthenticatedUser(BaseModel):
    user_id: str
    role: Role                                    # "consumer"|"institutional"|"admin"
    institutional_type: Optional[InstitutionalType]  # "buyer"|"lender"|"insurer"|"grower"
    tenant_name: Optional[str]
    tenant_id: Optional[str]                      # Primary tenant
    tenant_ids: List[str] = []                    # All tenants
    member_role: Optional[MemberRole]             # "owner"|"officer"|"viewer"
```

### `verify_token`
**File:** `deps.py:142–254` — returns bare `user_id: str`. DO NOT CHANGE SIGNATURE.

### `resolve_access` (the 403-vs-404 pattern)
**File:** `services/field_state/aggregator.py:653–706`

```python
def resolve_access(field_id, requester_id, tenant_ids=None, is_admin=False) -> Dict:
```
1. Fetches field by id WITHOUT tenant filter
2. If field not found → raises `FieldNotFound` (404)
3. If found but caller has no access → raises `FieldAccessDenied` (403)
4. Access granted if: admin, OR field's `tenant_id` in caller's `tenant_ids`, OR legacy `user_id` match
5. Returns field row dict

### Custom exceptions
`FieldNotFound(field_id)` and `FieldAccessDenied(field_id)` defined at `aggregator.py:42–47`.

---

## 5. Available Indices (G2 Confirmation)

### `daily_logs` table (from `db/schema.sql:29–40` and `database.py:147–160`)
Columns: `id`, `field_id`, `user_id`, `log_date`, `ndvi`, `evi`, `soil_moisture`, `cloud_cover`, `source`, `insight_text`, `created_at`. Unique on `(field_id, log_date)`.

**Confirmed:** `ndre`, `ndmi`, `savi`, `sar_vv_db` are NOT persisted. The aggregator sets them to `None` with comment `# not stored today (audit G2)`.

**Backtest constraint:** Use only `ndvi`, `evi`, `soil_moisture` until G2 is closed.

---

## 6. Operational Items

### Environment Variables — Backend (Render)

| Variable | Used In | Required? | Notes |
|---|---|---|---|
| `DATABASE_URL` | `database.py`, all migrations | **Yes** | Postgres/Supabase connection |
| `ADMIN_TOKEN` | `deps.py` (admin endpoint guard) | Yes | Admin API auth |
| `OPENAI_API_KEY` | `deps.py`, AI features | Yes | AI chat, vision, RAG |
| `SUPABASE_JWT_SECRET` | `deps.py:verify_token` | Yes* | JWT HS256 verification |
| `SUPABASE_JWT_PUBLIC_KEY` | `deps.py:verify_token` | Yes* | JWT RS256/ES256 verification |
| `SUPABASE_URL` | `deps.py` | Yes* | JWKS fetch fallback |
| `SUPABASE_ANON_KEY` / `SUPABASE_KEY` | various | Optional | Supabase client calls |
| `SATELLITE_API_CLIENT_ID` | `tools/get_crop_health.py` | Yes (Task 5) | CDSE OAuth |
| `SATELLITE_API_CLIENT_SECRET` | `tools/get_crop_health.py` | Yes (Task 5) | CDSE OAuth |
| `SATELLITE_TOKEN_URL` | `tools/get_crop_health.py` | Optional | Override token endpoint |
| `SATELLITE_STATS_URL` | `tools/get_crop_health.py` | Optional | Override stats endpoint |
| `CORS_ORIGINS` | `app.py` | Optional | CORS allowed origins |
| `DEBUG_MODE` | `deps.py` | Optional | Relaxes auth checks |
| `ANTHROPIC_API_KEY` | various | Optional | Alt AI provider |
| `GOOGLE_AI_KEY` | various | Optional | Alt AI provider |
| `WEATHER_API_KEY` | various | Optional | Alt weather provider |
| `AGRONOMY_KB_PATH` | knowledge base | Optional | Custom KB path |
| `INSTITUTIONAL_API_KEY` | institutional routes | Optional | Institution API key |
| `PROACTIVE_TARGETS_JSON` | proactive intelligence | Optional | Alert targets |

*At least one of the JWT verification methods must be set for auth to work.

### Frontend (Vercel)

| Variable | Notes |
|---|---|
| `NEXT_PUBLIC_API_URL` | Backend base URL (inlines at build time) |
| `NEXT_PUBLIC_ARCGIS_API_KEY` | Now unused after keyless Esri switch |

### DB Connection Pattern

**File:** `database.py`

- **Pool:** `psycopg2.pool.ThreadedConnectionPool(minconn=2, maxconn=20)`
- **Per-request:** `get_db_connection()` returns a `_PooledConn` wrapper. `.close()` returns to pool.
- **Context manager:** `with get_db_connection() as conn:` supported.
- **Transactions:** Manual `conn.commit()` / `conn.rollback()`. No autocommit.
- **Cursor:** Always `RealDictCursor` at call sites.

**Task 2 safety pattern:** Snapshot writes get their own connection from the pool (`get_db_connection()`), commit/rollback independently. A snapshot failure cannot poison the read connection used by the field-state response. The pool's 20-connection ceiling is adequate.

### Deploy / Migration Commands

- **Backend deploy:** Render hosts the backend via Dockerfile (`uvicorn app:app --host 0.0.0.0 --port 8000`). **No auto-deploy on push** confirmed — only a manual demo-backfill GitHub Action exists (`.github/workflows/demo-backfill.yml`, `workflow_dispatch`).
- **Frontend deploy:** Vercel hosts `kurima-sense`. Auto-deploy behavior not confirmed from repo (no Vercel config in repo).
- **Migration run:** Standalone Python scripts against the Render DB:
  ```bash
  DATABASE_URL="..." python migrate_create_tenants.py
  ```
  Not wired into deploy — run manually before/after code deploys as needed.

### Test Runners

- **Backend:** `pytest tests/` — 14 test files, ~185 test functions. No conftest.py or pytest.ini.
- **Frontend:** `tsx --test 'tests/**/*.test.ts'` — 11 test files (confirmed in `package.json`).

---

## CLAUDE.md Corrections

1. **`yield_projection` field name:** Correct at top level (`FieldState.yield_projection`). The yield value within it is `projected_tonnes_per_ha` (confirmed, no correction needed — spec was right to be cautious).
2. **`_build_yield` / `_fetch_yield`:** Both exist. `_fetch_yield` (line 872) calls the yield model; `_build_yield` (line 481) maps raw dict to Pydantic. Spec was correct.
3. **Auth tables:** `chat_logs`, `user_events`, `knowledge_base` — confirmed `chat_logs` and `user_events` in `database.py`. Knowledge base uses file-based KB (`AGRONOMY_KB_PATH`), not a DB table.
4. **Auto-deploy:** No auto-deploy on push to main for either repo (from repo config).
5. **Backend test count:** ~185 tests (not 111+ as stated — the suite has grown).
6. **`daily_logs` extra columns:** Table also has `user_id` and `insight_text` columns not mentioned in CLAUDE.md (but not relevant to Sprint 1).
7. **`fields` has NO `deleted_at` column.** Unlike `tenants` and `growers` (which soft-delete), `fields` is **hard-deleted** (`DELETE FROM fields` in `app.py:1206`, `scripts/seed_demo_fields.py:288`). No query in the repo filters `fields` by `deleted_at`. Tenant-scoped field lookups must NOT add `deleted_at IS NULL` — that column does not exist and would raise. (Caught in the cross-model review; `resolve_access` in the aggregator correctly omits it.)
8. **`fields.natural_region`** is added idempotently by the demo seeder (`ALTER TABLE fields ADD COLUMN IF NOT EXISTS natural_region TEXT`) and is hard-referenced by existing operational scripts (`recompute_kurima_scores.py:56`). It exists on the seeded live DB. The calibration backtest/recompute read it directly; on a fresh non-seeded DB the seeder must run first.

## Cross-model review corrections (post-Opus review of the Sonnet draft)

These bugs were found re-auditing the first-pass implementation and are now fixed:
- **`outcome_routes._resolve_field_for_tenant`** filtered `fields` by a non-existent `deleted_at` column (would 500 on every harvest call) and failed to `SELECT user_id` (legacy consumer fallback silently dead). Both fixed; regression test added (`TestResolveQuerySchema`).
- **Harvest insert/list** used `RETURNING *, id::text AS id` (fragile duplicate columns); replaced with an explicit `_HARVEST_COLS` list matching the `grower_routes` convention.
- **`admin/calibration/recompute`** paired projections to harvests via `season_year = EXTRACT(YEAR FROM projection_date)` — wrong for tobacco (planted in the prior calendar year). Now pairs on the season window (`projection_date BETWEEN planting_date AND COALESCE(harvest_date, planting_date + 365d)`).
- **`get_calibration` `is_validated`** wrongly excluded `historical_backfill` (that IS the real contractor-book path) and would have mislabeled fabricated demo-field actuals as validated. Now: validated = real actuals exist on **non-demo** fields (`name NOT LIKE 'DEMO_SEED:%'`).
- **`get_calibration` headline** sorted by bucket string, so `"unknown"` outranked real buckets. Now uses an explicit bucket rank (70-100% > 50-70% > 0-50% > unknown), and dedupes to the latest row per segment via `DISTINCT ON`.
- **Backtest harness** `is_sample` detection referenced columns not in the SELECT and had inverted logic; now flags SAMPLE if any demo-seeded field is touched or any actual isn't from a trusted real source. Backtest projection writes are now idempotent (`ON CONFLICT` on a new partial unique index) and anchor on the harvest's own `planting_date` for multi-season correctness.
