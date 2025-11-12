#!/usr/bin/env python3
"""
Unit Tests for LLM Extraction Pipeline

Tests LLM extraction and normalization functionality including:
- Prompt template handling
- Data validation and schema compliance
- Caching mechanisms
- Error handling and recovery
- Batch processing logic

Author: Cursor Agent White (PR 5.1)
Created: 2025-11-11
"""

import json
import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, AsyncMock
from datetime import datetime, timedelta

from pipelines.llm.extract_school_data import (
    SchoolDataExtractor,
    ExtractionResult,
    BatchResult,
    ExtractionError
)
from utils.llm_client import LLMResponse, LLMProvider
from schemas.school_schema import FlightSchool


class TestSchoolDataExtractor:
    """Test the main extraction class."""

    @pytest.fixture
    def sample_extracted_text(self):
        """Sample extracted text data for testing."""
        return {
            "document_id": "test_doc_001",
            "url": "https://example.com/school",
            "title": "Test Aviation School",
            "source_name": "Test Source",
            "extracted_text": "Test Aviation School offers PPL training with 40 hours ground and 60 hours flight time. Located in California."
        }

    @pytest.fixture
    def mock_prompt_template(self):
        """Mock prompt template content."""
        return """
Extract flight school information from the following text:

{extracted_text}

Return as JSON with this structure:
{
    "name": "school name",
    "location": {"city": "city", "state": "state", "country": "country"},
    "confidence": 0.95
}
"""

    @pytest.fixture
    def valid_extraction_result(self):
        """Valid extraction result for testing."""
        return {
            "name": "Test Aviation School",
            "description": "Professional flight training school",
            "location": {
                "city": "Los Angeles",
                "state": "CA",
                "country": "United States"
            },
            "accreditation": {
                "type": "FAA Part 141",
                "vaApproved": True
            },
            "operations": {
                "foundedYear": 1995
            },
            "confidence": 0.95,
            "source_type": "website",
            "source_url": "https://example.com/school",
            "extractor_version": "1.0.0",
            "snapshot_id": "test_snapshot"
        }

    def test_initialization_with_prompt_template(self, tmp_path, mock_prompt_template):
        """Test extractor initialization with prompt template."""
        prompt_file = tmp_path / "test_prompt.txt"
        prompt_file.write_text(mock_prompt_template)

        extractor = SchoolDataExtractor(str(prompt_file))

        assert extractor.prompt_template == mock_prompt_template.strip()
        assert extractor.llm_client is not None
        assert extractor.cache_dir is None

    def test_initialization_with_cache_dir(self, tmp_path, mock_prompt_template):
        """Test extractor initialization with cache directory."""
        prompt_file = tmp_path / "test_prompt.txt"
        cache_dir = tmp_path / "cache"
        prompt_file.write_text(mock_prompt_template)

        extractor = SchoolDataExtractor(str(prompt_file), str(cache_dir))

        assert extractor.cache_dir == cache_dir
        assert cache_dir.exists()

    def test_load_extracted_text_success(self, tmp_path, sample_extracted_text):
        """Test successful loading of extracted text JSON."""
        json_file = tmp_path / "test.json"
        json_file.write_text(json.dumps(sample_extracted_text))

        extractor = SchoolDataExtractor("dummy_prompt.txt")

        result = extractor._load_extracted_text(json_file)
        assert result == sample_extracted_text

    def test_load_extracted_text_file_not_found(self, tmp_path):
        """Test error handling for missing JSON file."""
        extractor = SchoolDataExtractor("dummy_prompt.txt")

        with pytest.raises(ExtractionError, match="Failed to load"):
            extractor._load_extracted_text(tmp_path / "nonexistent.json")

    def test_get_cache_key(self, sample_extracted_text):
        """Test cache key generation."""
        extractor = SchoolDataExtractor("dummy_prompt.txt")

        document_id = "test_doc_001"
        content_hash = "abc12345"

        cache_key = extractor._get_cache_key(document_id, content_hash)
        assert cache_key == f"{document_id}_{content_hash}"

    def test_get_cached_result_expired(self, tmp_path, sample_extracted_text):
        """Test cache retrieval with expired cache."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()

        extractor = SchoolDataExtractor("dummy_prompt.txt", str(cache_dir))

        # Create expired cache file (more than 24 hours old)
        expired_time = (datetime.utcnow() - timedelta(hours=25)).isoformat()
        cache_data = {
            "cached_at": expired_time,
            "result": {"test": "data"}
        }

        cache_file = cache_dir / "test_key.json"
        cache_file.write_text(json.dumps(cache_data))

        result = extractor._get_cached_result("test_key")
        assert result is None

    def test_get_cached_result_valid(self, tmp_path, sample_extracted_text):
        """Test cache retrieval with valid cache."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()

        extractor = SchoolDataExtractor("dummy_prompt.txt", str(cache_dir))

        # Create valid cache file (less than 24 hours old)
        recent_time = datetime.utcnow().isoformat()
        cache_data = {
            "cached_at": recent_time,
            "result": {"test": "data"}
        }

        cache_file = cache_dir / "test_key.json"
        cache_file.write_text(json.dumps(cache_data))

        result = extractor._get_cached_result("test_key")
        assert result == {"test": "data"}

    def test_create_extraction_prompt_basic(self, sample_extracted_text, mock_prompt_template):
        """Test basic prompt creation."""
        extractor = SchoolDataExtractor.__new__(SchoolDataExtractor)
        extractor.prompt_template = mock_prompt_template

        prompt = extractor._create_extraction_prompt(sample_extracted_text)

        assert "Test Aviation School" in prompt
        assert "Test Source" in prompt
        assert "Page Title: Test Aviation School" in prompt
        assert "Source: Test Source" in prompt

    def test_create_extraction_prompt_no_metadata(self):
        """Test prompt creation without metadata."""
        extractor = SchoolDataExtractor.__new__(SchoolDataExtractor)
        extractor.prompt_template = "Extract: {extracted_text}"

        text_data = {
            "extracted_text": "Basic school information."
        }

        prompt = extractor._create_extraction_prompt(text_data)
        assert prompt == "Extract: Basic school information."

    def test_validate_extraction_result_valid(self, valid_extraction_result):
        """Test validation of valid extraction result."""
        extractor = SchoolDataExtractor("dummy_prompt.txt")

        is_valid, error_msg = extractor._validate_extraction_result(valid_extraction_result)

        assert is_valid is True
        assert error_msg is None

    def test_validate_extraction_result_missing_name(self):
        """Test validation failure for missing required fields."""
        extractor = SchoolDataExtractor("dummy_prompt.txt")

        invalid_result = {
            "description": "No name provided"
        }

        is_valid, error_msg = extractor._validate_extraction_result(invalid_result)

        assert is_valid is False
        assert "Missing required field: name" in error_msg

    def test_validate_extraction_result_low_confidence(self):
        """Test validation failure for low confidence."""
        extractor = SchoolDataExtractor("dummy_prompt.txt")

        low_confidence_result = {
            "name": "Test School",
            "confidence": 0.05,
            "source_type": "website",
            "source_url": "https://example.com",
            "extractor_version": "1.0.0",
            "snapshot_id": "test"
        }

        is_valid, error_msg = extractor._validate_extraction_result(low_confidence_result)

        assert is_valid is False
        assert "Confidence too low" in error_msg

    def test_validate_extraction_result_schema_error(self):
        """Test validation failure for schema errors."""
        extractor = SchoolDataExtractor("dummy_prompt.txt")

        schema_invalid_result = {
            "name": "Test School",
            "location": "invalid_location_format",  # Should be object
            "source_type": "website",
            "source_url": "https://example.com",
            "extractor_version": "1.0.0",
            "snapshot_id": "test"
        }

        is_valid, error_msg = extractor._validate_extraction_result(schema_invalid_result)

        assert is_valid is False
        assert "Schema validation failed" in error_msg

    @pytest.mark.asyncio
    async def test_extract_single_document_success(self, tmp_path, sample_extracted_text, valid_extraction_result, mock_prompt_template):
        """Test successful single document extraction."""
        # Setup
        json_file = tmp_path / "test.json"
        json_file.write_text(json.dumps(sample_extracted_text))

        prompt_file = tmp_path / "prompt.txt"
        prompt_file.write_text(mock_prompt_template)

        extractor = SchoolDataExtractor(str(prompt_file))

        # Mock LLM response
        mock_llm_response = LLMResponse(
            content=json.dumps(valid_extraction_result),
            provider=LLMProvider.CLAUDE_BEDROCK,
            tokens_used=150,
            confidence_score=0.9,
            raw_response={},
            processing_time=2.5
        )

        with patch('pipelines.llm.extract_school_data.extract_flight_school_data', new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = mock_llm_response

            result = await extractor._extract_single_document(json_file)

            assert result.success is True
            assert result.document_id == "test_doc_001"
            assert result.source_url == "https://example.com/school"
            assert result.tokens_used == 150
            assert result.provider == "claude_bedrock"
            assert result.extracted_data is not None

    @pytest.mark.asyncio
    async def test_extract_single_document_cache_hit(self, tmp_path, sample_extracted_text, valid_extraction_result, mock_prompt_template):
        """Test cache hit scenario."""
        # Setup
        json_file = tmp_path / "test.json"
        json_file.write_text(json.dumps(sample_extracted_text))

        cache_dir = tmp_path / "cache"
        prompt_file = tmp_path / "prompt.txt"
        prompt_file.write_text(mock_prompt_template)

        extractor = SchoolDataExtractor(str(prompt_file), str(cache_dir))

        # Pre-populate cache
        cache_key = extractor._get_cache_key("test_doc_001", "a7b8c9d0")  # MD5 hash prefix
        cache_file = cache_dir / f"{cache_key}.json"
        cache_file.parent.mkdir(parents=True, exist_ok=True)

        cache_data = {
            "cached_at": datetime.utcnow().isoformat(),
            "result": valid_extraction_result
        }
        cache_file.write_text(json.dumps(cache_data))

        result = await extractor._extract_single_document(json_file)

        assert result.success is True
        assert result.provider == "cached"
        assert result.tokens_used == 0

    @pytest.mark.asyncio
    async def test_extract_single_document_json_error(self, tmp_path, sample_extracted_text, mock_prompt_template):
        """Test handling of invalid JSON response from LLM."""
        # Setup
        json_file = tmp_path / "test.json"
        json_file.write_text(json.dumps(sample_extracted_text))

        prompt_file = tmp_path / "prompt.txt"
        prompt_file.write_text(mock_prompt_template)

        extractor = SchoolDataExtractor(str(prompt_file))

        # Mock invalid JSON response
        mock_llm_response = LLMResponse(
            content="Invalid JSON response",
            provider=LLMProvider.CLAUDE_BEDROCK,
            tokens_used=50,
            confidence_score=0.1,
            raw_response={},
            processing_time=1.0
        )

        with patch('pipelines.llm.extract_school_data.extract_flight_school_data', new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = mock_llm_response

            result = await extractor._extract_single_document(json_file)

            assert result.success is False
            assert "Invalid JSON response" in result.error_message

    @pytest.mark.asyncio
    async def test_extract_batch_success(self, tmp_path, sample_extracted_text, valid_extraction_result, mock_prompt_template):
        """Test successful batch processing."""
        # Setup multiple files
        files = []
        for i in range(3):
            json_file = tmp_path / f"test_{i}.json"
            json_file.write_text(json.dumps(sample_extracted_text))
            files.append(json_file)

        prompt_file = tmp_path / "prompt.txt"
        prompt_file.write_text(mock_prompt_template)

        extractor = SchoolDataExtractor(str(prompt_file))

        # Mock LLM response
        mock_llm_response = LLMResponse(
            content=json.dumps(valid_extraction_result),
            provider=LLMProvider.CLAUDE_BEDROCK,
            tokens_used=150,
            confidence_score=0.9,
            raw_response={},
            processing_time=2.5
        )

        with patch('pipelines.llm.extract_school_data.extract_flight_school_data', new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = mock_llm_response

            batch_result = await extractor.extract_batch(files, "test_batch")

            assert batch_result.batch_id == "test_batch"
            assert len(batch_result.results) == 3
            assert batch_result.success_count == 3
            assert batch_result.error_count == 0
            assert batch_result.total_tokens == 450  # 3 * 150

    def test_get_statistics(self, mock_prompt_template):
        """Test statistics retrieval."""
        extractor = SchoolDataExtractor("dummy_prompt.txt")

        # Modify stats
        extractor.stats['total_processed'] = 10
        extractor.stats['successful_extractions'] = 8

        stats = extractor.get_statistics()

        assert stats['total_processed'] == 10
        assert stats['successful_extractions'] == 8
        assert isinstance(stats, dict)


class TestExtractionResult:
    """Test the ExtractionResult dataclass."""

    def test_extraction_result_creation(self):
        """Test ExtractionResult dataclass creation."""
        result = ExtractionResult(
            document_id="test_doc",
            source_url="https://example.com",
            extracted_data={"name": "Test School"},
            confidence_score=0.95,
            processing_time=2.5,
            tokens_used=150,
            provider="claude_bedrock",
            success=True
        )

        assert result.document_id == "test_doc"
        assert result.success is True
        assert result.confidence_score == 0.95
        assert result.tokens_used == 150

    def test_extraction_result_with_error(self):
        """Test ExtractionResult with error information."""
        result = ExtractionResult(
            document_id="test_doc",
            source_url="https://example.com",
            extracted_data=None,
            confidence_score=0.0,
            processing_time=1.0,
            tokens_used=0,
            provider="error",
            success=False,
            error_message="JSON parsing failed"
        )

        assert result.success is False
        assert result.error_message == "JSON parsing failed"
        assert result.extracted_data is None


class TestBatchResult:
    """Test the BatchResult dataclass."""

    def test_batch_result_creation(self):
        """Test BatchResult dataclass creation."""
        results = [
            ExtractionResult("doc1", "url1", {"name": "School 1"}, 0.9, 2.0, 100, "claude", True),
            ExtractionResult("doc2", "url2", {"name": "School 2"}, 0.8, 2.5, 120, "claude", True)
        ]

        batch = BatchResult(
            batch_id="batch_001",
            results=results,
            total_tokens=220,
            total_time=4.5,
            success_count=2,
            error_count=0
        )

        assert batch.batch_id == "batch_001"
        assert len(batch.results) == 2
        assert batch.success_count == 2
        assert batch.total_tokens == 220


if __name__ == "__main__":
    pytest.main([__file__])
