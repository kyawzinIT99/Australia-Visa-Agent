
import unittest
from unittest.mock import MagicMock, patch, mock_open
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.agent import VisaAgent
from core.utils import extract_text_from_pdf

class TestOCRImprovements(unittest.TestCase):
    
    def setUp(self):
        # Patch dependencies for Agent
        self.patcher1 = patch('core.agent.GoogleDriveService')
        self.patcher2 = patch('core.agent.OpenAIService')
        self.patcher3 = patch('core.agent.SessionLocal')
        self.patcher4 = patch('core.agent.init_db')
        
        self.MockDrive = self.patcher1.start()
        self.MockOpenAI = self.patcher2.start()
        self.MockSession = self.patcher3.start()
        self.MockInitDB = self.patcher4.start()
        
        self.agent = VisaAgent()
        self.agent.db = MagicMock()
        self.agent.openai = MagicMock()
        self.agent.drive = MagicMock()

    def tearDown(self):
        patch.stopall()

    @patch('core.agent.extract_text_from_pdf')
    def test_image_file_processing(self, mock_extract_pdf):
        """Test that image files trigger OCR directly."""
        file_id = "test_img_id"
        file_name = "test_document.jpg"
        file_path = "/tmp/test_document.jpg"
        
        # Mock OCR response
        self.agent.openai.ocr_from_images.return_value = {
            "transcribed_text": "OCR Text Content",
            "ocr_confidence": 95
        }
        
        # Mock classification and analysis to avoid failures later in the function
        self.agent.openai.classify_document.return_value = {"document_type": "Passport", "visa_subclass": "500", "confidence": 0.9}
        self.agent.openai.analyze_document.return_value = {"completeness_score": 90, "confidence_score": 95}

        self.agent.process_single_document(file_id, file_name, file_path)

        # Verify OCR was called
        self.agent.openai.ocr_from_images.assert_called_once_with([file_path])
        # Verify extract_text_from_pdf was NOT called
        mock_extract_pdf.assert_not_called()

    @patch('core.utils.PyPDF2.PdfReader')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists', return_value=True)
    @patch('os.remove')
    def test_pdf_ocr_fallback_short_text(self, mock_remove, mock_exists, mock_file, mock_pdf_reader):
        """Test that PDF extraction falls back to OCR if text is too short."""
        pdf_path = "test_document.pdf"
        openai_service = MagicMock()
        
        # Setup PdfReader mock to return short text
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "   Short Text   " # < 200 chars
        mock_pdf_reader.return_value.pages = [mock_page]
        
        # Mock OCR response
        openai_service.ocr_from_images.return_value = {
            "transcribed_text": "Full OCR Text Content",
            "ocr_confidence": 90
        }
        
        # Mock fitz module in sys.modules
        mock_fitz = MagicMock()
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_fitz.open.return_value = mock_doc
        
        with patch.dict(sys.modules, {'fitz': mock_fitz}):
            text, metadata = extract_text_from_pdf(pdf_path, openai_service)

        # Verify expected behavior
        self.assertTrue(metadata['ocr_used'])
        self.assertEqual(text, "Full OCR Text Content")

    @patch('core.utils.PyPDF2.PdfReader')
    @patch('builtins.open', new_callable=mock_open)
    def test_pdf_direct_extraction_sufficient_text(self, mock_file, mock_pdf_reader):
        """Test that PDF extraction uses direct text if it's long enough."""
        pdf_path = "test_document.pdf"
        openai_service = MagicMock()
        
        # Generate text > 200 chars
        long_text = "A" * 250 
        mock_page = MagicMock()
        mock_page.extract_text.return_value = long_text
        mock_pdf_reader.return_value.pages = [mock_page]

        text, metadata = extract_text_from_pdf(pdf_path, openai_service)

        # Verify OCR was NOT triggered
        openai_service.ocr_from_images.assert_not_called()
        self.assertEqual(text, long_text)
        self.assertIsNone(metadata)

if __name__ == '__main__':
    unittest.main()
