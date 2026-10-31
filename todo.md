# Todo List

## Navigation & View Architecture
- [x] Retire old `/calendar` page: deleted `templates/calendar.html` and redirected `/calendar` to `/?view=gantt`.
- [x] Integrated view switching into the main `.navbar-nav-tabs` ("פרויקטים", "קנבן", "גאנט").
- [x] Removed `.dashboard-view-toggle` from dashboard header for a clean, streamlined layout.

## Wide Modal Layout & Popup Experience
- [x] Redesigned Task Edit (`#taskModal`) and Task Creation (`#createTaskModal`) into a wide 2-column layout (`.modal-content-wide`).
- [x] Right column (RTL): Task name, description/notes, subtasks checklist with progress bar, and comments thread.
- [x] Left column (RTL): Card box with status, priority, project, team, start/end dates, assigned members chips, and action buttons.
- [x] Zero-scroll desktop experience fitting all data and action controls seamlessly without vertical modal scroll.
- [x] Responsive layout with graceful single-column stacking for mobile/smaller screens.
- [x] Full Dark Mode styling across all wide modal components.

## Tasks Page
- [x] After creating a project, when clicking the plus icon in the project to create a new task, the team should be already selected. Currently it works only if the filter on a specific team is selected.
- [x] Filter tasks by team members (not just team ID) when a team filter is active.
- [x] Fix special days list rendering date format.
- [x] Fix seed data generation logic (consistent teams per project).
- [x] Add tooltips to team members (team name on hover) in all views.

## Print Page
- [x] Add filtering by Status and Priority.
- [x] Add filtering by Project.
- [x] Dynamic project list updates based on other filters. 

## Layout & Design
- [x] Add Dark Mode toggle and styling for all pages.

## Automatic Database Backups & Version History
- [x] Dedicated backend service (`backup_service.py`) for online, transactionally safe SQLite backups.
- [x] Fully automatic daily backup scheduled at 23:00 to the instance mountpoint (`instance/backups`).
- [x] Multi-worker safe daily scheduling with atomic filesystem locks (`os.O_CREAT | os.O_EXCL`).
- [x] Version retention policy automatically keeping the 14 latest backup versions and pruning older ones.
- [x] Fast Restore directly from the server backup history with full database integrity verification and automatic version bump.
- [x] "Backup Now" (`גבה עכשיו לשרת`) button to take immediate on-demand server snapshots.
- [x] Direct download link for each database version file (`.db`).
- [x] Dedicated UI in Admin panel (`/admin` -> "גיבוי ושחזור") with live status badges, history table, and action controls.
- [x] MCP tools integration (`list_database_backups`, `create_database_backup`, `restore_database_backup`).

## Task Comments & Subtasks Features
- [x] Database models for TaskComment and Subtask with foreign keys and cascade delete.
- [x] REST API endpoints for Subtasks (CRUD operations and toggle completion).
- [x] REST API endpoints for Comments (CRUD operations with author and avatar support).
- [x] Visual Subtask progress bar and interactive checklist in task edit modal.
- [x] Task Comments thread with member author selection, avatar display, and timestamps.
- [x] Visual badges (subtasks completion status and comments counter) on task cards in dashboard and printable views.
- [x] Full integration into Calendar task modal.
- [x] Full backup & restore support for subtasks and comments in JSON backups and admin panel.

## Kanban Board & Gantt View Features
- [x] View switcher toggle in dashboard header (Projects Grid / Kanban Board / Gantt Chart).
- [x] Kanban Board with 4 workflow columns (Not Started, In Progress, Delayed, Done).
- [x] HTML5 Drag & Drop for Kanban cards with real-time status update, persistence, and live counters.
- [x] Direct task creation per column with preset status.
- [x] Interactive 28-day Gantt timeline with date navigation (previous, today, next period).
- [x] Visual status colors, subtask completion progress fill on Gantt bars, and quick-date assignment button.
- [x] Interactive Timeline Date Resizing: Drag left/right handles on task bars to adjust start and end dates.
- [x] Interactive Timeline Move/Paste: Drag the whole task bar along the dates axis to reschedule dates with fixed duration.
- [x] Interactive Mouse Date Marking: Click and drag across day cells on unscheduled tasks to mark and set start & end dates.
- [x] Direct task modal click handling from Kanban and Gantt.
- [x] Universal filtering (teams, members, status, priority, text search) synchronized across all three views.
- [x] Dark Mode support and responsive mobile layout. 

## AI Assistant Task Modal Integration
- [x] Fixed task opening from AI Assistant on Admin page (`/admin`).
- [x] Extracted shared `templates/task_modal.html` included in both `index.html` and `admin.html`.
- [x] Added `openStandaloneTaskModal` in `static/js/ai_assistant.js` with full editing, saving, subtasks checklist, comments thread, flatpickr dates, and "Open in Dashboard" link.
- [x] Added `?open_task=` query parameter handler in `static/js/main.js` to automatically open the task modal when navigating from external pages.
- [x] Enhanced AI chat text parsing to detect Hebrew task references (e.g. `משימה 12`, `משימה מס' 12`, `#12`).

