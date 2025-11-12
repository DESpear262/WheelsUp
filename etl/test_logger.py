#!/usr/bin/env python3
"""
Test script for ETL Logger functionality
"""

import os
import sys
from pathlib import Path

# Add the utils directory to the path
sys.path.insert(0, str(Path(__file__).parent / 'utils'))

def test_etl_logger():
    """Test basic ETL logger functionality."""
    from logger import get_logger, log_pipeline_start, log_pipeline_complete

    logger = get_logger()

    print("Testing ETL Logger...")

    # Test basic logging
    logger.info("ETL Logger test started")
    logger.warning("This is a test warning")
    logger.error("This is a test error")

    # Test pipeline logging
    log_pipeline_start("test_pipeline", {"batch_size": 100, "source": "test"})

    # Simulate some work
    import time
    time.sleep(0.1)

    log_pipeline_complete("test_pipeline", {
        "records_processed": 150,
        "success_rate": 0.95,
        "errors": 8
    }, 0.1)

    # Test crawl logging
    logger.crawl_start("test_source", "https://example.com")
    logger.crawl_complete("test_source", {
        "total": 100,
        "successful": 95,
        "failed": 5
    })

    # Test data quality logging
    logger.data_quality_check("schools", {"missing_emails": 25, "invalid_phones": 10})

    # Test performance logging
    logger.performance_metric("database_query", 0.05, {"table": "schools", "operation": "select"})

    print("ETL Logger tests completed successfully!")

if __name__ == "__main__":
    test_etl_logger()
