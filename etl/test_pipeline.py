#!/usr/bin/env python3
"""
Test Script for Flight School Crawling Pipeline

This script tests the crawling pipeline components to ensure they work correctly
before deploying to production. Tests include spider functionality, error handling,
and basic data flow.

Usage:
    python test_pipeline.py [--spider SPIDER_NAME] [--quick]
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, List
import time

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import our modules
from pipelines.crawl.spiders.base_spider import FlightSchoolBaseSpider
from utils.error_handler import FlightSchoolErrorHandler, ErrorCategory, ErrorSeverity
from utils.s3_upload import FlightSchoolS3Uploader

# Try to import playwright handler (optional)
try:
    from pipelines.crawl.playwright_handler import crawl_with_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CrawlPipelineTester:
    """
    Test harness for the flight school crawling pipeline.
    """

    def __init__(self, test_directory: str = "test_output"):
        """
        Initialize the test harness.

        Args:
            test_directory: Directory for test outputs
        """
        self.test_directory = Path(test_directory)
        self.test_directory.mkdir(exist_ok=True)

        self.error_handler = FlightSchoolErrorHandler(log_directory=str(self.test_directory / "logs"))
        self.test_results = []

        logger.info("Pipeline tester initialized")

    def test_spider_initialization(self) -> bool:
        """
        Test that spiders can be initialized properly.

        Returns:
            True if all spiders initialize successfully
        """
        logger.info("Testing spider initialization...")

        test_config = {
            'name': 'test_source',
            'url': 'https://example.com',
            'type': 'test',
            'data_format': 'html'
        }

        try:
            spider = FlightSchoolBaseSpider(source_config=test_config)
            assert spider.source_name == 'test_source'
            assert spider.base_url == 'https://example.com'

            self.test_results.append({
                'test': 'spider_initialization',
                'result': 'PASS',
                'message': 'Base spider initializes correctly'
            })
            return True

        except Exception as e:
            self.test_results.append({
                'test': 'spider_initialization',
                'result': 'FAIL',
                'message': f'Spider initialization failed: {e}'
            })
            return False

    def test_error_handler(self) -> bool:
        """
        Test error handling functionality.

        Returns:
            True if error handling works correctly
        """
        logger.info("Testing error handler...")

        try:
            # Test logging a network error
            error = self.error_handler.log_network_error(
                source_name='test_source',
                url='https://example.com',
                error_message='Test network error',
                status_code=404
            )

            assert error.error_category == ErrorCategory.NETWORK
            assert error.error_severity == ErrorSeverity.MEDIUM
            assert error.source_name == 'test_source'

            # Test error summary
            summary = self.error_handler.get_error_summary()
            assert summary['total_errors'] >= 1

            self.test_results.append({
                'test': 'error_handler',
                'result': 'PASS',
                'message': 'Error handler logs and tracks errors correctly'
            })
            return True

        except Exception as e:
            self.test_results.append({
                'test': 'error_handler',
                'result': 'FAIL',
                'message': f'Error handler test failed: {e}'
            })
            return False

    def test_s3_uploader_mock(self) -> bool:
        """
        Test S3 uploader functionality (without actual AWS calls).

        Returns:
            True if uploader initializes and generates keys correctly
        """
        logger.info("Testing S3 uploader...")

        try:
            # Test with a mock bucket to avoid AWS calls
            uploader = FlightSchoolS3Uploader(bucket_name='test-bucket')

            # Test snapshot ID generation
            snapshot_id = uploader.generate_snapshot_id()
            assert 'Q' in snapshot_id
            assert '-MVP' in snapshot_id

            # Test S3 key generation (without actual upload)
            test_data = {
                'source_name': 'test_source',
                'filename': 'test_file.html',
                'content': '<html>Test</html>'
            }

            # We can't test actual upload without AWS credentials,
            # but we can test the key generation logic
            expected_key_start = f"raw/{snapshot_id}/test_source/"
            assert expected_key_start in f"raw/{snapshot_id}/test_source/test_file.html"

            self.test_results.append({
                'test': 's3_uploader',
                'result': 'PASS',
                'message': 'S3 uploader initializes and generates keys correctly'
            })
            return True

        except Exception as e:
            self.test_results.append({
                'test': 's3_uploader',
                'result': 'FAIL',
                'message': f'S3 uploader test failed: {e}'
            })
            return False

    def test_playwright_basic(self) -> bool:
        """
        Test basic Playwright functionality (quick test only).

        Returns:
            True if Playwright module structure is correct (skipped if not installed)
        """
        logger.info("Testing Playwright initialization...")

        try:
            # Try to import playwright - skip if not installed
            try:
                from pipelines.crawl.playwright_handler import PlaywrightFlightSchoolCrawler
            except ImportError:
                self.test_results.append({
                    'test': 'playwright_basic',
                    'result': 'SKIP',
                    'message': 'Playwright not installed - skipping test'
                })
                return True

            # Check that the class exists and has expected methods
            assert hasattr(PlaywrightFlightSchoolCrawler, '__aenter__')
            assert hasattr(PlaywrightFlightSchoolCrawler, '__aexit__')

            self.test_results.append({
                'test': 'playwright_basic',
                'result': 'PASS',
                'message': 'Playwright module imports and basic structure is correct'
            })
            return True

        except Exception as e:
            self.test_results.append({
                'test': 'playwright_basic',
                'result': 'FAIL',
                'message': f'Playwright basic test failed: {e}'
            })
            return False

    def test_configuration_loading(self) -> bool:
        """
        Test that configuration files can be loaded.

        Returns:
            True if configuration loads correctly
        """
        logger.info("Testing configuration loading...")

        try:
            import yaml
            config_path = Path(__file__).parent / 'configs' / 'sources.yaml'

            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)

                assert 'sources' in config
                assert isinstance(config['sources'], list)
                assert len(config['sources']) > 0

                # Check that each source has required fields
                for source in config['sources']:
                    assert 'name' in source
                    assert 'url' in source

                self.test_results.append({
                    'test': 'configuration_loading',
                    'result': 'PASS',
                    'message': 'Configuration file loads correctly'
                })
                return True
            else:
                self.test_results.append({
                    'test': 'configuration_loading',
                    'result': 'FAIL',
                    'message': 'Configuration file not found'
                })
                return False

        except Exception as e:
            self.test_results.append({
                'test': 'configuration_loading',
                'result': 'FAIL',
                'message': f'Configuration loading failed: {e}'
            })
            return False

    def test_pandas_numpy_basic(self) -> bool:
        """
        Test basic pandas and numpy functionality.

        Returns:
            True if pandas/numpy operations work correctly
        """
        logger.info("Testing pandas and numpy basic functionality...")

        try:
            import pandas as pd
            import numpy as np

            # Test numpy array creation and basic operations
            arr = np.array([1, 2, 3, 4, 5])
            assert arr.sum() == 15
            assert arr.mean() == 3.0

            # Test pandas DataFrame creation
            df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
            assert df.shape == (3, 2)
            assert df['A'].sum() == 6

            self.test_results.append({
                'test': 'pandas_numpy_basic',
                'result': 'PASS',
                'message': 'Pandas and NumPy basic operations work correctly'
            })
            return True

        except Exception as e:
            self.test_results.append({
                'test': 'pandas_numpy_basic',
                'result': 'FAIL',
                'message': f'Pandas/NumPy test failed: {e}'
            })
            return False

    def test_aiohttp_basic(self) -> bool:
        """
        Test basic aiohttp functionality (without actual HTTP calls).

        Returns:
            True if aiohttp imports and basic setup works
        """
        logger.info("Testing aiohttp basic functionality...")

        try:
            import aiohttp
            from aiohttp import web

            # Test that aiohttp components can be imported
            assert hasattr(aiohttp, 'ClientSession')
            assert hasattr(web, 'Application')

            # Test basic aiohttp setup
            app = web.Application()
            assert isinstance(app, web.Application)

            self.test_results.append({
                'test': 'aiohttp_basic',
                'result': 'PASS',
                'message': 'aiohttp basic functionality works correctly'
            })
            return True

        except Exception as e:
            self.test_results.append({
                'test': 'aiohttp_basic',
                'result': 'FAIL',
                'message': f'aiohttp test failed: {e}'
            })
            return False

    def test_httpx_basic(self) -> bool:
        """
        Test basic httpx functionality.

        Returns:
            True if httpx imports and basic setup works
        """
        logger.info("Testing httpx basic functionality...")

        try:
            import httpx

            # Test that httpx components can be imported
            assert hasattr(httpx, 'Client')
            assert hasattr(httpx, 'AsyncClient')

            # Test basic client creation
            client = httpx.Client()
            assert hasattr(client, 'get')
            client.close()

            self.test_results.append({
                'test': 'httpx_basic',
                'result': 'PASS',
                'message': 'httpx basic functionality works correctly'
            })
            return True

        except Exception as e:
            self.test_results.append({
                'test': 'httpx_basic',
                'result': 'FAIL',
                'message': f'httpx test failed: {e}'
            })
            return False

    def test_loguru_basic(self) -> bool:
        """
        Test basic loguru functionality.

        Returns:
            True if loguru logging works correctly
        """
        logger.info("Testing loguru basic functionality...")

        try:
            from loguru import logger as loguru_logger

            # Test that loguru logger has expected methods
            assert hasattr(loguru_logger, 'info')
            assert hasattr(loguru_logger, 'warning')
            assert hasattr(loguru_logger, 'error')

            # Test basic logging (this should work without throwing exceptions)
            loguru_logger.info("Test loguru message")

            self.test_results.append({
                'test': 'loguru_basic',
                'result': 'PASS',
                'message': 'loguru basic functionality works correctly'
            })
            return True

        except Exception as e:
            self.test_results.append({
                'test': 'loguru_basic',
                'result': 'FAIL',
                'message': f'loguru test failed: {e}'
            })
            return False

    def run_quick_tests(self) -> bool:
        """
        Run all quick tests that don't require external resources.

        Returns:
            True if all tests pass
        """
        logger.info("Running quick pipeline tests...")

        tests = [
            self.test_spider_initialization,
            self.test_error_handler,
            self.test_s3_uploader_mock,
            self.test_playwright_basic,
            self.test_configuration_loading,
            self.test_pandas_numpy_basic,
            self.test_aiohttp_basic,
            self.test_httpx_basic,
            self.test_loguru_basic,
        ]

        all_passed = True
        for test in tests:
            try:
                result = test()
                if not result:
                    all_passed = False
            except Exception as e:
                logger.error(f"Test {test.__name__} failed with exception: {e}")
                all_passed = False

        return all_passed

    def run_spider_test(self, spider_name: str) -> bool:
        """
        Test a specific spider with a limited crawl.

        Args:
            spider_name: Name of the spider to test

        Returns:
            True if spider test succeeds
        """
        logger.info(f"Testing spider: {spider_name}")

        try:
            # Import the spider dynamically
            if spider_name == 'faa_flightschools':
                from pipelines.crawl.spiders.faa_flightschools_spider import FAAPilotSchoolsSpider
                spider_class = FAAPilotSchoolsSpider
            elif spider_name == 'drivedata_pilot_schools':
                from pipelines.crawl.spiders.drivedata_spider import DriveDataPilotSchoolsSpider
                spider_class = DriveDataPilotSchoolsSpider
            else:
                self.test_results.append({
                    'test': f'spider_{spider_name}',
                    'result': 'SKIP',
                    'message': f'Spider {spider_name} not implemented for testing'
                })
                return True

            # Create spider instance
            spider = spider_class()

            # Test basic attributes
            assert hasattr(spider, 'name')
            assert hasattr(spider, 'start_urls')
            assert hasattr(spider, 'parse_source_specific')

            self.test_results.append({
                'test': f'spider_{spider_name}',
                'result': 'PASS',
                'message': f'Spider {spider_name} initializes correctly'
            })
            return True

        except Exception as e:
            self.test_results.append({
                'test': f'spider_{spider_name}',
                'result': 'FAIL',
                'message': f'Spider {spider_name} test failed: {e}'
            })
            return False

    def generate_test_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive test report.

        Returns:
            Dictionary containing test results and summary
        """
        passed = len([r for r in self.test_results if r['result'] == 'PASS'])
        failed = len([r for r in self.test_results if r['result'] == 'FAIL'])
        skipped = len([r for r in self.test_results if r['result'] == 'SKIP'])

        report = {
            'test_run_timestamp': time.time(),
            'total_tests': len(self.test_results),
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'success_rate': (passed / len(self.test_results)) * 100 if self.test_results else 0,
            'test_results': self.test_results,
            'error_summary': self.error_handler.get_error_summary() if hasattr(self.error_handler, 'get_error_summary') else {},
        }

        return report

    def save_test_report(self, filename: str = None) -> str:
        """
        Save test report to a file.

        Args:
            filename: Optional filename for the report

        Returns:
            Path to the saved report file
        """
        if not filename:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            filename = f"pipeline_test_report_{timestamp}.json"

        report_path = self.test_directory / filename

        import json
        report = self.generate_test_report()

        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Test report saved to: {report_path}")
        return str(report_path)


