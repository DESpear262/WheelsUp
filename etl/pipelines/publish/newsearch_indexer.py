# OpenSearch/NewSearch Indexer for Flight School ETL Pipeline
#
# This module handles indexing flight school data into OpenSearch
# with optimized document structures for search and filtering.

import logging
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import yaml

# OpenSearch client (optional)
try:
    from opensearchpy import OpenSearch, helpers
    from opensearchpy.exceptions import NotFoundError, RequestError
    HAS_OPENSEARCH = True
except ImportError:
    # Create mock objects for testing
    class MockOpenSearch:
        def __init__(self, **kwargs):
            pass
        def info(self):
            return {"version": {"number": "mock"}}
        def indices(self):
            return self
        def exists(self, **kwargs):
            return False
        def create(self, **kwargs):
            pass
        def bulk(self, **kwargs):
            return (0, 0)

    class MockHelpers:
        def bulk(self, client, actions, **kwargs):
            return (len(actions), [])

    OpenSearch = MockOpenSearch
    helpers = MockHelpers()
    NotFoundError = Exception
    RequestError = Exception
    HAS_OPENSEARCH = False

# Schema imports
from schemas.school_schema import FlightSchool
from schemas.program_schema import FlightProgram
from schemas.pricing_schema import PricingInfo

logger = logging.getLogger(__name__)


