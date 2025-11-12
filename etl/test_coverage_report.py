#!/usr/bin/env python3
"""
Test script for Coverage Report functionality
"""

import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

def test_coverage_report_mock():
    """Test coverage report with mocked database."""

    # Import after setting up path
    import sys
    sys.path.insert(0, str(Path(__file__).parent))

    from reports.coverage_report import CoverageReportGenerator

    print("Testing Coverage Report with mocked database...")

    # Mock database responses
    mock_results = {
        'schools_count': [(150,)],
        'programs_count': [(450,)],
        'pricing_count': [(120,)],
        'schools_field_coverage': [(120,), (135,), (110,), (140,), (100,)],  # Mock counts for various fields
        'programs_field_coverage': [(400,), (380,), (350,), (420,)],
        'pricing_field_coverage': [(100,), (95,), (120,)],
        'schools_confidence': [(0.85, 0.6, 0.95, 150)],
        'programs_confidence': [(0.82, 0.55, 0.92, 450)],
        'pricing_confidence': [(0.88, 0.7, 0.96, 120)]
    }

    def mock_execute_query(query, params=None):
        """Mock execute_query method."""
        if 'COUNT(*) FROM schools' in query:
            return mock_results['schools_count']
        elif 'COUNT(*) FROM programs' in query:
            return mock_results['programs_count']
        elif 'COUNT(*) FROM pricing' in query:
            return mock_results['pricing_count']
        elif 'schools WHERE' in query:
            # Return varying coverage for different fields
            return mock_results['schools_field_coverage'].pop(0) if mock_results['schools_field_coverage'] else [(0,)]
        elif 'programs WHERE' in query:
            return mock_results['programs_field_coverage'].pop(0) if mock_results['programs_field_coverage'] else [(0,)]
        elif 'pricing WHERE' in query:
            return mock_results['pricing_field_coverage'].pop(0) if mock_results['pricing_field_coverage'] else [(0,)]
        elif 'AVG(confidence)' in query and 'schools' in query:
            return mock_results['schools_confidence']
        elif 'AVG(confidence)' in query and 'programs' in query:
            return mock_results['programs_confidence']
        elif 'AVG(confidence)' in query and 'pricing' in query:
            return mock_results['pricing_confidence']
        else:
            return [(0,)]

    # Create generator and mock the database connection
    generator = CoverageReportGenerator()

    # Mock the database methods
    generator.connect = Mock()
    generator.disconnect = Mock()
    generator.execute_query = mock_execute_query
    generator.connection = True  # Simulate connected state

    # Generate report
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
        temp_path = temp_file.name

    try:
        report = generator.generate_report(temp_path)

        # Verify report structure
        assert 'report_metadata' in report
        assert 'table_counts' in report
        assert 'schools_coverage' in report
        assert 'programs_coverage' in report
        assert 'pricing_coverage' in report
        assert 'confidence_scores' in report

        # Verify table counts
        assert report['table_counts']['schools'] == 150
        assert report['table_counts']['programs'] == 450
        assert report['table_counts']['pricing'] == 120

        # Verify schools coverage
        schools_cov = report['schools_coverage']
        assert schools_cov['total_schools'] == 150
        assert 'field_coverage' in schools_cov

        # Verify confidence scores
        confidence = report['confidence_scores']
        assert 'schools' in confidence
        assert 'programs' in confidence
        assert 'pricing' in confidence

        schools_conf = confidence['schools']
        assert abs(schools_conf['mean_confidence'] - 0.85) < 0.01
        assert schools_conf['total_records'] == 150

        # Verify overall metrics are calculated
        assert 'overall_metrics' in report
        metrics = report['overall_metrics']
        assert 'average_field_completeness' in metrics
        assert 'most_complete_field' in metrics
        assert 'least_complete_field' in metrics

        # Verify JSON file was created and is valid
        assert os.path.exists(temp_path)
        with open(temp_path, 'r') as f:
            saved_report = json.load(f)

        assert saved_report == report

        print("[OK] All coverage report tests passed!")
        print(f"Report generated with {report['table_counts']['schools']} schools")
        print(f"Average field completeness: {report['overall_metrics']['average_field_completeness']}%")
        print(f"Most complete field: {report['overall_metrics']['most_complete_field']}")
        print(f"Report saved to: {temp_path}")

        return True

    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        return False
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)

if __name__ == "__main__":
    success = test_coverage_report_mock()
    exit(0 if success else 1)
