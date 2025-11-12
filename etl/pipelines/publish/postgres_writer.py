# PostgreSQL Data Writer for Flight School ETL Pipeline
#
# This module handles loading validated flight school data into PostgreSQL
# using Drizzle ORM schema with upsert logic for conflict resolution.

import logging
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import yaml

# Database imports (optional)
try:
    import psycopg2
    from psycopg2.extras import execute_values
    import psycopg2.pool
    HAS_PSYCOPG2 = True
except ImportError:
    # Create mock objects to avoid import errors
    class MockPsycopg2:
        def __init__(self):
            self.pool = None
    psycopg2 = MockPsycopg2()
    execute_values = None
    HAS_PSYCOPG2 = False

# Schema imports
from schemas.school_schema import FlightSchool
from schemas.program_schema import FlightProgram
from schemas.pricing_schema import PricingInfo

logger = logging.getLogger(__name__)


class PostgresWriter:
    """
    Handles writing flight school data to PostgreSQL with upsert logic.

    Supports schools, programs, and pricing tables with conflict resolution
    based on unique identifiers and confidence scores.
    """

    def __init__(self, config_file: str = "configs/db_config.yaml"):
        """
        Initialize the PostgreSQL writer.

        Args:
            config_file: Path to database configuration file
        """
        if not HAS_PSYCOPG2:
            raise ImportError("psycopg2 is required for PostgreSQL operations. Install with: pip install psycopg2-binary")

        self.config_file = Path(__file__).parent.parent.parent / config_file
        self.config = self._load_config()
        self.pool = None
        self._initialize_connection_pool()

        logger.info("PostgreSQL writer initialized")

    def _load_config(self) -> Dict[str, Any]:
        """Load database configuration from YAML file."""
        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
            return config.get('postgresql', {})
        except Exception as e:
            logger.error(f"Failed to load database config: {e}")
            raise

    def _initialize_connection_pool(self):
        """Initialize PostgreSQL connection pool."""
        try:
            self.pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=self.config.get('pool_size', 10),
                host=self.config.get('host'),
                port=self.config.get('port'),
                database=self.config.get('database'),
                user=self.config.get('username'),
                password=self.config.get('password'),
                sslmode=self.config.get('ssl_mode', 'disable')
            )
            logger.info("PostgreSQL connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise

    def get_connection(self):
        """Get a connection from the pool."""
        if not self.pool:
            raise RuntimeError("Connection pool not initialized")
        return self.pool.getconn()

    def release_connection(self, conn):
        """Release a connection back to the pool."""
        if self.pool:
            self.pool.putconn(conn)

    def upsert_schools(self, schools: List[FlightSchool], snapshot_id: str) -> Dict[str, Any]:
        """
        Upsert flight schools into the database.

        Args:
            schools: List of validated FlightSchool objects
            snapshot_id: Snapshot identifier for provenance tracking

        Returns:
            Dictionary with operation results and statistics
        """
        results = {
            'total_processed': len(schools),
            'inserted': 0,
            'updated': 0,
            'errors': 0,
            'error_details': []
        }

        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            for school in schools:
                try:
                    school_data = self._map_school_to_db(school, snapshot_id)
                    result = self._upsert_school_record(cursor, school_data)
                    results[result] += 1
                except Exception as e:
                    results['errors'] += 1
                    results['error_details'].append({
                        'school_id': getattr(school, 'school_id', 'unknown'),
                        'error': str(e)
                    })
                    logger.error(f"Error upserting school {getattr(school, 'school_id', 'unknown')}: {e}")

            conn.commit()
            logger.info(f"Schools upsert complete: {results}")

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Schools upsert failed: {e}")
            raise
        finally:
            if conn:
                self.release_connection(conn)

        return results

    def upsert_programs(self, programs: List[FlightProgram], snapshot_id: str) -> Dict[str, Any]:
        """
        Upsert flight programs into the database.

        Args:
            programs: List of validated FlightProgram objects
            snapshot_id: Snapshot identifier for provenance tracking

        Returns:
            Dictionary with operation results and statistics
        """
        results = {
            'total_processed': len(programs),
            'inserted': 0,
            'updated': 0,
            'errors': 0,
            'error_details': []
        }

        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            for program in programs:
                try:
                    program_data = self._map_program_to_db(program, snapshot_id)
                    result = self._upsert_program_record(cursor, program_data)
                    results[result] += 1
                except Exception as e:
                    results['errors'] += 1
                    results['error_details'].append({
                        'program_id': getattr(program, 'program_id', 'unknown'),
                        'error': str(e)
                    })
                    logger.error(f"Error upserting program {getattr(program, 'program_id', 'unknown')}: {e}")

            conn.commit()
            logger.info(f"Programs upsert complete: {results}")

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Programs upsert failed: {e}")
            raise
        finally:
            if conn:
                self.release_connection(conn)

        return results

    def upsert_pricing(self, pricing_records: List[PricingInfo], snapshot_id: str) -> Dict[str, Any]:
        """
        Upsert pricing information into the database.

        Args:
            pricing_records: List of validated PricingInfo objects
            snapshot_id: Snapshot identifier for provenance tracking

        Returns:
            Dictionary with operation results and statistics
        """
        results = {
            'total_processed': len(pricing_records),
            'inserted': 0,
            'updated': 0,
            'errors': 0,
            'error_details': []
        }

        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            for pricing in pricing_records:
                try:
                    pricing_data = self._map_pricing_to_db(pricing, snapshot_id)
                    result = self._upsert_pricing_record(cursor, pricing_data)
                    results[result] += 1
                except Exception as e:
                    results['errors'] += 1
                    results['error_details'].append({
                        'school_id': getattr(pricing, 'school_id', 'unknown'),
                        'error': str(e)
                    })
                    logger.error(f"Error upserting pricing for school {getattr(pricing, 'school_id', 'unknown')}: {e}")

            conn.commit()
            logger.info(f"Pricing upsert complete: {results}")

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Pricing upsert failed: {e}")
            raise
        finally:
            if conn:
                self.release_connection(conn)

        return results

    def _map_school_to_db(self, school: FlightSchool, snapshot_id: str) -> Dict[str, Any]:
        """Map FlightSchool object to database schema format."""
        return {
            'school_id': school.school_id,
            'name': school.name,
            'description': school.description,
            'specialties': school.specialties or [],
            'contact': {
                'phone': school.contact.phone,
                'email': school.contact.email,
                'website': school.contact.website,
            } if school.contact else {},
            'location': {
                'address': school.location.address,
                'city': school.location.city,
                'state': school.location.state,
                'zipCode': school.location.zip_code,
                'country': school.location.country,
                'latitude': getattr(school.location, 'latitude', None),
                'longitude': getattr(school.location, 'longitude', None),
                'nearestAirportIcao': getattr(school.location, 'nearest_airport_icao', None),
                'nearestAirportName': getattr(school.location, 'nearest_airport_name', None),
                'airportDistanceMiles': getattr(school.location, 'airport_distance_miles', None),
            } if school.location else {},
            'accreditation': {
                'type': school.accreditation.type.value if school.accreditation and school.accreditation.type else None,
                'certificateNumber': school.accreditation.certificate_number if school.accreditation else None,
                'inspectionDate': school.accreditation.inspection_date.isoformat() if school.accreditation and school.accreditation.inspection_date else None,
                'vaApproved': school.accreditation.va_approved if school.accreditation else None,
            } if school.accreditation else {},
            'operations': {
                'foundedYear': school.operations.founded_year if school.operations else None,
                'employeeCount': school.operations.employee_count if school.operations else None,
                'fleetSize': school.operations.fleet_size if school.operations else None,
                'studentCapacity': school.operations.student_capacity if school.operations else None,
            } if school.operations else {},
            'googleRating': school.google_rating,
            'googleReviewCount': school.google_review_count,
            'yelpRating': school.yelp_rating,
            'sourceType': school.source_type,
            'sourceUrl': school.source_url,
            'extractedAt': school.extracted_at.isoformat(),
            'confidence': school.confidence,
            'extractorVersion': school.extractor_version,
            'snapshotId': snapshot_id,
        }

    def _map_program_to_db(self, program: FlightProgram, snapshot_id: str) -> Dict[str, Any]:
        """Map FlightProgram object to database schema format."""
        return {
            'school_id': program.school_id,
            'program_id': program.program_id,
            'details': {
                'programType': program.details.program_type.value,
                'name': program.details.name,
                'description': program.details.description,
                'duration': {
                    'hoursMin': program.details.duration.hours_min,
                    'hoursMax': program.details.duration.hours_max,
                    'hoursTypical': program.details.duration.hours_typical,
                    'weeksMin': program.details.duration.weeks_min,
                    'weeksMax': program.details.duration.weeks_max,
                    'weeksTypical': program.details.duration.weeks_typical,
                },
                'requirements': {
                    'ageMinimum': program.details.requirements.age_minimum,
                    'englishProficiency': program.details.requirements.english_proficiency,
                    'medicalCertificateClass': program.details.requirements.medical_certificate_class.value if program.details.requirements.medical_certificate_class else None,
                    'priorCertifications': program.details.requirements.prior_certifications,
                    'flightExperienceHours': program.details.requirements.flight_experience_hours,
                },
                'includesGroundSchool': program.details.includes_ground_school,
                'includesCheckride': program.details.includes_checkride,
                'aircraftTypes': program.details.aircraft_types,
                'part61Available': program.details.part_61_available,
                'part141Available': program.details.part_141_available,
                'isPopular': program.details.is_popular,
            },
            'isActive': program.is_active,
            'seasonalAvailability': program.seasonal_availability,
            'sourceType': program.source_type,
            'sourceUrl': program.source_url,
            'extractedAt': program.extracted_at.isoformat(),
            'confidence': program.confidence,
            'extractorVersion': program.extractor_version,
            'snapshotId': snapshot_id,
        }

    def _map_pricing_to_db(self, pricing: PricingInfo, snapshot_id: str) -> Dict[str, Any]:
        """Map PricingInfo object to database schema format."""
        return {
            'school_id': pricing.school_id,
            'hourlyRates': [
                {
                    'aircraftCategory': rate.aircraft_category,
                    'ratePerHour': rate.rate_per_hour,
                    'includesInstructor': rate.includes_instructor,
                    'includesFuel': rate.includes_fuel,
                    'blockHoursMin': rate.block_hours_min,
                    'blockHoursMax': rate.block_hours_max,
                }
                for rate in pricing.hourly_rates
            ] if pricing.hourly_rates else [],
            'packagePricing': [
                {
                    'programType': package.program_type,
                    'packageName': package.package_name,
                    'totalCost': package.total_cost,
                    'flightHoursIncluded': package.flight_hours_included,
                    'groundHoursIncluded': package.ground_hours_included,
                    'includesMaterials': package.includes_materials,
                    'validForMonths': package.valid_for_months,
                    'completionDeadlineMonths': package.completion_deadline_months,
                }
                for package in pricing.package_pricing
            ] if pricing.package_pricing else [],
            'programCosts': [
                {
                    'programType': cost.program_type,
                    'costBand': cost.cost_band.value if cost.cost_band else None,
                    'estimatedTotalMin': cost.estimated_total_min,
                    'estimatedTotalMax': cost.estimated_total_max,
                    'estimatedTotalTypical': cost.estimated_total_typical,
                    'flightCostEstimate': cost.flight_cost_estimate,
                    'groundCostEstimate': cost.ground_cost_estimate,
                    'materialsCostEstimate': cost.materials_cost_estimate,
                    'examFeesEstimate': cost.exam_fees_estimate,
                    'assumptions': cost.assumptions or {},
                }
                for cost in pricing.program_costs
            ] if pricing.program_costs else [],
            'additionalFees': {
                'checkrideFee': pricing.additional_fees.checkride_fee if pricing.additional_fees else None,
                'medicalExamFee': pricing.additional_fees.medical_exam_fee if pricing.additional_fees else None,
                'knowledgeTestFee': pricing.additional_fees.knowledge_test_fee if pricing.additional_fees else None,
                'membershipFee': pricing.additional_fees.membership_fee if pricing.additional_fees else None,
                'multiEngineSurcharge': pricing.additional_fees.multi_engine_surcharge if pricing.additional_fees else None,
                'nightSurcharge': pricing.additional_fees.night_surcharge if pricing.additional_fees else None,
                'weekendSurcharge': pricing.additional_fees.weekend_surcharge if pricing.additional_fees else None,
                'enrollmentDeposit': pricing.additional_fees.enrollment_deposit if pricing.additional_fees else None,
            } if pricing.additional_fees else {},
            'currency': pricing.currency or 'USD',
            'priceLastUpdated': pricing.price_last_updated.isoformat() if pricing.price_last_updated else None,
            'valueInclusions': pricing.value_inclusions or [],
            'scholarshipsAvailable': pricing.scholarships_available,
            'sourceType': pricing.source_type,
            'sourceUrl': pricing.source_url,
            'extractedAt': pricing.extracted_at.isoformat(),
            'confidence': pricing.confidence,
            'extractorVersion': pricing.extractor_version,
            'snapshotId': snapshot_id,
        }

    def _upsert_school_record(self, cursor, school_data: Dict[str, Any]) -> str:
        """Upsert a single school record."""
        query = """
        INSERT INTO schools (
            school_id, name, description, specialties, contact, location,
            accreditation, operations, google_rating, google_review_count,
            yelp_rating, source_type, source_url, extracted_at, confidence,
            extractor_version, snapshot_id, last_updated, is_active
        ) VALUES (
            %(school_id)s, %(name)s, %(description)s, %(specialties)s,
            %(contact)s, %(location)s, %(accreditation)s, %(operations)s,
            %(googleRating)s, %(googleReviewCount)s, %(yelpRating)s,
            %(sourceType)s, %(sourceUrl)s, %(extractedAt)s, %(confidence)s,
            %(extractorVersion)s, %(snapshotId)s, NOW(), true
        )
        ON CONFLICT (school_id) DO UPDATE SET
            name = EXCLUDED.name,
            description = EXCLUDED.description,
            specialties = EXCLUDED.specialties,
            contact = EXCLUDED.contact,
            location = EXCLUDED.location,
            accreditation = EXCLUDED.accreditation,
            operations = EXCLUDED.operations,
            google_rating = EXCLUDED.google_rating,
            google_review_count = EXCLUDED.google_review_count,
            yelp_rating = EXCLUDED.yelp_rating,
            source_type = EXCLUDED.source_type,
            source_url = EXCLUDED.source_url,
            extracted_at = EXCLUDED.extracted_at,
            confidence = EXCLUDED.confidence,
            extractor_version = EXCLUDED.extractor_version,
            snapshot_id = EXCLUDED.snapshot_id,
            last_updated = NOW()
        WHERE schools.confidence < EXCLUDED.confidence
        RETURNING CASE WHEN xmax = 0 THEN 'inserted' ELSE 'updated' END as operation
        """

        cursor.execute(query, school_data)
        result = cursor.fetchone()

        return result[0] if result else 'skipped'

    def _upsert_program_record(self, cursor, program_data: Dict[str, Any]) -> str:
        """Upsert a single program record."""
        query = """
        INSERT INTO programs (
            school_id, program_id, details, is_active, seasonal_availability,
            source_type, source_url, extracted_at, confidence,
            extractor_version, snapshot_id, last_updated
        ) VALUES (
            %(school_id)s, %(program_id)s, %(details)s, %(isActive)s,
            %(seasonalAvailability)s, %(sourceType)s, %(sourceUrl)s,
            %(extractedAt)s, %(confidence)s, %(extractorVersion)s,
            %(snapshotId)s, NOW()
        )
        ON CONFLICT (program_id) DO UPDATE SET
            details = EXCLUDED.details,
            is_active = EXCLUDED.is_active,
            seasonal_availability = EXCLUDED.seasonal_availability,
            source_type = EXCLUDED.source_type,
            source_url = EXCLUDED.source_url,
            extracted_at = EXCLUDED.extracted_at,
            confidence = EXCLUDED.confidence,
            extractor_version = EXCLUDED.extractor_version,
            snapshot_id = EXCLUDED.snapshot_id,
            last_updated = NOW()
        WHERE programs.confidence < EXCLUDED.confidence
        RETURNING CASE WHEN xmax = 0 THEN 'inserted' ELSE 'updated' END as operation
        """

        cursor.execute(query, program_data)
        result = cursor.fetchone()

        return result[0] if result else 'skipped'

    def _upsert_pricing_record(self, cursor, pricing_data: Dict[str, Any]) -> str:
        """Upsert a single pricing record."""
        query = """
        INSERT INTO pricing (
            school_id, hourly_rates, package_pricing, program_costs,
            additional_fees, currency, price_last_updated, value_inclusions,
            scholarships_available, source_type, source_url, extracted_at,
            confidence, extractor_version, snapshot_id, last_updated
        ) VALUES (
            %(school_id)s, %(hourlyRates)s, %(packagePricing)s, %(programCosts)s,
            %(additionalFees)s, %(currency)s, %(priceLastUpdated)s, %(valueInclusions)s,
            %(scholarshipsAvailable)s, %(sourceType)s, %(sourceUrl)s, %(extractedAt)s,
            %(confidence)s, %(extractorVersion)s, %(snapshotId)s, NOW()
        )
        ON CONFLICT (school_id) DO UPDATE SET
            hourly_rates = EXCLUDED.hourly_rates,
            package_pricing = EXCLUDED.package_pricing,
            program_costs = EXCLUDED.program_costs,
            additional_fees = EXCLUDED.additional_fees,
            currency = EXCLUDED.currency,
            price_last_updated = EXCLUDED.price_last_updated,
            value_inclusions = EXCLUDED.value_inclusions,
            scholarships_available = EXCLUDED.scholarships_available,
            source_type = EXCLUDED.source_type,
            source_url = EXCLUDED.source_url,
            extracted_at = EXCLUDED.extracted_at,
            confidence = EXCLUDED.confidence,
            extractor_version = EXCLUDED.extractor_version,
            snapshot_id = EXCLUDED.snapshot_id,
            last_updated = NOW()
        WHERE pricing.confidence < EXCLUDED.confidence
        RETURNING CASE WHEN xmax = 0 THEN 'inserted' ELSE 'updated' END as operation
        """

        cursor.execute(query, pricing_data)
        result = cursor.fetchone()

        return result[0] if result else 'skipped'

    def close(self):
        """Close the connection pool."""
        if self.pool:
            self.pool.closeall()
            logger.info("PostgreSQL connection pool closed")


# Convenience functions
def publish_schools_to_postgres(schools: List[FlightSchool], snapshot_id: str, config_file: str = "configs/db_config.yaml") -> Dict[str, Any]:
    """
    Convenience function to publish schools to PostgreSQL.

    Args:
        schools: List of validated FlightSchool objects
        snapshot_id: Snapshot identifier
        config_file: Database configuration file path

    Returns:
        Operation results and statistics
    """
    writer = PostgresWriter(config_file)
    try:
        return writer.upsert_schools(schools, snapshot_id)
    finally:
        writer.close()


def publish_programs_to_postgres(programs: List[FlightProgram], snapshot_id: str, config_file: str = "configs/db_config.yaml") -> Dict[str, Any]:
    """
    Convenience function to publish programs to PostgreSQL.

    Args:
        programs: List of validated FlightProgram objects
        snapshot_id: Snapshot identifier
        config_file: Database configuration file path

    Returns:
        Operation results and statistics
    """
    writer = PostgresWriter(config_file)
    try:
        return writer.upsert_programs(programs, snapshot_id)
    finally:
        writer.close()


def publish_pricing_to_postgres(pricing_records: List[PricingInfo], snapshot_id: str, config_file: str = "configs/db_config.yaml") -> Dict[str, Any]:
    """
    Convenience function to publish pricing to PostgreSQL.

    Args:
        pricing_records: List of validated PricingInfo objects
        snapshot_id: Snapshot identifier
        config_file: Database configuration file path

    Returns:
        Operation results and statistics
    """
    writer = PostgresWriter(config_file)
    try:
        return writer.upsert_pricing(pricing_records, snapshot_id)
    finally:
        writer.close()
