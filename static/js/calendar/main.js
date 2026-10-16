// Calendar Main
import * as API from './api.js';
import * as UI from './ui.js';
import * as Events from './events.js';
import { state, setCurrentView, setActiveTeamFilter, setSpecialDays, setTasks, setTeams, setMembers, setStatusFilter, setPriorityFilter } from './state.js';
import { subscribeLiveSync } from '../live_sync.js';

// Expose for global coordination (e.g. AI Assistant)
window.calendarUI = UI;
window.calendarEvents = Events;
window.calendarState = state;

let lastCalendarVersion = null;
let isUpdating = false;

async function checkCalendarUpdates() {
    if (isUpdating) return;
    try {
        const data = await API.fetchVersion();
        if (data && typeof data.timestamp !== 'undefined') {
            if (lastCalendarVersion === null) {
                lastCalendarVersion = data.timestamp;
                return;
            }
            if (data.timestamp > lastCalendarVersion) {
                lastCalendarVersion = data.timestamp;
                if (!UI.isModalOpen()) {
                    isUpdating = true;
                    const specialDays = await API.fetchSpecialDays();
                    setSpecialDays(specialDays);
                    await renderCurrentView();
                    isUpdating = false;
                }
            }
        }
    } catch (e) {
        isUpdating = false;
    }
}

async function init() {
    UI.updateDOMElements();
    UI.initializeFlatpickr();
    Events.attachEventListeners();

    // Init Logic
    const storedTeamId = localStorage.getItem('activeTeamFilter');
    if (storedTeamId) {
        setActiveTeamFilter(storedTeamId);
        // Visual update of buttons
        if (UI.elements.teamFilterBtns) {
            UI.elements.teamFilterBtns.forEach(btn => {
                if (btn.dataset.teamId === storedTeamId) btn.classList.add('active');
                else btn.classList.remove('active');
            });
        }
    }

    const storedStatus = localStorage.getItem('activeStatusFilter');
    if (storedStatus) {
        setStatusFilter(storedStatus);
        if (UI.elements.filterStatus) {
            UI.elements.filterStatus.value = storedStatus;
        }
    }

    const storedPriority = localStorage.getItem('activePriorityFilter');
    if (storedPriority) {
        setPriorityFilter(storedPriority);
        if (UI.elements.filterPriority) {
            UI.elements.filterPriority.value = storedPriority;
        }
    }

    // Listen to custom events
    window.addEventListener('calendar:refresh', () => renderCurrentView());
    window.addEventListener('teamtasks:refresh', async () => {
        if (!UI.isModalOpen()) {
            const specialDays = await API.fetchSpecialDays();
            setSpecialDays(specialDays);
            await renderCurrentView();
        }
    });

    window.addEventListener('calendar:switchView', (e) => {
        setCurrentView(e.detail.view);
        UI.switchView(e.detail.view);
        renderCurrentView();
    });

    // Cross-tab live sync
    subscribeLiveSync(async () => {
        if (!UI.isModalOpen()) {
            const specialDays = await API.fetchSpecialDays();
            setSpecialDays(specialDays);
            await renderCurrentView();
        }
    });

    // Special Days load
    const specialDays = await API.fetchSpecialDays();
    setSpecialDays(specialDays);

    // Initial Fetch of Teams and Members for Modal
    const [teams, members, versionData] = await Promise.all([
        API.fetchTeams(),
        API.fetchMembers(),
        API.fetchVersion()
    ]);
    setTeams(teams);
    setMembers(members);
    if (versionData && typeof versionData.timestamp !== 'undefined') {
        lastCalendarVersion = versionData.timestamp;
    }

    await renderCurrentView();

    // Start fast polling (every 1.5 seconds)
    setInterval(checkCalendarUpdates, 1500);

    // Links to task board - Preserve all filters
    const navTasks = document.getElementById('navTasksLink');
    if (navTasks) {
        navTasks.addEventListener('click', (e) => {
            e.preventDefault();
            const storedTeam = localStorage.getItem('activeTeamFilter');
            if (storedTeam === 'archive') {
                window.location.href = '/?mode=archive';
            } else if (storedTeam) {
                window.location.href = `/?team=${encodeURIComponent(storedTeam)}`;
            } else {
                window.location.href = '/';
            }
        });
    }
}

export async function renderCurrentView() {
    // Determine what to fetch
    if (state.currentView === 'week') {
        const data = await API.fetchWeekData(state.currentDate, state.activeTeamFilter);
        setTasks(data.tasks || []);
        UI.renderWeekView();
    } else if (state.currentView === 'workload') {
        const data = await API.fetchWorkloadData(state.currentDate, state.activeTeamFilter);
        setTasks(data.workload || []); // reusing tasks state for member-workload array?
        // Note: UI.renderWorkloadView expects state.tasks to be the array of member data.
        UI.renderWorkloadView();
    }
}

document.addEventListener('DOMContentLoaded', init);
