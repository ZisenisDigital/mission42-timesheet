# Quick Start Guide - Local Testing

## ✅ Step 1: PocketBase is Already Running!

PocketBase is currently running at:
**http://127.0.0.1:8090**

## 🔧 Step 2: Create Admin Account

1. Open your browser and go to: **http://127.0.0.1:8090/_/**
2. You'll see the "Create admin account" page
3. Fill in:
   - **Email**: `admin@example.com` (or your preferred email)
   - **Password**: `admin123456` (or your preferred password)
4. Click "Create"

> **Note**: If you use different credentials, update them in `.env` file:
> ```bash
> PB_ADMIN_EMAIL=your-email@example.com
> PB_ADMIN_PASSWORD=your-password
> ```

## 📊 Step 3: Seed Initial Data

After creating the admin account, run these commands to populate initial data:

```bash
# Seed default settings (31 configuration values)
uv run python scripts/seed_settings.py

# Seed work packages (6 default categories)
uv run python scripts/seed_work_packages.py

# Seed project specs (6 default specifications)
uv run python scripts/seed_project_specs.py
```

Or run all at once:
```bash
uv run python scripts/seed_settings.py && \
uv run python scripts/seed_work_packages.py && \
uv run python scripts/seed_project_specs.py
```

## 🚀 Step 4: Start the API

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The `--reload` flag enables auto-reload during development.

## 🌐 Step 5: Access the Application

Once everything is running:

### PocketBase Admin UI
- **URL**: http://127.0.0.1:8090/_/
- **Login**: Use the credentials you created in Step 2
- **Features**:
  - View all collections (settings, time_blocks, raw_events, etc.)
  - Modify configuration settings
  - Browse data
  - Manage accounts

### FastAPI Application
- **URL**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Key API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Scheduler status
curl http://localhost:8000/status/scheduler

# Manual processing trigger
curl -X POST http://localhost:8000/process/manual

# View current month timesheet
curl http://localhost:8000/timesheet/current

# Export timesheet as HTML
curl "http://localhost:8000/export/month/2026/1?format=html" > timesheet.html

# Export as CSV
curl "http://localhost:8000/export/month/2026/1?format=csv" > timesheet.csv

# Export as Excel
curl "http://localhost:8000/export/month/2026/1?format=excel" > timesheet.xlsx
```

## 🔌 Step 6: Configure Data Sources (Optional)

To enable data fetching from external sources:

### 1. WakaTime
- Get API key from: https://wakatime.com/settings/api-key
- Add to `.env`: `WAKATIME_API_KEY=waka_your_key`

### 2. GitHub
- Create token at: https://github.com/settings/tokens
- Add to `.env`: `GITHUB_TOKEN=ghp_your_token`
- Configure repos in PocketBase settings: `github_repositories`

### 3. Google Calendar & Gmail
- Follow the detailed guide: [docs/OAUTH_GUIDE.md](docs/OAUTH_GUIDE.md)
- Set up OAuth in Google Cloud Console
- Add credentials to `.env`

After adding API keys, restart the FastAPI application.

## 🧪 Step 7: Test the System

### Test Manual Processing
```bash
# Trigger manual data fetch and processing
curl -X POST http://localhost:8000/process/manual
```

This will:
1. Fetch data from all enabled sources
2. Process into 30-minute blocks
3. Resolve overlaps by priority
4. Auto-fill to 40 hours (if enabled)
5. Save to PocketBase

### View Results
```bash
# Check processing results
curl http://localhost:8000/timesheet/current | python -m json.tool
```

Or view in PocketBase admin:
- Go to http://127.0.0.1:8090/_/
- Click on "time_blocks" collection
- See your processed time blocks

## 📝 Configuration

All settings can be modified in PocketBase admin UI:
1. Go to http://127.0.0.1:8090/_/
2. Click "Collections" → "settings"
3. Edit any setting value
4. Changes take effect on next processing cycle

Key settings to explore:
- `target_hours_per_week` - Default: 40
- `rounding_mode` - Options: "up" or "nearest"
- `overlap_handling` - Options: "priority", "show_both", "combine"
- `auto_fill_enabled` - Enable/disable auto-fill to 40 hours

## 🛑 Stopping Services

### Stop FastAPI
Press `Ctrl+C` in the terminal running uvicorn

### Stop PocketBase
```bash
# Find PocketBase process
ps aux | grep pocketbase | grep -v grep

# Kill it (replace PID with actual process ID)
kill <PID>
```

Or use:
```bash
pkill -f pocketbase
```

## 🚀 Next Steps

Now that you have the system running locally:

1. **Explore the Admin UI**: Browse all collections and data
2. **Configure Settings**: Adjust the 31 configuration options
3. **Add API Keys**: Enable external data sources
4. **Test Processing**: Trigger manual processing and view results
5. **Export Timesheets**: Try different export formats
6. **Read Documentation**:
   - [SPECIFICATION.md](docs/SPECIFICATION.md) - Technical specifications
   - [ADMIN_GUIDE.md](docs/ADMIN_GUIDE.md) - Admin workflows
   - [OAUTH_GUIDE.md](docs/OAUTH_GUIDE.md) - OAuth setup

## 🐛 Troubleshooting

### PocketBase won't start
```bash
# Check if port 8090 is in use
lsof -i :8090

# Kill any process using port 8090
kill -9 $(lsof -t -i:8090)

# Start PocketBase again
cd pocketbase/pocketbase && ./pocketbase serve --http=127.0.0.1:8090
```

### FastAPI won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Check logs for errors
tail -f /tmp/fastapi.log
```

### Settings not loading
Make sure you:
1. Created admin account in PocketBase
2. Updated `.env` with correct admin credentials
3. Ran the seed scripts successfully

### No data appearing
1. Check that data sources are enabled in settings
2. Add API keys to `.env`
3. Trigger manual processing: `curl -X POST http://localhost:8000/process/manual`

## 📚 Documentation

- **Quick Start**: This file
- **Admin Guide**: [docs/ADMIN_GUIDE.md](docs/ADMIN_GUIDE.md)
- **Technical Spec**: [docs/SPECIFICATION.md](docs/SPECIFICATION.md)
- **OAuth Setup**: [docs/OAUTH_GUIDE.md](docs/OAUTH_GUIDE.md)
- **Deployment**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- **Contributing**: [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)
- **API Docs**: http://localhost:8000/docs (when running)

---

**Happy Testing!** 🎉
