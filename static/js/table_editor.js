// Maps and Helpers for Member Translation
// Globals initialTasks, allTeams, allMembers are defined in the HTML

// Initialize Flatpickr for Add Task inputs
document.addEventListener('DOMContentLoaded', function () {
    const flatpickrConfig = {
        locale: "he",
        dateFormat: "Y-m-d", // Value format (for API)
        altInput: true,
        altFormat: "d/m/Y",  // Display format
        allowInput: true
    };

    flatpickr(".input-start-date", flatpickrConfig);
    flatpickr(".input-end-date", flatpickrConfig);
});

// Maps and Helpers for Member Translation
// Globals initialTasks, allTeams, allMembers are defined in the HTML


// Create Maps for Member Translation
const membersMap = {}; // English -> Hebrew
const reverseMembersMap = {}; // Hebrew -> English

if (allMembers) {
    allMembers.forEach(m => {
        membersMap[m.name_en] = m.name_he;
        reverseMembersMap[m.name_he] = m.name_en;
    });
}

// Helper: Parse members input (Hebrew/English mixed) -> English Array
function parseMembersInput(inputString) {
    if (!inputString) return [];
    return inputString.split(/[, ]+/).map(s => s.trim()).filter(s => s)
        .map(s => {
            // Check if it's a known Hebrew name
            if (reverseMembersMap[s]) return reverseMembersMap[s];
            // Check if it's a known English name (case insensitive)
            const lowerS = s.toLowerCase();
            const foundMember = allMembers.find(m => m.name_en.toLowerCase() === lowerS);
            if (foundMember) return foundMember.name_en;
            // Otherwise return as is (maybe new member or unknown)
            return s;
        });
}

// Helper: Format members for display (English Array -> Hebrew String)
function formatMembersForDisplay(membersArray) {
    if (!membersArray || !Array.isArray(membersArray)) return '';
    return membersArray.map(m => membersMap[m] || m).join(', ');
}

// Helper: Format Date YYYY-MM-DD -> dd/mm/yyyy
function formatDateForDisplay(dateStr) {
    if (!dateStr) return '';
    try {
        const [y, m, d] = dateStr.split('-');
        return `${d}/${m}/${y}`;
    } catch (e) { return dateStr; }
}

// DOM Elements
const tableBody = document.getElementById('taskTableBody');
const teamFilter = document.getElementById('teamFilter');
const searchInput = document.getElementById('searchInput');

// Render initial tasks
function renderTasks() {
    tableBody.innerHTML = '';

    const selectedTeam = teamFilter.value;
    const searchTerm = searchInput.value.toLowerCase().trim();

    const filteredTasks = initialTasks.filter(task => {
        // Filter by Team
        if (selectedTeam !== 'all' && task.team_id != selectedTeam) {
            return false;
        }
        // Filter by Search
        if (searchTerm) {
            const team = allTeams.find(t => t.id === task.team_id);
            const teamName = team ? team.name_he : '';
            const membersDisplay = formatMembersForDisplay(task.members); // Search in Hebrew names
            const fullText = `${teamName} ${task.project} ${task.task} ${membersDisplay} ${task.notes} `.toLowerCase();
            return fullText.includes(searchTerm);
        }
        return true;
    });

    filteredTasks.forEach(task => {
        const row = document.createElement('tr');
        row.dataset.id = task.id;

        // Team Cell
        const team = allTeams.find(t => t.id === task.team_id);
        row.innerHTML = `
            <td class="editable-cell" data-field="team_id" data-type="select-team">${team ? team.name_he : '---'}</td>
            <td class="editable-cell" data-field="project">${task.project || ''}</td>
            <td class="editable-cell" data-field="task">${task.task || ''}</td>
            <td class="editable-cell" data-field="members">${formatMembersForDisplay(task.members)}</td>
            <td class="editable-cell" data-field="start_date" data-type="date" data-raw="${task.start_date || ''}">${formatDateForDisplay(task.start_date)}</td>
            <td class="editable-cell" data-field="end_date" data-type="date" data-raw="${task.end_date || ''}">${formatDateForDisplay(task.end_date)}</td>
            <td class="editable-cell" data-field="status" data-type="select-status">${getStatusLabel(task.status)}</td>
            <td class="editable-cell" data-field="priority" data-type="select-priority">${getPriorityLabel(task.priority)}</td>
            <td class="editable-cell" data-field="notes" style="white-space: pre-wrap;">${task.notes || ''}</td>
            <td>
                <button class="btn-icon delete-btn" title="מחק">🗑️</button>
            </td>
`;
        tableBody.appendChild(row);
    });
}

