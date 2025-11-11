# PDF Text Extraction Module
#
# This module handles the extraction of text from PDF documents with
# OCR fallback capabilities for scanned or image-based PDFs.

import io
import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from dataclasses import dataclass
import re
from datetime import datetime

# PDF processing
try:
    # Try pdfminer.six first (newer, Python 3 compatible)
    from pdfminer.high_level import extract_text
    from pdfminer.pdfparser import PDFParser
    from pdfminer.pdfdocument import PDFDocument
    from pdfminer.pdfpage import PDFPage
    from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
    from pdfminer.converter import TextConverter
except ImportError:
    # Fallback to older pdfminer if pdfminer.six not available
    from pdfminer.high_level import extract_text
    from pdfminer.pdfparser import PDFParser
    from pdfminer.pdfdocument import PDFDocument
    from pdfminer.pdfpage import PDFPage
    from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
    from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams

# OCR fallback
try:
    import pytesseract
    from PIL import Image
    import fitz  # PyMuPDF for better PDF image extraction
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    fitz = None
    pytesseract = None

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.text_cleaning import TextQualityChecker, TextQualityMetrics, HTMLCleaner

logger = logging.getLogger(__name__)


@dataclass
class PDFMetadata:
    """Metadata extracted from PDF documents."""
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    creation_date: Optional[str] = None
    modification_date: Optional[str] = None
    pages: int = 0
    encrypted: bool = False
    file_size: int = 0


@dataclass
class PDFExtractionResult:
    """Result of PDF text extraction."""
    text: str
    metadata: PDFMetadata
    quality_metrics: TextQualityMetrics
    extraction_method: str  # 'direct', 'ocr', 'hybrid'
    confidence_score: float  # 0-100, higher is better
    processing_time: float
    errors: List[str]


