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

6. **Setup PocketBase collections**
   ```bash
   python scripts/setup_pocketbase.py
   python scripts/seed_data.py
   ```

7. **Start FastAPI processor**
   ```bash
   python app/main.py
   ```
   API available at: http://localhost:8000
   Docs at: http://localhost:8000/docs

## Configuration

All configuration is managed through PocketBase admin UI (http://localhost:8090/_/).

### Key Settings

- **Work Week**: Monday 6 PM → Saturday 6 PM
- **Target Hours**: 40 hours per week
- **Fetch Interval**: Every 5 hours
- **Auto-fill**: Enabled (Mondays only)
- **Time Block Size**: 30 minutes
- **Minimum Task Duration**: 15 minutes (rounded to 30 min)

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
