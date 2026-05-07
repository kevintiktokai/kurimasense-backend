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
        # 1. Extend daily_logs with satellite index ensemble columns
        cursor.execute("""
            ALTER TABLE daily_logs
                ADD COLUMN IF NOT EXISTS indices JSONB,
                ADD COLUMN IF NOT EXISTS satellite_source TEXT,
                ADD COLUMN IF NOT EXISTS cloud_pct FLOAT,
                ADD COLUMN IF NOT EXISTS observation_quality TEXT;
        """)
        print("✅ daily_logs: satellite index columns verified/added")

        # 2. Constrain satellite_source to known values (NULL allowed)
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints
                    WHERE table_name = 'daily_logs'
                      AND constraint_name = 'daily_logs_satellite_source_check'
                ) THEN
                    ALTER TABLE daily_logs
                        ADD CONSTRAINT daily_logs_satellite_source_check
                        CHECK (satellite_source IN ('s2-l2a', 's1-grd', 'merged') OR satellite_source IS NULL);
                END IF;
            END $$;
        """)
        print("✅ daily_logs: satellite_source CHECK constraint verified/added")

        # 3. Constrain observation_quality to known values (NULL allowed)
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints
                    WHERE table_name = 'daily_logs'
                      AND constraint_name = 'daily_logs_observation_quality_check'
                ) THEN
                    ALTER TABLE daily_logs
                        ADD CONSTRAINT daily_logs_observation_quality_check
                        CHECK (observation_quality IN ('good', 'partial', 'rejected') OR observation_quality IS NULL);
                END IF;
            END $$;
        """)
        print("✅ daily_logs: observation_quality CHECK constraint verified/added")

        # 4. Indexes on daily_logs
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_daily_logs_field_date
                ON daily_logs (field_id, log_date DESC);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_daily_logs_quality
                ON daily_logs (observation_quality)
                WHERE observation_quality = 'good';
        """)
        print("✅ daily_logs: idx_daily_logs_field_date and idx_daily_logs_quality verified/created")

        # 5. field_aoi_cache: per-field area-of-interest cache
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS field_aoi_cache (
                field_id UUID PRIMARY KEY,
                bbox JSONB NOT NULL,
                geometry JSONB,
                area_ha FLOAT,
                last_updated TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        print("✅ field_aoi_cache: table verified/created")

        conn.commit()
        print("🎉 Satellite index migration completed successfully")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    migrate()
