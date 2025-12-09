// Calendar UI
import { state, setCurrentTaskId } from './state.js';
import { hebrewDays, hebrewMonths, priorityColors } from './constants.js';
import { getWeekStart, formatDateToISO, formatDateDisplay, parseDateFromISO } from './utils.js';
import * as Events from './events.js'; // Circular dependency risk? Events uses UI, UI might need Events for attaching listener logic?
// Better to pass callbacks or function references.

// DOM Elements Cache
export const elements = {};

export function updateDOMElements() {
    elements.periodTitle = document.getElementById('periodTitle');
    elements.prevPeriodBtn = document.getElementById('prevPeriod');
    elements.nextPeriodBtn = document.getElementById('nextPeriod');
    elements.todayBtn = document.getElementById('todayBtn');
    elements.viewBtns = document.querySelectorAll('.view-btn');
    elements.teamFilterBtns = document.querySelectorAll('.filter-team-btn');

    elements.weekView = document.getElementById('weekView');
    elements.workloadView = document.getElementById('workloadView');

    // Task Modal
    elements.taskModal = document.getElementById('taskModal');
    elements.closeTaskModalBtn = elements.taskModal ? elements.taskModal.querySelector('.close-modal') : null;
    elements.taskSaveBtn = document.getElementById('saveBtn'); // Note IDs from copied HTML
    elements.taskDeleteBtn = document.getElementById('deleteBtn');

    // Task Inputs
    elements.taskTeam = document.getElementById('taskTeam');
    elements.taskProject = document.getElementById('projectNameInput');
    elements.taskName = document.getElementById('taskNameInput');
    elements.taskStatus = document.getElementById('taskStatus');
    elements.taskPriority = document.getElementById('taskPriority');
    elements.taskStartDate = document.getElementById('taskStartDate');
    elements.taskEndDate = document.getElementById('taskEndDate');
    elements.taskNotes = document.getElementById('taskNotes');
    elements.taskMembersContainer = elements.taskModal ? elements.taskModal.querySelector('.members-select') : null;

    // Keep old references just in case, or remove if unused
    elements.scheduleModal = document.getElementById('scheduleModal');

    // Special Days
    elements.specialDaysModal = document.getElementById('specialDaysModal');
    elements.manageHolidaysBtn = document.getElementById('manageHolidaysBtn');
    elements.closeSpecialModalBtn = elements.specialDaysModal ? elements.specialDaysModal.querySelector('.close-modal') : null;
}

export function initializeFlatpickr() {
    const config = {
        dateFormat: "d/m/Y",
        allowInput: true,
        locale: "he"
    };

    if (elements.taskStartDate) flatpickr(elements.taskStartDate, config);
    if (elements.taskEndDate) flatpickr(elements.taskEndDate, config);

    // Also init for Special Days
    const specialDayParams = { ...config };
    const specialDayInput = document.getElementById('specialDayDate');
    if (specialDayInput) flatpickr(specialDayInput, specialDayParams);
}

// ... existing switchView ...
export function switchView(newView) {
    if (!elements.weekView || !elements.workloadView) return;

    elements.weekView.classList.remove('active');
    elements.workloadView.classList.remove('active');

    if (newView === 'week') {
        elements.weekView.classList.add('active');
    } else if (newView === 'workload') {
        elements.workloadView.classList.add('active');
    }

    // Update buttons
    elements.viewBtns.forEach(btn => {
        if (btn.dataset.view === newView) btn.classList.add('active');
        else btn.classList.remove('active');
    });
}

