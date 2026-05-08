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
        # 1. api_keys table — one row per issued key (hashed).
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id UUID NOT NULL,
                key_hash TEXT NOT NULL UNIQUE,
                name TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                expires_at TIMESTAMPTZ,
                is_active BOOLEAN DEFAULT TRUE
            );
        """)
        print("✅ api_keys: table verified/created")

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_api_keys_tenant_id ON api_keys(tenant_id);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash);"
        )
        print("✅ api_keys: indexes verified/created")

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
