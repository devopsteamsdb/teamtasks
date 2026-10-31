// Calendar Events
import { state, setCurrentDate, setActiveTeamFilter, setCurrentTaskId, setSpecialDays, setStatusFilter, setPriorityFilter } from './state.js';
import * as UI from './ui.js';
import * as API from './api.js';
import { formatDateToISO, parseDateFromISO } from './utils.js';
import { renderCurrentView } from './main.js'; // We need access to re-render
import { notifyDataChanged } from '../live_sync.js';
import { createSubtask, updateSubtask, deleteSubtask, createTaskComment, deleteTaskComment } from '../api.js';

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
            const val = e.target.value;
            setStatusFilter(val);
            if (val && val !== 'all') {
                localStorage.setItem('activeStatusFilter', val);
            } else {
                localStorage.removeItem('activeStatusFilter');
            }
            window.dispatchEvent(new CustomEvent('calendar:refresh'));
        });
    }

    // Priority Filter
    if (UI.elements.filterPriority) {
        UI.elements.filterPriority.addEventListener('change', (e) => {
            const val = e.target.value;
            setPriorityFilter(val);
            if (val && val !== 'all') {
                localStorage.setItem('activePriorityFilter', val);
            } else {
                localStorage.removeItem('activePriorityFilter');
            }
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
            localStorage.removeItem('activeMemberFilter');
            localStorage.removeItem('activeStatusFilter');
            localStorage.removeItem('activePriorityFilter');

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

    // Subtasks & Comments in Calendar Modal
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

    if (UI.elements.addCommentBtn) {
        UI.elements.addCommentBtn.onclick = handleAddComment;
    }
    if (UI.elements.commentsList) {
        UI.elements.commentsList.onclick = handleCommentListClick;
    }

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
                    notifyDataChanged();
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
        const parts = dateVal.trim().replace(/[\.\-]/g, '/').split('/');
        if (parts.length === 3) {
            isoDate = `${parts[2].trim()}-${parts[1].trim().padStart(2, '0')}-${parts[0].trim().padStart(2, '0')}`;
        }
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
            notifyDataChanged();
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
        const parts = startDateInput.trim().replace(/[\.\-]/g, '/').split('/');
        if (parts.length === 3) {
            start_date = `${parts[2].trim()}-${parts[1].trim().padStart(2, '0')}-${parts[0].trim().padStart(2, '0')}`;
        }
    }
    if (endDateInput) {
        const parts = endDateInput.trim().replace(/[\.\-]/g, '/').split('/');
        if (parts.length === 3) {
            end_date = `${parts[2].trim()}-${parts[1].trim().padStart(2, '0')}-${parts[0].trim().padStart(2, '0')}`;
        }
    }

    if (start_date && end_date && start_date > end_date) {
        alert('תאריך ההתחלה לא יכול להיות מאוחר מתאריך הסיום');
        return;
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
            notifyDataChanged();
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
            notifyDataChanged();
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
                notifyDataChanged();
            }
        } catch (err) {
            console.error(err);
        }
    }

    document.querySelectorAll('.dragging').forEach(el => el.classList.remove('dragging'));
}

// Subtasks & Comments Event Handlers for Calendar
async function handleAddSubtask() {
    const taskId = state.currentTaskId;
    if (!taskId) return;
    const input = UI.elements.newSubtaskInput;
    if (!input) return;
    const title = input.value.trim();
    if (!title) return;

    try {
        const res = await createSubtask(taskId, title);
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
    const taskId = state.currentTaskId;
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
            await updateSubtask(subtaskId, { is_completed: isCompleted });
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
            const res = await deleteSubtask(subtaskId);
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
    const taskId = state.currentTaskId;
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
        const res = await createTaskComment(taskId, payload);
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
    const taskId = state.currentTaskId;
    if (!taskId) return;

    const deleteBtn = e.target.closest('.comment-delete-btn');
    if (deleteBtn) {
        e.stopPropagation();
        if (!confirm('האם למחוק תגובה זו?')) return;
        const commentId = deleteBtn.dataset.id;
        try {
            const res = await deleteTaskComment(commentId);
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
