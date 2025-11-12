#!/usr/bin/env python3
"""
Flight School Data Extraction Pipeline

Uses LLM (Claude 3.5 Sonnet) to extract structured flight school data from
unstructured text. Processes extracted text files in batches with caching,
validation, and error handling.

Author: Cursor Agent White (PR-1.4)
Created: 2025-11-11

Usage:
    python extract_school_data.py --input-dir ../extracted_text --output-dir ../extracted_data --batch-size 5
"""

import asyncio
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import hashlib
import argparse

from loguru import logger

from utils.llm_client import extract_flight_school_data, get_llm_client, LLMProvider
from schemas.school_schema import FlightSchool
from error_handler import ExtractionError, ErrorSeverity


@dataclass
class ExtractionResult:
    """Result of a single extraction operation."""
    document_id: str
    source_url: str
    extracted_data: Optional[Dict[str, Any]]
    confidence_score: float
    processing_time: float
    tokens_used: int
    provider: str
    success: bool
    error_message: Optional[str] = None


@dataclass
class BatchResult:
    """Results from a batch of extractions."""
    batch_id: str
    results: List[ExtractionResult]
    total_tokens: int
    total_time: float
    success_count: int
    error_count: int


class SchoolDataExtractor:
    """
    Batch processor for flight school data extraction using LLM.
    """

    def __init__(self, prompt_template_path: str, cache_dir: Optional[str] = None):
        self.prompt_template_path = prompt_template_path
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.llm_client = get_llm_client()

        # Load prompt template
        with open(prompt_template_path, 'r', encoding='utf-8') as f:
            self.prompt_template = f.read()

        # Create cache directory if needed
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Statistics
        self.stats = {
            'total_processed': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'total_tokens': 0,
            'total_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }

    def _load_extracted_text(self, file_path: Path) -> Dict[str, Any]:
        """Load extracted text data from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise ExtractionError(f"Failed to load {file_path}: {e}", severity=ErrorSeverity.ERROR)

    def _get_cache_key(self, document_id: str, content_hash: str) -> str:
        """Generate cache key for document."""
        return f"{document_id}_{content_hash}"

    def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached extraction result."""
        if not self.cache_dir:
            return None

        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached = json.load(f)
                    # Check if cache is still valid (24 hours)
                    cached_time = datetime.fromisoformat(cached['cached_at'])
                    if (datetime.utcnow() - cached_time).total_seconds() < 86400:  # 24 hours
                        self.stats['cache_hits'] += 1
                        return cached['result']
            except Exception:
                pass  # Cache corrupted, ignore

        self.stats['cache_misses'] += 1
        return None

    def _save_to_cache(self, cache_key: str, result: Dict[str, Any]):
        """Save extraction result to cache."""
        if not self.cache_dir:
            return

        cache_file = self.cache_dir / f"{cache_key}.json"
        cached_data = {
            'cached_at': datetime.utcnow().isoformat(),
            'result': result
        }

        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cached_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

    def _create_extraction_prompt(self, extracted_text_data: Dict[str, Any]) -> str:
        """Create the LLM prompt for extraction."""
        extracted_text = extracted_text_data.get('extracted_text', '')

        # Add context from metadata if available
        context_parts = []
        if extracted_text_data.get('title'):
            context_parts.append(f"Page Title: {extracted_text_data['title']}")
        if extracted_text_data.get('source_name'):
            context_parts.append(f"Source: {extracted_text_data['source_name']}")

        context = "\n".join(context_parts)
        if context:
            extracted_text = f"{context}\n\n{extracted_text}"

        return self.prompt_template.replace("{extracted_text}", extracted_text)

    def _validate_extraction_result(self, raw_result: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate extraction result and create FlightSchool instance.

        Returns (is_valid, error_message)
        """
        try:
            # Check required fields
            if not raw_result.get('name'):
                return False, "Missing required field: name"

            # Try to create FlightSchool instance (this validates the schema)
            school_data = raw_result.copy()

            # Add required provenance fields if missing
            if 'source_type' not in school_data:
                school_data['source_type'] = 'website'
            if 'source_url' not in school_data:
                school_data['source_url'] = 'unknown'
            if 'extractor_version' not in school_data:
                school_data['extractor_version'] = '1.0.0'
            if 'snapshot_id' not in school_data:
                school_data['snapshot_id'] = f"extraction_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

            # Create and validate FlightSchool instance
            flight_school = FlightSchool(**school_data)

            # Additional validation
            if flight_school.confidence < 0.1:
                return False, f"Confidence too low: {flight_school.confidence}"

            return True, None

        except Exception as e:
            return False, f"Schema validation failed: {str(e)}"

    async def _extract_single_document(self, file_path: Path) -> ExtractionResult:
        """Extract data from a single document."""
        start_time = time.time()

        try:
            # Load extracted text
            text_data = self._load_extracted_text(file_path)

            document_id = text_data.get('document_id', file_path.stem)
            source_url = text_data.get('url', text_data.get('source_url', 'unknown'))

            # Create cache key
            content_hash = hashlib.md5(
                text_data.get('extracted_text', '').encode()
            ).hexdigest()[:8]
            cache_key = self._get_cache_key(document_id, content_hash)

            # Check cache
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                processing_time = time.time() - start_time
                return ExtractionResult(
                    document_id=document_id,
                    source_url=source_url,
                    extracted_data=cached_result,
                    confidence_score=cached_result.get('extraction_metadata', {}).get('confidence_score', 0.5),
                    processing_time=processing_time,
                    tokens_used=0,  # Cached, no tokens used
                    provider="cached",
                    success=True
                )

            # Create extraction prompt
            prompt = self._create_extraction_prompt(text_data)

            # Call LLM
            llm_response = await extract_flight_school_data(prompt)

            # Parse JSON response
            try:
                raw_result = json.loads(llm_response.content)
            except json.JSONDecodeError as e:
                raise ExtractionError(f"Invalid JSON response: {e}", severity=ErrorSeverity.WARNING)

            # Validate result
            is_valid, error_msg = self._validate_extraction_result(raw_result)
            if not is_valid:
                raise ExtractionError(f"Validation failed: {error_msg}", severity=ErrorSeverity.WARNING)

            # Add LLM metadata
            raw_result['extraction_metadata'] = raw_result.get('extraction_metadata', {})
            raw_result['extraction_metadata'].update({
                'llm_provider': llm_response.provider.value,
                'llm_tokens_used': llm_response.tokens_used,
                'llm_processing_time': llm_response.processing_time,
                'llm_confidence': llm_response.confidence_score
            })

            # Cache result
            self._save_to_cache(cache_key, raw_result)

            processing_time = time.time() - start_time

            return ExtractionResult(
                document_id=document_id,
                source_url=source_url,
                extracted_data=raw_result,
                confidence_score=raw_result.get('extraction_metadata', {}).get('confidence_score', 0.5),
                processing_time=processing_time,
                tokens_used=llm_response.tokens_used,
                provider=llm_response.provider.value,
                success=True
            )

        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)

            self.stats['failed_extractions'] += 1

            return ExtractionResult(
                document_id=file_path.stem,
                source_url="unknown",
                extracted_data=None,
                confidence_score=0.0,
                processing_time=processing_time,
                tokens_used=0,
                provider="error",
                success=False,
                error_message=error_msg
            )

    async def extract_batch(self, file_paths: List[Path], batch_id: str) -> BatchResult:
        """Extract data from a batch of documents."""
        batch_start = time.time()

        logger.info(f"Processing batch {batch_id} with {len(file_paths)} documents")

        # Process documents concurrently
        tasks = [self._extract_single_document(file_path) for file_path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle results
        processed_results = []
        total_tokens = 0
        success_count = 0

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Handle unexpected exceptions
                error_result = ExtractionResult(
                    document_id=file_paths[i].stem,
                    source_url="unknown",
                    extracted_data=None,
                    confidence_score=0.0,
                    processing_time=0.0,
                    tokens_used=0,
                    provider="error",
                    success=False,
                    error_message=str(result)
                )
                processed_results.append(error_result)
                self.stats['failed_extractions'] += 1
            else:
                processed_results.append(result)
                total_tokens += result.tokens_used
                if result.success:
                    success_count += 1
                    self.stats['successful_extractions'] += 1
                else:
                    self.stats['failed_extractions'] += 1

        batch_time = time.time() - batch_start
        self.stats['total_processed'] += len(file_paths)
        self.stats['total_tokens'] += total_tokens
        self.stats['total_time'] += batch_time

        batch_result = BatchResult(
            batch_id=batch_id,
            results=processed_results,
            total_tokens=total_tokens,
            total_time=batch_time,
            success_count=success_count,
            error_count=len(file_paths) - success_count
        )

        logger.info(f"Batch {batch_id} completed: {success_count}/{len(file_paths)} successful, "
                   f"{total_tokens} tokens, {batch_time:.2f}s")

        return batch_result

    def get_statistics(self) -> Dict[str, Any]:
        """Get extraction statistics."""
        return self.stats.copy()


async def main():
    """Main extraction pipeline."""
    parser = argparse.ArgumentParser(description="Extract flight school data using LLM")
    parser.add_argument(
        "--input-dir",
        type=str,
        default="../extracted_text",
        help="Directory containing extracted text JSON files"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="../extracted_data",
        help="Directory to save extracted data"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=3,
        help="Number of documents to process concurrently"
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default="../cache/llm_extraction",
        help="Directory for caching LLM responses"
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=None,
        help="Maximum number of files to process (for testing)"
    )

    args = parser.parse_args()

    # Setup paths
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    cache_dir = Path(args.cache_dir)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Setup logging
    logger.add(output_dir / "extraction.log", rotation="10 MB")

    logger.info("Starting flight school data extraction pipeline")
    logger.info(f"Input directory: {input_dir}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Batch size: {args.batch_size}")

    # Find input files
    json_files = list(input_dir.glob("*.json"))
    if not json_files:
        logger.error(f"No JSON files found in {input_dir}")
        return

    if args.max_files:
        json_files = json_files[:args.max_files]
        logger.info(f"Limited to {args.max_files} files for testing")

    logger.info(f"Found {len(json_files)} files to process")

    # Initialize extractor
    prompt_template = Path(__file__).parent / "prompts" / "school_prompt.txt"
    extractor = SchoolDataExtractor(
        prompt_template_path=str(prompt_template),
        cache_dir=str(cache_dir)
    )

    # Process files in batches
    all_results = []
    batch_num = 1

    for i in range(0, len(json_files), args.batch_size):
        batch_files = json_files[i:i + args.batch_size]
        batch_id = f"batch_{batch_num:03d}"

        batch_result = await extractor.extract_batch(batch_files, batch_id)
        all_results.extend(batch_result.results)

        batch_num += 1

        # Save intermediate results
        await save_results(all_results, output_dir, intermediate=True)

    # Save final results
    await save_results(all_results, output_dir, intermediate=False)

    # Print final statistics
    stats = extractor.get_statistics()
    llm_stats = extractor.llm_client.get_token_usage()

    logger.info("=== EXTRACTION COMPLETE ===")
    logger.info(f"Total files processed: {stats['total_processed']}")
    logger.info(f"Successful extractions: {stats['successful_extractions']}")
    logger.info(f"Failed extractions: {stats['failed_extractions']}")
    logger.info(f"Cache hits: {stats['cache_hits']}")
    logger.info(f"Cache misses: {stats['cache_misses']}")
    logger.info(f"Total processing time: {stats['total_time']:.2f}s")
    logger.info(f"Average time per file: {stats['total_time']/max(stats['total_processed'],1):.2f}s")
    logger.info("=== TOKEN USAGE ===")
    logger.info(f"Claude (Bedrock): {llm_stats['claude_bedrock']} tokens")
    logger.info(f"GPT-4o (OpenAI): {llm_stats['openai_gpt4o']} tokens")
    logger.info(f"Total tokens: {llm_stats['total']} tokens")


async def save_results(results: List[ExtractionResult], output_dir: Path, intermediate: bool = False):
    """Save extraction results to files."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    # Save individual results
    successful_results = [r for r in results if r.success and r.extracted_data]

    for result in successful_results:
        output_file = output_dir / f"extracted_{result.document_id}.json"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result.extracted_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save {output_file}: {e}")

    # Save summary
    summary_file = output_dir / f"extraction_summary_{timestamp}.json"
    if not intermediate:
        summary_file = output_dir / "extraction_summary_final.json"

    summary = {
        "extraction_timestamp": timestamp,
        "total_files": len(results),
        "successful_extractions": len(successful_results),
        "failed_extractions": len(results) - len(successful_results),
        "results": [
            {
                "document_id": r.document_id,
                "source_url": r.source_url,
                "success": r.success,
                "confidence_score": r.confidence_score,
                "processing_time": r.processing_time,
                "tokens_used": r.tokens_used,
                "provider": r.provider,
                "error_message": r.error_message
            }
            for r in results
        ]
    }

    try:
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved summary to {summary_file}")
    except Exception as e:
        logger.error(f"Failed to save summary: {e}")


if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(lambda msg: print(msg, end=""), level="INFO")

    # Run the pipeline
    asyncio.run(main())
