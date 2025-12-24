#!/usr/bin/env python3
"""
Database migration script to add remote desktop functionality
"""
import sqlite3
import os

def migrate_database():
    """Add remote desktop columns and fix missing columns in existing database"""
    db_paths = ['helpdesk.db', 'instance/helpdesk.db']
    
    database_found = False
    for db_path in db_paths:
        if os.path.exists(db_path):
            database_found = True
            migrate_single_database(db_path)
            break
    
    if not database_found:
        print("No existing database found. New database will be created when running the app.")
        return

def migrate_single_database(db_path):
    """Migrate a single database file"""
    print(f"Migrating database: {db_path}")
    print("Adding remote desktop functionality and missing columns...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check ticket table columns
        cursor.execute("PRAGMA table_info(ticket)")
        ticket_columns = [column[1] for column in cursor.fetchall()]
        
        if 'remote_session_id' not in ticket_columns:
            cursor.execute('ALTER TABLE ticket ADD COLUMN remote_session_id VARCHAR(100)')
            print("✅ Added remote_session_id column to ticket table")
        else:
            print("⚠️  remote_session_id column already exists in ticket table")
        
        if 'remote_session_status' not in ticket_columns:
            cursor.execute('ALTER TABLE ticket ADD COLUMN remote_session_status VARCHAR(20) DEFAULT "none"')
            print("✅ Added remote_session_status column to ticket table")
        else:
            print("⚠️  remote_session_status column already exists in ticket table")
        
        # Check it_staff table columns
        cursor.execute("PRAGMA table_info(it_staff)")
        staff_columns = [column[1] for column in cursor.fetchall()]
        
        if 'created_at' not in staff_columns:
            # SQLite requires a constant default value in ALTER TABLE
            from datetime import datetime
            current_timestamp = datetime.utcnow().isoformat()
            cursor.execute('ALTER TABLE it_staff ADD COLUMN created_at DATETIME')
            # Update all existing records with current timestamp
            cursor.execute('UPDATE it_staff SET created_at = ?', (current_timestamp,))
            print("✅ Added created_at column to it_staff table")
        else:
            print("⚠️  created_at column already exists in it_staff table")
        
        conn.commit()
        conn.close()
        
        print("🎉 Database migration completed successfully!")
        print("    Your existing tickets are preserved.")
        print("    New remote desktop features are now available.")
        print("    Authentication system columns are up to date.")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    migrate_database()
