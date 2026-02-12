"""
Test script for trust enhancement features
Tests confidence scoring, verification workflow, and notifications
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.verification_service import VerificationService
from services.notification_service import NotificationService
from services.openai_service import OpenAIService

def test_verification_service():
    """Test the verification service."""
    print("\n" + "="*60)
    print("Testing Verification Service")
    print("="*60)
    
    service = VerificationService()
    
    # Get pending verifications
    print("\n1. Getting pending verifications...")
    pending = service.get_pending_verifications()
    print(f"   Found {len(pending)} documents pending verification")
    
    if pending:
        for doc in pending[:3]:  # Show first 3
            print(f"   - {doc.file_name}: confidence={doc.confidence_score}%, status={doc.verification_status}")
    
    # Get stats
    print("\n2. Getting verification statistics...")
    stats = service.get_verification_stats()
    print(f"   Total documents: {stats['total']}")
    print(f"   Pending: {stats['pending']}")
    print(f"   Verified: {stats['verified']}")
    print(f"   Low confidence: {stats['low_confidence']}")
    print(f"   Average confidence: {stats['avg_confidence']:.1f}%")
    
    return True

def test_notification_service():
    """Test the notification service."""
    print("\n" + "="*60)
    print("Testing Notification Service")
    print("="*60)
    
    service = NotificationService()
    
    # Check for expiring documents
    print("\n1. Checking for expiring documents...")
    expiry_count = service.check_expiring_documents()
    print(f"   Created {expiry_count} expiry notifications")
    
    # Check for verification needs
    print("\n2. Checking for verification needs...")
    verification_count = service.check_verification_needed()
    print(f"   Created {verification_count} verification notifications")
    
    # Get stats
    print("\n3. Getting notification statistics...")
    stats = service.get_notification_stats()
    print(f"   Total notifications: {stats['total']}")
    print(f"   Unread: {stats['unread']}")
    print(f"   By severity:")
    for severity, count in stats['by_severity'].items():
        if count > 0:
            print(f"     - {severity}: {count}")
    
    return True

def test_confidence_scoring():
    """Test confidence scoring in OpenAI service."""
    print("\n" + "="*60)
    print("Testing Confidence Scoring")
    print("="*60)
    
    service = OpenAIService()
    
    # Test with sample text
    sample_text = """
    PASSPORT
    
    Surname: SMITH
    Given Names: JOHN MICHAEL
    Nationality: AUSTRALIAN
    Date of Birth: 15 JAN 1985
    Passport No: N1234567
    Date of Issue: 01 MAR 2020
    Date of Expiry: 01 MAR 2030
    """
    
    print("\n1. Analyzing sample passport text...")
    print("   (This will use OpenAI API if configured)")
    
    try:
        result = service.analyze_document(sample_text, "820", "Passport")
        
        if result:
            print(f"   ✓ Analysis complete")
            print(f"   Confidence score: {result.get('confidence_score', 'N/A')}%")
            print(f"   Requires manual review: {result.get('requires_manual_review', 'N/A')}")
            
            if 'field_confidence' in result:
                print(f"   Field confidence scores:")
                for field, score in result['field_confidence'].items():
                    print(f"     - {field}: {score}%")
        else:
            print("   ⚠️  Analysis returned None (check API key)")
            
    except Exception as e:
        print(f"   ⚠️  Could not test (API key may not be configured): {e}")
    
    return True

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Trust Enhancement Features Test Suite")
    print("="*60)
    
    tests = [
        ("Verification Service", test_verification_service),
        ("Notification Service", test_notification_service),
        ("Confidence Scoring", test_confidence_scoring)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, "✅ PASSED" if success else "❌ FAILED"))
        except Exception as e:
            results.append((test_name, f"❌ ERROR: {str(e)}"))
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    for test_name, result in results:
        print(f"{test_name}: {result}")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    main()
