# Error Handling and Logging Infrastructure
#
# This module provides comprehensive error handling, logging, and monitoring
# utilities for the flight school crawling pipeline. As requested, failures
# are logged but no retry logic is implemented.

import logging
import logging.handlers
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys
from dataclasses import dataclass, asdict
from enum import Enum

# Configure main logger
logger = logging.getLogger('flight_school_crawler')
logger.setLevel(logging.INFO)

# Create formatters
detailed_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
)

simple_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)


class ErrorSeverity(Enum):
    """Enumeration of error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Enumeration of error categories."""
    NETWORK = "network"
    PARSING = "parsing"
    CONFIGURATION = "configuration"
    RESOURCE = "resource"
    VALIDATION = "validation"
    UNKNOWN = "unknown"


@dataclass
class CrawlError:
    """
    Structured error information for crawl operations.
    """
    timestamp: str
    source_name: str
    url: str
    error_category: ErrorCategory
    error_severity: ErrorSeverity
    error_message: str
    error_code: Optional[str] = None
    user_agent: Optional[str] = None
    request_method: Optional[str] = None
    response_status: Optional[int] = None
    duration_ms: Optional[int] = None
    stack_trace: Optional[str] = None
    additional_context: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format."""
        data = asdict(self)
        # Convert enums to strings
        data['error_category'] = self.error_category.value
        data['error_severity'] = self.error_severity.value
        return data

    def to_json(self) -> str:
        """Convert error to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)


class FlightSchoolErrorHandler:
    """
    Centralized error handling and logging for flight school crawling operations.

    Provides structured error logging without automatic retry logic.
    """

    def __init__(self, log_directory: str = "logs", max_log_files: int = 10):
        """
        Initialize the error handler.

        Args:
            log_directory: Directory to store log files
            max_log_files: Maximum number of log files to keep
        """
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(exist_ok=True)

        # Set up file handlers
        self._setup_file_handlers(max_log_files)

        # Error tracking
        self.errors_by_source = {}
        self.errors_by_category = {}
        self.total_errors = 0

        logger.info("Error handler initialized")

    def _setup_file_handlers(self, max_log_files: int):
        """Set up rotating file handlers for different log types."""

        # Main application log
        main_handler = logging.handlers.RotatingFileHandler(
            self.log_directory / "flight_school_crawler.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=max_log_files
        )
        main_handler.setFormatter(detailed_formatter)
        main_handler.setLevel(logging.INFO)
        logger.addHandler(main_handler)

        # Error-only log
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_directory / "errors.log",
            maxBytes=10*1024*1024,
            backupCount=max_log_files
        )
        error_handler.setFormatter(detailed_formatter)
        error_handler.setLevel(logging.ERROR)
        logger.addHandler(error_handler)

        # Structured error JSON log
        json_error_handler = logging.handlers.RotatingFileHandler(
            self.log_directory / "errors.json",
            maxBytes=10*1024*1024,
            backupCount=max_log_files
        )
        json_error_handler.setFormatter(logging.Formatter('%(message)s'))
        json_error_handler.setLevel(logging.ERROR)
        logger.addHandler(json_error_handler)

        # Console handler for development
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(simple_formatter)
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)

    def log_error(self, error: CrawlError):
        """
        Log a structured crawl error.

        Args:
            error: CrawlError instance with error details
        """
        self.total_errors += 1

        # Update tracking statistics
        source = error.source_name
        category = error.error_category.value

        if source not in self.errors_by_source:
            self.errors_by_source[source] = 0
        self.errors_by_source[source] += 1

        if category not in self.errors_by_category:
            self.errors_by_category[category] = 0
        self.errors_by_category[category] += 1

        # Log the error
        error_json = error.to_json()

        # Choose log level based on severity
        if error.error_severity == ErrorSeverity.CRITICAL:
            logger.critical(f"Crawl error: {error.error_message}")
            logger.critical(error_json)
        elif error.error_severity == ErrorSeverity.HIGH:
            logger.error(f"Crawl error: {error.error_message}")
            logger.error(error_json)
        elif error.error_severity == ErrorSeverity.MEDIUM:
            logger.warning(f"Crawl error: {error.error_message}")
            logger.warning(error_json)
        else:
            logger.info(f"Crawl error: {error.error_message}")
            logger.info(error_json)

    def log_network_error(self,
                         source_name: str,
                         url: str,
                         error_message: str,
                         status_code: Optional[int] = None,
                         duration_ms: Optional[int] = None) -> CrawlError:
        """
        Log a network-related error.

        Args:
            source_name: Name of the data source
            url: URL that failed
            error_message: Description of the error
            status_code: HTTP status code if applicable
            duration_ms: Request duration in milliseconds

        Returns:
            The created CrawlError instance
        """
        severity = ErrorSeverity.HIGH if status_code and status_code >= 500 else ErrorSeverity.MEDIUM

        error = CrawlError(
            timestamp=datetime.now().isoformat(),
            source_name=source_name,
            url=url,
            error_category=ErrorCategory.NETWORK,
            error_severity=severity,
            error_message=error_message,
            response_status=status_code,
            duration_ms=duration_ms,
        )

        self.log_error(error)
        return error

    def log_parsing_error(self,
                         source_name: str,
                         url: str,
                         error_message: str,
                         stack_trace: Optional[str] = None) -> CrawlError:
        """
        Log a parsing-related error.

        Args:
            source_name: Name of the data source
            url: URL that failed to parse
            error_message: Description of the parsing error
            stack_trace: Python stack trace if available

        Returns:
            The created CrawlError instance
        """
        error = CrawlError(
            timestamp=datetime.now().isoformat(),
            source_name=source_name,
            url=url,
            error_category=ErrorCategory.PARSING,
            error_severity=ErrorSeverity.MEDIUM,
            error_message=error_message,
            stack_trace=stack_trace,
        )

        self.log_error(error)
        return error

    def log_timeout_error(self,
                         source_name: str,
                         url: str,
                         timeout_seconds: int) -> CrawlError:
        """
        Log a timeout error.

        Args:
            source_name: Name of the data source
            url: URL that timed out
            timeout_seconds: Timeout duration in seconds

        Returns:
            The created CrawlError instance
        """
        error_message = f"Request timed out after {timeout_seconds} seconds"

        error = CrawlError(
            timestamp=datetime.now().isoformat(),
            source_name=source_name,
            url=url,
            error_category=ErrorCategory.NETWORK,
            error_severity=ErrorSeverity.MEDIUM,
            error_message=error_message,
            additional_context={"timeout_seconds": timeout_seconds},
        )

        self.log_error(error)
        return error

    def log_configuration_error(self,
                               source_name: str,
                               error_message: str,
                               config_key: Optional[str] = None) -> CrawlError:
        """
        Log a configuration-related error.

        Args:
            source_name: Name of the data source
            error_message: Description of the configuration error
            config_key: Configuration key that caused the error

        Returns:
            The created CrawlError instance
        """
        error = CrawlError(
            timestamp=datetime.now().isoformat(),
            source_name=source_name,
            url="",  # No URL for config errors
            error_category=ErrorCategory.CONFIGURATION,
            error_severity=ErrorSeverity.HIGH,
            error_message=error_message,
            additional_context={"config_key": config_key} if config_key else None,
        )

        self.log_error(error)
        return error

    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all logged errors.

        Returns:
            Dictionary with error statistics
        """
        return {
            'total_errors': self.total_errors,
            'errors_by_source': self.errors_by_source,
            'errors_by_category': self.errors_by_category,
            'generated_at': datetime.now().isoformat(),
        }

    def export_error_summary(self, filename: Optional[str] = None) -> str:
        """
        Export error summary to a JSON file.

        Args:
            filename: Optional filename (default: error_summary_YYYYMMDD.json)

        Returns:
            Path to the exported file
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d')
            filename = f"error_summary_{timestamp}.json"

        filepath = self.log_directory / filename

        summary = self.get_error_summary()

        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2, default=str)

        logger.info(f"Error summary exported to {filepath}")
        return str(filepath)


