"""
Field Validators for Flight School Data

This module provides validation functions for flight school data schemas,
performing field-level validation and cross-schema consistency checks.
"""

from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import logging

from etl.schemas.school_schema import FlightSchool, OperationalInfo, LocationInfo, ContactInfo
from etl.schemas.pricing_schema import PricingInfo, HourlyRate, PackagePricing, ProgramCostEstimate
from etl.schemas.program_schema import FlightProgram, ProgramDetails, ProgramDuration
from etl.utils.validation_rules import (
    validate_hourly_rate, validate_total_cost, validate_training_hours,
    validate_training_weeks, validate_fleet_size, validate_employee_count,
    validate_coordinates, validate_airport_distance, validate_phone_number,
    validate_email_domain, validate_url_format, validate_cost_consistency,
    validate_duration_consistency, calculate_field_confidence, clean_whitespace
)

logger = logging.getLogger(__name__)


class ValidationResult:
    """Container for validation results."""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.field_confidence_updates: Dict[str, float] = {}
        self.normalized_values: Dict[str, Any] = {}

    def add_error(self, message: str):
        """Add a validation error."""
        self.errors.append(message)
        logger.warning(f"Validation error: {message}")

    def add_warning(self, message: str):
        """Add a validation warning."""
        self.warnings.append(message)
        logger.info(f"Validation warning: {message}")

    def update_confidence(self, field_path: str, confidence: float):
        """Update confidence score for a field."""
        self.field_confidence_updates[field_path] = confidence

    def set_normalized_value(self, field_path: str, value: Any):
        """Set a normalized value for a field."""
        self.normalized_values[field_path] = value

    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return len(self.errors) == 0

    def summary(self) -> str:
        """Get a summary of validation results."""
        parts = []
        if self.errors:
            parts.append(f"{len(self.errors)} errors")
        if self.warnings:
            parts.append(f"{len(self.warnings)} warnings")
        if not parts:
            parts.append("passed")
        return ", ".join(parts)


def validate_flight_school(school: FlightSchool) -> ValidationResult:
    """
    Validate a FlightSchool object.

    Args:
        school: FlightSchool instance to validate

    Returns:
        ValidationResult with errors, warnings, and updates
    """
    result = ValidationResult()

    # Validate core identifiers
    if not school.school_id or len(school.school_id) < 8:
        result.add_error("School ID is required and must be at least 8 characters")

    if not school.name or len(school.name.strip()) == 0:
        result.add_error("School name is required")
    else:
        # Normalize name
        normalized_name = clean_whitespace(school.name)
        if normalized_name != school.name:
            result.set_normalized_value("name", normalized_name)

    # Validate contact information
    if school.contact.phone:
        is_valid, error = validate_phone_number(school.contact.phone)
        if not is_valid:
            result.add_error(f"Phone validation failed: {error}")
            result.update_confidence("contact.phone", calculate_field_confidence(school.confidence, False))

    if school.contact.email:
        is_valid, error = validate_email_domain(school.contact.email)
        if not is_valid:
            result.add_error(f"Email validation failed: {error}")
            result.update_confidence("contact.email", calculate_field_confidence(school.confidence, False))

    if school.contact.website:
        is_valid, error = validate_url_format(school.contact.website)
        if not is_valid:
            result.add_error(f"Website validation failed: {error}")
            result.update_confidence("contact.website", calculate_field_confidence(school.confidence, False))

    # Validate location information
    if school.location.latitude is not None and school.location.longitude is not None:
        is_valid, error = validate_coordinates(school.location.latitude, school.location.longitude)
        if not is_valid:
            result.add_error(f"Coordinates validation failed: {error}")
            result.update_confidence("location.latitude", calculate_field_confidence(school.confidence, False))
            result.update_confidence("location.longitude", calculate_field_confidence(school.confidence, False))

    if school.location.airport_distance_miles is not None:
        is_valid, error = validate_airport_distance(school.location.airport_distance_miles)
        if not is_valid:
            result.add_error(f"Airport distance validation failed: {error}")
            result.update_confidence("location.airport_distance_miles", calculate_field_confidence(school.confidence, False))

    # Validate operational information
    if school.operations.fleet_size is not None:
        is_valid, error = validate_fleet_size(school.operations.fleet_size)
        if not is_valid:
            result.add_error(f"Fleet size validation failed: {error}")
            result.update_confidence("operations.fleet_size", calculate_field_confidence(school.confidence, False))

    if school.operations.employee_count is not None:
        is_valid, error = validate_employee_count(school.operations.employee_count)
        if not is_valid:
            result.add_error(f"Employee count validation failed: {error}")
            result.update_confidence("operations.employee_count", calculate_field_confidence(school.confidence, False))

    if school.operations.founded_year is not None:
        current_year = datetime.now().year
        if school.operations.founded_year > current_year:
            result.add_error(f"Founded year {school.operations.founded_year} cannot be in the future")
            result.update_confidence("operations.founded_year", calculate_field_confidence(school.confidence, False))

    # Validate ratings
    if school.google_rating is not None:
        if not (1.0 <= school.google_rating <= 5.0):
            result.add_error(f"Google rating {school.google_rating} must be between 1.0 and 5.0")
            result.update_confidence("google_rating", calculate_field_confidence(school.confidence, False))

    if school.google_review_count is not None and school.google_review_count < 0:
        result.add_error("Google review count cannot be negative")
        result.update_confidence("google_review_count", calculate_field_confidence(school.confidence, False))

    return result