// Helpers
function getStatusLabel(status) {
    const map = {
        'status-notstarted': 'טרם החל',
        'status-inprogress': 'בתהליך',
        'status-done': 'הושלם',
        'status-delayed': 'מעוכב'
    };
    return map[status] || status;
}

function getPriorityLabel(priority) {
    const map = {
        'none': 'ללא',
        'low': 'נמוכה',
        'medium': 'בינונית',
        'high': 'גבוהה'
    };
    return map[priority] || priority;
}

// Event Delegation for Interactions
tableBody.addEventListener('click', (e) => {
    const cell = e.target.closest('.editable-cell');
    if (cell && !cell.classList.contains('editing')) {
        makeEditable(cell);
    }

    if (e.target.closest('.delete-btn')) {
        const row = e.target.closest('tr');
        deleteTask(row.dataset.id);
    }
});

function makeEditable(cell) {
    cell.classList.add('editing');
    const currentValue = cell.innerText;
    const field = cell.dataset.field;
    const type = cell.dataset.type || 'text';
    const taskId = cell.closest('tr').dataset.id;

    let input;

    if (type === 'select-status') {
        input = document.createElement('select');
        input.classList.add('status-select', 'editable-input');
        input.innerHTML = `
            <option value="status-notstarted">טרם החל</option>
            <option value="status-inprogress">בתהליך</option>
            <option value="status-done">הושלם</option>
            <option value="status-delayed">מעוכב</option>
        `;
        // Set value from task object ideally, but simplistic reverse lookup for now
        // A better way is to find task in initialTasks by id
        const task = initialTasks.find(t => t.id == taskId);
        input.value = task.status;
    } else if (type === 'select-priority') {
        input = document.createElement('select');
        input.classList.add('priority-select', 'editable-input');
        input.innerHTML = `
            <option value="none">ללא</option>
            <option value="low">נמוכה</option>
            <option value="medium">בינונית</option>
            <option value="high">גבוהה</option>
        `;
        const task = initialTasks.find(t => t.id == taskId);
        input.value = task.priority;
    } else if (type === 'select-team') {
        input = document.createElement('select');
        input.classList.add('team-select', 'editable-input');
        allTeams.forEach(t => {
            const opt = document.createElement('option');
            opt.value = t.id;
            opt.text = t.name_he;
            input.appendChild(opt);
        });
        const task = initialTasks.find(t => t.id == taskId);
        input.value = task.team_id;
    } else if (type === 'date') {
        input = document.createElement('input');
        input.type = 'text'; // Use text for flatpickr
        // Use raw value (YYYY-MM-DD) for flatpickr initialization
        const rawValue = cell.dataset.raw || '';
        input.value = rawValue;
        input.classList.add('editable-input');

        input.classList.add('editable-input');

        // Append input to cell FIRST
        cell.innerHTML = '';
        cell.appendChild(input);

        // Initialize flatpickr on the attached element
        const fp = flatpickr(input, {
            locale: "he",
            dateFormat: "Y-m-d",
            altInput: true,
            altFormat: "d/m/Y",
            allowInput: true,
            defaultDate: rawValue,
            onClose: function (selectedDates, dateStr, instance) {
                // Save on close
                saveCell(cell, dateStr, taskId, field);
            }
        });

        // Open immediately so user knows it's editable
        fp.open();

        return;
        return;
    } else if (field === 'notes') {
        input = document.createElement('textarea');
        input.value = currentValue;
        input.classList.add('editable-input');
        input.style.width = '100%';
        input.style.minHeight = '60px'; // Make it large enough
        input.style.resize = 'vertical';
    } else {
        input = document.createElement('input');
        input.type = 'text';
        input.value = currentValue;
        input.classList.add('editable-input');
    }

    cell.innerHTML = '';
    cell.appendChild(input);
    input.focus();

    // Save on blur or enter (for non-date inputs)
    input.addEventListener('blur', () => saveCell(cell, input.value, taskId, field));
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) { // Shift+Enter for newline in textarea
            e.preventDefault(); // Prevent newline in textarea if we are saving
            input.blur();
        }
    });
}

