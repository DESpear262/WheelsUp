"""
Program Schema for Flight Training Courses

This module defines Pydantic models for flight training programs
such as Private Pilot License (PPL), Instrument Rating (IR), etc.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class ProgramType(str, Enum):
    """Standard flight training program types."""
    PPL = "Private Pilot License"
    IR = "Instrument Rating"
    CPL = "Commercial Pilot License"
    CFI = "Certified Flight Instructor"
    CFII = "Certified Flight Instructor - Instrument"
    MEI = "Multi-Engine Instructor"
    ATP = "Airline Transport Pilot"
    SPORT = "Sport Pilot"
    ROTORCRAFT = "Rotorcraft Helicopter"
    SEAPLANE = "Seaplane Rating"
    TAILWHEEL = "Tailwheel Endorsement"


class ProgramDuration(BaseModel):
    """Duration information for a training program."""
    hours_min: Optional[int] = Field(None, ge=1, description="Minimum training hours")
    hours_max: Optional[int] = Field(None, ge=1, description="Maximum training hours")
    hours_typical: Optional[int] = Field(None, ge=1, description="Typical training hours")
    weeks_min: Optional[int] = Field(None, ge=1, description="Minimum weeks to complete")
    weeks_max: Optional[int] = Field(None, ge=1, description="Maximum weeks to complete")
    weeks_typical: Optional[int] = Field(None, ge=1, description="Typical weeks to complete")

    @validator('hours_max')
    def validate_hours_max(cls, v, values):
        """Ensure hours_max is greater than or equal to hours_min."""
        if 'hours_min' in values and v is not None:
            min_val = values['hours_min']
            if min_val is not None and v < min_val:
                raise ValueError('Maximum hours must be >= minimum hours')
        return v

    @validator('weeks_max')
    def validate_weeks_max(cls, v, values):
        """Ensure weeks_max is greater than or equal to weeks_min."""
        if 'weeks_min' in values and v is not None:
            min_val = values['weeks_min']
            if min_val is not None and v < min_val:
                raise ValueError('Maximum weeks must be >= minimum weeks')
        return v


class ProgramRequirements(BaseModel):
    """Prerequisites and requirements for a program."""
    age_minimum: Optional[int] = Field(None, ge=14, le=100, description="Minimum age requirement")
    english_proficiency: Optional[bool] = Field(None, description="English language proficiency required")
    medical_certificate_class: Optional[str] = Field(None, description="Required medical certificate class (1st, 2nd, 3rd)")
    prior_certifications: List[str] = Field(default_factory=list, description="Required prior certifications")
    flight_experience_hours: Optional[int] = Field(None, ge=0, description="Required flight experience in hours")


class ProgramDetails(BaseModel):
    """Detailed information about a training program."""
    program_type: ProgramType = Field(..., description="Type of flight training program")
    name: str = Field(..., min_length=1, max_length=200, description="Program name")
    description: Optional[str] = Field(None, max_length=1000, description="Program description")

    # Duration and requirements
    duration: ProgramDuration = Field(default_factory=ProgramDuration, description="Program duration information")
    requirements: ProgramRequirements = Field(default_factory=ProgramRequirements, description="Program prerequisites")

    # Program specifics
    includes_ground_school: Optional[bool] = Field(None, description="Whether ground school is included")
    includes_checkride: Optional[bool] = Field(None, description="Whether practical test is included")
    aircraft_types: List[str] = Field(default_factory=list, description="Aircraft types used in training")

    # Program availability
    part_61_available: bool = Field(default=True, description="Available under Part 61")
    part_141_available: bool = Field(default=False, description="Available under Part 141")

    # Additional metadata
    is_popular: Optional[bool] = Field(None, description="Whether this is a popular program at the school")


class FlightProgram(BaseModel):
    """
    Flight training program offered by a flight school.

    Represents a specific training course with duration, requirements, and details.
    """
    program_id: str = Field(..., description="Unique identifier for the program")
    school_id: str = Field(..., description="ID of the flight school offering this program")

    # Program details
    details: ProgramDetails = Field(..., description="Detailed program information")

    # Operational info
    is_active: bool = Field(default=True, description="Whether program is currently offered")
    seasonal_availability: Optional[str] = Field(None, description="Seasonal availability notes")

    # Provenance tracking
    source_type: str = Field(..., description="Data source type")
    source_url: str = Field(..., description="Original source URL")
    extracted_at: datetime = Field(default_factory=datetime.utcnow, description="When data was extracted")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    extractor_version: str = Field(..., description="Version of extraction pipeline")
    snapshot_id: str = Field(..., description="ETL snapshot identifier")

    # Metadata
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Example data for testing
def get_example_program() -> FlightProgram:
    """Return an example FlightProgram instance for testing."""
    return FlightProgram(
        program_id="ppl_cert_001",
        school_id="example_flight_school_001",
        details=ProgramDetails(
            program_type=ProgramType.PPL,
            name="Private Pilot License (PPL)",
            description="Complete private pilot certification training including ground school and flight instruction.",
            duration=ProgramDuration(
                hours_min=35,
                hours_max=70,
                hours_typical=45,
                weeks_min=4,
                weeks_max=16,
                weeks_typical=8
            ),
            requirements=ProgramRequirements(
                age_minimum=16,
                english_proficiency=True,
                medical_certificate_class="3rd",
                flight_experience_hours=0
            ),
            includes_ground_school=True,
            includes_checkride=True,
            aircraft_types=["Cessna 172", "Piper Cherokee"],
            part_61_available=True,
            part_141_available=True,
            is_popular=True
        ),
        source_type="website",
        source_url="https://exampleaviation.com/programs/ppl",
        confidence=0.92,
        extractor_version="1.0.0",
        snapshot_id="2025Q1-MVP"
    )


if __name__ == "__main__":
    # Test the schema
    example = get_example_program()
    print("Program schema validation successful!")
    print(f"Program: {example.details.name}")
    print(f"Type: {example.details.program_type.value}")
    print(f"Typical Hours: {example.details.duration.hours_typical}")
    print(f"Confidence: {example.confidence}")
