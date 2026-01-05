// Event Listeners
import { state, setActiveTeamFilter, setActiveMemberFilter, setCurrentTaskItem, setStatusFilter, setPriorityFilter } from './state.js';
import * as UI from './ui.js';
import * as API from './api.js';
import * as Utils from './utils.js';

let searchTimeout;

export function attachGlobalListeners() {
    window.addEventListener('resetMemberFilter', function () {
        setActiveMemberFilter(null);
        UI.applyFilters();
    });

    let mouseDownTarget = null;

    window.addEventListener('mousedown', (e) => {
        mouseDownTarget = e.target;
    });

    window.addEventListener('mouseup', (e) => {
        // Only close if both mousedown and mouseup happened on the modal backdrop (not the content)
        if (UI.elements.modal && mouseDownTarget === UI.elements.modal && e.target === UI.elements.modal) {
            UI.elements.modal.style.display = 'none';
        }
        if (UI.elements.createModal && mouseDownTarget === UI.elements.createModal && e.target === UI.elements.createModal) {
            UI.elements.createModal.style.display = 'none';
        }
        mouseDownTarget = null;
    });

    // Navbar calendar link logic
    const navCalendar = document.getElementById('navCalendarLink');
    if (navCalendar) {
        navCalendar.addEventListener('click', () => {
            // If we are in archive mode, we might want to stay in archive mode? 
            // Original logic persisted 'archive' to localStorage if current mode was archive.
            // And cleared it if it was archive but we are not?
            // Let's simplified: If we are navigating away, we might want to save state if needed.
            // The original code tried to sync localstorage.
            if (state.activeTeamFilter === 'archive') {
                localStorage.setItem('activeTeamFilter', 'archive');
            } else {
                if (localStorage.getItem('activeTeamFilter') === 'archive') {
                    localStorage.removeItem('activeTeamFilter');
                }
                // If a specific team is selected, maybe save it? Original code saved team ID too.
                if (state.activeTeamFilter) {
                    localStorage.setItem('activeTeamFilter', state.activeTeamFilter);
                }
            }
        });
    }
}

export function attachEventListeners() {

    // Add Task Button
    if (UI.elements.addTaskBtn) {
        // Remove old listener if possible (not needed if elements are fresh)
        // But since we replace innerHTML of main-container, the button is new.
        UI.elements.addTaskBtn.addEventListener('click', () => UI.openCreateModal());
    }

    // Close Modals
    if (UI.elements.closeModal) {
        UI.elements.closeModal.addEventListener('click', () => UI.closeModals());
    }
    if (UI.elements.closeCreateModal) {
        UI.elements.closeCreateModal.addEventListener('click', () => UI.closeModals());
    }

    // Add Task to Project Buttons (delegation or direct)
    document.querySelectorAll('.add-task-project-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const projectCard = btn.closest('.project-card');
            const teamId = projectCard ? projectCard.dataset.teamId : null;
            UI.openCreateModal(btn.dataset.project, teamId);
        });
    });

    // Task Item Click (Edit)
    document.querySelectorAll('.task-item').forEach(item => {
        item.addEventListener('click', (e) => {
            if (e.target.closest('button') || e.target.closest('input') || e.target.closest('a')) {
                return;
            }
            setCurrentTaskItem(item);
            UI.openEditModal(item);
        });
    });

    // Save/Delete
    if (UI.elements.saveBtn) {
        UI.elements.saveBtn.onclick = handleSaveTask; // use onclick to prevent duplicates if function re-run without cleanup
    }
    if (UI.elements.createSaveBtn) {
        UI.elements.createSaveBtn.onclick = handleCreateTask;
    }
    if (UI.elements.deleteBtn) {
        UI.elements.deleteBtn.onclick = handleDeleteTask;
    }

    // Search
    if (UI.elements.searchBox) {
        UI.elements.searchBox.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            if (UI.elements.clearSearchBtn) {
                UI.elements.clearSearchBtn.style.display = query ? 'block' : 'none';
            }

            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => handleSearch(query), 300);
        });
    }

    if (UI.elements.clearSearchBtn) {
        UI.elements.clearSearchBtn.addEventListener('click', () => {
            UI.elements.searchBox.value = '';
            UI.elements.clearSearchBtn.style.display = 'none';
            handleSearch('');
        });
    }

    // Team Filters
    if (UI.elements.teamFilterButtons) {
        UI.elements.teamFilterButtons.forEach(btn => {
            btn.addEventListener('click', () => handleTeamFilterClick(btn));
        });
    }

    // Member Filters
    if (UI.elements.memberFilterButtons) {
        UI.elements.memberFilterButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const member = btn.dataset.member;
                if (state.activeMemberFilter === member) {
                    setActiveMemberFilter(null);
                } else {
                    setActiveMemberFilter(member);
                }
                UI.applyFilters();
            });
        });
    }

    // Status Filter
    if (UI.elements.filterStatus) {
        UI.elements.filterStatus.addEventListener('change', (e) => {
            setStatusFilter(e.target.value);
            UI.applyFilters();
        });
    }

    // Priority Filter
    if (UI.elements.filterPriority) {
        UI.elements.filterPriority.addEventListener('change', (e) => {
            setPriorityFilter(e.target.value);
            UI.applyFilters();
        });
    }

    // Clear All Filters
    if (UI.elements.clearFiltersBtn) {
        UI.elements.clearFiltersBtn.addEventListener('click', () => {
            // Reset State
            setActiveTeamFilter(null);
            setActiveMemberFilter(null);
            setStatusFilter('all');
            setPriorityFilter('all');

            // Clear Local Storage
            localStorage.removeItem('activeTeamFilter');

            // Reset UI - Team Filters
            if (UI.elements.teamFilterButtons) {
                UI.elements.teamFilterButtons.forEach(btn => btn.classList.remove('active'));
            }

            // Reset Dropdowns
            if (UI.elements.filterStatus) UI.elements.filterStatus.value = 'all';
            if (UI.elements.filterPriority) UI.elements.filterPriority.value = 'all';

            // Apply Filters (which will also reset member visibility)
            UI.applyFilters();
        });
    }
}