class NewSearchIndexer:
    """
    Handles indexing flight school data into OpenSearch with optimized search documents.

    Creates search-optimized JSON documents and manages bulk indexing operations
    with error handling and retry logic.
    """

    def __init__(self, config_file: str = "configs/db_config.yaml"):
        """
        Initialize the OpenSearch indexer.

        Args:
            config_file: Path to database configuration file
        """
        if not HAS_OPENSEARCH:
            raise ImportError("opensearchpy is required for OpenSearch operations. Install with: pip install opensearch-py")

        self.config_file = Path(__file__).parent.parent.parent / config_file
        self.config = self._load_config()
        self.client = self._initialize_client()

        # Index names from config
        self.schools_index = self.config.get('opensearch', {}).get('schools_index', 'wheelsup-schools')
        self.programs_index = self.config.get('opensearch', {}).get('programs_index', 'wheelsup-programs')
        self.pricing_index = self.config.get('opensearch', {}).get('pricing_index', 'wheelsup-pricing')

        logger.info("NewSearch indexer initialized")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise

    def _initialize_client(self) -> OpenSearch:
        """Initialize OpenSearch client."""
        opensearch_config = self.config.get('opensearch', {})

        # Build connection URL
        url = opensearch_config.get('url')
        if not url:
            protocol = opensearch_config.get('protocol', 'http')
            host = opensearch_config.get('host', 'localhost')
            port = opensearch_config.get('port', 9200)
            url = f"{protocol}://{host}:{port}"

        # Initialize client
        client_config = {
            'hosts': [url],
            'timeout': opensearch_config.get('bulk_timeout', 30),
            'max_retries': opensearch_config.get('bulk_max_retries', 3),
            'retry_on_timeout': True,
        }

        # Add AWS authentication if configured
        if opensearch_config.get('aws_region'):
            # For AWS OpenSearch, additional authentication would be needed
            # This is a simplified version for development
            pass

        try:
            client = OpenSearch(**client_config)
            # Test connection
            info = client.info()
            logger.info(f"Connected to OpenSearch: {info['version']['number']}")
            return client
        except Exception as e:
            logger.error(f"Failed to connect to OpenSearch: {e}")
            raise

    def index_schools(self, schools: List[FlightSchool], snapshot_id: str) -> Dict[str, Any]:
        """
        Index flight schools into OpenSearch.

        Args:
            schools: List of validated FlightSchool objects
            snapshot_id: Snapshot identifier for provenance tracking

        Returns:
            Dictionary with operation results and statistics
        """
        documents = []
        for school in schools:
            try:
                doc = self._create_school_document(school, snapshot_id)
                documents.append(doc)
            except Exception as e:
                logger.error(f"Error creating document for school {getattr(school, 'school_id', 'unknown')}: {e}")

        return self._bulk_index_documents(self.schools_index, documents, 'schools')

    def index_programs(self, programs: List[FlightProgram], snapshot_id: str) -> Dict[str, Any]:
        """
        Index flight programs into OpenSearch.

        Args:
            programs: List of validated FlightProgram objects
            snapshot_id: Snapshot identifier for provenance tracking

        Returns:
            Dictionary with operation results and statistics
        """
        documents = []
        for program in programs:
            try:
                doc = self._create_program_document(program, snapshot_id)
                documents.append(doc)
            except Exception as e:
                logger.error(f"Error creating document for program {getattr(program, 'program_id', 'unknown')}: {e}")

        return self._bulk_index_documents(self.programs_index, documents, 'programs')

    def index_pricing(self, pricing_records: List[PricingInfo], snapshot_id: str) -> Dict[str, Any]:
        """
        Index pricing information into OpenSearch.

        Args:
            pricing_records: List of validated PricingInfo objects
            snapshot_id: Snapshot identifier for provenance tracking

        Returns:
            Dictionary with operation results and statistics
        """
        documents = []
        for pricing in pricing_records:
            try:
                doc = self._create_pricing_document(pricing, snapshot_id)
                documents.append(doc)
            except Exception as e:
                logger.error(f"Error creating document for pricing {getattr(pricing, 'school_id', 'unknown')}: {e}")

        return self._bulk_index_documents(self.pricing_index, documents, 'pricing')

    def _create_school_document(self, school: FlightSchool, snapshot_id: str) -> Dict[str, Any]:
        """Create OpenSearch document for a flight school."""
        # Flatten nested structures for better searchability
        location = school.location
        contact = school.contact
        accreditation = school.accreditation
        operations = school.operations

        document = {
            # Primary identifiers
            'school_id': school.school_id,
            'name': school.name,
            'description': school.description,

            # Flattened contact info for search
            'phone': contact.phone if contact else None,
            'email': contact.email if contact else None,
            'website': contact.website if contact else None,

            # Flattened location for geo search
            'city': location.city if location else None,
            'state': location.state if location else None,
            'zip_code': location.zip_code if location else None,
            'country': location.country if location else 'United States',
            'latitude': getattr(location, 'latitude', None) if location else None,
            'longitude': getattr(location, 'longitude', None) if location else None,
            'nearest_airport_icao': getattr(location, 'nearest_airport_icao', None) if location else None,
            'nearest_airport_name': getattr(location, 'nearest_airport_name', None) if location else None,

            # Accreditation and operations
            'accreditation_type': accreditation.type.value if accreditation and accreditation.type else None,
            'va_approved': accreditation.va_approved if accreditation else None,
            'founded_year': operations.founded_year if operations else None,
            'employee_count': operations.employee_count if operations else None,
            'fleet_size': operations.fleet_size if operations else None,
            'student_capacity': operations.student_capacity if operations else None,

            # Ratings and reviews
            'google_rating': school.google_rating,
            'google_review_count': school.google_review_count,
            'yelp_rating': school.yelp_rating,

            # Specialties as searchable array
            'specialties': school.specialties or [],

            # Provenance and metadata
            'source_type': school.source_type,
            'source_url': school.source_url,
            'extracted_at': school.extracted_at.isoformat(),
            'confidence': school.confidence,
            'extractor_version': school.extractor_version,
            'snapshot_id': snapshot_id,

            # Search optimization fields
            'search_text': self._create_search_text(school),
            'location_text': self._create_location_text(location) if location else None,

            # Timestamp for sorting
            'indexed_at': datetime.now().isoformat(),
        }

        return document

    def _create_program_document(self, program: FlightProgram, snapshot_id: str) -> Dict[str, Any]:
        """Create OpenSearch document for a flight program."""
        details = program.details
        requirements = details.requirements

        document = {
            # Primary identifiers
            'school_id': program.school_id,
            'program_id': program.program_id,

            # Program details
            'program_type': details.program_type.value,
            'program_name': details.name,
            'description': details.description,

            # Duration information
            'hours_min': details.duration.hours_min,
            'hours_max': details.duration.hours_max,
            'hours_typical': details.duration.hours_typical,
            'weeks_min': details.duration.weeks_min,
            'weeks_max': details.duration.weeks_max,
            'weeks_typical': details.duration.weeks_typical,

            # Requirements
            'age_minimum': requirements.age_minimum,
            'english_proficiency': requirements.english_proficiency,
            'medical_certificate_class': requirements.medical_certificate_class.value if requirements.medical_certificate_class else None,
            'prior_certifications': requirements.prior_certifications or [],
            'flight_experience_hours': requirements.flight_experience_hours,

            # Program features
            'includes_ground_school': details.includes_ground_school,
            'includes_checkride': details.includes_checkride,
            'aircraft_types': details.aircraft_types or [],
            'part_61_available': details.part_61_available,
            'part_141_available': details.part_141_available,
            'is_popular': details.is_popular,

            # Status and availability
            'is_active': program.is_active,
            'seasonal_availability': program.seasonal_availability,

            # Provenance
            'source_type': program.source_type,
            'source_url': program.source_url,
            'extracted_at': program.extracted_at.isoformat(),
            'confidence': program.confidence,
            'extractor_version': program.extractor_version,
            'snapshot_id': snapshot_id,

            # Search optimization
            'search_text': self._create_program_search_text(program),

            # Timestamp for sorting
            'indexed_at': datetime.now().isoformat(),
        }

        return document

    def _create_pricing_document(self, pricing: PricingInfo, snapshot_id: str) -> Dict[str, Any]:
        """Create OpenSearch document for pricing information."""
        document = {
            # Primary identifier
            'school_id': pricing.school_id,

            # Hourly rates (flattened for search)
            'hourly_rates': [
                {
                    'aircraft_category': rate.aircraft_category,
                    'rate_per_hour': rate.rate_per_hour,
                    'includes_instructor': rate.includes_instructor,
                    'includes_fuel': rate.includes_fuel,
                }
                for rate in pricing.hourly_rates
            ] if pricing.hourly_rates else [],

            # Package pricing
            'package_pricing': [
                {
                    'program_type': package.program_type,
                    'package_name': package.package_name,
                    'total_cost': package.total_cost,
                    'flight_hours_included': package.flight_hours_included,
                    'ground_hours_included': package.ground_hours_included,
                }
                for package in pricing.package_pricing
            ] if pricing.package_pricing else [],

            # Program cost estimates
            'program_costs': [
                {
                    'program_type': cost.program_type,
                    'cost_band': cost.cost_band.value if cost.cost_band else None,
                    'estimated_total_min': cost.estimated_total_min,
                    'estimated_total_max': cost.estimated_total_max,
                    'estimated_total_typical': cost.estimated_total_typical,
                }
                for cost in pricing.program_costs
            ] if pricing.program_costs else [],

            # Additional fees
            'additional_fees': {
                'checkride_fee': pricing.additional_fees.checkride_fee if pricing.additional_fees else None,
                'medical_exam_fee': pricing.additional_fees.medical_exam_fee if pricing.additional_fees else None,
                'knowledge_test_fee': pricing.additional_fees.knowledge_test_fee if pricing.additional_fees else None,
            } if pricing.additional_fees else {},

            # Metadata
            'currency': pricing.currency or 'USD',
            'price_last_updated': pricing.price_last_updated.isoformat() if pricing.price_last_updated else None,
            'value_inclusions': pricing.value_inclusions or [],
            'scholarships_available': pricing.scholarships_available,

            # Provenance
            'source_type': pricing.source_type,
            'source_url': pricing.source_url,
            'extracted_at': pricing.extracted_at.isoformat(),
            'confidence': pricing.confidence,
            'extractor_version': pricing.extractor_version,
            'snapshot_id': snapshot_id,

            # Search optimization
            'search_text': self._create_pricing_search_text(pricing),

            # Timestamp for sorting
            'indexed_at': datetime.now().isoformat(),
        }

        return document

    def _create_search_text(self, school: FlightSchool) -> str:
        """Create searchable text field for school."""
        parts = [
            school.name,
            school.description,
            f"{' '.join(school.specialties)}" if school.specialties else "",
        ]

        if school.location:
            location_parts = [
                school.location.city,
                school.location.state,
                getattr(school.location, 'nearest_airport_name', None),
            ]
            parts.extend([p for p in location_parts if p])

        return ' '.join([p for p in parts if p]).lower()

    def _create_location_text(self, location) -> str:
        """Create location text for search."""
        if not location:
            return None

        parts = [
            location.city,
            location.state,
            location.zip_code,
            getattr(location, 'nearest_airport_name', None),
        ]

        return ' '.join([p for p in parts if p]).lower()

    def _create_program_search_text(self, program: FlightProgram) -> str:
        """Create searchable text field for program."""
        details = program.details
        parts = [
            details.program_type.value,
            details.name,
            details.description,
            f"{' '.join(details.aircraft_types)}" if details.aircraft_types else "",
        ]

        return ' '.join([p for p in parts if p]).lower()

    def _create_pricing_search_text(self, pricing: PricingInfo) -> str:
        """Create searchable text field for pricing."""
        parts = []

        # Add aircraft categories from hourly rates
        if pricing.hourly_rates:
            categories = [rate.aircraft_category for rate in pricing.hourly_rates]
            parts.extend(categories)

        # Add program types from packages
        if pricing.package_pricing:
            program_types = [package.program_type for package in pricing.package_pricing]
            parts.extend(program_types)

        return ' '.join(set(parts)).lower()  # Remove duplicates

    def _bulk_index_documents(self, index_name: str, documents: List[Dict[str, Any]], doc_type: str) -> Dict[str, Any]:
        """
        Bulk index documents into OpenSearch.

        Args:
            index_name: Name of the index
            documents: List of documents to index
            doc_type: Type of documents (for logging)

        Returns:
            Dictionary with operation results and statistics
        """
        results = {
            'total_processed': len(documents),
            'successful': 0,
            'failed': 0,
            'errors': []
        }

        if not documents:
            logger.info(f"No {doc_type} documents to index")
            return results

        # Ensure index exists
        self._ensure_index_exists(index_name)

        # Prepare bulk operations
        actions = []
        for doc in documents:
            action = {
                '_index': index_name,
                '_id': doc.get(f'{doc_type[:-1]}_id'),  # Remove 's' from type for id field
                '_source': doc
            }
            actions.append(action)

        # Execute bulk operation
        try:
            success, failed = helpers.bulk(
                self.client,
                actions,
                stats_only=True,
                raise_on_error=False
            )

            results['successful'] = success
            results['failed'] = failed

            logger.info(f"Bulk indexed {doc_type}: {success} successful, {failed} failed")

        except Exception as e:
            logger.error(f"Bulk indexing failed for {doc_type}: {e}")
            results['errors'].append(str(e))

        return results

    def _ensure_index_exists(self, index_name: str):
        """Ensure the index exists, creating it if necessary."""
        try:
            if not self.client.indices.exists(index=index_name):
                # Create index with basic mapping
                mapping = {
                    'mappings': {
                        'properties': {
                            'school_id': {'type': 'keyword'},
                            'program_id': {'type': 'keyword'},
                            'name': {'type': 'text', 'analyzer': 'standard'},
                            'description': {'type': 'text', 'analyzer': 'standard'},
                            'search_text': {'type': 'text', 'analyzer': 'standard'},
                            'location_text': {'type': 'text', 'analyzer': 'standard'},
                            'city': {'type': 'keyword'},
                            'state': {'type': 'keyword'},
                            'latitude': {'type': 'float'},
                            'longitude': {'type': 'float'},
                            'confidence': {'type': 'float'},
                            'extracted_at': {'type': 'date'},
                            'indexed_at': {'type': 'date'},
                            'specialties': {'type': 'keyword'},
                            'aircraft_types': {'type': 'keyword'},
                            'program_type': {'type': 'keyword'},
                        }
                    },
                    'settings': {
                        'number_of_shards': self.config.get('opensearch', {}).get('number_of_shards', 1),
                        'number_of_replicas': self.config.get('opensearch', {}).get('number_of_replicas', 0),
                    }
                }

                self.client.indices.create(index=index_name, body=mapping)
                logger.info(f"Created index: {index_name}")

        except Exception as e:
            logger.error(f"Error ensuring index exists {index_name}: {e}")

    def close(self):
        """Close the OpenSearch client connection."""
        # OpenSearch client doesn't need explicit closing
        logger.info("NewSearch indexer closed")


