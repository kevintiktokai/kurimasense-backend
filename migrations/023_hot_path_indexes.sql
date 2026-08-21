-- 023: indexes for the queries the app actually runs.
--
-- `fields` carried exactly one index — on `user_id`, the *legacy* consumer
-- column. Every institutional query scopes by tenant:
--
--     WHERE (tenant_id = ANY(%s::uuid[]) OR user_id = %s::uuid)
--
-- (see tenancy.field_scope_sql). With no index on `tenant_id`, Postgres cannot
-- satisfy the first arm and falls back to a sequential scan of the whole table
-- for the OR. That is on the path of every portfolio load, every document
-- generated, and every single field page — the busiest table in the product,
-- scanned end to end, every time.
--
-- It is invisible in a demo and linear in customers, which is the shape of
-- problem that looks fine right up until a real contractor's book is loaded.
--
-- None of these change behaviour. They are all CREATE INDEX IF NOT EXISTS, so
-- re-running is free; on a large table build them CONCURRENTLY by hand instead
-- (CONCURRENTLY cannot run inside the transaction a migration runner uses).

-- The one that matters. `tenant_id` alone rather than a composite: the scope
-- predicate is an equality/ANY on this column and nothing else is stable across
-- the call sites.
CREATE INDEX IF NOT EXISTS idx_fields_tenant ON fields (tenant_id);

-- The evidence pack and the portfolio report both join fields to their grower.
-- Without this that join is a scan per pack.
CREATE INDEX IF NOT EXISTS idx_fields_grower ON fields (grower_id)
    WHERE grower_id IS NOT NULL;

-- The grower roster: WHERE tenant_id = %s AND deleted_at IS NULL
--                    ORDER BY created_at DESC
-- Partial, because a soft-deleted grower is never listed, and ordered so the
-- index also satisfies the sort.
CREATE INDEX IF NOT EXISTS idx_growers_tenant_active
    ON growers (tenant_id, created_at DESC)
    WHERE deleted_at IS NULL;

-- field_inputs is read by field *and* by date window (the evidence pack's
-- crop-protection theme). The existing index leads with field_id, which serves
-- the per-field read; this serves the tenant-wide window scan.
CREATE INDEX IF NOT EXISTS idx_field_inputs_date ON field_inputs (input_date)
    WHERE input_date IS NOT NULL;
