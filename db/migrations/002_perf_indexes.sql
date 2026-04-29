-- Migration 002: Performance indexes for hot-path endpoints
--
-- Targets every WHERE / JOIN column hit by the endpoints audited in the
-- backend latency pass.  All statements are idempotent (IF NOT EXISTS) so
-- this can be re-run safely on environments that already have a subset.
--
-- Run: psql $DATABASE_URL -f db/migrations/002_perf_indexes.sql

-- fields: GET /fields, /dashboard/init, /dashboard, every /fields/{id}/*
CREATE INDEX IF NOT EXISTS idx_fields_user_id          ON fields(user_id);
CREATE INDEX IF NOT EXISTS idx_fields_user_created     ON fields(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_fields_id_user          ON fields(id, user_id);

-- daily_logs: /fields/{id}/insight, /fields/{id}/history, /fields list LATERAL
CREATE INDEX IF NOT EXISTS idx_daily_logs_field_id     ON daily_logs(field_id);
CREATE INDEX IF NOT EXISTS idx_daily_logs_field_date   ON daily_logs(field_id, log_date DESC);

-- field_inputs: /inputs writes, agronomic feedback loop, yield invalidation
CREATE INDEX IF NOT EXISTS idx_field_inputs_field_date ON field_inputs(field_id, input_date DESC);
CREATE INDEX IF NOT EXISTS idx_field_inputs_user_id    ON field_inputs(user_id);

-- chat_logs: /chat/history (most common ordering: user + created_at)
CREATE INDEX IF NOT EXISTS idx_chat_logs_user_created  ON chat_logs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_logs_user_field    ON chat_logs(user_id, field_context_id, created_at DESC);

-- farm_tasks: /ai/tasks (today), /ai/tasks/history, /ai/insights
CREATE INDEX IF NOT EXISTS idx_farm_tasks_user_date    ON farm_tasks(user_id, task_date);
CREATE INDEX IF NOT EXISTS idx_farm_tasks_field        ON farm_tasks(field_id);
CREATE INDEX IF NOT EXISTS idx_farm_tasks_user_completed_priority
    ON farm_tasks(user_id, completed, priority);

-- yield_history: /fields/{id}/yield-history, /yield-analytics
CREATE INDEX IF NOT EXISTS idx_yield_history_user      ON yield_history(user_id);
CREATE INDEX IF NOT EXISTS idx_yield_history_field     ON yield_history(field_id);
CREATE INDEX IF NOT EXISTS idx_yield_history_user_field_year
    ON yield_history(user_id, field_id, season_year DESC);

-- crop_varieties: /crops/{name}/varieties, variety join in /dashboard
-- (idx_crop_varieties_crop_name already exists from migration 001)
CREATE INDEX IF NOT EXISTS idx_crop_varieties_crop_variety_lower
    ON crop_varieties(LOWER(crop_name), LOWER(variety_name));

-- user_events: /events analytics, optional but cheap
CREATE INDEX IF NOT EXISTS idx_user_events_user_id     ON user_events(user_id, created_at DESC);

-- ANALYZE so the planner picks up the new indexes immediately.
ANALYZE fields;
ANALYZE daily_logs;
ANALYZE field_inputs;
ANALYZE chat_logs;
ANALYZE farm_tasks;
