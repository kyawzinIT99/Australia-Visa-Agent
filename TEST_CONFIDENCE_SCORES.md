# Quick Test: Verify Confidence Scores are Being Saved

This script tests that the agent properly saves confidence scores when processing documents.

```python
import sys
sys.path.insert(0, '/Users/berry/Antigravity/Australia Agent copy')

from services.database_service import SessionLocal, VisaApplication

db = SessionLocal()

# Get recent documents
recent_docs = db.query(VisaApplication).order_by(VisaApplication.updated_at.desc()).limit(5).all()

print("Recent Documents with Confidence Scores:")
print("=" * 80)

for doc in recent_docs:
    print(f"\nFile: {doc.file_name}")
    print(f"  Confidence Score: {doc.confidence_score}%")
    print(f"  Verification Status: {doc.verification_status}")
    print(f"  Field Confidence: {doc.field_confidence}")
    if doc.ocr_metadata:
        print(f"  OCR Used: {doc.ocr_metadata.get('ocr_used', False)}")
        print(f"  OCR Confidence: {doc.ocr_metadata.get('ocr_confidence', 'N/A')}")

db.close()
```

## Expected Result

After processing new documents, you should see:
- `confidence_score`: 0-100 value
- `verification_status`: 'pending' or 'verified'
- `field_confidence`: JSON with per-field scores
- `ocr_metadata`: OCR quality metrics (if OCR was used)

## How to Test

1. Upload a new document to Google Drive incoming folder
2. Wait for agent to process it (or run `python core/agent.py` manually)
3. Run this test script to verify confidence scores are saved
4. Check the dashboard API: `curl http://localhost:5001/api/verifications/pending`
