#!/usr/bin/env python3
"""
Coverage & Confidence Report for WheelsUp ETL Pipeline

This script analyzes the completeness and confidence of flight school data
in the database, generating coverage percentages and confidence score aggregations.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
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

# Local imports
import sys
from pathlib import Path

# Add parent directory to path for imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

from utils.logger import get_logger

logger = get_logger()


class CoverageReportGenerator:
    """
    Generates comprehensive coverage and confidence reports for flight school data.

    Analyzes database completeness, field coverage percentages, and confidence scores
    to provide insights into ETL pipeline effectiveness.
    """

    def __init__(self, config_file: str = "configs/db_config.yaml"):
        """
        Initialize the coverage report generator.

        Args:
            config_file: Path to database configuration file
        """
        self.config = self._load_config(config_file)
        self.connection = None
        self.cursor = None

    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load database configuration from YAML file."""
        config_path = Path(__file__).parent.parent / config_file
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def connect(self):
        """Establish database connection."""
        if not HAS_PSYCOPG2:
            logger.warning("psycopg2 not available - using mock connection")
            return

        db_config = self.config.get('postgresql', {})

        try:
            self.connection = psycopg2.connect(
                host=db_config.get('host', 'localhost'),
                port=db_config.get('port', 5432),
                database=db_config.get('database', 'wheelsup_db'),
                user=db_config.get('user', 'user'),
                password=db_config.get('password', 'password')
            )
            self.cursor = self.connection.cursor()
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def disconnect(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")

    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Tuple]:
        """
        Execute a database query and return results.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            List of result tuples
        """
        if not self.cursor:
            logger.warning("No database connection - returning empty results")
            return []

        try:
            self.cursor.execute(query, params or ())
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return []

    def get_table_counts(self) -> Dict[str, int]:
        """
        Get total record counts for all tables.

        Returns:
            Dictionary with table counts
        """
        counts = {}

        tables = ['schools', 'programs', 'pricing']
        for table in tables:
            query = f"SELECT COUNT(*) FROM {table}"
            result = self.execute_query(query)
            counts[table] = result[0][0] if result else 0

        logger.info(f"Table counts: {counts}")
        return counts

    def analyze_school_coverage(self) -> Dict[str, Any]:
        """
        Analyze coverage of core school fields.

        Returns:
            Dictionary with coverage statistics for school fields
        """
        total_schools = self.get_table_counts()['schools']
        if total_schools == 0:
            return {"total_schools": 0, "field_coverage": {}}

        coverage_stats = {
            "total_schools": total_schools,
            "field_coverage": {}
        }

        # Define core fields to analyze
        core_fields = {
            "name": "name IS NOT NULL AND name != ''",
            "description": "description IS NOT NULL AND description != ''",
            "website": "contact->>'website' IS NOT NULL AND contact->>'website' != ''",
            "phone": "contact->>'phone' IS NOT NULL AND contact->>'phone' != ''",
            "email": "contact->>'email' IS NOT NULL AND contact->>'email' != ''",
            "city": "location->>'city' IS NOT NULL AND location->>'city' != ''",
            "state": "location->>'state' IS NOT NULL AND location->>'state' != ''",
            "country": "location->>'country' IS NOT NULL AND location->>'country' != ''",
            "accreditation_type": "accreditation->>'type' IS NOT NULL AND accreditation->>'type' != ''",
            "va_approved": "accreditation->>'vaApproved' IS NOT NULL",
            "latitude": "location->>'latitude' IS NOT NULL",
            "longitude": "location->>'longitude' IS NOT NULL",
            "google_rating": "google_rating IS NOT NULL",
            "founded_year": "operations->>'foundedYear' IS NOT NULL",
            "fleet_size": "operations->>'fleetSize' IS NOT NULL"
        }

        for field_name, condition in core_fields.items():
            query = f"SELECT COUNT(*) FROM schools WHERE {condition}"
            result = self.execute_query(query)
            count = result[0][0] if result else 0
            percentage = (count / total_schools) * 100 if total_schools > 0 else 0

            coverage_stats["field_coverage"][field_name] = {
                "count": count,
                "percentage": round(percentage, 2)
            }

        return coverage_stats

    def analyze_program_coverage(self) -> Dict[str, Any]:
        """
        Analyze coverage of program fields.

        Returns:
            Dictionary with coverage statistics for program fields
        """
        total_programs = self.get_table_counts()['programs']
        if total_programs == 0:
            return {"total_programs": 0, "field_coverage": {}}

        coverage_stats = {
            "total_programs": total_programs,
            "field_coverage": {}
        }

        # Define core program fields
        core_fields = {
            "program_name": "name IS NOT NULL AND name != ''",
            "description": "description IS NOT NULL AND description != ''",
            "duration_hours": "duration_hours IS NOT NULL",
            "cost_per_hour": "cost_per_hour IS NOT NULL",
            "total_cost": "total_cost IS NOT NULL",
            "requirements": "requirements IS NOT NULL",
            "aircraft_types": "aircraft_types IS NOT NULL",
            "certificate_type": "certificate_type IS NOT NULL AND certificate_type != ''"
        }

        for field_name, condition in core_fields.items():
            query = f"SELECT COUNT(*) FROM programs WHERE {condition}"
            result = self.execute_query(query)
            count = result[0][0] if result else 0
            percentage = (count / total_programs) * 100 if total_programs > 0 else 0

            coverage_stats["field_coverage"][field_name] = {
                "count": count,
                "percentage": round(percentage, 2)
            }

        return coverage_stats

    def analyze_pricing_coverage(self) -> Dict[str, Any]:
        """
        Analyze coverage of pricing fields.

        Returns:
            Dictionary with coverage statistics for pricing fields
        """
        total_pricing = self.get_table_counts()['pricing']
        if total_pricing == 0:
            return {"total_pricing_records": 0, "field_coverage": {}}

        coverage_stats = {
            "total_pricing_records": total_pricing,
            "field_coverage": {}
        }

        # Define core pricing fields
        core_fields = {
            "hourly_rate": "hourly_rate IS NOT NULL",
            "total_cost": "total_cost IS NOT NULL",
            "currency": "currency IS NOT NULL AND currency != ''",
            "cost_band": "cost_band IS NOT NULL AND cost_band != ''",
            "aircraft_type": "aircraft_type IS NOT NULL AND aircraft_type != ''"
        }

        for field_name, condition in core_fields.items():
            query = f"SELECT COUNT(*) FROM pricing WHERE {condition}"
            result = self.execute_query(query)
            count = result[0][0] if result else 0
            percentage = (count / total_pricing) * 100 if total_pricing > 0 else 0

            coverage_stats["field_coverage"][field_name] = {
                "count": count,
                "percentage": round(percentage, 2)
            }

        return coverage_stats

    def analyze_confidence_scores(self) -> Dict[str, Any]:
        """
        Analyze confidence scores across all tables.

        Returns:
            Dictionary with confidence score statistics
        """
        confidence_stats = {}

        # Schools confidence
        schools_query = """
            SELECT
                AVG(confidence) as mean_confidence,
                MIN(confidence) as min_confidence,
                MAX(confidence) as max_confidence,
                COUNT(*) as total_records
            FROM schools
        """
        result = self.execute_query(schools_query)
        if result:
            row = result[0]
            confidence_stats["schools"] = {
                "mean_confidence": round(float(row[0] or 0), 4),
                "min_confidence": round(float(row[1] or 0), 4),
                "max_confidence": round(float(row[2] or 0), 4),
                "total_records": row[3]
            }

        # Programs confidence (if available)
        programs_query = """
            SELECT
                AVG(confidence) as mean_confidence,
                MIN(confidence) as min_confidence,
                MAX(confidence) as max_confidence,
                COUNT(*) as total_records
            FROM programs
        """
        result = self.execute_query(programs_query)
        if result:
            row = result[0]
            confidence_stats["programs"] = {
                "mean_confidence": round(float(row[0] or 0), 4),
                "min_confidence": round(float(row[1] or 0), 4),
                "max_confidence": round(float(row[2] or 0), 4),
                "total_records": row[3]
            }

        # Pricing confidence (if available)
        pricing_query = """
            SELECT
                AVG(confidence) as mean_confidence,
                MIN(confidence) as min_confidence,
                MAX(confidence) as max_confidence,
                COUNT(*) as total_records
            FROM pricing
        """
        result = self.execute_query(pricing_query)
        if result:
            row = result[0]
            confidence_stats["pricing"] = {
                "mean_confidence": round(float(row[0] or 0), 4),
                "min_confidence": round(float(row[1] or 0), 4),
                "max_confidence": round(float(row[2] or 0), 4),
                "total_records": row[3]
            }

        return confidence_stats

    def generate_report(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate comprehensive coverage and confidence report.

        Args:
            output_file: Optional path to save JSON output

        Returns:
            Complete coverage report dictionary
        """
        logger.info("Starting coverage and confidence analysis")

        try:
            self.connect()

            report = {
                "report_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "environment": os.getenv('ENVIRONMENT', 'development'),
                    "database_connected": self.connection is not None
                },
                "table_counts": self.get_table_counts(),
                "schools_coverage": self.analyze_school_coverage(),
                "programs_coverage": self.analyze_program_coverage(),
                "pricing_coverage": self.analyze_pricing_coverage(),
                "confidence_scores": self.analyze_confidence_scores()
            }

            # Calculate overall completeness metrics
            schools_coverage = report["schools_coverage"]
            if schools_coverage["total_schools"] > 0:
                field_percentages = [
                    field_data["percentage"]
                    for field_data in schools_coverage["field_coverage"].values()
                ]
                report["overall_metrics"] = {
                    "average_field_completeness": round(sum(field_percentages) / len(field_percentages), 2),
                    "most_complete_field": max(
                        schools_coverage["field_coverage"].items(),
                        key=lambda x: x[1]["percentage"]
                    )[0],
                    "least_complete_field": min(
                        schools_coverage["field_coverage"].items(),
                        key=lambda x: x[1]["percentage"]
                    )[0]
                }

            logger.info("Coverage analysis completed successfully")

            # Save to file if requested
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)

                logger.info(f"Report saved to: {output_path}")

            return report

        except Exception as e:
            logger.error(f"Failed to generate coverage report: {e}")
            raise
        finally:
            self.disconnect()


def main():
    """Main entry point for command-line execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate coverage and confidence report")
    parser.add_argument(
        "--config",
        default="configs/db_config.yaml",
        help="Database configuration file"
    )
    parser.add_argument(
        "--output",
        default="output/coverage_summary_2025Q1-MVP.json",
        help="Output JSON file path"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        os.environ['LOG_LEVEL'] = 'DEBUG'

    # Generate report
    generator = CoverageReportGenerator(args.config)
    report = generator.generate_report(args.output)

    # Print summary to console
    print("\n=== Coverage & Confidence Report Summary ===")
    print(f"Generated at: {report['report_metadata']['generated_at']}")
    print(f"Database connected: {report['report_metadata']['database_connected']}")

    table_counts = report['table_counts']
    print(f"\nTable Counts:")
    for table, count in table_counts.items():
        print(f"  {table}: {count}")

    schools_coverage = report['schools_coverage']
    if schools_coverage['total_schools'] > 0:
        print(f"\nSchools Coverage ({schools_coverage['total_schools']} total):")
        for field, data in schools_coverage['field_coverage'].items():
            print("20")

    if 'overall_metrics' in report:
        metrics = report['overall_metrics']
        print(f"\nOverall Metrics:")
        print(".2f")
        print(f"  Most complete field: {metrics['most_complete_field']}")
        print(f"  Least complete field: {metrics['least_complete_field']}")

    confidence_scores = report['confidence_scores']
    if confidence_scores:
        print(f"\nConfidence Scores:")
        for table, scores in confidence_scores.items():
            print(".4f")

    print(f"\nFull report saved to: {args.output}")


if __name__ == "__main__":
    main()
