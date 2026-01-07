# Mission42 Timesheet

Automated timesheet system that aggregates time tracking data from multiple sources (WakaTime, Google Calendar, Gmail, GitHub, Cloud Events), processes them into 30-minute blocks, and automatically fills work weeks to 40 hours.

## Features

- **Multi-source data aggregation**: WakaTime, Google Calendar, Gmail, GitHub, custom cloud events
- **Priority-based overlap resolution**: Higher priority sources win when events overlap
- **Automatic 40-hour weekly fill-up**: Auto-fills missing hours with "Development" work package
- **30-minute block granularity**: All time tracked in 30-minute increments
- **Smart rounding**: Tasks <15 minutes rounded to 30-minute blocks
- **Carry-over tracking**: Hours >40 accumulate (max 2000 total)
- **PocketBase admin UI**: Easy configuration and data management
- **Automated processing**: Background jobs run every 5 hours
- **Monday fill-up**: Automatic weekly finalization every Monday at 6 PM

## Architecture

```
PocketBase (Port 8090)          FastAPI Processor (Port 8000)
├─ Admin UI                     ├─ Data Fetchers (5-hour cron)
├─ Database (SQLite)            ├─ Time Block Processor
├─ REST API                     ├─ Priority & Overlap Resolution
└─ Settings Storage             ├─ Auto-fill Logic (40 hours)
                                └─ Background Scheduler
```

## Tech Stack

- **Database & Admin**: PocketBase
- **Processing Service**: FastAPI
- **Package Manager**: uv
- **Task Scheduler**: APScheduler
- **APIs**: Google Calendar, Gmail, WakaTime, GitHub

## Quick Start

### Prerequisites

- Python 3.11+
- uv package manager
- Google Cloud account (for Calendar/Gmail OAuth)
- GitHub account (for commit tracking)
- WakaTime account (for coding time tracking)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ZisenisDigital/mission42-timesheet.git
   cd mission42-timesheet
   ```

2. **Setup Python environment**
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv sync
   ```

3. **Download PocketBase**
   ```bash
   ./scripts/download_pocketbase.sh
   # Or manually download from https://pocketbase.io/docs/
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and fill in your API keys and secrets
   ```

5. **Start PocketBase**
   ```bash
   cd pocketbase
   ./pocketbase serve
   ```
   Access admin UI at: http://localhost:8090/_/

6. **Setup PocketBase collections and seed settings**
   ```bash
   # Run migrations (when PocketBase is running)
   cd pocketbase && ./pocketbase migrate

   # Seed default settings (31 configuration values)
   python scripts/seed_settings.py
   ```

7. **Start FastAPI processor**
   ```bash
   python app/main.py
   ```
   API available at: http://localhost:8000
   Docs at: http://localhost:8000/docs

## Configuration

