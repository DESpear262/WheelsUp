"""
Attributes Schema for Semi-Structured Flight School Data

This module defines Pydantic models for semi-structured flight school attributes
that don't fit into the other normalized schemas. This includes amenities,
special programs, equipment details, and other flexible data.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator


class AmenityType(str, Enum):
    """Types of amenities offered by flight schools."""
    WIFI = "wifi"
    LOUNGE = "lounge"
    KITCHEN = "kitchen"
    PARKING = "parking"
    TRANSPORTATION = "transportation"
    ACCOMMODATION = "accommodation"
    GYM = "gym"
    STUDY_ROOM = "study_room"


class EquipmentType(str, Enum):
    """Types of equipment available."""
    SIMULATOR = "simulator"
    COMPUTER = "computer"
    HEADSET = "headset"
    IPAD = "ipad"
    EFB = "efb"  # Electronic Flight Bag
    CHART = "chart"


class ProgramType(str, Enum):
    """Special program types."""
    ACCELERATED = "accelerated"
    WEEKEND = "weekend"
    EVENING = "evening"
    MILITARY = "military"
    WOMEN_ONLY = "women_only"
    INTERNATIONAL = "international"


class Amenity(BaseModel):
    """Specific amenity offered by the school."""
    type: AmenityType = Field(..., description="Type of amenity")
    name: str = Field(..., min_length=1, max_length=100, description="Amenity name")
    description: Optional[str] = Field(None, max_length=500, description="Amenity description")
    available: bool = Field(default=True, description="Whether amenity is currently available")


class Equipment(BaseModel):
    """Equipment available for student use."""
    type: EquipmentType = Field(..., description="Type of equipment")
    name: str = Field(..., min_length=1, max_length=100, description="Equipment name")
    description: Optional[str] = Field(None, max_length=500, description="Equipment description")
    available: bool = Field(default=True, description="Whether equipment is available")
    quantity: Optional[int] = Field(None, ge=1, description="Quantity available")


class SpecialProgram(BaseModel):
    """Special training programs offered."""
    type: ProgramType = Field(..., description="Type of special program")
    name: str = Field(..., min_length=1, max_length=200, description="Program name")
    description: Optional[str] = Field(None, max_length=1000, description="Program description")
    active: bool = Field(default=True, description="Whether program is currently active")


class Certification(BaseModel):
    """Additional certifications or approvals."""
    name: str = Field(..., min_length=1, max_length=200, description="Certification name")
    issuer: str = Field(..., min_length=1, max_length=100, description="Issuing authority")
    issue_date: Optional[datetime] = Field(None, description="Date certification was issued")
    expiry_date: Optional[datetime] = Field(None, description="Date certification expires")
    is_active: bool = Field(default=True, description="Whether certification is current")


class Partnership(BaseModel):
    """Business partnerships and affiliations."""
    partner_name: str = Field(..., min_length=1, max_length=200, description="Partner organization name")
    partnership_type: str = Field(..., min_length=1, max_length=100, description="Type of partnership")
    description: Optional[str] = Field(None, max_length=500, description="Partnership description")
    active: bool = Field(default=True, description="Whether partnership is active")


class Award(BaseModel):
    """Awards and recognitions received."""
    name: str = Field(..., min_length=1, max_length=200, description="Award name")
    issuer: str = Field(..., min_length=1, max_length=100, description="Awarding organization")
    year: int = Field(..., ge=1900, le=datetime.now().year, description="Year award was received")
    description: Optional[str] = Field(None, max_length=500, description="Award description")


class SchoolAttributes(BaseModel):
    """
    Semi-structured attributes for a flight school.

    This schema captures flexible, unstructured data that doesn't fit into
    the normalized schemas. All fields are optional and can be extended.
    """
    school_id: str = Field(..., description="ID of the flight school")

    # Facilities and amenities
    amenities: List[Amenity] = Field(default_factory=list, description="Amenities offered by the school")
    equipment: List[Equipment] = Field(default_factory=list, description="Equipment available for students")

    # Programs and offerings
    special_programs: List[SpecialProgram] = Field(default_factory=list, description="Special training programs")
    certifications: List[Certification] = Field(default_factory=list, description="Additional certifications")

    # Business relationships
    partnerships: List[Partnership] = Field(default_factory=list, description="Business partnerships")
    awards: List[Award] = Field(default_factory=list, description="Awards and recognitions")

    # Flexible custom attributes (JSONB-like)
    custom_attributes: Dict[str, Any] = Field(default_factory=dict, description="Custom key-value attributes")

    # Social media and online presence
    social_media: Dict[str, str] = Field(default_factory=dict, description="Social media handles (platform: handle)")
    online_presence: Dict[str, Any] = Field(default_factory=dict, description="Online presence metrics")

    # Operational notes
    operational_notes: List[str] = Field(default_factory=list, description="Operational notes and observations")

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
def get_example_attributes() -> SchoolAttributes:
    """Return an example SchoolAttributes instance for testing."""
    return SchoolAttributes(
        school_id="example_flight_school_001",
        amenities=[
            Amenity(
                type=AmenityType.WIFI,
                name="High-Speed WiFi",
                description="Complimentary high-speed internet throughout the facility",
                available=True
            ),
            Amenity(
                type=AmenityType.LOUNGE,
                name="Student Lounge",
                description="Comfortable lounge area with refreshments",
                available=True
            ),
            Amenity(
                type=AmenityType.PARKING,
                name="Free Parking",
                description="Ample free parking for students",
                available=True
            )
        ],
        equipment=[
            Equipment(
                type=EquipmentType.SIMULATOR,
                name="Redbird FMX Simulator",
                description="Full-motion flight simulator for instrument training",
                available=True,
                quantity=1
            ),
            Equipment(
                type=EquipmentType.COMPUTER,
                name="Training Computers",
                description="Dedicated computers for ground school and flight planning",
                available=True,
                quantity=8
            )
        ],
        special_programs=[
            SpecialProgram(
                type=ProgramType.ACCELERATED,
                name="Accelerated Private Pilot Program",
                description="Intensive 4-week program for accelerated PPL completion",
                active=True
            ),
            SpecialProgram(
                type=ProgramType.WEEKEND,
                name="Weekend Warrior Program",
                description="Training available on weekends for working professionals",
                active=True
            )
        ],
        certifications=[
            Certification(
                name="Argus Platinum Rated",
                issuer=" Aviation Consumer Protection",
                issue_date=datetime(2023, 6, 15),
                is_active=True
            )
        ],
        partnerships=[
            Partnership(
                partner_name="FlightSafety International",
                partnership_type="Training Partnership",
                description="Collaborative training programs and resource sharing",
                active=True
            )
        ],
        awards=[
            Award(
                name="Flight School of the Year",
                issuer="AOPA Flight Training Magazine",
                year=2023,
                description="Recognized for excellence in flight training"
            )
        ],
        custom_attributes={
            "training_philosophy": "Safety first, excellence always",
            "instructor_student_ratio": "1:3",
            "weather_cancellation_policy": "Make-up flights provided",
            "uniform_required": False,
            "medical_kit_provided": True
        },
        social_media={
            "facebook": "@ExampleAviation",
            "instagram": "@exampleaviation",
            "linkedin": "company/example-aviation"
        },
        online_presence={
            "website_rating": 4.8,
            "review_platforms": ["Google", "Yelp", "AOPA"],
            "blog_active": True
        },
        operational_notes=[
            "Excellent maintenance facilities on-site",
            "Strong emphasis on student safety briefings",
            "Flexible scheduling accommodates various student needs"
        ],
        source_type="website",
        source_url="https://exampleaviation.com/about",
        confidence=0.82,
        extractor_version="1.0.0",
        snapshot_id="2025Q1-MVP"
    )


if __name__ == "__main__":
    # Test the schema
    example = get_example_attributes()
    print("Attributes schema validation successful!")
    print(f"Amenities: {len(example.amenities)} available")
    print(f"Equipment: {len(example.equipment)} types")
    print(f"Special Programs: {len(example.special_programs)}")
    print(f"Confidence: {example.confidence}")
