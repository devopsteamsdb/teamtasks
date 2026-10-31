from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Association table for Many-to-Many relationship between TeamMember and Team
member_teams = db.Table('member_teams',
    db.Column('member_id', db.Integer, db.ForeignKey('team_member.id', ondelete='CASCADE'), primary_key=True),
    db.Column('team_id', db.Integer, db.ForeignKey('team.id', ondelete='CASCADE'), primary_key=True)
)


class Team(db.Model):
    """Team model - represents a team in the organization"""
    id = db.Column(db.Integer, primary_key=True)
    name_en = db.Column(db.String(100), nullable=False, unique=True)  # English name for code
    name_he = db.Column(db.String(100), nullable=False)  # Hebrew name for UI
    
    # Relationships
    members = db.relationship('TeamMember', secondary=member_teams, lazy='subquery',
                              backref=db.backref('teams', lazy='subquery'))
    tasks = db.relationship('Task', backref='team', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name_en': self.name_en,
            'name_he': self.name_he,
            'members': [member.to_dict() for member in self.members]
        }
    
    def __repr__(self):
        return f'<Team {self.name_en}>'


class TeamMember(db.Model):
    """TeamMember model - represents a member of one or more teams"""
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)
    name_en = db.Column(db.String(100), nullable=False)  # English name for code (lowercase)
    name_he = db.Column(db.String(100), nullable=False)  # Hebrew name for UI
    avatar_path = db.Column(db.String(200), default='default.png')  # Relative path to avatar image
    
    @property
    def team(self):
        return self.teams[0] if self.teams else (db.session.get(Team, self.team_id) if self.team_id else None)

    def to_dict(self):
        team_ids = [t.id for t in self.teams] if self.teams else ([self.team_id] if self.team_id else [])
        team_names = [t.name_he for t in self.teams] if self.teams else []
        return {
            'id': self.id,
            'team_id': team_ids[0] if team_ids else self.team_id,
            'team_ids': team_ids,
            'name_en': self.name_en,
            'name_he': self.name_he,
            'avatar_path': self.avatar_path,
            'team_name': ', '.join(team_names) if team_names else '',
            'team_names': team_names,
            'teams': [{'id': t.id, 'name_en': t.name_en, 'name_he': t.name_he} for t in self.teams] if self.teams else []
        }
    
    def __repr__(self):
        return f'<TeamMember {self.name_en}>'


# Association table for Many-to-Many relationship between Project and Team
project_teams = db.Table('project_teams',
    db.Column('project_id', db.Integer, db.ForeignKey('project.id', ondelete='CASCADE'), primary_key=True),
    db.Column('team_id', db.Integer, db.ForeignKey('team.id', ondelete='CASCADE'), primary_key=True)
)


