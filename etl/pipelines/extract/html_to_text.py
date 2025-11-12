# HTML to Text Extraction Pipeline
#
# This module orchestrates the conversion of raw HTML and PDF documents
# into clean, structured text with metadata and quality assessment.

import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pathlib import Path
import hashlib

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from pipelines.extract.pdf_to_text import PDFTextExtractor, extract_text_from_pdf
from utils.text_cleaning import HTMLCleaner, TextQualityChecker, TextQualityMetrics
from utils.s3_upload import FlightSchoolS3Uploader

logger = logging.getLogger(__name__)


class DocumentExtractionResult:
    """
    Result of document text extraction and processing.
    """

    def __init__(self,
                 document_id: str,
                 source_name: str,
                 url: str,
                 document_type: str,  # 'html' or 'pdf'
                 extracted_text: str,
                 title: str = "",
                 metadata: Optional[Dict[str, Any]] = None,
                 quality_metrics: Optional[TextQualityMetrics] = None,
                 extraction_method: str = "",
                 confidence_score: float = 0.0,
                 processing_time: float = 0.0,
                 errors: Optional[List[str]] = None):
        """
        Initialize extraction result.

        Args:
            document_id: Unique identifier for the document
            source_name: Name of the data source
            url: Source URL
            document_type: Type of document ('html' or 'pdf')
            extracted_text: The cleaned, extracted text
            title: Document title
            metadata: Additional metadata
            quality_metrics: Text quality metrics
            extraction_method: Method used for extraction
            confidence_score: Confidence in extraction quality (0-100)
            processing_time: Time taken to process (seconds)
            errors: List of errors encountered
        """
        self.document_id = document_id
        self.source_name = source_name
        self.url = url
        self.document_type = document_type
        self.extracted_text = extracted_text
        self.title = title
        self.metadata = metadata or {}
        self.quality_metrics = quality_metrics or TextQualityMetrics()
        self.extraction_method = extraction_method
        self.confidence_score = confidence_score
        self.processing_time = processing_time
        self.errors = errors or []
        self.extraction_timestamp = datetime.now().isoformat()

    @property
    def extraction_success(self) -> bool:
        """Check if extraction was successful (no errors)."""
        return len(self.errors) == 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'document_id': self.document_id,
            'source_name': self.source_name,
            'url': self.url,
            'document_type': self.document_type,
            'title': self.title,
            'extracted_text': self.extracted_text,
            'metadata': self.metadata,
            'quality_metrics': {
                'total_chars': self.quality_metrics.total_chars,
                'total_words': self.quality_metrics.total_words,
                'avg_word_length': self.quality_metrics.avg_word_length,
                'readability_score': self.quality_metrics.readability_score,
                'has_meaningful_content': self.quality_metrics.has_meaningful_content,
                'language_confidence': self.quality_metrics.language_confidence,
            },
            'extraction_method': self.extraction_method,
            'confidence_score': self.confidence_score,
            'processing_time': self.processing_time,
            'extraction_timestamp': self.extraction_timestamp,
            'errors': self.errors,
            'extraction_success': len(self.errors) == 0,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert result to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def save_to_file(self, output_dir: Union[str, Path], filename: Optional[str] = None) -> str:
        """
        Save extraction result to JSON file.

        Args:
            output_dir: Directory to save the file
            filename: Optional filename (auto-generated if not provided)

        Returns:
            Path to the saved file
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        if not filename:
            # Generate filename based on document ID and timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{self.document_id}_{timestamp}.json"

        filepath = output_path / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_json())

        logger.info(f"Saved extraction result to {filepath}")
        return str(filepath)

    def meets_quality_thresholds(self,
                               min_words: int = 50,
                               min_readability: float = 20.0,
                               min_confidence: float = 60.0) -> bool:
        """
        Check if extraction result meets quality thresholds.

        Args:
            min_words: Minimum word count
            min_readability: Minimum readability score
            min_confidence: Minimum confidence score

        Returns:
            True if all thresholds are met
        """
        return (
            self.quality_metrics.total_words >= min_words and
            self.quality_metrics.readability_score >= min_readability and
            self.confidence_score >= min_confidence and
            self.quality_metrics.has_meaningful_content and
            len(self.errors) == 0
        )


class TextExtractionPipeline:
    """
    Main pipeline for extracting and processing text from HTML and PDF documents.

    Handles the complete workflow from raw content to structured text output.
    """

    def __init__(self,
                 output_dir: Union[str, Path] = "extracted_text",
                 s3_bucket: Optional[str] = None,
                 min_quality_threshold: float = 60.0):
        """
        Initialize the text extraction pipeline.

        Args:
            output_dir: Directory for local output files
            s3_bucket: Optional S3 bucket for storing results
            min_quality_threshold: Minimum quality score (0-100)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.s3_uploader = None
        if s3_bucket:
            self.s3_uploader = FlightSchoolS3Uploader(bucket_name=s3_bucket)

        self.min_quality_threshold = min_quality_threshold
        self.html_cleaner = HTMLCleaner()
        self.pdf_extractor = PDFTextExtractor()

        logger.info(f"Text extraction pipeline initialized with output dir: {output_dir}")

    def process_document(self,
                        content: Union[str, bytes],
                        source_name: str,
                        url: str,
                        document_type: Optional[str] = None,
                        filename: Optional[str] = None) -> DocumentExtractionResult:
        """
        Process a single document (HTML or PDF).

        Args:
            content: Raw document content (string for HTML, bytes for PDF)
            source_name: Name of the data source
            url: Source URL
            document_type: 'html' or 'pdf' (auto-detected if not provided)
            filename: Original filename

        Returns:
            DocumentExtractionResult with processed text and metadata
        """
        start_time = datetime.now()

        # Generate document ID
        content_hash = self._generate_content_hash(content)
        document_id = f"{source_name}_{content_hash[:12]}"

        # Auto-detect document type if not provided
        if not document_type:
            document_type = self._detect_document_type(content, filename)

        try:
            if document_type == 'html':
                result = self._process_html_document(content, source_name, url, document_id)
            elif document_type == 'pdf':
                result = self._process_pdf_document(content, source_name, url, document_id, filename)
            else:
                raise ValueError(f"Unsupported document type: {document_type}")

            # Add processing time
            result.processing_time = (datetime.now() - start_time).total_seconds()

            # Save to file and optionally S3
            self._save_result(result)

            return result

        except Exception as e:
            error_msg = f"Document processing failed: {str(e)}"
            logger.error(error_msg)

            # Create error result
            result = DocumentExtractionResult(
                document_id=document_id,
                source_name=source_name,
                url=url,
                document_type=document_type or 'unknown',
                extracted_text="",
                errors=[error_msg],
                processing_time=(datetime.now() - start_time).total_seconds()
            )

            return result

    def _process_html_document(self,
                             content: str,
                             source_name: str,
                             url: str,
                             document_id: str) -> DocumentExtractionResult:
        """Process HTML document."""
        # Clean HTML content
        clean_result = self.html_cleaner.clean_html(content, url)

        if not clean_result['extraction_success']:
            return DocumentExtractionResult(
                document_id=document_id,
                source_name=source_name,
                url=url,
                document_type='html',
                extracted_text="",
                errors=clean_result.get('error', 'HTML cleaning failed'),
                quality_metrics=clean_result['quality_metrics']
            )

        # Calculate overall quality score
        quality_score = TextQualityChecker.get_quality_score(clean_result['quality_metrics'])

        return DocumentExtractionResult(
            document_id=document_id,
            source_name=source_name,
            url=url,
            document_type='html',
            extracted_text=clean_result['cleaned_text'],
            title=clean_result['title'],
            metadata=clean_result['metadata'],
            quality_metrics=clean_result['quality_metrics'],
            extraction_method='html_cleaning',
            confidence_score=quality_score,
        )

    def _process_pdf_document(self,
                            content: bytes,
                            source_name: str,
                            url: str,
                            document_id: str,
                            filename: Optional[str] = None) -> DocumentExtractionResult:
        """Process PDF document."""
        # Extract text from PDF
        pdf_result = self.pdf_extractor.extract_from_pdf(content, filename)

        # Convert PDF result to our format
        quality_score = TextQualityChecker.get_quality_score(pdf_result.quality_metrics)

        return DocumentExtractionResult(
            document_id=document_id,
            source_name=source_name,
            url=url,
            document_type='pdf',
            extracted_text=pdf_result.text,
            metadata={
                'title': pdf_result.metadata.title,
                'author': pdf_result.metadata.author,
                'pages': pdf_result.metadata.pages,
                'file_size': pdf_result.metadata.file_size,
                'creation_date': pdf_result.metadata.creation_date,
            },
            quality_metrics=pdf_result.quality_metrics,
            extraction_method=pdf_result.extraction_method,
            confidence_score=pdf_result.confidence_score,
            errors=pdf_result.errors,
        )

    def _detect_document_type(self, content: Union[str, bytes], filename: Optional[str] = None) -> str:
        """Detect document type from content and filename."""
        # Check filename first
        if filename:
            filename_lower = filename.lower()
            if filename_lower.endswith('.pdf'):
                return 'pdf'
            elif filename_lower.endswith(('.html', '.htm')):
                return 'html'

        # Check content
        if isinstance(content, bytes):
            # Check for PDF header
            if content.startswith(b'%PDF-'):
                return 'pdf'
            else:
                # Try to decode as UTF-8 text
                try:
                    text_content = content.decode('utf-8')
                    if '<html' in text_content.lower() or '<!doctype html' in text_content.lower():
                        return 'html'
                except UnicodeDecodeError:
                    pass

        elif isinstance(content, str):
            if '<html' in content.lower() or '<!doctype html' in content.lower():
                return 'html'

        # Default to HTML if uncertain
        return 'html'

    def _generate_content_hash(self, content: Union[str, bytes]) -> str:
        """Generate SHA256 hash of content for document ID."""
        if isinstance(content, str):
            content = content.encode('utf-8')
        return hashlib.sha256(content).hexdigest()

    def _save_result(self, result: DocumentExtractionResult) -> None:
        """Save extraction result to file and optionally S3."""
        # Save locally
        result.save_to_file(self.output_dir)

        # Save to S3 if configured
        if self.s3_uploader:
            upload_data = {
                'source_name': f"{result.source_name}_extracted",
                'url': result.url,
                'filename': f"{result.document_id}.json",
                'content': result.to_json(),
                'content_type': 'json',
                'crawl_timestamp': result.extraction_timestamp,
            }

            success = self.s3_uploader.upload_raw_html(upload_data)
            if success:
                logger.info(f"Uploaded extraction result to S3: {result.document_id}")
            else:
                logger.warning(f"Failed to upload extraction result to S3: {result.document_id}")

    def batch_process_documents(self,
                               documents: List[Dict[str, Any]],
                               save_individual: bool = True) -> List[DocumentExtractionResult]:
        """
        Process multiple documents in batch.

        Args:
            documents: List of document dictionaries with 'content', 'source_name', 'url', etc.
            save_individual: Whether to save each result individually

        Returns:
            List of extraction results
        """
        results = []

        for doc in documents:
            result = self.process_document(
                content=doc['content'],
                source_name=doc['source_name'],
                url=doc['url'],
                document_type=doc.get('document_type'),
                filename=doc.get('filename')
            )
            results.append(result)

        # Save batch summary
        self._save_batch_summary(results)

        return results

    def _save_batch_summary(self, results: List[DocumentExtractionResult]) -> None:
        """Save summary of batch processing."""
        summary = {
            'batch_timestamp': datetime.now().isoformat(),
            'total_documents': len(results),
            'successful_extractions': len([r for r in results if r.extraction_success]),
            'quality_passed': len([r for r in results if r.meets_quality_thresholds()]),
            'by_source': {},
            'by_document_type': {},
            'errors': [],
        }

        for result in results:
            # Group by source
            source = result.source_name
            if source not in summary['by_source']:
                summary['by_source'][source] = {'total': 0, 'successful': 0}
            summary['by_source'][source]['total'] += 1
            if result.extraction_success:
                summary['by_source'][source]['successful'] += 1

            # Group by document type
            doc_type = result.document_type
            if doc_type not in summary['by_document_type']:
                summary['by_document_type'][doc_type] = 0
            summary['by_document_type'][doc_type] += 1

            # Collect errors
            if result.errors:
                summary['errors'].extend(result.errors)

        # Save summary
        summary_file = self.output_dir / f"batch_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved batch summary to {summary_file}")


