// Calendar Events
import { state, setCurrentDate, setActiveTeamFilter, setCurrentTaskId, setSpecialDays, setStatusFilter, setPriorityFilter } from './state.js';
import * as UI from './ui.js';
import * as API from './api.js';
import { formatDateToISO, parseDateFromISO } from './utils.js';
import { renderCurrentView } from './main.js'; // We need access to re-render

export function attachEventListeners() {
    // View Toggle
    if (UI.elements.viewBtns) {
        UI.elements.viewBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const view = btn.dataset.view;
                window.dispatchEvent(new CustomEvent('calendar:switchView', { detail: { view } }));
            });
        });
    }

    // Navigation
    if (UI.elements.prevPeriodBtn) {
        UI.elements.prevPeriodBtn.addEventListener('click', () => navigatePeriod(-1));
    }
    if (UI.elements.nextPeriodBtn) {
        UI.elements.nextPeriodBtn.addEventListener('click', () => navigatePeriod(1));
    }
    if (UI.elements.todayBtn) {
        UI.elements.todayBtn.addEventListener('click', () => {
            setCurrentDate(new Date());
            window.dispatchEvent(new CustomEvent('calendar:refresh'));
        });
    }

    // Team Filter
    if (UI.elements.teamFilterBtns) {
        UI.elements.teamFilterBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const teamId = btn.dataset.teamId;
                if (state.activeTeamFilter === teamId) {
                    setActiveTeamFilter(null);
                    localStorage.removeItem('activeTeamFilter');
                    btn.classList.remove('active');
                } else {
                    setActiveTeamFilter(teamId);
                    localStorage.setItem('activeTeamFilter', teamId);
                    UI.elements.teamFilterBtns.forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                }
                window.dispatchEvent(new CustomEvent('calendar:refresh'));
            });
        });
    }

    // Status Filter
    if (UI.elements.filterStatus) {
        UI.elements.filterStatus.addEventListener('change', (e) => {
            setStatusFilter(e.target.value);
            window.dispatchEvent(new CustomEvent('calendar:refresh'));
        });
    }

    // Priority Filter
    if (UI.elements.filterPriority) {
        UI.elements.filterPriority.addEventListener('change', (e) => {
            setPriorityFilter(e.target.value);
            window.dispatchEvent(new CustomEvent('calendar:refresh'));
        });
    }

    // Clear All Filters
    if (UI.elements.clearFiltersBtn) {
        UI.elements.clearFiltersBtn.addEventListener('click', () => {
            // Reset State
            setActiveTeamFilter(null);
            setStatusFilter('all');
            setPriorityFilter('all');

            // Clear Local Storage
            localStorage.removeItem('activeTeamFilter');

            // Reset UI - Team Filters
            if (UI.elements.teamFilterBtns) {
                UI.elements.teamFilterBtns.forEach(btn => btn.classList.remove('active'));
            }

            // Reset Dropdowns
            if (UI.elements.filterStatus) UI.elements.filterStatus.value = 'all';
            if (UI.elements.filterPriority) UI.elements.filterPriority.value = 'all';

            // Refresh
            window.dispatchEvent(new CustomEvent('calendar:refresh'));
        });
    }

    // Task Modal - New
    if (UI.elements.closeTaskModalBtn) UI.elements.closeTaskModalBtn.addEventListener('click', UI.closeTaskModal);
    if (UI.elements.taskSaveBtn) UI.elements.taskSaveBtn.addEventListener('click', saveTask);
    if (UI.elements.taskDeleteBtn) UI.elements.taskDeleteBtn.addEventListener('click', deleteTaskHandler);

    // Schedule Modal (Legacy Support if elements still exist)
    if (UI.elements.closeModalBtn) UI.elements.closeModalBtn.addEventListener('click', UI.closeScheduleModal);
    if (UI.elements.scheduleCancelBtn) UI.elements.scheduleCancelBtn.addEventListener('click', UI.closeScheduleModal);

    // Special Days Modal links
    if (UI.elements.manageHolidaysBtn) {
        UI.elements.manageHolidaysBtn.addEventListener('click', UI.openSpecialDaysModal);
    }
    if (UI.elements.closeSpecialModalBtn) {
        UI.elements.closeSpecialModalBtn.addEventListener('click', UI.closeSpecialDaysModal);
    }
    const addSpecialDayBtn = document.getElementById('addSpecialDayBtn');
    if (addSpecialDayBtn) {
        addSpecialDayBtn.addEventListener('click', handleAddSpecialDay);
    }

    // Modal Background Click
    window.addEventListener('click', (e) => {
        if (UI.elements.scheduleModal && e.target === UI.elements.scheduleModal) UI.closeScheduleModal();
        if (UI.elements.taskModal && e.target === UI.elements.taskModal) UI.closeTaskModal();
        if (UI.elements.specialDaysModal && e.target === UI.elements.specialDaysModal) UI.closeSpecialDaysModal();
    });

    // Handle Delete Special Day custom event
    window.addEventListener('calendar:deleteSpecialDay', async (e) => {
        const id = e.detail.id;
        if (confirm('האם אתה בטוח שברצונך למחוק יום מיוחד זה?')) {
            try {
                const res = await API.deleteSpecialDay(id);
                if (res.success) {
                    // Refresh data
                    const specialDays = await API.fetchSpecialDays();
                    setSpecialDays(specialDays);
                    UI.renderSpecialDaysList();
                    window.dispatchEvent(new CustomEvent('calendar:refresh'));
                }
            } catch (err) {
                alert('שגיאה במחיקת יום מיוחד');
            }
        }
    });
}

