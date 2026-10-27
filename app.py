from flask import Flask, render_template, redirect, url_for, request, jsonify, send_from_directory
from sqlalchemy import case, distinct, or_, and_
from werkzeug.utils import secure_filename
import os
import time
import json
import re
import logging

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads/avatars'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size
# Import models and initialize db
from models import db, Team, TeamMember, Task, SpecialDay, Project, project_teams, member_teams
db.init_app(app)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Route to serve uploaded files
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded files from the uploads directory, falling back to static/avatars or default image if missing"""
    base_dir = os.path.abspath(os.path.dirname(__file__))
    uploads_dir = os.path.join(base_dir, 'uploads')
    target = os.path.abspath(os.path.join(uploads_dir, filename))
    if target.startswith(uploads_dir + os.sep) and os.path.isfile(target):
        return send_from_directory(uploads_dir, filename)
    
    # Check if file exists in static/avatars
    avatar_name = os.path.basename(filename)
    static_avatars_dir = os.path.join(base_dir, 'static', 'avatars')
    static_avatar = os.path.abspath(os.path.join(static_avatars_dir, avatar_name))
    if static_avatar.startswith(static_avatars_dir + os.sep) and os.path.isfile(static_avatar):
        return send_from_directory(static_avatars_dir, avatar_name)

    return send_from_directory(os.path.join(base_dir, 'static', 'images'), 'default.png')


@app.route('/api/avatars', methods=['GET'])
def api_get_predefined_avatars():
    """Returns list of predefined avatar files available in static/avatars"""
    base_dir = os.path.abspath(os.path.dirname(__file__))
    avatar_dir = os.path.join(base_dir, 'static', 'avatars')
    avatars = []
    if os.path.exists(avatar_dir):
        files = [f for f in os.listdir(avatar_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.svg'))]
        def sort_key(name):
            nums = re.findall(r'\d+', name)
            return int(nums[0]) if nums else 999
        files.sort(key=sort_key)
        for f in files:
            avatars.append({
                'id': f,
                'filename': f,
                'url': f'/static/avatars/{f}'
            })
    return jsonify({'success': True, 'avatars': avatars})

from sqlalchemy import event
from sqlalchemy.orm import Session

_last_data_version = time.time()

def _bump_data_version(*args, **kwargs):
    global _last_data_version
    _last_data_version = time.time()

try:
    event.listen(Session, 'after_commit', _bump_data_version)
except Exception as e:
    app.logger.warning(f"Could not attach after_commit listener: {e}")

@app.context_processor
def inject_now():
    from datetime import datetime
    return {'now': datetime.now()}


@app.route('/api/version')
def api_version():
    global _last_data_version
    try:
        # Check database file modification time
        db_path = os.path.join(app.instance_path, 'tasks.db')
        if not os.path.exists(db_path):
             db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'tasks.db')
             
        file_mtime = os.path.getmtime(db_path) if os.path.exists(db_path) else 0
        current_version = max(_last_data_version, file_mtime)
            
        response = jsonify({'timestamp': current_version})
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        return response
    except Exception:
        return jsonify({'timestamp': _last_data_version})

# API endpoint to add a task (AJAX)
@app.route('/api/tasks', methods=['POST'])
def api_add_task():
    data = request.json or {}
    project_id = data.get('project_id')
    project_name = data.get('project')
    
    project_obj = None
    if project_id:
        project_obj = db.session.get(Project, project_id)
    elif project_name and project_name.strip():
        project_obj = Project.query.filter_by(name=project_name.strip()).first()
        
    if not project_obj:
        return jsonify({'success': False, 'error': 'יש לבחור פרויקט קיים'}), 400
        
    project = project_obj.name
    project_id = project_obj.id
        
    task = data.get('task')
    if not task or not task.strip():
        task = "ללא שם"
    members = ','.join(data.get('members', []))
    status = data.get('status')
    priority = data.get('priority', 'none')
    notes = data.get('notes', '')
    team_id = data.get('team_id')
    if not team_id and project_obj.teams:
        team_id = project_obj.teams[0].id
    
    # Calendar fields (v3)
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    estimated_hours = data.get('estimated_hours')
    
    # Parse date strings to date objects if provided
    from datetime import datetime
    if start_date and start_date.strip():
        try:
            start_date = datetime.fromisoformat(start_date).date()
        except (ValueError, AttributeError):
            start_date = None
    else:
        start_date = None
        
    if end_date and end_date.strip():
        try:
            end_date = datetime.fromisoformat(end_date).date()
        except (ValueError, AttributeError):
            end_date = None
    else:
        end_date = None
            
    new_task = Task(
        project_id=project_id,
        project=project, 
        task=task, 
        members=members, 
        status=status, 
        priority=priority, 
        notes=notes, 
        team_id=team_id,
        start_date=start_date,
        end_date=end_date,
        estimated_hours=estimated_hours
    )
    db.session.add(new_task)
    db.session.commit()
    
    return jsonify({'success': True, 'id': new_task.id})

# API endpoint to get or edit a task (AJAX)
@app.route('/api/tasks/<int:id>', methods=['GET', 'PUT'])
def api_edit_task(id):
    task = db.get_or_404(Task, id)
    if request.method == 'GET':
        return jsonify(task.to_dict())
    data = request.json or {}
    
    if 'project_id' in data and data['project_id']:
        project_obj = db.session.get(Project, data['project_id'])
        if project_obj:
            task.project_id = project_obj.id
            task.project = project_obj.name
    elif 'project' in data and data['project']:
        project_obj = Project.query.filter_by(name=data['project'].strip()).first()
        if project_obj:
            task.project_id = project_obj.id
            task.project = project_obj.name
        else:
            task.project = data['project']
            
    task.task = data.get('task', task.task)
    task.members = ','.join(data.get('members', task.members.split(',')))
    task.status = data.get('status', task.status)
    task.priority = data.get('priority', task.priority)
    task.notes = data.get('notes', task.notes)
    task.team_id = data.get('team_id', task.team_id)
    
    # Handle calendar fields (v3)
    from datetime import datetime
    if 'start_date' in data:
        start_date = data.get('start_date')
        if start_date:
            try:
                task.start_date = datetime.fromisoformat(start_date).date()
            except (ValueError, AttributeError):
                pass
        else:
            task.start_date = None
    
    if 'end_date' in data:
        end_date = data.get('end_date')
        if end_date:
            try:
                task.end_date = datetime.fromisoformat(end_date).date()
            except (ValueError, AttributeError):
                pass
        else:
            task.end_date = None
    
    if 'estimated_hours' in data:
        task.estimated_hours = data.get('estimated_hours')

    # Handle archiving
    if 'is_archived' in data:
        task.is_archived = bool(data['is_archived'])
        if not task.is_archived:
            if task.project_id:
                proj = db.session.get(Project, task.project_id)
                if proj and proj.is_archived:
                    proj.is_archived = False
            elif task.project:
                proj = Project.query.filter_by(name=task.project).first()
                if proj and proj.is_archived:
                    proj.is_archived = False
    
    db.session.commit()
    
    return jsonify({'success': True})

# API endpoint to get archived tasks
@app.route('/api/archive')
def api_get_archive():
    tasks = Task.query.filter_by(is_archived=True).order_by(Task.task).all()
    tasks_list = [task.to_dict() for task in tasks]
    return jsonify(tasks_list)

# API endpoint to delete a task (AJAX)
@app.route('/api/tasks/<int:id>', methods=['DELETE'])
def api_delete_task(id):
    task = db.get_or_404(Task, id)
    db.session.delete(task)
    db.session.commit()
    return jsonify({'success': True})


# ============ PROJECT MANAGEMENT API ============

# Get all projects (optionally filtered by team and mode)
@app.route('/api/projects', methods=['GET'])
def api_get_projects():
    team_id = request.args.get('team_id')
    mode = request.args.get('mode', 'active')

    query = Project.query
    if mode == 'archive':
        query = query.filter(Project.is_archived == True)
    elif mode == 'all':
        pass
    else:
        query = query.filter(Project.is_archived == False)

    if team_id and team_id.isdigit():
        team_id = int(team_id)
        projects = query.filter(Project.teams.any(Team.id == team_id)).order_by(Project.name).all()
    else:
        projects = query.order_by(Project.name).all()
    return jsonify([project.to_dict() for project in projects])

# Create a new project
@app.route('/api/projects', methods=['POST'])
def api_create_project():
    data = request.json or {}
    name = data.get('name', '').strip()
    team_ids = data.get('team_ids', [])
    
    if not name:
        return jsonify({'success': False, 'error': 'שם פרויקט הוא שדה חובה'}), 400
    
    existing = Project.query.filter_by(name=name).first()
    if existing:
        return jsonify({'success': False, 'error': 'פרויקט בשם זה כבר קיים'}), 400
        
    if not team_ids:
        return jsonify({'success': False, 'error': 'יש לשייך את הפרויקט לצוות אחד לפחות'}), 400
        
    teams = []
    for tid in team_ids:
        try:
            tid_int = int(tid)
            team = db.session.get(Team, tid_int)
            if team:
                teams.append(team)
        except (ValueError, TypeError):
            continue
            
    project = Project(name=name, teams=teams)
    db.session.add(project)
    db.session.commit()
    
    return jsonify({'success': True, 'project': project.to_dict()})

# Update a project
@app.route('/api/projects/<int:id>', methods=['PUT'])
def api_update_project(id):
    project = db.get_or_404(Project, id)
    data = request.json or {}
    
    old_name = project.name
    new_name = data.get('name', '').strip()
    team_ids = data.get('team_ids')
    
    if new_name and new_name != old_name:
        existing = Project.query.filter_by(name=new_name).first()
        if existing and existing.id != id:
            return jsonify({'success': False, 'error': 'פרויקט בשם זה כבר קיים'}), 400
        project.name = new_name
        for task in project.tasks:
            task.project = new_name
            
    if team_ids is not None:
        teams = []
        for tid in team_ids:
            try:
                tid_int = int(tid)
                team = db.session.get(Team, tid_int)
                if team:
                    teams.append(team)
            except (ValueError, TypeError):
                continue
        project.teams = teams
                
    db.session.commit()
    return jsonify({'success': True, 'project': project.to_dict()})

# Delete a project (and all tasks in it)
@app.route('/api/projects/<int:id>', methods=['DELETE'])
def api_delete_project(id):
    project = db.get_or_404(Project, id)
    # Delete all tasks belonging to this project (both by project_id and project name)
    Task.query.filter((Task.project_id == project.id) | (Task.project == project.name)).delete(synchronize_session='fetch')
    db.session.delete(project)
    db.session.commit()
    return jsonify({'success': True})

# Archive an entire project and its tasks
@app.route('/api/projects/<int:id>/archive', methods=['POST'])
def api_archive_project(id):
    project = db.get_or_404(Project, id)
    project.is_archived = True
    Task.query.filter((Task.project_id == project.id) | (Task.project == project.name)).update({'is_archived': True}, synchronize_session='fetch')
    db.session.commit()
    return jsonify({'success': True, 'project': project.to_dict()})

# Restore an entire project and its tasks from archive
@app.route('/api/projects/<int:id>/unarchive', methods=['POST'])
def api_unarchive_project(id):
    project = db.get_or_404(Project, id)
    project.is_archived = False
    Task.query.filter((Task.project_id == project.id) | (Task.project == project.name)).update({'is_archived': False}, synchronize_session='fetch')
    db.session.commit()
    return jsonify({'success': True, 'project': project.to_dict()})

# Archive a single task
@app.route('/api/tasks/<int:id>/archive', methods=['POST'])
def api_archive_task(id):
    task = db.get_or_404(Task, id)
    task.is_archived = True
    db.session.commit()
    return jsonify({'success': True, 'task': task.to_dict()})

# Restore a single task from archive
@app.route('/api/tasks/<int:id>/unarchive', methods=['POST'])
def api_unarchive_task(id):
    task = db.get_or_404(Task, id)
    task.is_archived = False
    if task.project_id:
        proj = db.session.get(Project, task.project_id)
        if proj and proj.is_archived:
            proj.is_archived = False
    elif task.project:
        proj = Project.query.filter_by(name=task.project).first()
        if proj and proj.is_archived:
            proj.is_archived = False
    db.session.commit()
    return jsonify({'success': True, 'task': task.to_dict()})


# ============ TEAM MANAGEMENT API ============

# Get all teams with their members
@app.route('/api/teams', methods=['GET'])
def api_get_teams():
    teams = Team.query.all()
    return jsonify([team.to_dict() for team in teams])

# Create a new team
@app.route('/api/teams', methods=['POST'])
def api_create_team():
    data = request.json
    name_en = data.get('name_en', '').strip().lower()
    name_he = data.get('name_he', '').strip()
    
    if not name_en or not name_he:
        return jsonify({'success': False, 'error': 'Both English and Hebrew names are required'}), 400
    
    # Check if team already exists
    existing = Team.query.filter_by(name_en=name_en).first()
    if existing:
        return jsonify({'success': False, 'error': 'Team with this English name already exists'}), 400
    
    team = Team(name_en=name_en, name_he=name_he)
    db.session.add(team)
    db.session.commit()
    
    return jsonify({'success': True, 'team': team.to_dict()})

# Update a team
@app.route('/api/teams/<int:id>', methods=['PUT'])
def api_update_team(id):
    team = db.get_or_404(Team, id)
    data = request.json
    
    if 'name_en' in data:
        team.name_en = data['name_en'].strip().lower()
    if 'name_he' in data:
        team.name_he = data['name_he'].strip()
    
    db.session.commit()
    
    return jsonify({'success': True, 'team': team.to_dict()})

# Delete a team
@app.route('/api/teams/<int:id>', methods=['DELETE'])
def api_delete_team(id):
    team = db.get_or_404(Team, id)
    db.session.delete(team)
    db.session.commit()
    
    return jsonify({'success': True})


# ============ TEAM MEMBER API ============

# Get members of a specific team
@app.route('/api/teams/<int:team_id>/members', methods=['GET'])
def api_get_team_members(team_id):
    team = db.get_or_404(Team, team_id)
    return jsonify([member.to_dict() for member in team.members])

# Get all members (across all teams)
@app.route('/api/members', methods=['GET'])
def api_get_all_members():
    members = TeamMember.query.order_by(TeamMember.name_he).all()
    return jsonify([member.to_dict() for member in members])

# Add a member globally or to teams
@app.route('/api/members', methods=['POST'])
def api_add_member():
    data = request.json or {}
    name_en = data.get('name_en', '').strip().lower()
    name_he = data.get('name_he', '').strip()
    avatar_path = data.get('avatar_path', 'default.png')
    team_ids = data.get('team_ids')
    if team_ids is None and data.get('team_id'):
        team_ids = [data.get('team_id')]
    elif team_ids is None:
        team_ids = []
    
    if not name_en or not name_he:
        return jsonify({'success': False, 'error': 'Both English and Hebrew names are required'}), 400
    
    member = TeamMember(
        team_id=team_ids[0] if team_ids else None,
        name_en=name_en,
        name_he=name_he,
        avatar_path=avatar_path
    )
    for tid in team_ids:
        t = db.session.get(Team, tid)
        if t and t not in member.teams:
            member.teams.append(t)
            
    db.session.add(member)
    db.session.commit()
    return jsonify({'success': True, 'member': member.to_dict()})

# Add a member to a team (card support)
@app.route('/api/teams/<int:team_id>/members', methods=['POST'])
def api_add_team_member(team_id):
    team = db.get_or_404(Team, team_id)
    data = request.json or {}
    
    name_en = data.get('name_en', '').strip().lower()
    name_he = data.get('name_he', '').strip()
    avatar_path = data.get('avatar_path', 'default.png')
    team_ids = data.get('team_ids')
    
    if not name_en or not name_he:
        return jsonify({'success': False, 'error': 'Both English and Hebrew names are required'}), 400
    
    member = TeamMember(
        team_id=team_id,
        name_en=name_en,
        name_he=name_he,
        avatar_path=avatar_path
    )
    if team_ids is not None:
        target_tids = set(team_ids)
        target_tids.add(team_id)
        for tid in target_tids:
            t = db.session.get(Team, tid)
            if t and t not in member.teams:
                member.teams.append(t)
    else:
        member.teams.append(team)

    db.session.add(member)
    db.session.commit()
    
    return jsonify({'success': True, 'member': member.to_dict()})

# Update a team member globally
@app.route('/api/members/<int:member_id>', methods=['PUT'])
def api_update_member(member_id):
    member = db.get_or_404(TeamMember, member_id)
    data = request.json or {}
    
    if 'name_en' in data:
        member.name_en = data['name_en'].strip().lower()
    if 'name_he' in data:
        member.name_he = data['name_he'].strip()
    if 'avatar_path' in data:
        member.avatar_path = data['avatar_path']
    if 'team_ids' in data:
        team_ids = data['team_ids']
        new_teams = []
        for tid in team_ids:
            t = db.session.get(Team, tid)
            if t:
                new_teams.append(t)
        member.teams = new_teams
        member.team_id = new_teams[0].id if new_teams else None
    
    db.session.commit()
    return jsonify({'success': True, 'member': member.to_dict()})

# Update a team member from team route
@app.route('/api/teams/<int:team_id>/members/<int:member_id>', methods=['PUT'])
def api_update_team_member(team_id, member_id):
    return api_update_member(member_id)

# Delete a member globally
@app.route('/api/members/<int:member_id>', methods=['DELETE'])
def api_delete_member(member_id):
    member = db.get_or_404(TeamMember, member_id)
    db.session.delete(member)
    db.session.commit()
    return jsonify({'success': True})

# Delete a team member from a specific team
@app.route('/api/teams/<int:team_id>/members/<int:member_id>', methods=['DELETE'])
def api_delete_team_member(team_id, member_id):
    member = db.get_or_404(TeamMember, member_id)
    team = db.get_or_404(Team, team_id)
    if team in member.teams:
        member.teams.remove(team)
    if len(member.teams) == 0:
        db.session.delete(member)
    else:
        member.team_id = member.teams[0].id
    db.session.commit()
    return jsonify({'success': True})

# Upload avatar for a member
@app.route('/api/members/<int:member_id>/avatar', methods=['POST'])
@app.route('/api/teams/<int:team_id>/members/<int:member_id>/avatar', methods=['POST'])
def api_upload_avatar(member_id, team_id=None):
    member = db.get_or_404(TeamMember, member_id)
    
    if 'avatar' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['avatar']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        return jsonify({'success': False, 'error': 'Invalid file type. Allowed: png, jpg, jpeg, gif'}), 400
    
    safe_name = secure_filename(member.name_en) or f"member_{member.id}"
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{safe_name}.{ext}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    member.avatar_path = filename
    db.session.commit()
    
    return jsonify({'success': True, 'avatar_path': filename})



# ============ SEARCH API ============

@app.route('/api/search', methods=['GET'])
def api_search():
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify([])
    
    # Search in task name, project, notes, and members
    search_pattern = f'%{query}%'
    tasks = Task.query.filter(
        or_(
            Task.task.like(search_pattern),
            Task.project.like(search_pattern),
            Task.notes.like(search_pattern),
            Task.members.like(search_pattern)
        )
    ).all()
    
    return jsonify([task.to_dict() for task in tasks])



# ============ CALENDAR API (v3) ============

def _apply_calendar_team_filter(query, team_id):
    """Helper to filter calendar queries by archive or team_id + team members."""
    if team_id == 'archive':
        return query.filter(Task.is_archived == True)
    query = query.filter(Task.is_archived == False)
    if team_id and str(team_id).isdigit():
        tid = int(team_id)
        team = db.session.get(Team, tid)
        if team:
            member_names = [m.name_en for m in team.members if m.name_en]
            if member_names:
                member_filters = [Task.members.contains(name) for name in member_names]
                return query.filter(or_(Task.team_id == tid, *member_filters))
        return query.filter(Task.team_id == tid)
    return query


@app.route('/api/calendar/week', methods=['GET'])
def api_calendar_week():
    """Get tasks for a specific week"""
    from datetime import datetime, timedelta
    
    # Support both start_date/end_date and date parameters
    date_str = request.args.get('date') or request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    team_id = request.args.get('team_id')
    
    if date_str:
        try:
            reference_date = datetime.fromisoformat(date_str).date()
        except ValueError:
            reference_date = datetime.now().date()
    else:
        reference_date = datetime.now().date()
    
    # Calculate week start (Sunday) and end (Saturday)
    days_since_sunday = (reference_date.weekday() + 1) % 7
    week_start = reference_date - timedelta(days=days_since_sunday)
    if end_date_str:
        try:
            week_end = datetime.fromisoformat(end_date_str).date()
        except ValueError:
            week_end = week_start + timedelta(days=6)
    else:
        week_end = week_start + timedelta(days=6)
    
    # Query tasks that fall within this week
    query = Task.query.filter(
        or_(
            Task.start_date.between(week_start, week_end),
            Task.end_date.between(week_start, week_end),
            and_(Task.start_date <= week_start, Task.end_date >= week_end)
        )
    )
    
    query = _apply_calendar_team_filter(query, team_id)
    tasks = query.all()
    
    return jsonify({
        'week_start': week_start.isoformat(),
        'week_end': week_end.isoformat(),
        'tasks': [task.to_dict() for task in tasks]
    })


@app.route('/api/calendar/month', methods=['GET'])
def api_calendar_month():
    """Get tasks for a specific month"""
    from datetime import datetime
    from calendar import monthrange
    
    # Get month/year parameters (defaults to current month)
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    team_id = request.args.get('team_id')
    
    now = datetime.now()
    if not year:
        year = now.year
    if not month or not (1 <= month <= 12):
        month = now.month
    
    # Calculate month boundaries
    month_start = datetime(year, month, 1).date()
    last_day = monthrange(year, month)[1]
    month_end = datetime(year, month, last_day).date()
    
    # Query tasks that fall within this month
    query = Task.query.filter(
        or_(
            Task.start_date.between(month_start, month_end),
            Task.end_date.between(month_start, month_end),
            and_(Task.start_date <= month_start, Task.end_date >= month_end)
        )
    )
    
    query = _apply_calendar_team_filter(query, team_id)
    tasks = query.all()
    
    return jsonify({
        'month': month,
        'year': year,
        'month_start': month_start.isoformat(),
        'month_end': month_end.isoformat(),
        'tasks': [task.to_dict() for task in tasks]
    })


@app.route('/api/calendar/workload', methods=['GET'])
def api_calendar_workload():
    """Get member workload data for a date range"""
    from datetime import datetime, timedelta
    
    # Get date range parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    team_id = request.args.get('team_id')
    
    # Default to current week if not specified
    if not start_date_str or not end_date_str:
        today = datetime.now().date()
        days_since_sunday = (today.weekday() + 1) % 7
        start_date = today - timedelta(days=days_since_sunday)
        end_date = start_date + timedelta(days=6)
    else:
        try:
            start_date = datetime.fromisoformat(start_date_str).date()
            end_date = datetime.fromisoformat(end_date_str).date()
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
    
    # 1. Base Task Query (Date Range)
    query = Task.query.filter(
        or_(
            Task.start_date.between(start_date, end_date),
            Task.end_date.between(start_date, end_date),
            and_(Task.start_date <= start_date, Task.end_date >= end_date)
        )
    )
    
    members = []
    
    if team_id == 'archive':
        query = query.filter(Task.is_archived == True)
        tasks = query.all()
        members = TeamMember.query.all()
        
    elif team_id and str(team_id).isdigit():
        tid = int(team_id)
        query = query.filter(Task.is_archived == False)
        
        # Get Core Members of the team via M2M relationship (falling back to team_id)
        team_obj = db.session.get(Team, tid)
        core_members = list(team_obj.members) if team_obj and team_obj.members else TeamMember.query.filter_by(team_id=tid).all()
        core_names = [m.name_en for m in core_members if m.name_en]
        
        if core_names:
            # Filter tasks: Assigned to Team OR Assigned to any Core Member
            member_filters = [Task.members.contains(name) for name in core_names]
            query = query.filter(or_(Task.team_id == tid, *member_filters))
        else:
            query = query.filter(Task.team_id == tid)
             
        tasks = query.all()
        
        # Get all members involved in these tasks + core members
        relevant_names = set(n.lower() for n in core_names)
        for task in tasks:
            if task.members:
                relevant_names.update([n.strip().lower() for n in task.members.split(',') if n.strip()])
        
        if relevant_names:
            members = [m for m in TeamMember.query.all() if m.name_en and m.name_en.strip().lower() in relevant_names]
        else:
            members = core_members
            
    else:
        # No Filter
        query = query.filter(Task.is_archived == False)
        tasks = query.all()
        members = TeamMember.query.all()
    
    # Build workload data structure
    workload_data = []
    for member in members:
        m_en = (member.name_en or '').strip().lower()
        member_tasks = [
            task.to_dict() for task in tasks 
            if m_en and m_en in [n.strip().lower() for n in (task.members or '').split(',') if n.strip()]
        ]
        workload_data.append({
            'member': member.to_dict(),
            'tasks': member_tasks
        })
    
    return jsonify({
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'workload': workload_data
    })


@app.route('/api/tasks/<int:id>/schedule', methods=['PUT'])
def api_update_task_schedule(id):
    """Update task scheduling information (dates and estimated hours)"""
    from datetime import datetime
    
    task = db.get_or_404(Task, id)
    data = request.json or {}
    old_start = task.start_date
    old_end = task.end_date
    
    # Update start_date
    if 'start_date' in data:
        start_date = data.get('start_date')
        if start_date:
            try:
                task.start_date = datetime.fromisoformat(start_date).date()
            except (ValueError, AttributeError):
                return jsonify({'success': False, 'error': 'Invalid start_date format'}), 400
        else:
            task.start_date = None
    
    # Update end_date
    if 'end_date' in data:
        end_date = data.get('end_date')
        if end_date:
            try:
                task.end_date = datetime.fromisoformat(end_date).date()
            except (ValueError, AttributeError):
                return jsonify({'success': False, 'error': 'Invalid end_date format'}), 400
        else:
            task.end_date = None
    elif 'start_date' in data and task.start_date and old_end:
        # When moving start_date without specifying end_date (e.g. calendar drag & drop),
        # preserve duration if old_start existed, or ensure end_date >= start_date
        if old_start:
            delta = task.start_date - old_start
            task.end_date = old_end + delta
        elif task.start_date > old_end:
            task.end_date = task.start_date
    
    # Update estimated_hours
    if 'estimated_hours' in data:
        task.estimated_hours = data.get('estimated_hours')
    
    db.session.commit()
    
    return jsonify({'success': True, 'task': task.to_dict()})



# ============ SPECIAL DAYS API ============

@app.route('/api/special-days', methods=['GET'])
def api_get_special_days():
    from datetime import datetime
    
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    query = SpecialDay.query
    
    if start_date_str and end_date_str:
        try:
            start_date = datetime.fromisoformat(start_date_str).date()
            end_date = datetime.fromisoformat(end_date_str).date()
            query = query.filter(SpecialDay.date.between(start_date, end_date))
        except ValueError:
            pass
            
    special_days = query.order_by(SpecialDay.date).all()
    return jsonify([day.to_dict() for day in special_days])

@app.route('/api/special-days', methods=['POST'])
def api_create_special_day():
    data = request.json
    from datetime import datetime
    
    try:
        date_obj = datetime.fromisoformat(data['date']).date()
    except (ValueError, KeyError):
        return jsonify({'success': False, 'error': 'Invalid date'}), 400
        
    name = data.get('name')
    if not name:
        return jsonify({'success': False, 'error': 'Name is required'}), 400
        
    special_day = SpecialDay(
        date=date_obj,
        name=name,
        type=data.get('type', 'holiday'),
        color=data.get('color')
    )
    
    db.session.add(special_day)
    db.session.commit()
    
    return jsonify({'success': True, 'special_day': special_day.to_dict()})

@app.route('/api/special-days/<int:id>', methods=['DELETE'])
def api_delete_special_day(id):
    day = db.get_or_404(SpecialDay, id)
    db.session.delete(day)
    db.session.commit()
    return jsonify({'success': True})


# Initialize database tables and migrations
def init_db():
    with app.app_context():
        db.create_all()
        # Ensure project_id column exists on task table in SQLite
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('task')]
        if 'project_id' not in columns:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE task ADD COLUMN project_id INTEGER REFERENCES project(id)"))
                conn.commit()

        # Ensure is_archived column exists on project table in SQLite
        columns_project = [col['name'] for col in inspector.get_columns('project')]
        if 'is_archived' not in columns_project:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE project ADD COLUMN is_archived BOOLEAN DEFAULT 0"))
                conn.commit()

        # Migrate existing team_member.team_id to member_teams table
        all_members = TeamMember.query.all()
        for m in all_members:
            if m.team_id and not m.teams:
                t = db.session.get(Team, m.team_id)
                if t and t not in m.teams:
                    m.teams.append(t)
        db.session.commit()

        # Migrate existing distinct projects to Project model
        distinct_projects = db.session.query(Task.project).distinct().all()
        for (p_name,) in distinct_projects:
            if not p_name or not p_name.strip():
                continue
            p_name = p_name.strip()
            proj = Project.query.filter_by(name=p_name).first()
            if not proj:
                proj = Project(name=p_name)
                db.session.add(proj)
                db.session.flush()
            # Link project teams based on existing tasks
            tasks_in_project = Task.query.filter_by(project=p_name).all()
            team_ids = set(t.team_id for t in tasks_in_project if t.team_id)
            for tid in team_ids:
                team = db.session.get(Team, tid)
                if team and team not in proj.teams:
                    proj.teams.append(team)
            if not proj.teams:
                first_team = Team.query.first()
                if first_team:
                    proj.teams.append(first_team)
            for t in tasks_in_project:
                if not t.project_id:
                    t.project_id = proj.id
        db.session.commit()

init_db()


# ============ AI ASSISTANT API ============

from ai_service import ai_service
from ai_context import build_system_context, get_executive_summary, get_deadlines_analysis, get_stale_and_suggestions
from ai_tools import (
    extract_json_actions, execute_actions, detect_fallback_action,
    filter_hallucinated_actions, format_task_status_summary, is_task_status_query,
    sanitize_ai_reply, find_target_task_in_context,
    is_user_requesting_mutation, is_user_requesting_creation,
    get_team_tasks_query_info, format_team_tasks_summary,
    get_member_tasks_query_info, format_member_tasks_summary
)

def _generate_ai_system_prompt():
    ctx = build_system_context()
    
    # Teams summary - Hebrew names only, zero technical IDs
    teams_summary = []
    for t in ctx['teams']:
        m_list = [m['name_he'] for m in t['members']]
        teams_summary.append(f"צוות '{t['name_he']}' - חברים: {', '.join(m_list) if m_list else 'ללא'}")
    
    # Projects summary - clean summary without technical IDs
    projects_summary = []
    for p in ctx['projects']:
        t_names = [t['name_he'] for t in p['teams']]
        projects_summary.append(f"פרויקט '{p['name']}' (צוותים: {', '.join(t_names) if t_names else 'ללא'}, משימות פתוחות: {p['task_count']})")

    status_map_he = {
        'status-inprogress': 'בתהליך',
        'status-done': 'הושלם',
        'status-delayed': 'מעוכב',
        'status-notstarted': 'טרם החל'
    }
    priority_map_he = {
        'high': 'גבוהה',
        'medium': 'בינונית',
        'low': 'נמוכה',
        'none': 'ללא'
    }

    # Tasks summary (up to 120 active tasks)
    tasks_summary = []
    for t in ctx['tasks'][:120]:
        m_he = [ctx['members_lookup'].get(m.lower().strip(), m) for m in t['members']]
        members_str = ', '.join(m_he) if m_he else 'ללא משויך'
        st_he = status_map_he.get(t['status'], t['status'])
        prio_he = priority_map_he.get(t['priority'], t['priority'])
        dates_str = []
        if t['start_date']: dates_str.append(f"התחלה: {t['start_date']}")
        if t['end_date']: dates_str.append(f"יעד: {t['end_date']}")
        dates_desc = f" (תאריכים: {', '.join(dates_str)})" if dates_str else ""
        hours_desc = f" [{t['estimated_hours']} שעות]" if t.get('estimated_hours') else ""
        notes_desc = f" [הערות: {t['notes']}]" if t.get('notes') else ""
        tasks_summary.append(f"#{t['id']}: [{t['project']}] {t['task']} | סטטוס: {st_he} (קוד מערכת: {t['status']}) | עדיפות: {prio_he} | משויך: {members_str}{dates_desc}{hours_desc}{notes_desc}")

    # Archived tasks summary (up to 30 recent archived tasks)
    archived_summary = []
    for t in ctx.get('archived_tasks', [])[:30]:
        m_he = [ctx['members_lookup'].get(m.lower().strip(), m) for m in t['members']]
        members_str = ', '.join(m_he) if m_he else 'ללא משויך'
        st_he = status_map_he.get(t['status'], t['status'])
        archived_summary.append(f"#{t['id']}: [{t['project']}] {t['task']} | סטטוס: בארכיון (היה: {st_he}) | משויך: {members_str}")

    prompt = f"""אתה עוזר AI מקצועי, אינטליגנטי וידידותי של מערכת TeamTasks לניהול פרויקטים ומשימות.
