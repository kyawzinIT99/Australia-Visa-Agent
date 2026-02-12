"""
Google Sheets Service
Handles logging of email deliveries and tracking follow-ups
"""

import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class GoogleSheetsService:
    def __init__(self, service_account_file='gcp-service-account.json'):
        self.scopes = ['https://www.googleapis.com/auth/spreadsheets']
        self.creds = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=self.scopes
        )
        self.service = build('sheets', 'v4', credentials=self.creds)
        self.spreadsheet_id = os.getenv('EMAIL_TRACKING_SPREADSHEET_ID')
        
        if not self.spreadsheet_id:
            raise ValueError("EMAIL_TRACKING_SPREADSHEET_ID not set in .env file")
    
    def log_email_delivery(self, applicant_name, document_id, contact, issue_type, email_address, reason):
        """
        Log an email delivery to Google Sheets
        
        Args:
            applicant_name: Name of the applicant
            document_id: Passport or document ID
            contact: Contact information (phone/email)
            issue_type: Type of issue (missing_elements, low_confidence, expiring_soon)
            email_address: Email address where email was sent
            reason: Detailed reason for the email
        
        Returns:
            Row number where the data was inserted
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Default follow-up: 7 days (staff can change this in the dropdown)
        followup_default = "7 days"
        
        values = [[
            timestamp,
            applicant_name,
            document_id,
            contact,
            issue_type,
            email_address,
            reason,
            "Sent",  # Status
            followup_default,  # Follow-up Date (dropdown value)
            "No"  # Response Received
        ]]
        
        body = {
            'values': values
        }
        
        try:
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range='Sheet1!A:J',  # Append to columns A through J
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            print(f"✓ Logged email to Google Sheets: {applicant_name} - {issue_type}")
            return result.get('updates', {}).get('updatedRows', 0)
        except Exception as e:
            print(f"✗ Error logging to Google Sheets: {e}")
            return None
    
    def get_pending_followups(self):
        """
        Get emails that need follow-up (sent 7+ days ago, no response)
        
        Returns:
            List of dictionaries with email details
        """
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='Sheet1!A:J'
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                return []
            
            # Skip header row
            headers = values[0]
            rows = values[1:]
            
            pending_followups = []
            today = datetime.now()
            
            for idx, row in enumerate(rows, start=2):  # Start at 2 because of header
                if len(row) < 10:
                    continue
                
                timestamp_str = row[0]
                status = row[7] if len(row) > 7 else ""
                followup_date_str = row[8] if len(row) > 8 else ""
                response_received = row[9] if len(row) > 9 else "No"
                
                # Skip if already followed up or response received
                if "Follow-up Sent" in status or response_received == "Yes":
                    continue
                
                # Parse follow-up date (staff can manually edit this)
                try:
                    # Try to parse the follow-up date
                    if followup_date_str:
                        # Support multiple date formats
                        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"]:
                            try:
                                followup_date = datetime.strptime(followup_date_str.split()[0], fmt)
                                break
                            except:
                                continue
                        else:
                            # If no format matched, skip this row
                            continue
                        
                        # Check if follow-up date has passed
                        if today.date() >= followup_date.date():
                            sent_date = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                            days_ago = (today - sent_date).days
                            
                            pending_followups.append({
                                'row_number': idx,
                                'applicant_name': row[1],
                                'document_id': row[2],
                                'contact': row[3],
                                'issue_type': row[4],
                                'email_address': row[5],
                                'reason': row[6],
                                'sent_date': sent_date,
                                'followup_date': followup_date,
                                'days_ago': days_ago
                            })
                except Exception as e:
                    print(f"  Warning: Could not parse date for row {idx}: {e}")
                    continue
            
            return pending_followups
        except Exception as e:
            print(f"✗ Error getting pending follow-ups: {e}")
            return []
    
    def mark_followup_sent(self, row_number):
        """
        Mark a follow-up as sent in the spreadsheet
        
        Args:
            row_number: Row number to update
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Update status column (H)
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f'Sheet1!H{row_number}',
                valueInputOption='RAW',
                body={'values': [[f"Follow-up Sent ({timestamp})"]]}
            ).execute()
            
            print(f"✓ Marked row {row_number} as follow-up sent")
            return True
        except Exception as e:
            print(f"✗ Error marking follow-up: {e}")
            return False
    
    def get_pending_responses(self):
        """
        Get all emails waiting for customer responses (Response Received = No)
        
        Returns:
            List of dicts with {row_number, email_address, applicant_name, sent_date}
        """
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='Sheet1!A:J'
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                return []
            
            # Skip header row
            rows = values[1:]
            
            pending_responses = []
            
            for idx, row in enumerate(rows, start=2):  # Start at 2 because of header
                if len(row) < 10:
                    continue
                
                timestamp_str = row[0]
                applicant_name = row[1]
                email_address = row[5]
                response_received = row[9] if len(row) > 9 else "No"
                
                # Only include rows where response not yet received
                if response_received == "No":
                    try:
                        sent_date = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                        
                        pending_responses.append({
                            'row_number': idx,
                            'email_address': email_address,
                            'applicant_name': applicant_name,
                            'sent_date': sent_date
                        })
                    except Exception as e:
                        print(f"  Warning: Could not parse date for row {idx}: {e}")
                        continue
            
            return pending_responses
        except Exception as e:
            print(f"✗ Error getting pending responses: {e}")
            return []
    
    def mark_response_received(self, row_number, applicant_name):
        """
        Mark that a customer response was received
        
        Args:
            row_number: Row number to update
            applicant_name: Name of applicant (for logging)
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Update Response Received column (J) to "Yes"
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f'Sheet1!J{row_number}',
                valueInputOption='RAW',
                body={'values': [["Yes"]]}
            ).execute()
            
            # Update Status column (H) to show response received
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f'Sheet1!H{row_number}',
                valueInputOption='RAW',
                body={'values': [[f"Response Received ({timestamp})"]]}
            ).execute()
            
            print(f"✓ Marked row {row_number} as response received from {applicant_name}")
            return True
        except Exception as e:
            print(f"✗ Error marking response received: {e}")
            return False
    
    def initialize_spreadsheet(self):
        """
        Initialize the spreadsheet with headers if empty
        """
        try:
            # Check if spreadsheet has data
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='Sheet1!A1:J1'
            ).execute()
            
            values = result.get('values', [])
            
            # If no headers, add them
            if not values:
                headers = [[
                    'Timestamp',
                    'Applicant Name',
                    'Passport/Document ID',
                    'Contact',
                    'Issue Type',
                    'Email Address',
                    'Reason/Details',
                    'Status',
                    'Follow-up Date',
                    'Response Received'
                ]]
                
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range='Sheet1!A1:J1',
                    valueInputOption='RAW',
                    body={'values': headers}
                ).execute()
                
                print("✓ Initialized Google Sheets with headers")
                return True
        except Exception as e:
            print(f"✗ Error initializing spreadsheet: {e}")
            return False

if __name__ == "__main__":
    # Test the service
    sheets = GoogleSheetsService()
    sheets.initialize_spreadsheet()
    
    # Test logging
    sheets.log_email_delivery(
        applicant_name="Test Applicant",
        document_id="TEST123",
        contact="test@example.com",
        issue_type="missing_elements",
        email_address="test@example.com",
        reason="Missing passport expiry date"
    )
    
    # Test getting pending follow-ups
    pending = sheets.get_pending_followups()
    print(f"\nPending follow-ups: {len(pending)}")
