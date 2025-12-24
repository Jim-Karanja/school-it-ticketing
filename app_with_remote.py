from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_wtf import FlaskForm
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from wtforms import StringField, TextAreaField, BooleanField, SelectField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()
import logging
from werkzeug.security import generate_password_hash, check_password_hash

# Import authentication utilities
from auth_utils import AuthenticationManager, PasswordManager, SecurityUtils, login_required

# Import remote desktop components
from remote_desktop.screen_capture import screen_capturer
from remote_desktop.input_handler import input_handler
from remote_desktop.session_manager import session_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///helpdesk.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', '587'))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'helpdesk@school.edu')
app.config['IT_EMAIL'] = os.environ.get('IT_EMAIL', 'it@school.edu')

db = SQLAlchemy(app)
mail = Mail(app)
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

# Database Models (same as before)
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
    
    # Remote desktop session tracking
    remote_session_id = db.Column(db.String(100), nullable=True)
    remote_session_status = db.Column(db.String(20), default='none')  # none, pending, active, closed
    
    def __repr__(self):
        return f'<Ticket {self.id}: {self.user_name}>'

class ITStaff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    
    def set_password(self, password):
        self.password_hash = PasswordManager.hash_password(password)
    
    def check_password(self, password):
        return PasswordManager.verify_password(password, self.password_hash)

# Forms (same as before)
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
        logger.error(f"Email sending failed: {e}")

# Login required decorator now imported from auth_utils

# Original Routes (same as before)
@app.route('/')
@app.route('/helpdesk')
def index():
    form = TicketForm()
    return render_template('ticket_form.html', form=form)

@app.route('/submit_ticket', methods=['POST'])
def submit_ticket():
    form = TicketForm()
    if form.validate_on_submit():
        ticket = Ticket(
            user_name=form.user_name.data,
            user_email=form.user_email.data,
            pc_location=form.pc_location.data,
            problem_description=form.problem_description.data,
            remote_access_requested=form.remote_access_requested.data
        )
        
        db.session.add(ticket)
        db.session.commit()
        
        # Send emails (same as before)
        send_email(
            subject=f'IT Ticket #{ticket.id} Submitted Successfully',
            recipient=ticket.user_email,
            template='email/ticket_confirmation.html',
            ticket=ticket
        )
        
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
    # If already logged in, redirect to dashboard
    if AuthenticationManager.is_logged_in():
        return redirect(url_for('dashboard'))
        
    form = LoginForm()
    if form.validate_on_submit():
        staff = ITStaff.query.filter_by(username=form.username.data).first()
        if staff and staff.check_password(form.password.data):
            # Use AuthenticationManager for secure login
            AuthenticationManager.login_user(staff)
            
            # Log security event
            SecurityUtils.log_security_event('user_login', {
                'username': staff.username,
                'success': True
            })
            
            flash('Logged in successfully!', 'success')
            
            # Redirect to requested page or dashboard
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            # Log failed login attempt
            SecurityUtils.log_security_event('login_failed', {
                'username': form.username.data,
                'success': False
            })
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    # Log security event before clearing session
    user_info = AuthenticationManager.get_current_user()
    if user_info:
        SecurityUtils.log_security_event('user_logout', {
            'username': user_info['username']
        })
    
    AuthenticationManager.logout()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    status_filter = request.args.get('status', 'all')
    sort_by = request.args.get('sort', 'created_at')
    
    query = Ticket.query
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if sort_by == 'status':
        tickets = query.order_by(Ticket.status, Ticket.created_at.desc()).all()
    elif sort_by == 'location':
        tickets = query.order_by(Ticket.pc_location, Ticket.created_at.desc()).all()
    else:
        tickets = query.order_by(Ticket.created_at.desc()).all()
    
    return render_template('dashboard.html', tickets=tickets, status_filter=status_filter, sort_by=sort_by)

@app.route('/ticket/<int:ticket_id>')
@login_required
def view_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    form = UpdateTicketForm(obj=ticket)
    
    # Get remote session info
    remote_session = None
    if ticket.remote_session_id:
        remote_session = session_manager.get_session(ticket.remote_session_id)
    
    return render_template('ticket_detail.html', ticket=ticket, form=form, remote_session=remote_session)

