from services.database_service import SessionLocal, VisaApplication
import json

def check_dates():
    db = SessionLocal()
    apps = db.query(VisaApplication).all()
    
    print(f"{'File Name':<40} | {'Extracted Expiry'}")
    print("-" * 60)
    
    for app in apps:
        analysis = app.ai_analysis
        expiry_in_db = app.expiry_date
        
        extracted_expiry = "MISSING"
        if analysis and "extracted_data" in analysis:
            dates = analysis["extracted_data"].get("dates", {})
            extracted_expiry = dates.get("expiry_date", "NOT IN JSON")
            
        print(f"{app.file_name:<40} | AI: {extracted_expiry} | DB: {expiry_in_db}")

if __name__ == "__main__":
    check_dates()
