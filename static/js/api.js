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
        const response = await fetch(url);
        return await response.text();
    } catch (error) {
        console.error('Error fetching page content:', error);
        throw error;
    }
}
