# User-Friendly Data Access 🎯

Your FastAPI now has **beautiful, user-friendly endpoints** for viewing and copying data!

---

## 🌟 **NEW: Interactive Data Viewer**

### **Open the Beautiful Web Interface**
```bash
open http://localhost:8000/viewer
```

**Features:**
- ✅ Click **"Copy JSON"** to copy data to clipboard
- ✅ Click **"Copy Table"** to paste into Excel/Google Sheets
- ✅ Switch between tabs to view all 8 collections
- ✅ Beautiful color-coded categories
- ✅ Live data refresh
- ✅ Shows API endpoints for each collection

**This is the EASIEST way to view and copy your data!**

---

## 📊 **Dashboard Overview**

### **View System Summary**
```bash
open http://localhost:8000/dashboard
```

**What you get:**
- Record counts for all collections
- Recent events and time blocks
- Configuration summary
- Scheduler status
- Quick links to all endpoints

**JSON Format** (easy to copy):
```bash
curl http://localhost:8000/dashboard | jq
```

---

## 📁 **Collection Data Endpoints**

### **Get Any Collection's Data**

**Format:**
```
http://localhost:8000/data/{collection}
```

**Available Collections:**

| Endpoint | What It Shows |
|----------|---------------|
| `/data/settings` | All 31 configuration settings |
| `/data/work_packages` | All 6 work package categories |
| `/data/project_specs` | All 6 project specifications |
| `/data/raw_events` | Raw events from all sources |
| `/data/time_blocks` | Processed 30-minute time blocks |
| `/data/week_summaries` | Weekly hour summaries |
| `/data/calendar_accounts` | Google Calendar OAuth accounts |
| `/data/email_accounts` | Gmail OAuth accounts |

### **Examples:**

**View settings in browser:**
```bash
open http://localhost:8000/data/settings
```

**Copy settings as JSON:**
```bash
curl http://localhost:8000/data/settings | jq '.records' | pbcopy
```

**View work packages:**
```bash
open http://localhost:8000/data/work_packages
```

**Get specific data:**
```bash
# Get all settings
curl http://localhost:8000/data/settings | jq

# Get count only
curl http://localhost:8000/data/settings | jq '.count'

# Get just the records
curl http://localhost:8000/data/settings | jq '.records'

# Get specific field from all records
curl http://localhost:8000/data/settings | jq '.records[] | {key, value, category}'
```

---

## 🚀 **Quick Access URLs**

### **Open in Browser:**

```bash
# Interactive Data Viewer (BEST OPTION!)
open http://localhost:8000/viewer

# Dashboard Overview
open http://localhost:8000/dashboard

# Settings
open http://localhost:8000/data/settings

# Work Packages
open http://localhost:8000/data/work_packages

# Project Specs
open http://localhost:8000/data/project_specs

# API Documentation
open http://localhost:8000/docs
```

---

## 📋 **Copy Data Examples**

### **Copy to Clipboard (macOS)**

```bash
# Copy all settings
curl -s http://localhost:8000/data/settings | jq '.records' | pbcopy

# Copy all work packages
curl -s http://localhost:8000/data/work_packages | jq '.records' | pbcopy

# Copy dashboard summary
curl -s http://localhost:8000/dashboard | pbcopy
```

### **Export to Files**

```bash
# Save settings to JSON file
curl -s http://localhost:8000/data/settings | jq '.records' > settings.json

# Save work packages
curl -s http://localhost:8000/data/work_packages | jq '.records' > work_packages.json

# Save dashboard
curl -s http://localhost:8000/dashboard > dashboard.json
```

### **Convert to CSV**

```bash
# Settings to CSV
curl -s http://localhost:8000/data/settings | jq -r '.records[] | [.key, .value, .category, .description] | @csv' > settings.csv

# Work packages to CSV
curl -s http://localhost:8000/data/work_packages | jq -r '.records[] | [.name, .description, .is_active] | @csv' > work_packages.csv
```

---

## 🎨 **Response Format**

All `/data/{collection}` endpoints return data in this format:

```json
{
  "collection": "settings",
  "count": 31,
  "records": [
    {
      "id": "abc123",
      "created": "2026-01-07T12:29:18Z",
      "updated": "2026-01-07T12:29:18Z",
      "key": "work_week_start_day",
      "value": "monday",
      "type": "string",
      "category": "core",
      "description": "Day of the week when work week starts"
    }
    // ... more records
  ],
  "timestamp": "2026-01-07T14:57:19.492574"
}
```

---

## 📚 **All Available Endpoints**

### **Data Viewing**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/viewer` | Interactive web viewer (HTML) |
| GET | `/dashboard` | System overview dashboard |
| GET | `/data/{collection}` | Get collection data |

### **Timesheet Access**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/timesheet/current` | Current month timesheet |
| GET | `/timesheet/month/{year}/{month}` | Specific month |
| GET | `/summary/week/{week_start}` | Week summary |

### **Export**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/export/month/{year}/{month}?format=html` | HTML export |
| GET | `/export/month/{year}/{month}?format=csv` | CSV export |
| GET | `/export/month/{year}/{month}?format=excel` | Excel export |

### **Processing**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/process/manual` | Trigger data fetch |
| POST | `/process/week/{date}` | Process specific week |

### **System Status**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/status/scheduler` | Scheduler status |
| GET | `/` | API info |
| GET | `/docs` | API documentation |

---

## 💡 **Best Options for Different Needs**

### **👀 Just Want to Look at Data?**
```bash
open http://localhost:8000/viewer
```
Click around, view everything in beautiful tables!

### **📋 Need to Copy Data?**
```bash
open http://localhost:8000/viewer
```
Click **"Copy JSON"** or **"Copy Table"** button!

### **📊 Need Data in Excel/Google Sheets?**
```bash
open http://localhost:8000/viewer
```
Click **"Copy Table"**, then paste into Excel/Sheets!

### **🤖 Need Programmatic Access?**
```bash
curl http://localhost:8000/data/settings | jq
```

### **📱 Want a Quick Overview?**
```bash
open http://localhost:8000/dashboard
```

### **📖 Want to Explore the API?**
```bash
open http://localhost:8000/docs
```

---

## 🎯 **Recommended Workflow**

1. **View data interactively:**
   ```bash
   open http://localhost:8000/viewer
   ```

2. **Check system status:**
   ```bash
   open http://localhost:8000/dashboard
   ```

3. **Copy what you need:**
   - Click "Copy JSON" for code/scripts
   - Click "Copy Table" for Excel/Sheets

4. **Explore API capabilities:**
   ```bash
   open http://localhost:8000/docs
   ```

---

## 🆕 **What Changed?**

**NEW Endpoints Added:**
- ✅ `/viewer` - Beautiful interactive data viewer
- ✅ `/dashboard` - System overview with stats
- ✅ `/data/{collection}` - Easy data access for all collections

**Benefits:**
- No need to use PocketBase admin UI
- Copy data with one click
- Beautiful, user-friendly interface
- All accessible through FastAPI (port 8000)

---

## 🎉 **Try It Now!**

```bash
# Open the interactive viewer
open http://localhost:8000/viewer

# Or view the dashboard
open http://localhost:8000/dashboard

# Or browse the API docs
open http://localhost:8000/docs
```

**Everything is user-friendly now!** 🚀