תאריך היום הנוכחי במערכת: {ctx['today_hebrew']} ({ctx['today']}).

תפקידך המרכזי:
1. לספק סיכומים מנהליים, תמונת מצב שוטפת וניתוח עומסי עבודה של צוותים ופרויקטים.
2. לנתר דדליינים: להתריע על משימות באיחור (overdue), משימות שמתקרבות לדדליין בשבוע הקרוב, ומשימות חסרות תאריכים.
3. להציע שיפורים ועדכונים למשימות ולפרויקטים שאינם מעודכנים (משימות ללא משויכים, משימות תקועות בתהליך, פרויקטים ריקים).
4. לאפשר למשתמש לנהל את המערכת בצורה מלאה בטקסט חופשי (בעברית או באנגלית): הוספה, עריכה, מחיקה וארכוב של משימות, פרויקטים, צוותים, חברי צוות וימים מיוחדים.

מידע עדכני על המערכת:
---
צוותים וחברים:
{chr(10).join(teams_summary)}

פרויקטים:
{chr(10).join(projects_summary)}

משימות פעילות ({len(ctx['tasks'])} סה"כ):
{chr(10).join(tasks_summary)}

משימות בארכיון ({len(ctx.get('archived_tasks', []))} מוצגות):
{chr(10).join(archived_summary) if archived_summary else 'אין משימות בארכיון'}
---

כללי ברזל לתקשורת עם המשתמש (חובה עליונה):
1. **איסור מוחלט על אזכור בלוק JSON או המילה JSON!**
   - המשתמש הוא אדם ולא מתכנת. הוא אינו מכיר ואינו אמור לדעת מה זה JSON.
   - לעולם אל תכתוב בתשובתך למשתמש את הביטויים: "בלוק JSON", "בלוק json", "קוד JSON", "פקודת JSON", "מבנה JSON", או המילה "JSON" כלל!
   - לעולם אל תכתוב פתיחים כגון: "להלן בלוק ה-JSON", "הנה ה-JSON", "לפי המבנה התקני של בלוק JSON", "פלוט בלוק JSON" וכו'.
   - בלוק ה-JSON (```json ... ```) הוא פקודה פנימית שקטה בלבד שהשרת קורא מאחורי הקלעים כדי לעדכן את בסיס הנתונים.
   - בתשובתך הגלויה למשתמש, כתוב אך ורק משפט אנושי טבעי וידידותי (למשל: "עדכנתי את משימת שדרוג מתגים לסטטוס בתהליך.") או אל תוסיף טקסט מיותר אם אין צורך.

2. **מענה על שאלות מידע, בירור, רשימות או סטטוס משימות (למשל: "מה המשימות של...", "איזה משימות יש ל...", "מה הסטטוס של...", "מה המצב של...", "מי עובד על...", "תסכם לי את...", "פרטי משימה..."):**
   - **איסור מוחלט על פליטת בלוק JSON או ביצוע פעולות בשאלות מידע!**
   - שאלות אלו הן לקריאה בלבד (Read-Only). חל איסור מוחלט לעדכן, לשנות, לסמן או למחוק שום משימה או פרויקט בעת מענה על שאלת מידע!
   - הצג תמיד סיכום מפורט, מסודר ומאורגן היטב בעברית ברורה בלבד:
     - עבור שאלת סטטוס על משימה ספציפית:
       **פרטי משימה #[מספר]: [שם המשימה]**
       • פרויקט: [שם הפרויקט]
       • סטטוס: [בעברית בלבד: "בתהליך" / "הושלם" / "מעוכב" / "טרם החל" / "בארכיון"]
       • עדיפות: [בעברית בלבד: "גבוהה" / "בינונית" / "נמוכה" / "ללא"]
       • אחראי / משויך: [שמות חברי הצוות בעברית בלבד! למשל: "אלעד, אלי". אם אין, כתוב "ללא משויך"]
       • תאריכים: [התחלה ויעד אם קיימים בפורמט DD/MM/YYYY]
       • שעות משוערות: [אם קיימות]
       • הערות: [אם קיימות]
     - עבור שאלות על משימות של חבר צוות או פרויקט (למשל: "מה המשימות של אלירן"): הצג רשימה ממוספרת או עם תבליטים בעברית בלבד עם שם המשימה, הפרויקט, הסטטוס והעדיפות (ללא בלוק JSON!).
     - עבור שאלות על משימות פתוחות של חבר צוות או צוות (למשל: "כמה משימות פתוחות יש לנועם", "איזה משימות פתוחות יש לצוות DEVOPS"):
       * "משימות פתוחות" הן אך ורק משימות בסטטוס: "בתהליך" (status-inprogress), "טרם החל" (status-notstarted), או "מעוכב" (status-delayed)!
       * חל איסור מוחלט להחזיר או לספור משימות שהושלמו ("status-done") כאשר המשתמש שואל על משימות פתוחות!
       * אם כל המשימות של חבר צוות או צוות כבר הושלמו (כמו נועם שכל משימותיו הושלמו), התשובה הנכונה היא שאין לו משימות פתוחות כרגע (0 משימות פתוחות).
   - **איסור מוחלט על כפילות מספר משימה (ID):** מספר המשימה (#ID) נכתב כבר בכותרת בלבד (למשל: פרטי משימה #77)! חל איסור מוחלט להוסיף שורה '• ID: #...' או '• מזהה: #...'. אל תחזור על ה-ID בגוף הפרטים!
   - **איסור מוחלט על עדיפות באנגלית:** חל איסור מוחלט לכתוב 'low', 'medium', 'high', 'urgent', 'none'! כתוב תמיד אך ורק בעברית: 'נמוכה', 'בינונית', 'גבוהה', 'דחופה', 'ללא'.
   - **איסור מוחלט על קודי סטטוס באנגלית:** לעולם אל תציג למשתמש קודים כגון "status-inprogress", "status-done", "status-delayed", "status-notstarted"! תמיד הצג את המונח העברי ("בתהליך", "הושלם", "מעוכב", "טרם החל").
   - **איסור מוחלט על מספרי ID של משתמשים/חברי צוות:** לעולם אל תציג מספרי ID של משתמשים (כמו ID: 1, User ID וכו'). הצג תמיד אך ורק את השם העברי המלא של חבר הצוות!

3. **ביצוע פעולות במערכת (Action Execution Rules):**
   - **בצע פעולות (בלוק JSON) אך ורק כאשר המשתמש מבקש במפורש לבצע פעולה!** (למשל: "תסמן אותה הושלמה", "סמן כהושלם", "סמן כבוצע", "סיימתי אותה", "סגור אותה", "תשנה ל...", "תעדכן את...", "תמחק את...", "תעביר לארכיון", "תוסיף משימה...").
   - **פניות בלשון נקבה, זכר או ציווי:** המשתמש עשוי לפנות אליך בלשון נקבה (למשל: "תשני את המשימה 82 בתהליך", "שני את משימה 82 לבתהליך", "תעדכני את משימה 82 לבתהליך", "עדכני", "תסמני", "סמני", "תמחקי", "מחקי", "תוסיפי", "צרי", "תפתחי") בדיוק כמו בלשון זכר ("תשנה", "שנה", "סמן", "עדכן"). חובה להתייחס לכל הפניות הללו כהוראות לביצוע פעולה ולפלוט מיד בלוק JSON שקט מתאים!
   - **אזהרה חמורה - איסור מענה יבש במקום פעולה:** כאשר המשתמש מבקש לסמן או לעדכן משימה (כגון "תסמן אותה הושלמה" או "תשני את המשימה 82 בתהליך"), אסור לענות רק בטקסט המשחזר את פרטי המשימה עם הסטטוס החדש! ללא בלוק ה-JSON המערכת לא תבצע דבר והמשתמש יקבל שגיאה!
   - חובה להשתמש ב-ID האמיתי של המשימה מתוך הרשימה למעלה או מהמשימה שדובר עליה בהקשר השיחה!
   - פלוט לכל היותר בלוק JSON אחד בלבד לכל הודעה.
   - ערכי קוד מערכת עבור סטטוס בתוך ה-JSON בלבד:
     - "status-inprogress" (עבור בתהליך / in progress)
     - "status-done" (עבור הושלם / done / הושלמה / בוצע)
     - "status-delayed" (עבור מעוכב / delayed)
     - "status-notstarted" (עבור טרם החל / not started)

דוגמה 1 - שאלת מידע (חובה: טקסט בלבד, איסור מוחלט על בלוק JSON ואיסור על עדכון נתונים!):
משתמש: "מה המשימות של אלירן?"
תשובתך (טקסט בלבד, ללא בלוק JSON!):
"להלן המשימות הפעילות של אלירן:
• #34 [שדרוג ליבה]: בדיקת יתירות (סטטוס: בתהליך, עדיפות: גבוהה)
• #35 [שדרוג ליבה]: הגדרת NAC (סטטוס: הושלם, עדיפות: בינונית)"

דוגמה 2 - בקשה מפורשת לשינוי/סימון (חובה: בלוק JSON שקט):
משתמש: "תסמן אותה הושלמה" (או: "סמן כהושלם", "היא הושלמה", "סגור אותה")
תשובתך חייבת להכיל את הבלוק הבא:
```json
{{
  "actions": [
    {{
      "action": "edit_task",
      "params": {{
        "id": <TASK_ID>,
        "status": "status-done"
      }}
    }}
  ]
}}
```

דוגמה 3 - הוספת חבר צוות חדש (חובה: בלוק JSON שקט):
משתמש: "תוסיף חבר צוות חדש בשם 'דניאל' (daniel) לצוות דבאופס"
תשובתך חייבת להכיל:
```json
{{
  "actions": [
    {{
      "action": "create_member",
      "params": {{
        "name_he": "דניאל",
        "name_en": "daniel",
        "team": "דבאופס"
      }}
    }}
  ]
}}
```

דוגמה 4 - הוספת חבר למשימה או דחיית משימה (חובה: בלוק JSON שקט):
משתמש: "תוסיף את גיא למשימה בדיקת ביצועים"
תשובתך חייבת להכיל:
```json
{{
  "actions": [
    {{
      "action": "edit_task",
      "params": {{
        "id": <TASK_ID>,
        "add_members": ["גיא"]
      }}
    }}
  ]
}}
```

משתמש: "תדחה את המשימה בדיקת גיבויים ב-AWS לתאריך 28/10/2026"
תשובתך חייבת להכיל:
```json
{{
  "actions": [
    {{
      "action": "edit_task",
      "params": {{
        "id": <TASK_ID>,
        "end_date": "2026-10-28"
      }}
    }}
  ]
}}
```

דוגמה 5 - פנייה בלשון נקבה לעדכון סטטוס משימה:
משתמש: "תשני את המשימה 82 בתהליך" (או: "שני את משימה 82 לבתהליך", "תעדכני את משימה 82 לבתהליך")
תשובתך חייבת להכיל:
```json
{{
  "actions": [
    {{
      "action": "edit_task",
      "params": {{
        "id": 82,
        "status": "status-inprogress"
      }}
    }}
  ]
}}
```

רשימת הפעולות הנתמכות:
- create_task: הוספת משימה חדשה (params: project, task, members, status, priority, start_date, end_date, estimated_hours, notes)
- edit_task: עריכת משימה קיימת (params: id, status, task, project, priority, members, start_date, end_date, estimated_hours, notes)
- delete_task: מחיקת משימה (params: {{"id": <REAL_TASK_ID>}})
- archive_task: העברת משימה לארכיון (params: {{"id": <REAL_TASK_ID>}})
- unarchive_task: שחזור משימה מהארכיון (params: {{"id": <REAL_TASK_ID>}})
- create_project: יצירת פרויקט (params: {{"name": "שם הפרויקט", "teams": ["פיתוח"]}})
- edit_project: עריכת פרויקט (params: {{"name": "שם הפרויקט", "new_name": "שם חדש"}})
- delete_project: מחיקת פרויקט (params: {{"name": "שם הפרויקט"}})
- archive_project: העברת פרויקט לארכיון (params: {{"name": "שם הפרויקט"}})
- unarchive_project: שחזור פרויקט מהארכיון (params: {{"name": "שם הפרויקט"}})
- create_team: יצירת צוות (params: {{"name_he": "תשתיות", "name_en": "infra"}})
- edit_team: עריכת צוות (params: {{"id": <TEAM_ID>, "name_he": "...", "name_en": "..."}})
- delete_team: מחיקת צוות (params: {{"id": <TEAM_ID>}})
- create_member: הוספת חבר צוות (params: {{"name_he": "יוסי", "name_en": "yossi", "team": "פיתוח"}})
- delete_member: מחיקת חבר צוות (params: {{"id": <MEMBER_ID>}})
- create_special_day: יצירת חג/יום מיוחד (params: {{"date": "YYYY-MM-DD", "name": "חג", "type": "holiday"}})
- delete_special_day: מחיקת יום מיוחד (params: {{"id": <DAY_ID>}})
"""
    return prompt


@app.route('/api/ai/status', methods=['GET'])
def api_ai_status():
    """Returns AI service status and active provider."""
    try:
        status = ai_service.get_status()
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ai/chat', methods=['POST'])
def api_ai_chat():
    """Chat with AI Assistant and execute free text actions."""
    data = request.json or {}
    user_msg = data.get('message', '').strip()
    history = data.get('history', [])

    if not user_msg:
        return jsonify({'success': False, 'error': 'הודעה ריקה'}), 400

    try:
        logger.info(f"[AI Chat] Received query: '{user_msg}'")
        system_prompt = _generate_ai_system_prompt()
        ctx = build_system_context()
        
        # Build message chain for AI without duplicate trailing user_msg
        clean_history = history[:-1] if (history and history[-1].get('content', '').strip() == user_msg) else history
        messages = []
        # Keep last 6 history messages for conversation context
        for h in clean_history[-6:]:
            role = h.get('role', 'user')
            content = h.get('content', '')
            if role in ['user', 'assistant'] and content:
                # Remove large json action blocks from history context to preserve token window
                clean_content = re.sub(r'```(?:json)?\s*\{[\s\S]*?\}\s*```', '', content).strip()
                if clean_content:
                    messages.append({'role': role, 'content': clean_content})

        messages.append({'role': 'user', 'content': user_msg})

        # Call AI
        ai_reply = ai_service.chat(messages, system_prompt=system_prompt)
        ai_reply_str = json.dumps(ai_reply, ensure_ascii=False) if isinstance(ai_reply, (dict, list)) else str(ai_reply)
        logger.info(f"[AI Chat] AI reply: {ai_reply_str[:300]}")

        # Extract and execute actions
        actions = extract_json_actions(ai_reply)

        # Fallback intent detection if AI didn't emit a valid JSON action block
        if not actions:
            fallback = detect_fallback_action(user_msg, ai_reply_str, history=messages)
            if fallback:
                logger.info(f"[AI Chat] Fallback action detected and applied: {fallback}")
                actions = fallback

        # Filter out hallucinated actions (e.g. model arbitrarily picked a task the user never asked for)
        had_actions_before_filter = bool(actions)
        actions = filter_hallucinated_actions(actions, user_msg, history=clean_history)
        dropped_hallucinated = had_actions_before_filter and not actions

        executed_actions = []
        refresh_needed = False

        if actions:
            executed_actions, refresh_needed = execute_actions(actions)
            logger.info(f"[AI Chat] Executed actions: {executed_actions}, refresh_needed={refresh_needed}")

        mutating_successes = [
            a for a in executed_actions
            if a.get('status') == 'success' and a.get('action') not in ['list_tasks', 'list_projects', 'search_tasks', 'get_tasks']
        ]

        # Use our strict sanitizer to clean the response
        clean_reply = sanitize_ai_reply(ai_reply_str, mutating_successes=mutating_successes, members_lookup=ctx.get('members_lookup'))

        # Check if user had action intent
        user_has_action_intent = is_user_requesting_mutation(user_msg) or is_user_requesting_creation(user_msg)

        # If model hallucinated an action on an unreferenced task and it was dropped:
        if dropped_hallucinated and user_has_action_intent:
            clean_reply = "באיזו משימה מדובר? לא ציינת איזו משימה תרצה לעדכן או למחוק. אנא ציין את שם המשימה או מספר המשימה (למשל: 'שנה את שדרוג VMware לבתהליך')."
        elif not mutating_successes and is_task_status_query(user_msg):
            # The user asked about task status / details!
            target_task = find_target_task_in_context(user_msg, ai_reply_str, history=messages)
            if target_task:
                detailed_summary = format_task_status_summary(target_task, members_lookup=ctx.get('members_lookup'))
                # If clean_reply doesn't already have the organized summary, provide it
                if f"#{target_task.id}" not in clean_reply or "סטטוס:" not in clean_reply:
                    if clean_reply and len(clean_reply) < 120 and not clean_reply.startswith('**פרטי'):
                        clean_reply = f"{clean_reply}\n\n{detailed_summary}".strip()
                    else:
                        clean_reply = detailed_summary
        elif not mutating_successes:
            # Check team tasks query first (e.g. "איזה משימות פתוחות יש לצוות DEVOPS")
            team_info = get_team_tasks_query_info(user_msg, ctx)
            if team_info:
                team_obj, team_tasks, is_open_only, is_count_query, all_team_tasks = team_info
                clean_reply = format_team_tasks_summary(
                    team_obj, team_tasks,
                    is_open_only=is_open_only,
                    is_count_query=is_count_query,
                    all_team_tasks=all_team_tasks,
                    members_lookup=ctx.get('members_lookup')
                )
            else:
                # Check member tasks query (e.g. "כמה משימות פתוחות יש לנועם", "מה המשימות של אלירן")
                member_info = get_member_tasks_query_info(user_msg, ctx)
                if member_info:
                    member_name, member_tasks, is_open_only, is_count_query, all_member_tasks = member_info
                    has_task_ids = any(f"#{t.get('id')}" in clean_reply for t in member_tasks)
                    if not clean_reply or len(clean_reply) < 40 or not has_task_ids or is_open_only:
                        clean_reply = format_member_tasks_summary(
                            member_name, member_tasks,
                            is_open_only=is_open_only,
                            is_count_query=is_count_query,
                            all_member_tasks=all_member_tasks
                        )

        if not clean_reply or clean_reply in ['.', ':', '!', '-']:
            if executed_actions:
                successes = [a for a in executed_actions if a.get('status') == 'success']
                if successes:
                    if any(s.get('action') in ['list_tasks', 'list_projects'] for s in successes):
                        clean_reply = "\n\n".join([s.get('description', '') for s in successes if s.get('description')])
                    else:
                        # For mutating actions, leave clean_reply empty so ONLY the single styled action card renders!
                        clean_reply = ""
                else:
                    errors = [a.get('error') for a in executed_actions if a.get('error')]
                    clean_reply = "שגיאה בביצוע:\n" + "\n".join(errors) if errors else ""
            else:
                clean_reply = sanitize_ai_reply(ai_reply_str, members_lookup=ctx.get('members_lookup'))

        # If user intended an action but no mutating success occurred yet, try fallback detection now:
        if not mutating_successes and user_has_action_intent:
            fallback = detect_fallback_action(user_msg, ai_reply_str, history=messages)
            if fallback:
                fb_exec, fb_refresh = execute_actions(fallback)
                fb_successes = [
                    a for a in fb_exec
                    if a.get('status') == 'success' and a.get('action') not in ['list_tasks', 'list_projects', 'search_tasks', 'get_tasks']
                ]
                if fb_successes:
                    executed_actions = fb_exec
                    refresh_needed = fb_refresh or refresh_needed
                    mutating_successes = fb_successes
                    clean_reply = ""

        # CRITICAL: If a mutating action succeeded, suppress any LLM hallucinated refusal/error messages
        if mutating_successes:
            refusal_patterns = [
                r'לא\s+ניתן', r'אי\s+אפשר', r'אין\s+באפשרותי', r'לא\s+הצלחתי',
                r'לא\s+נמצא[הת]?', r'שגיאה', r'נכשל[הת]?', r'תופסק'
            ]
            if any(re.search(p, clean_reply) for p in refusal_patterns):
                clean_reply = ""

        # CRITICAL SAFETY & INTEGRITY: Never allow the assistant to falsely claim an action was executed if it was not!
        if not mutating_successes and user_has_action_intent:
            false_claim_patterns = [
                r'בוצע[הת]?\s+בהצלחה',
                r'הועבר[הו]?\s+(?:בהצלחה\s+)?לארכיון',
                r'ארכיב[הת]?\s+משימה',
                r'ארכבתי',
                r'נמחק[הו]?\s+(?:בהצלחה\s+)?(?:משימה|פרויקט)?',
                r'מחקתי',
                r'עודכן[הו]?\s+(?:בהצלחה\s+)?(?:משימה|פרויקט)?',
                r'עדכנתי',
                r'נוצר[הו]?\s+(?:בהצלחה\s+)?(?:משימה|פרויקט)?',
                r'נוסף[הו]?\s+(?:בהצלחה\s+)?(?:משימה|פרויקט)?',
                r'הוספתי',
                r'שוחזר[הו]?\s+(?:בהצלחה\s+)?(?:מהארכיון)?',
                r'שחזרתי',
                r'סומנ[הת]?\s+(?:כ?הושלמ[הת]|כ?בוצע[הת]?)',
                r'סימנתי',
                r'סגרתי',
                r'השלמתי',
                r'סטטוס:\s*(?:הושלם|בוצע)'
            ]
            has_false_claim = any(re.search(pat, clean_reply) for pat in false_claim_patterns)

            if has_false_claim or (user_has_action_intent and (not clean_reply or clean_reply in ['.', ':', '!', '-'])):
                errors = [a.get('error') for a in executed_actions if a.get('error')]
                if errors:
                    clean_reply = f"שגיאה בביצוע הפעולה: {', '.join(errors)}"
                else:
                    clean_reply = "לא ניתן היה לבצע את הפעולה במערכת (לא זוהתה משימה מתאימה או שפרטי הפעולה לא היו ברורים). אנא ציין את מספר המשימה במפורש (למשל: #56) כדי שאוכל לבצע זאת."

        return jsonify({
            'success': True,
            'reply': clean_reply,
            'raw_reply': ai_reply,
            'actions': executed_actions,
            'refresh_needed': refresh_needed
        })
    except Exception as e:
        logger.error(f"Error in AI chat endpoint: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ai/quick', methods=['POST'])
def api_ai_quick():
    """Handles one-click smart actions: summary, deadlines, stale."""
    data = request.json or {}
    action_type = data.get('action', 'summary')

    try:
        if action_type == 'summary':
            summary_data = get_executive_summary()
            prompt = f"""הנה נתוני המערכת העדכניים:
- תאריך: {summary_data['date_hebrew']}
- סה"כ פרויקטים: {summary_data['total_projects']}
- סה"כ משימות פעילות: {summary_data['total_tasks']}
- אחוז השלמה כולל: {summary_data['completion_rate']}%
- התפלגות סטטוסים: הושלם: {summary_data['status_counts'].get('status-done', 0)}, בתהליך: {summary_data['status_counts'].get('status-inprogress', 0)}, טרם החל: {summary_data['status_counts'].get('status-notstarted', 0)}, מעוכב: {summary_data['status_counts'].get('status-delayed', 0)}
- משימות ללא משויך: {summary_data['unassigned_count']}
- עומס חברי צוות: {json.dumps(summary_data['member_workload'], ensure_ascii=False)}

אנא כתוב סקירה ניהולית תמציתית, חדה ומרשימה בעברית. כלול:
1. תמונת מצב כללית והתקדמות.
2. פרויקטים בולטים והספקים.
3. תמונת עומסים לפי חברי צוות (מי עמוס ומי פנוי).
4. המלצות קונקרטיות להמשך.
"""
            ai_reply = ai_service.chat([{'role': 'user', 'content': prompt}])
            return jsonify({
                'success': True,
                'action': 'summary',
                'reply': ai_reply,
                'data': summary_data
            })

        elif action_type == 'deadlines':
            deadlines_data = get_deadlines_analysis()
            overdue_list = [f"#{t['id']} [{t['project']}] {t['task']} (איחור של {t['days_overdue']} ימים! דדליין: {t['end_date']}, משויך: {','.join(t['members'])})" for t in deadlines_data['overdue_tasks']]
            due_week_list = [f"#{t['id']} [{t['project']}] {t['task']} (נותרו {t['days_left']} ימים, דדליין: {t['end_date']})" for t in deadlines_data['due_this_week_tasks']]
            
            prompt = f"""הנה תמונת הדדליינים והעיכובים במערכת נכון להיום ({deadlines_data['today_hebrew']}):
- משימות באיחור (Overdue - דורשות טיפול מיידי!): {len(overdue_list)}
{chr(10).join(overdue_list[:15]) if overdue_list else 'אין משימות באיחור! כל הכבוד.'}

- משימות לדדליין בשבוע הקרוב: {len(due_week_list)}
{chr(10).join(due_week_list[:15]) if due_week_list else 'אין משימות קרובות לדדליין.'}

- משימות בסטטוס מעוכב (Delayed): {deadlines_data['delayed_count']}
- משימות פעילות ללא תאריך סיום מוגדר: {deadlines_data['missing_dates_count']}

כתוב תדריך דדליינים ברור, ממוקד ומניע לפעולה בעברית. הדגש מה דורש טיפול מיידי היום ומה הצעדים המומלצים עבור כל משימה באיחור.
"""
            ai_reply = ai_service.chat([{'role': 'user', 'content': prompt}])
            return jsonify({
                'success': True,
                'action': 'deadlines',
                'reply': ai_reply,
                'data': deadlines_data
            })

        elif action_type == 'stale':
            stale_data = get_stale_and_suggestions()
            empty_projs = [f"פרויקט '{p['name']}' (ללא משימות)" for p in stale_data['empty_projects']]
            unassigned = [f"#{t['id']} [{t['project']}] {t['task']}" for t in stale_data['unassigned_tasks'][:10]]
            stuck = [f"#{t['id']} [{t['project']}] {t['task']} (בתהליך ללא תאריך סיום או באיחור)" for t in stale_data['stuck_in_progress'][:10]]

            prompt = f"""נמצאו המשימות והפרויקטים הבאים הדורשים עדכון, טיפול או סדר במערכת:
- פרויקטים ריקים ללא משימות:
{chr(10).join(empty_projs) if empty_projs else 'אין פרויקטים ריקים.'}

- משימות פעילות ללא חבר צוות משויך:
{chr(10).join(unassigned) if unassigned else 'כל המשימות משויכות.'}

- משימות שתקועות בסטטוס 'בתהליך' (ללא תאריכים או עברו את הזמן):
{chr(10).join(stuck) if stuck else 'אין משימות תקועות.'}

- משימות ללא הערכת שעות: {stale_data['missing_hours_count']} משימות.

אנא נסח הצעות אופרטיביות וברורות בעברית לשיפור וסדר במערכת:
הצע פעולות ספציפיות שהמשתמש יכול לבקש ממך לבצע מיד (למשל: למחוק פרויקט ריק, לשייך משימה לחבר צוות, לסגור משימות).
"""
            ai_reply = ai_service.chat([{'role': 'user', 'content': prompt}])
            return jsonify({
                'success': True,
                'action': 'stale',
                'reply': ai_reply,
                'data': stale_data
            })
        else:
            return jsonify({'success': False, 'error': f'פעולה לא מוכרת: {action_type}'}), 400
    except Exception as e:
        logger.error(f"Error in AI quick endpoint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============ BACKUP & RESTORE API ============

@app.route('/api/backup/<string:table_name>', methods=['GET'])
def api_backup_table(table_name):
    """Export table data as JSON with full relationship preservation"""
    models = {
        'teams': Team,
        'projects': Project,
        'members': TeamMember,
        'tasks': Task,
        'special_days': SpecialDay
    }
    
    if table_name == 'all':
        full_data = {}
        total_count = 0
        for name, model in models.items():
            records = [r.to_dict() for r in model.query.all()]
            full_data[name] = records
            total_count += len(records)
            
        # Export association tables explicitly
        pt_rows = db.session.execute(project_teams.select()).fetchall()
        full_data['project_teams'] = [{'project_id': r[0], 'team_id': r[1]} for r in pt_rows]
        total_count += len(pt_rows)

        mt_rows = db.session.execute(member_teams.select()).fetchall()
        full_data['member_teams'] = [{'member_id': r[0], 'team_id': r[1]} for r in mt_rows]
        total_count += len(mt_rows)
            
        response_data = {
            'table': 'all',
            'count': total_count,
            'timestamp': time.time(),
            'data': full_data
        }
    elif table_name in models:
        model = models[table_name]
        records = model.query.all()
        data = [record.to_dict() for record in records]
        
        response_data = {
            'table': table_name,
            'count': len(data),
            'timestamp': time.time(),
            'data': data
        }
    else:
        return jsonify({'error': 'Invalid table name'}), 400
    
    response = jsonify(response_data)
    response.headers['Content-Disposition'] = f'attachment; filename=backup_{table_name}_{int(time.time())}.json'
    return response

@app.route('/api/restore/<string:table_name>', methods=['POST'])
def api_restore_table(table_name):
    """Import table data from JSON with comprehensive validation and relationship preservation"""
    from datetime import datetime, date
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file part'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'}), 400

    def parse_date(val):
        if not val:
            return None
        if isinstance(val, (datetime, date)):
            return val if isinstance(val, date) else val.date()
        if isinstance(val, str):
            val = val.strip()
            if not val or val.lower() in ('null', 'none', 'undefined'):
                return None
            iso_prefix = val[:10]
            try:
                return datetime.fromisoformat(iso_prefix).date()
            except Exception:
                try:
                    return datetime.strptime(iso_prefix, '%Y-%m-%d').date()
                except Exception:
                    return None
        return None

    def parse_float(val):
        if val is None or val == '':
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    def parse_int(val):
        if val is None or val == '':
            return None
        try:
            return int(val)
        except (ValueError, TypeError):
            return None

    def parse_bool(val, default=False):
        if val is None:
            return default
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.lower() in ('true', '1', 'yes')
        if isinstance(val, (int, float)):
            return bool(val)
        return default

    valid_tables = {'all', 'teams', 'projects', 'members', 'tasks', 'special_days'}
    if table_name not in valid_tables:
        return jsonify({'success': False, 'error': f'Invalid table name: {table_name}'}), 400
        
    try:
        raw_bytes = file.read()
        text_content = raw_bytes.decode('utf-8-sig')
        content = json.loads(text_content)
        
        is_full_backup = (table_name == 'all')
        
        if isinstance(content, dict) and 'table' in content:
            source_table = content['table']
            if is_full_backup and source_table != 'all':
                return jsonify({'success': False, 'error': 'Cannot restore single table backup to "All System"'}), 400
            if not is_full_backup and source_table == 'all':
                return jsonify({'success': False, 'error': 'Cannot restore "All System" backup to single table. Select "All System" to restore.'}), 400
            if not is_full_backup and source_table != table_name:
                return jsonify({'success': False, 'error': f'Table mismatch: File is "{source_table}", expected "{table_name}"'}), 400
            data = content.get('data')
        else:
            if is_full_backup:
                return jsonify({'success': False, 'error': 'Invalid backup format for full restore'}), 400
            data = content if isinstance(content, list) else []

        if data is None or (isinstance(data, list) and len(data) == 0) or (isinstance(data, dict) and len(data) == 0):
            return jsonify({'success': True, 'message': 'No data to restore', 'counts': {}})

        if is_full_backup:
            if not isinstance(data, dict):
                return jsonify({'success': False, 'error': 'Invalid data format for full restore (expected JSON object)'}), 400

            # 1. Clear existing data in reverse foreign key dependency order
            try:
                db.session.execute(project_teams.delete())
                db.session.execute(member_teams.delete())
                Task.query.delete()
                SpecialDay.query.delete()
                TeamMember.query.delete()
                Project.query.delete()
                Team.query.delete()
                db.session.flush()
            except Exception as e:
                db.session.rollback()
                return jsonify({'success': False, 'error': f'Failed to clear existing data: {str(e)}'}), 500

            restored_counts = {}

            # 2. Restore Teams
            teams_data = data.get('teams', [])
            team_count = 0
            for item in teams_data:
                clean = {
                    'id': parse_int(item.get('id')),
                    'name_en': str(item.get('name_en', '')).strip(),
                    'name_he': str(item.get('name_he', '')).strip()
                }
                if not clean['name_en'] or not clean['name_he']:
                    continue
                t = Team(**clean)
                if clean['id']:
                    db.session.merge(t)
                else:
                    db.session.add(t)
                team_count += 1
            db.session.flush()
            restored_counts['teams'] = team_count

            # 3. Restore Projects
            projects_data = data.get('projects', [])
            project_count = 0
            for item in projects_data:
                clean = {
                    'id': parse_int(item.get('id')),
                    'name': str(item.get('name', '')).strip(),
                    'is_archived': parse_bool(item.get('is_archived'), False)
                }
                if not clean['name']:
                    continue
                p = Project(**clean)
                if clean['id']:
                    db.session.merge(p)
                else:
                    db.session.add(p)
                project_count += 1
            db.session.flush()
            restored_counts['projects'] = project_count

            # 4. Restore Members
            members_data = data.get('members', [])
            member_count = 0
            valid_team_ids = set(r[0] for r in db.session.query(Team.id).all())
            for item in members_data:
                tid = parse_int(item.get('team_id'))
                clean = {
                    'id': parse_int(item.get('id')),
                    'team_id': tid if tid in valid_team_ids else None,
                    'name_en': str(item.get('name_en', '')).strip(),
                    'name_he': str(item.get('name_he', '')).strip(),
                    'avatar_path': str(item.get('avatar_path', 'default.png')).strip() or 'default.png'
                }
                if not clean['name_en'] or not clean['name_he']:
                    continue
                m = TeamMember(**clean)
                if clean['id']:
                    db.session.merge(m)
                else:
                    db.session.add(m)
                member_count += 1
            db.session.flush()
            restored_counts['members'] = member_count

            # 5. Restore Many-to-Many Associations
            valid_project_ids = set(r[0] for r in db.session.query(Project.id).all())
            valid_member_ids = set(r[0] for r in db.session.query(TeamMember.id).all())

            # 5a. project_teams
            pt_pairs = set()
            for row in data.get('project_teams', []):
                pid = parse_int(row.get('project_id'))
                tid = parse_int(row.get('team_id'))
                if pid in valid_project_ids and tid in valid_team_ids:
                    pt_pairs.add((pid, tid))
            for p_item in projects_data:
                pid = parse_int(p_item.get('id'))
                if pid in valid_project_ids:
                    t_ids = p_item.get('team_ids')
                    if isinstance(t_ids, list):
                        for tid in t_ids:
                            tid_int = parse_int(tid)
                            if tid_int in valid_team_ids:
                                pt_pairs.add((pid, tid_int))
            for pid, tid in pt_pairs:
                db.session.execute(project_teams.insert().values(project_id=pid, team_id=tid))
            restored_counts['project_teams'] = len(pt_pairs)

            # 5b. member_teams
            mt_pairs = set()
            for row in data.get('member_teams', []):
                mid = parse_int(row.get('member_id'))
                tid = parse_int(row.get('team_id'))
                if mid in valid_member_ids and tid in valid_team_ids:
                    mt_pairs.add((mid, tid))
            for m_item in members_data:
                mid = parse_int(m_item.get('id'))
                if mid in valid_member_ids:
                    t_ids = m_item.get('team_ids')
                    if isinstance(t_ids, list) and len(t_ids) > 0:
                        for tid in t_ids:
                            tid_int = parse_int(tid)
                            if tid_int in valid_team_ids:
                                mt_pairs.add((mid, tid_int))
                    elif m_item.get('team_id'):
                        tid_int = parse_int(m_item['team_id'])
                        if tid_int in valid_team_ids:
                            mt_pairs.add((mid, tid_int))
            for mid, tid in mt_pairs:
                db.session.execute(member_teams.insert().values(member_id=mid, team_id=tid))
            restored_counts['member_teams'] = len(mt_pairs)

            # 6. Restore Tasks
            tasks_data = data.get('tasks', [])
            task_count = 0
            for item in tasks_data:
                m_val = item.get('members', '')
                if isinstance(m_val, list):
                    members_str = ','.join(str(m).strip() for m in m_val if m and str(m).strip())
                else:
                    members_str = str(m_val or '').strip()

                p_id = parse_int(item.get('project_id'))
                t_id = parse_int(item.get('team_id'))
                clean = {
                    'id': parse_int(item.get('id')),
                    'project_id': p_id if p_id in valid_project_ids else None,
                    'project': str(item.get('project', '')).strip(),
                    'task': str(item.get('task', '')).strip(),
                    'members': members_str,
                    'status': str(item.get('status', 'status-inprogress')).strip() or 'status-inprogress',
                    'priority': str(item.get('priority', 'none')).strip() or 'none',
                    'notes': item.get('notes'),
                    'team_id': t_id if t_id in valid_team_ids else None,
                    'start_date': parse_date(item.get('start_date')),
                    'end_date': parse_date(item.get('end_date')),
                    'estimated_hours': parse_float(item.get('estimated_hours')),
                    'is_archived': parse_bool(item.get('is_archived'), False)
                }
                if not clean['task']:
                    continue
                t = Task(**clean)
                if clean['id']:
                    db.session.merge(t)
                else:
                    db.session.add(t)
                task_count += 1
            db.session.flush()
            restored_counts['tasks'] = task_count

            # 7. Restore SpecialDays
            special_days_data = data.get('special_days', [])
            sd_count = 0
            for item in special_days_data:
                d = parse_date(item.get('date'))
                if not d:
                    continue
                clean = {
                    'id': parse_int(item.get('id')),
                    'date': d,
                    'name': str(item.get('name', '')).strip(),
                    'type': str(item.get('type', 'holiday')).strip() or 'holiday',
                    'color': str(item.get('color', '')).strip() if item.get('color') else None
                }
                if not clean['name']:
                    continue
                sd = SpecialDay(**clean)
                if clean['id']:
                    db.session.merge(sd)
                else:
                    db.session.add(sd)
                sd_count += 1
            db.session.flush()
            restored_counts['special_days'] = sd_count

            db.session.commit()
            return jsonify({'success': True, 'counts': restored_counts})

        else:
            # Single Table Restore
            if not isinstance(data, list):
                return jsonify({'success': False, 'error': 'Invalid data format for single table restore (expected list)'}), 400

            valid_team_ids = set(r[0] for r in db.session.query(Team.id).all())
            valid_project_ids = set(r[0] for r in db.session.query(Project.id).all())
            count = 0

            if table_name == 'teams':
                for item in data:
                    clean = {
                        'id': parse_int(item.get('id')),
                        'name_en': str(item.get('name_en', '')).strip(),
                        'name_he': str(item.get('name_he', '')).strip()
                    }
                    if not clean['name_en'] or not clean['name_he']:
                        continue
                    t = Team(**clean)
                    if clean['id']:
                        db.session.merge(t)
                    else:
                        db.session.add(t)
                    count += 1

            elif table_name == 'projects':
                for item in data:
                    clean = {
                        'id': parse_int(item.get('id')),
                        'name': str(item.get('name', '')).strip(),
                        'is_archived': parse_bool(item.get('is_archived'), False)
                    }
                    if not clean['name']:
                        continue
                    p = Project(**clean)
                    if clean['id']:
                        merged = db.session.merge(p)
                        db.session.flush()
                        proj_id = merged.id
                    else:
                        db.session.add(p)
                        db.session.flush()
                        proj_id = p.id

                    if 'team_ids' in item and isinstance(item['team_ids'], list):
                        db.session.execute(project_teams.delete().where(project_teams.c.project_id == proj_id))
                        for tid in item['team_ids']:
                            tid_int = parse_int(tid)
                            if tid_int in valid_team_ids:
                                db.session.execute(project_teams.insert().values(project_id=proj_id, team_id=tid_int))
                    count += 1

            elif table_name == 'members':
                for item in data:
                    tid = parse_int(item.get('team_id'))
                    clean = {
                        'id': parse_int(item.get('id')),
                        'team_id': tid if tid in valid_team_ids else None,
                        'name_en': str(item.get('name_en', '')).strip(),
                        'name_he': str(item.get('name_he', '')).strip(),
                        'avatar_path': str(item.get('avatar_path', 'default.png')).strip() or 'default.png'
                    }
                    if not clean['name_en'] or not clean['name_he']:
                        continue
                    m = TeamMember(**clean)
                    if clean['id']:
                        merged = db.session.merge(m)
                        db.session.flush()
                        mem_id = merged.id
                    else:
                        db.session.add(m)
                        db.session.flush()
                        mem_id = m.id

                    if 'team_ids' in item and isinstance(item['team_ids'], list):
                        db.session.execute(member_teams.delete().where(member_teams.c.member_id == mem_id))
                        for t in item['team_ids']:
                            t_int = parse_int(t)
                            if t_int in valid_team_ids:
                                db.session.execute(member_teams.insert().values(member_id=mem_id, team_id=t_int))
                    elif tid and tid in valid_team_ids:
                        exists = db.session.execute(
                            member_teams.select().where(
                                and_(member_teams.c.member_id == mem_id, member_teams.c.team_id == tid)
                            )
                        ).first()
                        if not exists:
                            db.session.execute(member_teams.insert().values(member_id=mem_id, team_id=tid))
                    count += 1

            elif table_name == 'tasks':
                for item in data:
                    m_val = item.get('members', '')
                    if isinstance(m_val, list):
                        members_str = ','.join(str(m).strip() for m in m_val if m and str(m).strip())
                    else:
                        members_str = str(m_val or '').strip()

                    p_id = parse_int(item.get('project_id'))
                    t_id = parse_int(item.get('team_id'))
                    clean = {
                        'id': parse_int(item.get('id')),
                        'project_id': p_id if p_id in valid_project_ids else None,
                        'project': str(item.get('project', '')).strip(),
                        'task': str(item.get('task', '')).strip(),
                        'members': members_str,
                        'status': str(item.get('status', 'status-inprogress')).strip() or 'status-inprogress',
                        'priority': str(item.get('priority', 'none')).strip() or 'none',
                        'notes': item.get('notes'),
                        'team_id': t_id if t_id in valid_team_ids else None,
                        'start_date': parse_date(item.get('start_date')),
                        'end_date': parse_date(item.get('end_date')),
                        'estimated_hours': parse_float(item.get('estimated_hours')),
                        'is_archived': parse_bool(item.get('is_archived'), False)
                    }
                    if not clean['task']:
                        continue
                    t = Task(**clean)
                    if clean['id']:
                        db.session.merge(t)
                    else:
                        db.session.add(t)
                    count += 1

            elif table_name == 'special_days':
                for item in data:
                    d = parse_date(item.get('date'))
                    if not d:
                        continue
                    clean = {
                        'id': parse_int(item.get('id')),
                        'date': d,
                        'name': str(item.get('name', '')).strip(),
                        'type': str(item.get('type', 'holiday')).strip() or 'holiday',
                        'color': str(item.get('color', '')).strip() if item.get('color') else None
                    }
                    if not clean['name']:
                        continue
                    sd = SpecialDay(**clean)
                    if clean['id']:
                        db.session.merge(sd)
                    else:
                        db.session.add(sd)
                    count += 1

            db.session.commit()
            return jsonify({'success': True, 'counts': {table_name: count}})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# --- General System & Environment Settings ---

def get_env_file_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')

def read_env_file():
    path = get_env_file_path()
    env_vars = {}
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    env_vars[key.strip()] = val.strip().strip('"').strip("'")
    return env_vars

def update_env_file(updates: dict):
    path = get_env_file_path()
    lines = []
    found_keys = set()
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and '=' in stripped:
            key, _ = stripped.split('=', 1)
            key = key.strip()
            if key in updates:
                new_lines.append(f"{key}={updates[key]}\n")
                found_keys.add(key)
                continue
        new_lines.append(line)

    for key, val in updates.items():
        if key not in found_keys:
            if new_lines and not new_lines[-1].endswith('\n'):
                new_lines[-1] += '\n'
            new_lines.append(f"{key}={val}\n")

    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    for k, v in updates.items():
        os.environ[k] = str(v)


@app.route('/api/system/settings', methods=['GET'])
def api_get_system_settings():
    """Retrieve full system settings, .env configurations, metrics, and runtime info."""
    try:
        import platform
        env_vars = read_env_file()
        ai_status = ai_service.get_status()

        # Database metrics
        db_path = os.path.join(app.instance_path, 'tasks.db')
        db_size_bytes = os.path.getsize(db_path) if os.path.exists(db_path) else 0
        if db_size_bytes < 1024 * 1024:
            db_size_formatted = f"{db_size_bytes / 1024:.1f} KB"
        else:
            db_size_formatted = f"{db_size_bytes / (1024 * 1024):.2f} MB"

        # Table counts
        total_tasks = Task.query.count()
        done_tasks = Task.query.filter_by(status='status-done').count()
        inprogress_tasks = Task.query.filter_by(status='status-inprogress').count()
        notstarted_tasks = Task.query.filter_by(status='status-notstarted').count()
        delayed_tasks = Task.query.filter_by(status='status-delayed').count()

        total_projects = Project.query.count()
        active_projects = Project.query.filter_by(is_archived=False).count()
        archived_projects = Project.query.filter_by(is_archived=True).count()

        total_teams = Team.query.count()
        total_members = TeamMember.query.count()
        special_days_count = SpecialDay.query.count()

        # Uploads metrics
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads/avatars')
        upload_count = 0
        upload_size_bytes = 0
        if os.path.exists(upload_folder):
            for f in os.listdir(upload_folder):
                fp = os.path.join(upload_folder, f)
                if os.path.isfile(fp):
                    upload_count += 1
                    upload_size_bytes += os.path.getsize(fp)
        if upload_size_bytes < 1024 * 1024:
            upload_size_formatted = f"{upload_size_bytes / 1024:.1f} KB"
        else:
            upload_size_formatted = f"{upload_size_bytes / (1024 * 1024):.2f} MB"

        # Mask sensitive tokens
        cf_token = env_vars.get('CLOUDFLARE_API_TOKEN', '')
        cf_token_masked = (cf_token[:5] + '••••••••••••••••' + cf_token[-4:]) if len(cf_token) > 10 else ('••••••••' if cf_token else '')

        openai_key = env_vars.get('OPENAI_API_KEY', '') or env_vars.get('AI_API_KEY', '')
        openai_key_masked = (openai_key[:4] + '••••••••' + openai_key[-3:]) if len(openai_key) > 8 else ('••••••••' if openai_key else '')

        # Active provider
        active_provider = env_vars.get('AI_PROVIDER', '').lower().strip()
        if not active_provider:
            active_provider = ai_status.get('provider', 'cloudflare')

        return jsonify({
            'success': True,
            'settings': {
                'ai_provider': active_provider,
                # Local OpenAI settings
                'openai_base_url': env_vars.get('OPENAI_API_BASE', '') or env_vars.get('AI_BASE_URL', ''),
                'openai_model': env_vars.get('OPENAI_MODEL', '') or env_vars.get('AI_MODEL', 'llama3.3'),
                'openai_api_key_masked': openai_key_masked,
                'has_openai_key': bool(openai_key),
                # Cloudflare settings
                'cloudflare_account_id': env_vars.get('CLOUDFLARE_ACCOUNT_ID', ''),
                'cloudflare_api_token_masked': cf_token_masked,
                'has_cloudflare_token': bool(cf_token),
                'cloudflare_model': env_vars.get('CLOUDFLARE_MODEL', '@cf/meta/llama-3.1-8b-instruct'),
                # App config
                'app_name': env_vars.get('APP_NAME', 'TeamTasks'),
            },
            'ai_status': ai_status,
            'system_info': {
                'db_path': db_path,
                'db_size': db_size_formatted,
                'metrics': {
                    'total_tasks': total_tasks,
                    'done_tasks': done_tasks,
                    'inprogress_tasks': inprogress_tasks,
                    'notstarted_tasks': notstarted_tasks,
                    'delayed_tasks': delayed_tasks,
                    'total_projects': total_projects,
                    'active_projects': active_projects,
                    'archived_projects': archived_projects,
                    'total_teams': total_teams,
                    'total_members': total_members,
                    'special_days': special_days_count,
                },
                'uploads': {
                    'count': upload_count,
                    'size': upload_size_formatted,
                    'folder': upload_folder
                },
                'runtime': {
                    'python_version': platform.python_version(),
                    'platform': f"{platform.system()} {platform.release()}",
                    'debug': app.debug,
                    'is_airgapped': ai_status.get('is_airgapped', False)
                }
            }
        })
    except Exception as e:
        logger.error(f"Error getting system settings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/system/settings', methods=['POST'])
def api_update_system_settings():
    """Save updated .env configuration and immediately reload AI service."""
    try:
        data = request.json or {}
        updates = {}

        provider = data.get('ai_provider', '').strip().lower()
        if provider in ['local_openai', 'cloudflare']:
            updates['AI_PROVIDER'] = provider

        # Local AI parameters
        if 'openai_base_url' in data:
            updates['OPENAI_API_BASE'] = data.get('openai_base_url', '').strip()
        if 'openai_model' in data:
            updates['OPENAI_MODEL'] = data.get('openai_model', '').strip()
        if 'openai_api_key' in data:
            val = data.get('openai_api_key', '').strip()
            if val and not '••••' in val:
                updates['OPENAI_API_KEY'] = val

        # Cloudflare parameters
        if 'cloudflare_account_id' in data:
            updates['CLOUDFLARE_ACCOUNT_ID'] = data.get('cloudflare_account_id', '').strip()
        if 'cloudflare_api_token' in data:
            val = data.get('cloudflare_api_token', '').strip()
            if val and not '••••' in val:
                updates['CLOUDFLARE_API_TOKEN'] = val
        if 'cloudflare_model' in data:
            updates['CLOUDFLARE_MODEL'] = data.get('cloudflare_model', '').strip()

        if 'app_name' in data and data.get('app_name', '').strip():
            updates['APP_NAME'] = data.get('app_name', '').strip()

        # Update .env
        update_env_file(updates)

        # Reload AI service configuration live
        ai_service.reload_config()

        new_status = ai_service.get_status()
        return jsonify({
            'success': True,
            'message': 'ההגדרות נשמרו בהצלחה בקובץ .env ומנוע ה-AI עודכן',
            'ai_status': new_status
        })
    except Exception as e:
        logger.error(f"Error saving system settings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/system/test-ai', methods=['POST'])
def api_test_ai_connection():
    """Test AI endpoint connection with latency measurement (can test unsaved form data or current)."""
    import requests
    t0 = time.time()
    try:
        data = request.json or {}
        provider = data.get('ai_provider', '').strip().lower() or ai_service.provider

        if provider == 'local_openai':
            base_url = (data.get('openai_base_url') or ai_service.openai_base_url or '').rstrip('/')
            model = data.get('openai_model') or ai_service.openai_model or 'llama3.3'
            api_key = data.get('openai_api_key') or ai_service.openai_api_key or 'sk-local'
            if '••••' in api_key:
                api_key = ai_service.openai_api_key

            if not base_url:
                return jsonify({'success': False, 'error': 'כתובת שרת מקומי (OPENAI_API_BASE) חסרה'}), 400

            url = f"{base_url}/chat/completions"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {api_key}"
            }
            payload = {
                'model': model,
                'messages': [{'role': 'user', 'content': 'ענה במילה אחת בלבד: פועל'}],
                'temperature': 0.1,
                'max_tokens': 15
            }
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            res_json = response.json()
            choices = res_json.get('choices', [])
            reply = choices[0]['message']['content'].strip() if choices else res_json.get('response', 'OK')

            latency_ms = round((time.time() - t0) * 1000)
            return jsonify({
                'success': True,
                'latency_ms': latency_ms,
                'reply': reply,
                'provider': 'local_openai',
                'model': model,
                'endpoint': base_url,
                'is_airgapped': True
            })

        elif provider == 'cloudflare':
            account_id = data.get('cloudflare_account_id') or ai_service.cf_account_id
            api_token = data.get('cloudflare_api_token') or ai_service.cf_api_token
            if '••••' in api_token:
                api_token = ai_service.cf_api_token
            model = data.get('cloudflare_model') or ai_service.cf_model or '@cf/meta/llama-3.1-8b-instruct'

            if not account_id or not api_token:
                return jsonify({'success': False, 'error': 'Account ID או API Token של Cloudflare חסרים'}), 400

            url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
            headers = {
                'Authorization': f'Bearer {api_token}',
                'Content-Type': 'application/json'
            }
            payload = {
                'messages': [{'role': 'user', 'content': 'ענה במילה אחת בלבד: פועל'}],
                'max_tokens': 15
            }
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            response.raise_for_status()
            res_json = response.json()
            reply = res_json.get('result', {}).get('response', 'OK')

            latency_ms = round((time.time() - t0) * 1000)
            return jsonify({
                'success': True,
                'latency_ms': latency_ms,
                'reply': reply.strip() if isinstance(reply, str) else str(reply),
                'provider': 'cloudflare',
                'model': model,
                'is_airgapped': False
            })

        else:
            return jsonify({'success': False, 'error': f'ספק AI לא מוכר: {provider}'}), 400

    except requests.exceptions.ConnectionError:
        latency_ms = round((time.time() - t0) * 1000)
        return jsonify({
            'success': False,
            'latency_ms': latency_ms,
            'error': 'שגיאת חיבור (Connection Refused): לא ניתן להגיע לכתובת השרת. ודא שה-Gateway/Ollama פעיל ומאזין בפורט זה.'
        }), 400
    except requests.exceptions.Timeout:
        latency_ms = round((time.time() - t0) * 1000)
        return jsonify({
            'success': False,
            'latency_ms': latency_ms,
            'error': 'זמן ההמתנה לשרת פג (Timeout לאחר 15-20 שניות). ייתכן שהשרת עמוס או שהמודל נטען לזיכרון.'
        }), 400
    except requests.exceptions.HTTPError as he:
        latency_ms = round((time.time() - t0) * 1000)
        status_code = he.response.status_code if he.response else 500
        text = he.response.text if he.response else str(he)
        return jsonify({
            'success': False,
            'latency_ms': latency_ms,
            'error': f"שגיאת HTTP {status_code}: {text}"
        }), 400
    except Exception as e:
        latency_ms = round((time.time() - t0) * 1000)
        return jsonify({
            'success': False,
            'latency_ms': latency_ms,
            'error': str(e)
        }), 500


@app.route('/api/system/check-db', methods=['POST'])
def api_check_db_integrity():
    """Run SQLite integrity check on tasks.db."""
    try:
        from sqlalchemy import text
        res = db.session.execute(text("PRAGMA integrity_check")).fetchone()
        status = res[0] if res else 'unknown'
        return jsonify({'success': True, 'integrity': status})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/')
def index():
    project_filter = request.args.get('project')
    member_filter = request.args.get('member')
    team_filter = request.args.get('team')
    query_str = request.args.get('q', '').strip()
    mode = request.args.get('mode', 'active') # 'active' or 'archive'

    # Order by priority (high, medium, low, none)
    priority_order = case(
        (Task.priority == 'high', 1),
        (Task.priority == 'medium', 2),
        (Task.priority == 'low', 3),
        (Task.priority == 'none', 4),
    )
    
    # Base query
    query = Task.query.order_by(priority_order, Task.project)
    
    # Filter by Archive Status based on mode
    if mode == 'archive':
        query = query.filter(Task.is_archived == True)
    else:
        query = query.filter(Task.is_archived == False)

    # Search Logic
    if query_str:
        search_pattern = f'%{query_str}%'
        query = query.filter(
            or_(
                Task.task.like(search_pattern),
                Task.project.like(search_pattern),
                Task.notes.like(search_pattern),
                Task.members.like(search_pattern)
            )
        )

    if project_filter:
        query = query.filter(Task.project == project_filter)
    if member_filter:
        query = query.filter(Task.members.contains(member_filter))
    
    # Team filtering context
    active_team_id = None
    active_team_members = []
    
    if team_filter and team_filter.isdigit():
        active_team_id = int(team_filter)
        # Fetch team members for relaxed filtering (Team OR Member)
        team = db.session.get(Team, active_team_id)
        if team:
            active_team_members = [m.name_en for m in team.members]

    tasks = query.all()

    # Query projects
    if mode == 'archive':
        # In archive mode, show projects marked as is_archived OR projects that have archived tasks
        archived_proj_names = set(task.project for task in tasks)
        proj_filter = or_(Project.is_archived == True, Project.name.in_(archived_proj_names)) if archived_proj_names else (Project.is_archived == True)
        projects = Project.query.filter(proj_filter).order_by(Project.name).all()
    else:
        projects = Project.query.filter(Project.is_archived == False).order_by(Project.name).all()
    
    # Get all teams and members dynamically
    teams = Team.query.all()
    members = TeamMember.query.order_by(TeamMember.name_he).all()
    
    # Create a mapping of project names to team names
    project_teams = {}
    for project in projects:
        if project.teams:
            project_teams[project.name] = ", ".join([t.name_he for t in project.teams])
        else:
            project_teams[project.name] = "כללי"
    
    return render_template('index.html', tasks=tasks, projects=projects, members=members, teams=teams, project_teams=project_teams, active_team_id=active_team_id, active_team_members=active_team_members, q=query_str, mode=mode)







@app.route('/print')
def print_view():
    project_filter = request.args.get('project')
    member_filter = request.args.get('member')
    team_filter = request.args.get('team')
    status_filter = request.args.get('status')
    priority_filter = request.args.get('priority')

    # Base query for filtering
    query = Task.query.filter(Task.is_archived == False)

    # Apply filters that limit the SCOPE of projects (Team, Member, Status, Priority)
    # We apply these FIRST so we can get the list of relevant projects.
    if member_filter:
        query = query.filter(Task.members.contains(member_filter))
    if team_filter and str(team_filter).isdigit():
        tid = int(team_filter)
        team_obj = db.session.get(Team, tid)
        if team_obj and team_obj.members:
            member_filters = [Task.members.contains(m.name_en) for m in team_obj.members if m.name_en]
            query = query.filter(or_(Task.team_id == tid, *member_filters))
        else:
            query = query.filter(Task.team_id == tid)
    if status_filter and status_filter != 'all':
        if status_filter in ['not-done', 'status-notdone']:
            query = query.filter(Task.status != 'status-done')
        else:
            query = query.filter(Task.status == status_filter)
    if priority_filter and priority_filter != 'all':
        query = query.filter(Task.priority == priority_filter)
    
    # Helper to get distinct projects from the currently filtered scope
    # This list allows switching between projects that match the other criteria
    # e.g. If specific Team is selected, only show projects from that Team.
    available_projects_query = query.with_entities(Task.project).distinct()
    available_projects = sorted([p[0] for p in available_projects_query.all()])

    # Now apply the specific project filter if selected
    if project_filter:
        query = query.filter(Task.project == project_filter)

    # Apply ordering for display
    priority_order = case(
        (Task.priority == 'high', 1),
        (Task.priority == 'medium', 2),
        (Task.priority == 'low', 3),
        (Task.priority == 'none', 4),
    )
    query = query.order_by(priority_order, Task.project)

    tasks = query.all()
    
    # Projects to actually display sections for in the report
    display_projects = sorted(list(set(task.project for task in tasks)))
    
    # Get all teams and members dynamically
    teams = Team.query.all()
    members = TeamMember.query.all()
    
    return render_template('printable.html', tasks=tasks, projects=display_projects, all_projects=available_projects, members=members, teams=teams)


@app.route('/calendar')
def calendar():
    """Calendar page for week/month planning"""
    teams = Team.query.all()
    members = TeamMember.query.all()
    return render_template('calendar.html', teams=teams, members=members)


@app.route('/admin')
def admin():
    """Admin page for managing teams and members"""
    teams = Team.query.all()
    return render_template('admin.html', teams=teams)


@app.route('/archive')
def archive():
    """Page to view and restore archived tasks"""
    teams = [team.to_dict() for team in Team.query.all()]
    members = [member.to_dict() for member in TeamMember.query.all()]
    return render_template('archive.html', teams=teams, members=members)


if __name__ == '__main__':
    app.run(debug=True)
