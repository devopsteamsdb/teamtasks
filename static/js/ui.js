// UI Manipulation
import { state } from './state.js';
import { formatDateFromISO, getStatusFromClass, getFlatpickrConfig } from './utils.js';
import { fetchPageContent } from './api.js';

// DOM Elements Cache
export const elements = {};

export function updateDOMElements() {
    elements.modal = document.getElementById('taskModal');
    elements.createModal = document.getElementById('createTaskModal');
    elements.closeModal = document.querySelector('.close-modal');
    elements.closeCreateModal = document.querySelector('.close-modal-create');

    elements.saveBtn = document.getElementById('saveBtn');
    elements.deleteBtn = document.getElementById('deleteBtn');
    elements.createSaveBtn = document.getElementById('createSaveBtn');
    elements.addTaskBtn = document.getElementById('addTaskBtn');

    elements.taskNameInput = document.getElementById('taskNameInput');
    elements.projectNameInput = document.getElementById('projectNameInput');
    elements.taskStatus = document.getElementById('taskStatus');
    elements.taskPriority = document.getElementById('taskPriority');
    elements.taskNotes = document.getElementById('taskNotes');
    elements.taskTeam = document.getElementById('taskTeam');
    elements.taskStartDate = document.getElementById('taskStartDate');
    elements.taskEndDate = document.getElementById('taskEndDate');

    elements.createTaskNameInput = document.getElementById('createTaskNameInput');
    elements.createProjectNameInput = document.getElementById('createProjectNameInput');
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
}

export function initializeFlatpickr() {
    const config = getFlatpickrConfig();
    flatpickr("#taskStartDate", config);
    flatpickr("#taskEndDate", config);
    flatpickr("#createTaskStartDate", config);
    flatpickr("#createTaskEndDate", config);
}

export function populateDropdowns() {
    const teams = state.teams;
    const options = teams.map(team =>
        `<option value="${team.id}">${team.name_he}</option>`
    ).join('');

    const defaultOption = '<option value="">בחר צוות...</option>';
    const archiveOption = '<option value="archive">ארכיון</option>';

    if (elements.createTaskTeam) elements.createTaskTeam.innerHTML = defaultOption + options;
    if (elements.taskTeam) elements.taskTeam.innerHTML = defaultOption + options + archiveOption;
}

export function populateMemberCheckboxes() {
    const members = state.members;
    const containers = document.querySelectorAll('.members-select');

    containers.forEach(container => {
        container.innerHTML = members.map(member => `
                <label class="member-checkbox">
                    <input type="checkbox" value="${member.name_en}"
                        data-img="/uploads/avatars/${member.avatar_path}">
                    <img src="/uploads/avatars/${member.avatar_path}" class="avatar-sm"
                        onerror="this.src='/static/images/default.png'"> ${member.name_he}
                </label>
            `).join('');
    });
}

export function openEditModal(taskItem) {
    const taskId = taskItem.dataset.id;
    const taskNameElem = taskItem.querySelector('.task-name');

    elements.taskNameInput.value = taskNameElem ? taskNameElem.textContent : '';
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
    if (projectCard) {
        const projectTitle = projectCard.querySelector('.project-title');
        elements.projectNameInput.value = projectTitle ? projectTitle.textContent.trim() : '';
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

    // Set Team or Archive
    const isArchived = taskItem.dataset.isArchived === 'true';
    if (isArchived) {
        if (elements.taskTeam.querySelector('option[value="archive"]')) {
            elements.taskTeam.value = 'archive';
        } else {
            elements.taskTeam.value = '';
        }
    } else {
        elements.taskTeam.value = taskItem.dataset.teamId || '';
    }

    elements.taskStartDate.value = '';
    elements.taskEndDate.value = '';
    if (taskItem.dataset.startDate) elements.taskStartDate.value = formatDateFromISO(taskItem.dataset.startDate);
    if (taskItem.dataset.endDate) elements.taskEndDate.value = formatDateFromISO(taskItem.dataset.endDate);

    elements.modal.style.display = 'block';
}

export function openCreateModal(projectName = null, teamId = null) {
    elements.createTaskNameInput.value = '';
    elements.createProjectNameInput.value = projectName || '';
    elements.createTaskStatus.value = 'status-notstarted';
    elements.createTaskPriority.value = 'none';
    elements.createTaskNotes.value = '';

    // Determine team selection
    let defaultTeam = '';
    if (teamId) {
        defaultTeam = teamId;
    } else if (state.activeTeamFilter && state.activeTeamFilter !== 'archive') {
        defaultTeam = state.activeTeamFilter;
    }
    elements.createTaskTeam.value = defaultTeam;

    elements.createTaskStartDate.value = '';
    elements.createTaskEndDate.value = '';

    document.querySelectorAll('#createTaskModal .members-select input[type="checkbox"]').forEach(cb => cb.checked = false);

    elements.createModal.style.display = 'block';
    elements.createModal.style.zIndex = 2000;
    elements.createModal.style.visibility = 'visible';
}

export function closeModals() {
    if (elements.modal) elements.modal.style.display = 'none';
    if (elements.createModal) elements.createModal.style.display = 'none';
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
            if (taskTeamId && taskTeamId !== state.activeTeamFilter) {
                visible = false;
            } else if (!taskTeamId) {
                visible = false;
            }
        }

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

        if (task.classList.contains('search-hidden')) {
            visible = false;
        }

        if (visible) {
            task.classList.remove('filtered-hidden');
        } else {
            task.classList.add('filtered-hidden');
        }
    });

    document.querySelectorAll('.project-card').forEach(card => {
        const visibleTasks = card.querySelectorAll('.task-item:not(.filtered-hidden):not(.search-hidden)');
        if (visibleTasks.length === 0) {
            card.classList.add('filtered-hidden');
        } else {
            card.classList.remove('filtered-hidden');
        }
    });

    updateMemberFiltersVisibility();
    updateFilterValidationUI();
}

export function updateMemberFiltersVisibility() {
    if (!elements.memberFilterButtons) return;

    const activeTeam = state.activeTeamFilter;
    const isArchive = activeTeam === 'archive';

    elements.memberFilterButtons.forEach(btn => {
        const memberTeamId = btn.dataset.teamId;

        // Show all if no team selected or archive mode (assuming archive shows all members for now)
        if (!activeTeam || isArchive) {
            btn.style.display = ''; // Reset to default (inline-block or flex)
            return;
        }

        // Filter by team
        if (memberTeamId === activeTeam) {
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
                btn.style.boxShadow = `0 0 0 2px ${btn.style.borderColor || '#3b82f6'}`;
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
                if (state.activeTeamFilter === teamId) btn.classList.add('active');
                else btn.classList.remove('active');
            }
        });
    }
}

export async function refreshContent(attachedListenersCallback) {
    try {
        const activeElement = document.activeElement;
        const activeId = activeElement ? activeElement.id : null;
        const selectionStart = (activeId === 'searchBox') ? activeElement.selectionStart : 0;
        const selectionEnd = (activeId === 'searchBox') ? activeElement.selectionEnd : 0;

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

        if (activeId === 'searchBox') {
            const el = document.getElementById('searchBox');
            if (el) {
                el.focus();
                el.setSelectionRange(selectionStart, selectionEnd);
            }
        }

        updateDOMElements();
        populateDropdowns();
        populateMemberCheckboxes();

        if (typeof attachedListenersCallback === 'function') {
            attachedListenersCallback();
        }

        applyFilters();

    } catch (error) {
        console.error('Error refreshing content:', error);
    }
}
