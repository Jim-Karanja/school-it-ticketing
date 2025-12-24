"""
Remote Desktop Session Manager
Manages remote desktop sessions, security, and authentication
"""
import uuid
import time
import logging
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import secrets
import hashlib

logger = logging.getLogger(__name__)

class RemoteSession:
    def __init__(self, ticket_id, user_name, it_staff_name):
        self.session_id = str(uuid.uuid4())
        self.ticket_id = ticket_id
        self.user_name = user_name
        self.it_staff_name = it_staff_name
        self.created_at = datetime.utcnow()
        self.expires_at = self.created_at + timedelta(hours=2)  # 2-hour session limit
        self.status = 'pending'  # pending, active, closed
        self.user_token = self._generate_token()
        self.it_token = self._generate_token()
        self.connection_key = None
        self.user_connected = False
        self.it_connected = False
        self.last_activity = self.created_at
        
    def _generate_token(self):
        """Generate a secure token"""
        return secrets.token_urlsafe(32)
    
    def is_expired(self):
        """Check if session is expired"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """Check if session is valid"""
        return not self.is_expired() and self.status != 'closed'
    
    def activate(self):
        """Activate the session"""
        if self.is_valid():
            self.status = 'active'
            self.last_activity = datetime.utcnow()
            return True
        return False
    
    def close(self):
        """Close the session"""
        self.status = 'closed'
        self.user_connected = False
        self.it_connected = False
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()
    
    def to_dict(self):
        """Convert session to dictionary"""
        return {
            'session_id': self.session_id,
            'ticket_id': self.ticket_id,
            'user_name': self.user_name,
            'it_staff_name': self.it_staff_name,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'status': self.status,
            'user_connected': self.user_connected,
            'it_connected': self.it_connected,
            'last_activity': self.last_activity.isoformat()
        }

class SessionManager:
    def __init__(self):
        self.sessions = {}  # session_id -> RemoteSession
        self.ticket_sessions = {}  # ticket_id -> session_id
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        
        # Cleanup expired sessions every 5 minutes
        self._start_cleanup_timer()
        
        logger.info("Session manager initialized")
    
    def create_session(self, ticket_id, user_name, it_staff_name):
        """Create a new remote desktop session"""
        # Close any existing session for this ticket
        if ticket_id in self.ticket_sessions:
            old_session_id = self.ticket_sessions[ticket_id]
            self.close_session(old_session_id)
        
        session = RemoteSession(ticket_id, user_name, it_staff_name)
        self.sessions[session.session_id] = session
        self.ticket_sessions[ticket_id] = session.session_id
        
        logger.info(f"Created session {session.session_id} for ticket {ticket_id}")
        return session
    
    def get_session(self, session_id):
        """Get session by ID"""
        session = self.sessions.get(session_id)
        if session and session.is_valid():
            return session
        return None
    
    def get_session_by_ticket(self, ticket_id):
        """Get session by ticket ID"""
        session_id = self.ticket_sessions.get(ticket_id)
        if session_id:
            return self.get_session(session_id)
        return None
    
    def authenticate_user(self, session_id, token):
        """Authenticate user token"""
        session = self.get_session(session_id)
        if session and session.user_token == token:
            session.user_connected = True
            session.update_activity()
            logger.info(f"User authenticated for session {session_id}")
            return True
        return False
    
    def authenticate_it_staff(self, session_id, token):
        """Authenticate IT staff token"""
        session = self.get_session(session_id)
        if session and session.it_token == token:
            session.it_connected = True
            session.update_activity()
            logger.info(f"IT staff authenticated for session {session_id}")
            return True
        return False
    
    def activate_session(self, session_id):
        """Activate a session"""
        session = self.get_session(session_id)
        if session and session.user_connected and session.it_connected:
            session.activate()
            logger.info(f"Session {session_id} activated")
            return True
        return False
    
    def close_session(self, session_id):
        """Close a session"""
        session = self.sessions.get(session_id)
        if session:
            session.close()
            ticket_id = session.ticket_id
            
            # Clean up references
            if ticket_id in self.ticket_sessions:
                del self.ticket_sessions[ticket_id]
            
            logger.info(f"Session {session_id} closed")
            return True
        return False
    
    def disconnect_user(self, session_id):
        """Disconnect user from session"""
        session = self.get_session(session_id)
        if session:
            session.user_connected = False
            if session.status == 'active':
                session.status = 'pending'
            logger.info(f"User disconnected from session {session_id}")
    
    def disconnect_it_staff(self, session_id):
        """Disconnect IT staff from session"""
        session = self.get_session(session_id)
        if session:
            session.it_connected = False
            if session.status == 'active':
                session.status = 'pending'
            logger.info(f"IT staff disconnected from session {session_id}")
    
    def update_session_activity(self, session_id):
        """Update session activity"""
        session = self.get_session(session_id)
        if session:
            session.update_activity()
    
    def encrypt_data(self, data):
        """Encrypt sensitive data"""
        if isinstance(data, str):
            data = data.encode()
        return self.cipher.encrypt(data)
    
    def decrypt_data(self, encrypted_data):
        """Decrypt sensitive data"""
        return self.cipher.decrypt(encrypted_data).decode()
    
    def get_active_sessions(self):
        """Get all active sessions"""
        return [s for s in self.sessions.values() if s.status == 'active']
    
    def get_session_stats(self):
        """Get session statistics"""
        total = len(self.sessions)
        active = len([s for s in self.sessions.values() if s.status == 'active'])
        pending = len([s for s in self.sessions.values() if s.status == 'pending'])
        closed = len([s for s in self.sessions.values() if s.status == 'closed'])
        
        return {
            'total_sessions': total,
            'active_sessions': active,
            'pending_sessions': pending,
            'closed_sessions': closed
        }
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        expired_sessions = []
        for session_id, session in self.sessions.items():
            if session.is_expired():
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.close_session(session_id)
            del self.sessions[session_id]
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    def _start_cleanup_timer(self):
        """Start periodic cleanup of expired sessions"""
        import threading
        
        def cleanup_worker():
            while True:
                time.sleep(300)  # 5 minutes
                try:
                    self.cleanup_expired_sessions()
                except Exception as e:
                    logger.error(f"Cleanup error: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()

# Global session manager instance
session_manager = SessionManager()
