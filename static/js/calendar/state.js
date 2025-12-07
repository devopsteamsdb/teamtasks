// Calendar State

export const state = {
    currentView: 'week', // 'week' or 'workload'
    currentDate: new Date(),
    activeTeamFilter: null,
    tasks: [],
    specialDays: [],
    currentTaskId: null
};

export function setCurrentView(view) {
    state.currentView = view;
}

export function setCurrentDate(date) {
    state.currentDate = date;
}

export function setActiveTeamFilter(filter) {
    state.activeTeamFilter = filter;
}

export function setTasks(tasks) {
    state.tasks = tasks;
}

export function setSpecialDays(days) {
    state.specialDays = days;
}

export function setCurrentTaskId(id) {
    state.currentTaskId = id;
}
