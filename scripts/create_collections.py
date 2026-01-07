#!/usr/bin/env python3
"""
Create PocketBase Collections

This script creates all necessary PocketBase collections for Mission42 Timesheet.
Run this instead of migrations if the JavaScript migrations have syntax errors.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pocketbase import PocketBase
from pocketbase.client import ClientResponseError

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# PocketBase configuration
PB_URL = os.getenv("POCKETBASE_URL", "http://127.0.0.1:8090")
PB_ADMIN_EMAIL = os.getenv("PB_ADMIN_EMAIL")
PB_ADMIN_PASSWORD = os.getenv("PB_ADMIN_PASSWORD")


def main():
    print("=" * 80)
    print("🔧 Creating PocketBase Collections")
    print("=" * 80)
    print()

    # Initialize PocketBase client
    print("Step 1: Connecting to PocketBase...")
    pb = PocketBase(PB_URL)

    # Test connection
    try:
        pb.health.check()
        print("✅ Connected to PocketBase")
    except Exception as e:
        print(f"❌ Error: Cannot connect to PocketBase at {PB_URL}")
        print(f"   Make sure PocketBase is running: ./pocketbase serve")
        sys.exit(1)

    # Authenticate as admin
    print("\nStep 2: Authenticating as admin...")
    try:
        pb.admins.auth_with_password(PB_ADMIN_EMAIL, PB_ADMIN_PASSWORD)
        print(f"✅ Authenticated as admin: {PB_ADMIN_EMAIL}")
    except Exception as e:
        print(f"❌ Error: Invalid admin credentials")
        print(f"   Please check PB_ADMIN_EMAIL and PB_ADMIN_PASSWORD in .env")
        sys.exit(1)

    # Define collections to create
    collections = [
        {
            "name": "settings",
            "type": "base",
            "schema": [
                {"name": "key", "type": "text", "required": True, "options": {"min": 1, "max": 100}},
                {"name": "value", "type": "text", "required": True, "options": {"max": 1000}},
                {"name": "type", "type": "select", "required": True, "options": {"maxSelect": 1, "values": ["string", "number", "boolean"]}},
                {"name": "description", "type": "text", "required": False, "options": {"max": 500}},
                {"name": "category", "type": "select", "required": True, "options": {"maxSelect": 1, "values": ["core", "wakatime", "calendar", "gmail", "github", "cloud_events", "processing", "export"]}},
                {"name": "validation_rules", "type": "json", "required": False},
            ],
        },
        {
            "name": "raw_events",
            "type": "base",
            "schema": [
                {"name": "source", "type": "text", "required": True, "options": {"max": 50}},
                {"name": "source_id", "type": "text", "required": True, "options": {"max": 200}},
                {"name": "timestamp", "type": "date", "required": True},
                {"name": "duration_minutes", "type": "number", "required": True},
                {"name": "description", "type": "text", "required": False, "options": {"max": 500}},
                {"name": "metadata", "type": "json", "required": False},
            ],
        },
        {
            "name": "time_blocks",
            "type": "base",
            "schema": [
                {"name": "week_start", "type": "date", "required": True},
                {"name": "block_start", "type": "date", "required": True},
                {"name": "block_end", "type": "date", "required": True},
                {"name": "source", "type": "text", "required": True, "options": {"max": 50}},
                {"name": "description", "type": "text", "required": True, "options": {"max": 500}},
                {"name": "duration_hours", "type": "number", "required": True},
                {"name": "metadata", "type": "json", "required": False},
            ],
        },
        {
            "name": "week_summaries",
            "type": "base",
            "schema": [
                {"name": "week_start", "type": "date", "required": True},
                {"name": "total_hours", "type": "number", "required": True},
                {"name": "metadata", "type": "json", "required": False},
            ],
        },
        {
            "name": "claude_time_tracking",
            "type": "base",
            "schema": [
                {"name": "session_id", "type": "text", "required": True, "options": {"max": 100}},
                {"name": "tool_name", "type": "text", "required": True, "options": {"max": 100}},
                {"name": "project", "type": "text", "required": False, "options": {"max": 200}},
                {"name": "topic", "type": "text", "required": False, "options": {"max": 200}},
                {"name": "duration_minutes", "type": "number", "required": True},
                {"name": "timestamp", "type": "date", "required": True},
            ],
        },
        {
            "name": "email_accounts",
            "type": "base",
            "schema": [
                {"name": "email", "type": "email", "required": True},
                {"name": "provider", "type": "select", "required": True, "options": {"maxSelect": 1, "values": ["gmail", "outlook"]}},
                {"name": "encrypted_token", "type": "text", "required": False, "options": {"max": 5000}},
                {"name": "is_active", "type": "bool", "required": True},
            ],
        },
        {
            "name": "calendar_accounts",
            "type": "base",
            "schema": [
                {"name": "email", "type": "email", "required": True},
                {"name": "provider", "type": "select", "required": True, "options": {"maxSelect": 1, "values": ["google", "outlook"]}},
                {"name": "encrypted_token", "type": "text", "required": False, "options": {"max": 5000}},
                {"name": "is_active", "type": "bool", "required": True},
            ],
        },
        {
            "name": "work_packages",
            "type": "base",
            "schema": [
                {"name": "name", "type": "text", "required": True, "options": {"max": 100}},
                {"name": "description", "type": "text", "required": False, "options": {"max": 500}},
                {"name": "is_active", "type": "bool", "required": True},
                {"name": "is_default", "type": "bool", "required": True},
            ],
        },
        {
            "name": "project_specs",
            "type": "base",
            "schema": [
                {"name": "name", "type": "text", "required": True, "options": {"max": 100}},
                {"name": "description", "type": "text", "required": False, "options": {"max": 500}},
                {"name": "work_package", "type": "text", "required": True, "options": {"max": 100}},
                {"name": "is_active", "type": "bool", "required": True},
            ],
        },
    ]

    # Create collections
    print("\nStep 3: Creating collections...")
    created_count = 0
    skipped_count = 0

    for collection_data in collections:
        collection_name = collection_data["name"]

        try:
            # Check if collection already exists
            try:
                existing = pb.collections.get_one(collection_name)
                print(f"⏭️  Skipping {collection_name} (already exists)")
                skipped_count += 1
                continue
            except ClientResponseError as e:
                if e.status != 404:
                    raise

            # Create collection
            pb.collections.create(collection_data)
            print(f"✅ Created collection: {collection_name}")
            created_count += 1

        except Exception as e:
            print(f"❌ Error creating {collection_name}: {e}")
            continue

    print()
    print("=" * 80)
    print(f"✨ Collection creation complete!")
    print(f"   Created: {created_count} collections")
    print(f"   Skipped: {skipped_count} collections (already exist)")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Run seed scripts to populate data:")
    print("   uv run python scripts/seed_settings.py")
    print("   uv run python scripts/seed_work_packages.py")
    print("   uv run python scripts/seed_project_specs.py")
    print()
    print("2. Start the FastAPI application:")
    print("   uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
    print()


if __name__ == "__main__":
    main()