function navigatePeriod(direction) {
    const d = new Date(state.currentDate);
    // 7 days jump
    d.setDate(d.getDate() + (direction * 7));
    setCurrentDate(d);
    window.dispatchEvent(new CustomEvent('calendar:refresh'));
}

async function handleAddSpecialDay() {
    const dateInput = document.getElementById('specialDayDate');
    const nameInput = document.getElementById('specialDayName');
    const typeInput = document.getElementById('specialDayType');

    if (!dateInput || !nameInput) return;

    // Convert dd/mm/yyyy to ISO
    const dateVal = dateInput.value;
    let isoDate = null;
    if (dateVal) {
        const parts = dateVal.split('/');
        if (parts.length === 3) isoDate = `${parts[2]}-${parts[1]}-${parts[0]}`;
    }

    if (!isoDate) {
        alert('נא להזין תאריך');
        return;
    }
    if (!nameInput.value.trim()) {
        alert('נא להזין שם');
        return;
    }

    try {
        const type = typeInput ? typeInput.value : 'holiday';
        const res = await API.addSpecialDay(isoDate, nameInput.value.trim(), type);

        if (res.success) {
            // Clear inputs
            dateInput.value = '';
            nameInput.value = '';

            // Refresh
            const specialDays = await API.fetchSpecialDays();
            setSpecialDays(specialDays);
            UI.renderSpecialDaysList();
            window.dispatchEvent(new CustomEvent('calendar:refresh'));
        } else {
            alert('שגיאה בהוספת יום מיוחד');
        }
    } catch (err) {
        console.error(err);
        alert('שגיאה בהוספת יום מיוחד');
    }
}

async function saveTask() {
    if (!state.currentTaskId) return;

    // Gather Data
    const teamId = UI.elements.taskTeam ? UI.elements.taskTeam.value : null;
    const project = UI.elements.taskProject ? UI.elements.taskProject.value : '';
    const taskName = UI.elements.taskName ? UI.elements.taskName.value : '';
    const status = UI.elements.taskStatus ? UI.elements.taskStatus.value : 'status-notstarted';
    const priority = UI.elements.taskPriority ? UI.elements.taskPriority.value : 'none';
    const notes = UI.elements.taskNotes ? UI.elements.taskNotes.value : '';

    // Dates (dd/mm/yyyy to ISO)
    const startDateInput = UI.elements.taskStartDate.value;
    const endDateInput = UI.elements.taskEndDate.value;
    let start_date = null;
    let end_date = null;

    if (startDateInput) {
        const parts = startDateInput.split('/');
        if (parts.length === 3) start_date = `${parts[2]}-${parts[1]}-${parts[0]}`;
    }
    if (endDateInput) {
        const parts = endDateInput.split('/');
        if (parts.length === 3) end_date = `${parts[2]}-${parts[1]}-${parts[0]}`;
    }

    // Members
    const selectedMembers = [];
    if (UI.elements.taskMembersContainer) {
        const checkboxes = UI.elements.taskMembersContainer.querySelectorAll('input[type="checkbox"]:checked');
        checkboxes.forEach(cb => selectedMembers.push(cb.value));
    }
    const taskData = {
        team_id: teamId,
        project: project,
        task: taskName,
        status: status,
        priority: priority,
        notes: notes,
        start_date: start_date,
        end_date: end_date,
        members: selectedMembers
    };

    try {
        const res = await API.updateTask(state.currentTaskId, taskData);
        if (res.success) {
            UI.closeTaskModal();
            window.dispatchEvent(new CustomEvent('calendar:refresh'));
        } else {
            alert('שגיאה בשמירת המשימה');
        }
    } catch (error) {
        console.error(error);
        alert('שגיאה בשמירת המשימה');
    }
}

async function deleteTaskHandler() {
    if (!state.currentTaskId) return;
    if (!confirm('האם אתה בטוח שברצונך למחוק משימה זו?')) return;

    try {
        const res = await API.deleteTask(state.currentTaskId);
        if (res.success) {
            UI.closeTaskModal();
            window.dispatchEvent(new CustomEvent('calendar:refresh'));
        } else {
            alert('שגיאה במחיקת המשימה');
        }
    } catch (error) {
        console.error(error);
        alert('שגיאה במחיקת המשימה');
    }
}

// Drag & Drop
export function handleDragStart(e) {
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', e.target.dataset.taskId);
    e.target.classList.add('dragging');
}

export function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
}

export async function handleDrop(e) {
    e.preventDefault();
    const taskId = e.dataTransfer.getData('text/plain');
    const col = e.target.closest('.calendar-day-column');
    const newDate = col ? col.dataset.date : null;

    if (taskId && newDate) {
        try {
            const response = await fetch(`/api/tasks/${taskId}/schedule`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ start_date: newDate })
            });
            const res = await response.json();

            if (res.success) {
                window.dispatchEvent(new CustomEvent('calendar:refresh'));
            }
        } catch (err) {
            console.error(err);
        }
    }

    document.querySelectorAll('.dragging').forEach(el => el.classList.remove('dragging'));
}
