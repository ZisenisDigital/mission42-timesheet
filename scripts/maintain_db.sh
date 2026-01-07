#!/bin/bash
set -e

# Mission42 Timesheet Database Maintenance Script
# Performs SQLite database optimization and cleanup

# Configuration
POCKETBASE_DATA_DIR="${POCKETBASE_DATA_DIR:-/opt/mission42-timesheet/pocketbase/pb_data}"
DB_FILE="${DB_FILE:-${POCKETBASE_DATA_DIR}/data.db}"
LOG_FILE="${LOG_FILE:-/var/log/mission42-maintenance.log}"
BACKUP_BEFORE_MAINTENANCE="${BACKUP_BEFORE_MAINTENANCE:-true}"

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

# Check if database exists
if [ ! -f "$DB_FILE" ]; then
    log_error "Database file not found: $DB_FILE"
    exit 1
fi

# Check if sqlite3 is installed
if ! command -v sqlite3 &> /dev/null; then
    log_error "sqlite3 is not installed"
    exit 1
fi

log_info "Starting database maintenance for Mission42 Timesheet..."
log_info "Database: $DB_FILE"

# Get database size before maintenance
SIZE_BEFORE=$(du -h "$DB_FILE" | cut -f1)
log_info "Database size before maintenance: $SIZE_BEFORE"

# Backup before maintenance (optional)
if [ "$BACKUP_BEFORE_MAINTENANCE" = "true" ]; then
    log_info "Creating backup before maintenance..."
    BACKUP_FILE="${DB_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    if cp "$DB_FILE" "$BACKUP_FILE"; then
        log_success "Backup created: $BACKUP_FILE"
    else
        log_error "Failed to create backup"
        exit 1
    fi
fi

# Perform integrity check
log_info "Performing integrity check..."
INTEGRITY_CHECK=$(sqlite3 "$DB_FILE" "PRAGMA integrity_check;")
if [ "$INTEGRITY_CHECK" = "ok" ]; then
    log_success "Integrity check passed"
else
    log_error "Integrity check failed: $INTEGRITY_CHECK"
    exit 1
fi

# Analyze the database
log_info "Analyzing database statistics..."
if sqlite3 "$DB_FILE" "ANALYZE;" 2>&1 | tee -a "$LOG_FILE"; then
    log_success "Database analysis completed"
else
    log_warning "Database analysis completed with warnings"
fi

# Reindex the database
log_info "Reindexing database..."
if sqlite3 "$DB_FILE" "REINDEX;" 2>&1 | tee -a "$LOG_FILE"; then
    log_success "Database reindexing completed"
else
    log_warning "Database reindexing completed with warnings"
fi

# Vacuum the database (reclaim unused space)
log_info "Running VACUUM to reclaim unused space..."
if sqlite3 "$DB_FILE" "VACUUM;" 2>&1 | tee -a "$LOG_FILE"; then
    log_success "Database VACUUM completed"
else
    log_error "Database VACUUM failed"
    exit 1
fi

# Get database size after maintenance
SIZE_AFTER=$(du -h "$DB_FILE" | cut -f1)
log_info "Database size after maintenance: $SIZE_AFTER"

# Calculate size savings
SIZE_BEFORE_BYTES=$(du -b "$DB_FILE.backup."* 2>/dev/null | tail -1 | cut -f1 || echo "0")
SIZE_AFTER_BYTES=$(du -b "$DB_FILE" | cut -f1)
if [ "$SIZE_BEFORE_BYTES" != "0" ]; then
    SAVED_BYTES=$((SIZE_BEFORE_BYTES - SIZE_AFTER_BYTES))
    SAVED_MB=$((SAVED_BYTES / 1024 / 1024))
    if [ $SAVED_BYTES -gt 0 ]; then
        log_success "Space reclaimed: ${SAVED_MB}MB"
    fi
fi

# Get database statistics
log_info "Database Statistics:"
sqlite3 "$DB_FILE" <<EOF | while IFS= read -r line; do log_info "  $line"; done
SELECT 'Total tables: ' || COUNT(*) FROM sqlite_master WHERE type='table';
SELECT 'Total indexes: ' || COUNT(*) FROM sqlite_master WHERE type='index';
EOF

# Table row counts
log_info "Table row counts:"
sqlite3 "$DB_FILE" "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '_pb_%';" | while IFS= read -r table; do
    if [ -n "$table" ]; then
        COUNT=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM \"$table\";")
        log_info "  $table: $COUNT rows"
    fi
done

# Clean up old backups (keep only last 3)
log_info "Cleaning up old maintenance backups..."
BACKUP_COUNT=$(ls -1 "${DB_FILE}.backup."* 2>/dev/null | wc -l)
if [ "$BACKUP_COUNT" -gt 3 ]; then
    ls -1t "${DB_FILE}.backup."* | tail -n +4 | while IFS= read -r old_backup; do
        if [ -f "$old_backup" ]; then
            rm -f "$old_backup"
            log_info "Removed old backup: $(basename "$old_backup")"
        fi
    done
    log_success "Old backups cleaned up (kept latest 3)"
else
    log_info "No old backups to clean up"
fi

# Optimize PocketBase-specific settings
log_info "Optimizing database settings..."
sqlite3 "$DB_FILE" <<EOF
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=10000;
PRAGMA temp_store=MEMORY;
EOF
log_success "Database settings optimized"

log_success "Database maintenance completed successfully!"
log_info "Summary:"
log_info "  - Integrity: OK"
log_info "  - Size before: $SIZE_BEFORE"
log_info "  - Size after: $SIZE_AFTER"

# Exit with success
exit 0
