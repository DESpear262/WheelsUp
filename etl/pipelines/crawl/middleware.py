# Custom Scrapy Middleware for Flight School Crawling
#
# This module provides custom middleware for enhanced error handling,
# retry logic, and logging for the flight school crawling pipeline.

import logging
import time
from typing import Optional, Dict, Any
from datetime import datetime

from scrapy import signals
from scrapy.exceptions import IgnoreRequest, NotConfigured
from scrapy.http import Request, Response

logger = logging.getLogger(__name__)


class FlightSchoolRetryMiddleware:
    """
    Custom retry middleware with enhanced error handling for flight school sources.

    Provides exponential backoff retry logic and detailed error logging.
    """

    def __init__(self, settings):
        if not settings.getbool('FLIGHTSCHOOL_RETRY_ENABLED'):
            raise NotConfigured('FlightSchoolRetryMiddleware disabled')

        self.max_retry_times = settings.getint('FLIGHTSCHOOL_MAX_RETRY_TIMES', 3)
        self.retry_http_codes = set(settings.getlist('FLIGHTSCHOOL_RETRY_HTTP_CODES', [500, 502, 503, 504, 408, 429]))
        self.retry_delays = settings.getlist('FLIGHTSCHOOL_RETRY_DELAYS', [1, 2, 4])
        self.priority_adjust = settings.getint('FLIGHTSCHOOL_RETRY_PRIORITY_ADJUST', -1)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def process_response(self, request, response, spider):
        """
        Process response and determine if retry is needed.
        """
        if request.meta.get('dont_retry', False):
            return response

        if response.status in self.retry_http_codes:
            return self._retry_request(request, response, spider, f"HTTP {response.status}")

        return response

    def process_exception(self, request, exception, spider):
        """
        Process exceptions and determine if retry is needed.
        """
        if isinstance(exception, self.EXCEPTIONS_TO_RETRY) and not request.meta.get('dont_retry', False):
            return self._retry_request(request, exception, spider, str(exception))

        return None

    EXCEPTIONS_TO_RETRY = (
        ConnectionError,
        TimeoutError,
        OSError,
    )

    def _retry_request(self, request, reason, spider, error_msg):
        """
        Retry a request with exponential backoff.
        """
        retries = request.meta.get('retry_times', 0) + 1

        if retries <= self.max_retry_times:
            logger.warning(f"Retrying {request.url} (failed {retries}/{self.max_retry_times}): {error_msg}")

            retryreq = request.copy()
            retryreq.meta['retry_times'] = retries
            retryreq.meta['retry_reason'] = error_msg
            retryreq.dont_filter = True

            # Apply exponential backoff delay
            if retries <= len(self.retry_delays):
                delay = self.retry_delays[retries - 1]
            else:
                delay = self.retry_delays[-1] * 2  # Double the last delay

            retryreq.meta['download_delay'] = delay
            retryreq.priority = request.priority + self.priority_adjust

            return retryreq
        else:
            logger.error(f"Giving up on {request.url} after {self.max_retry_times} retries: {error_msg}")
            # Log final failure
            self._log_final_failure(request, spider, error_msg)
            return None

    def _log_final_failure(self, request, spider, error_msg):
        """
        Log final failure after all retries are exhausted.
        """
        failure_data = {
            'url': request.url,
            'spider': spider.name,
            'error': error_msg,
            'retry_times': request.meta.get('retry_times', 0),
            'timestamp': datetime.now().isoformat(),
            'user_agent': request.headers.get('User-Agent', b'').decode('utf-8', errors='ignore'),
        }

        # This would be saved to a failure log or database
        logger.error(f"Final failure: {failure_data}")


class FlightSchoolLoggingMiddleware:
    """
    Enhanced logging middleware for flight school crawling.

    Provides detailed logging of crawl statistics and performance metrics.
    """

    def __init__(self, stats):
        self.stats = stats

    @classmethod
    def from_crawler(cls, crawler):
        o = cls(crawler.stats)
        crawler.signals.connect(o.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(o.spider_closed, signal=signals.spider_closed)
        return o

    def spider_opened(self, spider):
        """Log spider startup."""
        logger.info(f"Spider {spider.name} started crawling")
        self.stats.set_value('start_time', datetime.now())

    def spider_closed(self, spider, reason):
        """Log spider completion with statistics."""
        end_time = datetime.now()
        start_time = self.stats.get_value('start_time')

        if start_time:
            duration = (end_time - start_time).total_seconds()
        else:
            duration = 0

        stats_summary = {
            'spider': spider.name,
            'reason': reason,
            'duration_seconds': duration,
            'pages_crawled': self.stats.get_value('response_received_count', 0),
            'items_scraped': self.stats.get_value('item_scraped_count', 0),
            'errors': self.stats.get_value('log_count/ERROR', 0),
            'warnings': self.stats.get_value('log_count/WARNING', 0),
            'finish_time': end_time.isoformat(),
        }

        logger.info(f"Spider {spider.name} completed: {stats_summary}")

    def process_response(self, request, response, spider):
        """
        Log response details.
        """
        # Log only errors and warnings, not every successful response
        if response.status >= 400:
            logger.warning(f"HTTP {response.status} for {response.url}")

        return response

    def process_exception(self, request, exception, spider):
        """
        Log exceptions with context.
        """
        logger.error(f"Exception in {spider.name} for {request.url}: {exception}")
        return None


class FlightSchoolRateLimitMiddleware:
    """
    Rate limiting middleware to respect crawl delays and avoid overloading servers.
    """

    def __init__(self, crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_request(self, request, spider):
        """
        Apply rate limiting before making requests.
        """
        # Get crawl delay from spider settings or request meta
        delay = getattr(spider, 'download_delay', 2)
        delay = request.meta.get('download_delay', delay)

        if delay > 0:
            logger.debug(f"Applying {delay}s delay before {request.url}")
            time.sleep(delay)

        return None
