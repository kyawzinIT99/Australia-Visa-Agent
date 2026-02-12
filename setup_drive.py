import os
from services.google_drive_service import GoogleDriveService

def setup_drive_structure():
    drive = GoogleDriveService()
    print("Initializing Google Drive folder structure...")
    
    # 1. Main Root Folder
    root_name = "Australia Visa Applications"
    root_id = drive.get_folder_id_by_name(root_name)
    if not root_id:
        print(f"Creating root folder: {root_name}")
        root_id = drive.create_folder(root_name)
    else:
        print(f"Found existing root folder: {root_name} ({root_id})")
    
    # 2. Subfolders
    folders = ["incoming", "processing", "verified", "needs-review", "archived"]
    folder_ids = {}
    
    for folder_name in folders:
        f_id = drive.get_folder_id_by_name(folder_name, root_id)
        if not f_id:
            print(f"Creating subfolder: {folder_name}")
            f_id = drive.create_folder(folder_name, root_id)
        else:
            print(f"Found existing subfolder: {folder_name} ({f_id})")
        folder_ids[folder_name] = f_id
    
    # 3. Update .env file
    env_content = f"""# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Google Drive Folder IDs (Generated)
GOOGLE_DRIVE_INCOMING_FOLDER_ID={folder_ids['incoming']}
GOOGLE_DRIVE_PROCESSING_FOLDER_ID={folder_ids['processing']}
GOOGLE_DRIVE_VERIFIED_FOLDER_ID={folder_ids['verified']}
GOOGLE_DRIVE_NEEDS_REVIEW_FOLDER_ID={folder_ids['needs-review']}

# Email Configuration
SENDER_EMAIL=your_email@gmail.com
ADMIN_EMAIL=admin@yourorganization.com

# Database URL
DATABASE_URL=sqlite:///./data/visa_agent.db
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("\n.env file updated with Google Drive folder IDs:")
    for name, f_id in folder_ids.items():
        print(f"{name}: {f_id}")

if __name__ == "__main__":
    setup_drive_structure()
