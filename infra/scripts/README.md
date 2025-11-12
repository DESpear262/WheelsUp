# WheelsUp Backup & Snapshot Automation

This directory contains automated backup and snapshot management scripts for the WheelsUp infrastructure.

## Overview

The backup system provides comprehensive data protection through:

- **RDS Automated Backups**: Daily snapshots with 30-day retention
- **S3 Lifecycle Management**: Automated data tiering and cleanup
- **Cross-Region Replication**: Production data backup to secondary region
- **AWS Backup Service**: Advanced backup management and monitoring
- **Snapshot Verification**: Automated integrity checks via cron jobs

## Components

### 1. RDS Backup Automation (`../terraform/modules/rds/main.tf`)

**Features:**
- Daily automated backups (configurable retention: 30 days)
- Manual snapshot creation capability
- CloudWatch monitoring and alerts
- Performance Insights enabled
- Enhanced monitoring with IAM roles

**Configuration:**
```hcl
backup_retention_period = 30  # Days to keep automated backups
backup_window          = "03:00-04:00"  # UTC time window
maintenance_window     = "sun:04:00-sun:05:00"  # UTC maintenance window
```

### 2. S3 Lifecycle Policies (`../terraform/modules/s3/main.tf`)

**Data Retention Strategy:**
- **Raw Data**: 30 days → IA → Glacier → Deep Archive (7 years total)
- **Extracted Text**: 60 days → IA → Glacier → Deep Archive (10 years)
- **Normalized Data**: 90 days → IA → Glacier (indefinite retention)
- **Published Snapshots**: 180 days → IA → Glacier (5 years)
- **Logs**: 30 days → IA → Glacier → Deep Archive (7 years)
- **Web Assets**: 90 days → IA (manual cleanup)

**Benefits:**
- ~70% cost reduction through automated storage tiering
- Compliance-ready retention policies
- Automatic cleanup of incomplete multipart uploads

### 3. Advanced Backup Service (`../terraform/backups.tf`)

**Production Features:**
- AWS Backup Service integration
- Cross-region replication for critical data
- Automated backup schedules
- Backup vault with encryption
- CloudWatch monitoring dashboard

### 4. Snapshot Verification Script (`create_snapshot.sh`)

**Capabilities:**
- Automated RDS snapshot verification
- S3 backup integrity checks
- ETL pipeline data validation
- AWS Backup job monitoring
- Email notifications for failures

## Usage

### Automated Verification (Cron Job)

Add to crontab for daily verification:

```bash
# Daily backup verification at 6 AM UTC
0 6 * * * /path/to/wheelsup/infra/scripts/create_snapshot.sh prod check-only

# Weekly full backup creation (Sundays at 2 AM UTC)
0 2 * * 0 /path/to/wheelsup/infra/scripts/create_snapshot.sh prod
```

### Manual Verification

```bash
# Check all backups without creating new ones
./create_snapshot.sh dev check-only

# Create additional snapshots
./create_snapshot.sh staging

# Full production backup and verification
./create_snapshot.sh prod
```

## Environment Variables

```bash
# Required
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret

# Optional
NOTIFICATION_EMAIL=alerts@wheelsup.com
```

## Monitoring & Alerts

### CloudWatch Metrics

The system creates CloudWatch alarms for:
- RDS CPU utilization > 80%
- RDS free storage space < 2GB
- Backup job failures

### Email Notifications

Configure `NOTIFICATION_EMAIL` to receive:
- Backup verification failures
- Snapshot creation errors
- Storage threshold alerts

## Cost Optimization

**Monthly Cost Breakdown (Production):**
- RDS Automated Backups: $50-100
- S3 Lifecycle Management: $20-50 (70% savings)
- AWS Backup Service: $10-30
- Cross-Region Replication: $50-200 (data transfer)

**Total: ~$130-380/month**

## Recovery Procedures

### RDS Recovery

```bash
# List available snapshots
aws rds describe-db-snapshots --db-instance-identifier wheelsup-prod-db

# Restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier wheelsup-prod-db-restored \
  --db-snapshot-identifier your-snapshot-id
```

### S3 Data Recovery

```bash
# Restore from Glacier
aws s3api restore-object \
  --bucket wheelsup-prod-published-snapshots \
  --key snapshots/snapshot-20251111.json \
  --restore-request '{"Days":7,"GlacierJobParameters":{"Tier":"Standard"}}'
```

## Security Considerations

- All backups are encrypted with KMS keys
- IAM roles follow least-privilege principle
- Cross-region replication for disaster recovery
- Automated cleanup prevents data accumulation
- Audit logging for all backup operations

## Compliance

The backup system supports:
- **GDPR**: Data minimization and retention controls
- **SOX**: Automated audit trails and verification
- **HIPAA**: Encrypted storage and access controls (if applicable)
- **ISO 27001**: Systematic backup and recovery procedures

## Troubleshooting

### Common Issues

1. **AWS CLI Access Denied**
   ```bash
   aws sts get-caller-identity  # Verify credentials
   aws configure  # Reconfigure if needed
   ```

2. **RDS Snapshot Failures**
   - Check RDS instance status
   - Verify IAM permissions for snapshot creation
   - Monitor CloudWatch logs for errors

3. **S3 Access Issues**
   ```bash
   aws s3 ls s3://wheelsup-prod-published-snapshots/  # Test access
   ```

4. **Email Notifications Not Working**
   - Verify NOTIFICATION_EMAIL environment variable
   - Check mail server configuration
   - Review cron job logs

### Log Locations

- Script logs: `/path/to/project/logs/backup_verification_*.log`
- AWS CloudWatch: RDS and Backup service logs
- Cron logs: System cron log files

## Maintenance

### Monthly Tasks

1. Review backup costs and optimize retention policies
2. Test recovery procedures quarterly
3. Update IAM policies as needed
4. Monitor storage growth trends

### Annual Tasks

1. Review and update compliance requirements
2. Audit backup access logs
3. Update encryption keys (if nearing expiration)
4. Perform disaster recovery drills

---

**Author**: Cursor Agent Orange (PR-4.5)
**Last Updated**: 2025-11-11
