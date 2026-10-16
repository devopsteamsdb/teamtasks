// State Management

export const state = {
    teams: [],
    members: [],
    projects: [],
    currentTaskItem: null,
    currentProjectId: null,
    activeTeamFilter: null,
    activeMemberFilter: null,
    statusFilter: 'all',
    priorityFilter: 'all',
    searchTimeout: null,
    lastUpdateTimestamp: 0
};

export function setTeams(newTeams) {
    state.teams = newTeams;
}

export function setMembers(newMembers) {
    state.members = newMembers;
}

export function setProjects(newProjects) {
    state.projects = newProjects;
}

export function setCurrentProjectId(id) {
    state.currentProjectId = id;
}

export function setCurrentTaskItem(item) {
    state.currentTaskItem = item;
}

export function setActiveTeamFilter(filter) {
    state.activeTeamFilter = filter;
}

export function setActiveMemberFilter(filter) {
    state.activeMemberFilter = filter;
}

export function setStatusFilter(filter) {
    state.statusFilter = filter;
}

export function setPriorityFilter(filter) {
    state.priorityFilter = filter;
}

export function setLastUpdateTimestamp(ts) {
    state.lastUpdateTimestamp = ts;
}
