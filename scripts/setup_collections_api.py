#!/usr/bin/env python3
"""
Setup Collections via Admin API

This script creates all collections using the PocketBase Admin API,
bypassing migration issues.
"""

import os
import sys
from pathlib import Path
import requests
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pocketbase import PocketBase
from dotenv import load_dotenv

load_dotenv()

# PocketBase configuration
PB_URL = os.getenv("POCKETBASE_URL", "http://127.0.0.1:8090")
PB_ADMIN_EMAIL = os.getenv("PB_ADMIN_EMAIL")
PB_ADMIN_PASSWORD = os.getenv("PB_ADMIN_PASSWORD")


def create_admin_account():
    """Create admin account if it doesn't exist"""
    import subprocess

    result = subprocess.run(
        ["./pocketbase/pocketbase/pocketbase", "superuser", "upsert", PB_ADMIN_EMAIL, PB_ADMIN_PASSWORD],
        capture_output=True,
        text=True,
        cwd="/Users/mr-jy/github/mission42-timesheet"
    )

    if result.returncode == 0:
        print(f"✅ Admin account ready: {PB_ADMIN_EMAIL}")
    else:
        print(f"⚠️  Admin account status: {result.stderr}")


def main():
    print("=" * 80)
    print("🔧 Setting Up PocketBase Collections via API")
    print("=" * 80)
    print()

    # Ensure admin account exists
    create_admin_account()
    print()

    # Initialize PocketBase and authenticate
    pb = PocketBase(PB_URL)

    try:
        pb.health.check()
        print("✅ Connected to PocketBase")
    except Exception as e:
        print(f"❌ Error: Cannot connect to PocketBase at {PB_URL}")
        print(f"   Make sure PocketBase is running!")
        sys.exit(1)

    try:
        pb.admins.auth_with_password(PB_ADMIN_EMAIL, PB_ADMIN_PASSWORD)
        print(f"✅ Authenticated as: {PB_ADMIN_EMAIL}")
    except Exception as e:
        print(f"❌ Error: Authentication failed - {e}")
        sys.exit(1)

    print()

    # Get auth token for direct API calls
    auth_token = pb.auth_store.token

    # Define collection schema
    collections_schema = {
        "settings": {
            "name": "settings",
            "type": "base",
            "schema": [
                {
                    "name": "key",
                    "type": "text",
                    "required": True,
                    "presentable": False,
                    "unique": True,
                    "options": {
                        "min": 1,
                        "max": 100,
                        "pattern": ""
                    }
                },
                {
                    "name": "value",
                    "type": "text",
                    "required": True,
                    "presentable": False,
                    "unique": False,
                    "options": {
                        "min": None,
                        "max": 1000,
                        "pattern": ""
                    }
                },
                {
                    "name": "type",
                    "type": "select",
                    "required": True,
                    "presentable": False,
                    "unique": False,
                    "options": {
                        "maxSelect": 1,
                        "values": ["string", "number", "boolean"]
                    }
                },
                {
                    "name": "description",
                    "type": "text",
                    "required": False,
                    "presentable": False,
                    "unique": False,
                    "options": {
                        "min": None,
                        "max": 500,
                        "pattern": ""
                    }
                },
                {
                    "name": "category",
                    "type": "select",
                    "required": True,
                    "presentable": False,
                    "unique": False,
                    "options": {
                        "maxSelect": 1,
                        "values": ["core", "wakatime", "calendar", "gmail", "github", "cloud_events", "processing", "export"]
                    }
                },
                {
                    "name": "validation_rules",
                    "type": "json",
                    "required": False,
                    "presentable": False,
                    "unique": False,
                    "options": {
                        "maxSize": 2000000
                    }
                }
            ],
            "indexes": [],
            "listRule": "",
            "viewRule": "",
            "createRule": "",
            "updateRule": "",
            "deleteRule": ""
        }
    }

    print("Creating/updating collections...")
    print()

    for coll_name, coll_data in collections_schema.items():
        try:
            # Check if collection exists
            try:
                existing = pb.collections.get_one(coll_name)
                print(f"⏭️  {coll_name} - already exists, updating...")

                # Update existing collection
                response = requests.patch(
                    f"{PB_URL}/api/collections/{existing.id}",
                    json=coll_data,
                    headers={"Authorization": auth_token}
                )

                if response.status_code in [200, 201]:
                    print(f"  ✅ {coll_name} - updated successfully")
                else:
                    print(f"  ❌ {coll_name} - update failed: {response.status_code}")
                    print(f"     Response: {response.text}")

            except Exception:
                # Collection doesn't exist, create it
                response = requests.post(
                    f"{PB_URL}/api/collections",
                    json=coll_data,
                    headers={"Authorization": auth_token}
                )

                if response.status_code in [200, 201]:
                    print(f"  ✅ {coll_name} - created successfully")
                else:
                    print(f"  ❌ {coll_name} - creation failed: {response.status_code}")
                    print(f"     Response: {response.text}")

        except Exception as e:
            print(f"  ❌ {coll_name} - error: {e}")

    print()
    print("=" * 80)
    print("✨ Collection setup complete!")
    print("=" * 80)
    print()
    print("Next step: Populate settings data")
    print("  uv run python scripts/add_minimal_settings.py")
    print()


if __name__ == "__main__":
    main()
