"""
Gmail Reply Monitor Service
Automatically detects customer replies and updates Google Sheets

NOTE: This version uses a simplified approach that checks for manual staff updates.
For full automation, Gmail API domain-wide delegation is required.
"""

import os
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv
from services.google_sheets_service import GoogleSheetsService

load_dotenv()

class GmailReplyMonitor:
    """Monitor for customer replies - simplified version for manual staff updates"""
    
    def __init__(self):
        """Initialize service"""
        self.sheets_service = GoogleSheetsService()
        print("📬 Gmail Reply Monitor initialized (manual mode)")
        print("   Staff should manually update 'Response Received' column when customers reply")
    
    def get_pending_responses(self):
        """
        Get all email addresses waiting for responses from Google Sheets
        
        Returns:
            List of dicts with {row_number, email_address, applicant_name, sent_date}
        """
        return self.sheets_service.get_pending_responses()
    
    def monitor_all_replies(self):
        """
        Check for manual updates to Response Received column
        
        Returns:
            Number of responses marked as received
        """
        print(f"\n📬 Checking Response Received status...")
        
        pending = self.get_pending_responses()
        
        if not pending:
            print("  ✓ All emails have received responses or are awaiting replies")
            return 0
        
        print(f"  ℹ {len(pending)} email(s) still waiting for customer responses")
        print("  → Staff can manually update 'Response Received' column to 'Yes' when customers reply")
        
        return 0

# For future full automation with Gmail API:
# 
# To enable automatic reply detection, you need to:
# 1. Enable Gmail API in Google Cloud Console
# 2. Set up domain-wide delegation for the service account
# 3. Grant the following scope: https://www.googleapis.com/auth/gmail.readonly
# 4. Uncomment the code below and remove the simplified version above
#
# class GmailReplyMonitor:
#     def __init__(self):
#         scopes = ['https://www.googleapis.com/auth/gmail.readonly']
#         creds = service_account.Credentials.from_service_account_file(
#             'gcp-service-account.json', scopes=scopes
#         )
#         delegated_creds = creds.with_subject('kyawzin.ccna@gmail.com')
#         self.service = build('gmail', 'v1', credentials=delegated_creds)
#         self.sheets_service = GoogleSheetsService()
#     
#     def check_for_reply(self, email_address, sent_date):
#         query = f'from:{email_address} after:{sent_date.strftime("%Y/%m/%d")}'
#         results = self.service.users().messages().list(
#             userId='me', q=query, maxResults=10
#         ).execute()
#         return len(results.get('messages', [])) > 0
#     
#     def monitor_all_replies(self):
#         pending = self.get_pending_responses()
#         replies_detected = 0
#         for entry in pending:
#             if self.check_for_reply(entry['email_address'], entry['sent_date']):
#                 self.sheets_service.mark_response_received(
#                     entry['row_number'], entry['applicant_name']
#                 )
#                 replies_detected += 1
#         return replies_detected

if __name__ == "__main__":
    # Test the reply monitor
    print("=" * 80)
    print("TESTING GMAIL REPLY MONITOR")
    print("=" * 80)
    
    monitor = GmailReplyMonitor()
    count = monitor.monitor_all_replies()
    
    print()
    print("=" * 80)
    print(f"✅ Monitor check complete")
    print("=" * 80)
