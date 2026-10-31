// UI Manipulation
import { state, setTeams, setMembers, setProjects, setSpecialDays } from './state.js';
import { formatDateFromISO, getStatusFromClass, getFlatpickrConfig } from './utils.js';
import { renderGantt } from './gantt.js';
import { updateKanbanCounters } from './kanban.js';
import {
    fetchPageContent,
    fetchTeams,
    fetchMembers,
    fetchProjects,
    fetchSpecialDays,
    fetchTaskSubtasks,
    createSubtask,
    updateSubtask,
    deleteSubtask,
    fetchTaskComments,
    createTaskComment,
    deleteTaskComment
} from './api.js';

// DOM Elements Cache
export const elements = {};

export function updateDOMElements() {
    elements.modal = document.getElementById('taskModal');
    elements.createModal = document.getElementById('createTaskModal');
    elements.projectModal = document.getElementById('projectModal');
    elements.closeModal = document.querySelector('.close-modal');
    elements.closeCreateModal = document.querySelector('.close-modal-create');
    elements.closeProjectModal = document.querySelector('.close-modal-project');

    // View toggles & containers
    elements.viewBtnGrid = document.getElementById('viewBtnGrid');
    elements.viewBtnKanban = document.getElementById('viewBtnKanban');
    elements.viewBtnGantt = document.getElementById('viewBtnGantt');
    elements.viewContainerGrid = document.getElementById('viewContainerGrid');
    elements.viewContainerKanban = document.getElementById('viewContainerKanban');
    elements.viewContainerGantt = document.getElementById('viewContainerGantt');
    elements.projectsEmptyState = document.getElementById('projectsEmptyState');
    elements.projectsGrid = document.querySelector('.projects-grid');

    elements.saveBtn = document.getElementById('saveBtn');
    elements.archiveBtn = document.getElementById('archiveBtn');
    elements.deleteBtn = document.getElementById('deleteBtn');
    elements.createSaveBtn = document.getElementById('createSaveBtn');
    elements.addProjectBtn = document.getElementById('addProjectBtn');

    elements.projectModalTitle = document.getElementById('projectModalTitle');
    elements.projectModalId = document.getElementById('projectModalId');
    elements.projectModalNameInput = document.getElementById('projectModalNameInput');
    elements.projectTeamsSelect = document.getElementById('projectTeamsSelect');
    elements.projectModalSaveBtn = document.getElementById('projectModalSaveBtn');
    elements.projectModalArchiveBtn = document.getElementById('projectModalArchiveBtn');
    elements.projectModalDeleteBtn = document.getElementById('projectModalDeleteBtn');

    elements.taskProject = document.getElementById('taskProject');
    elements.taskNameInput = document.getElementById('taskNameInput');
    elements.taskStatus = document.getElementById('taskStatus');
    elements.taskPriority = document.getElementById('taskPriority');
    elements.taskNotes = document.getElementById('taskNotes');
    elements.taskTeam = document.getElementById('taskTeam');
    elements.taskStartDate = document.getElementById('taskStartDate');
    elements.taskEndDate = document.getElementById('taskEndDate');

    elements.createTaskProject = document.getElementById('createTaskProject');
    elements.createTaskNameInput = document.getElementById('createTaskNameInput');
    elements.createTaskStatus = document.getElementById('createTaskStatus');
    elements.createTaskPriority = document.getElementById('createTaskPriority');
    elements.createTaskNotes = document.getElementById('createTaskNotes');
    elements.createTaskTeam = document.getElementById('createTaskTeam');
    elements.createTaskStartDate = document.getElementById('createTaskStartDate');
    elements.createTaskEndDate = document.getElementById('createTaskEndDate');

    elements.searchBox = document.getElementById('searchBox');
    elements.clearSearchBtn = document.getElementById('clearSearch');
    elements.teamFilterButtons = document.querySelectorAll('.filter-team-btn');
    elements.memberFilterButtons = document.querySelectorAll('.filter-avatar-btn');
    elements.resetMemberFiltersBtn = document.getElementById('resetMemberFiltersBtn');

    // Filters
    elements.filterStatus = document.getElementById('filterStatus');
    elements.filterPriority = document.getElementById('filterPriority');
    elements.clearFiltersBtn = document.getElementById('clearFiltersBtn');

    // Subtasks & Comments
    elements.subtasksList = document.getElementById('subtasksList');
    elements.subtaskProgressText = document.getElementById('subtaskProgressText');
    elements.subtaskProgressBar = document.getElementById('subtaskProgressBar');
    elements.newSubtaskInput = document.getElementById('newSubtaskInput');
    elements.addSubtaskBtn = document.getElementById('addSubtaskBtn');

    elements.commentsList = document.getElementById('commentsList');
    elements.commentCounter = document.getElementById('commentCounter');
    elements.commentAuthorSelect = document.getElementById('commentAuthorSelect');
    elements.newCommentInput = document.getElementById('newCommentInput');
    elements.addCommentBtn = document.getElementById('addCommentBtn');
}

