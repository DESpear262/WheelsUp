#!/bin/bash
# WheelsUp Backup & Snapshot Verification Script
#
# This script performs automated verification of backup integrity:
# - Checks RDS snapshot creation and status
# - Verifies S3 backup file integrity
# - Validates ETL pipeline data snapshots
# - Sends alerts for backup failures
#
# Usage: ./create_snapshot.sh [environment] [check-only]
#   environment: dev|staging|prod (default: dev)
#   check-only: if provided, only checks existing backups, doesn't create new ones
#
# Author: Cursor Agent Orange (PR-4.5)
# Created: 2025-11-11

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
LOG_FILE="${PROJECT_ROOT}/logs/backup_verification_$(date +%Y%m%d_%H%M%S).log"
NOTIFICATION_EMAIL="${NOTIFICATION_EMAIL:-}"  # Set via environment

# Default values
ENVIRONMENT="${1:-dev}"
CHECK_ONLY="${2:-false}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# AWS Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
RDS_INSTANCE_ID="wheelsup-${ENVIRONMENT}-db"
BACKUP_BUCKET="wheelsup-${ENVIRONMENT}-published-snapshots"

# Logging functions
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] [${level}] ${message}" | tee -a "${LOG_FILE}"
}

error_exit() {
    local message="$1"
    log "ERROR" "${message}"
    send_notification "ERROR" "${message}"
    exit 1
}

send_notification() {
    local level="$1"
    local message="$2"

    if [[ -n "${NOTIFICATION_EMAIL}" ]]; then
        echo "Subject: WheelsUp ${ENVIRONMENT} Backup ${level}: $(date)

${message}

Log file: ${LOG_FILE}
Environment: ${ENVIRONMENT}
Timestamp: $(date)
" | mail -s "WheelsUp ${ENVIRONMENT} Backup ${level}" "${NOTIFICATION_EMAIL}"
    fi
}

# ============================================================================
# RDS Backup Verification
# ============================================================================

