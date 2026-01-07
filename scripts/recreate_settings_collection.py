#!/usr/bin/env python3
"""
Recreate Settings Collection

This script deletes and recreates the settings collection with proper schema.
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
    print("🔧 Recreating Settings Collection")
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

    # Step 1: Delete existing collection
    try:
        collection = pb.collections.get_one("settings")
        pb.collections.delete(collection.id)
        print("✅ Deleted existing settings collection")
    except ClientResponseError as e:
        if e.status == 404:
            print("⏭️  Settings collection doesn't exist, skipping delete")
        else:
            raise

    # Step 2: Create new collection with proper schema using raw API
    import requests

    # Get auth token
    auth_token = pb.auth_store.token

    # Create collection with schema
    collection_data = {
        "name": "settings",
        "type": "base",
        "schema": [
            {
                "name": "key",
                "type": "text",
                "required": True,
                "presentable": False,
                "unique": False,
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
        "listRule": "",
        "viewRule": "",
        "createRule": "",
        "updateRule": "",
        "deleteRule": ""
    }

    response = requests.post(
        f"{PB_URL}/api/collections",
        json=collection_data,
        headers={"Authorization": auth_token}
    )

    if response.status_code in [200, 201]:
        print("✅ Created settings collection with schema")
    else:
        print(f"❌ Failed to create collection: {response.status_code}")
        print(f"   Response: {response.text}")
        sys.exit(1)

    print()
    print("=" * 80)
    print("✨ Complete!")
    print("=" * 80)
    print()
    print("Next step: Run seed script to add settings data")
    print("  uv run python scripts/add_minimal_settings.py")
    print()


if __name__ == "__main__":
    main()
