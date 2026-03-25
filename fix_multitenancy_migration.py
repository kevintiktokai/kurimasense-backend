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
        # 1. Add user_id to daily_logs if missing
        cursor.execute("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name='daily_logs' AND column_name='user_id') THEN
                    ALTER TABLE daily_logs ADD COLUMN user_id UUID;
                    -- Try to populate it from the field's user_id
                    UPDATE daily_logs dl
                    SET user_id = f.user_id::uuid
                    FROM fields f
                    WHERE dl.field_id = f.id;
                END IF;
            END $$;
        """)
        print("✅ daily_logs: user_id column verified/added")

        # 2. Add user_id to field_inputs if missing
        cursor.execute("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name='field_inputs' AND column_name='user_id') THEN
                    ALTER TABLE field_inputs ADD COLUMN user_id UUID;
                    -- Try to populate it from the field's user_id
                    UPDATE field_inputs fi
                    SET user_id = f.user_id::uuid
                    FROM fields f
                    WHERE fi.field_id = f.id;
                END IF;
            END $$;
        """)
        print("✅ field_inputs: user_id column verified/added")

        # 3. Ensure chat_logs user_id is UUID compatible where possible
        # (Though chat_logs already has it as TEXT, we should keep it TEXT for now if guest support is needed, 
        # but for authenticated users we filter with ::uuid)
        
        # 4. Add Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fields_user_id ON fields(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_logs_user_id ON chat_logs(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_logs_user_id ON daily_logs(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_field_inputs_user_id ON field_inputs(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_farm_tasks_user_id ON farm_tasks(user_id);")
        print("✅ Database indexes verified/created")

        conn.commit()
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    migrate()
