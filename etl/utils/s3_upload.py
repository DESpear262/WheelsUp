# S3 Upload Utilities for Flight School Raw Data
#
# This module provides utilities for uploading raw HTML data and crawl results
# to Amazon S3 with proper error handling, logging, and organization.

import boto3
import logging
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Dict, Any, Optional, List
import os
from datetime import datetime
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)


class FlightSchoolS3Uploader:
    """
    Handles uploading flight school crawl data to S3.

    Organizes data by snapshot, source, and provides proper error handling.
    """

    def __init__(self,
                 bucket_name: str = "wheelsup-flight-school-raw-data",
                 region: str = "us-east-1",
                 config_file: Optional[str] = None,
                 snapshot_id: Optional[str] = None):
        """
        Initialize the S3 uploader.

        Args:
            bucket_name: S3 bucket name for storing data
            region: AWS region for the bucket
            config_file: Path to configuration file (optional)
            snapshot_id: Snapshot ID to use (optional, generates if not provided)
        """
        self.bucket_name = bucket_name
        self.region = region
        self.snapshot_id = snapshot_id or self.generate_snapshot_id()

        # Load configuration if provided
        self.config = {}
        if config_file:
            config_path = Path(config_file)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    self.config = yaml.safe_load(f)

        # Initialize S3 client
        try:
            self.s3_client = boto3.client(
                's3',
                region_name=region,
                # Credentials will be loaded from environment or AWS config
            )
            logger.info(f"S3 client initialized for bucket: {bucket_name}")
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure AWS credentials.")
            raise
        except Exception as e:
            logger.error(f"Error initializing S3 client: {e}")
            raise

    def generate_snapshot_id(self) -> str:
        """
        Generate a unique snapshot ID for this crawl session.

        Returns:
            Snapshot ID string in format YYYYQ1-MVP
        """
        now = datetime.now()
        quarter = (now.month - 1) // 3 + 1
        return f"{now.year}Q{quarter}-MVP"

    def upload_raw_html(self, data: Dict[str, Any]) -> bool:
        """
        Upload raw HTML content to S3.

        Args:
            data: Dictionary containing HTML data and metadata

        Returns:
            True if upload successful, False otherwise
        """
        try:
            source_name = data.get('source_name', 'unknown')
            filename = data.get('filename', f"unknown_{datetime.now().timestamp()}.html")
            content = data.get('content', '')

            # Construct S3 key
            s3_key = f"raw/{self.snapshot_id}/{source_name}/{filename}"

            # Prepare metadata
            metadata = {
                'source': source_name,
                'url': data.get('url', ''),
                'crawl-timestamp': data.get('crawl_timestamp', datetime.now().isoformat()),
                'content-type': data.get('content_type', 'html'),
                'snapshot-id': self.snapshot_id,
            }

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=content,
                ContentType='text/html',
                Metadata=metadata
            )

            logger.info(f"Uploaded {filename} to s3://{self.bucket_name}/{s3_key}")
            return True

        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"S3 upload failed for {filename}: {error_code} - {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error uploading {filename}: {e}")
            return False

    def upload_batch(self, data_items: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Upload multiple data items to S3.

        Args:
            data_items: List of data dictionaries to upload

        Returns:
            Dictionary with success/failure counts
        """
        results = {'successful': 0, 'failed': 0}

        for item in data_items:
            if self.upload_raw_html(item):
                results['successful'] += 1
            else:
                results['failed'] += 1

        logger.info(f"Batch upload complete: {results['successful']} successful, {results['failed']} failed")
        return results

    def list_snapshot_files(self, source_name: Optional[str] = None) -> List[str]:
        """
        List files in the current snapshot.

        Args:
            source_name: Optional source name to filter by

        Returns:
            List of S3 keys for files in the snapshot
        """
        try:
            prefix = f"raw/{self.snapshot_id}/"
            if source_name:
                prefix += f"{source_name}/"

            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)

            files = []
            for page in page_iterator:
                if 'Contents' in page:
                    files.extend([obj['Key'] for obj in page['Contents']])

            return files

        except ClientError as e:
            logger.error(f"Error listing snapshot files: {e}")
            return []

    def get_file_metadata(self, s3_key: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific S3 file.

        Args:
            s3_key: S3 key of the file

        Returns:
            Dictionary with file metadata, or None if not found
        """
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return {
                'key': s3_key,
                'size': response.get('ContentLength', 0),
                'last_modified': response.get('LastModified'),
                'metadata': response.get('Metadata', {}),
                'content_type': response.get('ContentType'),
            }
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.warning(f"File not found: {s3_key}")
            else:
                logger.error(f"Error getting metadata for {s3_key}: {e}")
            return None

    def generate_manifest(self) -> Dict[str, Any]:
        """
        Generate a manifest file for the current snapshot.

        Returns:
            Dictionary containing snapshot manifest data
        """
        files = self.list_snapshot_files()

        # Group files by source
        sources = {}
        total_size = 0

        for file_key in files:
            # Parse key: raw/{snapshot_id}/{source_name}/{filename}
            parts = file_key.split('/')
            if len(parts) >= 4:
                source_name = parts[2]
                if source_name not in sources:
                    sources[source_name] = {'files': [], 'count': 0, 'size': 0}

                # Get file metadata
                metadata = self.get_file_metadata(file_key)
                if metadata:
                    sources[source_name]['files'].append({
                        'key': file_key,
                        'filename': parts[3],
                        'size': metadata['size'],
                        'crawl_timestamp': metadata['metadata'].get('crawl-timestamp'),
                        'url': metadata['metadata'].get('url'),
                    })
                    sources[source_name]['count'] += 1
                    sources[source_name]['size'] += metadata['size']
                    total_size += metadata['size']

        manifest = {
            'snapshot_id': self.snapshot_id,
            'created_at': datetime.now().isoformat(),
            'total_files': len(files),
            'total_size_bytes': total_size,
            'sources': sources,
            'crawl_config': self.config,
        }

        return manifest

    def upload_manifest(self, manifest: Optional[Dict[str, Any]] = None) -> bool:
        """
        Upload the snapshot manifest to S3.

        Args:
            manifest: Optional manifest data (generated if not provided)

        Returns:
            True if upload successful
        """
        if manifest is None:
            manifest = self.generate_manifest()

        try:
            manifest_key = f"snapshots/manifest_{self.snapshot_id}.json"
            manifest_json = yaml.dump(manifest, default_flow_style=False)

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=manifest_key,
                Body=manifest_json,
                ContentType='application/json',
                Metadata={
                    'snapshot-id': self.snapshot_id,
                    'created-at': datetime.now().isoformat(),
                    'type': 'manifest',
                }
            )

            logger.info(f"Uploaded manifest to s3://{self.bucket_name}/{manifest_key}")
            return True

        except Exception as e:
            logger.error(f"Error uploading manifest: {e}")
            return False


