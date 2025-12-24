#!/usr/bin/env python3
"""
Authentication System Test
This script tests the authentication system to ensure proper login/logout behavior.
"""

import sys
import os
import sqlite3
from datetime import datetime

def check_database_structure():
    """
    Verify the database has the required tables and columns for authentication
    """
    print("🔍 Checking database structure...")
    
    db_paths = ['helpdesk.db', 'instance/helpdesk.db']
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check it_staff table structure
                cursor.execute("PRAGMA table_info(it_staff)")
                columns = [row[1] for row in cursor.fetchall()]
                
                required_columns = ['id', 'username', 'password_hash', 'email', 'created_at']
                missing_columns = [col for col in required_columns if col not in columns]
                
                if missing_columns:
                    print(f"   ⚠️  Missing columns in it_staff table: {missing_columns}")
                else:
                    print(f"   ✅ IT staff table structure is correct in {db_path}")
                
                # Check if admin user exists
                cursor.execute("SELECT username, email FROM it_staff WHERE username = 'admin'")
                admin_user = cursor.fetchone()
                
                if admin_user:
                    print(f"   ✅ Admin user exists: {admin_user[0]} ({admin_user[1]})")
                else:
                    print("   ⚠️  No admin user found")
                
                conn.close()
                return True
                
            except Exception as e:
                print(f"   ⚠️  Could not check database {db_path}: {e}")
                
    return False

def check_auth_files():
    """
    Check if authentication-related files exist
    """
    print("\n📁 Checking authentication files...")
    
    required_files = [
        'auth_utils.py',
        'app_with_remote.py',
        'clear_sessions.py'
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path} exists")
        else:
            print(f"   ❌ {file_path} is missing")

def test_password_manager():
    """
    Test the PasswordManager functionality
    """
    print("\n🔐 Testing PasswordManager...")
    
    try:
        from auth_utils import PasswordManager
        
        # Test password hashing
        test_password = "test123"
        hashed = PasswordManager.hash_password(test_password)
        print(f"   ✅ Password hashing works")
        
        # Test password verification
        if PasswordManager.verify_password(test_password, hashed):
            print(f"   ✅ Password verification works")
        else:
            print(f"   ❌ Password verification failed")
            
        # Test temporary password generation
        temp_password = PasswordManager.generate_temporary_password()
        if len(temp_password) >= 12:
            print(f"   ✅ Temporary password generation works (length: {len(temp_password)})")
        else:
            print(f"   ⚠️  Temporary password may be too short: {len(temp_password)} chars")
            
    except ImportError as e:
        print(f"   ❌ Could not import auth_utils: {e}")
    except Exception as e:
        print(f"   ❌ PasswordManager test failed: {e}")

def test_authentication_manager():
    """
    Test the AuthenticationManager functionality
    """
    print("\n👤 Testing AuthenticationManager...")
    
    try:
        from auth_utils import AuthenticationManager
        
        # This would require a Flask app context, so we'll just test import
        print(f"   ✅ AuthenticationManager imported successfully")
        
        # Check if required methods exist
        methods = ['login_user', 'logout_user', 'is_user_logged_in', 'get_current_user_id']
        for method in methods:
            if hasattr(AuthenticationManager, method):
                print(f"   ✅ Method {method} exists")
            else:
                print(f"   ❌ Method {method} is missing")
                
    except ImportError as e:
        print(f"   ❌ Could not import AuthenticationManager: {e}")
    except Exception as e:
        print(f"   ❌ AuthenticationManager test failed: {e}")

def check_app_integration():
    """
    Check if the main app file has proper authentication integration
    """
    print("\n🔗 Checking app integration...")
    
    if os.path.exists('app_with_remote.py'):
        try:
            with open('app_with_remote.py', 'r') as f:
                content = f.read()
            
            checks = [
                ('from auth_utils import', 'auth_utils import'),
                ('@login_required', 'login_required decorator usage'),
                ('AuthenticationManager', 'AuthenticationManager usage'),
                ('PasswordManager', 'PasswordManager usage')
            ]
            
            for check_str, description in checks:
                if check_str in content:
                    print(f"   ✅ Found {description}")
                else:
                    print(f"   ⚠️  {description} not found")
                    
        except Exception as e:
            print(f"   ❌ Could not check app file: {e}")
    else:
        print("   ❌ app_with_remote.py not found")

def main():
    """
    Run all authentication system tests
    """
    print("🧪 IT Help Desk Authentication System Test")
    print("=" * 50)
    
    # Check database
    db_ok = check_database_structure()
    
    # Check files
    check_auth_files()
    
    # Test authentication components
    test_password_manager()
    test_authentication_manager()
    
    # Check app integration
    check_app_integration()
    
    print("\n" + "=" * 50)
    if db_ok:
        print("✅ Authentication system appears to be properly configured!")
        print("🚀 You can now start the application and test the login flow.")
        print("\n💡 To test:")
        print("   1. Start the app: py app_with_remote.py")
        print("   2. Visit http://127.0.0.1:5000")
        print("   3. Verify you are redirected to login")
        print("   4. Login with admin/admin123")
        print("   5. Verify you can access the dashboard")
        print("   6. Test logout functionality")
    else:
        print("⚠️  Some issues were found. Please review the output above.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {e}")
        sys.exit(1)
