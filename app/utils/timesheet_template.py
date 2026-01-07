"""
Simple Timesheet Template for Google Sheets Export

Creates a clean, copy-pasteable timesheet view.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
import calendar


def render_monthly_timesheet(year: int, month: int, time_blocks: List[Dict[str, Any]], total_hours: float) -> str:
    """
    Render monthly timesheet as simple HTML table for Google Sheets.

    Args:
        year: Year
        month: Month (1-12)
        time_blocks: List of time block dictionaries
        total_hours: Total hours for the month

    Returns:
        HTML string
    """
    # Get month name
    month_name = calendar.month_name[month]

    # Format current timestamp
    now = datetime.now()
    updated_at = now.strftime("%d.%m.%Y %H:%M")

    # Sort time blocks by date
    sorted_blocks = sorted(time_blocks, key=lambda b: b.get('block_start', ''))

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Timesheet - {month_name} {year}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }}

        .header {{
            background: #1976d2;
            color: white;
            padding: 24px 30px;
        }}

        .header h1 {{
            font-size: 1.5em;
            font-weight: 500;
            margin-bottom: 4px;
        }}

        .header .subtitle {{
            font-size: 1em;
            opacity: 0.95;
        }}

        .summary {{
            background: #e8f5e9;
            border-left: 4px solid #4caf50;
            padding: 16px 30px;
            font-size: 0.95em;
        }}

        .summary strong {{
            font-weight: 600;
        }}

        .actions {{
            padding: 16px 30px;
            background: #fafafa;
            border-bottom: 1px solid #e0e0e0;
            display: flex;
            gap: 12px;
            align-items: center;
        }}

        .btn {{
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9em;
            font-weight: 500;
            transition: all 0.2s;
        }}

        .btn-primary {{
            background: #1976d2;
            color: white;
        }}

        .btn-primary:hover {{
            background: #1565c0;
        }}

        .btn-secondary {{
            background: #e0e0e0;
            color: #333;
        }}

        .btn-secondary:hover {{
            background: #d5d5d5;
        }}

        .table-container {{
            padding: 0;
            overflow-x: auto;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.95em;
        }}

        thead {{
            background: #1976d2;
            color: white;
        }}

        th {{
            padding: 12px 16px;
            text-align: left;
            font-weight: 500;
            white-space: nowrap;
        }}

        td {{
            padding: 10px 16px;
            border-bottom: 1px solid #e0e0e0;
        }}

        tbody tr:hover {{
            background: #f5f5f5;
        }}

        tbody tr:last-child td {{
            border-bottom: none;
        }}

        .no-data {{
            text-align: center;
            padding: 60px 20px;
            color: #666;
        }}

        .footer {{
            padding: 16px 30px;
            background: #fafafa;
            border-top: 1px solid #e0e0e0;
            text-align: center;
            font-size: 0.85em;
            color: #666;
        }}

        .copy-notice {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 4px;
            padding: 12px;
            margin: 0 30px 20px 30px;
            font-size: 0.9em;
        }}

        .copy-notice strong {{
            color: #856404;
        }}

        /* Make table cells easier to select */
        td, th {{
            user-select: text;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Zeiterfassung - Mission42</h1>
            <div class="subtitle">{month_name} {year}</div>
        </div>

        <div class="summary">
            Daten aktualisiert: {updated_at} | Gesamt: <strong>{total_hours:.1f} Stunden</strong>
        </div>

        <div class="copy-notice">
            <strong>📋 Copy to Google Sheets:</strong> Select the table below (click on first cell, Shift+Click on last cell), copy (Cmd+C / Ctrl+C), and paste into Google Sheets.
        </div>

        <div class="actions">
            <button class="btn btn-primary" onclick="copyTable()">📋 Copy Table</button>
            <button class="btn btn-secondary" onclick="window.location.reload()">🔄 Refresh</button>
            <a href="/dashboard" class="btn btn-secondary">← Back to Dashboard</a>
        </div>

        <div class="table-container">
"""

    if not sorted_blocks:
        html += """
            <div class="no-data">
                <p>No time entries for this month.</p>
                <p style="margin-top: 8px; font-size: 0.9em; color: #999;">Trigger data fetch: <a href="/process/manual" style="color: #1976d2;">POST /process/manual</a></p>
            </div>
"""
    else:
        html += """
            <table id="timesheet-table">
                <thead>
                    <tr>
                        <th>No</th>
                        <th>Datum</th>
                        <th>Stunden</th>
                        <th>Beschreibung</th>
                        <th>Ort</th>
                    </tr>
                </thead>
                <tbody>
"""

        for idx, block in enumerate(sorted_blocks, start=1):
            # Format date
            try:
                block_start = block.get('block_start', '')
                if isinstance(block_start, str):
                    dt = datetime.fromisoformat(block_start.replace('Z', '+00:00'))
                else:
                    dt = block_start
                date_str = dt.strftime('%d.%m.%Y')
            except:
                date_str = str(block.get('block_start', ''))[:10]

            # Get hours
            hours = block.get('duration_hours', 0)
            hours_str = f"{hours:.1f}"

            # Get description
            description = block.get('description', '')

            # Get location (source)
            source = block.get('source', 'Remote')
            location_map = {
                'wakatime': 'Remote',
                'github': 'Remote',
                'calendar': 'Office/Meeting',
                'gmail': 'Remote',
                'auto_fill': 'Remote',
            }
            location = location_map.get(source, 'Remote')

            # Format row number
            no = f"{idx:04d}"

            html += f"""
                    <tr>
                        <td>{no}</td>
                        <td>{date_str}</td>
                        <td>{hours_str}</td>
                        <td>{description}</td>
                        <td>{location}</td>
                    </tr>
"""

        html += """
                </tbody>
            </table>
"""

    html += f"""
        </div>

        <div class="footer">
            Mission42 Timesheet • Generated at {now.strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>

    <script>
        function copyTable() {{
            const table = document.getElementById('timesheet-table');
            if (!table) {{
                alert('No table to copy');
                return;
            }}

            // Create TSV (tab-separated values) for better Excel/Sheets compatibility
            let tsv = '';
            const rows = table.querySelectorAll('tr');
            rows.forEach(row => {{
                const cells = row.querySelectorAll('th, td');
                const values = Array.from(cells).map(cell => cell.textContent.trim());
                tsv += values.join('\\t') + '\\n';
            }});

            // Copy to clipboard
            navigator.clipboard.writeText(tsv).then(() => {{
                // Show success message
                const btn = event.target;
                const originalText = btn.textContent;
                btn.textContent = '✓ Copied!';
                btn.style.background = '#4caf50';
                setTimeout(() => {{
                    btn.textContent = originalText;
                    btn.style.background = '';
                }}, 2000);
            }}).catch(err => {{
                alert('Failed to copy: ' + err);
            }});
        }}

        // Allow selecting entire table with keyboard
        document.addEventListener('keydown', function(e) {{
            if ((e.ctrlKey || e.metaKey) && e.key === 'a') {{
                const table = document.getElementById('timesheet-table');
                if (table && document.activeElement.tagName !== 'INPUT') {{
                    e.preventDefault();
                    const selection = window.getSelection();
                    const range = document.createRange();
                    range.selectNodeContents(table);
                    selection.removeAllRanges();
                    selection.addRange(range);
                }}
            }}
        }});
    </script>
</body>
</html>
"""

    return html
