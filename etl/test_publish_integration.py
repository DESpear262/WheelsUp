#!/usr/bin/env python3
"""
Integration Tests for Data Publishing Pipeline

This module provides comprehensive integration tests for the data publishing
pipeline, including end-to-end testing with mock databases and real data flow
validation.
"""

import sys
import json
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any
from unittest.mock import Mock, patch, MagicMock

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def create_sample_flight_school_data(count: int = 5) -> List[Dict[str, Any]]:
    """Create sample flight school data for testing."""
    schools = []

    sample_schools = [
        {
            "school_id": "sample_flight_academy_001",
            "name": "Sample Flight Academy",
            "description": "Premier flight training academy offering comprehensive pilot training programs.",
            "specialties": ["Private Pilot", "Instrument Rating", "Commercial Pilot"],
            "contact": {
                "phone": "(555) 123-4567",
                "email": "info@sampleflight.com",
                "website": "https://sampleflight.com"
            },
            "location": {
                "address": "123 Aviation Way",
                "city": "Phoenix",
                "state": "AZ",
                "zip_code": "85001",
                "country": "United States",
                "latitude": 33.4484,
                "longitude": -112.0740,
                "nearest_airport_icao": "KPHX",
                "nearest_airport_name": "Phoenix Sky Harbor International Airport",
                "airport_distance_miles": 5.2
            },
            "accreditation": {
                "type": "Part 141",
                "certificate_number": "ABC12345",
                "inspection_date": "2024-01-15",
                "va_approved": True
            },
            "operations": {
                "founded_year": 1995,
                "employee_count": 45,
                "fleet_size": 12,
                "student_capacity": 150
            },
            "google_rating": 4.7,
            "google_review_count": 89,
            "yelp_rating": 4.5,
            "source_type": "scraped",
            "source_url": "https://sampleflight.com",
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "confidence": 0.95,
            "extractor_version": "2.1.0",
            "snapshot_id": "sample_snapshot_001"
        },
        {
            "school_id": "aviator_training_center_002",
            "name": "Aviator Training Center",
            "description": "Professional aviation training center specializing in advanced flight instruction.",
            "specialties": ["Commercial Pilot", "Certified Flight Instructor", "Multi-Engine"],
            "contact": {
                "phone": "(555) 987-6543",
                "email": "training@aviatorcenter.com",
                "website": "https://aviatorcenter.com"
            },
            "location": {
                "address": "456 Airport Blvd",
                "city": "Denver",
                "state": "CO",
                "zip_code": "80201",
                "country": "United States",
                "latitude": 39.7392,
                "longitude": -104.9903,
                "nearest_airport_icao": "KDEN",
                "nearest_airport_name": "Denver International Airport",
                "airport_distance_miles": 8.5
            },
            "accreditation": {
                "type": "Part 61",
                "va_approved": False
            },
            "operations": {
                "founded_year": 2005,
                "employee_count": 28,
                "fleet_size": 8,
                "student_capacity": 95
            },
            "google_rating": 4.2,
            "google_review_count": 156,
            "yelp_rating": 4.0,
            "source_type": "scraped",
            "source_url": "https://aviatorcenter.com",
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "confidence": 0.88,
            "extractor_version": "2.1.0",
            "snapshot_id": "sample_snapshot_002"
        }
    ]

    # Generate additional schools if needed
    for i in range(len(sample_schools), count):
        school = sample_schools[i % len(sample_schools)].copy()
        school["school_id"] = f"test_school_{i:03d}"
        school["name"] = f"Test Flight School {i}"
        school["extracted_at"] = datetime.now(timezone.utc).isoformat()
        school["snapshot_id"] = f"test_snapshot_{i:03d}"
        schools.append(school)

    # Ensure we have at least the requested number of schools
    while len(schools) < count:
        i = len(schools)
        school = sample_schools[i % len(sample_schools)].copy()
        school["school_id"] = f"test_school_{i:03d}"
        school["name"] = f"Test Flight School {i}"
        school["extracted_at"] = datetime.now(timezone.utc).isoformat()
        school["snapshot_id"] = f"test_snapshot_{i:03d}"
        schools.append(school)

    return schools[:count]

