# Backup & Snapshot Automation
# Automated backup policies for RDS and data snapshot management
# NOTE: Disabled for MVP - enable when needed for production

# ============================================================================
# RDS Automated Backups (Daily)
# ============================================================================

# Note: RDS automated backups are configured in the RDS module above
# This section provides additional backup automation and monitoring

# RDS Snapshot Creation (Manual/On-Demand) - DISABLED FOR MVP
# resource "aws_db_snapshot" "wheelsup_manual_snapshot" {
#   count                  = var.environment == "prod" ? 1 : 0  # Only for production
#   db_instance_identifier = aws_db_instance.wheelsup.id
#   db_snapshot_identifier = "wheelsup-${var.environment}-manual-${formatdate("YYYY-MM-DD", timestamp())}"
#
#   tags = {
#     Name        = "wheelsup-${var.environment}-manual-snapshot"
#     Environment = var.environment
#     Project     = "WheelsUp"
#     ManagedBy   = "Terraform"
#     Type        = "Manual"
#   }
# }

# ============================================================================
# S3 Backup Automation - DISABLED FOR MVP
# ============================================================================

# S3 Backup Bucket for Cross-Region Replication (Optional) - DISABLED FOR MVP
# resource "aws_s3_bucket" "backup_replica" {
#   count  = var.environment == "prod" ? 1 : 0
#   bucket = "wheelsup-${var.environment}-backup-replica-${random_string.backup_suffix[0].result}"
#   provider = aws.backup_region
#
#   tags = {
#     Name        = "wheelsup-${var.environment}-backup-replica"
#     Environment = var.environment
#     Project     = "WheelsUp"
#     ManagedBy   = "Terraform"
#     Purpose     = "Cross-region backup replica"
#   }
# }

# resource "random_string" "backup_suffix" {
#   count   = var.environment == "prod" ? 1 : 0
#   length  = 8
#   lower   = true
#   upper   = false
#   numeric = true
#   special = false
# }

# Cross-Region Replication for Critical Data (Production Only) - DISABLED FOR MVP
# resource "aws_s3_bucket_replication_configuration" "published_snapshots" {
#   count  = var.environment == "prod" ? 1 : 0
#   bucket = aws_s3_bucket.published_snapshots.id
#   role   = aws_iam_role.s3_replication[0].arn
#
#   rule {
#     id     = "published_snapshots_replication"
#     status = "Enabled"
#
#     destination {
#       bucket        = aws_s3_bucket.backup_replica[0].arn
#       storage_class = "STANDARD_IA"
#     }
#
#     filter {
#       prefix = ""
#     }
#   }
#
#   depends_on = [aws_s3_bucket_versioning.published_snapshots]
# }

# IAM Role for S3 Cross-Region Replication - DISABLED FOR MVP
# resource "aws_iam_role" "s3_replication" {
#   count = var.environment == "prod" ? 1 : 0
#   name  = "wheelsup-${var.environment}-s3-replication-role"
#
#   assume_role_policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Action = "sts:AssumeRole"
#         Effect = "Allow"
#         Principal = {
#           Service = "s3.amazonaws.com"
#         }
#       }
#     ]
#   })
#
#   tags = {
#     Name        = "wheelsup-${var.environment}-s3-replication-role"
#     Environment = var.environment
#     Project     = "WheelsUp"
#     ManagedBy   = "Terraform"
#   }
# }

# resource "aws_iam_role_policy" "s3_replication" {
#   count = var.environment == "prod" ? 1 : 0
#   name  = "wheelsup-${var.environment}-s3-replication-policy"
#   role  = aws_iam_role.s3_replication[0].id
#
#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Action = [
#           "s3:GetReplicationConfiguration",
#           "s3:ListBucket"
#         ]
#         Effect = "Allow"
#         Resource = [
#           aws_s3_bucket.published_snapshots.arn
#         ]
#       },
#       {
#         Action = [
#           "s3:GetObjectVersionForReplication",
#           "s3:GetObjectVersionAcl",
#           "s3:GetObjectVersionTagging"
#         ]
#         Effect = "Allow"
#         Resource = [
#           "${aws_s3_bucket.published_snapshots.arn}/*"
#         ]
#       },
#       {
#         Action = [
#           "s3:ReplicateObject",
#           "s3:ReplicateDelete",
#           "s3:ReplicateTags"
#         ]
#         Effect = "Allow"
#         Resource = [
#           "${aws_s3_bucket.backup_replica[0].arn}/*"
#         ]
#       }
#     ]
#  })
# }

# ============================================================================
# AWS Backup Service (Advanced Backup Management) - DISABLED FOR MVP
# ============================================================================

# AWS Backup Vault - DISABLED FOR MVP
# resource "aws_backup_vault" "wheelsup" {
#   name        = "wheelsup-${var.environment}-backup-vault"
#   kms_key_arn = aws_kms_key.backup.arn
#
#   tags = {
#     Name        = "wheelsup-${var.environment}-backup-vault"
#     Environment = var.environment
#     Project     = "WheelsUp"
#     ManagedBy   = "Terraform"
#   }
# }

# KMS Key for Backup Encryption - DISABLED FOR MVP
# resource "aws_kms_key" "backup" {
#   description             = "KMS key for WheelsUp backup encryption"
#   deletion_window_in_days = 30
#
#   tags = {
#     Name        = "wheelsup-${var.environment}-backup-kms"
#     Environment = var.environment
#     Project     = "WheelsUp"
#     ManagedBy   = "Terraform"
#   }
# }

# resource "aws_kms_alias" "backup" {
#   name          = "alias/wheelsup-${var.environment}-backup"
#   target_key_id = aws_kms_key.backup.key_id
# }

