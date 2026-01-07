# Mission42 Timesheet - Master Implementation Plan

## Project Overview

Automated timesheet system that aggregates time tracking data from multiple sources, processes them into 30-minute blocks, and automatically fills work weeks to 40 hours.

**Key Features:**
- Multi-source data aggregation (WakaTime, Google Calendar, Gmail, GitHub, Claude Code Events)
- Priority-based overlap resolution
- Automatic 40-hour weekly fill-up (Monday 6 PM trigger)
- 30-minute block granularity
- PocketBase for settings & data storage
- FastAPI for data processing & scheduling

---

## Architecture

```
┌─────────────────────────────────────────────┐
│         PocketBase (Port 8090)              │
├─────────────────────────────────────────────┤
│  • Admin UI (/admin)                        │
│  • Authentication                           │
│  • Database (SQLite)                        │
│  • REST API (auto-generated)                │
│  • Settings & Configuration                 │
└─────────────────────────────────────────────┘
                    ▲
                    │ REST API calls
                    │
┌─────────────────────────────────────────────┐
│       FastAPI Processor (Port 8000)         │
├─────────────────────────────────────────────┤
│  • Data Fetchers (5-hour cron)              │
│  • Time Block Processor                     │
│  • Priority & Overlap Resolution            │
│  • Auto-fill Logic (40 hours)               │
│  • Background Scheduler (APScheduler)       │
└─────────────────────────────────────────────┘
        │
        ├─── WakaTime API
        ├─── Google Calendar API
        ├─── Gmail API
        ├─── GitHub API
        └─── PocketBase Claude Code Events
```

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Database & Admin | PocketBase | Settings, data storage, admin UI |
| Processing Service | FastAPI | Data fetching & processing |
| Package Manager | uv | Fast Python dependency management |
| Task Scheduler | APScheduler | Background jobs (5-hour cron, Monday fill-up) |
| PocketBase Client | pocketbase-python | Python SDK for PocketBase |
| Google APIs | google-api-python-client | Calendar & Gmail integration |
| GitHub API | PyGithub | Commit tracking |
| WakaTime API | requests | Coding time tracking |
| Configuration | python-dotenv | Environment variables |

---

## Core Business Rules

### Time Tracking Rules

1. **Smallest Unit**: 30-minute blocks
2. **Minimum Task Duration**: 15 minutes (rounded up to 30 min)
3. **Work Week Definition**: Monday 6 PM → Saturday 6 PM
4. **Target Hours**: 40 hours per week
5. **Auto-fill**: Only on Mondays at 6 PM
6. **Carry-over**: Hours >40 accumulate (max 2000 total)
7. **Fill-up**: Hours <40 filled with "Development" work package

### Priority System

When events overlap, higher priority wins:

| Priority | Source | Value |
|----------|--------|-------|
| Highest | WakaTime (tracked coding time) | 100 |
| High | Calendar meetings | 80 |
| Medium-High | Sent emails | 60 |
| Lower | GitHub commits | 40 |
| Lower | Claude Code events | 40 |

### Data Sources

**Google Calendar:**
- Check meetings where:
  - Created by user, OR
  - User is invited by specific email addresses, OR
  - User invited specific email addresses
- Support multiple calendar accounts

**Gmail:**
- Track sent emails
- Estimate duration based on thread activity

**WakaTime:**
- Primary coding time tracker
- Highest priority (ground truth)

**GitHub:**
- Track commits
- Estimate duration based on changes

**Claude Code Events:**
- Custom events from PocketBase cloud_events table
- Track Claude Code AI assistant usage and sessions
- User-defined activity tracking for AI-assisted work

---

## Project Structure

