"""
Validation Rules for Flight School Data

This module contains reusable validation functions for flight training data,
including outlier detection, range validation, and business logic checks.
"""

from typing import Optional, Tuple, List
import re
from datetime import datetime, timedelta


# Cost and pricing validation
def validate_hourly_rate(rate: float, aircraft_type: str = "single_engine") -> Tuple[bool, str]:
    """
    Validate hourly rates are within reasonable market ranges.

    Args:
        rate: Hourly rate in USD
        aircraft_type: Type of aircraft for context

    Returns:
        Tuple of (is_valid, error_message)
    """
    if rate <= 0:
        return False, "Hourly rate must be positive"

    # Market rate ranges (approximate US averages)
    rate_ranges = {
        "single_engine": (75, 350),
        "multi_engine": (150, 600),
        "rotorcraft": (200, 800),
        "seaplane": (150, 500),
        "default": (50, 1000)  # Fallback range
    }

    min_rate, max_rate = rate_ranges.get(aircraft_type, rate_ranges["default"])

    if rate < min_rate * 0.5:  # Allow some flexibility below minimum
        return False, f"Hourly rate ${rate} seems unusually low (market range: ${min_rate}-${max_rate})"
    if rate > max_rate * 2:  # Allow some flexibility above maximum
        return False, f"Hourly rate ${rate} seems unusually high (market range: ${min_rate}-${max_rate})"

    return True, ""


def validate_total_cost(cost: float, program_type: str = "general") -> Tuple[bool, str]:
    """
    Validate total program costs are within reasonable ranges.

    Args:
        cost: Total cost in USD
        program_type: Type of program for context

    Returns:
        Tuple of (is_valid, error_message)
    """
    if cost <= 0:
        return False, "Total cost must be positive"

    # Program cost ranges (approximate US market)
    cost_ranges = {
        "sport": (3000, 8000),
        "private_pilot": (5000, 15000),
        "instrument": (8000, 25000),
        "commercial": (25000, 50000),
        "cfi": (15000, 35000),
        "default": (1000, 100000)
    }

    min_cost, max_cost = cost_ranges.get(program_type.lower().replace(" ", "_"), cost_ranges["default"])

    if cost < min_cost * 0.3:  # Allow flexibility
        return False, f"Total cost ${cost} seems unusually low for {program_type}"
    if cost > max_cost * 3:  # Allow flexibility
        return False, f"Total cost ${cost} seems unusually high for {program_type}"

    return True, ""


def normalize_cost_to_band(cost: float) -> str:
    """
    Normalize a cost amount to a cost band category.

    Args:
        cost: Cost in USD

    Returns:
        Cost band string
    """
    if cost < 5000:
        return "budget"
    elif cost < 10000:
        return "$5k-$10k"
    elif cost < 15000:
        return "$10k-$15k"
    elif cost < 25000:
        return "$15k-$25k"
    else:
        return "$25k+"


# Duration and time validation
def validate_training_hours(hours: int, program_type: str = "private_pilot") -> Tuple[bool, str]:
    """
    Validate training hours are reasonable for the program type.

    Args:
        hours: Total training hours
        program_type: Type of program

    Returns:
        Tuple of (is_valid, error_message)
    """
    if hours <= 0:
        return False, "Training hours must be positive"

    # FAA minimum requirements with reasonable maximums
    hour_ranges = {
        "sport": (20, 100),
        "private_pilot": (35, 100),
        "instrument": (35, 80),
        "commercial": (150, 300),
        "cfi": (100, 200),
        "atp": (1200, 2000),
        "default": (1, 5000)
    }

    min_hours, max_hours = hour_ranges.get(program_type.lower().replace(" ", "_"), hour_ranges["default"])

    if hours < min_hours * 0.5:  # Allow some flexibility
        return False, f"Training hours {hours} seem too low for {program_type} (FAA minimum: {min_hours})"
    if hours > max_hours * 2:  # Allow flexibility
        return False, f"Training hours {hours} seem unusually high for {program_type}"

    return True, ""