// ... existing renderWeekView ...
export function renderWeekView() {
    if (!elements.periodTitle || !elements.weekView) return;

    const weekStart = getWeekStart(state.currentDate);
    const weekEnd = new Date(weekStart);
    weekEnd.setDate(weekEnd.getDate() + 6); // 7 days

    // Update title
    elements.periodTitle.textContent = `${formatDateDisplay(weekStart)} - ${formatDateDisplay(weekEnd)}`;

    // Build grid
    const grid = elements.weekView.querySelector('.calendar-week-grid');
    if (!grid) return;
    grid.innerHTML = '';

    for (let i = 0; i < 5; i++) { // 5 work days
        const day = new Date(weekStart);
        day.setDate(day.getDate() + i);

        const dayColumn = document.createElement('div');
        dayColumn.className = 'calendar-day-column';
        const dayIso = formatDateToISO(day);
        dayColumn.dataset.date = dayIso;

        // Header
        const dayHeader = document.createElement('div');
        dayHeader.className = 'calendar-day-header';

        dayHeader.innerHTML = `
            <div class="day-name">${hebrewDays[day.getDay()]}</div>
            <div class="day-number">${formatDateDisplay(day)}</div>
        `;

        // Special day
        const specialDay = state.specialDays.find(sd => sd.date === dayIso);
        if (specialDay) {
            dayHeader.classList.add('special-day');
            const label = document.createElement('span');
            label.className = 'special-day-label';
            label.textContent = specialDay.name;
            dayHeader.appendChild(label);
        }

        dayColumn.appendChild(dayHeader);

        // Tasks
        const dayTasks = document.createElement('div');
        dayTasks.className = 'calendar-day-tasks';

        const tasksForDay = state.tasks.filter(task => {
            if (!task.start_date) return false;
            // Display logic: show if task falls on this day
            return task.start_date === dayIso || (task.end_date && task.start_date <= dayIso && task.end_date >= dayIso);
        });

        tasksForDay.forEach(task => {
            const taskCard = createTaskCard(task);
            dayTasks.appendChild(taskCard);
        });

        dayColumn.appendChild(dayTasks);
        grid.appendChild(dayColumn);

        // Drag events
        dayColumn.addEventListener('dragover', Events.handleDragOver);
        dayColumn.addEventListener('drop', Events.handleDrop);
    }
}

