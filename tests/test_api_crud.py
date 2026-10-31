"""
QA Automated Test Suite - REST API & CRUD Operations
Covers all endpoints: Projects, Tasks, Subtasks, Comments, Teams, Members, Special Days, Backup & Restore
"""
import unittest
import json
import os
import io
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models import db, Project, Task, Subtask, TaskComment, Team, TeamMember, SpecialDay

class TestApiCrud(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import shutil
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        cls.client = app.test_client()
        cls.db_path = os.path.join(app.instance_path, 'tasks.db')
        cls.backup_path = os.path.join(app.instance_path, 'tasks.db.crud_qa_bak')
        if os.path.exists(cls.db_path):
            shutil.copyfile(cls.db_path, cls.backup_path)
        with app.app_context():
            db.drop_all()
            db.create_all()

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
    # 1. Projects API Tests
    # -------------------------------------------------------------
    def test_project_crud_lifecycle(self):
        """Test full project CRUD: create, list, get, update, archive, unarchive, delete"""
        # First create a team to assign to the project
        t_res = self.client.post('/api/teams', json={'name_en': 'devops', 'name_he': 'צוות דבאופס'})
        self.assertIn(t_res.status_code, (200, 201))
        t_data = t_res.get_json()
        team_id = t_data.get('team', t_data)['id']

        # Create project with team_ids
        res = self.client.post('/api/projects', json={'name': 'פרויקט אלפא', 'team_ids': [team_id]})
        self.assertIn(res.status_code, (200, 201))
        data = res.get_json()
        project = data.get('project', data)
        self.assertIn('id', project)
        proj_id = project['id']
        self.assertEqual(project['name'], 'פרויקט אלפא')

        # List projects
        res = self.client.get('/api/projects')
        self.assertEqual(res.status_code, 200)
        projects = res.get_json()
        self.assertTrue(any(p['id'] == proj_id for p in projects))

        # Get project by ID
        res = self.client.get(f'/api/projects/{proj_id}')
        self.assertEqual(res.status_code, 200)
        proj_data = res.get_json()
        self.assertEqual(proj_data.get('project', proj_data)['name'], 'פרויקט אלפא')

        # Update project name
        res = self.client.put(f'/api/projects/{proj_id}', json={'name': 'פרויקט בטא מעודכן', 'team_ids': [team_id]})
        self.assertEqual(res.status_code, 200)
        updated_data = res.get_json()
        self.assertEqual(updated_data.get('project', updated_data)['name'], 'פרויקט בטא מעודכן')

        # Archive project (supports both POST and PUT)
        res = self.client.post(f'/api/projects/{proj_id}/archive')
        self.assertEqual(res.status_code, 200)

        # Verify archived status
        res = self.client.get(f'/api/projects/{proj_id}')
        proj_obj = res.get_json().get('project', res.get_json())
        self.assertTrue(proj_obj.get('is_archived', False))

        # Unarchive project
        res = self.client.post(f'/api/projects/{proj_id}/unarchive')
        self.assertEqual(res.status_code, 200)
        res = self.client.get(f'/api/projects/{proj_id}')
        proj_obj = res.get_json().get('project', res.get_json())
        self.assertFalse(proj_obj.get('is_archived', False))

        # Delete project
        res = self.client.delete(f'/api/projects/{proj_id}')
        self.assertEqual(res.status_code, 200)

        # Verify not found after delete
        res = self.client.get(f'/api/projects/{proj_id}')
        self.assertEqual(res.status_code, 404)

    # -------------------------------------------------------------
    # 2. Teams & Members API Tests
    # -------------------------------------------------------------
    def test_teams_and_members_crud(self):
        """Test team and member creation, listing, updating, and deletion"""
        # Create team
        res = self.client.post('/api/teams', json={'name_en': 'infra', 'name_he': 'צוות תשתיות'})
        self.assertIn(res.status_code, (200, 201))
        team = res.get_json().get('team', res.get_json())
        team_id = team['id']

        # Create member in team
        res = self.client.post('/api/members', json={
            'name_en': 'israel',
            'name_he': 'ישראל ישראלי',
            'team_id': team_id,
            'avatar_path': 'avatar1.png'
        })
        self.assertIn(res.status_code, (200, 201))
        member = res.get_json().get('member', res.get_json())
        member_id = member['id']
        self.assertEqual(member['name_he'], 'ישראל ישראלי')

        # List members
        res = self.client.get('/api/members')
        self.assertEqual(res.status_code, 200)
        members = res.get_json()
        self.assertTrue(any(m['id'] == member_id for m in members))

        # Update member
        res = self.client.put(f'/api/members/{member_id}', json={
            'name_en': 'israel',
            'name_he': 'ישראל כהן',
            'team_id': team_id
        })
        self.assertEqual(res.status_code, 200)
        updated = res.get_json().get('member', res.get_json())
        self.assertEqual(updated['name_he'], 'ישראל כהן')

        # Delete member
        res = self.client.delete(f'/api/members/{member_id}')
        self.assertEqual(res.status_code, 200)

        # Delete team
        res = self.client.delete(f'/api/teams/{team_id}')
        self.assertEqual(res.status_code, 200)

    # -------------------------------------------------------------
    # 3. Tasks API & Filtering Tests
    # -------------------------------------------------------------
    def test_task_crud_and_filters(self):
        """Test task creation, updates, filtering by status, priority, and text search"""
        # Setup team and project
        t_res = self.client.post('/api/teams', json={'name_en': 'cloud', 'name_he': 'Cloud Team'})
        team_id = t_res.get_json().get('team', t_res.get_json())['id']

        p_res = self.client.post('/api/projects', json={'name': 'DevOps Hub', 'team_ids': [team_id]})
        proj = p_res.get_json().get('project', p_res.get_json())
        proj_name = proj['name']

        # Create Task
        res = self.client.post('/api/tasks', json={
            'task': 'הקמת אשכול קוברנטיס',
            'project': proj_name,
            'team_id': team_id,
            'status': 'status-inprogress',
            'priority': 'high',
            'start_date': '2026-11-01',
            'end_date': '2026-11-10',
            'notes': 'הערות בדיקה למשימה',
            'members': ['יוסי', 'דנה']
        })
        self.assertIn(res.status_code, (200, 201))
        task_data = res.get_json()
        task = task_data.get('task', task_data)
        task_id = task['id']
        self.assertEqual(task['task'], 'הקמת אשכול קוברנטיס')
        self.assertEqual(task['priority'], 'high')
        self.assertEqual(task['status'], 'status-inprogress')
        self.assertIn('יוסי', task['members'])

        # Filter by status
        res = self.client.get('/api/tasks?status=status-inprogress')
        self.assertEqual(res.status_code, 200)
        tasks = res.get_json()
        self.assertTrue(any(t['id'] == task_id for t in tasks))

        res = self.client.get('/api/tasks?status=status-done')
        self.assertEqual(res.status_code, 200)
        tasks = res.get_json()
        self.assertFalse(any(t['id'] == task_id for t in tasks))

        # Filter by priority
        res = self.client.get('/api/tasks?priority=high')
        self.assertTrue(any(t['id'] == task_id for t in res.get_json()))

        # Filter by text search
        res = self.client.get('/api/tasks?search=קוברנטיס')
        self.assertTrue(any(t['id'] == task_id for t in res.get_json()))

        # Update task
        res = self.client.put(f'/api/tasks/{task_id}', json={
            'task': 'הקמת אשכול קוברנטיס - הושלם',
            'project': proj_name,
            'team_id': team_id,
            'status': 'status-done',
            'priority': 'medium',
            'notes': 'הערה עודכנה',
            'members': ['יוסי']
        })
        self.assertEqual(res.status_code, 200)
        updated = res.get_json().get('task', res.get_json())
        self.assertEqual(updated['status'], 'status-done')
        self.assertEqual(updated['priority'], 'medium')

        # Archive and unarchive task
        res = self.client.post(f'/api/tasks/{task_id}/archive')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json().get('task', res.get_json()).get('is_archived', False))

        res = self.client.post(f'/api/tasks/{task_id}/unarchive')
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.get_json().get('task', res.get_json()).get('is_archived', False))

    # -------------------------------------------------------------
    # 4. Task Schedule API Tests (Gantt timeline updates)
    # -------------------------------------------------------------
    def test_task_schedule_endpoint(self):
        """Test /api/tasks/<id>/schedule endpoint for resizing and shifting dates"""
        t_res = self.client.post('/api/teams', json={'name_en': 'tl', 'name_he': 'צוות לוח'})
        team_id = t_res.get_json().get('team', t_res.get_json())['id']

        p_res = self.client.post('/api/projects', json={'name': 'Timeline Test', 'team_ids': [team_id]})
        
        task_res = self.client.post('/api/tasks', json={
            'task': 'משימת לוח זמנים',
            'project': 'Timeline Test',
            'status': 'status-inprogress'
        })
        task_id = task_res.get_json()['id']

        # Assign initial dates
        res = self.client.put(f'/api/tasks/{task_id}/schedule', json={
            'start_date': '2026-11-05',
            'end_date': '2026-11-12'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue('2026-11-05' in data['task']['start_date'])
        self.assertTrue('2026-11-12' in data['task']['end_date'])

        # Resize end date (extend schedule)
        res = self.client.put(f'/api/tasks/{task_id}/schedule', json={
            'start_date': '2026-11-05',
            'end_date': '2026-11-20'
        })
        self.assertEqual(res.status_code, 200)
        self.assertTrue('2026-11-20' in res.get_json()['task']['end_date'])

        # Shift schedule to next month
        res = self.client.put(f'/api/tasks/{task_id}/schedule', json={
            'start_date': '2026-12-01',
            'end_date': '2026-12-16'
        })
        self.assertEqual(res.status_code, 200)
        self.assertTrue('2026-12-01' in res.get_json()['task']['start_date'])

        # Clear dates
        res = self.client.put(f'/api/tasks/{task_id}/schedule', json={
            'start_date': None,
            'end_date': None
        })
        self.assertEqual(res.status_code, 200)
        self.assertIsNone(res.get_json()['task']['start_date'])
        self.assertIsNone(res.get_json()['task']['end_date'])

    # -------------------------------------------------------------
    # 5. Subtasks (Checklist) API Tests
    # -------------------------------------------------------------
    def test_subtasks_crud_and_progress(self):
        """Test checklist subtasks: create, list, toggle completion, delete"""
        t_res = self.client.post('/api/teams', json={'name_en': 'st', 'name_he': 'צוות צקליסט'})
        team_id = t_res.get_json().get('team', t_res.get_json())['id']

        p_res = self.client.post('/api/projects', json={'name': 'Subtask Proj', 'team_ids': [team_id]})

        t_res = self.client.post('/api/tasks', json={'task': 'משימת צ\'ק ליסט', 'project': 'Subtask Proj'})
        task_id = t_res.get_json()['id']

        # Create subtasks
        st1_res = self.client.post(f'/api/tasks/{task_id}/subtasks', json={'title': 'שלב א: אפיון'})
        self.assertIn(st1_res.status_code, (200, 201))
        st1_data = st1_res.get_json()
        st1 = st1_data.get('subtask', st1_data)
        self.assertFalse(st1['is_completed'])
        st1_id = st1['id']

        st2_res = self.client.post(f'/api/tasks/{task_id}/subtasks', json={'title': 'שלב ב: פיתוח'})
        self.assertIn(st2_res.status_code, (200, 201))
        st2_data = st2_res.get_json()
        st2_id = st2_data.get('subtask', st2_data)['id']

        # List subtasks
        res = self.client.get(f'/api/tasks/{task_id}/subtasks')
        self.assertEqual(res.status_code, 200)
        subtasks = res.get_json()
        self.assertEqual(len(subtasks), 2)

        # Mark first subtask completed
        res = self.client.put(f'/api/subtasks/{st1_id}', json={'is_completed': True})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json().get('subtask', res.get_json())['is_completed'])

        # Verify task subtasks count and completion in list
        res = self.client.get(f'/api/tasks/{task_id}/subtasks')
        subtasks = res.get_json()
        completed = [s for s in subtasks if s['is_completed']]
        self.assertEqual(len(completed), 1)

        # Delete subtask
        res = self.client.delete(f'/api/subtasks/{st2_id}')
        self.assertEqual(res.status_code, 200)

        res = self.client.get(f'/api/tasks/{task_id}/subtasks')
        self.assertEqual(len(res.get_json()), 1)

        # Check /api/version returns timestamp and no-cache
        res_v = self.client.get('/api/version')
        self.assertEqual(res_v.status_code, 200)
        self.assertIn('timestamp', res_v.get_json())
        self.assertIn('no-cache', res_v.headers.get('Cache-Control', ''))

        # Check index returns no-cache headers for dynamic page refreshes
        res_idx = self.client.get('/')
        self.assertEqual(res_idx.status_code, 200)
        self.assertIn('no-cache', res_idx.headers.get('Cache-Control', ''))

    # -------------------------------------------------------------
    # 6. Task Comments API Tests
    # -------------------------------------------------------------
    def test_comments_crud(self):
        """Test task comments thread: posting with author and avatar, listing, deleting"""
        t_res = self.client.post('/api/teams', json={'name_en': 'cm', 'name_he': 'צוות תגובות'})
        team_id = t_res.get_json().get('team', t_res.get_json())['id']

        p_res = self.client.post('/api/projects', json={'name': 'Comment Proj', 'team_ids': [team_id]})

        t_res = self.client.post('/api/tasks', json={'task': 'משימת תגובות', 'project': 'Comment Proj'})
        task_id = t_res.get_json()['id']

        # Post comment
        c1_res = self.client.post(f'/api/tasks/{task_id}/comments', json={
            'content': 'התחלנו בעבודה על המשימה',
            'author_name': 'רון מנהל',
            'author_avatar': 'avatar3.png'
        })
        self.assertIn(c1_res.status_code, (200, 201))
        c1_data = c1_res.get_json()
        c1 = c1_data.get('comment', c1_data)
        c1_id = c1['id']
        self.assertEqual(c1['author_name'], 'רון מנהל')
        self.assertIn('created_at', c1)

        # Post second comment
        c2_res = self.client.post(f'/api/tasks/{task_id}/comments', json={
            'content': 'בדיקות ראשוניות עברו בהצלחה',
            'author_name': 'מאיה בודקת'
        })
        self.assertIn(c2_res.status_code, (200, 201))
        c2_data = c2_res.get_json()
        c2_id = c2_data.get('comment', c2_data)['id']

        # List comments
        res = self.client.get(f'/api/tasks/{task_id}/comments')
        self.assertEqual(res.status_code, 200)
        comments = res.get_json()
        self.assertEqual(len(comments), 2)

        # Delete comment
        res = self.client.delete(f'/api/comments/{c1_id}')
        self.assertEqual(res.status_code, 200)

        res = self.client.get(f'/api/tasks/{task_id}/comments')
        self.assertEqual(len(res.get_json()), 1)
        self.assertEqual(res.get_json()[0]['id'], c2_id)

    # -------------------------------------------------------------
    # 7. System Backup & Restore Tests
    # -------------------------------------------------------------
    def test_system_backup_and_restore_integrity(self):
        """Test full system backup JSON export and restore, verifying subtasks and comments persistence"""
        t_res = self.client.post('/api/teams', json={'name_en': 'qa', 'name_he': 'QA Team'})
        team_id = t_res.get_json().get('team', t_res.get_json())['id']

        p_res = self.client.post('/api/projects', json={'name': 'Project Backup Test', 'team_ids': [team_id]})
        proj_name = p_res.get_json().get('project', p_res.get_json())['name']

        task_res = self.client.post('/api/tasks', json={
            'task': 'משימה לגיבוי',
            'project': proj_name,
            'team_id': team_id,
            'status': 'status-inprogress',
            'priority': 'high',
            'notes': 'הערת גיבוי סודית'
        })
        task_id = task_res.get_json()['id']

        # Add subtask and comment
        st_res = self.client.post(f'/api/tasks/{task_id}/subtasks', json={'title': 'תת-משימה לגיבוי'})
        st_data = st_res.get_json()
        st_id = st_data.get('subtask', st_data)['id']

        c_res = self.client.post(f'/api/tasks/{task_id}/comments', json={
            'content': 'תגובת גיבוי חשובה',
            'author_name': 'בודק גיבוי'
        })

        # Export backup
        backup_res = self.client.get('/api/backup/all')
        self.assertEqual(backup_res.status_code, 200)
        backup_data = json.loads(backup_res.data.decode('utf-8'))

        self.assertIn('data', backup_data)
        tables = backup_data['data']
        self.assertIn('tasks', tables)
        self.assertIn('projects', tables)
        self.assertIn('teams', tables)

        # Clear/delete task
        self.client.delete(f'/api/tasks/{task_id}')
        get_res = self.client.get(f'/api/tasks/{task_id}')
        self.assertEqual(get_res.status_code, 404)

        # Restore from backup
        restore_res = self.client.post('/api/restore/all', data={
            'file': (io.BytesIO(backup_res.data), 'backup_all.json')
        }, content_type='multipart/form-data')
        self.assertEqual(restore_res.status_code, 200)
        restore_result = restore_res.get_json()
        self.assertTrue(restore_result.get('success', True))

        # Verify task is restored
        restored_task_res = self.client.get(f'/api/tasks/{task_id}')
        self.assertEqual(restored_task_res.status_code, 200)
        self.assertEqual(restored_task_res.get_json()['task'], 'משימה לגיבוי')

    # -------------------------------------------------------------
    # 8. Special Days & Avatars
    # -------------------------------------------------------------
    def test_special_days_and_avatars(self):
        """Test special days CRUD and avatar endpoints"""
        # Avatars list
        res = self.client.get('/api/avatars')
        self.assertEqual(res.status_code, 200)
        avatar_data = res.get_json()
        self.assertTrue('avatars' in avatar_data or isinstance(avatar_data, list))

        # Special days create
        res = self.client.post('/api/special-days', json={
            'name': 'יום עיון צוותי',
            'date': '2026-11-15',
            'type': 'holiday'
        })
        self.assertIn(res.status_code, (200, 201))
        sd_id = res.get_json()['id']

        # List special days
        res = self.client.get('/api/special-days')
        self.assertEqual(res.status_code, 200)
        days = res.get_json()
        self.assertTrue(any(d['id'] == sd_id for d in days))

        # Update special day (PUT)
        res = self.client.put(f'/api/special-days/{sd_id}', json={
            'name': 'יום עיון צוותי מעודכן',
            'type': 'company_event',
            'color': '#4CAF50'
        })
        self.assertEqual(res.status_code, 200)
        updated_sd = res.get_json().get('special_day', res.get_json())
        self.assertEqual(updated_sd['name'], 'יום עיון צוותי מעודכן')
        self.assertEqual(updated_sd['type'], 'company_event')
        self.assertEqual(updated_sd['color'], '#4CAF50')

        # Delete special day
        res = self.client.delete(f'/api/special-days/{sd_id}')
        self.assertEqual(res.status_code, 200)

    # -------------------------------------------------------------
    # 9. Local Database Backups, Fast Restore & 14-Version Retention
    # -------------------------------------------------------------
    def test_database_version_history_and_fast_restore(self):
        """Test daily/manual database backups, fast restore, download, and 14-version retention policy"""
        # 1. Test Backup Now endpoint
        res = self.client.post('/api/backups/now', json={'type': 'manual'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('success'))
        self.assertIn('backup', data)
        first_backup = data['backup']
        fname = first_backup['filename']
        self.assertTrue(fname.endswith('.db'))
        self.assertIn('tasks_manual_', fname)

        # 2. Test List Backups
        list_res = self.client.get('/api/backups')
        self.assertEqual(list_res.status_code, 200)
        list_data = list_res.get_json()
        self.assertTrue(list_data.get('success'))
        self.assertEqual(list_data.get('retention_limit'), 14)
        self.assertEqual(list_data.get('auto_backup_time'), '23:00')
        self.assertTrue(any(b['filename'] == fname for b in list_data.get('backups', [])))

        # 3. Test Download Backup
        dl_res = self.client.get(f'/api/backups/{fname}/download')
        self.assertEqual(dl_res.status_code, 200)
        self.assertIn('attachment;', dl_res.headers.get('Content-Disposition', ''))
        self.assertTrue(len(dl_res.data) > 0)
        dl_res.close()

        # 4. Test Fast Restore Journey
        # Create a team and project first
        team_res = self.client.post('/api/teams', json={'name_en': 'backuptm', 'name_he': 'צוות גיבוי'})
        t_id = team_res.get_json().get('team', team_res.get_json())['id']
        proj_res = self.client.post('/api/projects', json={'name': 'Fast Restore Project', 'team_ids': [t_id]})
        p_name = proj_res.get_json().get('project', proj_res.get_json())['name']

        token_name = f"FastRestoreTask_{int(time.time())}"
        task_res = self.client.post('/api/tasks', json={'task': token_name, 'project': p_name, 'team_id': t_id})
        self.assertEqual(task_res.status_code, 200)
        task_id = task_res.get_json()['id']

        # Take snapshot containing this task
        snap_res = self.client.post('/api/backups/now', json={'type': 'manual'})
        self.assertEqual(snap_res.status_code, 200)
        snap_filename = snap_res.get_json()['backup']['filename']

        # Delete task (State B)
        del_task = self.client.delete(f'/api/tasks/{task_id}')
        self.assertEqual(del_task.status_code, 200)
        chk_res = self.client.get(f'/api/tasks/{task_id}')
        self.assertEqual(chk_res.status_code, 404)

        # Fast Restore from snapshot
        restore_res = self.client.post(f'/api/backups/{snap_filename}/restore')
        self.assertEqual(restore_res.status_code, 200)
        self.assertTrue(restore_res.get_json().get('success'))

        # Verify task is restored (State A restored!)
        after_restore = self.client.get(f'/api/tasks/{task_id}')
        self.assertEqual(after_restore.status_code, 200)
        self.assertEqual(after_restore.get_json()['task'], token_name)

        # 5. Test 14-version retention limit
        for _ in range(16):
            self.client.post('/api/backups/now', json={'type': 'manual'})

        final_list = self.client.get('/api/backups').get_json()
        self.assertLessEqual(len(final_list.get('backups', [])), 14)

        # 6. Test Security: Reject path traversal
        bad_res = self.client.get('/api/backups/..%2f..%2ftasks.db/download')
        self.assertIn(bad_res.status_code, (400, 404))

if __name__ == '__main__':
    unittest.main()
