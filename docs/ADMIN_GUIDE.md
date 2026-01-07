# PocketBase Admin Guide

Complete guide for administering the Mission42 Timesheet system via PocketBase admin UI.

## Table of Contents

- [Initial Setup](#initial-setup)
- [Accessing Admin UI](#accessing-admin-ui)
- [Managing Settings](#managing-settings)
- [Managing Work Packages](#managing-work-packages)
- [Managing Project Specs](#managing-project-specs)
- [Managing Accounts](#managing-accounts)
- [Viewing Data](#viewing-data)
- [Common Tasks](#common-tasks)
- [Troubleshooting](#troubleshooting)

## Initial Setup

### 1. Download and Start PocketBase

```bash
# Download PocketBase (if not already done)
./scripts/download_pocketbase.sh

# Start PocketBase
cd pocketbase
./pocketbase serve
```

PocketBase will start on **http://127.0.0.1:8090**

### 2. Create Admin Account

On first run, navigate to **http://127.0.0.1:8090/_/** and you'll be prompted to create an admin account:

- **Email**: Your admin email (e.g., admin@example.com)
- **Password**: Strong password (minimum 8 characters)

**Important**: Save these credentials securely!

### 3. Run Migrations

PocketBase will automatically run migrations on startup. Verify all collections exist:

Navigate to **Collections** in the admin UI and verify you see:
- settings
- raw_events
- time_blocks
- week_summaries
- claude_time_tracking
- email_accounts
- calendar_accounts
- work_packages
- project_specs

### 4. Seed Default Data

Run the seed scripts to populate default configuration:

```bash
# Seed settings (31 configuration values)
python scripts/seed_settings.py

# Seed work packages (6 default categories)
python scripts/seed_work_packages.py

# Seed project specs (6 default specifications)
python scripts/seed_project_specs.py
```

Verify data was seeded by checking the collections in the admin UI.

## Accessing Admin UI

**URL**: http://127.0.0.1:8090/_/

**Login**: Use the admin credentials you created during setup

### Admin UI Navigation

- **Collections**: View and manage all data tables
- **Logs**: View system logs and API requests
- **Settings**: Configure PocketBase settings (advanced)
- **Admins**: Manage admin accounts

## Managing Settings

Settings control all system behavior. Navigate to **Collections** → **settings**.

### Viewing Settings

Click on any setting row to view/edit its value.

Settings are organized by category:
- **core** (10 settings) - Work week, scheduling, auto-fill
- **wakatime** (1 setting) - WakaTime integration
- **calendar** (2 settings) - Google Calendar integration
- **gmail** (3 settings) - Gmail integration
- **github** (5 settings) - GitHub integration
- **cloud_events** (1 setting) - Custom events
- **processing** (7 settings) - Time block processing rules
- **export** (2 settings) - Export formatting

### Editing a Setting

1. Click on the setting row
2. Modify the **value** field
3. Click **Save**
4. Changes take effect on next fetch/process cycle

### Important Settings

**Work Week Definition**:
- `work_week_start_day`: Default "monday"
- `work_week_start_time`: Default "18:00" (6 PM)
- `work_week_end_day`: Default "saturday"
- `work_week_end_time`: Default "18:00" (6 PM)

**Processing Behavior**:
- `target_hours_per_week`: Default 40 (minimum hours per week)
- `auto_fill_enabled`: Default true (enables automatic filling to target)
- `fetch_interval_hours`: Default 5 (how often to fetch data)

**Data Sources**:
- `wakatime_enabled`: Enable/disable WakaTime fetching
- `calendar_enabled`: Enable/disable Calendar fetching
- `gmail_enabled`: Enable/disable Gmail fetching
- `github_enabled`: Enable/disable GitHub fetching
- `cloud_events_enabled`: Enable/disable Claude Code tracking

## Managing Work Packages

Work packages are billable project categories. Navigate to **Collections** → **work_packages**.

### Default Work Packages

After seeding, you'll have:
- **Development** (default) - General software development
- **Planning** - Project planning and architecture
- **Testing** - QA and testing activities
- **Troubleshooting** - Debugging and issue resolution
- **Meetings** - Team meetings and calls
- **Emails** - Email correspondence

### Adding a Work Package

1. Click **+ New Record**
2. Fill in fields:
   - **name**: Unique identifier (e.g., "Research")
   - **description**: Brief explanation
   - **is_active**: true (to enable)
   - **is_default**: true (only one should be default)
3. Click **Create**

### Editing a Work Package

1. Click on the work package row
2. Modify fields as needed
3. Click **Save**

### Deactivating a Work Package

1. Click on the work package
2. Set **is_active** to false
3. Click **Save**

This hides it from selection but preserves historical data.

## Managing Project Specs

Project specs provide granular categorization within work packages. Navigate to **Collections** → **project_specs**.

### Default Project Specs

After seeding:
- **Lead** - Technical leadership
- **Backend** - Server-side development
- **Frontend** - Client-side development
- **Infrastructure** - DevOps and deployment
- **Documentation** - Technical writing
- **Other** - Miscellaneous tasks

### Adding a Project Spec

1. Click **+ New Record**
2. Fill in fields:
   - **name**: Unique identifier (e.g., "Mobile")
   - **description**: Brief explanation
   - **work_package**: Associated work package (optional)
   - **is_active**: true
3. Click **Create**

### Editing/Deactivating

Same process as work packages.

## Managing Accounts

### Gmail Accounts

Navigate to **Collections** → **email_accounts**.

**Fields**:
- **email**: Gmail address
- **display_name**: Friendly name (optional)
- **encrypted_token**: OAuth token (managed by system)
- **is_active**: Enable/disable this account
- **last_sync**: Last fetch timestamp

**Adding an Account**:
OAuth flow is managed through the FastAPI application. See [OAUTH_GUIDE.md](OAUTH_GUIDE.md) for setup.

### Calendar Accounts

Navigate to **Collections** → **calendar_accounts**.

**Fields**:
- **email**: Google account email
- **display_name**: Friendly name (optional)
- **calendar_id**: Calendar ID (optional, defaults to primary)
- **encrypted_token**: OAuth token (managed by system)
- **is_active**: Enable/disable
- **last_sync**: Last fetch timestamp

**Adding an Account**:
OAuth flow is managed through the FastAPI application. See [OAUTH_GUIDE.md](OAUTH_GUIDE.md) for setup.

## Viewing Data

### Raw Events

Navigate to **Collections** → **raw_events**.

View all fetched events from data sources before processing:
- **source**: wakatime, calendar, gmail, github, cloud_events
- **source_id**: Unique ID from source
- **timestamp**: Event date/time
- **duration_minutes**: Duration
- **description**: Event description
- **metadata**: Additional data (JSON)

**Filters**:
- Filter by source: `source = "wakatime"`
- Filter by date: `timestamp >= "2026-01-01"`
- Combine: `source = "calendar" && timestamp >= "2026-01-01"`

### Time Blocks

Navigate to **Collections** → **time_blocks**.

View processed 30-minute billable blocks:
- **week_start**: Work week start date
- **block_start**: Block start time
- **block_end**: Block end time
- **source**: Original data source
- **description**: Block description
- **duration_hours**: Duration in hours (0.5 increments)
- **metadata**: Additional data (JSON)

**Filters**:
- View specific week: `week_start = "2026-01-06T18:00:00Z"`
- View auto-filled: `source = "auto_fill"`
- View by source: `source = "wakatime"`

### Week Summaries

Navigate to **Collections** → **week_summaries**.

View weekly totals and statistics:
- **week_start**: Work week start date
- **total_hours**: Total hours for the week
- **metadata**: Additional statistics (JSON)

**Metadata includes**:
- week_end: End of work week
- hours_filled: Auto-filled hours
- Additional processing info

### Claude Time Tracking

Navigate to **Collections** → **claude_time_tracking**.

View Claude Code AI assistant usage:
- **session_id**: Unique session identifier
- **tool_name**: Tool used
- **description**: Session description
- **started_at**: Session start
- **completed_at**: Session end
- **duration**: Duration in seconds
- **status**: Session status
- **topic**: Task topic
- **project**: Project name

## Common Tasks

### Task 1: Change Work Week Hours

**Goal**: Change from 40h to 35h per week

1. Navigate to **Collections** → **settings**
2. Find setting with key "target_hours_per_week"
3. Click to edit
4. Change **value** from "40" to "35"
5. Click **Save**

Next Monday fill-up job will use 35h target.

### Task 2: Disable Gmail Tracking

**Goal**: Stop fetching Gmail data

1. Navigate to **Collections** → **settings**
2. Find setting with key "gmail_enabled"
3. Click to edit
4. Change **value** from "true" to "false"
5. Click **Save**

Gmail data will no longer be fetched.

### Task 3: View This Week's Time Blocks

**Goal**: See all time blocks for current week

1. Navigate to **Collections** → **time_blocks**
2. Click **Filters**
3. Set filter: `week_start >= "2026-01-06T18:00:00Z"`
   (Replace with your current Monday 6 PM)
4. Click **Apply**

### Task 4: Change Fetch Interval

**Goal**: Fetch data every 3 hours instead of 5

1. Navigate to **Collections** → **settings**
2. Find setting with key "fetch_interval_hours"
3. Click to edit
4. Change **value** from "5" to "3"
5. Click **Save**
6. **Restart the scheduler** for changes to take effect

### Task 5: Add Custom Work Package

**Goal**: Add "Research" category

1. Navigate to **Collections** → **work_packages**
2. Click **+ New Record**
3. Fill in:
   - name: "Research"
   - description: "Research and learning activities"
   - is_active: true
   - is_default: false
4. Click **Create**

### Task 6: Export Week Data

**Goal**: Download week data as JSON

1. Navigate to **Collections** → **time_blocks**
2. Filter for desired week
3. Click **Export** button (top right)
4. Select format (JSON, CSV)
5. Click **Download**

## Troubleshooting

### PocketBase Won't Start

**Symptoms**: Error when running `./pocketbase serve`

**Solutions**:
- Check if port 8090 is in use: `lsof -i :8090`
- Kill existing process: `kill -9 <PID>`
- Check file permissions: `chmod +x pocketbase`
- Check logs in `pocketbase/pb_data/logs/`

### Can't Login to Admin UI

**Symptoms**: Invalid credentials error

**Solutions**:
- Verify admin email/password
- Reset admin password via CLI:
  ```bash
  cd pocketbase
  ./pocketbase admin create admin@example.com newpassword123
  ```
- Check PocketBase logs for errors

### Settings Not Taking Effect

**Symptoms**: Changed settings but behavior unchanged

**Solutions**:
- Restart FastAPI application
- Restart background scheduler
- Check setting **type** matches **value** format:
  - type="number" → value="40" (no decimals for integers)
  - type="boolean" → value="true" or "false"
  - type="string" → value="any text"
- Check PocketBase logs for validation errors

### No Data Being Fetched

**Symptoms**: raw_events collection is empty

**Solutions**:
- Verify data source is enabled in settings
- Check API keys in `.env` file
- Verify OAuth tokens are valid (for Gmail/Calendar)
- Check FastAPI logs: `tail -f logs/app.log`
- Manually trigger fetch:
  ```bash
  curl -X POST http://localhost:8000/process/manual
  ```

### Auto-fill Not Working

**Symptoms**: Weeks not filling to 40 hours

**Solutions**:
- Check `auto_fill_enabled` is "true"
- Check `target_hours_per_week` setting
- Verify work week definition (Monday 6 PM → Saturday 6 PM)
- Auto-fill only runs on Monday at work_week_start_time
- Check scheduler logs for errors

### Collections Missing

**Symptoms**: Expected collections don't exist

**Solutions**:
- Stop PocketBase
- Run migrations manually:
  ```bash
  cd pocketbase
  ./pocketbase migrate up
  ```
- Check migration files in `pocketbase/pb_migrations/`
- Restart PocketBase

## Best Practices

### 1. Regular Backups

Backup PocketBase data regularly:

```bash
# Stop PocketBase
cd pocketbase
./pocketbase stop

# Backup database
cp -r pb_data pb_data_backup_$(date +%Y%m%d)

# Restart PocketBase
./pocketbase serve
```

### 2. Monitor Logs

Regularly check PocketBase logs:

```bash
cd pocketbase/pb_data/logs
tail -f $(ls -t | head -1)
```

### 3. Validate Settings Changes

After changing critical settings:
- Verify in UI
- Test with manual fetch
- Check resulting time blocks

### 4. Keep OAuth Tokens Fresh

OAuth tokens expire. Monitor:
- `email_accounts.last_sync`
- `calendar_accounts.last_sync`

If not updating, re-authenticate.

### 5. Clean Old Data Periodically

Archive or delete old data:
- raw_events older than 6 months
- time_blocks older than 2 years
- Use PocketBase filters to bulk delete

## Security Notes

### Access Control

PocketBase admin UI should only be accessible locally (127.0.0.1). For production:

1. Enable authentication
2. Use reverse proxy (nginx) with SSL
3. Restrict IP access
4. Use strong admin passwords

### API Keys

Never commit `.env` file. Keep API keys secure:
- Use environment-specific .env files
- Rotate keys periodically
- Use read-only tokens where possible

### OAuth Tokens

OAuth tokens are encrypted in database using ENCRYPTION_KEY from `.env`. Keep this key secure and backed up.

## Support

For issues:
- Check PocketBase logs: `pocketbase/pb_data/logs/`
- Check FastAPI logs: `logs/app.log`
- GitHub Issues: https://github.com/ZisenisDigital/mission42-timesheet/issues
- PocketBase Docs: https://pocketbase.io/docs/
