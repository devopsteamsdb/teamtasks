# -*- coding: utf-8 -*-
"""
Automated 50-Query Evaluation Suite for TeamTasks AI Assistant
Simulates a human user asking questions and giving commands in natural Hebrew.
Verifies understanding, execution accuracy, polite natural language responses,
and checks for edge cases, slang, and formatting integrity.
"""

import os
import sys
import json
import time
import shutil

# Ensure UTF-8 output encoding across Windows terminals
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from app import app
from models import db, Task, Project, Team, TeamMember

QUERIES = [
    # ------------------------------------------------------------------
    # Category 1: Questions & Status Lookups (Read-Only)
    # ------------------------------------------------------------------
    {
        "id": 1,
        "query": "מה המצב של משימה 2?",
        "expected_type": "read",
        "description": "Status lookup by ID"
    },
    {
        "id": 2,
        "query": "תגיד לי מה הסטטוס של שדרוג Ingress Controller?",
        "expected_type": "read",
        "description": "Status lookup by task name substring"
    },
    {
        "id": 3,
        "query": "מי עובד על משימה 3?",
        "expected_type": "read",
        "description": "Assignee lookup by task ID"
    },
    {
        "id": 4,
        "query": "מה המשימות של מיכל?",
        "expected_type": "read",
        "description": "Member tasks list"
    },
    {
        "id": 5,
        "query": "כמה משימות פתוחות יש לרועי?",
        "expected_type": "read",
        "description": "Member open tasks count query"
    },
    {
        "id": 6,
        "query": "איזה משימות יש לצוות DevOps?",
        "expected_type": "read",
        "description": "Team tasks list"
    },
    {
        "id": 7,
        "query": "מה המשימות הפתוחות של צוות Frontend?",
        "expected_type": "read",
        "description": "Team open tasks list"
    },
    {
        "id": 8,
        "query": "ספר לי קצת על פרויקט אפליקציית מובייל ללקוחות",
        "expected_type": "read",
        "description": "Project overview query"
    },
    {
        "id": 9,
        "query": "איזה משימות נמצאות בעיכוב כרגע?",
        "expected_type": "read",
        "description": "Delayed tasks query"
    },
    {
        "id": 10,
        "query": "מה הדדליינים שמגיעים השבוע?",
        "expected_type": "read",
        "description": "Deadlines analysis query"
    },

    # ------------------------------------------------------------------
    # Category 2: Marking Done / Status Updates (Action)
    # ------------------------------------------------------------------
    {
        "id": 11,
        "query": "סיימתי את משימה 3",
        "expected_type": "mutation",
        "expected_action": ["edit_task", "update_task"],
        "expected_task_id": 3,
        "description": "Colloquial completion ('סיימתי את')"
    },
    {
        "id": 12,
        "query": "תסמן את משימה 5 כבתהליך",
        "expected_type": "mutation",
        "expected_action": ["edit_task", "update_task"],
        "expected_task_id": 5,
        "description": "Explicit status update to in-progress"
    },
    {
        "id": 13,
        "query": "משימה 10 תקועה, שים אותה בעיכוב",
        "expected_type": "mutation",
        "expected_action": ["edit_task", "update_task"],
        "expected_task_id": 10,
        "description": "Slang status update: 'תקועה שים בעיכוב' -> delayed"
    },
    {
        "id": 14,
        "query": "תחזיר את משימה 1 לסטטוס טרם החל",
        "expected_type": "mutation",
        "expected_action": ["edit_task", "update_task"],
        "expected_task_id": 1,
        "description": "Reset status to not-started"
    },
    {
        "id": 15,
        "query": "סגור לי בבקשה את המשימה של Terraform Cloud",
        "expected_type": "mutation",
        "expected_action": ["edit_task", "update_task"],
        "expected_task_id": 2,
        "description": "Close task by name ('סגור לי')"
    },
    {
        "id": 16,
        "query": "תשני את משימה 9 לבוצע",
        "expected_type": "mutation",
        "expected_action": ["edit_task", "update_task"],
        "expected_task_id": 9,
        "description": "Female conjugation ('תשני') + done ('בוצע')"
    },
    {
        "id": 17,
        "query": "תעדכן את משימה 11 שהתחלנו לעבוד עליה",
        "expected_type": "mutation",
        "expected_action": ["edit_task", "update_task"],
        "expected_task_id": 11,
        "description": "Colloquial in-progress: 'התחלנו לעבוד עליה'"
    },
    {
        "id": 18,
        "query": "משימה 6 הסתיימה בהצלחה",
        "expected_type": "mutation",
        "expected_action": ["edit_task", "update_task"],
        "expected_task_id": 6,
        "description": "Colloquial completion: 'הסתיימה בהצלחה'"
    },
    {
        "id": 19,
        "query": "תעביר את משימה 15 לבתהליך",
        "expected_type": "mutation",
        "expected_action": ["edit_task", "update_task"],
        "expected_task_id": 15,
        "description": "Move to in-progress"
    },
    {
        "id": 20,
        "query": "יאללה סיימנו את אופטימיזציית ביצועים וטעינת תמונות, תסמן כהושלם",
        "expected_type": "mutation",
        "expected_action": ["edit_task", "update_task"],
        "expected_task_id": 10,
        "description": "Slang + long task title completion"
    },

    # ------------------------------------------------------------------
    # Category 3: Creating New Tasks & Projects (Action)
    # ------------------------------------------------------------------
    {
        "id": 21,
        "query": "תוסיף משימה חדשה בשם 'בדיקת גיבויים שבועית' בפרויקט שדרוג תשתיות ענן ו-Kubernetes",
        "expected_type": "mutation",
        "expected_action": ["create_task"],
        "description": "Create standard task with project name"
    },
    {
        "id": 22,
        "query": "פתח משימה חדשה לאלעד שנקראת 'הגדרת התראות PagerDuty' בעדיפות גבוהה",
        "expected_type": "mutation",
        "expected_action": ["create_task"],
        "description": "Create task with member and priority"
    },
    {
        "id": 23,
        "query": "תוסיף משימה 'עדכון תעודות SSL' לדוד עם יעד למחר",
        "expected_type": "mutation",
        "expected_action": ["create_task"],
        "description": "Create task with relative date 'למחר'"
    },
    {
        "id": 24,
        "query": "צור משימה דחופה לנועה: 'בדיקת קריסות באייפון' עם הערות 'דחוף מאוד לפני ההשקה'",
        "expected_type": "mutation",
        "expected_action": ["create_task"],
        "description": "Create task with notes and urgent priority"
    },
    {
        "id": 25,
        "query": "תוסיף משימה חדשה 'שדרוג Node.js' לצוות Backend עם 8 שעות משוערות",
        "expected_type": "mutation",
        "expected_action": ["create_task"],
        "description": "Create task with team and estimated hours"
    },
    {
        "id": 26,
        "query": "פתח פרויקט חדש בשם 'אבטחת שרשרת אספקה' לצוות אבטחת מידע",
        "expected_type": "mutation",
        "expected_action": ["create_project"],
        "description": "Create project with team"
    },
    {
        "id": 27,
        "query": "תוסיף פרויקט 'מיגרציה לענן 2027'",
        "expected_type": "mutation",
        "expected_action": ["create_project"],
        "description": "Create project standalone"
    },
    {
        "id": 28,
        "query": "צור משימה עם צ'קליסט: 'התקנת שרת חדש' בפרויקט שדרוג תשתיות ענן ו-Kubernetes עם תתי משימות: 'הזמנת חומרה', 'התקנת לינוקס', 'חיבור לרשת'",
        "expected_type": "mutation",
        "expected_action": ["create_task"],
        "description": "Create task with checklist / subtasks"
    },
    {
        "id": 29,
        "query": "תוסיף משימה 'בדיקות רגרסיה' לפרויקט אוטומציית בדיקות ו-CI/CD שמשויכת לגל ועומר",
        "expected_type": "mutation",
        "expected_action": ["create_task"],
        "description": "Create task with multiple assignees ('גל ועומר')"
    },
    {
        "id": 30,
        "query": "שים משימה חדשה 'כתיבת תיעוד API' בתהליך בעדיפות בינונית",
        "expected_type": "mutation",
        "expected_action": ["create_task"],
        "description": "Create task with status in-progress and medium priority"
    },

    # ------------------------------------------------------------------
    # Category 4: Modifying Existing Tasks (Assignees, Dates, Notes, Priorities)
    # ------------------------------------------------------------------
    {
        "id": 31,
        "query": "תוסיף את רועי למשימה 5",
        "expected_type": "mutation",
        "expected_action": ["edit_task", "update_task"],
        "expected_task_id": 5,
        "description": "Add member to existing task"
    },
    {
        "id": 32,
        "query": "תוריד את אלכס ממשימה 4",
        "expected_type": "mutation",
        "expected_action": ["edit_task", "update_task"],
        "expected_task_id": 4,
        "description": "Remove member from existing task"
    },
    {
        "id": 33,
        "query": "תשנה את העדיפות של משימה 6 לגבוהה",
        "expected_type": "mutation",
        "expected_action": ["edit_task", "update_task"],
        "expected_task_id": 6,
        "description": "Change priority to high"
    },
    {
        "id": 34,
        "query": "תעדכן את משימה 2 שהעדיפות שלה נמוכה",
        "expected_type": "mutation",
        "expected_action": ["edit_task", "update_task"],
        "expected_task_id": 2,
        "description": "Change priority to low"
    },
    {
        "id": 35,
        "query": "תוסיף הערה למשימה 3: 'ממתינים לאישור מנהל'",
        "expected_type": "mutation",
        "expected_action": ["edit_task", "update_task"],
        "expected_task_id": 3,
        "description": "Append note to task"
    },
    {
        "id": 36,
        "query": "תשנה את השם של משימה 11 ל-'מסך פרופיל מעודכן 2026'",
        "expected_type": "mutation",
        "expected_action": ["edit_task", "update_task"],
        "expected_task_id": 11,
        "description": "Rename existing task"
    },
    {
        "id": 37,
        "query": "תעדכן את תאריך היעד של משימה 8 ל-15/11/2026",
        "expected_type": "mutation",
        "expected_action": ["edit_task", "update_task"],
        "expected_task_id": 8,
        "description": "Update end date"
    },
    {
        "id": 38,
        "query": "שים את משימה 14 בעדיפות דחופה",
        "expected_type": "mutation",
        "expected_action": ["edit_task", "update_task"],
        "expected_task_id": 14,
        "description": "Colloquial priority: 'דחופה' -> high"
    },
    {
        "id": 39,
        "query": "תקצה את משימה 10 למאיה בלבד",
        "expected_type": "mutation",
        "expected_action": ["edit_task", "update_task"],
        "expected_task_id": 10,
        "description": "Assign task to single member"
    },
    {
        "id": 40,
        "query": "תוסיף תת משימה 'בדיקת עומסים' למשימה 2",
        "expected_type": "mutation",
        "expected_action": ["edit_task", "update_task", "create_subtask"],
        "expected_task_id": 2,
        "description": "Add subtask to existing task"
    },

    # ------------------------------------------------------------------
    # Category 5: Complex, Colloquial, Archiving, Deletion & Conversational
    # ------------------------------------------------------------------
    {
        "id": 41,
        "query": "היי, מה קורה? מי אתה ומה אתה יודע לעשות?",
        "expected_type": "chat",
        "description": "Greeting and bot identity / help"
    },
    {
        "id": 42,
        "query": "תן לי סיכום מנהלים מהיר על המערכת",
        "expected_type": "read",
        "description": "Executive summary request"
    },
    {
        "id": 43,
        "query": "תעביר את משימה 15 לארכיון",
        "expected_type": "mutation",
        "expected_action": ["archive_task"],
        "expected_task_id": 15,
        "description": "Archive task"
    },
    {
        "id": 44,
        "query": "תשחזר את משימה 15 מהארכיון",
        "expected_type": "mutation",
        "expected_action": ["unarchive_task", "archive_task"],
        "expected_task_id": 15,
        "description": "Unarchive task"
    },
    {
        "id": 45,
        "query": "תמחק את משימה 6",
        "expected_type": "mutation",
        "expected_action": ["delete_task"],
        "expected_task_id": 6,
        "description": "Delete task"
    },
    {
        "id": 46,
        "query": "יש איזה משימות בלי אחראי?",
        "expected_type": "read",
        "description": "Unassigned / stale tasks inquiry"
    },
    {
        "id": 47,
        "query": "תוסיף חבר צוות חדש בשם 'דניאל כהן' (daniel) לצוות DevOps",
        "expected_type": "mutation",
        "expected_action": ["create_member"],
        "description": "Create new team member"
    },
    {
        "id": 48,
        "query": "תמחק את פרויקט בדיקות אוטומציה",
        "expected_type": "mutation",
        "expected_action": ["delete_project"],
        "description": "Delete project by name"
    },
    {
        "id": 49,
        "query": "תודה רבה לך, עזרת לי מאוד!",
        "expected_type": "chat",
        "description": "Gratitude / closing conversational message"
    },
    {
        "id": 50,
        "query": "איזה צוותים יש במערכת ומי נמצא בהם?",
        "expected_type": "read",
        "description": "Full teams and members overview"
    }
]


