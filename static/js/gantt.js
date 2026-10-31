// Gantt Chart Module
import { state } from './state.js';
import * as API from './api.js';
import { notifyDataChanged } from './live_sync.js';

const HEBREW_DAYS = ['א\'', 'ב\'', 'ג\'', 'ד\'', 'ה\'', 'ו\'', 'ש\''];
const HEBREW_MONTHS = ['ינואר', 'פברואר', 'מרץ', 'אפריל', 'מאי', 'יוני', 'יולי', 'אוגוסט', 'ספטמבר', 'אוקטובר', 'נובמבר', 'דצמבר'];

const PRIORITY_COLORS = {
    'high': '#ef4444',
    'medium': '#f59e0b',
    'low': '#eab308',
    'none': '#cbd5e1'
};

const STATUS_COLORS = {
    'status-notstarted': '#64748b',
    'status-inprogress': '#4f46e5',
    'status-delayed': '#ea580c',
    'status-done': '#10b981'
};

const STATUS_LABELS = {
    'status-notstarted': 'טרם החל',
    'status-inprogress': 'בתהליך',
    'status-delayed': 'מעוכב',
    'status-done': 'הושלם'
};

const DAYS_COUNT = 28; // 4 weeks window
let ganttStartDate = getDefaultStartDate();
let isFetchingSpecialDays = false;

export function truncateBarTitle(title, spanDays) {
    if (!title) return '';
    const clean = title.trim();
    if (spanDays <= 1) {
        return clean.length > 4 ? clean.slice(0, 3) + '..' : clean;
    } else if (spanDays === 2) {
        return clean.length > 8 ? clean.slice(0, 7) + '..' : clean;
    } else if (spanDays === 3) {
        return clean.length > 14 ? clean.slice(0, 12) + '..' : clean;
    } else if (spanDays <= 5) {
        return clean.length > 24 ? clean.slice(0, 22) + '..' : clean;
    }
    return clean;
}

function getDefaultStartDate() {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const day = today.getDay(); // 0 is Sunday
    const start = new Date(today);
    // Start on Sunday 7 days ago to give historical context and forward view
    start.setDate(today.getDate() - day - 7);
    return start;
}

export function prevPeriod() {
    ganttStartDate.setDate(ganttStartDate.getDate() - 14);
    renderGantt();
}

export function nextPeriod() {
    ganttStartDate.setDate(ganttStartDate.getDate() + 14);
    renderGantt();
}

export function resetToToday() {
    ganttStartDate = getDefaultStartDate();
    renderGantt();
}

export function getDateForDayIndex(dayIndex) {
    const d = new Date(ganttStartDate);
    d.setDate(ganttStartDate.getDate() + dayIndex);
    d.setHours(0, 0, 0, 0);
    return d;
}

export function formatDateISO(d) {
    if (!d) return '';
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
}

