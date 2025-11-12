# Drive Data FAA Part 141 Flight Schools Spider
#
# This spider crawls the Drive Data FAA Part 141 certified flight schools directory
# at drivedata.org/pilot-schools, which provides structured data about certified schools.

import scrapy
import json
from urllib.parse import urljoin, urlparse, parse_qs
from .base_spider import FlightSchoolBaseSpider


class DriveDataPilotSchoolsSpider(FlightSchoolBaseSpider):
    """
    Spider for crawling the Drive Data FAA Part 141 certified flight schools directory.

    This site provides structured data about officially certified flight schools
    with filtering and search capabilities.
    """

    name = 'drivedata_pilot_schools'
    allowed_domains = ['drivedata.org']
    start_urls = ['https://www.drivedata.org/pilot-schools']

    def parse_source_specific(self, response):
        """
        Parse the Drive Data pilot schools directory.

        This site uses a filterable table format. We need to:
        1. Extract the main directory page
        2. Handle pagination if present
        3. Extract school detail links
        """
        # Store the main directory page
        yield self.store_raw_html(response)

        # Look for school listing links or API endpoints
        school_links = response.css('a[href*="school"][href*="detail"]::attr(href)').getall()
        api_links = response.css('a[href*="api"][href*="school"]::attr(href)').getall()

        # Follow school detail links
        for link in school_links:
            full_url = urljoin(response.url, link)
            yield scrapy.Request(
                url=full_url,
                callback=self.parse_school_detail,
                meta={'source': self.source_name}
            )

        # If no direct links, try to extract from JavaScript data or tables
        if not school_links:
            yield from self.parse_table_data(response)

        # Check for pagination
        next_page = response.css('a[rel="next"]::attr(href), .pagination .next::attr(href)').get()
        if next_page:
            full_next_url = urljoin(response.url, next_page)
            yield scrapy.Request(
                url=full_next_url,
                callback=self.parse_source_specific,
                meta={'source': self.source_name}
            )

    def parse_table_data(self, response):
        """
        Parse school data from HTML tables or structured data.

        Some directories embed school data in tables or JSON-LD.
        """
        # Try to extract structured data from tables
        rows = response.css('table tr, .school-listing, .school-item')

        for row in rows:
            school_name = row.css('td:first-child::text, .name::text, h3::text').get()
            location = row.css('.location::text, .state::text').get()
            link = row.css('a::attr(href)').get()

            if school_name and link:
                full_url = urljoin(response.url, link)
                yield scrapy.Request(
                    url=full_url,
                    callback=self.parse_school_detail,
                    meta={
                        'source': self.source_name,
                        'school_name': school_name.strip(),
                        'location': location.strip() if location else None
                    }
                )

        # Try to extract JSON-LD structured data
        json_ld = response.css('script[type="application/ld+json"]::text').getall()
        for script in json_ld:
            try:
                data = json.loads(script)
                if isinstance(data, list):
                    for item in data:
                        if item.get('@type') == 'EducationalOrganization':
                            yield {
                                'school_name': item.get('name'),
                                'url': item.get('url', response.url),
                                'source': self.source_name,
                                'structured_data': item,
                            }
                elif data.get('@type') == 'EducationalOrganization':
                    yield {
                        'school_name': data.get('name'),
                        'url': data.get('url', response.url),
                        'source': self.source_name,
                        'structured_data': data,
                    }
            except json.JSONDecodeError:
                continue

    def parse_school_detail(self, response):
        """
        Parse an individual school detail page from Drive Data.

        These pages contain detailed information about FAA Part 141 certified schools.
        """
        # Extract school information
        school_name = (
            response.css('h1::text, .school-name::text, .title::text').get() or
            response.meta.get('school_name')
        )

        # Extract various data points that might be available
        certificate_number = response.css('[data-cert], .certificate::text').get()
        location = (
            response.css('.location::text, .address::text').get() or
            response.meta.get('location')
        )

        # Store the raw HTML
        yield self.store_raw_html(response)

        # Return structured data
        yield {
            'school_name': school_name,
            'certificate_number': certificate_number,
            'location': location,
            'url': response.url,
            'source': self.source_name,
            'certification_type': 'FAA Part 141',
            'crawl_timestamp': self.crawl_start_time.isoformat(),
        }
