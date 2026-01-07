#!/bin/bash
set -e

# Mission42 Timesheet Backup Script
# Automated backup of PocketBase data with rotation

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups/mission42-timesheet}"
POCKETBASE_DATA_DIR="${POCKETBASE_DATA_DIR:-/opt/mission42-timesheet/pocketbase/pb_data}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
LOG_FILE="${LOG_FILE:-/var/log/mission42-backup.log}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# Check if source directory exists
if [ ! -d "$POCKETBASE_DATA_DIR" ]; then
    log_error "PocketBase data directory not found: $POCKETBASE_DATA_DIR"
    exit 1
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Generate backup filename with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="pb_data_${TIMESTAMP}.tar.gz"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILE}"

log_info "Starting backup of Mission42 Timesheet..."
log_info "Source: $POCKETBASE_DATA_DIR"
log_info "Destination: $BACKUP_PATH"

# Create backup with compression
log_info "Creating compressed backup..."
if tar -czf "$BACKUP_PATH" -C "$(dirname "$POCKETBASE_DATA_DIR")" "$(basename "$POCKETBASE_DATA_DIR")" 2>&1 | tee -a "$LOG_FILE"; then
    BACKUP_SIZE=$(du -h "$BACKUP_PATH" | cut -f1)
    log_success "Backup created successfully: $BACKUP_FILE (Size: $BACKUP_SIZE)"
else
    log_error "Backup creation failed"
    exit 1
fi

# Verify backup integrity
log_info "Verifying backup integrity..."
if tar -tzf "$BACKUP_PATH" > /dev/null 2>&1; then
    log_success "Backup integrity verified"
else
    log_error "Backup integrity check failed"
    exit 1
fi

# Create checksum
log_info "Creating checksum..."
CHECKSUM_FILE="${BACKUP_PATH}.sha256"
if sha256sum "$BACKUP_PATH" > "$CHECKSUM_FILE"; then
    log_success "Checksum created: ${BACKUP_FILE}.sha256"
else
    log_warning "Failed to create checksum"
fi

# Remove old backups based on retention policy
log_info "Cleaning up old backups (retention: ${RETENTION_DAYS} days)..."
DELETED_COUNT=0
while IFS= read -r old_backup; do
    if [ -f "$old_backup" ]; then
        rm -f "$old_backup"
        rm -f "${old_backup}.sha256"
        DELETED_COUNT=$((DELETED_COUNT + 1))
        log_info "Deleted old backup: $(basename "$old_backup")"
    fi
done < <(find "$BACKUP_DIR" -name "pb_data_*.tar.gz" -type f -mtime +"$RETENTION_DAYS")

if [ $DELETED_COUNT -gt 0 ]; then
    log_success "Removed $DELETED_COUNT old backup(s)"
else
    log_info "No old backups to remove"
fi

# Display backup summary
log_info "Backup Summary:"
log_info "  Total backups: $(find "$BACKUP_DIR" -name "pb_data_*.tar.gz" -type f | wc -l)"
log_info "  Total size: $(du -sh "$BACKUP_DIR" | cut -f1)"
log_info "  Latest backup: $BACKUP_FILE ($BACKUP_SIZE)"

log_success "Backup completed successfully!"

# Exit with success
exit 0
