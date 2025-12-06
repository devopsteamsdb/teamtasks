from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Team(db.Model):
    """Team model - represents a team in the organization"""
    id = db.Column(db.Integer, primary_key=True)
    name_en = db.Column(db.String(100), nullable=False, unique=True)  # English name for code
    name_he = db.Column(db.String(100), nullable=False)  # Hebrew name for UI
    
    # Relationships
    members = db.relationship('TeamMember', backref='team', lazy=True, cascade='all, delete-orphan')
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
    """TeamMember model - represents a member of a team"""
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    name_en = db.Column(db.String(100), nullable=False)  # English name for code (lowercase)
    name_he = db.Column(db.String(100), nullable=False)  # Hebrew name for UI
    avatar_path = db.Column(db.String(200), default='default.png')  # Relative path to avatar image
    
    def to_dict(self):
        return {
            'id': self.id,
            'team_id': self.team_id,
            'name_en': self.name_en,
            'name_he': self.name_he,
            'avatar_path': self.avatar_path
        }
    
    def __repr__(self):
        return f'<TeamMember {self.name_en}>'


class Task(db.Model):
    """Task model - represents a task in a project"""
    id = db.Column(db.Integer, primary_key=True)
    project = db.Column(db.String(100), nullable=False)
    task = db.Column(db.String(200), nullable=False)
    members = db.Column(db.String(200), nullable=False)  # Comma-separated member names
    status = db.Column(db.String(50), nullable=False)
    priority = db.Column(db.String(10), nullable=False, default='none')  # 'high', 'medium', 'low', 'none'
    notes = db.Column(db.Text, nullable=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)  # Nullable for migration
    
    # Calendar-related fields (v3)
    start_date = db.Column(db.Date, nullable=True)  # When task is scheduled to start
    end_date = db.Column(db.Date, nullable=True)  # When task is scheduled to end
    estimated_hours = db.Column(db.Float, nullable=True)  # Estimated work hours for workload calculations
    is_archived = db.Column(db.Boolean, default=False, nullable=False)  # Archive status
    
    def to_dict(self):
        return {
            'id': self.id,
            'project': self.project,
            'task': self.task,
            'members': self.members.split(',') if self.members else [],
            'status': self.status,
            'priority': self.priority,
            'notes': self.notes,
            'team_id': self.team_id,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'estimated_hours': self.estimated_hours,
            'is_archived': self.is_archived
        }
    
    def __repr__(self):
        return f'<Task {self.id}>'


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
