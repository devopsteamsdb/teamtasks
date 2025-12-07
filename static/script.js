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
    let taskNameInput, projectNameInput, taskStatus, taskPriority, taskNotes, taskTeam, taskStartDate, taskEndDate;
    let createTaskNameInput, createProjectNameInput, createTaskStatus, createTaskPriority, createTaskNotes, createTaskTeam, createTaskStartDate, createTaskEndDate;
    let searchBox, clearSearchBtn, teamFilterButtons, memberFilterButtons;

    // Initialize
    init();

    function initializeFlatpickr() {
        const config = {
            locale: "he",
            dateFormat: "d/m/Y",
            allowInput: true,
            firstDayOfWeek: 0, // Sunday
            disableMobile: "true",
            parseDate: (datestr, format) => {
                // Return null or undefined if empty
                if (!datestr) return null;

                // Allow free form entry (e.g. 07122025 -> 2025-12-07)
                // Normalize separators
                let cleanStr = datestr.replace(/[\.\-]/g, '/');

                // Handle 8 digit number (07122025)
                if (/^\d{8}$/.test(cleanStr)) {
                    cleanStr = cleanStr.substring(0, 2) + '/' + cleanStr.substring(2, 4) + '/' + cleanStr.substring(4);
                }

                return flatpickr.parseDate(cleanStr, format);
            }
        };

        flatpickr("#taskStartDate", config);
        flatpickr("#taskEndDate", config);
        flatpickr("#createTaskStartDate", config);
        flatpickr("#createTaskEndDate", config);
    }

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
        taskStartDate = document.getElementById('taskStartDate');
        taskEndDate = document.getElementById('taskEndDate');

        createTaskNameInput = document.getElementById('createTaskNameInput');
        createProjectNameInput = document.getElementById('createProjectNameInput');
        createTaskStatus = document.getElementById('createTaskStatus');
        createTaskPriority = document.getElementById('createTaskPriority');
        createTaskNotes = document.getElementById('createTaskNotes');
        createTaskTeam = document.getElementById('createTaskTeam');
        createTaskStartDate = document.getElementById('createTaskStartDate');
        createTaskEndDate = document.getElementById('createTaskEndDate');

        searchBox = document.getElementById('searchBox');
        clearSearchBtn = document.getElementById('clearSearch');
        teamFilterButtons = document.querySelectorAll('.filter-team-btn');
        memberFilterButtons = document.querySelectorAll('.filter-avatar-btn');
    }

    async function init() {
        updateDOMElements();
        initializeFlatpickr();
        await Promise.all([loadTeams(), loadMembers(), checkVersion(true)]);
        populateDropdowns();
        populateMemberCheckboxes();
        attachEventListeners();
        attachGlobalListeners();

        // Start polling for updates
        setInterval(() => checkVersion(false), 5000);

        // Check localStorage or URL for team filter
        const urlParams = new URLSearchParams(window.location.search);
        const teamId = urlParams.get('team');
        const storedTeamId = localStorage.getItem('activeTeamFilter');

        if (teamId) {
            activeTeamFilter = teamId;
        } else if (storedTeamId) {
            activeTeamFilter = storedTeamId;
            // Update URL to match state without reload
            const url = new URL(window.location);
            url.searchParams.set('team', activeTeamFilter);
            window.history.replaceState({}, '', url);
        }

        // Update UI buttons if filter is active
        if (activeTeamFilter) {
            teamFilterButtons.forEach(btn => {
                if (btn.dataset.teamId === activeTeamFilter) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });
        }

        applyFilters();
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
            // Preserve focus state
            const activeElement = document.activeElement;
            const activeId = activeElement ? activeElement.id : null;
            const selectionStart = (activeId === 'searchBox') ? activeElement.selectionStart : 0;
            const selectionEnd = (activeId === 'searchBox') ? activeElement.selectionEnd : 0;

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

            // Restore focus if needed
            if (activeId === 'searchBox') {
                const el = document.getElementById('searchBox');
                if (el) {
                    el.focus();
                    el.setSelectionRange(selectionStart, selectionEnd);
                }
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
        // ... (existing code, not changing)
        const options = teams.map(team =>
            `<option value="${team.id}">${team.name_he}</option>`
        ).join('');

        const defaultOption = '<option value="">בחר צוות...</option>';
        const archiveOption = '<option value="archive">ארכיון</option>';

        if (createTaskTeam) createTaskTeam.innerHTML = defaultOption + options; // No archive for new tasks? Or maybe yes? Let's keep it simple for now and only allow moving to archive for existing.
        if (taskTeam) taskTeam.innerHTML = defaultOption + options + archiveOption;
    }
    // ... skipping unchanged lines until performSearch ...

    // Search & Filter Logic
    async function performSearch(query) {
        // Update URL with search query
        const url = new URL(window.location);
        if (query) {
            url.searchParams.set('q', query);
        } else {
            url.searchParams.delete('q');
        }
        window.history.pushState({}, '', url);

        // Trigger content refresh (which will now use the new query param)
        // This allows archived tasks to be rendered by the server
        await refreshContent();
    }

    function populateMemberCheckboxes() {
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


    // Event Listeners and Logic
    function attachEventListeners() {
        // Add Task Button
        if (addTaskBtn) {
            // Remove old listener to avoid duplicates if re-running
            addTaskBtn.removeEventListener('click', openCreateModal);
            addTaskBtn.addEventListener('click', openCreateModal);
        }

        // Close Modal Buttons
        if (closeModal) {
            closeModal.addEventListener('click', () => {
                if (modal) modal.style.display = 'none';
            });
        }

        if (closeCreateModal) {
            closeCreateModal.addEventListener('click', () => {
                if (createModal) createModal.style.display = 'none';
            });
        }

        // Add Task to Project Buttons
        document.querySelectorAll('.add-task-project-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                openCreateModal(null, btn.dataset.project);
            });
        });

        // Task Item Click (Edit)
        document.querySelectorAll('.task-item').forEach(item => {
            item.removeEventListener('click', handleTaskClick); // Prevent duplicates
            item.addEventListener('click', handleTaskClick);
        });

        function handleTaskClick(e) {
            // Prevent if clicking on interactive elements
            if (e.target.closest('button') || e.target.closest('input') || e.target.closest('a')) {
                return;
            }
            // Open modal
            const taskItem = e.currentTarget;
            openEditModal(taskItem);
        }

        // Save Buttons
        if (saveBtn) saveBtn.addEventListener('click', saveTask);
        if (createSaveBtn) createSaveBtn.addEventListener('click', createTask);
        if (deleteBtn) deleteBtn.addEventListener('click', deleteTask);
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
            btn.addEventListener('click', async () => {
                const teamId = btn.dataset.teamId;
                const mode = btn.dataset.mode || 'active'; // 'active' or 'archive'

                // 1. Archive Toggle Button Logic
                if (mode === 'archive') {
                    const currentUrl = new URL(window.location);
                    const isArchiveActive = currentUrl.searchParams.get('mode') === 'archive';

                    if (isArchiveActive) {
                        // Toggle Off -> Go to active
                        updateUrlParams('mode', 'active');
                        btn.classList.remove('active');
                    } else {
                        // Toggle On -> Go to archive
                        updateUrlParams('mode', 'archive');
                        btn.classList.add('active');

                        // Clear active team filter visually & URL
                        activeTeamFilter = null;
                        updateUrlParams('team', null);

                        // Deselect all team buttons
                        Array.from(document.querySelectorAll('.filter-team-btn:not(.archive-filter-btn)')).forEach(b => b.classList.remove('active'));
                    }
                    await refreshContent();
                    return;
                }

                // 2. Normal Team Button Logic 
                // Checks if we need to switch from Archive mode first
                const currentUrlParams = new URLSearchParams(window.location.search);
                const wasInArchiveMode = currentUrlParams.get('mode') === 'archive';

                if (wasInArchiveMode) {
                    // Switch to Active Mode AND Select the team
                    updateUrlParams('mode', 'active');

                    // Set team filter
                    activeTeamFilter = teamId;
                    updateUrlParams('team', teamId);

                    // We must refresh because we are changing mode
                    await refreshContent();
                    return;
                }

                // 3. Active Mode - Toggle Logic
                if (activeTeamFilter === teamId) {
                    // Deselect Current Team
                    activeTeamFilter = null;
                    btn.classList.remove('active');
                    updateUrlParams('team', null);

                    // Reset UI to show all active tasks
                    document.querySelectorAll('.project-card').forEach(card => {
                        card.classList.remove('filtered-hidden');
                        card.style.display = '';
                    });

                    if (typeof window.resetMemberFilter === 'function') {
                        window.resetMemberFilter();
                    }
                    selectedTeamMemberButtonsUpdate();
                    applyFilters();
                    return;
                }

                // 4. Active Mode - Select New Team
                activeTeamFilter = teamId;

                // Remove active class from ALL buttons
                Array.from(document.querySelectorAll('.filter-team-btn')).forEach(b => b.classList.remove('active'));

                // Add active class to clicked button
                btn.classList.add('active');
                updateUrlParams('team', teamId);

                // Clear member filter when switching teams
                activeMemberFilter = null;
                memberFilterButtons.forEach(mb => mb.classList.remove('active'));

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

    function selectedTeamMemberButtonsUpdate() {
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

    function updateUrlParams(key, value) {
        const url = new URL(window.location);
        if (value) {
            url.searchParams.set(key, value);
            if (key === 'team') {
                localStorage.setItem('activeTeamFilter', value);
                // Also ensure mode is active if selecting team logic happened elsewhere? 
                // Rely on caller to set mode.
            }
        } else {
            url.searchParams.delete(key);
            if (key === 'team') {
                localStorage.removeItem('activeTeamFilter');
            }
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
            const cardTeamId = card.getAttribute('data-team-id');

            // If team filter is active, only show relevant project cards if they belong to team (mixed usage, but safe)
            // or if they contain relevant tasks.
            // Simplified: Hide card if no visible tasks inside.

            const visibleTasks = card.querySelectorAll('.task-item:not(.filtered-hidden):not(.search-hidden)');

            // Check if card itself matches filter (if cards have team ID)
            let cardMatchesTeam = true;
            if (activeTeamFilter && cardTeamId && cardTeamId !== activeTeamFilter) {
                // However, card might have tasks from other teams? 
                // Based on template, project card has team_id.
                cardMatchesTeam = false;
            }

            if (visibleTasks.length === 0) {
                // Even if card matches team, if no tasks, maybe hide?
                // Let's stick to task visibility driving it
                card.classList.add('filtered-hidden');
            } else {
                card.classList.remove('filtered-hidden');
            }
        });

        selectedTeamMemberButtonsUpdate();
    }

    // Modal Logic
    function openEditModal(taskItem) {
        currentTaskItem = taskItem;
        const taskId = taskItem.dataset.id;

        taskNameInput.value = taskItem.querySelector('.task-name').textContent;
        // Using dataset for notes if available, or try to find hidden element? 
        // Template shows: data-notes="{{ task.notes|default('') }}"
        taskNotes.value = taskItem.dataset.notes || '';

        const statusBadge = taskItem.querySelector('.status-badge');
        // Fallback if classList[1] isn't the status
        let statusClass = 'status-inprogress';
        statusBadge.classList.forEach(cls => {
            if (cls.startsWith('status-')) statusClass = cls;
        });
        taskStatus.value = getStatusFromClass(statusClass);

        taskPriority.value = taskItem.dataset.priority || 'none';

        const projectCard = taskItem.closest('.project-card');
        projectNameInput.value = projectCard.querySelector('.project-title').textContent.trim();

        // Reset checkboxes
        document.querySelectorAll('#taskModal .members-select input[type="checkbox"]').forEach(cb => cb.checked = false);

        // Check members based on avatars
        const avatars = taskItem.querySelectorAll('.avatar');
        avatars.forEach(img => {
            // Using name data attribute is safer than image src matching
            const memberName = img.dataset.memberName;
            if (memberName) {
                const checkbox = document.querySelector(`#taskModal .members-select input[value="${memberName}"]`);
                if (checkbox) checkbox.checked = true;
            } else {
                // Fallback to src matching
                const src = img.getAttribute('src');
                const checkbox = document.querySelector(`#taskModal .members-select input[data-img="${src}"]`);
                if (checkbox) checkbox.checked = true;
            }
        });

        // Set Team or Archive
        // Check if archived using data attribute
        const isArchived = taskItem.dataset.isArchived === 'true';
        if (isArchived) {
            taskTeam.value = 'archive';
        } else if (taskItem.dataset.teamId) {
            taskTeam.value = taskItem.dataset.teamId;
        } else {
            taskTeam.value = '';
        }

        taskStartDate.value = '';
        taskEndDate.value = '';
        if (taskItem.dataset.startDate) taskStartDate.value = formatDateFromISO(taskItem.dataset.startDate);
        if (taskItem.dataset.endDate) taskEndDate.value = formatDateFromISO(taskItem.dataset.endDate);

        modal.style.display = 'block';
    }

    function openCreateModal(e, projectName = null) {
        createTaskNameInput.value = '';
        // If triggered by + button on project
        createProjectNameInput.value = projectName || '';
        if (projectName) {
            // Maybe lock it?
        }

        createTaskStatus.value = 'status-notstarted';
        createTaskPriority.value = 'none';
        createTaskNotes.value = '';
        createTaskTeam.value = '';
        createTaskStartDate.value = '';
        createTaskEndDate.value = '';

        document.querySelectorAll('#createTaskModal .members-select input[type="checkbox"]').forEach(cb => cb.checked = false);

        createModal.style.display = 'block';
        createModal.style.zIndex = 2000;
        createModal.style.visibility = 'visible';
    }

    // CRUD Operations
    async function saveTask() {
        if (!currentTaskItem) return;

        const taskId = currentTaskItem.dataset.id;

        // Determine is_archived state from team selection
        const selectedTeam = taskTeam.value;
        const isArchiveSelected = selectedTeam === 'archive';

        const payload = {
            project: projectNameInput.value.trim(),
            task: taskNameInput.value.trim(),
            members: getSelectedMembers('taskModal'),
            status: taskStatus.value,
            priority: taskPriority.value,
            notes: taskNotes.value.trim(),
            // If archive is selected, we might want to keep the old team_id or clear it? 
            // The requirement says "move task from archived back to a certain team".
            // If I set team_id to null when archiving, I lose the history.
            // But if I unarchive I set it to the new team.
            // Let's keep team_id as is if archiving (or maybe the user does not care).
            // Actually, if I select "archive", the value is "archive". I can't send "archive" as team_id (int).
            // So if archive, send existing team_id? Or null?
            // Let's check what backend expects. It expects team_id as int or null.
            // For now, let's set team_id to null if archived, unless we want to "remember" it.
            // But the dropdown UI forces a choice: Team OR Archive. 
            // So if I choose Archive, I am NOT choosing a Team.
            team_id: isArchiveSelected ? null : (selectedTeam || null),
            start_date: parseDateToISO(taskStartDate.value),
            end_date: parseDateToISO(taskEndDate.value),
            is_archived: isArchiveSelected
        };

        if (taskStartDate.value && taskEndDate.value) {
            const start = flatpickr.parseDate(taskStartDate.value, "d/m/Y");
            const end = flatpickr.parseDate(taskEndDate.value, "d/m/Y");
            if (start > end) {
                alert('תאריך ההתחלה לא יכול להיות מאוחר מתאריך הסיום');
                return;
            }
        }

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
            team_id: createTaskTeam.value || null,
            start_date: parseDateToISO(createTaskStartDate.value),
            end_date: parseDateToISO(createTaskEndDate.value)
        };

        if (createTaskStartDate.value && createTaskEndDate.value) {
            const start = flatpickr.parseDate(createTaskStartDate.value, "d/m/Y");
            const end = flatpickr.parseDate(createTaskEndDate.value, "d/m/Y");
            if (start > end) {
                alert('תאריך ההתחלה לא יכול להיות מאוחר מתאריך הסיום');
                return;
            }
        }

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

    async function archiveTask() {
        if (!currentTaskItem || !confirm('האם להעביר משימה זו לארכיון?')) return;

        const taskId = currentTaskItem.dataset.id;
        try {
            const response = await fetch(`/api/tasks/${taskId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_archived: true })
            });

            const data = await response.json();
            if (data.success) {
                checkVersion(false);
                modal.style.display = 'none';
            } else {
                alert('שגיאה בארכוב המשימה');
            }
        } catch (error) {
            console.error('Error archiving task:', error);
            alert('שגיאה בארכוב המשימה');
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
        if (!className) return 'status-inprogress';
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

// Helper: Convert dd/mm/yyyy to yyyy-mm-dd (ISO format)
function parseDateToISO(dateStr) {
    if (!dateStr || !dateStr.trim()) return null;
    const parts = dateStr.split('/');
    if (parts.length !== 3) return null;
    return `${parts[2]}-${parts[1]}-${parts[0]}`;
}

// Helper: Convert yyyy-mm-dd (ISO) to dd/mm/yyyy
function formatDateFromISO(isoStr) {
    if (!isoStr) return '';
    const parts = isoStr.split('-');
    if (parts.length !== 3) return '';
    return `${parts[2]}/${parts[1]}/${parts[0]}`;
}