export function initializeFlatpickr() {
    const config = getFlatpickrConfig();
    flatpickr("#taskStartDate", config);
    flatpickr("#taskEndDate", config);
    flatpickr("#createTaskStartDate", config);
    flatpickr("#createTaskEndDate", config);
}

export function populateDropdowns() {
    const teams = state.teams || [];
    const options = teams.map(team =>
        `<option value="${team.id}">${team.name_he}</option>`
    ).join('');

    const defaultOption = '<option value="">בחר צוות...</option>';

    if (elements.createTaskTeam) elements.createTaskTeam.innerHTML = defaultOption + options;
    if (elements.taskTeam) elements.taskTeam.innerHTML = defaultOption + options;
}

export function populateProjectDropdowns() {
    const allProjects = state.projects || [];
    const activeProjects = allProjects.filter(p => !p.is_archived);

    const activeOptions = activeProjects.map(p => {
        const teamIds = (p.team_ids || (p.teams ? p.teams.map(t => t.id) : [])).join(',');
        return `<option value="${p.name}" data-id="${p.id}" data-team-ids="${teamIds}">${p.name}</option>`;
    }).join('');

    const allOptions = allProjects.map(p => {
        const teamIds = (p.team_ids || (p.teams ? p.teams.map(t => t.id) : [])).join(',');
        return `<option value="${p.name}" data-id="${p.id}" data-team-ids="${teamIds}">${p.name}</option>`;
    }).join('');

    if (elements.createTaskProject) elements.createTaskProject.innerHTML = activeOptions;
    if (elements.taskProject) elements.taskProject.innerHTML = allOptions;
}

export function populateProjectTeamCheckboxes() {
    const teams = state.teams || [];
    if (!elements.projectTeamsSelect) return;
    elements.projectTeamsSelect.innerHTML = teams.map(team => `
        <label class="project-team-checkbox">
            <input type="checkbox" value="${team.id}">
            <span>${team.name_he}</span>
        </label>
    `).join('');
}

export function populateMemberCheckboxes() {
    const members = state.members || [];
    const containers = document.querySelectorAll('.members-select');

    containers.forEach(container => {
        container.innerHTML = members.map(member => `
            <label class="member-checkbox" title="${member.name_he} - ${member.team_name}">
                <input type="checkbox" value="${member.name_en}"
                    data-img="/uploads/avatars/${member.avatar_path}">
                <img src="/uploads/avatars/${member.avatar_path}" class="avatar-sm"
                    onerror="this.src='/static/images/default.png'"> ${member.name_he}
            </label>
        `).join('');
    });
}

export function openCreateProjectModal() {
    if (!elements.projectModal) return;
    if (elements.projectModalId) elements.projectModalId.value = '';
    if (elements.projectModalNameInput) elements.projectModalNameInput.value = '';
    if (elements.projectModalTitle) elements.projectModalTitle.textContent = 'הוסף פרויקט חדש';
    if (elements.projectModalSaveBtn) elements.projectModalSaveBtn.textContent = 'צור פרויקט';
    if (elements.projectModalDeleteBtn) elements.projectModalDeleteBtn.style.display = 'none';
    if (elements.projectModalArchiveBtn) elements.projectModalArchiveBtn.style.display = 'none';

    // Reset checkboxes and pre-select active team if one is filtered
    if (elements.projectTeamsSelect) {
        const checkboxes = elements.projectTeamsSelect.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(cb => {
            if (state.activeTeamFilter && state.activeTeamFilter !== 'archive' && String(cb.value) === String(state.activeTeamFilter)) {
                cb.checked = true;
            } else {
                cb.checked = false;
            }
        });
    }

    elements.projectModal.style.display = 'block';
    if (elements.projectModalNameInput) elements.projectModalNameInput.focus();
}

export function openEditProjectModal(projectId) {
    if (!elements.projectModal) return;
    const project = (state.projects || []).find(p => p.id == projectId);
    if (!project) return;

    if (elements.projectModalId) elements.projectModalId.value = project.id;
    if (elements.projectModalNameInput) elements.projectModalNameInput.value = project.name;
    if (elements.projectModalTitle) elements.projectModalTitle.textContent = 'עריכת פרויקט';
    if (elements.projectModalSaveBtn) elements.projectModalSaveBtn.textContent = 'שמור שינויים';
    if (elements.projectModalDeleteBtn) elements.projectModalDeleteBtn.style.display = 'inline-flex';

    if (elements.projectModalArchiveBtn) {
        elements.projectModalArchiveBtn.style.display = 'inline-flex';
        if (project.is_archived) {
            elements.projectModalArchiveBtn.textContent = 'שחזר פרויקט מארכיון';
            elements.projectModalArchiveBtn.className = 'btn btn-success';
            elements.projectModalArchiveBtn.dataset.isArchived = 'true';
        } else {
            elements.projectModalArchiveBtn.textContent = 'העבר פרויקט לארכיון';
            elements.projectModalArchiveBtn.className = 'btn btn-secondary';
            elements.projectModalArchiveBtn.dataset.isArchived = 'false';
        }
    }

    const teamIds = (project.team_ids || (project.teams ? project.teams.map(t => t.id) : [])).map(String);
    if (elements.projectTeamsSelect) {
        const checkboxes = elements.projectTeamsSelect.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(cb => {
            cb.checked = teamIds.includes(String(cb.value));
        });
    }

    elements.projectModal.style.display = 'block';
    if (elements.projectModalNameInput) elements.projectModalNameInput.focus();
}

