// API Interactions

export async function fetchTeams() {
    try {
        const response = await fetch('/api/teams');
        return await response.json();
    } catch (error) {
        console.error('Error loading teams:', error);
        return [];
    }
}

export async function fetchMembers() {
    try {
        const response = await fetch('/api/members');
        return await response.json();
    } catch (error) {
        console.error('Error loading members:', error);
        return [];
    }
}

export async function fetchProjects(mode = 'all') {
    try {
        const response = await fetch(`/api/projects?mode=${encodeURIComponent(mode)}`);
        return await response.json();
    } catch (error) {
        console.error('Error loading projects:', error);
        return [];
    }
}

export async function createProject(payload) {
    try {
        const response = await fetch('/api/projects', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        return await response.json();
    } catch (error) {
        console.error('Error creating project:', error);
        throw error;
    }
}

export async function updateProject(id, payload) {
    try {
        const response = await fetch(`/api/projects/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        return await response.json();
    } catch (error) {
        console.error('Error updating project:', error);
        throw error;
    }
}

export async function deleteProject(id) {
    try {
        const response = await fetch(`/api/projects/${id}`, {
            method: 'DELETE'
        });
        return await response.json();
    } catch (error) {
        console.error('Error deleting project:', error);
        throw error;
    }
}

export async function archiveProject(id) {
    try {
        const response = await fetch(`/api/projects/${id}/archive`, {
            method: 'POST'
        });
        return await response.json();
    } catch (error) {
        console.error('Error archiving project:', error);
        throw error;
    }
}

export async function unarchiveProject(id) {
    try {
        const response = await fetch(`/api/projects/${id}/unarchive`, {
            method: 'POST'
        });
        return await response.json();
    } catch (error) {
        console.error('Error unarchiving project:', error);
        throw error;
    }
}

export async function fetchVersion() {
    try {
        const response = await fetch('/api/version?t=' + new Date().getTime());
        return await response.json();
    } catch (error) {
        console.error('Error checking version:', error);
        return null; // Return null on error
    }
}

export async function updateTask(taskId, payload) {
    try {
        const response = await fetch(`/api/tasks/${taskId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        return await response.json();
    } catch (error) {
        console.error('Error saving task:', error);
        throw error;
    }
}

export async function createTask(payload) {
    try {
        const response = await fetch('/api/tasks', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        return await response.json();
    } catch (error) {
        console.error('Error creating task:', error);
        throw error;
    }
}

export async function deleteTask(taskId) {
    try {
        const response = await fetch(`/api/tasks/${taskId}`, {
            method: 'DELETE'
        });
        return await response.json();
    } catch (error) {
        console.error('Error deleting task:', error);
        throw error;
    }
}

export async function archiveTask(taskId) {
    try {
        const response = await fetch(`/api/tasks/${taskId}/archive`, {
            method: 'POST'
        });
        return await response.json();
    } catch (error) {
        console.error('Error archiving task:', error);
        throw error;
    }
}

export async function unarchiveTask(taskId) {
    try {
        const response = await fetch(`/api/tasks/${taskId}/unarchive`, {
            method: 'POST'
        });
        return await response.json();
    } catch (error) {
        console.error('Error unarchiving task:', error);
        throw error;
    }
}

export async function searchTasks(query) {
    try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        return await response.json();
    } catch (error) {
        console.error('Search error:', error);
        throw error;
    }
}

export async function fetchPageContent(url) {
    try {
        const u = new URL(url, window.location.origin);
        u.searchParams.set('_t', Date.now().toString());
        const response = await fetch(u.toString(), {
            headers: {
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache'
            }
        });
        return await response.text();
    } catch (error) {
        console.error('Error fetching page content:', error);
        throw error;
    }
}

// Subtasks API
export async function fetchTaskSubtasks(taskId) {
    try {
        const response = await fetch(`/api/tasks/${taskId}/subtasks`);
        return await response.json();
    } catch (error) {
        console.error('Error fetching subtasks:', error);
        return [];
    }
}

export async function createSubtask(taskId, title) {
    try {
        const response = await fetch(`/api/tasks/${taskId}/subtasks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: title })
        });
        return await response.json();
    } catch (error) {
        console.error('Error creating subtask:', error);
        throw error;
    }
}

export async function updateSubtask(subtaskId, payload) {
    try {
        const response = await fetch(`/api/subtasks/${subtaskId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        return await response.json();
    } catch (error) {
        console.error('Error updating subtask:', error);
        throw error;
    }
}

export async function deleteSubtask(subtaskId) {
    try {
        const response = await fetch(`/api/subtasks/${subtaskId}`, {
            method: 'DELETE'
        });
        return await response.json();
    } catch (error) {
        console.error('Error deleting subtask:', error);
        throw error;
    }
}

// Comments API
export async function fetchTaskComments(taskId) {
    try {
        const response = await fetch(`/api/tasks/${taskId}/comments`);
        return await response.json();
    } catch (error) {
        console.error('Error fetching comments:', error);
        return [];
    }
}

export async function createTaskComment(taskId, payload) {
    try {
        const response = await fetch(`/api/tasks/${taskId}/comments`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        return await response.json();
    } catch (error) {
        console.error('Error creating comment:', error);
        throw error;
    }
}

export async function deleteTaskComment(commentId) {
    try {
        const response = await fetch(`/api/comments/${commentId}`, {
            method: 'DELETE'
        });
        return await response.json();
    } catch (error) {
        console.error('Error deleting comment:', error);
        throw error;
    }
}

// Special Days API
export async function fetchSpecialDays(startDateStr = '', endDateStr = '') {
    try {
        let url = '/api/special-days';
        if (startDateStr && endDateStr) {
            url += `?start_date=${encodeURIComponent(startDateStr)}&end_date=${encodeURIComponent(endDateStr)}`;
        }
        const response = await fetch(url);
        return await response.json();
    } catch (error) {
        console.error('Error loading special days:', error);
        return [];
    }
}

export async function createSpecialDay(payload) {
    try {
        const response = await fetch('/api/special-days', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        return await response.json();
    } catch (error) {
        console.error('Error creating special day:', error);
        throw error;
    }
}

export async function updateSpecialDay(id, payload) {
    try {
        const response = await fetch(`/api/special-days/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        return await response.json();
    } catch (error) {
        console.error('Error updating special day:', error);
        throw error;
    }
}

export async function deleteSpecialDay(id) {
    try {
        const response = await fetch(`/api/special-days/${id}`, {
            method: 'DELETE'
        });
        return await response.json();
    } catch (error) {
        console.error('Error deleting special day:', error);
        throw error;
    }
}
