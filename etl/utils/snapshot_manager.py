"""
Snapshot Manager for ETL Pipeline Manifests

This module manages the creation, validation, and storage of comprehensive manifests
for ETL pipeline snapshots, ensuring data reproducibility and integrity tracking.
"""

import json
import hashlib
import logging
import copy
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import os

try:
    from etl.utils.s3_upload import FlightSchoolS3Uploader
except ImportError:
    # Create a mock uploader for testing when boto3 is not available
    class FlightSchoolS3Uploader:
        def __init__(self, bucket_name="wheelsup-flight-school-raw-data", snapshot_id=None):
            self.bucket_name = bucket_name
            self.snapshot_id = snapshot_id or "TEST-SNAPSHOT"

            # Mock S3 client
            from unittest.mock import MagicMock
            self.s3_client = MagicMock()

logger = logging.getLogger(__name__)


class ManifestGenerator:
    """
    Generates comprehensive manifests for ETL pipeline snapshots.

    Tracks data lineage from source discovery through publishing,
    with integrity verification and reproducibility metadata.
    """

    def __init__(self, snapshot_id: Optional[str] = None, base_path: Optional[str] = None):
        """
        Initialize the manifest generator.

        Args:
            snapshot_id: Snapshot identifier (generated if not provided)
            base_path: Base path for ETL data directories
        """
        self.snapshot_id = snapshot_id or self._generate_snapshot_id()
        self.base_path = Path(base_path or Path(__file__).parent.parent)
        self.created_at = datetime.now()

        # S3 uploader for manifest storage
        self.s3_uploader = FlightSchoolS3Uploader(snapshot_id=self.snapshot_id)

    def _generate_snapshot_id(self) -> str:
        """Generate a snapshot ID in YYYYQ1-MVP format."""
        now = datetime.now()
        quarter = (now.month - 1) // 3 + 1
        return f"{now.year}Q{quarter}-MVP"

    def _calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate SHA-256 hash of a file.

        Args:
            file_path: Path to the file

        Returns:
            Hexadecimal SHA-256 hash string
        """
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256()
                while chunk := f.read(8192):
                    file_hash.update(chunk)
                return file_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""

    def _calculate_data_hash(self, data: Any) -> str:
        """
        Calculate SHA-256 hash of data structure.

        Args:
            data: Data to hash (will be JSON serialized)

        Returns:
            Hexadecimal SHA-256 hash string
        """
        try:
            json_str = json.dumps(data, sort_keys=True, default=str)
            return hashlib.sha256(json_str.encode('utf-8')).hexdigest()
        except Exception as e:
            logger.error(f"Error calculating data hash: {e}")
            return ""

    def _scan_directory_for_files(self, directory: Path, pattern: str = "*.json") -> List[Dict[str, Any]]:
        """
        Scan a directory for files matching a pattern and collect metadata.

        Args:
            directory: Directory to scan
            pattern: File pattern to match

        Returns:
            List of file metadata dictionaries
        """
        files = []
        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return files

        for file_path in directory.glob(pattern):
            if file_path.is_file():
                try:
                    stat = file_path.stat()
                    file_info = {
                        'filename': file_path.name,
                        'path': str(file_path.relative_to(self.base_path)),
                        'size_bytes': stat.st_size,
                        'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'hash_sha256': self._calculate_file_hash(file_path)
                    }
                    files.append(file_info)
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")

        return files

    def _load_json_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load and parse a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading JSON file {file_path}: {e}")
            return None

    def collect_source_discovery_data(self) -> Dict[str, Any]:
        """
        Collect data from source discovery phase.

        Returns:
            Dictionary with source discovery metadata
        """
        output_dir = self.base_path / "output"
        discovery_files = self._scan_directory_for_files(output_dir, "seed_discovery_*.json")

        discovery_data = {
            'files': discovery_files,
            'total_files': len(discovery_files),
            'total_size_bytes': sum(f['size_bytes'] for f in discovery_files),
            'sources': {}
        }

        # Load summary file if it exists
        summary_file = output_dir / f"seed_discovery_summary_{self.created_at.strftime('%Y%m%d_%H%M%S')}.json"
        if not summary_file.exists():
            # Try to find the most recent summary file
            summary_files = list(output_dir.glob("seed_discovery_summary_*.json"))
            if summary_files:
                summary_file = max(summary_files, key=lambda p: p.stat().st_mtime)

        if summary_file.exists():
            summary_data = self._load_json_file(summary_file)
            if summary_data:
                discovery_data.update({
                    'summary': summary_data,
                    'total_sources_processed': summary_data.get('total_sources_processed', 0),
                    'total_schools_discovered': summary_data.get('total_schools_discovered', 0),
                    'total_unique_domains': summary_data.get('total_unique_domains', 0)
                })

                # Extract source details
                for source in summary_data.get('sources', []):
                    source_name = source['source_name']
                    discovery_data['sources'][source_name] = {
                        'type': source.get('source_type', 'unknown'),
                        'schools_discovered': source.get('schools_discovered', 0),
                        'unique_domains': source.get('unique_domains', 0),
                        'processing_time': source.get('processing_time', 0),
                        'success': source.get('success', False)
                    }

        return discovery_data

    def collect_text_extraction_data(self) -> Dict[str, Any]:
        """
        Collect data from text extraction phase.

        Returns:
            Dictionary with text extraction metadata
        """
        extracted_dir = self.base_path / "extracted_text"
        extraction_files = self._scan_directory_for_files(extracted_dir, "*.json")

        extraction_data = {
            'files': extraction_files,
            'total_files': len(extraction_files),
            'total_size_bytes': sum(f['size_bytes'] for f in extraction_files),
            'batches': {},
            'sources': {},
            'quality_metrics': {}
        }

        # Group files by source and batch (only process actual extraction files)
        for file_info in extraction_files:
            filename = file_info['filename']

            # Skip batch summary files and other non-extraction files
            if filename.startswith('batch_summary_'):
                continue

            # Parse filename: {source}_{hash}_{timestamp}.json
            # The hash is a 6-character alphanumeric string, timestamp is YYYYMMDD_HHMMSS
            parts = filename.replace('.json', '').split('_')
            if len(parts) >= 6:  # source_name + hash + date + time (minimum)
                # Find the hash (6-character alphanumeric string, should be lowercase and contain both letters and numbers)
                hash_index = -1
                for i, part in enumerate(parts):
                    if (len(part) == 6 and part.isalnum() and
                        any(c.isdigit() for c in part) and  # Contains at least one digit
                        any(c.islower() for c in part)):   # Contains at least one lowercase letter
                        hash_index = i
                        break

                if hash_index >= 0:
                    source_name = '_'.join(parts[:hash_index])
                    file_hash = parts[hash_index]
                    timestamp_str = '_'.join(parts[hash_index + 1:])
                else:
                    # Skip this file if we can't parse it
                    continue

                if source_name not in extraction_data['sources']:
                    extraction_data['sources'][source_name] = {
                        'files': [],
                        'total_size_bytes': 0,
                        'quality_scores': []
                    }

                extraction_data['sources'][source_name]['files'].append(file_info)
                extraction_data['sources'][source_name]['total_size_bytes'] += file_info['size_bytes']

                # Load file to extract quality metrics
                file_path = extracted_dir / filename
                file_data = self._load_json_file(file_path)
                if file_data:
                    confidence = file_data.get('confidence_score', 0)
                    quality_score = file_data.get('quality_metrics', {}).get('has_meaningful_content', False)

                    if confidence > 0:
                        extraction_data['sources'][source_name]['quality_scores'].append(confidence)

                    # Track quality metrics
                    if 'quality_metrics' not in extraction_data:
                        extraction_data['quality_metrics'] = {}

                    extraction_data['quality_metrics'][filename] = {
                        'confidence_score': confidence,
                        'quality_score': quality_score,
                        'word_count': file_data.get('quality_metrics', {}).get('total_words', 0),
                        'extraction_success': file_data.get('extraction_success', False)
                    }

        # Calculate source-level aggregates
        for source_name, source_data in extraction_data['sources'].items():
            quality_scores = source_data['quality_scores']
            if quality_scores:
                source_data['avg_confidence'] = sum(quality_scores) / len(quality_scores)
                source_data['min_confidence'] = min(quality_scores)
                source_data['max_confidence'] = max(quality_scores)
            else:
                source_data['avg_confidence'] = 0.0

        # Load batch summary if available
        batch_summaries = list(extracted_dir.glob("batch_summary_*.json"))
        if batch_summaries:
            latest_batch = max(batch_summaries, key=lambda p: p.stat().st_mtime)
            batch_data = self._load_json_file(latest_batch)
            if batch_data:
                extraction_data['latest_batch'] = batch_data
                extraction_data['batches'][latest_batch.name] = batch_data

        return extraction_data

    def collect_processing_metadata(self) -> Dict[str, Any]:
        """
        Collect ETL pipeline processing metadata.

        Returns:
            Dictionary with processing metadata
        """
        metadata = {
            'pipeline_version': '1.0.0',
            'snapshot_id': self.snapshot_id,
            'created_at': self.created_at.isoformat(),
            'environment': {
                'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
                'platform': os.sys.platform,
            },
            'processing_steps': []
        }

        # Check for test output to get processing metrics
        test_output_dir = self.base_path / "test_output"
        if test_output_dir.exists():
            test_reports = list(test_output_dir.glob("pipeline_test_report_*.json"))
            if test_reports:
                latest_report = max(test_reports, key=lambda p: p.stat().st_mtime)
                report_data = self._load_json_file(latest_report)
                if report_data:
                    metadata['test_results'] = report_data
                    metadata['processing_steps'].append({
                        'step': 'pipeline_test',
                        'timestamp': report_data.get('timestamp'),
                        'success': report_data.get('overall_success', False),
                        'tests_run': report_data.get('tests_run', 0),
                        'tests_passed': report_data.get('tests_passed', 0)
                    })

        return metadata

    def generate_manifest(self) -> Dict[str, Any]:
        """
        Generate a comprehensive manifest for the current snapshot.

        Returns:
            Complete manifest dictionary
        """
        logger.info(f"Generating manifest for snapshot {self.snapshot_id}")

        # Collect data from all pipeline stages
        source_discovery = self.collect_source_discovery_data()
        text_extraction = self.collect_text_extraction_data()
        processing_metadata = self.collect_processing_metadata()

        # Calculate composite hashes
        manifest_data = {
            'manifest_version': '1.0',
            'snapshot_id': self.snapshot_id,
            'created_at': self.created_at.isoformat(),
            'created_by': 'WheelsUp ETL Pipeline v1.0.0',

            # Pipeline stages data
            'pipeline_stages': {
                'source_discovery': source_discovery,
                'text_extraction': text_extraction,
                'processing_metadata': processing_metadata,
            },

            # Overall statistics
            'statistics': {
                'total_source_files': source_discovery['total_files'],
                'total_extraction_files': text_extraction['total_files'],
                'total_sources_discovered': source_discovery.get('total_sources_processed', 0),
                'total_schools_discovered': source_discovery.get('total_schools_discovered', 0),
                'total_extraction_size_bytes': text_extraction['total_size_bytes'],
                'sources_with_extractions': len(text_extraction['sources'])
            },

            # Integrity verification
            'integrity': {
                'source_discovery_hash': self._calculate_data_hash(source_discovery),
                'text_extraction_hash': self._calculate_data_hash(text_extraction),
                'processing_metadata_hash': self._calculate_data_hash(processing_metadata),
                'composite_manifest_hash': ''  # Will be filled after manifest is complete
            }
        }

        # Calculate the composite manifest hash
        temp_manifest = copy.deepcopy(manifest_data)
        temp_manifest['integrity']['composite_manifest_hash'] = ''  # Placeholder
        manifest_data['integrity']['composite_manifest_hash'] = self._calculate_data_hash(temp_manifest)

        logger.info(f"Manifest generated with {manifest_data['statistics']['total_source_files'] + manifest_data['statistics']['total_extraction_files']} total files")
        return manifest_data

    def validate_manifest(self, manifest: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a manifest for schema compliance and integrity.

        Args:
            manifest: Manifest dictionary to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Required top-level fields
        required_fields = ['manifest_version', 'snapshot_id', 'created_at', 'pipeline_stages', 'statistics', 'integrity']
        for field in required_fields:
            if field not in manifest:
                errors.append(f"Missing required field: {field}")

        # Validate snapshot ID format
        if 'snapshot_id' in manifest:
            snapshot_id = manifest['snapshot_id']
            if not isinstance(snapshot_id, str) or len(snapshot_id) < 5:
                errors.append("Invalid snapshot_id format")

        # Validate pipeline stages
        if 'pipeline_stages' in manifest:
            stages = manifest['pipeline_stages']
            required_stages = ['source_discovery', 'text_extraction', 'processing_metadata']
            for stage in required_stages:
                if stage not in stages:
                    errors.append(f"Missing pipeline stage: {stage}")

        # Validate integrity hashes
        if 'integrity' in manifest:
            integrity = manifest['integrity']
            required_hashes = ['source_discovery_hash', 'text_extraction_hash', 'processing_metadata_hash', 'composite_manifest_hash']
            for hash_field in required_hashes:
                if hash_field not in integrity:
                    errors.append(f"Missing integrity hash: {hash_field}")
                elif not integrity[hash_field] or len(integrity[hash_field]) != 64:  # SHA-256 is 64 chars
                    errors.append(f"Invalid hash format for {hash_field}")

        # Verify composite manifest hash
        if len(errors) == 0:
            temp_manifest = copy.deepcopy(manifest)
            temp_manifest['integrity']['composite_manifest_hash'] = ''
            expected_hash = self._calculate_data_hash(temp_manifest)
            actual_hash = manifest['integrity']['composite_manifest_hash']
            if expected_hash != actual_hash:
                errors.append("Manifest integrity check failed - composite hash mismatch")

        is_valid = len(errors) == 0
        return is_valid, errors

    def save_manifest_locally(self, manifest: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
        """
        Save manifest to local file system.

        Args:
            manifest: Manifest dictionary
            output_path: Optional output path (default: etl/output/)

        Returns:
            Path to saved manifest file
        """
        if output_path is None:
            output_path = self.base_path / "output" / f"manifest_{self.snapshot_id}.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, default=str)

        logger.info(f"Manifest saved locally to {output_path}")
        return output_path

    def upload_manifest_to_s3(self, manifest: Optional[Dict[str, Any]] = None) -> bool:
        """
        Upload manifest to S3 with proper key structure.

        Args:
            manifest: Optional manifest (generated if not provided)

        Returns:
            True if upload successful
        """
        if manifest is None:
            manifest = self.generate_manifest()

        # Validate manifest before upload
        is_valid, errors = self.validate_manifest(manifest)
        if not is_valid:
            logger.error(f"Manifest validation failed: {errors}")
            return False

        # Create S3 key with date structure: snapshots/YYYYMMDD/manifest_{snapshot_id}_{timestamp}.json
        date_str = self.created_at.strftime('%Y%m%d')
        timestamp_str = self.created_at.strftime('%H%M%S')
        s3_key = f"snapshots/{date_str}/manifest_{self.snapshot_id}_{timestamp_str}.json"

        try:
            # Convert to JSON string
            manifest_json = json.dumps(manifest, indent=2, default=str)

            # Upload to S3
            self.s3_uploader.s3_client.put_object(
                Bucket=self.s3_uploader.bucket_name,
                Key=s3_key,
                Body=manifest_json,
                ContentType='application/json',
                Metadata={
                    'snapshot-id': self.snapshot_id,
                    'manifest-version': manifest.get('manifest_version', '1.0'),
                    'created-at': self.created_at.isoformat(),
                    'composite-hash': manifest.get('integrity', {}).get('composite_manifest_hash', ''),
                    'type': 'manifest',
                    'pipeline-stage': 'final'
                }
            )

            logger.info(f"Manifest uploaded to s3://{self.s3_uploader.bucket_name}/{s3_key}")
            return True

        except Exception as e:
            logger.error(f"Error uploading manifest to S3: {e}")
            return False

    def create_snapshot_manifest(self) -> Tuple[bool, Path]:
        """
        Create, validate, and save a complete snapshot manifest.

        Returns:
            Tuple of (success, manifest_file_path)
        """
        try:
            # Generate manifest
            manifest = self.generate_manifest()

            # Validate manifest
            is_valid, errors = self.validate_manifest(manifest)
            if not is_valid:
                logger.error(f"Manifest validation failed: {errors}")
                return False, Path()

            # Save locally
            local_path = self.save_manifest_locally(manifest)

            # Upload to S3
            s3_success = self.upload_manifest_to_s3(manifest)

            if s3_success:
                logger.info(f"Snapshot manifest created successfully for {self.snapshot_id}")
                return True, local_path
            else:
                logger.warning("Manifest saved locally but S3 upload failed")
                return False, local_path

        except Exception as e:
            logger.error(f"Error creating snapshot manifest: {e}")
            return False, Path()


def create_etl_manifest(snapshot_id: Optional[str] = None, upload_to_s3: bool = True) -> Tuple[bool, Path]:
    """
    Convenience function to create a complete ETL manifest.

    Args:
        snapshot_id: Optional snapshot ID
        upload_to_s3: Whether to upload to S3

    Returns:
        Tuple of (success, local_manifest_path)
    """
    manager = ManifestGenerator(snapshot_id=snapshot_id)

    success, local_path = manager.create_snapshot_manifest()

    if success and not upload_to_s3:
        logger.info("Manifest created locally (S3 upload skipped)")
    elif not success:
        logger.error("Failed to create manifest")

    return success, local_path


if __name__ == "__main__":
    # Example usage
    manager = ManifestGenerator()
    manifest = manager.generate_manifest()

    print(f"Generated manifest for snapshot: {manager.snapshot_id}")
    print(f"Total source files: {manifest['statistics']['total_source_files']}")
    print(f"Total extraction files: {manifest['statistics']['total_extraction_files']}")

    # Validate manifest
    is_valid, errors = manager.validate_manifest(manifest)
    print(f"Manifest validation: {'PASS' if is_valid else 'FAIL'}")
    if not is_valid:
        print(f"Errors: {errors}")

    # Save locally
    local_path = manager.save_manifest_locally(manifest)
    print(f"Manifest saved to: {local_path}")

    # Try to upload to S3 (will fail without AWS credentials)
    s3_success = manager.upload_manifest_to_s3(manifest)
    print(f"S3 upload: {'SUCCESS' if s3_success else 'FAILED (expected without AWS credentials)'}")