export function formatDateDisp(d) {
    if (!d) return '';
    return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}`;
}

let activeTooltip = null;

function showDragTooltip(text, x, y) {
    if (!activeTooltip) {
        activeTooltip = document.createElement('div');
        activeTooltip.className = 'gantt-drag-tooltip';
        document.body.appendChild(activeTooltip);
    }
    activeTooltip.textContent = text;
    activeTooltip.style.left = `${x}px`;
    activeTooltip.style.top = `${y - 38}px`;
    activeTooltip.style.display = 'block';
}

function hideDragTooltip() {
    if (activeTooltip) {
        activeTooltip.style.display = 'none';
    }
}

export async function updateTaskDates(taskId, startStr, endStr) {
    if (!taskId || !startStr || !endStr) return;

    // 1. Immediate DOM update across all views (Gantt, Kanban, Projects Grid)
    const items = document.querySelectorAll(`.task-item[data-id="${taskId}"]`);
    items.forEach(el => {
        el.dataset.startDate = startStr;
        el.dataset.endDate = endStr;

        const dateBadge = el.querySelector('.kanban-date-badge');
        const startParts = startStr ? startStr.split('-') : null;
        const endParts = endStr ? endStr.split('-') : null;
        let disp = '';
        let tip = '';

        if (startParts && endParts) {
            const startDisp = `${startParts[2]}/${startParts[1]}`;
            const endDisp = `${endParts[2]}/${endParts[1]}`;
            disp = (startStr === endStr) ? endDisp : `${startDisp} - ${endDisp}`;
            tip = (startStr === endStr)
                ? `תאריך: ${endParts[2]}/${endParts[1]}/${endParts[0]}`
                : `תאריכים: ${startParts[2]}/${startParts[1]}/${startParts[0]} - ${endParts[2]}/${endParts[1]}/${endParts[0]}`;
        } else if (endParts) {
            disp = `${endParts[2]}/${endParts[1]}`;
            tip = `יעד: ${endParts[2]}/${endParts[1]}/${endParts[0]}`;
        } else if (startParts) {
            disp = `${startParts[2]}/${startParts[1]}`;
            tip = `התחלה: ${startParts[2]}/${startParts[1]}/${startParts[0]}`;
        }

        if (dateBadge) {
            dateBadge.classList.remove('no-date');
            dateBadge.setAttribute('title', tip);
            const span = dateBadge.querySelector('span');
            if (span) {
                span.textContent = disp;
                span.setAttribute('dir', 'ltr');
            }
        } else {
            const badgesContainer = el.querySelector('.kanban-card-badges');
            if (badgesContainer && disp) {
                const badge = document.createElement('span');
                badge.className = 'kanban-date-badge';
                badge.setAttribute('title', tip);
                badge.innerHTML = `
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                    <span dir="ltr">${disp}</span>
                `;
                badgesContainer.appendChild(badge);
            }
        }
    });

    // 2. Re-render Gantt immediately
    renderGantt();

    // 3. Persist to API
    try {
        await API.updateTask(taskId, {
            start_date: startStr,
            end_date: endStr
        });
        notifyDataChanged();
    } catch (err) {
        console.error('Failed to update task dates:', err);
    }
}

export function renderGantt() {
    const container = document.getElementById('ganttChartBody');
    const titleElem = document.getElementById('ganttPeriodTitle');
    if (!container) return;

    // Asynchronously fetch special days if not present yet
    if ((!state.specialDays || state.specialDays.length === 0) && !isFetchingSpecialDays) {
        isFetchingSpecialDays = true;
        API.fetchSpecialDays().then(days => {
            isFetchingSpecialDays = false;
            if (Array.isArray(days) && days.length > 0) {
                state.specialDays = days;
                renderGantt();
            }
        }).catch(() => {
            isFetchingSpecialDays = false;
        });
    }

    // Special days mapping by ISO date (YYYY-MM-DD)
    const specialDaysMap = {};
    (state.specialDays || []).forEach(sd => {
        if (!sd.date) return;
        const dateKey = typeof sd.date === 'string' ? sd.date.slice(0, 10) : formatDateISO(new Date(sd.date));
        if (!specialDaysMap[dateKey]) {
            specialDaysMap[dateKey] = [];
        }
        specialDaysMap[dateKey].push(sd);
    });

    // Calculate window dates
    const dates = [];
    for (let i = 0; i < DAYS_COUNT; i++) {
        const d = new Date(ganttStartDate);
        d.setDate(ganttStartDate.getDate() + i);
        dates.push(d);
    }

    const firstDate = dates[0];
    const lastDate = dates[dates.length - 1];

    if (titleElem) {
        const m1 = HEBREW_MONTHS[firstDate.getMonth()];
        const m2 = HEBREW_MONTHS[lastDate.getMonth()];
        const y1 = firstDate.getFullYear();
        const y2 = lastDate.getFullYear();
        if (m1 === m2 && y1 === y2) {
            titleElem.textContent = `${m1} ${y1}`;
        } else if (y1 === y2) {
            titleElem.textContent = `${m1} - ${m2} ${y1}`;
        } else {
            titleElem.textContent = `${m1} ${y1} - ${m2} ${y2}`;
        }
    }

    // Collect visible tasks from the DOM
    const rawCards = Array.from(document.querySelectorAll('.kanban-card'));
    const sourceElements = rawCards.length > 0 ? rawCards : Array.from(document.querySelectorAll('.projects-grid .task-item'));

    const visibleTasks = [];
    sourceElements.forEach(el => {
        if (el.classList.contains('filtered-hidden') || el.classList.contains('search-hidden')) {
            return;
        }

        const taskId = el.dataset.id;
        let taskName = el.dataset.taskName || '';
        if (!taskName && el.querySelector('.task-name')) {
            taskName = el.querySelector('.task-name').textContent.trim();
        }
        if (!taskName) {
            const gridMatch = document.querySelector(`.projects-grid .task-item[data-id="${taskId}"] .task-name`);
            if (gridMatch) {
                taskName = gridMatch.textContent.trim();
            }
        }
        if (!taskName) {
            taskName = el.getAttribute('title') || `משימה #${taskId}`;
        }

        const project = el.dataset.project || (el.closest('.project-card') ? (el.closest('.project-card').dataset.projectName || '') : '');
        const status = el.dataset.status || 'status-notstarted';
        const priority = el.dataset.priority || 'none';
        const startStr = el.dataset.startDate;
        const endStr = el.dataset.endDate;

        // Subtask data
        const subtaskBadge = el.querySelector('.subtask-badge span');
        let subtasksText = '';
        let subtasksPercent = 0;
        if (subtaskBadge) {
            subtasksText = subtaskBadge.textContent.trim();
            const parts = subtasksText.split('/');
            if (parts.length === 2) {
                const done = parseInt(parts[0], 10) || 0;
                const tot = parseInt(parts[1], 10) || 0;
                if (tot > 0) subtasksPercent = Math.min(100, Math.round((done / tot) * 100));
            }
        }

        // Avatars
        const avatars = Array.from(el.querySelectorAll('.avatar')).map(img => ({
            src: img.getAttribute('src'),
            title: img.getAttribute('title') || ''
        }));

        visibleTasks.push({
            id: taskId,
            name: taskName,
            task: taskName,
            title: taskName,
            project: project || 'כללי',
            status: status,
            priority: priority,
            startDate: startStr ? new Date(startStr + 'T00:00:00') : null,
            endDate: endStr ? new Date(endStr + 'T00:00:00') : null,
            subtasksText: subtasksText,
            subtasksPercent: subtasksPercent,
            avatars: avatars,
            domElement: el
        });
    });

    if (visibleTasks.length === 0) {
        container.innerHTML = `
            <div class="gantt-empty-state">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="4" y1="6" x2="16" y2="6"></line><line x1="8" y1="12" x2="20" y2="12"></line><line x1="6" y1="18" x2="14" y2="18"></line>
                </svg>
                <p>אין משימות להצגה בסינון הנוכחי</p>
            </div>
        `;
        return;
    }

    // Group tasks by project
    const projectsMap = {};
    visibleTasks.forEach(t => {
        if (!projectsMap[t.project]) {
            projectsMap[t.project] = [];
        }
        projectsMap[t.project].push(t);
    });

    // Check today date
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // Build Table Header
    let daysHeaderHtml = '';
    dates.forEach((d) => {
        const isoDate = formatDateISO(d);
        const isToday = (d.getTime() === today.getTime());
        const isWeekend = (d.getDay() === 5 || d.getDay() === 6);
        const dayLetter = HEBREW_DAYS[d.getDay()];
        const dateDisplay = `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}`;

        const daySpecials = specialDaysMap[isoDate] || [];
        const isSpecialDay = daySpecials.length > 0;
        const primarySpecial = isSpecialDay ? daySpecials[0] : null;

        let headerTitle = `${dayLetter} ${dateDisplay}`;
        let specialIndicatorHtml = '';

        if (isSpecialDay) {
            const specialNames = daySpecials.map(s => s.name).join(', ');
            headerTitle += ` - ${specialNames}`;
            const badgeColor = (primarySpecial && primarySpecial.color) ? primarySpecial.color : '#f59e0b';
            specialIndicatorHtml = `
                <span class="gantt-special-badge" style="background-color: ${badgeColor};" title="${escapeHtml(specialNames)}">
                    ★ ${escapeHtml(primarySpecial.name)}
                </span>
            `;
        }

        daysHeaderHtml += `
            <div class="gantt-day-header-cell ${isToday ? 'is-today' : ''} ${isWeekend ? 'is-weekend' : ''} ${isSpecialDay ? 'is-special-day' : ''}"
                 style="width: calc(100% / ${DAYS_COUNT});"
                 title="${headerTitle}"
                 data-date="${isoDate}">
                <span class="day-letter">${dayLetter}</span>
                <span class="day-num">${d.getDate()}</span>
                ${specialIndicatorHtml}
            </div>
        `;
    });

    // Build Rows
    let rowsHtml = '';

    Object.keys(projectsMap).forEach(projectName => {
        const projectTasks = projectsMap[projectName];

        // Project Header Row
        rowsHtml += `
            <div class="gantt-project-row">
                <div class="gantt-left-cell project-title-cell">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--primary);">
                        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                    </svg>
                    <span class="gantt-proj-name">${escapeHtml(projectName)}</span>
                    <span class="gantt-proj-count">${projectTasks.length} משימות</span>
                </div>
                <div class="gantt-timeline-track project-track">
                </div>
            </div>
        `;

        // Task Rows
        projectTasks.forEach(task => {
            const prioColor = PRIORITY_COLORS[task.priority] || '#cbd5e1';
            const statusColor = STATUS_COLORS[task.status] || '#64748b';
            const statusLabel = STATUS_LABELS[task.status] || 'בתהליך';
            const displayName = task.name || task.task || task.title || `משימה #${task.id}`;

            // Left Cell (Task details)
            const leftCellHtml = `
                <div class="gantt-left-cell task-title-cell" data-task-id="${task.id}" title="${escapeHtml(displayName)} - לחץ לפתיחת פרטים">
                    <span class="gantt-prio-dot" style="background-color: ${prioColor};"></span>
                    <span class="gantt-task-name">${escapeHtml(displayName)}</span>
                    <span class="gantt-status-pill ${task.status}">${statusLabel}</span>
                </div>
            `;

            // 28 background day cells
            let bgDaysHtml = '';
            dates.forEach((d) => {
                const isoDate = formatDateISO(d);
                const isToday = (d.getTime() === today.getTime());
                const isWeekend = (d.getDay() === 5 || d.getDay() === 6);
                const daySpecials = specialDaysMap[isoDate] || [];
                const isSpecialDay = daySpecials.length > 0;
                const primarySpecial = isSpecialDay ? daySpecials[0] : null;

                let cellTitle = '';
                let cellCustomStyle = '';
                if (isSpecialDay) {
                    const specialNames = daySpecials.map(s => s.name).join(', ');
                    cellTitle = `יום מיוחד: ${specialNames}`;
                    if (primarySpecial && primarySpecial.color) {
                        cellCustomStyle = `border-bottom-color: ${primarySpecial.color};`;
                    }
                }

                bgDaysHtml += `
                    <div class="gantt-grid-cell ${isToday ? 'is-today' : ''} ${isWeekend ? 'is-weekend' : ''} ${isSpecialDay ? 'is-special-day' : ''}"
                         style="width: calc(100% / ${DAYS_COUNT}); ${cellCustomStyle}"
                         ${cellTitle ? `title="${escapeHtml(cellTitle)}"` : ''}
                         data-date="${isoDate}">
                    </div>
                `;
            });

            // Bar or Schedule button
            let barHtml = '';
            if (task.startDate || task.endDate) {
                const tStart = task.startDate || task.endDate;
                const tEnd = task.endDate || task.startDate;

                const startMidnight = new Date(tStart);
                startMidnight.setHours(0, 0, 0, 0);
                const endMidnight = new Date(tEnd);
                endMidnight.setHours(0, 0, 0, 0);

                const msPerDay = 1000 * 60 * 60 * 24;
                const dayIndexStart = Math.round((startMidnight.getTime() - ganttStartDate.getTime()) / msPerDay);
                const dayIndexEnd = Math.round((endMidnight.getTime() - ganttStartDate.getTime()) / msPerDay);

                // Check overlap with 0..DAYS_COUNT-1
                if (dayIndexEnd >= 0 && dayIndexStart < DAYS_COUNT) {
                    const colStart = Math.max(0, dayIndexStart);
                    const colEnd = Math.min(DAYS_COUNT - 1, dayIndexEnd);
                    const spanCols = Math.max(1, colEnd - colStart + 1);

                    const rightPercent = (colStart / DAYS_COUNT) * 100;
                    const widthPercent = (spanCols / DAYS_COUNT) * 100;

                    const dateTip = `${formatDateDisp(tStart)} - ${formatDateDisp(tEnd)}`;
                    const truncatedTitle = truncateBarTitle(displayName, spanCols);
                    const spanClass = `span-${Math.min(spanCols, 5)}`;
                    const showSubtasks = spanCols >= 3 && task.subtasksText;

                    barHtml = `
                        <div class="gantt-bar ${spanClass}"
                             data-task-id="${task.id}"
                             data-full-title="${escapeHtml(displayName)}"
                             data-start-day="${dayIndexStart}"
                             data-end-day="${dayIndexEnd}"
                             data-start-date="${task.startDate ? formatDateISO(task.startDate) : ''}"
                             data-end-date="${task.endDate ? formatDateISO(task.endDate) : ''}"
                             style="right: ${rightPercent}%; width: ${widthPercent}%; background-color: ${statusColor};"
                             title="${escapeHtml(displayName)} (${dateTip}) - גרור להעתקת תאריכים או גרור קצוות לשינוי משך">
                            <div class="gantt-resize-handle handle-right" title="גרור לשינוי תאריך התחלה"></div>
                            ${task.subtasksPercent > 0 ? `<div class="gantt-progress-fill" style="width: ${task.subtasksPercent}%;"></div>` : ''}
                            <span class="gantt-bar-title" title="${escapeHtml(displayName)}">${escapeHtml(truncatedTitle)}</span>
                            ${showSubtasks ? `<span class="gantt-bar-subtasks" title="תתי-משימות: ${task.subtasksText}">${task.subtasksText}</span>` : ''}
                            <div class="gantt-resize-handle handle-left" title="גרור לשינוי תאריך סיום"></div>
                        </div>
                    `;
                }
            } else {
                barHtml = `
                    <button type="button" class="gantt-no-date-btn" data-task-id="${task.id}" title="לחץ או גרור עם העכבר על השורה לסמן תאריכים">
                        + קבע תאריך
                    </button>
                    <span class="gantt-track-hint">גרור עם העכבר לסמן תאריכים</span>
                `;
            }

            const trackContentHtml = `
                <div class="gantt-timeline-track" data-task-id="${task.id}" title="גרור לסימון תאריכים עבור משימה זו">
                    <div class="gantt-grid-cells-row">
                        ${bgDaysHtml}
                    </div>
                    ${barHtml}
                </div>
            `;

            rowsHtml += `
                <div class="gantt-task-row">
                    ${leftCellHtml}
                    ${trackContentHtml}
                </div>
            `;
        });
    });

    container.innerHTML = `
        <div class="gantt-table">
            <div class="gantt-header-row">
                <div class="gantt-left-cell gantt-left-header">
                    <span>פרויקט ומשימה</span>
                </div>
                <div class="gantt-timeline-header">
                    ${daysHeaderHtml}
                </div>
            </div>
            <div class="gantt-rows-container">
                ${rowsHtml}
            </div>
        </div>
    `;

    attachInteractiveTimelineListeners(container);
}

