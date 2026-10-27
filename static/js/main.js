// Main Entry Point
import * as API from './api.js';
import * as UI from './ui.js';
import * as Events from './events.js';
import * as Utils from './utils.js';
import { state, setTeams, setMembers, setProjects, setLastUpdateTimestamp, setActiveTeamFilter, setActiveMemberFilter, setStatusFilter, setPriorityFilter, setCurrentTaskItem } from './state.js';
import { subscribeLiveSync } from './live_sync.js';

// Expose for global coordination (e.g. AI Assistant)
window.mainUI = UI;
window.mainEvents = Events;
window.mainState = state;
window.setCurrentTaskItem = setCurrentTaskItem;

let isUpdating = false;

async function checkForUpdates() {
    if (isUpdating) return;
    try {
        const data = await API.fetchVersion();
        if (data && data.timestamp && state.lastUpdateTimestamp && data.timestamp > state.lastUpdateTimestamp) {
            isUpdating = true;
            setLastUpdateTimestamp(data.timestamp);
            await UI.refreshContent(Events.attachEventListeners);
            isUpdating = false;
        }
    } catch (e) {
        isUpdating = false;
    }
}

async function init() {
    UI.updateDOMElements();
    UI.initializeFlatpickr();

    // Load Initial Data
    const [teams, members, projects, versionData] = await Promise.all([
        API.fetchTeams(),
        API.fetchMembers(),
        API.fetchProjects(),
        API.fetchVersion()
    ]);

    setTeams(teams);
    setMembers(members);
    setProjects(projects);
    if (versionData) {
        setLastUpdateTimestamp(versionData.timestamp);
    }

    UI.populateDropdowns();
    UI.populateProjectDropdowns();
    UI.populateProjectTeamCheckboxes();
    UI.populateMemberCheckboxes();
    Events.attachEventListeners();
    Events.attachGlobalListeners();

    // Start fast polling (every 1.5 seconds)
    setInterval(checkForUpdates, 1500);

    // Live cross-tab sync listener
    subscribeLiveSync(async () => {
        await UI.refreshContent(Events.attachEventListeners);
    });

    // Initial State from URL / LocalStorage
    const urlParams = new URLSearchParams(window.location.search);
    const mode = urlParams.get('mode');
    const teamId = urlParams.get('team');
    const storedTeamId = localStorage.getItem('activeTeamFilter');

    if (mode === 'archive') {
        setActiveTeamFilter('archive');
        localStorage.setItem('activeTeamFilter', 'archive');
    } else if (teamId) {
        setActiveTeamFilter(teamId);
        localStorage.setItem('activeTeamFilter', teamId);
    } else if (storedTeamId) {
        setActiveTeamFilter(storedTeamId);
        if (storedTeamId === 'archive') {
            const url = new URL(window.location);
            url.searchParams.set('mode', 'archive');
            window.history.replaceState({}, '', url);
            await UI.refreshContent(Events.attachEventListeners);
            return;
        } else {
            const url = new URL(window.location);
            url.searchParams.set('team', storedTeamId);
            window.history.replaceState({}, '', url);
        }
    } else {
        setActiveTeamFilter(null);
    }

    const urlParams = new URLSearchParams(window.location.search);
    const urlStatus = urlParams.get('status');
    const storedStatus = urlStatus || localStorage.getItem('activeStatusFilter');
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

    const storedMember = localStorage.getItem('activeMemberFilter');
    if (storedMember) {
        setActiveMemberFilter(storedMember);
    }

    UI.applyFilters();
}

// Run init when DOM is ready
document.addEventListener('DOMContentLoaded', init);
