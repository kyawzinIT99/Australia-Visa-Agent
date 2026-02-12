import os
import base64
from email.mime.text import MIMEText
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

class EmailService:
    def __init__(self, credentials_path='client_secret_931330138105-bsg4ghrk6baig3ta0d8uvcmdcnb5v46k.apps.googleusercontent.com.json', token_path='token.pickle'):
        self.scopes = ['https://www.googleapis.com/auth/gmail.send']
        self.creds = None
        
        # The file token.pickle stores the user's access and refresh tokens
        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                self.creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, self.scopes)
                # This will require interactive login, which might be tricky in an agent environment.
                # In a real deployment, we'd use a saved token or a service account with delegation.
                self.creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(token_path, 'wb') as token:
                pickle.dump(self.creds, token)

        self.service = build('gmail', 'v1', credentials=self.creds)

    def send_email(self, to, subject, body):
        """Sends an email using the Gmail API."""
        message = MIMEText(body, 'html')
        message['to'] = to
        message['subject'] = subject
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        try:
            message = self.service.users().messages().send(
                userId='me', body={'raw': raw_message}).execute()
            print(f"Message Id: {message['id']} sent successfully to {to}")
            return message
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

if __name__ == "__main__":
    # This test will likely fail in a non-interactive environment without a token.pickle
    # print("Initializing Email Service...")
    # email_service = EmailService()
    pass
