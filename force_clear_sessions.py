#!/usr/bin/env python3
"""
Force Clear Sessions Utility
This script aggressively clears all possible session storage and forces fresh login.
"""

import os
import sys
import shutil
from datetime import datetime

def clear_all_session_storage():
    """
    Aggressively clear all possible session storage locations
    """
    print("🧹 Force clearing ALL session storage...")
    
    # Session directories to clear
    session_dirs = [
        'flask_session',
        'sessions', 
        'tmp',
        '__pycache__',
        'instance/flask_session',
        '.sessions'
    ]
    
    cleared_count = 0
    
    for session_dir in session_dirs:
        if os.path.exists(session_dir):
            try:
                if session_dir == '__pycache__':
                    # Only clear Flask-related cache files
                    for filename in os.listdir(session_dir):
                        if 'flask' in filename.lower() or 'session' in filename.lower():
                            file_path = os.path.join(session_dir, filename)
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                                cleared_count += 1
                else:
                    # Clear entire directory
                    shutil.rmtree(session_dir)
                    os.makedirs(session_dir)
                    cleared_count += 1
                    
                print(f"   ✅ Cleared {session_dir}")
                
            except Exception as e:
                print(f"   ⚠️  Could not clear {session_dir}: {e}")
    
    print(f"   📊 Total items cleared: {cleared_count}")

def reset_flask_secret_key():
    """
    Generate a new secret key to invalidate any existing sessions
    """
    print("\n🔑 Resetting Flask secret key to invalidate sessions...")
    
    try:
        import secrets
        new_secret = secrets.token_hex(32)
        
        # Create a temporary environment file
        env_file = '.env'
        with open(env_file, 'w') as f:
            f.write(f"SECRET_KEY={new_secret}\n")
            f.write(f"# Generated on {datetime.now().isoformat()}\n")
        
        print(f"   ✅ New secret key generated and saved to {env_file}")
        print("   ⚠️  This will invalidate ALL existing sessions")
        
        # Update the app to use the new key
        app_file = 'app_with_remote.py'
        if os.path.exists(app_file):
            with open(app_file, 'r') as f:
                content = f.read()
            
            # Add environment file loading if not present
            if 'from dotenv import load_dotenv' not in content:
                lines = content.split('\n')
                # Add after the imports
                for i, line in enumerate(lines):
                    if line.startswith('import os'):
                        lines.insert(i + 1, 'from dotenv import load_dotenv')
                        lines.insert(i + 2, 'load_dotenv()')
                        break
                
                with open(f'{app_file}.new', 'w') as f:
                    f.write('\n'.join(lines))
                
                print(f"   💡 Updated {app_file} to use environment variables")
                print(f"   📝 Backup saved as {app_file}.new")
        
    except ImportError:
        print("   ⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
    except Exception as e:
        print(f"   ❌ Could not reset secret key: {e}")

def create_session_clear_route():
    """
    Add a debug route to the Flask app for clearing sessions
    """
    print("\n🔧 Adding session clear route to Flask app...")
    
    debug_route_code = '''
# DEBUG: Session clearing route (remove in production)
@app.route('/debug/clear_session')
def debug_clear_session():
    \"\"\"Debug route to clear current session\"\"\"
    session.clear()
    return jsonify({
        'status': 'success', 
        'message': 'Session cleared',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/debug/session_info')
def debug_session_info():
    \"\"\"Debug route to check session information\"\"\"
    return jsonify({
        'session_data': dict(session),
        'is_logged_in': AuthenticationManager.is_logged_in(),
        'current_user': AuthenticationManager.get_current_user(),
        'timestamp': datetime.utcnow().isoformat()
    })
'''
    
    try:
        app_file = 'app_with_remote.py'
        if os.path.exists(app_file):
            with open(app_file, 'r') as f:
                content = f.read()
            
            if '/debug/clear_session' not in content:
                # Add the debug routes before the main execution block
                lines = content.split('\n')
                for i in range(len(lines) - 1, -1, -1):
                    if lines[i].strip().startswith('if __name__'):
                        lines.insert(i, debug_route_code)
                        break
                
                with open(app_file, 'w') as f:
                    f.write('\n'.join(lines))
                
                print("   ✅ Added debug routes to Flask app")
                print("   🔍 Access /debug/clear_session to clear session")
                print("   🔍 Access /debug/session_info to check session status")
            else:
                print("   ℹ️  Debug routes already exist")
                
    except Exception as e:
        print(f"   ❌ Could not add debug routes: {e}")

def main():
    """
    Force clear all sessions and reset authentication
    """
    print("💥 IT Help Desk FORCE Session Clear Utility")
    print("=" * 60)
    print("⚠️  This will aggressively clear ALL session data!")
    print()
    
    # Confirm with user
    confirm = input("Are you sure you want to proceed? (yes/N): ").lower().strip()
    if confirm not in ['yes', 'y']:
        print("❌ Operation cancelled.")
        return
    
    clear_all_session_storage()
    reset_flask_secret_key()
    create_session_clear_route()
    
    print("\n" + "=" * 60)
    print("✅ FORCE session clear completed!")
    print()
    print("🔄 Next steps:")
    print("   1. Restart the Flask application")
    print("   2. Clear ALL browser data (Ctrl+Shift+Delete)")
    print("   3. Or use Incognito/Private mode")
    print("   4. Visit http://127.0.0.1:5000/debug/session_info")
    print("   5. Should show empty session data")
    print()
    print("🚨 IMPORTANT: Remove debug routes before production!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Force clear failed: {e}")
        sys.exit(1)
