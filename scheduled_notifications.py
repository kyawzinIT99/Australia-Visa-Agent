"""
Scheduled Notification Checker
Runs periodically to check for expiring documents and verification needs.
Can be run as a cron job or background service.
"""

import sys
import os
import time
import schedule
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.notification_service import NotificationService
from services.client_alert_service import ClientAlertService
from services.followup_service import FollowupService
from services.gmail_reply_monitor import GmailReplyMonitor

def check_notifications():
    """Main function to check and create notifications."""
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running notification check...")
    
    notification_service = NotificationService()
    alert_service = ClientAlertService()
    
    try:
        # 1. Standard Expiry Notifications (Internal Dashboard)
        expiry_count = notification_service.check_expiring_documents()
        print(f"  ✓ Created {expiry_count} internal expiry notifications")
        
        # 2. Manual Verification Notifications (Internal Dashboard)
        verification_count = notification_service.check_verification_needed()
        print(f"  ✓ Created {verification_count} internal verification notifications")
        
        # 3. AI-Powered Client Alerts (Outgoing Emails)
        print("  Running AI-Powered Client Alert checks...")
        
        # Low Confidence Alerts
        low_conf_alerts = alert_service.send_alerts_for_low_confidence_documents(threshold=70)
        print(f"  ✓ Sent {low_conf_alerts} AI-powered low confidence alerts")
        
        # Expiring Document Client Alerts
        expiring_alerts = alert_service.send_alerts_for_expiring_documents(days_threshold=90)
        print(f"  ✓ Sent {expiring_alerts} AI-powered expiry alerts")
        
        # Missing Elements Alerts
        missing_alerts = alert_service.send_alerts_for_missing_elements()
        print(f"  ✓ Sent {missing_alerts} AI-powered missing elements alerts")
        
        # 4. Follow-up Reminders (7+ days old)
        print("  Running Follow-up Reminder checks...")
        try:
            followup_service = FollowupService()
            followup_count = followup_service.send_pending_followups()
            print(f"  ✓ Sent {followup_count} follow-up reminders")
        except Exception as e:
            print(f"  ℹ Follow-up service not available: {e}")
            followup_count = 0
        
        # 5. Check for Customer Replies
        print("  Checking for customer replies...")
        try:
            reply_monitor = GmailReplyMonitor()
            replies_detected = reply_monitor.monitor_all_replies()
            print(f"  ✓ Detected {replies_detected} customer reply(ies)")
        except Exception as e:
            print(f"  ℹ Reply detection not available: {e}")
            replies_detected = 0
        
        total_internal = expiry_count + verification_count
        total_client = low_conf_alerts + expiring_alerts + missing_alerts + followup_count
        
        print(f"  📧 Internal notifications: {total_internal}")
        print(f"  ✉️  Client alerts sent: {total_client}")
        
    except Exception as e:
        print(f"  ❌ Error during notification check: {e}")
        import traceback
        traceback.print_exc()

def run_scheduler():
    """Run the scheduler continuously."""
    print("=" * 60)
    print("Notification Scheduler Started")
    print("=" * 60)
    print("Schedule: Every 6 hours")
    print("Press Ctrl+C to stop")
    print()
    
    # Schedule checks every 6 hours
    schedule.every(6).hours.do(check_notifications)
    
    # Also run once at startup
    check_notifications()
    
    # Keep running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n\nScheduler stopped by user.")

def run_once():
    """Run notification check once and exit."""
    print("=" * 60)
    print("Running One-Time Notification Check")
    print("=" * 60)
    check_notifications()
    print("\n✅ Check complete!")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Notification Checker')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--daemon', action='store_true', help='Run as continuous scheduler')
    
    args = parser.parse_args()
    
    if args.once:
        run_once()
    elif args.daemon:
        run_scheduler()
    else:
        # Default: run once
        run_once()
