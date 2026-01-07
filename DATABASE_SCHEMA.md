# Database Schema Reference

## Location

**Database file:**
```
/Users/mr-jy/github/mission42-timesheet/pocketbase/pocketbase/pb_data/data.db
```

**Access via:**
- PocketBase Admin UI: http://127.0.0.1:8090/_/
- SQLite CLI: `sqlite3 <path-to-db>`
- REST API: http://127.0.0.1:8090/api/collections

---

## Collections (Tables)

### 1. **settings** (31 records)

Configuration key-value storage for all app settings.

**Schema:**
```sql
CREATE TABLE settings (
    id TEXT PRIMARY KEY NOT NULL,
    created TEXT DEFAULT (datetime('now')) NOT NULL,
    updated TEXT DEFAULT (datetime('now')) NOT NULL,
    key TEXT NOT NULL UNIQUE,              -- Setting key (e.g., "work_week_start_day")
    value TEXT NOT NULL,                   -- Setting value (stored as text)
    type TEXT NOT NULL,                    -- Data type: string, number, boolean
    category TEXT NOT NULL,                -- Category: core, wakatime, github, etc.
    description TEXT,                      -- Human-readable description
    validation_rules TEXT                  -- JSON validation rules (optional)
);
```

**Example records:**
- `work_week_start_day`: "monday"
- `target_hours_per_week`: "40"
- `wakatime_enabled`: "true"
- `github_repositories`: "altacarn/acr-hub"

**View all settings:**
```bash
./scripts/show_tables.sh settings
```

---

### 2. **work_packages** (6 records)

Billable project categories for time tracking.

**Schema:**
```sql
CREATE TABLE work_packages (
    id TEXT PRIMARY KEY NOT NULL,
    created TEXT DEFAULT (datetime('now')) NOT NULL,
    updated TEXT DEFAULT (datetime('now')) NOT NULL,
    name TEXT NOT NULL UNIQUE,             -- Package name (e.g., "Development")
    description TEXT,                      -- Description
    is_active INTEGER NOT NULL DEFAULT 1,  -- Active status (1=active, 0=inactive)
    is_default INTEGER NOT NULL DEFAULT 0  -- Default package (1=default, 0=not default)
);
```

**Default packages:**
- Development (default)
- Planning
- Testing
- Troubleshooting
- Meetings
- Emails

**View work packages:**
```bash
./scripts/show_tables.sh work_packages
```

---

### 3. **project_specs** (6 records)

Granular project specifications within work packages.

**Schema:**
```sql
CREATE TABLE project_specs (
    id TEXT PRIMARY KEY NOT NULL,
    created TEXT DEFAULT (datetime('now')) NOT NULL,
    updated TEXT DEFAULT (datetime('now')) NOT NULL,
    name TEXT NOT NULL UNIQUE,             -- Spec name (e.g., "Backend")
    description TEXT,                      -- Description
    work_package TEXT,                     -- Associated work package
    is_active INTEGER NOT NULL DEFAULT 1   -- Active status
);
```

**Default specs:**
- Lead
- Backend
- Frontend
- Infrastructure
- Documentation
- Other

**View project specs:**
```bash
./scripts/show_tables.sh project_specs
```

---

### 4. **raw_events** (0 records - awaiting data)

Raw events from all data sources (WakaTime, GitHub, Calendar, Gmail).

**Schema:**
```sql
CREATE TABLE raw_events (
    id TEXT PRIMARY KEY NOT NULL,
    created TEXT DEFAULT (datetime('now')) NOT NULL,
    updated TEXT DEFAULT (datetime('now')) NOT NULL,
    source TEXT NOT NULL,                  -- Source: wakatime, github, calendar, gmail, cloud_events
    source_id TEXT NOT NULL,               -- Unique ID from source
    timestamp TEXT NOT NULL,               -- Event timestamp (ISO 8601)
    duration_minutes INTEGER NOT NULL,     -- Duration in minutes
    description TEXT NOT NULL,             -- Event description
    metadata TEXT                          -- JSON metadata from source
);
```

**Indexes:**
- `idx_raw_events_source` on `source`
- `idx_raw_events_timestamp` on `timestamp`
- `idx_raw_events_source_id` on `(source, source_id)` (unique)

**Example raw event:**
```json
{
  "source": "wakatime",
  "source_id": "waka_12345",
  "timestamp": "2026-01-07T10:30:00Z",
  "duration_minutes": 120,
  "description": "Coding: Python",
  "metadata": {
    "project": "mission42-timesheet",
    "language": "Python",
    "editor": "VSCode"
  }
}
```

**View raw events:**
```bash
./scripts/show_tables.sh raw_events
```

---

### 5. **time_blocks** (0 records - awaiting processing)

Processed 30-minute time blocks with overlap resolution.

**Schema:**
```sql
CREATE TABLE time_blocks (
    id TEXT PRIMARY KEY NOT NULL,
    created TEXT DEFAULT (datetime('now')) NOT NULL,
    updated TEXT DEFAULT (datetime('now')) NOT NULL,
    week_start TEXT NOT NULL,              -- Start of work week (ISO 8601)
    block_start TEXT NOT NULL,             -- Block start time
    block_end TEXT NOT NULL,               -- Block end time
    source TEXT NOT NULL,                  -- Source: wakatime, github, calendar, gmail, auto_fill
    description TEXT NOT NULL,             -- Block description
    duration_hours REAL NOT NULL,          -- Duration in hours (e.g., 0.5, 1.0, 2.0)
    metadata TEXT                          -- JSON metadata
);
```

**Indexes:**
- `idx_time_blocks_week_start` on `week_start`
- `idx_time_blocks_source` on `source`
- `idx_time_blocks_block_start` on `block_start`

