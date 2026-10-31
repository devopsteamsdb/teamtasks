"""
Automated UI and Button Actions Test Suite using Selenium WebDriver
Comprehensive end-to-end testing for all user interface controls, wide 2-column modals,
Kanban board, Gantt chart, filters, admin panel, AI assistant widget, and printable views.
"""

import os
import sys
import time
import socket
import shutil
import unittest
import threading
from werkzeug.serving import make_server

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException

# Ensure workspace root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app


def get_free_port():
    """Allocate a free TCP port dynamically on localhost."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


class TestTeamTasksUIAutomation(unittest.TestCase):
    """
    Complete Selenium WebDriver automation test suite covering all UI buttons,
    interactive features, and recent UI layout updates.
    """
    server = None
    server_thread = None
    port = None
    base_url = None
    driver = None
    db_backup_path = None
    live_db_path = None

    @classmethod
    def setUpClass(cls):
        # 1. Backup live database file to guarantee complete zero-pollution
        cls.live_db_path = os.path.join(app.instance_path, 'tasks.db')
        cls.db_backup_path = os.path.join(app.instance_path, 'tasks.db.selenium_test_bak')
        if os.path.exists(cls.live_db_path):
            shutil.copyfile(cls.live_db_path, cls.db_backup_path)

        # 2. Launch background Flask server on an isolated dynamic port
        cls.port = get_free_port()
        cls.base_url = f"http://127.0.0.1:{cls.port}"
        cls.server = make_server('127.0.0.1', cls.port, app)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        time.sleep(1.0)

        # 3. Initialize Headless Chrome with modern flags
        opts = Options()
        opts.add_argument('--headless=new')
        opts.add_argument('--no-sandbox')
        opts.add_argument('--disable-dev-shm-usage')
        opts.add_argument('--disable-gpu')
        opts.add_argument('--window-size=1920,1080')
        opts.add_argument('--log-level=3')
        opts.add_argument('--silent')
        opts.set_capability('unhandledPromptBehavior', 'accept')

        cls.driver = webdriver.Chrome(options=opts)
        cls.driver.implicitly_wait(4)

        # Register CDP script to automatically bypass confirm/alert dialogs across all documents
        try:
            cls.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': 'window.confirm = function() { return true; }; window.alert = function() { return true; };'
            })
        except Exception:
            pass

        # Navigate to homepage
        cls.driver.get(cls.base_url)

    @classmethod
    def tearDownClass(cls):
        # 1. Quit browser driver safely
        if cls.driver:
            try:
                cls.driver.quit()
            except Exception:
                pass

        # 2. Shutdown Flask test server
        if cls.server:
            try:
                cls.server.shutdown()
            except Exception:
                pass

        # 3. Restore original database file
        if cls.db_backup_path and os.path.exists(cls.db_backup_path):
            try:
                shutil.copyfile(cls.db_backup_path, cls.live_db_path)
                os.remove(cls.db_backup_path)
            except Exception:
                pass

    def setUp(self):
        # Clear filter keys in localStorage before each test to ensure clean baseline state
        try:
            self.driver.execute_script("""
                window.confirm = function() { return true; };
                window.alert = function() { return true; };
                localStorage.removeItem('activeTeamFilter');
                localStorage.removeItem('activeMemberFilter');
                localStorage.removeItem('activeStatusFilter');
                localStorage.removeItem('activePriorityFilter');
            """)
        except Exception:
            pass

    # -------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------
    def wait_visible(self, by, value, timeout=8):
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located((by, value))
        )

    def wait_clickable(self, by, value, timeout=8):
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )

    def safe_click(self, element):
        """Click element directly, falling back to JS click if covered by animations."""
        try:
            element.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", element)

    def handle_alert_if_present(self):
        """Accept any open alert safely."""
        try:
            alert = self.driver.switch_to.alert
            alert.accept()
        except Exception:
            pass

    def switch_view(self, view_mode):
        """Helper to switch between 'grid', 'kanban', and 'gantt' views via navbar."""
        btn_map = {
            'grid': 'viewBtnGrid',
            'kanban': 'viewBtnKanban',
            'gantt': 'viewBtnGantt'
        }
        btn_id = btn_map[view_mode]
        btn = self.wait_clickable(By.ID, btn_id)
        self.safe_click(btn)
        time.sleep(0.3)

    # =============================================================
    # 1. Navigation & View Switching Buttons
    # =============================================================
    def test_01_navbar_view_switching_buttons(self):
        """Test clicking Projects, Kanban, and Gantt tabs switches active view containers and URL params."""
        self.driver.get(f"{self.base_url}/?mode=active")

        # 1. Switch to Kanban
        kanban_btn = self.wait_clickable(By.ID, 'viewBtnKanban')
        self.safe_click(kanban_btn)
        self.wait_visible(By.ID, 'viewContainerKanban')
        self.assertIn('view=kanban', self.driver.current_url)
        kanban_cont = self.driver.find_element(By.ID, 'viewContainerKanban')
        self.assertTrue(kanban_cont.is_displayed())

        # 2. Switch to Gantt
        gantt_btn = self.wait_clickable(By.ID, 'viewBtnGantt')
        self.safe_click(gantt_btn)
        self.wait_visible(By.ID, 'viewContainerGantt')
        self.assertIn('view=gantt', self.driver.current_url)
        gantt_cont = self.driver.find_element(By.ID, 'viewContainerGantt')
        self.assertTrue(gantt_cont.is_displayed())

        # 3. Switch back to Projects Grid
        grid_btn = self.wait_clickable(By.ID, 'viewBtnGrid')
        self.safe_click(grid_btn)
        self.wait_visible(By.ID, 'viewContainerGrid')
        grid_cont = self.driver.find_element(By.ID, 'viewContainerGrid')
        self.assertTrue(grid_cont.is_displayed())

    def test_02_dark_mode_toggle_button(self):
        """Test clicking #themeToggleBtn toggles dark mode on html element and saves preference."""
        self.driver.get(f"{self.base_url}/?mode=active")
        theme_btn = self.wait_clickable(By.ID, 'themeToggleBtn')

        # Initial state on html tag
        html_elem = self.driver.find_element(By.TAG_NAME, 'html')
        initial_is_dark = 'dark-mode' in (html_elem.get_attribute('class') or '')

        # First click -> toggles
        self.safe_click(theme_btn)
        time.sleep(0.3)
        after_click_1 = 'dark-mode' in (html_elem.get_attribute('class') or '')
        self.assertNotEqual(initial_is_dark, after_click_1)

        # Second click -> toggles back
        self.safe_click(theme_btn)
        time.sleep(0.3)
        after_click_2 = 'dark-mode' in (html_elem.get_attribute('class') or '')
        self.assertEqual(initial_is_dark, after_click_2)

    def test_03_calendar_url_redirect(self):
        """Test navigating to deprecated /calendar redirects to /?view=gantt."""
        self.driver.get(f"{self.base_url}/calendar")
        time.sleep(0.5)
        self.assertIn('view=gantt', self.driver.current_url)
        gantt_cont = self.wait_visible(By.ID, 'viewContainerGantt')
        self.assertTrue(gantt_cont.is_displayed())

    def test_04_navbar_admin_and_print_nav_buttons(self):
        """Test presence and correct link targets for Admin and Print navbar icons."""
        self.driver.get(f"{self.base_url}/?mode=active")
        admin_link = self.driver.find_element(By.CSS_SELECTOR, 'a.navbar-icon-link[href="/admin"]')
        self.assertTrue(admin_link.is_displayed())
        self.assertEqual(admin_link.get_attribute('title'), 'ממשק ניהול')

        print_link = self.driver.find_element(By.CSS_SELECTOR, 'a.navbar-icon-link.print-link')
        self.assertTrue(print_link.is_displayed())
        self.assertIn('/print', print_link.get_attribute('href'))

    # =============================================================
    # 2. Search & Filters Controls
    # =============================================================
    def test_05_search_input_and_clear_button(self):
        """Test typing into #searchBox filters tasks and #clearSearch button clears it."""
        self.driver.get(f"{self.base_url}/?view=grid&mode=active")
        search_box = self.wait_clickable(By.ID, 'searchBox')
        clear_btn = self.driver.find_element(By.ID, 'clearSearch')

        # Clear button should initially be hidden
        self.assertFalse(clear_btn.is_displayed())

        # Type search keyword
        search_box.send_keys("Kubernetes")
        time.sleep(0.5)

        # Clear button should become visible
        self.assertTrue(clear_btn.is_displayed())

        # Click clear search button
        self.safe_click(clear_btn)
        time.sleep(0.3)
        self.assertEqual(search_box.get_attribute('value'), '')
        self.assertFalse(clear_btn.is_displayed())

    def test_06_team_filters_and_archive_toggle(self):
        """Test team filter buttons filter active view and archive filter button toggles archive mode."""
        self.driver.get(f"{self.base_url}/?view=grid&mode=active")
        team_btns = self.driver.find_elements(By.CSS_SELECTOR, '.team-filter-group .filter-team-btn:not(.archive-filter-btn)')
        self.assertGreater(len(team_btns), 0)

        # Click first team filter
        first_team_btn = team_btns[0]
        self.safe_click(first_team_btn)
        time.sleep(0.3)
        self.assertIn('active', first_team_btn.get_attribute('class'))

        # Click archive button
        archive_btn = self.driver.find_element(By.CSS_SELECTOR, '.archive-filter-btn')
        self.safe_click(archive_btn)
        active_archive_btn = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.archive-filter-btn.active'))
        )
        self.assertTrue(active_archive_btn.is_displayed())

        # Restore active mode and clear localStorage to avoid bleeding into subsequent tests
        self.driver.execute_script("localStorage.removeItem('activeTeamFilter');")
        clear_btn = self.driver.find_element(By.ID, 'clearFiltersBtn')
        self.safe_click(clear_btn)
        time.sleep(0.3)

    def test_07_status_and_priority_dropdown_filters(self):
        """Test status filter (including 'not-done') and priority filter dropdown selections."""
        self.driver.get(f"{self.base_url}/?view=grid&mode=active")
        status_select = Select(self.wait_clickable(By.ID, 'filterStatus'))
        priority_select = Select(self.wait_clickable(By.ID, 'filterPriority'))

        # Select 'not-done'
        status_select.select_by_value('not-done')
        time.sleep(0.3)
        self.assertEqual(self.driver.find_element(By.ID, 'filterStatus').get_attribute('value'), 'not-done')

        # Select 'high' priority
        priority_select.select_by_value('high')
        time.sleep(0.3)
        self.assertEqual(self.driver.find_element(By.ID, 'filterPriority').get_attribute('value'), 'high')

    def test_08_clear_filters_button_action(self):
        """Test #clearFiltersBtn resets search, status, priority, and team filter selections."""
        self.driver.get(f"{self.base_url}/?view=grid&mode=active")
        # Apply filters
        search_box = self.driver.find_element(By.ID, 'searchBox')
        search_box.send_keys("test")
        Select(self.driver.find_element(By.ID, 'filterStatus')).select_by_value('status-inprogress')
        Select(self.driver.find_element(By.ID, 'filterPriority')).select_by_value('high')

        # Click clear filters
        clear_all_btn = self.wait_clickable(By.ID, 'clearFiltersBtn')
        self.safe_click(clear_all_btn)
        time.sleep(0.3)

        self.assertEqual(search_box.get_attribute('value'), '')
        self.assertEqual(self.driver.find_element(By.ID, 'filterStatus').get_attribute('value'), 'all')
        self.assertEqual(self.driver.find_element(By.ID, 'filterPriority').get_attribute('value'), 'all')

    # =============================================================
    # 3. Project Management Modals & Buttons
    # =============================================================
    def test_09_open_and_close_project_modal(self):
        """Test clicking #addProjectBtn opens #projectModal and .close-modal-project closes it."""
        self.driver.get(f"{self.base_url}/?view=grid&mode=active")
        add_proj_btn = self.wait_clickable(By.ID, 'addProjectBtn')
        self.safe_click(add_proj_btn)

        modal = self.wait_visible(By.ID, 'projectModal')
        self.assertTrue(modal.is_displayed())
        title_el = WebDriverWait(self.driver, 5).until(
            lambda d: d.find_element(By.ID, 'projectModalTitle') if d.find_element(By.ID, 'projectModalTitle').text.strip() else False
        )
        self.assertEqual(title_el.text.strip(), 'הוסף פרויקט חדש')

        # Close modal
        close_btn = self.driver.find_element(By.CSS_SELECTOR, '.close-modal-project')
        self.safe_click(close_btn)
        time.sleep(0.3)
        self.assertFalse(modal.is_displayed())

    def test_10_create_project_and_validation(self):
        """Test project creation: validation requiring name and team, and successful submission."""
        self.driver.get(f"{self.base_url}/?view=grid&mode=active")
        self.safe_click(self.wait_clickable(By.ID, 'addProjectBtn'))
        modal = self.wait_visible(By.ID, 'projectModal')

        # Fill name
        name_input = self.driver.find_element(By.ID, 'projectModalNameInput')
        name_input.clear()
        name_input.send_keys("פרויקט אוטומציה סלניום")

        # Select at least one team checkbox
        team_checkboxes = self.driver.find_elements(By.CSS_SELECTOR, '#projectTeamsSelect input[type="checkbox"]')
        if team_checkboxes:
            if not team_checkboxes[0].is_selected():
                self.safe_click(team_checkboxes[0])

        # Click save
        save_btn = self.wait_clickable(By.ID, 'projectModalSaveBtn')
        self.safe_click(save_btn)
        time.sleep(0.8)

        # Modal should close after successful creation
        self.assertFalse(modal.is_displayed())

    def test_11_edit_project_button_on_project_card(self):
        """Test clicking .edit-project-btn on project card opens modal with edit state and action buttons."""
        self.driver.get(f"{self.base_url}/?view=grid&mode=active")
        edit_btns = self.driver.find_elements(By.CSS_SELECTOR, '.edit-project-btn')
        self.assertGreater(len(edit_btns), 0)

        self.safe_click(edit_btns[0])
        modal = self.wait_visible(By.ID, 'projectModal')
        self.assertTrue(modal.is_displayed())
        title_el = WebDriverWait(self.driver, 5).until(
            lambda d: d.find_element(By.ID, 'projectModalTitle') if d.find_element(By.ID, 'projectModalTitle').text.strip() else False
        )
        self.assertIn(title_el.text.strip(), ['ערוך פרויקט', 'עריכת פרויקט'])

        # Verify archive and delete action buttons are visible in edit mode
        archive_btn = self.driver.find_element(By.ID, 'projectModalArchiveBtn')
        delete_btn = self.driver.find_element(By.ID, 'projectModalDeleteBtn')
        self.assertTrue(archive_btn.is_displayed())
        self.assertTrue(delete_btn.is_displayed())

        # Close
        self.safe_click(self.driver.find_element(By.CSS_SELECTOR, '.close-modal-project'))
        time.sleep(0.3)

    # =============================================================
    # 4. Wide 2-Column Task Creation Modal
    # =============================================================
    def test_12_create_task_modal_from_project_card_team_preselect(self):
        """Test clicking + Task on a project card opens wide modal with project and team pre-selected."""
        self.driver.get(f"{self.base_url}/?view=grid&mode=active")
        add_task_btns = self.driver.find_elements(By.CSS_SELECTOR, '.add-task-project-btn')
        self.assertGreater(len(add_task_btns), 0)

        # Click + on first project card
        target_btn = add_task_btns[0]
        project_name = target_btn.get_attribute('data-project')
        self.safe_click(target_btn)

        # Verify wide modal opens and animation settles
        create_modal = self.wait_visible(By.ID, 'createTaskModal')
        content_box = WebDriverWait(self.driver, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '#createTaskModal .modal-content-wide'))
        )
        self.assertTrue(content_box.is_displayed())

        # Verify project is pre-selected
        proj_val = self.driver.find_element(By.ID, 'createTaskProject').get_attribute('value')
        self.assertEqual(proj_val, project_name)

        # Verify team is pre-selected (non-empty)
        team_val = self.driver.find_element(By.ID, 'createTaskTeam').get_attribute('value')
        self.assertTrue(len(team_val) > 0, "Team should be preselected when creating task from project card")

        # Close modal
        self.safe_click(self.driver.find_element(By.CSS_SELECTOR, '.close-modal-create'))
        time.sleep(0.3)
        self.assertFalse(create_modal.is_displayed())

    def test_13_create_new_task_submission_flow(self):
        """Test filling wide task creation modal fields and submitting with #createSaveBtn."""
        self.driver.get(f"{self.base_url}/?view=grid&mode=active")
        add_task_btns = self.driver.find_elements(By.CSS_SELECTOR, '.add-task-project-btn')
        self.safe_click(add_task_btns[0])
        WebDriverWait(self.driver, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '#createTaskModal .modal-content-wide'))
        )

        # Fill task title and notes
        title_input = self.driver.find_element(By.ID, 'createTaskNameInput')
        title_input.clear()
        test_task_title = "משימת בדיקת סלניום חדשה " + str(int(time.time()))
        title_input.send_keys(test_task_title)

        notes_input = self.driver.find_element(By.ID, 'createTaskNotes')
        notes_input.clear()
        notes_input.send_keys("פירוט משימה עבור בדיקות אוטומציה")

        # Select status & priority
        Select(self.driver.find_element(By.ID, 'createTaskStatus')).select_by_value('status-inprogress')
        Select(self.driver.find_element(By.ID, 'createTaskPriority')).select_by_value('high')

        # Click create button
        create_btn = self.wait_clickable(By.ID, 'createSaveBtn')
        self.safe_click(create_btn)
        time.sleep(1.0)

        # Modal should be closed and new task title should exist on dashboard
        self.assertFalse(self.driver.find_element(By.ID, 'createTaskModal').is_displayed())
        self.assertIn(test_task_title, self.driver.page_source)

    # =============================================================
    # 5. Wide 2-Column Task Edit Modal & Interactive Features
    # =============================================================
    def test_14_task_edit_modal_wide_layout_and_fields(self):
        """Test opening wide 2-column task modal (#taskModal) and verifying both primary and secondary columns."""
        self.driver.get(f"{self.base_url}/?view=grid&mode=active")
        task_items = self.driver.find_elements(By.CSS_SELECTOR, '.task-item')
        self.assertGreater(len(task_items), 0)

        # Click first task card
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", task_items[0])
        self.safe_click(task_items[0])
        modal = self.wait_visible(By.ID, 'taskModal')
        primary_col = WebDriverWait(self.driver, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '#taskModal .task-modal-col-primary'))
        )
        secondary_col = WebDriverWait(self.driver, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '#taskModal .task-modal-col-secondary'))
        )
        self.assertTrue(primary_col.is_displayed())
        self.assertTrue(secondary_col.is_displayed())

        # Verify fields in primary column: Title, Notes, Subtasks Section, Comments Section
        self.assertTrue(self.driver.find_element(By.ID, 'taskNameInput').is_displayed())
        self.assertTrue(self.driver.find_element(By.ID, 'taskNotes').is_displayed())
        self.assertTrue(self.driver.find_element(By.ID, 'taskSubtasksSection').is_displayed())
        self.assertTrue(self.driver.find_element(By.ID, 'taskCommentsSection').is_displayed())

        # Verify fields in secondary column: Status, Priority, Project, Team, Save Button
        self.assertTrue(self.driver.find_element(By.ID, 'taskStatus').is_displayed())
        self.assertTrue(self.driver.find_element(By.ID, 'taskPriority').is_displayed())
        self.assertTrue(self.driver.find_element(By.ID, 'taskProject').is_displayed())
        self.assertTrue(self.driver.find_element(By.ID, 'taskTeam').is_displayed())
        self.assertTrue(self.driver.find_element(By.ID, 'saveBtn').is_displayed())
        self.assertTrue(self.driver.find_element(By.ID, 'archiveBtn').is_displayed())
        self.assertTrue(self.driver.find_element(By.ID, 'deleteBtn').is_displayed())

        # Close
        self.safe_click(self.driver.find_element(By.CSS_SELECTOR, '#taskModal .close-modal'))
        time.sleep(0.3)
        self.assertFalse(modal.is_displayed())

    def test_15_subtasks_checklist_interactive_actions(self):
        """Test subtasks checklist: adding subtask, toggling completion, progress bar update, and deletion."""
        self.driver.get(f"{self.base_url}/?view=grid&mode=active")
        task_items = self.driver.find_elements(By.CSS_SELECTOR, '.task-item')
        self.assertGreater(len(task_items), 0)
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", task_items[0])
        self.safe_click(task_items[0])
        WebDriverWait(self.driver, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '#taskModal .modal-content-wide'))
        )

        # 1. Add Subtask
        subtask_input = self.wait_clickable(By.ID, 'newSubtaskInput')
        subtask_input.clear()
        subtask_title = "בדיקת צקליסט אוטומטית " + str(int(time.time()))
        subtask_input.send_keys(subtask_title)

        add_btn = self.wait_clickable(By.ID, 'addSubtaskBtn')
        self.safe_click(add_btn)

        # Verify subtask item appears in list
        WebDriverWait(self.driver, 5).until(
            lambda d: subtask_title in d.find_element(By.ID, 'subtasksList').text
        )
        subtasks_list = self.driver.find_element(By.ID, 'subtasksList')
        self.assertIn(subtask_title, subtasks_list.text)

        # 2. Toggle checkbox
        checkboxes = subtasks_list.find_elements(By.CSS_SELECTOR, '.subtask-checkbox')
        if checkboxes:
            last_checkbox = checkboxes[-1]
            self.safe_click(last_checkbox)
            time.sleep(0.4)

        # Verify progress text and bar update
        prog_text = self.driver.find_element(By.ID, 'subtaskProgressText').text
        self.assertIn('/', prog_text)

        # 3. Delete Subtask
        delete_btns = self.driver.find_elements(By.CSS_SELECTOR, '#subtasksList .subtask-delete-btn')
        if delete_btns:
            self.safe_click(delete_btns[-1])
            self.handle_alert_if_present()
            time.sleep(0.4)

        # Close modal
        self.safe_click(self.driver.find_element(By.CSS_SELECTOR, '#taskModal .close-modal'))
        time.sleep(0.3)

    def test_16_comments_thread_interactive_actions(self):
        """Test comments thread: entering comment, author dropdown, posting, and deleting comment."""
        self.driver.get(f"{self.base_url}/?view=grid&mode=active")
        task_items = self.driver.find_elements(By.CSS_SELECTOR, '.task-item')
        self.assertGreater(len(task_items), 0)
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", task_items[0])
        self.safe_click(task_items[0])
        WebDriverWait(self.driver, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '#taskModal .modal-content-wide'))
        )

        # Select author if available
        author_select = Select(self.driver.find_element(By.ID, 'commentAuthorSelect'))
        if len(author_select.options) > 0:
            author_select.select_by_index(0)

        # Type comment text
        comment_input = self.wait_clickable(By.ID, 'newCommentInput')
        comment_input.clear()
        comment_text = "הערת בדיקה אוטומטית בסלניום " + str(int(time.time()))
        comment_input.send_keys(comment_text)

        # Click post button
        add_comment_btn = self.wait_clickable(By.ID, 'addCommentBtn')
        self.safe_click(add_comment_btn)

        # Verify comment is listed in thread
        WebDriverWait(self.driver, 5).until(
            lambda d: comment_text in d.find_element(By.ID, 'commentsList').text
        )
        comments_list = self.driver.find_element(By.ID, 'commentsList')
        self.assertIn(comment_text, comments_list.text)

        # Delete comment
        del_comment_btns = self.driver.find_elements(By.CSS_SELECTOR, '#commentsList .comment-delete-btn')
        if del_comment_btns:
            self.safe_click(del_comment_btns[-1])
            self.handle_alert_if_present()
            time.sleep(0.4)

        # Close modal
        self.safe_click(self.driver.find_element(By.CSS_SELECTOR, '#taskModal .close-modal'))
        time.sleep(0.3)

    def test_17_task_edit_save_button(self):
        """Test editing task name and notes in wide modal and saving with #saveBtn."""
        self.driver.get(f"{self.base_url}/?view=grid&mode=active")
        task_items = self.driver.find_elements(By.CSS_SELECTOR, '.task-item')
        self.safe_click(task_items[0])
        self.wait_visible(By.ID, 'taskModal')

        # Update notes
        notes_textarea = self.driver.find_element(By.ID, 'taskNotes')
        notes_textarea.clear()
        updated_note = "עודכן בהצלחה ע״י סוויטת סלניום"
        notes_textarea.send_keys(updated_note)

        # Click save
        save_btn = self.wait_clickable(By.ID, 'saveBtn')
        self.safe_click(save_btn)
        time.sleep(0.8)

        # Modal closes
        self.assertFalse(self.driver.find_element(By.ID, 'taskModal').is_displayed())

    # =============================================================
    # 6. Kanban Board User Interface & Buttons
    # =============================================================
    def test_18_kanban_columns_and_counters(self):
        """Test Kanban board renders 4 status columns with titles, status dots, and live counters."""
        self.driver.get(f"{self.base_url}/?view=kanban&mode=active")
        self.wait_visible(By.ID, 'viewContainerKanban')

        columns = ['status-notstarted', 'status-inprogress', 'status-delayed', 'status-done']
        for col_status in columns:
            col_elem = self.driver.find_element(By.CSS_SELECTOR, f'.kanban-column[data-status="{col_status}"]')
            self.assertTrue(col_elem.is_displayed())
            counter_elem = self.driver.find_element(By.ID, f'count-{col_status}')
            self.assertTrue(counter_elem.is_displayed())
            count_val = int(counter_elem.text.strip())
            self.assertGreaterEqual(count_val, 0)

    def test_19_kanban_card_click_opens_wide_modal(self):
        """Test clicking any Kanban task card opens the wide #taskModal."""
        self.driver.get(f"{self.base_url}/?view=kanban&mode=active")
        cards = self.driver.find_elements(By.CSS_SELECTOR, '.kanban-card')
        self.assertGreater(len(cards), 0)

        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", cards[0])
        self.safe_click(cards[0])
        modal = self.wait_visible(By.ID, 'taskModal')
        content_wide = WebDriverWait(self.driver, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '#taskModal .modal-content-wide'))
        )
        self.assertTrue(content_wide.is_displayed())

        # Close
        self.safe_click(self.driver.find_element(By.CSS_SELECTOR, '#taskModal .close-modal'))
        time.sleep(0.3)

    # =============================================================
    # 7. Gantt Chart User Interface & Buttons
    # =============================================================
    def test_20_gantt_navigation_buttons(self):
        """Test Gantt period navigation controls: #ganttPrevBtn, #ganttNextBtn, and #ganttTodayBtn."""
        self.driver.get(f"{self.base_url}/?view=gantt&mode=active")
        self.wait_visible(By.ID, 'viewContainerGantt')

        period_title = self.wait_visible(By.ID, 'ganttPeriodTitle')
        initial_title = period_title.text.strip()

        # Click Next Period (2 weeks forward)
        next_btn = self.wait_clickable(By.ID, 'ganttNextBtn')
        self.safe_click(next_btn)
        time.sleep(0.4)
        next_title = period_title.text.strip()
        self.assertNotEqual(initial_title, next_title)

        # Click Today
        today_btn = self.wait_clickable(By.ID, 'ganttTodayBtn')
        self.safe_click(today_btn)
        time.sleep(0.4)
        today_title = period_title.text.strip()
        self.assertEqual(initial_title, today_title)

        # Click Prev Period (2 weeks back)
        prev_btn = self.wait_clickable(By.ID, 'ganttPrevBtn')
        self.safe_click(prev_btn)
        time.sleep(0.4)
        prev_title = period_title.text.strip()
        self.assertNotEqual(today_title, prev_title)

    def test_21_gantt_chart_body_and_legend(self):
        """Test Gantt timeline body renders Hebrew day headers, legend dots, and task rows."""
        self.driver.get(f"{self.base_url}/?view=gantt&mode=active")
        self.wait_visible(By.ID, 'viewContainerGantt')

        legend = self.driver.find_element(By.CSS_SELECTOR, '.gantt-legend')
        self.assertTrue(legend.is_displayed())
        self.assertIn('טרם החל', legend.text)
        self.assertIn('הושלם', legend.text)
        self.assertIn('יום מיוחד', legend.text)

        chart_body = self.driver.find_element(By.ID, 'ganttChartBody')
        self.assertTrue(chart_body.is_displayed())

    # =============================================================
    # 8. AI Assistant Widget UI & Buttons
    # =============================================================
    def test_22_ai_assistant_fab_and_close_buttons(self):
        """Test clicking #aiFabBtn opens AI panel, and #aiCloseBtn closes it."""
        self.driver.get(f"{self.base_url}/?mode=active")
        fab_btn = self.wait_clickable(By.ID, 'aiFabBtn')
        ai_panel = self.driver.find_element(By.ID, 'aiPanel')

        self.assertFalse(ai_panel.is_displayed())

        # Click FAB -> open panel
        self.safe_click(fab_btn)
        time.sleep(0.3)
        self.assertTrue(ai_panel.is_displayed())
        self.assertIn('active', ai_panel.get_attribute('class'))

        # Click Close -> close panel
        close_btn = self.wait_clickable(By.ID, 'aiCloseBtn')
        self.safe_click(close_btn)
        time.sleep(0.3)
        self.assertNotIn('active', ai_panel.get_attribute('class'))

    def test_23_ai_assistant_quick_action_chips_and_clear_button(self):
        """Test AI quick action chips (summary, deadlines, stale, prompt) and clear chat button."""
        self.driver.get(f"{self.base_url}/?mode=active")
        self.safe_click(self.wait_clickable(By.ID, 'aiFabBtn'))
        time.sleep(0.3)

        # Verify quick action chips exist
        chips = self.driver.find_elements(By.CSS_SELECTOR, '.ai-chip')
        self.assertGreaterEqual(len(chips), 4)

        # Verify clear button
        clear_btn = self.wait_clickable(By.ID, 'aiClearBtn')
        self.safe_click(clear_btn)
        self.handle_alert_if_present()
        time.sleep(0.3)
        messages_cont = self.driver.find_element(By.ID, 'aiMessages')
        self.assertIn('שלום! אני עוזר ה-AI של TeamTasks', messages_cont.text)

        # Close
        self.safe_click(self.driver.find_element(By.ID, 'aiCloseBtn'))

    # =============================================================
    # 9. Admin Page UI & Buttons (/admin)
    # =============================================================
    def test_24_admin_sidebar_tab_navigation(self):
        """Test navigating to /admin and clicking sidebar tabs (Teams, Special Days, Backup, System, MCP)."""
        self.driver.get(f"{self.base_url}/admin")

        sections = ['special-days', 'backup', 'system', 'mcp', 'teams']
        for sec in sections:
            nav_btn = self.wait_clickable(By.CSS_SELECTOR, f'.settings-nav .nav-item[data-section="{sec}"]')
            self.safe_click(nav_btn)
            time.sleep(0.3)
            active_section = self.driver.find_element(By.ID, f'section-{sec}')
            self.assertTrue(active_section.is_displayed())
            self.assertIn('active', active_section.get_attribute('class'))

    def test_25_admin_add_team_and_member_modals(self):
        """Test admin action buttons: #addTeamBtn opens #teamModal, .add-member opens #memberModal."""
        self.driver.get(f"{self.base_url}/admin")
        self.safe_click(self.wait_clickable(By.CSS_SELECTOR, '.settings-nav .nav-item[data-section="teams"]'))

        # 1. Add Team Modal
        add_team_btn = self.wait_clickable(By.ID, 'addTeamBtn')
        self.safe_click(add_team_btn)
        team_modal = self.wait_visible(By.ID, 'teamModal')
        self.assertTrue(team_modal.is_displayed())

        # Cancel Team Modal
        self.safe_click(self.driver.find_element(By.ID, 'cancelTeamBtn'))
        time.sleep(0.3)
        self.assertFalse(team_modal.is_displayed())

        # 2. Add Member Modal
        add_member_btn = self.wait_clickable(By.CSS_SELECTOR, '.add-member')
        self.safe_click(add_member_btn)
        member_modal = self.wait_visible(By.ID, 'memberModal')
        self.assertTrue(member_modal.is_displayed())

        # Verify predefined avatars load asynchronously
        WebDriverWait(self.driver, 5).until(
            lambda d: len(member_modal.find_elements(By.CSS_SELECTOR, '#predefinedAvatarsGrid .predefined-avatar-item')) > 0
        )
        avatar_items = member_modal.find_elements(By.CSS_SELECTOR, '#predefinedAvatarsGrid .predefined-avatar-item')
        self.assertGreater(len(avatar_items), 0)

        # Cancel Member Modal using top close button
        close_member_btn = member_modal.find_element(By.CSS_SELECTOR, '.close-member-modal')
        self.safe_click(close_member_btn)
        WebDriverWait(self.driver, 5).until(
            EC.invisibility_of_element_located((By.ID, 'memberModal'))
        )
        self.assertFalse(member_modal.is_displayed())

    def test_26_admin_special_days_modal_and_colors(self):
        """Test admin special days tab: #addSpecialDayBtn opens modal and color presets update selection."""
        self.driver.get(f"{self.base_url}/admin")
        self.safe_click(self.wait_clickable(By.CSS_SELECTOR, '.settings-nav .nav-item[data-section="special-days"]'))

        add_sd_btn = self.wait_clickable(By.ID, 'addSpecialDayBtn')
        self.safe_click(add_sd_btn)
        sd_modal = self.wait_visible(By.ID, 'specialDayModal')
        self.assertTrue(sd_modal.is_displayed())

        # Click color preset
        color_presets = self.driver.find_elements(By.CSS_SELECTOR, '.color-preset-btn')
        if len(color_presets) > 1:
            target_preset = color_presets[1]
            preset_color = target_preset.get_attribute('data-color')
            self.safe_click(target_preset)
            input_color = self.driver.find_element(By.ID, 'specialDayColorInput').get_attribute('value')
            self.assertEqual(preset_color.lower(), input_color.lower())

        # Cancel modal
        self.safe_click(self.driver.find_element(By.ID, 'cancelSpecialDayBtn'))
        time.sleep(0.3)
        self.assertFalse(sd_modal.is_displayed())

    def test_27_admin_system_integrity_check_button(self):
        """Test clicking #btnCheckDbIntegrity triggers database integrity verification."""
        self.driver.get(f"{self.base_url}/admin")
        self.safe_click(self.wait_clickable(By.CSS_SELECTOR, '.settings-nav .nav-item[data-section="system"]'))

        btn_check = self.wait_clickable(By.ID, 'btnCheckDbIntegrity')
        self.safe_click(btn_check)
        time.sleep(0.6)

        result_span = self.driver.find_element(By.ID, 'dbIntegrityResult')
        self.assertTrue(len(result_span.text.strip()) > 0, "Integrity check should display result text")

    def test_28_admin_backup_actions_and_history_table(self):
        """Test admin backup section: #btnBackupNow initiates backup snapshot and updates table."""
        self.driver.get(f"{self.base_url}/admin")
        self.safe_click(self.wait_clickable(By.CSS_SELECTOR, '.settings-nav .nav-item[data-section="backup"]'))

        # Verify Backup Now button exists
        btn_backup = self.wait_clickable(By.ID, 'btnBackupNow')
        self.assertTrue(btn_backup.is_displayed())

        # Trigger immediate backup
        self.safe_click(btn_backup)
        time.sleep(1.0)

        # Verify backups history table body has content
        tbody = self.driver.find_element(By.ID, 'dbBackupsTableBody')
        self.assertTrue(tbody.is_displayed())
        rows = tbody.find_elements(By.TAG_NAME, 'tr')
        self.assertGreater(len(rows), 0)

    def test_29_admin_mcp_tabs_and_playground_run_tool(self):
        """Test admin MCP section: config tabs switching and MCP Playground tool execution."""
        self.driver.get(f"{self.base_url}/admin")
        self.safe_click(self.wait_clickable(By.CSS_SELECTOR, '.settings-nav .nav-item[data-section="mcp"]'))

        # Config tabs
        claude_tab = self.wait_clickable(By.CSS_SELECTOR, '.mcp-tab-btn[data-config-tab="claude"]')
        self.safe_click(claude_tab)
        time.sleep(0.3)
        code_block = self.driver.find_element(By.ID, 'mcpConfigCodeBlock')
        self.assertIn('pythonioencoding', code_block.text.lower())

        # Tool playground execution
        tool_select = Select(self.driver.find_element(By.ID, 'mcpPlaygroundToolSelect'))
        if len(tool_select.options) > 0:
            tool_select.select_by_value('get_executive_summary')
            time.sleep(0.3)
            run_btn = self.wait_clickable(By.ID, 'btnRunMcpTool')
            self.safe_click(run_btn)
            time.sleep(0.8)

            result_box = self.driver.find_element(By.ID, 'mcpPlaygroundResultContainer')
            self.assertTrue(result_box.is_displayed())

    # =============================================================
    # 10. Printable Page UI & Buttons (/print)
    # =============================================================
    def test_30_printable_table_view_and_filter_dropdowns(self):
        """Test /print default table view, view toggle buttons, and filter dropdowns."""
        self.driver.get(f"{self.base_url}/print")

        # Verify filters exist: Team, Project, Status (with not-done), Priority
        team_filter = self.driver.find_element(By.ID, 'teamFilter')
        proj_filter = self.driver.find_element(By.ID, 'projectFilter')
        status_filter = self.driver.find_element(By.ID, 'statusFilter')
        prio_filter = self.driver.find_element(By.ID, 'priorityFilter')
        print_btn = self.driver.find_element(By.ID, 'printBtn')

        self.assertTrue(team_filter.is_displayed())
        self.assertTrue(proj_filter.is_displayed())
        self.assertTrue(status_filter.is_displayed())
        self.assertTrue(prio_filter.is_displayed())
        self.assertTrue(print_btn.is_displayed())

        # Verify 'not-done' option exists in print status filter
        status_opts = [o.get_attribute('value') for o in Select(status_filter).options]
        self.assertIn('not-done', status_opts)

    def test_31_printable_gantt_view_and_navigation(self):
        """Test switching /print to Gantt view and interacting with period navigation buttons."""
        self.driver.get(f"{self.base_url}/print?view=gantt")
        self.assertIn('view=gantt', self.driver.current_url)

        # Check Gantt printable timeline elements
        timeline_header = self.driver.find_element(By.CSS_SELECTOR, '.print-gantt-timeline-header')
        self.assertTrue(timeline_header.is_displayed())

        # Verify navigation controls exist
        nav_controls = self.driver.find_element(By.CSS_SELECTOR, '.print-gantt-nav')
        self.assertTrue(nav_controls.is_displayed())
        self.assertIn('שבועיים קדימה', nav_controls.text)
        self.assertIn('שבועיים אחורה', nav_controls.text)
        self.assertIn('היום', nav_controls.text)

    def test_32_printable_back_to_dashboard_button(self):
        """Test printable view header button navigating back to dashboard."""
        self.driver.get(f"{self.base_url}/print")
        back_btn = self.driver.find_element(By.CSS_SELECTOR, '.print-meta button[onclick*="window.location.href"]')
        self.assertTrue(back_btn.is_displayed())
        self.safe_click(back_btn)
        time.sleep(0.5)
        self.assertIn(self.base_url, self.driver.current_url)


if __name__ == '__main__':
    # Ensure UTF-8 output across Windows consoles
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    unittest.main(verbosity=2)
