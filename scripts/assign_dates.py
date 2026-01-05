
import sys
import os
import random
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Task

def assign_dates():
    with app.app_context():
        tasks = Task.query.all()
        if not tasks:
            print("No tasks found.")
            return
            
        print(f"Assigning dates to {len(tasks)} tasks...")
        
        today = datetime.now()
        # Start of current week (assume Sunday)
        # Python weekday: Mon=0, Sun=6.
        # If today is Mon(0), days_since_sun = 1. If today is Sun(6), days_since_sun = 0.
        # Wait, if Sun is start:
        # If today is Mon(0): start was yesterday (-1 day).
        # (0 + 1) % 7 = 1. Correct.
        # If today is Sun(6): start is today. (6+1)%7 = 0. Correct.
        days_since_sunday = (today.weekday() + 1) % 7
        week_start = today - timedelta(days=days_since_sunday)
        
        for task in tasks:
            # Randomly assign to current week or previous/next week
            week_offset = random.choice([-1, 0, 0, 0, 1]) # Weighted towards current week
            base_date = week_start + timedelta(weeks=week_offset)
            
            # Random day in week (Sun-Thu work week usually in Israel, but specific logic said 0-4)
            day_offset = random.randint(0, 4)
            start_date = base_date + timedelta(days=day_offset)
            
            # Duration 1 to 3 days
            duration = random.randint(0, 2)
            end_date = start_date + timedelta(days=duration)
            
            task.start_date = start_date.date()
            task.end_date = end_date.date()
            
        db.session.commit()
        print("Dates assigned successfully.")

if __name__ == '__main__':
    assign_dates()
