"""
Flight School Data Validation and Normalization Pipeline

This package provides comprehensive validation and normalization of flight school data,
including field validation, cross-schema consistency checks, and data standardization.
"""

from .validators import (
    ValidationResult,
    validate_flight_school,
    validate_pricing_info,
    validate_flight_program,
    validate_cross_schema_consistency,
    validate_all_data,
    apply_validation_updates
)

from .normalizer import (
    NormalizationResult,
    normalize_flight_school,
    normalize_pricing_info,
    normalize_flight_program,
    normalize_all_data,
    apply_normalization_defaults,
    create_cost_summary
)

__all__ = [
    # Validation classes and functions
    'ValidationResult',
    'validate_flight_school',
    'validate_pricing_info',
    'validate_flight_program',
    'validate_cross_schema_consistency',
    'validate_all_data',
    'apply_validation_updates',

    # Normalization classes and functions
    'NormalizationResult',
    'normalize_flight_school',
    'normalize_pricing_info',
    'normalize_flight_program',
    'normalize_all_data',
    'apply_normalization_defaults',
    'create_cost_summary'
]

__version__ = "1.0.0"