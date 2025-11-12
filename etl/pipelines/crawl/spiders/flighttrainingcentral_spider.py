# Flight Training Central Directory Spider
#
# This spider crawls the Flight Training Central flight school directory
# which uses a location-based search interface to find schools.

import scrapy
from urllib.parse import urljoin, urlencode
from .base_spider import FlightSchoolBaseSpider


class FlightTrainingCentralSpider(FlightSchoolBaseSpider):
    """
    Spider for crawling the Flight Training Central flight school directory.

    This site provides a search-based interface for finding flight schools
    by location, with detailed school profiles.
    """

    name = 'flighttrainingcentral'
    allowed_domains = ['flighttrainingcentral.com']
    start_urls = ['https://flighttrainingcentral.com/flight-school-directory/']

    # US States for systematic crawling
    US_STATES = [
        'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado',
        'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho',
        'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana',
        'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota',
        'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada',
        'New Hampshire', 'New Jersey', 'New Mexico', 'New York',
        'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon',
        'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota',
        'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington',
        'West Virginia', 'Wisconsin', 'Wyoming'
    ]

    def parse_source_specific(self, response):
        """
        Parse the Flight Training Central directory page.

        This site uses a search form, so we need to:
        1. Store the main directory page
        2. Systematically search by state to get comprehensive coverage
        """
        # Store the main directory page
        yield self.store_raw_html(response)

        # Search by each state to get comprehensive coverage
        for state in self.US_STATES:
            search_url = self.build_search_url(state)
            yield scrapy.Request(
                url=search_url,
                callback=self.parse_search_results,
                meta={
                    'source': self.source_name,
                    'search_state': state
                }
            )

    def build_search_url(self, location: str) -> str:
        """
        Build a search URL for the Flight Training Central search form.

        Args:
            location: State name or location to search for

        Returns:
            Complete search URL
        """
        base_url = "https://flighttrainingcentral.com/flight-school-directory/"
        params = {
            's': location,
            'post_type': 'flight-school'
        }
        return f"{base_url}?{urlencode(params)}"

    def parse_search_results(self, response):
        """
        Parse search results page for a specific location/state.

        Extract school listing links and follow them to detail pages.
        """
        search_state = response.meta.get('search_state', 'Unknown')

        # Store the search results page
        yield self.store_raw_html(response)

        # Extract school detail links
        school_links = response.css(
            'a[href*="flight-school"][href*="/"]:not([href*="category"]):not([href*="tag"])::attr(href)'
        ).getall()

        self.logger.info(f"Found {len(school_links)} schools in {search_state}")

        for link in school_links:
            # Avoid duplicate links by checking if it's a detail page
            if '/flight-school/' in link and not link.endswith('/flight-school/'):
                full_url = urljoin(response.url, link)
                yield scrapy.Request(
                    url=full_url,
                    callback=self.parse_school_detail,
                    meta={
                        'source': self.source_name,
                        'search_state': search_state
                    }
                )

        # Check for pagination
        next_page = response.css('.pagination .next::attr(href), a[rel="next"]::attr(href)').get()
        if next_page:
            full_next_url = urljoin(response.url, next_page)
            yield scrapy.Request(
                url=full_next_url,
                callback=self.parse_search_results,
                meta={
                    'source': self.source_name,
                    'search_state': search_state
                }
            )

    def parse_school_detail(self, response):
        """
        Parse an individual flight school detail page.

        Extract comprehensive information about the school including
        contact details, services, and location information.
        """
        # Extract school information
        school_name = response.css('h1::text, .school-title::text').get()

        # Extract location information
        location_parts = response.css('.location::text, .address::text').getall()
        location = ' '.join(part.strip() for part in location_parts if part.strip())

        # Extract contact information
        phone = response.css('.phone::text, .contact-phone::text').get()
        email = response.css('.email::text, a[href^="mailto:"]::text').get()
        website = response.css('a[href^="http"]:not([href*="flighttrainingcentral"])::attr(href)').get()

        # Extract school type/categories
        categories = response.css('.category::text, .type::text').getall()

        search_state = response.meta.get('search_state')

        # Store the raw HTML
        yield self.store_raw_html(response)

        # Return structured data
        yield {
            'school_name': school_name,
            'location': location,
            'phone': phone,
            'email': email,
            'website': website,
            'categories': categories,
            'search_state': search_state,
            'url': response.url,
            'source': self.source_name,
            'crawl_timestamp': self.crawl_start_time.isoformat(),
        }
