
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def add_insight_column():
    if not DATABASE_URL:
        print("❌ DATABASE_URL not set")
        return

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("Checking if insight_text column exists in daily_logs...")
        
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='daily_logs' AND column_name='insight_text';
        """)
        
        if cursor.fetchone():
            print("✅ insight_text column already exists.")
        else:
            print("Running migration to add insight_text...")
            cursor.execute("ALTER TABLE daily_logs ADD COLUMN insight_text TEXT;")
            conn.commit()
            print("✅ Successfully added insight_text column to daily_logs.")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    add_insight_column()
