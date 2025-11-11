# Amazon OpenSearch Service Module
# Creates an OpenSearch domain for search functionality

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID (optional - for VPC-based deployment)"
  type        = string
  default     = null
}

variable "subnet_ids" {
  description = "Subnet IDs for VPC deployment (optional)"
  type        = list(string)
  default     = []
}

variable "opensearch_security_group_id" {
  description = "Security group ID for OpenSearch (optional)"
  type        = string
  default     = null
}

# Get current region
data "aws_region" "current" {}

# Get current account ID
data "aws_caller_identity" "current" {}

# OpenSearch Domain
resource "aws_opensearch_domain" "wheelsup" {
  domain_name           = "wheelsup-${var.environment}"
  engine_version        = "OpenSearch_2.13"

  cluster_config {
    instance_type          = "t3.small.search"
    instance_count         = 2
    dedicated_master_enabled = false
    zone_awareness_enabled   = true

    zone_awareness_config {
      availability_zone_count = 2
    }
  }

  # VPC configuration (if VPC ID provided)
  dynamic "vpc_options" {
    for_each = var.vpc_id != null ? [1] : []
    content {
      subnet_ids         = var.subnet_ids
      security_group_ids = var.opensearch_security_group_id != null ? [var.opensearch_security_group_id] : []
    }
  }

  # EBS storage
  ebs_options {
    ebs_enabled = true
    volume_size = 20
    volume_type = "gp3"
  }

  # Encryption
  encrypt_at_rest {
    enabled = true
  }

  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
  }

  # Node-to-node encryption
  node_to_node_encryption {
    enabled = true
  }

  # Access policies
  access_policies = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "es:*"
        Resource = "arn:aws:es:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:domain/wheelsup-${var.environment}/*"
      }
    ]
  })

  # Advanced options
  advanced_options = {
    "rest.action.multi.allow_explicit_index" = "true"
  }

  # Auto-tune disabled for t3 instance types
  auto_tune_options {
    desired_state = "DISABLED"
  }

  tags = {
    Name        = "wheelsup-opensearch-${var.environment}"
    Environment = var.environment
    Project     = "WheelsUp"
    ManagedBy   = "Terraform"
  }
}

# Outputs
output "opensearch_endpoint" {
  description = "OpenSearch domain endpoint"
  value       = aws_opensearch_domain.wheelsup.endpoint
}

output "opensearch_domain_arn" {
  description = "OpenSearch domain ARN"
  value       = aws_opensearch_domain.wheelsup.arn
}

output "opensearch_domain_id" {
  description = "OpenSearch domain ID"
  value       = aws_opensearch_domain.wheelsup.domain_id
}

output "opensearch_dashboard_endpoint" {
  description = "OpenSearch Dashboards endpoint"
  value       = aws_opensearch_domain.wheelsup.dashboard_endpoint
}
