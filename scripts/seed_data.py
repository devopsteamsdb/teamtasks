import random
from app import app, db
from models import Team, TeamMember, Task

def seed_data():
    with app.app_context():
        teams = Team.query.all()
        members = TeamMember.query.all()
        
        if not teams:
            print("No teams found. Please create teams first.")
            return

        statuses = ['status-notstarted', 'status-inprogress', 'status-done', 'status-delayed']
        priorities = ['high', 'medium', 'low', 'none']
        
        print("Generating dummy data...")
        
        # Create 10 dummy projects
        for i in range(1, 11):
            project_suffix = random.choice(['Alpha', 'Beta', 'Gamma', 'Delta', 'Omega', 'Sigma'])
            project_name = f"Project {i} - {project_suffix}"
            
            # Assign a random team to the project (or None for General)
            # 80% chance of having a team
            project_team = random.choice(teams) if random.random() > 0.2 else None
            
            # Create 3-8 tasks per project
            for j in range(1, random.randint(4, 9)):
                task_action = random.choice(['Fix bug', 'Implement feature', 'Review code', 'Write docs', 'Deploy', 'Test', 'Design'])
                task_name = f"{task_action} #{random.randint(100, 999)}"
                
                # Assign members
                task_members = []
                if project_team:
                    # Pick random members from the project's team
                    team_members = [m for m in members if m.team_id == project_team.id]
                    if team_members:
                        # Pick 1-2 members
                        selected = random.sample(team_members, k=min(len(team_members), random.randint(1, 2)))
                        task_members = [m.name_en for m in selected]
                
                new_task = Task(
                    project=project_name,
                    task=task_name,
                    members=','.join(task_members),
                    status=random.choice(statuses),
                    priority=random.choice(priorities),
                    notes=f"Auto-generated note for task {j} in {project_name}",
                    team_id=project_team.id if project_team else None
                )
                db.session.add(new_task)
        
        db.session.commit()
        print("Dummy data created successfully!")

if __name__ == '__main__':
    seed_data()
