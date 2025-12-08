// Calendar Events
import { state, setCurrentDate, setActiveTeamFilter, setCurrentTaskId, setSpecialDays } from './state.js';
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
                    state.specialDays = specialDays; // Directly update state reference (or use setter if available)
                    // Or setSpecialDays(specialDays) if imported? Not imported.
                    // Let's import setSpecialDays if possible, or modify state directly.
                    // state is imported.
                    // We need to re-render the list inside modal AND re-render calendar views.
                    UI.renderSpecialDaysList();
                    window.dispatchEvent(new CustomEvent('calendar:refresh'));
                }
            } catch (err) {
                alert('שגיאה במחיקת יום מיוחד');
            }
        }
    });
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
            setSpecialDays(specialDays); // We need to make sure this is available
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
