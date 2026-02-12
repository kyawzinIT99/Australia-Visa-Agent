import time
import os
from services.database_service import SessionLocal, VisaApplication
from core.agent import VisaAgent
from unittest.mock import MagicMock

def simulate_workflow():
    print("🧪 Starting End-to-End Simulation...")
    
    # 1. Initialize Agent
    agent = VisaAgent()
    
    # 2. Mock OpenAI and Drive for Simulation
    # This allows us to test the DB, Dashboard, and Logic without real API calls
    agent.openai.classify_document = MagicMock(return_value={
        "document_type": "Passport",
        "visa_subclass": "189"
    })
    
    agent.openai.analyze_document = MagicMock(return_value={
        "is_correct_type": True,
        "completeness_score": 95,
        "findings": ["Clear photo identified", "Valid expiry datefound"],
        "missing_elements": [],
        "compliance_status": "Passed",
        "summary": "Passport appears valid and matches all Subclass 189 requirements."
    })
    
    agent.drive.move_file = MagicMock()
    agent.drive.download_file = MagicMock()
    
    # 3. Simulate finding a file
    file_id = "mock_file_id_123"
    file_name = "john_doe_passport.pdf"
    
    print(f"📄 Found file: {file_name}")
    
    # 4. Trigger processing (Modified for simulation)
    # We manually call a simplified version of agent.process_file
    print("⚙️ Processing document...")
    
    db = SessionLocal()
    try:
        # Check if already exists to avoid unique constraint error
        existing = db.query(VisaApplication).filter(VisaApplication.document_id == file_id).first()
        if existing:
            db.delete(existing)
            db.commit()
            
        app_entry = VisaApplication(
            document_id=file_id,
            visa_subclass="189",
            document_type="Passport",
            file_name=file_name,
            status="Passed",
            completeness_score=95,
            ai_analysis={
                "is_correct_type": True,
                "completeness_score": 95,
                "findings": ["Clear photo identified", "Valid expiry date found"],
                "missing_elements": [],
                "compliance_status": "Passed",
                "summary": "Passport appears valid and matches all Subclass 189 requirements."
            },
            processing_stage="Verified"
        )
        db.add(app_entry)
        db.commit()
        print("✅ Entry added to Database.")
        
        # 5. Notify
        agent.notify_applicant(file_name, "Verified", visa_subclass="189", score=95)
        
    finally:
        db.close()

    # 6. Simulate a failing case
    print("\n📄 Simulating a problematic document...")
    file_id_2 = "mock_file_id_456"
    file_name_2 = "missing_signature_form.pdf"
    
    db = SessionLocal()
    try:
        app_entry_2 = VisaApplication(
            document_id=file_id_2,
            visa_subclass="842",
            document_type="Form 80",
            file_name=file_name_2,
            status="Needs Review",
            completeness_score=45,
            ai_analysis={
                "is_correct_type": True,
                "completeness_score": 45,
                "findings": ["Personal details found"],
                "missing_elements": ["Applicant signature missing on page 17"],
                "compliance_status": "Needs Review",
                "summary": "Document is missing a critical signature on the final page."
            },
            processing_stage="Review Flagged"
        )
        db.add(app_entry_2)
        db.commit()
        print("✅ Warning entry added to Database.")
        
        agent.notify_applicant(file_name_2, "Needs Review", summary="Missing signature on page 17", visa_subclass="842", score=45)
        
    finally:
        db.close()

    print("\n✨ Simulation Complete! Open your dashboard at http://localhost:5001 to see the results.")

if __name__ == "__main__":
    simulate_workflow()