class PDFTextExtractor:
    """
    Extract text from PDF documents with OCR fallback.

    Features:
    - Direct text extraction from searchable PDFs
    - OCR processing for scanned/image PDFs
    - Quality assessment and confidence scoring
    - Metadata extraction
    """

    def __init__(self,
                 ocr_fallback: bool = True,
                 ocr_min_confidence: float = 60.0,
                 tesseract_config: str = '--oem 3 --psm 6'):
        """
        Initialize the PDF extractor.

        Args:
            ocr_fallback: Whether to use OCR for PDFs with low text confidence
            ocr_min_confidence: Minimum confidence score to skip OCR
            tesseract_config: Tesseract OCR configuration string
        """
        self.ocr_fallback = ocr_fallback and OCR_AVAILABLE
        self.ocr_min_confidence = ocr_min_confidence
        self.tesseract_config = tesseract_config

        if not OCR_AVAILABLE and ocr_fallback:
            logger.warning("OCR dependencies not available. OCR fallback disabled.")

    def extract_from_pdf(self, pdf_content: bytes, filename: Optional[str] = None) -> PDFExtractionResult:
        """
        Extract text from PDF content.

        Args:
            pdf_content: Raw PDF file bytes
            filename: Original filename for context

        Returns:
            PDFExtractionResult with extracted text and metadata
        """
        start_time = datetime.now()
        errors = []

        try:
            # Extract metadata first
            metadata = self._extract_metadata(pdf_content)

            # Try direct text extraction
            direct_text, direct_confidence = self._extract_text_direct(pdf_content)

            extraction_method = 'direct'
            final_text = direct_text
            confidence_score = direct_confidence

            # Use OCR fallback if confidence is low and OCR is available
            if (self.ocr_fallback and
                direct_confidence < self.ocr_min_confidence and
                len(direct_text.strip()) < 1000):  # Also check if we got minimal text

                logger.info(f"Low confidence ({direct_confidence:.1f}) for direct extraction, trying OCR")
                ocr_text, ocr_confidence = self._extract_text_ocr(pdf_content)

                if ocr_confidence > direct_confidence:
                    extraction_method = 'ocr'
                    final_text = ocr_text
                    confidence_score = ocr_confidence
                elif ocr_text and len(ocr_text.strip()) > len(direct_text.strip()):
                    # Use hybrid approach if OCR provides more text
                    extraction_method = 'hybrid'
                    final_text = self._merge_texts(direct_text, ocr_text)
                    confidence_score = max(direct_confidence, ocr_confidence)

            # Clean the final text
            final_text = self._clean_extracted_text(final_text)

            # Calculate quality metrics
            quality_metrics = self._calculate_quality_metrics(final_text)

            processing_time = (datetime.now() - start_time).total_seconds()

            return PDFExtractionResult(
                text=final_text,
                metadata=metadata,
                quality_metrics=quality_metrics,
                extraction_method=extraction_method,
                confidence_score=confidence_score,
                processing_time=processing_time,
                errors=errors
            )

        except Exception as e:
            error_msg = f"PDF extraction failed: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

            processing_time = (datetime.now() - start_time).total_seconds()

            return PDFExtractionResult(
                text="",
                metadata=PDFMetadata(),
                quality_metrics=TextQualityMetrics(),
                extraction_method='failed',
                confidence_score=0.0,
                processing_time=processing_time,
                errors=errors
            )

    def _extract_metadata(self, pdf_content: bytes) -> PDFMetadata:
        """Extract metadata from PDF."""
        try:
            pdf_file = io.BytesIO(pdf_content)
            parser = PDFParser(pdf_file)
            document = PDFDocument(parser)

            metadata = PDFMetadata()

            if document.info:
                info = document.info[0]  # PDF metadata is stored as lists
                metadata.title = self._decode_pdf_string(info.get('Title', ''))
                metadata.author = self._decode_pdf_string(info.get('Author', ''))
                metadata.subject = self._decode_pdf_string(info.get('Subject', ''))
                metadata.creator = self._decode_pdf_string(info.get('Creator', ''))
                metadata.producer = self._decode_pdf_string(info.get('Producer', ''))

                # Handle date fields
                creation_date = info.get('CreationDate', '')
                mod_date = info.get('ModDate', '')
                metadata.creation_date = self._parse_pdf_date(creation_date)
                metadata.modification_date = self._parse_pdf_date(mod_date)

            # Count pages
            metadata.pages = len(list(PDFPage.create_pages(document)))
            metadata.file_size = len(pdf_content)
            metadata.encrypted = document.is_encrypted

            return metadata

        except Exception as e:
            logger.warning(f"Failed to extract PDF metadata: {e}")
            return PDFMetadata()

    def _extract_text_direct(self, pdf_content: bytes) -> Tuple[str, float]:
        """
        Extract text directly from PDF using pdfminer.

        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        try:
            # Use pdfminer's high-level API
            text = extract_text(io.BytesIO(pdf_content))

            # Calculate confidence based on text characteristics
            confidence = self._calculate_text_confidence(text)

            return text, confidence

        except Exception as e:
            logger.warning(f"Direct PDF text extraction failed: {e}")
            return "", 0.0

    def _extract_text_ocr(self, pdf_content: bytes) -> Tuple[str, float]:
        """
        Extract text from PDF using OCR.

        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        if not OCR_AVAILABLE:
            return "", 0.0

        try:
            # Open PDF with PyMuPDF
            pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
            extracted_text = []
            total_confidence = 0.0
            page_count = 0

            for page_num in range(min(len(pdf_document), 50)):  # Limit to first 50 pages
                page = pdf_document.load_page(page_num)

                # Convert page to image
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x scaling for better OCR
                img = Image.open(io.BytesIO(pix.tobytes()))

                # Perform OCR
                page_text = pytesseract.image_to_string(img, config=self.tesseract_config)
                page_data = pytesseract.image_to_data(img, config=self.tesseract_config, output_type=pytesseract.Output.DICT)

                # Calculate average confidence for this page
                confidences = [int(conf) for conf in page_data['conf'] if conf != '-1']
                page_confidence = sum(confidences) / len(confidences) if confidences else 0

                extracted_text.append(page_text)
                total_confidence += page_confidence
                page_count += 1

            pdf_document.close()

            final_text = '\n\n'.join(extracted_text)
            avg_confidence = total_confidence / page_count if page_count > 0 else 0

            return final_text, avg_confidence

        except Exception as e:
            logger.warning(f"OCR PDF text extraction failed: {e}")
            return "", 0.0

    def _merge_texts(self, direct_text: str, ocr_text: str) -> str:
        """
        Merge direct and OCR extracted texts intelligently.

        Prefers direct text where available, falls back to OCR.
        """
        if not direct_text:
            return ocr_text
        if not ocr_text:
            return direct_text

        # For now, use a simple approach: prefer longer, higher quality text
        direct_quality = self._calculate_quality_metrics(direct_text)
        ocr_quality = self._calculate_quality_metrics(ocr_text)

        if direct_quality.has_meaningful_content and not ocr_quality.has_meaningful_content:
            return direct_text
        elif ocr_quality.has_meaningful_content and not direct_quality.has_meaningful_content:
            return ocr_text
        else:
            # Return the longer text
            return direct_text if len(direct_text) >= len(ocr_text) else ocr_text

    def _calculate_text_confidence(self, text: str) -> float:
        """
        Calculate confidence score for extracted text.

        Returns:
            Confidence score between 0-100
        """
        if not text or not text.strip():
            return 0.0

        # Basic heuristics for text quality
        words = re.findall(r'\b\w+\b', text)
        chars = len(text)

        if not words:
            return 0.0

        # Average word length (good text has reasonable word lengths)
        avg_word_len = sum(len(word) for word in words) / len(words)

        # Ratio of alphabetic characters
        alpha_ratio = sum(1 for c in text if c.isalpha()) / chars

        # Penalize very short or very long average word lengths
        word_len_score = max(0, 100 - abs(avg_word_len - 5) * 10)

        # Reward high alphabetic content
        alpha_score = alpha_ratio * 100

        # Combine scores
        confidence = (word_len_score * 0.4 + alpha_score * 0.6)

        return min(100.0, max(0.0, confidence))

    def _calculate_quality_metrics(self, text: str) -> TextQualityMetrics:
        """Calculate quality metrics for extracted text."""
        from ..utils.text_cleaning import HTMLCleaner
        cleaner = HTMLCleaner()
        return cleaner._calculate_quality_metrics(text)

    def _clean_extracted_text(self, text: str) -> str:
        """Clean and normalize extracted PDF text."""
        if not text:
            return ""

        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)

        # Remove page headers/footers (common PDF artifacts)
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Skip very short lines that might be headers/footers
            if len(line) < 5:
                continue

            # Skip lines that look like page numbers
            if re.match(r'^\d+$', line) and len(line) <= 4:
                continue

            cleaned_lines.append(line)

        return '\n'.join(cleaned_lines).strip()

    def _decode_pdf_string(self, pdf_string) -> str:
        """Decode PDF string objects."""
        if isinstance(pdf_string, bytes):
            try:
                return pdf_string.decode('utf-8')
            except UnicodeDecodeError:
                return pdf_string.decode('latin-1', errors='ignore')
        elif isinstance(pdf_string, str):
            return pdf_string
        else:
            return str(pdf_string) if pdf_string else ""

    def _parse_pdf_date(self, date_string) -> Optional[str]:
        """Parse PDF date format (D:YYYYMMDDHHMMSS)."""
        if not date_string:
            return None

        try:
            # PDF dates start with 'D:'
            if isinstance(date_string, str) and date_string.startswith('D:'):
                date_part = date_string[2:16]  # YYYYMMDDHHMMSS
                if len(date_part) >= 8:
                    # Parse as YYYY-MM-DD HH:MM:SS
                    year = date_part[0:4]
                    month = date_part[4:6]
                    day = date_part[6:8]
                    hour = date_part[8:10] if len(date_part) > 8 else '00'
                    minute = date_part[10:12] if len(date_part) > 10 else '00'
                    second = date_part[12:14] if len(date_part) > 12 else '00'

                    return f"{year}-{month}-{day} {hour}:{minute}:{second}"
        except:
            pass

        return None


