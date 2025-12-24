"""
Authentication and Session Management Utilities
This module provides secure session handling and authentication abstractions.
"""
import os
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import session, request, redirect, url_for, flash, current_app
from werkzeug.security import generate_password_hash, check_password_hash


class AuthenticationManager:
    """
    Handles authentication, session management, and security for the IT Help Desk system.
    """
    
    # Session timeout duration (2 hours)
    SESSION_TIMEOUT = timedelta(hours=2)
    
    @staticmethod
    def generate_secure_session_token():
        """Generate a secure session token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def is_logged_in():
        """Check if user is currently logged in with valid session"""
        if 'logged_in' not in session:
            return False
            
        if 'username' not in session:
            return False
            
        # Check session timeout
        if 'login_time' in session:
            login_time = datetime.fromisoformat(session['login_time'])
            if datetime.utcnow() - login_time > AuthenticationManager.SESSION_TIMEOUT:
                AuthenticationManager.logout()
                return False
        
        return True
        
    @staticmethod
    def is_user_logged_in():
        """Alias for is_logged_in to match expected interface"""
        return AuthenticationManager.is_logged_in()
    
    @staticmethod
    def login_user(user):
        """
        Log in a user and create secure session
        
        Args:
            user: ITStaff user object
        """
        session.clear()  # Clear any existing session data
        session['logged_in'] = True
        session['username'] = user.username
        session['user_id'] = user.id
        session['login_time'] = datetime.utcnow().isoformat()
        session['session_token'] = AuthenticationManager.generate_secure_session_token()
        session.permanent = True
        
        # Set session lifetime
        current_app.permanent_session_lifetime = AuthenticationManager.SESSION_TIMEOUT
        
    @staticmethod
    def logout():
        """Log out current user and clear session"""
        session.clear()
        
    @staticmethod
    def logout_user():
        """Alias for logout to match expected interface"""
        return AuthenticationManager.logout()
        
    @staticmethod
    def get_current_user():
        """Get current logged in user info"""
        if AuthenticationManager.is_logged_in():
            return {
                'username': session.get('username'),
                'user_id': session.get('user_id'),
                'login_time': session.get('login_time'),
                'session_token': session.get('session_token')
            }
        return None
    
    @staticmethod
    def get_current_user_id():
        """Get current logged in user ID"""
        user = AuthenticationManager.get_current_user()
        return user.get('user_id') if user else None
    
    @staticmethod
    def require_authentication():
        """Decorator factory for routes that require authentication"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not AuthenticationManager.is_logged_in():
                    flash('Your session has expired. Please log in again.', 'warning')
                    return redirect(url_for('login'))
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    @staticmethod
    def update_activity():
        """Update last activity time for current session"""
        if AuthenticationManager.is_logged_in():
            session['last_activity'] = datetime.utcnow().isoformat()


class PasswordManager:
    """
    Handles password hashing, validation, and security policies
    """
    
    # Minimum password requirements
    MIN_LENGTH = 8
    
    @staticmethod
    def hash_password(password):
        """Generate secure password hash"""
        return generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
    
    @staticmethod
    def verify_password(password, hash_value):
        """Verify password against hash"""
        return check_password_hash(hash_value, password)
    
    @staticmethod
    def validate_password_strength(password):
        """
        Validate password meets security requirements
        
        Returns:
            tuple: (is_valid: bool, errors: list)
        """
        errors = []
        
        if len(password) < PasswordManager.MIN_LENGTH:
            errors.append(f'Password must be at least {PasswordManager.MIN_LENGTH} characters long')
            
        if not any(c.isupper() for c in password):
            errors.append('Password must contain at least one uppercase letter')
            
        if not any(c.islower() for c in password):
            errors.append('Password must contain at least one lowercase letter')
            
        if not any(c.isdigit() for c in password):
            errors.append('Password must contain at least one number')
            
        return len(errors) == 0, errors
    
    @staticmethod
    def generate_temporary_password():
        """Generate a secure temporary password"""
        import string
        import random
        
        # Generate a password with mix of characters
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(random.choice(chars) for _ in range(12))
        
        # Ensure it meets requirements
        if not any(c.isupper() for c in password):
            password = password[:-1] + random.choice(string.ascii_uppercase)
        if not any(c.islower() for c in password):
            password = password[:-2] + random.choice(string.ascii_lowercase) + password[-1]
        if not any(c.isdigit() for c in password):
            password = password[:-3] + random.choice(string.digits) + password[-2:]
            
        return password


class SecurityUtils:
    """
    Additional security utilities for the application
    """
    
    @staticmethod
    def get_client_ip():
        """Get client IP address, accounting for proxies"""
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        return request.remote_addr
    
    @staticmethod
    def log_security_event(event_type, details=None):
        """Log security-related events"""
        import logging
        
        logger = logging.getLogger('security')
        user_info = AuthenticationManager.get_current_user()
        
        log_data = {
            'event': event_type,
            'ip': SecurityUtils.get_client_ip(),
            'user_agent': request.headers.get('User-Agent', 'Unknown'),
            'timestamp': datetime.utcnow().isoformat(),
            'user': user_info.get('username') if user_info else 'Anonymous'
        }
        
        if details:
            log_data.update(details)
            
        logger.info(f"Security Event: {log_data}")
    
    @staticmethod
    def validate_session_security():
        """Validate current session meets security requirements"""
        if not AuthenticationManager.is_logged_in():
            return False
            
        # Check for session hijacking indicators
        user_agent = request.headers.get('User-Agent', '')
        if 'session_user_agent' in session:
            if session['session_user_agent'] != user_agent:
                SecurityUtils.log_security_event('session_hijack_attempt', {
                    'expected_agent': session['session_user_agent'],
                    'actual_agent': user_agent
                })
                AuthenticationManager.logout()
                return False
        else:
            session['session_user_agent'] = user_agent
            
        return True


# Backward compatibility - provide the original decorator
def login_required(f):
    """
    Enhanced login required decorator with improved security
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Validate session security
        if not SecurityUtils.validate_session_security():
            flash('Session security validation failed. Please log in again.', 'error')
            return redirect(url_for('login'))
            
        if not AuthenticationManager.is_logged_in():
            flash('Please log in to access this page.', 'info')
            return redirect(url_for('login'))
            
        # Update activity tracking
        AuthenticationManager.update_activity()
        
        return f(*args, **kwargs)
    return decorated_function


# Export commonly used functions
__all__ = [
    'AuthenticationManager',
    'PasswordManager', 
    'SecurityUtils',
    'login_required'
]
