
import os
import sys
import pickle
from services.email_service import EmailService
from dotenv import load_dotenv

def test_email():
    load_dotenv()
    admin_email = os.getenv("ADMIN_EMAIL")
    
    print("="*60)
    print("TESTING EMAIL FUNCTIONALITY")
    print(f"Target Recipient: {admin_email}")
    print("="*60)
    
    try:
        service = EmailService()
        if not service.service:
            print("❌ Failed to initialize EmailService (service object is None)")
            return
            
        subject = "Test Email from Australia Visa Agent"
        body = "<h1>System Test</h1><p>This is a test email to verify the new email identity configuration.</p><p>Sender should be: <b>kyawzin.ccna@gmail.com</b></p>"
        
        print("Attempting to send email...")
        result = service.send_email(admin_email, subject, body)
        
        if result:
            print("✅ Email sent successfully!")
            print(f"Message ID: {result.get('id')}")
        else:
            print("❌ Failed to send email (check logs/token)")
            
    except Exception as e:
        print(f"❌ Exception during test: {e}")

if __name__ == "__main__":
    test_email()
