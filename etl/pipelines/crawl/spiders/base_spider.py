# Base Spider for Flight School Directory Crawling
#
# This module provides a base Scrapy spider class with common functionality
# for crawling flight school directories while respecting robots.txt and
# implementing proper error handling and logging.

import scrapy
import logging
from datetime import datetime
import hashlib
import os
from typing import Dict, Any, Optional
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FlightSchoolBaseSpider(scrapy.Spider):
    """
    Base spider class for crawling flight school directories.

    Provides common functionality for:
    - Configuration loading
    - Robots.txt compliance
    - Error logging
    - S3 upload integration
    - Request throttling
    """

    name = 'flight_school_base'  # Default name for base class

    # Default settings that can be overridden by subclasses
    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 2,  # 2 second delay between requests
        'CONCURRENT_REQUESTS': 1,  # Only 1 concurrent request to be respectful
        'USER_AGENT': 'WheelsUp-Flight-School-Directory-Crawler/1.0 (Educational Research Project)',
        'FEEDS': {
            'logs/crawl_log.json': {
                'format': 'json',
                'fields': ['url', 'status', 'timestamp', 'error'],
            }
        }
    }

    def __init__(self, source_config: Optional[Dict[str, Any]] = None, s3_uploader=None, *args, **kwargs):
        """
        Initialize the spider with source configuration.

        Args:
            source_config: Dictionary containing source configuration from sources.yaml
            s3_uploader: S3 uploader instance for storing crawled data
        """
        super().__init__(*args, **kwargs)

        # Load source configuration
        if source_config:
            self.source_config = source_config
        else:
            # Load from config file if not provided
            config_path = os.path.join(os.path.dirname(__file__), '../../../configs/sources.yaml')
            with open(config_path, 'r') as f:
                sources = yaml.safe_load(f)
                # Find this spider's source config by name
                self.source_config = next(
                    (s for s in sources['sources'] if s['name'] == self.name),
                    {}
                )

        # Set spider attributes from config
        self.source_name = self.source_config.get('name', self.name)
        self.base_url = self.source_config.get('url', '')
        self.data_format = self.source_config.get('data_format', 'html')

        # Initialize S3 uploader
        self.s3_uploader = s3_uploader

        # Initialize crawl tracking
        self.crawl_start_time = datetime.now()
        self.pages_crawled = 0
        self.errors_encountered = 0

        logger.info(f"Initialized spider: {self.source_name} for URL: {self.base_url}")

    def start_requests(self):
        """
        Generate initial requests for the spider.

        Uses seed discovery results if available, otherwise falls back to base URL.
        """
        # Check if we have seed schools from discovery
        seed_schools = self.source_config.get('seed_schools', [])

        if seed_schools:
            # Use seed URLs for targeted crawling
            logger.info(f"Using {len(seed_schools)} seed URLs for {self.source_name}")
            for school in seed_schools:
                school_url = school.get('source_url')
                if school_url:
                    yield scrapy.Request(
                        url=school_url,
                        callback=self.parse_school_page,
                        meta={
                            'source': self.source_name,
                            'school_data': school
                        }
                    )
        else:
            # Fall back to base URL crawling
            logger.info(f"No seed URLs found, using base URL crawling for {self.source_name}")
            if self.base_url:
                yield scrapy.Request(
                    url=self.base_url,
                    callback=self.parse,
                    meta={'source': self.source_name}
                )

    def parse_school_page(self, response):
        """
        Parse a specific school page from seed discovery.

        Args:
            response: Scrapy response object
        """
        # Store the raw HTML content
        yield self.store_raw_html(response)

        # Extract school-specific data
        school_data = response.meta.get('school_data', {})
        school_info = {
            'url': response.url,
            'title': response.css('title::text').get(),
            'source': self.source_name,
            'crawl_timestamp': datetime.now().isoformat(),
            'school_data': school_data,
        }

        yield school_info

    def parse(self, response):
        """
        Default parse method. Should be overridden by subclasses.

        This method handles the basic response processing and
        delegates to subclasses for specific parsing logic.
        """
        self.pages_crawled += 1

        # Log successful crawl
        self.log_crawl_result(response.url, 'success')

        # Store raw HTML in S3 (to be implemented)
        yield self.store_raw_html(response)

        # Allow subclasses to extract additional data
        yield from self.parse_source_specific(response)

    def parse_source_specific(self, response):
        """
        Source-specific parsing logic. Should be overridden by subclasses.

        Args:
            response: Scrapy response object

        Yields:
            Parsed items or additional requests
        """
        # Default implementation - just yield the response for storage
        yield {
            'url': response.url,
            'title': response.css('title::text').get(),
            'source': self.source_name,
            'crawl_timestamp': datetime.now().isoformat(),
        }

    def store_raw_html(self, response):
        """
        Store raw HTML content for later processing.

        Args:
            response: Scrapy response object

        Returns:
            Dictionary with storage metadata
        """
        # Generate unique filename based on URL and timestamp
        url_hash = hashlib.md5(response.url.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.source_name.replace(' ', '_').lower()}_{url_hash}_{timestamp}.html"

        # Prepare upload data
        upload_data = {
            'source_name': self.source_name,
            'url': response.url,
            'filename': filename,
            'content': response.text,
            'content_type': 'html',
            'crawl_timestamp': datetime.now().isoformat(),
            'status_code': response.status,
        }

        # Upload to S3 if uploader is available
        if self.s3_uploader:
            try:
                success = self.s3_uploader.upload_raw_html(upload_data)
                if success:
                    logger.info(f"Uploaded {filename} to S3")
                    upload_data['s3_uploaded'] = True
                else:
                    logger.warning(f"Failed to upload {filename} to S3")
                    upload_data['s3_uploaded'] = False
            except Exception as e:
                logger.error(f"S3 upload error for {filename}: {e}")
                upload_data['s3_uploaded'] = False
                upload_data['s3_error'] = str(e)
        else:
            upload_data['s3_uploaded'] = False

        return upload_data

    def log_crawl_result(self, url: str, status: str, error: Optional[str] = None):
        """
        Log the result of a crawl attempt.

        Args:
            url: URL that was crawled
            status: 'success' or 'error'
            error: Error message if applicable
        """
        if status == 'success':
            logger.info(f"Successfully crawled: {url}")
        else:
            self.errors_encountered += 1
            logger.error(f"Failed to crawl {url}: {error}")

    def closed(self, reason):
        """
        Called when the spider is closed. Log final statistics.
        """
        duration = datetime.now() - self.crawl_start_time
        logger.info(
            f"Spider {self.source_name} closed. "
            f"Reason: {reason}. "
            f"Pages crawled: {self.pages_crawled}. "
            f"Errors: {self.errors_encountered}. "
            f"Duration: {duration}"
        )