def validate_pricing_info(pricing: PricingInfo) -> ValidationResult:
    """
    Validate a PricingInfo object.

    Args:
        pricing: PricingInfo instance to validate

    Returns:
        ValidationResult with errors, warnings, and updates
    """
    result = ValidationResult()

    # Validate hourly rates
    for i, rate in enumerate(pricing.hourly_rates):
        aircraft_type = rate.aircraft_category.value.lower().replace("_", " ")

        is_valid, error = validate_hourly_rate(rate.rate_per_hour, aircraft_type)
        if not is_valid:
            result.add_error(f"Hourly rate validation failed for {rate.aircraft_category.value}: {error}")
            result.update_confidence(f"hourly_rates[{i}].rate_per_hour", calculate_field_confidence(pricing.confidence, False))

        # Check block hour ranges
        if rate.block_hours_min is not None and rate.block_hours_max is not None:
            if rate.block_hours_max < rate.block_hours_min:
                result.add_error(f"Block hours max ({rate.block_hours_max}) cannot be less than min ({rate.block_hours_min})")
                result.update_confidence(f"hourly_rates[{i}].block_hours_min", calculate_field_confidence(pricing.confidence, False))
                result.update_confidence(f"hourly_rates[{i}].block_hours_max", calculate_field_confidence(pricing.confidence, False))

    # Validate package pricing
    for i, package in enumerate(pricing.package_pricing):
        program_type = package.program_type.lower().replace(" ", "_")

        is_valid, error = validate_total_cost(package.total_cost, program_type)
        if not is_valid:
            result.add_error(f"Package pricing validation failed for {package.program_type}: {error}")
            result.update_confidence(f"package_pricing[{i}].total_cost", calculate_field_confidence(pricing.confidence, False))

        # Check included hours vs total cost consistency
        if package.flight_hours_included and package.flight_hours_included > 0:
            # Estimate reasonable cost per hour (rough check)
            avg_hourly_rate = 150  # Rough average
            expected_cost = package.flight_hours_included * avg_hourly_rate
            variance = abs(package.total_cost - expected_cost) / expected_cost

            if variance > 1.0:  # Allow 100% variance for packages
                result.add_warning(f"Package cost ${package.total_cost} seems inconsistent with {package.flight_hours_included} included hours")

    # Validate program cost estimates
    for i, estimate in enumerate(pricing.program_costs):
        program_type = estimate.program_type.lower().replace(" ", "_")

        # Check cost ranges
        if estimate.estimated_total_min and estimate.estimated_total_max:
            if estimate.estimated_total_max < estimate.estimated_total_min:
                result.add_error("Maximum estimated cost cannot be less than minimum")
                result.update_confidence(f"program_costs[{i}].estimated_total_min", calculate_field_confidence(pricing.confidence, False))
                result.update_confidence(f"program_costs[{i}].estimated_total_max", calculate_field_confidence(pricing.confidence, False))

            # Validate against program type expectations
            avg_cost = (estimate.estimated_total_min + estimate.estimated_total_max) / 2
            is_valid, error = validate_total_cost(avg_cost, program_type)
            if not is_valid:
                result.add_warning(f"Program cost estimate seems unusual: {error}")

    # Validate additional fees
    if pricing.additional_fees.enrollment_deposit and pricing.additional_fees.enrollment_deposit < 0:
        result.add_error("Enrollment deposit cannot be negative")
        result.update_confidence("additional_fees.enrollment_deposit", calculate_field_confidence(pricing.confidence, False))

    if pricing.additional_fees.checkride_fee and pricing.additional_fees.checkride_fee < 0:
        result.add_error("Checkride fee cannot be negative")
        result.update_confidence("additional_fees.checkride_fee", calculate_field_confidence(pricing.confidence, False))

    return result


