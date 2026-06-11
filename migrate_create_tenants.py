"""
Migration: tenants + tenant_members (Workstream 3, Block 1)
==========================================================
Introduces the tenant model. A *tenant* is the real ownership boundary for field
data; *tenant_members* maps users to tenants with a member role.

* Consumers get a 1-member `consumer` tenant (they are the `owner`) so that
  re-scoping queries from user_id -> tenant_id is behaviour-preserving.
* Institutional tenants (e.g. "Northern Tobacco") can have many officers.

Idempotent: CREATE TABLE/INDEX IF NOT EXISTS; running twice is a no-op and never
duplicates data. Backfill of rows is a separate migration
(migrate_backfill_consumer_tenants.py).

Run:  python migrate_create_tenants.py
"""

import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

MIGRATION_SQL = """
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    tenant_type TEXT NOT NULL
        CHECK (tenant_type IN ('consumer', 'institutional')),
    institutional_type TEXT
        CHECK (institutional_type IS NULL OR
               institutional_type IN ('buyer', 'lender', 'insurer', 'grower')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT institutional_tenants_have_type CHECK (
        tenant_type != 'institutional' OR institutional_type IS NOT NULL
    )
);

-- deleted_at also added defensively for DBs where tenants already existed.
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;

CREATE INDEX IF NOT EXISTS idx_tenants_type ON tenants(tenant_type);

CREATE TABLE IF NOT EXISTS tenant_members (
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    member_role TEXT NOT NULL DEFAULT 'owner'
        CHECK (member_role IN ('owner', 'officer', 'viewer')),
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (tenant_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_tenant_members_user ON tenant_members(user_id);
CREATE INDEX IF NOT EXISTS idx_tenant_members_tenant ON tenant_members(tenant_id);
"""

VERIFY_SQL = """
SELECT table_name FROM information_schema.tables
WHERE table_schema='public' AND table_name IN ('tenants', 'tenant_members')
ORDER BY table_name;
"""


def migrate():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set")
        return
    conn = psycopg2.connect(db_url)
    try:
        cur = conn.cursor()
        print("Creating tenants + tenant_members…")
        cur.execute(MIGRATION_SQL)
        conn.commit()
        cur.execute(VERIFY_SQL)
        present = [r[0] for r in cur.fetchall()]
        print(f"✅ Tables present: {present}")
        cur.close()
    except Exception as exc:  # pragma: no cover - operational
        conn.rollback()
        print(f"❌ Migration failed (rolled back): {exc}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
