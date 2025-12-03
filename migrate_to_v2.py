"""
Database migration script for v2
Migrates from v1 schema to v2 schema with Team and TeamMember support
"""
import os
import shutil
import sqlite3
from datetime import datetime
from flask import Flask
from models import db, Team, TeamMember, Task

def migrate_database():
    """Migrate database from v1 to v2"""
    
    # Create Flask app context
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    with app.app_context():
        # Backup existing database
        db_path = 'instance/tasks.db'
        if os.path.exists(db_path):
            backup_path = f'instance/tasks_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
            shutil.copy2(db_path, backup_path)
            print(f"✓ Database backed up to: {backup_path}")
            
            # Read existing tasks before schema change
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if team_id column exists
            cursor.execute("PRAGMA table_info(task)")
            columns = [col[1] for col in cursor.fetchall()]
            
            existing_tasks = []
            if 'team_id' not in columns:
                # Read existing tasks
                cursor.execute("SELECT id, project, task, members, status, priority, notes FROM task")
                existing_tasks = cursor.fetchall()
                print(f"✓ Found {len(existing_tasks)} existing tasks to migrate")
            
            conn.close()
        else:
            existing_tasks = []
        
        # Create all tables (will add new tables, update existing)
        db.create_all()
        print("✓ Database schema updated")
        
        # Check if default team exists
        default_team = Team.query.filter_by(name_en='devops').first()
        
        if not default_team:
            # Create default team
            default_team = Team(
                name_en='devops',
                name_he='צוות DevOps'
            )
            db.session.add(default_team)
            db.session.commit()
            print(f"✓ Created default team: {default_team.name_he}")
            
            # Create default team members (migrating from hardcoded list)
            default_members = [
                {'name_en': 'elad', 'name_he': 'אלעד', 'avatar': 'elad.png'},
                {'name_en': 'guy', 'name_he': 'גיא', 'avatar': 'guy.png'},
                {'name_en': 'itamar', 'name_he': 'איתמר', 'avatar': 'itamar.png'},
                {'name_en': 'noam', 'name_he': 'נועם', 'avatar': 'noam.png'},
                {'name_en': 'david', 'name_he': 'דוד', 'avatar': 'david.png'},
            ]
            
            for member_data in default_members:
                member = TeamMember(
                    team_id=default_team.id,
                    name_en=member_data['name_en'],
                    name_he=member_data['name_he'],
                    avatar_path=member_data['avatar']
                )
                db.session.add(member)
            
            db.session.commit()
            print(f"✓ Created {len(default_members)} team members")
        else:
            print(f"✓ Default team already exists: {default_team.name_he}")
        
        # If we had existing tasks without team_id, update them
        if existing_tasks:
            for task_data in existing_tasks:
                task = Task.query.get(task_data[0])
                if task and task.team_id is None:
                    task.team_id = default_team.id
            db.session.commit()
            print(f"✓ Updated {len(existing_tasks)} tasks to reference default team")
        
        # Update any remaining tasks without team
        tasks_without_team = Task.query.filter_by(team_id=None).all()
        if tasks_without_team:
            for task in tasks_without_team:
                task.team_id = default_team.id
            db.session.commit()
            print(f"✓ Updated {len(tasks_without_team)} additional tasks to reference default team")
        else:
            print("✓ All tasks already have team assignments")
        
        # Verify migration
        total_teams = Team.query.count()
        total_members = TeamMember.query.count()
        total_tasks = Task.query.count()
        
        print("\n=== Migration Summary ===")
        print(f"Teams: {total_teams}")
        print(f"Members: {total_members}")
        print(f"Tasks: {total_tasks}")
        print("=========================")
        print("\n✓ Migration completed successfully!")

if __name__ == '__main__':
    migrate_database()