check_rds_snapshots() {
    log "INFO" "Checking RDS snapshots for instance: ${RDS_INSTANCE_ID}"

    # Get automated snapshots
    local automated_snapshots
    automated_snapshots=$(aws rds describe-db-snapshots \
        --db-instance-identifier "${RDS_INSTANCE_ID}" \
        --snapshot-type automated \
        --query 'DBSnapshots[?Status==`available`].[DBSnapshotIdentifier,SnapshotCreateTime]' \
        --output text \
        --region "${AWS_REGION}" 2>/dev/null || echo "")

    if [[ -z "${automated_snapshots}" ]]; then
        log "WARNING" "No automated RDS snapshots found"
        return 1
    fi

    # Check if we have a recent snapshot (within last 24 hours)
    local recent_snapshot_count
    recent_snapshot_count=$(echo "${automated_snapshots}" | \
        awk -v yesterday="$(date -d 'yesterday' +%s)" '
        {
            # Convert AWS timestamp to epoch
            cmd="date -d \"" $2 "\" +%s 2>/dev/null"
            cmd | getline timestamp
            close(cmd)
            if (timestamp > yesterday) count++
        }
        END { print count }
        ')

    if [[ "${recent_snapshot_count}" -gt 0 ]]; then
        log "INFO" "Found ${recent_snapshot_count} recent RDS automated snapshots"
        return 0
    else
        log "WARNING" "No RDS snapshots from the last 24 hours"
        return 1
    fi
}

create_rds_snapshot() {
    if [[ "${CHECK_ONLY}" == "true" ]]; then
        log "INFO" "Check-only mode: Skipping RDS snapshot creation"
        return 0
    fi

    log "INFO" "Creating manual RDS snapshot"

    local snapshot_id="wheelsup-${ENVIRONMENT}-manual-${TIMESTAMP}"

    if aws rds create-db-snapshot \
        --db-instance-identifier "${RDS_INSTANCE_ID}" \
        --db-snapshot-identifier "${snapshot_id}" \
        --region "${AWS_REGION}" >/dev/null 2>&1; then

        log "INFO" "RDS snapshot created: ${snapshot_id}"

        # Wait for snapshot to complete
        local attempts=0
        local max_attempts=30  # 15 minutes max wait

        while [[ $attempts -lt $max_attempts ]]; do
            local status
            status=$(aws rds describe-db-snapshots \
                --db-snapshot-identifier "${snapshot_id}" \
                --query 'DBSnapshots[0].Status' \
                --output text \
                --region "${AWS_REGION}" 2>/dev/null || echo "unknown")

            if [[ "${status}" == "available" ]]; then
                log "INFO" "RDS snapshot ${snapshot_id} completed successfully"
                return 0
            elif [[ "${status}" == "failed" ]]; then
                error_exit "RDS snapshot ${snapshot_id} failed"
            fi

            sleep 30
            ((attempts++))
        done

        error_exit "RDS snapshot ${snapshot_id} timed out"
    else
        error_exit "Failed to create RDS snapshot"
    fi
}

# ============================================================================
# S3 Backup Verification
# ============================================================================

check_s3_backups() {
    log "INFO" "Checking S3 backup integrity"

    # Check if backup bucket exists and is accessible
    if ! aws s3 ls "s3://${BACKUP_BUCKET}/" --region "${AWS_REGION}" >/dev/null 2>&1; then
        log "ERROR" "Cannot access S3 backup bucket: ${BACKUP_BUCKET}"
        return 1
    fi

    # Check for recent ETL snapshots (within last 7 days)
    local recent_objects
    recent_objects=$(aws s3api list-objects-v2 \
        --bucket "${BACKUP_BUCKET}" \
        --prefix "snapshots/" \
        --query 'Contents[?LastModified>=`'"$(date -d '7 days ago' +%Y-%m-%d)"'`].[Key,LastModified]' \
        --output text \
        --region "${AWS_REGION}" 2>/dev/null || echo "")

    if [[ -z "${recent_objects}" ]]; then
        log "WARNING" "No recent ETL snapshots found in S3 bucket"
        return 1
    fi

    local snapshot_count
    snapshot_count=$(echo "${recent_objects}" | wc -l)
    log "INFO" "Found ${snapshot_count} recent ETL snapshots in S3"

    # Check integrity of most recent snapshot
    local latest_snapshot
    latest_snapshot=$(echo "${recent_objects}" | sort -k2 | tail -1 | awk '{print $1}')

    if [[ -n "${latest_snapshot}" ]]; then
        log "INFO" "Verifying integrity of latest snapshot: ${latest_snapshot}"

        # Download and verify the snapshot file
        local temp_file="/tmp/snapshot_verify_${TIMESTAMP}.json"

        if aws s3 cp "s3://${BACKUP_BUCKET}/${latest_snapshot}" "${temp_file}" \
            --region "${AWS_REGION}" >/dev/null 2>&1; then

            # Check if it's valid JSON
            if jq empty "${temp_file}" >/dev/null 2>&1; then
                log "INFO" "Latest snapshot is valid JSON"
                rm -f "${temp_file}"
                return 0
            else
                log "ERROR" "Latest snapshot is not valid JSON"
                rm -f "${temp_file}"
                return 1
            fi
        else
            log "ERROR" "Failed to download latest snapshot for verification"
            return 1
        fi
    fi

    return 0
}

# ============================================================================
# ETL Pipeline Data Verification
# ============================================================================

check_etl_pipeline() {
    log "INFO" "Checking ETL pipeline data integrity"

    # Check for ETL logs and verify recent activity
    local log_bucket="wheelsup-${ENVIRONMENT}-logs"

    # Look for ETL logs from the last 24 hours
    local recent_logs
    recent_logs=$(aws s3api list-objects-v2 \
        --bucket "${log_bucket}" \
        --prefix "etl/" \
        --query 'Contents[?LastModified>=`'"$(date -d 'yesterday' +%Y-%m-%d)"'`].[Key]' \
        --output text \
        --region "${AWS_REGION}" 2>/dev/null || echo "")

    if [[ -z "${recent_logs}" ]]; then
        log "WARNING" "No recent ETL logs found (last 24 hours)"
        return 1
    fi

    local log_count
    log_count=$(echo "${recent_logs}" | wc -l)
    log "INFO" "Found ${log_count} recent ETL log files"

    # Check for any error logs
    local error_logs
    error_logs=$(echo "${recent_logs}" | grep -i error || echo "")

    if [[ -n "${error_logs}" ]]; then
        log "WARNING" "Found error logs in recent ETL runs"
        # Don't fail here, just warn
    fi

    return 0
}

# ============================================================================
# AWS Backup Service Verification
# ============================================================================

check_aws_backup_jobs() {
    log "INFO" "Checking AWS Backup job status"

    # Check backup jobs from the last 24 hours
    local recent_jobs
    recent_jobs=$(aws backup list-backup-jobs \
        --by-created-after "$(date -d 'yesterday' +%s)" \
        --query 'BackupJobs[?Status==`COMPLETED` || Status==`FAILED`].[BackupJobId,Status,CreationDate]' \
        --output text \
        --region "${AWS_REGION}" 2>/dev/null || echo "")

    if [[ -z "${recent_jobs}" ]]; then
        log "WARNING" "No AWS Backup jobs found in the last 24 hours"
        return 1
    fi

    # Check for failed jobs
    local failed_jobs
    failed_jobs=$(echo "${recent_jobs}" | grep FAILED || echo "")

    if [[ -n "${failed_jobs}" ]]; then
        log "ERROR" "Found failed AWS Backup jobs"
        echo "${failed_jobs}" | while read -r job_id status date; do
            log "ERROR" "Failed backup job: ${job_id} (${date})"
        done
        return 1
    fi

    local completed_jobs
    completed_jobs=$(echo "${recent_jobs}" | grep COMPLETED | wc -l)
    log "INFO" "Found ${completed_jobs} successful AWS Backup jobs in the last 24 hours"

    return 0
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    log "INFO" "Starting WheelsUp backup verification for environment: ${ENVIRONMENT}"

    local checks_passed=0
    local total_checks=0

    # RDS Snapshot Check
    ((total_checks++))
    if check_rds_snapshots; then
        ((checks_passed++))
    fi

    # S3 Backup Check
    ((total_checks++))
    if check_s3_backups; then
        ((checks_passed++))
    fi

    # ETL Pipeline Check
    ((total_checks++))
    if check_etl_pipeline; then
        ((checks_passed++))
    fi

    # AWS Backup Check
    ((total_checks++))
    if check_aws_backup_jobs; then
        ((checks_passed++))
    fi

    # Create snapshots if not in check-only mode
    if [[ "${CHECK_ONLY}" != "true" ]]; then
        log "INFO" "Creating additional backup snapshots"
        create_rds_snapshot
    fi

    # Summary
    log "INFO" "Backup verification completed: ${checks_passed}/${total_checks} checks passed"

    if [[ ${checks_passed} -eq ${total_checks} ]]; then
        send_notification "SUCCESS" "All backup checks passed (${checks_passed}/${total_checks})"
        exit 0
    else
        send_notification "WARNING" "Some backup checks failed (${checks_passed}/${total_checks})"
        exit 1
    fi
}

# ============================================================================
# Script Entry Point
# ============================================================================

# Validate environment
case "${ENVIRONMENT}" in
    dev|staging|prod)
        ;;
    *)
        error_exit "Invalid environment: ${ENVIRONMENT}. Must be dev, staging, or prod."
        ;;
esac

# Validate AWS CLI access
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    error_exit "AWS CLI not configured or credentials invalid"
fi

# Validate jq is available
if ! command -v jq >/dev/null 2>&1; then
    error_exit "jq is required but not installed"
fi

# Run main function
main "$@"