class Project(db.Model):
    """Project model - represents a project associated with one or more teams"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    is_archived = db.Column(db.Boolean, default=False, nullable=False)
    
    # Relationships
    teams = db.relationship('Team', secondary=project_teams, lazy='subquery',
                            backref=db.backref('projects', lazy=True))
    tasks = db.relationship('Task', backref='project_rel', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'is_archived': self.is_archived,
            'teams': [{'id': t.id, 'name_en': t.name_en, 'name_he': t.name_he} for t in self.teams],
            'team_ids': [t.id for t in self.teams]
        }
    
    def __repr__(self):
        return f'<Project {self.name}>'


class Task(db.Model):
    """Task model - represents a task in a project"""
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id', ondelete='SET NULL'), nullable=True)
    project = db.Column(db.String(100), nullable=False)
    task = db.Column(db.String(200), nullable=False)
    members = db.Column(db.String(200), nullable=False, default='')  # Comma-separated member names
    status = db.Column(db.String(50), nullable=False, default='status-notstarted')
    priority = db.Column(db.String(10), nullable=False, default='none')  # 'high', 'medium', 'low', 'none'
    notes = db.Column(db.Text, nullable=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)  # Nullable for migration
    
    # Calendar-related fields (v3)
    start_date = db.Column(db.Date, nullable=True)  # When task is scheduled to start
    end_date = db.Column(db.Date, nullable=True)  # When task is scheduled to end
    estimated_hours = db.Column(db.Float, nullable=True)  # Estimated work hours for workload calculations
    is_archived = db.Column(db.Boolean, default=False, nullable=False)  # Archive status

    # Relationships for subtasks and comments
    comments = db.relationship('TaskComment', backref=db.backref('task_rel', lazy=True), cascade='all, delete-orphan', lazy='subquery', order_by='TaskComment.created_at.asc()')
    subtasks = db.relationship('Subtask', backref=db.backref('task_rel', lazy=True), cascade='all, delete-orphan', lazy='subquery', order_by='Subtask.order.asc(), Subtask.id.asc()')

    @property
    def name(self):
        return self.task

    @name.setter
    def name(self, val):
        self.task = val

    @property
    def title(self):
        return self.task

    @title.setter
    def title(self, val):
        self.task = val
    
    def to_dict(self):
        subtasks_list = [s.to_dict() for s in self.subtasks] if self.subtasks else []
        comments_list = [c.to_dict() for c in self.comments] if self.comments else []
        completed_count = sum(1 for s in subtasks_list if s.get('is_completed'))
        return {
            'id': self.id,
            'project_id': self.project_id,
            'project': self.project,
            'task': self.task,
            'name': self.task,
            'title': self.task,
            'members': self.members.split(',') if self.members else [],
            'status': self.status,
            'priority': self.priority,
            'notes': self.notes,
            'team_id': self.team_id,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'estimated_hours': self.estimated_hours,
            'is_archived': self.is_archived,
            'subtasks': subtasks_list,
            'subtasks_count': len(subtasks_list),
            'subtasks_completed_count': completed_count,
            'comments': comments_list,
            'comments_count': len(comments_list)
        }
    
    def __repr__(self):
        return f'<Task {self.id}>'


class TaskComment(db.Model):
    """TaskComment model - represents discussion and work notes on a task"""
    __tablename__ = 'task_comment'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id', ondelete='CASCADE'), nullable=False)
    author_name = db.Column(db.String(100), nullable=False)
    author_avatar = db.Column(db.String(200), default='default.png')
    member_id = db.Column(db.Integer, db.ForeignKey('team_member.id', ondelete='SET NULL'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    member = db.relationship('TeamMember', backref=db.backref('comments', lazy=True))

    def to_dict(self):
        avatar = self.author_avatar
        if not avatar or avatar == 'default.png':
            if self.member and self.member.avatar_path:
                avatar = self.member.avatar_path
            else:
                avatar = 'default.png'
        return {
            'id': self.id,
            'task_id': self.task_id,
            'author_name': self.author_name,
            'author_avatar': avatar,
            'member_id': self.member_id,
            'content': self.content,
            'comment': self.content,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M') if self.created_at else None,
            'created_at_iso': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<TaskComment {self.id} on Task {self.task_id}>'


class Subtask(db.Model):
    """Subtask model - represents checklist items for a task"""
    __tablename__ = 'subtask'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    is_completed = db.Column(db.Boolean, default=False, nullable=False)
    order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'title': self.title,
            'is_completed': self.is_completed,
            'order': self.order,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M') if self.created_at else None
        }

    def __repr__(self):
        return f'<Subtask {self.id} on Task {self.task_id}: {self.title}>'


class SpecialDay(db.Model):
    """SpecialDay model - represents holidays and non-working days"""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), default='holiday')  # 'holiday', 'company_event', 'other'
    color = db.Column(db.String(20), nullable=True)  # Hex color code

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'name': self.name,
            'type': self.type,
            'color': self.color
        }

    def __repr__(self):
        return f'<SpecialDay {self.name} {self.date}>'