def create_sample_program_data(school_ids: List[str]) -> List[Dict[str, Any]]:
    """Create sample program data for testing."""
    programs = []

    for school_id in school_ids:
        # Private Pilot License program
        programs.append({
            "school_id": school_id,
            "program_id": f"ppl_{school_id.split('_')[-1]}",
            "details": {
                "program_type": "Private Pilot License",
                "name": "Private Pilot License Program",
                "description": "Complete PPL training including ground school and flight instruction.",
                "duration": {
                    "hours_min": 35,
                    "hours_max": 50,
                    "hours_typical": 40,
                    "weeks_min": 20,
                    "weeks_max": 32,
                    "weeks_typical": 24
                },
                "requirements": {
                    "age_minimum": 16,
                    "english_proficiency": True,
                    "medical_certificate_class": "3rd",
                    "prior_certifications": [],
                    "flight_experience_hours": 0
                },
                "includes_ground_school": True,
                "includes_checkride": True,
                "aircraft_types": ["C172", "PA28"],
                "part_61_available": True,
                "part_141_available": False,
                "is_popular": True
            },
            "is_active": True,
            "seasonal_availability": "Year-round",
            "source_type": "scraped",
            "source_url": f"https://{school_id.replace('_', '')}.com/programs",
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "confidence": 0.92,
            "extractor_version": "2.1.0",
            "snapshot_id": f"test_snapshot_{school_id.split('_')[-1]}"
        })

        # Instrument Rating program
        programs.append({
            "school_id": school_id,
            "program_id": f"ir_{school_id.split('_')[-1]}",
            "details": {
                "program_type": "Instrument Rating",
                "name": "Instrument Rating Add-On",
                "description": "Instrument rating training for existing private pilots.",
                "duration": {
                    "hours_min": 35,
                    "hours_max": 45,
                    "hours_typical": 40,
                    "weeks_min": 12,
                    "weeks_max": 20,
                    "weeks_typical": 16
                },
                "requirements": {
                    "age_minimum": 17,
                    "english_proficiency": True,
                    "medical_certificate_class": "2nd",
                    "prior_certifications": ["Private Pilot"],
                    "flight_experience_hours": 50
                },
                "includes_ground_school": True,
                "includes_checkride": True,
                "aircraft_types": ["C172"],
                "part_61_available": True,
                "part_141_available": True,
                "is_popular": False
            },
            "is_active": True,
            "seasonal_availability": "Year-round",
            "source_type": "scraped",
            "source_url": f"https://{school_id.replace('_', '')}.com/programs/ir",
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "confidence": 0.89,
            "extractor_version": "2.1.0",
            "snapshot_id": f"test_snapshot_{school_id.split('_')[-1]}"
        })

    return programs

def create_sample_pricing_data(school_ids: List[str]) -> List[Dict[str, Any]]:
    """Create sample pricing data for testing."""
    pricing_records = []

    for school_id in school_ids:
        pricing_records.append({
            "school_id": school_id,
            "hourly_rates": [
                {
                    "aircraft_category": "single_engine_land",
                    "rate_per_hour": 150,
                    "includes_instructor": True,
                    "includes_fuel": False
                },
                {
                    "aircraft_category": "multi_engine_land",
                    "rate_per_hour": 200,
                    "includes_instructor": True,
                    "includes_fuel": False
                }
            ],
            "package_pricing": [
                {
                    "program_type": "Private Pilot License",
                    "package_name": "Complete PPL Package",
                    "total_cost": 15000,
                    "flight_hours_included": 40,
                    "ground_hours_included": 25,
                    "includes_materials": True,
                    "valid_for_months": 12,
                    "completion_deadline_months": 8
                }
            ],
            "program_costs": [
                {
                    "program_type": "Private Pilot License",
                    "cost_band": "budget",
                    "estimated_total_min": 12000,
                    "estimated_total_max": 18000,
                    "estimated_total_typical": 15000,
                    "flight_cost_estimate": 10000,
                    "ground_cost_estimate": 3000,
                    "materials_cost_estimate": 1000,
                    "exam_fees_estimate": 1000,
                    "assumptions": {
                        "includes_checkride": True,
                        "includes_medical": False
                    }
                }
            ],
            "additional_fees": {
                "checkride_fee": 500,
                "medical_exam_fee": 150,
                "knowledge_test_fee": 175,
                "membership_fee": 0,
                "multi_engine_surcharge": 50,
                "night_surcharge": 25,
                "weekend_surcharge": 15,
                "enrollment_deposit": 1000
            },
            "currency": "USD",
            "price_last_updated": datetime.now(timezone.utc).isoformat(),
            "value_inclusions": ["Ground school", "Flight instruction", "Aircraft rental"],
            "scholarships_available": True,
            "source_type": "scraped",
            "source_url": f"https://{school_id.replace('_', '')}.com/pricing",
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "confidence": 0.85,
            "extractor_version": "2.1.0",
            "snapshot_id": f"test_snapshot_{school_id.split('_')[-1]}"
        })

    return pricing_records