# Scrapy pipeline integration
class S3Pipeline:
    """
    Scrapy pipeline for automatically uploading crawl results to S3.
    """

    def __init__(self, bucket_name: str = "wheelsup-flight-school-raw-data"):
        """
        Initialize the S3 pipeline.

        Args:
            bucket_name: S3 bucket name
        """
        self.uploader = FlightSchoolS3Uploader(bucket_name)

    @classmethod
    def from_crawler(cls, crawler):
        """Create pipeline instance from Scrapy crawler."""
        bucket_name = crawler.settings.get('S3_BUCKET_NAME', 'wheelsup-flight-school-raw-data')
        return cls(bucket_name=bucket_name)

    def process_item(self, item, spider):
        """
        Process a scraped item by uploading it to S3.

        Args:
            item: Scraped item
            spider: Scrapy spider instance

        Returns:
            The processed item
        """
        try:
            # Convert item to the expected format for upload
            upload_data = dict(item)
            upload_data['source_name'] = spider.name
            upload_data['crawl_timestamp'] = datetime.now().isoformat()

            self.uploader.upload_raw_html(upload_data)
            logger.info(f"Uploaded item from {spider.name} to S3")

        except Exception as e:
            logger.error(f"Error processing item in S3 pipeline: {e}")

        return item


# Utility functions
def upload_crawl_results(results: List[Dict[str, Any]],
                        bucket_name: str = "wheelsup-flight-school-raw-data") -> Dict[str, int]:
    """
    Convenience function to upload crawl results to S3.

    Args:
        results: List of crawl result dictionaries
        bucket_name: S3 bucket name

    Returns:
        Dictionary with upload statistics
    """
    uploader = FlightSchoolS3Uploader(bucket_name)
    return uploader.upload_batch(results)


def create_snapshot_manifest(bucket_name: str = "wheelsup-flight-school-raw-data") -> bool:
    """
    Create and upload a manifest for the current snapshot.

    Args:
        bucket_name: S3 bucket name

    Returns:
        True if manifest upload successful
    """
    uploader = FlightSchoolS3Uploader(bucket_name)
    manifest = uploader.generate_manifest()
    return uploader.upload_manifest(manifest)


if __name__ == '__main__':
    # Example usage
    uploader = FlightSchoolS3Uploader()

    # Example data
    sample_data = {
        'source_name': 'test_source',
        'url': 'https://example.com',
        'filename': 'test_20241111.html',
        'content': '<html><body>Test content</body></html>',
        'content_type': 'html',
        'crawl_timestamp': datetime.now().isoformat(),
    }

    success = uploader.upload_raw_html(sample_data)
    print(f"Upload successful: {success}")

    # Generate and upload manifest
    manifest_success = uploader.upload_manifest()
    print(f"Manifest upload successful: {manifest_success}")
