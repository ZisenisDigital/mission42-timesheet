#!/usr/bin/env python3
"""
Seed Default Settings

Populates the PocketBase settings collection with all 28 default configuration values.
This script is idempotent - safe to run multiple times without duplicating settings.

Usage:
    python scripts/seed_settings.py

Requirements:
    - PocketBase must be running at POCKETBASE_URL
    - Admin credentials must be set in .env (PB_ADMIN_EMAIL, PB_ADMIN_PASSWORD)
    - Settings collection must exist (run migration first)
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from pocketbase import PocketBase
from pocketbase.client import ClientResponseError

# Load environment variables
load_dotenv()

POCKETBASE_URL = os.getenv("POCKETBASE_URL", "http://127.0.0.1:8090")
PB_ADMIN_EMAIL = os.getenv("PB_ADMIN_EMAIL")
PB_ADMIN_PASSWORD = os.getenv("PB_ADMIN_PASSWORD")


# All 31 settings with their default values, types, categories, descriptions, and validation rules
# Count: Core(10) + WakaTime(1) + Calendar(2) + Gmail(3) + GitHub(5) + CloudEvents(1) + Processing(7) + Export(2) = 31
SETTINGS_DATA = [
    # ===== CORE SETTINGS (10) =====
    {
        "key": "work_week_start_day",
        "value": "monday",
        "type": "string",
        "category": "core",
        "description": "Day of the week when work week starts (monday through sunday)",
        "validation_rules": {
            "enum": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        }
    },
    {
        "key": "work_week_start_time",
        "value": "18:00",
        "type": "string",
        "category": "core",
        "description": "Time when work week starts in 24-hour format (HH:MM). Default: 6 PM",
        "validation_rules": {
            "pattern": "^([01]\\d|2[0-3]):([0-5]\\d)$"
        }
    },
    {
        "key": "work_week_end_day",
        "value": "saturday",
        "type": "string",
        "category": "core",
        "description": "Day of the week when work week ends (monday through sunday)",
        "validation_rules": {
            "enum": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        }
    },
    {
        "key": "work_week_end_time",
        "value": "18:00",
        "type": "string",
        "category": "core",
        "description": "Time when work week ends in 24-hour format (HH:MM). Default: 6 PM",
        "validation_rules": {
            "pattern": "^([01]\\d|2[0-3]):([0-5]\\d)$"
        }
    },
    {
        "key": "target_hours_per_week",
        "value": "40",
        "type": "number",
        "category": "core",
        "description": "Target number of hours to track per work week. Auto-fill fills to this target.",
        "validation_rules": {
            "min": 1,
            "max": 168
        }
    },
    {
        "key": "fetch_interval_hours",
        "value": "5",
        "type": "number",
        "category": "core",
        "description": "How often to fetch data from all sources (in hours). Default: every 5 hours",
        "validation_rules": {
            "min": 1,
            "max": 24
        }
    },
    {
        "key": "time_block_size_minutes",
        "value": "30",
        "type": "number",
        "category": "core",
        "description": "Size of time blocks in minutes. Fixed at 30 minutes (0.5 hours).",
        "validation_rules": {
            "enum": [30]
        }
    },
    {
        "key": "auto_fill_enabled",
        "value": "true",
        "type": "boolean",
        "category": "core",
        "description": "Enable automatic filling of hours to reach target_hours_per_week",
        "validation_rules": {}
    },
    {
        "key": "auto_fill_day",
        "value": "monday",
        "type": "string",
        "category": "core",
        "description": "Day of week when auto-fill job runs (at work_week_start_time)",
        "validation_rules": {
            "enum": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        }
    },
    {
        "key": "default_location",
        "value": "Remote",
        "type": "string",
        "category": "core",
        "description": "Default location value for time entries. Default: Remote",
        "validation_rules": {
            "max_length": 100
        }
    },

    # ===== WAKATIME SETTINGS (1) =====
    {
        "key": "wakatime_enabled",
        "value": "true",
        "type": "boolean",
        "category": "wakatime",
        "description": "Enable WakaTime coding activity tracking (priority: 100)",
        "validation_rules": {}
    },

    # ===== GOOGLE CALENDAR SETTINGS (2) =====
    {
        "key": "calendar_enabled",
        "value": "true",
        "type": "boolean",
        "category": "calendar",
        "description": "Enable Google Calendar meeting tracking (priority: 80)",
        "validation_rules": {}
    },
    {
        "key": "calendar_monitored_emails",
        "value": "",
        "type": "string",
        "category": "calendar",
        "description": "Comma-separated list of calendar email addresses to monitor for meetings. Leave empty to monitor all.",
        "validation_rules": {
            "format": "email_list"
        }
    },

    # ===== GMAIL SETTINGS (3) =====
    {
        "key": "gmail_enabled",
        "value": "true",
        "type": "boolean",
        "category": "gmail",
        "description": "Enable Gmail sent email tracking (priority: 60)",
        "validation_rules": {}
    },
    {
        "key": "gmail_monitored_recipients",
        "value": "",
        "type": "string",
        "category": "gmail",
        "description": "Comma-separated list of recipient emails to track sent emails to. Leave empty to track all.",
        "validation_rules": {
            "format": "email_list"
        }
    },
    {
        "key": "gmail_default_duration_minutes",
        "value": "30",
        "type": "number",
        "category": "gmail",
        "description": "Default duration in minutes to assign to each sent email",
        "validation_rules": {
            "min": 5,
            "max": 240
        }
    },

    # ===== GITHUB SETTINGS (5) =====
    {
        "key": "github_enabled",
        "value": "true",
        "type": "boolean",
        "category": "github",
        "description": "Enable GitHub activity tracking (priority: 40)",
        "validation_rules": {}
    },
    {
        "key": "github_repositories",
        "value": "",
        "type": "string",
        "category": "github",
        "description": "Comma-separated list of repositories to track (format: owner/repo, e.g. 'user/repo1,org/repo2')",
        "validation_rules": {
            "format": "repo_list"
        }
    },
    {
        "key": "github_track_commits",
        "value": "true",
        "type": "boolean",
        "category": "github",
        "description": "Track commit activity in monitored repositories",
        "validation_rules": {}
    },
    {
        "key": "github_track_issues",
        "value": "true",
        "type": "boolean",
        "category": "github",
        "description": "Track assigned issue activity in monitored repositories",
        "validation_rules": {}
    },
    {
        "key": "github_track_prs",
        "value": "false",
        "type": "boolean",
        "category": "github",
        "description": "Track pull request review activity in monitored repositories",
        "validation_rules": {}
    },

    # ===== CLAUDE CODE EVENTS SETTINGS (1) =====
    {
        "key": "cloud_events_enabled",
        "value": "true",
        "type": "boolean",
        "category": "cloud_events",
        "description": "Enable Claude Code AI assistant usage tracking (priority: 40)",
        "validation_rules": {}
    },

    # ===== PROCESSING SETTINGS (7) =====
    {
        "key": "rounding_mode",
        "value": "up",
        "type": "string",
        "category": "processing",
        "description": "How to round time durations to 0.5h blocks: 'up' (always round up) or 'nearest' (round to nearest)",
        "validation_rules": {
            "enum": ["up", "nearest"]
        }
    },
    {
        "key": "group_same_activities",
        "value": "false",
        "type": "boolean",
        "category": "processing",
        "description": "Group identical activities in the same day into one entry",
        "validation_rules": {}
    },
    {
        "key": "fill_up_topic_mode",
        "value": "manual",
        "type": "string",
        "category": "processing",
        "description": "How to determine topic for auto-filled hours: 'manual' (user sets), 'auto' (most frequent), 'generic' (use default)",
        "validation_rules": {
            "enum": ["manual", "auto", "generic"]
        }
    },
    {
        "key": "fill_up_default_topic",
        "value": "General",
        "type": "string",
        "category": "processing",
        "description": "Default topic to use when auto-filling hours (used with 'generic' mode)",
        "validation_rules": {
            "max_length": 100
        }
    },
    {
        "key": "fill_up_distribution",
        "value": "end_of_week",
        "type": "string",
        "category": "processing",
        "description": "How to distribute auto-filled hours: 'end_of_week' (all at end), 'distributed' (spread evenly), 'empty_slots' (fill gaps)",
        "validation_rules": {
            "enum": ["end_of_week", "distributed", "empty_slots"]
        }
    },
    {
        "key": "overlap_handling",
        "value": "priority",
        "type": "string",
        "category": "processing",
        "description": "How to handle overlapping time blocks: 'priority' (highest only), 'show_both' (display both), 'combine' (merge descriptions)",
        "validation_rules": {
            "enum": ["priority", "show_both", "combine"]
        }
    },
    {
        "key": "max_carry_over_hours",
        "value": "2000",
        "type": "number",
        "category": "processing",
        "description": "Maximum hours that can accumulate as carry-over (hours above target_hours_per_week)",
        "validation_rules": {
            "min": 0,
            "max": 10000
        }
    },

    # ===== EXPORT SETTINGS (2) =====
    {
        "key": "export_show_weekly_breakdown",
        "value": "false",
        "type": "boolean",
        "category": "export",
        "description": "Show weekly hour totals breakdown in monthly export files",
        "validation_rules": {}
    },
    {
        "key": "export_title_name",
        "value": "Koni",
        "type": "string",
        "category": "export",
        "description": "Name to display in export title (e.g., 'Zeiterfassung - {name}')",
        "validation_rules": {
            "max_length": 50
        }
    },
]


def verify_pocketbase_connection(pb: PocketBase) -> bool:
    """Verify PocketBase is running and accessible"""
    try:
        # Try to get health status
        pb.health.check()
        return True
    except Exception as e:
        print(f"❌ Error: Cannot connect to PocketBase at {POCKETBASE_URL}")
        print(f"   {str(e)}")
        print("\n💡 Make sure PocketBase is running:")
        print(f"   cd pocketbase && ./pocketbase serve")
        return False


def authenticate_admin(pb: PocketBase) -> bool:
    """Authenticate as admin user"""
    if not PB_ADMIN_EMAIL or not PB_ADMIN_PASSWORD:
        print("❌ Error: PB_ADMIN_EMAIL and PB_ADMIN_PASSWORD must be set in .env")
        return False

    try:
        pb.admins.auth_with_password(PB_ADMIN_EMAIL, PB_ADMIN_PASSWORD)
        print(f"✅ Authenticated as admin: {PB_ADMIN_EMAIL}")
        return True
    except ClientResponseError as e:
        if e.status == 400:
            print(f"❌ Error: Invalid admin credentials")
            print(f"   Please check PB_ADMIN_EMAIL and PB_ADMIN_PASSWORD in .env")
        else:
            print(f"❌ Error authenticating admin: {e}")
        return False


def verify_settings_collection(pb: PocketBase) -> bool:
    """Verify settings collection exists"""
    try:
        pb.collection("settings").get_full_list(batch=1)
        print("✅ Settings collection found")
        return True
    except ClientResponseError as e:
        if e.status == 404:
            print("❌ Error: Settings collection not found")
            print("   Please run the migration first:")
            print("   pocketbase/pocketbase migrate")
        else:
            print(f"❌ Error checking settings collection: {e}")
        return False


def seed_setting(pb: PocketBase, setting: dict) -> bool:
    """
    Seed a single setting into PocketBase.
    Returns True if created/updated, False if error.
    """
    key = setting["key"]

    try:
        # Check if setting already exists
        existing = pb.collection("settings").get_first_list_item(f'key="{key}"')

        # Setting exists - check if we should update
        if existing.value == setting["value"]:
            print(f"  ⏭️  {key:<35} (already set to '{setting['value']}')")
            return True
        else:
            # Update with new value
            pb.collection("settings").update(existing.id, setting)
            print(f"  🔄 {key:<35} (updated: '{existing.value}' → '{setting['value']}')")
            return True

    except ClientResponseError as e:
        if e.status == 404:
            # Setting doesn't exist - create it
            try:
                pb.collection("settings").create(setting)
                print(f"  ✅ {key:<35} (created: '{setting['value']}')")
                return True
            except Exception as create_error:
                print(f"  ❌ {key:<35} (error creating: {create_error})")
                return False
        else:
            print(f"  ❌ {key:<35} (error: {e})")
            return False


def main():
    """Main seeding function"""
    print("=" * 80)
    print("🌱 Seeding PocketBase Settings Collection")
    print("=" * 80)
    print()

    # Initialize PocketBase client
    pb = PocketBase(POCKETBASE_URL)

    # Step 1: Verify connection
    print("Step 1: Verifying PocketBase connection...")
    if not verify_pocketbase_connection(pb):
        sys.exit(1)
    print()

    # Step 2: Authenticate as admin
    print("Step 2: Authenticating as admin...")
    if not authenticate_admin(pb):
        sys.exit(1)
    print()

    # Step 3: Verify settings collection exists
    print("Step 3: Verifying settings collection...")
    if not verify_settings_collection(pb):
        sys.exit(1)
    print()

    # Step 4: Seed all settings
    print("Step 4: Seeding settings...")
    print()

    success_count = 0
    error_count = 0

    # Group by category for better output
    categories = {}
    for setting in SETTINGS_DATA:
        cat = setting["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(setting)

    # Seed by category
    for category, settings in categories.items():
        print(f"📁 {category.upper().replace('_', ' ')} ({len(settings)} settings)")

        for setting in settings:
            if seed_setting(pb, setting):
                success_count += 1
            else:
                error_count += 1

        print()

    # Summary
    print("=" * 80)
    print("📊 Seeding Summary")
    print("=" * 80)
    print(f"✅ Successfully seeded: {success_count}/{len(SETTINGS_DATA)} settings (expected 31)")
    if error_count > 0:
        print(f"❌ Errors: {error_count}")
        sys.exit(1)
    else:
        print()
        print("🎉 All settings seeded successfully!")
        print()
        print("📝 You can now manage settings via PocketBase admin UI:")
        print(f"   {POCKETBASE_URL}/_/collections?collectionId=settings")
        print()


if __name__ == "__main__":
    main()
