#!/usr/bin/env python3
"""
Seed Work Packages

Seeds default work package categories into PocketBase.
Work packages represent billable project categories for time tracking.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.pocketbase_client import PocketBaseClient


def seed_work_packages():
    """Seed default work packages into PocketBase."""

    # Initialize PocketBase client
    pb_client = PocketBaseClient()

    # Check PocketBase connection
    if not pb_client.health_check():
        print("❌ Error: PocketBase is not running or not accessible")
        print("   Please start PocketBase with: cd pocketbase && ./pocketbase serve")
        sys.exit(1)

    print("✓ Connected to PocketBase")

    # Default work packages to seed
    work_packages = [
        {
            "name": "Development",
            "description": "Software development and coding tasks",
            "is_active": True,
            "is_default": True,
        },
        {
            "name": "Planning",
            "description": "Project planning, architecture, and design",
            "is_active": True,
            "is_default": False,
        },
        {
            "name": "Testing",
            "description": "Quality assurance, testing, and bug verification",
            "is_active": True,
            "is_default": False,
        },
        {
            "name": "Troubleshooting",
            "description": "Debugging, issue investigation, and problem resolution",
            "is_active": True,
            "is_default": False,
        },
        {
            "name": "Meetings",
            "description": "Team meetings, client calls, and discussions",
            "is_active": True,
            "is_default": False,
        },
        {
            "name": "Emails",
            "description": "Email correspondence and communication",
            "is_active": True,
            "is_default": False,
        },
    ]

    print(f"\n📦 Seeding {len(work_packages)} work packages...")

    created = 0
    updated = 0
    errors = 0

    for wp in work_packages:
        try:
            # Check if work package already exists
            if pb_client.exists(
                pb_client.COLLECTION_WORK_PACKAGES,
                f'name="{wp["name"]}"'
            ):
                # Update existing work package
                existing = pb_client.get_first_list_item(
                    pb_client.COLLECTION_WORK_PACKAGES,
                    f'name="{wp["name"]}"'
                )
                pb_client.update(
                    pb_client.COLLECTION_WORK_PACKAGES,
                    existing.id,
                    wp
                )
                print(f"   ↻ Updated: {wp['name']}")
                updated += 1
            else:
                # Create new work package
                pb_client.create(pb_client.COLLECTION_WORK_PACKAGES, wp)
                print(f"   ✓ Created: {wp['name']}")
                created += 1

        except Exception as e:
            print(f"   ✗ Error seeding {wp['name']}: {str(e)}")
            errors += 1

    # Summary
    print(f"\n✅ Work package seeding complete!")
    print(f"   Created: {created}")
    print(f"   Updated: {updated}")
    print(f"   Errors:  {errors}")

    if errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    seed_work_packages()
