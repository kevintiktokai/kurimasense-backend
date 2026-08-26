-- 028: make the weather cache survive a restart.
--
-- WHY
-- ---
-- `climate_service` already had the right resilience model — TTL cache,
-- single-flight, serve-stale-on-error — and on 26 Aug 2026 it still served the
-- farmer nothing, because the cache lives in the process and Render restarts
-- the process on every deploy.
--
-- The sequence from the production logs:
--
--   09:37–09:46  Open-Meteo returns 429 for every call. The shared Render
--                egress IP is over its free-tier quota. Stale-serve is what
--                should carry us through this.
--   09:55        Deploy. New process, empty cache.
--   ...          Every key is now a miss with nothing behind it. The layer
--                built to survive this outage has nothing to survive it with.
--
-- The data needed to keep the app useful existed twenty minutes earlier and was
-- thrown away at the exact moment it was needed. This table is where it goes
-- instead.
--
-- SHAPE
-- -----
-- Read only when an upstream fetch has already failed, so the healthy path never
-- pays for it. Written through on every success.
--
-- No pruning, deliberately. `cache_key` is (endpoint × snapped grid square) and
-- both are bounded — the coordinate grid is 0.05 deg, so a farm's worth of
-- fields collapse to one key. The table upserts in place and settles at a few
-- hundred rows however long it runs. A cleanup job here would be code that
-- never has anything to do.

CREATE TABLE IF NOT EXISTS climate_cache (
    cache_key    TEXT PRIMARY KEY,
    fetched_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ttl_seconds  INTEGER     NOT NULL,
    payload      JSONB       NOT NULL
);

-- Reads are all by primary key. This index is for the operator question — "how
-- stale is what we are serving?" — and for a manual purge if a bad payload ever
-- needs clearing out.
CREATE INDEX IF NOT EXISTS idx_climate_cache_fetched ON climate_cache(fetched_at);

-- No RLS policy, and that is not an oversight: there is no tenant in here.
-- Rows are weather for a 5.5 km grid square, keyed by a coordinate that has
-- already been snapped away from any field boundary, and the same row serves
-- every grower in that square. Nothing in it is derived from, or attributable
-- to, a particular farm.

-- Verify:
--   SELECT cache_key, ttl_seconds, NOW() - fetched_at AS age FROM climate_cache
--   ORDER BY fetched_at DESC LIMIT 10;
--
-- Rollback:
--   DROP TABLE climate_cache;
--   (climate_service degrades to the in-memory cache it had before — every
--   durable read and write is already wrapped so a missing table only logs)
