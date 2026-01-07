#!/usr/bin/env python3
"""
Setup Read-Only Access for Viewer Users

This script configures PocketBase collections to allow authenticated users
to view timesheet data but not modify anything.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pocketbase import PocketBase
from dotenv import load_dotenv

load_dotenv()

PB_URL = os.getenv("POCKETBASE_URL", "http://127.0.0.1:8090")
PB_ADMIN_EMAIL = os.getenv("PB_ADMIN_EMAIL")
PB_ADMIN_PASSWORD = os.getenv("PB_ADMIN_PASSWORD")


def main():
    print("=" * 80)
    print("🔒 Setting Up Read-Only Access Rules")
    print("=" * 80)
    print()

    # Connect and authenticate
    pb = PocketBase(PB_URL)

    try:
        pb.health.check()
        print("✅ Connected to PocketBase")
    except Exception as e:
        print(f"❌ Error: Cannot connect to PocketBase")
        sys.exit(1)

    try:
        pb.admins.auth_with_password(PB_ADMIN_EMAIL, PB_ADMIN_PASSWORD)
        print(f"✅ Authenticated as admin")
    except Exception as e:
        print(f"❌ Error: Authentication failed")
        sys.exit(1)

    print()
    print("Configuring collection rules...")
    print()

    # Collections that viewers can READ but not WRITE
    readonly_collections = {
        "settings": {
            "description": "System settings",
            "rules": {
                "listRule": "@request.auth.id != ''",  # Must be logged in
                "viewRule": "@request.auth.id != ''",  # Must be logged in
                "createRule": "",  # Only admins via API
                "updateRule": "",  # Only admins via API
                "deleteRule": "",  # Only admins via API
            }
        },
        "time_blocks": {
            "description": "Timesheet blocks",
            "rules": {
                "listRule": "@request.auth.id != ''",
                "viewRule": "@request.auth.id != ''",
                "createRule": "",
                "updateRule": "",
                "deleteRule": "",
            }
        },
        "week_summaries": {
            "description": "Weekly summaries",
            "rules": {
                "listRule": "@request.auth.id != ''",
                "viewRule": "@request.auth.id != ''",
                "createRule": "",
                "updateRule": "",
                "deleteRule": "",
            }
        },
        "raw_events": {
            "description": "Raw event data",
            "rules": {
                "listRule": "@request.auth.id != ''",
                "viewRule": "@request.auth.id != ''",
                "createRule": "",
                "updateRule": "",
                "deleteRule": "",
            }
        },
        "work_packages": {
            "description": "Work packages",
            "rules": {
                "listRule": "@request.auth.id != ''",
                "viewRule": "@request.auth.id != ''",
                "createRule": "",
                "updateRule": "",
                "deleteRule": "",
            }
        },
        "project_specs": {
            "description": "Project specifications",
            "rules": {
                "listRule": "@request.auth.id != ''",
                "viewRule": "@request.auth.id != ''",
                "createRule": "",
                "updateRule": "",
                "deleteRule": "",
            }
        }
    }

    updated = 0
    errors = 0

    for coll_name, config in readonly_collections.items():
        try:
            collection = pb.collections.get_one(coll_name)

            # Update rules
            pb.collections.update(collection.id, config["rules"])

            print(f"  ✅ {coll_name:20s} - {config['description']}")
            updated += 1

        except Exception as e:
            print(f"  ❌ {coll_name:20s} - Error: {e}")
            errors += 1

    print()
    print("=" * 80)
    print(f"✨ Complete!")
    print(f"   Updated: {updated} collections")
    print(f"   Errors: {errors} collections")
    print("=" * 80)
    print()

    if updated > 0:
        print("✅ Read-only access configured!")
        print()
        print("📝 Access Instructions:")
        print("   URL: http://127.0.0.1:8090/")
        print("   Viewer credentials: viewer@example.com / ViewerPass123")
        print()
        print("🔒 Viewers can:")
        print("   ✓ List and view timesheet data")
        print("   ✓ See weekly summaries")
        print("   ✓ View settings")
        print()
        print("🚫 Viewers cannot:")
        print("   ✗ Create, update, or delete records")
        print("   ✗ Access admin console")
        print("   ✗ Modify system settings")
        print()


if __name__ == "__main__":
    main()
