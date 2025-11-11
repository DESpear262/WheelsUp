# Route53 DNS Module
# Creates hosted zone and DNS records for the WheelsUp domain

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
}

variable "existing_ec2_ip" {
  description = "IP address of existing EC2 instance"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

# Create hosted zone
resource "aws_route53_zone" "wheelsup" {
  name = var.domain_name

  tags = {
    Name        = "wheelsup-${var.environment}"
    Environment = var.environment
    Project     = "WheelsUp"
    ManagedBy   = "Terraform"
  }
}

# A record for the root domain pointing to EC2
resource "aws_route53_record" "root_a" {
  zone_id = aws_route53_zone.wheelsup.zone_id
  name    = var.domain_name
  type    = "A"
  ttl     = 300
  records = [var.existing_ec2_ip]

  depends_on = [aws_route53_zone.wheelsup]
}

# CNAME record for www subdomain
resource "aws_route53_record" "www_cname" {
  zone_id = aws_route53_zone.wheelsup.zone_id
  name    = "www.${var.domain_name}"
  type    = "CNAME"
  ttl     = 300
  records = [var.domain_name]

  depends_on = [aws_route53_zone.wheelsup]
}

# API subdomain (for future API endpoints)
resource "aws_route53_record" "api_a" {
  zone_id = aws_route53_zone.wheelsup.zone_id
  name    = "api.${var.domain_name}"
  type    = "A"
  ttl     = 300
  records = [var.existing_ec2_ip]

  depends_on = [aws_route53_zone.wheelsup]
}

# Outputs
output "hosted_zone_id" {
  description = "Route53 hosted zone ID"
  value       = aws_route53_zone.wheelsup.zone_id
}

output "name_servers" {
  description = "Name servers for the hosted zone"
  value       = aws_route53_zone.wheelsup.name_servers
}

output "domain_name" {
  description = "Configured domain name"
  value       = var.domain_name
}
