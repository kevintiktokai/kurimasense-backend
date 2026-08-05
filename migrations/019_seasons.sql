-- 019_seasons.sql
-- ============================================================================
-- Seasons: the temporal crop record, split out from `fields`.
--
-- Before this migration a field *was* its current season — crop_type,
-- planting_date and variety were single-valued columns on `fields`, so planting
-- a new crop overwrote the previous one and rotation history was unrecoverable.
-- This table gives every crop cycle its own row, which unlocks (all blocked on
-- the same missing entity): multi-season history, rotation-aware advice,
-- residue-inoculum disease risk, pre-plant planning, and yield-gap attribution.
--
-- `fields` keeps its crop/planting columns as a READ-THROUGH CACHE of the
-- active season so every existing endpoint and screen keeps working unchanged.
-- services/seasons/service.py maintains that mirror on write. Dropping the
-- mirrored columns is a later cleanup, deliberately not part of this migration.
--
-- Lifecycle:  planned → active → harvested → closed   (also: abandoned)
--   planned   — a pre-plant record; crop chosen, not yet in the ground
--   active    — planted; exactly one per field, enforced by a partial unique index
--   harvested — off the field, post-harvest (drying/storage) still in progress
--   closed    — season finished; yield recorded, eligible for retrospective
--
-- RLS: tenant-scoped like daily_logs / field_section_analysis — rows carry the
-- parent field's tenant_id and are visible only when the transaction GUC
-- contains it (app_tenant_ids(), migration 008).
-- ============================================================================

CREATE TABLE IF NOT EXISTS seasons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_id UUID NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
    tenant_id UUID,
    user_id TEXT,

    status TEXT NOT NULL DEFAULT 'planned',
    season_label TEXT,

    crop_type TEXT NOT NULL,
    variety TEXT,

    planned_planting_date DATE,
    planting_date DATE,
    transplant_date DATE,
    expected_harvest_date DATE,
    harvest_date DATE,

    -- Establishment. Targets are set pre-plant; established_* is measured by
    -- the Stand Check after emergence. The established population is the
    -- denominator the KurimaScore needs to tell a thin stand apart from a
    -- stressed one — see docs/farmer_growth_cycle_research.md §2.4.
    row_spacing_cm NUMERIC(5,1),
    in_row_spacing_cm NUMERIC(5,1),
    target_population_per_ha INTEGER,
    seed_rate_kg_ha NUMERIC(6,2),
    planting_depth_cm NUMERIC(4,1),
    emergence_date DATE,
    established_population_per_ha INTEGER,
    emergence_uniformity TEXT,

    -- Rotation & residue context. The crop profiles already model residue-borne
    -- inoculum in detail ("worse under continuous maize"); without these
    -- columns none of that knowledge could be applied.
    previous_crop TEXT,
    tillage_practice TEXT,
    residue_management TEXT,

    yield_tonnes_per_ha NUMERIC(8,3),
    notes TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_seasons_field_status
    ON seasons(field_id, status);

-- History queries walk backwards through closed seasons by planting date.
CREATE INDEX IF NOT EXISTS idx_seasons_field_planting
    ON seasons(field_id, planting_date DESC);

-- At most one live season per field. Any number of planned/harvested/closed.
CREATE UNIQUE INDEX IF NOT EXISTS idx_seasons_one_active
    ON seasons(field_id) WHERE status = 'active';

-- --------------------------------------------------------------------------
-- Season attribution on existing observation/input tables.
-- Nullable throughout: pre-migration rows that predate any season stay
-- readable, and the field-level queries that ignore season_id keep working.
-- --------------------------------------------------------------------------
ALTER TABLE daily_logs             ADD COLUMN IF NOT EXISTS season_id UUID REFERENCES seasons(id) ON DELETE SET NULL;
ALTER TABLE field_inputs           ADD COLUMN IF NOT EXISTS season_id UUID REFERENCES seasons(id) ON DELETE SET NULL;
ALTER TABLE field_activities       ADD COLUMN IF NOT EXISTS season_id UUID REFERENCES seasons(id) ON DELETE SET NULL;
ALTER TABLE field_section_analysis ADD COLUMN IF NOT EXISTS season_id UUID REFERENCES seasons(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_daily_logs_season ON daily_logs(season_id, log_date);

-- --------------------------------------------------------------------------
-- Backfill: one active season per already-planted field.
-- Idempotent — the NOT EXISTS guard means re-running adds nothing.
-- --------------------------------------------------------------------------
INSERT INTO seasons (
    field_id, tenant_id, user_id, status, crop_type, variety,
    planting_date, transplant_date, created_at
)
SELECT f.id, f.tenant_id, f.user_id, 'active', COALESCE(f.crop_type, 'Unknown'),
       f.variety, f.planting_date, f.transplant_date, f.created_at
FROM fields f
WHERE f.planting_date IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM seasons s WHERE s.field_id = f.id);

-- Attribute existing observations to that season by date. Rows older than the
-- planting date belong to a season we have no record of, and stay NULL.
UPDATE daily_logs dl
SET season_id = s.id
FROM seasons s
WHERE dl.field_id = s.field_id
  AND dl.season_id IS NULL
  AND s.planting_date IS NOT NULL
  AND dl.log_date >= s.planting_date;

UPDATE field_inputs fi
SET season_id = s.id
FROM seasons s
WHERE fi.field_id = s.field_id
  AND fi.season_id IS NULL
  AND s.planting_date IS NOT NULL
  AND fi.input_date >= s.planting_date;

UPDATE field_activities fa
SET season_id = s.id
FROM seasons s
WHERE fa.field_id = s.field_id
  AND fa.season_id IS NULL
  AND s.planting_date IS NOT NULL
  AND fa.visit_date >= s.planting_date;

-- --------------------------------------------------------------------------
-- RLS
-- --------------------------------------------------------------------------
ALTER TABLE seasons ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS ts_seasons ON public.seasons;
CREATE POLICY ts_seasons ON public.seasons
    FOR ALL
    USING (tenant_id = ANY (app_tenant_ids()))
    WITH CHECK (tenant_id = ANY (app_tenant_ids()));

-- Rollback:
--   DROP POLICY IF EXISTS ts_seasons ON public.seasons;
--   ALTER TABLE seasons DISABLE ROW LEVEL SECURITY;
--   ALTER TABLE daily_logs             DROP COLUMN IF EXISTS season_id;
--   ALTER TABLE field_inputs           DROP COLUMN IF EXISTS season_id;
--   ALTER TABLE field_activities       DROP COLUMN IF EXISTS season_id;
--   ALTER TABLE field_section_analysis DROP COLUMN IF EXISTS season_id;
--   DROP TABLE seasons;
