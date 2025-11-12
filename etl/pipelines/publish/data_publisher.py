# Data Publishing Orchestrator for Flight School ETL Pipeline
#
# This module orchestrates the publishing of validated flight school data
# to both PostgreSQL and OpenSearch with bulk loading, error handling,
# and comprehensive logging.

import logging
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import yaml

# Local imports (handle both direct execution and module import)
try:
    from .postgres_writer import PostgresWriter, publish_schools_to_postgres, publish_programs_to_postgres, publish_pricing_to_postgres
    from .newsearch_indexer import NewSearchIndexer, index_schools_to_opensearch, index_programs_to_opensearch, index_pricing_to_opensearch
except ImportError:
    # Handle direct execution
    import sys
    from pathlib import Path
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))

    from postgres_writer import PostgresWriter, publish_schools_to_postgres, publish_programs_to_postgres, publish_pricing_to_postgres
    from newsearch_indexer import NewSearchIndexer, index_schools_to_opensearch, index_programs_to_opensearch, index_pricing_to_opensearch

# Schema imports
from schemas.school_schema import FlightSchool
from schemas.program_schema import FlightProgram
from schemas.pricing_schema import PricingInfo

logger = logging.getLogger(__name__)


class DataPublisher:
    """
    Orchestrates publishing of flight school data to multiple targets.

    Handles bulk loading, error recovery, and comprehensive logging
    for publishing to PostgreSQL and OpenSearch.
    """

    def __init__(self, config_file: str = "configs/db_config.yaml"):
        """
        Initialize the data publisher.

        Args:
            config_file: Path to database configuration file
        """
        self.config_file = Path(__file__).parent.parent.parent / config_file
        self.config = self._load_config()

        # Initialize writers/indexers
        self.postgres_writer = None
        self.opensearch_indexer = None

        # Publishing configuration
        self.publishing_config = self.config.get('publishing', {})
        self.batch_size = self.publishing_config.get('batch_size', 100)
        self.max_workers = self.publishing_config.get('max_workers', 4)
        self.continue_on_error = self.publishing_config.get('continue_on_error', True)

        # Setup logging
        self._setup_logging()

        logger.info("Data publisher initialized")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise

    def _setup_logging(self):
        """Setup logging configuration."""
        log_config = self.config.get('logging', {})
        log_file = log_config.get('file', 'logs/publish_pipeline.log')

        # Ensure log directory exists
        log_dir = Path(log_file).parent
        log_dir.mkdir(exist_ok=True)

        # Configure file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_config.get('level', 'INFO')))
        file_formatter = logging.Formatter(log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        file_handler.setFormatter(file_formatter)

        # Add handler to logger
        logger.addHandler(file_handler)

    def publish_all_data(self,
                        schools: List[FlightSchool] = None,
                        programs: List[FlightProgram] = None,
                        pricing: List[PricingInfo] = None,
                        snapshot_id: str = None) -> Dict[str, Any]:
        """
        Publish all flight school data to PostgreSQL and OpenSearch.

        Args:
            schools: List of validated FlightSchool objects
            programs: List of validated FlightProgram objects
            pricing: List of validated PricingInfo objects
            snapshot_id: Snapshot identifier (auto-generated if not provided)

        Returns:
            Comprehensive publishing results and statistics
        """
        start_time = datetime.now()

        # Validate inputs
        if not any([schools, programs, pricing]):
            raise ValueError("At least one data type (schools, programs, or pricing) must be provided")

        # Generate snapshot ID if not provided
        if not snapshot_id:
            snapshot_id = self._generate_snapshot_id()

        # Validate snapshot ID requirement
        if self.publishing_config.get('snapshot_id_required', True) and not snapshot_id:
            raise ValueError("Snapshot ID is required for publishing")

        results = {
            'snapshot_id': snapshot_id,
            'start_time': start_time.isoformat(),
            'end_time': None,
            'duration_seconds': None,
            'total_processed': 0,
            'postgresql': {},
            'opensearch': {},
            'errors': [],
            'warnings': []
        }

        try:
            # Initialize writers/indexers
            self._initialize_writers()

            # Publish data in parallel where possible
            publish_tasks = []

            if schools:
                publish_tasks.append(('schools', schools, snapshot_id))
            if programs:
                publish_tasks.append(('programs', programs, snapshot_id))
            if pricing:
                publish_tasks.append(('pricing', pricing, snapshot_id))

            # Execute publishing tasks
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []

                for data_type, data, snap_id in publish_tasks:
                    # Submit both PostgreSQL and OpenSearch tasks
                    pg_future = executor.submit(self._publish_to_postgres, data_type, data, snap_id)
                    os_future = executor.submit(self._publish_to_opensearch, data_type, data, snap_id)

                    futures.extend([(data_type, 'postgresql', pg_future), (data_type, 'opensearch', os_future)])

                # Collect results
                for data_type, target, future in futures:
                    try:
                        result = future.result()
                        results[target][data_type] = result
                        results['total_processed'] += result.get('total_processed', 0)

                        # Log errors
                        if result.get('errors'):
                            results['errors'].extend(result['errors'])

                    except Exception as e:
                        error_msg = f"Failed to publish {data_type} to {target}: {e}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)

                        if not self.continue_on_error:
                            raise

            # Calculate final statistics
            end_time = datetime.now()
            results['end_time'] = end_time.isoformat()
            results['duration_seconds'] = (end_time - start_time).total_seconds()

            # Log summary
            self._log_publish_summary(results)

        except Exception as e:
            logger.error(f"Data publishing failed: {e}")
            results['errors'].append(str(e))
            raise
        finally:
            self._cleanup()

        return results

    def _initialize_writers(self):
        """Initialize PostgreSQL and OpenSearch writers/indexers."""
        try:
            # Check for mock mode
            if self.config.get('development', {}).get('mock_postgres', False):
                logger.info("Using mock PostgreSQL writer")
                self.postgres_writer = MockPostgresWriter()
            else:
                self.postgres_writer = PostgresWriter(str(self.config_file))

            if self.config.get('development', {}).get('mock_opensearch', False):
                logger.info("Using mock OpenSearch indexer")
                self.opensearch_indexer = MockOpenSearchIndexer()
            else:
                self.opensearch_indexer = NewSearchIndexer(str(self.config_file))

        except Exception as e:
            logger.error(f"Failed to initialize writers: {e}")
            raise

    def _publish_to_postgres(self, data_type: str, data: List, snapshot_id: str) -> Dict[str, Any]:
        """Publish data to PostgreSQL."""
        logger.info(f"Publishing {len(data)} {data_type} to PostgreSQL")

        if data_type == 'schools':
            return self.postgres_writer.upsert_schools(data, snapshot_id)
        elif data_type == 'programs':
            return self.postgres_writer.upsert_programs(data, snapshot_id)
        elif data_type == 'pricing':
            return self.postgres_writer.upsert_pricing(data, snapshot_id)
        else:
            raise ValueError(f"Unknown data type: {data_type}")

    def _publish_to_opensearch(self, data_type: str, data: List, snapshot_id: str) -> Dict[str, Any]:
        """Publish data to OpenSearch."""
        logger.info(f"Publishing {len(data)} {data_type} to OpenSearch")

        if data_type == 'schools':
            return self.opensearch_indexer.index_schools(data, snapshot_id)
        elif data_type == 'programs':
            return self.opensearch_indexer.index_programs(data, snapshot_id)
        elif data_type == 'pricing':
            return self.opensearch_indexer.index_pricing(data, snapshot_id)
        else:
            raise ValueError(f"Unknown data type: {data_type}")

    def _generate_snapshot_id(self) -> str:
        """Generate a unique snapshot ID."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"snapshot_{timestamp}"

    def _log_publish_summary(self, results: Dict[str, Any]):
        """Log a comprehensive summary of the publishing operation."""
        summary = {
            'snapshot_id': results.get('snapshot_id'),
            'duration': results.get('duration_seconds'),
            'total_processed': results.get('total_processed'),
            'postgresql': {
                data_type: {
                    'inserted': stats.get('inserted', 0),
                    'updated': stats.get('updated', 0),
                    'errors': len(stats.get('error_details', []))
                }
                for data_type, stats in results.get('postgresql', {}).items()
            },
            'opensearch': {
                data_type: {
                    'successful': stats.get('successful', 0),
                    'failed': stats.get('failed', 0)
                }
                for data_type, stats in results.get('opensearch', {}).items()
            },
            'total_errors': len(results.get('errors', []))
        }

        logger.info(f"Publishing complete: {json.dumps(summary, indent=2)}")

        # Save detailed results to file
        results_file = f"logs/publish_results_{results['snapshot_id']}.json"
        results_path = Path(results_file)
        results_path.parent.mkdir(exist_ok=True)

        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"Detailed results saved to {results_path}")

    def _cleanup(self):
        """Clean up resources."""
        try:
            if self.postgres_writer and hasattr(self.postgres_writer, 'close'):
                self.postgres_writer.close()
            if self.opensearch_indexer and hasattr(self.opensearch_indexer, 'close'):
                self.opensearch_indexer.close()
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")

    def validate_data_quality(self, data: List, data_type: str) -> Tuple[List, List]:
        """
        Validate data quality before publishing.

        Args:
            data: List of data objects to validate
            data_type: Type of data ('schools', 'programs', or 'pricing')

        Returns:
            Tuple of (valid_data, invalid_data)
        """
        if not self.publishing_config.get('validate_before_publish', True):
            return data, []

        valid_data = []
        invalid_data = []

        min_confidence = self.config.get('provenance', {}).get('min_confidence_threshold', 0.5)

        for item in data:
            is_valid = True
            issues = []

            # Check confidence score
            confidence = getattr(item, 'confidence', 0)
            if confidence < min_confidence:
                is_valid = False
                issues.append(f"Low confidence: {confidence}")

            # Type-specific validations
            if data_type == 'schools':
                if not getattr(item, 'school_id', None):
                    is_valid = False
                    issues.append("Missing school_id")
                if not getattr(item, 'name', None):
                    is_valid = False
                    issues.append("Missing name")

            elif data_type == 'programs':
                if not getattr(item, 'program_id', None):
                    is_valid = False
                    issues.append("Missing program_id")
                if not getattr(item, 'school_id', None):
                    is_valid = False
                    issues.append("Missing school_id")

            elif data_type == 'pricing':
                if not getattr(item, 'school_id', None):
                    is_valid = False
                    issues.append("Missing school_id")

            if is_valid:
                valid_data.append(item)
            else:
                invalid_item = {
                    'data': item,
                    'issues': issues,
                    'data_type': data_type
                }
                invalid_data.append(invalid_item)

                if self.publishing_config.get('skip_invalid_records', True):
                    logger.warning(f"Skipping invalid {data_type} record: {issues}")
                else:
                    logger.error(f"Invalid {data_type} record found: {issues}")
                    if not self.continue_on_error:
                        raise ValueError(f"Invalid {data_type} record: {issues}")

        return valid_data, invalid_data


class MockPostgresWriter:
    """Mock PostgreSQL writer for testing."""

    def upsert_schools(self, schools, snapshot_id):
        logger.info(f"Mock: Would upsert {len(schools)} schools")
        return {'total_processed': len(schools), 'inserted': len(schools), 'updated': 0, 'errors': 0}

    def upsert_programs(self, programs, snapshot_id):
        logger.info(f"Mock: Would upsert {len(programs)} programs")
        return {'total_processed': len(programs), 'inserted': len(programs), 'updated': 0, 'errors': 0}

    def upsert_pricing(self, pricing, snapshot_id):
        logger.info(f"Mock: Would upsert {len(pricing)} pricing records")
        return {'total_processed': len(pricing), 'inserted': len(pricing), 'updated': 0, 'errors': 0}

    def close(self):
        pass


class MockOpenSearchIndexer:
    """Mock OpenSearch indexer for testing."""

    def index_schools(self, schools, snapshot_id):
        logger.info(f"Mock: Would index {len(schools)} schools")
        return {'total_processed': len(schools), 'successful': len(schools), 'failed': 0}

    def index_programs(self, programs, snapshot_id):
        logger.info(f"Mock: Would index {len(programs)} programs")
        return {'total_processed': len(programs), 'successful': len(programs), 'failed': 0}

    def index_pricing(self, pricing, snapshot_id):
        logger.info(f"Mock: Would index {len(pricing)} pricing records")
        return {'total_processed': len(pricing), 'successful': len(pricing), 'failed': 0}

    def close(self):
        pass


# Convenience functions
def publish_flight_school_data(schools: List[FlightSchool] = None,
                             programs: List[FlightProgram] = None,
                             pricing: List[PricingInfo] = None,
                             snapshot_id: str = None,
                             config_file: str = "configs/db_config.yaml") -> Dict[str, Any]:
    """
    Convenience function to publish all flight school data.

    Args:
        schools: List of validated FlightSchool objects
        programs: List of validated FlightProgram objects
        pricing: List of validated PricingInfo objects
        snapshot_id: Snapshot identifier (auto-generated if not provided)
        config_file: Database configuration file path

    Returns:
        Comprehensive publishing results and statistics
    """
    publisher = DataPublisher(config_file)
    return publisher.publish_all_data(schools, programs, pricing, snapshot_id)


if __name__ == '__main__':
    # Example usage with mock mode enabled
    logging.basicConfig(level=logging.INFO)

    # Enable mock mode for testing (modify config temporarily)
    config_path = Path("configs/db_config.yaml")
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Enable mock mode
        if 'development' not in config:
            config['development'] = {}
        config['development']['mock_postgres'] = True
        config['development']['mock_opensearch'] = True

        # Write back temporarily
        with open(config_path, 'w') as f:
            yaml.dump(config, f)

    try:
        # Mock data for testing
        from schemas.school_schema import FlightSchool, ContactInfo, LocationInfo

        # Create sample school
        contact = ContactInfo(phone="(555) 123-4567", email="info@sampleflight.com", website="https://sampleflight.com")
        location = LocationInfo(city="Sample City", state="CA", zip_code="12345", country="United States")

        school = FlightSchool(
            school_id="sample_001",
            name="Sample Flight School",
            description="A great flight school for learning to fly",
            contact=contact,
            location=location,
            source_type="test",
            source_url="https://example.com",
            extracted_at=datetime.now(),
            confidence=0.9,
            extractor_version="1.0.0",
            snapshot_id="sample_snapshot_001"
        )

        print("Testing data publisher with mock data...")
        results = publish_flight_school_data(
            schools=[school],
            config_file="configs/db_config.yaml"
        )

        print(f"Publishing completed: {results['total_processed']} records processed")
        print(f"PostgreSQL results: {results.get('postgresql', {})}")
        print(f"OpenSearch results: {results.get('opensearch', {})}")

    finally:
        # Restore original config (remove mock flags)
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            if 'development' in config:
                config['development'].pop('mock_postgres', None)
                config['development'].pop('mock_opensearch', None)

            with open(config_path, 'w') as f:
                yaml.dump(config, f)