def validate_flight_program(program: FlightProgram) -> ValidationResult:
    """
    Validate a FlightProgram object.

    Args:
        program: FlightProgram instance to validate

    Returns:
        ValidationResult with errors, warnings, and updates
    """
    result = ValidationResult()

    # Validate program details
    program_type = program.details.program_type.value

    # Validate duration information
    if program.details.duration.hours_typical:
        is_valid, error = validate_training_hours(program.details.duration.hours_typical, program_type)
        if not is_valid:
            result.add_error(f"Training hours validation failed: {error}")
            result.update_confidence("details.duration.hours_typical", calculate_field_confidence(program.confidence, False))

    if program.details.duration.weeks_typical:
        is_valid, error = validate_training_weeks(program.details.duration.weeks_typical, program_type)
        if not is_valid:
            result.add_error(f"Training weeks validation failed: {error}")
            result.update_confidence("details.duration.weeks_typical", calculate_field_confidence(program.confidence, False))

    # Check duration consistency
    if (program.details.duration.hours_typical and program.details.duration.weeks_typical):
        is_valid, error = validate_duration_consistency(
            program.details.duration.hours_typical,
            program.details.duration.weeks_typical
        )
        if not is_valid:
            result.add_warning(f"Duration consistency check: {error}")

    # Validate hour ranges
    if (program.details.duration.hours_min and program.details.duration.hours_max):
        if program.details.duration.hours_max < program.details.duration.hours_min:
            result.add_error("Maximum hours cannot be less than minimum hours")
            result.update_confidence("details.duration.hours_min", calculate_field_confidence(program.confidence, False))
            result.update_confidence("details.duration.hours_max", calculate_field_confidence(program.confidence, False))

    if (program.details.duration.weeks_min and program.details.duration.weeks_max):
        if program.details.duration.weeks_max < program.details.duration.weeks_min:
            result.add_error("Maximum weeks cannot be less than minimum weeks")
            result.update_confidence("details.duration.weeks_min", calculate_field_confidence(program.confidence, False))
            result.update_confidence("details.duration.weeks_max", calculate_field_confidence(program.confidence, False))

    # Validate requirements
    if program.details.requirements.age_minimum:
        if program.details.requirements.age_minimum < 14 or program.details.requirements.age_minimum > 100:
            result.add_error(f"Age minimum {program.details.requirements.age_minimum} is outside reasonable range (14-100)")
            result.update_confidence("details.requirements.age_minimum", calculate_field_confidence(program.confidence, False))

    if program.details.requirements.flight_experience_hours and program.details.requirements.flight_experience_hours < 0:
        result.add_error("Flight experience hours cannot be negative")
        result.update_confidence("details.requirements.flight_experience_hours", calculate_field_confidence(program.confidence, False))

    return result