export function getSelectedProjectTeamIds() {
    if (!elements.projectTeamsSelect) return [];
    const checked = elements.projectTeamsSelect.querySelectorAll('input[type="checkbox"]:checked');
    return Array.from(checked).map(cb => parseInt(cb.value));
}

export function openEditModal(taskItem) {
    const taskId = taskItem.dataset.id;
    const taskNameElem = taskItem.querySelector('.task-name');

    elements.taskNameInput.value = taskNameElem ? taskNameElem.textContent.trim() : '';
    elements.taskNotes.value = taskItem.dataset.notes || '';

    const statusBadge = taskItem.querySelector('.status-badge');
    let statusClass = 'status-inprogress';
    if (statusBadge) {
        statusBadge.classList.forEach(cls => {
            if (cls.startsWith('status-')) statusClass = cls;
        });
    }
    elements.taskStatus.value = getStatusFromClass(statusClass);
    elements.taskPriority.value = taskItem.dataset.priority || 'none';

    const projectCard = taskItem.closest('.project-card');
    if (projectCard && elements.taskProject) {
        const projName = projectCard.dataset.projectName || (projectCard.querySelector('.project-name-text') ? projectCard.querySelector('.project-name-text').textContent.trim() : '');
        elements.taskProject.value = projName;
    }

    // Reset and check members
    document.querySelectorAll('#taskModal .members-select input[type="checkbox"]').forEach(cb => cb.checked = false);

    const avatars = taskItem.querySelectorAll('.avatar');
    avatars.forEach(img => {
        const memberName = img.dataset.memberName;
        if (memberName) {
            const checkbox = document.querySelector(`#taskModal .members-select input[value="${memberName}"]`);
            if (checkbox) checkbox.checked = true;
        } else {
            const src = img.getAttribute('src');
            if (src) {
                const checkbox = document.querySelector(`#taskModal .members-select input[data-img="${src}"]`);
                if (checkbox) checkbox.checked = true;
            }
        }
    });

    // Set Team
    const isArchived = taskItem.dataset.isArchived === 'true';
    elements.taskTeam.value = taskItem.dataset.teamId || '';

    // Archive / Unarchive button
    if (elements.archiveBtn) {
        elements.archiveBtn.style.display = 'inline-flex';
        if (isArchived) {
            elements.archiveBtn.textContent = 'שחזר מארכיון';
            elements.archiveBtn.className = 'btn btn-success';
            elements.archiveBtn.dataset.isArchived = 'true';
        } else {
            elements.archiveBtn.textContent = 'העבר לארכיון';
            elements.archiveBtn.className = 'btn btn-secondary';
            elements.archiveBtn.dataset.isArchived = 'false';
        }
    }

    elements.taskStartDate.value = '';
    elements.taskEndDate.value = '';
    if (taskItem.dataset.startDate) elements.taskStartDate.value = formatDateFromISO(taskItem.dataset.startDate);
    if (taskItem.dataset.endDate) elements.taskEndDate.value = formatDateFromISO(taskItem.dataset.endDate);

    if (elements.modal) {
        elements.modal.dataset.currentTaskId = taskId;
    }

    if (elements.newSubtaskInput) elements.newSubtaskInput.value = '';
    if (elements.newCommentInput) elements.newCommentInput.value = '';

    loadAndRenderTaskSubtasks(taskId);
    loadAndRenderTaskComments(taskId);

    elements.modal.style.display = 'block';
}

// Subtasks and Comments UI helpers
export function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

export async function loadAndRenderTaskSubtasks(taskId) {
    if (!elements.subtasksList) return;
    elements.subtasksList.innerHTML = '<div class="empty-subtasks-text">טוען צ\'ק-ליסט...</div>';
    try {
        const subtasks = await fetchTaskSubtasks(taskId);
        renderSubtasks(subtasks, taskId);
    } catch (err) {
        console.error('Failed to load subtasks:', err);
        elements.subtasksList.innerHTML = '<div class="empty-subtasks-text">שגיאה בטעינת צ\'ק-ליסט</div>';
    }
}

