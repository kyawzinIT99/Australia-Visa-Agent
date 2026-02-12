from flask import Flask, render_template, jsonify, request
import os
from services.database_service import SessionLocal, VisaApplication, Applicant, Notification, AuditLog
from services.openai_service import OpenAIService
from services.verification_service import VerificationService
from services.notification_service import NotificationService
from services.client_alert_service import ClientAlertService
from services.assistant_service import AssistantService
from sqlalchemy import desc

app = Flask(__name__)

# Initialize AI Assistant (lazy loading to avoid errors if TAVILY_API_KEY not set)
assistant = None

def get_assistant():
    global assistant
    if assistant is None:
        try:
            assistant = AssistantService()
        except ValueError as e:
            print(f"[WARNING] Assistant service not available: {e}")
            assistant = None
    return assistant

def get_stats():
    db = SessionLocal()
    total = db.query(VisaApplication).count()
    passed = db.query(VisaApplication).filter(VisaApplication.status == 'Passed').count()
    needs_review = db.query(VisaApplication).filter(VisaApplication.status == 'Needs Review').count()
    db.close()
    return {
        "total": total,
        "passed": passed,
        "needs_review": needs_review
    }

@app.route('/')
def index():
    db = SessionLocal()
    recent_apps = db.query(VisaApplication).order_by(desc(VisaApplication.updated_at)).limit(10).all()
    stats = get_stats()
    db.close()
    return render_template('index.html', apps=recent_apps, stats=stats)

@app.route('/alerts')
def dashboard_alerts():
    return render_template('alerts.html')

@app.route('/api/stats')
def api_stats():
    return jsonify(get_stats())

@app.route('/api/applications')
def api_applications():
    db = SessionLocal()
    apps = db.query(VisaApplication).order_by(desc(VisaApplication.updated_at)).all()
    result = []
    for app in apps:
        result.append({
            "id": app.id,
            "document_id": app.document_id,
            "file_name": app.file_name,
            "visa_subclass": app.visa_subclass,
            "status": app.status,
            "score": app.completeness_score,
            "analysis": app.ai_analysis,
            "processed_at": app.upload_date.strftime("%Y-%m-%d %H:%M:%S") if app.upload_date else "N/A",
            "applicant_id": app.applicant_id,
            "expiry_date": app.expiry_date.strftime("%Y-%m-%d") if app.expiry_date else None,
            # Add confidence scoring fields
            "confidence_score": app.confidence_score,
            "field_confidence": app.field_confidence,
            "ocr_metadata": app.ocr_metadata,
            "verification_status": app.verification_status,
            "verified_by": app.verified_by,
            "verified_at": app.verified_at.strftime("%Y-%m-%d %H:%M:%S") if app.verified_at else None
        })
    db.close()
    return jsonify(result)

@app.route('/api/checklist/<subclass>')
def api_checklist(subclass):
    db = SessionLocal()
    from services.database_service import DocumentChecklist
    items = db.query(DocumentChecklist).filter(DocumentChecklist.visa_subclass == subclass).all()
    result = []
    for item in items:
        result.append({
            "name": item.document_name,
            "required": item.is_required,
            "category": item.category,
            "desc": item.description
        })
    db.close()
    return jsonify(result)

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """AI Assistant chat endpoint."""
    asst = get_assistant()
    if not asst:
        return jsonify({
            'error': 'AI Assistant not available. Please set TAVILY_API_KEY in .env file.'
        }), 503
    
    data = request.json
    user_message = data.get('message', '')
    context = data.get('context', None)
    
    if not user_message:
        return jsonify({'error': 'Message is required'}), 400
    
    response = asst.chat(user_message, context=context)
    return jsonify(response)