function attachInteractiveTimelineListeners(container) {
    // 1. Task details click
    container.querySelectorAll('.task-title-cell').forEach(cell => {
        cell.onclick = (e) => {
            e.stopPropagation();
            openEditModalForTask(cell.dataset.taskId);
        };
    });

    // 2. Unscheduled button click
    container.querySelectorAll('.gantt-no-date-btn').forEach(btn => {
        btn.onclick = (e) => {
            e.stopPropagation();
            openEditModalForTask(btn.dataset.taskId);
        };
    });

    // 3. Bar dragging & resizing
    container.querySelectorAll('.gantt-bar').forEach(bar => {
        const taskId = bar.dataset.taskId;
        const track = bar.closest('.gantt-timeline-track');
        if (!track || !taskId) return;

        const rightHandle = bar.querySelector('.gantt-resize-handle.handle-right');
        const leftHandle = bar.querySelector('.gantt-resize-handle.handle-left');

        if (rightHandle) {
            setupResizeHandle(rightHandle, bar, track, taskId, true);
        }
        if (leftHandle) {
            setupResizeHandle(leftHandle, bar, track, taskId, false);
        }

        setupBarDragAndClick(bar, track, taskId);
    });

    // 4. Track date marking
    container.querySelectorAll('.gantt-timeline-track').forEach(track => {
        const taskId = track.dataset.taskId;
        if (!taskId) return;
        setupTrackMarking(track, taskId);
    });
}

