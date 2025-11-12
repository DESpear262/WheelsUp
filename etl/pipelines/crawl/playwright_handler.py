# Playwright Handler for JS-Heavy Flight School Sites
#
# This module provides Playwright-based crawling capabilities for flight school
# directories that require JavaScript execution to load content or interact
# with search forms.

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
import os
from pathlib import Path

from playwright.async_api import async_playwright, Browser, Page, BrowserContext

logger = logging.getLogger(__name__)


class PlaywrightFlightSchoolCrawler:
    """
    Playwright-based crawler for JavaScript-heavy flight school directories.

    Handles sites that require JS execution, form interactions, or dynamic content loading.
    """

    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        Initialize the Playwright crawler.

        Args:
            headless: Whether to run browser in headless mode
            timeout: Default timeout for page operations (ms)
        """
        self.headless = headless
        self.timeout = timeout
        self.playwright = None
        self.browser = None
        self.context = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()

    async def start(self):
        """Start the Playwright browser and context."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--single-process',  # Helps with memory issues
                '--disable-gpu'
            ]
        )

        self.context = await self.browser.new_context(
            user_agent='WheelsUp-Flight-School-Directory-Crawler/1.0 (Educational Research Project)',
            viewport={'width': 1280, 'height': 720}
        )

        # Set reasonable timeouts
        self.context.set_default_timeout(self.timeout)

        logger.info("Playwright browser started successfully")

    async def stop(self):
        """Stop the Playwright browser and cleanup."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

        logger.info("Playwright browser stopped")

    async def crawl_flight_training_central(self) -> List[Dict[str, Any]]:
        """
        Crawl Flight Training Central directory using Playwright.

        This site uses a location-based search interface that requires JS execution.

        Returns:
            List of crawled page data
        """
        results = []

        try:
            page = await self.context.new_page()

            # Navigate to the directory
            url = "https://flighttrainingcentral.com/flight-school-directory/"
            logger.info(f"Navigating to {url}")
            await page.goto(url, wait_until='networkidle')

            # Wait for the page to fully load
            await page.wait_for_timeout(2000)

            # Store the main directory page
            main_page_data = await self.extract_page_data(page, url, "flighttrainingcentral_main")
            results.append(main_page_data)

            # Get list of US states for systematic searching
            states = [
                'California', 'Florida', 'Texas', 'Arizona', 'Colorado',
                'New York', 'Illinois', 'Washington', 'Nevada', 'Georgia'
            ]  # Focus on states with most flight schools

            for state in states:
                logger.info(f"Searching for flight schools in {state}")
                state_results = await self.search_flight_training_central(page, state)
                results.extend(state_results)

                # Be respectful with delays between searches
                await page.wait_for_timeout(2000)

            await page.close()

        except Exception as e:
            logger.error(f"Error crawling Flight Training Central: {e}")

        return results

    async def search_flight_training_central(self, page: Page, location: str) -> List[Dict[str, Any]]:
        """
        Search Flight Training Central for schools in a specific location.

        Args:
            page: Playwright page object
            location: Location to search for (state name)

        Returns:
            List of search result data
        """
        results = []

        try:
            # Fill in the search form
            search_input = page.locator('input[name="s"], #search-input, .search-input')
            await search_input.fill(location)

            # Click the search button
            search_button = page.locator('button[type="submit"], .search-button, #search-button')
            await search_button.click()

            # Wait for search results to load
            await page.wait_for_timeout(3000)

            # Store the search results page
            search_url = page.url
            search_data = await self.extract_page_data(page, search_url, f"flighttrainingcentral_search_{location}")
            results.append(search_data)

            # Extract school links from search results
            school_links = await page.query_selector_all('a[href*="flight-school"]:not([href*="category"])')

            for link_element in school_links[:10]:  # Limit to first 10 schools per state to be respectful
                href = await link_element.get_attribute('href')
                if href and '/flight-school/' in href:
                    logger.info(f"Following school link: {href}")

                    try:
                        # Open link in new page to avoid navigation issues
                        school_page = await self.context.new_page()
                        await school_page.goto(href, wait_until='networkidle')
                        await school_page.wait_for_timeout(2000)

                        # Extract school data
                        school_data = await self.extract_page_data(school_page, href, "flighttrainingcentral_school")
                        results.append(school_data)

                        await school_page.close()

                        # Delay between school pages
                        await page.wait_for_timeout(1000)

                    except Exception as e:
                        logger.error(f"Error crawling school page {href}: {e}")

        except Exception as e:
            logger.error(f"Error searching {location}: {e}")

        return results

    async def extract_page_data(self, page: Page, url: str, source_tag: str) -> Dict[str, Any]:
        """
        Extract data from a Playwright page.

        Args:
            page: Playwright page object
            url: URL of the page
            source_tag: Tag to identify the source of the data

        Returns:
            Dictionary containing page data and metadata
        """
        try:
            # Get the HTML content
            content = await page.content()

            # Generate filename
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{source_tag}_{url_hash}_{timestamp}.html"

            # Extract basic metadata
            title = await page.title()

            return {
                'source_name': 'flighttrainingcentral_playwright',
                'url': url,
                'filename': filename,
                'content': content,
                'content_type': 'html',
                'title': title,
                'crawl_timestamp': datetime.now().isoformat(),
                'user_agent': 'playwright_crawler',
                'status_code': 200,  # Playwright doesn't provide HTTP status, assume success
            }

        except Exception as e:
            logger.error(f"Error extracting data from {url}: {e}")
            return {
                'source_name': 'flighttrainingcentral_playwright',
                'url': url,
                'error': str(e),
                'crawl_timestamp': datetime.now().isoformat(),
            }

    async def crawl_generic_js_site(self, url: str, interactions: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Generic method for crawling JS-heavy sites with custom interactions.

        Args:
            url: URL to crawl
            interactions: List of interactions to perform on the page

        Returns:
            Page data dictionary
        """
        page = await self.context.new_page()

        try:
            logger.info(f"Crawling JS site: {url}")
            await page.goto(url, wait_until='networkidle')
            await page.wait_for_timeout(2000)

            # Perform custom interactions if specified
            if interactions:
                for interaction in interactions:
                    await self.perform_interaction(page, interaction)
                    await page.wait_for_timeout(1000)

            # Extract page data
            data = await self.extract_page_data(page, url, "generic_js_crawl")

        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            data = {
                'source_name': 'generic_js_crawler',
                'url': url,
                'error': str(e),
                'crawl_timestamp': datetime.now().isoformat(),
            }

        finally:
            await page.close()

        return data

    async def perform_interaction(self, page: Page, interaction: Dict[str, Any]):
        """
        Perform a specific interaction on a page.

        Args:
            page: Playwright page object
            interaction: Dictionary describing the interaction
        """
        action = interaction.get('action')
        selector = interaction.get('selector')
        value = interaction.get('value', '')

        try:
            if action == 'click':
                await page.click(selector)
            elif action == 'fill':
                await page.fill(selector, value)
            elif action == 'select':
                await page.select_option(selector, value)
            elif action == 'wait':
                await page.wait_for_timeout(int(value))
            elif action == 'scroll':
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        except Exception as e:
            logger.error(f"Error performing interaction {action} on {selector}: {e}")


# Synchronous wrapper for easier integration
def crawl_with_playwright(target_sites: List[str] = None) -> List[Dict[str, Any]]:
    """
    Synchronous wrapper to run Playwright crawling.

    Args:
        target_sites: List of site names to crawl (currently only supports flighttrainingcentral)

    Returns:
        List of crawled data
    """
    async def run_crawler():
        async with PlaywrightFlightSchoolCrawler() as crawler:
            results = []

            if not target_sites or 'flighttrainingcentral' in target_sites:
                ftc_results = await crawler.crawl_flight_training_central()
                results.extend(ftc_results)

            return results

    # Run the async crawler
    return asyncio.run(run_crawler())


if __name__ == '__main__':
    # Example usage
    results = crawl_with_playwright(['flighttrainingcentral'])
    print(f"Crawled {len(results)} pages")
    for result in results:
        print(f"- {result.get('url', 'Unknown URL')}")