@app.route('/update_ticket/<int:ticket_id>', methods=['POST'])
@login_required
def update_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    form = UpdateTicketForm()
    
    if form.validate_on_submit():
        old_status = ticket.status
        ticket.status = form.status.data
        
        if form.notes.data.strip():
            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            new_note = f"[{timestamp} - {session['username']}]: {form.notes.data.strip()}"
            if ticket.notes:
                ticket.notes += "\n\n" + new_note
            else:
                ticket.notes = new_note
        
        ticket.updated_at = datetime.utcnow()
        db.session.commit()
        
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

# NEW REMOTE DESKTOP ROUTES
@app.route('/start_remote_session/<int:ticket_id>')
@login_required
def start_remote_session(ticket_id):
    """Start a remote desktop session for a ticket"""
    ticket = Ticket.query.get_or_404(ticket_id)
    
    if not ticket.remote_access_requested:
        flash('Remote access was not requested for this ticket.', 'error')
        return redirect(url_for('view_ticket', ticket_id=ticket_id))
    
    # Create remote session
    remote_session = session_manager.create_session(
        ticket_id=ticket.id,
        user_name=ticket.user_name,
        it_staff_name=session['username']
    )
    
    # Update ticket
    ticket.remote_session_id = remote_session.session_id
    ticket.remote_session_status = 'pending'
    db.session.commit()
    
    flash('Remote session started! Share the connection details with the user.', 'success')
    return redirect(url_for('remote_session_setup', session_id=remote_session.session_id))

@app.route('/remote_session/<session_id>/setup')
@login_required
def remote_session_setup(session_id):
    """Show remote session setup page for IT staff"""
    remote_session = session_manager.get_session(session_id)
    if not remote_session:
        flash('Remote session not found or expired.', 'error')
        return redirect(url_for('dashboard'))
    
    ticket = Ticket.query.get(remote_session.ticket_id)
    return render_template('remote_session_setup.html', session=remote_session, ticket=ticket)

@app.route('/remote_client/<session_id>/<token>')
def remote_client(session_id, token):
    """Client-side remote desktop page (for end user)"""
    remote_session = session_manager.get_session(session_id)
    if not remote_session:
        return render_template('error.html', message='Session not found or expired.')
    
    # Verify user token
    if not session_manager.authenticate_user(session_id, token):
        return render_template('error.html', message='Invalid session token.')
    
    return render_template('remote_client.html', session=remote_session)

