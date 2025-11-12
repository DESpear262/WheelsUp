"""
Metrics Schema for Flight School Performance Data

This module defines Pydantic models for flight school performance metrics,
reliability data, and operational statistics. This is currently a placeholder
schema that can be expanded as more data sources become available.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class TrainingMetrics(BaseModel):
    """Metrics related to training completion and efficiency."""
    average_completion_months: Optional[float] = Field(None, gt=0, description="Average months to complete PPL")
    completion_rate_percent: Optional[float] = Field(None, ge=0, le=100, description="Percentage of students who complete training")
    pass_rate_first_attempt: Optional[float] = Field(None, ge=0, le=100, description="First-attempt pass rate for checkrides")

    # Training velocity (hours per month)
    average_hours_per_month: Optional[float] = Field(None, gt=0, description="Average flight hours completed per student per month")

    # Student progress metrics
    solo_rate_percent: Optional[float] = Field(None, ge=0, le=100, description="Percentage of students who solo")
    dropout_rate_percent: Optional[float] = Field(None, ge=0, le=100, description="Student dropout rate")


class OperationalMetrics(BaseModel):
    """Operational performance and reliability metrics."""
    cancellation_rate_percent: Optional[float] = Field(None, ge=0, le=100, description="Percentage of scheduled lessons cancelled")
    no_show_rate_percent: Optional[float] = Field(None, ge=0, le=100, description="Percentage of no-shows for scheduled lessons")
    aircraft_utilization_percent: Optional[float] = Field(None, ge=0, le=100, description="Aircraft fleet utilization rate")

    # Scheduling efficiency
    average_booking_lead_days: Optional[float] = Field(None, gt=0, description="Average days in advance lessons are booked")


class StudentExperienceMetrics(BaseModel):
    """Student satisfaction and experience metrics."""
    nps_score: Optional[float] = Field(None, ge=-100, le=100, description="Net Promoter Score")
    satisfaction_rating: Optional[float] = Field(None, ge=1, le=5, description="Average student satisfaction rating")

    # Retention and loyalty
    repeat_customer_rate: Optional[float] = Field(None, ge=0, le=100, description="Percentage of graduates who return for additional ratings")
    referral_rate_percent: Optional[float] = Field(None, ge=0, le=100, description="Student referral rate")


class AccreditationMetrics(BaseModel):
    """Accreditation and compliance metrics."""
    inspection_score: Optional[float] = Field(None, ge=0, le=100, description="Latest FAA inspection score")
    compliance_violations_count: Optional[int] = Field(None, ge=0, description="Number of compliance violations in last 3 years")
    safety_incident_count: Optional[int] = Field(None, ge=0, description="Number of safety incidents in last 5 years")


class FinancialMetrics(BaseModel):
    """Financial stability and value metrics."""
    years_in_operation: Optional[int] = Field(None, ge=0, description="Years school has been operating")

    # Value indicators (derived from pricing and reviews)
    value_score: Optional[float] = Field(None, ge=0, le=10, description="Composite value score (1-10)")

    # Financial health indicators
    fleet_age_average_years: Optional[float] = Field(None, gt=0, description="Average age of aircraft fleet")


class SchoolMetrics(BaseModel):
    """
    Comprehensive performance metrics for a flight school.

    This is currently a placeholder schema that aggregates various
    performance indicators. As more data sources become available,
    this can be expanded with additional metric categories.
    """
    school_id: str = Field(..., description="ID of the flight school")

    # Metric categories
    training: TrainingMetrics = Field(default_factory=TrainingMetrics, description="Training completion and efficiency metrics")
    operational: OperationalMetrics = Field(default_factory=OperationalMetrics, description="Operational performance metrics")
    experience: StudentExperienceMetrics = Field(default_factory=StudentExperienceMetrics, description="Student experience metrics")
    accreditation: AccreditationMetrics = Field(default_factory=AccreditationMetrics, description="Accreditation and compliance metrics")
    financial: FinancialMetrics = Field(default_factory=FinancialMetrics, description="Financial stability metrics")

    # Metadata about metrics collection
    metrics_last_updated: Optional[datetime] = Field(None, description="When metrics were last updated")
    data_sources: List[str] = Field(default_factory=list, description="Sources used for metrics calculation")
    sample_size: Optional[int] = Field(None, ge=0, description="Sample size for metrics (if applicable)")

    # Overall scores (computed or derived)
    overall_reliability_score: Optional[float] = Field(None, ge=0, le=10, description="Composite reliability score (0-10)")
    overall_quality_score: Optional[float] = Field(None, ge=0, le=10, description="Composite quality score (0-10)")

    # Provenance tracking
    source_type: str = Field(..., description="Data source type")
    source_url: str = Field(..., description="Original source URL")
    extracted_at: datetime = Field(default_factory=datetime.utcnow, description="When data was extracted")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    extractor_version: str = Field(..., description="Version of extraction pipeline")
    snapshot_id: str = Field(..., description="ETL snapshot identifier")

    # Metadata
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    is_current: bool = Field(default=True, description="Whether these metrics are current")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    @validator('overall_reliability_score', 'overall_quality_score')
    def validate_scores(cls, v):
        """Ensure overall scores are within valid range."""
        if v is not None and (v < 0 or v > 10):
            raise ValueError('Overall scores must be between 0 and 10')
        return v


# Example data for testing
def get_example_metrics() -> SchoolMetrics:
    """Return an example SchoolMetrics instance for testing."""
    return SchoolMetrics(
        school_id="example_flight_school_001",
        training=TrainingMetrics(
            average_completion_months=8.5,
            completion_rate_percent=85.0,
            pass_rate_first_attempt=78.0,
            average_hours_per_month=5.5,
            solo_rate_percent=95.0,
            dropout_rate_percent=12.0
        ),
        operational=OperationalMetrics(
            cancellation_rate_percent=8.0,
            no_show_rate_percent=5.0,
            aircraft_utilization_percent=75.0,
            average_booking_lead_days=14.0
        ),
        experience=StudentExperienceMetrics(
            nps_score=42.0,
            satisfaction_rating=4.6,
            repeat_customer_rate=35.0,
            referral_rate_percent=28.0
        ),
        accreditation=AccreditationMetrics(
            inspection_score=96.0,
            compliance_violations_count=0,
            safety_incident_count=0
        ),
        financial=FinancialMetrics(
            years_in_operation=18,
            value_score=8.2,
            fleet_age_average_years=4.5
        ),
        metrics_last_updated=datetime(2024, 11, 1),
        data_sources=["student_surveys", "faa_records", "operational_data"],
        sample_size=150,
        overall_reliability_score=8.5,
        overall_quality_score=8.7,
        source_type="aggregated",
        source_url="https://exampleaviation.com/metrics",
        confidence=0.75,  # Lower confidence since this is placeholder data
        extractor_version="1.0.0",
        snapshot_id="2025Q1-MVP"
    )


if __name__ == "__main__":
    # Test the schema
    example = get_example_metrics()
    print("Metrics schema validation successful!")
    print(f"Completion Rate: {example.training.completion_rate_percent}%")
    print(f"Overall Quality Score: {example.overall_quality_score}/10")
    print(f"Years in Operation: {example.financial.years_in_operation}")
    print(f"Confidence: {example.confidence}")
