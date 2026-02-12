import os, zipfile, shutil, json, sys
from core.utils import extract_text_from_pdf
from services.openai_service import OpenAIService

def trace(msg):
    print(f"TRACE: {msg}", flush=True)

try:
    trace("Initializing OpenAIService...")
    openai = OpenAIService()
    
    # 1. Prepare scanned PDF
    pdf_path = 'scanned_test_2.pdf'
    archive_path = 'tmp_Notaries.zip'
    
    trace(f"Extracting 'Notaries/SMMO csc.pdf' from {archive_path}...")
    with zipfile.ZipFile(archive_path, 'r') as zf:
        zf.extract('Notaries/SMMO csc.pdf', '.')
        os.rename('Notaries/SMMO csc.pdf', pdf_path)
        os.rmdir('Notaries')

    trace(f"File size: {os.path.getsize(pdf_path)} bytes")

    # 2. Test OCR Fallback
    trace("Starting AI OCR fallback process. This may take a moment...")
    text = extract_text_from_pdf(pdf_path, openai_service=openai)
    
    if text and text.strip():
        trace(f"OCR SUCCESS! Extracted {len(text)} characters.")
        trace(f"Result snippet: {text[:300]}...")
        
        # 3. Test Enhanced Analysis
        trace("Starting Enhanced AI Analysis...")
        analysis = openai.analyze_document(text, "600", "Government Document")
        trace("Analysis complete. Results:")
        print(json.dumps(analysis, indent=2), flush=True)
    else:
        trace("OCR FAILED: No text extracted.")

except Exception as e:
    trace(f"CRITICAL ERROR: {str(e)}")

finally:
    if os.path.exists('scanned_test_2.pdf'):
        os.remove('scanned_test_2.pdf')
        trace("Cleaned up PDF.")
    trace("Script finished.")

