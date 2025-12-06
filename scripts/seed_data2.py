import random
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Team, TeamMember, Task

def seed_data_hebrew():
    with app.app_context():
        teams = Team.query.all()
        members = TeamMember.query.all()
        
        if not teams:
            print("No teams found. Please create teams first.")
            return

        statuses = ['status-notstarted', 'status-inprogress', 'status-done', 'status-delayed']
        priorities = ['high', 'medium', 'low', 'none']
        
        # Content mapping based on team name (Hebrew)
        team_content = {
            'דבאופס': {
                'projects': [
                    'מיגרציה לענן', 'אוטומציה CI/CD', 'שדרוג תשתיות 2025', 'ניטור ובקרה',
                    'ניהול קונטיינרים', 'אופטימיזציה של עלויות', 'ארכיטקטורת Microservices', 'Disaster Recovery'
                ],
                'tasks': [
                    'התקנת קוברנטיס', 'כתיבת פייפליין ל-Jenkins', 'שדרוג שרתי פרודקשן', 'הגדרת Prometheus', 
                    'אופטימיזציה ל-Docker', 'ניהול סודות ב-Vault', 'כתיבת Terraform', 'בדיקת גיבויים ב-AWS',
                    'הגדרת Grafana Dashboards', 'טיפול ב-Alertים', 'עדכון גרסאות Helm', 'בדיקת ביצועים',
                    'הגדרת Autoscaling', 'מיגרציה ל-GitLab CI', 'תיעוד ארכיטקטורה', 'בדיקת שחזור מאסון'
                ]
            },
            'אבטחת מידע': {
                'projects': [
                    'הקשחת אבטחה', 'תאימות ISO 27001', 'מבדקי חדירות', 'ניהול זהויות',
                    'אבטחת אפליקציות', 'מודעות עובדים', 'הגנה על נקודות קצה', 'DLP'
                ],
                'tasks': [
                    'סריקת פגיעויות', 'הטמעת MFA', 'עדכון חוקי Firewall', 'בדיקת הרשאות משתמשים', 
                    'טיפול באירוע סייבר', 'הדרכת אבטחה לעובדים', 'סקירת קוד מאובטח', 'הגדרת WAF',
                    'בדיקת Phishing', 'עדכון מדיניות סיסמאות', 'הטמעת EDR', 'ניתוח לוגים ב-SIEM',
                    'בדיקת תאימות GDPR', 'ניהול מפתחות הצפנה', 'בדיקת ספקים צד ג', 'הקשחת שרתי Linux'
                ]
            },
            'תקשורת': {
                'projects': [
                    'שדרוג ליבה', 'חיבור סניף חדש', 'שדרוג WiFi', 'החלפת מתגים',
                    'טלפוניה IP', 'חיבורי WAN', 'אבטחת רשת', 'ניטור תעבורה'
                ],
                'tasks': [
                    'שדרוג Firewall', 'הגדרת VLANs', 'החלפת מתג בקומה 3', 'בדיקת סיבים אופטיים', 
                    'הגדרת VPN', 'פתרון תקלת ניתוקים', 'התקנת Access Points', 'הגדרת QoS',
                    'בדיקת רוחב פס', 'החלפת נתב ראשי', 'הגדרת BGP', 'מיפוי שקעי רשת',
                    'הגדרת NAC', 'בדיקת יתירות', 'שדרוג קושחה לציוד', 'הגדרת ניטור ב-SolarWinds'
                ]
            },
            'סיסטם': {
                'projects': [
                    'שדרוג מערכות הפעלה', 'תחזוקה שוטפת', 'ניהול משתמשים', 'וירטואליזציה',
                    'ניהול אחסון', 'גיבוי ושחזור', 'ניהול תחנות קצה', 'Office 365'
                ],
                'tasks': [
                    'התקנת שרת Windows 2022', 'יצירת משתמשים חדשים', 'בדיקת גיבויים', 'התקנת מדפסות', 
                    'עדכון דרייברים', 'פרמוט עמדות קצה', 'הרחבת דיסק ב-VM', 'ניהול GPO',
                    'עדכון Windows Update', 'טיפול בתקלות Outlook', 'הגדרת שרת קבצים', 'ניהול רישיונות',
                    'החלפת דיסקים ב-Storage', 'שדרוג VMware ESXi', 'הגדרת DHCP', 'בדיקת UPS'
                ]
            }
        }

        # General content for fallback
        general_content = {
            'projects': ['פרויקט כללי', 'משימות מנהלה', 'אירוע חברה', 'רכש', 'משאבי אנוש'],
            'tasks': [
                'פגישת צוות', 'הכנת מצגת', 'רכש ציוד', 'סידור מחסן', 'ראיונות עבודה',
                'הזמנת ציוד משרדי', 'תכנון תקציב', 'עדכון נהלים', 'ארגון Happy Hour', 'טיפול בפרט'
            ]
        }

        print("Generating Hebrew dummy data...")
        
        # Create data for each team
        for team in teams:
            # Find matching content
            content = None
            for key, val in team_content.items():
                if key in team.name_he:
                    content = val
                    break
            
            if not content:
                content = general_content
                print(f"Using general content for team: {team.name_he}")

            # Create 3-5 projects per team (increased from 2-3)
            projects_list = content['projects']
            tasks_list = content['tasks']
            
            # Shuffle lists to ensure variety
            random.shuffle(projects_list)
            
            for i in range(random.randint(3, 5)):
                if i < len(projects_list):
                    project_base = projects_list[i]
                else:
                    project_base = random.choice(projects_list) # Fallback if run out
                    
                project_name = f"{project_base} - {random.choice(['שלב א', 'שלב ב', 'Q1', 'Q2', 'דחוף', '2025'])}"
                
                # Create 4-8 tasks per project (increased from 3-6)
                # Shuffle tasks for this project
                current_tasks = tasks_list.copy()
                random.shuffle(current_tasks)
                
                for j in range(random.randint(4, 8)):
                    if j < len(current_tasks):
                        task_name = current_tasks[j]
                    else:
                        task_name = random.choice(tasks_list) # Fallback
                    
                    # Pick random members from this team
                    team_members = [m for m in members if m.team_id == team.id]
                    task_members_names = []
                    if team_members:
                        selected = random.sample(team_members, k=min(len(team_members), random.randint(1, 3))) # 1-3 members
                        task_members_names = [m.name_en for m in selected]
                    
                    new_task = Task(
                        project=project_name,
                        task=task_name,
                        members=','.join(task_members_names),
                        status=random.choice(statuses),
                        priority=random.choice(priorities),
                        notes=f"הערה אוטומטית למשימה {j+1}",
                        team_id=team.id
                    )
                    db.session.add(new_task)
        
        # Add some "General" tasks (no team)
        for _ in range(5):
            project_name = "משימות כלליות"
            task_name = random.choice(general_content['tasks'])
            new_task = Task(
                project=project_name,
                task=task_name,
                members="",
                status=random.choice(statuses),
                priority='low',
                notes="משימה ללא צוות",
                team_id=None
            )
            db.session.add(new_task)

        db.session.commit()
        print("Hebrew dummy data created successfully!")

if __name__ == '__main__':
    seed_data_hebrew()
