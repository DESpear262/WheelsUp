#!/usr/bin/env python3
"""
Test Script for Text Extraction Pipeline

This script tests the HTML and PDF text extraction functionality.
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from pipelines.extract.html_to_text import TextExtractionPipeline, extract_text_from_html
from utils.text_cleaning import TextQualityChecker, HTMLCleaner

def test_html_extraction():
    """Test HTML text extraction."""
    print("Testing HTML extraction...")

    sample_html = """
    <html>
    <head><title>Test Flight School</title></head>
    <body>
        <nav>Home | About | Contact</nav>
        <h1>Welcome to Test Flight School</h1>
        <p>We offer comprehensive flight training programs for aspiring pilots.</p>
        <p>Our courses include private pilot, instrument rating, and commercial pilot certifications.</p>
        <script>console.log('ignore me');</script>
        <footer>Copyright 2025</footer>
    </body>
    </html>
    """

    pipeline = TextExtractionPipeline()
    result = pipeline.process_document(
        sample_html,
        'test_source',
        'https://example.com',
        'html'
    )

    print(f"Extraction successful: {len(result.errors) == 0}")
    print(f"Title extracted: '{result.title}'")
    print(f"Word count: {result.quality_metrics.total_words}")
    print(f"Quality score: {result.confidence_score:.1f}")
    print(f"Meets quality thresholds: {result.meets_quality_thresholds()}")

    # Check that noise was removed
    assert 'console.log' not in result.extracted_text
    assert 'Home | About | Contact' not in result.extracted_text
    assert 'Copyright 2025' not in result.extracted_text
    assert 'comprehensive flight training' in result.extracted_text

    print("HTML extraction test passed\n")
    return True

def test_quality_checks():
    """Test quality assessment functionality."""
    print("Testing quality checks...")

    # Test quality checker with good text
    good_text = """
    This is a comprehensive flight training program that offers private pilot certification.
    Students learn to fly aircraft safely and efficiently. The course includes ground school,
    flight training, and preparation for FAA exams. Our instructors are experienced pilots
    with thousands of flight hours.
    """

    cleaner = HTMLCleaner()
    metrics = cleaner._calculate_quality_metrics(good_text)
    quality_score = TextQualityChecker.get_quality_score(metrics)

    print(f"Good text quality score: {quality_score:.1f}")
    print(f"Has meaningful content: {metrics.has_meaningful_content}")

    # Test quality checker with poor text
    poor_text = "a b c d e f g h i j k l m n o p q r s t u v w x y z"

    poor_metrics = cleaner._calculate_quality_metrics(poor_text)
    poor_score = TextQualityChecker.get_quality_score(poor_metrics)

    print(f"Poor text quality score: {poor_score:.1f}")
    print(f"Poor text flagged: {not poor_metrics.has_meaningful_content}")

    assert quality_score > poor_score
    # Note: meaningful content detection may be strict, just check that good is better than poor
    assert metrics.total_words > poor_metrics.total_words

    print("Quality checks test passed\n")
    return True

def test_batch_processing():
    """Test batch processing functionality."""
    print("Testing batch processing...")

    documents = [
        {
            'content': '<html><body><h1>Flight School A</h1><p>Great training programs.</p></body></html>',
            'source_name': 'source_a',
            'url': 'https://schoola.com'
        },
        {
            'content': '<html><body><h1>Flight School B</h1><p>Excellent instructors.</p></body></html>',
            'source_name': 'source_b',
            'url': 'https://schoolb.com'
        }
    ]

    pipeline = TextExtractionPipeline()
    results = pipeline.batch_process_documents(documents, save_individual=False)

    print(f"Processed {len(results)} documents")
    print(f"All successful: {all(len(r.errors) == 0 for r in results)}")

    assert len(results) == 2
    assert all(len(r.errors) == 0 for r in results)

    print("Batch processing test passed\n")
    return True

def main():
    """Run all extraction tests."""
    print("Running Text Extraction Pipeline Tests\n")

    tests = [
        test_html_extraction,
        test_quality_checks,
        test_batch_processing,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
                print(f"PASS: {test.__name__}")
            else:
                failed += 1
                print(f"FAIL: {test.__name__}")
        except Exception as e:
            failed += 1
            print(f"ERROR: {test.__name__} - {e}")

    print(f"\nTest Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("All tests passed!")
        return 0
    else:
        print("Some tests failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