# Scrapy middleware for error handling
class CrawlErrorMiddleware:
    """
    Scrapy middleware for catching and logging crawl errors.
    """

    def __init__(self):
        """Initialize the middleware."""
        self.error_handler = FlightSchoolErrorHandler()

    @classmethod
    def from_crawler(cls, crawler):
        """Create middleware instance from Scrapy crawler."""
        return cls()

    def process_exception(self, request, exception, spider):
        """
        Process exceptions that occur during crawling.

        Args:
            request: Scrapy request object
            exception: The exception that occurred
            spider: Scrapy spider instance
        """
        error_message = f"{type(exception).__name__}: {str(exception)}"

        self.error_handler.log_error(CrawlError(
            timestamp=datetime.now().isoformat(),
            source_name=spider.name,
            url=request.url,
            error_category=ErrorCategory.NETWORK,
            error_severity=ErrorSeverity.MEDIUM,
            error_message=error_message,
            user_agent=request.headers.get('User-Agent', [b''])[0].decode('utf-8', errors='ignore'),
            request_method=request.method,
            stack_trace=str(exception.__traceback__) if hasattr(exception, '__traceback__') else None,
        ))

        # Return None to continue processing (no retry as requested)
        return None


# Utility functions
def create_error_handler(log_directory: str = "logs") -> FlightSchoolErrorHandler:
    """
    Create and return an error handler instance.

    Args:
        log_directory: Directory for log files

    Returns:
        Configured FlightSchoolErrorHandler instance
    """
    return FlightSchoolErrorHandler(log_directory)


def log_crawl_failure(source_name: str,
                     url: str,
                     error_message: str,
                     error_category: ErrorCategory = ErrorCategory.UNKNOWN,
                     severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> CrawlError:
    """
    Convenience function to log a crawl failure.

    Args:
        source_name: Name of the data source
        url: URL that failed
        error_message: Description of the failure
        error_category: Category of the error
        severity: Severity level of the error

    Returns:
        The created CrawlError instance
    """
    handler = FlightSchoolErrorHandler()
    error = CrawlError(
        timestamp=datetime.now().isoformat(),
        source_name=source_name,
        url=url,
        error_category=error_category,
        error_severity=severity,
        error_message=error_message,
    )
    handler.log_error(error)
    return error


if __name__ == '__main__':
    # Example usage
    handler = FlightSchoolErrorHandler()

    # Log a network error
    handler.log_network_error(
        source_name="test_source",
        url="https://example.com",
        error_message="Connection timeout",
        status_code=408,
        duration_ms=30000
    )

    # Log a parsing error
    handler.log_parsing_error(
        source_name="test_source",
        url="https://example.com/page",
        error_message="Invalid HTML structure"
    )

    # Export summary
    summary_file = handler.export_error_summary()
    print(f"Error summary saved to: {summary_file}")

    print("Error summary:", json.dumps(handler.get_error_summary(), indent=2))
