# 👀 Viewer Access Instructions

## How to View Timesheet Data (Read-Only)

You've been given **read-only access** to view timesheet data. Here's how to access it:

---

## Option 1: PocketBase Web UI (Easiest - Visual Interface)

**Unfortunately**: PocketBase Admin UI requires admin privileges. Regular users cannot access the `/_/` admin dashboard.

**Alternative**: Use the REST API below or wait for a custom viewer page.

---

## Option 2: PocketBase REST API (Direct Access)

### Step 1: Get Your Authentication Token

Run this command (or use curl/Postman):

```bash
curl -X POST http://127.0.0.1:8090/api/collections/users/auth-with-password \
  -H "Content-Type: application/json" \
  -d '{
    "identity": "viewer@example.com",
    "password": "ViewerPass123"
  }'
```

**Response** (save the `token`):
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "record": {
    "id": "lu55fr6vf319898",
    "email": "viewer@example.com",
    ...
  }
}
```

### Step 2: Use Token to View Data

**List all settings:**
```bash
curl http://127.0.0.1:8090/api/collections/settings/records \
  -H "Authorization: YOUR_TOKEN_HERE"
```

**Get a specific setting:**
```bash
curl http://127.0.0.1:8090/api/collections/settings/records/RECORD_ID \
  -H "Authorization: YOUR_TOKEN_HERE"
```

**Filter settings by category:**
```bash
curl "http://127.0.0.1:8090/api/collections/settings/records?filter=category='core'" \
  -H "Authorization: YOUR_TOKEN_HERE"
```

---

## Option 3: FastAPI Endpoints (If They Add Auth)

Once FastAPI adds authentication, you can use these endpoints:

- **Health**: http://localhost:8000/health
- **Current Timesheet**: http://localhost:8000/timesheet/current
- **Monthly Export**: http://localhost:8000/export/month/2026/1

(Currently these are public - no auth required)

---

## Option 4: Custom Viewer Page (Coming Soon)

A simple web page where you can:
- Login with your credentials
- View timesheets in a nice format
- Export to Excel/PDF
- See charts and summaries

---

## Your Credentials

- **Email**: `viewer@example.com`
- **Password**: `ViewerPass123`
- **Access Level**: Read-only
- **Base URL**: http://127.0.0.1:8090

## What You CAN Do:
✅ View all timesheet data
✅ See weekly summaries
✅ Read system settings
✅ Export data via API

## What You CANNOT Do:
❌ Edit or delete any records
❌ Access PocketBase Admin UI
❌ Create new entries
❌ Change system settings

---

## Need Help?

Contact the administrator if you have issues accessing the data.

### Common Issues:

**"Unauthorized" error**:
- Your token might have expired (tokens last 14 days by default)
- Re-authenticate using Step 1 to get a new token

**"Forbidden" or "Not allowed"**:
- You're trying to modify data (read-only access)
- Contact admin if you need write access

**Can't connect**:
- Make sure you're on the same network
- If accessing remotely, the admin needs to set up port forwarding or a tunnel
