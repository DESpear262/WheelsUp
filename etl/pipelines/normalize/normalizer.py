"""
Data Normalizer for Flight Training Information

This module provides normalization functions for flight training data,
including cost band conversion, unit standardization, and data cleanup.
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import logging

from etl.schemas.school_schema import FlightSchool
from etl.schemas.pricing_schema import PricingInfo, CostBand
from etl.schemas.program_schema import FlightProgram
from etl.utils.validation_rules import normalize_cost_to_band, clean_whitespace, normalize_text_case

logger = logging.getLogger(__name__)


class NormalizationResult:
    """Container for normalization results."""

    def __init__(self):
        self.normalized_fields: Dict[str, Any] = {}
        self.transformations_applied: List[str] = []
        self.warnings: List[str] = []

    def add_normalization(self, field_path: str, original_value: Any, new_value: Any, reason: str = ""):
        """Record a normalization transformation."""
        self.normalized_fields[field_path] = {
            'original': original_value,
            'normalized': new_value,
            'reason': reason
        }
        description = f"Normalized {field_path}: {original_value} -> {new_value}"
        if reason:
            description += f" ({reason})"
        self.transformations_applied.append(description)
        logger.info(description)

    def add_warning(self, message: str):
        """Add a normalization warning."""
        self.warnings.append(message)
        logger.warning(f"Normalization warning: {message}")


def normalize_flight_school(school: FlightSchool) -> tuple[FlightSchool, NormalizationResult]:
    """
    Normalize a FlightSchool object.

    Args:
        school: FlightSchool instance to normalize

    Returns:
        Tuple of (normalized_school, normalization_result)
    """
    result = NormalizationResult()
    normalized_school = school.copy(deep=True)

    # Normalize text fields
    if school.name:
        normalized_name = clean_whitespace(school.name)
        if normalized_name != school.name:
            result.add_normalization("name", school.name, normalized_name, "whitespace cleanup")
            normalized_school.name = normalized_name

    if school.description:
        normalized_desc = clean_whitespace(school.description)
        if normalized_desc != school.description:
            result.add_normalization("description", school.description, normalized_desc, "whitespace cleanup")
            normalized_school.description = normalized_desc

    # Normalize location fields
    if school.location.address:
        normalized_address = clean_whitespace(school.location.address)
        if normalized_address != school.location.address:
            result.add_normalization("location.address", school.location.address, normalized_address, "whitespace cleanup")
            normalized_school.location.address = normalized_address

    if school.location.city:
        normalized_city = normalize_text_case(school.location.city, "title")
        if normalized_city != school.location.city:
            result.add_normalization("location.city", school.location.city, normalized_city, "title case")
            normalized_school.location.city = normalized_city

    if school.location.state:
        normalized_state = school.location.state.upper()
        if normalized_state != school.location.state:
            result.add_normalization("location.state", school.location.state, normalized_state, "uppercase")
            normalized_school.location.state = normalized_state

    # Normalize contact fields
    if school.contact.website and not school.contact.website.startswith(('http://', 'https://')):
        normalized_url = f"https://{school.contact.website}"
        result.add_normalization("contact.website", school.contact.website, normalized_url, "add https protocol")
        normalized_school.contact.website = normalized_url

    # Normalize specialty names
    normalized_specialties = []
    for specialty in school.specialties:
        normalized_specialty = normalize_text_case(specialty, "title")
        if normalized_specialty != specialty:
            result.add_normalization(f"specialties[{school.specialties.index(specialty)}]",
                                   specialty, normalized_specialty, "title case")
        normalized_specialties.append(normalized_specialty)
    normalized_school.specialties = normalized_specialties

    return normalized_school, result


def normalize_pricing_info(pricing: PricingInfo) -> tuple[PricingInfo, NormalizationResult]:
    """
    Normalize a PricingInfo object, including cost band conversion.

    Args:
        pricing: PricingInfo instance to normalize

    Returns:
        Tuple of (normalized_pricing, normalization_result)
    """
    result = NormalizationResult()
    normalized_pricing = pricing.copy(deep=True)

    # Normalize package names and descriptions
    for i, package in enumerate(normalized_pricing.package_pricing):
        if package.package_name:
            normalized_name = clean_whitespace(package.package_name)
            if normalized_name != package.package_name:
                result.add_normalization(f"package_pricing[{i}].package_name",
                                       package.package_name, normalized_name, "whitespace cleanup")
                normalized_pricing.package_pricing[i].package_name = normalized_name

    # Convert cost estimates to cost bands if not already normalized
    for i, cost_est in enumerate(normalized_pricing.program_costs):
        # Calculate typical cost for band assignment
        typical_cost = cost_est.estimated_total_typical
        if not typical_cost and cost_est.estimated_total_min and cost_est.estimated_total_max:
            typical_cost = (cost_est.estimated_total_min + cost_est.estimated_total_max) / 2

        if typical_cost:
            current_band = cost_est.cost_band
            calculated_band = normalize_cost_to_band(typical_cost)

            if current_band != calculated_band:
                result.add_normalization(f"program_costs[{i}].cost_band",
                                       current_band, calculated_band,
                                       f"normalized from ${typical_cost} typical cost")
                normalized_pricing.program_costs[i].cost_band = calculated_band

    # Normalize value inclusions
    normalized_inclusions = []
    for inclusion in pricing.value_inclusions:
        normalized_inclusion = normalize_text_case(inclusion, "title")
        if normalized_inclusion != inclusion:
            result.add_normalization(f"value_inclusions[{pricing.value_inclusions.index(inclusion)}]",
                                   inclusion, normalized_inclusion, "title case")
        normalized_inclusions.append(normalized_inclusion)
    normalized_pricing.value_inclusions = normalized_inclusions

    return normalized_pricing, result


def normalize_flight_program(program: FlightProgram) -> tuple[FlightProgram, NormalizationResult]:
    """
    Normalize a FlightProgram object.

    Args:
        program: FlightProgram instance to normalize

    Returns:
        Tuple of (normalized_program, normalization_result)
    """
    result = NormalizationResult()
    normalized_program = program.copy(deep=True)

    # Normalize program name and description
    if program.details.name:
        normalized_name = clean_whitespace(program.details.name)
        if normalized_name != program.details.name:
            result.add_normalization("details.name", program.details.name, normalized_name, "whitespace cleanup")
            normalized_program.details.name = normalized_name

    if program.details.description:
        normalized_desc = clean_whitespace(program.details.description)
        if normalized_desc != program.details.description:
            result.add_normalization("details.description", program.details.description, normalized_desc, "whitespace cleanup")
            normalized_program.details.description = normalized_desc

    # Normalize aircraft types
    normalized_aircraft = []
    for aircraft in program.details.aircraft_types:
        # Standardize common aircraft type names
        normalized_aircraft_type = _normalize_aircraft_type(aircraft)
        if normalized_aircraft_type != aircraft:
            result.add_normalization(f"details.aircraft_types[{program.details.aircraft_types.index(aircraft)}]",
                                   aircraft, normalized_aircraft_type, "standardization")
        normalized_aircraft.append(normalized_aircraft_type)
    normalized_program.details.aircraft_types = normalized_aircraft

    return normalized_program, result


def normalize_all_data(
    school: FlightSchool,
    pricing: PricingInfo,
    programs: List[FlightProgram]
) -> tuple[FlightSchool, PricingInfo, List[FlightProgram], Dict[str, NormalizationResult]]:
    """
    Normalize all flight school data objects.

    Args:
        school: FlightSchool instance
        pricing: PricingInfo instance
        programs: List of FlightProgram instances

    Returns:
        Tuple of (normalized_school, normalized_pricing, normalized_programs, results_dict)
    """
    results = {}

    # Normalize individual objects
    normalized_school, school_result = normalize_flight_school(school)
    results['school'] = school_result

    normalized_pricing, pricing_result = normalize_pricing_info(pricing)
    results['pricing'] = pricing_result

    normalized_programs = []
    for i, program in enumerate(programs):
        normalized_program, program_result = normalize_flight_program(program)
        normalized_programs.append(normalized_program)
        results[f'program_{i}'] = program_result

    return normalized_school, normalized_pricing, normalized_programs, results


def apply_normalization_defaults(
    school: FlightSchool,
    pricing: PricingInfo,
    programs: List[FlightProgram],
    default_confidence: float = 0.95
) -> tuple[FlightSchool, PricingInfo, List[FlightProgram]]:
    """
    Apply default confidence scores to human-verified fields.

    Args:
        school: FlightSchool instance
        pricing: PricingInfo instance
        programs: List of FlightProgram instances
        default_confidence: Default confidence score for verified fields

    Returns:
        Updated instances with default confidence applied
    """
    # This function would be used when data has been manually verified
    # For now, it serves as a placeholder for future enhancement

    return school, pricing, programs


# Utility functions
def _normalize_aircraft_type(aircraft_type: str) -> str:
    """
    Normalize aircraft type names to standard formats.

    Args:
        aircraft_type: Raw aircraft type string

    Returns:
        Normalized aircraft type string
    """
    if not aircraft_type:
        return aircraft_type

    # Common normalization mappings
    normalization_map = {
        "cessna 172": "Cessna 172",
        "c172": "Cessna 172",
        "172": "Cessna 172",
        "piper cherokee": "Piper Cherokee",
        "cherokee": "Piper Cherokee",
        "pa-28": "Piper Cherokee",
        "cessna 152": "Cessna 152",
        "c152": "Cessna 152",
        "152": "Cessna 152",
        "diamond da40": "Diamond DA40",
        "da40": "Diamond DA40",
        "cirrus sr20": "Cirrus SR20",
        "sr20": "Cirrus SR20",
        "beechcraft bonanza": "Beechcraft Bonanza",
        "bonanza": "Beechcraft Bonanza",
        "piper arrow": "Piper Arrow",
        "arrow": "Piper Arrow",
        "cessna 182": "Cessna 182",
        "c182": "Cessna 182",
        "182": "Cessna 182"
    }

    # Clean and standardize
    cleaned = clean_whitespace(aircraft_type.lower())

    # Try exact match first
    if cleaned in normalization_map:
        return normalization_map[cleaned]

    # Try partial matches
    for key, value in normalization_map.items():
        if key in cleaned or cleaned in key:
            return value

    # Return title case if no match found
    return normalize_text_case(aircraft_type, "title")


def standardize_currency_values(value: Union[float, int], from_currency: str = "USD", to_currency: str = "USD") -> float:
    """
    Standardize currency values (placeholder for future multi-currency support).

    Args:
        value: Monetary value
        from_currency: Source currency code
        to_currency: Target currency code

    Returns:
        Standardized value in target currency
    """
    # For now, assume all values are in USD
    # Future enhancement: add currency conversion logic
    if from_currency != to_currency:
        logger.warning(f"Currency conversion not implemented: {from_currency} to {to_currency}")

    return float(value)


def normalize_time_units(hours: Optional[int] = None, weeks: Optional[int] = None) -> Dict[str, Any]:
    """
    Normalize time units and provide conversions.

    Args:
        hours: Hours value
        weeks: Weeks value

    Returns:
        Dictionary with normalized time values
    """
    result = {}

    if hours is not None:
        result['hours'] = hours
        result['weeks_equivalent'] = round(hours / 40, 1) if hours > 0 else 0  # Assuming 40 hours/week

    if weeks is not None:
        result['weeks'] = weeks
        result['hours_equivalent'] = weeks * 40  # Assuming 40 hours/week

    return result


def create_cost_summary(pricing: PricingInfo) -> Dict[str, Any]:
    """
    Create a summary of cost information for easy comparison.

    Args:
        pricing: PricingInfo instance

    Returns:
        Dictionary with cost summary information
    """
    summary = {
        'hourly_rates': {},
        'package_ranges': {},
        'cost_bands': set(),
        'estimated_ranges': {},
        'currency': pricing.currency
    }

    # Summarize hourly rates by aircraft category
    for rate in pricing.hourly_rates:
        category = rate.aircraft_category.value
        summary['hourly_rates'][category] = {
            'rate': rate.rate_per_hour,
            'includes_instructor': rate.includes_instructor,
            'includes_fuel': rate.includes_fuel
        }

    # Summarize package pricing ranges
    program_packages = {}
    for package in pricing.package_pricing:
        program = package.program_type
        if program not in program_packages:
            program_packages[program] = []
        program_packages[program].append(package.total_cost)

    for program, costs in program_packages.items():
        summary['package_ranges'][program] = {
            'min': min(costs),
            'max': max(costs),
            'count': len(costs)
        }

    # Collect cost bands
    for cost_est in pricing.program_costs:
        summary['cost_bands'].add(cost_est.cost_band)
        program = cost_est.program_type
        if program not in summary['estimated_ranges']:
            summary['estimated_ranges'][program] = []
        summary['estimated_ranges'][program].append({
            'band': cost_est.cost_band,
            'min': cost_est.estimated_total_min,
            'max': cost_est.estimated_total_max,
            'typical': cost_est.estimated_total_typical
        })

    summary['cost_bands'] = list(summary['cost_bands'])

    return summary