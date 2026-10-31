// Event Listeners
import { state, setActiveTeamFilter, setActiveMemberFilter, setCurrentTaskItem, setStatusFilter, setPriorityFilter } from './state.js';
import * as UI from './ui.js';
import * as API from './api.js';
import * as Utils from './utils.js';
import { notifyDataChanged } from './live_sync.js';
import { initKanbanDragAndDrop } from './kanban.js';
import { prevPeriod, nextPeriod, resetToToday } from './gantt.js';

let searchTimeout;

export function attachGlobalListeners() {
    window.addEventListener('resetMemberFilter', function () {
        setActiveMemberFilter(null);
        localStorage.removeItem('activeMemberFilter');
        UI.applyFilters();
    });

    let mouseDownTarget = null;

    window.addEventListener('mousedown', (e) => {
        mouseDownTarget = e.target;
    });

    window.addEventListener('mouseup', (e) => {
        // Only close if both mousedown and mouseup happened on the modal backdrop (not the content)
        if (
            (UI.elements.modal && mouseDownTarget === UI.elements.modal && e.target === UI.elements.modal) ||
            (UI.elements.createModal && mouseDownTarget === UI.elements.createModal && e.target === UI.elements.createModal) ||
            (UI.elements.projectModal && mouseDownTarget === UI.elements.projectModal && e.target === UI.elements.projectModal)
        ) {
            UI.closeModals();
        }
        mouseDownTarget = null;
    });

    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && UI.isAnyModalOpen()) {
            UI.closeModals();
        }
    });
}

