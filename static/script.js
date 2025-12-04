document.addEventListener('DOMContentLoaded', () => {
    // State
    let teams = [];
    let members = [];
    let currentTaskItem = null;
    let activeTeamFilter = null;
    let activeMemberFilter = null;
    let searchTimeout;

    // Listen for member filter reset event
    window.addEventListener('resetMemberFilter', function () {
        activeMemberFilter = null;
        applyFilters();
    });

    // DOM Elements - Modals
    const modal = document.getElementById('taskModal');
    const createModal = document.getElementById('createTaskModal');
    const closeModal = document.querySelector('.close-modal');
    const closeCreateModal = document.querySelector('.close-modal-create');

    // DOM Elements - Forms
    const saveBtn = document.getElementById('saveBtn');
    const deleteBtn = document.getElementById('deleteBtn');
    const createSaveBtn = document.getElementById('createSaveBtn');

    // DOM Elements - Inputs (Edit)
    const taskNameInput = document.getElementById('taskNameInput');
    const projectNameInput = document.getElementById('projectNameInput');
    const taskStatus = document.getElementById('taskStatus');
    const taskPriority = document.getElementById('taskPriority');
    const taskNotes = document.getElementById('taskNotes');
    const taskTeam = document.getElementById('taskTeam');

    // DOM Elements - Inputs (Create)
    const createTaskNameInput = document.getElementById('createTaskNameInput');
    const createProjectNameInput = document.getElementById('createProjectNameInput');
    const createTaskStatus = document.getElementById('createTaskStatus');
    const createTaskPriority = document.getElementById('createTaskPriority');
    const createTaskNotes = document.getElementById('createTaskNotes');
    const createTaskTeam = document.getElementById('createTaskTeam');

    // DOM Elements - Search & Filter
    const searchBox = document.getElementById('searchBox');
    const clearSearchBtn = document.getElementById('clearSearch');
    const teamFilterButtons = document.querySelectorAll('.filter-team-btn');
    const memberFilterButtons = document.querySelectorAll('.filter-avatar-btn');

    // Initialize
    init();

    async function init() {
        await Promise.all([loadTeams(), loadMembers()]);
        populateDropdowns();
        populateMemberCheckboxes();
        attachEventListeners();

        // Check URL for team filter
        const urlParams = new URLSearchParams(window.location.search);
        const teamId = urlParams.get('team');
        if (teamId) {
            const btn = document.querySelector(`.filter-team-btn[data-team-id="${teamId}"]`);
            if (btn) btn.click();
        }
    }

    // Data Loading
    async function loadTeams() {
        try {
            const response = await fetch('/api/teams');
            teams = await response.json();
        } catch (error) {
            console.error('Error loading teams:', error);
        }
    }

    async function loadMembers() {
        try {
            const response = await fetch('/api/members');
            members = await response.json();
        } catch (error) {
            console.error('Error loading members:', error);
        }
    }

    // UI Population
    function populateDropdowns() {
        const options = teams.map(team =>
            `<option value="${team.id}">${team.name_he}</option>`
        ).join('');

        const defaultOption = '<option value="">בחר צוות...</option>';

        if (createTaskTeam) createTaskTeam.innerHTML = defaultOption + options;
        if (taskTeam) taskTeam.innerHTML = defaultOption + options;
    }

    function populateMemberCheckboxes() {
        const containers = document.querySelectorAll('.members-select');

        containers.forEach(container => {
            container.innerHTML = members.map(member => `
                <label class="member-checkbox">
                    <input type="checkbox" value="${member.name_en}" 
                           data-img="/static/images/${member.avatar_path}">
                    <img src="/static/images/${member.avatar_path}" class="avatar-sm"> ${member.name_he}
                </label>
            `).join('');
        });
    }

    // Event Listeners
    function attachEventListeners() {
        // Modals
        if (closeModal) closeModal.addEventListener('click', () => modal.style.display = 'none');
        if (closeCreateModal) closeCreateModal.addEventListener('click', () => createModal.style.display = 'none');

        window.addEventListener('click', (e) => {
            if (e.target == modal) modal.style.display = 'none';
            if (e.target == createModal) createModal.style.display = 'none';
        });

        // Task Items
        document.querySelectorAll('.task-item').forEach(item => {
            item.addEventListener('click', () => openEditModal(item));
            const editBtn = item.querySelector('.edit-btn');
            if (editBtn) {
                editBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    openEditModal(item);
                });
            }
        });

        // Add Task Button
        const addTaskBtn = document.getElementById('addTaskBtn');
        if (addTaskBtn) {
            addTaskBtn.addEventListener('click', openCreateModal);
        }

        // Add Task to Project Buttons
        document.querySelectorAll('.add-task-project-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                openCreateModal(null, btn.dataset.project);
            });
        });

        // Save Buttons
        if (saveBtn) saveBtn.addEventListener('click', saveTask);
        if (createSaveBtn) createSaveBtn.addEventListener('click', createTask);
        if (deleteBtn) deleteBtn.addEventListener('click', deleteTask);

        // Search
        if (searchBox) {
            searchBox.addEventListener('input', (e) => {
                const query = e.target.value.trim();
                clearSearchBtn.style.display = query ? 'block' : 'none';
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => performSearch(query), 300);
            });
        }

        if (clearSearchBtn) {
            clearSearchBtn.addEventListener('click', () => {
                searchBox.value = '';
                clearSearchBtn.style.display = 'none';
                performSearch('');
            });
        }

        // Team Filters
        teamFilterButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const teamId = btn.dataset.teamId;
                if (activeTeamFilter === teamId) {
                    activeTeamFilter = null;
                    btn.classList.remove('active');
                    updateUrlParams('team', null);
                } else {
                    activeTeamFilter = teamId;
                    teamFilterButtons.forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    updateUrlParams('team', teamId);
                }
                applyFilters();
            });
        });

        // Member Filters
        memberFilterButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const member = btn.dataset.member;
                if (activeMemberFilter === member) {
                    activeMemberFilter = null;
                    btn.classList.remove('active');
                    // updateUrlParams('member', null);
                } else {
                    activeMemberFilter = member;
                    memberFilterButtons.forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    // updateUrlParams('member', member);
                }
                applyFilters();
            });
        });
    }

    function updateUrlParams(key, value) {
        const url = new URL(window.location);
        if (value) {
            url.searchParams.set(key, value);
        } else {
            url.searchParams.delete(key);
        }
        window.history.pushState({}, '', url);
    }

    async function applyFilters() {
        const allTasks = document.querySelectorAll('.task-item');

        allTasks.forEach(task => {
            let visible = true;

            // Team Filter
            if (activeTeamFilter) {
                // Check if we have data-team-id on the task item.
                // If not, we need to rely on the project badge or fetch it.
                // Assuming we will add data-team-id to the task item in index.html.
                // For now, let's try to match by project name if we have team info loaded.
                // But wait, the task item doesn't have team info directly.
                // We need to add data-team-id to the task item in index.html.
                const taskTeamId = task.dataset.teamId;
                if (taskTeamId && taskTeamId !== activeTeamFilter) {
                    visible = false;
                } else if (!taskTeamId) {
                    // If no team ID on task, maybe it's a legacy task or we forgot to add the attribute.
                    // Let's assume it doesn't match if we are filtering by team.
                    // visible = false; 
                    // Actually, let's try to be smart.
                    // We can check the project badge in the same card? No, tasks can be in different projects.
                    // The project card has the badge.
                    // Let's check the project card's team.
                    const projectCard = task.closest('.project-card');
                    const badge = projectCard.querySelector('.project-badge');
                    // This is hard because badge text is Hebrew name.
                    // We need the ID.
                    // Best solution: Add data-team-id to task-item in index.html.
                }
            }

            // Member Filter
            if (activeMemberFilter && visible) {
                const avatars = task.querySelectorAll('.avatar');
                let hasMember = false;
                avatars.forEach(avatar => {
                    const memberName = avatar.dataset.memberName;
                    if (memberName && memberName === activeMemberFilter) {
                        hasMember = true;
                    }
                });
                if (!hasMember) visible = false;
            }

            if (visible) {
                task.classList.remove('filtered-hidden');
            } else {
                task.classList.add('filtered-hidden');
            }
        });

        // Hide project cards with no visible tasks
        document.querySelectorAll('.project-card').forEach(card => {
            const visibleTasks = card.querySelectorAll('.task-item:not(.filtered-hidden):not(.search-hidden)');
            if (visibleTasks.length === 0) {
                card.classList.add('filtered-hidden');
            } else {
                card.classList.remove('filtered-hidden');
            }
        });
    }

    // Modal Logic
    function openEditModal(taskItem) {
        currentTaskItem = taskItem;
        const taskId = taskItem.dataset.id;

        taskNameInput.value = taskItem.querySelector('.task-name').textContent;
        taskNotes.value = taskItem.dataset.notes || '';

        const statusBadge = taskItem.querySelector('.status-badge');
        taskStatus.value = getStatusFromClass(statusBadge.classList[1]);

        taskPriority.value = taskItem.dataset.priority || 'none';

        const projectCard = taskItem.closest('.project-card');
        projectNameInput.value = projectCard.querySelector('.project-title').textContent.trim();

        // Reset checkboxes
        document.querySelectorAll('#taskModal .members-select input[type="checkbox"]').forEach(cb => cb.checked = false);

        // Check members based on avatars
        const avatars = taskItem.querySelectorAll('.avatar');
        avatars.forEach(img => {
            const src = img.getAttribute('src');
            const checkbox = document.querySelector(`#taskModal .members-select input[data-img="${src}"]`);
            if (checkbox) checkbox.checked = true;

            const filename = src.split('/').pop();
            const checkboxByFile = document.querySelector(`#taskModal .members-select input[data-img$="${filename}"]`);
            if (checkboxByFile) checkboxByFile.checked = true;
        });

        // Set Team
        // We need to set the team dropdown.
        // If we have data-team-id on task item, use it.
        if (taskItem.dataset.teamId) {
            taskTeam.value = taskItem.dataset.teamId;
        } else {
            taskTeam.value = '';
        }

        modal.style.display = 'block';
    }

    function openCreateModal(e, projectName = null) {
        createTaskNameInput.value = '';
        createProjectNameInput.value = projectName || '';
        createTaskStatus.value = 'status-notstarted';
        createTaskPriority.value = 'none';
        createTaskNotes.value = '';
        createTaskTeam.value = '';

        document.querySelectorAll('#createTaskModal .members-select input[type="checkbox"]').forEach(cb => cb.checked = false);

        createModal.style.display = 'block';
        createModal.style.zIndex = 2000;
        createModal.style.visibility = 'visible';
    }

    // CRUD Operations
    async function saveTask() {
        if (!currentTaskItem) return;

        const taskId = currentTaskItem.dataset.id;
        const payload = {
            project: projectNameInput.value.trim(),
            task: taskNameInput.value.trim(),
            members: getSelectedMembers('taskModal'),
            status: taskStatus.value,
            priority: taskPriority.value,
            notes: taskNotes.value.trim(),
            team_id: taskTeam.value || null
        };

        try {
            const response = await fetch(`/api/tasks/${taskId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            if (data.success) {
                location.reload();
            } else {
                alert('שגיאה בשמירת המשימה');
            }
        } catch (error) {
            console.error('Error saving task:', error);
            alert('שגיאה בשמירת המשימה');
        }
    }

    async function createTask() {
        const payload = {
            project: createProjectNameInput.value.trim(),
            task: createTaskNameInput.value.trim(),
            members: getSelectedMembers('createTaskModal'),
            status: createTaskStatus.value,
            priority: createTaskPriority.value,
            notes: createTaskNotes.value.trim(),
            team_id: createTaskTeam.value || null
        };

        try {
            const response = await fetch('/api/tasks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            if (data.success) {
                location.reload();
            } else {
                alert('שגיאה ביצירת המשימה');
            }
        } catch (error) {
            console.error('Error creating task:', error);
            alert('שגיאה ביצירת המשימה');
        }
    }

    async function deleteTask() {
        if (!currentTaskItem || !confirm('האם אתה בטוח שברצונך למחוק משימה זו?')) return;

        const taskId = currentTaskItem.dataset.id;
        try {
            const response = await fetch(`/api/tasks/${taskId}`, {
                method: 'DELETE'
            });

            const data = await response.json();
            if (data.success) {
                location.reload();
            } else {
                alert('שגיאה במחיקת המשימה');
            }
        } catch (error) {
            console.error('Error deleting task:', error);
            alert('שגיאה במחיקת המשימה');
        }
    }

    // Search & Filter Logic
    async function performSearch(query) {
        if (!query) {
            document.querySelectorAll('.task-item, .project-card').forEach(el => {
                el.classList.remove('search-hidden');
            });
            return;
        }

        try {
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            const results = await response.json();
            const resultIds = new Set(results.map(r => r.id));

            document.querySelectorAll('.task-item').forEach(task => {
                const taskId = parseInt(task.dataset.id);
                if (resultIds.has(taskId)) {
                    task.classList.remove('search-hidden');
                } else {
                    task.classList.add('search-hidden');
                }
            });

            document.querySelectorAll('.project-card').forEach(card => {
                const visibleTasks = card.querySelectorAll('.task-item:not(.search-hidden):not(.filtered-hidden)');
                if (visibleTasks.length === 0) {
                    card.classList.add('search-hidden');
                } else {
                    card.classList.remove('search-hidden');
                }
            });
        } catch (error) {
            console.error('Search error:', error);
        }
    }

    // Helpers
    function getStatusFromClass(className) {
        if (className.includes('status-inprogress')) return 'status-inprogress';
        if (className.includes('status-done')) return 'status-done';
        if (className.includes('status-notstarted')) return 'status-notstarted';
        if (className.includes('status-delayed')) return 'status-delayed';
        return 'status-inprogress';
    }

    function getSelectedMembers(modalId) {
        const checkboxes = document.querySelectorAll(`#${modalId} .members-select input[type="checkbox"]`);
        return Array.from(checkboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.value);
    }
});

