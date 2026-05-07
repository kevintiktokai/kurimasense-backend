import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def rollback():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found")
        return

    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()

    try:
        # 1. Drop field_aoi_cache table
        cursor.execute("DROP TABLE IF EXISTS field_aoi_cache;")
        print("✅ field_aoi_cache: table dropped")

        # 2. Drop indexes on daily_logs
        cursor.execute("DROP INDEX IF EXISTS idx_daily_logs_quality;")
        cursor.execute("DROP INDEX IF EXISTS idx_daily_logs_field_date;")
        print("✅ daily_logs: indexes dropped")

        # 3. Drop CHECK constraints
        cursor.execute("""
            ALTER TABLE daily_logs
                DROP CONSTRAINT IF EXISTS daily_logs_observation_quality_check;
        """)
        cursor.execute("""
            ALTER TABLE daily_logs
                DROP CONSTRAINT IF EXISTS daily_logs_satellite_source_check;
        """)
        print("✅ daily_logs: CHECK constraints dropped")

        # 4. Drop satellite index ensemble columns
        cursor.execute("""
            ALTER TABLE daily_logs
                DROP COLUMN IF EXISTS observation_quality,
                DROP COLUMN IF EXISTS cloud_pct,
                DROP COLUMN IF EXISTS satellite_source,
                DROP COLUMN IF EXISTS indices;
        """)
        print("✅ daily_logs: satellite index columns dropped")

        conn.commit()
        print("🎉 Satellite index rollback completed successfully")
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    rollback()
