-- 015_bootstrap_schema.sql
-- ============================================================================
-- The complete runtime schema, captured as a migration (RLS Step D unblocking,
-- July 2026). Until now this DDL lived in database.init_db() and
-- services/notifications/repository.ensure_schema() and ran on every boot
-- ("self-healing schema"). That pattern is incompatible with running the
-- backend as a locked-down NOBYPASSRLS role (which must not own tables or run
-- DDL), so the schema now converges here instead.
--
-- Idempotent: every statement is IF NOT EXISTS / ADD COLUMN IF NOT EXISTS, so
-- applying this against the live database is a no-op where objects already
-- exist. Apply as the table-owning role (postgres), NOT as the app role.
--
-- After applying, set DB_SELF_HEAL_SCHEMA=false on the backend so boot stops
-- issuing DDL (see database.schema_self_heal_enabled).
-- ============================================================================

CREATE TABLE IF NOT EXISTS chat_logs (
    id SERIAL PRIMARY KEY,
    user_id TEXT, -- Can be UUID or 'web-user-xx'
    role TEXT,
    content TEXT,
    field_context_id TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    title TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE chat_logs ADD COLUMN IF NOT EXISTS session_id UUID;
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user ON chat_sessions(user_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_logs_session ON chat_logs(session_id, created_at);

CREATE TABLE IF NOT EXISTS fields (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    crop_type TEXT,
    polygon_coordinates JSONB,
    size_hectares DECIMAL(10,2),
    health_score INTEGER,
    planting_date DATE,
    variety TEXT,
    fertilizer_history TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='fields' AND column_name='user_id') THEN
        ALTER TABLE fields ADD COLUMN user_id TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='fields' AND column_name='planting_date') THEN
        ALTER TABLE fields ADD COLUMN planting_date DATE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='fields' AND column_name='variety') THEN
        ALTER TABLE fields ADD COLUMN variety TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='fields' AND column_name='fertilizer_history') THEN
        ALTER TABLE fields ADD COLUMN fertilizer_history TEXT;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS daily_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_id UUID REFERENCES fields(id) ON DELETE CASCADE,
    user_id UUID, -- Added for isolation
    log_date DATE DEFAULT CURRENT_DATE,
    ndvi DOUBLE PRECISION,
    evi DOUBLE PRECISION,
    soil_moisture DOUBLE PRECISION,
    cloud_cover DOUBLE PRECISION,
    source TEXT DEFAULT 'Sentinel-2',
    insight_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE daily_logs ADD COLUMN IF NOT EXISTS sar_vv_db DOUBLE PRECISION;
ALTER TABLE daily_logs ADD COLUMN IF NOT EXISTS sar_vh_db DOUBLE PRECISION;

CREATE TABLE IF NOT EXISTS field_inputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_id UUID REFERENCES fields(id) ON DELETE CASCADE,
    user_id UUID, -- Added for isolation
    input_type TEXT,
    quantity DECIMAL(10,2),
    unit TEXT,
    input_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT, -- Can be UUID or 'web-user-xx'
    event_type TEXT,     -- e.g. 'feature_usage', 'user_action'
    event_name TEXT,     -- e.g. 'weather_check', 'yield_projection'
    event_data JSONB,    -- e.g. { "location": "Harare" }
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS crop_varieties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crop_name TEXT NOT NULL,         -- e.g. 'Maize', 'Tobacco'
    variety_name TEXT NOT NULL,      -- e.g. 'SC 727', 'K RK26R'
    breeder TEXT,                    -- e.g. 'Seed Co', 'Kutsaga'
    days_to_maturity INTEGER,        -- e.g. 155
    yield_potential_low DECIMAL(10,2), -- t/ha
    yield_potential_high DECIMAL(10,2), -- t/ha
    description TEXT,
    characteristics JSONB,           -- e.g. { "disease_resistance": [...], "drought_tolerance": "High" }
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(crop_name, variety_name)
);

CREATE TABLE IF NOT EXISTS farm_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    field_id UUID REFERENCES fields(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    activity_type TEXT NOT NULL, -- irrigation, spraying, scouting, harvest, fertilize, custom
    priority TEXT NOT NULL,      -- urgent, high, normal, low
    task_date DATE DEFAULT CURRENT_DATE,
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP WITH TIME ZONE,
    is_ai_generated BOOLEAN DEFAULT FALSE,
    recurring_rule JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS soil_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_id UUID NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    profile JSONB NOT NULL DEFAULT '{}'::jsonb,
    provider_status JSONB NOT NULL DEFAULT '{}'::jsonb,
    schema_version INTEGER NOT NULL DEFAULT 1,
    built_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    refresh_after TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (field_id)
);

