import os
from dotenv import load_dotenv
from services.google_drive_service import GoogleDriveService

def share_all_folders():
    load_dotenv()
    drive = GoogleDriveService()
    
    # Emails to share with
    emails = [
        os.getenv("SENDER_EMAIL"),
        os.getenv("ADMIN_EMAIL")
    ]
    
    # Folder IDs from .env
    folder_ids = [
        os.getenv("GOOGLE_DRIVE_INCOMING_FOLDER_ID"),
        os.getenv("GOOGLE_DRIVE_PROCESSING_FOLDER_ID"),
        os.getenv("GOOGLE_DRIVE_VERIFIED_FOLDER_ID"),
        os.getenv("GOOGLE_DRIVE_NEEDS_REVIEW_FOLDER_ID")
    ]
    
    print("🚀 Starting folder sharing process...")
    
    for email in filter(None, emails):
        print(f"\n📧 Granting access to: {email}")
        for folder_id in filter(None, folder_ids):
            try:
                drive.share_folder(folder_id, email, role='writer')
                print(f"✅ Shared folder {folder_id} with {email}")
            except Exception as e:
                print(f"❌ Failed to share folder {folder_id} with {email}: {e}")

    print("\n✨ Sharing complete! You should now have access to all folders.")

if __name__ == "__main__":
    share_all_folders()
