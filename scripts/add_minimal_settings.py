#!/usr/bin/env python3
"""
Add Minimal Settings to PocketBase

This script adds just the essential settings needed to start the FastAPI application.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pocketbase import PocketBase
from dotenv import load_dotenv

load_dotenv()

# PocketBase configuration
PB_URL = os.getenv("POCKETBASE_URL", "http://127.0.0.1:8090")
PB_ADMIN_EMAIL = os.getenv("PB_ADMIN_EMAIL")
PB_ADMIN_PASSWORD = os.getenv("PB_ADMIN_PASSWORD")

# Minimum required settings
MINIMAL_SETTINGS = [
    # Core settings
    {"key": "work_week_start_day", "value": "monday", "type": "string", "category": "core", "description": "Day of the week when work week starts"},
    {"key": "work_week_start_time", "value": "18:00", "type": "string", "category": "core", "description": "Time when work week starts"},
    {"key": "work_week_end_day", "value": "saturday", "type": "string", "category": "core", "description": "Day of the week when work week ends"},
    {"key": "work_week_end_time", "value": "18:00", "type": "string", "category": "core", "description": "Time when work week ends"},
    {"key": "target_hours_per_week", "value": "40", "type": "number", "category": "core", "description": "Target hours per week"},
    {"key": "fetch_interval_hours", "value": "5", "type": "number", "category": "core", "description": "Data fetch interval in hours"},
    {"key": "time_block_size_minutes", "value": "30", "type": "number", "category": "core", "description": "Time block size in minutes"},
    {"key": "auto_fill_enabled", "value": "true", "type": "boolean", "category": "core", "description": "Enable auto-fill"},
    {"key": "auto_fill_day", "value": "monday", "type": "string", "category": "core", "description": "Day when auto-fill runs"},
    {"key": "default_location", "value": "Remote", "type": "string", "category": "core", "description": "Default location"},

    # Data sources
    {"key": "wakatime_enabled", "value": "true", "type": "boolean", "category": "wakatime", "description": "Enable WakaTime"},
    {"key": "calendar_enabled", "value": "false", "type": "boolean", "category": "calendar", "description": "Enable Google Calendar"},
    {"key": "calendar_monitored_emails", "value": "", "type": "string", "category": "calendar", "description": "Monitored calendar emails"},
    {"key": "gmail_enabled", "value": "false", "type": "boolean", "category": "gmail", "description": "Enable Gmail"},
    {"key": "gmail_monitored_recipients", "value": "", "type": "string", "category": "gmail", "description": "Monitored Gmail recipients"},
    {"key": "gmail_default_duration_minutes", "value": "30", "type": "number", "category": "gmail", "description": "Default email duration"},
    {"key": "github_enabled", "value": "true", "type": "boolean", "category": "github", "description": "Enable GitHub"},
    {"key": "github_repositories", "value": "altacarn/acr-hub", "type": "string", "category": "github", "description": "GitHub repositories to track"},
    {"key": "github_track_commits", "value": "true", "type": "boolean", "category": "github", "description": "Track commits"},
    {"key": "github_track_issues", "value": "true", "type": "boolean", "category": "github", "description": "Track issues"},
    {"key": "github_track_prs", "value": "false", "type": "boolean", "category": "github", "description": "Track PRs"},
    {"key": "cloud_events_enabled", "value": "true", "type": "boolean", "category": "cloud_events", "description": "Enable cloud events"},

    # Processing
    {"key": "rounding_mode", "value": "up", "type": "string", "category": "processing", "description": "Rounding mode"},
    {"key": "group_same_activities", "value": "false", "type": "boolean", "category": "processing", "description": "Group same activities"},
    {"key": "fill_up_topic_mode", "value": "manual", "type": "string", "category": "processing", "description": "Fill-up topic mode"},
    {"key": "fill_up_default_topic", "value": "General", "type": "string", "category": "processing", "description": "Default fill-up topic"},
    {"key": "fill_up_distribution", "value": "end_of_week", "type": "string", "category": "processing", "description": "Fill-up distribution"},
    {"key": "overlap_handling", "value": "priority", "type": "string", "category": "processing", "description": "Overlap handling"},
    {"key": "max_carry_over_hours", "value": "2000", "type": "number", "category": "processing", "description": "Max carry-over hours"},

    # Export
    {"key": "export_show_weekly_breakdown", "value": "false", "type": "boolean", "category": "export", "description": "Show weekly breakdown"},
    {"key": "export_title_name", "value": "Jan", "type": "string", "category": "export", "description": "Export title name"},
]

def main():
    print("=" * 80)
    print("🌱 Adding Minimal Settings to PocketBase")
    print("=" * 80)
    print()

    # Initialize PocketBase
    pb = PocketBase(PB_URL)

    # Test connection
    try:
        pb.health.check()
        print("✅ Connected to PocketBase")
    except Exception as e:
        print(f"❌ Error: Cannot connect to PocketBase")
        sys.exit(1)

    # Authenticate
    try:
        pb.admins.auth_with_password(PB_ADMIN_EMAIL, PB_ADMIN_PASSWORD)
        print(f"✅ Authenticated as: {PB_ADMIN_EMAIL}")
    except Exception as e:
        print(f"❌ Error: Authentication failed")
        sys.exit(1)

    print()
    print(f"Adding {len(MINIMAL_SETTINGS)} settings...")
    print()

    success = 0
    skipped = 0
    errors = 0

    for setting in MINIMAL_SETTINGS:
        key = setting["key"]
        try:
            # Try to create the setting
            pb.collection("settings").create(setting)
            print(f"  ✅ {key}")
            success += 1
        except Exception as e:
            # If it already exists, that's okay
            if "already exists" in str(e).lower() or "unique" in str(e).lower():
                print(f"  ⏭️  {key} (already exists)")
                skipped += 1
            else:
                print(f"  ❌ {key} (error: {str(e)[:50]})")
                errors += 1

    print()
    print("=" * 80)
    print(f"✨ Complete!")
    print(f"   Created: {success} settings")
    print(f"   Skipped: {skipped} settings (already exist)")
    print(f"   Errors: {errors} settings")
    print("=" * 80)
    print()

    if success > 0 or skipped >= len(MINIMAL_SETTINGS):
        print("✅ Ready to start FastAPI!")
        print()
        print("Run: uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
        print()

if __name__ == "__main__":
    main()
