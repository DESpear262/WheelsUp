# S3 Buckets Module
# Creates S3 buckets for data storage and static assets

variable "environment" {
  description = "Environment name"
  type        = string
}

# Get current region
data "aws_region" "current" {}

# Get current account ID
data "aws_caller_identity" "current" {}

# Raw data bucket (for scraped HTML/PDF)
resource "aws_s3_bucket" "raw_data" {
  bucket = "wheelsup-${var.environment}-raw-data-${random_string.suffix.result}"

  tags = {
    Name        = "wheelsup-${var.environment}-raw-data"
    Environment = var.environment
    Purpose     = "Raw crawled data storage"
    Project     = "WheelsUp"
    ManagedBy   = "Terraform"
  }
}

# Extracted text bucket
resource "aws_s3_bucket" "extracted_text" {
  bucket = "wheelsup-${var.environment}-extracted-text-${random_string.suffix.result}"

  tags = {
    Name        = "wheelsup-${var.environment}-extracted-text"
    Environment = var.environment
    Purpose     = "Extracted and cleaned text storage"
    Project     = "WheelsUp"
    ManagedBy   = "Terraform"
  }
}

# Normalized data bucket
resource "aws_s3_bucket" "normalized_data" {
  bucket = "wheelsup-${var.environment}-normalized-data-${random_string.suffix.result}"

  tags = {
    Name        = "wheelsup-${var.environment}-normalized-data"
    Environment = var.environment
    Purpose     = "Normalized and validated data storage"
    Project     = "WheelsUp"
    ManagedBy   = "Terraform"
  }
}

# Published snapshots bucket
resource "aws_s3_bucket" "published_snapshots" {
  bucket = "wheelsup-${var.environment}-published-snapshots-${random_string.suffix.result}"

  tags = {
    Name        = "wheelsup-${var.environment}-published-snapshots"
    Environment = var.environment
    Purpose     = "Published data snapshots"
    Project     = "WheelsUp"
    ManagedBy   = "Terraform"
  }
}

# Logs bucket
resource "aws_s3_bucket" "logs" {
  bucket = "wheelsup-${var.environment}-logs-${random_string.suffix.result}"

  tags = {
    Name        = "wheelsup-${var.environment}-logs"
    Environment = var.environment
    Purpose     = "Application and ETL logs"
    Project     = "WheelsUp"
    ManagedBy   = "Terraform"
  }
}

# Web assets bucket (for static files)
resource "aws_s3_bucket" "web_assets" {
  bucket = "wheelsup-${var.environment}-web-assets-${random_string.suffix.result}"

  tags = {
    Name        = "wheelsup-${var.environment}-web-assets"
    Environment = var.environment
    Purpose     = "Static web assets"
    Project     = "WheelsUp"
    ManagedBy   = "Terraform"
  }
}

# Random suffix for globally unique bucket names
resource "random_string" "suffix" {
  length  = 8
  lower   = true
  upper   = false
  numeric = true
  special = false
}