# Convenience functions
def extract_text_from_html(html_content: str, url: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract clean text from HTML content.

    Args:
        html_content: Raw HTML string
        url: Source URL

    Returns:
        Dictionary with extraction results
    """
    pipeline = TextExtractionPipeline()
    result = pipeline.process_document(html_content, 'html_extraction', url or '', 'html')
    return result.to_dict()


def extract_text_from_pdf(pdf_content: bytes, url: str = '', filename: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract text from PDF content.

    Args:
        pdf_content: Raw PDF bytes
        url: Source URL
        filename: Original filename

    Returns:
        Dictionary with extraction results
    """
    pipeline = TextExtractionPipeline()
    result = pipeline.process_document(pdf_content, 'pdf_extraction', url, 'pdf', filename)
    return result.to_dict()


if __name__ == '__main__':
    # Example usage
    pipeline = TextExtractionPipeline()

    # Test HTML extraction
    sample_html = """
    <html>
    <head><title>Test Flight School</title></head>
    <body>
        <h1>Welcome to Test Flight School</h1>
        <p>We offer comprehensive flight training programs for aspiring pilots.</p>
        <p>Our courses include private pilot, instrument rating, and commercial pilot certifications.</p>
        <nav>Home | About | Contact</nav>
        <script>console.log('ignore me');</script>
    </body>
    </html>
    """

    result = pipeline.process_document(
        sample_html,
        'test_source',
        'https://example.com',
        'html'
    )

    print(f"Extraction successful: {result.extraction_success}")
    print(f"Title: {result.title}")
    print(f"Word count: {result.quality_metrics.total_words}")
    print(f"Quality score: {result.confidence_score:.1f}")
    print(f"Text preview: {result.extracted_text[:200]}...")
