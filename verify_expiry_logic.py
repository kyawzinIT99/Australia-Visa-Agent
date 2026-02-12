from services.database_service import SessionLocal, VisaApplication, init_db
from core.agent import VisaAgent
import datetime
import json

def verify_expiry():
    agent = VisaAgent()
    db = SessionLocal()
    
    # Mock data with various expiry dates
    mock_scenarios = [
        {"name": "Passport_Expiring_Soon.pdf", "expiry": "2026-03-01"}, # Critical (within 30 days)
        {"name": "Passport_Valid.pdf", "expiry": "2027-01-01"},        # Far future
        {"name": "Passport_Expired.pdf", "expiry": "2024-01-01"},      # Past
        {"name": "Police_Clearance_Amber.pdf", "expiry": "2026-05-01"} # Warning (within 90 days)
    ]
    
    print("Simulating document analysis with expiry dates...")
    
    for scenario in mock_scenarios:
        # Create a mock analysis result
        analysis = {
            "document_type_detected": "Passport",
            "completeness_score": 95,
            "extracted_data": {
                "dates": {
                    "expiry_date": scenario["expiry"]
                }
            },
            "summary": f"Mock analysis for {scenario['name']}"
        }
        
        # Manually create application entries to test extraction logic
        # (This mimics the logic I just added to agent.py)
        from dateutil.parser import parse
        expiry_date = parse(scenario["expiry"])
        
        app = VisaApplication(
            document_id=f"doc_{scenario['name']}",
            file_name=scenario["name"],
            visa_subclass="600",
            document_type="Passport",
            status="Passed",
            completeness_score=95,
            ai_analysis=analysis,
            processing_stage="Verified",
            upload_date=datetime.datetime.now(),
            expiry_date=expiry_date
        )
        db.add(app)
    
    db.commit()
    print(f"Added {len(mock_scenarios)} mock records with expiry dates.")
    db.close()

if __name__ == "__main__":
    verify_expiry()
