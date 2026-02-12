import os
from core.agent import VisaAgent
from services.database_service import init_db

init_db()
agent = VisaAgent()

# Reprocess the major zip file that was all scans
zip_path = 'tmp_Notaries.zip'
if os.path.exists(zip_path):
    print(f"Reprocessing {zip_path} with new OCR logic...")
    # Manual trigger of archive processing
    agent.process_archive(
        archive_file_id='reprocess_notaries', 
        archive_file_name='Notaries.zip', 
        archive_path=zip_path,
        applicant_name='Notaries'
    )
    print("Reprocessing complete for Notaries.zip")
else:
    print("tmp_Notaries.zip not found for reprocessing.")

