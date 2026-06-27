-- Migration 007: scouting_observations (Sprint 3 — grower capture persistence)
-- Durable storage for field scouting reports (previously localStorage-only pins).
-- Idempotent. RLS enabled deny-by-default (backend postgres owner bypasses; the
-- public anon/authenticated keys are denied) — consistent with migrations 004/005.

CREATE TABLE IF NOT EXISTS scouting_observations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_id UUID REFERENCES fields(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES tenants(id),
    user_id UUID,
    category TEXT
        CHECK (category IN ('pest','disease','weed','water','nutrient','general')),
    severity TEXT
        CHECK (severity IN ('low','medium','high','critical')),
    notes TEXT,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    photo_url TEXT,
    diagnosis JSONB,
    observed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source TEXT DEFAULT 'grower_logged'
        CHECK (source IN ('grower_logged','ai_diagnosis','institution_recorded')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_scouting_field ON scouting_observations(field_id, observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_scouting_tenant ON scouting_observations(tenant_id);

ALTER TABLE scouting_observations ENABLE ROW LEVEL SECURITY;
