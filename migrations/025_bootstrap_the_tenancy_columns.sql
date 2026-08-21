-- 025: put the tenancy columns into the migration sequence.
--
-- THE GAP
-- -------
-- `fields.tenant_id` is the column the entire product scopes on. Every
-- institutional read goes through `tenancy.field_scope_sql()`:
--
--     WHERE (tenant_id = ANY(%s::uuid[]) OR user_id = %s::uuid)
--
-- It is not created by any numbered migration. It is added by
-- `migrate_fields_to_tenants.py` — a standalone script, run by hand, outside
-- the sequence. Same for `fields.grower_id` and for the `growers` table itself.
--
-- 015 calls itself "the complete runtime schema". It creates 19 tables, and
-- `growers` is not among them — yet it carries `ALTER TABLE growers ADD COLUMN
-- timb_grower_number` (021) and two `CREATE INDEX ... ON growers` (021, 023),
-- plus `CREATE INDEX ... ON fields (tenant_id)` and `(grower_id)` (023).
--
-- So on a database built from the migrations alone, the bootstrap references
-- three objects it never creates, and 023 is the statement that finally fails
-- on them. It has never been noticed because every existing installation was
-- built the other way round: the script ran first, on a database that already
-- had rows in it, and 015 was captured from the result.
--
-- That is fine right up until someone stands up a fresh environment — a
-- staging database, a second region, a restore drill — and discovers that the
-- documented path does not produce a working schema.
--
-- WHAT THIS DOES
-- --------------
-- Moves the DDL half of `migrate_fields_to_tenants.py` into the sequence,
-- unchanged and idempotent. The backfill half stays in the script: it reads
-- live rows and reports orphans, which is operator work, not schema.
--
-- `tenant_id` is added NULLABLE here. The script sets NOT NULL only once no
-- NULLs remain, and that ordering is load-bearing — asserting NOT NULL against
-- unbackfilled rows fails the migration and takes the deploy with it.
--
-- Ordering note: this must sort before 023, which indexes these columns. It
-- does not, and cannot without renaming a merged migration. It is idempotent
-- and 023's indexes are IF NOT EXISTS, so on a fresh build the operator applies
-- 025 and then re-runs 023 — one line in the runbook, versus a bootstrap that
-- silently is not one. `database.init_db()` orders them correctly for the
-- self-heal path, which is how every environment to date has been built.

-- --------------------------------------------------------------------------
-- growers — institutional tenants' contracted growers.
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS growers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    coordinates JSONB,
    claimed_by_user_id UUID REFERENCES profiles(id),
    created_by_user_id UUID REFERENCES profiles(id),
    notes TEXT,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_growers_tenant ON growers(tenant_id);
CREATE INDEX IF NOT EXISTS idx_growers_claimed ON growers(claimed_by_user_id);
CREATE INDEX IF NOT EXISTS idx_growers_active ON growers(deleted_at) WHERE deleted_at IS NULL;

-- --------------------------------------------------------------------------
-- fields.tenant_id / fields.grower_id
-- --------------------------------------------------------------------------
ALTER TABLE fields ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id);
ALTER TABLE fields ADD COLUMN IF NOT EXISTS grower_id UUID REFERENCES growers(id);

COMMENT ON COLUMN fields.user_id IS
  'Deprecated as of Workstream 3. Retained for migration safety. To be removed '
  'in a future cleanup PR once all endpoints are confirmed using tenant_id.';

-- --------------------------------------------------------------------------
-- RLS. growers is in 017's FORCE list and 008's policy sweep, both of which
-- guard on table existence — so on a fresh build they ran before the table
-- existed and skipped it. Applied here, where it does exist.
-- --------------------------------------------------------------------------
ALTER TABLE public.growers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.growers FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS ts_growers ON public.growers;
CREATE POLICY ts_growers ON public.growers
    FOR ALL
    USING (tenant_id = ANY (public.app_tenant_ids()))
    WITH CHECK (tenant_id = ANY (public.app_tenant_ids()));

ALTER TABLE public.fields ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fields FORCE ROW LEVEL SECURITY;

-- Verify a fresh build actually produced them:
--
--   SELECT column_name FROM information_schema.columns
--   WHERE table_name = 'fields' AND column_name IN ('tenant_id', 'grower_id');
--   --> 2 rows
--
-- Rollback: none worth writing. Dropping fields.tenant_id takes the product
-- with it.
