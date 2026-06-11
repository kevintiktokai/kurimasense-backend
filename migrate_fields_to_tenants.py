"""
Migration: growers table + fields.tenant_id/grower_id (Workstream 3, Block 1)
============================================================================
1. Create the `growers` table (institutional tenants' contracted growers).
2. Add `fields.tenant_id` and `fields.grower_id` (nullable for now).
3. Backfill `fields.tenant_id` from the field's owner via tenant_members.
4. Once every field has a tenant_id, set the column NOT NULL.

`fields.user_id` is DELIBERATELY RETAINED (deprecated) — see the comment stamped
on the column below. Removing it is a future cleanup PR after all endpoints are
confirmed on tenant_id.

Idempotent: IF NOT EXISTS guards everywhere; backfill only touches rows whose
tenant_id is still NULL; NOT NULL is only applied when no NULLs remain.

Run:  python migrate_fields_to_tenants.py

----------------------------------------------------------------------------
Verification (run automatically below) — expected output:

  SELECT COUNT(*) FROM fields WHERE tenant_id IS NULL;   --> 0
----------------------------------------------------------------------------
"""

import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

CREATE_GROWERS_SQL = """
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
"""

ALTER_FIELDS_SQL = """
ALTER TABLE fields ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id);
ALTER TABLE fields ADD COLUMN IF NOT EXISTS grower_id UUID REFERENCES growers(id);

-- fields.user_id is DEPRECATED as of Workstream 3. Retained for migration safety.
-- To be removed in a future cleanup PR once all endpoints are confirmed using
-- tenant_id. (Documented via column comment so it surfaces in \\d+ / introspection.)
COMMENT ON COLUMN fields.user_id IS
  'Deprecated as of Workstream 3. Retained for migration safety. To be removed in a future cleanup PR once all endpoints are confirmed using tenant_id.';

CREATE INDEX IF NOT EXISTS idx_fields_tenant ON fields(tenant_id);
CREATE INDEX IF NOT EXISTS idx_fields_grower ON fields(grower_id);
"""

BACKFILL_FIELDS_SQL = """
UPDATE fields f
SET tenant_id = tm.tenant_id
FROM tenant_members tm
WHERE f.user_id = tm.user_id
  AND f.tenant_id IS NULL
  AND tm.member_role = 'owner';
"""

SET_NOT_NULL_SQL = """
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM fields WHERE tenant_id IS NULL) THEN
        ALTER TABLE fields ALTER COLUMN tenant_id SET NOT NULL;
    END IF;
END $$;
"""

COUNT_NULL_SQL = "SELECT COUNT(*) FROM fields WHERE tenant_id IS NULL;"
COUNT_ORPHAN_SQL = (
    "SELECT COUNT(*) FROM fields f WHERE NOT EXISTS "
    "(SELECT 1 FROM tenant_members tm WHERE tm.user_id = f.user_id AND tm.member_role='owner');"
)


def migrate():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set")
        return
    conn = psycopg2.connect(db_url)
    try:
        cur = conn.cursor()

        print("1) Creating growers table…")
        cur.execute(CREATE_GROWERS_SQL)

        print("2) Adding fields.tenant_id / fields.grower_id…")
        cur.execute(ALTER_FIELDS_SQL)
        conn.commit()

        # Pre-backfill safety: any field whose owner has no tenant would be left
        # NULL and block the NOT NULL step — surface it instead of silently failing.
        cur.execute(COUNT_ORPHAN_SQL)
        orphans = cur.fetchone()[0]
        if orphans:
            print(f"⚠️  {orphans} field(s) have an owner with no tenant_members(owner) row. "
                  "Run migrate_backfill_consumer_tenants.py first.")

        print("3) Backfilling fields.tenant_id from tenant_members…")
        cur.execute(BACKFILL_FIELDS_SQL)
        conn.commit()

        cur.execute(COUNT_NULL_SQL)
        remaining = cur.fetchone()[0]
        print(f"   fields with NULL tenant_id after backfill: {remaining} (expected 0)")

        print("4) Setting fields.tenant_id NOT NULL (only if no NULLs remain)…")
        cur.execute(SET_NOT_NULL_SQL)
        conn.commit()

        cur.execute(COUNT_NULL_SQL)
        print(f"✅ Done. Remaining NULL tenant_id: {cur.fetchone()[0]}")
        cur.close()
    except Exception as exc:  # pragma: no cover - operational
        conn.rollback()
        print(f"❌ Migration failed (rolled back): {exc}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