@app.route('/api/chat/document-help', methods=['POST'])
def api_document_help():
    """Get AI help for a specific document."""
    asst = get_assistant()
    if not asst:
        return jsonify({
            'error': 'AI Assistant not available. Please set TAVILY_API_KEY in .env file.'
        }), 503
    
    data = request.json
    document_type = data.get('document_type', '')
    visa_subclass = data.get('visa_subclass', '')
    analysis = data.get('analysis', None)
    
    if not document_type or not visa_subclass:
        return jsonify({'error': 'document_type and visa_subclass are required'}), 400
    
    response = asst.get_document_help(document_type, visa_subclass, analysis)
    return jsonify(response)

@app.route('/api/applicant/<int:applicant_id>/readiness')
def api_applicant_readiness(applicant_id):
    """Generate or retrieve readiness report for an applicant."""
    db = SessionLocal()
    from services.database_service import get_application_summary
    applicant = db.query(Applicant).filter(Applicant.id == applicant_id).first()
    if not applicant:
        db.close()
        return jsonify({'error': 'Applicant not found'}), 404
    
    documents = get_application_summary(db, applicant_id)
    if not documents:
        db.close()
        return jsonify({'error': 'No documents found for this applicant'}), 404
    
    asst = get_assistant()
    if not asst:
        db.close()
        return jsonify({'error': 'Assistant not available'}), 503
    
    # Use the first document's subclass as the target (simplification)
    visa_subclass = documents[0].visa_subclass
    report = asst.generate_readiness_report(applicant.full_name, visa_subclass, documents)
    
    db.close()
    return jsonify(report)

@app.route('/api/chat/clear', methods=['POST'])
def api_chat_clear():
    """Clear chat history."""
    asst = get_assistant()
    if asst:
        asst.clear_history()
    return jsonify({'status': 'ok'})

# ============ Verification Endpoints ============

@app.route('/api/verifications/pending')
def api_pending_verifications():
    """Get documents requiring manual verification."""
    applicant_id = request.args.get('applicant_id')
    verification_service = VerificationService()
    pending = verification_service.get_pending_verifications(applicant_id)
    
    result = []
    for doc in pending:
        result.append({
            "id": doc.id,
            "document_id": doc.document_id,
            "file_name": doc.file_name,
            "confidence_score": doc.confidence_score,
            "field_confidence": doc.field_confidence,
            "ocr_metadata": doc.ocr_metadata,
            "verification_status": doc.verification_status,
            "analysis": doc.ai_analysis,
            "upload_date": doc.upload_date.strftime("%Y-%m-%d %H:%M:%S") if doc.upload_date else None
        })
    
    return jsonify(result)

@app.route('/api/verifications/<document_id>/approve', methods=['POST'])
def api_approve_verification(document_id):
    """Approve a document extraction."""
    data = request.json
    verified_by = data.get('verified_by', 'admin')
    notes = data.get('notes')
    
    verification_service = VerificationService()
    result = verification_service.approve_extraction(document_id, verified_by, notes)
    
    if result:
        return jsonify({
            "status": "approved",
            "document_id": document_id,
            "verified_at": result.verified_at.strftime("%Y-%m-%d %H:%M:%S") if result.verified_at else None
        })
    else:
        return jsonify({"error": "Document not found"}), 404

@app.route('/api/verifications/<document_id>/reject', methods=['POST'])
def api_reject_verification(document_id):
    """Reject a document extraction."""
    data = request.json
    verified_by = data.get('verified_by', 'admin')
    reason = data.get('reason', 'No reason provided')
    reprocess = data.get('reprocess', True)
    
    verification_service = VerificationService()
    result = verification_service.reject_and_reprocess(document_id, verified_by, reason, reprocess)
    
    if result:
        return jsonify({
            "status": "rejected",
            "document_id": document_id,
            "reprocess": reprocess
        })
    else:
        return jsonify({"error": "Document not found"}), 404

@app.route('/api/verifications/stats')
def api_verification_stats():
    """Get verification statistics."""
    applicant_id = request.args.get('applicant_id')
    verification_service = VerificationService()
    stats = verification_service.get_verification_stats(applicant_id)
    return jsonify(stats)

# ============ Notification Endpoints ============