```
mission42-timesheet/
├── .env                           # Environment secrets (not committed)
├── .gitignore
├── pyproject.toml                 # uv dependencies
├── README.md
├── MASTER_PLAN.md                 # This file
│
├── pocketbase/                    # PocketBase binary & data
│   ├── pocketbase                 # Binary (download separately)
│   ├── pb_data/                   # Database & uploads (gitignored)
│   └── pb_migrations/             # Collection schemas (committed)
│       └── initial_setup.js
│
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry point
│   ├── config.py                  # Configuration loader
│   ├── pocketbase_client.py       # PocketBase SDK wrapper
│   │
│   ├── models/                    # Data models & schemas
│   │   ├── __init__.py
│   │   ├── event.py              # Raw event models
│   │   └── timeblock.py          # Time block models
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   │
│   │   ├── fetchers/             # Data source fetchers
│   │   │   ├── __init__.py
│   │   │   ├── base.py           # Base fetcher class
│   │   │   ├── wakatime_fetcher.py
│   │   │   ├── calendar_fetcher.py
│   │   │   ├── gmail_fetcher.py
│   │   │   ├── github_fetcher.py
│   │   │   └── cloud_fetcher.py
│   │   │
│   │   ├── processor.py          # Time block processing logic
│   │   └── scheduler.py          # APScheduler job definitions
│   │
│   └── utils/
│       ├── __init__.py
│       ├── priority.py           # Priority constants & resolution
│       ├── time_utils.py         # Time calculations & rounding
│       └── oauth.py              # OAuth helper functions
│
├── scripts/
│   ├── setup_pocketbase.py       # Initial PocketBase setup
│   ├── download_pocketbase.sh    # Download PocketBase binary
│   └── seed_data.py              # Seed default settings
│
└── tests/
    ├── __init__.py
    ├── test_processor.py
    ├── test_priority.py
    └── test_time_utils.py
```

---

## PocketBase Collections Schema

### 1. settings
Configuration key-value pairs

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| key | text | ✓ | ✓ | Setting key (e.g., 'target_hours_per_week') |
| value | text | | | Setting value (stored as string) |
| description | text | | | Human-readable description |

**Default Settings:**
```javascript
{
  'work_week_start_day': 'monday',
  'work_week_start_time': '18:00',
  'work_week_end_day': 'saturday',
  'work_week_end_time': '18:00',
  'target_hours_per_week': '40',
  'fetch_interval_hours': '5',
  'max_carry_over_hours': '2000',
  'min_task_duration_minutes': '15',
  'time_block_size_minutes': '30',
  'default_work_package': 'Development',
  'auto_fill_enabled': 'true',
  'auto_fill_day': 'monday'
}
```

### 2. email_accounts
Gmail accounts to monitor for sent emails

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| email | text | ✓ | ✓ | Email address |
| oauth_token | text | | | OAuth access token (encrypted in .env) |
| refresh_token | text | | | OAuth refresh token (encrypted in .env) |
| active | bool | | | Whether to actively fetch from this account |

### 3. calendar_accounts
Google Calendar accounts to monitor

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| email | text | ✓ | | Calendar email |
| oauth_token | text | | | OAuth access token (encrypted in .env) |
| refresh_token | text | | | OAuth refresh token (encrypted in .env) |
| check_created | bool | | | Check meetings created by this user |
| check_invited | bool | | | Check meetings user is invited to |
| monitor_invites_from | text | | | Comma-separated emails to monitor invites from |
| active | bool | | | Whether to actively fetch from this account |

### 4. work_packages
Types of work (Development, Planning, Testing, etc.)

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| name | text | ✓ | ✓ | Work package name |
| is_default | bool | | | Use for auto-fill |
| color | text | | | Hex color for UI display |
| description | text | | | Optional description |

