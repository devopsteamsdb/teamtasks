document.addEventListener('DOMContentLoaded', () => {
    // State
    let teams = [];
    let members = [];
    let currentTaskItem = null;
    let activeTeamFilter = null;
    let activeMemberFilter = null;
    let searchTimeout;
    let lastUpdateTimestamp = 0;

    // DOM Elements Cache
    let modal, createModal, closeModal, closeCreateModal;
    let saveBtn, deleteBtn, createSaveBtn;
    let taskNameInput, projectNameInput, taskStatus, taskPriority, taskNotes, taskTeam;
    let createTaskNameInput, createProjectNameInput, createTaskStatus, createTaskPriority, createTaskNotes, createTaskTeam;
    let searchBox, clearSearchBtn, teamFilterButtons, memberFilterButtons;

    // Initialize
    init();

    function updateDOMElements() {
        modal = document.getElementById('taskModal');
        createModal = document.getElementById('createTaskModal');
        closeModal = document.querySelector('.close-modal');
        closeCreateModal = document.querySelector('.close-modal-create');

        saveBtn = document.getElementById('saveBtn');
        deleteBtn = document.getElementById('deleteBtn');
        createSaveBtn = document.getElementById('createSaveBtn');

        taskNameInput = document.getElementById('taskNameInput');
        projectNameInput = document.getElementById('projectNameInput');
        taskStatus = document.getElementById('taskStatus');
        taskPriority = document.getElementById('taskPriority');
        taskNotes = document.getElementById('taskNotes');
        taskTeam = document.getElementById('taskTeam');

        createTaskNameInput = document.getElementById('createTaskNameInput');
        createProjectNameInput = document.getElementById('createProjectNameInput');
        createTaskStatus = document.getElementById('createTaskStatus');
        createTaskPriority = document.getElementById('createTaskPriority');
        createTaskNotes = document.getElementById('createTaskNotes');
        createTaskTeam = document.getElementById('createTaskTeam');

        searchBox = document.getElementById('searchBox');
        clearSearchBtn = document.getElementById('clearSearch');
        teamFilterButtons = document.querySelectorAll('.filter-team-btn');
        memberFilterButtons = document.querySelectorAll('.filter-avatar-btn');
    }

    async function init() {
        updateDOMElements();
        await Promise.all([loadTeams(), loadMembers(), checkVersion(true)]);
        populateDropdowns();
        populateMemberCheckboxes();
        attachEventListeners();
        attachGlobalListeners();

        // Start polling for updates
        setInterval(() => checkVersion(false), 5000);

        // Check URL for team filter
        const urlParams = new URLSearchParams(window.location.search);
        const teamId = urlParams.get('team');
        if (teamId) {
            activeTeamFilter = teamId;
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

    async function checkVersion(firstLoad = false) {
        try {
            const response = await fetch('/api/version?t=' + new Date().getTime());
            const data = await response.json();

            if (firstLoad) {
                lastUpdateTimestamp = data.timestamp;
            } else if (data.timestamp > lastUpdateTimestamp) {
                lastUpdateTimestamp = data.timestamp;
                await refreshContent();
            }
        } catch (error) {
            console.error('Error checking version:', error);
        }
    }

    async function refreshContent() {
        try {
            const response = await fetch(window.location.href);
            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');

            const newMainContainer = doc.querySelector('.main-container');
            const newNavbar = doc.querySelector('.navbar');

            if (newMainContainer) {
                document.querySelector('.main-container').innerHTML = newMainContainer.innerHTML;
            }

            // Only update navbar if changed (to prevent flicker)
            const currentNavbar = document.querySelector('.navbar');
            if (newNavbar && currentNavbar.innerHTML !== newNavbar.innerHTML) {
                currentNavbar.innerHTML = newNavbar.innerHTML;
            }

            // Re-initialize DOM elements and listeners
            updateDOMElements();
            populateDropdowns(); // Re-populate dropdowns as modals are recreated
            attachEventListeners();

            // Re-apply filters if needed
            if (activeTeamFilter) {
                // Ensure active class on button
                const btn = document.querySelector(`.filter-team-btn[data-team-id="${activeTeamFilter}"]`);
                if (btn) btn.classList.add('active');
            }
            applyFilters();

        } catch (error) {
            console.error('Error refreshing content:', error);
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

    // Global Listeners (attached once)
    function attachGlobalListeners() {
        // Listen for member filter reset event
        window.addEventListener('resetMemberFilter', function () {
            activeMemberFilter = null;
            if (memberFilterButtons) {
                memberFilterButtons.forEach(b => b.classList.remove('active'));
            }
            applyFilters();
        });

        window.addEventListener('click', (e) => {
            // We need to check modal visibility because element references might be stale if not updated properly
            // But we update modal variables on refreshContent, so it should be fine.
            if (modal && e.target == modal) modal.style.display = 'none';
            if (createModal && e.target == createModal) createModal.style.display = 'none';
        });
    }

    // Content Listeners (attached on init and refresh)
    function attachEventListeners() {
        // Modals
        if (closeModal) closeModal.addEventListener('click', () => modal.style.display = 'none');
        if (closeCreateModal) closeCreateModal.addEventListener('click', () => createModal.style.display = 'none');

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

                // Check if clicking currently active team (deselect logic)
                if (activeTeamFilter === teamId) {
                    activeTeamFilter = null;
                    btn.classList.remove('active');

                    // Clear URL param
                    const url = new URL(window.location);
                    url.searchParams.delete('team');
                    window.history.pushState({}, '', url);

                    // Reset task visibility (show all)
                    document.querySelectorAll('.project-card').forEach(card => {
                        card.classList.remove('filtered-hidden');
                        card.style.display = '';
                    });

                    // Reset member filters too
                    if (typeof window.resetMemberFilter === 'function') {
                        window.resetMemberFilter();
                    }
                    // Make sure member buttons are shown
                    if (memberFilterButtons) {
                        memberFilterButtons.forEach(mb => mb.style.display = 'inline-block');
                    }
                    return;
                }

                // Select Logic
                activeTeamFilter = teamId;
                teamFilterButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                updateUrlParams('team', teamId);

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
                } else {
                    activeMemberFilter = member;
                    memberFilterButtons.forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
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
                const taskTeamId = task.dataset.teamId;
                if (taskTeamId && taskTeamId !== activeTeamFilter) {
                    visible = false;
                } else if (!taskTeamId) {
                    // Check project team? No, assume task data is correct.
                    // visible = false; 
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
            // Handle team filter visibility for project cards via class first
            const cardTeamId = card.getAttribute('data-team-id');
            if (activeTeamFilter && cardTeamId && cardTeamId !== activeTeamFilter) {
                card.classList.add('filtered-hidden');
                return; // Skip further checks
            } else if (activeTeamFilter && cardTeamId && cardTeamId === activeTeamFilter) {
                card.classList.remove('filtered-hidden');
            }

            const visibleTasks = card.querySelectorAll('.task-item:not(.filtered-hidden):not(.search-hidden)');
            if (visibleTasks.length === 0) {
                card.classList.add('filtered-hidden');
            } else {
                card.classList.remove('filtered-hidden');
            }
        });

        // Filter member buttons based on team
        if (activeTeamFilter) {
            memberFilterButtons.forEach(mb => {
                const memberTeamId = mb.getAttribute('data-team-id');
                if (memberTeamId === activeTeamFilter) {
                    mb.style.display = 'inline-block';
                } else {
                    mb.style.display = 'none';
                }
            });
        } else {
            memberFilterButtons.forEach(mb => mb.style.display = 'inline-block');
        }
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
                // Manually trigger refresh after save
                checkVersion(false);
                // Close modal
                modal.style.display = 'none';
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
                checkVersion(false);
                createModal.style.display = 'none';
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
                checkVersion(false);
                modal.style.display = 'none';
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
// INLINE SCRIPTS MOVED FROM INDEX.HTML (Refactored into main logic if possible, or kept global)
// ============================================

// Live clock for navbar (Global)
function updateClock() {
    const now = new Date();
    const day = String(now.getDate()).padStart(2, '0');
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const year = now.getFullYear();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    const formatted = `${day}/${month}/${year} ${hours}:${minutes}:${seconds}`;
    const el = document.getElementById('liveClock');
    if (el) el.textContent = ` ${formatted} `;
}
setInterval(updateClock, 1000);
updateClock();

// Make member filter reset accessible globally
window.resetMemberFilter = function () {
    // This is dispatched custom event, listener handles logic
    window.dispatchEvent(new CustomEvent('resetMemberFilter'));
};