@app.route('/api/notifications')
def api_notifications():
    """Get notifications for an applicant."""
    applicant_id = request.args.get('applicant_id')
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    
    if not applicant_id:
        return jsonify({"error": "applicant_id is required"}), 400
    
    notification_service = NotificationService()
    notifications = notification_service.get_applicant_notifications(applicant_id, unread_only)
    
    result = []
    for notif in notifications:
        result.append({
            "id": notif.id,
            "type": notif.notification_type,
            "severity": notif.severity,
            "message": notif.message,
            "sent_at": notif.sent_at.strftime("%Y-%m-%d %H:%M:%S") if notif.sent_at else None,
            "read_at": notif.read_at.strftime("%Y-%m-%d %H:%M:%S") if notif.read_at else None,
            "document_id": notif.document_id
        })
    
    return jsonify(result)

@app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
def api_mark_notification_read(notification_id):
    """Mark a notification as read."""
    notification_service = NotificationService()
    success = notification_service.mark_notification_read(notification_id)
    
    if success:
        return jsonify({"status": "marked_read", "notification_id": notification_id})
    else:
        return jsonify({"error": "Notification not found or already read"}), 404

@app.route('/api/notifications/<int:notification_id>/dismiss', methods=['POST'])
def api_dismiss_notification(notification_id):
    """Dismiss a notification."""
    notification_service = NotificationService()
    success = notification_service.dismiss_notification(notification_id)
    
    if success:
        return jsonify({"status": "dismissed", "notification_id": notification_id})
    else:
        return jsonify({"error": "Notification not found"}), 404

@app.route('/api/notifications/stats')
def api_notification_stats():
    """Get notification statistics."""
    applicant_id = request.args.get('applicant_id')
    notification_service = NotificationService()
    stats = notification_service.get_notification_stats(applicant_id)
    return jsonify(stats)

@app.route('/api/notifications/check', methods=['POST'])
def api_check_notifications():
    """Manually trigger notification checks."""
    notification_service = NotificationService()
    
    expiry_count = notification_service.check_expiring_documents()
    verification_count = notification_service.check_verification_needed()
    
    return jsonify({
        "expiry_notifications_created": expiry_count,
        "verification_notifications_created": verification_count,
        "total": expiry_count + verification_count
    })


# ============================================================================
# CLIENT ALERT EMAIL ENDPOINTS
# ============================================================================

@app.route('/api/alerts/generate', methods=['POST'])
def generate_client_alerts():
    """Generate AI-powered alert emails for documents needing attention"""
    alert_service = ClientAlertService()
    data = request.json or {}
    
    alert_type = data.get('type', 'all')  # all, low_confidence, expiring, missing_elements
    threshold = data.get('threshold', 70)
    days = data.get('days', 90)
    
    results = {
        "low_confidence": 0,
        "expiring": 0,
        "missing_elements": 0
    }
    
    if alert_type in ['all', 'low_confidence']:
        results['low_confidence'] = alert_service.send_alerts_for_low_confidence_documents(threshold)
    
    if alert_type in ['all', 'expiring']:
        results['expiring'] = alert_service.send_alerts_for_expiring_documents(days)
    
    if alert_type in ['all', 'missing_elements']:
        results['missing_elements'] = alert_service.send_alerts_for_missing_elements()
    
    return jsonify({
        "success": True,
        "alerts_generated": sum(results.values()),
        "breakdown": results
    })

@app.route('/api/alerts/history', methods=['GET'])
def get_alert_history():
    """Get history of sent AI alerts"""
    db = SessionLocal()
    notifications = db.query(Notification).filter(
        Notification.notification_type.like('ai_alert_%')
    ).order_by(desc(Notification.sent_at)).limit(50).all()
    
    result = []
    for n in notifications:
        result.append({
            "id": n.id,
            "applicant_id": n.applicant_id,
            "document_id": n.document_id,
            "type": n.notification_type,
            "message": n.message,
            "sent_at": n.sent_at.strftime("%Y-%m-%d %H:%M:%S") if n.sent_at else None
        })
    db.close()
    return jsonify(result)