@app.route('/remote_viewer/<session_id>/<token>')
@login_required
def remote_viewer(session_id, token):
    """IT staff remote desktop viewer"""
    remote_session = session_manager.get_session(session_id)
    if not remote_session:
        flash('Session not found or expired.', 'error')
        return redirect(url_for('dashboard'))
    
    # Verify IT staff token
    if not session_manager.authenticate_it_staff(session_id, token):
        flash('Invalid session token.', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('remote_viewer.html', session=remote_session)

# SOCKETIO EVENTS FOR REAL-TIME COMMUNICATION
@socketio.on('connect')
def handle_connect():
    logger.info(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f'Client disconnected: {request.sid}')
    
    # Clean up any screen capture connections
    screen_capturer.remove_client(request.sid)
    
    # Revoke any input authorizations
    input_handler.revoke_session(request.sid)

@socketio.on('join_session')
def handle_join_session(data):
    """Join a remote desktop session"""
    session_id = data.get('session_id')
    token = data.get('token')
    user_type = data.get('type')  # 'user' or 'it_staff'
    
    remote_session = session_manager.get_session(session_id)
    if not remote_session:
        emit('error', {'message': 'Session not found'})
        return
    
    # Authenticate and join
    if user_type == 'user' and session_manager.authenticate_user(session_id, token):
        join_room(f'session_{session_id}')
        emit('session_joined', {'type': 'user', 'session': remote_session.to_dict()})
        emit('user_connected', {'session_id': session_id}, room=f'session_{session_id}')
        
    elif user_type == 'it_staff' and session_manager.authenticate_it_staff(session_id, token):
        join_room(f'session_{session_id}')
        emit('session_joined', {'type': 'it_staff', 'session': remote_session.to_dict()})
        emit('it_staff_connected', {'session_id': session_id}, room=f'session_{session_id}')
        
        # Authorize input handling for IT staff
        input_handler.authorize_session(request.sid)
        
        # Start screen capture for this session
        screen_capturer.add_client(request.sid)
        
    else:
        emit('error', {'message': 'Authentication failed'})

@socketio.on('request_screen_frame')
def handle_request_screen_frame():
    """IT staff requests screen frame"""
    frame_data = screen_capturer.get_frame()
    if frame_data:
        emit('screen_frame', frame_data)

@socketio.on('mouse_move')
def handle_mouse_move(data):
    """Handle remote mouse movement"""
    session_id = data.get('session_id')
    x = data.get('x')
    y = data.get('y')
    screen_width = data.get('screen_width')
    screen_height = data.get('screen_height')
    
    success = input_handler.handle_mouse_move(request.sid, x, y, screen_width, screen_height)
    if success:
        session_manager.update_session_activity(session_id)

@socketio.on('mouse_click')
def handle_mouse_click(data):
    """Handle remote mouse clicks"""
    session_id = data.get('session_id')
    x = data.get('x')
    y = data.get('y')
    screen_width = data.get('screen_width')
    screen_height = data.get('screen_height')
    button = data.get('button', 'left')
    click_type = data.get('click_type', 'single')
    
    success = input_handler.handle_mouse_click(request.sid, x, y, screen_width, screen_height, button, click_type)
    if success:
        session_manager.update_session_activity(session_id)

@socketio.on('mouse_scroll')
def handle_mouse_scroll(data):
    """Handle remote mouse scroll"""
    session_id = data.get('session_id')
    x = data.get('x')
    y = data.get('y')
    screen_width = data.get('screen_width')
    screen_height = data.get('screen_height')
    delta = data.get('delta')
    
    success = input_handler.handle_mouse_scroll(request.sid, x, y, screen_width, screen_height, delta)
    if success:
        session_manager.update_session_activity(session_id)

@socketio.on('key_press')
def handle_key_press(data):
    """Handle remote key press"""
    session_id = data.get('session_id')
    key = data.get('key')
    action = data.get('action', 'press')
    
    success = input_handler.handle_key_press(request.sid, key, action)
    if success:
        session_manager.update_session_activity(session_id)

@socketio.on('key_combination')
def handle_key_combination(data):
    """Handle remote key combinations"""
    session_id = data.get('session_id')
    keys = data.get('keys', [])
    
    success = input_handler.handle_key_combination(request.sid, keys)
    if success:
        session_manager.update_session_activity(session_id)

@socketio.on('text_input')
def handle_text_input(data):
    """Handle remote text input"""
    session_id = data.get('session_id')
    text = data.get('text', '')
    
    success = input_handler.handle_text_input(request.sid, text)
    if success:
        session_manager.update_session_activity(session_id)

# API ENDPOINTS FOR STATUS AND STATS
@app.route('/api/remote_sessions')
@login_required
def api_remote_sessions():
    """Get remote session statistics"""
    return jsonify(session_manager.get_session_stats())

@app.route('/api/screen_stats')
@login_required
def api_screen_stats():
    """Get screen capture statistics"""
    return jsonify(screen_capturer.get_stats())

@app.route('/api/input_stats')
@login_required
def api_input_stats():
    """Get input handler statistics"""
    return jsonify(input_handler.get_stats())

# Initialize database
def create_tables():
    with app.app_context():
        db.create_all()
        
        if not ITStaff.query.first():
            admin = ITStaff(username='admin', email='admin@school.edu')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            logger.info("Default admin user created: username='admin', password='admin123'")


# DEBUG: Session clearing route (remove in production)
@app.route('/debug/clear_session')
def debug_clear_session():
    """Debug route to clear current session"""
    session.clear()
    return jsonify({
        'status': 'success', 
        'message': 'Session cleared',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/debug/session_info')
def debug_session_info():
    """Debug route to check session information"""
    return jsonify({
        'session_data': dict(session),
        'is_logged_in': AuthenticationManager.is_logged_in(),
        'current_user': AuthenticationManager.get_current_user(),
        'timestamp': datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    create_tables()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