def validate_cross_schema_consistency(
    school: Optional[FlightSchool] = None,
    pricing: Optional[PricingInfo] = None,
    programs: Optional[List[FlightProgram]] = None
) -> ValidationResult:
    """
    Validate consistency across related schema objects.

    Args:
        school: FlightSchool instance
        pricing: PricingInfo instance
        programs: List of FlightProgram instances

    Returns:
        ValidationResult with cross-schema validation results
    """
    result = ValidationResult()

    # Validate school-pricing consistency
    if school and pricing:
        if school.school_id != pricing.school_id:
            result.add_error(f"School ID mismatch: school={school.school_id}, pricing={pricing.school_id}")

        # Check if school has programs that match pricing
        if programs:
            school_program_types = {p.details.program_type.value for p in programs}
            pricing_program_types = {p.program_type for p in pricing.program_costs}

            missing_pricing = school_program_types - pricing_program_types
            if missing_pricing:
                result.add_warning(f"Programs offered but no pricing: {missing_pricing}")

            extra_pricing = pricing_program_types - school_program_types
            if extra_pricing:
                result.add_warning(f"Pricing for programs not offered: {extra_pricing}")

    # Validate program-pricing consistency
    if programs and pricing:
        for program in programs:
            # Find matching pricing estimate
            matching_pricing = None
            for price_est in pricing.program_costs:
                if price_est.program_type == program.details.program_type.value:
                    matching_pricing = price_est
                    break

            if matching_pricing and program.details.duration.hours_typical:
                # Check if package pricing exists for this program
                matching_package = None
                for package in pricing.package_pricing:
                    if package.program_type == program.details.program_type.value:
                        matching_package = package
                        break

                if matching_package and matching_package.flight_hours_included:
                    # Validate cost consistency
                    is_valid, error = validate_cost_consistency(
                        matching_package.total_cost / matching_package.flight_hours_included,  # Effective hourly rate
                        matching_package.total_cost,
                        matching_package.flight_hours_included
                    )
                    if not is_valid:
                        result.add_warning(f"Cost consistency issue for {program.details.program_type.value}: {error}")

    return result


def validate_all_data(
    school: FlightSchool,
    pricing: PricingInfo,
    programs: List[FlightProgram]
) -> Dict[str, ValidationResult]:
    """
    Validate all flight school data objects comprehensively.

    Args:
        school: FlightSchool instance
        pricing: PricingInfo instance
        programs: List of FlightProgram instances

    Returns:
        Dictionary mapping object types to ValidationResult instances
    """
    results = {}

    # Validate individual objects
    results['school'] = validate_flight_school(school)
    results['pricing'] = validate_pricing_info(pricing)

    for i, program in enumerate(programs):
        results[f'program_{i}'] = validate_flight_program(program)

    # Cross-schema validation
    results['cross_schema'] = validate_cross_schema_consistency(school, pricing, programs)

    return results


# Utility functions for applying validation results
def apply_validation_updates(
    school: FlightSchool,
    pricing: PricingInfo,
    programs: List[FlightProgram],
    validation_results: Dict[str, ValidationResult]
) -> Tuple[FlightSchool, PricingInfo, List[FlightProgram]]:
    """
    Apply validation updates (normalized values, confidence adjustments) to the data objects.

    Args:
        school: Original FlightSchool instance
        pricing: Original PricingInfo instance
        programs: Original list of FlightProgram instances
        validation_results: Results from validate_all_data()

    Returns:
        Updated instances with validation corrections applied
    """
    # Apply school updates
    school_result = validation_results.get('school')
    if school_result and school_result.normalized_values:
        # Apply normalized values (this would require more complex logic for nested updates)
        pass

    # Apply confidence updates based on validation failures
    if school_result and school_result.field_confidence_updates:
        # Reduce overall confidence if critical fields failed validation
        critical_failures = [k for k in school_result.field_confidence_updates.keys()
                           if school_result.field_confidence_updates[k] < school.confidence]
        if critical_failures:
            school.confidence = min(school.confidence, 0.7)  # Reduce confidence for validation issues

    return school, pricing, programs