-- KurimaSense Zimbabwe Crop Varieties Schema
-- Migration 001: Create crop_varieties table
-- Run: psql $DATABASE_URL -f backend/db/migrations/001_create_crop_varieties.sql

-- Drop existing table if recreating
-- DROP TABLE IF EXISTS crop_varieties CASCADE;

-- Create crop_varieties table
CREATE TABLE IF NOT EXISTS crop_varieties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Core identification
    crop_name TEXT NOT NULL,              -- e.g. 'Maize', 'Tobacco', 'Soybeans'
    variety_name TEXT NOT NULL,           -- e.g. 'SC 727', 'KRK26R', 'Star 3311'
    breeder TEXT,                         -- e.g. 'Seed Co', 'Kutsaga', 'Starke Ayres'
    
    -- Maturity & Yield
    days_to_maturity INTEGER,             -- Days from planting to harvest
    yield_potential_low DECIMAL(10,2),    -- Low end yield (t/ha or t/ha for veg)
    yield_potential_high DECIMAL(10,2),   -- High end yield potential
    
    -- Descriptive
    description TEXT,                     -- Human-readable description
    
    -- JSONB characteristics for flexible traits storage
    -- Common keys:
    --   drought_tolerance: "low" | "moderate" | "high" | "very high"
    --   heat_tolerance: "low" | "moderate" | "high"
    --   disease_resistance: ["Grey Leaf Spot", "Rust", ...]
    --   region_suitability: ["Natural Region I", "Natural Region II", ...]
    --   gls_tolerance: "low" | "moderate" | "high" | "very high"
    --   grain_type: "white dent", "white flint", etc.
    --   growth_habit: "Determinate", "Indeterminate"
    --   style: "Lemon", "Orange/Mahogany" (for tobacco)
    --   use: ["Food", "Brewing", "Processing"]
    characteristics JSONB,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Unique constraint on crop + variety
    UNIQUE(crop_name, variety_name)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_crop_varieties_crop_name ON crop_varieties(crop_name);
CREATE INDEX IF NOT EXISTS idx_crop_varieties_breeder ON crop_varieties(breeder);
CREATE INDEX IF NOT EXISTS idx_crop_varieties_days_to_maturity ON crop_varieties(days_to_maturity);

-- GIN index for JSONB characteristics search
CREATE INDEX IF NOT EXISTS idx_crop_varieties_characteristics ON crop_varieties USING GIN (characteristics);

-- Add trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_crop_varieties_updated_at ON crop_varieties;
CREATE TRIGGER update_crop_varieties_updated_at
    BEFORE UPDATE ON crop_varieties
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Sample queries for reference:

-- Get all maize varieties
-- SELECT variety_name, days_to_maturity, yield_potential_high 
-- FROM crop_varieties 
-- WHERE crop_name = 'Maize' 
-- ORDER BY days_to_maturity;

-- Get drought-tolerant varieties
-- SELECT crop_name, variety_name, characteristics->>'drought_tolerance' as drought
-- FROM crop_varieties 
-- WHERE characteristics->>'drought_tolerance' IN ('high', 'very high');

-- Get varieties suitable for Natural Region IV
-- SELECT crop_name, variety_name 
-- FROM crop_varieties 
-- WHERE characteristics->'region_suitability' ? 'Natural Region IV';

-- Full-text search in description
-- SELECT variety_name, description 
-- FROM crop_varieties 
-- WHERE description ILIKE '%drought%';

COMMENT ON TABLE crop_varieties IS 'Zimbabwe crop varieties knowledge base for AI agronomist';
COMMENT ON COLUMN crop_varieties.characteristics IS 'JSONB field for flexible trait storage (drought_tolerance, disease_resistance, region_suitability, etc.)';
