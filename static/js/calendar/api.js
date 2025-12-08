// Calendar API

import { getWeekStart, formatDateToISO } from './utils.js'; // We'll create utils next
// Or import generic utils if possible. Let's make a local utils for calendar specific stuff or use shared.
// We need to fetch data.

export async function fetchWeekData(date, teamId) {
    try {
        const weekStart = getWeekStart(date);
        const weekEnd = new Date(weekStart);
        weekEnd.setDate(weekEnd.getDate() + 6); // 7 days inclusive

        let url = `/api/calendar/week?start_date=${formatDateToISO(weekStart)}&end_date=${formatDateToISO(weekEnd)}`;

        if (teamId) {
            url += `&team_id=${teamId}`;
        }

        const response = await fetch(url);
        return await response.json();
    } catch (error) {
        console.error('Error loading week data:', error);
        return { tasks: [] };
    }
}

export async function fetchWorkloadData(date, teamId) {
    try {
        const weekStart = getWeekStart(date);
        const weekEnd = new Date(weekStart);
        weekEnd.setDate(weekEnd.getDate() + 4); // 5 days (Sun-Thu)

        let url = `/api/calendar/workload?start_date=${formatDateToISO(weekStart)}&end_date=${formatDateToISO(weekEnd)}`;

        if (teamId) {
            url += `&team_id=${teamId}`;
        }

        const response = await fetch(url);
        return await response.json();
    } catch (error) {
        console.error('Error loading workload data:', error);
        return { workload: [] };
    }
}

export async function fetchSpecialDays() {
    try {
        const response = await fetch('/api/special-days');
        return await response.json();
    } catch (error) {
        console.error('Error loading special days:', error);
        return [];
    }
}

export async function updateTaskSchedule(taskId, startDate, endDate, estimatedHours) {
    try {
        const response = await fetch(`/api/tasks/${taskId}/schedule`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                start_date: startDate,
                end_date: endDate,
                estimated_hours: estimatedHours
            })
        });
        return await response.json();
    } catch (error) {
        console.error('Error saving task schedule:', error);
        throw error;
    }
}

export async function addSpecialDay(date, name, type) {
    // Assuming there is an endpoint for this, though the original parsed code didn't show the POST implementation fully.
    // The original code had manageHolidaysBtn logic cut off.
    // I will assume standard POST /api/special-days or similar if it exists, or just log error if not implemented.
    // Checking original code... it ended with `loadSpecialDaysList` and modal display. 
    // It didn't fully show the save logic. 
    // I will implement a placeholder or basic POST if I can infer it. 
    // Let's assume standard REST.
    try {
        const response = await fetch('/api/special-days', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ date, name, type })
        });
        return await response.json();
    } catch (error) {
        console.error('Error adding special day:', error);
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

export async function updateTask(id, taskData) {
    try {
        const response = await fetch(`/api/tasks/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(taskData)
        });
        return await response.json();
    } catch (error) {
        console.error('Error updating task:', error);
        throw error;
    }
}

export async function deleteTask(id) {
    try {
        const response = await fetch(`/api/tasks/${id}`, {
            method: 'DELETE'
        });
        return await response.json();
    } catch (error) {
        console.error('Error deleting task:', error);
        throw error;
    }
}

export async function fetchTeams() {
    try {
        const response = await fetch('/api/teams?mode=active');
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
