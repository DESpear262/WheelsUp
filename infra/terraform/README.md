# WheelsUp Infrastructure - Terraform Setup

This directory contains the Terraform configuration for provisioning AWS infrastructure for the WheelsUp MVP.

## Overview

Since you already have EC2 and RDS instances set up, this Terraform configuration focuses on creating the remaining infrastructure components needed for the MVP:

- **Amazon OpenSearch Service**: For search functionality
- **S3 Buckets**: For data storage (raw, extracted, normalized data, logs, etc.)
- **Route53**: For DNS configuration pointing to your existing EC2 IP

## Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Existing EC2  │────│   Existing RDS  │
│   (18.222.210.65)│    │  (PostgreSQL)  │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────────────────┘
                 │
        ┌─────────────────┐
        │   Route53       │
        │   (DNS)         │
        └─────────────────┘
                 │
        ┌─────────────────┐
        │   OpenSearch    │
        │   (Search)      │
        └─────────────────┘
                 │
        ┌─────────────────┐
        │   S3 Buckets    │
        │   (Data Store)  │
        └─────────────────┘
```

## Prerequisites

1. **AWS CLI configured** with appropriate permissions
2. **Terraform 1.10+** installed
3. **Existing EC2 and RDS** instances already running

## Required AWS Permissions

Your AWS user/role needs the following permissions:
- `opensearch:*`
- `s3:*`
- `route53:*`
- `iam:*` (for service roles)
- `ec2:DescribeVpcs`, `ec2:DescribeSubnets` (to reference existing VPC)

## Configuration

### Variables

Edit `variables.tf` to customize:

```hcl
variable "aws_region" {
  default = "us-east-1"  # Your AWS region
}

variable "domain_name" {
  default = "wheelsup-mvp.com"  # Your domain
}

variable "existing_ec2_ip" {
  default = "18.222.210.65"  # Your EC2 IP from ssh.info
}
```

### VPC Integration (Optional)

If you want OpenSearch to be VPC-integrated with your existing VPC:

1. Uncomment the VPC configuration in `main.tf`
2. Provide your existing VPC ID and subnet IDs:

```hcl
module "opensearch" {
  # ... existing config ...
  vpc_id                      = "vpc-12345678"        # Your VPC ID
  subnet_ids                  = ["subnet-1", "subnet-2"]  # Private subnets
  opensearch_security_group_id = module.security_groups.opensearch_security_group_id
}
```

## Usage

### Initialize Terraform

```bash
cd infra/terraform
terraform init
```

### Plan Deployment

```bash
terraform plan -out=tfplan
```

### Apply Configuration

```bash
terraform apply tfplan
```

### Destroy Resources (if needed)

```bash
terraform destroy
```

## Outputs

After applying, Terraform will output:

- `opensearch_endpoint`: OpenSearch domain endpoint URL
- `s3_bucket_names`: Map of all created S3 bucket names
- `route53_name_servers`: Name servers for DNS configuration

## Next Steps

1. **Update your domain registrar** with the Route53 name servers
2. **Configure your application** to use the OpenSearch endpoint
3. **Update your ETL pipeline** to use the S3 buckets
4. **Test connectivity** between your EC2 instance and the new services

## Troubleshooting

### OpenSearch Access
- OpenSearch domains are created with HTTPS-only access
- Initial access is restricted to the AWS account root user
- Add additional IAM users/roles as needed for application access

### S3 Bucket Names
- Bucket names include random suffixes for global uniqueness
- All buckets have encryption and versioning enabled
- Lifecycle policies automatically transition data to cheaper storage classes

### DNS Configuration
- Route53 creates a hosted zone for your domain
- Records point to your existing EC2 IP address
- DNS propagation can take up to 48 hours

## Cost Estimation

Monthly costs (approximate for us-east-1):
- **OpenSearch**: $100-200 (2 t3.small.search instances)
- **S3**: $5-20 (depending on data volume and lifecycle)
- **Route53**: $0.50 (hosted zone)

Total: ~$100-250/month for the core infrastructure.