def run_evaluation():
    print("=" * 75)
    print("  TEAMTASKS AI ASSISTANT - 50 NATURAL LANGUAGE QUERIES EVALUATION")
    print("=" * 75)

    # Ensure Task 6 exists before backup
    with app.app_context():
        if not db.session.get(Task, 6):
            proj = Project.query.filter_by(name='שדרוג תשתיות ענן ו-Kubernetes').first()
            t6 = Task(
                id=6,
                project_id=proj.id if proj else 1,
                project=proj.name if proj else 'שדרוג תשתיות ענן ו-Kubernetes',
                task='אופטימיזציית עלויות ענן (FinOps)',
                notes='סריקת משאבים עודפים, מחיקת דיסקים יתומים ורכישת התחייבויות שמורות.',
                members='michal',
                status='status-notstarted',
                priority='none',
                estimated_hours=16.0
            )
            db.session.add(t6)
            db.session.commit()

    # Backup production database before evaluation
    db_path = os.path.join(app.instance_path, 'tasks.db')
    backup_path = os.path.join(app.instance_path, 'tasks.db.eval_50_bak')
    if os.path.exists(db_path):
        shutil.copyfile(db_path, backup_path)
        print(f"Backed up tasks.db -> {backup_path}")

    client = app.test_client()
    history = []

    passed_count = 0
    failed_count = 0
    results_log = []

    try:
        for item in QUERIES:
            q_id = item["id"]
            user_msg = item["query"]
            q_type = item["expected_type"]
            q_desc = item["description"]

            print(f"\n[{q_id:02d}/50] ({q_type.upper()}) \"{user_msg}\"")
            print(f"       Intent: {q_desc}")

            start_t = time.time()
            try:
                resp = client.post('/api/ai/chat', json={
                    'message': user_msg,
                    'history': history[-6:]  # keep last 3 turns
                })
                duration = time.time() - start_t
                status_code = resp.status_code
                data = resp.get_json() or {}
            except Exception as e:
                duration = time.time() - start_t
                status_code = 500
                data = {'error': str(e)}

            if status_code != 200:
                print(f"       [FAIL] HTTP {status_code}: {data.get('error')}")
                failed_count += 1
                results_log.append({
                    "id": q_id,
                    "query": user_msg,
                    "passed": False,
                    "reason": f"HTTP status {status_code}: {data.get('error')}"
                })
                continue

            reply = data.get('reply', '')
            actions = data.get('actions', [])
            refresh = data.get('refresh_needed', False)

            # Check rule violations (e.g. leaking "בלוק JSON")
            has_json_leak = any(k in reply for k in ["בלוק JSON", "בלוק json", "קוד JSON", "מבנה JSON", "```json"])
            
            # Verify based on expected type
            is_valid = True
            reasons = []

            if has_json_leak:
                is_valid = False
                reasons.append("Leaked JSON technical phrasing to user")

            if q_type == "read":
                mutating_actions = [a for a in actions if a.get('action') not in ['list_tasks', 'list_projects', 'search_tasks', 'get_tasks']]
                if mutating_actions:
                    is_valid = False
                    reasons.append(f"Read query emitted unexpected mutating actions: {mutating_actions}")
                if not reply or len(reply.strip()) < 5:
                    is_valid = False
                    reasons.append("Empty or trivial read reply")

            elif q_type == "mutation":
                expected_actions = item.get("expected_action", [])
                expected_task_id = item.get("expected_task_id")

                if not actions:
                    is_valid = False
                    reasons.append("Expected mutating action, but none executed")
                else:
                    act_names = [a.get('action') for a in actions]
                    if expected_actions and not any(ea in act_names for ea in expected_actions):
                        is_valid = False
                        reasons.append(f"Executed actions {act_names} did not match expected {expected_actions}")

                    if expected_task_id:
                        matched_id = any(
                            (a.get('task_id') == expected_task_id) or
                            (isinstance(a.get('task'), dict) and a['task'].get('id') == expected_task_id) or
                            (f"#{expected_task_id}" in str(a.get('description', '')))
                            for a in actions
                        )
                        if not matched_id:
                            is_valid = False
                            reasons.append(f"Action did not target expected task #{expected_task_id}")

            elif q_type == "chat":
                mutating_actions = [a for a in actions if a.get('action') not in ['list_tasks', 'list_projects']]
                if mutating_actions:
                    is_valid = False
                    reasons.append(f"Casual chat query emitted mutating actions: {mutating_actions}")
                if not reply or len(reply.strip()) < 5:
                    is_valid = False
                    reasons.append("Empty casual reply")

            if is_valid:
                passed_count += 1
                act_str = f" | Actions: {[a.get('action') for a in actions]}" if actions else ""
                rep_preview = (reply.replace('\n', ' ')[:85] + '...') if len(reply) > 85 else reply.replace('\n', ' ')
                print(f"       [PASS] ({duration:.2f}s){act_str}")
                print(f"       Reply: \"{rep_preview}\"")
                history.append({'role': 'user', 'content': user_msg})
                history.append({'role': 'assistant', 'content': reply})
            else:
                failed_count += 1
                fail_reason = "; ".join(reasons)
                print(f"       [FAIL] ({duration:.2f}s) Reason: {fail_reason}")
                print(f"       Reply: \"{reply[:120]}\"")
                print(f"       Actions: {actions}")

            results_log.append({
                "id": q_id,
                "query": user_msg,
                "type": q_type,
                "passed": is_valid,
                "reasons": reasons,
                "duration": duration,
                "reply": reply,
                "actions": actions
            })

    finally:
        try:
            with app.app_context():
                db.session.remove()
                db.engine.dispose()
        except Exception:
            pass

        # Restore production database backup
        if os.path.exists(backup_path):
            try:
                shutil.copyfile(backup_path, db_path)
                os.remove(backup_path)
                print(f"\nRestored original tasks.db from backup.")
            except Exception as e:
                print(f"Error restoring backup: {e}")

    print("\n" + "=" * 75)
    print("  EVALUATION SUMMARY")
    print("=" * 75)
    print(f"Total Queries: {len(QUERIES)}")
    print(f"Passed:        {passed_count} ({passed_count/len(QUERIES)*100:.1f}%)")
    print(f"Failed:        {failed_count} ({failed_count/len(QUERIES)*100:.1f}%)")
    print("=" * 75)

    return {
        "total": len(QUERIES),
        "passed": passed_count,
        "failed": failed_count,
        "results": results_log
    }

if __name__ == '__main__':
    run_evaluation()
