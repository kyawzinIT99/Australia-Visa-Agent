"""
Check Google Drive Incoming Folder Status
This script checks what files are currently in the incoming folder
"""
import sys
sys.path.insert(0, '/Users/berry/Antigravity/Australia Agent copy')

from services.google_drive_service import GoogleDriveService
import os
from dotenv import load_dotenv

load_dotenv()

drive = GoogleDriveService()
incoming_folder_id = os.getenv("GOOGLE_DRIVE_INCOMING_FOLDER_ID")

print("\n" + "=" * 80)
print("Google Drive Incoming Folder Status")
print("=" * 80)

if not incoming_folder_id:
    print("❌ GOOGLE_DRIVE_INCOMING_FOLDER_ID not set in .env file!")
else:
    print(f"Incoming Folder ID: {incoming_folder_id}")
    
    try:
        files = drive.list_files_in_folder(incoming_folder_id)
        
        if not files:
            print("\n✅ No files pending in incoming folder")
        else:
            print(f"\n📋 Found {len(files)} file(s) in incoming folder:")
            for f in files:
                file_type = "📁 Folder" if f.get('mimeType') == 'application/vnd.google-apps.folder' else "📄 File"
                print(f"  {file_type}: {f['name']}")
                print(f"     ID: {f['id']}")
                print(f"     Created: {f.get('createdTime', 'Unknown')}")
                
    except Exception as e:
        print(f"\n❌ Error accessing Google Drive: {e}")

print("=" * 80)
