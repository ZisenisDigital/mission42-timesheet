#!/bin/bash
# Create all remaining PocketBase collections via direct SQLite access
# This bypasses the migration system issues

set -e

DB_PATH="/Users/mr-jy/github/mission42-timesheet/pocketbase/pocketbase/pb_data/data.db"

echo "================================================"
echo "Creating PocketBase Collections"
echo "================================================"
echo

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "❌ Error: Database not found at $DB_PATH"
    exit 1
fi

echo "✓ Database found at $DB_PATH"
echo

# Function to check if table exists
table_exists() {
    sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name='$1';" | grep -q "$1"
}

# Function to check if collection is registered
collection_registered() {
    sqlite3 "$DB_PATH" "SELECT name FROM _collections WHERE name='$1';" | grep -q "$1"
}

# 1. Create raw_events collection
echo "📝 Creating raw_events collection..."
if table_exists "raw_events"; then
    echo "   ⚠️  Table already exists, skipping table creation"
else
    sqlite3 "$DB_PATH" <<EOF
CREATE TABLE raw_events (
    id TEXT PRIMARY KEY NOT NULL,
    created TEXT DEFAULT (datetime('now')) NOT NULL,
    updated TEXT DEFAULT (datetime('now')) NOT NULL,
    source TEXT NOT NULL,
    source_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL,
    description TEXT NOT NULL,
    metadata TEXT
);

CREATE INDEX idx_raw_events_source ON raw_events(source);
CREATE INDEX idx_raw_events_timestamp ON raw_events(timestamp);
CREATE UNIQUE INDEX idx_raw_events_source_id ON raw_events(source, source_id);
EOF
    echo "   ✓ Table created"
fi

# Register in _collections if not already registered
if collection_registered "raw_events"; then
    echo "   ⚠️  Collection already registered"
else
    sqlite3 "$DB_PATH" <<EOF
INSERT INTO _collections (id, created, updated, name, type, system, fields, indexes, listRule, viewRule, createRule, updateRule, deleteRule, options)
VALUES (
    'raw_events_collection',
    datetime('now'),
    datetime('now'),
    'raw_events',
    'base',
    0,
    json('[
        {"id":"field_source","name":"source","type":"text","system":false,"required":true,"presentable":false,"unique":false,"options":{"min":null,"max":100,"pattern":""}},
        {"id":"field_source_id","name":"source_id","type":"text","system":false,"required":true,"presentable":false,"unique":false,"options":{"min":null,"max":255,"pattern":""}},
        {"id":"field_timestamp","name":"timestamp","type":"date","system":false,"required":true,"presentable":false,"unique":false,"options":{"min":"","max":""}},
        {"id":"field_duration_minutes","name":"duration_minutes","type":"number","system":false,"required":true,"presentable":false,"unique":false,"options":{"min":0,"max":null,"noDecimal":true}},
        {"id":"field_description","name":"description","type":"text","system":false,"required":true,"presentable":false,"unique":false,"options":{"min":null,"max":1000,"pattern":""}},
        {"id":"field_metadata","name":"metadata","type":"json","system":false,"required":false,"presentable":false,"unique":false,"options":{"maxSize":2000000}}
    ]'),
    json('["CREATE INDEX idx_raw_events_source ON raw_events(source)","CREATE INDEX idx_raw_events_timestamp ON raw_events(timestamp)","CREATE UNIQUE INDEX idx_raw_events_source_id ON raw_events(source, source_id)"]'),
    '',
    '',
    '',
    '',
    '',
    '{}'
);
EOF
    echo "   ✓ Collection registered"
fi

# 2. Create time_blocks collection
echo "📦 Creating time_blocks collection..."
if table_exists "time_blocks"; then
    echo "   ⚠️  Table already exists, skipping table creation"
else
    sqlite3 "$DB_PATH" <<EOF
CREATE TABLE time_blocks (
    id TEXT PRIMARY KEY NOT NULL,
    created TEXT DEFAULT (datetime('now')) NOT NULL,
    updated TEXT DEFAULT (datetime('now')) NOT NULL,
    week_start TEXT NOT NULL,
    block_start TEXT NOT NULL,
    block_end TEXT NOT NULL,
    source TEXT NOT NULL,
    description TEXT NOT NULL,
    duration_hours REAL NOT NULL,
    metadata TEXT
);

CREATE INDEX idx_time_blocks_week_start ON time_blocks(week_start);
CREATE INDEX idx_time_blocks_source ON time_blocks(source);
CREATE INDEX idx_time_blocks_block_start ON time_blocks(block_start);
EOF
    echo "   ✓ Table created"
