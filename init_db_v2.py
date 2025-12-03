"""
Simple database initialization for v2
Creates fresh database with Team and TeamMember support
"""
import os
import shutil
from datetime import datetime
from flask import Flask
from models import db, Team, TeamMember, Task

def init_database():
    """Initialize database with default data"""
    
    # Create Flask app context
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    with app.app_context():
        # Backup existing database if it exists
        db_path = 'instance/tasks.db'
        if os.path.exists(db_path):
            backup_path = f'instance/tasks_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
            shutil.copy2(db_path, backup_path)
            print(f"✓ Database backed up to: {backup_path}")
            
            # Remove old database
            os.remove(db_path)
            print("✓ Removed old database")
        
        # Create all tables
        db.create_all()
        print("✓ Database schema created")
        
        # Create default team
        default_team = Team(
            name_en='devops',
            name_he='צוות DevOps'
        )
        db.session.add(default_team)
        db.session.commit()
        print(f"✓ Created default team: {default_team.name_he}")
        
        # Create default team members
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
        
        # Verify
        total_teams = Team.query.count()
        total_members = TeamMember.query.count()
        
        print("\n=== Initialization Summary ===")
        print(f"Teams: {total_teams}")
        print(f"Members: {total_members}")
        print("==============================")
        print("\n✓ Database initialized successfully!")
        print("\nNote: Old database was backed up. You can restore tasks manually if needed.")

if __name__ == '__main__':
    init_database()