@app.route('/api/alerts/send', methods=['POST'])
def send_client_alert():
    """Send a specific alert that has been reviewed (and potentially edited)"""
    data = request.json or {}
    document_id = data.get('document_id')
    issue_type = data.get('type', 'missing_elements')
    
    # Custom fields from user edits
    custom_subject = data.get('subject')
    custom_body = data.get('body')
    custom_email = data.get('recipient_email')
    
    if not document_id:
        return jsonify({"error": "Document ID required"}), 400
        
    db = SessionLocal()
    document = db.query(VisaApplication).filter(VisaApplication.id == document_id).first()
    
    if not document:
        db.close()
        return jsonify({"error": "Document not found"}), 404
        
    applicant = db.query(Applicant).filter(Applicant.id == document.applicant_id).first()
    
    # Use custom email if provided, otherwise fallback to database
    recipient_email = custom_email or (applicant.email if applicant else None)
    
    if not recipient_email:
        db.close()
        return jsonify({"error": "Applicant email not found and no override provided"}), 400
        
    alert_service = ClientAlertService()
    
    # Map type if needed
    if issue_type == 'missing': issue_type = 'missing_elements'
    if issue_type == 'confidence': issue_type = 'low_confidence'
    
    # Create a temporary applicant-like object if we have a custom email
    # or just use the existing one but with the target email
    class TempApplicant:
        def __init__(self, id, full_name, email):
            self.id = id
            self.full_name = full_name
            self.email = email
            
    # Use existing applicant info but with potential email override
    display_name = applicant.full_name if applicant else "Valued Client"
    target_applicant = TempApplicant(document.applicant_id, display_name, recipient_email)

    # Determine email content - use custom edits or generate new
    if custom_subject or custom_body:
        # If any part is custom, we might need to get the "original" to fill the gaps
        # but usually the frontend sends both if it's editing. 
        # Let's be safe and generate the original if something is missing.
        original_content = None
        
        final_subject = custom_subject
        final_body = custom_body
        
        if not final_subject or not final_body:
            original_content = alert_service.generate_alert_email(document, issue_type, target_applicant)
            if not final_subject: final_subject = original_content['subject']
            if not final_body: final_body = original_content['body']
            
        email_content = {
            "subject": final_subject,
            "body": final_body
        }
    else:
        email_content = alert_service.generate_alert_email(document, issue_type, target_applicant)
    
    success = alert_service.send_email(target_applicant, document, email_content, issue_type)
    
    db.close()
    if success:
        return jsonify({"success": True, "message": "Email sent successfully"})
    else:
        return jsonify({"error": "Failed to send email"}), 500

@app.route('/api/alerts/preview/<int:document_id>', methods=['GET'])
def preview_alert_email(document_id):
    """Preview the AI-generated email for a specific document"""
    db = SessionLocal()
    document = db.query(VisaApplication).filter(VisaApplication.id == document_id).first()
    
    if not document:
        db.close()
        return jsonify({"error": "Document not found"}), 404
        
    applicant = db.query(Applicant).filter(Applicant.id == document.applicant_id).first()
    
    alert_service = ClientAlertService()
    issue_type = request.args.get('type', 'missing_elements')
    
    email_content = alert_service.generate_alert_email(document, issue_type, applicant)
    
    db.close()
    return jsonify({
        "document_id": document_id,
        "file_name": document.file_name,
        "applicant": {
            "name": applicant.full_name if applicant else "Unknown",
            "email": applicant.email if applicant else "No Email Registered"
        },
        "email": email_content
    })

if __name__ == '__main__':
    # Initialize AI Assistant
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key:
        print("Warning: TAVILY_API_KEY not set. AI Assistant features may be limited.")
    
    # Start the app
    print("Starting Australia Visa Agent Dashboard...")
    print("Dashboard available at: http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=False)
