from app import app, db
from sqlalchemy import text

def migrate():
    with app.app_context():
        # Check if column exists
        with db.engine.connect() as conn:
            try:
                # SQLite specific check
                result = conn.execute(text("PRAGMA table_info(task)")).fetchall()
                columns = [row[1] for row in result]
                
                if 'is_archived' not in columns:
                    print("Adding 'is_archived' column to task table...")
                    conn.execute(text("ALTER TABLE task ADD COLUMN is_archived BOOLEAN DEFAULT 0 NOT NULL"))
                    conn.commit()
                    print("Migration successful: 'is_archived' column added.")
                else:
                    print("Migration skipped: 'is_archived' column already exists.")
            except Exception as e:
                print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate()