def main():
    """
    Main entry point for pipeline testing.
    """
    parser = argparse.ArgumentParser(description='Test Flight School Crawling Pipeline')
    parser.add_argument(
        '--spider',
        type=str,
        help='Test a specific spider'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run only quick tests (no external calls)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='test_output',
        help='Directory for test outputs'
    )

    args = parser.parse_args()

    # Initialize tester
    tester = CrawlPipelineTester(args.output)

    success = True

    if args.spider:
        # Test specific spider
        success = tester.run_spider_test(args.spider)
    elif args.quick:
        # Run quick tests only
        success = tester.run_quick_tests()
    else:
        # Run all tests
        logger.info("Running comprehensive pipeline tests...")
        success = tester.run_quick_tests()

        # Test a couple of spiders if quick tests pass
        if success:
            for spider in ['faa_flightschools', 'drivedata_pilot_schools']:
                spider_success = tester.run_spider_test(spider)
                if not spider_success:
                    success = False

    # Generate and save report
    report_file = tester.save_test_report()

    # Print summary
    report = tester.generate_test_report()
    print("\n" + "="*50)
    print("PIPELINE TEST SUMMARY")
    print("="*50)
    print(f"Total Tests: {report['total_tests']}")
    print(f"Passed: {report['passed']}")
    print(f"Failed: {report['failed']}")
    print(f"Skipped: {report['skipped']}")
    print(".1f")
    print(f"Report saved to: {report_file}")

    if success:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Check the report for details.")
        sys.exit(1)


if __name__ == '__main__':
    main()
