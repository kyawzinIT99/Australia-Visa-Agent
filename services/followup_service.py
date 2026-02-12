"""
Follow-up Service
Sends reminder emails for pending follow-ups after 7 days
"""

from services.google_sheets_service import GoogleSheetsService
from services.openai_service import OpenAIService
from services.email_service import EmailService
import json

class FollowupService:
    def __init__(self):
        self.sheets = GoogleSheetsService()
        self.openai = OpenAIService()
        self.email = EmailService()
    
    def generate_followup_email(self, applicant_name, issue_type, original_reason, days_ago):
        """
        Generate a follow-up email using AI
        
        Args:
            applicant_name: Name of the applicant
            issue_type: Original issue type
            original_reason: Original reason for contact
            days_ago: Number of days since original email
        
        Returns:
            dict with subject and body
        """
        prompt = f"""
You are a Senior Immigration Consultant at Australia Visa Agent. Generate a polite follow-up email to an applicant who was contacted {days_ago} days ago.

CRITICAL RULES:
1. Be professional and courteous
2. Reference the original issue
3. Offer assistance
4. Keep it concise and compact HTML
5. Do NOT hallucinate names or details
6. Use ONLY the provided information

EMAIL STRUCTURE:

<p>Dear {applicant_name},</p>

<p>I hope this email finds you well.</p>

<p>I am following up on our previous correspondence regarding your {issue_type} issue sent {days_ago} days ago.</p>

<p>Original concern: {original_reason}</p>

<p>We wanted to check if you have had the opportunity to address this matter or if you require any assistance from our team.</p>

<p>If you have already submitted the updated documents, please disregard this message. Otherwise, we are here to help guide you through the process.</p>

<p>Please feel free to reach out if you have any questions or need clarification.</p>

<p>Kind regards,<br>
<strong>Senior Immigration Consultant</strong><br>
Australia Visa Agent</p>

CONTEXT:
- Applicant: {applicant_name}
- Issue: {issue_type}
- Original Reason: {original_reason}
- Days Since Contact: {days_ago}

Return JSON format:
{{
    "subject": "Follow-up: {issue_type} - Australia Visa Application",
    "body": "Full email body in compact HTML format"
}}
"""
        
        try:
            response = self.openai.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a professional senior immigration consultant. You write clear, supportive follow-up communications."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.6
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            print(f"Error generating follow-up email: {e}")
            # Fallback template
            return {
                "subject": f"Follow-up: {issue_type} - Australia Visa Application",
                "body": f"""
<p>Dear {applicant_name},</p>

<p>I hope this email finds you well.</p>

<p>I am following up on our previous correspondence regarding your {issue_type} issue sent {days_ago} days ago.</p>

<p>We wanted to check if you have had the opportunity to address this matter or if you require any assistance from our team.</p>

<p>Please feel free to reach out if you have any questions.</p>

<p>Kind regards,<br>
<strong>Senior Immigration Consultant</strong><br>
Australia Visa Agent</p>
"""
            }
    
    def send_pending_followups(self):
        """
        Check for and send all pending follow-up emails
        
        Returns:
            Number of follow-ups sent
        """
        print("\n🔔 Checking for pending follow-ups...")
        
        pending = self.sheets.get_pending_followups()
        
        if not pending:
            print("  No pending follow-ups")
            return 0
        
        print(f"  Found {len(pending)} pending follow-up(s)")
        
        sent_count = 0
        
        for followup in pending:
            try:
                applicant_name = followup['applicant_name']
                email_address = followup['email_address']
                issue_type = followup['issue_type']
                reason = followup['reason']
                days_ago = followup['days_ago']
                row_number = followup['row_number']
                
                print(f"  → Sending follow-up to {applicant_name} ({email_address}) - {days_ago} days ago")
                
                # Generate follow-up email
                email_content = self.generate_followup_email(
                    applicant_name=applicant_name,
                    issue_type=issue_type,
                    original_reason=reason,
                    days_ago=days_ago
                )
                
                # Send email
                self.email.send_email(
                    to=email_address,
                    subject=email_content['subject'],
                    body=email_content['body']
                )
                
                # Mark as sent in Google Sheets
                self.sheets.mark_followup_sent(row_number)
                
                print(f"  ✓ Follow-up sent to {applicant_name}")
                sent_count += 1
                
            except Exception as e:
                print(f"  ✗ Error sending follow-up to {followup.get('applicant_name', 'Unknown')}: {e}")
                continue
        
        return sent_count

if __name__ == "__main__":
    service = FollowupService()
    count = service.send_pending_followups()
    print(f"\n✅ Sent {count} follow-up email(s)")