fi

if collection_registered "time_blocks"; then
    echo "   ⚠️  Collection already registered"
else
    sqlite3 "$DB_PATH" <<EOF
INSERT INTO _collections (id, created, updated, name, type, system, fields, indexes, listRule, viewRule, createRule, updateRule, deleteRule, options)
VALUES (
    'time_blocks_collection',
    datetime('now'),
    datetime('now'),
    'time_blocks',
    'base',
    0,
    json('[
        {"id":"field_week_start","name":"week_start","type":"date","system":false,"required":true,"presentable":false,"unique":false,"options":{"min":"","max":""}},
        {"id":"field_block_start","name":"block_start","type":"date","system":false,"required":true,"presentable":false,"unique":false,"options":{"min":"","max":""}},
        {"id":"field_block_end","name":"block_end","type":"date","system":false,"required":true,"presentable":false,"unique":false,"options":{"min":"","max":""}},
        {"id":"field_source","name":"source","type":"text","system":false,"required":true,"presentable":false,"unique":false,"options":{"min":null,"max":100,"pattern":""}},
        {"id":"field_description","name":"description","type":"text","system":false,"required":true,"presentable":false,"unique":false,"options":{"min":null,"max":1000,"pattern":""}},
        {"id":"field_duration_hours","name":"duration_hours","type":"number","system":false,"required":true,"presentable":false,"unique":false,"options":{"min":0,"max":null,"noDecimal":false}},
        {"id":"field_metadata","name":"metadata","type":"json","system":false,"required":false,"presentable":false,"unique":false,"options":{"maxSize":2000000}}
    ]'),
    json('["CREATE INDEX idx_time_blocks_week_start ON time_blocks(week_start)","CREATE INDEX idx_time_blocks_source ON time_blocks(source)","CREATE INDEX idx_time_blocks_block_start ON time_blocks(block_start)"]'),
    '',
    '',
    '',
    '',
    '',
    '{}'
);
EOF
    echo "   ✓ Collection registered"
fi

# 3. Create week_summaries collection
echo "📊 Creating week_summaries collection..."
if table_exists "week_summaries"; then
    echo "   ⚠️  Table already exists, skipping table creation"
else
    sqlite3 "$DB_PATH" <<EOF
CREATE TABLE week_summaries (
    id TEXT PRIMARY KEY NOT NULL,
    created TEXT DEFAULT (datetime('now')) NOT NULL,
    updated TEXT DEFAULT (datetime('now')) NOT NULL,
    week_start TEXT NOT NULL UNIQUE,
    total_hours REAL NOT NULL DEFAULT 0,
    metadata TEXT
);

CREATE UNIQUE INDEX idx_week_summaries_week_start ON week_summaries(week_start);
EOF
    echo "   ✓ Table created"
fi

if collection_registered "week_summaries"; then
    echo "   ⚠️  Collection already registered"
else
    sqlite3 "$DB_PATH" <<EOF
INSERT INTO _collections (id, created, updated, name, type, system, fields, indexes, listRule, viewRule, createRule, updateRule, deleteRule, options)
VALUES (
    'week_summaries_collection',
    datetime('now'),
    datetime('now'),
    'week_summaries',
    'base',
    0,
    json('[
        {"id":"field_week_start","name":"week_start","type":"date","system":false,"required":true,"presentable":true,"unique":true,"options":{"min":"","max":""}},
        {"id":"field_total_hours","name":"total_hours","type":"number","system":false,"required":true,"presentable":false,"unique":false,"options":{"min":0,"max":null,"noDecimal":false}},
        {"id":"field_metadata","name":"metadata","type":"json","system":false,"required":false,"presentable":false,"unique":false,"options":{"maxSize":2000000}}
    ]'),
    json('["CREATE UNIQUE INDEX idx_week_summaries_week_start ON week_summaries(week_start)"]'),
    '',
    '',
    '',
    '',
    '',
    '{}'
);
EOF
    echo "   ✓ Collection registered"
fi

# 4. Create work_packages collection
echo "📁 Creating work_packages collection..."
if table_exists "work_packages"; then
    echo "   ⚠️  Table already exists, skipping table creation"
else
    sqlite3 "$DB_PATH" <<EOF
CREATE TABLE work_packages (
    id TEXT PRIMARY KEY NOT NULL,
    created TEXT DEFAULT (datetime('now')) NOT NULL,
    updated TEXT DEFAULT (datetime('now')) NOT NULL,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    is_default INTEGER NOT NULL DEFAULT 0
);

