# WheelsUp MVP Infrastructure Variables
# Terraform variables for AWS resource configuration

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
  default     = "mvp"
}

# VPC Configuration (for new VPC if needed)
variable "vpc_cidr_block" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

# OpenSearch Configuration
variable "opensearch_instance_type" {
  description = "Instance type for OpenSearch data nodes"
  type        = string
  default     = "t3.small.search"
}

variable "opensearch_instance_count" {
  description = "Number of OpenSearch data nodes"
  type        = number
  default     = 2
}

variable "opensearch_version" {
  description = "OpenSearch version"
  type        = string
  default     = "OpenSearch_2.13"
}

# S3 Bucket Configuration
variable "s3_bucket_prefix" {
  description = "Prefix for S3 bucket names"
  type        = string
  default     = "wheelsup-mvp"
}

# CloudFront Configuration
variable "cloudfront_price_class" {
  description = "CloudFront price class"
  type        = string
  default     = "PriceClass_100"  # US, Canada, Europe only
}

# Domain Configuration (using IP address as mentioned)
variable "domain_name" {
  description = "Domain name for Route53 (using IP address)"
  type        = string
  default     = "wheelsup-mvp.com"
}

variable "existing_ec2_ip" {
  description = "Existing EC2 instance public IP"
  type        = string
  default     = "18.222.210.65"
}

# SSL Certificate ARN (will need to be created separately or provided)
variable "certificate_arn" {
  description = "ACM certificate ARN for HTTPS"
  type        = string
  default     = ""  # To be filled in after certificate creation
}

# Database Configuration
variable "db_instance_id" {
  description = "RDS instance identifier for CloudWatch monitoring"
  type        = string
  default     = "wheelsup-db"  # Update with actual RDS instance ID
}

# Key pair name for EC2 (if creating new instances)
variable "key_name" {
  description = "SSH key pair name for EC2 access"
  type        = string
  default     = "wheelsup-mvp-key"
}

# Tags
variable "common_tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "WheelsUp"
    Environment = "MVP"
    ManagedBy   = "Terraform"
  }
}