## Comprehensive User QA & End-to-End Test Suite
- [x] Built automated REST API and Database CRUD QA suite (`tests/test_api_crud.py`) covering all 8 core API modules.
- [x] Built HTML Template DOM & Routing QA suite (`tests/test_template_dom.py`) verifying view tabs, wide 2-column modals, calendar redirect, and admin modal inclusion.
- [x] Built User Journeys & End-to-End Workflow suite (`tests/test_user_workflows.py`) simulating real user sessions for task lifecycle, Kanban drag & drop, Gantt date rescheduling, and multi-filter queries.
- [x] Built Frontend JavaScript & Math Logic suite (`tests/test_frontend_logic.js`) verifying timeline calculations, date ISO conversions, and regex markdown parsing.
- [x] Built Master Test Runner (`run_all_qa_tests.py`) running all 37 tests with 100% pass rate. 

## Mock Data & Seeding
- [x] Comprehensive mock data generator ([`seed_data.py`](file:///d:/projects/teamtasks/seed_data.py)) with 6 teams, 20 members with 3D avatars, 7 realistic tech projects, 30 tasks across all statuses and priorities, 87 checklist subtasks with progress tracking, 30 discussion comments, and 5 special days.
- [x] Dual operational modes: fresh clean-slate seeding (`python seed_data.py --reset`) and in-place enrichment (`python seed_data.py --enrich`).

## Printable Gantt Version in /print
- [x] Integrated printable Gantt timeline view at `/print?view=gantt` and `/printable?view=gantt`.
- [x] View switcher toggle in print header between "רשימת משימות" (table) and "תרשים גאנט" (timeline).
- [x] 28-day timeline window with SSR coordinate calculations and Hebrew day headers.
- [x] Two-week period navigation ("שבועיים אחורה", "שבועיים קדימה", "היום") and Hebrew period title.
- [x] Task rows grouped by project with priority dots, status pills, subtasks progress fill, member names, and scheduled date badges.
- [x] Full print optimization (`@media print`) with landscape page setup, exact color printing, and page-break avoidance.
- [x] Direct navbar print button integration routing to `/print?view=gantt` when viewing Gantt on dashboard.

## Full UI & Button Automation Test Suite (Selenium / Browser Automation)
- [x] Built comprehensive 32-test automated browser suite in `tests/test_ui_selenium.py` using headless Chrome.
- [x] Navbar buttons & view switching: Grid (`view=projects`), Kanban (`view=kanban`), Gantt (`view=gantt`), dark mode toggle (`#themeToggleBtn`), calendar redirect, admin navigation icon, and print navigation icon.
- [x] Search & Filtering controls: Search box typing, `#clearSearch`, team buttons, `.archive-filter-btn`, status dropdown (`not-done`, etc.), priority dropdown, and `#clearFiltersBtn` reset action.
- [x] Project modal actions: `#addProjectBtn` open/close, project creation with team checkbox selection and validation, `.edit-project-btn` on project cards with archive/delete actions.
- [x] Wide 2-column task modals: Opening `#createTaskModal` via `+ Task` on project card with team & project pre-selection, submitting new tasks, and wide 2-column layout verification (`.task-modal-col-primary` & `.task-modal-col-secondary`).
- [x] Interactive checklist & comments: Adding subtasks, toggling checkboxes, dynamic `#subtaskProgressBar` and `#subtaskProgressText` updates, deleting subtasks, author selection, adding comments, and deleting comments.
- [x] Kanban Board & Gantt Chart: 4 status columns with live badge counters, opening wide modal on card click, Gantt navigation buttons (`#ganttNextBtn`, `#ganttPrevBtn`, `#ganttTodayBtn`), timeline body, and status/holiday legends.
- [x] AI Assistant widget: Floating button (`#aiFabBtn`) opening `#aiPanel.active`, quick action prompt chips, `#aiClearBtn`, and `#aiCloseBtn`.
- [x] Admin panel buttons & workflows: Sidebar tab switching, `#addTeamBtn` -> `#teamModal`, `#addMemberBtn` -> `#memberModal` with predefined avatars grid, `#addSpecialDayBtn` -> `#specialDayModal` with color presets, database integrity check button (`#btnCheckDbIntegrity`), server snapshot creation (`#btnBackupNow`), and MCP playground (`#btnRunMcpTool`).
- [x] Printable view buttons: Table/Gantt view switching, filter dropdowns, 2-week period navigation, and back-to-dashboard navigation.
- [x] Standalone test runner `run_ui_tests.py` and integration into `run_all_qa_tests.py --ui`.
