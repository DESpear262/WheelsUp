# Text Cleaning Utilities
#
# This module provides utilities for cleaning and normalizing text extracted
# from HTML and PDF documents, preparing them for LLM processing.

import re
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from bs4 import BeautifulSoup, NavigableString, Tag
from dataclasses import dataclass
import unicodedata

logger = logging.getLogger(__name__)


@dataclass
class TextQualityMetrics:
    """Metrics for assessing text extraction quality."""
    total_chars: int = 0
    total_words: int = 0
    avg_word_length: float = 0.0
    readability_score: float = 0.0  # Simplified readability metric
    has_meaningful_content: bool = False
    language_confidence: float = 0.0


class HTMLCleaner:
    """
    Comprehensive HTML cleaner that removes noise and extracts meaningful text content.

    Features:
    - Removes scripts, styles, navigation, ads, footers
    - Preserves main content structure
    - Handles encoding issues
    - Extracts metadata
    """

    # Elements to completely remove
    ELEMENTS_TO_REMOVE = {
        'script', 'style', 'noscript', 'iframe', 'embed', 'object',
        'nav', 'header', 'footer', 'aside', 'sidebar',
        'advertisement', 'ads', 'banner', 'popup',
        'social-share', 'share-buttons', 'comments',
        'cookie-notice', 'gdpr-banner', 'newsletter-signup'
    }

    # Classes/IDs that indicate noise content
    NOISE_PATTERNS = [
        re.compile(r'\b(ads?|advertisement|banner|popup|modal|overlay)\b', re.I),
        re.compile(r'\b(share|social|facebook|twitter|linkedin|instagram)\b', re.I),
        re.compile(r'\b(cookie|gdpr|privacy|newsletter|subscribe)\b', re.I),
        re.compile(r'\b(nav|menu|header|footer|sidebar)\b', re.I),
    ]

    def __init__(self, preserve_structure: bool = True, min_text_length: int = 50):
        """
        Initialize the HTML cleaner.

        Args:
            preserve_structure: Whether to preserve some HTML structure in output
            min_text_length: Minimum text length to consider content meaningful
        """
        self.preserve_structure = preserve_structure
        self.min_text_length = min_text_length

    def clean_html(self, html_content: str, url: Optional[str] = None) -> Dict[str, Any]:
        """
        Clean HTML content and extract meaningful text.

        Args:
            html_content: Raw HTML string
            url: Source URL for context

        Returns:
            Dictionary with cleaned text and metadata
        """
        try:
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove unwanted elements
            self._remove_unwanted_elements(soup)

            # Extract title
            title = self._extract_title(soup)

            # Extract main content
            main_content = self._extract_main_content(soup)

            # Clean and normalize text
            cleaned_text = self._clean_text(main_content)

            # Calculate quality metrics
            quality_metrics = self._calculate_quality_metrics(cleaned_text)

            # Extract metadata
            metadata = self._extract_metadata(soup, url)

            return {
                'title': title,
                'cleaned_text': cleaned_text,
                'quality_metrics': quality_metrics,
                'metadata': metadata,
                'extraction_success': True,
                'error': None
            }

        except Exception as e:
            logger.error(f"Error cleaning HTML from {url}: {e}")
            return {
                'title': '',
                'cleaned_text': '',
                'quality_metrics': TextQualityMetrics(),
                'metadata': {},
                'extraction_success': False,
                'error': str(e)
            }

    def _remove_unwanted_elements(self, soup: BeautifulSoup) -> None:
        """Remove unwanted HTML elements."""
        # Remove elements by tag name
        for tag_name in self.ELEMENTS_TO_REMOVE:
            for element in soup.find_all(tag_name):
                element.decompose()

        # Remove elements by class/id patterns
        for pattern in self.NOISE_PATTERNS:
            for element in soup.find_all(attrs={'class': pattern}):
                element.decompose()
            for element in soup.find_all(attrs={'id': pattern}):
                element.decompose()

        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, str) and '<!--' in text):
            comment.extract()

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        title_tag = soup.find('title')
        if title_tag and title_tag.get_text().strip():
            return title_tag.get_text().strip()

        # Fallback to h1 or other heading tags
        h1 = soup.find('h1')
        if h1 and h1.get_text().strip():
            return h1.get_text().strip()

        return ""

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """
        Extract main content from HTML.

        Uses heuristics to find the most content-rich section.
        """
        # Try common content selectors
        content_selectors = [
            'main',
            '[role="main"]',
            '.content',
            '.main-content',
            '.post-content',
            '.entry-content',
            'article',
            '.article-content'
        ]

        for selector in content_selectors:
            content_element = soup.select_one(selector)
            if content_element:
                text = content_element.get_text(separator='\n', strip=True)
                if len(text) > self.min_text_length:
                    return text

        # Fallback: find the div with the most text content
        best_div = None
        max_length = 0

        for div in soup.find_all('div'):
            text = div.get_text(separator=' ', strip=True)
            if len(text) > max_length and len(text) > self.min_text_length:
                max_length = len(text)
                best_div = div

        if best_div:
            return best_div.get_text(separator='\n', strip=True)

        # Last resort: entire body text
        body = soup.find('body')
        if body:
            return body.get_text(separator='\n', strip=True)

        return ""

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text.

        Args:
            text: Raw extracted text

        Returns:
            Cleaned and normalized text
        """
        if not text:
            return ""

        # Normalize unicode
        text = unicodedata.normalize('NFKC', text)

        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Multiple newlines to double
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs to single space

        # Remove lines that are mostly non-alphabetic (likely navigation/artifacts)
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Skip very short lines or lines with mostly symbols
            if len(line) < 10:
                continue

            # Skip lines with high ratio of non-alphabetic characters
            alpha_chars = sum(1 for c in line if c.isalpha())
            if alpha_chars / len(line) < 0.3 and len(line) > 20:
                continue

            cleaned_lines.append(line)

        # Join lines back
        text = '\n'.join(cleaned_lines)

        # Final cleanup
        text = text.strip()

        return text

    def _calculate_quality_metrics(self, text: str) -> TextQualityMetrics:
        """Calculate quality metrics for extracted text."""
        if not text:
            return TextQualityMetrics()

        words = re.findall(r'\b\w+\b', text)
        total_chars = len(text)
        total_words = len(words)

        # Average word length
        avg_word_length = sum(len(word) for word in words) / total_words if words else 0

        # Simple readability score (words per sentence approximation)
        sentences = re.split(r'[.!?]+', text)
        avg_words_per_sentence = total_words / len(sentences) if sentences else 0
        readability_score = max(0, 100 - avg_words_per_sentence)  # Higher is better

        # Check for meaningful content
        has_meaningful_content = (
            total_words > 50 and  # At least 50 words
            avg_word_length > 3 and  # Average word length > 3 chars
            readability_score > 20  # Some readability
        )

        # Simple language detection (English words ratio)
        english_words = sum(1 for word in words if re.match(r'^[a-zA-Z]+$', word))
        language_confidence = english_words / total_words if words else 0

        return TextQualityMetrics(
            total_chars=total_chars,
            total_words=total_words,
            avg_word_length=avg_word_length,
            readability_score=readability_score,
            has_meaningful_content=has_meaningful_content,
            language_confidence=language_confidence
        )

    def _extract_metadata(self, soup: BeautifulSoup, url: Optional[str] = None) -> Dict[str, Any]:
        """Extract metadata from HTML."""
        metadata = {}

        # Meta tags
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                metadata[name] = content

        # Open Graph tags
        og_tags = soup.find_all('meta', attrs={'property': re.compile(r'^og:')})
        for og in og_tags:
            prop = og.get('property', '').replace('og:', '')
            content = og.get('content')
            if prop and content:
                metadata[f'og_{prop}'] = content

        # Additional metadata
        metadata.update({
            'source_url': url,
            'extracted_at': str(datetime.now()),
            'has_title': bool(soup.find('title')),
            'has_meta_description': bool(soup.find('meta', attrs={'name': 'description'})),
        })

        return metadata


class TextQualityChecker:
    """
    Utility for checking and validating text quality.
    """

    @staticmethod
    def meets_minimum_quality(metrics: TextQualityMetrics,
                            min_words: int = 50,
                            min_readability: float = 20.0,
                            min_language_confidence: float = 0.7) -> bool:
        """
        Check if text meets minimum quality standards.

        Args:
            metrics: Text quality metrics
            min_words: Minimum word count
            min_readability: Minimum readability score
            min_language_confidence: Minimum language confidence

        Returns:
            True if text meets quality standards
        """
        return (
            metrics.total_words >= min_words and
            metrics.readability_score >= min_readability and
            metrics.language_confidence >= min_language_confidence and
            metrics.has_meaningful_content
        )

    @staticmethod
    def get_quality_score(metrics: TextQualityMetrics) -> float:
        """
        Calculate an overall quality score (0-100).

        Args:
            metrics: Text quality metrics

        Returns:
            Quality score between 0 and 100
        """
        if not metrics.total_words:
            return 0.0

        # Weighted scoring
        word_score = min(100, metrics.total_words / 2)  # 200+ words = 100 points
        readability_score = max(0, min(100, metrics.readability_score))
        language_score = metrics.language_confidence * 100

        # Weighted average
        return (word_score * 0.4 + readability_score * 0.3 + language_score * 0.3)


# Convenience functions
def clean_html_content(html_content: str, url: Optional[str] = None) -> Dict[str, Any]:
    """
    Clean HTML content using default settings.

    Args:
        html_content: Raw HTML string
        url: Source URL

    Returns:
        Cleaned content dictionary
    """
    cleaner = HTMLCleaner()
    return cleaner.clean_html(html_content, url)


def validate_text_quality(text: str) -> TextQualityMetrics:
    """
    Validate text quality.

    Args:
        text: Text to validate

    Returns:
        Quality metrics
    """
    # Create a minimal cleaner just for quality assessment
    cleaner = HTMLCleaner()
    return cleaner._calculate_quality_metrics(text)


if __name__ == '__main__':
    # Example usage
    sample_html = """
    <html>
    <head><title>Test Page</title></head>
    <body>
        <nav>Navigation menu</nav>
        <script>console.log('test');</script>
        <main>
            <h1>Main Content</h1>
            <p>This is some meaningful content about flight schools.</p>
            <p>It contains information that should be preserved.</p>
        </main>
        <footer>Copyright 2025</footer>
    </body>
    </html>
    """

    cleaner = HTMLCleaner()
    result = cleaner.clean_html(sample_html, "https://example.com")

    print("Title:", result['title'])
    print("Quality Score:", TextQualityChecker.get_quality_score(result['quality_metrics']))
    print("Meets Quality:", TextQualityChecker.meets_minimum_quality(result['quality_metrics']))
