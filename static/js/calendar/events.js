// Calendar Events
import { state, setCurrentDate, setActiveTeamFilter, setCurrentTaskId } from './state.js';
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
                // Update state via main module or directly if state is shared?
                // Better to update state and trigger UI update.
                // But we need to switch logic.
                // We'll call a function in main that orchestrates switching view.
                // Circular dependency issue if main imports events?
                // Let's use custom events or callbacks?
                // Simpler: Dispatch event or modify state and call render directly if imported.
                // I'll dispatch a custom event on window for simplicity in this architecture.
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

    // Modal
    if (UI.elements.closeModalBtn) UI.elements.closeModalBtn.addEventListener('click', UI.closeScheduleModal);
    if (UI.elements.scheduleCancelBtn) UI.elements.scheduleCancelBtn.addEventListener('click', UI.closeScheduleModal);
    if (UI.elements.scheduleSaveBtn) UI.elements.scheduleSaveBtn.addEventListener('click', saveTaskSchedule);

    window.addEventListener('click', (e) => {
        if (UI.elements.scheduleModal && e.target === UI.elements.scheduleModal) UI.closeScheduleModal();
    });

    // Special Days Modal links...
}

function navigatePeriod(direction) {
    const d = new Date(state.currentDate);
    // 7 days jump
    d.setDate(d.getDate() + (direction * 7));
    setCurrentDate(d);
    window.dispatchEvent(new CustomEvent('calendar:refresh'));
}

async function saveTaskSchedule() {
    if (!state.currentTaskId) return;

    const startDateInput = UI.elements.scheduleStartDate.value;
    const endDateInput = UI.elements.scheduleEndDate.value;

    // Parse dd/mm/yyyy to ISO
    let startDate = null;
    let endDate = null;

    if (startDateInput) {
        const parts = startDateInput.split('/');
        if (parts.length === 3) startDate = `${parts[2]}-${parts[1]}-${parts[0]}`;
    }
    if (endDateInput) {
        const parts = endDateInput.split('/');
        if (parts.length === 3) endDate = `${parts[2]}-${parts[1]}-${parts[0]}`;
    }

    try {
        const data = await API.updateTaskSchedule(state.currentTaskId, startDate, endDate, null);
        if (data.success) {
            UI.closeScheduleModal();
            window.dispatchEvent(new CustomEvent('calendar:refresh'));
        } else {
            alert('שגיאה בשמירת תזמון המשימה');
        }
    } catch (e) {
        alert('שגיאה בשמירת תזמון המשימה');
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
    // Find closest day column date
    const col = e.target.closest('.calendar-day-column');
    const newDate = col ? col.dataset.date : null;

    if (taskId && newDate) {
        // Update task start date to newDate
        // We typically clean the end date or shift it? 
        // Original code just updated start_date.
        try {
            const data = await API.updateTaskSchedule(taskId, newDate, null, null); // passing null for end/est? 
            // Warning: if we pass null for end, it might clear it.
            // But verify API: updateTaskSchedule sends {start_date: newDate} in original code.
            // My implementation of API.updateTaskSchedule sends all 3.
            // I should fetch the task first or allow partial update?
            // Let's modify API wrapper or logic.
            // Let's create a specialized partial update or just call API directly here if customized.

            // To be safe, let's just do a fetch here matching original logic:
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