def validate_training_weeks(weeks: int, program_type: str = "private_pilot") -> Tuple[bool, str]:
    """
    Validate training duration in weeks is reasonable.

    Args:
        weeks: Training duration in weeks
        program_type: Type of program

    Returns:
        Tuple of (is_valid, error_message)
    """
    if weeks <= 0:
        return False, "Training weeks must be positive"

    # Reasonable duration ranges
    week_ranges = {
        "sport": (2, 24),
        "private_pilot": (4, 52),
        "instrument": (4, 24),
        "commercial": (12, 104),
        "cfi": (8, 52),
        "default": (1, 208)  # Up to 4 years
    }

    min_weeks, max_weeks = week_ranges.get(program_type.lower().replace(" ", "_"), week_ranges["default"])

    if weeks < min_weeks * 0.5:
        return False, f"Training duration {weeks} weeks seems unusually short for {program_type}"
    if weeks > max_weeks * 2:
        return False, f"Training duration {weeks} weeks seems unusually long for {program_type}"

    return True, ""


# Fleet and operational validation
def validate_fleet_size(fleet_size: int) -> Tuple[bool, str]:
    """
    Validate fleet size is reasonable for a flight school.

    Args:
        fleet_size: Number of aircraft

    Returns:
        Tuple of (is_valid, error_message)
    """
    if fleet_size < 0:
        return False, "Fleet size cannot be negative"
    if fleet_size == 0:
        return False, "Flight school must have at least 1 aircraft"
    if fleet_size > 500:
        return False, f"Fleet size {fleet_size} seems unusually large for a flight school"

    return True, ""


def validate_employee_count(employee_count: int) -> Tuple[bool, str]:
    """
    Validate employee count is reasonable for a flight school.

    Args:
        employee_count: Number of employees

    Returns:
        Tuple of (is_valid, error_message)
    """
    if employee_count < 1:
        return False, "Flight school must have at least 1 employee"
    if employee_count > 1000:
        return False, f"Employee count {employee_count} seems unusually large for a flight school"

    return True, ""


# Geographic and contact validation
def validate_coordinates(lat: float, lon: float) -> Tuple[bool, str]:
    """
    Validate latitude and longitude are within valid ranges.

    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not (-90 <= lat <= 90):
        return False, f"Latitude {lat} is outside valid range (-90 to 90)"
    if not (-180 <= lon <= 180):
        return False, f"Longitude {lon} is outside valid range (-180 to 180)"

    return True, ""


def validate_airport_distance(distance_miles: float) -> Tuple[bool, str]:
    """
    Validate distance to nearest airport is reasonable.

    Args:
        distance_miles: Distance in miles

    Returns:
        Tuple of (is_valid, error_message)
    """
    if distance_miles < 0:
        return False, "Distance cannot be negative"
    if distance_miles > 200:
        return False, f"Distance to airport {distance_miles} miles seems unusually far"

    return True, ""


def validate_phone_number(phone: str) -> Tuple[bool, str]:
    """
    Validate phone number format.

    Args:
        phone: Phone number string

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not phone or not phone.strip():
        return False, "Phone number cannot be empty"

    # Remove all non-digit characters for length check
    digits_only = re.sub(r'\D', '', phone)

    if len(digits_only) < 10:
        return False, "Phone number must have at least 10 digits"
    if len(digits_only) > 15:
        return False, "Phone number seems too long"

    # More permissive format check - just ensure it has some digits and common phone characters
    if not re.match(r'^[\+]?[\d\s\-\(\)\.]{10,}$', phone):
        return False, "Phone number format appears invalid"

    return True, ""


def validate_email_domain(email: str) -> Tuple[bool, str]:
    """
    Validate email domain looks legitimate.

    Args:
        email: Email address

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email or '@' not in email:
        return False, "Invalid email format"

    local, domain = email.rsplit('@', 1)

    # Check for suspicious patterns
    suspicious_domains = ['10minutemail', 'guerrillamail', 'mailinator', 'temp-mail']
    if any(susp in domain.lower() for susp in suspicious_domains):
        return False, "Email domain appears to be temporary/disposable"

    # Check domain has valid structure
    if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$', domain):
        return False, "Email domain format appears invalid"

    return True, ""


def validate_url_format(url: str) -> Tuple[bool, str]:
    """
    Validate URL format and scheme.

    Args:
        url: URL string

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url:
        return False, "URL cannot be empty"

    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    # Basic URL validation
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)  # path

    if not url_pattern.match(url):
        return False, "URL format appears invalid"

    return True, ""


