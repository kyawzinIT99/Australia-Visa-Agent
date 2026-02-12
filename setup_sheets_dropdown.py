"""
Setup Follow-up Date Dropdown in Google Sheets
Adds data validation dropdown for common follow-up timeframes
"""

import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

def setup_followup_dropdown():
    """
    Add dropdown validation to the Follow-up Date column (Column I)
    Staff can select from common timeframes or enter custom dates
    """
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = service_account.Credentials.from_service_account_file(
        'gcpkyawzin.ccna.json', scopes=scopes
    )
    service = build('sheets', 'v4', credentials=creds)
    spreadsheet_id = os.getenv('EMAIL_TRACKING_SPREADSHEET_ID')
    
    # Define dropdown options (common follow-up timeframes)
    dropdown_values = [
        "1 day",
        "3 days", 
        "5 days",
        "7 days",
        "14 days",
        "30 days",
        "Custom"
    ]
    
    # Create data validation rule
    requests = [
        {
            "setDataValidation": {
                "range": {
                    "sheetId": 0,  # First sheet
                    "startRowIndex": 1,  # Start from row 2 (after header)
                    "endRowIndex": 1000,  # Apply to first 1000 rows
                    "startColumnIndex": 8,  # Column I (Follow-up Date)
                    "endColumnIndex": 9
                },
                "rule": {
                    "condition": {
                        "type": "ONE_OF_LIST",
                        "values": [{"userEnteredValue": val} for val in dropdown_values]
                    },
                    "showCustomUi": True,
                    "strict": False  # Allow custom values
                }
            }
        }
    ]
    
    body = {
        'requests': requests
    }
    
    try:
        response = service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=body
        ).execute()
        
        print("✓ Added follow-up date dropdown to Google Sheets")
        print(f"  Options: {', '.join(dropdown_values)}")
        print("  Staff can also enter custom dates in YYYY-MM-DD format")
        return True
    except Exception as e:
        print(f"✗ Error setting up dropdown: {e}")
        return False

if __name__ == "__main__":
    setup_followup_dropdown()