export function renderSubtasks(subtasks, taskId) {
    if (!elements.subtasksList) return;
    const list = Array.isArray(subtasks) ? subtasks : [];
    const total = list.length;
    const completed = list.filter(s => s.is_completed).length;
    const percent = total > 0 ? Math.round((completed / total) * 100) : 0;

    if (elements.subtaskProgressText) {
        elements.subtaskProgressText.textContent = `${completed}/${total} (${percent}%)`;
    }
    if (elements.subtaskProgressBar) {
        elements.subtaskProgressBar.style.width = `${percent}%`;
    }

    // Immediately update subtask badges on task cards across Grid, Kanban, and Gantt
    updateTaskSubtaskBadges(taskId, completed, total);

    if (total === 0) {
        elements.subtasksList.innerHTML = '<div class="empty-subtasks-text">אין עדיין פריטים בצ\'ק-ליסט. הוסף פריט ראשון למטה.</div>';
        return;
    }

    elements.subtasksList.innerHTML = list.map(item => `
        <div class="subtask-item ${item.is_completed ? 'completed' : ''}" data-id="${item.id}" data-task-id="${taskId}">
            <input type="checkbox" class="subtask-checkbox" ${item.is_completed ? 'checked' : ''} data-id="${item.id}" title="סמן כהושלם">
            <span class="subtask-title">${escapeHtml(item.title)}</span>
            <button type="button" class="subtask-delete-btn" data-id="${item.id}" title="מחק פריט">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
            </button>
        </div>
    `).join('');
}

export async function loadAndRenderTaskComments(taskId) {
    if (!elements.commentsList) return;
    elements.commentsList.innerHTML = '<div class="empty-comments-text">טוען תגובות...</div>';
    populateCommentAuthors();
    try {
        const comments = await fetchTaskComments(taskId);
        renderComments(comments, taskId);
    } catch (err) {
        console.error('Failed to load comments:', err);
        elements.commentsList.innerHTML = '<div class="empty-comments-text">שגיאה בטעינת תגובות</div>';
    }
}

export function populateCommentAuthors() {
    if (!elements.commentAuthorSelect) return;
    const members = state.members || [];
    const savedAuthor = localStorage.getItem('teamtasks_last_author') || '';

    let options = '<option value="">בחר/י מגיב/ה...</option>';
    options += members.map(m => {
        const isMatch = (savedAuthor && (savedAuthor === String(m.id) || savedAuthor === m.name_he || savedAuthor === m.name_en));
        return `<option value="${m.id}" data-name="${m.name_he}" data-avatar="${m.avatar_path || 'default.png'}" ${isMatch ? 'selected' : ''}>${m.name_he}</option>`;
    }).join('');
    options += `<option value="guest" data-name="חבר צוות" data-avatar="default.png" ${savedAuthor === 'guest' ? 'selected' : ''}>חבר צוות (אורח)</option>`;
    elements.commentAuthorSelect.innerHTML = options;
}

export function renderComments(comments, taskId) {
    if (!elements.commentsList) return;
    const list = Array.isArray(comments) ? comments : [];
    const count = list.length;
    if (elements.commentCounter) {
        elements.commentCounter.textContent = count;
    }

    // Immediately update comment badges on task cards across Grid and Kanban
    updateTaskCommentBadges(taskId, count);

    if (count === 0) {
        elements.commentsList.innerHTML = '<div class="empty-comments-text">אין עדיין תגובות למשימה זו. כתוב את התגובה הראשונה למטה!</div>';
        return;
    }

    elements.commentsList.innerHTML = list.map(c => `
        <div class="comment-item" data-id="${c.id}" data-task-id="${taskId}">
            <img src="/uploads/avatars/${c.author_avatar || 'default.png'}"
                 class="comment-avatar"
                 onerror="this.src='/static/images/default.png'"
                 alt="${escapeHtml(c.author_name)}">
            <div class="comment-content-wrap">
                <div class="comment-header">
                    <span class="comment-author">${escapeHtml(c.author_name)}</span>
                    <span class="comment-date">${c.created_at || ''}</span>
                    <button type="button" class="comment-delete-btn" data-id="${c.id}" title="מחק תגובה">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                    </button>
                </div>
                <div class="comment-text">${escapeHtml(c.content)}</div>
            </div>
        </div>
    `).join('');
}

