#!/usr/bin/env python3
"""
System Health Monitor
Checks if all components are running and processing files correctly
"""

import os
import sys
import subprocess
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from services.google_drive_service import GoogleDriveService
from dotenv import load_dotenv

load_dotenv()

def check_processes():
    """Check if required processes are running"""
    print("🔍 Checking System Processes...")
    
    processes_to_check = [
        ("agent.py", "AI Agent"),
        ("app.py", "Dashboard"),
        ("scheduled_notifications.py", "Scheduler")
    ]
    
    running_processes = []
    
    for script_name, display_name in processes_to_check:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True
        )
        
        if script_name in result.stdout:
            print(f"  ✅ {display_name} is running")
            running_processes.append(display_name)
        else:
            print(f"  ❌ {display_name} is NOT running")
    
    return len(running_processes) == len(processes_to_check)

def check_google_drive():
    """Check Google Drive connectivity and file count"""
    print("\n📂 Checking Google Drive...")
    
    try:
        drive = GoogleDriveService()
        incoming_folder_id = os.getenv("GOOGLE_DRIVE_INCOMING_FOLDER_ID")
        
        if not incoming_folder_id:
            print("  ❌ INCOMING_FOLDER_ID not configured")
            return False
        
        files = drive.list_files_in_folder(incoming_folder_id)
        files = [f for f in files if f.get('mimeType') != 'application/vnd.google-apps.folder']
        
        print(f"  ✅ Google Drive accessible")
        print(f"  📄 {len(files)} file(s) in inbox")
        
        if files:
            print("  Files pending processing:")
            for f in files:
                print(f"    - {f['name']}")
        
        return True
    except Exception as e:
        print(f"  ❌ Google Drive error: {e}")
        return False

def check_database():
    """Check database connectivity"""
    print("\n💾 Checking Database...")
    
    try:
        from services.database_service import SessionLocal, VisaApplication
        
        db = SessionLocal()
        count = db.query(VisaApplication).count()
        db.close()
        
        print(f"  ✅ Database accessible")
        print(f"  📊 {count} document(s) in database")
        return True
    except Exception as e:
        print(f"  ❌ Database error: {e}")
        return False

def main():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("=" * 80)
    print(f"SYSTEM HEALTH CHECK - {timestamp}")
    print("=" * 80)
    
    all_ok = True
    
    # Check processes
    if not check_processes():
        all_ok = False
        print("\n⚠️  WARNING: Not all processes are running!")
        print("   Run: python3 run_system.py")
    
    # Check Google Drive
    if not check_google_drive():
        all_ok = False
    
    # Check Database
    if not check_database():
        all_ok = False
    
    print("\n" + "=" * 80)
    if all_ok:
        print("✅ SYSTEM STATUS: HEALTHY")
    else:
        print("❌ SYSTEM STATUS: ISSUES DETECTED")
    print("=" * 80)
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
