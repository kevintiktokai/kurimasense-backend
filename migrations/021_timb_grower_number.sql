-- 021: TIMB grower number on growers.
--
-- A Season Evidence Pack claims grower-level traceability. That claim is only
-- checkable if each grower row carries the number TIMB's own register is keyed
-- on — without it a buyer has a report, not evidence, because there is nothing
-- to reconcile it against.
--
-- Deliberately TEXT with no CHECK constraint. TIMB's format is not documented
-- in anything we can verify, and a pattern guessed from a few examples would
-- reject valid growers on write. See services/documents/grower_number.py.
--
-- Not unique, and not NOT NULL:
--   * Many growers in the system are not registered tobacco growers at all.
--   * Duplicates are real and meaningful — a number typed twice is a data-entry
--     problem to surface in the app, not one to block a row on at 6am when
--     someone is registering a hundred growers before a deadline.
-- The partial index makes finding those duplicates cheap without enforcing.

ALTER TABLE growers ADD COLUMN IF NOT EXISTS timb_grower_number TEXT;

COMMENT ON COLUMN growers.timb_grower_number IS
    'TIMB grower registration number. The join key to the sector''s register, '
    'printed on every grower row of a Season Evidence Pack. Stored as entered '
    '(normalised for case/whitespace); format is not validated on write.';

-- Lookup by number, and duplicate detection within a tenant. Partial so the
-- index only carries the rows that actually have a number.
CREATE INDEX IF NOT EXISTS idx_growers_timb_number
    ON growers (tenant_id, timb_grower_number)
    WHERE timb_grower_number IS NOT NULL;
