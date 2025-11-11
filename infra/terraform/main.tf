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

# VPC and Networking
module "vpc" {
  source = "./modules/vpc"

  vpc_cidr_block = var.vpc_cidr_block
  environment    = var.environment
}

# Security Groups
module "security_groups" {
  source = "./modules/security-groups"

  vpc_id      = module.vpc.vpc_id
  environment = var.environment
}

# RDS PostgreSQL Database
module "rds" {
  source = "./modules/rds"

  vpc_id                   = module.vpc.vpc_id
  subnet_ids              = module.vpc.private_subnet_ids
  db_security_group_id    = module.security_groups.rds_security_group_id
  environment             = var.environment
  db_instance_class       = var.db_instance_class
  db_allocated_storage    = var.db_allocated_storage
}

# Amazon OpenSearch Service
module "opensearch" {
  source = "./modules/opensearch"

  vpc_id                      = module.vpc.vpc_id
  subnet_ids                  = module.vpc.private_subnet_ids
  opensearch_security_group_id = module.security_groups.opensearch_security_group_id
  environment                 = var.environment
}

# EC2 Instance for Web Application
module "ec2_web" {
  source = "./modules/ec2"

  vpc_id              = module.vpc.vpc_id
  subnet_ids          = module.vpc.public_subnet_ids
  security_group_ids  = [module.security_groups.web_security_group_id]
  environment         = var.environment
  instance_type       = var.web_instance_type
  key_name           = var.key_name

  tags = {
    Name        = "wheelsup-web"
    Application = "web"
  }
}

# S3 Buckets
module "s3" {
  source = "./modules/s3"

  environment = var.environment
}

# CloudFront Distribution
module "cloudfront" {
  source = "./modules/cloudfront"

  web_bucket_domain_name = module.s3.web_bucket_domain_name
  web_bucket_id         = module.s3.web_bucket_id
  environment           = var.environment
}

# Application Load Balancer
module "alb" {
  source = "./modules/alb"

  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.public_subnet_ids
  security_group_ids = [module.security_groups.alb_security_group_id]
  environment        = var.environment
  certificate_arn    = var.certificate_arn
}

# Route 53 (DNS)
module "route53" {
  source = "./modules/route53"

  domain_name     = var.domain_name
  cloudfront_domain = module.cloudfront.cloudfront_domain_name
  cloudfront_zone_id = module.cloudfront.cloudfront_zone_id
  environment     = var.environment
}

# Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = module.rds.rds_endpoint
  sensitive   = true
}

output "opensearch_endpoint" {
  description = "OpenSearch endpoint"
  value       = module.opensearch.opensearch_endpoint
}

output "web_instance_public_ip" {
  description = "Web server public IP"
  value       = module.ec2_web.instance_public_ip
}

output "cloudfront_domain" {
  description = "CloudFront distribution domain"
  value       = module.cloudfront.cloudfront_domain_name
}

output "alb_dns_name" {
  description = "Application Load Balancer DNS name"
  value       = module.alb.alb_dns_name
}