All configuration is managed through PocketBase admin UI (http://localhost:8090/_/collections?collectionId=settings).

### Settings Overview

The system has **31 configuration settings** organized into 8 categories:

| Category | Count | Description |
|----------|-------|-------------|
| Core | 10 | Work week definition, scheduling, auto-fill behavior |
| WakaTime | 1 | Coding time tracking configuration |
| Calendar | 2 | Google Calendar meeting tracking |
| Gmail | 3 | Email activity tracking |
| GitHub | 5 | Repository activity tracking |
| Cloud Events | 1 | Custom event tracking |
| Processing | 7 | Time block processing rules |
| Export | 2 | Timesheet export formatting |

### Core Settings (10)

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `work_week_start_day` | string | monday | Day of week when work week starts |
| `work_week_start_time` | string | 18:00 | Time when work week starts (24-hour format) |
| `work_week_end_day` | string | saturday | Day of week when work week ends |
| `work_week_end_time` | string | 18:00 | Time when work week ends |
| `target_hours_per_week` | number | 40 | Target hours to track per week (1-168) |
| `fetch_interval_hours` | number | 5 | How often to fetch data from sources (1-24) |
| `time_block_size_minutes` | number | 30 | Size of time blocks (fixed at 30) |
| `auto_fill_enabled` | boolean | true | Enable automatic filling to target hours |
| `auto_fill_day` | string | monday | Day when auto-fill runs |
| `default_location` | string | Remote | Default location for time entries |

### Data Source Settings

#### WakaTime (1)
| Setting | Default | Description |
|---------|---------|-------------|
| `wakatime_enabled` | true | Enable WakaTime coding activity tracking |

#### Google Calendar (2)
| Setting | Default | Description |
|---------|---------|-------------|
| `calendar_enabled` | true | Enable Google Calendar meeting tracking |
| `calendar_monitored_emails` | "" | Comma-separated calendar emails to monitor |

#### Gmail (3)
| Setting | Default | Description |
|---------|---------|-------------|
| `gmail_enabled` | true | Enable Gmail sent email tracking |
| `gmail_monitored_recipients` | "" | Comma-separated recipient emails to track |
| `gmail_default_duration_minutes` | 30 | Default duration per sent email (5-240) |

#### GitHub (5)
| Setting | Default | Description |
|---------|---------|-------------|
| `github_enabled` | true | Enable GitHub activity tracking |
| `github_repositories` | "" | Comma-separated repos (format: owner/repo) |
| `github_track_commits` | true | Track commit activity |
| `github_track_issues` | true | Track assigned issue activity |
| `github_track_prs` | false | Track pull request review activity |

#### Cloud Events (1)
| Setting | Default | Description |
|---------|---------|-------------|
| `cloud_events_enabled` | true | Enable custom cloud events tracking |

### Processing Settings (7)

| Setting | Default | Description | Valid Values |
|---------|---------|-------------|--------------|
| `rounding_mode` | up | How to round time to 0.5h blocks | `up`, `nearest` |
| `group_same_activities` | false | Group identical activities in same day | - |
| `fill_up_topic_mode` | manual | How to determine auto-fill topic | `manual`, `auto`, `generic` |
| `fill_up_default_topic` | General | Default topic for auto-filled hours | Any string (max 100 chars) |
| `fill_up_distribution` | end_of_week | How to distribute auto-filled hours | `end_of_week`, `distributed`, `empty_slots` |
| `overlap_handling` | priority | How to handle overlapping time blocks | `priority`, `show_both`, `combine` |
| `max_carry_over_hours` | 2000 | Maximum accumulated carry-over hours (0-10000) | - |

### Export Settings (2)

| Setting | Default | Description |
|---------|---------|-------------|
| `export_show_weekly_breakdown` | false | Show weekly totals in monthly export |
| `export_title_name` | Koni | Name in export title (e.g., "Zeiterfassung - {name}") |

### Managing Settings

**Via PocketBase Admin UI:**
1. Open http://localhost:8090/_/
2. Navigate to "Collections" → "settings"
3. Click on any setting to edit its value
4. Changes take effect on next fetch/process cycle

**Via Python API:**
```python
from app.config import config

# Get all settings
settings = config.settings.get_all()
print(settings.core.target_hours_per_week)  # 40

# Update a single setting
config.settings.update("target_hours_per_week", 35)

# Update multiple settings
config.settings.update_many({
    "target_hours_per_week": 35,
    "fetch_interval_hours": 3
})

# Force reload from database
settings = config.settings.reload()
```

### Adding Data Sources

1. **Google Calendar/Gmail**
   - Setup OAuth in Google Cloud Console
   - Add credentials to `.env`
   - Add accounts via PocketBase admin

2. **WakaTime**
   - Get API key from https://wakatime.com/settings/api-key
   - Add to `.env` as `WAKATIME_API_KEY`

3. **GitHub**
   - Create personal access token at https://github.com/settings/tokens
   - Add to `.env` as `GITHUB_TOKEN`

## Usage

### Manual Processing

Trigger immediate data fetch and processing:
```bash
curl -X POST http://localhost:8000/process/manual
```

### Viewing Timesheets

Access PocketBase admin UI to view:
- **Raw Events**: All fetched events from sources
- **Time Blocks**: Processed 30-minute blocks
- **Week Summaries**: Weekly hour totals

### Exporting Data

```bash
# Export current week as CSV
curl http://localhost:8000/export/week/2026-01-06?format=csv -o timesheet.csv

# Export as Excel
curl http://localhost:8000/export/week/2026-01-06?format=excel -o timesheet.xlsx
```

## Priority System

When events overlap, higher priority sources win:

| Priority | Source | Value |
|----------|--------|-------|
| Highest | WakaTime (tracked coding time) | 100 |
| High | Calendar meetings | 80 |
| Medium-High | Sent emails | 60 |
| Lower | GitHub commits | 40 |
| Lower | Cloud events | 40 |

## Development

### Project Structure

```
mission42-timesheet/
├── app/
│   ├── main.py                    # FastAPI entry point
│   ├── pocketbase_client.py       # PocketBase SDK wrapper
│   ├── services/
│   │   ├── fetchers/              # Data source fetchers
│   │   ├── processor.py           # Time block processing
│   │   └── scheduler.py           # Background jobs
│   └── utils/                     # Utilities
├── pocketbase/                    # PocketBase binary & data
├── scripts/                       # Setup scripts
└── tests/                         # Test suite
```

### Running Tests

```bash
uv run pytest tests/
```

### Adding a New Data Source

1. Create fetcher in `app/services/fetchers/`
2. Inherit from `BaseFetcher`
3. Implement `fetch()` method
4. Add to scheduler in `app/services/scheduler.py`
5. Add priority constant in `app/utils/priority.py`

## Deployment

See [MASTER_PLAN.md](MASTER_PLAN.md) Phase 9 for deployment options:
- Docker Compose
- Systemd services
- Cloud deployment (Fly.io, Railway, etc.)

## Documentation

- **Master Plan**: [MASTER_PLAN.md](MASTER_PLAN.md) - Complete implementation plan
- **API Docs**: http://localhost:8000/docs (when running)
- **PocketBase Docs**: https://pocketbase.io/docs/

## Troubleshooting

### PocketBase won't start
- Check if port 8090 is already in use
- Verify PocketBase binary has execute permissions: `chmod +x pocketbase/pocketbase`

### OAuth errors
- Verify OAuth credentials in `.env`
- Check redirect URIs match in Google Cloud Console
- Ensure OAuth consent screen is configured

### No data being fetched
- Check logs: `tail -f logs/fetcher.log`
- Verify API keys are correct in `.env`
- Manually trigger fetch: `curl -X POST http://localhost:8000/process/manual`

### Hours not filling to 40
- Auto-fill only runs on Mondays at 6 PM
- Check setting `auto_fill_enabled` is `true` in PocketBase
- Verify work week definition (Monday 6 PM → Saturday 6 PM)

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## Support

For issues and questions, please use the GitHub issue tracker:
https://github.com/ZisenisDigital/mission42-timesheet/issues

---

**Version**: 1.0.0
**Last Updated**: 2026-01-07
