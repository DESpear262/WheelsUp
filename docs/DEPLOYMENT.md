# WheelsUp Deployment Guide

## Overview

This guide provides configuration templates and deployment procedures for WheelsUp environments. It covers staging environment setup, environment variable configurations, and deployment workflows.

## Table of Contents

- [Environment Overview](#environment-overview)
- [Staging Environment Setup](#staging-environment-setup)
- [Environment Variables](#environment-variables)
- [Infrastructure Configuration](#infrastructure-configuration)
- [Application Deployment](#application-deployment)
- [Database Setup](#database-setup)
- [Monitoring & Alerting](#monitoring--alerting)
- [Rollback Procedures](#rollback-procedures)

## Environment Overview

### Environment Types

- **Development**: Local Docker Compose setup
- **Staging**: AWS infrastructure mirror of production
- **Production**: Live customer-facing environment

### Infrastructure Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CloudFront    │    │   Application   │    │   Database      │
│   (CDN)         │◄──▶│   Load Balancer │◄──▶│   (RDS)         │
│                 │    │                 │    │                 │
│ • SSL/TLS       │    │ • EC2 Instances │    │ • PostgreSQL    │
│ • Global CDN    │    │ • Auto Scaling  │    │ • PostGIS       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   OpenSearch    │    │   S3 Storage    │    │   Secrets        │
│   Service       │    │                 │    │   Manager       │
│                 │    │ • Raw Data      │    │                 │
│ • Search Index  │    │ • Logs          │    │ • API Keys      │
│ • Faceted Search│    │ • Backups       │    │ • Certificates  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Staging Environment Setup

### Prerequisites

- AWS CLI configured with appropriate permissions
- Terraform 1.10+
- Docker & Docker Compose (for local testing)
- GitHub repository access

### AWS Infrastructure Setup

```bash
# Clone infrastructure code
git clone <repo-url>
cd infra/terraform

# Initialize Terraform
terraform init

# Create staging workspace
terraform workspace select staging || terraform workspace new staging

# Configure staging variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with staging values

# Plan staging deployment
terraform plan -var-file=staging.tfvars

# Apply staging infrastructure
terraform apply -var-file=staging.tfvars
```

### Staging Infrastructure Configuration

#### terraform.tfvars (Staging)

```hcl
# AWS Region
region = "us-east-1"

# Environment
environment = "staging"

# VPC Configuration
vpc_cidr = "10.1.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]

# EC2 Configuration
instance_type = "t3.medium"
min_instances = 1
max_instances = 3
desired_instances = 1

# RDS Configuration
db_instance_class = "db.t3.micro"
db_allocated_storage = 20
db_engine_version = "16.1"

# OpenSearch Configuration
opensearch_instance_type = "t3.small.search"
opensearch_instance_count = 1

# Domain Configuration
domain_name = "staging.wheelsup.com"
certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/staging-cert"

# Monitoring
enable_monitoring = true
log_retention_days = 30
```

## Environment Variables

### Frontend Application (.env)

#### Development
```bash
# Database
DATABASE_URL="postgresql://wheelsup_user:wheelsup_password@localhost:5432/wheelsup_dev"

# Search
OPENSEARCH_URL="http://localhost:9200"

# External APIs
NEXT_PUBLIC_MAPBOX_TOKEN="pk.eyJ1Ijoid2hlZWxzdXAtZGV2IiwiYSI6ImNsZGt3ZWx5MzB"
NEXT_PUBLIC_MAPBOX_STYLE="mapbox://styles/wheelsup-dev/clf8x9y7k002901m"
MAPBOX_ACCESS_TOKEN="sk.eyJ1Ijoid2hlZWxzdXAtZGV2IiwiYSI6ImNsZGt3ZWx5MzA"

# Application
NODE_ENV="development"
NEXT_PUBLIC_API_URL="http://localhost:3000"
NEXT_PUBLIC_ENVIRONMENT="development"

# Security
NEXTAUTH_SECRET="dev-secret-key-change-in-production"
NEXTAUTH_URL="http://localhost:3000"

# Analytics (disabled in development)
NEXT_PUBLIC_ANALYTICS_ID=""
```

#### Staging
```bash
# Database
DATABASE_URL="postgresql://wheelsup_app:staging_password_2025@wheelsup-staging-db.cluster-xyz.us-east-1.rds.amazonaws.com:5432/wheelsup_staging"

# Search
OPENSEARCH_URL="https://search-wheelsup-staging-xyz.us-east-1.opensearch.amazonaws.com"

# External APIs
NEXT_PUBLIC_MAPBOX_TOKEN="pk.eyJ1Ijoid2hlZWxzdXAtc3RhZ2luZyIsImEiOiJjbGRrd2V4NX"
NEXT_PUBLIC_MAPBOX_STYLE="mapbox://styles/wheelsup-staging/clf8x9y7k002901m"
MAPBOX_ACCESS_TOKEN="sk.eyJ1Ijoid2hlZWxzdXAtc3RhZ2luZyIsImEiOiJjbGRrd2V4NX"

# Application
NODE_ENV="production"
NEXT_PUBLIC_API_URL="https://api.staging.wheelsup.com"
NEXT_PUBLIC_ENVIRONMENT="staging"

# Security
NEXTAUTH_SECRET="staging-secret-key-2025-secure-random-string"
NEXTAUTH_URL="https://staging.wheelsup.com"

# Analytics
NEXT_PUBLIC_ANALYTICS_ID="GA-STAGING-12345"
```

#### Production
```bash
# Database
DATABASE_URL="postgresql://wheelsup_app:prod_password_2025@wheelsup-prod-db.cluster-xyz.us-east-1.rds.amazonaws.com:5432/wheelsup_prod"

# Search
OPENSEARCH_URL="https://search-wheelsup-prod-xyz.us-east-1.opensearch.amazonaws.com"

# External APIs
NEXT_PUBLIC_MAPBOX_TOKEN="pk.eyJ1Ijoid2hlZWxzdXAtcHJvZCIsImEiOiJjbGRrd2V4NX"
NEXT_PUBLIC_MAPBOX_STYLE="mapbox://styles/wheelsup-prod/clf8x9y7k002901m"
MAPBOX_ACCESS_TOKEN="sk.eyJ1Ijoid2hlZWxzdXAtcHJvZCIsImEiOiJjbGRrd2V4NX"

# Application
NODE_ENV="production"
NEXT_PUBLIC_API_URL="https://api.wheelsup.com"
NEXT_PUBLIC_ENVIRONMENT="production"

# Security
NEXTAUTH_SECRET="prod-secret-key-2025-secure-random-string-256-bits"
NEXTAUTH_URL="https://wheelsup.com"

# Analytics
NEXT_PUBLIC_ANALYTICS_ID="GA-PRODUCTION-67890"
```

### ETL Pipeline (.env)

#### Development
```bash
# Database
DATABASE_URL="postgresql://wheelsup_user:wheelsup_password@localhost:5432/wheelsup_dev"
OPENSEARCH_URL="http://localhost:9200"

# LLM APIs
ANTHROPIC_API_KEY="sk-ant-api03-dev-test-key-1234567890"
OPENAI_API_KEY="sk-dev-test-key-1234567890abcdef"

# AWS (development uses LocalStack)
AWS_ACCESS_KEY_ID="test"
AWS_SECRET_ACCESS_KEY="test"
AWS_REGION="us-east-1"
AWS_S3_BUCKET="wheelsup-dev-raw-data"
AWS_S3_ENDPOINT="http://localhost:4566"

# Logging
LOG_LEVEL="DEBUG"
LOG_FORMAT="json"
LOG_FILE="etl/logs/etl_dev.log"

# Performance
MAX_CONCURRENT_REQUESTS="3"
CRAWL_DELAY_SECONDS="1"
LLM_BATCH_SIZE="5"
```

#### Staging
```bash
# Database
DATABASE_URL="postgresql://wheelsup_etl:staging_etl_password_2025@wheelsup-staging-db.cluster-xyz.us-east-1.rds.amazonaws.com:5432/wheelsup_staging"
OPENSEARCH_URL="https://search-wheelsup-staging-xyz.us-east-1.opensearch.amazonaws.com"

# LLM APIs
ANTHROPIC_API_KEY="sk-ant-api03-staging-key-secure-random-256"
OPENAI_API_KEY="sk-staging-key-secure-random-256-bits-long"

# AWS
AWS_ACCESS_KEY_ID="AKIA_STAGING_KEY_EXAMPLE"
AWS_SECRET_ACCESS_KEY="staging_secret_key_secure_256_bits"
AWS_REGION="us-east-1"
AWS_S3_BUCKET="wheelsup-staging-raw-data"

# Logging
LOG_LEVEL="INFO"
LOG_FORMAT="json"
LOG_FILE="etl/logs/etl_staging.log"

# Performance
MAX_CONCURRENT_REQUESTS="10"
CRAWL_DELAY_SECONDS="2"
LLM_BATCH_SIZE="20"

# Monitoring
SENTRY_DSN="https://staging-sentry-dsn@sentry.io/project-id"
DATADOG_API_KEY="staging-datadog-api-key"
```

#### Production
```bash
# Database
DATABASE_URL="postgresql://wheelsup_etl:prod_etl_password_2025@wheelsup-prod-db.cluster-xyz.us-east-1.rds.amazonaws.com:5432/wheelsup_prod"
OPENSEARCH_URL="https://search-wheelsup-prod-xyz.us-east-1.opensearch.amazonaws.com"

# LLM APIs
ANTHROPIC_API_KEY="sk-ant-api03-prod-key-secure-random-256-bit"
OPENAI_API_KEY="sk-prod-key-secure-random-256-bits-longer"

# AWS
AWS_ACCESS_KEY_ID="AKIA_PRODUCTION_KEY_SECURE"
AWS_SECRET_ACCESS_KEY="production_secret_key_secure_256_bits_long"
AWS_REGION="us-east-1"
AWS_S3_BUCKET="wheelsup-prod-raw-data"

# Logging
LOG_LEVEL="WARNING"
LOG_FORMAT="json"
LOG_FILE="etl/logs/etl_prod.log"

# Performance
MAX_CONCURRENT_REQUESTS="25"
CRAWL_DELAY_SECONDS="5"
LLM_BATCH_SIZE="50"

# Monitoring
SENTRY_DSN="https://prod-sentry-dsn@sentry.io/project-id"
DATADOG_API_KEY="prod-datadog-api-key-secure"
```

## Infrastructure Configuration

### AWS Resource Naming Convention

```
wheelsup-{environment}-{resource-type}-{identifier}
```

Examples:
- `wheelsup-prod-db-cluster-001`
- `wheelsup-staging-app-alb`
- `wheelsup-dev-opensearch-domain`

### Security Groups

#### Application Load Balancer
```hcl
resource "aws_security_group" "alb" {
  name_prefix = "wheelsup-${var.environment}-alb"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP access"
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS access"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

#### EC2 Application Instances
```hcl
resource "aws_security_group" "app" {
  name_prefix = "wheelsup-${var.environment}-app"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 3000
    to_port         = 3000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
    description     = "Next.js application"
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]  # VPN access only
    description = "SSH access"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

#### RDS Database
```hcl
resource "aws_security_group" "rds" {
  name_prefix = "wheelsup-${var.environment}-rds"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
    description     = "PostgreSQL access from app instances"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

### CloudFront Distribution

```hcl
resource "aws_cloudfront_distribution" "main" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "WheelsUp ${var.environment} distribution"
  default_root_object = ""
  price_class         = "PriceClass_100"

  origin {
    domain_name = aws_lb.app.dns_name
    origin_id   = "ALB"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "ALB"

    forwarded_values {
      query_string = true
      cookies {
        forward = "all"
      }
      headers = ["Authorization", "Host"]
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn = var.certificate_arn
    ssl_support_method  = "sni-only"
  }
}
```

## Application Deployment

### Docker Image Build

```bash
# Frontend build
cd apps/web
docker build -t wheelsup-web:${TAG} .

# ETL build
cd ../etl
docker build -t wheelsup-etl:${TAG} .
```

### ECR Repository Setup

```bash
# Create ECR repositories
aws ecr create-repository --repository-name wheelsup-web --region us-east-1
aws ecr create-repository --repository-name wheelsup-etl --region us-east-1

# Authenticate Docker with ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com

# Push images
docker tag wheelsup-web:${TAG} ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/wheelsup-web:${TAG}
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/wheelsup-web:${TAG}
```

### ECS Deployment

#### Task Definition
```json
{
  "family": "wheelsup-web-staging",
  "taskRoleArn": "arn:aws:iam::123456789012:role/wheelsup-ecs-task-role",
  "executionRoleArn": "arn:aws:iam::123456789012:role/wheelsup-ecs-execution-role",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "wheelsup-web",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/wheelsup-web:staging-latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 3000,
          "hostPort": 3000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "NODE_ENV", "value": "production"},
        {"name": "NEXT_PUBLIC_ENVIRONMENT", "value": "staging"}
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:wheelsup/staging/database-url"
        },
        {
          "name": "OPENSEARCH_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:wheelsup/staging/opensearch-url"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/wheelsup-web-staging",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:3000/api/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

#### Service Configuration
```json
{
  "cluster": "wheelsup-staging",
  "serviceName": "wheelsup-web-service",
  "taskDefinition": "wheelsup-web-staging:1",
  "desiredCount": 2,
  "launchType": "FARGATE",
  "platformVersion": "1.4.0",
  "networkConfiguration": {
    "awsvpcConfiguration": {
      "subnets": ["subnet-12345", "subnet-67890"],
      "securityGroups": ["sg-app-security-group"],
      "assignPublicIp": "ENABLED"
    }
  },
  "loadBalancers": [
    {
      "targetGroupArn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/wheelsup-staging/abc123",
      "containerName": "wheelsup-web",
      "containerPort": 3000
    }
  ],
  "serviceRegistries": [
    {
      "registryArn": "arn:aws:servicediscovery:us-east-1:123456789012:service/srv-staging-service"
    }
  ],
  "enableECSManagedTags": true,
  "propagateTags": "SERVICE"
}
```

### Blue-Green Deployment Strategy

```bash
# Create new task definition
aws ecs register-task-definition --cli-input-json file://task-definition-staging-v2.json

# Update service to use new task definition
aws ecs update-service \
  --cluster wheelsup-staging \
  --service wheelsup-web-service \
  --task-definition wheelsup-web-staging:2 \
  --desired-count 2

# Wait for deployment to complete
aws ecs wait services-stable \
  --cluster wheelsup-staging \
  --services wheelsup-web-service

# Verify deployment
curl -f https://api.staging.wheelsup.com/api/meta
```

## Database Setup

### RDS Instance Configuration

```bash
# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier wheelsup-staging-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 16.1 \
  --master-username wheelsup_admin \
  --master-user-password "$(openssl rand -base64 16)" \
  --allocated-storage 20 \
  --vpc-security-group-ids sg-database-group \
  --db-subnet-group-name wheelsup-staging-db-subnet \
  --backup-retention-period 7 \
  --enable-performance-insights \
  --performance-insights-retention-period 7

# Create database and users
psql "postgresql://wheelsup_admin:password@host:5432/postgres" << EOF
CREATE DATABASE wheelsup_staging;
CREATE USER wheelsup_app WITH PASSWORD 'app_password';
CREATE USER wheelsup_etl WITH PASSWORD 'etl_password';
GRANT ALL PRIVILEGES ON DATABASE wheelsup_staging TO wheelsup_app;
GRANT ALL PRIVILEGES ON DATABASE wheelsup_staging TO wheelsup_etl;
EOF
```

### Schema Migration

```bash
# Deploy schema migrations
cd apps/web

# Generate and apply migrations
npm run db:generate
npm run db:push

# Seed initial data (optional)
npm run db:seed
```

### PostGIS Setup

```sql
-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Verify installation
SELECT PostGIS_Version();
```

## Monitoring & Alerting

### CloudWatch Alarms

```bash
# High CPU utilization
aws cloudwatch put-metric-alarm \
  --alarm-name "wheelsup-staging-high-cpu" \
  --alarm-description "CPU utilization above 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=InstanceId,Value=i-1234567890abcdef0 \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:wheelsup-alerts

# Database connection count
aws cloudwatch put-metric-alarm \
  --alarm-name "wheelsup-staging-db-connections" \
  --alarm-description "Database connections above threshold" \
  --metric-name DatabaseConnections \
  --namespace AWS/RDS \
  --statistic Maximum \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=DBInstanceIdentifier,Value=wheelsup-staging-db \
  --evaluation-periods 2
```

### Application Monitoring

```typescript
// pages/api/health.ts
import { NextApiRequest, NextApiResponse } from 'next/server';
import { checkConnection } from '../../../lib/db';
import { opensearchClient } from '../../../lib/Newsearch';

export async function GET() {
  try {
    // Check database connectivity
    const dbHealthy = await checkConnection();

    // Check OpenSearch connectivity
    const osResponse = await opensearchClient.cluster.health();
    const osHealthy = osResponse.body.status === 'green' || osResponse.body.status === 'yellow';

    // Check memory usage
    const memUsage = process.memoryUsage();
    const memHealthy = memUsage.heapUsed / memUsage.heapTotal < 0.9;

    const overallHealthy = dbHealthy && osHealthy && memHealthy;

    return NextResponse.json({
      status: overallHealthy ? 'healthy' : 'unhealthy',
      timestamp: new Date().toISOString(),
      checks: {
        database: dbHealthy,
        opensearch: osHealthy,
        memory: memHealthy,
      },
      metrics: {
        memoryUsage: {
          used: Math.round(memUsage.heapUsed / 1024 / 1024),
          total: Math.round(memUsage.heapTotal / 1024 / 1024),
          percentage: Math.round((memUsage.heapUsed / memUsage.heapTotal) * 100),
        },
      },
    }, {
      status: overallHealthy ? 200 : 503,
      headers: {
        'Cache-Control': 'no-cache',
      },
    });
  } catch (error) {
    console.error('Health check failed:', error);
    return NextResponse.json({
      status: 'unhealthy',
      error: 'Health check failed',
      timestamp: new Date().toISOString(),
    }, { status: 503 });
  }
}
```

### Log Aggregation

```bash
# CloudWatch log groups
aws logs create-log-group --log-group-name "/ecs/wheelsup-web-staging"
aws logs create-log-group --log-group-name "/ecs/wheelsup-etl-staging"
aws logs create-log-group --log-group-name "/rds/wheelsup-staging-db"

# Log retention policies
aws logs put-retention-policy \
  --log-group-name "/ecs/wheelsup-web-staging" \
  --retention-in-days 30

aws logs put-retention-policy \
  --log-group-name "/ecs/wheelsup-etl-staging" \
  --retention-in-days 90
```

## Rollback Procedures

### Application Rollback

```bash
# Rollback to previous task definition
aws ecs update-service \
  --cluster wheelsup-staging \
  --service wheelsup-web-service \
  --task-definition wheelsup-web-staging:1 \
  --desired-count 2

# Verify rollback
aws ecs describe-services \
  --cluster wheelsup-staging \
  --services wheelsup-web-service \
  --query 'services[0].taskDefinition'
```

### Database Rollback

```bash
# Create restore point
aws rds create-db-snapshot \
  --db-instance-identifier wheelsup-staging-db \
  --db-snapshot-identifier wheelsup-staging-pre-deployment-$(date +%Y%m%d_%H%M%S)

# Restore from snapshot if needed
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier wheelsup-staging-db-rollback \
  --db-snapshot-identifier wheelsup-staging-pre-deployment-20251115 \
  --db-instance-class db.t3.micro
```

### Emergency Rollback Script

```bash
#!/bin/bash
# emergency-rollback.sh

echo "🚨 Starting emergency rollback for WheelsUp staging..."

# 1. Scale down current service
aws ecs update-service \
  --cluster wheelsup-staging \
  --service wheelsup-web-service \
  --desired-count 0

# 2. Deploy previous version
aws ecs update-service \
  --cluster wheelsup-staging \
  --service wheelsup-web-service \
  --task-definition wheelsup-web-staging:stable \
  --desired-count 2

# 3. Wait for deployment
aws ecs wait services-stable \
  --cluster wheelsup-staging \
  --services wheelsup-web-service

# 4. Verify health
curl -f https://api.staging.wheelsup.com/api/health

echo "✅ Emergency rollback completed"
```

## Security Considerations

### Secrets Management

```bash
# Store secrets in AWS Secrets Manager
aws secretsmanager create-secret \
  --name "wheelsup/staging/database-url" \
  --secret-string "postgresql://user:pass@host:5432/db"

# IAM roles for ECS tasks
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:us-east-1:123456789012:secret:wheelsup/staging/*"
      ]
    }
  ]
}
```

### SSL/TLS Configuration

```bash
# Request ACM certificate
aws acm request-certificate \
  --domain-name staging.wheelsup.com \
  --validation-method DNS \
  --subject-alternative-names "*.staging.wheelsup.com"

# Update CloudFront distribution
aws cloudfront update-distribution \
  --distribution-config file://cloudfront-config.json \
  --id E1234567890123
```

### Backup Strategy

```bash
# Automated RDS backups
aws rds modify-db-instance \
  --db-instance-identifier wheelsup-staging-db \
  --backup-retention-period 7 \
  --preferred-backup-window "03:00-04:00"

# S3 backup replication
aws s3api put-bucket-replication \
  --bucket wheelsup-staging-raw-data \
  --replication-configuration file://replication-config.json
```

---

**Deployment Guide** - Comprehensive configuration for WheelsUp staging and production environments.
