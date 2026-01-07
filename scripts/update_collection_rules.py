#!/usr/bin/env python3
"""
Update PocketBase Collection Rules

This script updates collection rules to allow API access.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pocketbase import PocketBase
from pocketbase.client import ClientResponseError
from dotenv import load_dotenv

load_dotenv()

# PocketBase configuration
PB_URL = os.getenv("POCKETBASE_URL", "http://127.0.0.1:8090")
PB_ADMIN_EMAIL = os.getenv("PB_ADMIN_EMAIL")
PB_ADMIN_PASSWORD = os.getenv("PB_ADMIN_PASSWORD")


def main():
    print("=" * 80)
    print("🔧 Updating PocketBase Collection Rules")
    print("=" * 80)
    print()

    # Initialize PocketBase
    pb = PocketBase(PB_URL)

    # Test connection
    try:
        pb.health.check()
        print("✅ Connected to PocketBase")
    except Exception as e:
        print(f"❌ Error: Cannot connect to PocketBase at {PB_URL}")
        sys.exit(1)

    # Authenticate
    try:
        pb.admins.auth_with_password(PB_ADMIN_EMAIL, PB_ADMIN_PASSWORD)
        print(f"✅ Authenticated as: {PB_ADMIN_EMAIL}")
    except Exception as e:
        print(f"❌ Error: Authentication failed - {e}")
        sys.exit(1)

    print()
    print("Updating collection rules...")
    print()

    # Collections that need API access
    collections_to_update = [
        "settings",
        "raw_events",
        "time_blocks",
        "week_summaries",
        "claude_time_tracking",
        "email_accounts",
        "calendar_accounts",
        "work_packages",
        "project_specs",
    ]

    updated = 0
    errors = 0

    for collection_name in collections_to_update:
        try:
            # Get existing collection
            collection = pb.collections.get_one(collection_name)

            # Update rules to allow API access
            # Empty string means "allow all authenticated requests"
            pb.collections.update(collection.id, {
                "listRule": "",  # Allow listing
                "viewRule": "",  # Allow viewing
                "createRule": "",  # Allow creating
                "updateRule": "",  # Allow updating
                "deleteRule": "",  # Allow deleting
            })

            print(f"  ✅ {collection_name}")
            updated += 1

        except ClientResponseError as e:
            print(f"  ❌ {collection_name} (error: {e})")
            errors += 1

    print()
    print("=" * 80)
    print(f"✨ Complete!")
    print(f"   Updated: {updated} collections")
    print(f"   Errors: {errors} collections")
    print("=" * 80)
    print()

    if updated > 0:
        print("✅ Collection rules updated - API access enabled!")
        print()


if __name__ == "__main__":
    main()