# Business logic validation
def validate_cost_consistency(hourly_rate: float, total_cost: float, hours: int) -> Tuple[bool, str]:
    """
    Check if hourly rate, total cost, and hours are mathematically consistent.

    Args:
        hourly_rate: Hourly rate in USD
        total_cost: Total cost in USD
        hours: Number of hours

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not all([hourly_rate > 0, total_cost > 0, hours > 0]):
        return True, ""  # Skip validation if any value is missing/invalid

    expected_cost = hourly_rate * hours
    variance = abs(total_cost - expected_cost) / expected_cost

    # Allow 50% variance (packages often include extras)
    if variance > 0.5:
        return False, f"Cost inconsistency detected: expected ~${expected_cost} based on ${hourly_rate}/hr × {hours}hrs, but total is ${total_cost}"

    return True, ""


def validate_duration_consistency(hours: int, weeks: int, weekly_hours: int = 5) -> Tuple[bool, str]:
    """
    Check if training hours and weeks are durationally consistent.

    Args:
        hours: Total training hours
        weeks: Training duration in weeks
        weekly_hours: Expected hours per week

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not all([hours > 0, weeks > 0]):
        return True, ""  # Skip validation if values missing

    expected_hours = weeks * weekly_hours
    variance = abs(hours - expected_hours) / expected_hours

    # Allow 100% variance (training schedules vary widely)
    if variance > 1.0:
        return False, f"Duration inconsistency: expected ~{expected_hours} hours over {weeks} weeks, but total hours is {hours}"

    return True, ""


# Confidence scoring utilities
def calculate_field_confidence(base_confidence: float, validation_passed: bool, is_human_verified: bool = False) -> float:
    """
    Calculate adjusted confidence score based on validation results.

    Args:
        base_confidence: Original confidence score (0-1)
        validation_passed: Whether field passed validation
        is_human_verified: Whether field was manually verified

    Returns:
        Adjusted confidence score (0-1)
    """
    if is_human_verified:
        return min(0.95, base_confidence * 1.2)  # Boost confidence for verified fields

    if not validation_passed:
        return max(0.1, base_confidence * 0.5)  # Reduce confidence for failed validation

    return base_confidence


def detect_outliers(values: List[float], method: str = "iqr", threshold: float = 1.5) -> List[int]:
    """
    Detect outlier indices in a list of numeric values.

    Args:
        values: List of numeric values
        method: Outlier detection method ("iqr" or "zscore")
        threshold: Threshold for outlier detection

    Returns:
        List of indices that are outliers
    """
    if len(values) < 4:
        return []  # Need minimum data for outlier detection

    if method == "iqr":
        # Interquartile range method
        sorted_values = sorted(values)
        q1 = sorted_values[len(sorted_values) // 4]
        q3 = sorted_values[3 * len(sorted_values) // 4]
        iqr = q3 - q1
        lower_bound = q1 - threshold * iqr
        upper_bound = q3 + threshold * iqr

        outliers = [i for i, v in enumerate(values) if v < lower_bound or v > upper_bound]

    elif method == "zscore":
        # Z-score method
        mean_val = sum(values) / len(values)
        std_val = (sum((v - mean_val) ** 2 for v in values) / len(values)) ** 0.5
        if std_val == 0:
            return []  # No variance

        outliers = [i for i, v in enumerate(values) if abs((v - mean_val) / std_val) > threshold]

    else:
        raise ValueError(f"Unknown outlier detection method: {method}")

    return outliers


# Utility functions
def clean_whitespace(text: str) -> str:
    """
    Clean and normalize whitespace in text.

    Args:
        text: Input text

    Returns:
        Cleaned text
    """
    if not text:
        return text

    # Replace multiple whitespace with single space
    cleaned = re.sub(r'\s+', ' ', text.strip())
    return cleaned


def normalize_text_case(text: str, case_type: str = "title") -> str:
    """
    Normalize text case.

    Args:
        text: Input text
        case_type: Type of case normalization ("title", "upper", "lower")

    Returns:
        Normalized text
    """
    if not text:
        return text

    if case_type == "title":
        return text.title()
    elif case_type == "upper":
        return text.upper()
    elif case_type == "lower":
        return text.lower()
    else:
        return text


def validate_date_range(start_date: datetime, end_date: datetime, max_days: int = 365*10) -> Tuple[bool, str]:
    """
    Validate date range is reasonable.

    Args:
        start_date: Start date
        end_date: End date
        max_days: Maximum allowed days between dates

    Returns:
        Tuple of (is_valid, error_message)
    """
    if end_date < start_date:
        return False, "End date cannot be before start date"

    days_diff = (end_date - start_date).days
    if days_diff > max_days:
        return False, f"Date range of {days_diff} days seems unusually long (max allowed: {max_days})"

    return True, ""