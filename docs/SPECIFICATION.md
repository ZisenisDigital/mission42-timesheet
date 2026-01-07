# Mission42 Timesheet - Technical Specification

Complete specification of timesheet processing rules and output format based on implemented system.

**Version**: 1.0.0
**Last Updated**: 2026-01-07
**Status**: Implemented and Production-Ready

---

## Table of Contents

- [Output Format](#output-format)
- [Processing Rules](#processing-rules)
- [Configuration Options](#configuration-options)
- [Data Source Priorities](#data-source-priorities)
- [Export Formats](#export-formats)

---

## Output Format

### Monthly View Structure

The system exports timesheets in monthly format (not weekly) with the following structure:

```
Zeiterfassung - {Name}
Monat: {Month Name} {Year}
Erstellt am: {DD.MM.YYYY HH:MM} | Gesamt: {Total} Stunden

╔═══════╦════════════╦═════════╦═══════════════════════════════════╦═══════╗
║  Nr.  ║   Datum    ║ Stunden ║           Beschreibung            ║  Ort  ║
╠═══════╬════════════╬═════════╬═══════════════════════════════════╬═══════╣
║ 0001  ║ 05.01.2026 ║    2.0  ║ Coding: mission42-timesheet       ║ Remote║
║ 0002  ║ 05.01.2026 ║    0.5  ║ Meeting: Daily Standup            ║ Remote║
║ 0003  ║ 06.01.2026 ║    8.0  ║ Coding: mission42-timesheet       ║ Remote║
║ ...   ║    ...     ║   ...   ║              ...                  ║  ...  ║
╠═══════╩════════════╬═════════╬═══════════════════════════════════╩═══════╣
║      Gesamt:       ║  167.5  ║                                            ║
╚════════════════════╩═════════╩════════════════════════════════════════════╝
```

### Field Specifications

| Field | Format | Description |
|-------|--------|-------------|
| **Nr.** | 0001, 0002, ... | Sequential numbering starting at 0001 |
| **Datum** | DD.MM.YYYY | German date format (05.01.2026) |
| **Stunden** | 0.5, 1.0, 1.5, ... | Hours in 0.5 increments |
| **Beschreibung** | Text | Activity description from data source |
| **Ort** | Remote | Always "Remote" (fixed) |

### Weekly Breakdown

**Default**: Disabled
**Configuration**: `export_show_weekly_breakdown` (default: `false`)

When enabled, monthly export includes weekly totals:

```
Week 1 (30.12-04.01): 42.0h
Week 2 (05.01-11.01): 40.0h
Week 3 (12.01-18.01): 45.5h
Week 4 (19.01-25.01): 40.0h
---
Total January: 167.5h
```

---

## Processing Rules

### 1. Rounding Logic

**Decision**: Configurable via `rounding_mode` setting

**Default**: Round UP (`RoundingMode.UP`)

#### Round UP Mode (Default)
- 1-30 minutes → 0.5 hours
- 31-60 minutes → 1.0 hours
- 61-90 minutes → 1.5 hours
- 91-120 minutes → 2.0 hours

Examples:
- 10 minutes → 0.5h
- 45 minutes → 1.0h
- 5h 23m → 5.5h

#### Round NEAREST Mode (Optional)
- 0-15 minutes → 0.5 hours
- 16-45 minutes → 0.5 hours
- 46-75 minutes → 1.0 hours
- 76-105 minutes → 1.5 hours

**Configuration**:
```python
settings.processing.rounding_mode = "up"  # or "nearest"
```

---

### 2. Activity Grouping

**Decision**: Configurable via `group_same_activities` setting

**Default**: Disabled (`group_same_activities = False`)

#### When Disabled (Default)
Separate entries for each time block:
```
0001 | 05.01.2026 | 2.0 | Coding: mission42-timesheet | Remote
0002 | 05.01.2026 | 3.0 | Coding: mission42-timesheet | Remote
```

#### When Enabled
Combines same activities on the same day:
```
0001 | 05.01.2026 | 5.0 | Coding: mission42-timesheet | Remote
```

**Grouping Criteria**:
- Same date
- Same source
- Same description

**Configuration**:
```python
settings.processing.group_same_activities = True
```

---

### 3. Fill-up Topic Selection

**Decision**: Configurable via `fill_up_topic_mode` setting

**Default**: Manual (`FillUpTopicMode.MANUAL`)

When auto-filling to reach 40 hours per week, the system determines the development topic using one of three modes:

#### Mode A: Manual (Default)
User configures default topic in settings:
```python
settings.processing.fill_up_topic_mode = "manual"
settings.processing.fill_up_default_topic = "Lead form"
```
Result: `Development: Lead form`

#### Mode B: Auto-detect
Automatically uses most-worked topic from the week:
```python
settings.processing.fill_up_topic_mode = "auto"
```
Example: If you worked 20h on "mission42-timesheet", auto-fill uses:
Result: `Coding: mission42-timesheet`

#### Mode C: Generic
Uses generic default topic:
```python
settings.processing.fill_up_topic_mode = "generic"
settings.processing.fill_up_default_topic = "General"
```
Result: `Development: General`

---

### 4. Fill-up Distribution

**Decision**: Configurable via `fill_up_distribution` setting

**Default**: End of week (`FillUpDistribution.END_OF_WEEK`)

When filling 5 hours to reach 40h target:

#### Option A: End of Week (Default)
Single entry at end of week (Saturday 12:00 PM):
```
0010 | 11.01.2026 | 5.0 | Development: Lead form | Remote
```

**Configuration**:
```python
settings.processing.fill_up_distribution = "end_of_week"
```

#### Option B: Distributed
Spreads hours evenly across work week:
```
0001 | 06.01.2026 | 1.0 | Development: Lead form | Remote
0005 | 07.01.2026 | 1.0 | Development: Lead form | Remote
0010 | 08.01.2026 | 1.0 | Development: Lead form | Remote
0015 | 09.01.2026 | 1.0 | Development: Lead form | Remote
0020 | 10.01.2026 | 1.0 | Development: Lead form | Remote
```

**Configuration**:
```python
settings.processing.fill_up_distribution = "distributed"
```

#### Option C: Empty Slots
Fills only actual empty 30-minute time slots throughout the week:
```python
settings.processing.fill_up_distribution = "empty_slots"
```

---

### 5. Overlap Handling

**Decision**: Configurable via `overlap_handling` setting

**Default**: Priority-based (`OverlapHandling.PRIORITY`)

When calendar meeting 10:00-10:30 overlaps with WakaTime coding 10:00-10:30:

#### Option A: Priority (Default)
Only highest priority source is kept (WakaTime wins, priority 100 > 80):
```
0001 | 05.01.2026 | 0.5 | Coding: mission42-timesheet | Remote
(Meeting is hidden/not saved to database)
```

**Configuration**:
```python
settings.processing.overlap_handling = "priority"
```

#### Option B: Show Both
Both activities are saved separately (time is double-counted):
```
0001 | 05.01.2026 | 0.5 | Coding: mission42-timesheet | Remote
0002 | 05.01.2026 | 0.5 | Meeting: Daily Standup | Remote
(Total: 1.0h for that time slot)
```

**Configuration**:
```python
settings.processing.overlap_handling = "show_both"
```

#### Option C: Combine
Merges descriptions into single entry:
```
0001 | 05.01.2026 | 0.5 | Coding during Meeting: Daily Standup | Remote
```

**Configuration**:
```python
settings.processing.overlap_handling = "combine"
```

---

### 6. GitHub Tracking

**Decision**: Configurable via GitHub settings

**Defaults**:
- Commits: **Enabled** (`github_track_commits = True`)
- Assigned Issues: **Enabled** (`github_track_issues = True`)
- Pull Request Reviews: **Disabled** (`github_track_prs = False`)

#### What's Tracked

| Activity | Enabled by Default | Configuration |
|----------|-------------------|---------------|
| Commits | ✅ Yes | `github_track_commits` |
| Assigned Issues | ✅ Yes | `github_track_issues` |
| Issue Comments | ❌ No | Not implemented |
| Pull Request Reviews | ❌ No | `github_track_prs` |

#### Description Formats

**Commits**:
```
Commit: Add user authentication module
```

**Issues**:
```
Working on Issue #350: Implement supplier identifier
```

**Pull Requests** (if enabled):
```
PR Review: #123 - Fix authentication bug
```

**Configuration**:
```python
settings.github.github_track_commits = True
settings.github.github_track_issues = True
settings.github.github_track_prs = False  # Disabled by default
```

---

## Configuration Options

### Core Settings (10 settings)

| Setting | Default | Description |
|---------|---------|-------------|
| `work_week_start_day` | `monday` | Work week start day |
| `work_week_start_time` | `18:00` | Work week start time (24h format) |
| `work_week_end_day` | `saturday` | Work week end day |
| `work_week_end_time` | `18:00` | Work week end time |
| `target_hours_per_week` | `40` | Target hours per week (1-168) |
| `fetch_interval_hours` | `5` | Data fetch interval (1-24 hours) |
| `time_block_size_minutes` | `30` | Time block size (fixed) |
| `auto_fill_enabled` | `true` | Enable auto-fill to target hours |
| `auto_fill_day` | `monday` | Day when auto-fill runs |
| `default_location` | `Remote` | Default location for entries |

### Processing Settings (7 settings)

| Setting | Default | Valid Values | Description |
|---------|---------|--------------|-------------|
| `rounding_mode` | `up` | `up`, `nearest` | Time rounding mode |
| `group_same_activities` | `false` | `true`, `false` | Group identical activities |
| `fill_up_topic_mode` | `manual` | `manual`, `auto`, `generic` | Topic selection mode |
| `fill_up_default_topic` | `General` | Any string (max 100 chars) | Default fill-up topic |
| `fill_up_distribution` | `end_of_week` | `end_of_week`, `distributed`, `empty_slots` | Hour distribution mode |
| `overlap_handling` | `priority` | `priority`, `show_both`, `combine` | Overlap resolution strategy |
| `max_carry_over_hours` | `2000` | 0-10000 | Maximum carry-over hours |

### Export Settings (2 settings)

| Setting | Default | Description |
|---------|---------|-------------|
| `export_show_weekly_breakdown` | `false` | Show weekly totals in monthly export |
| `export_title_name` | `Koni` | Name in export title |

### Data Source Settings

#### WakaTime (1 setting)
- `wakatime_enabled` (default: `true`)

#### Google Calendar (2 settings)
- `calendar_enabled` (default: `true`)
- `calendar_monitored_emails` (default: `""`)

#### Gmail (3 settings)
- `gmail_enabled` (default: `true`)
- `gmail_monitored_recipients` (default: `""`)
- `gmail_default_duration_minutes` (default: `30`)

#### GitHub (5 settings)
- `github_enabled` (default: `true`)
- `github_repositories` (default: `""`)
- `github_track_commits` (default: `true`)
- `github_track_issues` (default: `true`)
- `github_track_prs` (default: `false`)

#### Cloud Events (1 setting)
- `cloud_events_enabled` (default: `true`)

**Total Settings**: 31 across 8 categories

---

## Data Source Priorities

Priority values determine which source wins when time blocks overlap (when `overlap_handling = "priority"`):

| Priority | Source | Value | Description |
|----------|--------|-------|-------------|
| Highest | WakaTime | 100 | Tracked coding time |
| High | Google Calendar | 80 | Calendar meetings |
| Medium | Gmail | 60 | Sent emails |
| Lower | GitHub | 40 | Commits and issues |
| Lower | Cloud Events | 40 | Claude Code usage |

### Description Formats by Source

| Source | Format | Example |
|--------|--------|---------|
| WakaTime | `Coding: {project}` | `Coding: mission42-timesheet` |
| Calendar | `Meeting: {title}` | `Meeting: Daily Standup` |
| Gmail | `Email to {recipient}: {subject}` | `Email to client@example.com: Project Update` |
| GitHub (Commits) | `Commit: {message}` | `Commit: Fix authentication bug` |
| GitHub (Issues) | `Working on Issue #{number}: {title}` | `Working on Issue #350: Implement supplier identifier` |
| Cloud Events | `Development: Claude Code` | `Development: Claude Code` |
| Auto-fill | `Development: {topic}` | `Development: Lead form` |

---

## Export Formats

### 1. HTML Export

**Endpoint**: `GET /export/month/{year}/{month}?format=html`

**Features**:
- Professional styling with table borders
- German date format (DD.MM.YYYY)
- German month names (Januar, Februar, März...)
- Sequential numbering (0001, 0002, ...)
- Total hours at bottom
- Responsive design

**Example**:
```html
<!DOCTYPE html>
<html lang="de">
<head>
    <title>Zeiterfassung - Koni - Januar 2026</title>
    <!-- Styling -->
</head>
<body>
    <h1>Zeiterfassung - Koni</h1>
    <p>Monat: Januar 2026</p>
    <p>Gesamt: 167.5 Stunden</p>
    <table>
        <!-- Time blocks -->
    </table>
</body>
</html>
```

### 2. CSV Export

**Endpoint**: `GET /export/month/{year}/{month}?format=csv`

**Features**:
- Standard CSV format with comma separator
- Headers: Nr., Datum, Stunden, Beschreibung, Ort
- German date format
- Total row at bottom

**Example**:
```csv
Nr.,Datum,Stunden,Beschreibung,Ort
0001,05.01.2026,2.0,Coding: mission42-timesheet,Remote
0002,05.01.2026,0.5,Meeting: Daily Standup,Remote
Gesamt:,,167.5,,
```

### 3. Excel Export (XLSX)

**Endpoint**: `GET /export/month/{year}/{month}?format=excel`

**Features**:
- Native Excel format (.xlsx)
- Formatted headers with bold and background color
- Optimized column widths
- Total row with bold formatting
- Professional styling

**Libraries**: `openpyxl>=3.1.0`

---

## Fill-up Logic Details

### Minimum Hours

**Target**: 40 hours per week (configurable)

**Behavior**:
- **Never subtract**: If you work 45 hours, all 45 hours are kept
- **Only add**: If you work 35 hours, 5 hours of "Development" are added
- **Carry-over**: Hours >40 accumulate (max 2000 total)

### Work Week Definition

**Default**: Monday 18:00 → Saturday 18:00

Example work week:
```
Start: Monday, 05.01.2026 18:00
End:   Saturday, 11.01.2026 18:00
Duration: 6 days (144 hours total)
Target: 40 billable hours
```

### Auto-fill Trigger

**Day**: Configurable via `auto_fill_day` (default: `monday`)

**Time**: Runs as part of scheduled processing (default: every 5 hours)

When enabled (`auto_fill_enabled = true`), the system automatically fills weeks that haven't reached the target hours.

---

## API Endpoints

### Data Access

```bash
# Get current month timesheet
GET /timesheet/current

# Get specific month
GET /timesheet/month/{year}/{month}

# Get week summary
GET /summary/week/{week_start}
```

### Export

```bash
# Export as HTML
GET /export/month/2026/1?format=html

# Export as CSV
GET /export/month/2026/1?format=csv

# Export as Excel
GET /export/month/2026/1?format=excel
```

### Processing

```bash
# Manual trigger (current week)
POST /process/manual

# Process specific week
POST /process/week/2026-01-06
```

### Health & Status

```bash
# API health
GET /health

# Scheduler status
GET /status/scheduler
```

---

## Implementation Status

| Component | Status | Implementation |
|-----------|--------|----------------|
| **Time Block Processor** | ✅ Complete | `app/services/time_block_processor.py` |
| **Settings Model** | ✅ Complete | `app/models/settings.py` |
| **Monthly Exporter** | ✅ Complete | `app/services/exporters.py` |
| **API Endpoints** | ✅ Complete | `app/main.py` |
| **Data Fetchers** | ✅ Complete | `app/services/fetchers/` |
| **Priority System** | ✅ Complete | `app/utils/priority.py` |
| **Time Utilities** | ✅ Complete | `app/utils/time_utils.py` |

**Test Coverage**: 68% (270 tests passing)

---

## Related Documentation

- [Admin Guide](ADMIN_GUIDE.md) - PocketBase configuration
- [Settings Documentation](../SETTINGS_DOCUMENTATION.md) - All 31 settings explained
- [Deployment Guide](DEPLOYMENT.md) - Production deployment
- [OAuth Setup](OAUTH_GUIDE.md) - Authentication setup
- [Master Plan](../MASTER_PLAN.md) - Complete implementation plan

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-07 | Initial specification based on implemented system |

---

**Note**: All configuration settings can be modified via PocketBase admin UI at `http://localhost:8090/_/collections?collectionId=settings` without code changes.
