# School IT Helpdesk (Flask)

A web-based IT ticketing system designed for schools. Users (students, teachers, staff) can submit IT issues, and IT staff can manage tickets from a secure dashboard, including a workflow for remote desktop support using AnyDesk.

## Features

- Public-facing ticket submission form
- Fields: Name, Email, PC Location, Problem Description, Remote Access authorization
- Email notifications: submission confirmation, new ticket alert to IT, status updates
- IT staff dashboard (login required)
  - Sort and filter tickets
  - View ticket details and history
  - Update status (New, In Progress, On Hold, Closed)
  - Add timestamped notes
  - Remote desktop assistance workflow (manual via AnyDesk)
- SQLite database (upgradeable to PostgreSQL/MySQL)
- Clean, responsive UI (HTML/CSS/JS)

## Tech Stack

- Backend: Python, Flask
- Database: SQLite via SQLAlchemy
- Frontend: HTML, CSS, JavaScript
- Email: Flask-Mail (SMTP)
- Remote support: AnyDesk (manual workflow)

## Getting Started

### Prerequisites
- Python 3.10+
- pip

### Setup

1. Clone or create the project

2. Create a virtual environment and activate it
   - Windows (PowerShell):
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1

3. Install dependencies
   pip install -r requirements.txt

4. Configure environment variables
   - Copy .env.example to .env and fill in values (especially MAIL_* and IT_EMAIL)

5. Run the app
   python app.py
   - App runs at http://localhost:5000
   - Public form: http://localhost:5000/helpdesk
   - IT login: http://localhost:5000/login
   - Default IT user: admin / admin123 (change in production!)

## Configuration

Environment variables (from .env):
- SECRET_KEY: Flask secret key
- MAIL_SERVER, MAIL_PORT, MAIL_USE_TLS, MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER
- IT_EMAIL: distribution email for IT team

To use a different database, set SQLALCHEMY_DATABASE_URI accordingly (e.g., PostgreSQL URL).

## Email Notes
- For Gmail, use an App Password (2FA required). Enter it in MAIL_PASSWORD.
- In development without SMTP, emails fail silently with a console message; the app still works.

## Remote Desktop Workflow (AnyDesk)
- When a user authorizes remote access, tickets show clear indicators.
- The dashboard offers a Remote Connect page with step-by-step instructions.
- IT staff should initiate AnyDesk manually and request the user's AnyDesk ID.

## Security and Production Hardening
- Change default admin credentials immediately.
- Set a strong SECRET_KEY and store secrets securely.
- Run Flask behind a production server (e.g., gunicorn + reverse proxy like Nginx or IIS for Windows).
- Use a production database (PostgreSQL/MySQL) as needed.
- Enforce HTTPS, secure cookies, CSRF protection (Flask-WTF enabled).

## Project Structure

school-it-ticketing/
├─ app.py
├─ requirements.txt
├─ .env.example
├─ templates/
│  ├─ base.html
│  ├─ ticket_form.html
│  ├─ login.html
│  ├─ dashboard.html
│  ├─ ticket_detail.html
│  └─ email/
│     ├─ ticket_confirmation.html
│     ├─ new_ticket_notification.html
│     └─ status_update.html
└─ static/
   ├─ css/
   │  └─ style.css
   └─ js/
      └─ main.js

## Upgrading to PostgreSQL
- Install psycopg2-binary
  pip install psycopg2-binary
- Set SQLALCHEMY_DATABASE_URI in environment to your Postgres URL
- Initialize database
  In app startup, create_tables() handles initial creation.

## Windows Service (Optional)
- Use NSSM or a task scheduler to run the Flask app as a service on Windows.

## License
- Internal use for your school. Add your preferred license if distributing.

