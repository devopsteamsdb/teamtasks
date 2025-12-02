from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import case, distinct

# Initialize Flask app and DB at the very top
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# API endpoint to add a task (AJAX)
@app.route('/api/tasks', methods=['POST'])
def api_add_task():
    data = request.json
    project = data.get('project')
    task = data.get('task')
    members = ','.join(data.get('members', []))
    status = data.get('status')
    priority = data.get('priority', 'none')
    notes = data.get('notes', '')
    new_task = Task(project=project, task=task, members=members, status=status, priority=priority, notes=notes)
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
    db.session.commit()
    return jsonify({'success': True})

# API endpoint to delete a task (AJAX)
@app.route('/api/tasks/<int:id>', methods=['DELETE'])
def api_delete_task(id):
    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    return jsonify({'success': True})

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project = db.Column(db.String(100), nullable=False)
    task = db.Column(db.String(200), nullable=False)
    members = db.Column(db.String(200), nullable=False)  # Store members as a comma-separated string
    status = db.Column(db.String(50), nullable=False)
    priority = db.Column(db.String(10), nullable=False, default='none')  # 'high', 'medium', 'low', 'none'
    notes = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Task {self.id}>'

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    project_filter = request.args.get('project')
    member_filter = request.args.get('member')

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

    tasks = query.all()
    projects = [project[0] for project in db.session.query(distinct(Task.project)).all()]
    members = ['Elad', 'Guy', 'Itamar', 'Noam', 'David']
    return render_template('index.html', tasks=tasks, projects=projects, members=members)

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
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