// ... existing renderWorkloadView ...
export function renderWorkloadView() {
    if (!elements.periodTitle || !elements.workloadView) return;

    const weekStart = getWeekStart(state.currentDate);
    const weekEnd = new Date(weekStart);
    weekEnd.setDate(weekEnd.getDate() + 4); // 5 days

    elements.periodTitle.textContent = `חברי צוות: ${formatDateDisplay(weekStart)} - ${formatDateDisplay(weekEnd)}`;

    const container = elements.workloadView.querySelector('.workload-container');
    if (!container) return;
    container.innerHTML = '';

    if (!Array.isArray(state.tasks)) {
        console.error('Workload data invalid');
        return;
    }

    // Header Row
    const headerRow = document.createElement('div');
    headerRow.className = 'workload-header-row';

    const headerLabel = document.createElement('div');
    headerLabel.className = 'workload-member-info';
    headerLabel.innerHTML = '<span style="font-weight: 600;">חבר צוות</span>';
    headerRow.appendChild(headerLabel);

    const headerTimeline = document.createElement('div');
    headerTimeline.className = 'workload-timeline';

    for (let i = 0; i < 5; i++) {
        const day = new Date(weekStart);
        day.setDate(day.getDate() + i);
        const dayHeader = document.createElement('div');
        dayHeader.className = 'workload-day-header';

        dayHeader.innerHTML = `
            <div style="font-weight: 600; font-size: 0.9rem;">${hebrewDays[day.getDay()]}</div>
            <div style="font-size: 0.8rem; color: #6B7280;">${formatDateDisplay(day)}</div>
        `;

        const dayIso = formatDateToISO(day);
        const specialDay = state.specialDays.find(sd => sd.date === dayIso);
        if (specialDay) {
            dayHeader.classList.add('special-day');
            const label = document.createElement('div');
            label.style.fontSize = '0.7rem';
            label.style.color = '#B45309';
            label.textContent = specialDay.name;
            dayHeader.appendChild(label);
        }

        headerTimeline.appendChild(dayHeader);
    }
    headerRow.appendChild(headerTimeline);
    container.appendChild(headerRow);

    // Member Rows
    state.tasks.forEach(memberData => {
        const memberRow = document.createElement('div');
        memberRow.className = 'workload-member-row';

        const memberInfo = document.createElement('div');
        memberInfo.className = 'workload-member-info';
        memberInfo.innerHTML = `
            <img src="/uploads/avatars/${memberData.member.avatar_path}" class="workload-avatar"
                onerror="this.src='/static/images/default.png'">
            <span class="workload-member-name">${memberData.member.name_he}</span>
        `;
        memberRow.appendChild(memberInfo);

        const timeline = document.createElement('div');
        timeline.className = 'workload-timeline';

        for (let i = 0; i < 5; i++) {
            const day = new Date(weekStart);
            day.setDate(day.getDate() + i);
            const dayStr = formatDateToISO(day);

            const dayCell = document.createElement('div');
            dayCell.className = 'workload-day-cell';
            dayCell.dataset.date = dayStr;

            const specialDay = state.specialDays.find(sd => sd.date === dayStr);
            if (specialDay) dayCell.classList.add('special-day');

            const tasksForDay = memberData.tasks.filter(task => {
                if (!task.start_date) return false;
                return task.start_date === dayStr || (task.end_date && task.start_date <= dayStr && task.end_date >= dayStr);
            });

            tasksForDay.forEach(task => {
                const taskBlock = document.createElement('div');
                taskBlock.className = 'workload-task-block';
                taskBlock.style.backgroundColor = priorityColors[task.priority || 'none'];

                // Better visibility for low priority (yellow background needs dark text)
                if ((task.priority || 'none') === 'low') {
                    taskBlock.style.color = '#1f2937'; // Dark Slate
                }

                if (task.is_archived) {
                    taskBlock.style.opacity = '0.5';
                    taskBlock.style.border = '1px dashed #666';
                    taskBlock.title = `[ארכיון] ${task.task}\nפרויקט: ${task.project}`;
                } else {
                    taskBlock.title = `${task.task}\nפרויקט: ${task.project}`;
                }

                // Truncate
                taskBlock.textContent = task.task.substring(0, 30) + (task.task.length > 30 ? '...' : '');

                // Click - use openTaskModal
                taskBlock.style.cursor = 'pointer';
                taskBlock.onclick = (e) => {
                    e.stopPropagation();
                    openTaskModal(task);
                };

                dayCell.appendChild(taskBlock);
            });

            timeline.appendChild(dayCell);
        }
        memberRow.appendChild(timeline);
        container.appendChild(memberRow);
    });
}

export function createTaskCard(task) {
    const card = document.createElement('div');
    card.className = 'calendar-task-card';
    card.draggable = true;
    card.dataset.taskId = task.id;
    card.style.borderRight = `4px solid ${priorityColors[task.priority || 'none']}`;

    card.innerHTML = `
        <div class="task-card-name">${task.task}</div>
        <div class="task-card-project">${task.project}</div>
    `;

    card.addEventListener('click', () => openTaskModal(task));
    card.addEventListener('dragstart', Events.handleDragStart);

    return card;
}

export function openTaskModal(task) {
    setCurrentTaskId(task.id);

    // Populate simple fields
    if (elements.taskProject) elements.taskProject.value = task.project;
    if (elements.taskName) elements.taskName.value = task.task;
    if (elements.taskStatus) elements.taskStatus.value = task.status;
    if (elements.taskPriority) elements.taskPriority.value = task.priority || 'none';
    if (elements.taskNotes) elements.taskNotes.value = task.notes || '';

    // Dates
    if (elements.taskStartDate) elements.taskStartDate.value = parseDateFromISO(task.start_date) || '';
    if (elements.taskEndDate) elements.taskEndDate.value = parseDateFromISO(task.end_date) || '';

    // Populate Teams and Members
    populateTaskModalDropdowns(task);

    if (elements.taskModal) elements.taskModal.style.display = 'block';
}

