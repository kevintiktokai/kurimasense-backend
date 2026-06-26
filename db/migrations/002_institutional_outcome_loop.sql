-- Migration 002: Institutional Outcome Loop Tables
-- Sprint 1 — yield_projections, harvest_records, model_calibration
-- Idempotent: running twice is a clean no-op.

CREATE TABLE IF NOT EXISTS yield_projections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_id UUID REFERENCES fields(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES tenants(id),
    projection_date DATE DEFAULT CURRENT_DATE,
    projected_tonnes_per_ha DECIMAL(10,2),
    confidence_band TEXT,
    confidence_pct INTEGER CHECK (confidence_pct BETWEEN 0 AND 100),
    model_version TEXT NOT NULL,
    is_backtest BOOLEAN DEFAULT FALSE,
    season_progress_pct INTEGER,
    inputs_snapshot JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
-- One live projection per field per day (idempotent daily snapshot upsert).
CREATE UNIQUE INDEX IF NOT EXISTS idx_yield_proj_field_date_bt
    ON yield_projections(field_id, projection_date, is_backtest)
    WHERE is_backtest = FALSE;
-- One backtest projection per field per checkpoint date (idempotent re-runs).
CREATE UNIQUE INDEX IF NOT EXISTS idx_yield_proj_backtest
    ON yield_projections(field_id, projection_date, season_progress_pct)
    WHERE is_backtest = TRUE;
CREATE INDEX IF NOT EXISTS idx_yield_proj_field ON yield_projections(field_id, projection_date DESC);
CREATE INDEX IF NOT EXISTS idx_yield_proj_tenant ON yield_projections(tenant_id);

CREATE TABLE IF NOT EXISTS harvest_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_id UUID REFERENCES fields(id) ON DELETE CASCADE,
    grower_id UUID REFERENCES growers(id),
    tenant_id UUID REFERENCES tenants(id),
    season_year INTEGER NOT NULL,
    season_type TEXT DEFAULT 'summer',
    crop_type TEXT,
    variety TEXT,
    planting_date DATE,
    harvest_date DATE,
    area_harvested_ha DECIMAL(10,2),
    actual_yield_tonnes DECIMAL(10,2),
    quality_grade TEXT,
    moisture_at_harvest DECIMAL(5,2),
    sale_price_per_tonne DECIMAL(12,2),
    delivered_to_tenant BOOLEAN,
    source TEXT DEFAULT 'grower_logged'
        CHECK (source IN ('grower_logged','historical_backfill','institution_recorded')),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_harvest_field ON harvest_records(field_id);
CREATE INDEX IF NOT EXISTS idx_harvest_tenant_season ON harvest_records(tenant_id, season_year);

CREATE TABLE IF NOT EXISTS model_calibration (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crop_type TEXT,
    natural_region TEXT,
    variety TEXT,
    season_progress_bucket TEXT,
    model_version TEXT NOT NULL,
    n_observations INTEGER,
    mae_pct DECIMAL(6,2),
    rmse DECIMAL(10,3),
    bias_pct DECIMAL(6,2),
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_calibration_lookup ON model_calibration(crop_type, natural_region, variety, model_version);
