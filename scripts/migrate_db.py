"""
Database migration script to add calendar fields to Task table.
Run this once to update your existing database.
"""
import sqlite3
import os

# Path to database
db_path = os.path.join('instance', 'tasks.db')

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    print("The database will be created automatically when you run the app.")
    exit(0)

print(f"Migrating database: {db_path}")

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if columns already exist
cursor.execute("PRAGMA table_info(task)")
columns = [column[1] for column in cursor.fetchall()]

migrations_needed = []

if 'start_date' not in columns:
    migrations_needed.append('start_date')
if 'end_date' not in columns:
    migrations_needed.append('end_date')
if 'estimated_hours' not in columns:
    migrations_needed.append('estimated_hours')

if not migrations_needed:
    print("✓ Database is already up to date!")
    conn.close()
    exit(0)

print(f"Adding columns: {', '.join(migrations_needed)}")

try:
    # Add new columns
    if 'start_date' in migrations_needed:
        cursor.execute("ALTER TABLE task ADD COLUMN start_date DATE")
        print("✓ Added start_date column")
    
    if 'end_date' in migrations_needed:
        cursor.execute("ALTER TABLE task ADD COLUMN end_date DATE")
        print("✓ Added end_date column")
    
    if 'estimated_hours' in migrations_needed:
        cursor.execute("ALTER TABLE task ADD COLUMN estimated_hours REAL")
        print("✓ Added estimated_hours column")
    
    # Commit changes
    conn.commit()
    print("\n✓ Migration completed successfully!")
    print("You can now run the application with: python app.py")
    
except Exception as e:
    print(f"\n✗ Migration failed: {e}")
    conn.rollback()
    
finally:
    conn.close()