function populateTaskModalDropdowns(task) {
    if (!state.teams || !state.members) return;

    // Team Select
    if (elements.taskTeam) {
        elements.taskTeam.innerHTML = '';
        state.teams.forEach(team => {
            const option = document.createElement('option');
            option.value = team.id;
            option.textContent = team.name_he;
            if (task.team_id == team.id) option.selected = true;
            elements.taskTeam.appendChild(option);
        });
        // We do NOT update members on team change anymore, as all members are shown.
    }

    // Initial render of members (All members)
    renderMembersCheckboxes(task.members || []);
}

function renderMembersCheckboxes(selectedNames) {
    if (!elements.taskMembersContainer) return;

    // Show all members
    const allMembers = state.members;

    elements.taskMembersContainer.innerHTML = allMembers.map(member => `
        <label class="member-checkbox" title="${member.name_he} - ${member.team_name}">
            <input type="checkbox" value="${member.name_en}" 
                ${selectedNames && selectedNames.includes(member.name_en) ? 'checked' : ''}
                id="member-${member.id}">
            <img src="/uploads/avatars/${member.avatar_path}" class="avatar-sm"
                onerror="this.src='/static/images/default.png'">
            ${member.name_he}
        </label>
    `).join('');
}

export function closeTaskModal() {
    if (elements.taskModal) elements.taskModal.style.display = 'none';
}

// Special Days UI
export function openSpecialDaysModal() {
    if (elements.specialDaysModal) {
        elements.specialDaysModal.style.display = 'block';
        renderSpecialDaysList();
    }
}

export function closeSpecialDaysModal() {
    if (elements.specialDaysModal) elements.specialDaysModal.style.display = 'none';
}

export function renderSpecialDaysList() {
    const listContainer = document.getElementById('specialDaysList');
    if (!listContainer) return;

    listContainer.innerHTML = '';

    if (!state.specialDays || state.specialDays.length === 0) {
        listContainer.innerHTML = '<div style="text-align:center; color:#6b7280; padding:1rem;">אין ימים מיוחדים מוגדרים</div>';
        return;
    }

    // Sort by date
    const sortedDays = [...state.specialDays].sort((a, b) => a.date.localeCompare(b.date));

    sortedDays.forEach(day => {
        const item = document.createElement('div');
        item.className = 'special-day-item';
        item.style.cssText = 'display:flex; justify-content:space-between; align-items:center; padding:0.5rem; border-bottom:1px solid #e5e7eb;';

        const info = document.createElement('div');
        info.innerHTML = `<strong>${parseDateFromISO(day.date)}</strong> - ${day.name} <span style="font-size:0.8rem; color:#6b7280;">(${getDayTypeLabel(day.type)})</span>`;

        const actions = document.createElement('div');
        const deleteBtn = document.createElement('button');
        deleteBtn.innerHTML = '&times;';
        deleteBtn.style.cssText = 'background:none; border:none; color:#ef4444; font-size:1.2rem; cursor:pointer;';
        deleteBtn.title = 'מחק';
        deleteBtn.dataset.id = day.id;

        deleteBtn.addEventListener('click', () => {
            // Dispatch event to handle delete
            const event = new CustomEvent('calendar:deleteSpecialDay', { detail: { id: day.id } });
            window.dispatchEvent(event);
        });

        actions.appendChild(deleteBtn);
        item.appendChild(info);
        item.appendChild(actions);
        listContainer.appendChild(item);
    });
}

function getDayTypeLabel(type) {
    const types = {
        'holiday': 'חג',
        'company_event': 'אירוע חברה',
        'other': 'אחר'
    };
    return types[type] || type;
}
