// Main Entry Point
import * as API from './api.js';
import * as UI from './ui.js';
import * as Events from './events.js';
import * as Utils from './utils.js';
import { state, setTeams, setMembers, setLastUpdateTimestamp, setActiveTeamFilter } from './state.js';

async function init() {
    UI.updateDOMElements();
    UI.initializeFlatpickr();

    // Load Initial Data
    const [teams, members, versionData] = await Promise.all([
        API.fetchTeams(),
        API.fetchMembers(),
        API.fetchVersion()
    ]);

    setTeams(teams);
    setMembers(members);
    if (versionData) {
        setLastUpdateTimestamp(versionData.timestamp);
    }

    UI.populateDropdowns();
    UI.populateMemberCheckboxes();
    Events.attachEventListeners();
    Events.attachGlobalListeners();

    // Start polling
    setInterval(checkForUpdates, 5000);

    // Initial State from URL / LocalStorage
    const urlParams = new URLSearchParams(window.location.search);
    const mode = urlParams.get('mode');
    const teamId = urlParams.get('team');
    const storedTeamId = localStorage.getItem('activeTeamFilter');

    if (mode === 'archive') {
        setActiveTeamFilter('archive');
    } else if (teamId) {
        setActiveTeamFilter(teamId);
    } else if (storedTeamId) {
        // Determine if we should apply stored filter
        // If stored is 'archive', we probably want to switch to archive mode?
        if (storedTeamId === 'archive') {
            setActiveTeamFilter('archive');
            // Update URL
            const url = new URL(window.location);
            url.searchParams.set('mode', 'archive');
            window.history.replaceState({}, '', url);
            // We might need to refresh content if the server didn't render archive mode?
            // But if we just loaded the page, the server rendered what the URL said.
            // If URL didn't have mode=archive, but we force it now, we might need reload.
            // However, let's assume if user landed without params, server rendered active tasks.
            // If we switch to archive locally, we need to fetch archive content?
            // Yes, because archive is server-side filtered usually (or maybe not? original code refreshed for archive).
            // Let's safe bet: if we change mode from default to archive based on LS, we should refresh.
            if (mode !== 'archive') {
                await UI.refreshContent(Events.attachEventListeners);
                return; // refreshContent will re-run logic eventually or we stop here?
                // refreshContent re-runs nothing of main.js, just updates DOM and re-attaches listeners.
                // So we are good.
            }
        } else {
            setActiveTeamFilter(storedTeamId);
            // Update URL
            const url = new URL(window.location);
            url.searchParams.set('team', storedTeamId);
            // Ensure mode is active
            url.searchParams.set('mode', 'active');
            window.history.replaceState({}, '', url);
        }
    }

    UI.applyFilters();
}

// Run init when DOM is ready
document.addEventListener('DOMContentLoaded', init);
