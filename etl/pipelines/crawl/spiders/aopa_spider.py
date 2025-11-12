# AOPA Flight School Resources Spider
#
# This spider crawls AOPA (Aircraft Owners and Pilots Association) resources
# for flight school information and directories.

import scrapy
from urllib.parse import urljoin
from .base_spider import FlightSchoolBaseSpider


class AOPAFlightSchoolsSpider(FlightSchoolBaseSpider):
    """
    Spider for crawling AOPA flight school resources.

    AOPA provides various aviation resources including flight school
    directories, safety information, and pilot training resources.
    """

    name = 'aopa_flight_schools'
    allowed_domains = ['aopa.org', 'download.aopa.org']
    start_urls = [
        'https://www.aopa.org/training-and-safety',
        'https://download.aopa.org/',
    ]

    def parse_source_specific(self, response):
        """
        Parse AOPA training and safety pages for flight school resources.

        AOPA provides various resources that may link to flight school directories
        and training information.
        """
        # Store the main page
        yield self.store_raw_html(response)

        # Look for flight school related links
        flight_school_links = response.css(
            'a[href*="flight"][href*="school"], '
            'a[href*="training"], '
            'a[href*="pilot"]::attr(href)'
        ).getall()

        for link in flight_school_links:
            if self.is_relevant_link(link):
                full_url = urljoin(response.url, link)
                yield scrapy.Request(
                    url=full_url,
                    callback=self.parse_resource_page,
                    meta={'source': self.source_name}
                )

        # Look for download links that might contain directories
        download_links = response.css('a[href*="download"], a[href*=".pdf"], a[href*=".xls"]::attr(href)').getall()
        for link in download_links:
            full_url = urljoin(response.url, link)
            if 'flight' in full_url.lower() or 'school' in full_url.lower() or 'training' in full_url.lower():
                yield scrapy.Request(
                    url=full_url,
                    callback=self.parse_download,
                    meta={'source': self.source_name}
                )

    def parse_resource_page(self, response):
        """
        Parse AOPA resource pages that contain flight school information.
        """
        # Store the resource page
        yield self.store_raw_html(response)

        # Extract any embedded school information
        school_listings = response.css('.school-listing, .training-center, .flight-school')

        for listing in school_listings:
            school_name = listing.css('h3::text, .name::text').get()
            contact_info = listing.css('.contact::text, .phone::text').get()

            if school_name:
                yield {
                    'school_name': school_name,
                    'contact_info': contact_info,
                    'url': response.url,
                    'source': self.source_name,
                    'resource_type': 'aopa_listing',
                    'crawl_timestamp': self.crawl_start_time.isoformat(),
                }

        # Follow additional resource links
        resource_links = response.css('a[href*="resource"], a[href*="guide"]::attr(href)').getall()
        for link in resource_links:
            full_url = urljoin(response.url, link)
            yield scrapy.Request(
                url=full_url,
                callback=self.parse_resource_page,
                meta={'source': self.source_name}
            )

    def parse_download(self, response):
        """
        Parse downloadable resources from AOPA.

        These might include PDFs, spreadsheets, or other documents
        containing flight school information.
        """
        # Store the download content
        yield self.store_raw_html(response)

        # Check if this is a directory or listing document
        content_type = response.headers.get('Content-Type', b'').decode('utf-8', errors='ignore')

        yield {
            'url': response.url,
            'content_type': content_type,
            'filename': response.url.split('/')[-1],
            'source': self.source_name,
            'resource_type': 'download',
            'crawl_timestamp': self.crawl_start_time.isoformat(),
        }

    def is_relevant_link(self, link: str) -> bool:
        """
        Determine if a link is relevant for flight school crawling.

        Args:
            link: URL to check

        Returns:
            True if the link appears relevant for flight school data
        """
        link_lower = link.lower()
        relevant_terms = [
            'flight', 'school', 'training', 'pilot', 'aviation',
            'certificate', 'rating', 'academy', 'college'
        ]

        return any(term in link_lower for term in relevant_terms)