# Convenience functions
def index_schools_to_opensearch(schools: List[FlightSchool], snapshot_id: str, config_file: str = "configs/db_config.yaml") -> Dict[str, Any]:
    """
    Convenience function to index schools into OpenSearch.

    Args:
        schools: List of validated FlightSchool objects
        snapshot_id: Snapshot identifier
        config_file: Configuration file path

    Returns:
        Operation results and statistics
    """
    indexer = NewSearchIndexer(config_file)
    try:
        return indexer.index_schools(schools, snapshot_id)
    finally:
        indexer.close()


def index_programs_to_opensearch(programs: List[FlightProgram], snapshot_id: str, config_file: str = "configs/db_config.yaml") -> Dict[str, Any]:
    """
    Convenience function to index programs into OpenSearch.

    Args:
        programs: List of validated FlightProgram objects
        snapshot_id: Snapshot identifier
        config_file: Configuration file path

    Returns:
        Operation results and statistics
    """
    indexer = NewSearchIndexer(config_file)
    try:
        return indexer.index_programs(programs, snapshot_id)
    finally:
        indexer.close()


def index_pricing_to_opensearch(pricing_records: List[PricingInfo], snapshot_id: str, config_file: str = "configs/db_config.yaml") -> Dict[str, Any]:
    """
    Convenience function to index pricing into OpenSearch.

    Args:
        pricing_records: List of validated PricingInfo objects
        snapshot_id: Snapshot identifier
        config_file: Configuration file path

    Returns:
        Operation results and statistics
    """
    indexer = NewSearchIndexer(config_file)
    try:
        return indexer.index_pricing(pricing_records, snapshot_id)
    finally:
        indexer.close()
