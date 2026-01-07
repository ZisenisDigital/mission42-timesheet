"""
HTML Template Renderer for Data Collections

Generates beautiful HTML pages for viewing collection data.
"""

import json
from datetime import datetime
from typing import List, Dict, Any


def render_collection_html(collection: str, records: List[Dict[str, Any]]) -> str:
    """
    Render collection data as beautiful HTML.

    Args:
        collection: Collection name
        records: List of record dictionaries

    Returns:
        HTML string
    """
    collection_titles = {
        "settings": "Settings",
        "work_packages": "Work Packages",
        "project_specs": "Project Specifications",
        "raw_events": "Raw Events",
        "time_blocks": "Time Blocks",
        "week_summaries": "Week Summaries",
        "calendar_accounts": "Calendar Accounts",
        "email_accounts": "Email Accounts",
    }

    title = collection_titles.get(collection, collection.replace("_", " ").title())
    count = len(records)

    # Generate table based on collection type
    if collection == "settings":
        table_html = render_settings_table(records)
    elif collection == "work_packages":
        table_html = render_work_packages_table(records)
    elif collection == "project_specs":
        table_html = render_project_specs_table(records)
    elif collection == "raw_events":
        table_html = render_raw_events_table(records)
    elif collection == "time_blocks":
        table_html = render_time_blocks_table(records)
    else:
        table_html = render_generic_table(records)

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Mission42 Timesheet</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
        }}

        .header h1 {{
            font-size: 2em;
            margin-bottom: 5px;
        }}

        .header .subtitle {{
            opacity: 0.9;
            font-size: 1.1em;
        }}

        .info-bar {{
            background: #f8f9fa;
            padding: 20px 30px;
            border-bottom: 2px solid #e0e0e0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }}

        .info-bar .stats {{
            display: flex;
            gap: 30px;
            flex-wrap: wrap;
        }}

        .stat {{
            display: flex;
            flex-direction: column;
        }}

        .stat-label {{
            font-size: 0.85em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .stat-value {{
            font-size: 1.5em;
            font-weight: 600;
            color: #667eea;
        }}

        .actions {{
            display: flex;
            gap: 10px;
        }}

        .btn {{
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.95em;
            font-weight: 500;
            text-decoration: none;
            transition: all 0.3s;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}

        .btn-primary {{
            background: #667eea;
            color: white;
        }}

        .btn-primary:hover {{
            background: #5568d3;
            transform: translateY(-1px);
        }}

        .btn-secondary {{
            background: #e0e0e0;
            color: #333;
        }}

        .btn-secondary:hover {{
            background: #d0d0d0;
        }}

        .content {{
            padding: 30px;
        }}

        .table-container {{
            overflow-x: auto;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
        }}

        thead {{
            background: #667eea;
            color: white;
            position: sticky;
            top: 0;
            z-index: 10;
        }}

        th {{
            padding: 15px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 0.5px;
        }}

        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e0e0e0;
        }}

        tbody tr:hover {{
            background: #f8f9fa;
        }}

        tbody tr:last-child td {{
            border-bottom: none;
        }}

        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 500;
        }}

        .badge-core {{ background: #e3f2fd; color: #1976d2; }}
        .badge-wakatime {{ background: #fff3e0; color: #f57c00; }}
        .badge-calendar {{ background: #f3e5f5; color: #7b1fa2; }}
        .badge-gmail {{ background: #ffebee; color: #c62828; }}
        .badge-github {{ background: #e8f5e9; color: #388e3c; }}
        .badge-cloud_events {{ background: #e1f5fe; color: #0277bd; }}
        .badge-processing {{ background: #fce4ec; color: #c2185b; }}
        .badge-export {{ background: #f1f8e9; color: #558b2f; }}

        .badge-active {{ background: #e8f5e9; color: #388e3c; }}
        .badge-inactive {{ background: #ffebee; color: #c62828; }}

        .badge-true {{ background: #e8f5e9; color: #388e3c; }}
        .badge-false {{ background: #ffebee; color: #c62828; }}

        .empty-state {{
            text-align: center;
            padding: 60px 20px;
            color: #666;
        }}

        .empty-state-icon {{
            font-size: 4em;
            margin-bottom: 15px;
            opacity: 0.3;
        }}

        code {{
            background: #f5f5f5;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 0.9em;
        }}

        .json-value {{
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 0.9em;
            background: #f5f5f5;
            padding: 2px 6px;
            border-radius: 3px;
        }}

        .footer {{
            background: #f8f9fa;
            padding: 20px 30px;
            border-top: 2px solid #e0e0e0;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}

        .nav-links {{
            margin-top: 15px;
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
        }}

        .nav-links a {{
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }}

        .nav-links a:hover {{
            text-decoration: underline;
        }}

        .success-message {{
            background: #e8f5e9;
            color: #388e3c;
            padding: 12px 20px;
            border-radius: 6px;
            margin-bottom: 20px;
            display: none;
            border-left: 4px solid #388e3c;
        }}

        .success-message.show {{
            display: block;
            animation: fadeOut 3s forwards;
        }}

        @keyframes fadeOut {{
            0%, 70% {{ opacity: 1; }}
            100% {{ opacity: 0; }}
        }}

        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.5em;
            }}

            .info-bar {{
                flex-direction: column;
                align-items: flex-start;
            }}

            .actions {{
                width: 100%;
            }}

            .btn {{
                flex: 1;
                justify-content: center;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 {title}</h1>
            <div class="subtitle">Mission42 Timesheet Data</div>
        </div>

        <div class="info-bar">
            <div class="stats">
                <div class="stat">
                    <span class="stat-label">Total Records</span>
                    <span class="stat-value">{count}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Collection</span>
                    <span class="stat-value">{collection}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Updated</span>
                    <span class="stat-value" style="font-size: 1em;">{datetime.now().strftime("%H:%M:%S")}</span>
                </div>
            </div>
            <div class="actions">
                <button class="btn btn-secondary" onclick="window.location.reload()">🔄 Refresh</button>
                <button class="btn btn-primary" onclick="copyTableData()">📋 Copy Table</button>
                <a href="/data/{collection}?format=json" class="btn btn-secondary">📥 JSON</a>
                <a href="/viewer" class="btn btn-secondary">👀 Viewer</a>
                <a href="/dashboard" class="btn btn-secondary">📊 Dashboard</a>
            </div>
        </div>

        <div class="content">
            <div id="success-message" class="success-message"></div>

            {table_html}
        </div>

        <div class="footer">
            <div>Mission42 Timesheet API • Generated at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
            <div class="nav-links">
                <a href="/">Home</a>
                <a href="/docs">API Docs</a>
                <a href="/viewer">Interactive Viewer</a>
                <a href="/dashboard">Dashboard</a>
            </div>
        </div>
    </div>

    <script>
        function copyTableData() {{
            const table = document.querySelector('table');
            if (!table) return;

            let tsv = '';
            const rows = table.querySelectorAll('tr');
            rows.forEach(row => {{
                const cells = row.querySelectorAll('th, td');
                const values = Array.from(cells).map(cell => cell.textContent.trim());
                tsv += values.join('\\t') + '\\n';
            }});

            navigator.clipboard.writeText(tsv).then(() => {{
                const msg = document.getElementById('success-message');
                msg.textContent = '✓ Table copied to clipboard! Paste into Excel or Google Sheets.';
                msg.classList.add('show');
                setTimeout(() => msg.classList.remove('show'), 3000);
            }});
        }}
    </script>
</body>
</html>
"""
    return html


def render_settings_table(records: List[Dict[str, Any]]) -> str:
    """Render settings table."""
    if not records:
        return '<div class="empty-state"><div class="empty-state-icon">📭</div><p>No settings found</p></div>'

    # Group by category
    grouped = {}
    for record in records:
        category = record.get("category", "other")
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(record)

    html = '<div class="table-container"><table><thead><tr>'
    html += '<th>Key</th><th>Value</th><th>Type</th><th>Category</th><th>Description</th>'
    html += '</tr></thead><tbody>'

    for category, settings in sorted(grouped.items()):
        for setting in settings:
            key = setting.get("key", "")
            value = setting.get("value", "")
            stype = setting.get("type", "")
            cat = setting.get("category", "")
            desc = setting.get("description", "")

            html += '<tr>'
            html += f'<td><strong>{key}</strong></td>'
            html += f'<td><code>{value}</code></td>'
            html += f'<td>{stype}</td>'
            html += f'<td><span class="badge badge-{cat}">{cat}</span></td>'
            html += f'<td style="color: #666; font-size: 0.9em;">{desc or "-"}</td>'
            html += '</tr>'

    html += '</tbody></table></div>'
    return html


def render_work_packages_table(records: List[Dict[str, Any]]) -> str:
    """Render work packages table."""
    if not records:
        return '<div class="empty-state"><div class="empty-state-icon">📭</div><p>No work packages found</p></div>'

    html = '<div class="table-container"><table><thead><tr>'
    html += '<th>Name</th><th>Description</th><th>Active</th><th>Default</th>'
    html += '</tr></thead><tbody>'

    for record in records:
        name = record.get("name", "")
        desc = record.get("description", "")
        is_active = record.get("is_active", False)
        is_default = record.get("is_default", False)

        active_badge = 'active' if is_active else 'inactive'
        active_text = 'Active' if is_active else 'Inactive'
        default_text = '⭐ Default' if is_default else '-'

        html += '<tr>'
        html += f'<td><strong>{name}</strong></td>'
        html += f'<td style="color: #666;">{desc or "-"}</td>'
        html += f'<td><span class="badge badge-{active_badge}">{active_text}</span></td>'
        html += f'<td>{default_text}</td>'
        html += '</tr>'

    html += '</tbody></table></div>'
    return html


def render_project_specs_table(records: List[Dict[str, Any]]) -> str:
    """Render project specs table."""
    if not records:
        return '<div class="empty-state"><div class="empty-state-icon">📭</div><p>No project specs found</p></div>'

    html = '<div class="table-container"><table><thead><tr>'
    html += '<th>Name</th><th>Description</th><th>Work Package</th><th>Active</th>'
    html += '</tr></thead><tbody>'

    for record in records:
        name = record.get("name", "")
        desc = record.get("description", "")
        wp = record.get("work_package", "")
        is_active = record.get("is_active", False)

        active_badge = 'active' if is_active else 'inactive'
        active_text = 'Active' if is_active else 'Inactive'

        html += '<tr>'
        html += f'<td><strong>{name}</strong></td>'
        html += f'<td style="color: #666;">{desc or "-"}</td>'
        html += f'<td>{wp or "-"}</td>'
        html += f'<td><span class="badge badge-{active_badge}">{active_text}</span></td>'
        html += '</tr>'

    html += '</tbody></table></div>'
    return html


def render_raw_events_table(records: List[Dict[str, Any]]) -> str:
    """Render raw events table."""
    if not records:
        return '<div class="empty-state"><div class="empty-state-icon">📭</div><p>No raw events yet. Trigger data fetch: POST /process/manual</p></div>'

    html = '<div class="table-container"><table><thead><tr>'
    html += '<th>Source</th><th>Timestamp</th><th>Duration</th><th>Description</th>'
    html += '</tr></thead><tbody>'

    for record in records:
        source = record.get("source", "")
        timestamp = record.get("timestamp", "")
        duration = record.get("duration_minutes", 0)
        desc = record.get("description", "")

        # Format timestamp
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            timestamp_str = dt.strftime("%Y-%m-%d %H:%M")
        except:
            timestamp_str = timestamp

        html += '<tr>'
        html += f'<td><span class="badge badge-{source}">{source}</span></td>'
        html += f'<td>{timestamp_str}</td>'
        html += f'<td>{duration} min</td>'
        html += f'<td>{desc}</td>'
        html += '</tr>'

    html += '</tbody></table></div>'
    return html


def render_time_blocks_table(records: List[Dict[str, Any]]) -> str:
    """Render time blocks table."""
    if not records:
        return '<div class="empty-state"><div class="empty-state-icon">📭</div><p>No time blocks yet. Process data: POST /process/manual</p></div>'

    html = '<div class="table-container"><table><thead><tr>'
    html += '<th>Week Start</th><th>Block Start</th><th>Duration</th><th>Source</th><th>Description</th>'
    html += '</tr></thead><tbody>'

    for record in records:
        week_start = record.get("week_start", "")
        block_start = record.get("block_start", "")
        duration = record.get("duration_hours", 0)
        source = record.get("source", "")
        desc = record.get("description", "")

        # Format dates
        try:
            ws = datetime.fromisoformat(week_start.replace("Z", "+00:00"))
            week_str = ws.strftime("%Y-%m-%d")
        except:
            week_str = week_start

        try:
            bs = datetime.fromisoformat(block_start.replace("Z", "+00:00"))
            block_str = bs.strftime("%Y-%m-%d %H:%M")
        except:
            block_str = block_start

        html += '<tr>'
        html += f'<td>{week_str}</td>'
        html += f'<td>{block_str}</td>'
        html += f'<td><strong>{duration}h</strong></td>'
        html += f'<td><span class="badge badge-{source}">{source}</span></td>'
        html += f'<td>{desc}</td>'
        html += '</tr>'

    html += '</tbody></table></div>'
    return html


def render_generic_table(records: List[Dict[str, Any]]) -> str:
    """Render generic table for any collection."""
    if not records:
        return '<div class="empty-state"><div class="empty-state-icon">📭</div><p>No records found</p></div>'

    # Get all keys (excluding system fields)
    all_keys = set()
    for record in records:
        for key in record.keys():
            if not key.startswith("_") and key not in ["collectionId", "collectionName"]:
                all_keys.add(key)

    keys = sorted(all_keys)

    html = '<div class="table-container"><table><thead><tr>'
    for key in keys:
        html += f'<th>{key.replace("_", " ").title()}</th>'
    html += '</tr></thead><tbody>'

    for record in records:
        html += '<tr>'
        for key in keys:
            value = record.get(key, "")
            if isinstance(value, (dict, list)):
                value = f'<span class="json-value">{json.dumps(value)}</span>'
            elif isinstance(value, bool):
                badge_class = "true" if value else "false"
                value = f'<span class="badge badge-{badge_class}">{str(value)}</span>'
            html += f'<td>{value or "-"}</td>'
        html += '</tr>'

    html += '</tbody></table></div>'
    return html
