Team Task Manager - Full Stack Assignment

Overview:
This is a full-stack web application where users can create projects, assign tasks, and track progress with role-based access.

Tech Stack:
Frontend: HTML, CSS, Bootstrap
Backend: Python Flask
Database: SQLite locally / PostgreSQL on Railway
Deployment: Railway

Features:
1. User signup and login
2. Role-based access: Admin and Member
3. Admin can create projects
4. Admin can create and assign tasks to members
5. Members can view assigned tasks
6. Admin and assigned members can update task status
7. Dashboard shows total tasks, pending tasks, in-progress tasks, completed tasks, and overdue tasks
8. Proper validations and database relationships

How to Run Locally:
1. Install Python 3.11
2. Open terminal inside project folder
3. Run: pip install -r requirements.txt
4. Run: python app.py
5. Open browser: http://127.0.0.1:5000

Demo Login:
Create one Admin account from signup page by selecting Admin role.
Create one Member account from signup page by selecting Member role.
Login as Admin to create projects and tasks.
Login as Member to view and update assigned tasks.

Railway Deployment:
1. Push this project to GitHub
2. Open Railway
3. Create New Project
4. Select Deploy from GitHub Repo
5. Add PostgreSQL database plugin if needed
6. Set environment variable SECRET_KEY
7. Deploy the app
8. Copy live Railway URL and submit it

Project Structure:
app.py - Main Flask application
templates/ - HTML templates
static/style.css - CSS styling
requirements.txt - Python dependencies
Procfile - Railway start command
runtime.txt - Python version
README.txt - Project documentation

Author:
Divya Sree Nadigottu
