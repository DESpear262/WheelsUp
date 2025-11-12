"""
Pricing Schema for Flight Training Costs

This module defines Pydantic models for flight school pricing information,
including hourly rates, package deals, and cost normalization.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
import re


class RateType(str, Enum):
    """Types of pricing structures."""
    HOURLY = "hourly"
    PACKAGE = "package"
    AIRCRAFT_TYPE = "aircraft_type"
    INSTRUCTOR_TYPE = "instructor_type"
    MEMBERSHIP = "membership"


class AircraftCategory(str, Enum):
    """FAA aircraft categories for pricing."""
    SINGLE_ENGINE_LAND = "single_engine_land"
    MULTI_ENGINE_LAND = "multi_engine_land"
    SINGLE_ENGINE_SEA = "single_engine_sea"
    MULTI_ENGINE_SEA = "multi_engine_sea"
    ROTORCRAFT = "rotorcraft"
    GLIDER = "glider"
    LIGHTER_THAN_AIR = "lighter_than_air"


class Currency(str, Enum):
    """Supported currencies."""
    USD = "USD"


class HourlyRate(BaseModel):
    """Hourly pricing for different aircraft categories."""
    aircraft_category: AircraftCategory = Field(..., description="Aircraft category")
    rate_per_hour: float = Field(..., gt=0, description="Rate per flight hour in USD")
    includes_instructor: bool = Field(default=True, description="Whether instructor is included")
    includes_fuel: Optional[bool] = Field(None, description="Whether fuel is included")

    # Time-based discounts
    block_hours_min: Optional[int] = Field(None, ge=1, description="Minimum block hours for rate")
    block_hours_max: Optional[int] = Field(None, ge=1, description="Maximum block hours for rate")


class PackagePricing(BaseModel):
    """Package deal pricing for programs."""
    program_type: str = Field(..., description="Type of program (PPL, IR, etc.)")
    package_name: str = Field(..., min_length=1, max_length=200, description="Name of the package")
    total_cost: float = Field(..., gt=0, description="Total package cost in USD")

    # Breakdown
    flight_hours_included: Optional[int] = Field(None, ge=0, description="Flight hours included")
    ground_hours_included: Optional[int] = Field(None, ge=0, description="Ground instruction hours included")
    includes_materials: bool = Field(default=False, description="Whether materials are included")

    # Duration and validity
    valid_for_months: Optional[int] = Field(None, ge=1, description="Package validity in months")
    completion_deadline_months: Optional[int] = Field(None, ge=1, description="Months to complete training")


class CostBand(str, Enum):
    """Normalized cost bands for program completion."""
    BUDGET = "budget"        # <$5,000
    ECONOMY = "$5k-$10k"     # $5,000-$10,000
    STANDARD = "$10k-$15k"   # $10,000-$15,000
    PREMIUM = "$15k-$25k"    # $15,000-$25,000
    LUXURY = "$25k+"         # $25,000+


class ProgramCostEstimate(BaseModel):
    """Normalized cost estimate for completing a program."""
    program_type: str = Field(..., description="Program type (PPL, IR, CPL, etc.)")
    cost_band: CostBand = Field(..., description="Normalized cost band")

    # Detailed breakdown
    estimated_total_min: Optional[float] = Field(None, ge=0, description="Minimum estimated total cost")
    estimated_total_max: Optional[float] = Field(None, ge=0, description="Maximum estimated total cost")
    estimated_total_typical: Optional[float] = Field(None, ge=0, description="Typical estimated total cost")

    # Cost components
    flight_cost_estimate: Optional[float] = Field(None, ge=0, description="Estimated flight costs")
    ground_cost_estimate: Optional[float] = Field(None, ge=0, description="Estimated ground instruction costs")
    materials_cost_estimate: Optional[float] = Field(None, ge=0, description="Estimated materials/books costs")
    exam_fees_estimate: Optional[float] = Field(None, ge=0, description="Estimated FAA exam/checkride fees")

    # Assumptions used for estimate
    assumptions: Dict[str, Any] = Field(default_factory=dict, description="Assumptions made in cost calculation")


class AdditionalFees(BaseModel):
    """Additional fees beyond base pricing."""
    checkride_fee: Optional[float] = Field(None, ge=0, description="Practical test (checkride) fee")
    medical_exam_fee: Optional[float] = Field(None, ge=0, description="Medical examination fee")
    knowledge_test_fee: Optional[float] = Field(None, ge=0, description="Written knowledge test fee")
    membership_fee: Optional[float] = Field(None, ge=0, description="Monthly/annual membership fee")

    # Surcharges
    multi_engine_surcharge: Optional[float] = Field(None, ge=0, description="Multi-engine training surcharge per hour")
    night_surcharge: Optional[float] = Field(None, ge=0, description="Night flight surcharge per hour")
    weekend_surcharge: Optional[float] = Field(None, ge=0, description="Weekend training surcharge per hour")

    # Deposits and payments
    enrollment_deposit: Optional[float] = Field(None, ge=0, description="Required enrollment deposit")
    payment_plans_available: Optional[bool] = Field(None, description="Whether payment plans are offered")


class PricingInfo(BaseModel):
    """Complete pricing information for a flight school."""
    school_id: str = Field(..., description="ID of the flight school")

    # Different pricing structures
    hourly_rates: List[HourlyRate] = Field(default_factory=list, description="Hourly rates by aircraft category")
    package_pricing: List[PackagePricing] = Field(default_factory=list, description="Package deals available")

    # Normalized cost estimates
    program_costs: List[ProgramCostEstimate] = Field(default_factory=list, description="Normalized program cost estimates")

    # Additional fees
    additional_fees: AdditionalFees = Field(default_factory=AdditionalFees, description="Additional fees and surcharges")

    # Pricing metadata
    currency: Currency = Field(default=Currency.USD, description="Pricing currency")
    price_last_updated: Optional[datetime] = Field(None, description="When pricing was last verified")

    # Value propositions
    value_inclusions: List[str] = Field(default_factory=list, description="What's included in pricing")
    scholarships_available: Optional[bool] = Field(None, description="Whether scholarships are offered")

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

    @validator('program_costs')
    def validate_program_costs(cls, v):
        """Ensure cost estimates have reasonable ranges."""
        for cost in v:
            if cost.estimated_total_min and cost.estimated_total_max:
                if cost.estimated_total_max < cost.estimated_total_min:
                    raise ValueError('Maximum cost cannot be less than minimum cost')
        return v


# Example data for testing
def get_example_pricing() -> PricingInfo:
    """Return an example PricingInfo instance for testing."""
    return PricingInfo(
        school_id="example_flight_school_001",
        hourly_rates=[
            HourlyRate(
                aircraft_category=AircraftCategory.SINGLE_ENGINE_LAND,
                rate_per_hour=185.0,
                includes_instructor=True,
                includes_fuel=False,
                block_hours_min=10,
                block_hours_max=50
            ),
            HourlyRate(
                aircraft_category=AircraftCategory.MULTI_ENGINE_LAND,
                rate_per_hour=275.0,
                includes_instructor=True,
                includes_fuel=False
            )
        ],
        package_pricing=[
            PackagePricing(
                program_type="PPL",
                package_name="Private Pilot Package",
                total_cost=8900.0,
                flight_hours_included=45,
                ground_hours_included=25,
                includes_materials=True,
                valid_for_months=12
            )
        ],
        program_costs=[
            ProgramCostEstimate(
                program_type="PPL",
                cost_band=CostBand.STANDARD,
                estimated_total_min=8000,
                estimated_total_max=12000,
                estimated_total_typical=9500,
                flight_cost_estimate=7500,
                ground_cost_estimate=1200,
                materials_cost_estimate=500,
                exam_fees_estimate=300,
                assumptions={
                    "hours_required": 45,
                    "hourly_rate": 185,
                    "location_factor": "moderate"
                }
            )
        ],
        additional_fees=AdditionalFees(
            checkride_fee=600,
            knowledge_test_fee=160,
            multi_engine_surcharge=90,
            enrollment_deposit=500,
            payment_plans_available=True
        ),
        value_inclusions=[
            "Ground school",
            "Flight instruction",
            "Aircraft rental",
            "FAA written exam",
            "Checkride preparation"
        ],
        scholarships_available=True,
        source_type="website",
        source_url="https://exampleaviation.com/pricing",
        confidence=0.88,
        extractor_version="1.0.0",
        snapshot_id="2025Q1-MVP"
    )


if __name__ == "__main__":
    # Test the schema
    example = get_example_pricing()
    print("Pricing schema validation successful!")
    print(f"Hourly Rate (SEL): ${example.hourly_rates[0].rate_per_hour}/hr")
    print(f"PPL Package: ${example.package_pricing[0].total_cost}")
    print(f"Cost Band: {example.program_costs[0].cost_band.value}")
    print(f"Confidence: {example.confidence}")
