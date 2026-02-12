import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.database_service import SessionLocal, VisaApplication

def cleanup_duplicates():
    db = SessionLocal()
    try:
        # Find the specific old file to remove
        app_to_remove = db.query(VisaApplication).filter(VisaApplication.file_name == '842.pdf').first()
        
        if app_to_remove:
            print(f"Deleting older file entry: {app_to_remove.file_name} (ID: {app_to_remove.id}, Status: {app_to_remove.status})")
            db.delete(app_to_remove)
            db.commit()
            print("Cleanup complete.")
        else:
            print("File '842.pdf' not found.")

    except Exception as e:
        print(f"Error during cleanup: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_duplicates()
