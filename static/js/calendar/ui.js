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

    elements.scheduleModal = document.getElementById('scheduleModal');
    elements.closeModalBtn = elements.scheduleModal ? elements.scheduleModal.querySelector('.close-modal') : null;
    elements.scheduleSaveBtn = document.getElementById('scheduleSaveBtn');
    elements.scheduleCancelBtn = document.getElementById('scheduleCancelBtn');

    // Inputs
    elements.scheduleTaskName = document.getElementById('scheduleTaskName');
    elements.scheduleStartDate = document.getElementById('scheduleStartDate');
    elements.scheduleEndDate = document.getElementById('scheduleEndDate');

    // Special Days
    elements.specialDaysModal = document.getElementById('specialDaysModal');
    elements.manageHolidaysBtn = document.getElementById('manageHolidaysBtn');
    elements.closeSpecialModalBtn = elements.specialDaysModal ? elements.specialDaysModal.querySelector('.close-modal') : null;
}

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
        // Workload data from API structure: { workload: [...] } which sets state.tasks to array
        // But let's verify
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
                if (task.is_archived) {
                    taskBlock.style.opacity = '0.5';
                    taskBlock.style.border = '1px dashed #666';
                    taskBlock.title = '[ארכיון] ' + task.task;
                } else {
                    taskBlock.title = task.task;
                }

                // Truncate
                taskBlock.textContent = task.task.substring(0, 30) + (task.task.length > 30 ? '...' : '');

                // Click
                taskBlock.style.cursor = 'pointer';
                taskBlock.onclick = (e) => {
                    e.stopPropagation();
                    openScheduleModal(task);
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

    card.addEventListener('click', () => openScheduleModal(task));
    card.addEventListener('dragstart', Events.handleDragStart);

    return card;
}

export function openScheduleModal(task) {
    setCurrentTaskId(task.id);
    elements.scheduleTaskName.value = task.task;
    elements.scheduleStartDate.value = parseDateFromISO(task.start_date) || '';
    elements.scheduleEndDate.value = parseDateFromISO(task.end_date) || '';

    elements.scheduleModal.style.display = 'block';
}

export function closeScheduleModal() {
    if (elements.scheduleModal) elements.scheduleModal.style.display = 'none';
}