# Convenience functions
def extract_text_from_pdf(pdf_content: bytes, filename: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract text from PDF with automatic OCR fallback.

    Args:
        pdf_content: Raw PDF bytes
        filename: Original filename

    Returns:
        Dictionary with extraction results
    """
    extractor = PDFTextExtractor()
    result = extractor.extract_from_pdf(pdf_content, filename)

    return {
        'text': result.text,
        'metadata': {
            'title': result.metadata.title,
            'author': result.metadata.author,
            'pages': result.metadata.pages,
            'extraction_method': result.extraction_method,
            'confidence_score': result.confidence_score,
            'processing_time': result.processing_time,
        },
        'quality_metrics': {
            'total_chars': result.quality_metrics.total_chars,
            'total_words': result.quality_metrics.total_words,
            'has_meaningful_content': result.quality_metrics.has_meaningful_content,
        },
        'extraction_success': len(result.errors) == 0,
        'errors': result.errors,
    }


if __name__ == '__main__':
    # Example usage
    extractor = PDFTextExtractor()

    # This would normally load a real PDF file
    print("PDF Text Extractor initialized")
    print(f"OCR Available: {OCR_AVAILABLE}")

    # Test metadata extraction with empty content (would fail gracefully)
    empty_result = extractor.extract_from_pdf(b'', 'test.pdf')
    print(f"Empty PDF result: {len(empty_result.errors)} errors")
