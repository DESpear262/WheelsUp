#!/usr/bin/env python3
"""
Test suite for ETL Pipeline Manifest functionality.

This script tests the snapshot manager and manifest generation,
validation, and storage functionality.
"""

import sys
import json
import tempfile
import shutil
import copy
from pathlib import Path
from unittest.mock import Mock, patch

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from etl.utils.snapshot_manager import ManifestGenerator
    S3_AVAILABLE = True
except ImportError as e:
    if "boto3" in str(e):
        print("Warning: boto3 not available, S3 functionality will be mocked")
        S3_AVAILABLE = False

        # Mock the S3 components for testing
        import sys
        from unittest.mock import MagicMock

        # Create mock modules
        sys.modules['boto3'] = MagicMock()
        sys.modules['botocore.exceptions'] = MagicMock()

        # Now import should work
        from etl.utils.snapshot_manager import ManifestGenerator
    else:
        raise


def create_test_data_directories(base_path: Path):
    """Create test data directories and files."""
    # Create directories
    output_dir = base_path / "output"
    extracted_dir = base_path / "extracted_text"
    test_output_dir = base_path / "test_output"

    output_dir.mkdir(parents=True, exist_ok=True)
    extracted_dir.mkdir(parents=True, exist_ok=True)
    test_output_dir.mkdir(parents=True, exist_ok=True)

    # Create mock source discovery summary
    discovery_summary = {
        "batch_timestamp": "2025-11-11T14:49:04.022131",
        "total_sources_processed": 2,
        "successful_discoveries": 2,
        "total_schools_discovered": 15,
        "total_unique_domains": 15,
        "sources": [
            {
                "source_name": "test_source_a",
                "source_type": "directory",
                "schools_discovered": 8,
                "unique_domains": 8,
                "processing_time": 0.001,
                "success": True
            },
            {
                "source_name": "test_source_b",
                "source_type": "database",
                "schools_discovered": 7,
                "unique_domains": 7,
                "processing_time": 0.002,
                "success": True
            }
        ],
        "errors": []
    }

    with open(output_dir / "seed_discovery_summary_20251111_144904.json", 'w') as f:
        json.dump(discovery_summary, f)

    # Create mock discovery files
    discovery_a = {"source": "test_source_a", "schools": ["school1", "school2"]}
    with open(output_dir / "seed_discovery_test_source_a_20251111_144904.json", 'w') as f:
        json.dump(discovery_a, f)

    discovery_b = {"source": "test_source_b", "schools": ["school3", "school4"]}
    with open(output_dir / "seed_discovery_test_source_b_20251111_144904.json", 'w') as f:
        json.dump(discovery_b, f)

    # Create mock extracted text files
    extracted_a = {
        "document_id": "test_source_a_abc123",
        "source_name": "test_source_a",
        "confidence_score": 0.85,
        "quality_metrics": {
            "total_words": 150,
            "has_meaningful_content": True
        },
        "extraction_success": True
    }
    with open(extracted_dir / "test_source_a_abc123_20251111_134750.json", 'w') as f:
        json.dump(extracted_a, f)

    extracted_b = {
        "document_id": "test_source_b_def456",
        "source_name": "test_source_b",
        "confidence_score": 0.92,
        "quality_metrics": {
            "total_words": 200,
            "has_meaningful_content": True
        },
        "extraction_success": True
    }
    with open(extracted_dir / "test_source_b_def456_20251111_134750.json", 'w') as f:
        json.dump(extracted_b, f)

    # Create batch summary
    batch_summary = {
        "batch_timestamp": "2025-11-11T13:47:50.068130",
        "total_documents": 2,
        "successful_extractions": 2,
        "quality_passed": 2,
        "by_source": {
            "test_source_a": {"total": 1, "successful": 1},
            "test_source_b": {"total": 1, "successful": 1}
        }
    }
    with open(extracted_dir / "batch_summary_20251111_134750.json", 'w') as f:
        json.dump(batch_summary, f)

    # Create mock test report
    test_report = {
        "timestamp": "2025-11-11T15:00:00.000000",
        "overall_success": True,
        "tests_run": 5,
        "tests_passed": 5,
        "test_results": [
            {"name": "test_validation", "status": "passed"},
            {"name": "test_normalization", "status": "passed"}
        ]
    }
    with open(test_output_dir / "pipeline_test_report_20251111_150000.json", 'w') as f:
        json.dump(test_report, f)


