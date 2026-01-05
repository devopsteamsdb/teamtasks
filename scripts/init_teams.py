
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Team, TeamMember

def init_teams():
    with app.app_context():
        # Clear existing data? Maybe not, just check if exists.
        
        teams_data = [
            {'name_en': 'devops', 'name_he': 'דבאופס'},
            {'name_en': 'security', 'name_he': 'אבטחת מידע'},
            {'name_en': 'network', 'name_he': 'תקשורת'},
            {'name_en': 'system', 'name_he': 'סיסטם'}
        ]
        
        members_data = {
            'devops': [
                {'name_en': 'moshe', 'name_he': 'משה כהן'},
                {'name_en': 'david', 'name_he': 'דוד לוי'},
                {'name_en': 'sarah', 'name_he': 'שרה אברהם'}
            ],
            'security': [
                {'name_en': 'yossi', 'name_he': 'יוסי יוסף'},
                {'name_en': 'dina', 'name_he': 'דינה דן'}
            ],
            'network': [
                {'name_en': 'avi', 'name_he': 'אבי אבן'},
                {'name_en': 'ron', 'name_he': 'רון רונן'}
            ],
            'system': [
                {'name_en': 'danny', 'name_he': 'דני דין'},
                {'name_en': 'chen', 'name_he': 'חן חנוך'},
                {'name_en': 'gali', 'name_he': 'גלי גל'}
            ]
        }
        
        created_teams = {}
        
        for t in teams_data:
            team = Team.query.filter_by(name_en=t['name_en']).first()
            if not team:
                print(f"Creating team: {t['name_en']}")
                team = Team(name_en=t['name_en'], name_he=t['name_he'])
                db.session.add(team)
                db.session.commit() # Commit to get ID
            else:
                print(f"Team exists: {t['name_en']}")
            created_teams[t['name_en']] = team
            
        # Members
        for team_key, members in members_data.items():
            team = created_teams.get(team_key)
            if not team: continue
            
            for m in members:
                member = TeamMember.query.filter_by(name_en=m['name_en'], team_id=team.id).first()
                if not member:
                    print(f"Creating member: {m['name_en']} in {team_key}")
                    member = TeamMember(
                        team_id=team.id,
                        name_en=m['name_en'],
                        name_he=m['name_he'],
                        avatar_path='default.png'
                    )
                    db.session.add(member)
        
        db.session.commit()
        print("Teams and members initialized.")

if __name__ == '__main__':
    init_teams()
