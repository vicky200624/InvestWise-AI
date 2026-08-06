#!/bin/bash
# =============================================================================
# InvestWise AI - PostgreSQL Daily Backup Script
# Creates encrypted PostgreSQL backups and uploads to S3
# =============================================================================

set -euo pipefail

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups/postgres}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-investwise_db}"
DB_USER="${DB_USER:-investwise_user}"
DB_PASSWORD="${DB_PASSWORD:-}"
S3_BUCKET="${S3_BUCKET:-}"
S3_PREFIX="${S3_PREFIX:-backups/postgres}"
ENCRYPTION_KEY="${ENCRYPTION_KEY:-}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/investwise_db_${TIMESTAMP}.sql.gz"
ENCRYPTED_FILE="${BACKUP_FILE}.enc"

# Create backup directory
mkdir -p "${BACKUP_DIR}"

echo "=============================================="
echo "Starting PostgreSQL backup at $(date)"
echo "=============================================="

# Create backup
echo "Creating database dump..."
PGPASSWORD="${DB_PASSWORD}" pg_dump \
    -h "${DB_HOST}" \
    -p "${DB_PORT}" \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    --format=custom \
    --compress=9 \
    --no-owner \
    --no-privileges \
    | gzip > "${BACKUP_FILE}"

# Verify backup was created
if [ ! -s "${BACKUP_FILE}" ]; then
    echo "ERROR: Backup file is empty or was not created"
    exit 1
fi

echo "Backup created: ${BACKUP_FILE} ($(du -h "${BACKUP_FILE}" | cut -f1))"

# Encrypt backup if encryption key is provided
if [ -n "${ENCRYPTION_KEY}" ]; then
    echo "Encrypting backup..."
    openssl enc -aes-256-cbc -salt -pbkdf2 \
        -in "${BACKUP_FILE}" \
        -out "${ENCRYPTED_FILE}" \
        -pass pass:"${ENCRYPTION_KEY}"
    rm "${BACKUP_FILE}"
    BACKUP_FILE="${ENCRYPTED_FILE}"
    echo "Backup encrypted: ${BACKUP_FILE}"
fi

# Upload to S3 if bucket is configured
if [ -n "${S3_BUCKET}" ]; then
    echo "Uploading backup to S3..."
    aws s3 cp "${BACKUP_FILE}" "s3://${S3_BUCKET}/${S3_PREFIX}/$(basename "${BACKUP_FILE}")" \
        --storage-class STANDARD_IA
    echo "Backup uploaded to S3"
fi

# Cleanup old backups
echo "Cleaning up backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "*.sql.gz*" -mtime "+${RETENTION_DAYS}" -delete

# Cleanup old S3 backups
if [ -n "${S3_BUCKET}" ]; then
    aws s3 ls "s3://${S3_BUCKET}/${S3_PREFIX}/" | while read -r line; do
        createDate=$(echo "$line" | awk '{print $1" "$2}')
        createDate=$(date -d "$createDate" +%s)
        olderThan=$(date -d "-${RETENTION_DAYS} days" +%s)
        if [ "$createDate" -lt "$olderThan" ]; then
            fileName=$(echo "$line" | awk '{print $4}')
            if [ -n "$fileName" ]; then
                echo "Deleting old backup: $fileName"
                aws s3 rm "s3://${S3_BUCKET}/${S3_PREFIX}/$fileName"
            fi
        fi
    done
fi

echo "=============================================="
echo "PostgreSQL backup completed at $(date)"
echo "=============================================="