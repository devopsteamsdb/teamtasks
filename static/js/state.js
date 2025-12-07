// State Management

export const state = {
    teams: [],
    members: [],
    currentTaskItem: null,
    activeTeamFilter: null,
    activeMemberFilter: null,
    searchTimeout: null,
    lastUpdateTimestamp: 0
};

export function setTeams(newTeams) {
    state.teams = newTeams;
}

export function setMembers(newMembers) {
    state.members = newMembers;
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

export function setLastUpdateTimestamp(ts) {
    state.lastUpdateTimestamp = ts;
}
