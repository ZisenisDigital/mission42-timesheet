#!/usr/bin/env python3
"""
Seed Project Specs

Seeds default project specification categories into PocketBase.
Project specs provide granular breakdown within work packages.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.pocketbase_client import PocketBaseClient


def seed_project_specs():
    """Seed default project specs into PocketBase."""

    # Initialize PocketBase client
    pb_client = PocketBaseClient()

    # Check PocketBase connection
    if not pb_client.health_check():
        print("❌ Error: PocketBase is not running or not accessible")
        print("   Please start PocketBase with: cd pocketbase && ./pocketbase serve")
        sys.exit(1)

    print("✓ Connected to PocketBase")

    # Default project specs to seed
    project_specs = [
        {
            "name": "Lead",
            "description": "Technical leadership, team coordination, and mentoring",
            "work_package": "Development",
            "is_active": True,
        },
        {
            "name": "Backend",
            "description": "Server-side development, APIs, and database work",
            "work_package": "Development",
            "is_active": True,
        },
        {
            "name": "Frontend",
            "description": "Client-side development, UI, and user experience",
            "work_package": "Development",
            "is_active": True,
        },
        {
            "name": "Infrastructure",
            "description": "DevOps, deployment, monitoring, and system administration",
            "work_package": "Development",
            "is_active": True,
        },
        {
            "name": "Documentation",
            "description": "Technical writing, API docs, and user guides",
            "work_package": "Development",
            "is_active": True,
        },
        {
            "name": "Other",
            "description": "Miscellaneous tasks not covered by other categories",
            "work_package": "Development",
            "is_active": True,
        },
    ]

    print(f"\n📋 Seeding {len(project_specs)} project specs...")

    created = 0
    updated = 0
    errors = 0

    for spec in project_specs:
        try:
            # Check if project spec already exists
            if pb_client.exists(
                pb_client.COLLECTION_PROJECT_SPECS,
                f'name="{spec["name"]}"'
            ):
                # Update existing project spec
                existing = pb_client.get_first_list_item(
                    pb_client.COLLECTION_PROJECT_SPECS,
                    f'name="{spec["name"]}"'
                )
                pb_client.update(
                    pb_client.COLLECTION_PROJECT_SPECS,
                    existing.id,
                    spec
                )
                print(f"   ↻ Updated: {spec['name']}")
                updated += 1
            else:
                # Create new project spec
                pb_client.create(pb_client.COLLECTION_PROJECT_SPECS, spec)
                print(f"   ✓ Created: {spec['name']}")
                created += 1

        except Exception as e:
            print(f"   ✗ Error seeding {spec['name']}: {str(e)}")
            errors += 1

    # Summary
    print(f"\n✅ Project spec seeding complete!")
    print(f"   Created: {created}")
    print(f"   Updated: {updated}")
    print(f"   Errors:  {errors}")

    if errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    seed_project_specs()
