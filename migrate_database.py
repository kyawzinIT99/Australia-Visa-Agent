"""
Database Migration Script
Migrates existing database to add confidence tracking and notification features.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.database_service import engine, Base, SessionLocal, VisaApplication
from sqlalchemy import text

def migrate_database():
    """
    Migrates the database schema to add new columns for confidence tracking.
    Preserves existing data.
    """
    print("Starting database migration...")
    
    session = SessionLocal()
    
    try:
        # Check if we're using SQLite
        with engine.connect() as conn:
            # Add new columns to visa_applications if they don't exist
            new_columns = [
                ("confidence_score", "INTEGER"),
                ("field_confidence", "TEXT"),  # JSON stored as TEXT in SQLite
                ("ocr_metadata", "TEXT"),
                ("verification_status", "VARCHAR(50)", "'pending'"),
                ("verified_by", "VARCHAR(255)"),
                ("verified_at", "TIMESTAMP"),
                ("verification_notes", "TEXT"),
                ("version", "INTEGER", "1"),
                ("previous_version_id", "INTEGER")
            ]
            
            for column_info in new_columns:
                column_name = column_info[0]
                column_type = column_info[1]
                default_value = column_info[2] if len(column_info) > 2 else None
                
                try:
                    # Try to add the column
                    if default_value:
                        sql = f"ALTER TABLE visa_applications ADD COLUMN {column_name} {column_type} DEFAULT {default_value}"
                    else:
                        sql = f"ALTER TABLE visa_applications ADD COLUMN {column_name} {column_type}"
                    
                    conn.execute(text(sql))
                    conn.commit()
                    print(f"✓ Added column: {column_name}")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        print(f"  Column {column_name} already exists, skipping...")
                    else:
                        print(f"  Warning adding {column_name}: {e}")
        
        # Create new tables (notifications, notification_preferences)
        print("\nCreating new tables...")
        Base.metadata.create_all(bind=engine)
        print("✓ All tables created/verified")
        
        # Set default values for existing records
        print("\nUpdating existing records with default values...")
        existing_apps = session.query(VisaApplication).filter(
            VisaApplication.verification_status.is_(None)
        ).all()
        
        for app in existing_apps:
            app.verification_status = 'pending'
            app.version = 1
            # Set a default confidence score if not set
            if app.confidence_score is None:
                app.confidence_score = 75  # Assume medium confidence for existing data
        
        session.commit()
        print(f"✓ Updated {len(existing_apps)} existing records")
        
        print("\n✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration for Trust Enhancement Features")
    print("=" * 60)
    print()
    
    success = migrate_database()
    
    if success:
        print("\nYou can now use the new confidence tracking and notification features!")
    else:
        print("\nMigration failed. Please check the errors above.")
    
    sys.exit(0 if success else 1)
