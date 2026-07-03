-- Migration 012 — Soil Intelligence profiles
--
-- Persistent, per-field soil intelligence. One row per field holds the merged
-- multi-provider Soil Intelligence Profile as JSONB (each attribute carries its
-- own source/confidence/acquired_at/refresh_policy metadata — see
-- services/soil_intelligence/models.py). The profile is fetched once at field
-- creation and reused locally; ``refresh_after`` drives the lifecycle so the
-- system avoids re-downloading data that rarely changes.
--
-- Mirrors the field-scoped RLS pattern used for daily_logs/field_inputs
-- (migration 008): RLS enabled + a tenant policy that scopes through the parent
-- field. Safe/reversible — the backend connects as table owner and bypasses RLS
-- unless FORCE is set, exactly like the sibling tables.

CREATE TABLE IF NOT EXISTS soil_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_id UUID NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    profile JSONB NOT NULL DEFAULT '{}'::jsonb,       -- full SoilProfile.to_dict()
    provider_status JSONB NOT NULL DEFAULT '{}'::jsonb,
    schema_version INTEGER NOT NULL DEFAULT 1,
    built_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    refresh_after TIMESTAMP WITH TIME ZONE,           -- next eligible refresh
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (field_id)
);

CREATE INDEX IF NOT EXISTS idx_soil_profiles_field ON soil_profiles(field_id);
CREATE INDEX IF NOT EXISTS idx_soil_profiles_refresh ON soil_profiles(refresh_after);

ALTER TABLE soil_profiles ENABLE ROW LEVEL SECURITY;

-- Tenant policy: scope through the parent field's tenant (same shape as
-- ts_daily_logs). Additive/permissive; owner bypasses until FORCE is enabled.
DROP POLICY IF EXISTS ts_soil_profiles ON public.soil_profiles;
CREATE POLICY ts_soil_profiles ON public.soil_profiles
    FOR ALL
    USING (field_id IN (SELECT id FROM public.fields WHERE tenant_id = ANY (public.app_tenant_ids())))
    WITH CHECK (field_id IN (SELECT id FROM public.fields WHERE tenant_id = ANY (public.app_tenant_ids())));

-- ─────────────────────────────────────────────────────────────────────────────
-- ROLLBACK (manual):
--   DROP POLICY IF EXISTS ts_soil_profiles ON public.soil_profiles;
--   DROP TABLE IF EXISTS soil_profiles;
-- ─────────────────────────────────────────────────────────────────────────────
