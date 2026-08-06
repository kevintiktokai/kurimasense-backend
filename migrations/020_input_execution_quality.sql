-- 020_input_execution_quality.sql
-- ============================================================================
-- Execution quality on field inputs.
--
-- `field_inputs` recorded what went on and how much, never HOW — and for
-- nitrogen the how is most of the outcome. Urea banded, urea broadcast onto dry
-- soil, and urea followed by a downpour on sand all look identical in the task
-- list and differ enormously in what the crop actually receives.
--
-- Capturing the difference is what turns outcome data from "what happened" into
-- "what worked", and it is the only way the calibration loop can learn about
-- management rather than about weather.
--
-- Every column is nullable: an application logged without these details is
-- still a valid record, it simply cannot be assessed. See
-- services/planning/execution.py, which returns 'unknown' rather than guessing.
-- ============================================================================

ALTER TABLE field_inputs ADD COLUMN IF NOT EXISTS product_name TEXT;
ALTER TABLE field_inputs ADD COLUMN IF NOT EXISTS application_method TEXT;
    -- broadcast | banded | incorporated | fertigation
ALTER TABLE field_inputs ADD COLUMN IF NOT EXISTS incorporated BOOLEAN;
ALTER TABLE field_inputs ADD COLUMN IF NOT EXISTS rain_mm_48h NUMERIC(6,1);
    -- Rainfall in the 48h after application. Decides whether nitrogen was
    -- washed into the root zone, left on the surface to volatilise, or carried
    -- past the roots entirely.
ALTER TABLE field_inputs ADD COLUMN IF NOT EXISTS notes TEXT;

CREATE INDEX IF NOT EXISTS idx_field_inputs_season ON field_inputs(season_id, input_date);

-- Rollback:
--   ALTER TABLE field_inputs DROP COLUMN IF EXISTS product_name;
--   ALTER TABLE field_inputs DROP COLUMN IF EXISTS application_method;
--   ALTER TABLE field_inputs DROP COLUMN IF EXISTS incorporated;
--   ALTER TABLE field_inputs DROP COLUMN IF EXISTS rain_mm_48h;
--   ALTER TABLE field_inputs DROP COLUMN IF EXISTS notes;
