"""
Idempotent migration for the institutional B2B api_keys table.

Safe to run multiple times. Evolves the table in place: creates it if
absent, adds new columns / indexes if missing, conditionally drops the
legacy UNIQUE constraint on key_hash (we now look up by key_id_hex and
verify with bcrypt — the same secret hashed with bcrypt is salted and
will not be uniformly unique anyway), and adds an FK to tenants(id)
only if a tenants table is present.
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def migrate():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found")
        return

    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()

    try:
        # 1. Base table — creates it if absent. Existing deployments will
        #    keep their current shape; the ALTER TABLE block below evolves it.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id UUID NOT NULL,
                key_hash TEXT NOT NULL,
                name TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                expires_at TIMESTAMPTZ,
                last_used_at TIMESTAMPTZ,
                is_active BOOLEAN DEFAULT TRUE
            );
        """)
        print("✅ api_keys: table verified/created")

        # 2. Add new columns idempotently for tables that pre-date this rev.
        cursor.execute("""
            ALTER TABLE api_keys
                ADD COLUMN IF NOT EXISTS last_used_at TIMESTAMPTZ,
                ADD COLUMN IF NOT EXISTS rate_limit_override JSONB,
                ADD COLUMN IF NOT EXISTS key_id_hex TEXT;
        """)
        print("✅ api_keys: last_used_at, rate_limit_override, key_id_hex columns verified")

        # 3. Make `name` NOT NULL going forward; backfill any historical
        #    rows that pre-date the constraint with a placeholder so the
        #    constraint can be added without rewriting the table on prod.
        cursor.execute("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='api_keys'
                      AND column_name='name'
                      AND is_nullable='YES'
                ) THEN
                    UPDATE api_keys SET name = 'unnamed' WHERE name IS NULL;
                    ALTER TABLE api_keys ALTER COLUMN name SET NOT NULL;
                END IF;
            END $$;
        """)
        print("✅ api_keys.name: NOT NULL constraint verified")

        # 4. Drop the legacy UNIQUE constraint on key_hash if present —
        #    bcrypt-salted hashes don't compose with UNIQUE in a useful way.
        cursor.execute("""
            DO $$
            DECLARE
                cname TEXT;
            BEGIN
                SELECT conname INTO cname
                FROM pg_constraint
                WHERE conrelid = 'api_keys'::regclass
                  AND contype = 'u'
                  AND pg_get_constraintdef(oid) ILIKE '%(key_hash)%';
                IF cname IS NOT NULL THEN
                    EXECUTE format('ALTER TABLE api_keys DROP CONSTRAINT %I', cname);
                END IF;
            END $$;
        """)
        print("✅ api_keys: legacy UNIQUE(key_hash) dropped if present")

        # 5. UNIQUE index on key_id_hex (the lookup key embedded in raw API keys).
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_api_keys_key_id_hex
                ON api_keys (key_id_hex)
                WHERE key_id_hex IS NOT NULL;
        """)
        print("✅ api_keys.key_id_hex: unique index verified/created")

        # 6. Lookup indexes.
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_api_keys_tenant_id ON api_keys(tenant_id);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash);"
        )
        print("✅ api_keys: tenant_id and key_hash indexes verified/created")

        # 7. FK to tenants(id) only if a tenants table exists in this deployment.
        cursor.execute("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.tables WHERE table_name = 'tenants'
                ) AND NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'api_keys_tenant_id_fkey'
                ) THEN
                    ALTER TABLE api_keys
                        ADD CONSTRAINT api_keys_tenant_id_fkey
                        FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
                END IF;
            END $$;
        """)
        print("✅ api_keys: tenants(id) FK added if tenants table exists")

        conn.commit()
        print("🎉 api_keys migration completed successfully")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    migrate()
