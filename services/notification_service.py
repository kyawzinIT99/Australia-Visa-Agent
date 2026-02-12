import datetime
from services.database_service import SessionLocal, VisaApplication, Notification, NotificationPreferences, Applicant
from services.email_service import EmailService


class NotificationService:
    """Manages tiered notifications for expiring documents and verification needs."""
    
    def __init__(self):
        self.email_service = EmailService()
        self.default_alert_days = [90, 60, 30]  # Days before expiry to send alerts
    
    def check_expiring_documents(self):
        """
        Scans all documents and creates notifications for those approaching expiry.
        
        Returns:
            Number of notifications created
        """
        session = SessionLocal()
        notifications_created = 0
        
        try:
            now = datetime.datetime.now()
            
            # Get all documents with expiry dates
            documents = session.query(VisaApplication).filter(
                VisaApplication.expiry_date.isnot(None),
                VisaApplication.expiry_date > now
            ).all()
            
            for doc in documents:
                days_until_expiry = (doc.expiry_date - now).days
                
                # Get applicant's notification preferences
                prefs = session.query(NotificationPreferences).filter(
                    NotificationPreferences.applicant_id == doc.applicant_id
                ).first()
                
                alert_days = prefs.alert_days if prefs and prefs.alert_days else self.default_alert_days
                
                # Check if we should send a notification
                for threshold in alert_days:
                    if days_until_expiry <= threshold and days_until_expiry > threshold - 1:
                        # Check if notification already sent for this threshold
                        existing = session.query(Notification).filter(
                            Notification.document_id == doc.document_id,
                            Notification.notification_type == f'expiry_{threshold}d'
                        ).first()
                        
                        if not existing:
                            severity = self._get_severity(days_until_expiry)
                            message = self._create_expiry_message(doc, days_until_expiry)
                            
                            notification = Notification(
                                applicant_id=doc.applicant_id,
                                document_id=doc.document_id,
                                notification_type=f'expiry_{threshold}d',
                                severity=severity,
                                message=message
                            )
                            session.add(notification)
                            
                            # Send email if enabled
                            if prefs and prefs.email_enabled and 'email' in (prefs.notification_channels or []):
                                self._send_email_notification(doc, days_until_expiry, session)
                            
                            notifications_created += 1
            
            session.commit()
            return notifications_created
            
        except Exception as e:
            session.rollback()
            print(f"Error checking expiring documents: {e}")
            return 0
        finally:
            session.close()
    
    def check_verification_needed(self):
        """
        Creates notifications for documents requiring manual verification.
        
        Returns:
            Number of notifications created
        """
        session = SessionLocal()
        notifications_created = 0
        
        try:
            # Get documents with low confidence or pending verification
            documents = session.query(VisaApplication).filter(
                (VisaApplication.confidence_score < 70) |
                (VisaApplication.verification_status == 'pending')
            ).all()
            
            for doc in documents:
                # Check if notification already exists
                existing = session.query(Notification).filter(
                    Notification.document_id == doc.document_id,
                    Notification.notification_type == 'verification_needed',
                    Notification.dismissed_at.is_(None)
                ).first()
                
                if not existing:
                    message = f"Document '{doc.file_name}' requires manual verification (confidence: {doc.confidence_score}%)"
                    
                    notification = Notification(
                        applicant_id=doc.applicant_id,
                        document_id=doc.document_id,
                        notification_type='verification_needed',
                        severity='high',
                        message=message
                    )
                    session.add(notification)
                    notifications_created += 1
            
            session.commit()
            return notifications_created
            
        except Exception as e:
            session.rollback()
            print(f"Error checking verification needs: {e}")
            return 0
        finally:
            session.close()
    
    def get_applicant_notifications(self, applicant_id, unread_only=False):
        """
        Retrieves notifications for a specific applicant.
        
        Args:
            applicant_id: The applicant to get notifications for
            unread_only: If True, only return unread notifications
            
        Returns:
            List of Notification objects
        """
        session = SessionLocal()
        try:
            query = session.query(Notification).filter(
                Notification.applicant_id == applicant_id,
                Notification.dismissed_at.is_(None)
            )
            
            if unread_only:
                query = query.filter(Notification.read_at.is_(None))
            
            notifications = query.order_by(Notification.sent_at.desc()).all()
            return notifications
        finally:
            session.close()
    
    def mark_notification_read(self, notification_id):
        """Marks a notification as read."""
        session = SessionLocal()
        try:
            notification = session.query(Notification).filter(
                Notification.id == notification_id
            ).first()
            
            if notification and not notification.read_at:
                notification.read_at = datetime.datetime.now()
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    def dismiss_notification(self, notification_id):
        """Dismisses a notification."""
        session = SessionLocal()
        try:
            notification = session.query(Notification).filter(
                Notification.id == notification_id
            ).first()
            
            if notification:
                notification.dismissed_at = datetime.datetime.now()
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    def _get_severity(self, days_until_expiry):
        """Determines notification severity based on days until expiry."""
        if days_until_expiry <= 30:
            return 'critical'
        elif days_until_expiry <= 60:
            return 'high'
        elif days_until_expiry <= 90:
            return 'medium'
        else:
            return 'low'
    
    def _create_expiry_message(self, document, days_until_expiry):
        """Creates a user-friendly expiry notification message."""
        expiry_date = document.expiry_date.strftime('%Y-%m-%d')
        
        if days_until_expiry <= 7:
            urgency = "URGENT"
        elif days_until_expiry <= 30:
            urgency = "Important"
        else:
            urgency = "Reminder"
        
        return f"{urgency}: Document '{document.file_name}' expires in {days_until_expiry} days (on {expiry_date})"
    
    def _send_email_notification(self, document, days_until_expiry, session):
        """Sends an email notification for expiring document."""
        try:
            # Get applicant email
            applicant = session.query(Applicant).filter(
                Applicant.id == document.applicant_id
            ).first()
            
            if not applicant or not applicant.email:
                return
            
            subject = f"Document Expiry Alert - {days_until_expiry} days remaining"
            body = f"""
            Dear {applicant.full_name or 'Applicant'},
            
            This is an automated reminder that your document is approaching its expiry date:
            
            Document: {document.file_name}
            Document Type: {document.document_type}
            Expiry Date: {document.expiry_date.strftime('%Y-%m-%d')}
            Days Remaining: {days_until_expiry}
            
            Please ensure you renew or replace this document before it expires to avoid delays in your visa application.
            
            If you have already renewed this document, please upload the updated version to your application.
            
            Best regards,
            Australia Visa Agent
            """
            
            self.email_service.send_email(
                to_email=applicant.email,
                subject=subject,
                body=body
            )
            
        except Exception as e:
            print(f"Error sending email notification: {e}")
    
    def get_notification_stats(self, applicant_id=None):
        """
        Gets statistics about notifications.
        
        Returns:
            Dict with notification counts by type and severity
        """
        session = SessionLocal()
        try:
            query = session.query(Notification)
            if applicant_id:
                query = query.filter(Notification.applicant_id == applicant_id)
            
            all_notifications = query.all()
            
            stats = {
                'total': len(all_notifications),
                'unread': sum(1 for n in all_notifications if not n.read_at),
                'by_severity': {
                    'critical': sum(1 for n in all_notifications if n.severity == 'critical'),
                    'high': sum(1 for n in all_notifications if n.severity == 'high'),
                    'medium': sum(1 for n in all_notifications if n.severity == 'medium'),
                    'low': sum(1 for n in all_notifications if n.severity == 'low')
                },
                'by_type': {}
            }
            
            # Count by type
            for notification in all_notifications:
                ntype = notification.notification_type
                stats['by_type'][ntype] = stats['by_type'].get(ntype, 0) + 1
            
            return stats
        finally:
            session.close()


if __name__ == "__main__":
    # Test the service
    service = NotificationService()
    print("Notification Service initialized.")
    
    # Check for expiring documents
    created = service.check_expiring_documents()
    print(f"Created {created} expiry notifications")
    
    # Check for verification needs
    created = service.check_verification_needed()
    print(f"Created {created} verification notifications")
