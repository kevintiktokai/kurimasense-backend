-- 027: put the daily_logs uniqueness into the schema, where it wasn't.
--
-- Production enforces `daily_logs_field_id_log_date_key` — a UNIQUE constraint
-- on (field_id, log_date). We know because it fired:
--
--   duplicate key value violates unique constraint "daily_logs_field_id_log_date_key"
--   DETAIL: Key (field_id, log_date)=(6d17e519-…, 2026-08-25) already exists.
--
-- It is in no migration and not in the bootstrap. Those carry only a *non-unique*
-- index, idx_daily_logs_field_date. So the constraint was added by hand to the
-- live database at some point and never written down — the same drift as
-- `fields.tenant_id` (migration 025), found the same way: by something failing
-- that could only fail if the object existed.
--
-- WHY IT MATTERS NOW
-- ------------------
-- app.py now upserts the satellite reading with
-- `ON CONFLICT (field_id, log_date) DO UPDATE`, because the plain INSERT was
-- rolling the whole analysis back on the second run of any given day. That
-- clause needs a matching unique constraint. On production it finds one; on a
-- database built from the migrations it would fail with "no unique or exclusion
-- constraint matching the ON CONFLICT specification" — an error that only shows
-- up on a fresh environment, which is exactly the environment nobody tests.
--
-- The constraint is also right on its own terms: one satellite reading per field
-- per day is the model, and two rows for one date would make `logs[-1]`
-- ambiguous for every consumer of the field-state window.
--
-- Deduplicates first, because a database that never had the constraint may have
-- collected duplicates. Keeps the most recently created row per (field_id,
-- log_date) — the latest analysis is the one the farmer last asked for.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'daily_logs_field_id_log_date_key'
    ) THEN
        -- Keep the newest row per field per day; drop the rest.
        DELETE FROM daily_logs a
        USING daily_logs b
        WHERE a.field_id = b.field_id
          AND a.log_date = b.log_date
          AND (a.created_at, a.id) < (b.created_at, b.id);

        ALTER TABLE daily_logs
            ADD CONSTRAINT daily_logs_field_id_log_date_key
            UNIQUE (field_id, log_date);
    END IF;
END $$;

-- Verify:
--   SELECT conname FROM pg_constraint WHERE conname = 'daily_logs_field_id_log_date_key';
--   --> 1 row
--
--   SELECT field_id, log_date, COUNT(*) FROM daily_logs
--   GROUP BY 1, 2 HAVING COUNT(*) > 1;
--   --> 0 rows
--
-- Rollback:
--   ALTER TABLE daily_logs DROP CONSTRAINT daily_logs_field_id_log_date_key;
--   (and revert app.py's upsert to a plain INSERT, or it will start failing)