function saveCell(cell, newValue, taskId, field) {
    const task = initialTasks.find(t => t.id == taskId);
    let apiValue = newValue;

    // Update local object
    if (field === 'members') {
        const parsedMembers = parseMembersInput(newValue);
        task[field] = parsedMembers;
        apiValue = parsedMembers; // API expects array of English names
    } else {
        task[field] = newValue;
    }

    // Optimistic UI update
    cell.classList.remove('editing');
    if (field === 'status') cell.innerText = getStatusLabel(newValue);
    else if (field === 'priority') cell.innerText = getPriorityLabel(newValue);
    else if (field === 'team_id') {
        const t = allTeams.find(team => team.id == newValue);
        cell.innerText = t ? t.name_he : newValue;
    }
    else if (field === 'members') {
        cell.innerText = formatMembersForDisplay(task.members);
    }
    else if (field === 'start_date' || field === 'end_date') {
        // Update data-raw and display format
        cell.dataset.raw = apiValue; // apiValue is YYYY-MM-DD from Flatpickr
        cell.innerText = formatDateForDisplay(apiValue);
    }
    else cell.innerText = newValue;

    // Send to API
    const payload = {};
    payload[field] = apiValue;

    fetch(`/api/tasks/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    }).then(res => res.json())
        .then(data => {
            if (!data.success) {
                alert('Error saving');
                // Revert?
            }
        });
}

// Add New Task (Standalone Form)
document.querySelectorAll('.btn-add-task-submit').forEach(btn => {
    btn.addEventListener('click', (e) => {
        // Handle click on icon or button
        const button = e.target.closest('.btn-add-task-submit');
        if (!button) return;

        console.log("Add Task Button Clicked");

        try {
            // Find container: closest .add-task-form (was tr)
            const container = button.closest('.add-task-form') || button.closest('tr'); // Fallback just in case

            if (!container) throw new Error("Could not find container form");

            const teamIdInput = container.querySelector('.input-team');
            if (!teamIdInput) throw new Error("Could not find Team input");
            const teamId = teamIdInput.value;

            const projectInput = container.querySelector('.input-project');
            const taskNameInput = container.querySelector('.input-task');
            if (!taskNameInput) throw new Error("Could not find Task input");

            const membersInput = container.querySelector('.input-members');
            const startDateInput = container.querySelector('.input-start-date');
            const endDateInput = container.querySelector('.input-end-date');
            const statusInput = container.querySelector('.input-status');
            const priorityInput = container.querySelector('.input-priority');
            const notesInput = container.querySelector('.input-notes');
            const keepValuesCheckbox = container.querySelector('.input-keep-values');

            const status = statusInput ? statusInput.value : '';
            const priority = priorityInput ? priorityInput.value : '';

            const project = projectInput ? projectInput.value : '';
            const taskName = taskNameInput.value;
            const members = membersInput ? parseMembersInput(membersInput.value) : []; // Parse Hebrew input to English array
            const startDate = startDateInput ? startDateInput.value : '';
            const endDate = endDateInput ? endDateInput.value : '';
            const notes = notesInput ? notesInput.value : '';

            if (!taskName) {
                alert('אנא הזן שם משימה');
                return;
            }

            const payload = {
                team_id: parseInt(teamId),
                project: project,
                task: taskName,
                members: members, // This will be an array of English names
                start_date: startDate,
                end_date: endDate,
                status: status,
                priority: priority,
                notes: notes
            };

            console.log("Submitting Payload", payload);

            fetch('/api/tasks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            }).then(res => res.json())
                .then(data => {
                    if (data.success) {
                        // Add id to payload and PREPEND to local list (unshift)
                        payload.id = data.id;
                        initialTasks.unshift(payload); // Add to top
                        renderTasks(); // Re-render table

                        // Clear inputs based on Keep Values
                        if (!keepValuesCheckbox || !keepValuesCheckbox.checked) {
                            if (projectInput) projectInput.value = '';
                        }
                        taskNameInput.value = '';
                        if (membersInput) membersInput.value = '';
                        if (startDateInput) startDateInput.value = '';
                        if (endDateInput) endDateInput.value = '';
                        if (notesInput) notesInput.value = '';

                        // Clear date pickers if they exist
                        if (startDateInput && startDateInput._flatpickr) startDateInput._flatpickr.clear();
                        if (endDateInput && endDateInput._flatpickr) endDateInput._flatpickr.clear();

                    } else {
                        alert('Error creating task: ' + (data.error || 'Unknown error'));
                    }
                }).catch(err => {
                    console.error("Fetch Error:", err);
                    alert("Fetch Error: " + err.message);
                });
        } catch (e) {
            console.error(e);
            alert("Javascript Error: " + e.message);
        }
    });
});

function deleteTask(id) {
    if (!confirm('האם אתה בטוח שברצונך למחוק משימה זו?')) return;

    fetch(`/api/tasks/${id}`, {
        method: 'DELETE'
    }).then(res => res.json())
        .then(data => {
            if (data.success) {
                const idx = initialTasks.findIndex(t => t.id == id);
                if (idx > -1) initialTasks.splice(idx, 1);
                renderTasks();
            } else {
                alert('Error deleting');
            }
        });
}

// Filter Event Listeners
teamFilter.addEventListener('change', renderTasks);
searchInput.addEventListener('input', renderTasks);

// Initial Render
renderTasks();
