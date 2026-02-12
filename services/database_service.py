import datetime
from sqlalchemy import create_engine, Column, Integer, String, TIMESTAMP, JSON, Boolean, Text, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()

class VisaApplication(Base):
    __tablename__ = 'visa_applications'
    
    id = Column(Integer, primary_key=True)
    document_id = Column(String(255), unique=True, nullable=False)
    applicant_id = Column(String(255))
    visa_subclass = Column(String(10))
    document_type = Column(String(100))
    file_name = Column(String(500))
    upload_date = Column(TIMESTAMP)
    status = Column(String(50))
    processing_stage = Column(String(100))
    completeness_score = Column(Integer)
    ai_analysis = Column(JSON)
    expiry_date = Column(TIMESTAMP)
    
    # Confidence and Verification Fields
    confidence_score = Column(Integer)  # Overall confidence 0-100
    field_confidence = Column(JSON)  # Individual field confidence scores
    ocr_metadata = Column(JSON)  # OCR quality metrics if OCR was used
    verification_status = Column(String(50), default='pending')  # pending, verified, rejected
    verified_by = Column(String(255))  # Who verified the document
    verified_at = Column(TIMESTAMP)  # When verification occurred
    verification_notes = Column(Text)  # Manual verification notes
    
    # Version History
    version = Column(Integer, default=1)  # Document processing version
    previous_version_id = Column(Integer, ForeignKey('visa_applications.id'))  # Link to previous version
    
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class Applicant(Base):
    __tablename__ = 'applicants'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
    full_name = Column(String(255))
    visa_subclass = Column(String(10))
    application_status = Column(String(50))
    documents_submitted = Column(Integer, default=0)
    documents_required = Column(Integer)
    last_interaction = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.now())

class DocumentChecklist(Base):
    __tablename__ = 'document_checklists'
    
    id = Column(Integer, primary_key=True)
    visa_subclass = Column(String(10))
    document_name = Column(String(255))
    is_required = Column(Boolean, default=True)
    category = Column(String(100))
    description = Column(Text)

class AuditLog(Base):
    __tablename__ = 'audit_log'
    
    id = Column(Integer, primary_key=True)
    document_id = Column(String(255))
    action = Column(String(100))
    performed_by = Column(String(100))
    details = Column(JSON)
    timestamp = Column(TIMESTAMP, server_default=func.now())

class Notification(Base):
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True)
    applicant_id = Column(String(255))
    document_id = Column(String(255))
    notification_type = Column(String(50))  # expiry_warning, verification_needed, etc.
    severity = Column(String(20))  # low, medium, high, critical
    message = Column(Text)
    sent_at = Column(TIMESTAMP, server_default=func.now())
    read_at = Column(TIMESTAMP)
    dismissed_at = Column(TIMESTAMP)

class NotificationPreferences(Base):
    __tablename__ = 'notification_preferences'
    
    id = Column(Integer, primary_key=True)
    applicant_id = Column(String(255), unique=True)
    email_enabled = Column(Boolean, default=True)
    alert_days = Column(JSON, default=[90, 60, 30])  # Days before expiry to alert
    notification_channels = Column(JSON, default=["email", "dashboard"])  # email, sms, dashboard


# Database configuration
DATABASE_URL = "sqlite:///./data/visa_agent.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def cleanup_database(session, max_records=1000):
    """
    Performs database cleanup:
    1. FIFO: Removes oldest records if count exceeds max_records.
    2. Date Validation: Removes records with invalid dates (future or pre-2000).
    """
    try:
        now = datetime.datetime.now()
        min_date = datetime.datetime(2000, 1, 1)

        # --- 1. Cleanup invalid dates ---
        # VisaApplication
        invalid_apps = session.query(VisaApplication).filter(
            (VisaApplication.upload_date > now) | (VisaApplication.upload_date < min_date)
        ).delete()
        
        # AuditLog
        invalid_logs = session.query(AuditLog).filter(
            (AuditLog.timestamp > now) | (AuditLog.timestamp < min_date)
        ).delete()

        if invalid_apps or invalid_logs:
            print(f"Cleanup: Removed {invalid_apps} applications and {invalid_logs} logs with invalid dates.")

        # --- 2. FIFO Cleanup ---
        # VisaApplication
        app_count = session.query(VisaApplication).count()
        if app_count > max_records:
            to_delete = app_count - max_records
            old_apps = session.query(VisaApplication.id).order_by(VisaApplication.created_at.asc()).limit(to_delete).all()
            ids_to_delete = [a.id for a in old_apps]
            deleted = session.query(VisaApplication).filter(VisaApplication.id.in_(ids_to_delete)).delete(synchronize_session=False)
            print(f"Cleanup: Removed {deleted} oldest applications (FIFO).")

        # AuditLog (separate limit for logs as they grow faster)
        log_limit = max_records * 5 
        log_count = session.query(AuditLog).count()
        if log_count > log_limit:
            to_delete = log_count - log_limit
            old_logs = session.query(AuditLog.id).order_by(AuditLog.timestamp.asc()).limit(to_delete).all()
            ids_to_delete = [l.id for l in old_logs]
            deleted = session.query(AuditLog).filter(AuditLog.id.in_(ids_to_delete)).delete(synchronize_session=False)
            print(f"Cleanup: Removed {deleted} oldest audit logs (FIFO).")

        session.commit()
    except Exception as e:
        print(f"Error during database cleanup: {e}")
        session.rollback()

def get_application_summary(session, applicant_id):
    """Fetches all applications for a given applicant ID."""
    return session.query(VisaApplication).filter(VisaApplication.applicant_id == applicant_id).all()

def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database initialized.")

if __name__ == "__main__":
    init_db()
