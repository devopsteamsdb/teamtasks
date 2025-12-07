from flask import Flask, render_template, redirect, url_for, request, jsonify, send_from_directory
from sqlalchemy import case, distinct, or_, and_
from werkzeug.utils import secure_filename
import os
import time

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads/avatars'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size
# Import models and initialize db
from models import db, Team, TeamMember, Task, SpecialDay
db.init_app(app)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Route to serve uploaded files
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded files from the uploads directory"""
    return send_from_directory('uploads', filename)

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
    
    # Calendar fields (v3)
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    estimated_hours = data.get('estimated_hours')
    
    # Parse date strings to date objects if provided
    from datetime import datetime
    if start_date:
        try:
            start_date = datetime.fromisoformat(start_date).date()
        except (ValueError, AttributeError):
            start_date = None
    if end_date:
        try:
            end_date = datetime.fromisoformat(end_date).date()
        except (ValueError, AttributeError):
            end_date = None
            
    new_task = Task(
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
        task.is_archived = data['is_archived']
    
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



# ============ CALENDAR API (v3) ============

@app.route('/api/calendar/week', methods=['GET'])
def api_calendar_week():
    """Get tasks for a specific week"""
    from datetime import datetime, timedelta
    
    # Get date parameter (defaults to today)
    date_str = request.args.get('date')
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
    week_end = week_start + timedelta(days=6)
    
    # Query tasks that fall within this week
    query = Task.query.filter(
        or_(
            Task.start_date.between(week_start, week_end),
            Task.end_date.between(week_start, week_end),
            and_(Task.start_date <= week_start, Task.end_date >= week_end)
        )
    )
    
    if team_id:
        query = query.filter(Task.team_id == team_id)
    
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
    if not month:
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
    
    if team_id:
        query = query.filter(Task.team_id == team_id)
    
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
    
    # Get team members
    if team_id:
        members = TeamMember.query.filter_by(team_id=team_id).all()
    else:
        members = TeamMember.query.all()
    
    # Get tasks for the date range
    tasks = Task.query.filter(
        or_(
            Task.start_date.between(start_date, end_date),
            Task.end_date.between(start_date, end_date),
            and_(Task.start_date <= start_date, Task.end_date >= end_date)
        )
    ).all()
    
    # Build workload data structure
    workload_data = []
    for member in members:
        member_tasks = [
            task.to_dict() for task in tasks 
            if member.name_en in task.members.split(',')
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
    
    task = Task.query.get_or_404(id)
    data = request.json
    
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
    day = SpecialDay.query.get_or_404(id)
    db.session.delete(day)
    db.session.commit()
    return jsonify({'success': True})


# Initialize database tables
with app.app_context():
    db.create_all()


# ============ BACKUP & RESTORE API ============

@app.route('/api/backup/<string:table_name>', methods=['GET'])
def api_backup_table(table_name):
    """Export table data as JSON"""
    models = {
        'tasks': Task,
        'teams': Team,
        'members': TeamMember,
        'special_days': SpecialDay
    }
    
    if table_name == 'all':
        full_data = {}
        total_count = 0
        for name, model in models.items():
            records = [r.to_dict() for r in model.query.all()]
            full_data[name] = records
            total_count += len(records)
            
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
    """Import table data from JSON with validation"""
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file part'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'}), 400
        
    try:
        import json
        content = json.load(file)
        
        # Determine strictness and mode
        is_full_backup = (table_name == 'all')
        
        # Check metadata
        if isinstance(content, dict) and 'table' in content:
            source_table = content['table']
            # If user wants to restore 'all' but file is single table -> Error or Allow? 
            # Error is safer.
            if is_full_backup and source_table != 'all':
                 return jsonify({'success': False, 'error': 'Cannot restore single table backup to "All System"'}), 400
            
            # If user wants single table, but file is 'all' -> Error?
            if not is_full_backup and source_table == 'all':
                 return jsonify({'success': False, 'error': 'Cannot restore "All System" backup to single table. Select "All System" to restore.'}), 400
                 
            # Mismatch single to single
            if not is_full_backup and source_table != table_name:
                 return jsonify({'success': False, 'error': f'Table mismatch: File is "{source_table}", expected "{table_name}"'}), 400
            
            data = content.get('data')
        else:
            # Raw list?
            if is_full_backup:
                return jsonify({'success': False, 'error': 'Invalid backup format for full restore'}), 400
            data = content if isinstance(content, list) else []

        if not data:
             return jsonify({'success': True, 'message': 'No data to restore', 'count': 0})

        # Helper to restore a single list of items to a table
        def restore_single_table_data(t_name, t_data):
            models = {
                'tasks': Task,
                'teams': Team,
                'members': TeamMember,
                'special_days': SpecialDay
            }
            if t_name not in models: return 0
            if not t_data: return 0
            
            model = models[t_name]
            
            # Validation (check first record)
            required_fields = {
                'teams': ['name_en', 'name_he'],
                'members': ['name_en', 'name_he', 'team_id'],
                'tasks': ['project', 'task', 'status'],
                'special_days': ['date', 'name']
            }
            if t_name in required_fields:
                sample = t_data[0]
                for f in required_fields[t_name]:
                    if f not in sample:
                        raise ValueError(f'Missing field "{f}" in {t_name} data')

            valid_keys = [c.key for c in model.__table__.columns]
            from datetime import datetime
            
            count = 0
            for item in t_data:
                clean_item = {k: v for k, v in item.items() if k in valid_keys}
                
                # Date processing & Fixes
                if t_name == 'tasks':
                    # Convert members list to string if needed
                    if 'members' in clean_item and isinstance(clean_item['members'], list):
                        clean_item['members'] = ','.join(clean_item['members'])
                        
                    for date_field in ['start_date', 'end_date']:
                        if clean_item.get(date_field) and isinstance(clean_item[date_field], str):
                             try:
                                clean_item[date_field] = datetime.fromisoformat(clean_item[date_field]).date()
                             except ValueError:
                                clean_item[date_field] = None
                                
                if t_name == 'special_days':
                     if clean_item.get('date') and isinstance(clean_item['date'], str):
                         try:
                            clean_item['date'] = datetime.fromisoformat(clean_item['date']).date()
                         except ValueError:
                            pass

                # Use merge to handle both insert (with specific ID) and update
                record = model(**clean_item)
                db.session.merge(record)
                count += 1
            return count

        restored_counts = {}
        
        if is_full_backup:
            # WIPE DATA for full restore to ensure exact state match
            # Order matters: Dependencies first (Tasks depend on nothing? wait.)
            # Tasks -> TeamID (nullable). Members -> TeamID. 
            # Delete order: Tasks, SpecialDays, TeamMembers, Teams
            try:
                Task.query.delete()
                SpecialDay.query.delete()
                TeamMember.query.delete()
                Team.query.delete()
                db.session.flush() # Ensure deletes happen before inserts
            except Exception as e:
                db.session.rollback()
                return jsonify({'success': False, 'error': f'Failed to clear existing data: {str(e)}'}), 500

            # Restore Order: Teams -> Members -> Tasks -> SpecialDays
            restore_order = ['teams', 'members', 'tasks', 'special_days']
            for t_name in restore_order:
                if t_name in data:
                    cnt = restore_single_table_data(t_name, data[t_name])
                    restored_counts[t_name] = cnt
        else:
            # For single table, we generally APPEND/UPDATE. 
            # Wiping single table is risky without cascading, so we stick to additive.
            cnt = restore_single_table_data(table_name, data)
            restored_counts[table_name] = cnt
            
        db.session.commit()
        return jsonify({'success': True, 'counts': restored_counts})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

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
    query = Task.query.filter(Task.is_archived == False).order_by(priority_order, Task.project)

    if project_filter:
        query = query.filter(Task.project == project_filter)
    if member_filter:
        query = query.filter(Task.members.contains(member_filter))
    # Team filtering is now handled client-side to prevent flickering
    # But we pass the active team ID to the template for initial state
    active_team_id = None
    if team_filter and team_filter.isdigit():
        active_team_id = int(team_filter)

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
    
    return render_template('index.html', tasks=tasks, projects=projects, members=members, teams=teams, project_teams=project_teams, active_team_id=active_team_id)







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
    query = Task.query.filter(Task.is_archived == False).order_by(priority_order, Task.project)

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
