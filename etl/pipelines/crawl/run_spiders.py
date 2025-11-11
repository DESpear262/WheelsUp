#!/usr/bin/env python3
"""
Flight School Directory Crawler Runner

This script executes all configured flight school directory spiders
to collect raw HTML data from various aviation training resources.
Integrates with seed discovery results to crawl specific school URLs.

Usage:
    python run_spiders.py [--spider SPIDER_NAME] [--config CONFIG_FILE] [--seed-dir SEED_DIR]

Options:
    --spider SPIDER_NAME    Run only the specified spider
    --config CONFIG_FILE    Use custom config file (default: configs/sources.yaml)
    --seed-dir SEED_DIR     Directory with seed discovery results (default: etl/output)
"""

import sys
import os
import argparse
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml

# Add the spiders directory to Python path
spiders_path = Path(__file__).parent / 'spiders'
sys.path.insert(0, str(spiders_path))

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

# Import our spiders
from faa_flightschools_spider import FAAPilotSchoolsSpider
from drivedata_spider import DriveDataPilotSchoolsSpider
from flighttrainingcentral_spider import FlightTrainingCentralSpider
from aopa_spider import AOPAFlightSchoolsSpider
from faa_official_spider import FAAPilotSchoolsOfficialSpider

# Import utilities
from utils.s3_upload import FlightSchoolS3Uploader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FlightSchoolCrawlerProcess:
    """
    Manages the execution of flight school directory spiders.
    Integrates with seed discovery results for targeted crawling.
    """

    def __init__(self, config_file: str = 'configs/sources.yaml',
                 crawl_settings_file: str = 'configs/crawl_settings.yaml',
                 seed_dir: str = 'etl/output'):
        """
        Initialize the crawler process.

        Args:
            config_file: Path to the sources configuration file
            crawl_settings_file: Path to crawl settings configuration file
            seed_dir: Directory containing seed discovery results
        """
        self.project_root = Path(__file__).parent.parent.parent
        self.config_file = self.project_root / config_file
        self.crawl_settings_file = self.project_root / crawl_settings_file
        self.seed_dir = self.project_root / seed_dir

        self.sources_config = self.load_config()
        self.crawl_settings = self.load_crawl_settings()
        self.seed_results = self.load_seed_discovery_results()
        self.spiders = self.get_available_spiders()

        # Initialize S3 uploader with snapshot ID from seed discovery
        self.s3_uploader = None
        if self.crawl_settings.get('output', {}).get('s3_bucket'):
            snapshot_id = self.get_snapshot_id()
            if snapshot_id:
                self.s3_uploader = FlightSchoolS3Uploader(
                    bucket_name=self.crawl_settings['output']['s3_bucket'],
                    snapshot_id=snapshot_id
                )

    def load_config(self) -> Dict[str, Any]:
        """
        Load the sources configuration from YAML file.

        Returns:
            Configuration dictionary
        """
        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
                logger.info(f"Loaded sources configuration from {self.config_file}")
                return config
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_file}")
            sys.exit(1)
        except yaml.YAMLError as e:
            logger.error(f"Error parsing configuration file: {e}")
            sys.exit(1)

    def load_crawl_settings(self) -> Dict[str, Any]:
        """
        Load the crawl settings configuration from YAML file.

        Returns:
            Crawl settings dictionary
        """
        try:
            with open(self.crawl_settings_file, 'r') as f:
                settings = yaml.safe_load(f)
                logger.info(f"Loaded crawl settings from {self.crawl_settings_file}")
                return settings
        except FileNotFoundError:
            logger.warning(f"Crawl settings file not found: {self.crawl_settings_file}, using defaults")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing crawl settings file: {e}")
            return {}

    def load_seed_discovery_results(self) -> Dict[str, Any]:
        """
        Load seed discovery results from JSON files.

        Returns:
            Dictionary mapping source names to seed discovery results
        """
        seed_results = {}

        if not self.seed_dir.exists():
            logger.warning(f"Seed directory not found: {self.seed_dir}")
            return seed_results

        # Look for seed discovery files
        for json_file in self.seed_dir.glob("seed_discovery_*.json"):
            if "summary" not in json_file.name:  # Skip summary files
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        result = json.load(f)
                        source_name = result.get('source_name', 'unknown')
                        seed_results[source_name] = result
                        logger.info(f"Loaded seed results for {source_name} from {json_file.name}")
                except Exception as e:
                    logger.error(f"Error loading seed results from {json_file}: {e}")

        logger.info(f"Loaded seed discovery results for {len(seed_results)} sources")
        return seed_results

    def get_snapshot_id(self) -> Optional[str]:
        """
        Extract snapshot ID from seed discovery results.

        Returns:
            Snapshot ID string or None
        """
        # Look for snapshot ID in any seed result
        for result in self.seed_results.values():
            # Try to extract from discovery_timestamp or other fields
            timestamp = result.get('discovery_timestamp', '')
            if timestamp:
                # Extract date part for snapshot ID
                date_part = timestamp.split('T')[0].replace('-', '')
                return f"{date_part}_crawl"

        # Fallback: generate from current time
        from datetime import datetime
        return datetime.now().strftime('%Y%m%d_crawl')

    def get_available_spiders(self) -> Dict[str, scrapy.Spider]:
        """
        Get all available spider classes.

        Returns:
            Dictionary mapping spider names to spider classes
        """
        return {
            'faa_flightschools': FAAPilotSchoolsSpider,
            'drivedata_pilot_schools': DriveDataPilotSchoolsSpider,
            'flighttrainingcentral': FlightTrainingCentralSpider,
            'aopa_flight_schools': AOPAFlightSchoolsSpider,
            'faa_official_pilot_schools': FAAPilotSchoolsOfficialSpider,
        }

    def get_spider_config(self, spider_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific spider, enhanced with seed discovery data.

        Args:
            spider_name: Name of the spider

        Returns:
            Spider configuration dictionary with seed data
        """
        sources = self.sources_config.get('sources', [])
        for source in sources:
            if source['name'].lower().replace(' ', '_') == spider_name:
                # Enhance config with seed discovery results
                seed_data = self.seed_results.get(source['name'], {})
                if seed_data:
                    source['seed_schools'] = seed_data.get('discovered_schools', [])
                    source['snapshot_id'] = self.get_snapshot_id()
                    logger.info(f"Enhanced {spider_name} config with {len(source.get('seed_schools', []))} seed schools")
                return source

        logger.warning(f"No configuration found for spider: {spider_name}")
        return {}

    def should_use_playwright(self, spider_config: Dict[str, Any]) -> bool:
        """
        Determine if a spider should use Playwright based on configuration.

        Args:
            spider_config: Spider configuration dictionary

        Returns:
            True if Playwright should be used
        """
        crawl_method = spider_config.get('crawl_method', 'scrapy')
        return crawl_method == 'playwright'

    def run_spider(self, spider_name: str):
        """
        Run a single spider with enhanced configuration and method selection.

        Args:
            spider_name: Name of the spider to run
        """
        if spider_name not in self.spiders:
            logger.error(f"Unknown spider: {spider_name}")
            logger.info(f"Available spiders: {list(self.spiders.keys())}")
            return

        spider_config = self.get_spider_config(spider_name)

        # Check if we should use Playwright for this source
        if self.should_use_playwright(spider_config):
            logger.info(f"Running {spider_name} with Playwright")
            self.run_playwright_spider(spider_name, spider_config)
        else:
            logger.info(f"Running {spider_name} with Scrapy")
            self.run_scrapy_spider(spider_name, spider_config)

    def run_scrapy_spider(self, spider_name: str, spider_config: Dict[str, Any]):
        """
        Run a spider using Scrapy.

        Args:
            spider_name: Name of the spider
            spider_config: Spider configuration
        """
        spider_class = self.spiders[spider_name]

        # Get crawl settings
        crawl_settings = self.crawl_settings.get('crawl_settings', {})
        middleware_settings = self.crawl_settings.get('scrapy_middleware', {})

        # Create Scrapy settings from crawl configuration
        settings = Settings({
            'ROBOTSTXT_OBEY': crawl_settings.get('respect_robots_txt', True),
            'DOWNLOAD_DELAY': crawl_settings.get('crawl_delay', 2),
            'CONCURRENT_REQUESTS': crawl_settings.get('max_concurrent_requests', 1),
            'USER_AGENT': crawl_settings.get('user_agent'),
            'DOWNLOAD_TIMEOUT': crawl_settings.get('timeout', 30),
            'LOG_LEVEL': 'INFO',
            'FEEDS': {
                f"{self.crawl_settings.get('output', {}).get('local_output_dir', 'logs')}/{spider_name}_crawl_log.json": {
                    'format': 'json',
                    'fields': ['url', 'status', 'timestamp', 'error'],
                }
            },
        })

        # Configure custom middlewares
        if middleware_settings.get('flight_school_retry_middleware', {}).get('enabled', False):
            retry_config = middleware_settings['flight_school_retry_middleware']
            settings.set('FLIGHTSCHOOL_RETRY_ENABLED', True)
            settings.set('FLIGHTSCHOOL_MAX_RETRY_TIMES', retry_config.get('max_retry_times', 3))
            settings.set('FLIGHTSCHOOL_RETRY_HTTP_CODES', retry_config.get('retry_http_codes', [500, 502, 503, 504, 408, 429]))
            settings.set('FLIGHTSCHOOL_RETRY_DELAYS', retry_config.get('retry_delays', [1, 2, 4]))
            settings.set('FLIGHTSCHOOL_RETRY_PRIORITY_ADJUST', retry_config.get('priority_adjust', -1))

            # Disable default retry middleware to avoid conflicts
            settings.set('DOWNLOADER_MIDDLEWARES', {
                'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
                'etl.pipelines.crawl.middleware.FlightSchoolRetryMiddleware': 543,
            })

        if middleware_settings.get('flight_school_logging_middleware', {}).get('enabled', False):
            settings.set('SPIDER_MIDDLEWARES', {
                'etl.pipelines.crawl.middleware.FlightSchoolLoggingMiddleware': 542,
            })

        if middleware_settings.get('flight_school_rate_limit_middleware', {}).get('enabled', False):
            settings.set('DOWNLOADER_MIDDLEWARES', {
                **settings.get('DOWNLOADER_MIDDLEWARES', {}),
                'etl.pipelines.crawl.middleware.FlightSchoolRateLimitMiddleware': 541,
            })

        # Create and configure the crawler process
        process = CrawlerProcess(settings)

        # Add the spider with its configuration
        process.crawl(spider_class, source_config=spider_config, s3_uploader=self.s3_uploader)

        logger.info(f"Starting Scrapy spider: {spider_name}")
        process.start()

    def run_playwright_spider(self, spider_name: str, spider_config: Dict[str, Any]):
        """
        Run a spider using Playwright for JS-heavy sites.

        Args:
            spider_name: Name of the spider
            spider_config: Spider configuration
        """
        # Import Playwright handler
        from .playwright_handler import PlaywrightFlightSchoolCrawler

        playwright_settings = self.crawl_settings.get('playwright', {})

        # Run Playwright crawler asynchronously
        import asyncio

        async def run_async():
            async with PlaywrightFlightSchoolCrawler(
                headless=playwright_settings.get('headless', True),
                timeout=playwright_settings.get('browser_timeout', 30) * 1000  # Convert to ms
            ) as crawler:
                # Get seed URLs from configuration
                seed_schools = spider_config.get('seed_schools', [])
                urls_to_crawl = [school.get('source_url') for school in seed_schools if school.get('source_url')]

                if not urls_to_crawl:
                    logger.warning(f"No seed URLs found for {spider_name}, falling back to base URL")
                    urls_to_crawl = [spider_config.get('url')]

                results = []
                for url in urls_to_crawl:
                    try:
                        logger.info(f"Crawling {url} with Playwright")
                        result = await crawler.crawl_generic_js_site(url)
                        results.append(result)

                        # Upload to S3 if configured
                        if self.s3_uploader and result.get('content') and not result.get('error'):
                            upload_data = {
                                'source_name': spider_config.get('name', spider_name),
                                'url': url,
                                'filename': result.get('filename', f"{spider_name}_{hash(url)}.html"),
                                'content': result['content'],
                                'content_type': 'html',
                                'crawl_timestamp': result.get('crawl_timestamp'),
                            }
                            self.s3_uploader.upload_raw_html(upload_data)

                    except Exception as e:
                        logger.error(f"Error crawling {url} with Playwright: {e}")

                logger.info(f"Playwright crawling completed for {spider_name}: {len(results)} pages crawled")

        # Run the async function
        asyncio.run(run_async())

    def run_all_spiders(self):
        """
        Run all configured spiders sequentially, filtered by crawl method if enabled.
        """
        sources = self.sources_config.get('sources', [])
        integration_settings = self.crawl_settings.get('integration', {})

        for source in sources:
            spider_name = source['name'].lower().replace(' ', '_')

            # Check if spider implementation exists
            if spider_name not in self.spiders:
                logger.warning(f"No spider implementation found for: {spider_name}")
                continue

            # Check crawl method filtering
            if integration_settings.get('filter_by_crawl_method', False):
                supported_methods = integration_settings.get('supported_methods', ['scrapy'])
                crawl_method = source.get('crawl_method', 'scrapy')
                if crawl_method not in supported_methods:
                    logger.info(f"Skipping {spider_name} (crawl method {crawl_method} not supported)")
                    continue

            # Check if seed discovery is required but not available
            if integration_settings.get('use_seed_discovery', False):
                if source['name'] not in self.seed_results:
                    logger.warning(f"No seed discovery results found for {source['name']}, skipping")
                    continue

            logger.info(f"Running spider: {spider_name}")
            try:
                self.run_spider(spider_name)
            except Exception as e:
                logger.error(f"Error running spider {spider_name}: {e}")
                continue


def main():
    """
    Main entry point for the crawler.
    """
    parser = argparse.ArgumentParser(description='Flight School Directory Crawler')
    parser.add_argument(
        '--spider',
        type=str,
        help='Run only the specified spider'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='configs/sources.yaml',
        help='Sources configuration file path'
    )
    parser.add_argument(
        '--crawl-settings',
        type=str,
        default='configs/crawl_settings.yaml',
        help='Crawl settings configuration file path'
    )
    parser.add_argument(
        '--seed-dir',
        type=str,
        default='etl/output',
        help='Directory containing seed discovery results'
    )

    args = parser.parse_args()

    # Initialize the crawler
    crawler = FlightSchoolCrawlerProcess(
        config_file=args.config,
        crawl_settings_file=args.crawl_settings,
        seed_dir=args.seed_dir
    )

    if args.spider:
        # Run specific spider
        crawler.run_spider(args.spider)
    else:
        # Run all spiders
        crawler.run_all_spiders()


if __name__ == '__main__':
    main()