async function handleSaveTask() {
    if (!state.currentTaskItem) return;

    const taskId = state.currentTaskItem.dataset.id;
    const selectedTeam = UI.elements.taskTeam.value;
    const isArchiveSelected = selectedTeam === 'archive';

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
        project: UI.elements.projectNameInput.value.trim(),
        task: UI.elements.taskNameInput.value.trim(),
        members: UI.getSelectedMembers('taskModal'),
        status: UI.elements.taskStatus.value,
        priority: UI.elements.taskPriority.value,
        notes: UI.elements.taskNotes.value.trim(),
        team_id: isArchiveSelected ? null : (selectedTeam || null),
        start_date: Utils.parseDateToISO(startStr),
        end_date: Utils.parseDateToISO(endStr),
        is_archived: isArchiveSelected
    };

    try {
        const data = await API.updateTask(taskId, payload);
        if (data.success) {
            UI.closeModals();
            await UI.refreshContent(attachEventListeners);
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
    const isArchiveSelected = selectedTeam === 'archive'; // Usually not available for create, but safe check

    const payload = {
        project: UI.elements.createProjectNameInput.value.trim() || 'כללי',
        task: UI.elements.createTaskNameInput.value.trim(),
        members: UI.getSelectedMembers('createTaskModal'),
        status: UI.elements.createTaskStatus.value,
        priority: UI.elements.createTaskPriority.value,
        notes: UI.elements.createTaskNotes.value.trim(),
        team_id: isArchiveSelected ? null : (selectedTeam || null),
        start_date: Utils.parseDateToISO(startStr),
        end_date: Utils.parseDateToISO(endStr),
        is_archived: isArchiveSelected
    };

    try {
        const data = await API.createTask(payload);
        if (data.success) {
            UI.closeModals();
            await UI.refreshContent(attachEventListeners);
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
        // Do AJAX search
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
            UI.applyFilters(); // Re-apply to hide empty projects etc

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
    const mode = btn.dataset.mode || 'active'; // 'active' or 'archive'

    const url = new URL(window.location);

    if (mode === 'archive') {
        if (state.activeTeamFilter === 'archive') {
            // Toggle Off -> Go to last known active or all?
            // Reset to 'active' mode, no team filter
            url.searchParams.set('mode', 'active');
            url.searchParams.delete('team');
            setActiveTeamFilter(null);
            localStorage.removeItem('activeTeamFilter');
        } else {
            // Activate archive
            url.searchParams.set('mode', 'archive');
            url.searchParams.delete('team');
            setActiveTeamFilter('archive');
            localStorage.setItem('activeTeamFilter', 'archive');
        }
        window.history.pushState({}, '', url);
        await UI.refreshContent(attachEventListeners);
        return;
    }

    // Normal team click
    // If we were in archive mode, we must switch to active and refresh
    if (state.activeTeamFilter === 'archive') {
        url.searchParams.set('mode', 'active');
        url.searchParams.set('team', teamId);
        setActiveTeamFilter(teamId);
        localStorage.setItem('activeTeamFilter', teamId);

        window.history.pushState({}, '', url);
        await UI.refreshContent(attachEventListeners);
        return;
    }

    // Toggle logic for active team
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

    // Clear member filter when switching teams?
    // Optional, but often good UX.
    setActiveMemberFilter(null);

    UI.applyFilters();
}
