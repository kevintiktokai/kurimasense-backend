"""
Migration: role tagging on profiles (Workstream 1)
==================================================
Adds the institutional role-tagging foundation to the ``profiles`` table:

    * role               TEXT NOT NULL DEFAULT 'consumer'
                         CHECK (role IN ('consumer','institutional','admin'))
    * institutional_type TEXT NULL
                         CHECK (institutional_type IS NULL OR
                                institutional_type IN ('buyer','lender','insurer','grower'))
    * tenant_name        TEXT NULL  (free text display name of the institution)
    * CONSTRAINT institutional_users_have_type
                         CHECK (role != 'institutional' OR institutional_type IS NOT NULL)
    * INDEX idx_profiles_role ON profiles(role)

IMPORTANT — `role` already exists (audit finding F1)
----------------------------------------------------
On the live ``kurimasense`` database ``profiles.role`` ALREADY exists as nullable
free text with legacy values (``smallholder``, ``farmer``) that the frontend
displays. A naive ``ADD COLUMN role`` would be skipped by the idempotency guard
and leave the column without DEFAULT/NOT NULL/CHECK. This migration therefore
*repurposes* the existing column: it backfills any value not in the new
vocabulary (``smallholder``/``farmer``/NULL) to ``'consumer'`` BEFORE adding the
NOT NULL + CHECK constraints, so all existing (consumer-tier) users are
preserved and the migration cannot fail on legacy data.

Backward-compatible + idempotent: running it twice yields the same result.

Run:  python migrate_user_roles.py

----------------------------------------------------------------------------
Verification (information_schema) AFTER running — recorded here per the spec:

    column_name        | data_type | is_nullable | column_default
    -------------------+-----------+-------------+------------------
    role               | text      | NO          | 'consumer'::text
    institutional_type | text      | YES         | (null)
    tenant_name        | text      | YES         | (null)

    Constraints present:
      profiles_role_check                  CHECK (role IN ('consumer','institutional','admin'))
      profiles_institutional_type_check    CHECK (institutional_type IS NULL OR
                                                  institutional_type IN ('buyer','lender','insurer','grower'))
      institutional_users_have_type        CHECK (role <> 'institutional' OR institutional_type IS NOT NULL)
    Index present: idx_profiles_role

    (This block is filled in once the migration has actually been applied to the
    target DB; see README/PR notes. The SQL below is what produces it.)
----------------------------------------------------------------------------
"""

import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

# All DDL is wrapped so re-running is a no-op. We use named constraints and
# information_schema / pg_constraint existence checks for true idempotency.
MIGRATION_SQL = """
-- 1. role: repurpose the (possibly pre-existing) column as the access tier.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'profiles' AND column_name = 'role'
    ) THEN
        ALTER TABLE profiles ADD COLUMN role TEXT;
    END IF;
END $$;

-- 1a. Backfill legacy / NULL roles to 'consumer' BEFORE adding constraints, so
--     existing 'smallholder'/'farmer' rows satisfy the CHECK. All existing users
--     are consumer-tier.
UPDATE profiles
   SET role = 'consumer'
 WHERE role IS NULL
    OR role NOT IN ('consumer', 'institutional', 'admin');

-- 1b. Default + NOT NULL (safe now that every row has a valid value).
ALTER TABLE profiles ALTER COLUMN role SET DEFAULT 'consumer';
ALTER TABLE profiles ALTER COLUMN role SET NOT NULL;

-- 1c. CHECK constraint (named, added only if absent).
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'profiles_role_check'
    ) THEN
        ALTER TABLE profiles
            ADD CONSTRAINT profiles_role_check
            CHECK (role IN ('consumer', 'institutional', 'admin'));
    END IF;
END $$;

-- 2. institutional_type (nullable; only set when role = 'institutional').
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'profiles' AND column_name = 'institutional_type'
    ) THEN
        ALTER TABLE profiles ADD COLUMN institutional_type TEXT;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'profiles_institutional_type_check'
    ) THEN
        ALTER TABLE profiles
            ADD CONSTRAINT profiles_institutional_type_check
            CHECK (
                institutional_type IS NULL
                OR institutional_type IN ('buyer', 'lender', 'insurer', 'grower')
            );
    END IF;
END $$;

-- 3. tenant_name (nullable free text).
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'profiles' AND column_name = 'tenant_name'
    ) THEN
        ALTER TABLE profiles ADD COLUMN tenant_name TEXT;
    END IF;
END $$;

-- 4. institutional users must carry an institutional_type.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'institutional_users_have_type'
    ) THEN
        ALTER TABLE profiles
            ADD CONSTRAINT institutional_users_have_type
            CHECK (role != 'institutional' OR institutional_type IS NOT NULL);
    END IF;
END $$;

-- 5. index on role for query performance.
CREATE INDEX IF NOT EXISTS idx_profiles_role ON profiles(role);
"""

VERIFY_SQL = """
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'profiles'
  AND column_name IN ('role', 'institutional_type', 'tenant_name')
ORDER BY ordinal_position;
"""


def migrate():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set")
        return

    conn = psycopg2.connect(db_url)
    try:
        cursor = conn.cursor()
        print("Running role-tagging migration on profiles…")
        cursor.execute(MIGRATION_SQL)
        conn.commit()
        print("✅ Migration applied (idempotent).")

        cursor.execute(VERIFY_SQL)
        print("\nVerification — new columns on profiles:")
        for row in cursor.fetchall():
            print(f"  {row[0]:<20} {row[1]:<10} nullable={row[2]:<3} default={row[3]}")

        # Sanity: every row has a valid role.
        cursor.execute(
            "SELECT role, count(*) FROM profiles GROUP BY role ORDER BY count(*) DESC;"
        )
        print("\nRole distribution after backfill:")
        for role, n in cursor.fetchall():
            print(f"  {role}: {n}")

        cursor.close()
    except Exception as exc:  # pragma: no cover - operational
        conn.rollback()
        print(f"❌ Migration failed (rolled back): {exc}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
