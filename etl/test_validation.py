#!/usr/bin/env python3
"""
Test script for the validation and normalization pipeline.

This script tests the validation and normalization functionality
using example data from the schemas.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from etl.schemas.school_schema import get_example_school
from etl.schemas.pricing_schema import get_example_pricing
from etl.schemas.program_schema import get_example_program
from etl.pipelines.normalize import (
    validate_all_data,
    normalize_all_data,
    ValidationResult,
    NormalizationResult
)


def test_validation():
    """Test the validation functionality."""
    print("Testing validation pipeline...")

    # Get example data
    school = get_example_school()
    pricing = get_example_pricing()
    programs = [get_example_program()]

    # Run validation
    validation_results = validate_all_data(school, pricing, programs)

    print(f"Validation completed for {len(validation_results)} objects:")

    total_errors = 0
    total_warnings = 0

    for obj_type, result in validation_results.items():
        status = "PASS" if result.is_valid else "FAIL"
        print(f"  {obj_type}: {status} - {result.summary()}")

        total_errors += len(result.errors)
        total_warnings += len(result.warnings)

        if result.errors:
            print("    Errors:")
            for error in result.errors[:3]:  # Show first 3 errors
                print(f"      - {error}")

        if result.warnings:
            print("    Warnings:")
            for warning in result.warnings[:3]:  # Show first 3 warnings
                print(f"      - {warning}")

    print(f"\nTotal: {total_errors} errors, {total_warnings} warnings")

    return total_errors == 0


def test_normalization():
    """Test the normalization functionality."""
    print("\nTesting normalization pipeline...")

    # Get example data
    school = get_example_school()
    pricing = get_example_pricing()
    programs = [get_example_program()]

    # Run normalization
    normalized_school, normalized_pricing, normalized_programs, normalization_results = normalize_all_data(
        school, pricing, programs
    )

    print(f"Normalization completed for {len(normalization_results)} objects:")

    total_transformations = 0

    for obj_type, result in normalization_results.items():
        transformations = len(result.transformations_applied)
        total_transformations += transformations
        print(f"  {obj_type}: {transformations} transformations applied")

        if result.transformations_applied:
            print("    Transformations:")
            for transformation in result.transformations_applied[:3]:  # Show first 3
                # Replace Unicode arrow with ASCII equivalent for Windows compatibility
                safe_transformation = transformation.replace('\u2192', '->')
                print(f"      - {safe_transformation}")

        if result.warnings:
            print("    Warnings:")
            for warning in result.warnings:
                print(f"      - {warning}")

    print(f"\nTotal transformations applied: {total_transformations}")

    return True


def test_with_invalid_data():
    """Test validation with intentionally invalid data."""
    print("\nTesting validation with invalid data...")

    from etl.schemas.school_schema import FlightSchool, ContactInfo, LocationInfo, AccreditationInfo, OperationalInfo

    # Create school with data that passes Pydantic but fails business logic validation
    # We'll skip the schema validators and test our business logic directly
    from etl.pipelines.normalize.validators import ValidationResult

    # Test individual validation functions directly
    from etl.utils.validation_rules import (
        validate_coordinates, validate_airport_distance, validate_fleet_size, validate_employee_count
    )

    result = ValidationResult()

    # Test invalid coordinates
    is_valid, error = validate_coordinates(100, 50)  # Invalid latitude
    if not is_valid:
        result.add_error(f"Coordinate validation: {error}")

    # Test invalid airport distance
    is_valid, error = validate_airport_distance(-5)  # Negative distance
    if not is_valid:
        result.add_error(f"Airport distance validation: {error}")

    # Test invalid fleet size
    is_valid, error = validate_fleet_size(0)  # Zero fleet
    if not is_valid:
        result.add_error(f"Fleet size validation: {error}")

    # Test invalid employee count
    is_valid, error = validate_employee_count(0)  # Zero employees
    if not is_valid:
        result.add_error(f"Employee count validation: {error}")

    print(f"Business logic validation: {len(result.errors)} errors, {len(result.warnings)} warnings")

    if result.errors:
        print("  Errors found (as expected):")
        for error in result.errors[:5]:  # Show first 5
            print(f"    - {error}")

    return len(result.errors) > 0  # Should have errors


if __name__ == "__main__":
    print("Flight School Data Validation & Normalization - Test Suite")
    print("=" * 60)

    try:
        # Test validation with valid data
        validation_passed = test_validation()

        # Test normalization
        normalization_passed = test_normalization()

        # Test validation with invalid data
        invalid_test_passed = test_with_invalid_data()

        print("\n" + "=" * 60)
        print("Test Results:")
        print(f"  Validation (valid data): {'PASS' if validation_passed else 'FAIL'}")
        print(f"  Normalization: {'PASS' if normalization_passed else 'FAIL'}")
        print(f"  Validation (invalid data): {'PASS' if invalid_test_passed else 'FAIL'}")

        overall_success = all([validation_passed, normalization_passed, invalid_test_passed])
        print(f"\nOverall: {'SUCCESS' if overall_success else 'FAILED'}")

        sys.exit(0 if overall_success else 1)

    except Exception as e:
        print(f"\nTest suite failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
