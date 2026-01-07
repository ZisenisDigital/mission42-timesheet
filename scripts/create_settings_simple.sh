#!/bin/bash
# Create Settings Collection - Simple Working Version
#
# This script creates the settings collection using direct SQL
# to bypass API schema issues.

set -e

DB_PATH="/Users/mr-jy/github/mission42-timesheet/pocketbase/pocketbase/pb_data/data.db"

echo "========================================="
echo "Creating Settings Table"
echo "========================================="
echo

# Create settings table directly in SQLite
sqlite3 "$DB_PATH" <<'SQL'
-- Drop existing settings table if it exists
DROP TABLE IF EXISTS settings;

-- Create settings table
CREATE TABLE settings (
    id TEXT PRIMARY KEY NOT NULL,
    created TEXT DEFAULT (datetime('now')) NOT NULL,
    updated TEXT DEFAULT (datetime('now')) NOT NULL,
    key TEXT NOT NULL UNIQUE,
    value TEXT NOT NULL,
    type TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    validation_rules TEXT
);

-- Create indexes
CREATE UNIQUE INDEX idx_settings_key ON settings(key);
CREATE INDEX idx_settings_category ON settings(category);

-- Verify
SELECT sql FROM sqlite_master WHERE name='settings';
SQL

echo "✅ Settings table created successfully"
echo

# Now register the collection in PocketBase
TOKEN=$(uv run python -c "from pocketbase import PocketBase; pb = PocketBase('http://127.0.0.1:8090'); pb.admins.auth_with_password('admin@example.com', 'admin123456'); print(pb.auth_store.token)" 2>/dev/null)

# Force PocketBase to recognize the new table by restarting it
echo "Restarting PocketBase to recognize new table..."
pkill -f "pocketbase serve" 2>/dev/null || true
sleep 2
cd /Users/mr-jy/github/mission42-timesheet/pocketbase/pocketbase
./pocketbase serve > /tmp/pocketbase.log 2>&1 &
sleep 3

echo "✅ PocketBase restarted"
echo
echo "Next step: Run seed script"
echo "  uv run python scripts/add_minimal_settings.py"