**Example time block:**
```json
{
  "week_start": "2026-01-05T18:00:00",
  "block_start": "2026-01-07T10:00:00",
  "block_end": "2026-01-07T12:00:00",
  "source": "wakatime",
  "description": "Development: Python coding",
  "duration_hours": 2.0,
  "metadata": {
    "project": "mission42-timesheet",
    "auto_generated": false
  }
}
```

**View time blocks:**
```bash
./scripts/show_tables.sh time_blocks
```

---

### 6. **week_summaries** (0 records - awaiting processing)

Weekly hour summaries and statistics.

**Schema:**
```sql
CREATE TABLE week_summaries (
    id TEXT PRIMARY KEY NOT NULL,
    created TEXT DEFAULT (datetime('now')) NOT NULL,
    updated TEXT DEFAULT (datetime('now')) NOT NULL,
    week_start TEXT NOT NULL UNIQUE,       -- Start of work week (ISO 8601)
    total_hours REAL NOT NULL DEFAULT 0,   -- Total hours for the week
    metadata TEXT                          -- JSON metadata (hours_filled, etc.)
);
```

**Indexes:**
- `idx_week_summaries_week_start` on `week_start` (unique)

**Example summary:**
```json
{
  "week_start": "2026-01-05T18:00:00",
  "total_hours": 42.5,
  "metadata": {
    "week_end": "2026-01-10T18:00:00",
    "hours_filled": 2.5,
    "breakdown": {
      "wakatime": 30.0,
      "github": 5.0,
      "calendar": 5.0,
      "auto_fill": 2.5
    }
  }
}
```

**View week summaries:**
```bash
./scripts/show_tables.sh week_summaries
```

---

### 7. **calendar_accounts** (0 records - awaiting OAuth)

OAuth tokens for Google Calendar access.

**Schema:**
```sql
CREATE TABLE calendar_accounts (
    id TEXT PRIMARY KEY NOT NULL,
    created TEXT DEFAULT (datetime('now')) NOT NULL,
    updated TEXT DEFAULT (datetime('now')) NOT NULL,
    user_email TEXT NOT NULL UNIQUE,       -- Google account email
    oauth_token TEXT NOT NULL,             -- Encrypted OAuth token (JSON)
    calendar_id TEXT,                      -- Primary calendar ID
    last_sync TEXT,                        -- Last sync timestamp
    is_active INTEGER NOT NULL DEFAULT 1   -- Active status
);
```

**View calendar accounts:**
```bash
./scripts/show_tables.sh calendar_accounts
```

---

### 8. **email_accounts** (0 records - awaiting OAuth)

OAuth tokens for Gmail access.

**Schema:**
```sql
CREATE TABLE email_accounts (
    id TEXT PRIMARY KEY NOT NULL,
    created TEXT DEFAULT (datetime('now')) NOT NULL,
    updated TEXT DEFAULT (datetime('now')) NOT NULL,
    user_email TEXT NOT NULL UNIQUE,       -- Gmail account email
    oauth_token TEXT NOT NULL,             -- Encrypted OAuth token (JSON)
    last_sync TEXT,                        -- Last sync timestamp
    is_active INTEGER NOT NULL DEFAULT 1   -- Active status
);
```

**View email accounts:**
```bash
./scripts/show_tables.sh email_accounts
```

---

## Quick Access Commands

### View all tables
```bash
./scripts/show_tables.sh
```

### View specific table
```bash
./scripts/show_tables.sh <table_name>
# Examples:
./scripts/show_tables.sh settings
./scripts/show_tables.sh raw_events
./scripts/show_tables.sh time_blocks
```

### Direct SQLite queries
```bash
DB="/Users/mr-jy/github/mission42-timesheet/pocketbase/pocketbase/pb_data/data.db"

# Count records
sqlite3 "$DB" "SELECT COUNT(*) FROM settings;"

# View all settings
sqlite3 -header -column "$DB" "SELECT key, value, category FROM settings ORDER BY category;"

# View work packages
sqlite3 -header -column "$DB" "SELECT name, description FROM work_packages WHERE is_active=1;"

# View raw events for today
sqlite3 -header -column "$DB" "SELECT source, description, duration_minutes FROM raw_events WHERE date(timestamp) = date('now');"
```

### Via PocketBase API
```bash
# List all collections
curl http://127.0.0.1:8090/api/collections | jq

# Get settings
curl http://127.0.0.1:8090/api/collections/settings/records | jq

# Get work packages
curl http://127.0.0.1:8090/api/collections/work_packages/records | jq

# Get raw events
curl http://127.0.0.1:8090/api/collections/raw_events/records | jq
```

---

## Data Flow

```
1. Data Sources (WakaTime, GitHub, Calendar, Gmail)
   ↓
2. Fetchers collect raw data
   ↓
3. Stored in: raw_events table
   ↓
4. Processor converts to 30-min blocks
   ↓
5. Stored in: time_blocks table
   ↓
6. Weekly aggregation
   ↓
7. Stored in: week_summaries table
   ↓
8. Export to HTML/CSV/Excel
```

---

## Database Location

**File path:**
```
/Users/mr-jy/github/mission42-timesheet/pocketbase/pocketbase/pb_data/data.db
```

**Backup database:**
```bash
cp /Users/mr-jy/github/mission42-timesheet/pocketbase/pocketbase/pb_data/data.db \
   ~/Desktop/mission42-backup-$(date +%Y%m%d).db
```

**View database size:**
```bash
ls -lh /Users/mr-jy/github/mission42-timesheet/pocketbase/pocketbase/pb_data/data.db
```

---

## Migration History

Collections were created using direct SQL due to PocketBase migration issues:
- Script: `scripts/create_all_collections.sh`
- Method: Direct SQLite table creation + metadata registration
- Date: 2026-01-07
