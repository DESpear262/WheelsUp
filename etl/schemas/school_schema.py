"""
Flight School Data Schemas for ETL Pipeline

This module defines Pydantic models for validating and normalizing
flight school data extracted via LLM processing.

All models include provenance tracking for auditability and confidence scoring.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator, constr
import re


class AccreditationType(str, Enum):
    """FAA accreditation types for flight schools."""
    PART_61 = "Part 61"
    PART_141 = "Part 141"
    PART_142 = "Part 142"  # Specialized training


class ContactInfo(BaseModel):
    """Contact information for a flight school."""
    phone: Optional[constr(min_length=10, max_length=20)] = Field(None, description="Primary phone number")
    email: Optional[str] = Field(None, description="Primary email address")
    website: Optional[str] = Field(None, description="Official website URL")

    @validator('email')
    def validate_email(cls, v):
        if v and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v

    @validator('website')
    def validate_website(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            v = f'https://{v}'
        return v


class LocationInfo(BaseModel):
    """Geographic location information for a flight school."""
    address: Optional[str] = Field(None, description="Full street address")
    city: Optional[str] = Field(None, description="City name")
    state: Optional[str] = Field(None, description="State or province")
    zip_code: Optional[str] = Field(None, description="Postal code")
    country: str = Field(default="United States", description="Country name")

    # Geographic coordinates
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude in decimal degrees")

    # Airport information
    nearest_airport_icao: Optional[str] = Field(None, description="Nearest airport ICAO code")
    nearest_airport_name: Optional[str] = Field(None, description="Nearest airport name")
    airport_distance_miles: Optional[float] = Field(None, gt=0, description="Distance to nearest airport in miles")


class AccreditationInfo(BaseModel):
    """FAA accreditation and certification details."""
    type: Optional[AccreditationType] = Field(None, description="FAA accreditation type")
    certificate_number: Optional[str] = Field(None, description="FAA certificate number")
    inspection_date: Optional[datetime] = Field(None, description="Last FAA inspection date")
    va_approved: Optional[bool] = Field(None, description="VA-approved for GI Bill benefits")


class OperationalInfo(BaseModel):
    """Operational and business information."""
    founded_year: Optional[int] = Field(None, ge=1900, le=datetime.now().year, description="Year school was founded")
    employee_count: Optional[int] = Field(None, ge=1, description="Number of employees")
    fleet_size: Optional[int] = Field(None, ge=0, description="Number of aircraft in fleet")
    student_capacity: Optional[int] = Field(None, ge=1, description="Maximum concurrent student enrollment")


class FlightSchool(BaseModel):
    """
    Core flight school entity with comprehensive information.

    This model represents a single flight school with all extracted and normalized data.
    Includes full provenance tracking for auditability.
    """
    # Core identifiers
    school_id: str = Field(..., description="Unique identifier for the school")
    name: str = Field(..., min_length=1, max_length=200, description="Official school name")

    # Descriptive information
    description: Optional[str] = Field(None, max_length=2000, description="School description or mission statement")
    specialties: List[str] = Field(default_factory=list, description="Special training programs or focuses")

    # Contact and location
    contact: ContactInfo = Field(default_factory=ContactInfo, description="Contact information")
    location: LocationInfo = Field(default_factory=LocationInfo, description="Location and geographic data")

    # Accreditation and operations
    accreditation: AccreditationInfo = Field(default_factory=AccreditationInfo, description="FAA accreditation details")
    operations: OperationalInfo = Field(default_factory=OperationalInfo, description="Operational information")

    # External references and ratings
    google_rating: Optional[float] = Field(None, ge=1.0, le=5.0, description="Google Places rating")
    google_review_count: Optional[int] = Field(None, ge=0, description="Number of Google reviews")
    yelp_rating: Optional[float] = Field(None, ge=1.0, le=5.0, description="Yelp rating")

    # Provenance tracking (required for all fields)
    source_type: str = Field(..., description="Data source type (website, directory, reddit, manual)")
    source_url: str = Field(..., description="Original source URL")
    extracted_at: datetime = Field(default_factory=datetime.utcnow, description="When data was extracted")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score (0-1)")
    extractor_version: str = Field(..., description="Version of extraction pipeline")
    snapshot_id: str = Field(..., description="ETL snapshot identifier")

    # Additional metadata
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last time this record was updated")
    is_active: bool = Field(default=True, description="Whether school is currently operational")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    @validator('school_id')
    def validate_school_id(cls, v):
        """Ensure school_id follows expected format."""
        if not re.match(r'^[a-zA-Z0-9_-]{8,50}$', v):
            raise ValueError('school_id must be 8-50 alphanumeric characters with dashes/underscores')
        return v


# Example data for testing and validation
def get_example_school() -> FlightSchool:
    """Return an example FlightSchool instance for testing."""
    return FlightSchool(
        school_id="example_flight_school_001",
        name="Example Aviation Academy",
        description="Premier flight training academy specializing in private pilot certification.",
        specialties=["Private Pilot License", "Instrument Rating", "Commercial Pilot"],
        contact=ContactInfo(
            phone="(555) 123-4567",
            email="info@exampleaviation.com",
            website="https://exampleaviation.com"
        ),
        location=LocationInfo(
            address="123 Aviation Way",
            city="Springfield",
            state="IL",
            zip_code="62701",
            latitude=39.7817,
            longitude=-89.6501,
            nearest_airport_icao="KSPI",
            nearest_airport_name="Abraham Lincoln Capital Airport",
            airport_distance_miles=5.2
        ),
        accreditation=AccreditationInfo(
            type=AccreditationType.PART_141,
            certificate_number="ABC12345",
            va_approved=True
        ),
        operations=OperationalInfo(
            founded_year=1995,
            employee_count=25,
            fleet_size=12,
            student_capacity=40
        ),
        google_rating=4.8,
        google_review_count=127,
        source_type="website",
        source_url="https://exampleaviation.com",
        confidence=0.95,
        extractor_version="1.0.0",
        snapshot_id="2025Q1-MVP"
    )


if __name__ == "__main__":
    # Test the schema with example data
    example = get_example_school()
    print("School schema validation successful!")
    print(f"School: {example.name}")
    print(f"Location: {example.location.city}, {example.location.state}")
    print(f"Confidence: {example.confidence}")
    print(f"VA Approved: {example.accreditation.va_approved}")
