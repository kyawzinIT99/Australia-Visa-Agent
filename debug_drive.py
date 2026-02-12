import os
import sys
from dotenv import load_dotenv
import json

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from services.google_drive_service import GoogleDriveService

def test_drive_connection():
    load_dotenv()
    
    print("🔍 Testing Google Drive Connection...")
    
    incoming_folder_id = os.getenv("GOOGLE_DRIVE_INCOMING_FOLDER_ID")
    print(f"📂 Incoming Folder ID: {incoming_folder_id}")
    
    if not incoming_folder_id:
        print("❌ Error: GOOGLE_DRIVE_INCOMING_FOLDER_ID not set in .env")
        return

    try:
        drive_service = GoogleDriveService()
        print("✅ GoogleDriveService initialized successfully.")
        
        print(f"Listing files in folder: {incoming_folder_id}")
        files = drive_service.list_files_in_folder(incoming_folder_id)
        
        print(f"Found {len(files)} files/folders.")
        
        if not files:
            print("⚠️ Folder appears empty.")
        
        for f in files:
            print(f"- [ID: {f['id']}] {f['name']} ({f['mimeType']})")
            
    except Exception as e:
        print(f"❌ Error during Drive operations: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_drive_connection()