# Backup Plan for RDS - DISABLED FOR MVP
# resource "aws_backup_plan" "rds" {
#   name = "wheelsup-${var.environment}-rds-backup-plan"
#
#   rule {
#     rule_name         = "rds_daily_backups"
#     target_vault_name = aws_backup_vault.wheelsup.name
#     schedule          = "cron(0 3 ? * * *)"  # Daily at 3 AM UTC
#
#     lifecycle {
#       delete_after = 30  # Keep backups for 30 days
#     }
#
#     copy_action {
#       destination_vault_arn = var.environment == "prod" ? aws_backup_vault.cross_region_backup[0].arn : null
#     }
#   }
#
#   tags = {
#     Name        = "wheelsup-${var.environment}-rds-backup-plan"
#     Environment = var.environment
#     Project     = "WheelsUp"
#     ManagedBy   = "Terraform"
#   }
# }

# Cross-region backup vault (Production only) - DISABLED FOR MVP
# resource "aws_backup_vault" "cross_region_backup" {
#   count       = var.environment == "prod" ? 1 : 0
#   name        = "wheelsup-${var.environment}-cross-region-backup-vault"
#   kms_key_arn = aws_kms_key.backup.arn
#   provider    = aws.backup_region
#
#   tags = {
#     Name        = "wheelsup-${var.environment}-cross-region-backup-vault"
#     Environment = var.environment
#     Project     = "WheelsUp"
#     ManagedBy   = "Terraform"
#     Region      = "Cross-region"
#   }
# }

# Backup Selection for RDS - DISABLED FOR MVP
# resource "aws_backup_selection" "rds" {
#   iam_role_arn = aws_iam_role.backup_service_role.arn
#   name         = "wheelsup-${var.environment}-rds-backup-selection"
#   plan_id      = aws_backup_plan.rds.id
#
#   resources = [
#     aws_db_instance.wheelsup.arn
#   ]
# }

# IAM Role for AWS Backup Service - DISABLED FOR MVP
# resource "aws_iam_role" "backup_service_role" {
#   name = "wheelsup-${var.environment}-backup-service-role"
#
#   assume_role_policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Action = "sts:AssumeRole"
#         Effect = "Allow"
#         Principal = {
#           Service = "backup.amazonaws.com"
#         }
#       }
#     ]
#   })
#
#   tags = {
#     Name        = "wheelsup-${var.environment}-backup-service-role"
#     Environment = var.environment
#     Project     = "WheelsUp"
#     ManagedBy   = "Terraform"
#   }
# }

# resource "aws_iam_role_policy_attachment" "backup_service_role" {
#   policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
#   role       = aws_iam_role.backup_service_role.name
# }

# Additional policy for RDS backup permissions - DISABLED FOR MVP
# resource "aws_iam_role_policy" "backup_rds_permissions" {
#   name = "wheelsup-${var.environment}-backup-rds-permissions"
#   role = aws_iam_role.backup_service_role.id
#
#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Effect = "Allow"
#         Action = [
#           "rds:DescribeDBSnapshots",
#           "rds:DescribeDBInstances",
#           "rds:CreateDBSnapshot",
#           "rds:DeleteDBSnapshot",
#           "rds:CopyDBSnapshot",
#           "rds:RestoreDBInstanceFromDBSnapshot"
#         ]
#         Resource = "*"
#       },
#       {
#         Effect = "Allow"
#         Action = [
#           "kms:Decrypt",
#           "kms:DescribeKey",
#           "kms:Encrypt",
#           "kms:GenerateDataKey*",
#           "kms:ReEncrypt*"
#         ]
#         Resource = aws_kms_key.backup.arn
#       }
#     ]
#  })
# }

# ============================================================================
# Monitoring & Alerts - DISABLED FOR MVP
# ============================================================================

# CloudWatch Dashboard for Backup Monitoring - DISABLED FOR MVP
# resource "aws_cloudwatch_dashboard" "backup_monitoring" {
#   dashboard_name = "wheelsup-${var.environment}-backup-monitoring"
#
#   dashboard_body = jsonencode({
#     widgets = [
#       {
#         type   = "metric"
#         x      = 0
#         y      = 0
#         width  = 12
#         height = 6
#
#         properties = {
#           metrics = [
#             ["AWS/Backup", "NumberOfBackupJobsCompleted", "BackupVaultName", aws_backup_vault.wheelsup.name],
#             [".", "NumberOfBackupJobsFailed", ".", "."]
#           ]
#           view    = "timeSeries"
#           stacked = false
#           region  = var.aws_region
#           title   = "Backup Job Status"
#           period  = 300
#         }
#       },
#       {
#         type   = "metric"
#         x      = 12
#         y      = 0
#         width  = 12
#         height = 6
#
#         properties = {
#           metrics = [
#             ["AWS/RDS", "SnapshotStorageUsed", "DBInstanceIdentifier", aws_db_instance.wheelsup.identifier]
#           ]
#           view    = "timeSeries"
#           stacked = false
#           region  = var.aws_region
#           title   = "RDS Snapshot Storage"
#           period  = 300
#         }
#       }
#     ]
#   })
# }

# ============================================================================
# Outputs - DISABLED FOR MVP
# ============================================================================

# output "backup_vault_arn" {
#   description = "ARN of the AWS Backup vault"
#   value       = aws_backup_vault.wheelsup.arn
# }

# output "backup_vault_name" {
#   description = "Name of the AWS Backup vault"
#   value       = aws_backup_vault.wheelsup.name
# }

# output "rds_backup_plan_id" {
#   description = "ID of the RDS backup plan"
#   value       = aws_backup_plan.rds.id
# }
