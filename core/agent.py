import os
import sys
import time
import datetime
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.database_service import SessionLocal, VisaApplication, Applicant, DocumentChecklist, init_db, cleanup_database
from services.google_drive_service import GoogleDriveService
from services.openai_service import OpenAIService
from services.email_service import EmailService
from core.utils import extract_text_from_pdf, get_file_extension, is_archive, extract_archive
import json
import shutil
from dateutil.parser import parse

load_dotenv()

class VisaAgent:
    def __init__(self):
        self.db = SessionLocal()
        self.drive = GoogleDriveService()
        self.openai = OpenAIService()
        # Email service might require interaction for first-time OAuth, 
        # so we initialize it only when needed or if token exists.
        self.email = None 
        
        self.incoming_folder_id = os.getenv("GOOGLE_DRIVE_INCOMING_FOLDER_ID")
        self.processing_folder_id = os.getenv("GOOGLE_DRIVE_PROCESSING_FOLDER_ID")
        self.verified_folder_id = os.getenv("GOOGLE_DRIVE_VERIFIED_FOLDER_ID")
        self.needs_review_folder_id = os.getenv("GOOGLE_DRIVE_NEEDS_REVIEW_FOLDER_ID")
        
        # Load mail configuration
        config_path = os.path.join(os.path.dirname(__file__), '..', 'mail_config.json')
        with open(config_path, 'r') as f:
            self.mail_config = json.load(f)

    def run_once(self):
        """Runs one iteration of the document processing pipeline."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"\n[{timestamp}] === AGENT POLLING CYCLE START ===")
        
        # Perform database cleanup
        cleanup_database(self.db)
        
        print(f"[{timestamp}] Checking for new documents in Google Drive...")
        try:
            all_files = self.drive.list_files_in_folder(self.incoming_folder_id)
            print(f"[{timestamp}] ✓ Successfully queried Google Drive")
        except Exception as e:
            print(f"[{timestamp}] ✗ ERROR querying Google Drive: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Filter out folders to avoid processing errors
        files = [f for f in all_files if f.get('mimeType') != 'application/vnd.google-apps.folder']
        folders = [f for f in all_files if f.get('mimeType') == 'application/vnd.google-apps.folder']
        
        if folders:
            print(f"[{timestamp}] Skipping {len(folders)} subfolders in incoming (Recursive scanning not yet implemented).")
        
        if not files:
            print(f"[{timestamp}] No new files found.")
            print(f"[{timestamp}] === AGENT POLLING CYCLE END (No files) ===")
            return
        
        print(f"[{timestamp}] Found {len(files)} file(s) to process:")
        for f in files:
            print(f"[{timestamp}]   - {f['name']} (ID: {f['id']})")

        for file in files:
            try:
                self.process_file(file)
            except Exception as e:
                print(f"[{timestamp}] ✗ ERROR processing file {file['name']}: {e}")
                import traceback
                traceback.print_exc()
                self.db.rollback()  # Ensure session is clean for next file
        
        print(f"[{timestamp}] === AGENT POLLING CYCLE END ===")

    def process_file(self, file_info):
        """Main entry point for file processing. Handles both archives and single files."""
        file_id = file_info['id']
        file_name = file_info['name']
        print(f"Processing {file_name}...")

        # 1. Move to processing
        self.drive.move_file(file_id, self.incoming_folder_id, self.processing_folder_id)
        
        # 2. Download file
        temp_path = f"tmp_{file_name}"
        self.drive.download_file(file_id, temp_path)
        
        # 3. Check if archive
        if is_archive(temp_path):
            self.process_archive(file_id, file_name, temp_path)
        else:
            self.process_single_document(file_id, file_name, temp_path, applicant_name=None)
        
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
        print(f"Finished processing {file_name}")

    def process_archive(self, archive_file_id, archive_file_name, archive_path):
        """Process ZIP/RAR archive containing multiple documents."""
        # Extract applicant name from archive filename (remove extension)
        applicant_name = os.path.splitext(archive_file_name)[0]
        print(f"📦 Batch processing archive for applicant: {applicant_name}")
        
        # 2. Extract archive to temporary directory
        extract_dir = f"tmp_extract_{applicant_name}"
        extracted_files = extract_archive(archive_path, extract_dir)
        
        if not extracted_files:
            print(f"No files extracted from {archive_file_name}")
            return
        
        # Process each extracted file
        for extracted_file_path in extracted_files:
            try:
                # Use absolute path for OS operations
                abs_file_path = os.path.abspath(extracted_file_path)
                
                # Get filename for display and DB
                file_name_for_db = os.path.basename(abs_file_path)
                
                # Skip macOS metadata files and empty directories
                if file_name_for_db.startswith('._') or '__MACOSX' in abs_file_path or os.path.isdir(abs_file_path):
                    continue
                    
                print(f"  → Processing {file_name_for_db} from archive...")
                
                # Process document
                # Create a composite document ID to satisfy uniqueness
                composite_id = f"{archive_file_id}:{file_name_for_db}"
                
                # Get or Create Applicant
                applicant = self.db.query(Applicant).filter(Applicant.full_name == applicant_name).first()
                if not applicant:
                    applicant = Applicant(full_name=applicant_name, application_status="Processing")
                    self.db.add(applicant)
                    self.db.commit()
                
                self.process_single_document(
                    file_id=composite_id,
                    file_name=file_name_for_db,
                    file_path=abs_file_path,
                    applicant_name=applicant_name,
                    applicant_id=applicant.id
                )
            except Exception as e:
                print(f"  ✗ Error processing {extracted_file_path}: {e}")
                self.db.rollback()
        
        # Cleanup extraction directory AFTER loop
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        
        # Move archive to verified folder
        self.drive.move_file(archive_file_id, self.processing_folder_id, self.verified_folder_id)
        print(f"✓ Batch processing complete for {applicant_name} ({len(extracted_files)} documents)")

    def process_single_document(self, file_id, file_name, file_path, applicant_name=None, applicant_id=None):
        """Process a single document (either standalone or from archive)."""
        doc_type = "Unknown"
        visa_subclass = "Unknown"
        
        # Extract text and OCR metadata
        text = ""
        ocr_metadata = {}
        file_ext = file_path.lower()
        
        if file_ext.endswith('.pdf'):
            result = extract_text_from_pdf(file_path, openai_service=self.openai)
            # Handle both old (string) and new (tuple) return formats
            if isinstance(result, tuple):
                text, ocr_metadata = result
            else:
                text = result
        elif file_ext.endswith(('.jpg', '.jpeg', '.png', '.heic')):
            print(f"  → Performing OCR on image: {file_name}")
            ocr_result = self.openai.ocr_from_images([file_path])
            if isinstance(ocr_result, dict):
                text = ocr_result.get("transcribed_text", "")
                ocr_metadata = {
                    "ocr_confidence": ocr_result.get("ocr_confidence", 0),
                    "quality_issues": ocr_result.get("quality_issues", []),
                    "text_clarity": ocr_result.get("text_clarity", "unknown"),
                    "ocr_used": True
                }
            else:
                text = str(ocr_result)
                ocr_metadata = {"ocr_used": True}
        else:
            # Handle other file types (images etc if added later)
            print(f"Skipping text extraction for unsupported file type: {file_name}")
            return
        
        if not text.strip():
            print(f"  ✗ OCR failed or no text extracted from {file_name}, flagging as Needs Review")
            # Store in database even if text extraction fails, so it shows on dashboard
            unique_file_name = f"{applicant_name}/{file_name}" if applicant_name else file_name
            app_entry = VisaApplication(
                document_id=file_id,
                visa_subclass=visa_subclass or "Unknown",
                document_type=doc_type or "Unknown",
                file_name=unique_file_name,
                status="Needs Review",
                completeness_score=0,
                ai_analysis={"error": "OCR/Text extraction failed. Manual review required."},
                processing_stage="Text Extraction Failed",
                upload_date=datetime.datetime.now(),
                applicant_id=applicant_id
            )
            self.db.add(app_entry)
            try:
                self.db.commit()
            except Exception as e:
                print(f"  ✗ Database commit failed for {file_name}: {e}")
                self.db.rollback()
            return
        
        # Classify document
        classification = self.openai.classify_document(text)
        if not classification:
            print(f"  ✗ Classification failed for {file_name}")
            return

        doc_type = classification.get('document_type', 'Unknown')
        visa_subclass = classification.get('visa_subclass', 'Unknown')
        
        print(f"  ✓ Classified as {doc_type} for Subclass {visa_subclass}")

        # AI Verify against requirements
        analysis = self.openai.analyze_document(text, visa_subclass, doc_type)
        if not analysis:
            print(f"  ✗ Analysis failed for {file_name}")
            return
        
        # --- SMART RETRY LOGIC FOR OCR ---
        # If analysis score is low (< 50) and we didn't use OCR, it might be a scanned form with non-extractable data.
        completeness_score = analysis.get('completeness_score', 0)
        ocr_used = ocr_metadata.get('ocr_used', False) if ocr_metadata else False
        
        if completeness_score < 50 and not ocr_used and file_ext.endswith('.pdf'):
            print(f"  ⚠ Low completeness score ({completeness_score}) for {file_name}. Retrying with Forced OCR...")
            
            # 1. Force OCR extraction
            text_ocr, ocr_metadata_new = extract_text_from_pdf(file_path, openai_service=self.openai, force_ocr=True)
            
            # 2. Re-classify (optional, but good if OCR text changes context)
            # classification_new = self.openai.classify_document(text_ocr)
            
            # 3. Re-analyze with new text
            analysis_new = self.openai.analyze_document(text_ocr, visa_subclass, doc_type)
            
            if analysis_new:
                new_score = analysis_new.get('completeness_score', 0)
                print(f"  ↻ Retry Result: Score went from {completeness_score} to {new_score}")
                
                # Keep the new result if it's better or at least the same (OCR text is usually more reliable for forms)
                if new_score >= completeness_score:
                    text = text_ocr
                    analysis = analysis_new
                    ocr_metadata = ocr_metadata_new
                    completeness_score = new_score
        # ---------------------------------
        
        # Store/Update in Database
        # For batch uploads, use "applicant_name/file_name" as unique identifier
        unique_file_name = f"{applicant_name}/{file_name}" if applicant_name else file_name
        existing_app = self.db.query(VisaApplication).filter(VisaApplication.file_name == unique_file_name).first()
        
        # Extract potential expiry date
        expiry_date = None
        if analysis and "extracted_data" in analysis:
            dates = analysis["extracted_data"].get("dates", {})
            
            # Helper to get date by fuzzy key matching
            def find_date(search_terms):
                # search_terms is a list of strings to look for in keys (case-insensitive)
                for k, v in dates.items():
                    k_lower = k.lower().replace(" ", "_")
                    if any(term in k_lower for term in search_terms) and v:
                        return v
                return None

            # 1. Look for explicit Expiry Date
            expiry_str = find_date(["expiry"])
            
            # Fallback for notarized documents: Use translation, authentication, or issue date if expiry is missing
            if not expiry_str or expiry_str in ["YYYY-MM-DD", "None", "Not applicable", "Not provided"]:
                # Check for explicit translation/notary dates in the JSON data first
                expiry_str = find_date(["translation", "authentication", "notary", "notarial"])
                
                if not expiry_str:
                    is_notary = any(x in (doc_type or "").lower() for x in ["notary", "notarial", "translation", "authenticated"])
                    if is_notary:
                        expiry_str = find_date(["issue_date", "issue"])
                
                if expiry_str:
                    print(f"  ℹ Using {expiry_str} (Reference Date) as validity reference for document: {file_name}")
                else:
                    print(f"  ℹ No expiry or reference date found for {file_name}. Dates: {dates}")

            if expiry_str and expiry_str not in ["YYYY-MM-DD", "None", "Not applicable", "Not provided"]:
                try:
                    # Attempt to parse YYYY-MM-DD or other common formats
                    expiry_date = parse(expiry_str)
                    print(f"  ✓ Parsed expiry date: {expiry_date}")
                except:
                    print(f"  ! Could not parse expiry date: {expiry_str}")

        if existing_app:
            print(f"  → Updating existing record for {file_name}")
            existing_app.document_id = file_id
            existing_app.visa_subclass = visa_subclass
            existing_app.document_type = doc_type
            completeness_score = analysis.get('completeness_score', 0)
            existing_app.status = "Passed" if completeness_score >= 90 else "Needs Review"
            existing_app.completeness_score = completeness_score
            existing_app.ai_analysis = analysis
            existing_app.processing_stage = "Verified"
            existing_app.upload_date = datetime.datetime.now()
            existing_app.expiry_date = expiry_date
            # Save confidence scoring fields
            existing_app.confidence_score = analysis.get('confidence_score')
            existing_app.field_confidence = analysis.get('field_confidence')
            existing_app.ocr_metadata = ocr_metadata if ocr_metadata else None
            existing_app.verification_status = 'verified' if analysis.get('confidence_score', 100) >= 70 else 'pending'
        else:
            print(f"  → Creating new record for {file_name}")
            completeness_score = analysis.get('completeness_score', 0)
            # Determine compliance status based on completeness score
            compliance_status = "Passed" if completeness_score >= 90 else "Needs Review"
            
            # Extract confidence fields from analysis
            confidence_score = analysis.get('confidence_score')
            field_confidence = analysis.get('field_confidence')
            verification_status = 'verified' if (confidence_score or 100) >= 70 else 'pending'

            app_entry = VisaApplication(
                document_id=file_id,
                file_name=unique_file_name, # Use unique_file_name here
                visa_subclass=visa_subclass,
                document_type=doc_type,
                status=compliance_status,
                completeness_score=completeness_score,
                ai_analysis=analysis,
                processing_stage="Verified",
                upload_date=datetime.datetime.now(),
                applicant_id=applicant_id,
                expiry_date=expiry_date,
                # Add confidence scoring fields
                confidence_score=confidence_score,
                field_confidence=field_confidence,
                ocr_metadata=ocr_metadata if ocr_metadata else None,
                verification_status=verification_status
            )
            self.db.add(app_entry)
            
        try:
            self.db.commit()
        except Exception as e:
            print(f"  ✗ Database commit failed: {e}")
            self.db.rollback()
            raise

        # For standalone files (not from archive), move to verified folder
        if not applicant_name:
            self.drive.move_file(file_id, self.processing_folder_id, self.verified_folder_id)
            self.notify_applicant(file_name, "Verified", visa_subclass=visa_subclass, score=analysis.get('completeness_score', 100))
            print(f"  ✓ {file_name} processed and moved to Verified")

    def sync_folders(self):
        """Reconciles database status with actual file locations in Google Drive."""
        print("Syncing folder states with database...")
        
        # 1. Check Verified Folder
        verified_files = self.drive.list_files_in_folder(self.verified_folder_id)
        for f in verified_files:
            app = self.db.query(VisaApplication).filter(VisaApplication.document_id == f['id']).first()
            if app and app.status != "Passed":
                print(f"Sync: Updating {f['name']} status to Passed (Found in Verified folder)")
                app.status = "Passed"
                self.db.commit()

        # 2. Check Needs Review Folder
        review_files = self.drive.list_files_in_folder(self.needs_review_folder_id)
        for f in review_files:
            app = self.db.query(VisaApplication).filter(VisaApplication.document_id == f['id']).first()
            if app and app.status not in ["Needs Review", "Partial"]:
                print(f"Sync: Updating {f['name']} status to Needs Review (Found in Needs Review folder)")
                app.status = "Needs Review"
                self.db.commit()

    def notify_applicant(self, file_name, status, summary=None, visa_subclass="Unknown", score=0):
        """Sends a notification email based on mail_config.json."""
        template_key = "verified" if status == "Verified" else "needs_review"
        template = self.mail_config['email_templates'].get(template_key)
        
        if not template:
            print(f"No email template found for key: {template_key}")
            return

        subject = template['subject'].format(file_name=file_name, visa_subclass=visa_subclass)
        body = template['body'].format(
            file_name=file_name, 
            visa_subclass=visa_subclass, 
            score=score, 
            summary=summary or "N/A"
        )

        print(f"NOTIFICATION [To: Applicant]: {subject}")
        # print(f"Body: {body[:100]}...")
        
        # Actual email sending logic using EmailService would go here

    def start_polling(self, interval=60):
        """Starts polling the incoming folder and syncing other folders."""
        print(f"Starting agent polling and folder sync every {interval} seconds...")
        while True:
            try:
                self.recover_stuck_files()
                self.run_once()
                self.sync_folders()
            except Exception as e:
                print(f"Error in agent polling loop: {e}")
                # Optional: log traceback
                import traceback
                traceback.print_exc()
            
            time.sleep(interval)

    def recover_stuck_files(self):
        """Checks for files stuck in process folder and moves them back to incoming."""
        print("Checking for stuck files in processing folder...")
        stuck_files = self.drive.list_files_in_folder(self.processing_folder_id)
        # Filter out folders from recovery as well
        stuck_files = [f for f in stuck_files if f.get('mimeType') != 'application/vnd.google-apps.folder']
        
        if stuck_files:
            print(f"Found {len(stuck_files)} potentially stuck files. Moving back to incoming for retry.")
            for f in stuck_files:
                try:
                    self.drive.move_file(f['id'], self.processing_folder_id, self.incoming_folder_id)
                    print(f"  → Recovered {f['name']}")
                except Exception as e:
                    print(f"  ✗ Failed to recover {f['name']}: {e}")

if __name__ == "__main__":
    init_db()
    agent = VisaAgent()
    # Change from run_once() to start_polling() for continuous monitoring
    agent.start_polling(interval=30)