function setupResizeHandle(handle, bar, track, taskId, isRightHandle) {
    handle.onmousedown = (e) => {
        e.preventDefault();
        e.stopPropagation();

        const trackRect = track.getBoundingClientRect();
        const origStartDay = parseInt(bar.dataset.startDay, 10);
        const origEndDay = parseInt(bar.dataset.endDay, 10);

        let currentStartDay = origStartDay;
        let currentEndDay = origEndDay;

        bar.classList.add('resizing');
        document.body.style.cursor = 'ew-resize';
        document.body.style.userSelect = 'none';

        const onMouseMove = (moveEvent) => {
            const frac = (trackRect.right - moveEvent.clientX) / trackRect.width;
            const clampedFrac = Math.max(0, Math.min(0.9999, frac));
            const mouseDay = Math.floor(clampedFrac * DAYS_COUNT);

            if (isRightHandle) {
                // Adjust START date (right edge in RTL)
                currentStartDay = Math.min(mouseDay, currentEndDay);
            } else {
                // Adjust END date (left edge in RTL)
                currentEndDay = Math.max(mouseDay, currentStartDay);
            }

            const span = currentEndDay - currentStartDay + 1;
            bar.style.right = `${(currentStartDay / DAYS_COUNT) * 100}%`;
            bar.style.width = `${(span / DAYS_COUNT) * 100}%`;

            const titleEl = bar.querySelector('.gantt-bar-title');
            const fullTitle = bar.getAttribute('data-full-title') || (titleEl ? titleEl.getAttribute('title') : '');
            if (titleEl && fullTitle) {
                titleEl.textContent = truncateBarTitle(fullTitle, span);
            }
            bar.className = `gantt-bar resizing span-${Math.min(span, 5)}`;

            const sDate = getDateForDayIndex(currentStartDay);
            const eDate = getDateForDayIndex(currentEndDay);
            showDragTooltip(`${formatDateDisp(sDate)} - ${formatDateDisp(eDate)} (${span} ימים)`, moveEvent.clientX, moveEvent.clientY);
        };

        const onMouseUp = async () => {
            window.removeEventListener('mousemove', onMouseMove);
            window.removeEventListener('mouseup', onMouseUp);
            bar.classList.remove('resizing');
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
            hideDragTooltip();

            const sDate = getDateForDayIndex(currentStartDay);
            const eDate = getDateForDayIndex(currentEndDay);
            await updateTaskDates(taskId, formatDateISO(sDate), formatDateISO(eDate));
        };

        window.addEventListener('mousemove', onMouseMove);
        window.addEventListener('mouseup', onMouseUp);
    };
}

