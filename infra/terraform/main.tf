# WheelsUp MVP Infrastructure
# Terraform configuration for AWS resources

terraform {
  required_version = ">= 1.10.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # TODO: Configure backend for state management
  # backend "s3" {
  #   bucket = "wheelsup-terraform-state"
  #   key    = "mvp/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

# AWS Provider configuration
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "WheelsUp"
      Environment = "MVP"
      ManagedBy   = "Terraform"
    }
  }
}

# NOTE: EC2 and RDS are already provisioned and connected
# Uncomment the VPC, Security Groups, RDS, and EC2 modules below if you need to recreate them

# # VPC and Networking
# module "vpc" {
#   source = "./modules/vpc"
#
#   vpc_cidr_block = var.vpc_cidr_block
#   environment    = var.environment
# }

# # Security Groups
# module "security_groups" {
#   source = "./modules/security-groups"
#
#   vpc_id      = module.vpc.vpc_id
#   environment = var.environment
# }

# # RDS PostgreSQL Database
# module "rds" {
#   source = "./modules/rds"
#
#   vpc_id                   = module.vpc.vpc_id
#   subnet_ids              = module.vpc.private_subnet_ids
#   db_security_group_id    = module.security_groups.rds_security_group_id
#   environment             = var.environment
#   db_instance_class       = var.db_instance_class
#   db_allocated_storage    = var.db_allocated_storage
# }

# # EC2 Instance for Web Application
# module "ec2_web" {
#   source = "./modules/ec2"
#
#   vpc_id              = module.vpc.vpc_id
#   subnet_ids          = module.vpc.public_subnet_ids
#   security_group_ids  = [module.security_groups.web_security_group_id]
#   environment         = var.environment
#   instance_type       = var.web_instance_type
#   key_name           = var.key_name
#
#   tags = {
#     Name        = "wheelsup-web"
#     Application = "web"
#   }
# }

# Amazon OpenSearch Service (needed for search functionality)
module "opensearch" {
  source = "./modules/opensearch"

  # Note: You'll need to provide VPC ID and subnet IDs for your existing VPC
  # vpc_id                      = "your-existing-vpc-id"
  # subnet_ids                  = ["subnet-1", "subnet-2"]  # Private subnets from your existing VPC
  # opensearch_security_group_id = module.security_groups.opensearch_security_group_id
  environment = var.environment
}

# S3 Buckets (for data storage)
module "s3" {
  source = "./modules/s3"

  environment = var.environment
}

# CloudFront Distribution (for CDN - optional for MVP)
# module "cloudfront" {
#   source = "./modules/cloudfront"
#
#   web_bucket_domain_name = module.s3.web_bucket_domain_name
#   web_bucket_id         = module.s3.web_bucket_id
#   environment           = var.environment
# }

# Application Load Balancer (for load balancing existing EC2)
# Uncomment if you want to add ALB in front of your existing EC2
# module "alb" {
#   source = "./modules/alb"
#
#   # vpc_id             = "your-existing-vpc-id"
#   # subnet_ids         = ["subnet-1", "subnet-2"]  # Public subnets from your existing VPC
#   # security_group_ids = [module.security_groups.alb_security_group_id]
#   environment = var.environment
#   certificate_arn = var.certificate_arn
# }

# Route 53 (DNS - points to existing EC2 IP)
module "route53" {
  source = "./modules/route53"

  domain_name = var.domain_name
  # Note: This will create DNS records pointing to your existing EC2 IP
  existing_ec2_ip = var.existing_ec2_ip
  environment     = var.environment
}

# Outputs
output "opensearch_endpoint" {
  description = "OpenSearch endpoint"
  value       = module.opensearch.opensearch_endpoint
}

output "s3_bucket_names" {
  description = "S3 bucket names for data storage"
  value       = module.s3.bucket_names
}

output "route53_name_servers" {
  description = "Route53 name servers for domain configuration"
  value       = module.route53.name_servers
}

output "existing_ec2_ip" {
  description = "Your existing EC2 instance IP"
  value       = var.existing_ec2_ip
}

# Commented out outputs for services not currently deployed
# output "cloudfront_domain" {
#   description = "CloudFront distribution domain"
#   value       = module.cloudfront.cloudfront_domain_name
# }

# output "alb_dns_name" {
#   description = "Application Load Balancer DNS name"
#   value       = module.alb.alb_dns_name
# }
