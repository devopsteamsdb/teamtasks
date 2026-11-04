// Personal, Team & General Focus Report Module (Style 1 - Executive Daily Briefing)
import { state, setActiveMemberFilter, setActiveTeamFilter } from './state.js';
import * as API from './api.js';
import { notifyDataChanged } from './live_sync.js';

const PRIORITY_WEIGHT = {
    'high': 4,
    'medium': 3,
    'low': 2,
    'none': 1,
    '': 1
};

const STATUS_WEIGHT = {
    'status-inprogress': 2,
    'status-notstarted': 1,
    'status-delayed': 0,
    'status-done': -1
};

const STATUS_LABELS = {
    'status-notstarted': 'טרם החל',
    'status-inprogress': 'בתהליך',
    'status-delayed': 'מעוכב',
    'status-done': 'הושלם'
};

let enrichedTasksMap = {};
let lastFetchedTimestamp = 0;
let isFetchingEnrichedTasks = false;

export function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function getTodayISO() {
    const now = new Date();
    const y = now.getFullYear();
    const m = String(now.getMonth() + 1).padStart(2, '0');
    const d = String(now.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
}

function getTodayDisplay() {
    const now = new Date();
    const d = String(now.getDate()).padStart(2, '0');
    const m = String(now.getMonth() + 1).padStart(2, '0');
    const y = now.getFullYear();
    return `${d}/${m}/${y}`;
}

function formatShortDate(isoStr) {
    if (!isoStr) return '';
    const parts = isoStr.slice(0, 10).split('-');
    if (parts.length !== 3) return isoStr;
    return `${parts[2]}/${parts[1]}`;
}

function formatDateRangeDisplay(startStr, endStr) {
    const s = formatShortDate(startStr);
    const e = formatShortDate(endStr);
    if (s && e) {
        return s === e ? e : `${s} - ${e}`;
    }
    if (e) return `יעד: ${e}`;
    if (s) return `התחלה: ${s}`;
    return 'ללא תאריך יעד';
}

function diffDaysFromToday(isoDateStr, todayISO) {
    if (!isoDateStr) return 0;
    const d1 = new Date(isoDateStr.slice(0, 10) + 'T00:00:00');
    const d2 = new Date(todayISO + 'T00:00:00');
    return Math.round((d2 - d1) / (1000 * 60 * 60 * 24));
}

async function ensureEnrichedTasksLoaded() {
    const currentTs = state.lastUpdateTimestamp || 1;
    if (isFetchingEnrichedTasks) return;
    if (Object.keys(enrichedTasksMap).length > 0 && lastFetchedTimestamp === currentTs) {
        return;
    }
    isFetchingEnrichedTasks = true;
    try {
        const res = await fetch('/api/tasks?include_archived=true');
        if (res.ok) {
            const list = await res.json();
            const nextMap = {};
            if (Array.isArray(list)) {
                list.forEach(t => {
                    nextMap[String(t.id)] = t;
                });
            }
            enrichedTasksMap = nextMap;
            lastFetchedTimestamp = currentTs;
            if (state.viewMode === 'report') {
                renderReport(true);
            }
        }
    } catch (err) {
        console.error('Failed to fetch enriched tasks for report:', err);
    } finally {
        isFetchingEnrichedTasks = false;
    }
}

function collectVisibleTasksFromDOM() {
    // Prefer grid items if available, otherwise kanban cards
    const gridItems = Array.from(document.querySelectorAll('.projects-grid .task-item'));
    const sourceElements = gridItems.length > 0
        ? gridItems
        : Array.from(document.querySelectorAll('.kanban-card'));

    const seenIds = new Set();
    const tasks = [];

    sourceElements.forEach(el => {
        if (el.classList.contains('filtered-hidden') || el.classList.contains('search-hidden')) {
            return;
        }
        const taskId = String(el.dataset.id || '');
        if (!taskId || seenIds.has(taskId)) return;
        seenIds.add(taskId);

        const enriched = enrichedTasksMap[taskId] || null;

        let taskName = el.dataset.taskName || '';
        if (!taskName && el.querySelector('.task-name')) {
            taskName = el.querySelector('.task-name').textContent.trim();
        }
        if (!taskName && enriched) {
            taskName = enriched.task || enriched.title || '';
        }

        const projectCard = el.closest('.project-card');
        const project = el.dataset.project || (projectCard ? (projectCard.dataset.projectName || '') : (enriched ? enriched.project : ''));
        const status = el.dataset.status || (enriched ? enriched.status : 'status-notstarted');
        const priority = el.dataset.priority || (enriched ? enriched.priority : 'none');
        const notes = (el.dataset.notes !== undefined ? el.dataset.notes : (enriched ? enriched.notes : '')) || '';
        const startStr = (el.dataset.startDate || (enriched && enriched.start_date ? enriched.start_date : '')) || '';
        const endStr = (el.dataset.endDate || (enriched && enriched.end_date ? enriched.end_date : '')) || '';
        const teamId = el.dataset.teamId || (enriched ? enriched.team_id : '') || '';

        const avatars = Array.from(el.querySelectorAll('.avatar')).map(img => {
            const memberKey = img.dataset.memberName || '';
            let memberNameHe = '';
            if (memberKey) {
                const memberObj = (state.members || []).find(m => m.name_en === memberKey);
                if (memberObj) {
                    memberNameHe = memberObj.name_he;
                }
            }
            if (!memberNameHe) {
                const titleStr = img.getAttribute('title') || '';
                memberNameHe = titleStr.split('-')[0].trim();
            }
            return {
                src: img.getAttribute('src'),
                title: img.getAttribute('title') || '',
                memberName: memberKey,
                nameHe: memberNameHe || memberKey
            };
        });

        // Subtasks & Comments from enriched cache (or badge fallback)
        const subtasks = enriched && Array.isArray(enriched.subtasks) ? enriched.subtasks : [];
        const comments = enriched && Array.isArray(enriched.comments) ? enriched.comments : [];

        let subtasksCount = subtasks.length;
        let subtasksCompletedCount = subtasks.filter(s => s.is_completed).length;

        if (!enriched) {
            const subBadge = el.querySelector('.subtask-badge span');
            if (subBadge) {
                const parts = subBadge.textContent.trim().split('/');
                if (parts.length === 2) {
                    subtasksCompletedCount = parseInt(parts[0], 10) || 0;
                    subtasksCount = parseInt(parts[1], 10) || 0;
                }
            }
        }

        tasks.push({
            id: taskId,
            title: taskName,
            project,
            status,
            priority,
            notes,
            start_date: startStr ? startStr.slice(0, 10) : '',
            end_date: endStr ? endStr.slice(0, 10) : '',
            team_id: teamId,
            avatars,
            subtasks,
            subtasksCount,
            subtasksCompletedCount,
            comments,
            lastComment: comments.length > 0 ? comments[comments.length - 1] : null
        });
    });

    return tasks;
}

function classifyAndSortTasks(tasks, todayISO) {
    const todayTasks = [];
    const priorityTasks = [];
    const delayedTasks = [];
    const doneTasks = [];

    tasks.forEach(task => {
        if (task.status === 'status-done') {
            doneTasks.push(task);
            return;
        }

        // Rule #2: Tasks marked as delayed ('status-delayed') go to the bottom section
        // because they are blocked/delayed not due to the employee
        if (task.status === 'status-delayed') {
            delayedTasks.push(task);
            return;
        }

        const s = task.start_date;
        const e = task.end_date;

        // Check if overdue (not marked delayed, but deadline passed) -> goes to the VERY TOP of Today's Focus!
        const isOverdueEnd = (e && e < todayISO);
        const isOverdueStartOnly = (!e && s && s < todayISO);

        if (isOverdueEnd || isOverdueStartOnly) {
            const refDate = e || s;
            const daysLate = diffDaysFromToday(refDate, todayISO);
            const lateText = daysLate === 1 ? 'באיחור של יום אחד' : `באיחור של ${daysLate} ימים`;
            task.focusUrgency = 1; // Highest urgency: Overdue
            task.focusReasonLabel = `⚠️ זמן היעד חלף (${lateText} • ${formatShortDate(refDate)})`;
            task.focusReasonClass = 'report-reason-overdue';
            todayTasks.push(task);
            return;
        }

        // Ends today
        if (e && e === todayISO) {
            task.focusUrgency = 2; // Ends today
            task.focusReasonLabel = `⏰ מסתיים היום (${formatShortDate(e)})`;
            task.focusReasonClass = 'report-reason-today-end';
            todayTasks.push(task);
            return;
        }

        // Starts today or active today (start_date <= today <= end_date)
        const isStartingToday = (s && s === todayISO);
        const isSpanningToday = (s && e && s <= todayISO && e >= todayISO);

        if (isStartingToday || isSpanningToday) {
            task.focusUrgency = 3; // Active today
            task.focusReasonLabel = isStartingToday && !e
                ? `📅 מתחיל היום (${formatShortDate(s)})`
                : `📅 משובץ להיום (${formatDateRangeDisplay(s, e)})`;
            task.focusReasonClass = 'report-reason-today-active';
            todayTasks.push(task);
            return;
        }

        // Otherwise: goes to Section 2 (Next Up by Priority)
        priorityTasks.push(task);
    });

    // Sort Section 1 (Today's Focus):
    // 1. Overdue first (urgency 1), then Ends Today (2), then Active Today (3)
    // 2. Priority (High -> Medium -> Low -> None)
    // 3. Status (In Progress -> Not Started)
    // 4. Earlier end_date / start_date
    todayTasks.sort((a, b) => {
        if (a.focusUrgency !== b.focusUrgency) {
            return a.focusUrgency - b.focusUrgency;
        }
        const pDiff = (PRIORITY_WEIGHT[b.priority] || 1) - (PRIORITY_WEIGHT[a.priority] || 1);
        if (pDiff !== 0) return pDiff;
        const sDiff = (STATUS_WEIGHT[b.status] || 0) - (STATUS_WEIGHT[a.status] || 0);
        if (sDiff !== 0) return sDiff;
        const dateA = a.end_date || a.start_date || '9999-99-99';
        const dateB = b.end_date || b.start_date || '9999-99-99';
        return dateA.localeCompare(dateB);
    });

    // Sort Section 2 (Priority Queue):
    // 1. Priority (High -> Medium -> Low -> None)
    // 2. Status (In Progress -> Not Started)
    // 3. Earlier date
    priorityTasks.sort((a, b) => {
        const pDiff = (PRIORITY_WEIGHT[b.priority] || 1) - (PRIORITY_WEIGHT[a.priority] || 1);
        if (pDiff !== 0) return pDiff;
        const sDiff = (STATUS_WEIGHT[b.status] || 0) - (STATUS_WEIGHT[a.status] || 0);
        if (sDiff !== 0) return sDiff;
        const dateA = a.end_date || a.start_date || '9999-99-99';
        const dateB = b.end_date || b.start_date || '9999-99-99';
        return dateA.localeCompare(dateB);
    });

    // Sort Section 3 (Delayed Tasks): by Priority then date
    delayedTasks.sort((a, b) => {
        const pDiff = (PRIORITY_WEIGHT[b.priority] || 1) - (PRIORITY_WEIGHT[a.priority] || 1);
        if (pDiff !== 0) return pDiff;
        const dateA = a.end_date || a.start_date || '9999-99-99';
        const dateB = b.end_date || b.start_date || '9999-99-99';
        return dateA.localeCompare(dateB);
    });

    return { todayTasks, priorityTasks, delayedTasks, doneTasks };
}

function renderPriorityBadge(priority) {
    if (priority === 'high') {
        return '<span class="report-prio-badge prio-high">🔥 עדיפות גבוהה</span>';
    }
    if (priority === 'medium') {
        return '<span class="report-prio-badge prio-medium">⚡ עדיפות בינונית</span>';
    }
    if (priority === 'low') {
        return '<span class="report-prio-badge prio-low">עדיפות נמוכה</span>';
    }
    return '<span class="report-prio-badge prio-none">ללא עדיפות</span>';
}

function renderStatusBadge(status) {
    const label = STATUS_LABELS[status] || status;
    return `<span class="status-badge ${escapeHtml(status)}">${escapeHtml(label)}</span>`;
}

function renderMembersStrip(membersList) {
    if (!membersList || membersList.length === 0) {
        return '<span class="report-no-member">לא שויך</span>';
    }
    const names = membersList
        .map(m => m.nameHe || m.memberName || '')
        .filter(Boolean);

    if (names.length === 0) {
        return '<span class="report-no-member">לא שויך</span>';
    }

    return `
        <div class="report-members-badge" title="משויך ל: ${escapeHtml(names.join(', '))}">
            <span class="report-member-icon">👤</span>
            <span class="report-member-names">${escapeHtml(names.join(', '))}</span>
        </div>
    `;
}

function renderInteractiveSubtasks(task) {
    if (!task.subtasks || task.subtasks.length === 0) {
        if (task.subtasksCount > 0) {
            return `<div class="report-subtasks-summary">☑️ צ'ק-ליסט: ${task.subtasksCompletedCount}/${task.subtasksCount} הושלמו</div>`;
        }
        return '';
    }
    const doneCount = task.subtasks.filter(s => s.is_completed).length;
    const total = task.subtasks.length;
    return `
        <div class="report-subtasks-box" onclick="event.stopPropagation();">
            <div class="report-subtasks-header">
                <span class="report-subtasks-title">צ'ק-ליסט לביצוע במשימה זו (לחץ לסימון):</span>
                <span class="report-subtasks-counter">${doneCount}/${total} הושלמו</span>
            </div>
            <div class="report-subtasks-list">
                ${task.subtasks.map(st => `
                    <label class="report-subtask-item ${st.is_completed ? 'is-done' : ''}">
                        <input type="checkbox"
                               class="report-subtask-checkbox"
                               data-task-id="${escapeHtml(task.id)}"
                               data-subtask-id="${escapeHtml(st.id)}"
                               ${st.is_completed ? 'checked' : ''}>
                        <span class="report-subtask-text">${escapeHtml(st.title)}</span>
                    </label>
                `).join('')}
            </div>
        </div>
    `;
}

function renderLastComment(task) {
    if (!task.lastComment) return '';
    const c = task.lastComment;
    return `
        <div class="report-last-comment">
            <span class="report-comment-icon">💬</span>
            <div class="report-comment-body">
                <strong>${escapeHtml(c.author_name || 'עדכון')}:</strong>
                <span>${escapeHtml(c.content || '')}</span>
                ${c.created_at ? `<span class="report-comment-date">(${escapeHtml(c.created_at)})</span>` : ''}
            </div>
        </div>
    `;
}

function renderContextSelectorBar(modeContext) {
    const members = state.members || [];
    const teams = state.teams || [];
    const activeTeamId = state.activeTeamFilter && state.activeTeamFilter !== 'archive' ? String(state.activeTeamFilter) : null;
    const activeMemberKey = state.activeMemberFilter || null;

    // Filter members to show in quick selector
    const visibleMembers = activeTeamId
        ? members.filter(m => {
            const tids = Array.isArray(m.team_ids) ? m.team_ids.map(String) : [];
            return tids.includes(activeTeamId) || String(m.team_id) === activeTeamId;
        })
        : members;

    return `
        <div class="report-quick-switcher no-print">
            <div class="report-switcher-row">
                <span class="report-switcher-label">מעבר מהיר לדוח:</span>
                <button type="button"
                        class="report-scope-pill ${!activeTeamId && !activeMemberKey ? 'active' : ''}"
                        data-action="select-general">
                    🌐 דוח כללי
                </button>
                ${teams.map(t => `
                    <button type="button"
                            class="report-scope-pill ${activeTeamId === String(t.id) && !activeMemberKey ? 'active' : ''}"
                            data-action="select-team"
                            data-team-id="${escapeHtml(t.id)}">
                        👥 ${escapeHtml(t.name_he)}
                    </button>
                `).join('')}
            </div>
            ${visibleMembers.length > 0 ? `
                <div class="report-switcher-row report-members-row">
                    <span class="report-switcher-label">דוח אישי לחבר צוות:</span>
                    <div class="report-member-pills">
                        ${visibleMembers.map(m => `
                            <button type="button"
                                    class="report-member-pill ${activeMemberKey === m.name_en ? 'active' : ''}"
                                    data-action="select-member"
                                    data-member="${escapeHtml(m.name_en)}">
                                <img src="/uploads/avatars/${escapeHtml(m.avatar_path || 'default.png')}"
                                     onerror="this.src='/static/images/default.png'"
                                     class="report-pill-avatar"
                                     alt="">
                                <span>${escapeHtml(m.name_he)}</span>
                            </button>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
        </div>
    `;
}

export function renderReport(skipFetch = false) {
    const container = document.getElementById('reportViewBody');
    if (!container) return;

    if (!skipFetch) {
        ensureEnrichedTasksLoaded();
    }

    const todayISO = getTodayISO();
    const todayDisp = getTodayDisplay();
    const visibleTasks = collectVisibleTasksFromDOM();
    const { todayTasks, priorityTasks, delayedTasks, doneTasks } = classifyAndSortTasks(visibleTasks, todayISO);

    const overdueCount = todayTasks.filter(t => t.focusUrgency === 1).length;
    const highPrioCount = priorityTasks.filter(t => t.priority === 'high').length;

    // Determine Report Mode: Personal vs Team vs General
    const activeMemberKey = state.activeMemberFilter || null;
    const activeTeamId = (state.activeTeamFilter && state.activeTeamFilter !== 'archive') ? String(state.activeTeamFilter) : null;
    const isArchiveMode = state.activeTeamFilter === 'archive';

    let headerTitle = '';
    let headerSubtitle = '';
    let headerAvatarHtml = '';
    let narrativeHtml = '';

    const summaryParts = [];
    if (todayTasks.length > 0) {
        summaryParts.push(`<strong class="report-highlight-primary">${todayTasks.length} משימות במיקוד להיום</strong>${overdueCount > 0 ? ` <span class="report-highlight-danger">(מתוכן ${overdueCount} שחלף זמן היעד שלהן!)</span>` : ''}`);
    }
    if (priorityTasks.length > 0) {
        summaryParts.push(`<strong>${priorityTasks.length} משימות בתור העדיפויות</strong>${highPrioCount > 0 ? ` (${highPrioCount} בעדיפות גבוהה)` : ''}`);
    }
    if (delayedTasks.length > 0) {
        summaryParts.push(`<strong>${delayedTasks.length} משימות המסומנות בעיכוב</strong>`);
    }

    const joinedSummary = summaryParts.length > 1
        ? summaryParts.slice(0, -1).join(', ') + ' ו-' + summaryParts[summaryParts.length - 1]
        : (summaryParts[0] || '');

    if (activeMemberKey) {
        const memberObj = (state.members || []).find(m => m.name_en === activeMemberKey);
        const memberName = memberObj ? memberObj.name_he : activeMemberKey;
        const firstName = memberName.split(' ')[0];
        const teamLabel = memberObj && memberObj.team_name ? memberObj.team_name : 'חבר צוות';
        const avatarPath = memberObj && memberObj.avatar_path ? memberObj.avatar_path : 'default.png';

        headerTitle = `הדוח האישי של ${escapeHtml(memberName)}`;
        headerSubtitle = escapeHtml(teamLabel);
        headerAvatarHtml = `
            <img src="/uploads/avatars/${escapeHtml(avatarPath)}"
                 onerror="this.src='/static/images/default.png'"
                 class="report-header-avatar"
                 alt="${escapeHtml(memberName)}">
        `;

        if (summaryParts.length === 0) {
            narrativeHtml = `שלום <strong>${escapeHtml(firstName)}</strong> 👋 — נכון להיום (<strong>${todayDisp}</strong>), אין לך משימות פתוחות הממתינות לטיפול בסינון הנוכחי.`;
        } else {
            narrativeHtml = `שלום <strong>${escapeHtml(firstName)}</strong> 👋 — נכון להיום (<strong>${todayDisp}</strong>), יש לך ${joinedSummary}. ${
                overdueCount > 0
                    ? 'מומלץ לטפל תחילה במשימות שזמן היעד שלהן חלף ומופיעות בראש הדוח.'
                    : (todayTasks.length > 0 ? 'מומלץ להתחיל ממשימת המיקוד הראשונה להיום.' : 'מומלץ לבחור את המשימה הראשונה מתור העדיפויות.')
            }`;
        }
    } else if (activeTeamId) {
        const teamObj = (state.teams || []).find(t => String(t.id) === activeTeamId);
        const teamName = teamObj ? teamObj.name_he : 'הצוות';
        headerTitle = `דוח מיקוד צוותי — ${escapeHtml(teamName)}`;
        headerSubtitle = `סיכום משימות הצוות • ${todayDisp}`;
        headerAvatarHtml = `
            <div class="report-header-icon report-icon-team">👥</div>
        `;
        if (summaryParts.length === 0) {
            narrativeHtml = `תדריך מיקוד עבור <strong>${escapeHtml(teamName)}</strong> להיום (<strong>${todayDisp}</strong>): אין משימות פתוחות להצגה בסינון הנוכחי.`;
        } else {
            narrativeHtml = `תדריך מיקוד עבור <strong>${escapeHtml(teamName)}</strong> להיום (<strong>${todayDisp}</strong>): לצוות יש ${joinedSummary}.`;
        }
    } else {
        headerTitle = isArchiveMode ? 'דוח משימות בארכיון' : 'דוח מיקוד כללי — כלל הצוותים והפרויקטים';
        headerSubtitle = `תמונת מצב רוחבית • ${todayDisp}`;
        headerAvatarHtml = `
            <div class="report-header-icon report-icon-general">📊</div>
        `;
        if (summaryParts.length === 0) {
            narrativeHtml = `תדריך מיקוד רוחבי לכלל הפרויקטים להיום (<strong>${todayDisp}</strong>): אין משימות פתוחות להצגה בסינון הנוכחי.`;
        } else {
            narrativeHtml = `תדריך מיקוד רוחבי לכלל הפרויקטים להיום (<strong>${todayDisp}</strong>): קיימות ${joinedSummary}.`;
        }
    }

    // Build Section 1: Today's Focus (Overdue first, then Today)
    let section1Html = '';
    if (todayTasks.length > 0) {
        const primaryTask = todayTasks[0];
        const restToday = todayTasks.slice(1);
        const primaryLabel = primaryTask.focusUrgency === 1
            ? '🚨 מיקוד #1 להיום (זמן היעד חלף!)'
            : '🎯 מיקוד #1 להיום';

        section1Html = `
            <section class="report-section">
                <div class="report-section-header">
                    <div class="report-section-title-wrap">
                        <span class="report-section-dot dot-today"></span>
                        <h3 class="report-section-title">חלק א׳: במה מתמקדים היום (${todayTasks.length} משימות)</h3>
                    </div>
                    <span class="report-section-subtitle">קודם משימות שחלף זמנן ואינן בעיכוב, ואחריהן משימות להיום לפי עדיפות</span>
                </div>

                <!-- #1 Primary Focus Card -->
                <div class="report-primary-card ${primaryTask.focusUrgency === 1 ? 'is-overdue-primary' : ''}" data-task-id="${escapeHtml(primaryTask.id)}">
                    <div class="report-card-top-bar">
                        <div class="report-badges-row">
                            <span class="report-rank-pill ${primaryTask.focusUrgency === 1 ? 'rank-overdue' : 'rank-primary'}">${primaryLabel}</span>
                            <span class="report-reason-badge ${primaryTask.focusReasonClass}">${escapeHtml(primaryTask.focusReasonLabel)}</span>
                            ${renderPriorityBadge(primaryTask.priority)}
                            ${renderStatusBadge(primaryTask.status)}
                        </div>
                        <div class="report-card-meta-left">
                            <span class="report-project-tag">📁 ${escapeHtml(primaryTask.project)}</span>
                            ${renderMembersStrip(primaryTask.avatars)}
                        </div>
                    </div>

                    <h4 class="report-primary-task-title">${escapeHtml(primaryTask.title)}</h4>
                    ${primaryTask.notes ? `<p class="report-task-notes">${escapeHtml(primaryTask.notes)}</p>` : ''}

                    ${renderInteractiveSubtasks(primaryTask)}
                    ${renderLastComment(primaryTask)}
                </div>

                <!-- Other Today Tasks -->
                ${restToday.length > 0 ? `
                    <div class="report-today-grid">
                        ${restToday.map((t, idx) => `
                            <div class="report-today-card prio-border-${escapeHtml(t.priority || 'none')} ${t.focusUrgency === 1 ? 'is-overdue-card' : ''}" data-task-id="${escapeHtml(t.id)}">
                                <div class="report-card-top-bar">
                                    <div class="report-badges-row">
                                        <span class="report-step-badge">מיקוד #${idx + 2}</span>
                                        <span class="report-reason-badge ${t.focusReasonClass}">${escapeHtml(t.focusReasonLabel)}</span>
                                        ${renderPriorityBadge(t.priority)}
                                        ${renderStatusBadge(t.status)}
                                    </div>
                                    ${renderMembersStrip(t.avatars)}
                                </div>
                                <div class="report-card-project-line">📁 ${escapeHtml(t.project)}</div>
                                <h4 class="report-card-title">${escapeHtml(t.title)}</h4>
                                ${t.notes ? `<p class="report-task-notes">${escapeHtml(t.notes)}</p>` : ''}
                                ${renderInteractiveSubtasks(t)}
                                ${renderLastComment(t)}
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </section>
        `;
    }

    // Build Section 2: Next Up by Priority
    let section2Html = '';
    if (priorityTasks.length > 0) {
        section2Html = `
            <section class="report-section">
                <div class="report-section-header">
                    <div class="report-section-title-wrap">
                        <span class="report-section-dot dot-priority"></span>
                        <h3 class="report-section-title">חלק ב׳: הבאות בתור לפי עדיפות (${priorityTasks.length} משימות)</h3>
                    </div>
                    <span class="report-section-subtitle">משימות פתוחות נוספות מדורגות מעדיפות גבוהה לנמוכה</span>
                </div>

                <div class="report-priority-list">
                    ${priorityTasks.map((pt, idx) => `
                        <div class="report-priority-row prio-border-${escapeHtml(pt.priority || 'none')}" data-task-id="${escapeHtml(pt.id)}">
                            <div class="report-priority-main">
                                <div class="report-badges-row">
                                    <span class="report-queue-num">#${idx + 1} בתור</span>
                                    ${renderPriorityBadge(pt.priority)}
                                    ${renderStatusBadge(pt.status)}
                                    <span class="report-project-tag">📁 ${escapeHtml(pt.project)}</span>
                                </div>
                                <h4 class="report-card-title">${escapeHtml(pt.title)}</h4>
                                ${pt.notes ? `<p class="report-task-notes">${escapeHtml(pt.notes)}</p>` : ''}
                                ${renderInteractiveSubtasks(pt)}
                                ${renderLastComment(pt)}
                            </div>
                            <div class="report-priority-side">
                                <span class="report-date-pill" dir="ltr">📅 ${escapeHtml(formatDateRangeDisplay(pt.start_date, pt.end_date))}</span>
                                ${renderMembersStrip(pt.avatars)}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </section>
        `;
    }

    const emptyAllHtml = (todayTasks.length === 0 && priorityTasks.length === 0 && delayedTasks.length === 0)
        ? `<div class="report-empty-box">✨ אין משימות פתוחות להצגה בסינון הנוכחי.</div>`
        : '';

    // Build Section 3: Delayed Tasks (at the bottom, as requested)
    let section3Html = '';
    if (delayedTasks.length > 0) {
        section3Html = `
            <section class="report-section report-section-delayed">
                <div class="report-section-header">
                    <div class="report-section-title-wrap">
                        <span class="report-section-dot dot-delayed"></span>
                        <h3 class="report-section-title">חלק ג׳: משימות המסומנות בעיכוב (${delayedTasks.length} משימות)</h3>
                    </div>
                    <span class="report-section-subtitle">משימות בעיכוב ידוע / תלויות בגורם חיצוני — מופיעות בסוף הדוח</span>
                </div>

                <div class="report-priority-list">
                    ${delayedTasks.map(dt => `
                        <div class="report-priority-row report-delayed-row" data-task-id="${escapeHtml(dt.id)}">
                            <div class="report-priority-main">
                                <div class="report-badges-row">
                                    ${renderStatusBadge(dt.status)}
                                    ${renderPriorityBadge(dt.priority)}
                                    <span class="report-project-tag">📁 ${escapeHtml(dt.project)}</span>
                                </div>
                                <h4 class="report-card-title">${escapeHtml(dt.title)}</h4>
                                ${dt.notes ? `<p class="report-task-notes">${escapeHtml(dt.notes)}</p>` : ''}
                                ${renderLastComment(dt)}
                            </div>
                            <div class="report-priority-side">
                                <span class="report-date-pill" dir="ltr">📅 ${escapeHtml(formatDateRangeDisplay(dt.start_date, dt.end_date))}</span>
                                ${renderMembersStrip(dt.avatars)}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </section>
        `;
    }

    // Optional collapsible completed tasks summary at the very bottom
    let sectionDoneHtml = '';
    if (doneTasks.length > 0) {
        sectionDoneHtml = `
            <details class="report-done-details no-print">
                <summary class="report-done-summary">✅ הצג משימות שהושלמו (${doneTasks.length})</summary>
                <div class="report-priority-list" style="margin-top: 0.75rem;">
                    ${doneTasks.map(dt => `
                        <div class="report-priority-row report-done-row" data-task-id="${escapeHtml(dt.id)}">
                            <div class="report-priority-main">
                                <div class="report-badges-row">
                                    ${renderStatusBadge(dt.status)}
                                    <span class="report-project-tag">📁 ${escapeHtml(dt.project)}</span>
                                </div>
                                <h4 class="report-card-title" style="text-decoration: line-through; opacity: 0.75;">${escapeHtml(dt.title)}</h4>
                            </div>
                            <div class="report-priority-side">
                                ${renderMembersStrip(dt.avatars)}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </details>
        `;
    }

    container.innerHTML = `
        <div class="report-briefing-container">
            <!-- Quick Scope & Member Switcher -->
            ${renderContextSelectorBar()}

            <!-- Main Executive Briefing Document -->
            <div class="report-document-card">
                <!-- Briefing Header -->
                <div class="report-doc-header">
                    <div class="report-doc-identity">
                        ${headerAvatarHtml}
                        <div class="report-doc-titles">
                            <div class="report-doc-title-row">
                                <h2 class="report-doc-title">${headerTitle}</h2>
                                <span class="report-doc-role-badge">${headerSubtitle}</span>
                            </div>
                            <p class="report-doc-narrative">${narrativeHtml}</p>
                        </div>
                    </div>
                    <div class="report-doc-actions no-print">
                        <div class="report-kpi-strip">
                            ${overdueCount > 0 ? `
                            <div class="report-kpi-box kpi-danger">
                                <span class="report-kpi-num">${overdueCount}</span>
                                <span class="report-kpi-label">חלף זמנן</span>
                            </div>` : ''}
                            ${todayTasks.length > 0 ? `
                            <div class="report-kpi-box kpi-primary">
                                <span class="report-kpi-num">${todayTasks.length}</span>
                                <span class="report-kpi-label">במיקוד היום</span>
                            </div>` : ''}
                            ${priorityTasks.length > 0 ? `
                            <div class="report-kpi-box">
                                <span class="report-kpi-num">${priorityTasks.length}</span>
                                <span class="report-kpi-label">לפי עדיפות</span>
                            </div>` : ''}
                            ${delayedTasks.length > 0 ? `
                            <div class="report-kpi-box">
                                <span class="report-kpi-num">${delayedTasks.length}</span>
                                <span class="report-kpi-label">בעיכוב</span>
                            </div>` : ''}
                        </div>
                        <button type="button" class="report-print-btn" id="reportPrintBtn" title="הדפס דוח זה">
                            🖨️ הדפס דוח
                        </button>
                    </div>
                </div>

                ${emptyAllHtml}
                ${section1Html}
                ${section2Html}
                ${section3Html}
                ${sectionDoneHtml}
            </div>
        </div>
    `;

    attachReportInteractions(container);
}

function attachReportInteractions(container) {
    // 1. Print button
    const printBtn = container.querySelector('#reportPrintBtn');
    if (printBtn) {
        printBtn.onclick = () => window.print();
    }

    // 2. Scope switcher buttons (General / Team / Member)
    container.querySelectorAll('[data-action="select-general"]').forEach(btn => {
        btn.onclick = () => {
            setActiveMemberFilter(null);
            setActiveTeamFilter(null);
            localStorage.removeItem('activeMemberFilter');
            localStorage.removeItem('activeTeamFilter');
            const url = new URL(window.location);
            url.searchParams.delete('team');
            window.history.replaceState({}, '', url);
            if (window.mainUI) window.mainUI.applyFilters();
        };
    });

    container.querySelectorAll('[data-action="select-team"]').forEach(btn => {
        btn.onclick = () => {
            const teamId = btn.dataset.teamId;
            setActiveMemberFilter(null);
            localStorage.removeItem('activeMemberFilter');
            setActiveTeamFilter(teamId);
            localStorage.setItem('activeTeamFilter', teamId);
            const url = new URL(window.location);
            url.searchParams.set('team', teamId);
            window.history.replaceState({}, '', url);
            if (window.mainUI) window.mainUI.applyFilters();
        };
    });

    container.querySelectorAll('[data-action="select-member"]').forEach(btn => {
        btn.onclick = () => {
            const member = btn.dataset.member;
            if (state.activeMemberFilter === member) {
                setActiveMemberFilter(null);
                localStorage.removeItem('activeMemberFilter');
            } else {
                setActiveMemberFilter(member);
                localStorage.setItem('activeMemberFilter', member);
            }
            if (window.mainUI) window.mainUI.applyFilters();
        };
    });

    // 3. Interactive Subtask Checkboxes inside Report
    container.querySelectorAll('.report-subtask-checkbox').forEach(cb => {
        cb.onchange = async (e) => {
            e.stopPropagation();
            const subtaskId = cb.dataset.subtaskId;
            const taskId = cb.dataset.taskId;
            const isCompleted = cb.checked;

            const labelEl = cb.closest('.report-subtask-item');
            if (labelEl) {
                labelEl.classList.toggle('is-done', isCompleted);
            }

            // Update local cache immediately
            const cachedTask = enrichedTasksMap[String(taskId)];
            if (cachedTask && Array.isArray(cachedTask.subtasks)) {
                const sub = cachedTask.subtasks.find(s => String(s.id) === String(subtaskId));
                if (sub) sub.is_completed = isCompleted;
                const total = cachedTask.subtasks.length;
                const completed = cachedTask.subtasks.filter(s => s.is_completed).length;
                if (window.mainUI && typeof window.mainUI.updateTaskSubtaskBadges === 'function') {
                    window.mainUI.updateTaskSubtaskBadges(taskId, completed, total);
                }
            }

            renderReport(true);

            try {
                await API.updateSubtask(subtaskId, { is_completed: isCompleted });
                notifyDataChanged();
            } catch (err) {
                console.error('Failed to update subtask from report:', err);
            }
        };
    });

    // 4. Click on any task card/row opens Edit Modal
    container.querySelectorAll('[data-task-id]').forEach(card => {
        card.onclick = (e) => {
            if (
                e.target.closest('input') ||
                e.target.closest('label.report-subtask-item') ||
                e.target.closest('button')
            ) {
                return;
            }
            const taskId = card.dataset.taskId;
            const targetTask = document.querySelector(`.task-item[data-id="${taskId}"]`);
            if (targetTask && window.mainUI && typeof window.mainUI.openEditModal === 'function') {
                if (window.mainState) window.mainState.currentTaskItem = targetTask;
                window.mainUI.openEditModal(targetTask);
            }
        };
    });
}
