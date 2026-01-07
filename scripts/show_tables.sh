#!/bin/bash
# Show all table information from PocketBase database

DB_PATH="/Users/mr-jy/github/mission42-timesheet/pocketbase/pocketbase/pb_data/data.db"

echo "================================================"
echo "PocketBase Database Table Information"
echo "================================================"
echo

# List all tables
echo "📋 All Tables:"
echo "----------------------------------------"
sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '_%' ORDER BY name;" | nl
echo

# Show record counts
echo "📊 Record Counts:"
echo "----------------------------------------"
sqlite3 "$DB_PATH" <<EOF
SELECT 'settings:         ' || COUNT(*) || ' records' FROM settings;
SELECT 'work_packages:    ' || COUNT(*) || ' records' FROM work_packages;
SELECT 'project_specs:    ' || COUNT(*) || ' records' FROM project_specs;
SELECT 'raw_events:       ' || COUNT(*) || ' records' FROM raw_events;
SELECT 'time_blocks:      ' || COUNT(*) || ' records' FROM time_blocks;
SELECT 'week_summaries:   ' || COUNT(*) || ' records' FROM week_summaries;
SELECT 'calendar_accounts:' || COUNT(*) || ' records' FROM calendar_accounts;
SELECT 'email_accounts:   ' || COUNT(*) || ' records' FROM email_accounts;
EOF
echo

# Show detailed schema for a specific table (pass as argument)
if [ -n "$1" ]; then
    echo "🔍 Schema for table: $1"
    echo "----------------------------------------"
    sqlite3 "$DB_PATH" ".schema $1"
    echo

    echo "📝 Sample data (first 5 records):"
    echo "----------------------------------------"
    sqlite3 -header -column "$DB_PATH" "SELECT * FROM $1 LIMIT 5;"
else
    echo "💡 Tip: Run with table name to see detailed schema"
    echo "   Example: $0 settings"
fi

echo
echo "================================================"
echo "✅ Done!"
echo "================================================"