function setupBarDragAndClick(bar, track, taskId) {
    bar.onmousedown = (e) => {
        if (e.target.closest('.gantt-resize-handle')) return;

        e.preventDefault();
        const startX = e.clientX;
        const startY = e.clientY;
        const trackRect = track.getBoundingClientRect();

        const origStartDay = parseInt(bar.dataset.startDay, 10);
        const origEndDay = parseInt(bar.dataset.endDay, 10);
        const duration = origEndDay - origStartDay;

        const mouseStartFrac = (trackRect.right - startX) / trackRect.width;
        const mouseStartDay = Math.floor(Math.max(0, Math.min(0.9999, mouseStartFrac)) * DAYS_COUNT);

        let isDragging = false;
        let finalStartDay = origStartDay;
        let finalEndDay = origEndDay;

        const onMouseMove = (moveEvent) => {
            const dist = Math.hypot(moveEvent.clientX - startX, moveEvent.clientY - startY);
            if (!isDragging && dist > 4) {
                isDragging = true;
                bar.classList.add('dragging-bar');
                document.body.style.cursor = 'grab';
                document.body.style.userSelect = 'none';
            }

            if (!isDragging) return;

            const curFrac = (trackRect.right - moveEvent.clientX) / trackRect.width;
            const curDay = Math.floor(Math.max(0, Math.min(0.9999, curFrac)) * DAYS_COUNT);
            const deltaDays = curDay - mouseStartDay;

            let newStart = origStartDay + deltaDays;
            let newEnd = newStart + duration;

            if (newStart < 0) {
                newStart = 0;
                newEnd = newStart + duration;
            }
            if (newEnd >= DAYS_COUNT) {
                newEnd = DAYS_COUNT - 1;
                newStart = Math.max(0, newEnd - duration);
            }

            finalStartDay = newStart;
            finalEndDay = newEnd;

            const span = finalEndDay - finalStartDay + 1;
            bar.style.right = `${(finalStartDay / DAYS_COUNT) * 100}%`;
            bar.style.width = `${(span / DAYS_COUNT) * 100}%`;

            const sDate = getDateForDayIndex(finalStartDay);
            const eDate = getDateForDayIndex(finalEndDay);
            showDragTooltip(`העתקת תאריכים: ${formatDateDisp(sDate)} - ${formatDateDisp(eDate)}`, moveEvent.clientX, moveEvent.clientY);
        };

        const onMouseUp = async () => {
            window.removeEventListener('mousemove', onMouseMove);
            window.removeEventListener('mouseup', onMouseUp);
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
            hideDragTooltip();

            if (isDragging) {
                bar.classList.remove('dragging-bar');
                const sDate = getDateForDayIndex(finalStartDay);
                const eDate = getDateForDayIndex(finalEndDay);
                await updateTaskDates(taskId, formatDateISO(sDate), formatDateISO(eDate));
            } else {
                openEditModalForTask(taskId);
            }
        };

        window.addEventListener('mousemove', onMouseMove);
        window.addEventListener('mouseup', onMouseUp);
    };
}

