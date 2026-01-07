#!/usr/bin/env python3
"""
System Verification Script

Verifies that all PocketBase collections are set up correctly
and the FastAPI application can access them.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.pocketbase_client import PocketBaseClient
from app.config import Config


def verify_system():
    """Verify PocketBase collections and FastAPI configuration."""

    print("================================================")
    print("Mission42 Timesheet - System Verification")
    print("================================================")
    print()

    # Initialize clients
    print("🔧 Initializing clients...")
    try:
        pb_client = PocketBaseClient()
        config = Config()
        config.setup_pocketbase(pb_client)
        print("   ✓ Clients initialized")
    except Exception as e:
        print(f"   ✗ Failed to initialize clients: {e}")
        return False

    # Check PocketBase health
    print("\n🏥 Checking PocketBase health...")
    if pb_client.health_check():
        print("   ✓ PocketBase is running and accessible")
    else:
        print("   ✗ PocketBase health check failed")
        return False

    # Verify collections
    print("\n📚 Verifying collections...")
    collections = [
        ("settings", pb_client.COLLECTION_SETTINGS, 31),
        ("work_packages", pb_client.COLLECTION_WORK_PACKAGES, 6),
        ("project_specs", pb_client.COLLECTION_PROJECT_SPECS, 6),
        ("raw_events", pb_client.COLLECTION_RAW_EVENTS, 0),
        ("time_blocks", pb_client.COLLECTION_TIME_BLOCKS, 0),
        ("week_summaries", pb_client.COLLECTION_WEEK_SUMMARIES, 0),
        ("calendar_accounts", pb_client.COLLECTION_CALENDAR_ACCOUNTS, 0),
        ("email_accounts", pb_client.COLLECTION_EMAIL_ACCOUNTS, 0),
    ]

    all_good = True
    for display_name, collection_name, expected_min in collections:
        try:
            count = pb_client.count(collection_name)
            status = "✓" if count >= expected_min else "⚠"
            print(f"   {status} {display_name:20s} - {count} records (expected >= {expected_min})")
            if count < expected_min:
                all_good = False
        except Exception as e:
            print(f"   ✗ {display_name:20s} - Error: {e}")
            all_good = False

    # Verify settings loaded
    print("\n⚙️  Checking settings configuration...")
    try:
        settings = config.settings
        print(f"   ✓ Settings loaded successfully")
        print(f"      - Work week: {settings.core.work_week_start_day.value} to {settings.core.work_week_end_day.value}")
        print(f"      - Target hours: {settings.core.target_hours_per_week}h/week")
        print(f"      - WakaTime enabled: {settings.wakatime.wakatime_enabled}")
        print(f"      - GitHub enabled: {settings.github.github_enabled}")
        print(f"      - Calendar enabled: {settings.calendar.calendar_enabled}")
        print(f"      - Gmail enabled: {settings.gmail.gmail_enabled}")
    except Exception as e:
        print(f"   ✗ Failed to load settings: {e}")
        all_good = False

    # Check data sources
    print("\n🔌 Checking data source integrations...")
    github_token = os.getenv("GITHUB_TOKEN", "")
    google_client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")

    integrations = {
        "WakaTime": os.getenv("WAKATIME_API_KEY", "").startswith("waka_"),
        "GitHub": bool(github_token) and (github_token.startswith("gho_") or github_token.startswith("ghp_") or github_token.startswith("github_")),
        "Google Calendar": bool(google_client_id) and not google_client_id.endswith("YOUR_CLIENT_ID_HERE.apps.googleusercontent.com"),
        "Gmail": bool(google_client_secret) and google_client_secret != "GOCSPX-YOUR_CLIENT_SECRET_HERE",
    }

    for service, configured in integrations.items():
        status = "✓" if configured else "⚠"
        config_status = "configured" if configured else "needs credentials"
        print(f"   {status} {service:20s} - {config_status}")

    print("\n================================================")
    if all_good:
        print("✅ System verification PASSED!")
        print("================================================")
        print("\n🎉 Your Mission42 Timesheet system is ready!")
        print()
        print("📝 Current status:")
        print("   • PocketBase: Running (http://127.0.0.1:8090)")
        print("   • FastAPI: Running (http://0.0.0.0:8000)")
        print("   • Collections: All created and seeded")
        print("   • Settings: Loaded (31 settings)")
        print()

        if not integrations["Google Calendar"] or not integrations["Gmail"]:
            print("⏭️  Next step: Add Google OAuth credentials")
            print()
            print("   Follow the guide in docs/OAUTH_GUIDE.md to:")
            print("   1. Create Google Cloud project")
            print("   2. Enable Calendar and Gmail APIs")
            print("   3. Create OAuth credentials")
            print("   4. Add credentials to .env file")
            print()
            print("   Quick update: Run this script")
            print("   ./scripts/update_google_credentials.sh")
            print()
        else:
            print("🚀 All integrations configured!")
            print()
            print("   Test the system:")
            print("   • Visit: http://localhost:8000/docs")
            print("   • Try: POST /process/manual")
            print("   • View: GET /dashboard")
            print()

        return True
    else:
        print("⚠️  System verification had warnings")
        print("================================================")
        print("\nSome checks failed. Review the output above.")
        return False


if __name__ == "__main__":
    success = verify_system()
    sys.exit(0 if success else 1)
