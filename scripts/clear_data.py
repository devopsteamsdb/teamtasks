import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Task

def clear_data():
    with app.app_context():
        print("Clearing all tasks...")
        num_deleted = db.session.query(Task).delete()
        db.session.commit()
        print(f"Deleted {num_deleted} tasks.")

if __name__ == '__main__':
    clear_data()
