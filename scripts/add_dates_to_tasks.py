"""
Quick script to add dates to existing tasks for testing the calendar.
This will assign this week's dates to your existing tasks.
"""
import sqlite3
from datetime import datetime, timedelta

# Connect to database
db_path = 'instance/tasks.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get today and calculate this week's dates (Sun-Thu)
today = datetime.now()
days_since_sunday = (today.weekday() + 1) % 7
week_start = today - timedelta(days=days_since_sunday)

# Get all tasks without dates
cursor.execute("SELECT id, task FROM task WHERE start_date IS NULL LIMIT 10")
tasks = cursor.fetchall()

if not tasks:
    print("No tasks found without dates, or all tasks already have dates!")
    conn.close()
    exit(0)

print(f"Found {len(tasks)} tasks without dates. Assigning dates...")

# Assign dates to tasks (spread across the week)
for i, (task_id, task_name) in enumerate(tasks):
    # Cycle through days 0-4 (Sun-Thu)
    day_offset = i % 5
    task_date = week_start + timedelta(days=day_offset)
    date_str = task_date.strftime('%Y-%m-%d')
    
    cursor.execute(
        "UPDATE task SET start_date = ? WHERE id = ?",
        (date_str, task_id)
    )
    print(f"✓ Task #{task_id} '{task_name[:30]}...' → {date_str}")

conn.commit()
conn.close()

print(f"\n✓ Successfully assigned dates to {len(tasks)} tasks!")
print("Refresh your calendar page to see them!")