function setupTrackMarking(track, taskId) {
    track.onmousedown = (e) => {
        if (e.target.closest('.gantt-bar') || e.target.closest('button')) return;

        e.preventDefault();
        const startX = e.clientX;
        const trackRect = track.getBoundingClientRect();

        const startFrac = (trackRect.right - startX) / trackRect.width;
        const startDay = Math.floor(Math.max(0, Math.min(0.9999, startFrac)) * DAYS_COUNT);

        let selectionBox = track.querySelector('.gantt-selection-box');
        if (!selectionBox) {
            selectionBox = document.createElement('div');
            selectionBox.className = 'gantt-selection-box';
            track.appendChild(selectionBox);
        }

        let isMarking = false;
        let minDay = startDay;
        let maxDay = startDay;

        selectionBox.style.right = `${(startDay / DAYS_COUNT) * 100}%`;
        selectionBox.style.width = `${(1 / DAYS_COUNT) * 100}%`;
        selectionBox.style.display = 'block';

        const sDateInitial = getDateForDayIndex(startDay);
        showDragTooltip(`קביעת תאריך: ${formatDateDisp(sDateInitial)}`, e.clientX, e.clientY);

        const onMouseMove = (moveEvent) => {
            isMarking = true;
            document.body.style.cursor = 'crosshair';
            document.body.style.userSelect = 'none';

            const curFrac = (trackRect.right - moveEvent.clientX) / trackRect.width;
            const curDay = Math.floor(Math.max(0, Math.min(0.9999, curFrac)) * DAYS_COUNT);

            minDay = Math.min(startDay, curDay);
            maxDay = Math.max(startDay, curDay);
            const span = maxDay - minDay + 1;

            selectionBox.style.right = `${(minDay / DAYS_COUNT) * 100}%`;
            selectionBox.style.width = `${(span / DAYS_COUNT) * 100}%`;

            const sDate = getDateForDayIndex(minDay);
            const eDate = getDateForDayIndex(maxDay);
            showDragTooltip(`קביעת תאריכים: ${formatDateDisp(sDate)} - ${formatDateDisp(eDate)} (${span} ימים)`, moveEvent.clientX, moveEvent.clientY);
        };

        const onMouseUp = async () => {
            window.removeEventListener('mousemove', onMouseMove);
            window.removeEventListener('mouseup', onMouseUp);
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
            hideDragTooltip();
            if (selectionBox) selectionBox.style.display = 'none';

            const sDate = getDateForDayIndex(minDay);
            const eDate = getDateForDayIndex(maxDay);
            await updateTaskDates(taskId, formatDateISO(sDate), formatDateISO(eDate));
        };

        window.addEventListener('mousemove', onMouseMove);
        window.addEventListener('mouseup', onMouseUp);
    };
}

function openEditModalForTask(taskId) {
    if (!taskId) return;
    const targetTask = document.querySelector(`.task-item[data-id="${taskId}"]`);
    if (targetTask && window.mainUI && typeof window.mainUI.openEditModal === 'function') {
        if (window.mainState) window.mainState.currentTaskItem = targetTask;
        window.mainUI.openEditModal(targetTask);
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