CREATE UNIQUE INDEX idx_work_packages_name ON work_packages(name);
EOF
    echo "   ✓ Table created"
fi

if collection_registered "work_packages"; then
    echo "   ⚠️  Collection already registered"
else
    sqlite3 "$DB_PATH" <<EOF
INSERT INTO _collections (id, created, updated, name, type, system, fields, indexes, listRule, viewRule, createRule, updateRule, deleteRule, options)
VALUES (
    'work_packages_collection',
    datetime('now'),
    datetime('now'),
    'work_packages',
    'base',
    0,
    json('[
        {"id":"field_name","name":"name","type":"text","system":false,"required":true,"presentable":true,"unique":true,"options":{"min":1,"max":255,"pattern":""}},
        {"id":"field_description","name":"description","type":"text","system":false,"required":false,"presentable":false,"unique":false,"options":{"min":null,"max":1000,"pattern":""}},
        {"id":"field_is_active","name":"is_active","type":"bool","system":false,"required":true,"presentable":false,"unique":false,"options":{}},
        {"id":"field_is_default","name":"is_default","type":"bool","system":false,"required":true,"presentable":false,"unique":false,"options":{}}
    ]'),
    json('["CREATE UNIQUE INDEX idx_work_packages_name ON work_packages(name)"]'),
    '',
    '',
    '',
    '',
    '',
    '{}'
);
EOF
    echo "   ✓ Collection registered"
fi

# 5. Create project_specs collection
echo "📋 Creating project_specs collection..."
if table_exists "project_specs"; then
    echo "   ⚠️  Table already exists, skipping table creation"
else
    sqlite3 "$DB_PATH" <<EOF
CREATE TABLE project_specs (
    id TEXT PRIMARY KEY NOT NULL,
    created TEXT DEFAULT (datetime('now')) NOT NULL,
    updated TEXT DEFAULT (datetime('now')) NOT NULL,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    work_package TEXT,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE UNIQUE INDEX idx_project_specs_name ON project_specs(name);
EOF
    echo "   ✓ Table created"
fi

if collection_registered "project_specs"; then
    echo "   ⚠️  Collection already registered"
else
    sqlite3 "$DB_PATH" <<EOF
INSERT INTO _collections (id, created, updated, name, type, system, fields, indexes, listRule, viewRule, createRule, updateRule, deleteRule, options)
VALUES (
    'project_specs_collection',
    datetime('now'),
    datetime('now'),
    'project_specs',
    'base',
    0,
    json('[
        {"id":"field_name","name":"name","type":"text","system":false,"required":true,"presentable":true,"unique":true,"options":{"min":1,"max":255,"pattern":""}},
        {"id":"field_description","name":"description","type":"text","system":false,"required":false,"presentable":false,"unique":false,"options":{"min":null,"max":1000,"pattern":""}},
        {"id":"field_work_package","name":"work_package","type":"text","system":false,"required":false,"presentable":false,"unique":false,"options":{"min":null,"max":255,"pattern":""}},
        {"id":"field_is_active","name":"is_active","type":"bool","system":false,"required":true,"presentable":false,"unique":false,"options":{}}
    ]'),
    json('["CREATE UNIQUE INDEX idx_project_specs_name ON project_specs(name)"]'),
    '',
    '',
    '',
    '',
    '',
    '{}'
);
EOF
    echo "   ✓ Collection registered"
fi

echo
echo "================================================"
echo "✅ All collections created successfully!"
echo "================================================"
echo
echo "Collections created:"
echo "  1. raw_events - Raw events from all data sources"
echo "  2. time_blocks - Processed 30-minute time blocks"
echo "  3. week_summaries - Weekly hour summaries"
echo "  4. work_packages - Billable project categories"
echo "  5. project_specs - Granular project specifications"
echo
echo "⏭️  Next steps:"
echo "  1. Restart PocketBase to load new collections:"
echo "     pkill -f pocketbase"
echo "     cd /Users/mr-jy/github/mission42-timesheet/pocketbase/pocketbase && ./pocketbase serve > /tmp/pocketbase.log 2>&1 &"
echo
echo "  2. Seed work packages and project specs:"
echo "     uv run python scripts/seed_work_packages.py"
echo "     uv run python scripts/seed_project_specs.py"
echo
echo "  3. Verify collections are accessible:"
echo "     curl http://127.0.0.1:8090/api/collections"
echo
