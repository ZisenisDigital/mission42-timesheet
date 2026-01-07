#!/usr/bin/env python3
"""
Add Fields to PocketBase Collections

This script adds missing schema fields to existing collections.
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
    print("🔧 Adding Fields to PocketBase Collections")
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
    print("Adding fields to collections...")
    print()

    # Define fields for settings collection
    settings_fields = [
        {
            "name": "key",
            "type": "text",
            "required": True,
            "options": {"min": 1, "max": 100, "pattern": ""}
        },
        {
            "name": "value",
            "type": "text",
            "required": True,
            "options": {"min": None, "max": 1000, "pattern": ""}
        },
        {
            "name": "type",
            "type": "select",
            "required": True,
            "options": {"maxSelect": 1, "values": ["string", "number", "boolean"]}
        },
        {
            "name": "description",
            "type": "text",
            "required": False,
            "options": {"min": None, "max": 500, "pattern": ""}
        },
        {
            "name": "category",
            "type": "select",
            "required": True,
            "options": {
                "maxSelect": 1,
                "values": ["core", "wakatime", "calendar", "gmail", "github", "cloud_events", "processing", "export"]
            }
        },
        {
            "name": "validation_rules",
            "type": "json",
            "required": False,
            "options": {"maxSize": 2000000}
        },
    ]

    try:
        # Get existing collection
        collection = pb.collections.get_one("settings")

        # Get existing field names (excluding system fields)
        existing_field_names = [f.name for f in collection.fields if not f.system]

        # Convert existing fields to dicts
        all_fields = []

        # Add existing non-system fields
        for field in collection.fields:
            if not field.system:
                # Convert CollectionField to dict
                field_dict = {
                    "name": field.name,
                    "type": field.type,
                    "required": field.required,
                    "options": field.options
                }
                all_fields.append(field_dict)

        # Add new fields (avoiding duplicates)
        for new_field in settings_fields:
            if new_field["name"] not in existing_field_names:
                all_fields.append(new_field)

        # Update collection with new fields (don't include system fields in update)
        pb.collections.update(collection.id, {"fields": all_fields})

        print(f"  ✅ settings - Added {len([f for f in settings_fields if f['name'] not in existing_field_names])} fields")

    except Exception as e:
        print(f"  ❌ settings - Error: {e}")

    print()
    print("=" * 80)
    print("✨ Complete!")
    print("=" * 80)
    print()


if __name__ == "__main__":
    main()
