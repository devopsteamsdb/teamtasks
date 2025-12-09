from app import app, db, Team, TeamMember, Task, SpecialDay
from datetime import date, timedelta
import random

def seed():
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables...")
        db.create_all()

        # Teams in Hebrew (name_en must be lowercase for filter logic)
        teams_data = [
            {'name_en': 'devops', 'name_he': 'צוות DevOps'},
            {'name_en': 'frontend', 'name_he': 'צוות Frontend'},
            {'name_en': 'backend', 'name_he': 'צוות Backend'},
            {'name_en': 'qa', 'name_he': 'צוות QA'}
        ]

        teams = []
        for t_data in teams_data:
            team = Team(name_en=t_data['name_en'], name_he=t_data['name_he'])
            db.session.add(team)
            teams.append(team)
        
        db.session.commit()
        print(f"Created {len(teams)} teams.")

        # Members
        member_defs = [
            ('david', 'דוד עמר'), ('michal', 'מיכל לוי'), ('yossi', 'יוסי מזרחי'), ('ronen', 'רונן בר'),
            ('dana', 'דנה רון'), ('roei', 'רועי שמיר'), ('noa', 'נועה ברק'), ('maya', 'מאיה גל'),
            ('itay', 'איתי גולן'), ('tamar', 'תמר שהם'), ('guy', 'גיא ורדי'), ('alon', 'אלון שחר'),
            ('omer', 'עומר דהן'), ('ron', 'רון אשכנזי'), ('gal', 'גל סופר'), ('shir', 'שיר כץ')
        ]

        # Distribute members: ensure at least 3 per team
        members = []
        member_idx = 0
        
        for team in teams:
            count = 4 # 4 members per team to use up the 16 names
            for _ in range(count):
                if member_idx < len(member_defs):
                    en, he = member_defs[member_idx]
                    member = TeamMember(
                        team_id=team.id,
                        name_en=en,
                        name_he=he,
                        avatar_path='default.png' 
                    )
                    db.session.add(member)
                    members.append(member)
                    member_idx += 1
        
        db.session.commit()
        print(f"Created {len(members)} members.")
        
        # Projects
        project_names = [
            'שדרוג תשתיות ענן', 
            'אפליקציית מובייל ללקוחות', 
            'מערכת ניהול מלאי',
            'אתר שיווקי חדש', 
            'מיגרציה לדאטה-בייס', 
            'אוטומציית בדיקות'
        ]

        tasks_count = 0
        statuses = ['status-notstarted', 'status-inprogress', 'status-done', 'status-delayed']
        priorities = ['high', 'medium', 'low', 'none']
        
        for proj_name in project_names:
            # Assign project primarily to a random team
            primary_team = random.choice(teams)
            
            # 3-8 tasks per project
            num_tasks = random.randint(3, 8)
            
            for i in range(1, num_tasks + 1):
                # Task team (always primary for consistency)
                task_team = primary_team
                # Removed random team assignment for individual tasks to ensure project consistency
                
                # Pick members primarily from task_team, but allow cross-collab
                team_members = [m for m in members if m.team_id == task_team.id]
                other_members = [m for m in members if m.team_id != task_team.id]
                
                selected_members = []
                if team_members:
                    selected_members.append(random.choice(team_members))
                
                if random.random() > 0.4 and team_members: # Add another team member
                     selected_members.append(random.choice(team_members))
                     
                if random.random() > 0.7 and other_members: # Add cross-functional member
                     selected_members.append(random.choice(other_members))
                
                members_str = ",".join(list(set([m.name_en for m in selected_members])))
                
                # Dates
                today = date.today()
                start_offset = random.randint(-15, 30)
                duration = random.randint(2, 14)
                start_date = today + timedelta(days=start_offset)
                end_date = start_date + timedelta(days=duration)
                
                task = Task(
                    project=proj_name,
                    task=f'משימה {i} - {proj_name}',
                    members=members_str,
                    status=random.choice(statuses),
                    priority=random.choice(priorities),
                    notes=f'הערות להדגמה עבור משימה {i}',
                    team_id=task_team.id,
                    start_date=start_date,
                    end_date=end_date,
                    estimated_hours=random.randint(2, 20) * 0.5
                )
                db.session.add(task)
                tasks_count += 1
                
        db.session.commit()
        print(f"Created {tasks_count} tasks across {len(project_names)} projects.")

        # Special Days
        special_days_data = [
            (date.today() + timedelta(days=2), 'יום גיבוש מחלקתי', 'company_event'),
            (date.today() + timedelta(days=9), 'חופשת חג', 'holiday'),
            (date.today() + timedelta(days=12), 'השקת גרסה חגיגית', 'other'),
        ]
        
        for d, name, dtype in special_days_data:
            sd = SpecialDay(date=d, name=name, type=dtype)
            db.session.add(sd)
            
        db.session.commit()
        print("Added special days.")

if __name__ == '__main__':
    seed()