export function switchViewMode(mode) {
    state.viewMode = mode;
    localStorage.setItem('teamtasks_view_mode', mode);
    if (document.body) {
        document.body.dataset.viewMode = mode;
    }

    const btnGrid = document.getElementById('viewBtnGrid');
    const btnKanban = document.getElementById('viewBtnKanban');
    const btnGantt = document.getElementById('viewBtnGantt');

    if (btnGrid) btnGrid.classList.toggle('active', mode === 'grid');
    if (btnKanban) btnKanban.classList.toggle('active', mode === 'kanban');
    if (btnGantt) btnGantt.classList.toggle('active', mode === 'gantt');

    const containerGrid = document.getElementById('viewContainerGrid');
    const containerKanban = document.getElementById('viewContainerKanban');
    const containerGantt = document.getElementById('viewContainerGantt');

    if (containerGrid) containerGrid.style.display = (mode === 'grid' ? '' : 'none');
    if (containerKanban) containerKanban.style.display = (mode === 'kanban' ? '' : 'none');
    if (containerGantt) containerGantt.style.display = (mode === 'gantt' ? '' : 'none');

    const addProjectBtn = document.getElementById('addProjectBtn');
    if (addProjectBtn) {
        addProjectBtn.style.display = (mode === 'grid' ? '' : 'none');
    }

    const printLink = document.querySelector('.navbar-meta .print-link');
    if (printLink) {
        printLink.href = (mode === 'gantt') ? '/print?view=gantt' : '/print';
    }

    if (mode === 'kanban') {
        updateKanbanCounters();
    } else if (mode === 'gantt') {
        renderGantt();
    }
}

export function openCreateModal(projectName = null, teamId = null, initialStatus = null) {
    elements.createTaskNameInput.value = '';
    
    if (elements.createTaskProject) {
        if (projectName) {
            elements.createTaskProject.value = projectName;
        } else if (elements.createTaskProject.options.length > 0) {
            elements.createTaskProject.selectedIndex = 0;
        }
    }

    elements.createTaskStatus.value = initialStatus || 'status-notstarted';
    elements.createTaskPriority.value = 'none';
    elements.createTaskNotes.value = '';

    // Determine team selection
    let defaultTeam = '';
    if (teamId) {
        defaultTeam = teamId;
    } else {
        const currentProjName = elements.createTaskProject ? elements.createTaskProject.value : '';
        const proj = (state.projects || []).find(p => p.name === currentProjName);
        if (proj) {
            const projTeamIds = proj.team_ids || (proj.teams ? proj.teams.map(t => t.id) : []);
            if (projTeamIds.length > 0) {
                if (state.activeTeamFilter && projTeamIds.map(String).includes(String(state.activeTeamFilter))) {
                    defaultTeam = state.activeTeamFilter;
                } else {
                    defaultTeam = projTeamIds[0];
                }
            }
        }
        if (!defaultTeam && state.activeTeamFilter && state.activeTeamFilter !== 'archive') {
            defaultTeam = state.activeTeamFilter;
        }
    }
    elements.createTaskTeam.value = defaultTeam;

    elements.createTaskStartDate.value = '';
    elements.createTaskEndDate.value = '';

    document.querySelectorAll('#createTaskModal .members-select input[type="checkbox"]').forEach(cb => cb.checked = false);

    elements.createModal.style.display = 'block';
    elements.createModal.style.zIndex = 2000;
    elements.createModal.style.visibility = 'visible';
}

let pendingRefresh = false;
let lastListenersCallback = null;

export function setLastListenersCallback(cb) {
    if (typeof cb === 'function') {
        lastListenersCallback = cb;
    }
}

export function isAnyModalOpen() {
    const taskModal = document.getElementById('taskModal');
    const createTaskModal = document.getElementById('createTaskModal');
    const projectModal = document.getElementById('projectModal');
    return (
        (taskModal && taskModal.style.display === 'block') ||
        (createTaskModal && createTaskModal.style.display === 'block') ||
        (projectModal && projectModal.style.display === 'block')
    );
}

export function setPendingRefresh(val) {
    pendingRefresh = val;
}

export function closeModals() {
    if (elements.modal) elements.modal.style.display = 'none';
    if (elements.createModal) elements.createModal.style.display = 'none';
    if (elements.projectModal) elements.projectModal.style.display = 'none';
    state.currentTaskItem = null;

    if (pendingRefresh) {
        pendingRefresh = false;
        const cb = lastListenersCallback || (window.mainEvents ? window.mainEvents.attachEventListeners : null);
        refreshContent(cb);
    }
}

