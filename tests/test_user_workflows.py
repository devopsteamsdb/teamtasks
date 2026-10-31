"""
QA Automated Test Suite - End-to-End User Journeys & Workflow Integration
Simulates full user interactions: Project & Task Lifecycle, Kanban drag/drop, Gantt rescheduling,
AI Assistant task opening, and Multi-filter cross checks.
"""
import unittest
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models import db, Project, Task, Subtask, TaskComment, Team, TeamMember

class TestUserWorkflows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import shutil
        app.config['TESTING'] = True
        cls.client = app.test_client()
        cls.db_path = os.path.join(app.instance_path, 'tasks.db')
        cls.backup_path = os.path.join(app.instance_path, 'tasks.db.wf_qa_bak')
        if os.path.exists(cls.db_path):
            shutil.copyfile(cls.db_path, cls.backup_path)

    @classmethod
    def tearDownClass(cls):
        import shutil
        if hasattr(cls, 'backup_path') and os.path.exists(cls.backup_path):
            shutil.copyfile(cls.backup_path, cls.db_path)
            try:
                os.remove(cls.backup_path)
            except Exception:
                pass

    def setUp(self):
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    # -------------------------------------------------------------
    # Journey 1: Complete Task Lifecycle (Create, Checklist, Comments, Status, Archive)
    # -------------------------------------------------------------
    def test_complete_task_lifecycle_journey(self):
        """Simulates full user interaction from project creation to task archiving and comments"""
        # Step 1: User creates Team and Project
        t_res = self.client.post('/api/teams', json={'name_en': 'core', 'name_he': 'צוות ליבה'})
        team_id = t_res.get_json().get('team', t_res.get_json())['id']

        m_res = self.client.post('/api/members', json={
            'name_en': 'noa',
            'name_he': 'נועה מהנדסת',
            'team_id': team_id,
            'avatar_path': 'avatar_5.png'
        })
        member_name = 'נועה מהנדסת'

        p_res = self.client.post('/api/projects', json={'name': 'מערכת ניהול משימות', 'team_ids': [team_id]})
        proj_name = 'מערכת ניהול משימות'

        # Step 2: User creates Task via wide modal
        task_payload = {
            'task': 'פיתוח רכיב אימות',
            'project': proj_name,
            'team_id': team_id,
            'status': 'status-notstarted',
            'priority': 'high',
            'start_date': '2026-11-01',
            'end_date': '2026-11-10',
            'notes': 'תיאור המשימה שנכתב בפופ-אפ הרחב',
            'members': [member_name]
        }
        create_res = self.client.post('/api/tasks', json=task_payload)
        self.assertEqual(create_res.status_code, 200)
        task_id = create_res.get_json()['id']

        # Step 3: User opens task in wide modal and views details
        get_res = self.client.get(f'/api/tasks/{task_id}')
        self.assertEqual(get_res.status_code, 200)
        task_data = get_res.get_json()
        self.assertEqual(task_data['task'], 'פיתוח רכיב אימות')
        self.assertEqual(task_data['status'], 'status-notstarted')
        self.assertEqual(task_data['priority'], 'high')

        # Step 4: User adds 3 subtasks to checklist
        st1_res = self.client.post(f'/api/tasks/{task_id}/subtasks', json={'title': 'בניית סכמת נתונים'})
        st1_id = st1_res.get_json()['subtask']['id']

        st2_res = self.client.post(f'/api/tasks/{task_id}/subtasks', json={'title': 'הטמעת טוקן JWT'})
        st2_id = st2_res.get_json()['subtask']['id']

        st3_res = self.client.post(f'/api/tasks/{task_id}/subtasks', json={'title': 'כתיבת בדיקות יחידה'})
        st3_id = st3_res.get_json()['subtask']['id']

        # Step 5: User completes 2 of 3 subtasks and checks progress
        self.client.put(f'/api/subtasks/{st1_id}', json={'is_completed': True})
        self.client.put(f'/api/subtasks/{st2_id}', json={'is_completed': True})

        subtasks_res = self.client.get(f'/api/tasks/{task_id}/subtasks')
        subtasks = subtasks_res.get_json()
        completed_count = sum(1 for s in subtasks if s['is_completed'])
        self.assertEqual(completed_count, 2)
        self.assertEqual(len(subtasks), 3)

        # Step 6: User posts 2 comments in the discussion thread
        c1_res = self.client.post(f'/api/tasks/{task_id}/comments', json={
            'content': 'הסכמה והטוקן הוטמעו בהצלחה',
            'author_name': member_name,
            'author_avatar': 'avatar_5.png'
        })
        self.assertEqual(c1_res.status_code, 200)
        c1_id = c1_res.get_json()['comment']['id']

        c2_res = self.client.post(f'/api/tasks/{task_id}/comments', json={
            'content': 'נשאר רק לסיים בדיקות יחידה',
            'author_name': 'מנהל צוות'
        })
        self.assertEqual(c2_res.status_code, 200)

        comments_res = self.client.get(f'/api/tasks/{task_id}/comments')
        self.assertEqual(len(comments_res.get_json()), 2)

        # Step 7: User deletes first comment
        self.client.delete(f'/api/comments/{c1_id}')
        comments_after = self.client.get(f'/api/tasks/{task_id}/comments').get_json()
        self.assertEqual(len(comments_after), 1)

        # Step 8: User moves task to in progress, delayed, then done
        for new_status in ['status-inprogress', 'status-delayed', 'status-done']:
            update_res = self.client.put(f'/api/tasks/{task_id}', json={'status': new_status})
            self.assertEqual(update_res.status_code, 200)
            verify = self.client.get(f'/api/tasks/{task_id}').get_json()
            self.assertEqual(verify['status'], new_status)

        # Step 9: User archives task and verifies default filter excludes it
        self.client.post(f'/api/tasks/{task_id}/archive')
        active_tasks = self.client.get('/api/tasks').get_json()
        self.assertFalse(any(t['id'] == task_id for t in active_tasks), "Archived task should not appear in active tasks list")

        # But appears with include_archived=true
        all_tasks = self.client.get('/api/tasks?include_archived=true').get_json()
        self.assertTrue(any(t['id'] == task_id for t in all_tasks))

    # -------------------------------------------------------------
    # Journey 2: Kanban Board Status Transitions & Counting
    # -------------------------------------------------------------
    def test_kanban_status_transitions_and_counts(self):
        """Simulates drag-and-drop status changes between Kanban columns"""
        # Create Project & Team
        t_res = self.client.post('/api/teams', json={'name_en': 'kb', 'name_he': 'קנבן'})
        team_id = t_res.get_json().get('team', t_res.get_json())['id']
        self.client.post('/api/projects', json={'name': 'קנבן בורד', 'team_ids': [team_id]})

        # Create 4 tasks across columns
        task_ids = []
        statuses = ['status-notstarted', 'status-inprogress', 'status-delayed', 'status-done']
        for i, st in enumerate(statuses):
            r = self.client.post('/api/tasks', json={
                'task': f'משימה קנבן #{i+1}',
                'project': 'קנבן בורד',
                'team_id': team_id,
                'status': st
            })
            task_ids.append(r.get_json()['id'])

        # Verify initial column distribution
        for st in statuses:
            col_tasks = self.client.get(f'/api/tasks?status={st}').get_json()
            self.assertEqual(len(col_tasks), 1)

        # Simulate user dragging task 0 (not started) -> in progress
        self.client.put(f'/api/tasks/{task_ids[0]}', json={'status': 'status-inprogress'})

        # Now in-progress has 2, not-started has 0
        self.assertEqual(len(self.client.get('/api/tasks?status=status-inprogress').get_json()), 2)
        self.assertEqual(len(self.client.get('/api/tasks?status=status-notstarted').get_json()), 0)

        # Simulate user dragging task 2 (delayed) -> done
        self.client.put(f'/api/tasks/{task_ids[2]}', json={'status': 'status-done'})
        self.assertEqual(len(self.client.get('/api/tasks?status=status-done').get_json()), 2)
        self.assertEqual(len(self.client.get('/api/tasks?status=status-delayed').get_json()), 0)

    # -------------------------------------------------------------
    # Journey 3: Gantt Timeline Mouse Rescheduling Interactions
    # -------------------------------------------------------------
    def test_gantt_timeline_mouse_rescheduling(self):
        """Simulates Gantt timeline interactions: date assignment, right-handle resizing, schedule shifting"""
        t_res = self.client.post('/api/teams', json={'name_en': 'gt', 'name_he': 'גאנט'})
        team_id = t_res.get_json().get('team', t_res.get_json())['id']
        self.client.post('/api/projects', json={'name': 'פרויקט גאנט', 'team_ids': [team_id]})

        # User creates unscheduled task (no dates)
        t_res = self.client.post('/api/tasks', json={
            'task': 'משימה ללא תאריך',
            'project': 'פרויקט גאנט'
        })
        task_id = t_res.get_json()['id']

        # User marks date range using mouse drag across days (e.g. 2026-11-01 to 2026-11-05)
        res = self.client.put(f'/api/tasks/{task_id}/schedule', json={
            'start_date': '2026-11-01',
            'end_date': '2026-11-05'
        })
        self.assertEqual(res.status_code, 200)
        self.assertTrue('2026-11-01' in res.get_json()['task']['start_date'])
        self.assertTrue('2026-11-05' in res.get_json()['task']['end_date'])

        # User drags right resize handle to extend 5 days (to 2026-11-10)
        res = self.client.put(f'/api/tasks/{task_id}/schedule', json={
            'start_date': '2026-11-01',
            'end_date': '2026-11-10'
        })
        self.assertEqual(res.status_code, 200)
        self.assertTrue('2026-11-10' in res.get_json()['task']['end_date'])

        # User drags the whole bar to move dates 10 days forward (fixed duration of 9 days)
        res = self.client.put(f'/api/tasks/{task_id}/schedule', json={
            'start_date': '2026-11-11',
            'end_date': '2026-11-20'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()['task']
        self.assertTrue('2026-11-11' in data['start_date'])
        self.assertTrue('2026-11-20' in data['end_date'])

    # -------------------------------------------------------------
    # Journey 4: AI Assistant Interaction & Navigation
    # -------------------------------------------------------------
    def test_ai_assistant_and_navigation(self):
        """Tests AI Assistant endpoints and dashboard ?open_task= query parameter handling"""
        # AI status check
        status_res = self.client.get('/api/ai/status')
        self.assertEqual(status_res.status_code, 200)
        self.assertTrue(status_res.get_json().get('success', False))

        # Create a task to reference
        t_res = self.client.post('/api/teams', json={'name_en': 'ai_team', 'name_he': 'צוות בינה'})
        team_id = t_res.get_json().get('team', t_res.get_json())['id']
        self.client.post('/api/projects', json={'name': 'פרויקט AI', 'team_ids': [team_id]})

        task_res = self.client.post('/api/tasks', json={'task': 'משימה לבדיקת AI', 'project': 'פרויקט AI'})
        task_id = task_res.get_json()['id']

        # User clicks a task pill in AI assistant from Admin page -> navigates to /?open_task=<id>
        dash_res = self.client.get(f'/?open_task={task_id}')
        self.assertEqual(dash_res.status_code, 200)
        html = dash_res.data.decode('utf-8')
        self.assertIn('taskModal', html)
        self.assertIn('aiFabBtn', html)

if __name__ == '__main__':
    unittest.main()
