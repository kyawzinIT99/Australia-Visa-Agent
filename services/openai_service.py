import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class OpenAIService:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            print("Warning: OPENAI_API_KEY not found in environment.")
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o-mini"

    def analyze_document(self, text, visa_subclass, document_type):
        """Analyzes a document against visa-specific requirements with detailed extraction and confidence scoring."""
        prompt = f"""
        You are an expert Australian Visa Compliance Officer. 
        Analyze the following text extracted from a {document_type} for a Subclass {visa_subclass} visa.
        
        Document Text:
        {text}
        
        Task:
        1. Verify if the document matches the expected type.
        2. Extract key data points:
           - Full Names of all parties mentioned
           - Important dates (Date of Birth, Issue Date, Expiry Date, Marriage Date, Notary/Translation/Authentication Date, etc.)
           - Specifically check for any "Valid Until", "Expiry", or "Validity" dates on Notary stamps or translation certificates.
           - Reference numbers (Passport Number, ID Number, Form numbers)
           - Presence of seals, stamps, or signatures
        3. Check for completeness based on standard Australian visa requirements for this type.
        4. Identify any missing elements or non-compliant information.
        5. Provide a completeness score (0-100).
        6. **IMPORTANT: Provide confidence scores (0-100) for each extracted field based on:**
           - Text clarity and readability
           - Presence of expected formatting (e.g., date formats, ID number patterns)
           - Consistency with document type expectations
           - Presence of verification elements (stamps, seals, signatures)
        7. Calculate an overall confidence score based on:
           - Text extraction quality
           - Field extraction confidence
           - Document completeness
           - Presence of expected elements
        
        Return the result in JSON format:
        {{
            "is_correct_type": bool,
            "document_type_detected": string,
            "extracted_data": {{
                "names": [list],
                "dates": {{ 
                    "date_of_birth": "YYYY-MM-DD",
                    "issue_date": "YYYY-MM-DD",
                    "expiry_date": "YYYY-MM-DD",
                    "translation_date": "YYYY-MM-DD",
                    "authentication_date": "YYYY-MM-DD",
                    "other_dates": {{ "type": "value" }}
                }},
                "reference_numbers": [list],
                "has_signature": bool,
                "has_official_seal": bool
            }},
            "field_confidence": {{
                "names": int (0-100),
                "dates": int (0-100),
                "reference_numbers": int (0-100),
                "signature_seal": int (0-100),
                "overall_text_quality": int (0-100)
            }},
            "confidence_score": int (0-100, weighted average of field confidences),
            "confidence_factors": {{
                "text_clarity": string (description),
                "format_consistency": string (description),
                "expected_elements_present": string (description)
            }},
            "completeness_score": int,
            "findings": [list of strings],
            "missing_elements": [list of strings],
            "compliance_status": "Passed" | "Partial" | "Failed",
            "detailed_justification": string,
            "summary": string,
            "requires_manual_review": bool (true if confidence_score < 70)
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional Australian visa document verifier. Extract as much specific data as possible and provide detailed confidence assessments."},
                    {"role": "user", "content": prompt}
                ],
                response_format={ "type": "json_object" }
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error in OpenAI analysis: {e}")
            return None


    def ocr_from_images(self, image_paths):
        """Performs OCR on multiple images using GPT-4o Vision with confidence assessment."""
        import base64
        
        content = [
            {
                "type": "text", 
                "text": """Please perform high-accuracy OCR on these document pages. 
                
                Transcribe all text exactly as it appears, including names, dates, and form headers.
                
                After transcription, provide a confidence assessment in JSON format:
                {{
                    "transcribed_text": "full text here",
                    "ocr_confidence": int (0-100),
                    "quality_issues": [list any issues like blur, poor scan quality, handwriting, etc.],
                    "text_clarity": "excellent" | "good" | "fair" | "poor"
                }}
                """
            }
        ]
        
        for img_path in image_paths:
            with open(img_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                })
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o", # Use full gpt-4o for vision
                messages=[
                    {"role": "system", "content": "You are a specialized OCR engine for immigration documents. Provide both transcription and quality assessment."},
                    {"role": "user", "content": content}
                ],
                max_tokens=4000,
                response_format={ "type": "json_object" }
            )
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            print(f"Error in OCR: {e}")
            return {"transcribed_text": "", "ocr_confidence": 0, "quality_issues": [str(e)], "text_clarity": "poor"}


    def classify_document(self, text):
        """Classifies the document type and potentially the visa subclass from extracted text."""
        prompt = f"""
        Analyze the following text from a document and identify what type of document it is 
        and if it references a specific Australian visa subclass.
        
        Text:
        {text[:2000]}
        
        Return the result in JSON format:
        {{
            "document_type": string,
            "visa_subclass": string or null,
            "confidence": float,
            "summary": string
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a document classification expert for Australian immigration."},
                    {"role": "user", "content": prompt}
                ],
                response_format={ "type": "json_object" }
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error in document classification: {e}")
            return None

if __name__ == "__main__":
    # Test initialization
    service = OpenAIService()
    print("OpenAI Service initialized.")
