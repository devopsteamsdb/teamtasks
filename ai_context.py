from datetime import datetime, date, timedelta
from models import db, Team, TeamMember, Project, Task, SpecialDay

def get_current_date():
    return date.today()

def format_date_hebrew(d):
    if not d:
        return ""
    days_he = ["שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת", "ראשון"]
    day_name = days_he[d.weekday()]
    return f"{d.strftime('%d/%m/%Y')} (יום {day_name})"

def build_system_context():
    """Builds a comprehensive system snapshot for the AI context."""
    today = get_current_date()
    
    # Teams & Members
    teams = Team.query.all()
    all_members = TeamMember.query.all()
    teams_data = []
    members_lookup = {}  # en -> he, and he -> en
    for m in all_members:
        if m.name_en and m.name_he:
            members_lookup[m.name_en.lower()] = m.name_he
            members_lookup[m.name_he] = m.name_en

    for t in teams:
        team_members = []
        for m in t.members:
            team_members.append({
                'id': m.id,
                'name_en': m.name_en,
                'name_he': m.name_he
            })
        teams_data.append({
            'id': t.id,
            'name_en': t.name_en,
            'name_he': t.name_he,
            'members': team_members
        })

    # Projects
    # Active Projects
    projects = Project.query.filter_by(is_archived=False).order_by(Project.name).all()
    projects_data = []
    for p in projects:
        projects_data.append({
            'id': p.id,
            'name': p.name,
            'teams': [{'id': t.id, 'name_he': t.name_he, 'name_en': t.name_en} for t in p.teams],
            'task_count': len([t for t in p.tasks if not t.is_archived])
        })

    # Active Tasks
    tasks = Task.query.filter_by(is_archived=False).all()
    tasks_data = []
    for t in tasks:
        tasks_data.append({
            'id': t.id,
            'project_id': t.project_id,
            'project': t.project,
            'task': t.task,
            'members': t.members.split(',') if t.members else [],
            'status': t.status,
            'priority': t.priority,
            'team_id': t.team_id,
            'start_date': t.start_date.isoformat() if t.start_date else None,
            'end_date': t.end_date.isoformat() if t.end_date else None,
            'estimated_hours': t.estimated_hours,
            'notes': t.notes or ''
        })

    # Archived count and recent archived tasks
    archived_tasks_query = Task.query.filter_by(is_archived=True).order_by(Task.id.desc()).limit(40).all()
    archived_tasks_data = []
    for t in archived_tasks_query:
        archived_tasks_data.append({
            'id': t.id,
            'project_id': t.project_id,
            'project': t.project,
            'task': t.task,
            'members': t.members.split(',') if t.members else [],
            'status': t.status,
            'priority': t.priority,
            'start_date': t.start_date.isoformat() if t.start_date else None,
            'end_date': t.end_date.isoformat() if t.end_date else None,
            'estimated_hours': t.estimated_hours,
            'notes': t.notes or '',
            'is_archived': True
        })
    archived_count = Task.query.filter_by(is_archived=True).count()

    # Special Days upcoming / recent
    special_days = SpecialDay.query.order_by(SpecialDay.date).all()
    special_days_data = [sd.to_dict() for sd in special_days]

    return {
        'today': today.isoformat(),
        'today_hebrew': format_date_hebrew(today),
        'teams': teams_data,
        'projects': projects_data,
        'tasks': tasks_data,
        'archived_tasks': archived_tasks_data,
        'archived_count': archived_count,
        'special_days': special_days_data,
        'members_lookup': members_lookup
    }

