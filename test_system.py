#!/usr/bin/env python3
"""
Simple test script for the School IT Helpdesk system
"""
import os
import sys
import subprocess

def check_python_version():
    """Check if Python version is 3.10+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print(f"❌ Python {version.major}.{version.minor} detected. Python 3.10+ required.")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected.")
    return True

def check_files():
    """Check if all required files exist"""
    required_files = [
        'app.py',
        'requirements.txt',
        '.env.example',
        'templates/base.html',
        'templates/ticket_form.html',
        'templates/dashboard.html',
        'static/css/style.css',
        'static/js/main.js'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files present.")
    return True

def check_dependencies():
    """Check if all required packages can be imported"""
    try:
        import flask
        import flask_sqlalchemy
        import flask_mail
        import flask_wtf
        import wtforms
        print("✅ All required Python packages available.")
        return True
    except ImportError as e:
        print(f"❌ Missing Python package: {e}")
        print("   Run: pip install -r requirements.txt")
        return False

def create_test_env():
    """Create a basic .env file for testing if it doesn't exist"""
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write("""# Basic test configuration
SECRET_KEY=test-secret-key-change-in-production
FLASK_ENV=development
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=test@example.com
MAIL_PASSWORD=test-password
MAIL_DEFAULT_SENDER=helpdesk@school.edu
IT_EMAIL=it@school.edu
""")
        print("✅ Created basic .env file for testing.")
    else:
        print("✅ .env file exists.")

def test_flask_import():
    """Test if the Flask app can be imported without errors"""
    try:
        # Change to the script directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # Try to import the app
        from app import app, db, Ticket, ITStaff
        print("✅ Flask application imports successfully.")
        
        # Test database operations
        with app.app_context():
            db.create_all()
            
            # Check if admin user exists
            admin = ITStaff.query.filter_by(username='admin').first()
            if admin:
                print("✅ Default admin user exists in database.")
            else:
                print("⚠️  Default admin user not found in database.")
            
        return True
    except Exception as e:
        print(f"❌ Error importing Flask app: {e}")
        return False

def main():
    """Run all tests"""
    print("🎓 School IT Helpdesk System - Test Script")
    print("=" * 50)
    
    tests = [
        ("Python Version", check_python_version),
        ("Required Files", check_files),
        ("Python Dependencies", check_dependencies),
        ("Environment Configuration", create_test_env),
        ("Flask Application", test_flask_import)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nTesting {test_name}...")
        if test_func():
            passed += 1
        
    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The system appears to be set up correctly.")
        print("\nNext steps:")
        print("1. Configure your .env file with real email settings")
        print("2. Run the application: python app.py")
        print("3. Access the system at http://localhost:5000")
        print("4. Login to IT dashboard with admin/admin123")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please fix the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
