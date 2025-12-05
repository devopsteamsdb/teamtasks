from flask import Flask, render_template, redirect, url_for, request, jsonify, send_from_directory
from sqlalchemy import case, distinct, or_
from werkzeug.utils import secure_filename
import os
import time

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size
# Import models and initialize db
from models import db, Team, TeamMember, Task
db.init_app(app)

@app.route('/api/version')
def api_version():
    try:
        # Check database file modification time
        db_path = os.path.join(app.instance_path, 'tasks.db')
        # If app.instance_path is not where we expect, try relative
        if not os.path.exists(db_path):
             db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'tasks.db')
             
        if os.path.exists(db_path):
            timestamp = os.path.getmtime(db_path)
        else:
            timestamp = time.time()
            
        response = jsonify({'timestamp': timestamp})
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response
    except Exception:
        return jsonify({'timestamp': time.time()})

# API endpoint to add a task (AJAX)
@app.route('/api/tasks', methods=['POST'])
def api_add_task():
    data = request.json
    project = data.get('project')
    if not project or not project.strip():
        project = "ללא פרויקט"
        
    task = data.get('task')
    if not task or not task.strip():
        task = "ללא שם"
    members = ','.join(data.get('members', []))
    status = data.get('status')
    priority = data.get('priority', 'none')
    notes = data.get('notes', '')
    team_id = data.get('team_id')
    new_task = Task(project=project, task=task, members=members, status=status, priority=priority, notes=notes, team_id=team_id)
    new_task = Task(project=project, task=task, members=members, status=status, priority=priority, notes=notes, team_id=team_id)
    db.session.add(new_task)
    db.session.commit()
    
    return jsonify({'success': True, 'id': new_task.id})

# API endpoint to edit a task (AJAX)
@app.route('/api/tasks/<int:id>', methods=['PUT'])
def api_edit_task(id):
    task = Task.query.get_or_404(id)
    data = request.json
    task.project = data.get('project', task.project)
    task.task = data.get('task', task.task)
    task.members = ','.join(data.get('members', task.members.split(',')))
    task.status = data.get('status', task.status)
    task.priority = data.get('priority', task.priority)
    task.notes = data.get('notes', task.notes)
    task.team_id = data.get('team_id', task.team_id)
    task.team_id = data.get('team_id', task.team_id)
    db.session.commit()
    
    return jsonify({'success': True})

# API endpoint to delete a task (AJAX)
@app.route('/api/tasks/<int:id>', methods=['DELETE'])
def api_delete_task(id):
    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    
    return jsonify({'success': True})


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
    team = Team(name_en=name_en, name_he=name_he)
    db.session.add(team)
    db.session.commit()
    
    return jsonify({'success': True, 'team': team.to_dict()})

# Update a team
@app.route('/api/teams/<int:id>', methods=['PUT'])
def api_update_team(id):
    team = Team.query.get_or_404(id)
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
    team = Team.query.get_or_404(id)
    db.session.delete(team)
    db.session.commit()
    
    return jsonify({'success': True})


# ============ TEAM MEMBER API ============

# Get members of a specific team
@app.route('/api/teams/<int:team_id>/members', methods=['GET'])
def api_get_team_members(team_id):
    team = Team.query.get_or_404(team_id)
    return jsonify([member.to_dict() for member in team.members])

# Get all members (across all teams)
@app.route('/api/members', methods=['GET'])
def api_get_all_members():
    members = TeamMember.query.all()
    return jsonify([member.to_dict() for member in members])

# Add a member to a team
@app.route('/api/teams/<int:team_id>/members', methods=['POST'])
def api_add_team_member(team_id):
    team = Team.query.get_or_404(team_id)
    data = request.json
    
    name_en = data.get('name_en', '').strip().lower()
    name_he = data.get('name_he', '').strip()
    avatar_path = data.get('avatar_path', 'default.png')
    
    if not name_en or not name_he:
        return jsonify({'success': False, 'error': 'Both English and Hebrew names are required'}), 400
    
    member = TeamMember(
        team_id=team_id,
        name_en=name_en,
        name_he=name_he,
        avatar_path=avatar_path
    )
    db.session.add(member)
    db.session.commit()
    
    return jsonify({'success': True, 'member': member.to_dict()})

# Update a team member
@app.route('/api/teams/<int:team_id>/members/<int:member_id>', methods=['PUT'])
def api_update_team_member(team_id, member_id):
    member = TeamMember.query.filter_by(id=member_id, team_id=team_id).first_or_404()
    data = request.json
    
    if 'name_en' in data:
        member.name_en = data['name_en'].strip().lower()
    if 'name_he' in data:
        member.name_he = data['name_he'].strip()
    if 'avatar_path' in data:
        member.avatar_path = data['avatar_path']
    
    db.session.commit()
    
    return jsonify({'success': True, 'member': member.to_dict()})