# Bucket versioning
resource "aws_s3_bucket_versioning" "raw_data" {
  bucket = aws_s3_bucket.raw_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_versioning" "extracted_text" {
  bucket = aws_s3_bucket.extracted_text.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_versioning" "normalized_data" {
  bucket = aws_s3_bucket.normalized_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_versioning" "published_snapshots" {
  bucket = aws_s3_bucket.published_snapshots.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "raw_data" {
  bucket = aws_s3_bucket.raw_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "extracted_text" {
  bucket = aws_s3_bucket.extracted_text.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "normalized_data" {
  bucket = aws_s3_bucket.normalized_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "published_snapshots" {
  bucket = aws_s3_bucket.published_snapshots.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "web_assets" {
  bucket = aws_s3_bucket.web_assets.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# Lifecycle policies for cost optimization and backup automation
resource "aws_s3_bucket_lifecycle_configuration" "raw_data" {
  bucket = aws_s3_bucket.raw_data.id

  rule {
    id     = "raw_data_lifecycle"
    status = "Enabled"

    filter {
      prefix = ""
    }

    # Transition to cheaper storage classes over time
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }

    # Delete after 7 years (long-term archival)
    expiration {
      days = 2555  # 7 years
    }

    # Clean up incomplete multipart uploads after 7 days
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  # Rule for cleaning up old versions (if versioning is enabled)
  rule {
    id     = "raw_data_versioning"
    status = "Enabled"

    filter {
      prefix = ""
    }

    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "STANDARD_IA"
    }

    noncurrent_version_transition {
      noncurrent_days = 90
      storage_class   = "GLACIER"
    }

    noncurrent_version_expiration {
      noncurrent_days = 365
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "extracted_text" {
  bucket = aws_s3_bucket.extracted_text.id

  rule {
    id     = "extracted_text_lifecycle"
    status = "Enabled"

    filter {
      prefix = ""
    }

    # Keep extracted text longer since it's processed data
    transition {
      days          = 60
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 180
      storage_class = "GLACIER"
    }

    transition {
      days          = 730  # 2 years
      storage_class = "DEEP_ARCHIVE"
    }

    # Delete after 10 years
    expiration {
      days = 3650
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "normalized_data" {
  bucket = aws_s3_bucket.normalized_data.id

  rule {
    id     = "normalized_data_lifecycle"
    status = "Enabled"

    filter {
      prefix = ""
    }

    # Normalized data is more valuable, keep longer
    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 365
      storage_class = "GLACIER"
    }

    # No expiration - keep indefinitely as it's normalized data
    # Can be manually cleaned up when no longer needed

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "published_snapshots" {
  bucket = aws_s3_bucket.published_snapshots.id

  rule {
    id     = "published_snapshots_lifecycle"
    status = "Enabled"

    filter {
      prefix = ""
    }

    # Published snapshots are important - keep accessible longer
    transition {
      days          = 180  # 6 months
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 730  # 2 years
      storage_class = "GLACIER"
    }

    # Keep published snapshots for 5 years minimum
    expiration {
      days = 1825  # 5 years
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  # Versioning cleanup for snapshots
  rule {
    id     = "published_snapshots_versioning"
    status = "Enabled"

    filter {
      prefix = ""
    }

    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "STANDARD_IA"
    }

    noncurrent_version_transition {
      noncurrent_days = 365
      storage_class   = "GLACIER"
    }

    noncurrent_version_expiration {
      noncurrent_days = 1095  # 3 years for old versions
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    id     = "logs_lifecycle"
    status = "Enabled"

    filter {
      prefix = ""
    }

    # Logs can be transitioned quickly
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }

    # Keep logs for compliance (7 years typical)
    expiration {
      days = 2555
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "web_assets" {
  bucket = aws_s3_bucket.web_assets.id

  rule {
    id     = "web_assets_lifecycle"
    status = "Enabled"

    filter {
      prefix = ""
    }

    # Web assets should stay accessible
    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }

    # No expiration for web assets - they may still be referenced
    # Clean up manually when assets are no longer needed

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  # Clean up old versions of web assets
  rule {
    id     = "web_assets_versioning"
    status = "Enabled"

    filter {
      prefix = ""
    }

    noncurrent_version_expiration {
      noncurrent_days = 30  # Keep old versions for rollback
    }
  }
}

# Public access block for security
resource "aws_s3_bucket_public_access_block" "raw_data" {
  bucket = aws_s3_bucket.raw_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "extracted_text" {
  bucket = aws_s3_bucket.extracted_text.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "normalized_data" {
  bucket = aws_s3_bucket.normalized_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "published_snapshots" {
  bucket = aws_s3_bucket.published_snapshots.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "logs" {
  bucket = aws_s3_bucket.logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "web_assets" {
  bucket = aws_s3_bucket.web_assets.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Outputs
output "bucket_names" {
  description = "All S3 bucket names"
  value = {
    raw_data           = aws_s3_bucket.raw_data.bucket
    extracted_text     = aws_s3_bucket.extracted_text.bucket
    normalized_data    = aws_s3_bucket.normalized_data.bucket
    published_snapshots = aws_s3_bucket.published_snapshots.bucket
    logs               = aws_s3_bucket.logs.bucket
    web_assets         = aws_s3_bucket.web_assets.bucket
  }
}

output "bucket_arns" {
  description = "All S3 bucket ARNs"
  value = {
    raw_data           = aws_s3_bucket.raw_data.arn
    extracted_text     = aws_s3_bucket.extracted_text.arn
    normalized_data    = aws_s3_bucket.normalized_data.arn
    published_snapshots = aws_s3_bucket.published_snapshots.arn
    logs               = aws_s3_bucket.logs.arn
    web_assets         = aws_s3_bucket.web_assets.arn
  }
}
