import PyPDF2
import os
import zipfile
import rarfile

def extract_text_from_pdf(pdf_path, openai_service=None, force_ocr=False):
    """
    Extracts text from a PDF file. 
    If direct extraction fails (scanned document) or force_ocr is True, falls back to AI OCR.
    Returns tuple: (text, ocr_metadata) where ocr_metadata contains confidence info if OCR was used.
    """
    import fitz  # PyMuPDF
    text = ""
    ocr_metadata = None
    
    try:
        # 1. Try direct extraction (skip if force_ocr is True)
        if not force_ocr:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                num_pages = len(reader.pages)
                if num_pages == 0:
                    print(f"Warning: PDF {pdf_path} has 0 pages.")
                    return "", None
                
                for page_num in range(num_pages):
                    page_text = reader.pages[page_num].extract_text()
                    if page_text:
                        text += page_text
        
        # 2. Fallback to OCR if no text found, text is very sparse, OR force_ocr is True
        # < 200 characters usually means just a header/footer was extracted but the main content is image
        if (force_ocr or not text.strip() or len(text.strip()) < 200) and openai_service:
            reason = "Force OCR requested" if force_ocr else f"Insufficient text ({len(text.strip())} chars)"
            print(f"  → {reason} for {os.path.basename(pdf_path)}. Falling back to AI OCR...")
            doc = fitz.open(pdf_path)
            temp_images = []
            
            # Convert pages to images (limit to first 10 pages for cost/performance)
            for i in range(min(len(doc), 10)):
                page = doc.load_page(i)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # High res for OCR
                img_path = f"tmp_page_{i}.jpg"
                pix.save(img_path)
                temp_images.append(img_path)
            
            # Use OpenAI Vision for OCR - now returns dict with confidence
            ocr_result = openai_service.ocr_from_images(temp_images)
            
            if isinstance(ocr_result, dict):
                text = ocr_result.get("transcribed_text", "")
                ocr_metadata = {
                    "ocr_confidence": ocr_result.get("ocr_confidence", 0),
                    "quality_issues": ocr_result.get("quality_issues", []),
                    "text_clarity": ocr_result.get("text_clarity", "unknown"),
                    "ocr_used": True
                }
            else:
                # Fallback for old format (plain string)
                text = str(ocr_result)
                ocr_metadata = {"ocr_used": True, "ocr_confidence": 50}
            
            # Cleanup temp images
            for img in temp_images:
                if os.path.exists(img):
                    os.remove(img)
            doc.close()
            
    except Exception as e:
        print(f"Error extracting text from PDF {pdf_path}: {e}")
    
    return text, ocr_metadata


def get_file_extension(file_path):
    """Returns the file extension."""
    return os.path.splitext(file_path)[1].lower()

def is_archive(file_path):
    """Check if file is a ZIP or RAR archive."""
    ext = get_file_extension(file_path)
    return ext in ['.zip', '.rar']

def extract_archive(archive_path, extract_dir):
    """
    Extract archive contents to specified directory.
    Returns list of extracted file paths.
    """
    extracted_files = []
    ext = get_file_extension(archive_path)
    
    try:
        os.makedirs(extract_dir, exist_ok=True)
        
        if ext == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
                extracted_files = [os.path.join(extract_dir, name) for name in zip_ref.namelist() if not name.endswith('/')]
        
        elif ext == '.rar':
            with rarfile.RarFile(archive_path, 'r') as rar_ref:
                rar_ref.extractall(extract_dir)
                extracted_files = [os.path.join(extract_dir, name) for name in rar_ref.namelist() if not name.endswith('/')]
        
        print(f"Extracted {len(extracted_files)} files from {os.path.basename(archive_path)}")
        return extracted_files
    
    except Exception as e:
        print(f"Error extracting archive {archive_path}: {e}")
        return []