// ============================================
// INLINE SCRIPTS MOVED FROM INDEX.HTML
// ============================================

// Add-task-per-project button logic
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.add-task-project-btn').forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            e.stopPropagation();
            var projectName = btn.getAttribute('data-project');
            var modal = document.getElementById('createTaskModal');
            var projectInput = document.getElementById('createProjectNameInput');
            if (projectInput) projectInput.value = projectName;
            // Clear other fields
            var nameInput = document.getElementById('createTaskNameInput');
            if (nameInput) nameInput.value = '';
            var statusInput = document.getElementById('createTaskStatus');
            if (statusInput) statusInput.value = 'status-inprogress';
            var priorityInput = document.getElementById('createTaskPriority');
            if (priorityInput) priorityInput.value = 'none';
            var notesInput = document.getElementById('createTaskNotes');
            if (notesInput) notesInput.value = '';
            document.querySelectorAll('#createTaskModal .members-select input[type=\"checkbox\"]').forEach(function (cb) { cb.checked = false; });
            modal.style.display = 'block';
            modal.style.zIndex = 2000;
            modal.style.visibility = 'visible';
        });
    });
});

// Live clock for navbar
function updateClock() {
    const now = new Date();
    const day = String(now.getDate()).padStart(2, '0');
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const year = now.getFullYear();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    // Format: dd/mm/yyyy hh:mm:ss
    const formatted = `${day}/${month}/${year} ${hours}:${minutes}:${seconds}`;
    const el = document.getElementById('liveClock');
    if (el) el.textContent = ` ${formatted} `;
}
setInterval(updateClock, 1000);
updateClock();