export function attachEventListeners() {

    // Add Project Button (Main top button)
    if (UI.elements.addProjectBtn) {
        UI.elements.addProjectBtn.onclick = () => UI.openCreateProjectModal();
    }
    // Fallback if referenced as addTaskBtn
    if (UI.elements.addTaskBtn) {
        UI.elements.addTaskBtn.onclick = () => UI.openCreateProjectModal();
    }

    // Close Modals
    if (UI.elements.closeModal) {
        UI.elements.closeModal.onclick = () => UI.closeModals();
    }
    if (UI.elements.closeCreateModal) {
        UI.elements.closeCreateModal.onclick = () => UI.closeModals();
    }
    if (UI.elements.closeProjectModal) {
        UI.elements.closeProjectModal.onclick = () => UI.closeModals();
    }

    // Project Modal Save / Archive / Delete
    if (UI.elements.projectModalSaveBtn) {
        UI.elements.projectModalSaveBtn.onclick = handleSaveProject;
    }
    if (UI.elements.projectModalArchiveBtn) {
        UI.elements.projectModalArchiveBtn.onclick = handleArchiveProjectToggle;
    }
    if (UI.elements.projectModalDeleteBtn) {
        UI.elements.projectModalDeleteBtn.onclick = handleDeleteProject;
    }

    // Edit Project Buttons
    document.querySelectorAll('.edit-project-btn').forEach(btn => {
        btn.onclick = (e) => {
            e.stopPropagation();
            UI.openEditProjectModal(btn.dataset.projectId);
        };
    });

    // Archive Project Buttons (from project card header)
    document.querySelectorAll('.archive-project-btn').forEach(btn => {
        btn.onclick = (e) => {
            e.stopPropagation();
            handleArchiveProjectCard(btn.dataset.projectId, btn.dataset.projectName);
        };
    });

    // Unarchive Project Buttons (from project card header)
    document.querySelectorAll('.unarchive-project-btn').forEach(btn => {
        btn.onclick = (e) => {
            e.stopPropagation();
            handleUnarchiveProjectCard(btn.dataset.projectId, btn.dataset.projectName);
        };
    });

    // Delete Project Buttons (from project card header)
    document.querySelectorAll('.delete-project-btn').forEach(btn => {
        btn.onclick = (e) => {
            e.stopPropagation();
            handleDeleteProjectCard(btn.dataset.projectId, btn.dataset.projectName, parseInt(btn.dataset.tasksCount || '0'));
        };
    });

    // Add Task to Project Buttons (+ next to project title)
    document.querySelectorAll('.add-task-project-btn').forEach(btn => {
        btn.onclick = (e) => {
            e.stopPropagation();
            const projectCard = btn.closest('.project-card');
            const teamIdsStr = projectCard ? (projectCard.dataset.teamIds || '') : '';
            const teamIds = teamIdsStr.split(',').filter(Boolean);
            let teamId = null;
            if (state.activeTeamFilter && teamIds.includes(String(state.activeTeamFilter))) {
                teamId = state.activeTeamFilter;
            } else if (teamIds.length > 0) {
                teamId = teamIds[0];
            }
            UI.openCreateModal(btn.dataset.project, teamId);
        };
    });

    // When Project changes in Create Task Modal, sync default team
    if (UI.elements.createTaskProject) {
        UI.elements.createTaskProject.onchange = () => {
            const currentProjName = UI.elements.createTaskProject.value;
            const proj = (state.projects || []).find(p => p.name === currentProjName);
            if (proj) {
                const projTeamIds = proj.team_ids || (proj.teams ? proj.teams.map(t => t.id) : []);
                if (projTeamIds.length > 0) {
                    if (state.activeTeamFilter && projTeamIds.map(String).includes(String(state.activeTeamFilter))) {
                        UI.elements.createTaskTeam.value = state.activeTeamFilter;
                    } else if (!projTeamIds.map(String).includes(String(UI.elements.createTaskTeam.value))) {
                        UI.elements.createTaskTeam.value = projTeamIds[0];
                    }
                }
            }
        };
    }

    // Task Item Click (Edit)
    document.querySelectorAll('.task-item').forEach(item => {
        item.onclick = (e) => {
            if (e.target.closest('button') || e.target.closest('input') || e.target.closest('a')) {
                return;
            }
            setCurrentTaskItem(item);
            UI.openEditModal(item);
        };
    });

    // Save/Archive/Delete Task
    if (UI.elements.saveBtn) {
        UI.elements.saveBtn.onclick = handleSaveTask;
    }
    if (UI.elements.archiveBtn) {
        UI.elements.archiveBtn.onclick = handleArchiveTaskToggle;
    }
    if (UI.elements.createSaveBtn) {
        UI.elements.createSaveBtn.onclick = handleCreateTask;
    }
    if (UI.elements.deleteBtn) {
        UI.elements.deleteBtn.onclick = handleDeleteTask;
    }

    // Subtasks event listeners
    if (UI.elements.addSubtaskBtn) {
        UI.elements.addSubtaskBtn.onclick = handleAddSubtask;
    }
    if (UI.elements.newSubtaskInput) {
        UI.elements.newSubtaskInput.onkeydown = (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                handleAddSubtask();
            }
        };
    }
    if (UI.elements.subtasksList) {
        UI.elements.subtasksList.onclick = handleSubtaskListClick;
    }

    // Comments event listeners
    if (UI.elements.addCommentBtn) {
        UI.elements.addCommentBtn.onclick = handleAddComment;
    }
    if (UI.elements.commentsList) {
        UI.elements.commentsList.onclick = handleCommentListClick;
    }

    // Search
    if (UI.elements.searchBox) {
        UI.elements.searchBox.oninput = (e) => {
            const query = e.target.value.trim();
            if (UI.elements.clearSearchBtn) {
                UI.elements.clearSearchBtn.style.display = query ? 'block' : 'none';
            }

            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => handleSearch(query), 300);
        };
    }

    if (UI.elements.clearSearchBtn) {
        UI.elements.clearSearchBtn.onclick = () => {
            UI.elements.searchBox.value = '';
            UI.elements.clearSearchBtn.style.display = 'none';
            handleSearch('');
        };
    }

    // Team Filters
    if (UI.elements.teamFilterButtons) {
        UI.elements.teamFilterButtons.forEach(btn => {
            btn.onclick = () => handleTeamFilterClick(btn);
        });
    }

    // Member Filters
    if (UI.elements.memberFilterButtons) {
        UI.elements.memberFilterButtons.forEach(btn => {
            btn.onclick = () => {
                const member = btn.dataset.member;
                if (state.activeMemberFilter === member) {
                    setActiveMemberFilter(null);
                    localStorage.removeItem('activeMemberFilter');
                } else {
                    setActiveMemberFilter(member);
                    localStorage.setItem('activeMemberFilter', member);
                }
                UI.applyFilters();
            };
        });
    }

    // Status Filter
    if (UI.elements.filterStatus) {
        UI.elements.filterStatus.onchange = (e) => {
            const val = e.target.value;
            setStatusFilter(val);
            if (val && val !== 'all') {
                localStorage.setItem('activeStatusFilter', val);
            } else {
                localStorage.removeItem('activeStatusFilter');
            }
            UI.applyFilters();
        };
    }

    // Priority Filter
    if (UI.elements.filterPriority) {
        UI.elements.filterPriority.onchange = (e) => {
            const val = e.target.value;
            setPriorityFilter(val);
            if (val && val !== 'all') {
                localStorage.setItem('activePriorityFilter', val);
            } else {
                localStorage.removeItem('activePriorityFilter');
            }
            UI.applyFilters();
        };
    }

    // Clear All Filters
    if (UI.elements.clearFiltersBtn) {
        UI.elements.clearFiltersBtn.onclick = () => {
            // Reset State
            setActiveTeamFilter(null);
            setActiveMemberFilter(null);
            setStatusFilter('all');
            setPriorityFilter('all');

            // Clear Local Storage
            localStorage.removeItem('activeTeamFilter');
            localStorage.removeItem('activeMemberFilter');
            localStorage.removeItem('activeStatusFilter');
            localStorage.removeItem('activePriorityFilter');

            // Reset UI - Team Filters
            if (UI.elements.teamFilterButtons) {
                UI.elements.teamFilterButtons.forEach(btn => btn.classList.remove('active'));
            }
            if (UI.elements.memberFilterButtons) {
                UI.elements.memberFilterButtons.forEach(btn => {
                    btn.classList.remove('active');
                    btn.style.boxShadow = 'none';
                });
            }

            // Reset Dropdowns
            if (UI.elements.filterStatus) UI.elements.filterStatus.value = 'all';
            if (UI.elements.filterPriority) UI.elements.filterPriority.value = 'all';
            if (UI.elements.searchBox) UI.elements.searchBox.value = '';

            // Update URL
            const url = new URL(window.location);
            url.searchParams.delete('team');
            if (url.searchParams.get('mode') === 'archive') {
                url.searchParams.set('mode', 'active');
                window.history.pushState({}, '', url);
                UI.refreshContent(attachEventListeners);
                return;
            }
            window.history.replaceState({}, '', url);

            // Apply Filters (which will also reset member visibility)
            UI.applyFilters();
        };
    }

    // Navbar View Mode Tabs (Grid / Kanban / Gantt)
    document.querySelectorAll('.navbar-nav-tabs .navbar-brand-link').forEach(btn => {
        btn.onclick = (e) => {
            const mode = btn.dataset.view;
            if (mode && window.location.pathname === '/') {
                e.preventDefault();
                UI.switchViewMode(mode);
                const url = new URL(window.location);
                url.searchParams.set('view', mode);
                window.history.replaceState({}, '', url);
            }
        };
    });

    // Kanban Column Add Task Buttons
    document.querySelectorAll('.kanban-col-add-btn').forEach(btn => {
        btn.onclick = (e) => {
            e.stopPropagation();
            const status = btn.dataset.status;
            UI.openCreateModal(null, null, status);
        };
    });

    // Initialize Kanban HTML5 Drag & Drop
    initKanbanDragAndDrop();

    // Gantt Navigation Controls
    const ganttPrev = document.getElementById('ganttPrevBtn');
    if (ganttPrev) ganttPrev.onclick = () => prevPeriod();

    const ganttNext = document.getElementById('ganttNextBtn');
    if (ganttNext) ganttNext.onclick = () => nextPeriod();

    const ganttToday = document.getElementById('ganttTodayBtn');
    if (ganttToday) ganttToday.onclick = () => resetToToday();
}

