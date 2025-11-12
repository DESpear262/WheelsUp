# FAA Flight Schools Directory Spider
#
# This spider crawls the FAA Flight Schools directory at faaflightschools.com
# which contains listings for 1200+ flight schools across all US states.

import scrapy
from urllib.parse import urljoin
from .base_spider import FlightSchoolBaseSpider


class FAAPilotSchoolsSpider(FlightSchoolBaseSpider):
    """
    Spider for crawling the FAA Flight Schools directory.

    This directory contains comprehensive listings of flight schools
    organized by state, with detailed information for each school.
    """

    name = 'faa_flightschools'
    allowed_domains = ['faaflightschools.com']
    start_urls = ['https://www.faaflightschools.com/']

    def parse_source_specific(self, response):
        """
        Parse the FAA Flight Schools directory structure.

        This site organizes schools by state, so we need to:
        1. Extract state links from the main page
        2. Follow each state link to get school listings
        3. Extract individual school pages
        """
        # Extract state links from the main page
        state_links = response.css('a[href*="aviation-"][href*="-flight-schools.php"]::attr(href)').getall()

        for state_link in state_links:
            full_url = urljoin(response.url, state_link)
            yield scrapy.Request(
                url=full_url,
                callback=self.parse_state_page,
                meta={'source': self.source_name}
            )

    def parse_state_page(self, response):
        """
        Parse a state-specific flight schools page.

        Each state page contains a list of schools in that state.
        We extract school detail page links and follow them.
        """
        # Extract school detail links
        school_links = response.css('a[href*="school-details.php"]::attr(href)').getall()

        for school_link in school_links:
            full_url = urljoin(response.url, school_link)
            yield scrapy.Request(
                url=full_url,
                callback=self.parse_school_detail,
                meta={'source': self.source_name}
            )

        # Also store the state listing page itself
        yield self.store_raw_html(response)

    def parse_school_detail(self, response):
        """
        Parse an individual school detail page.

        These pages contain comprehensive information about each flight school
        including contact info, services, ratings, etc.
        """
        # Extract basic school information for logging
        school_name = response.css('h1::text, .school-name::text, title::text').get()
        location = response.css('.location::text, .address::text').first()

        # Log the school found
        self.logger.info(f"Found school: {school_name} at {location.get() if location else 'Unknown'}")

        # Store the raw HTML and return structured data
        yield self.store_raw_html(response)

        yield {
            'school_name': school_name,
            'url': response.url,
            'source': self.source_name,
            'crawl_timestamp': self.crawl_start_time.isoformat(),
            'location': location.get() if location else None,
        }