// Make member filter reset accessible globally
window.resetMemberFilter = function () {
    const memberButtons = document.querySelectorAll('.filter-avatar-btn');
    memberButtons.forEach(mb => {
        mb.classList.remove('active');
    });
    const allTasks = document.querySelectorAll('.task-item');
    allTasks.forEach(task => {
        task.style.display = '';
    });
    // Trigger custom event to notify script.js
    window.dispatchEvent(new CustomEvent('resetMemberFilter'));
};

// Team filtering logic
document.addEventListener('DOMContentLoaded', function () {
    const teamButtons = document.querySelectorAll('.filter-team-btn');
    const clearTeamBtn = document.getElementById('clearTeamFilter');
    const projectCards = document.querySelectorAll('.project-card');
    const memberButtons = document.querySelectorAll('.filter-avatar-btn');

    teamButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            const teamId = this.getAttribute('data-team-id');

            // Update team button styles
            teamButtons.forEach(b => {
                b.classList.remove('active');
            });
            this.classList.add('active');
            clearTeamBtn.classList.remove('active');

            // Clear any active member filter and reset task visibility
            if (typeof window.resetMemberFilter === 'function') {
                window.resetMemberFilter();
            }

            // Filter member buttons - show only members from selected team
            memberButtons.forEach(mb => {
                const memberTeamId = mb.getAttribute('data-team-id');
                if (memberTeamId === teamId) {
                    mb.style.display = 'inline-block';
                } else {
                    mb.style.display = 'none';
                }
            });

            // Filter project cards
            projectCards.forEach(card => {
                const cardTeamId = card.getAttribute('data-team-id');
                if (cardTeamId === teamId) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    });

    clearTeamBtn.addEventListener('click', function () {
        // Reset all team buttons
        teamButtons.forEach(b => {
            b.classList.remove('active');
        });
        this.classList.add('active');

        // Clear any active member filter
        memberButtons.forEach(mb => {
            mb.classList.remove('active');
        });

        // Reset task filtering - show all tasks
        const taskItems = document.querySelectorAll('.task-item');
        taskItems.forEach(task => {
            task.style.display = '';
        });

        // Show all member buttons
        memberButtons.forEach(mb => {
            mb.style.display = 'inline-block';
        });

        // Show all project cards
        projectCards.forEach(card => {
            card.style.display = 'block';
        });
    });
});
