-- Enable PostGIS if available (Supabase supports it)
CREATE EXTENSION IF NOT EXISTS postgis;

-- Fields Table
CREATE TABLE IF NOT EXISTS fields (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL DEFAULT 'web-user-01', -- Mock user for now
    name TEXT NOT NULL,
    crop TEXT NOT NULL DEFAULT 'Maize',
    area_hectares FLOAT,
    polygon_coordinates JSONB, -- Storing as JSONB for ease, could be GEOMETRY
    health_score FLOAT DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Field Inputs (Log of seeds, fertilizer, etc.)
CREATE TABLE IF NOT EXISTS field_inputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_id UUID REFERENCES fields(id) ON DELETE CASCADE,
    input_date DATE DEFAULT CURRENT_DATE,
    input_type TEXT NOT NULL, -- 'Seed', 'Fertilizer', 'Pesticide'
    quantity FLOAT NOT NULL,
    unit TEXT NOT NULL, -- 'kg', 'liters', 'count'
    cost FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Daily Satellite/Weather Logs
CREATE TABLE IF NOT EXISTS daily_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_id UUID REFERENCES fields(id) ON DELETE CASCADE,
    log_date DATE DEFAULT CURRENT_DATE,
    ndvi FLOAT,
    evi FLOAT,
    soil_moisture FLOAT,
    cloud_cover FLOAT,
    source TEXT DEFAULT 'Sentinel-2',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(field_id, log_date)
);

-- Alerts Table
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_id UUID REFERENCES fields(id) ON DELETE SET NULL,
    type TEXT NOT NULL, -- 'Critical', 'Warning', 'Info'
    message TEXT NOT NULL,
    severity TEXT DEFAULT 'Medium',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
