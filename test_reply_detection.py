#!/usr/bin/env python3
"""
Test Gmail Reply Detection
Manually test the reply monitoring system
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.gmail_reply_monitor import GmailReplyMonitor
from datetime import datetime

def test_reply_detection():
    """Test the Gmail reply monitor"""
    print("=" * 80)
    print(f"TESTING GMAIL REPLY DETECTION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # Initialize monitor
    monitor = GmailReplyMonitor()
    
    # Check for replies
    count = monitor.monitor_all_replies()
    
    print()
    print("=" * 80)
    print(f"✅ Test complete! Detected {count} customer reply(ies)")
    print("=" * 80)
    print()
    print("Check your Google Sheets to see:")
    print("  - 'Response Received' column updated to 'Yes' (green)")
    print("  - 'Status' column shows 'Response Received (timestamp)'")

if __name__ == "__main__":
    test_reply_detection()