export function updateTaskSubtaskBadges(taskId, completed, total) {
    if (!taskId) return;
    const idStr = String(taskId);
    const subtaskSvg = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 11 12 14 22 4"></polyline><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path></svg>';
    const isAllDone = (total > 0 && completed === total);
    const textContent = `${completed}/${total}`;
    const titleText = `${completed}/${total} תתי-משימות הושלמו`;

    // 1. Projects Grid task items
    const gridItems = document.querySelectorAll(`.projects-grid .task-item[data-id="${idStr}"]`);
    gridItems.forEach(item => {
        const meta = item.querySelector('.task-meta');
        if (!meta) return;
        let badgesContainer = meta.querySelector('.task-meta-badges');
        let badge = badgesContainer ? badgesContainer.querySelector('.subtask-badge') : null;

        if (total > 0) {
            if (!badgesContainer) {
                badgesContainer = document.createElement('div');
                badgesContainer.className = 'task-meta-badges';
                const startContainer = meta.querySelector('.task-meta-start');
                if (startContainer) {
                    startContainer.appendChild(badgesContainer);
                } else {
                    meta.appendChild(badgesContainer);
                }
            }
            badgesContainer.style.display = 'inline-flex';
            if (!badge) {
                badge = document.createElement('span');
                badge.className = 'subtask-badge';
                badge.innerHTML = `${subtaskSvg}<span></span>`;
                badgesContainer.insertBefore(badge, badgesContainer.firstChild);
            }
            badge.className = `subtask-badge ${isAllDone ? 'all-done' : ''}`;
            badge.setAttribute('title', titleText);
            const span = badge.querySelector('span');
            if (span) span.textContent = textContent;
        } else if (badge) {
            badge.remove();
            if (badgesContainer && badgesContainer.children.length === 0) {
                badgesContainer.style.display = 'none';
            }
        }
    });

    // 2. Kanban cards
    const kanbanCards = document.querySelectorAll(`.kanban-card[data-id="${idStr}"]`);
    kanbanCards.forEach(card => {
        const meta = card.querySelector('.kanban-card-meta');
        if (!meta) return;
        let badgesContainer = meta.querySelector('.kanban-card-badges');
        if (!badgesContainer && total > 0) {
            badgesContainer = document.createElement('div');
            badgesContainer.className = 'kanban-card-badges';
            meta.appendChild(badgesContainer);
        }
        if (!badgesContainer) return;
        let badge = badgesContainer.querySelector('.subtask-badge');

        if (total > 0) {
            if (!badge) {
                badge = document.createElement('span');
                badge.className = 'subtask-badge';
                badge.innerHTML = `${subtaskSvg}<span></span>`;
                const nextBadge = badgesContainer.querySelector('.comment-badge, .kanban-date-badge');
                if (nextBadge) {
                    badgesContainer.insertBefore(badge, nextBadge);
                } else {
                    badgesContainer.appendChild(badge);
                }
            }
            badge.className = `subtask-badge ${isAllDone ? 'all-done' : ''}`;
            badge.setAttribute('title', titleText);
            const span = badge.querySelector('span');
            if (span) span.textContent = textContent;
        } else if (badge) {
            badge.remove();
        }
    });

    // 3. Gantt view
    if (state.viewMode === 'gantt' && typeof renderGantt === 'function') {
        renderGantt();
    }
}

export function updateTaskCommentBadges(taskId, count) {
    if (!taskId) return;
    const idStr = String(taskId);
    const commentSvg = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>';
    const titleText = `${count} תגובות`;

    // 1. Projects Grid task items
    const gridItems = document.querySelectorAll(`.projects-grid .task-item[data-id="${idStr}"]`);
    gridItems.forEach(item => {
        const meta = item.querySelector('.task-meta');
        if (!meta) return;
        let badgesContainer = meta.querySelector('.task-meta-badges');
        let badge = badgesContainer ? badgesContainer.querySelector('.comment-badge') : null;

        if (count > 0) {
            if (!badgesContainer) {
                badgesContainer = document.createElement('div');
                badgesContainer.className = 'task-meta-badges';
                const startContainer = meta.querySelector('.task-meta-start');
                if (startContainer) {
                    startContainer.appendChild(badgesContainer);
                } else {
                    meta.appendChild(badgesContainer);
                }
            }
            badgesContainer.style.display = 'inline-flex';
            if (!badge) {
                badge = document.createElement('span');
                badge.className = 'comment-badge';
                badge.innerHTML = `${commentSvg}<span></span>`;
                badgesContainer.appendChild(badge);
            }
            badge.setAttribute('title', titleText);
            const span = badge.querySelector('span');
            if (span) span.textContent = count;
        } else if (badge) {
            badge.remove();
            if (badgesContainer && badgesContainer.children.length === 0) {
                badgesContainer.style.display = 'none';
            }
        }
    });

    // 2. Kanban cards
    const kanbanCards = document.querySelectorAll(`.kanban-card[data-id="${idStr}"]`);
    kanbanCards.forEach(card => {
        const meta = card.querySelector('.kanban-card-meta');
        if (!meta) return;
        let badgesContainer = meta.querySelector('.kanban-card-badges');
        if (!badgesContainer && count > 0) {
            badgesContainer = document.createElement('div');
            badgesContainer.className = 'kanban-card-badges';
            meta.appendChild(badgesContainer);
        }
        if (!badgesContainer) return;
        let badge = badgesContainer.querySelector('.comment-badge');

        if (count > 0) {
            if (!badge) {
                badge = document.createElement('span');
                badge.className = 'comment-badge';
                badge.innerHTML = `${commentSvg}<span></span>`;
                const dateBadge = badgesContainer.querySelector('.kanban-date-badge');
                if (dateBadge) {
                    badgesContainer.insertBefore(badge, dateBadge);
                } else {
                    badgesContainer.appendChild(badge);
                }
            }
            badge.setAttribute('title', titleText);
            const span = badge.querySelector('span');
            if (span) span.textContent = count;
        } else if (badge) {
            badge.remove();
        }
    });
}

