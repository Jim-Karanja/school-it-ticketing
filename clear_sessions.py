#!/usr/bin/env python3
"""
Session Cleanup Utility
This script clears all existing sessions and forces users to log in fresh.
Run this script when you want to ensure no one is automatically logged in.
"""

import os
import sys
import sqlite3
from datetime import datetime

def clear_flask_sessions():
    """
    Clear Flask sessions by removing session files or database entries
    """
    print("🧹 Clearing Flask sessions...")
    
    # If using file-based sessions (Flask default)
    session_dirs = [
        'flask_session',
        'sessions', 
        'tmp/sessions',
        '/tmp/flask_sessions'
    ]
    
    sessions_cleared = 0
    for session_dir in session_dirs:
        if os.path.exists(session_dir):
            try:
                for filename in os.listdir(session_dir):
                    file_path = os.path.join(session_dir, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        sessions_cleared += 1
                print(f"   ✅ Cleared {sessions_cleared} session files from {session_dir}")
            except Exception as e:
                print(f"   ⚠️  Could not clear sessions from {session_dir}: {e}")
    
    if sessions_cleared == 0:
        print("   ℹ️  No file-based sessions found to clear")

def clear_database_sessions():
    """
    Clear any session data stored in the database
    Note: This is for custom session storage, not typically used by Flask
    """
    print("\n🗄️  Checking database for session data...")
    
    db_paths = ['helpdesk.db', 'instance/helpdesk.db']
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check if there's a sessions table (custom implementation)
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='sessions'
                """)
                
                if cursor.fetchone():
                    cursor.execute("DELETE FROM sessions")
                    deleted_count = cursor.rowcount
                    conn.commit()
                    print(f"   ✅ Cleared {deleted_count} database sessions from {db_path}")
                else:
                    print(f"   ℹ️  No sessions table found in {db_path}")
                    
                conn.close()
                
            except Exception as e:
                print(f"   ⚠️  Could not access database {db_path}: {e}")

def clear_browser_cache_instructions():
    """
    Provide instructions for users to clear browser cache/cookies
    """
    print("""
🌐 Browser Cache Cleanup Instructions:

To ensure complete session cleanup, users should also clear their browser data:

Chrome/Edge:
1. Press Ctrl+Shift+Delete
2. Select "Cookies and other site data" and "Cached images and files"
3. Choose "All time" and click "Clear data"

Firefox:
1. Press Ctrl+Shift+Delete  
2. Select "Cookies", "Cache", and "Site Data"
3. Choose "Everything" and click "Clear Now"

Safari:
1. Safari menu > Clear History...
2. Choose "all history" and click "Clear History"

This will ensure users need to log in fresh on their next visit.
""")

def reset_admin_password():
    """
    Optionally reset the admin password for security
    """
    response = input("\n🔐 Would you like to reset the admin password? (y/N): ").lower().strip()
    
    if response == 'y' or response == 'yes':
        from auth_utils import PasswordManager
        
        # Generate a new secure password
        new_password = PasswordManager.generate_temporary_password()
        
        db_paths = ['helpdesk.db', 'instance/helpdesk.db']
        
        for db_path in db_paths:
            if os.path.exists(db_path):
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    # Hash the new password
                    password_hash = PasswordManager.hash_password(new_password)
                    
                    # Update admin user
                    cursor.execute("""
                        UPDATE it_staff 
                        SET password_hash = ? 
                        WHERE username = 'admin'
                    """, (password_hash,))
                    
                    if cursor.rowcount > 0:
                        conn.commit()
                        print(f"   ✅ Admin password reset in {db_path}")
                        print(f"   🔑 New admin password: {new_password}")
                        print("   ⚠️  Please save this password securely and change it after first login!")
                    else:
                        print(f"   ⚠️  No admin user found in {db_path}")
                    
                    conn.close()
                    break
                    
                except Exception as e:
                    print(f"   ⚠️  Could not reset password in {db_path}: {e}")

def main():
    """
    Main cleanup function
    """
    print("🚀 IT Help Desk Session Cleanup Utility")
    print("=" * 50)
    
    # Clear Flask sessions
    clear_flask_sessions()
    
    # Clear database sessions
    clear_database_sessions()
    
    # Show browser cleanup instructions
    clear_browser_cache_instructions()
    
    # Optionally reset admin password
    reset_admin_password()
    
    print("\n✅ Session cleanup completed!")
    print("🎯 All users will now need to log in fresh when accessing the application.")
    print("\n🚀 You can now start the application with: python app_with_remote.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Session cleanup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during cleanup: {e}")
        sys.exit(1)
