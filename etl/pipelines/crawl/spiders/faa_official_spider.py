# Official FAA Pilot Schools Spider
#
# This spider crawls the official FAA pilot schools information page
# and follows links to related FAA resources and directories.

import scrapy
from urllib.parse import urljoin
from .base_spider import FlightSchoolBaseSpider


class FAAPilotSchoolsOfficialSpider(FlightSchoolBaseSpider):
    """
    Spider for crawling official FAA pilot schools information.

    This page provides official FAA guidance and links to other
    FAA-approved pilot school resources and directories.
    """

    name = 'faa_official_pilot_schools'
    allowed_domains = ['faa.gov']
    start_urls = [
        'https://www.faa.gov/training_testing/training/pilot_schools',
        'https://www.faa.gov/training_testing/schools',
    ]

    def parse_source_specific(self, response):
        """
        Parse the official FAA pilot schools information page.

        This page contains links to other FAA resources, approved schools,
        and aviation training information.
        """
        # Store the official page
        yield self.store_raw_html(response)

        # Extract links to external directories and resources
        external_links = response.css(
            'a[href^="http"]:not([href*="faa.gov"])::attr(href)'
        ).getall()

        # Extract FAA internal links that might lead to school data
        internal_links = response.css(
            'a[href*="/"][href*="school"], '
            'a[href*="/"][href*="training"], '
            'a[href*="/"][href*="certificate"]::attr(href)'
        ).getall()

        # Follow internal FAA links for more school information
        for link in internal_links:
            if link.startswith('/'):
                full_url = urljoin('https://www.faa.gov', link)
                yield scrapy.Request(
                    url=full_url,
                    callback=self.parse_faa_resource,
                    meta={'source': self.source_name}
                )

        # Log external directory links for reference
        for link in external_links:
            if self.is_aviation_directory_link(link):
                self.logger.info(f"Found external aviation directory: {link}")
                yield {
                    'url': link,
                    'source': self.source_name,
                    'link_type': 'external_directory',
                    'crawl_timestamp': self.crawl_start_time.isoformat(),
                }

    def parse_faa_resource(self, response):
        """
        Parse additional FAA resource pages.

        These may contain school listings, certification information,
        or links to approved training providers.
        """
        # Store the FAA resource page
        yield self.store_raw_html(response)

        # Look for school listings or contact information
        school_mentions = response.css(
            '[class*="school"], [id*="school"], '
            'table tr:has(td:contains("school")), '
            '.contact-info, .certification-info'
        )

        for mention in school_mentions:
            school_name = mention.css('::text').get()
            if school_name and len(school_name.strip()) > 3:
                yield {
                    'school_name': school_name.strip(),
                    'url': response.url,
                    'source': self.source_name,
                    'resource_type': 'faa_official',
                    'crawl_timestamp': self.crawl_start_time.isoformat(),
                }

        # Extract any downloadable resources
        download_links = response.css(
            'a[href$=".pdf"], a[href$=".xls"], a[href$=".xlsx"]::attr(href)'
        ).getall()

        for link in download_links:
            full_url = urljoin(response.url, link)
            yield scrapy.Request(
                url=full_url,
                callback=self.parse_faa_download,
                meta={'source': self.source_name}
            )

    def parse_faa_download(self, response):
        """
        Parse downloadable FAA resources.

        These might include official school listings, certification data,
        or training provider information.
        """
        # Store the download
        yield self.store_raw_html(response)

        yield {
            'url': response.url,
            'filename': response.url.split('/')[-1],
            'source': self.source_name,
            'resource_type': 'faa_download',
            'crawl_timestamp': self.crawl_start_time.isoformat(),
        }

    def is_aviation_directory_link(self, url: str) -> bool:
        """
        Determine if a URL points to an aviation directory or school listing.

        Args:
            url: URL to check

        Returns:
            True if the URL appears to be an aviation directory
        """
        url_lower = url.lower()
        directory_indicators = [
            'directory', 'schools', 'training', 'aviation',
            'pilot', 'flight', 'faa', 'aopa'
        ]

        return any(indicator in url_lower for indicator in directory_indicators)
