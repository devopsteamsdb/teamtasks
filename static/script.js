document.addEventListener('DOMContentLoaded', () => {
    // Edit modal
    const modal = document.getElementById('taskModal');
    const closeModal = document.querySelector('.close-modal');
    const saveBtn = document.getElementById('saveBtn');
    const deleteBtn = document.getElementById('deleteBtn');
    const modalTitle = document.getElementById('modalTitle');
    const taskNameInput = document.getElementById('taskNameInput');
    const taskNotes = document.getElementById('taskNotes');
    const taskStatus = document.getElementById('taskStatus');
    const taskPriority = document.getElementById('taskPriority');
    const memberCheckboxes = document.querySelectorAll('#taskModal .members-select input[type="checkbox"]');
    const projectNameInput = document.getElementById('projectNameInput');

    // Create modal
    const createModal = document.getElementById('createTaskModal');
    const closeCreateModal = document.querySelector('.close-modal-create');
    const createSaveBtn = document.getElementById('createSaveBtn');
    const createTaskNameInput = document.getElementById('createTaskNameInput');
    const createProjectNameInput = document.getElementById('createProjectNameInput');
    const createTaskStatus = document.getElementById('createTaskStatus');
    const createTaskPriority = document.getElementById('createTaskPriority');
    const createTaskNotes = document.getElementById('createTaskNotes');
    const createMemberCheckboxes = document.querySelectorAll('#createTaskModal .members-select input[type="checkbox"]');

    let currentTaskItem = null;

    // Helper: Get Status Text from Class
    function getStatusFromClass(className) {
        if (className.includes('status-inprogress')) return 'status-inprogress';
        if (className.includes('status-done')) return 'status-done';
        if (className.includes('status-notstarted')) return 'status-notstarted';
        if (className.includes('status-delayed')) return 'status-delayed';
        return 'status-inprogress';
    }

    // Helper: Get Dropdown Text
    function getDropdownText(selectElement) {
        return selectElement.options[selectElement.selectedIndex].text;
    }

    // Open Modal
    function openModal(taskItem) {
        currentTaskItem = taskItem;

        const taskName = taskItem.querySelector('.task-name').textContent;
        taskNameInput.value = taskName;
        modalTitle.textContent = `עריכת משימה`;

        const notes = taskItem.getAttribute('data-notes') || '';
        taskNotes.value = notes;

        const statusBadge = taskItem.querySelector('.status-badge');
        const currentStatusClass = statusBadge.classList[1];
        taskStatus.value = getStatusFromClass(currentStatusClass);

        const priority = taskItem.getAttribute('data-priority') || 'none';
        taskPriority.value = priority;

        memberCheckboxes.forEach(cb => cb.checked = false);
        const avatars = taskItem.querySelectorAll('.avatar');
        avatars.forEach(img => {
            const src = img.getAttribute('src');
            memberCheckboxes.forEach(cb => {
                if (cb.getAttribute('data-img') === src) {
                    cb.checked = true;
                }
            });
        });

        if (!taskItem) {
            projectNameInput.value = '';
        } else {
            const projectCard = taskItem.closest('.project-card');
            const projectName = projectCard.querySelector('.project-title').textContent.trim();
            projectNameInput.value = projectName;
        }

        modal.style.display = 'block';
    }

    // Close Modal
    function closeModalFunc() {
        modal.style.display = 'none';
        currentTaskItem = null;
    }

    // Event Listeners for Tasks
    document.querySelectorAll('.task-item').forEach(item => {
        item.addEventListener('click', (e) => {
            openModal(item);
        });

        const editBtn = item.querySelector('.edit-btn');
        if (editBtn) {
            editBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                openModal(item);
            });
        }
    });

    closeModal.addEventListener('click', closeModalFunc);
    window.addEventListener('click', (e) => {
        if (e.target == modal) closeModalFunc();
    });

    // Save Changes
    saveBtn.addEventListener('click', () => {
        const isEdit = !!currentTaskItem;
        const payload = {
            project: projectNameInput.value.trim(),
            task: taskNameInput.value.trim(),
            members: Array.from(memberCheckboxes).filter(cb => cb.checked).map(cb => cb.value),
            status: taskStatus.value,
            priority: taskPriority.value,
            notes: taskNotes.value.trim()
        };
        if (isEdit) {
            // Edit existing task
            const taskId = currentTaskItem.getAttribute('data-id');
            fetch(`/api/tasks/${taskId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    // Optionally, update UI or reload
                    location.reload();
                }
            });
        } else {
            // Add new task
            fetch('/api/tasks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                }
            });
        }
    });

    // Helper: Sort tasks by priority
    function sortTasksByPriority(taskList) {
        const priorityOrder = { 'high': 0, 'medium': 1, 'low': 2, 'none': 3 };
        const tasks = Array.from(taskList.querySelectorAll('.task-item'));
        tasks.sort((a, b) => {
            const priorityA = a.getAttribute('data-priority') || 'none';
            const priorityB = b.getAttribute('data-priority') || 'none';
            return priorityOrder[priorityA] - priorityOrder[priorityB];
        });
        tasks.forEach(task => taskList.appendChild(task));
    }

    // Team Member Filtering
    let activeFilter = null;
    const filterButtons = document.querySelectorAll('.filter-avatar-btn');
    const clearFilterBtn = document.getElementById('clearFilter');

    filterButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const member = btn.getAttribute('data-member');
            if (activeFilter === member) {
                clearFilter();
            } else {
                activeFilter = member;
                applyFilter(member);
                filterButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            }
        });
    });

    if (clearFilterBtn) {
        clearFilterBtn.addEventListener('click', clearFilter);
    }

    function applyFilter(member) {
        const allTasks = document.querySelectorAll('.task-item');
        allTasks.forEach(task => {
            const avatars = task.querySelectorAll('.avatar');
            let hasMember = false;
            avatars.forEach(avatar => {
                const src = avatar.getAttribute('src');
                if (src.includes(`${member}.png`)) {
                    hasMember = true;
                }
            });
            if (hasMember) {
                task.classList.remove('filtered-hidden');
            } else {
                task.classList.add('filtered-hidden');
            }
        });

        // Hide project cards with no visible tasks
        const projectCards = document.querySelectorAll('.project-card');
        projectCards.forEach(card => {
            const visibleTasks = card.querySelectorAll('.task-item:not(.filtered-hidden)');
            if (visibleTasks.length === 0) {
                card.classList.add('filtered-hidden');
            } else {
                card.classList.remove('filtered-hidden');
            }
        });
    }

    function clearFilter() {
        activeFilter = null;
        const allTasks = document.querySelectorAll('.task-item');
        allTasks.forEach(task => task.classList.remove('filtered-hidden'));
        const projectCards = document.querySelectorAll('.project-card');
        projectCards.forEach(card => card.classList.remove('filtered-hidden'));
        filterButtons.forEach(b => b.classList.remove('active'));
    }

    // Delete Task
    deleteBtn.addEventListener('click', () => {
        if (currentTaskItem && confirm('האם אתה בטוח שברצונך למחוק משימה זו?')) {
            const taskId = currentTaskItem.getAttribute('data-id');
            fetch(`/api/tasks/${taskId}`, {
                method: 'DELETE'
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                }
            });
        }
    });

    // Add event listener to "הוסף משימה" button (open create modal)
    const addTaskBtn = document.getElementById('addTaskBtn');
    addTaskBtn.addEventListener('click', () => {
        console.log('Add Task button clicked');
        // Clear create form fields
        createTaskNameInput.value = '';
        createProjectNameInput.value = '';
        createTaskStatus.value = 'status-inprogress';
        createTaskPriority.value = 'none';
        createTaskNotes.value = '';
        createMemberCheckboxes.forEach(cb => cb.checked = false);
        // Show create modal and force z-index/visibility
        createModal.style.display = 'block';
        createModal.style.zIndex = 2000;
        createModal.style.visibility = 'visible';
    });

    // Close create modal
    closeCreateModal.addEventListener('click', () => {
        createModal.style.display = 'none';
    });
    window.addEventListener('click', (e) => {
        if (e.target == createModal) createModal.style.display = 'none';
    });

    // Save new task from create modal
    createSaveBtn.addEventListener('click', () => {
        const payload = {
            project: createProjectNameInput.value.trim(),
            task: createTaskNameInput.value.trim(),
            members: Array.from(createMemberCheckboxes).filter(cb => cb.checked).map(cb => cb.value),
            status: createTaskStatus.value,
            priority: createTaskPriority.value,
            notes: createTaskNotes.value.trim()
        };
        fetch('/api/tasks', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                createModal.style.display = 'none';
                location.reload();
            } else {
                alert('שגיאה: לא ניתן להוסיף משימה. ודא שכל השדות מולאו ונסה שוב.');
            }
        })
        .catch(err => {
            alert('שגיאת רשת או שרת: לא ניתן להוסיף משימה.');
        });
    });
});
