
import os
import sys
import pickle
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from services.google_drive_service import GoogleDriveService
# We need to mock the modification to GmailReplyMonitor to test it effectively before changing the file,
# or we can just try to initialize it with the new email if we change it in memory?
# Actually, let's just test the connections we can.

def verify_config():
    print("="*60)
    print("VERIFYING EMAIL & DRIVE CONFIGURATION")
    print("="*60)
    
    # 1. Check .env
    print("\n1. Checking .env file...")
    load_dotenv()
    admin_email = os.getenv("ADMIN_EMAIL")
    sender_email = os.getenv("SENDER_EMAIL")
    incoming_id = os.getenv("GOOGLE_DRIVE_INCOMING_FOLDER_ID")
    
    print(f"   ADMIN_EMAIL: {admin_email}")
    print(f"   SENDER_EMAIL: {sender_email}")
    print(f"   INCOMING_FOLDER_ID: {incoming_id}")
    
    # 2. Check token.pickle
    print("\n2. Checking token.pickle (for sending emails)...")
    if os.path.exists('token.pickle'):
        try:
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
                print("   ✅ token.pickle exists and is loadable")
                print(f"   Valid: {creds.valid}")
                print(f"   Expired: {creds.expired}")
                print(f"   Scopes: {creds.scopes}")
                if creds.refresh_token:
                    print("   ✅ Refresh token present")
                else:
                    print("   ⚠️ No refresh token")
        except Exception as e:
            print(f"   ❌ Error reading token.pickle: {e}")
    else:
        print("   ❌ token.pickle NOT found")

    # 3. Check Google Drive Access
    print("\n3. Checking Google Drive Access...")
    try:
        drive = GoogleDriveService()
        files = drive.list_files_in_folder(incoming_id)
        print(f"   ✅ Successfully listed files in incoming folder")
        print(f"   Count: {len(files)}")
        if files:
            print(f"   First file: {files[0].get('name')}")
    except Exception as e:
        print(f"   ❌ Failed to access Google Drive: {e}")
        
    print("\n" + "="*60)
    print("Verification Script Complete")
    print("="*60)

if __name__ == "__main__":
    verify_config()
