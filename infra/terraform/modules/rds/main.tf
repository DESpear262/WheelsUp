# RDS PostgreSQL Module
# Creates PostgreSQL database with automated backup policies

variable "vpc_id" {
  description = "VPC ID where RDS will be deployed"
  type        = string
}

variable "subnet_ids" {
  description = "Private subnet IDs for RDS deployment"
  type        = list(string)
}

variable "db_security_group_id" {
  description = "Security group ID for RDS access"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "db_allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 100
}

variable "db_engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "16.1"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "wheelsup"
}

variable "backup_retention_period" {
  description = "Days to retain automated backups"
  type        = number
  default     = 30
}

variable "backup_window" {
  description = "Preferred backup window (UTC)"
  type        = string
  default     = "03:00-04:00"
}

variable "maintenance_window" {
  description = "Preferred maintenance window (UTC)"
  type        = string
  default     = "sun:04:00-sun:05:00"
}

# DB Subnet Group
resource "aws_db_subnet_group" "wheelsup" {
  name       = "wheelsup-${var.environment}-db-subnet-group"
  subnet_ids = var.subnet_ids

  tags = {
    Name        = "wheelsup-${var.environment}-db-subnet-group"
    Environment = var.environment
    Project     = "WheelsUp"
    ManagedBy   = "Terraform"
  }
}

# RDS PostgreSQL Instance
resource "aws_db_instance" "wheelsup" {
  identifier = "wheelsup-${var.environment}-db"

  # Engine configuration
  engine         = "postgres"
  engine_version = var.db_engine_version
  instance_class = var.db_instance_class

  # Database configuration
  db_name  = var.db_name
  username = "wheelsup_admin"  # Will be overridden by Secrets Manager
  password = "placeholder"     # Will be overridden by Secrets Manager
  port     = 5432

  # Storage configuration
  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_allocated_storage * 2  # Auto-scaling
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id           = aws_kms_key.rds.arn

  # Network configuration
  db_subnet_group_name   = aws_db_subnet_group.wheelsup.name
  vpc_security_group_ids = [var.db_security_group_id]
  publicly_accessible    = false

  # Backup configuration
  backup_retention_period = var.backup_retention_period
  backup_window          = var.backup_window
  copy_tags_to_snapshot = true

  # Maintenance configuration
  maintenance_window = var.maintenance_window
  auto_minor_version_upgrade = true

  # Monitoring and logging
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  monitoring_interval            = 60
  monitoring_role_arn           = aws_iam_role.rds_enhanced_monitoring.arn
  performance_insights_enabled  = true
  performance_insights_kms_key_id = aws_kms_key.rds.arn

  # Deletion protection (for production)
  deletion_protection = var.environment == "prod"

  # Final snapshot
  final_snapshot_identifier = "wheelsup-${var.environment}-db-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"
  skip_final_snapshot       = var.environment != "prod"

  tags = {
    Name        = "wheelsup-${var.environment}-db"
    Environment = var.environment
    Project     = "WheelsUp"
    ManagedBy   = "Terraform"
  }

  depends_on = [
    aws_iam_role.rds_enhanced_monitoring,
    aws_kms_key.rds
  ]
}

# KMS Key for RDS encryption
resource "aws_kms_key" "rds" {
  description             = "KMS key for WheelsUp RDS encryption"
  deletion_window_in_days = 30

  tags = {
    Name        = "wheelsup-${var.environment}-rds-kms"
    Environment = var.environment
    Project     = "WheelsUp"
    ManagedBy   = "Terraform"
  }
}

resource "aws_kms_alias" "rds" {
  name          = "alias/wheelsup-${var.environment}-rds"
  target_key_id = aws_kms_key.rds.key_id
}

# IAM Role for Enhanced Monitoring
resource "aws_iam_role" "rds_enhanced_monitoring" {
  name = "wheelsup-${var.environment}-rds-enhanced-monitoring"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "wheelsup-${var.environment}-rds-monitoring"
    Environment = var.environment
    Project     = "WheelsUp"
    ManagedBy   = "Terraform"
  }
}

resource "aws_iam_role_policy_attachment" "rds_enhanced_monitoring" {
  role       = aws_iam_role.rds_enhanced_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# CloudWatch Alarms for RDS
resource "aws_cloudwatch_metric_alarm" "rds_cpu_utilization" {
  alarm_name          = "wheelsup-${var.environment}-rds-cpu-utilization"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors RDS CPU utilization"
  alarm_actions       = []  # Add SNS topic ARN for notifications

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.wheelsup.id
  }

  tags = {
    Name        = "wheelsup-${var.environment}-rds-cpu-alarm"
    Environment = var.environment
    Project     = "WheelsUp"
    ManagedBy   = "Terraform"
  }
}

resource "aws_cloudwatch_metric_alarm" "rds_free_storage_space" {
  alarm_name          = "wheelsup-${var.environment}-rds-free-storage-space"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "2000000000"  # 2GB in bytes
  alarm_description   = "This metric monitors RDS free storage space"
  alarm_actions       = []  # Add SNS topic ARN for notifications

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.wheelsup.id
  }

  tags = {
    Name        = "wheelsup-${var.environment}-rds-storage-alarm"
    Environment = var.environment
    Project     = "WheelsUp"
    ManagedBy   = "Terraform"
  }
}

# Outputs
output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.wheelsup.endpoint
  sensitive   = true
}

output "rds_address" {
  description = "RDS instance address"
  value       = aws_db_instance.wheelsup.address
  sensitive   = true
}

output "rds_port" {
  description = "RDS instance port"
  value       = aws_db_instance.wheelsup.port
}

output "rds_database_name" {
  description = "RDS database name"
  value       = aws_db_instance.wheelsup.db_name
}

output "rds_instance_id" {
  description = "RDS instance identifier"
  value       = aws_db_instance.wheelsup.id
}

output "rds_arn" {
  description = "RDS instance ARN"
  value       = aws_db_instance.wheelsup.arn
}
