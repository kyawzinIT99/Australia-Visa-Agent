"""
Quick verification script to check if confidence scores are being saved
"""
import sys
sys.path.insert(0, '/Users/berry/Antigravity/Australia Agent copy')

from services.database_service import SessionLocal, VisaApplication

db = SessionLocal()

# Get recent documents
recent_docs = db.query(VisaApplication).order_by(VisaApplication.updated_at.desc()).limit(10).all()

print("\n" + "=" * 80)
print("Recent Documents - Confidence Score Status")
print("=" * 80)

has_confidence = 0
no_confidence = 0

for doc in recent_docs:
    if doc.confidence_score is not None:
        has_confidence += 1
        print(f"\n✅ {doc.file_name}")
        print(f"   Confidence: {doc.confidence_score}%")
        print(f"   Status: {doc.verification_status}")
        if doc.field_confidence:
            print(f"   Field Scores: {list(doc.field_confidence.keys())}")
    else:
        no_confidence += 1
        print(f"\n⚠️  {doc.file_name}")
        print(f"   Confidence: None (legacy document)")
        print(f"   Status: {doc.verification_status}")

print("\n" + "=" * 80)
print(f"Summary: {has_confidence} with confidence scores, {no_confidence} without")
print("=" * 80)

# Check if any documents need verification
pending = db.query(VisaApplication).filter(
    VisaApplication.verification_status == 'pending'
).count()

print(f"\n📋 Documents pending verification: {pending}")

db.close()