def test_manifest_generation():
    """Test basic manifest generation functionality."""
    print("Testing manifest generation...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test data
        create_test_data_directories(temp_path)

        # Create manifest generator
        generator = ManifestGenerator(snapshot_id="TEST2025Q1-MVP", base_path=temp_path)

        # Generate manifest
        manifest = generator.generate_manifest()

        # Verify basic structure
        required_fields = ['manifest_version', 'snapshot_id', 'created_at', 'pipeline_stages', 'statistics', 'integrity']
        for field in required_fields:
            assert field in manifest, f"Missing required field: {field}"

        # Verify snapshot ID
        assert manifest['snapshot_id'] == "TEST2025Q1-MVP"

        # Verify pipeline stages
        stages = manifest['pipeline_stages']
        assert 'source_discovery' in stages
        assert 'text_extraction' in stages
        assert 'processing_metadata' in stages

        # Verify statistics
        stats = manifest['statistics']
        assert stats['total_source_files'] == 3  # summary + 2 discovery files
        assert stats['total_extraction_files'] == 3  # 2 extracted + 1 batch summary
        assert stats['total_sources_discovered'] == 2
        assert stats['total_schools_discovered'] == 15

        # Verify integrity hashes exist and are valid
        integrity = manifest['integrity']
        required_hashes = ['source_discovery_hash', 'text_extraction_hash', 'processing_metadata_hash', 'composite_manifest_hash']
        for hash_field in required_hashes:
            assert hash_field in integrity
            assert len(integrity[hash_field]) == 64  # SHA-256 hex length

        print("+ Manifest generation test passed")
        return True


def test_manifest_validation():
    """Test manifest validation functionality."""
    print("Testing manifest validation...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        create_test_data_directories(temp_path)

        generator = ManifestGenerator(snapshot_id="TEST2025Q1-MVP", base_path=temp_path)
        manifest = generator.generate_manifest()

        # Test valid manifest
        is_valid, errors = generator.validate_manifest(manifest)
        if not is_valid:
            print(f"Validation errors: {errors}")
            # Debug: check the hashes
            temp_manifest = copy.deepcopy(manifest)
            temp_manifest['integrity']['composite_manifest_hash'] = ''
            expected_hash = generator._calculate_data_hash(temp_manifest)
            actual_hash = manifest['integrity']['composite_manifest_hash']
            print(f"Expected hash length: {len(expected_hash)}")
            print(f"Actual hash length: {len(actual_hash)}")
            print(f"Expected hash: {expected_hash}")
            print(f"Actual hash: {actual_hash}")
            print(f"Match: {expected_hash == actual_hash}")

            # Check all hash lengths
            integrity = manifest.get('integrity', {})
            for hash_field in ['source_discovery_hash', 'text_extraction_hash', 'processing_metadata_hash', 'composite_manifest_hash']:
                hash_val = integrity.get(hash_field, '')
                print(f"{hash_field}: length={len(hash_val)}, is_64={len(hash_val)==64}")

        assert is_valid, f"Valid manifest should pass validation: {errors}"
        assert len(errors) == 0

        # Test manifest with missing fields
        invalid_manifest = manifest.copy()
        del invalid_manifest['snapshot_id']
        is_valid, errors = generator.validate_manifest(invalid_manifest)
        assert not is_valid
        assert "Missing required field: snapshot_id" in errors

        # Test manifest with invalid hash
        invalid_manifest = copy.deepcopy(manifest)
        invalid_manifest['integrity']['composite_manifest_hash'] = "invalid_hash"
        is_valid, errors = generator.validate_manifest(invalid_manifest)
        print(f"Invalid hash test - is_valid: {is_valid}, errors: {errors}")
        assert not is_valid
        assert len(errors) > 0  # Should have some validation error

        print("+ Manifest validation test passed")
        return True


def test_file_hashing():
    """Test file hash calculation."""
    print("Testing file hash calculation...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test file
        test_file = temp_path / "test.json"
        test_data = {"test": "data", "number": 123}
        with open(test_file, 'w') as f:
            json.dump(test_data, f)

        generator = ManifestGenerator()

        # Calculate hash
        file_hash = generator._calculate_file_hash(test_file)
        assert len(file_hash) == 64  # SHA-256 hex length

    # File hash should be different from data hash (file includes JSON formatting)
    # Just verify both are valid SHA-256 hashes
    assert len(file_hash) == 64
    assert file_hash.isalnum() and all(c in '0123456789abcdef' for c in file_hash)

    print("+ File hash calculation test passed")
    return True


def test_data_hashing():
    """Test data hash calculation."""
    print("Testing data hash calculation...")

    generator = ManifestGenerator()

    # Test with different data types
    test_data = {
        "string": "test",
        "number": 123,
        "list": [1, 2, 3],
        "nested": {"key": "value"}
    }

    hash1 = generator._calculate_data_hash(test_data)
    assert len(hash1) == 64

    # Same data should produce same hash
    hash2 = generator._calculate_data_hash(test_data)
    assert hash1 == hash2

    # Different data should produce different hash
    different_data = test_data.copy()
    different_data["extra"] = "field"
    hash3 = generator._calculate_data_hash(different_data)
    assert hash1 != hash3

    print("+ Data hash calculation test passed")
    return True


def test_local_save():
    """Test local manifest saving."""
    print("Testing local manifest saving...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        create_test_data_directories(temp_path)

        generator = ManifestGenerator(snapshot_id="TEST2025Q1-MVP", base_path=temp_path)
        manifest = generator.generate_manifest()

        # Save manifest
        output_path = generator.save_manifest_locally(manifest, temp_path / "test_manifest.json")

        # Verify file was created
        assert output_path.exists()

        # Load and verify content
        with open(output_path, 'r') as f:
            saved_manifest = json.load(f)

        assert saved_manifest['snapshot_id'] == "TEST2025Q1-MVP"
        assert 'pipeline_stages' in saved_manifest
        assert 'statistics' in saved_manifest

        print("+ Local save test passed")
        return True


def test_s3_upload_simulation():
    """Test S3 upload functionality (without actual AWS calls)."""
    print("Testing S3 upload simulation...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        create_test_data_directories(temp_path)

        generator = ManifestGenerator(snapshot_id="TEST2025Q1-MVP", base_path=temp_path)

        # Mock S3 client to avoid actual AWS calls
        with patch.object(generator.s3_uploader, 's3_client') as mock_s3:
            mock_s3.put_object.return_value = {}

            manifest = generator.generate_manifest()
            success = generator.upload_manifest_to_s3(manifest)

            # Verify S3 put_object was called
            assert mock_s3.put_object.called
            call_args = mock_s3.put_object.call_args

            # Verify bucket and key
            assert call_args[1]['Bucket'] == generator.s3_uploader.bucket_name
            s3_key = call_args[1]['Key']
            assert s3_key.startswith('snapshots/')
            assert 'TEST2025Q1-MVP' in s3_key
            assert s3_key.endswith('.json')

            # Verify metadata
            metadata = call_args[1]['Metadata']
            assert metadata['snapshot-id'] == 'TEST2025Q1-MVP'
            assert metadata['type'] == 'manifest'

            print("+ S3 upload simulation test passed")
            return True


def test_data_collection():
    """Test data collection from different pipeline stages."""
    print("Testing data collection...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        create_test_data_directories(temp_path)

        generator = ManifestGenerator(snapshot_id="TEST2025Q1-MVP", base_path=temp_path)

        # Test source discovery data collection
        discovery_data = generator.collect_source_discovery_data()
        assert 'sources' in discovery_data
        assert len(discovery_data['sources']) == 2  # test_source_a and test_source_b
        assert discovery_data['total_sources_processed'] == 2
        assert discovery_data['total_schools_discovered'] == 15

        # Test text extraction data collection
        extraction_data = generator.collect_text_extraction_data()
        assert 'sources' in extraction_data
        print(f"Found sources: {list(extraction_data['sources'].keys())}")
        print(f"Number of sources: {len(extraction_data['sources'])}")
        print(f"Total files: {extraction_data['total_files']}")
        assert len(extraction_data['sources']) == 2
        assert extraction_data['total_files'] == 3  # 2 extracted files + 1 batch summary

        # Verify quality metrics (should only include actual extraction files, not batch summaries)
        assert 'quality_metrics' in extraction_data
        quality_files = list(extraction_data['quality_metrics'].keys())
        assert len(quality_files) == 2  # Only the 2 actual extraction files

        # Test processing metadata collection
        metadata = generator.collect_processing_metadata()
        assert 'pipeline_version' in metadata
        assert 'environment' in metadata
        assert metadata['snapshot_id'] == "TEST2025Q1-MVP"

        print("+ Data collection test passed")
        return True


if __name__ == "__main__":
    print("ETL Pipeline Manifest Test Suite")
    print("=" * 50)

    try:
        # Run all tests
        tests = [
            test_manifest_generation,
            test_manifest_validation,
            test_file_hashing,
            test_data_hashing,
            test_local_save,
            test_s3_upload_simulation,
            test_data_collection
        ]

        passed = 0
        failed = 0

        for test_func in tests:
            try:
                if test_func():
                    passed += 1
                    print(f"+ {test_func.__name__}")
                else:
                    failed += 1
                    print(f"X {test_func.__name__}")
            except Exception as e:
                failed += 1
                print(f"X {test_func.__name__}: {e}")

        print("\n" + "=" * 50)
        print(f"Test Results: {passed} passed, {failed} failed")

        if failed == 0:
            print("SUCCESS: All tests passed!")
            sys.exit(0)
        else:
            print("FAILED: Some tests failed")
            sys.exit(1)

    except Exception as e:
        print(f"\nTest suite failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