def get_executive_summary():
    """Deterministic executive summary of projects, tasks, and workloads."""
    today = get_current_date()
    tasks = Task.query.filter_by(is_archived=False).all()
    projects = Project.query.filter_by(is_archived=False).all()
    members = TeamMember.query.all()

    total_tasks = len(tasks)
    status_counts = {
        'status-done': 0,
        'status-inprogress': 0,
        'status-notstarted': 0,
        'status-delayed': 0
    }
    priority_counts = {'high': 0, 'medium': 0, 'low': 0, 'none': 0}
    
    # Member workload: task count and estimated hours
    member_workload = {
        m.name_en: {
            'name_he': m.name_he,
            'team': m.team.name_he if m.team else 'ללא צוות',
            'count': 0,
            'hours': 0.0
        } for m in members
    }
    unassigned_count = 0

    # Project status
    project_stats = {}
    for p in projects:
        project_stats[p.name] = {'total': 0, 'done': 0, 'in_progress': 0, 'remaining': 0}

    for t in tasks:
        # Status
        status_counts[t.status] = status_counts.get(t.status, 0) + 1
        # Priority
        prio = t.priority or 'none'
        priority_counts[prio] = priority_counts.get(prio, 0) + 1
        
        # Project
        if t.project in project_stats:
            project_stats[t.project]['total'] += 1
            if t.status == 'status-done':
                project_stats[t.project]['done'] += 1
            elif t.status == 'status-inprogress':
                project_stats[t.project]['in_progress'] += 1
            else:
                project_stats[t.project]['remaining'] += 1

        # Member workload
        if t.members:
            assigned = [m.strip().lower() for m in t.members.split(',') if m.strip()]
            for m_en in assigned:
                if m_en in member_workload:
                    member_workload[m_en]['count'] += 1
                    if t.estimated_hours:
                        member_workload[m_en]['hours'] += t.estimated_hours
        else:
            unassigned_count += 1

    completion_rate = round((status_counts['status-done'] / total_tasks * 100), 1) if total_tasks > 0 else 0.0

    return {
        'date': today.isoformat(),
        'date_hebrew': format_date_hebrew(today),
        'total_projects': len(projects),
        'total_tasks': total_tasks,
        'completion_rate': completion_rate,
        'status_counts': status_counts,
        'priority_counts': priority_counts,
        'project_stats': project_stats,
        'member_workload': member_workload,
        'unassigned_count': unassigned_count
    }

def get_deadlines_analysis():
    """Identifies overdue tasks, tasks due this week, and scheduling gaps."""
    today = get_current_date()
    tasks = Task.query.filter_by(is_archived=False).all()
    
    overdue_tasks = []
    due_today_tasks = []
    due_this_week_tasks = []
    missing_dates_tasks = []
    delayed_tasks = []

    week_ahead = today + timedelta(days=7)

    for t in tasks:
        if t.status == 'status-delayed':
            delayed_tasks.append(t.to_dict())

        if not t.end_date:
            missing_dates_tasks.append(t.to_dict())
            continue

        if t.status != 'status-done':
            if t.end_date < today:
                days_overdue = (today - t.end_date).days
                t_dict = t.to_dict()
                t_dict['days_overdue'] = days_overdue
                overdue_tasks.append(t_dict)
            elif t.end_date == today:
                due_today_tasks.append(t.to_dict())
            elif today < t.end_date <= week_ahead:
                days_left = (t.end_date - today).days
                t_dict = t.to_dict()
                t_dict['days_left'] = days_left
                due_this_week_tasks.append(t_dict)

    # Sort overdue by most days overdue
    overdue_tasks.sort(key=lambda x: x['days_overdue'], reverse=True)
    due_this_week_tasks.sort(key=lambda x: x['days_left'])

    return {
        'today': today.isoformat(),
        'today_hebrew': format_date_hebrew(today),
        'overdue_count': len(overdue_tasks),
        'overdue_tasks': overdue_tasks,
        'due_today_count': len(due_today_tasks),
        'due_today_tasks': due_today_tasks,
        'due_this_week_count': len(due_this_week_tasks),
        'due_this_week_tasks': due_this_week_tasks,
        'delayed_count': len(delayed_tasks),
        'delayed_tasks': delayed_tasks,
        'missing_dates_count': len(missing_dates_tasks)
    }

def get_stale_and_suggestions():
    """Finds tasks and projects requiring updates, attention, or cleanup."""
    today = get_current_date()
    tasks = Task.query.filter_by(is_archived=False).all()
    projects = Project.query.filter_by(is_archived=False).all()

    empty_projects = []
    for p in projects:
        active_p_tasks = [t for t in p.tasks if not t.is_archived]
        if not active_p_tasks:
            empty_projects.append({'id': p.id, 'name': p.name, 'teams': [t.name_he for t in p.teams]})

    unassigned_tasks = []
    missing_hours_tasks = []
    stuck_in_progress = []

    for t in tasks:
        # Unassigned
        if not t.members or not t.members.strip():
            unassigned_tasks.append(t.to_dict())

        # Missing hours
        if t.estimated_hours is None or t.estimated_hours <= 0:
            missing_hours_tasks.append(t.to_dict())

        # Stuck in progress without end date or overdue
        if t.status == 'status-inprogress':
            if not t.end_date or t.end_date < today:
                stuck_in_progress.append(t.to_dict())

    return {
        'today': today.isoformat(),
        'empty_projects': empty_projects,
        'unassigned_tasks': unassigned_tasks,
        'missing_hours_count': len(missing_hours_tasks),
        'stuck_in_progress': stuck_in_progress,
        'total_suggestions': len(empty_projects) + len(unassigned_tasks) + len(stuck_in_progress)
    }