# Delete a team member
@app.route('/api/teams/<int:team_id>/members/<int:member_id>', methods=['DELETE'])
def api_delete_team_member(team_id, member_id):
    member = TeamMember.query.filter_by(id=member_id, team_id=team_id).first_or_404()
    db.session.delete(member)
    db.session.commit()
    
    return jsonify({'success': True})

# Upload avatar for a team member
@app.route('/api/teams/<int:team_id>/members/<int:member_id>/avatar', methods=['POST'])
def api_upload_avatar(team_id, member_id):
    member = TeamMember.query.filter_by(id=member_id, team_id=team_id).first_or_404()
    
    if 'avatar' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['avatar']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    # Validate file extension
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        return jsonify({'success': False, 'error': 'Invalid file type. Allowed: png, jpg, jpeg, gif'}), 400
    
    # Save file with member's name
    filename = f"{member.name_en}.{file.filename.rsplit('.', 1)[1].lower()}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # Update member's avatar path
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



# Initialize database tables
with app.app_context():
    db.create_all()


@app.route('/')
def index():
    project_filter = request.args.get('project')
    member_filter = request.args.get('member')
    team_filter = request.args.get('team')

    # Order by priority (high, medium, low, none)
    priority_order = case(
        (Task.priority == 'high', 1),
        (Task.priority == 'medium', 2),
        (Task.priority == 'low', 3),
        (Task.priority == 'none', 4),
    )
    query = Task.query.order_by(priority_order, Task.project)

    if project_filter:
        query = query.filter(Task.project == project_filter)
    if member_filter:
        query = query.filter(Task.members.contains(member_filter))
    if member_filter:
        query = query.filter(Task.members.contains(member_filter))
    # Team filtering is now handled client-side to prevent flickering
    # But we pass the active team ID to the template for initial state
    active_team_id = None
    if team_filter and team_filter.isdigit():
        active_team_id = int(team_filter)
        
    # if team_filter:
    #     query = query.filter(Task.team_id == team_filter)

    tasks = query.all()
    projects = [project[0] for project in db.session.query(distinct(Task.project)).all()]
    
    # Get all teams and members dynamically
    teams = Team.query.all()
    members = TeamMember.query.join(Team).order_by(Team.id, TeamMember.id).all()
    
    # Create a mapping of project names to team names
    project_teams = {}
    for project in projects:
        # Get the first task of this project to determine its team
        first_task = Task.query.filter_by(project=project).first()
        if first_task and first_task.team_id:
            team = Team.query.get(first_task.team_id)
            if team:
                project_teams[project] = team.name_he
            else:
                project_teams[project] = None
        else:
            project_teams[project] = None
    
            project_teams[project] = None
    
    return render_template('index.html', tasks=tasks, projects=projects, members=members, teams=teams, project_teams=project_teams, active_team_id=active_team_id)

@app.route('/add', methods=['POST'])
def add_task():
    project = request.form['project']
    task = request.form['task']
    members = ','.join(request.form.getlist('members'))
    status = request.form['status']
    priority = request.form['priority']
    notes = request.form.get('notes', '')
    new_task = Task(project=project, task=task, members=members, status=status, priority=priority, notes=notes)
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_task(id):
    task = Task.query.get_or_404(id)
    projects = [project[0] for project in db.session.query(distinct(Task.project)).all()]
    if request.method == 'POST':
        task.project = request.form['project']
        task.task = request.form['task']
        task.members = ','.join(request.form.getlist('members'))
        task.status = request.form['status']
        task.priority = request.form['priority']
        task.notes = request.form.get('notes', '')
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('edit.html', task=task, projects=projects)

@app.route('/delete/<int:id>')
def delete_task(id):
    task = Task.query.get_or_404(id)
    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/print')
def print_view():
    project_filter = request.args.get('project')
    member_filter = request.args.get('member')
    team_filter = request.args.get('team')

    priority_order = case(
        (Task.priority == 'high', 1),
        (Task.priority == 'medium', 2),
        (Task.priority == 'low', 3),
        (Task.priority == 'none', 4),
    )
    query = Task.query.order_by(priority_order, Task.project)

    if project_filter:
        query = query.filter(Task.project == project_filter)
    if member_filter:
        query = query.filter(Task.members.contains(member_filter))
    if team_filter:
        query = query.filter(Task.team_id == team_filter)

    tasks = query.all()
    projects = [project[0] for project in db.session.query(distinct(Task.project)).all()]
    
    # Get all teams and members dynamically
    teams = Team.query.all()
    members = TeamMember.query.all()
    
    return render_template('printable.html', tasks=tasks, projects=projects, members=members, teams=teams)


@app.route('/admin')
def admin():
    """Admin page for managing teams and members"""
    teams = Team.query.all()
    return render_template('admin.html', teams=teams)


if __name__ == '__main__':
    app.run(debug=True)