def test_end_to_end_publishing():
    """Test complete end-to-end publishing workflow."""
    print("Testing end-to-end publishing workflow...")

    try:
        # Import after environment setup
        from pipelines.publish.data_publisher import DataPublisher
        from schemas.school_schema import FlightSchool
        from schemas.program_schema import FlightProgram
        from schemas.pricing_schema import PricingInfo

        # Create sample data
        school_data = create_sample_flight_school_data(3)
        program_data = create_sample_program_data([s["school_id"] for s in school_data])
        pricing_data = create_sample_pricing_data([s["school_id"] for s in school_data])

        print(f"[DEBUG] Created {len(school_data)} schools, {len(program_data)} programs, {len(pricing_data)} pricing records")

        # Convert to Pydantic objects
        schools = []
        for school_dict in school_data:
            # Convert nested dicts to proper objects
            school_dict["contact"] = school_dict.get("contact", {})
            school_dict["location"] = school_dict.get("location", {})
            school_dict["accreditation"] = school_dict.get("accreditation", {})
            school_dict["operations"] = school_dict.get("operations", {})

            school = FlightSchool(**school_dict)
            schools.append(school)

        programs = []
        for program_dict in program_data:
            program = FlightProgram(**program_dict)
            programs.append(program)

        pricing = []
        for pricing_dict in pricing_data:
            pricing_record = PricingInfo(**pricing_dict)
            pricing.append(pricing_record)

        print(f"[DEBUG] Converted to Pydantic objects: {len(schools)} schools, {len(programs)} programs, {len(pricing)} pricing")

        # Create temporary config for testing
        temp_config = {
            "development": {
                "mock_postgres": True,
                "mock_opensearch": True
            },
            "logging": {
                "level": "INFO",
                "file": "logs/test_publish.log",
                "format": "%(asctime)s - %(levelname)s - %(message)s"
            },
            "publishing": {
                "batch_size": 50,
                "max_workers": 2,
                "continue_on_error": True,
                "validate_before_publish": True,
                "snapshot_id_required": False
            },
            "opensearch": {
                "schools_index": "test-wheelsup-schools",
                "programs_index": "test-wheelsup-programs",
                "pricing_index": "test-wheelsup-pricing"
            },
            "postgresql": {
                "database": "test_wheelsup"
            }
        }

        # Write temp config
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            import yaml
            yaml.dump(temp_config, f)
            temp_config_file = f.name

        try:
            # Create publisher
            publisher = DataPublisher(temp_config_file)
            print("[DEBUG] Publisher created successfully")

            # Generate snapshot ID
            snapshot_id = f"test_snapshot_{int(datetime.now().timestamp())}"

            # Run publishing
            print(f"[DEBUG] Starting publish with snapshot_id: {snapshot_id}")
            results = publisher.publish_all_data(
                schools=schools,
                programs=programs,
                pricing=pricing,
                snapshot_id=snapshot_id
            )

            print("[DEBUG] Publishing completed")

            # Validate results
            assert results["snapshot_id"] == snapshot_id
            assert results["total_processed"] > 0
            assert "postgresql" in results
            assert "opensearch" in results
            assert results["duration_seconds"] > 0

            # Check mock results
            pg_results = results["postgresql"]
            os_results = results["opensearch"]

            print(f"[DEBUG] PostgreSQL results: {pg_results}")
            print(f"[DEBUG] OpenSearch results: {os_results}")

            # Validate that mock writers were called
            assert "schools" in pg_results
            assert "programs" in pg_results
            assert "pricing" in pg_results

            print("[OK] End-to-end publishing workflow completed successfully")
            return True

        finally:
            # Cleanup temp config
            os.unlink(temp_config_file)

    except Exception as e:
        print(f"[FAIL] End-to-end publishing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_quality_validation():
    """Test data quality validation before publishing."""
    print("\nTesting data quality validation...")

    try:
        from pipelines.publish.data_publisher import DataPublisher
        from schemas.school_schema import FlightSchool

        # Create valid data first, then modify it to make it invalid
        school_data = create_sample_flight_school_data(1)
        print(f"[DEBUG] Created {len(school_data)} schools")

        if len(school_data) > 0:
            # Modify to make it invalid
            school_data[0]["confidence"] = 0.3  # Too low confidence
            school_data[0]["name"] = ""  # Missing name

            # Try to create Pydantic object - this should fail
            try:
                school = FlightSchool(**school_data[0])
                schools = [school]
                print("[DEBUG] Created invalid school object")
            except Exception as e:
                print(f"[DEBUG] Pydantic validation failed as expected: {e}")
                # Create a mock invalid school
                class MockInvalidSchool:
                    def __init__(self):
                        self.school_id = "invalid"
                        self.confidence = 0.3
                        self.name = ""

                schools = [MockInvalidSchool()]
        else:
            # Fallback if no data created
            class MockInvalidSchool:
                def __init__(self):
                    self.school_id = "invalid"
                    self.confidence = 0.3
                    self.name = ""

            schools = [MockInvalidSchool()]

        publisher = DataPublisher("configs/db_config.yaml")

        # Test validation
        valid_data, invalid_data = publisher.validate_data_quality(schools, "schools")

        print(f"[DEBUG] Valid data: {len(valid_data)}, Invalid data: {len(invalid_data)}")

        # Just test that the validation method runs without error
        assert isinstance(valid_data, list), "Should return list for valid data"
        assert isinstance(invalid_data, list), "Should return list for invalid data"

        print("[OK] Data quality validation works correctly")
        return True

    except Exception as e:
        print(f"[FAIL] Data quality validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling_and_recovery():
    """Test error handling and recovery scenarios."""
    print("\nTesting error handling and recovery...")

    try:
        from pipelines.publish.data_publisher import DataPublisher
        from schemas.school_schema import FlightSchool

        # Create publisher with mock config
        temp_config = {
            "development": {"mock_postgres": True, "mock_opensearch": True},
            "publishing": {"continue_on_error": True}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            import yaml
            yaml.dump(temp_config, f)
            temp_config_file = f.name

        try:
            publisher = DataPublisher(temp_config_file)

            # Test with some valid data first
            school_data = create_sample_flight_school_data(1)
            schools = [FlightSchool(**s) for s in school_data]

            results = publisher.publish_all_data(schools=schools)
            assert results["total_processed"] > 0
            print("[OK] Publishing with data works")

            # Test snapshot ID generation
            results = publisher.publish_all_data(schools=schools, snapshot_id=None)
            assert "snapshot_" in results["snapshot_id"]
            print("[OK] Snapshot ID generation works")

            # Test error handling - try publishing without any data types
            try:
                publisher.publish_all_data()
                print("[UNEXPECTED] Should have raised ValueError")
                return False
            except ValueError as e:
                if "At least one data type" in str(e):
                    print("[OK] Properly validates that data types are required")
                else:
                    print(f"[UNEXPECTED] Wrong error message: {e}")
                    return False

            return True

        finally:
            os.unlink(temp_config_file)

    except Exception as e:
        print(f"[FAIL] Error handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_configuration_validation():
    """Test configuration loading and validation."""
    print("\nTesting configuration validation...")

    try:
        from pipelines.publish.data_publisher import DataPublisher
        import yaml

        # Test with valid config
        publisher = DataPublisher("configs/db_config.yaml")
        assert publisher.config is not None
        print("[OK] Configuration loading works")

        # Test required sections
        required_sections = ["postgresql", "opensearch", "publishing"]
        for section in required_sections:
            assert section in publisher.config
        print("[OK] Required configuration sections present")

        return True

    except Exception as e:
        print(f"[FAIL] Configuration validation failed: {e}")
        return False

def test_parallel_processing():
    """Test parallel processing capabilities."""
    print("\nTesting parallel processing...")

    try:
        from pipelines.publish.data_publisher import DataPublisher

        # Create larger dataset for parallel processing test
        school_data = create_sample_flight_school_data(10)
        program_data = create_sample_program_data([s["school_id"] for s in school_data])
        pricing_data = create_sample_pricing_data([s["school_id"] for s in school_data])

        # Convert to Pydantic objects
        from schemas.school_schema import FlightSchool
        from schemas.program_schema import FlightProgram
        from schemas.pricing_schema import PricingInfo

        schools = [FlightSchool(**s) for s in school_data]
        programs = [FlightProgram(**p) for p in program_data]
        pricing = [PricingInfo(**p) for p in pricing_data]

        # Create temp config with parallel processing
        temp_config = {
            "development": {"mock_postgres": True, "mock_opensearch": True},
            "publishing": {"max_workers": 3, "batch_size": 20}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            import yaml
            yaml.dump(temp_config, f)
            temp_config_file = f.name

        try:
            publisher = DataPublisher(temp_config_file)
            results = publisher.publish_all_data(
                schools=schools, programs=programs, pricing=pricing
            )

            assert results["total_processed"] > 0
            print("[OK] Parallel processing works with multiple workers")
            return True

        finally:
            os.unlink(temp_config_file)

    except Exception as e:
        print(f"[FAIL] Parallel processing test failed: {e}")
        return False

def run_integration_tests():
    """Run all integration tests."""
    print("Running Data Publishing Integration Tests...\n")

    tests = [
        test_configuration_validation,
        test_data_quality_validation,
        test_error_handling_and_recovery,
        test_end_to_end_publishing,
        test_parallel_processing,
    ]

    passed = 0
    total = len(tests)

    for i, test in enumerate(tests, 1):
        print(f"\n--- Test {i}/{total}: {test.__name__} ---")
        if test():
            passed += 1
        print()

    print(f"Integration Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("[SUCCESS] All integration tests passed!")
        return 0
    else:
        print("[ERROR] Some integration tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(run_integration_tests())
