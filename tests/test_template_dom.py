"""
QA Automated Test Suite - Template DOM Structure & View Routing
Verifies DOM element presence, wide modals, navbar tabs, AI inclusion, and route redirects
"""
import unittest
import os
import sys
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models import db, Project, Team, Task

class TestTemplateDom(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import shutil
        app.config['TESTING'] = True
        cls.client = app.test_client()
        cls.db_path = os.path.join(app.instance_path, 'tasks.db')
        cls.backup_path = os.path.join(app.instance_path, 'tasks.db.dom_qa_bak')
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
            # Seed minimal project and team safely
            t = Team.query.filter_by(name_en='devops').first()
            if not t:
                t = Team(name_en='devops', name_he='דבאופס')
                db.session.add(t)
                db.session.flush()
            p = Project.query.filter_by(name='Default Project').first()
            if not p:
                p = Project(name='Default Project', teams=[t])
                db.session.add(p)
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    # -------------------------------------------------------------
    # 1. Dashboard View & Navbar Navigation Tabs
    # -------------------------------------------------------------
    def test_dashboard_nav_tabs_and_view_containers(self):
        """Test navbar has the 3 main view tabs (Projects, Kanban, Gantt) and dashboard containers exist"""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')

        # Check navbar-nav-tabs
        nav_tabs = soup.select('.navbar-nav-tabs')
        self.assertTrue(len(nav_tabs) > 0, "navbar-nav-tabs should be present in navbar")

        links = soup.select('.navbar-nav-tabs a.navbar-brand-link')
        self.assertEqual(len(links), 3, "Should have 3 view links in navbar tabs")

        hrefs = [a.get('href') for a in links]
        self.assertTrue(any('view=grid' in h for h in hrefs), "Should have Projects (grid) link")
        self.assertTrue(any('view=kanban' in h for h in hrefs), "Should have Kanban link")
        self.assertTrue(any('view=gantt' in h for h in hrefs), "Should have Gantt link")

        # Verify old dashboard-view-toggle is NOT present
        old_toggle = soup.select('.dashboard-view-toggle')
        self.assertEqual(len(old_toggle), 0, "Old dashboard-view-toggle should be removed")

        # Check view containers exist
        self.assertIsNotNone(soup.find(id='viewContainerGrid'), "viewContainerGrid container should exist")
        self.assertIsNotNone(soup.find(id='viewContainerKanban'), "viewContainerKanban container should exist")
        self.assertIsNotNone(soup.find(id='viewContainerGantt'), "viewContainerGantt container should exist")

        # Check projects empty state in main view
        empty_state = soup.find(id='projectsEmptyState')
        self.assertIsNotNone(empty_state, "#projectsEmptyState should exist in main view")
        self.assertIn('gantt-empty-state', empty_state.get('class', []))
        self.assertIn('אין פרויקטים להצגה בסינון הנוכחי', empty_state.text)
        self.assertIsNotNone(empty_state.find('svg'))

    # -------------------------------------------------------------
    # 2. Wide Create Task Modal Structure
    # -------------------------------------------------------------
    def test_create_task_modal_structure(self):
        """Test #createTaskModal has wide 2-column layout and all input controls"""
        res = self.client.get('/')
        html = res.data.decode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')

        modal = soup.find(id='createTaskModal')
        self.assertIsNotNone(modal, "#createTaskModal should exist")

        modal_content = modal.select_one('.modal-content.modal-content-wide')
        self.assertIsNotNone(modal_content, "createTaskModal should have .modal-content-wide class")

        grid = modal.select_one('.task-modal-layout-grid')
        self.assertIsNotNone(grid, "createTaskModal should have 2-column grid layout")

        # Check inputs
        self.assertIsNotNone(modal.find(id='createTaskNameInput'), "createTaskNameInput should exist")
        self.assertIsNotNone(modal.find(id='createTaskNotes'), "createTaskNotes should exist")
        self.assertEqual(modal.find(id='createTaskNotes').get('rows'), '4', "createTaskNotes should have 4 rows by default")
        self.assertIsNotNone(modal.find(id='createTaskProject'), "createTaskProject should exist")
        self.assertIsNotNone(modal.find(id='createTaskTeam'), "createTaskTeam should exist")
        self.assertIsNotNone(modal.find(id='createTaskStatus'), "createTaskStatus should exist")
        self.assertIsNotNone(modal.find(id='createTaskPriority'), "createTaskPriority should exist")
        self.assertIsNotNone(modal.find(id='createTaskStartDate'), "createTaskStartDate should exist")
        self.assertIsNotNone(modal.find(id='createTaskEndDate'), "createTaskEndDate should exist")
        self.assertIsNotNone(modal.find(id='createSaveBtn'), "createSaveBtn should exist")
        self.assertIsNotNone(modal.select_one('.close-modal-create'), "close-modal-create button should exist")
        self.assertIsNotNone(modal.select_one('.members-select.side-members-select'), "createTaskModal should have .members-select.side-members-select")

    # -------------------------------------------------------------
    # 3. Wide Edit Task Modal & Subtasks/Comments Sections
    # -------------------------------------------------------------
    def test_edit_task_modal_structure(self):
        """Test #taskModal has wide 2-column layout, subtasks checklist, comments thread, and action controls"""
        res = self.client.get('/')
        html = res.data.decode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')

        modal = soup.find(id='taskModal')
        self.assertIsNotNone(modal, "#taskModal should exist")

        modal_content = modal.select_one('.modal-content.modal-content-wide')
        self.assertIsNotNone(modal_content, "taskModal should have .modal-content-wide class")

        grid = modal.select_one('.task-modal-layout-grid')
        self.assertIsNotNone(grid, "taskModal should have .task-modal-layout-grid")

        # Primary column fields
        self.assertIsNotNone(modal.find(id='taskNameInput'), "taskNameInput should exist")
        self.assertIsNotNone(modal.find(id='taskNotes'), "taskNotes should exist")
        self.assertEqual(modal.find(id='taskNotes').get('rows'), '4', "taskNotes should have 4 rows by default")

        # Subtasks section
        subtasks_sec = modal.find(id='taskSubtasksSection')
        self.assertIsNotNone(subtasks_sec, "taskSubtasksSection should exist")
        self.assertIsNotNone(modal.find(id='subtaskProgressText'), "subtaskProgressText should exist")
        self.assertIsNotNone(modal.find(id='subtaskProgressBar'), "subtaskProgressBar should exist")
        self.assertIsNotNone(modal.find(id='subtasksList'), "subtasksList should exist")
        self.assertIsNotNone(modal.find(id='newSubtaskInput'), "newSubtaskInput should exist")
        self.assertIsNotNone(modal.find(id='addSubtaskBtn'), "addSubtaskBtn should exist")

        # Comments section
        comments_sec = modal.find(id='taskCommentsSection')
        self.assertIsNotNone(comments_sec, "taskCommentsSection should exist")
        self.assertIsNotNone(modal.find(id='commentCounter'), "commentCounter should exist")
        self.assertIsNotNone(modal.find(id='commentsList'), "commentsList should exist")
        self.assertIsNotNone(modal.find(id='commentAuthorSelect'), "commentAuthorSelect should exist")
        self.assertIsNotNone(modal.find(id='newCommentInput'), "newCommentInput should exist")
        self.assertIsNotNone(modal.find(id='addCommentBtn'), "addCommentBtn should exist")

        # Secondary column card box & actions
        self.assertIsNotNone(modal.select_one('.task-modal-card-box'), "task-modal-card-box should exist")
        self.assertIsNotNone(modal.find(id='taskStatus'), "taskStatus should exist")
        self.assertIsNotNone(modal.find(id='taskPriority'), "taskPriority should exist")
        self.assertIsNotNone(modal.find(id='taskProject'), "taskProject should exist")
        self.assertIsNotNone(modal.find(id='taskTeam'), "taskTeam should exist")
        self.assertIsNotNone(modal.find(id='taskStartDate'), "taskStartDate should exist")
        self.assertIsNotNone(modal.find(id='taskEndDate'), "taskEndDate should exist")
        self.assertIsNotNone(modal.select_one('.members-select'), "members-select should exist")

        # Sidebar action buttons
        self.assertIsNotNone(modal.find(id='saveBtn'), "saveBtn should exist")
        self.assertIsNotNone(modal.find(id='archiveBtn'), "archiveBtn should exist")
        self.assertIsNotNone(modal.find(id='deleteBtn'), "deleteBtn should exist")
        self.assertIsNotNone(modal.select_one('.close-modal'), "close-modal button should exist")

    # -------------------------------------------------------------
    # 4. Old /calendar Deprecation & Redirect Check
    # -------------------------------------------------------------
    def test_calendar_route_redirects_to_gantt(self):
        """Test navigating to old /calendar redirects with 302 to /?view=gantt"""
        res = self.client.get('/calendar')
        self.assertIn(res.status_code, (301, 302), "Old /calendar should return HTTP redirect")
        self.assertTrue('view=gantt' in res.headers.get('Location', ''), "Redirect destination should be /?view=gantt")

    # -------------------------------------------------------------
    # 5. Admin Page Structure & Task Modal Integration
    # -------------------------------------------------------------
    def test_admin_page_task_modal_inclusion(self):
        """Test /admin includes #taskModal for standalone AI assistant task editing, flatpickr, and tabs"""
        res = self.client.get('/admin')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')

        # Check navigation tabs
        links = soup.select('.navbar-nav-tabs a.navbar-brand-link')
        self.assertEqual(len(links), 3, "Admin navbar should have 3 view navigation links")

        # Check taskModal inclusion in admin
        task_modal = soup.find(id='taskModal')
        self.assertIsNotNone(task_modal, "#taskModal should be included in admin.html for AI assistant task opening")
        self.assertIsNotNone(task_modal.find(id='taskNameInput'))
        self.assertIsNotNone(task_modal.find(id='saveBtn'))

        # Check flatpickr scripts included in admin
        scripts = [s.get('src', '') for s in soup.find_all('script')]
        self.assertTrue(any('flatpickr' in s for s in scripts), "Admin should include flatpickr scripts")

        # Check AI Assistant included
        self.assertIsNotNone(soup.find(id='aiFabBtn'), "aiFabBtn should exist in admin.html")
        self.assertIsNotNone(soup.find(id='aiPanel'), "aiPanel should exist in admin.html")

    # -------------------------------------------------------------
    # 6. Printable Page Filters
    # -------------------------------------------------------------
    def test_printable_view_structure(self):
        """Test /printable view renders correctly with required filters"""
        res = self.client.get('/printable')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')

        # Filter controls
        self.assertIsNotNone(soup.find(id='projectFilter'), "projectFilter should exist")
        self.assertIsNotNone(soup.find(id='teamFilter'), "teamFilter should exist")
        self.assertIsNotNone(soup.find(id='statusFilter'), "statusFilter should exist")
        self.assertIsNotNone(soup.find(id='priorityFilter'), "priorityFilter should exist")

    # -------------------------------------------------------------
    # 7. Task Name Visibility & Population in Kanban & Grid
    # -------------------------------------------------------------
    def test_task_names_visible_and_populated_in_kanban_and_grid(self):
        """Verify task names are non-empty and accurately rendered in both project grid and Kanban cards"""
        # Create a task with a distinct name
        task_title = "משימת בדיקה עבור שמות בממשק"
        with app.app_context():
            import datetime
            from models import Subtask, TaskComment
            p = Project.query.filter_by(name='Default Project').first()
            s_date = datetime.date(2026, 10, 25)
            e_date = datetime.date(2026, 10, 26)
            t = Task(project_id=p.id, project=p.name, task=task_title, status='status-inprogress', priority='high', start_date=s_date, end_date=e_date, notes='הערות לבדיקה')
            db.session.add(t)
            db.session.flush()
            sub = Subtask(task_id=t.id, title="תת משימה לבדיקה", is_completed=False)
            com = TaskComment(task_id=t.id, content="הערת בדיקה", author_name="admin")
            db.session.add_all([sub, com])
            db.session.commit()

        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')

        # Check kanban cards have data-task-name and non-empty .task-name
        kanban_cards = soup.select('.kanban-card')
        self.assertTrue(len(kanban_cards) > 0, "Kanban cards should be rendered")
        matching_kanban = [c for c in kanban_cards if task_title in c.get('data-task-name', '')]
        self.assertTrue(len(matching_kanban) > 0, f"Task '{task_title}' should be found in kanban cards data-task-name")

        for card in matching_kanban:
            name_el = card.select_one('.task-name')
            self.assertIsNotNone(name_el, "Kanban card must have .task-name element")
            self.assertTrue(len(name_el.text.strip()) > 0, "Kanban card .task-name must NOT be empty")
            # Verify priority tag is a circle icon without text
            prio_tag = card.select_one('.priority-tag.priority-high')
            self.assertIsNotNone(prio_tag, "Kanban card must have .priority-tag.priority-high")
            self.assertEqual(prio_tag.text.strip(), "", "Priority tag must be a circle icon with no inner text")
            self.assertIn("עדיפות גבוהה", prio_tag.get('title', ''))
            # Verify kanban date badge displays date range
            date_badge = card.select_one('.kanban-date-badge')
            self.assertIsNotNone(date_badge, "Kanban card must have .kanban-date-badge")
            self.assertIn('25/10 - 26/10', date_badge.text, "Date badge must display '25/10 - 26/10' date range")

        # Check project grid items
        grid_items = soup.select('.projects-grid .task-item')
        matching_grid = [item for item in grid_items if task_title in item.get('data-task-name', '')]
        self.assertTrue(len(matching_grid) > 0, f"Task '{task_title}' should be found in projects grid")
        for item in matching_grid:
            name_el = item.select_one('.task-name')
            self.assertIsNotNone(name_el, "Grid task item must have .task-name element")
            self.assertTrue(len(name_el.text.strip()) > 0, "Grid task item .task-name must NOT be empty")
            # Badges must be in .task-meta, NOT in .task-info
            task_info = item.select_one('.task-info')
            task_meta = item.select_one('.task-meta')
            self.assertIsNotNone(task_info, "task-info should exist")
            self.assertIsNotNone(task_meta, "task-meta should exist")
            self.assertIsNone(task_info.select_one('.subtask-badge'), "subtask-badge must NOT be inside .task-info")
            self.assertIsNone(task_info.select_one('.comment-badge'), "comment-badge must NOT be inside .task-info")
            self.assertIsNone(task_info.select_one('.note-icon'), "note-icon must NOT be inside .task-info")
            self.assertIsNone(task_meta.select_one('.note-badge'), "note-badge must NOT be on tasks page")
            self.assertEqual(item.get('title'), 'הערות לבדיקה', "task-item must have title tooltip displaying only notes on hover")
            self.assertIsNotNone(task_meta.select_one('.task-meta-top'), "task-meta-top must be inside .task-meta")
            # Verify 2 lines: task-meta-top (status + avatars)
            status_el = task_meta.select_one('.status-badge')
            avatars_el = task_meta.select_one('.avatar-group')
            self.assertIsNotNone(status_el, "status-badge must be in task-meta")
            self.assertIsNotNone(avatars_el, "avatar-group must be in task-meta")

    # 8. Kanban View Add Buttons Removed
    def test_kanban_view_add_buttons_removed(self):
        """Verify kanban column headers do not contain add-task buttons and addProjectBtn is hidden on kanban view"""
        res_grid = self.client.get('/')
        soup_grid = BeautifulSoup(res_grid.data.decode('utf-8'), 'html.parser')
        
        # Verify no kanban-col-add-btn in kanban columns
        kanban_add_btns = soup_grid.select('.kanban-col-add-btn')
        self.assertEqual(len(kanban_add_btns), 0, "There should be no .kanban-col-add-btn buttons in kanban columns")

        # Verify addProjectBtn exists and is visible by default
        add_proj_grid = soup_grid.find(id='addProjectBtn')
        self.assertIsNotNone(add_proj_grid, "addProjectBtn should exist in index")
        self.assertNotIn("display: none", add_proj_grid.get('style', ''), "addProjectBtn should be visible by default on grid view")

        # Test ?view=kanban render
        res_kanban = self.client.get('/?view=kanban')
        soup_kanban = BeautifulSoup(res_kanban.data.decode('utf-8'), 'html.parser')
        add_proj_kanban = soup_kanban.find(id='addProjectBtn')
        self.assertIsNotNone(add_proj_kanban, "addProjectBtn should exist in kanban view render")
        self.assertIn("display: none", add_proj_kanban.get('style', ''), "addProjectBtn should have display: none on ?view=kanban")

    # 9. Printable Gantt View
    def test_printable_gantt_view(self):
        """Verify printable Gantt view at /print?view=gantt and /printable?view=gantt renders chart and controls"""
        import datetime
        # Create a test task with dates
        with app.app_context():
            p = Project.query.filter_by(name='Default Project').first()
            t = Task(
                task="Printable Gantt Test Task",
                project="Default Project",
                project_id=p.id if p else None,
                status="status-inprogress",
                priority="high",
                start_date=datetime.date(2026, 10, 25),
                end_date=datetime.date(2026, 10, 28)
            )
            db.session.add(t)
            db.session.commit()

        # Test default printable view has switcher and table
        res_default = self.client.get('/print')
        self.assertEqual(res_default.status_code, 200)
        soup_default = BeautifulSoup(res_default.data.decode('utf-8'), 'html.parser')
        self.assertIsNotNone(soup_default.select_one('.print-view-toggle'), "View switcher should exist in /print")
        self.assertIsNotNone(soup_default.select_one('.print-projects'), "Default print view should show table .print-projects")

        # Test ?view=gantt printable view
        res_gantt = self.client.get('/print?view=gantt')
        self.assertEqual(res_gantt.status_code, 200)
        soup_gantt = BeautifulSoup(res_gantt.data.decode('utf-8'), 'html.parser')
        self.assertIsNotNone(soup_gantt.select_one('.print-gantt-view'), "Printable Gantt view should render .print-gantt-view")
        self.assertIsNotNone(soup_gantt.select_one('.print-gantt-nav'), "Printable Gantt view should render navigation controls")
        self.assertIsNotNone(soup_gantt.select_one('.print-period-title'), "Printable Gantt should display period title")

        # Verify timeline day cells and bars
        day_cells = soup_gantt.select('.print-gantt-day-cell')
        self.assertEqual(len(day_cells), 28, "Printable Gantt should render 28 day cells")

        gantt_bars = soup_gantt.select('.print-gantt-bar')
        self.assertTrue(len(gantt_bars) > 0, "Scheduled tasks should render .print-gantt-bar")

        # Verify filters remain accessible
        self.assertIsNotNone(soup_gantt.find(id='projectFilter'), "projectFilter should exist in Gantt print view")
        self.assertIsNotNone(soup_gantt.find(id='teamFilter'), "teamFilter should exist in Gantt print view")
        self.assertIsNotNone(soup_gantt.find(id='statusFilter'), "statusFilter should exist in Gantt print view")
        self.assertIsNotNone(soup_gantt.find(id='priorityFilter'), "priorityFilter should exist in Gantt print view")

        # Verify print action button
        print_btn = soup_gantt.find(id='printBtn')
        self.assertIsNotNone(print_btn, "Print action button should exist")
        self.assertNotIn('🖨️', print_btn.text, "Print button must not contain emoji")

    # -------------------------------------------------------------
    # 7. Special Days Admin Section & Gantt Legend Integration
    # -------------------------------------------------------------
    def test_special_days_admin_and_gantt_structure(self):
        """Test Admin page has special days management section & modal, and Gantt legend has special days"""
        # Admin page verification
        res_admin = self.client.get('/admin')
        self.assertEqual(res_admin.status_code, 200)
        soup_admin = BeautifulSoup(res_admin.data.decode('utf-8'), 'html.parser')

        # Check navigation item
        nav_item = soup_admin.select_one('.settings-nav button[data-section="special-days"]')
        self.assertIsNotNone(nav_item, "Admin sidebar must contain special-days navigation button")
        self.assertIn('ימים מיוחדים', nav_item.text)

        # Check section
        section = soup_admin.find(id='section-special-days')
        self.assertIsNotNone(section, "#section-special-days must exist in admin page")
        self.assertIsNotNone(section.find(id='addSpecialDayBtn'), "#addSpecialDayBtn must exist")
        self.assertIsNotNone(section.find(id='specialDaysContainer'), "#specialDaysContainer must exist")

        # Check modal
        modal = soup_admin.find(id='specialDayModal')
        self.assertIsNotNone(modal, "#specialDayModal must exist")
        self.assertIsNotNone(modal.find(id='specialDayDateInput'), "#specialDayDateInput must exist")
        self.assertIsNotNone(modal.find(id='specialDayNameInput'), "#specialDayNameInput must exist")
        self.assertIsNotNone(modal.find(id='specialDayTypeSelect'), "#specialDayTypeSelect must exist")
        self.assertIsNotNone(modal.find(id='specialDayColorPicker'), "#specialDayColorPicker must exist")
        self.assertIsNotNone(modal.find(id='saveSpecialDayBtn'), "#saveSpecialDayBtn must exist")

        # Main dashboard Gantt legend verification
        res_main = self.client.get('/?view=gantt')
        self.assertEqual(res_main.status_code, 200)
        soup_main = BeautifulSoup(res_main.data.decode('utf-8'), 'html.parser')
        legend = soup_main.select_one('.gantt-legend')
        self.assertIsNotNone(legend, ".gantt-legend must exist in Gantt view")
        special_dot = legend.select_one('.special-day-legend-dot')
        self.assertIsNotNone(special_dot, ".special-day-legend-dot must exist in Gantt legend")
        self.assertIn('יום מיוחד', legend.text)

    # -------------------------------------------------------------
    # 8. Database Version History & Backups Admin Section
    # -------------------------------------------------------------
    def test_database_backups_admin_structure(self):
        """Test Admin page contains database version history table, backup now button, and badges"""
        res = self.client.get('/admin')
        self.assertEqual(res.status_code, 200)
        soup = BeautifulSoup(res.data.decode('utf-8'), 'html.parser')

        # Check section & nav
        nav_item = soup.select_one('.settings-nav button[data-section="backup"]')
        self.assertIsNotNone(nav_item, "Sidebar must contain backup navigation button")

        section = soup.find(id='section-backup')
        self.assertIsNotNone(section, "#section-backup must exist")

        # Action buttons
        btn_now = section.find(id='btnBackupNow')
        self.assertIsNotNone(btn_now, "#btnBackupNow button must exist")
        self.assertIn('גבה עכשיו לשרת', btn_now.text)

        btn_refresh = section.find(id='btnRefreshDbBackups')
        self.assertIsNotNone(btn_refresh, "#btnRefreshDbBackups button must exist")

        # Table & badges
        tbody = section.find(id='dbBackupsTableBody')
        self.assertIsNotNone(tbody, "#dbBackupsTableBody must exist for history table")

        badge_retention = section.find(id='badgeRetentionPolicy')
        self.assertIsNotNone(badge_retention, "#badgeRetentionPolicy must exist")
        self.assertIn('14', badge_retention.text)

        badge_count = section.find(id='badgeBackupsCount')
        self.assertIsNotNone(badge_count, "#badgeBackupsCount must exist")

        # JSON cards preserved
        self.assertIsNotNone(section.find(id='downloadBackupBtn'))
        self.assertIsNotNone(section.find(id='restoreBtn'))

if __name__ == '__main__':
    unittest.main()