export function getSelectedMembers(modalId) {
    const checkboxes = document.querySelectorAll(`#${modalId} .members-select input[type="checkbox"]:checked`);
    return Array.from(checkboxes).map(cb => cb.value);
}

export function applyFilters() {
    const allTasks = document.querySelectorAll('.task-item');

    allTasks.forEach(task => {
        let visible = true;

        if (state.activeTeamFilter && state.activeTeamFilter !== 'archive') {
            const taskTeamId = task.dataset.teamId;
            const isTeamMatch = (taskTeamId && String(taskTeamId) === String(state.activeTeamFilter));

            let hasTeamMember = false;
            const activeTeamStr = String(state.activeTeamFilter);
            const activeTeamMembers = state.members
                .filter(m => {
                    if (Array.isArray(m.team_ids) && m.team_ids.map(String).includes(activeTeamStr)) {
                        return true;
                    }
                    return String(m.team_id) === activeTeamStr;
                })
                .map(m => m.name_en);

            if (activeTeamMembers.length > 0) {
                const avatars = task.querySelectorAll('.avatar');
                avatars.forEach(avatar => {
                    if (activeTeamMembers.includes(avatar.dataset.memberName)) {
                        hasTeamMember = true;
                    }
                });
            }

            if (!isTeamMatch && !hasTeamMember) {
                visible = false;
            }
        }

        // Check Member Filter
        if (state.activeMemberFilter && visible) {
            const avatars = task.querySelectorAll('.avatar');
            let hasMember = false;
            avatars.forEach(avatar => {
                const memberName = avatar.dataset.memberName;
                if (memberName && memberName === state.activeMemberFilter) {
                    hasMember = true;
                }
            });
            if (!hasMember) visible = false;
        }

        // Check Status Filter
        if (state.statusFilter && state.statusFilter !== 'all' && visible) {
            const taskStatus = task.dataset.status;
            if (state.statusFilter === 'not-done') {
                if (taskStatus === 'status-done') {
                    visible = false;
                }
            } else if (taskStatus !== state.statusFilter) {
                visible = false;
            }
        }

        // Check Priority Filter
        if (state.priorityFilter && state.priorityFilter !== 'all' && visible) {
            const taskPriority = task.dataset.priority;
            if (taskPriority !== state.priorityFilter) {
                visible = false;
            }
        }

        if (task.classList.contains('search-hidden')) {
            visible = false;
        }

        if (visible) {
            task.classList.remove('filtered-hidden');
        } else {
            task.classList.add('filtered-hidden');
        }
    });

    const isTaskFilterActive = (state.activeMemberFilter !== null) || (state.statusFilter && state.statusFilter !== 'all') || (state.priorityFilter && state.priorityFilter !== 'all');
    const searchQuery = (elements.searchBox ? elements.searchBox.value.trim().toLowerCase() : '');

    let visibleProjectsCount = 0;

    document.querySelectorAll('.project-card').forEach(card => {
        const cardTeamIds = (card.dataset.teamIds || '').split(',').map(s => s.trim()).filter(Boolean);
        const cardProjName = (card.dataset.projectName || '').toLowerCase();
        const totalTasksInCard = card.querySelectorAll('.task-item').length;
        const visibleTasks = card.querySelectorAll('.task-item:not(.filtered-hidden):not(.search-hidden)');

        let cardVisible = true;

        if (state.activeTeamFilter && state.activeTeamFilter !== 'archive') {
            const isTeamAssigned = cardTeamIds.includes(String(state.activeTeamFilter));
            const hasVisibleTasks = visibleTasks.length > 0;
            if (!isTeamAssigned && !hasVisibleTasks) {
                cardVisible = false;
            }
        } else if (state.activeTeamFilter === 'archive') {
            if (visibleTasks.length === 0) {
                cardVisible = false;
            }
        }

        if (cardVisible) {
            if (totalTasksInCard === 0) {
                // Empty project
                if (searchQuery) {
                    cardVisible = cardProjName.includes(searchQuery);
                } else if (isTaskFilterActive) {
                    cardVisible = false;
                } else {
                    cardVisible = true;
                }
            } else {
                // Has tasks
                if (searchQuery) {
                    cardVisible = (visibleTasks.length > 0) || cardProjName.includes(searchQuery);
                } else if (visibleTasks.length === 0) {
                    cardVisible = false;
                } else {
                    cardVisible = true;
                }
            }
        }

        if (cardVisible) {
            card.classList.remove('filtered-hidden');
            visibleProjectsCount++;
        } else {
            card.classList.add('filtered-hidden');
        }
    });

    const emptyStateEl = elements.projectsEmptyState || document.getElementById('projectsEmptyState');
    if (emptyStateEl) {
        emptyStateEl.style.display = (visibleProjectsCount === 0) ? 'flex' : 'none';
    }
    const projectsGrid = elements.projectsGrid || document.querySelector('.projects-grid');
    if (projectsGrid) {
        projectsGrid.style.display = (visibleProjectsCount === 0) ? 'none' : '';
    }

    updateMemberFiltersVisibility();
    updateFilterValidationUI();
    updateKanbanCounters();
    if (state.viewMode === 'gantt') {
        renderGantt();
    }
}

