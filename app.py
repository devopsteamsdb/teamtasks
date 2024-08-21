from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import case

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project = db.Column(db.String(100), nullable=False)
    task = db.Column(db.String(200), nullable=False)
    members = db.Column(db.String(200), nullable=False)  # Store members as a comma-separated string
    status = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f'<Task {self.id}>'

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    status_order = case(
        (Task.status == 'Completed', 1),
        (Task.status == 'In Progress', 2),
        (Task.status == 'Frozen', 3),
        (Task.status == 'Not Started', 4),
    )

    tasks = Task.query.order_by(Task.project, status_order).all()
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add_task():
    project = request.form['project']
    task = request.form['task']
    members = ','.join(request.form.getlist('members'))  # Join selected members into a comma-separated string
    status = request.form['status']
    new_task = Task(project=project, task=task, members=members, status=status)
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_task(id):
    task = Task.query.get_or_404(id)
    if request.method == 'POST':
        task.project = request.form['project']
        task.task = request.form['task']
        task.members = ','.join(request.form.getlist('members'))  # Join selected members into a comma-separated string
        task.status = request.form['status']
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('edit.html', task=task)

@app.route('/delete/<int:id>')
def delete_task(id):
    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