**Default Work Packages:**
- Development (default, #3B82F6)
- Planning (#8B5CF6)
- Testing (#10B981)
- Troubleshooting (#EF4444)
- Meetings (#F59E0B)
- Emails (#6366F1)

### 5. project_specs
Project specifications (Lead, Backend, Frontend, etc.)

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| name | text | ✓ | ✓ | Project spec name |
| description | text | | | Optional description |

**Default Project Specs:**
- Lead
- Backend
- Frontend
- Infrastructure
- Documentation
- Other

### 6. raw_events
Raw events from all sources before processing

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| source | text | ✓ | | Source: wakatime, calendar, email, github, cloud |
| source_id | text | | | External ID from source API |
| timestamp | date | ✓ | | Event start timestamp |
| duration_minutes | number | | | Duration in minutes |
| description | text | | | Event description |
| metadata | json | | | Additional data (project, participants, etc.) |

**Indexes:**
- `timestamp` (for week queries)
- `source` (for filtering by source)

### 7. time_blocks
Processed 30-minute time blocks

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| week_start | date | ✓ | | Monday 6 PM of the week |
| block_start | date | ✓ | | Block start timestamp |
| block_end | date | ✓ | | Block end timestamp (start + 30 min) |
| work_package | relation | | | → work_packages |
| project_spec | relation | | | → project_specs |
| description | text | | | Block description |
| source | text | | | Original source (wakatime, calendar, etc.) |
| priority | number | | | Priority value (for overlap resolution) |
| is_auto_filled | bool | | | Whether auto-filled to reach 40 hours |

**Indexes:**
- `week_start` (for weekly queries)
- `block_start` (for sorting)

### 8. week_summaries
Weekly hour summaries

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| week_start | date | ✓ | ✓ | Monday 6 PM of the week |
| total_hours | number | ✓ | | Total hours for the week |
| tracked_hours | number | | | Hours from actual tracking (not auto-filled) |
| auto_filled_hours | number | | | Hours auto-filled to reach 40 |
| carry_over_hours | number | | | Cumulative carry-over (if >40 hours) |
| processed_at | date | | | Last processing timestamp |

### 9. cloud_events
Claude Code AI assistant usage events

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| event_type | text | ✓ | | Type of Claude Code event (session, task, etc.) |
| timestamp | date | ✓ | | Event timestamp |
| duration_minutes | number | | | Duration in minutes |
| description | text | | | Event description (e.g., "Claude Code: Implemented feature X") |
| metadata | json | | | Additional metadata (session_id, task_type, etc.) |

---

## Environment Variables

**File: `.env`** (Never commit this file!)

```bash
# PocketBase Connection
POCKETBASE_URL=http://127.0.0.1:8090
PB_ADMIN_EMAIL=admin@example.com
PB_ADMIN_PASSWORD=your-secure-password

# WakaTime API
WAKATIME_API_KEY=waka_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# GitHub API
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_USERNAME=your-github-username

# Google OAuth (Calendar & Gmail)
GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxxxxx
GOOGLE_REDIRECT_URI=http://localhost:8000/oauth/google/callback

# Encryption Key (for storing OAuth tokens)
ENCRYPTION_KEY=your-random-32-byte-key-base64-encoded

# FastAPI
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
```

**Important:**
- OAuth tokens for individual accounts are stored in `.env` with prefixes like `GMAIL_TOKEN_1`, `CALENDAR_TOKEN_1`, etc.
- Use `cryptography.fernet` to encrypt sensitive tokens before storing

---

## Implementation Phases

### Phase 1: Project Foundation (Week 1)
**Goal:** Setup project structure, PocketBase, and basic FastAPI app

- [x] Initialize git repository
- [ ] Setup `uv` package manager
- [ ] Create project structure
- [ ] Download and configure PocketBase
- [ ] Create PocketBase collections schema
- [ ] Setup environment variables template
- [ ] Create `.gitignore` (exclude `.env`, `pb_data/`)
- [ ] Write README with setup instructions
- [ ] Initial git commit

**Deliverables:**
- Working PocketBase instance with admin UI
- FastAPI skeleton app
- PocketBase Python client wrapper

---

### Phase 2: Core Infrastructure (Week 1-2)
**Goal:** Build foundational services and utilities

- [ ] Implement `pocketbase_client.py` wrapper
- [ ] Create configuration loader (`config.py`)
- [ ] Build time utilities (`time_utils.py`)
  - Week calculation (Monday 6 PM → Saturday 6 PM)
  - 30-minute block rounding
  - Duration calculations
- [ ] Build priority system (`priority.py`)
- [ ] Setup OAuth helper utilities (`oauth.py`)
- [ ] Create base fetcher class
- [ ] Write unit tests for utilities

**Deliverables:**
- Reusable utility functions
- PocketBase client with CRUD operations
- Test coverage >80% for utilities

---

### Phase 3: Data Fetchers (Week 2-3)
**Goal:** Implement all data source fetchers

**Priority Order:**
1. **WakaTime Fetcher** (highest priority data)
   - [ ] Authenticate with API key
   - [ ] Fetch daily summaries
   - [ ] Extract project/language metadata
   - [ ] Save to `raw_events` collection

2. **Google Calendar Fetcher**
   - [ ] OAuth 2.0 authentication flow
   - [ ] Support multiple calendar accounts
   - [ ] Filter by creation/invitation rules
   - [ ] Handle recurring events
   - [ ] Save to `raw_events` collection

3. **Gmail Fetcher**
   - [ ] OAuth 2.0 authentication flow
   - [ ] Fetch sent emails
   - [ ] Estimate duration (15-30 min per email)
   - [ ] Extract recipients and subject
   - [ ] Save to `raw_events` collection

4. **GitHub Fetcher**
   - [ ] Authenticate with personal access token
   - [ ] Fetch commits for specified repos
   - [ ] Estimate duration from commit size
   - [ ] Save to `raw_events` collection

5. **Claude Code Events Fetcher**
   - [ ] Read from `cloud_events` collection (stores Claude Code usage)
   - [ ] Convert to `raw_events` format

**Deliverables:**
- 5 working fetchers
- OAuth token management
- Error handling and retry logic

---

### Phase 4: Time Block Processor (Week 3-4)
**Goal:** Process raw events into 30-minute blocks

**Core Logic:**

```python
def process_week(week_start: date) -> dict:
    """
    Main processing function

    Steps:
    1. Fetch all raw_events for the week
    2. Convert to 30-min blocks with priorities
    3. Resolve overlaps (higher priority wins)
    4. Round <15min tasks to 30min
    5. Calculate total hours
    6. Auto-fill to 40 hours (if Monday & enabled)
    7. Save to time_blocks collection
    8. Update week_summary
    """
```

**Tasks:**
- [ ] Implement `get_week_bounds()` - Calculate Monday 6 PM → Saturday 6 PM
- [ ] Implement `raw_event_to_blocks()` - Convert events to 30-min blocks
- [ ] Implement `resolve_overlaps()` - Priority-based conflict resolution
- [ ] Implement `calculate_week_hours()` - Sum up total hours
- [ ] Implement `auto_fill_development()` - Fill to 40 hours with default work package
- [ ] Implement `handle_carry_over()` - Track hours >40 (max 2000)
- [ ] Implement `save_time_blocks()` - Persist to PocketBase
- [ ] Write comprehensive unit tests

**Edge Cases to Handle:**
- Events spanning multiple days
- Events outside work week (still track, don't count for 40-hour fill)
- Overlapping events from same source
- Events with no duration (e.g., instantaneous commits)
- Week with >40 hours (carry-over logic)

**Deliverables:**
- Fully tested processor
- Week summary generation
- Carry-over tracking

---

### Phase 5: Background Scheduler (Week 4)
**Goal:** Automate data fetching and processing

**Jobs:**

1. **Every 5 Hours - Data Fetch & Process**
   ```python
   @scheduler.scheduled_job('interval', hours=5)
   async def fetch_and_process():
       await fetch_all_sources()
       await process_current_week()
   ```

2. **Monday 6 PM - Weekly Fill-up**
   ```python
   @scheduler.scheduled_job('cron', day_of_week='mon', hour=18)
   async def monday_fillup():
       await process_week_with_fillup(get_previous_week())
   ```

**Tasks:**
- [ ] Setup APScheduler with AsyncIOScheduler
- [ ] Implement 5-hour fetch job
- [ ] Implement Monday 6 PM fill-up job
- [ ] Add job status logging to PocketBase
- [ ] Create manual trigger endpoint (`/process/manual`)
- [ ] Error handling and retries
- [ ] Job overlap prevention

**Deliverables:**
- Automated background processing
- Manual trigger for testing
- Job execution logs

---

### Phase 6: Admin & Configuration (Week 5)
**Goal:** Finalize PocketBase admin setup and seed data

**Tasks:**
- [ ] Create PocketBase migration script (collection definitions)
- [ ] Seed default settings
- [ ] Seed default work packages
- [ ] Seed default project specs
- [ ] Create admin user setup script
- [ ] Document PocketBase admin workflows
- [ ] Create OAuth setup guide

**Admin UI Features (via PocketBase):**
- Manage settings (target hours, cron interval, etc.)
- Add/remove email accounts
- Add/remove calendar accounts
- Configure work packages
- Configure project specs
- View raw events
- View time blocks
- View week summaries

**Deliverables:**
- Fully configured PocketBase admin
- Seed data scripts
- Admin user guide

---

### Phase 7: API Endpoints & Export (Week 5-6)
**Goal:** Build FastAPI endpoints for data access and export

**Endpoints:**

```python
# Health & Status
GET  /                          # API status
GET  /health                    # Health check

# Manual Processing
POST /process/manual            # Trigger immediate processing
POST /process/week/{date}       # Process specific week

# Data Access (optional - can use PocketBase API directly)
GET  /timesheet/current         # Current week timesheet
GET  /timesheet/{week_start}    # Specific week timesheet
GET  /summary/{week_start}      # Week summary

# Export
GET  /export/week/{date}?format=csv|excel  # Export week to file
GET  /export/month/{date}?format=csv|excel # Export month

# OAuth Callbacks
GET  /oauth/google/authorize    # Initiate Google OAuth
GET  /oauth/google/callback     # Google OAuth callback
GET  /oauth/github/authorize    # Initiate GitHub OAuth
GET  /oauth/github/callback     # GitHub OAuth callback
```

**Tasks:**
- [ ] Implement core API endpoints
- [ ] Create CSV export functionality
- [ ] Create Excel export functionality
- [ ] OAuth flow implementation
- [ ] API documentation (FastAPI auto-docs)

**Deliverables:**
- RESTful API
- Export functionality
- OAuth integration

---

### Phase 8: Testing & Documentation (Week 6)
**Goal:** Comprehensive testing and documentation

**Testing:**
- [ ] Unit tests for all utilities (>90% coverage)
- [ ] Integration tests for fetchers
- [ ] Processor logic tests (edge cases)
- [ ] End-to-end test (full week processing)
- [ ] Manual testing with real data

**Documentation:**
- [ ] README with setup instructions
- [ ] API documentation (via FastAPI /docs)
- [ ] PocketBase schema documentation
- [ ] OAuth setup guide (Google & GitHub)
- [ ] Deployment guide
- [ ] Troubleshooting guide

**Deliverables:**
- Test suite with >80% coverage
- Complete documentation
- Setup guide for new users

---

### Phase 9: Deployment & Monitoring (Week 7)
**Goal:** Production deployment and monitoring setup

**Deployment Options:**
- **Option 1:** Docker Compose (PocketBase + FastAPI)
- **Option 2:** Systemd services (Linux)
- **Option 3:** Cloud deployment (Fly.io, Railway, etc.)

**Tasks:**
- [ ] Create Dockerfile for FastAPI app
- [ ] Create docker-compose.yml (PocketBase + FastAPI)
- [ ] Setup systemd service files (alternative)
- [ ] Create deployment script
- [ ] Setup logging (structured logs)
- [ ] Setup monitoring (health checks)
- [ ] Backup strategy for PocketBase data
- [ ] SSL/TLS setup (if deploying publicly)

**Deliverables:**
- Production-ready deployment
- Monitoring and logging
- Backup automation

---

## Development Workflow

### Local Development

1. **Start PocketBase:**
   ```bash
   cd pocketbase
   ./pocketbase serve
   ```
   Admin UI: http://localhost:8090/_/

2. **Start FastAPI:**
   ```bash
   source .venv/bin/activate
   python app/main.py
   ```
   API: http://localhost:8000
   Docs: http://localhost:8000/docs

3. **Run Tests:**
   ```bash
   uv run pytest tests/
   ```

### Git Workflow

- **Main branch:** `master`
- **Feature branches:** `feature/wakatime-fetcher`, `feature/processor`, etc.
- **Commit format:** Conventional Commits
  - `feat:` New features
  - `fix:` Bug fixes
  - `docs:` Documentation
  - `test:` Tests
  - `refactor:` Code refactoring
  - `chore:` Maintenance

---

## Security Considerations

1. **Secrets Management:**
   - All secrets in `.env` (never commit)
   - Encrypt OAuth tokens before storing
   - Use `cryptography.fernet` for encryption
   - Rotate encryption keys periodically

2. **PocketBase Security:**
   - Strong admin password
   - Enable HTTPS in production
   - Use collection rules to restrict access
   - Regular database backups

3. **API Security:**
   - Rate limiting on endpoints
   - Input validation
   - CORS configuration
   - OAuth token refresh handling

4. **Data Privacy:**
   - Sensitive data encrypted at rest
   - Logs exclude tokens and passwords
   - Regular security audits

---

## Performance Considerations

1. **Database:**
   - Index on `timestamp` fields
   - Index on `week_start` for queries
   - Regularly vacuum SQLite database

2. **API Calls:**
   - Batch requests where possible
   - Implement exponential backoff
   - Cache API responses (5-hour window)

3. **Processing:**
   - Process weeks incrementally (not full history)
   - Async/await for concurrent fetchers
   - Limit lookback period (e.g., last 4 weeks)

---

## Monitoring & Observability

**Key Metrics:**
- Fetch job success rate
- Processing duration
- API response times
- Error rates by source
- Weekly hour totals

**Logging:**
- Structured JSON logs
- Log levels: DEBUG, INFO, WARNING, ERROR
- Separate logs for each fetcher
- Processor decision logs (overlap resolution)

**Alerts:**
- Failed fetcher jobs
- Processing errors
- OAuth token expiration
- Carry-over hours approaching limit (2000)

---

## Future Enhancements

**Phase 10+ (Post-MVP):**
- [ ] Web UI for timesheet viewing (React/Vue)
- [ ] Mobile app (React Native)
- [ ] Slack integration (daily summaries)
- [ ] AI-powered work package classification
- [ ] Multi-user support
- [ ] Custom report generation
- [ ] Integration with JIRA/Linear
- [ ] Invoice generation from timesheets
- [ ] Machine learning for duration estimation

---

## Success Criteria

**MVP is successful when:**
1. ✅ Fetches data from all 5 sources automatically
2. ✅ Processes raw events into 30-minute blocks
3. ✅ Resolves overlaps by priority correctly
4. ✅ Auto-fills to 40 hours every Monday
5. ✅ Tracks carry-over hours accurately
6. ✅ Exports weekly timesheets to CSV/Excel
7. ✅ Runs reliably with minimal manual intervention
8. ✅ PocketBase admin UI allows easy configuration

---

## Timeline Summary

| Phase | Duration | Key Deliverable |
|-------|----------|-----------------|
| 1. Foundation | Week 1 | Working PocketBase + FastAPI skeleton |
| 2. Infrastructure | Week 1-2 | Utilities & PocketBase client |
| 3. Fetchers | Week 2-3 | All 5 data sources working |
| 4. Processor | Week 3-4 | Time block processing logic |
| 5. Scheduler | Week 4 | Automated background jobs |
| 6. Admin | Week 5 | PocketBase admin configured |
| 7. API & Export | Week 5-6 | REST API + CSV/Excel export |
| 8. Testing | Week 6 | Test suite + documentation |
| 9. Deployment | Week 7 | Production-ready deployment |

**Total MVP Timeline: ~7 weeks**

---

## Quick Start Checklist

After initial setup, to get running:

- [ ] Clone repository
- [ ] Copy `.env.example` to `.env` and fill in secrets
- [ ] Run `uv sync` to install dependencies
- [ ] Download PocketBase binary
- [ ] Start PocketBase: `./pocketbase/pocketbase serve`
- [ ] Run migrations: `python scripts/setup_pocketbase.py`
- [ ] Seed data: `python scripts/seed_data.py`
- [ ] Configure OAuth in Google Cloud Console & GitHub
- [ ] Add email/calendar accounts via PocketBase admin
- [ ] Start FastAPI: `python app/main.py`
- [ ] Verify first fetch: `curl http://localhost:8000/process/manual`
- [ ] Check PocketBase admin for raw events and time blocks

---

## Support & Resources

- **PocketBase Docs:** https://pocketbase.io/docs/
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **uv Docs:** https://docs.astral.sh/uv/
- **Google Calendar API:** https://developers.google.com/calendar
- **Gmail API:** https://developers.google.com/gmail/api
- **WakaTime API:** https://wakatime.com/developers
- **GitHub API:** https://docs.github.com/en/rest

---

## Contact & Maintenance

**Repository:** ZisenisDigital/mission42-timesheet
**Maintainer:** [Your Name]
**License:** MIT (or your choice)

---

**Last Updated:** 2026-01-07
**Version:** 1.0.0
