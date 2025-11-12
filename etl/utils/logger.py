"""
Logger Configuration for WheelsUp ETL Pipeline

Structured logging with CloudWatch integration, performance monitoring,
and configurable log levels for ETL operations.
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, Union
from pathlib import Path

try:
    from loguru import logger
    HAS_LOGURU = True
except ImportError:
    # Fallback logging if loguru is not available
    import logging
    logger = logging.getLogger(__name__)
    HAS_LOGURU = False


# ============================================================================
# Configuration
# ============================================================================

class LoggerConfig:
    """Logger configuration with environment-based settings."""

    def __init__(self):
        self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.log_format = os.getenv('LOG_FORMAT', 'json')  # json or text
        self.enable_cloudwatch = os.getenv('ENABLE_CLOUDWATCH', 'false').lower() == 'true'
        self.cloudwatch_group = os.getenv('CLOUDWATCH_LOG_GROUP', 'wheelsup-etl')
        self.cloudwatch_stream = os.getenv('CLOUDWATCH_LOG_STREAM', f'etl-{datetime.now().strftime("%Y%m%d-%H%M%S")}')
        self.log_file_path = os.getenv('LOG_FILE_PATH', 'logs/etl.log')
        self.max_file_size = int(os.getenv('MAX_LOG_FILE_SIZE', '10485760'))  # 10MB default
        self.retention_days = int(os.getenv('LOG_RETENTION_DAYS', '30'))


# ============================================================================
# CloudWatch Integration (Optional)
# ============================================================================

class CloudWatchHandler:
    """CloudWatch logging handler for AWS integration."""

    def __init__(self, log_group: str, log_stream: str):
        self.log_group = log_group
        self.log_stream = log_stream
        self.sequence_token = None

        try:
            import boto3
            self.cloudwatch = boto3.client('logs')
            self.enabled = True
        except ImportError:
            print("[WARNING] boto3 not available - CloudWatch logging disabled")
            self.enabled = False

    def send_log(self, message: str, timestamp: int):
        """Send log message to CloudWatch."""
        if not self.enabled:
            return

        try:
            # Create log group if it doesn't exist
            self.cloudwatch.create_log_group(logGroupName=self.log_group)

            # Create log stream if it doesn't exist
            try:
                self.cloudwatch.create_log_stream(
                    logGroupName=self.log_group,
                    logStreamName=self.log_stream
                )
            except self.cloudwatch.exceptions.ResourceAlreadyExistsException:
                pass

            # Send log events
            kwargs = {
                'logGroupName': self.log_group,
                'logStreamName': self.log_stream,
                'logEvents': [{
                    'timestamp': timestamp,
                    'message': message
                }]
            }

            if self.sequence_token:
                kwargs['sequenceToken'] = self.sequence_token

            response = self.cloudwatch.put_log_events(**kwargs)
            self.sequence_token = response.get('nextSequenceToken')

        except Exception as e:
            print(f"[ERROR] Failed to send log to CloudWatch: {e}")


# ============================================================================
# ETL Logger Class
# ============================================================================

class ETLLogger:
    """Structured logger for ETL pipeline operations."""

    def __init__(self):
        self.config = LoggerConfig()
        self.cloudwatch_handler = None
        self._setup_logger()

        if self.config.enable_cloudwatch:
            self.cloudwatch_handler = CloudWatchHandler(
                self.config.cloudwatch_group,
                self.config.cloudwatch_stream
            )

    def _setup_logger(self):
        """Configure the logger based on available packages."""

        if HAS_LOGURU:
            # Remove default handler
            logger.remove()

            # Create logs directory if it doesn't exist
            log_dir = Path(self.config.log_file_path).parent
            log_dir.mkdir(parents=True, exist_ok=True)

            # Configure loguru logger
            if self.config.log_format == 'json':
                log_format = json.dumps({
                    "timestamp": "{time:YYYY-MM-DD HH:mm:ss.SSS}",
                    "level": "{level}",
                    "message": "{message}",
                    "module": "{name}",
                    "function": "{function}",
                    "line": "{line}",
                    "extra": "{extra}"
                }, indent=None, separators=(',', ':'))
            else:
                log_format = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}"

            # Add file handler with rotation
            logger.add(
                self.config.log_file_path,
                rotation=self.config.max_file_size,
                retention=self.config.retention_days,
                level=self.config.log_level,
                format=log_format,
                serialize=self.config.log_format == 'json'
            )

            # Add console handler for development
            if self.config.environment == 'development':
                logger.add(
                    sys.stdout,
                    level=self.config.log_level,
                    format=log_format,
                    colorize=True
                )
        else:
            # Fallback to standard logging
            logging.basicConfig(
                level=getattr(logging, self.config.log_level, logging.INFO),
                format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
                handlers=[
                    logging.FileHandler(self.config.log_file_path),
                    logging.StreamHandler(sys.stdout)
                ]
            )

    def _log_with_cloudwatch(self, level: str, message: str, extra: Optional[Dict[str, Any]] = None):
        """Send log to CloudWatch if enabled."""
        if self.cloudwatch_handler and level in ['WARNING', 'ERROR', 'CRITICAL']:
            try:
                log_data = {
                    'level': level,
                    'message': message,
                    'timestamp': datetime.now().isoformat(),
                    'environment': self.config.environment
                }
                if extra:
                    log_data['extra'] = extra

                self.cloudwatch_handler.send_log(
                    json.dumps(log_data),
                    int(time.time() * 1000)
                )
            except Exception as e:
                print(f"[ERROR] Failed to send to CloudWatch: {e}")

    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log debug message."""
        logger.debug(message, extra=extra or {})

    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log info message."""
        logger.info(message, extra=extra or {})

    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        logger.warning(message, extra=extra or {})
        self._log_with_cloudwatch('WARNING', message, extra)

    def error(self, message: str, exception: Optional[Exception] = None, extra: Optional[Dict[str, Any]] = None):
        """Log error message with optional exception."""
        error_extra = extra or {}
        if exception:
            error_extra['exception'] = {
                'type': type(exception).__name__,
                'message': str(exception),
                'traceback': str(exception.__traceback__) if hasattr(exception, '__traceback__') else None
            }

        logger.error(message, extra=error_extra)
        self._log_with_cloudwatch('ERROR', message, error_extra)

    def critical(self, message: str, exception: Optional[Exception] = None, extra: Optional[Dict[str, Any]] = None):
        """Log critical message."""
        error_extra = extra or {}
        if exception:
            error_extra['exception'] = {
                'type': type(exception).__name__,
                'message': str(exception),
                'traceback': str(exception.__traceback__) if hasattr(exception, '__traceback__') else None
            }

        logger.critical(message, extra=error_extra)
        self._log_with_cloudwatch('CRITICAL', message, error_extra)

    # ETL-specific logging methods
    def pipeline_start(self, pipeline_name: str, config: Dict[str, Any]):
        """Log pipeline start event."""
        self.info(f"Starting ETL pipeline: {pipeline_name}", {
            'pipeline': pipeline_name,
            'config': config,
            'event': 'pipeline_start'
        })

    def pipeline_complete(self, pipeline_name: str, stats: Dict[str, Any], duration: float):
        """Log pipeline completion event."""
        self.info(f"ETL pipeline completed: {pipeline_name}", {
            'pipeline': pipeline_name,
            'stats': stats,
            'duration_seconds': duration,
            'event': 'pipeline_complete'
        })

    def crawl_start(self, source: str, url: str):
        """Log crawl start event."""
        self.info(f"Starting crawl: {source}", {
            'source': source,
            'url': url,
            'event': 'crawl_start'
        })

    def crawl_complete(self, source: str, stats: Dict[str, Union[int, float]]):
        """Log crawl completion event."""
        success_rate = (stats.get('successful', 0) / max(stats.get('total', 1), 1)) * 100

        if success_rate < 80:
            self.warning(f"Crawl completed with low success rate: {source} ({success_rate:.1f}%)", {
                'source': source,
                'stats': stats,
                'success_rate': success_rate,
                'event': 'crawl_complete'
            })
        else:
            self.info(f"Crawl completed: {source} ({success_rate:.1f}%)", {
                'source': source,
                'stats': stats,
                'success_rate': success_rate,
                'event': 'crawl_complete'
            })

    def data_quality_check(self, table: str, issues: Dict[str, int]):
        """Log data quality check results."""
        total_issues = sum(issues.values())

        if total_issues > 0:
            self.warning(f"Data quality issues found in {table}", {
                'table': table,
                'issues': issues,
                'total_issues': total_issues,
                'event': 'data_quality_check'
            })
        else:
            self.info(f"Data quality check passed for {table}", {
                'table': table,
                'event': 'data_quality_check'
            })

    def performance_metric(self, operation: str, duration: float, metadata: Optional[Dict[str, Any]] = None):
        """Log performance metric."""
        perf_data = {
            'operation': operation,
            'duration_seconds': duration,
            'event': 'performance_metric'
        }

        if metadata:
            perf_data.update(metadata)

        # Log as warning if operation is slow (>30 seconds for ETL operations)
        if duration > 30:
            self.warning(f"Slow operation detected: {operation} ({duration:.2f}s)", perf_data)
        else:
            self.debug(f"Performance metric: {operation} ({duration:.2f}s)", perf_data)


# ============================================================================
# Global Logger Instance
# ============================================================================

# Create global logger instance
etl_logger = ETLLogger()

# ============================================================================
# Convenience Functions
# ============================================================================

def get_logger() -> ETLLogger:
    """Get the global ETL logger instance."""
    return etl_logger


def log_pipeline_start(pipeline_name: str, config: Dict[str, Any]):
    """Convenience function to log pipeline start."""
    etl_logger.pipeline_start(pipeline_name, config)


def log_pipeline_complete(pipeline_name: str, stats: Dict[str, Any], duration: float):
    """Convenience function to log pipeline completion."""
    etl_logger.pipeline_complete(pipeline_name, stats, duration)


def log_crawl_start(source: str, url: str):
    """Convenience function to log crawl start."""
    etl_logger.crawl_start(source, url)


def log_crawl_complete(source: str, stats: Dict[str, Union[int, float]]):
    """Convenience function to log crawl completion."""
    etl_logger.crawl_complete(source, stats)


# ============================================================================
# Export
# ============================================================================

__all__ = [
    'ETLLogger',
    'get_logger',
    'etl_logger',
    'log_pipeline_start',
    'log_pipeline_complete',
    'log_crawl_start',
    'log_crawl_complete'
]
