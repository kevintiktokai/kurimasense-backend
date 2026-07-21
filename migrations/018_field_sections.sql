-- 018_field_sections.sql
-- ============================================================================
-- Zone-level satellite analysis (field sections): one row per zone per batch.
-- The table also self-heals via database.init_db (and is mirrored in 015) —
-- this migration is the canonical definition PLUS the RLS posture, which the
-- self-heal deliberately does not manage.
--
-- RLS: tenant-scoped like daily_logs — rows carry the parent field's
-- tenant_id and are visible only when the transaction GUC contains it
-- (app_tenant_ids(), migration 008). Deny-by-default for anon/authenticated
-- PostgREST clients; part of the FORCE isolation set once Step D lands.
-- ============================================================================

CREATE TABLE IF NOT EXISTS field_section_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_id UUID NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
    tenant_id UUID,
    batch_id UUID NOT NULL,
    grid_size INTEGER NOT NULL DEFAULT 2,
    section_index INTEGER NOT NULL,
    section_label TEXT,
    polygon JSONB,
    centroid JSONB,
    area_share REAL,
    ndvi DOUBLE PRECISION,
    evi DOUBLE PRECISION,
    cloud_cover DOUBLE PRECISION,
    status TEXT DEFAULT 'ok',
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_section_analysis_field
    ON field_section_analysis(field_id, grid_size, created_at DESC);

ALTER TABLE field_section_analysis ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS ts_field_section_analysis ON public.field_section_analysis;
CREATE POLICY ts_field_section_analysis ON public.field_section_analysis
    FOR ALL
    USING (tenant_id = ANY (app_tenant_ids()))
    WITH CHECK (tenant_id = ANY (app_tenant_ids()));

-- Rollback:
--   DROP POLICY IF EXISTS ts_field_section_analysis ON public.field_section_analysis;
--   ALTER TABLE field_section_analysis NO FORCE ROW LEVEL SECURITY;
--   ALTER TABLE field_section_analysis DISABLE ROW LEVEL SECURITY;
--   DROP TABLE field_section_analysis;
