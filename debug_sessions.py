#!/usr/bin/env python3
"""
Session Debug Utility
This script helps debug current session state and identify why auto-login might be happening.
"""

import os
import sqlite3
from datetime import datetime
import json

def check_database_sessions():
    """
    Check if there are any sessions stored in the database
    """
    print("🔍 Checking database for session-related data...")
    
    db_paths = ['helpdesk.db', 'instance/helpdesk.db']
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check all tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                print(f"   📋 Tables in {db_path}: {tables}")
                
                # Check IT staff table
                if 'it_staff' in tables:
                    cursor.execute("SELECT id, username, email FROM it_staff")
                    staff = cursor.fetchall()
                    print(f"   👥 IT Staff users: {staff}")
                
                # Look for any session-related tables or data
                for table in tables:
                    if 'session' in table.lower():
                        cursor.execute(f"SELECT * FROM {table}")
                        sessions = cursor.fetchall()
                        print(f"   🔑 Sessions in {table}: {sessions}")
                
                conn.close()
                
            except Exception as e:
                print(f"   ⚠️  Could not check database {db_path}: {e}")

def check_flask_session_files():
    """
    Check for Flask session files that might be persisting sessions
    """
    print("\n📁 Checking for Flask session files...")
    
    # Common Flask session directories
    session_locations = [
        'flask_session',
        'sessions', 
        'tmp/sessions',
        '/tmp/flask_sessions',
        os.path.join(os.path.expanduser('~'), '.flask_sessions'),
        'instance/sessions',
        '__pycache__'
    ]
    
    for location in session_locations:
        if os.path.exists(location):
            try:
                files = os.listdir(location)
                if files:
                    print(f"   📄 Found files in {location}: {files}")
                else:
                    print(f"   📁 Empty directory: {location}")
            except Exception as e:
                print(f"   ⚠️  Could not check {location}: {e}")
        else:
            print(f"   ❌ {location} does not exist")

def check_app_configuration():
    """
    Check application configuration that might affect sessions
    """
    print("\n⚙️  Checking application configuration...")
    
    app_file = 'app_with_remote.py'
    if os.path.exists(app_file):
        try:
            with open(app_file, 'r') as f:
                content = f.read()
            
            # Look for session configuration
            session_configs = [
                'SECRET_KEY',
                'session.permanent',
                'permanent_session_lifetime',
                'SESSION_TYPE'
            ]
            
            for config in session_configs:
                if config in content:
                    lines = [line.strip() for line in content.split('\n') if config in line]
                    for line in lines:
                        print(f"   🔧 {config}: {line}")
                        
        except Exception as e:
            print(f"   ⚠️  Could not check app configuration: {e}")

def check_browser_instructions():
    """
    Provide specific instructions for clearing browser sessions
    """
    print("\n🌐 Browser Session Clearing Instructions:")
    print("   To completely clear sessions, you MUST clear browser data:")
    print()
    print("   Chrome/Edge/Brave:")
    print("   1. Press F12 to open Developer Tools")
    print("   2. Go to Application tab")
    print("   3. Under Storage, click 'Clear storage'")
    print("   4. Make sure 'Cookies and other site data' is checked")
    print("   5. Click 'Clear site data'")
    print()
    print("   Alternative: Use Incognito/Private browsing mode to test")
    print("   This will ignore any existing cookies/sessions.")

def main():
    """
    Main debug function
    """
    print("🐛 IT Help Desk Session Debug Utility")
    print("=" * 50)
    
    check_database_sessions()
    check_flask_session_files()
    check_app_configuration()
    check_browser_instructions()
    
    print("\n" + "=" * 50)
    print("💡 Debugging Tips:")
    print("   1. Try accessing the app in incognito/private mode")
    print("   2. Check browser Developer Tools > Application > Storage")
    print("   3. Clear all browser data for localhost:5000")
    print("   4. Restart the Flask application after clearing sessions")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Debug failed: {e}")
