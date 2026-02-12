"""
AI-Powered Client Alert Email Service
Generates personalized emails to clients about their document status
"""

import os
from services.openai_service import OpenAIService
from services.email_service import EmailService
from services.database_service import SessionLocal, VisaApplication, Applicant, Notification
from datetime import datetime, timedelta
import json

class ClientAlertService:
    def __init__(self):
        self.openai = OpenAIService()
        self.email = EmailService()
        
        # Initialize Google Sheets service (optional - only if configured)
        try:
            from services.google_sheets_service import GoogleSheetsService
            self.sheets = GoogleSheetsService()
            print("✓ Google Sheets tracking enabled")
        except Exception as e:
            self.sheets = None
            print(f"ℹ Google Sheets tracking disabled: {e}")
        
    def generate_alert_email(self, document, issue_type="missing_elements", applicant=None):
        """
        Generate personalized email content using AI based on document analysis
        
        Args:
            document: VisaApplication object
            issue_type: Type of issue (missing_elements, low_confidence, expiring_soon)
        
        Returns:
            dict with subject and body
        """
        analysis = document.ai_analysis or {}
        
        # Prepare context for AI
        context = {
            "applicant_name": applicant.full_name if applicant else "Applicant",
            "document_type": document.document_type,
            "visa_subclass": document.visa_subclass,
            "file_name": document.file_name,
            "confidence_score": document.confidence_score,
            "completeness_score": document.completeness_score,
            "missing_elements": analysis.get("missing_elements", []),
            "findings": analysis.get("findings", []),
            "extracted_data": analysis.get("extracted_data", {}),
            "expiry_date": document.expiry_date.strftime("%Y-%m-%d") if document.expiry_date else None,
            "issue_type": issue_type
        }
        
        # AI prompt to generate email
        prompt = f"""
You are a Senior Immigration Consultant at Australia Visa Agent. Generate a high-premium, concise, and professional HTML email to a visa applicant regarding their document submission.

CRITICAL RULES - FOLLOW EXACTLY:
1. Generate minified, compact HTML. Do NOT include extra newlines or large vertical margins between sections.
2. ABSOLUTELY DO NOT HALLUCINATE OR INVENT ANY DATA:
   - Do NOT invent applicant names (no "John Doe", "Jane Smith", etc.)
   - Do NOT invent file names (no "Passport_Scan.pdf", etc.)
   - Do NOT invent dates, signatures, or any other details
   - ONLY use data explicitly provided in the context below
3. Use ONLY the applicant name provided: "{context['applicant_name']}"
4. Use ONLY the file name provided: "{context['file_name']}"
5. Use ONLY the document type provided: "{context['document_type']}"
6. For the signature, use EXACTLY this format with NO personal name:
   <p>Kind regards,<br>
   <strong>Senior Immigration Consultant</strong><br>
   Australia Visa Agent</p>
7. Extract "correctly included" points ONLY from the "Extracted Data" section below
8. Extract "missing" points ONLY from the "Missing" section below

EMAIL STRUCTURE:

<p>Dear {context['applicant_name']},</p>

<p>Thank you for submitting the {context['document_type']} ("{context['file_name']}").</p>

<p>After review, the following details are correctly included:</p>
<ul>
[Generate <li> items based ONLY on data found in "Extracted Data" below]
</ul>

<p>However, the document is missing:</p>
<ul>
[Generate <li> items based ONLY on "Missing" list below]
</ul>

<p>These are required to confirm validity and authenticity for immigration purposes.</p>

<p>Please contact the issuing authority to obtain a revised version including these details and send it to us once available.</p>

<p>Let us know once submitted so we can prioritise the review.</p>

<p>Kind regards,<br>
<strong>Senior Immigration Consultant</strong><br>
Australia Visa Agent</p>

CONTEXT DATA (USE ONLY THIS DATA):
- Applicant Name: {context['applicant_name']}
- Document Type: {context['document_type']}
- File Name: {context['file_name']}
- Issue Type: {issue_type}

Extracted Data (what IS in the document): {json.dumps(context['extracted_data'], indent=2)}

Findings (general observations): {json.dumps(context['findings'], indent=2)}

Missing (what is NOT in the document): {json.dumps(context['missing_elements'], indent=2)}

Return JSON format:
{{
    "subject": "Action Required: {context['document_type']} - {context['file_name']}",
    "body": "Full email body in compact HTML format"
}}
"""
        
        try:
            response = self.openai.client.chat.completions.create(
                model="gpt-4o",  # Using gpt-4o for higher quality email generation
                messages=[
                    {"role": "system", "content": "You are a professional senior immigration consultant. You write remarkably clear, structured, and helpful client communications. Your style is professional yet warm and supportive."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.6
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"Error generating email: {{e}}")
            # Fallback to template
            return self._fallback_email(document, issue_type)
    
    def _fallback_email(self, document, issue_type):
        """Fallback email template if AI generation fails"""
        subject = f"Action Required: {{document.document_type}} - {{document.file_name}}"
        
        body = f"""Dear Applicant,

We have reviewed your document: {{document.file_name}}

Our analysis indicates that this document requires your attention.

Document Type: {{document.document_type}}
Status: {{document.status}}
Confidence Score: {{document.confidence_score}}%

Please review and resubmit this document with the necessary corrections.

If you have any questions, please don't hesitate to contact us.

Best regards,
Australia Visa Processing Team
"""
        
        return {"subject": subject, "body": body}
    
    def send_email(self, applicant, document, email_info, issue_type):
        """
        Sends an email and records it in the Notification table
        """
        if not applicant.email:
            print(f"No email for applicant {applicant.full_name}")
            return False
            
        try:
            # Send the email
            self.email.send_email(
                to=applicant.email,
                subject=email_info['subject'],
                body=email_info['body']
            )
            
            # Record in Notification table
            db = SessionLocal()
            notification = Notification(
                applicant_id=applicant.id,
                document_id=document.document_id,
                notification_type=f"ai_alert_{issue_type}",
                severity="high" if issue_type in ["low_confidence", "expiring_soon"] else "medium",
                message=email_info['subject'],
                sent_at=datetime.now()
            )
            db.add(notification)
            db.commit()
            db.close()
            
            # Log to Google Sheets if enabled
            if self.sheets:
                try:
                    # Extract reason from email body (first 200 chars)
                    reason = email_info.get('subject', 'Document issue')
                    
                    self.sheets.log_email_delivery(
                        applicant_name=applicant.full_name,
                        document_id=document.document_id,
                        contact=applicant.email,
                        issue_type=issue_type,
                        email_address=applicant.email,
                        reason=reason
                    )
                except Exception as e:
                    print(f"Warning: Could not log to Google Sheets: {e}")
            
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    def is_alert_recently_sent(self, document_id, issue_type, days=7):
        """Checks if an alert was recently sent to avoid duplicate spamming"""
        db = SessionLocal()
        threshold_date = datetime.now() - timedelta(days=days)
        
        recent_notification = db.query(Notification).filter(
            Notification.document_id == document_id,
            Notification.notification_type == f"ai_alert_{issue_type}",
            Notification.sent_at >= threshold_date
        ).first()
        
        db.close()
        return recent_notification is not None
    
    def send_alerts_for_low_confidence_documents(self, threshold=70):
        """
        Send alert emails for all documents with confidence below threshold
        
        Args:
            threshold: Confidence threshold (default 70%)
        
        Returns:
            Number of emails sent
        """
        db = SessionLocal()
        
        # Get documents with low confidence
        low_confidence_docs = db.query(VisaApplication).filter(
            VisaApplication.confidence_score != None,
            VisaApplication.confidence_score < threshold,
            VisaApplication.verification_status == 'pending'
        ).all()
        
        emails_sent = 0
        
        for doc in low_confidence_docs:
            try:
                # Skip if alert recently sent
                if self.is_alert_recently_sent(doc.document_id, "low_confidence"):
                    print(f"  → Skipping {doc.file_name} (alert recently sent)")
                    continue

                # Get applicant info
                applicant = db.query(Applicant).filter(
                    Applicant.id == doc.applicant_id
                ).first()
                
                if not applicant:
                    print(f"No applicant found for document {doc.file_name}")
                    continue
                
                # Generate personalized email
                email_content = self.generate_alert_email(doc, "low_confidence", applicant)
                
                print(f"  ✓ Sending low confidence alert for {doc.file_name} to {applicant.email}")
                
                if self.send_email(applicant, doc, email_content, "low_confidence"):
                    emails_sent += 1
                
            except Exception as e:
                print(f"Error processing document {doc.file_name}: {e}")
                continue
        
        db.close()
        return emails_sent
    
    def send_alerts_for_expiring_documents(self, days_threshold=30):
        """
        Send alert emails for documents expiring soon
        
        Args:
            days_threshold: Days before expiry to send alert
        
        Returns:
            Number of emails sent
        """
        db = SessionLocal()
        
        # Calculate threshold date
        threshold_date = datetime.now() + timedelta(days=days_threshold)
        
        # Get expiring documents
        expiring_docs = db.query(VisaApplication).filter(
            VisaApplication.expiry_date != None,
            VisaApplication.expiry_date <= threshold_date,
            VisaApplication.expiry_date >= datetime.now()
        ).all()
        
        emails_sent = 0
        
        for doc in expiring_docs:
            try:
                # Skip if alert recently sent
                if self.is_alert_recently_sent(doc.document_id, "expiring_soon"):
                    continue

                applicant = db.query(Applicant).filter(
                    Applicant.id == doc.applicant_id
                ).first()
                
                if not applicant:
                    continue
                
                # Generate personalized email
                email_content = self.generate_alert_email(doc, "expiring_soon", applicant)
                
                print(f"  ✓ Sending expiry alert for {doc.file_name} to {applicant.email}")
                
                if self.send_email(applicant, doc, email_content, "expiring_soon"):
                    emails_sent += 1
                
            except Exception as e:
                print(f"Error processing document {doc.file_name}: {e}")
                continue
        
        db.close()
        return emails_sent
    
    def send_alerts_for_missing_elements(self):
        """
        Send alert emails for documents with missing required elements
        
        Returns:
            Number of emails sent
        """
        db = SessionLocal()
        
        # Get documents with missing elements
        docs_with_issues = db.query(VisaApplication).filter(
            VisaApplication.ai_analysis != None,
            VisaApplication.status == 'Needs Review'
        ).all()
        
        emails_sent = 0
        
        for doc in docs_with_issues:
            try:
                # Skip if alert recently sent
                if self.is_alert_recently_sent(doc.document_id, "missing_elements"):
                    continue

                analysis = doc.ai_analysis or {}
                missing = analysis.get("missing_elements", [])
                
                if not missing:
                    continue
                
                applicant = db.query(Applicant).filter(
                    Applicant.id == doc.applicant_id
                ).first()
                
                if not applicant:
                    continue
                
                # Generate personalized email
                email_content = self.generate_alert_email(doc, "missing_elements", applicant)
                
                print(f"  ✓ Sending missing elements alert for {doc.file_name} to {applicant.email}")
                
                if self.send_email(applicant, doc, email_content, "missing_elements"):
                    emails_sent += 1
                
            except Exception as e:
                print(f"Error processing document {doc.file_name}: {e}")
                continue
        
        db.close()
        return emails_sent


if __name__ == "__main__":
    service = ClientAlertService()
    
    print("\n" + "="*80)
    print("AI-Powered Client Alert Email Service")
    print("="*80)
    
    print("\n1. Checking for low confidence documents...")
    low_conf_count = service.send_alerts_for_low_confidence_documents(threshold=70)
    print(f"   Generated {low_conf_count} alert(s) for low confidence documents")
    
    print("\n2. Checking for expiring documents...")
    expiring_count = service.send_alerts_for_expiring_documents(days_threshold=90)
    print(f"   Generated {expiring_count} alert(s) for expiring documents")
    
    print("\n3. Checking for documents with missing elements...")
    missing_count = service.send_alerts_for_missing_elements()
    print(f"   Generated {missing_count} alert(s) for missing elements")
    
    total = low_conf_count + expiring_count + missing_count
    print(f"\n✅ Total alerts generated: {total}")
    print("\nNote: Emails are currently in preview mode. Uncomment email sending code to actually send.")
