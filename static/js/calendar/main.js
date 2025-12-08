// Calendar Main
import * as API from './api.js';
import * as UI from './ui.js';
import * as Events from './events.js';
import { state, setCurrentView, setActiveTeamFilter, setSpecialDays, setTasks, setTeams, setMembers } from './state.js';

async function init() {
    UI.updateDOMElements();
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

    // Listen to custom events
    window.addEventListener('calendar:refresh', () => renderCurrentView());
    window.addEventListener('calendar:switchView', (e) => {
        setCurrentView(e.detail.view);
        UI.switchView(e.detail.view);
        renderCurrentView();
    });

    // Special Days load
    const specialDays = await API.fetchSpecialDays();
    setSpecialDays(specialDays);

    // Initial Fetch of Teams and Members for Modal
    const teams = await API.fetchTeams();
    setTeams(teams);
    const members = await API.fetchMembers();
    setMembers(members);

    await renderCurrentView();

    // Links to task board
    const navTasks = document.getElementById('navTasksLink');
    if (navTasks) {
        navTasks.addEventListener('click', (e) => {
            e.preventDefault();
            if (state.activeTeamFilter === 'archive') {
                window.location.href = '/?mode=archive';
            } else if (state.activeTeamFilter) {
                window.location.href = `/?team=${state.activeTeamFilter}`;
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
