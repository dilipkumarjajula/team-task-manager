from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

database_url = os.environ.get("DATABASE_URL", "sqlite:///team_task_manager.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="Member")

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(30), default="Pending")
    due_date = db.Column(db.Date)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def current_user():
    if "user_id" not in session:
        return None
    return User.query.get(session["user_id"])

def login_required(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper

def admin_required(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user or user.role != "Admin":
            flash("Only Admin can access this page.", "danger")
            return redirect(url_for("dashboard"))
        return func(*args, **kwargs)
    return wrapper

@app.context_processor
def inject_user():
    return {"user": current_user()}

@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        role = request.form.get("role", "Member")

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("signup"))

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return redirect(url_for("signup"))

        new_user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role=role
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Signup successful. Please login.", "success")
        return redirect(url_for("login"))
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            flash("Login successful.", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()

    if user.role == "Admin":
        tasks = Task.query.all()
    else:
        tasks = Task.query.filter_by(assigned_to=user.id).all()

    total_tasks = len(tasks)
    pending = len([t for t in tasks if t.status == "Pending"])
    progress = len([t for t in tasks if t.status == "In Progress"])
    completed = len([t for t in tasks if t.status == "Completed"])
    overdue = len([t for t in tasks if t.due_date and t.due_date < date.today() and t.status != "Completed"])

    projects = Project.query.all()
    users = User.query.all()

    return render_template(
        "dashboard.html",
        tasks=tasks,
        projects=projects,
        users=users,
        total_tasks=total_tasks,
        pending=pending,
        progress=progress,
        completed=completed,
        overdue=overdue
    )

@app.route("/projects")
@login_required
def projects():
    return render_template("projects.html", projects=Project.query.all())

@app.route("/projects/create", methods=["GET", "POST"])
@login_required
@admin_required
def create_project():
    if request.method == "POST":
        name = request.form["name"].strip()
        description = request.form["description"].strip()

        if not name:
            flash("Project name is required.", "danger")
            return redirect(url_for("create_project"))

        project = Project(name=name, description=description, created_by=session["user_id"])
        db.session.add(project)
        db.session.commit()
        flash("Project created successfully.", "success")
        return redirect(url_for("projects"))

    return render_template("create_project.html")

@app.route("/tasks")
@login_required
def tasks():
    user = current_user()
    if user.role == "Admin":
        task_list = Task.query.order_by(Task.created_at.desc()).all()
    else:
        task_list = Task.query.filter_by(assigned_to=user.id).order_by(Task.created_at.desc()).all()
    return render_template("tasks.html", tasks=task_list, users=User.query.all(), projects=Project.query.all())

@app.route("/tasks/create", methods=["GET", "POST"])
@login_required
@admin_required
def create_task():
    users = User.query.all()
    projects = Project.query.all()

    if request.method == "POST":
        title = request.form["title"].strip()
        description = request.form["description"].strip()
        project_id = request.form["project_id"]
        assigned_to = request.form["assigned_to"]
        due_date_raw = request.form["due_date"]

        if not title or not project_id or not assigned_to:
            flash("Title, project and assigned user are required.", "danger")
            return redirect(url_for("create_task"))

        due_date = datetime.strptime(due_date_raw, "%Y-%m-%d").date() if due_date_raw else None

        task = Task(
            title=title,
            description=description,
            project_id=project_id,
            assigned_to=assigned_to,
            due_date=due_date,
            created_by=session["user_id"]
        )
        db.session.add(task)
        db.session.commit()
        flash("Task created and assigned successfully.", "success")
        return redirect(url_for("tasks"))

    return render_template("create_task.html", users=users, projects=projects)

@app.route("/tasks/<int:task_id>/status", methods=["POST"])
@login_required
def update_task_status(task_id):
    task = Task.query.get_or_404(task_id)
    user = current_user()

    if user.role != "Admin" and task.assigned_to != user.id:
        flash("You can update only your assigned tasks.", "danger")
        return redirect(url_for("tasks"))

    task.status = request.form["status"]
    db.session.commit()
    flash("Task status updated.", "success")
    return redirect(url_for("tasks"))

@app.route("/users")
@login_required
@admin_required
def users():
    return render_template("users.html", users=User.query.all())

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
