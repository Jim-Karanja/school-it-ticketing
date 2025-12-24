from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///helpdesk.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration (configure these environment variables)
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', '587'))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'helpdesk@school.edu')
app.config['IT_EMAIL'] = os.environ.get('IT_EMAIL', 'it@school.edu')

db = SQLAlchemy(app)
mail = Mail(app)

# Database Models
class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100), nullable=False)
    user_email = db.Column(db.String(100), nullable=False)
    pc_location = db.Column(db.String(100), nullable=False)
    problem_description = db.Column(db.Text, nullable=False)
    remote_access_requested = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='New')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text, default='')
    
    def __repr__(self):
        return f'<Ticket {self.id}: {self.user_name}>'

class ITStaff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Forms
class TicketForm(FlaskForm):
    user_name = StringField('Your Name', validators=[DataRequired(), Length(min=2, max=100)])
    user_email = StringField('Email Address', validators=[DataRequired(), Email()])
    pc_location = StringField('PC Location (e.g., Room 101)', validators=[DataRequired(), Length(min=2, max=100)])
    problem_description = TextAreaField('Problem Description', validators=[DataRequired(), Length(min=10)])
    remote_access_requested = BooleanField('I authorize remote desktop access to help resolve this issue')
    submit = SubmitField('Submit Ticket')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class UpdateTicketForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('New', 'New'),
        ('In Progress', 'In Progress'), 
        ('On Hold', 'On Hold'),
        ('Closed', 'Closed')
    ])
    notes = TextAreaField('Add Notes')
    submit = SubmitField('Update Ticket')

# Helper functions
def send_email(subject, recipient, template, **kwargs):
    try:
        msg = Message(subject=subject, recipients=[recipient])
        msg.html = render_template(template, **kwargs)
        mail.send(msg)
    except Exception as e:
        print(f"Email sending failed: {e}")

def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Please log in to access the dashboard.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Routes
@app.route('/')
@app.route('/helpdesk')
def index():
    form = TicketForm()
    return render_template('ticket_form.html', form=form)

@app.route('/submit_ticket', methods=['POST'])
def submit_ticket():
    form = TicketForm()
    if form.validate_on_submit():
        # Create new ticket
        ticket = Ticket(
            user_name=form.user_name.data,
            user_email=form.user_email.data,
            pc_location=form.pc_location.data,
            problem_description=form.problem_description.data,
            remote_access_requested=form.remote_access_requested.data
        )
        
        db.session.add(ticket)
        db.session.commit()
        
        # Send confirmation email to user
        send_email(
            subject=f'IT Ticket #{ticket.id} Submitted Successfully',
            recipient=ticket.user_email,
            template='email/ticket_confirmation.html',
            ticket=ticket
        )
        
        # Send notification email to IT staff
        send_email(
            subject=f'New IT Ticket #{ticket.id} - {ticket.pc_location}',
            recipient=app.config['IT_EMAIL'],
            template='email/new_ticket_notification.html',
            ticket=ticket
        )
        
        flash(f'Your ticket #{ticket.id} has been submitted successfully! You will receive an email confirmation shortly.', 'success')
        return redirect(url_for('index'))
    
    return render_template('ticket_form.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        staff = ITStaff.query.filter_by(username=form.username.data).first()
        if staff and staff.check_password(form.password.data):
            session['logged_in'] = True
            session['username'] = staff.username
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get filter parameters
    status_filter = request.args.get('status', 'all')
    sort_by = request.args.get('sort', 'created_at')
    
    # Build query
    query = Ticket.query
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    # Apply sorting
    if sort_by == 'status':
        tickets = query.order_by(Ticket.status, Ticket.created_at.desc()).all()
    elif sort_by == 'location':
        tickets = query.order_by(Ticket.pc_location, Ticket.created_at.desc()).all()
    else:  # default to created_at
        tickets = query.order_by(Ticket.created_at.desc()).all()
    
    return render_template('dashboard.html', tickets=tickets, status_filter=status_filter, sort_by=sort_by)

@app.route('/ticket/<int:ticket_id>')
@login_required
def view_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    form = UpdateTicketForm(obj=ticket)
    return render_template('ticket_detail.html', ticket=ticket, form=form)

@app.route('/update_ticket/<int:ticket_id>', methods=['POST'])
@login_required
def update_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    form = UpdateTicketForm()
    
    if form.validate_on_submit():
        old_status = ticket.status
        ticket.status = form.status.data
        
        # Add notes if provided
        if form.notes.data.strip():
            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            new_note = f"[{timestamp} - {session['username']}]: {form.notes.data.strip()}"
            if ticket.notes:
                ticket.notes += "\n\n" + new_note
            else:
                ticket.notes = new_note
        
        ticket.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Send status update email to user if status changed
        if old_status != ticket.status:
            send_email(
                subject=f'IT Ticket #{ticket.id} Status Update',
                recipient=ticket.user_email,
                template='email/status_update.html',
                ticket=ticket,
                old_status=old_status
            )
        
        flash('Ticket updated successfully!', 'success')
    
    return redirect(url_for('view_ticket', ticket_id=ticket_id))

@app.route('/remote_connect/<int:ticket_id>')
@login_required
def remote_connect(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if not ticket.remote_access_requested:
        flash('Remote access was not requested for this ticket.', 'warning')
        return redirect(url_for('view_ticket', ticket_id=ticket_id))
    
    return render_template('remote_connect.html', ticket=ticket)

# Initialize database and create default IT staff user
def create_tables():
    with app.app_context():
        db.create_all()
        
        # Create default IT admin user if none exists
        if not ITStaff.query.first():
            admin = ITStaff(username='admin', email='admin@school.edu')
            admin.set_password('admin123')  # Change this in production!
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created: username='admin', password='admin123'")

if __name__ == '__main__':
    # Initialize database on first run
    create_tables()
    app.run(debug=True, host='0.0.0.0', port=5000)