ALTER TABLE tenant_members DROP CONSTRAINT IF EXISTS tenant_members_member_role_check;
ALTER TABLE tenant_members ADD CONSTRAINT tenant_members_member_role_check
    CHECK (member_role IN ('owner', 'admin', 'manager', 'agronomist',
                           'field_officer', 'analyst', 'officer', 'viewer'));
ALTER TABLE tenant_members ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'active';
ALTER TABLE tenant_members ADD COLUMN IF NOT EXISTS display_name TEXT;
ALTER TABLE tenant_members ADD COLUMN IF NOT EXISTS email TEXT;

CREATE TABLE IF NOT EXISTS team_invites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email TEXT,
    member_role TEXT NOT NULL DEFAULT 'field_officer',
    code TEXT NOT NULL UNIQUE,
    invited_by_user_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    accepted_at TIMESTAMP WITH TIME ZONE,
    accepted_by_user_id UUID,
    revoked_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS field_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    field_id UUID NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    activity_type TEXT NOT NULL,
    title TEXT NOT NULL,
    notes TEXT,
    recommendation TEXT,
    visit_date DATE DEFAULT CURRENT_DATE,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    photo_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS field_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    field_id UUID NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
    assignee_user_id UUID NOT NULL,
    assigned_by_user_id UUID,
    note TEXT,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    unassigned_at TIMESTAMP WITH TIME ZONE
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_field_assignments_active
    ON field_assignments(field_id) WHERE unassigned_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_fields_user_id        ON fields(user_id);
CREATE INDEX IF NOT EXISTS idx_daily_logs_field_id   ON daily_logs(field_id);
CREATE INDEX IF NOT EXISTS idx_daily_logs_field_date ON daily_logs(field_id, log_date DESC);
CREATE INDEX IF NOT EXISTS idx_farm_tasks_user_date  ON farm_tasks(user_id, task_date);

-- NEW: Critical indexes for slow queries identified in performance audit
CREATE INDEX IF NOT EXISTS idx_chat_logs_user_date   ON chat_logs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_logs_user_field  ON chat_logs(user_id, field_context_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_field_inputs_field    ON field_inputs(field_id, input_date DESC);
CREATE INDEX IF NOT EXISTS idx_farm_tasks_user_status ON farm_tasks(user_id, completed, priority);
CREATE INDEX IF NOT EXISTS idx_user_events_user      ON user_events(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_daily_logs_user       ON daily_logs(user_id, log_date DESC);

CREATE INDEX IF NOT EXISTS idx_soil_profiles_field   ON soil_profiles(field_id);
CREATE INDEX IF NOT EXISTS idx_soil_profiles_refresh ON soil_profiles(refresh_after);

CREATE INDEX IF NOT EXISTS idx_team_invites_tenant      ON team_invites(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_field_activities_field   ON field_activities(field_id, visit_date DESC);
CREATE INDEX IF NOT EXISTS idx_field_activities_tenant  ON field_activities(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_field_activities_user    ON field_activities(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_field_assignments_assignee ON field_assignments(assignee_user_id) WHERE unassigned_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_field_assignments_field    ON field_assignments(field_id, assigned_at DESC);

-- ── Notification subsystem (from services/notifications/repository.py) ──

CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    category TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'info',
    title TEXT NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    field_id UUID,
    action_url TEXT,
    data JSONB NOT NULL DEFAULT '{}'::jsonb,
    dedupe_key TEXT,
    source TEXT NOT NULL DEFAULT 'system',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    read_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_notifications_user_dedupe
    ON notifications(user_id, dedupe_key) WHERE dedupe_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_notifications_user_created
    ON notifications(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_user_unread
    ON notifications(user_id) WHERE read_at IS NULL;

CREATE TABLE IF NOT EXISTS notification_deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notification_id UUID NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
    channel TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',   -- pending | sent | failed | skipped
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    deliver_after TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_notification_deliveries_due
    ON notification_deliveries(deliver_after) WHERE status = 'pending';

CREATE TABLE IF NOT EXISTS notification_preferences (
    user_id TEXT PRIMARY KEY,
    preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS notification_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    platform TEXT NOT NULL DEFAULT 'android',  -- android | ios | web
    token TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_notification_devices_user ON notification_devices(user_id);
