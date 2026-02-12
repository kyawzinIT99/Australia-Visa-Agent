#!/usr/bin/env python3
"""
Test Follow-up Service
Manually trigger follow-up email sending to test the system
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.followup_service import FollowupService
from datetime import datetime

def test_followup():
    """Test the follow-up service"""
    print("=" * 80)
    print(f"TESTING FOLLOW-UP SERVICE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # Initialize service
    service = FollowupService()
    
    # Send pending follow-ups
    count = service.send_pending_followups()
    
    print()
    print("=" * 80)
    print(f"✅ Test complete! Sent {count} follow-up email(s)")
    print("=" * 80)
    print()
    print("Check your Google Sheets to see the Status column updated!")
    print("Check the email inbox to see the follow-up email!")

if __name__ == "__main__":
    test_followup()
