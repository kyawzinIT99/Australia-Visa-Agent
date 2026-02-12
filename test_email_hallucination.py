import os
import sys
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from services.client_alert_service import ClientAlertService
from services.database_service import SessionLocal, VisaApplication, Applicant

def test_email_generation():
    print("🧪 Testing AI Email Generation (Anti-Hallucination)...")
    
    db = SessionLocal()
    
    # Get a document with known data
    doc = db.query(VisaApplication).filter(
        VisaApplication.ai_analysis != None
    ).first()
    
    if not doc:
        print("❌ No documents found in database")
        return
    
    print(f"📄 Testing with document: {doc.file_name}")
    print(f"   Document Type: {doc.document_type}")
    
    # Get applicant
    applicant = db.query(Applicant).filter(
        Applicant.id == doc.applicant_id
    ).first()
    
    if applicant:
        print(f"   Applicant: {applicant.full_name}")
    else:
        print("   Applicant: None (will use 'Applicant')")
    
    # Generate email
    service = ClientAlertService()
    email_content = service.generate_alert_email(doc, "missing_elements", applicant)
    
    print("\n" + "="*80)
    print("GENERATED EMAIL:")
    print("="*80)
    print(f"Subject: {email_content['subject']}")
    print(f"\nBody:\n{email_content['body']}")
    print("="*80)
    
    # Check for hallucinations
    hallucination_checks = [
        ("John Doe", "❌ HALLUCINATION DETECTED: 'John Doe' found in email"),
        ("Jane Smith", "❌ HALLUCINATION DETECTED: 'Jane Smith' found in email"),
        ("Passport_Scan.pdf", "❌ HALLUCINATION DETECTED: 'Passport_Scan.pdf' found in email"),
    ]
    
    hallucinations_found = False
    for term, message in hallucination_checks:
        if term in email_content['subject'] or term in email_content['body']:
            print(f"\n{message}")
            hallucinations_found = True
    
    if not hallucinations_found:
        print("\n✅ No hallucinations detected!")
    
    # Verify actual data is used
    if applicant and applicant.full_name in email_content['body']:
        print(f"✅ Correct applicant name used: {applicant.full_name}")
    
    if doc.file_name in email_content['body']:
        print(f"✅ Correct file name used: {doc.file_name}")
    
    db.close()

if __name__ == "__main__":
    test_email_generation()
