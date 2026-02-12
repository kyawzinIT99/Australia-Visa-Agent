from services.database_service import SessionLocal, VisaApplication, Applicant
import os

def backfill():
    db = SessionLocal()
    apps = db.query(VisaApplication).all()
    
    print(f"Checking {len(apps)} applications for backfilling...")
    
    for app in apps:
        if not app.applicant_id:
            # Try to infer applicant name from file_name (e.g., "Notaries/Name/file.pdf" or "Name/file.pdf")
            parts = app.file_name.split('/')
            if len(parts) > 1:
                applicant_name = parts[0]
                if applicant_name == "Notaries" and len(parts) > 2:
                    applicant_name = parts[1]
                
                print(f"Inferred applicant '{applicant_name}' for file: {app.file_name}")
                
                # Get or Create Applicant
                applicant = db.query(Applicant).filter(Applicant.full_name == applicant_name).first()
                if not applicant:
                    applicant = Applicant(full_name=applicant_name, application_status="Requires Review")
                    db.add(applicant)
                    db.commit()
                
                app.applicant_id = applicant.id
                db.commit()
    
    db.close()
    print("Backfill complete.")

if __name__ == "__main__":
    backfill()
