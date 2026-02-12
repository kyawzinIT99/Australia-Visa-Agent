import datetime
from services.database_service import SessionLocal, VisaApplication, AuditLog

class VerificationService:
    """Manages the verification workflow for low-confidence document extractions."""
    
    def __init__(self):
        self.confidence_threshold = 70  # Documents below this require manual review
    
    def get_pending_verifications(self, applicant_id=None):
        """
        Retrieves documents needing manual review (confidence < threshold or status=pending).
        
        Args:
            applicant_id: Optional filter by applicant
            
        Returns:
            List of VisaApplication objects requiring verification
        """
        session = SessionLocal()
        try:
            query = session.query(VisaApplication).filter(
                (VisaApplication.confidence_score < self.confidence_threshold) |
                (VisaApplication.verification_status == 'pending')
            )
            
            if applicant_id:
                query = query.filter(VisaApplication.applicant_id == applicant_id)
            
            pending = query.order_by(VisaApplication.upload_date.desc()).all()
            return pending
        finally:
            session.close()
    
    def approve_extraction(self, document_id, verified_by, notes=None):
        """
        Marks a document extraction as verified and approved.
        
        Args:
            document_id: The document to approve
            verified_by: Who is verifying (email or username)
            notes: Optional verification notes
            
        Returns:
            Updated VisaApplication object or None if not found
        """
        session = SessionLocal()
        try:
            app = session.query(VisaApplication).filter(
                VisaApplication.document_id == document_id
            ).first()
            
            if not app:
                return None
            
            app.verification_status = 'verified'
            app.verified_by = verified_by
            app.verified_at = datetime.datetime.now()
            app.verification_notes = notes
            
            # Log the approval
            audit = AuditLog(
                document_id=document_id,
                action='verification_approved',
                performed_by=verified_by,
                details={
                    'notes': notes,
                    'confidence_score': app.confidence_score,
                    'previous_status': 'pending'
                }
            )
            session.add(audit)
            session.commit()
            session.refresh(app)
            
            return app
        except Exception as e:
            session.rollback()
            print(f"Error approving extraction: {e}")
            return None
        finally:
            session.close()
    
    def reject_and_reprocess(self, document_id, verified_by, reason, reprocess=True):
        """
        Rejects a document extraction and optionally triggers reprocessing.
        
        Args:
            document_id: The document to reject
            verified_by: Who is rejecting
            reason: Reason for rejection
            reprocess: Whether to trigger reprocessing
            
        Returns:
            Updated VisaApplication object or None
        """
        session = SessionLocal()
        try:
            app = session.query(VisaApplication).filter(
                VisaApplication.document_id == document_id
            ).first()
            
            if not app:
                return None
            
            app.verification_status = 'rejected'
            app.verified_by = verified_by
            app.verified_at = datetime.datetime.now()
            app.verification_notes = reason
            
            if reprocess:
                app.status = 'reprocessing'
            
            # Log the rejection
            audit = AuditLog(
                document_id=document_id,
                action='verification_rejected',
                performed_by=verified_by,
                details={
                    'reason': reason,
                    'reprocess': reprocess,
                    'confidence_score': app.confidence_score
                }
            )
            session.add(audit)
            session.commit()
            session.refresh(app)
            
            return app
        except Exception as e:
            session.rollback()
            print(f"Error rejecting extraction: {e}")
            return None
        finally:
            session.close()
    
    def update_field_value(self, document_id, field_path, new_value, verified_by):
        """
        Allows manual correction of extracted data fields.
        
        Args:
            document_id: The document to update
            field_path: JSON path to the field (e.g., "extracted_data.dates.expiry_date")
            new_value: New value for the field
            verified_by: Who is making the correction
            
        Returns:
            Updated VisaApplication object or None
        """
        session = SessionLocal()
        try:
            app = session.query(VisaApplication).filter(
                VisaApplication.document_id == document_id
            ).first()
            
            if not app or not app.ai_analysis:
                return None
            
            # Store old value for audit
            old_analysis = app.ai_analysis.copy()
            
            # Update the field (simplified - in production use proper JSON path library)
            parts = field_path.split('.')
            current = app.ai_analysis
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            old_value = current.get(parts[-1])
            current[parts[-1]] = new_value
            
            # Mark as modified
            app.verification_status = 'manually_corrected'
            app.verified_by = verified_by
            app.verified_at = datetime.datetime.now()
            
            # Log the change
            audit = AuditLog(
                document_id=document_id,
                action='field_manually_corrected',
                performed_by=verified_by,
                details={
                    'field_path': field_path,
                    'old_value': old_value,
                    'new_value': new_value
                }
            )
            session.add(audit)
            session.commit()
            session.refresh(app)
            
            return app
        except Exception as e:
            session.rollback()
            print(f"Error updating field: {e}")
            return None
        finally:
            session.close()
    
    def get_verification_stats(self, applicant_id=None):
        """
        Gets statistics about verification status.
        
        Returns:
            Dict with counts of pending, verified, rejected documents
        """
        session = SessionLocal()
        try:
            query = session.query(VisaApplication)
            if applicant_id:
                query = query.filter(VisaApplication.applicant_id == applicant_id)
            
            all_docs = query.all()
            
            stats = {
                'total': len(all_docs),
                'pending': sum(1 for d in all_docs if d.verification_status == 'pending'),
                'verified': sum(1 for d in all_docs if d.verification_status == 'verified'),
                'rejected': sum(1 for d in all_docs if d.verification_status == 'rejected'),
                'low_confidence': sum(1 for d in all_docs if d.confidence_score and d.confidence_score < self.confidence_threshold),
                'avg_confidence': sum(d.confidence_score or 0 for d in all_docs) / len(all_docs) if all_docs else 0
            }
            
            return stats
        finally:
            session.close()


if __name__ == "__main__":
    # Test the service
    service = VerificationService()
    print("Verification Service initialized.")
    print(f"Confidence threshold: {service.confidence_threshold}")
    
    # Get pending verifications
    pending = service.get_pending_verifications()
    print(f"Pending verifications: {len(pending)}")