async function handleSaveProject() {
    const id = UI.elements.projectModalId.value;
    const name = UI.elements.projectModalNameInput.value.trim();
    const teamIds = UI.getSelectedProjectTeamIds();

    if (!name) {
        alert('נא להזין שם פרויקט');
        return;
    }
    if (teamIds.length === 0) {
        alert('יש לבחור לפחות צוות אחד לשיוך הפרויקט');
        return;
    }

    const payload = {
        name: name,
        team_ids: teamIds
    };

    try {
        let data;
        if (id) {
            data = await API.updateProject(id, payload);
        } else {
            data = await API.createProject(payload);
        }

        if (data.success) {
            UI.closeModals();
            await UI.refreshContent(attachEventListeners);
            notifyDataChanged();
        } else {
            alert('שגיאה בשמירת הפרויקט: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        alert('שגיאה בשמירת הפרויקט');
    }
}

async function handleDeleteProject() {
    const id = UI.elements.projectModalId.value;
    const name = UI.elements.projectModalNameInput.value.trim();
    if (!id) return;
    if (!confirm(`האם אתה בטוח שברצונך למחוק את הפרויקט "${name}" ואת כל המשימות שבו לצמיתות?\nפעולה זו אינה ניתנת לביטול!`)) return;

    try {
        const data = await API.deleteProject(id);
        if (data.success) {
            UI.closeModals();
            await UI.refreshContent(attachEventListeners);
            notifyDataChanged();
        } else {
            alert('שגיאה במחיקת הפרויקט: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        alert('שגיאה במחיקת הפרויקט');
    }
}

async function handleArchiveProjectToggle() {
    const id = UI.elements.projectModalId.value;
    if (!id) return;
    const isArchived = UI.elements.projectModalArchiveBtn.dataset.isArchived === 'true';
    const name = UI.elements.projectModalNameInput.value.trim();

    const msg = isArchived
        ? `האם לשחזר את הפרויקט "${name}" וכל משימותיו מהארכיון?`
        : `האם להעביר את הפרויקט "${name}" וכל משימותיו לארכיון?`;
    if (!confirm(msg)) return;

    try {
        const res = isArchived ? await API.unarchiveProject(id) : await API.archiveProject(id);
        if (res.success) {
            UI.closeModals();
            await UI.refreshContent(attachEventListeners);
            notifyDataChanged();
        } else {
            alert('שגיאה בעדכון ארכיון: ' + (res.error || 'Unknown error'));
        }
    } catch (err) {
        alert('שגיאה בעדכון ארכיון');
    }
}

async function handleArchiveProjectCard(projectId, projectName) {
    if (!confirm(`האם להעביר את הפרויקט "${projectName}" וכל משימותיו לארכיון?`)) return;
    try {
        const res = await API.archiveProject(projectId);
        if (res.success) {
            await UI.refreshContent(attachEventListeners);
            notifyDataChanged();
        } else {
            alert('שגיאה בארכוב פרויקט: ' + (res.error || 'Unknown error'));
        }
    } catch (err) {
        alert('שגיאה בארכוב פרויקט');
    }
}

async function handleUnarchiveProjectCard(projectId, projectName) {
    if (!confirm(`האם לשחזר את הפרויקט "${projectName}" וכל משימותיו מהארכיון?`)) return;
    try {
        const res = await API.unarchiveProject(projectId);
        if (res.success) {
            await UI.refreshContent(attachEventListeners);
            notifyDataChanged();
        } else {
            alert('שגיאה בשחזור פרויקט: ' + (res.error || 'Unknown error'));
        }
    } catch (err) {
        alert('שגיאה בשחזור פרויקט');
    }
}

async function handleDeleteProjectCard(projectId, projectName, tasksCount) {
    const msg = tasksCount > 0
        ? `האם אתה בטוח שברצונך למחוק את הפרויקט "${projectName}" ואת כל ${tasksCount} המשימות שבו לצמיתות?\nפעולה זו אינה ניתנת לביטול!`
        : `האם אתה בטוח שברצונך למחוק את הפרויקט "${projectName}"?`;
    if (!confirm(msg)) return;

    try {
        const res = await API.deleteProject(projectId);
        if (res.success) {
            await UI.refreshContent(attachEventListeners);
            notifyDataChanged();
        } else {
            alert('שגיאה במחיקת פרויקט: ' + (res.error || 'Unknown error'));
        }
    } catch (err) {
        alert('שגיאה במחיקת פרויקט');
    }
}

async function handleArchiveTaskToggle() {
    if (!state.currentTaskItem) return;
    const taskId = state.currentTaskItem.dataset.id;
    const isArchived = state.currentTaskItem.dataset.isArchived === 'true';

    try {
        const res = isArchived ? await API.unarchiveTask(taskId) : await API.archiveTask(taskId);
        if (res.success) {
            UI.closeModals();
            await UI.refreshContent(attachEventListeners);
            notifyDataChanged();
        } else {
            alert('שגיאה בעדכון מצב ארכיון: ' + (res.error || 'Unknown error'));
        }
    } catch (err) {
        alert('שגיאה בעדכון מצב ארכיון');
    }
}

async function handleSaveTask() {
    if (!state.currentTaskItem) return;

    const taskId = state.currentTaskItem.dataset.id;
    const selectedTeam = UI.elements.taskTeam.value;

    const selectedProject = UI.elements.taskProject ? UI.elements.taskProject.value : '';
    if (!selectedProject) {
        alert('נא לבחור פרויקט');
        return;
    }

    // Validate dates
    const startStr = UI.elements.taskStartDate.value;
    const endStr = UI.elements.taskEndDate.value;

    if (startStr && endStr) {
        const start = flatpickr.parseDate(startStr, "d/m/Y");
        const end = flatpickr.parseDate(endStr, "d/m/Y");
        if (start > end) {
            alert('תאריך ההתחלה לא יכול להיות מאוחר מתאריך הסיום');
            return;
        }
    }

    const payload = {
        project: selectedProject,
        task: UI.elements.taskNameInput.value.trim(),
        members: UI.getSelectedMembers('taskModal'),
        status: UI.elements.taskStatus.value,
        priority: UI.elements.taskPriority.value,
        notes: UI.elements.taskNotes.value.trim(),
        team_id: selectedTeam || null,
        start_date: Utils.parseDateToISO(startStr),
        end_date: Utils.parseDateToISO(endStr)
    };

    try {
        const data = await API.updateTask(taskId, payload);
        if (data.success) {
            UI.closeModals();
            await UI.refreshContent(attachEventListeners);
            notifyDataChanged();
        } else {
            alert('שגיאה בשמירת המשימה: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        alert('שגיאה בשמירת המשימה');
    }
}

async function handleCreateTask() {
    if (!UI.elements.createTaskNameInput.value.trim()) {
        alert('נא להזין שם משימה');
        return;
    }

    const selectedProject = UI.elements.createTaskProject ? UI.elements.createTaskProject.value : '';
    if (!selectedProject) {
        alert('נא לבחור פרויקט');
        return;
    }

    const startStr = UI.elements.createTaskStartDate.value;
    const endStr = UI.elements.createTaskEndDate.value;

    if (startStr && endStr) {
        const start = flatpickr.parseDate(startStr, "d/m/Y");
        const end = flatpickr.parseDate(endStr, "d/m/Y");
        if (start > end) {
            alert('תאריך ההתחלה לא יכול להיות מאוחר מתאריך הסיום');
            return;
        }
    }

    const selectedTeam = UI.elements.createTaskTeam.value;

    const payload = {
        project: selectedProject,
        task: UI.elements.createTaskNameInput.value.trim(),
        members: UI.getSelectedMembers('createTaskModal'),
        status: UI.elements.createTaskStatus.value,
        priority: UI.elements.createTaskPriority.value,
        notes: UI.elements.createTaskNotes.value.trim(),
        team_id: selectedTeam || null,
        start_date: Utils.parseDateToISO(startStr),
        end_date: Utils.parseDateToISO(endStr),
        is_archived: false
    };

    try {
        const data = await API.createTask(payload);
        if (data.success) {
            UI.closeModals();
            await UI.refreshContent(attachEventListeners);
            notifyDataChanged();
        } else {
            alert('שגיאה ביצירת המשימה: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        alert('שגיאה ביצירת המשימה');
    }
}

async function handleDeleteTask() {
    if (!state.currentTaskItem || !confirm('האם אתה בטוח שברצונך למחוק משימה זו?')) return;

    const taskId = state.currentTaskItem.dataset.id;
    try {
        const data = await API.deleteTask(taskId);
        if (data.success) {
            UI.closeModals();
            await UI.refreshContent(attachEventListeners);
            notifyDataChanged();
        } else {
            alert('שגיאה במחיקת המשימה');
        }
    } catch (error) {
        alert('שגיאה במחיקת המשימה');
    }
}

async function handleSearch(query) {
    const url = new URL(window.location);
    if (query) {
        url.searchParams.set('q', query);
        try {
            const results = await API.searchTasks(query);
            const resultIds = new Set(results.map(r => r.id));

            document.querySelectorAll('.task-item').forEach(task => {
                const taskId = parseInt(task.dataset.id);
                if (resultIds.has(taskId)) {
                    task.classList.remove('search-hidden');
                } else {
                    task.classList.add('search-hidden');
                }
            });
            UI.applyFilters();

        } catch (e) {
            console.error(e);
        }
    } else {
        url.searchParams.delete('q');
        document.querySelectorAll('.task-item').forEach(task => task.classList.remove('search-hidden'));
        UI.applyFilters();
    }

    window.history.replaceState({}, '', url);
}

async function handleTeamFilterClick(btn) {
    const teamId = btn.dataset.teamId;
    const mode = btn.dataset.mode || 'active';

    const url = new URL(window.location);

    if (mode === 'archive') {
        setActiveMemberFilter(null);
        localStorage.removeItem('activeMemberFilter');
        if (state.activeTeamFilter === 'archive') {
            url.searchParams.set('mode', 'active');
            url.searchParams.delete('team');
            setActiveTeamFilter(null);
            localStorage.removeItem('activeTeamFilter');
        } else {
            url.searchParams.set('mode', 'archive');
            url.searchParams.delete('team');
            setActiveTeamFilter('archive');
            localStorage.setItem('activeTeamFilter', 'archive');
        }
        window.history.pushState({}, '', url);
        await UI.refreshContent(attachEventListeners);
        return;
    }

    if (state.activeTeamFilter === 'archive') {
        setActiveMemberFilter(null);
        localStorage.removeItem('activeMemberFilter');
        url.searchParams.set('mode', 'active');
        url.searchParams.set('team', teamId);
        setActiveTeamFilter(teamId);
        localStorage.setItem('activeTeamFilter', teamId);

        window.history.pushState({}, '', url);
        await UI.refreshContent(attachEventListeners);
        return;
    }

    if (state.activeTeamFilter === teamId) {
        setActiveTeamFilter(null);
        url.searchParams.delete('team');
        localStorage.removeItem('activeTeamFilter');
    } else {
        setActiveTeamFilter(teamId);
        url.searchParams.set('team', teamId);
        localStorage.setItem('activeTeamFilter', teamId);
    }
    window.history.replaceState({}, '', url);

    setActiveMemberFilter(null);
    localStorage.removeItem('activeMemberFilter');
    UI.applyFilters();
}

// Subtasks & Comments Event Handlers
function getCurrentTaskId() {
    if (state.currentTaskItem && state.currentTaskItem.dataset.id) {
        return state.currentTaskItem.dataset.id;
    }
    if (UI.elements.modal && UI.elements.modal.dataset.currentTaskId) {
        return UI.elements.modal.dataset.currentTaskId;
    }
    return null;
}

async function handleAddSubtask() {
    const taskId = getCurrentTaskId();
    if (!taskId) return;
    const input = UI.elements.newSubtaskInput;
    if (!input) return;
    const title = input.value.trim();
    if (!title) return;

    try {
        const res = await API.createSubtask(taskId, title);
        if (res.success) {
            input.value = '';
            await UI.loadAndRenderTaskSubtasks(taskId);
            notifyDataChanged();
        } else {
            alert('שגיאה בהוספת פריט: ' + (res.error || 'Unknown error'));
        }
    } catch (err) {
        console.error('Failed to create subtask:', err);
        alert('שגיאה ביצירת פריט צ\'ק-ליסט');
    }
}

async function handleSubtaskListClick(e) {
    const taskId = getCurrentTaskId();
    if (!taskId) return;

    // Toggle checkbox
    const checkbox = e.target.closest('.subtask-checkbox');
    if (checkbox) {
        const subtaskId = checkbox.dataset.id;
        const itemElem = checkbox.closest('.subtask-item');
        const isCompleted = checkbox.checked;

        if (itemElem) {
            itemElem.classList.toggle('completed', isCompleted);
        }

        try {
            await API.updateSubtask(subtaskId, { is_completed: isCompleted });
            await UI.loadAndRenderTaskSubtasks(taskId);
            notifyDataChanged();
        } catch (err) {
            console.error('Failed to toggle subtask:', err);
            checkbox.checked = !isCompleted;
            if (itemElem) itemElem.classList.toggle('completed', !isCompleted);
        }
        return;
    }

    // Delete subtask
    const deleteBtn = e.target.closest('.subtask-delete-btn');
    if (deleteBtn) {
        e.stopPropagation();
        const subtaskId = deleteBtn.dataset.id;
        try {
            const res = await API.deleteSubtask(subtaskId);
            if (res.success) {
                await UI.loadAndRenderTaskSubtasks(taskId);
                notifyDataChanged();
            }
        } catch (err) {
            console.error('Failed to delete subtask:', err);
            alert('שגיאה במחיקת פריט');
        }
    }
}

async function handleAddComment() {
    const taskId = getCurrentTaskId();
    if (!taskId) return;
    const textarea = UI.elements.newCommentInput;
    if (!textarea) return;
    const content = textarea.value.trim();
    if (!content) {
        textarea.focus();
        return;
    }

    const select = UI.elements.commentAuthorSelect;
    let authorName = 'חבר צוות';
    let authorAvatar = 'default.png';
    let memberId = null;

    if (select && select.value) {
        if (select.value === 'guest') {
            authorName = 'חבר צוות';
            authorAvatar = 'default.png';
            localStorage.setItem('teamtasks_last_author', 'guest');
        } else {
            const selectedOpt = select.selectedOptions[0];
            if (selectedOpt) {
                authorName = selectedOpt.dataset.name || selectedOpt.textContent.trim();
                authorAvatar = selectedOpt.dataset.avatar || 'default.png';
                memberId = parseInt(select.value);
                localStorage.setItem('teamtasks_last_author', String(memberId));
            }
        }
    }

    try {
        const payload = {
            content: content,
            author_name: authorName,
            author_avatar: authorAvatar,
            member_id: memberId
        };
        const res = await API.createTaskComment(taskId, payload);
        if (res.success) {
            textarea.value = '';
            await UI.loadAndRenderTaskComments(taskId);
            notifyDataChanged();
        } else {
            alert('שגיאה בשמירת תגובה: ' + (res.error || 'Unknown error'));
        }
    } catch (err) {
        console.error('Failed to create comment:', err);
        alert('שגיאה בהוספת תגובה');
    }
}

async function handleCommentListClick(e) {
    const taskId = getCurrentTaskId();
    if (!taskId) return;

    const deleteBtn = e.target.closest('.comment-delete-btn');
    if (deleteBtn) {
        e.stopPropagation();
        if (!confirm('האם למחוק תגובה זו?')) return;
        const commentId = deleteBtn.dataset.id;
        try {
            const res = await API.deleteTaskComment(commentId);
            if (res.success) {
                await UI.loadAndRenderTaskComments(taskId);
                notifyDataChanged();
            }
        } catch (err) {
            console.error('Failed to delete comment:', err);
            alert('שגיאה במחיקת תגובה');
        }
    }
}
