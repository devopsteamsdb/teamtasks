import io
import json
import unittest
from datetime import date
from bs4 import BeautifulSoup

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, Team, TeamMember, Project, Task
from ai_context import build_system_context
import ai_tools
import mcp_server


class TestProjectLeaders(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import shutil
        app.config['TESTING'] = True
        cls.client = app.test_client()
        cls.db_path = os.path.join(app.instance_path, 'tasks.db')
        cls.backup_path = os.path.join(app.instance_path, 'tasks.db.leaders_qa_bak')
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
        with app.app_context():
            db.create_all()

    def setUp(self):
        with app.app_context():
            db.drop_all()
            db.create_all()
            self.team1 = Team(name_en='devops', name_he='דבאופס')
            self.team2 = Team(name_en='dev', name_he='פיתוח')
            db.session.add_all([self.team1, self.team2])
            db.session.flush()

            self.m_alice = TeamMember(name_en='alice', name_he='אליס', team_id=self.team1.id, teams=[self.team1])
            self.m_bob = TeamMember(name_en='bob', name_he='בוב', team_id=self.team1.id, teams=[self.team1])
            self.m_charlie = TeamMember(name_en='charlie', name_he='צ׳רלי', team_id=self.team2.id, teams=[self.team2])
            db.session.add_all([self.m_alice, self.m_bob, self.m_charlie])
            db.session.commit()

            self.t1_id = self.team1.id
            self.t2_id = self.team2.id
            self.alice_id = self.m_alice.id
            self.bob_id = self.m_bob.id
            self.charlie_id = self.m_charlie.id

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()
            db.create_all()

    def test_project_crud_with_multiple_optional_leaders(self):
        # Create project with no leaders (optional)
        res = self.client.post('/api/projects', json={
            'name': 'No Leader Project',
            'team_ids': [self.t1_id]
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['project']['leader_ids'], [])
        self.assertEqual(data['project']['leaders'], [])

        # Create project with multiple leaders (including member from another team)
        res2 = self.client.post('/api/projects', json={
            'name': 'Led Project',
            'team_ids': [self.t1_id],
            'leader_ids': [self.alice_id, self.charlie_id]
        })
        self.assertEqual(res2.status_code, 200)
        p2 = res2.get_json()['project']
        self.assertEqual(set(p2['leader_ids']), {self.alice_id, self.charlie_id})
        self.assertEqual(set(p2['leader_names']), {'alice', 'charlie'})

        # Update leaders to single leader
        res3 = self.client.put(f"/api/projects/{p2['id']}", json={
            'leader_ids': [self.bob_id]
        })
        self.assertEqual(res3.status_code, 200)
        p2_updated = res3.get_json()['project']
        self.assertEqual(p2_updated['leader_ids'], [self.bob_id])

        # Clear leaders
        res4 = self.client.put(f"/api/projects/{p2['id']}", json={
            'leader_ids': []
        })
        self.assertEqual(res4.status_code, 200)
        self.assertEqual(res4.get_json()['project']['leader_ids'], [])

    def test_index_dom_renders_leader_badges_and_data_attributes(self):
        with app.app_context():
            t1 = db.session.get(Team, self.t1_id)
            alice = db.session.get(TeamMember, self.alice_id)
            charlie = db.session.get(TeamMember, self.charlie_id)
            proj = Project(name='Alpha', teams=[t1], leaders=[alice, charlie])
            db.session.add(proj)
            db.session.flush()
            task = Task(
                project_id=proj.id,
                project='Alpha',
                task='Unassigned To Leader Task',
                members='bob',
                status='status-inprogress',
                team_id=self.t1_id
            )
            db.session.add(task)
            db.session.commit()

        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        soup = BeautifulSoup(res.data.decode('utf-8'), 'html.parser')

        # Project modal has leaders multi-select
        self.assertIsNotNone(soup.select_one('#projectModal #projectLeadersSelect'))

        # Project card has leader badges next to team tag and data attributes
        card = soup.select_one('.project-card[data-project-name="Alpha"]')
        self.assertIsNotNone(card)
        self.assertIn('alice', card.get('data-leader-names', ''))
        self.assertIn('charlie', card.get('data-leader-names', ''))
        leader_badges = card.select('.project-badges .project-leader-badge')
        self.assertEqual(len(leader_badges), 2)
        badge_texts = [b.get_text(strip=True) for b in leader_badges]
        self.assertTrue(any('אליס' in txt for txt in badge_texts))
        self.assertTrue(any('צ׳רלי' in txt for txt in badge_texts))

        # Grid task item and Kanban card carry data-project-leaders
        grid_task = card.select_one('.task-item')
        self.assertIn('alice', grid_task.get('data-project-leaders', ''))
        kanban_card = soup.select_one('.kanban-card[data-project="Alpha"]')
        self.assertIsNotNone(kanban_card)
        self.assertIn('alice', kanban_card.get('data-project-leaders', ''))

    def test_member_filtering_across_index_api_and_print_pages(self):
        with app.app_context():
            t1 = db.session.get(Team, self.t1_id)
            alice = db.session.get(TeamMember, self.alice_id)
            proj_led = Project(name='Alice Led Project', teams=[t1], leaders=[alice])
            proj_other = Project(name='Other Project', teams=[t1])
            db.session.add_all([proj_led, proj_other])
            db.session.flush()

            # Task in Alice's led project, assigned ONLY to Bob
            t_led = Task(
                project_id=proj_led.id,
                project='Alice Led Project',
                task='Bob Task In Alice Project',
                members='bob',
                status='status-inprogress',
                team_id=self.t1_id,
                start_date=date.today(),
                end_date=date.today()
            )
            # Task in another project, assigned ONLY to Bob
            t_other = Task(
                project_id=proj_other.id,
                project='Other Project',
                task='Bob Task Elsewhere',
                members='bob',
                status='status-inprogress',
                team_id=self.t1_id,
                start_date=date.today(),
                end_date=date.today()
            )
            db.session.add_all([t_led, t_other])
            db.session.commit()

        # 1. /api/tasks?member=alice
        api_res = self.client.get('/api/tasks?member=alice')
        self.assertEqual(api_res.status_code, 200)
        task_names = [t['task'] for t in api_res.get_json()]
        self.assertIn('Bob Task In Alice Project', task_names)
        self.assertNotIn('Bob Task Elsewhere', task_names)

        # 2. /?member=alice
        idx_res = self.client.get('/?member=alice')
        self.assertEqual(idx_res.status_code, 200)
        idx_html = idx_res.data.decode('utf-8')
        self.assertIn('Bob Task In Alice Project', idx_html)
        self.assertNotIn('Bob Task Elsewhere', idx_html)

        # 3. /print?member=alice (table view) + #memberFilter dropdown exists
        pr_res = self.client.get('/print?member=alice')
        self.assertEqual(pr_res.status_code, 200)
        pr_html = pr_res.data.decode('utf-8')
        self.assertIn('Bob Task In Alice Project', pr_html)
        self.assertNotIn('Bob Task Elsewhere', pr_html)
        soup = BeautifulSoup(pr_html, 'html.parser')
        member_select = soup.select_one('select#memberFilter')
        self.assertIsNotNone(member_select)
        selected_opt = member_select.select_one('option[selected]')
        self.assertIsNotNone(selected_opt)
        self.assertEqual(selected_opt.get('value'), 'alice')

        # 4. /print?view=gantt&member=alice
        prg_res = self.client.get('/print?view=gantt&member=alice')
        self.assertEqual(prg_res.status_code, 200)
        prg_html = prg_res.data.decode('utf-8')
        self.assertIn('Bob Task In Alice Project', prg_html)
        self.assertNotIn('Bob Task Elsewhere', prg_html)

    def test_backup_and_restore_preserves_project_leaders(self):
        with app.app_context():
            t1 = db.session.get(Team, self.t1_id)
            alice = db.session.get(TeamMember, self.alice_id)
            bob = db.session.get(TeamMember, self.bob_id)
            proj = Project(name='Backup Led Project', teams=[t1], leaders=[alice, bob])
            db.session.add(proj)
            db.session.commit()

        # Full backup
        b_res = self.client.get('/api/backup/all')
        self.assertEqual(b_res.status_code, 200)
        b_json = b_res.get_json()
        self.assertIn('project_leaders', b_json['data'])
        self.assertEqual(len(b_json['data']['project_leaders']), 2)

        # Full restore
        payload_bytes = json.dumps(b_json).encode('utf-8')
        r_res = self.client.post(
            '/api/restore/all',
            data={'file': (io.BytesIO(payload_bytes), 'backup_all.json')},
            content_type='multipart/form-data'
        )
        self.assertEqual(r_res.status_code, 200)
        r_json = r_res.get_json()
        self.assertTrue(r_json['success'])
        self.assertEqual(r_json['counts'].get('project_leaders'), 2)

        with app.app_context():
            restored = Project.query.filter_by(name='Backup Led Project').first()
            self.assertIsNotNone(restored)
            self.assertEqual({m.name_en for m in restored.leaders}, {'alice', 'bob'})

    def test_ai_and_mcp_leader_awareness(self):
        with app.app_context():
            # AI create_project with leader by Hebrew name
            res = ai_tools._action_create_project({
                'name': 'AI Led Project',
                'teams': ['דבאופס'],
                'leaders': ['אליס']
            })
            self.assertEqual(res['status'], 'success')
            proj = Project.query.filter_by(name='AI Led Project').first()
            self.assertEqual([m.name_en for m in proj.leaders], ['alice'])

            # Add task assigned to Bob in AI Led Project
            t = Task(project_id=proj.id, project=proj.name, task='Bob Work', members='bob', status='status-inprogress', team_id=self.t1_id)
            db.session.add(t)
            db.session.commit()

            # build_system_context includes leaders
            ctx = build_system_context()
            p_ctx = next(p for p in ctx['projects'] if p['name'] == 'AI Led Project')
            self.assertEqual([l['name_en'] for l in p_ctx['leaders']], ['alice'])

            # get_member_tasks_query_info includes Bob Work for Alice (leader)
            info = ai_tools.get_member_tasks_query_info('מה המשימות של אליס?', ctx=ctx)
            self.assertIsNotNone(info)
            _, matching_tasks, _, _, _ = info
            self.assertTrue(any(mt['task'] == 'Bob Work' for mt in matching_tasks))

            # MCP list_tasks(member='alice') includes Bob Work
            mcp_tasks = mcp_server.execute_mcp_tool('list_tasks', {'member': 'alice'})
            self.assertTrue(mcp_tasks['success'])
            self.assertTrue(any(mt['task'] == 'Bob Work' for mt in mcp_tasks['tasks']))

            # MCP list_projects(leader='alice') returns AI Led Project
            mcp_projs = mcp_server.execute_mcp_tool('list_projects', {'leader': 'alice'})
            self.assertTrue(mcp_projs['success'])
            self.assertEqual([p['name'] for p in mcp_projs['projects']], ['AI Led Project'])

            # MCP update_project add_leaders & remove_leaders
            upd = mcp_server.execute_mcp_tool('update_project', {'name': 'AI Led Project', 'add_leaders': ['בוב']})
            self.assertTrue(upd['success'])
            self.assertEqual(set(upd['project']['leader_names']), {'alice', 'bob'})

            upd2 = mcp_server.execute_mcp_tool('update_project', {'name': 'AI Led Project', 'remove_leaders': ['alice']})
            self.assertTrue(upd2['success'])
            self.assertEqual(upd2['project']['leader_names'], ['bob'])


if __name__ == '__main__':
    unittest.main()