export function updateMemberFiltersVisibility() {
    if (!elements.memberFilterButtons) return;

    const activeTeam = state.activeTeamFilter;
    const isArchive = activeTeam === 'archive';

    elements.memberFilterButtons.forEach(btn => {
        const memberTeamId = btn.dataset.teamId;
        const memberTeamIds = (btn.dataset.teamIds || '').split(',').map(s => s.trim()).filter(Boolean);

        if (!activeTeam || isArchive) {
            btn.style.display = '';
            return;
        }

        if (memberTeamIds.includes(String(activeTeam)) || String(memberTeamId) === String(activeTeam)) {
            btn.style.display = '';
        } else {
            btn.style.display = 'none';
        }
    });
}

function updateFilterValidationUI() {
    if (elements.memberFilterButtons) {
        elements.memberFilterButtons.forEach(btn => {
            const member = btn.dataset.member;
            if (member === state.activeMemberFilter) {
                btn.classList.add('active');
                btn.style.boxShadow = 'none';
            } else {
                btn.classList.remove('active');
                btn.style.boxShadow = 'none';
            }
        });
    }

    if (elements.teamFilterButtons) {
        elements.teamFilterButtons.forEach(btn => {
            const teamId = btn.dataset.teamId;
            const mode = btn.dataset.mode;

            if (mode === 'archive') {
                if (state.activeTeamFilter === 'archive') btn.classList.add('active');
                else btn.classList.remove('active');
            } else {
                if (String(state.activeTeamFilter) === String(teamId)) btn.classList.add('active');
                else btn.classList.remove('active');
            }
        });
    }
}

export async function refreshContent(attachedListenersCallback) {
    if (typeof attachedListenersCallback === 'function') {
        lastListenersCallback = attachedListenersCallback;
    }

    if (isAnyModalOpen()) {
        pendingRefresh = true;
        return;
    }

    try {
        const activeElement = document.activeElement;
        const activeId = activeElement ? activeElement.id : null;
        const currentSearchInput = document.getElementById('searchBox');
        const searchVal = currentSearchInput ? currentSearchInput.value : '';
        const selectionStart = (activeId === 'searchBox' && currentSearchInput) ? currentSearchInput.selectionStart : 0;
        const selectionEnd = (activeId === 'searchBox' && currentSearchInput) ? currentSearchInput.selectionEnd : 0;

        const [teams, members, projects, specialDays] = await Promise.all([
            fetchTeams(),
            fetchMembers(),
            fetchProjects(),
            fetchSpecialDays()
        ]);
        setTeams(teams);
        setMembers(members);
        setProjects(projects);
        setSpecialDays(specialDays || []);

        const html = await fetchPageContent(window.location.href);
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');

        const newMainContainer = doc.querySelector('.main-container');
        const newNavbar = doc.querySelector('.navbar');

        if (newMainContainer) {
            document.querySelector('.main-container').innerHTML = newMainContainer.innerHTML;
        }

        const currentNavbar = document.querySelector('.navbar');
        if (newNavbar && currentNavbar.innerHTML !== newNavbar.innerHTML) {
            currentNavbar.innerHTML = newNavbar.innerHTML;
        }

        const newSearchInput = document.getElementById('searchBox');
        if (newSearchInput && searchVal) {
            newSearchInput.value = searchVal;
        }

        if (activeId === 'searchBox') {
            const el = document.getElementById('searchBox');
            if (el) {
                el.focus();
                el.setSelectionRange(selectionStart, selectionEnd);
            }
        }

        updateDOMElements();
        populateDropdowns();
        populateProjectDropdowns();
        populateProjectTeamCheckboxes();
        populateMemberCheckboxes();

        if (typeof lastListenersCallback === 'function') {
            lastListenersCallback();
        }

        if (elements.filterStatus && state.statusFilter) {
            elements.filterStatus.value = state.statusFilter;
        }
        if (elements.filterPriority && state.priorityFilter) {
            elements.filterPriority.value = state.priorityFilter;
        }

        applyFilters();
        switchViewMode(state.viewMode || 'grid');

    } catch (error) {
        console.error('Error refreshing content:', error);
    }
}
