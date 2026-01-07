# Settings Documentation

Complete reference for all 28 configuration settings in the Mission42 Timesheet system.

## Table of Contents

- [Core Settings](#core-settings) (10)
- [WakaTime Settings](#wakatime-settings) (1)
- [Google Calendar Settings](#google-calendar-settings) (2)
- [Gmail Settings](#gmail-settings) (3)
- [GitHub Settings](#github-settings) (5)
- [Cloud Events Settings](#cloud-events-settings) (1)
- [Processing Settings](#processing-settings) (7)
- [Export Settings](#export-settings) (2)

---

## Core Settings

Core work week definition and scheduling configuration.

### `work_week_start_day`

- **Type**: `string`
- **Default**: `monday`
- **Valid Values**: `monday`, `tuesday`, `wednesday`, `thursday`, `friday`, `saturday`, `sunday`
- **Description**: Defines which day of the week your work week starts. Combined with `work_week_start_time` to determine the exact start moment.
- **Example**: If set to `monday`, the work week starts on Monday at the time specified in `work_week_start_time`.

### `work_week_start_time`

- **Type**: `string`
- **Default**: `18:00` (6:00 PM)
- **Format**: `HH:MM` (24-hour format)
- **Valid Range**: `00:00` to `23:59`
- **Description**: The time when your work week starts. For example, `18:00` means 6:00 PM.
- **Example**: If `work_week_start_day` is `monday` and this is `18:00`, the work week starts Monday at 6:00 PM.

### `work_week_end_day`

- **Type**: `string`
- **Default**: `saturday`
- **Valid Values**: `monday`, `tuesday`, `wednesday`, `thursday`, `friday`, `saturday`, `sunday`
- **Description**: Defines which day of the week your work week ends. Must come after `work_week_start_day`.
- **Example**: If set to `saturday`, the work week ends on Saturday at the time specified in `work_week_end_time`.

### `work_week_end_time`

- **Type**: `string`
- **Default**: `18:00` (6:00 PM)
- **Format**: `HH:MM` (24-hour format)
- **Valid Range**: `00:00` to `23:59`
- **Description**: The time when your work week ends.
- **Example**: If `work_week_end_day` is `saturday` and this is `18:00`, the work week ends Saturday at 6:00 PM, giving you a 4.5-day work week (Monday 6 PM → Saturday 6 PM).

### `target_hours_per_week`

- **Type**: `number`
- **Default**: `40`
- **Valid Range**: `1` to `168`
- **Description**: The target number of hours to track each work week. When `auto_fill_enabled` is `true`, the system will automatically fill missing hours to reach this target.
- **Example**: With default `40`, if you have 32 hours tracked, the system will auto-fill 8 hours to reach 40.
- **Note**: Hours above this target accumulate as "carry-over hours" (up to `max_carry_over_hours`).

### `fetch_interval_hours`

- **Type**: `number`
- **Default**: `5`
- **Valid Range**: `1` to `24`
- **Description**: How often (in hours) the system fetches data from all enabled sources (WakaTime, Google Calendar, Gmail, GitHub, Cloud Events).
- **Example**: With default `5`, data is fetched every 5 hours automatically.
- **Recommendation**: Lower values (1-3 hours) for more frequent updates, higher values (6-12 hours) for less API usage.

### `time_block_size_minutes`

- **Type**: `number`
- **Default**: `30`
- **Valid Values**: `30` (fixed)
- **Description**: The granularity of time blocks in minutes. All events are converted to 30-minute blocks (0.5 hours).
- **Note**: This value is fixed at 30 and cannot be changed. It's the fundamental time unit of the system.

### `auto_fill_enabled`

- **Type**: `boolean`
- **Default**: `true`
- **Description**: Enable or disable automatic filling of hours to reach `target_hours_per_week`.
- **Behavior**:
  - `true`: Auto-fill runs on the day specified in `auto_fill_day` at `work_week_start_time`
  - `false`: No automatic filling; only tracked hours are recorded
- **Example**: With `true` and `target_hours_per_week=40`, if you tracked 35 hours, the system adds 5 hours automatically.

### `auto_fill_day`

- **Type**: `string`
- **Default**: `monday`
- **Valid Values**: `monday`, `tuesday`, `wednesday`, `thursday`, `friday`, `saturday`, `sunday`
- **Description**: The day of the week when auto-fill job runs (at the time specified in `work_week_start_time`).
- **Example**: With `monday` and `work_week_start_time=18:00`, auto-fill runs every Monday at 6:00 PM to finalize the previous week's hours.

### `default_location`

- **Type**: `string`
- **Default**: `Remote`
- **Max Length**: 100 characters
- **Description**: The default location value assigned to all time entries.
- **Example**: Change to `Office`, `Home`, `Client Site`, etc. based on your work arrangement.

---

## WakaTime Settings

Configuration for WakaTime coding activity tracking (priority: 100).

### `wakatime_enabled`

- **Type**: `boolean`
- **Default**: `true`
- **Description**: Enable or disable WakaTime coding activity tracking.
- **Requirements**:
  - `WAKATIME_API_KEY` must be set in `.env`
  - WakaTime editor plugin installed and tracking
- **Priority**: 100 (highest) - WakaTime is considered ground truth for coding time
- **Note**: When disabled, no data is fetched from WakaTime even if the API key is configured.

---

## Google Calendar Settings

Configuration for Google Calendar meeting tracking (priority: 80).

### `calendar_enabled`

- **Type**: `boolean`
- **Default**: `true`
- **Description**: Enable or disable Google Calendar meeting tracking.
- **Requirements**:
  - Google OAuth configured in `.env`
  - Calendar accounts added in PocketBase `calendar_accounts` collection
- **Priority**: 80 (high) - Calendar meetings take precedence over emails and GitHub activity

### `calendar_monitored_emails`

- **Type**: `string`
- **Default**: `""` (empty = monitor all)
- **Format**: Comma-separated email addresses
- **Description**: Specify which calendar email addresses to monitor for meetings. Leave empty to monitor all connected calendars.
- **Example**:
  - `"work@example.com"` - Only monitor work calendar
  - `"work@example.com,personal@gmail.com"` - Monitor both calendars
  - `""` - Monitor all connected calendars
- **Validation**: Must be valid email format (e.g., `user@domain.com`)

---

## Gmail Settings

Configuration for Gmail sent email tracking (priority: 60).

### `gmail_enabled`

- **Type**: `boolean`
- **Default**: `true`
- **Description**: Enable or disable Gmail sent email tracking.
- **Requirements**:
  - Google OAuth configured in `.env`
  - Gmail accounts added in PocketBase `email_accounts` collection
- **Priority**: 60 (medium-high) - Sent emails tracked as work activities
- **Note**: Only sent emails are tracked (not received emails)

### `gmail_monitored_recipients`

- **Type**: `string`
- **Default**: `""` (empty = track all)
- **Format**: Comma-separated email addresses
- **Description**: Specify which recipient email addresses to track sent emails to. Leave empty to track all sent emails.
- **Example**:
  - `"client@example.com"` - Only track emails sent to this client
  - `"client1@example.com,client2@example.com"` - Track emails to multiple recipients
  - `""` - Track all sent emails
- **Validation**: Must be valid email format

### `gmail_default_duration_minutes`

- **Type**: `number`
- **Default**: `30`
- **Valid Range**: `5` to `240` (4 hours)
- **Description**: The default duration in minutes to assign to each sent email. Emails are treated as work activities with this duration.
- **Example**: With `30`, each sent email counts as 30 minutes (0.5 hours) of work.
- **Recommendation**:
  - `15-30`: Quick emails
  - `30-60`: Standard emails with some thought
  - `60-120`: Complex emails with research

---

## GitHub Settings

Configuration for GitHub activity tracking (priority: 40).

### `github_enabled`

- **Type**: `boolean`
- **Default**: `true`
- **Description**: Enable or disable GitHub activity tracking.
- **Requirements**:
  - `GITHUB_TOKEN` must be set in `.env`
  - `GITHUB_USERNAME` must be set in `.env`
- **Priority**: 40 (lower) - GitHub activities tracked but with lower priority than coding time

### `github_repositories`

- **Type**: `string`
- **Default**: `""` (empty = no repos tracked)
- **Format**: Comma-separated repository names in `owner/repo` format
- **Description**: Specify which GitHub repositories to track activity in.
- **Example**:
  - `"user/project1"` - Track one repository
  - `"user/project1,org/project2,user/project3"` - Track multiple repositories
  - `""` - Don't track any repositories (disables all GitHub tracking even if `github_enabled=true`)
- **Validation**: Must match pattern `owner/repo` (e.g., `microsoft/vscode`)

### `github_track_commits`

- **Type**: `boolean`
- **Default**: `true`
- **Description**: Track commit activity in monitored repositories.
- **Behavior**: When `true`, commits by your GitHub user are tracked as work activities.
- **Duration**: Commits are assigned duration based on lines changed (usually 15-30 minutes per commit).

### `github_track_issues`

- **Type**: `boolean`
- **Default**: `true`
- **Description**: Track activity on issues assigned to you in monitored repositories.
- **Behavior**: When `true`, issue creation, updates, and comments are tracked.
- **Duration**: Issues are assigned duration based on activity (comments, updates).

### `github_track_prs`

- **Type**: `boolean`
- **Default**: `false`
- **Description**: Track pull request review activity in monitored repositories.
- **Behavior**: When `true`, PR reviews, comments, and approvals are tracked.
- **Note**: Disabled by default as it can overlap with commit tracking and coding time from WakaTime.

---

## Cloud Events Settings

Configuration for custom cloud events tracking (priority: 40).

### `cloud_events_enabled`

- **Type**: `boolean`
- **Default**: `true`
- **Description**: Enable or disable custom cloud events tracking via API.
- **Priority**: 40 (same as GitHub)
- **Usage**: Allows manual creation of time entries via API:
  ```bash
  curl -X POST http://localhost:8000/events \
    -H "Content-Type: application/json" \
    -d '{
      "event_type": "meeting",
      "timestamp": "2026-01-07T14:00:00Z",
      "duration_minutes": 60,
      "description": "Client call"
    }'
  ```

---

## Processing Settings

Configuration for time block processing and auto-fill logic.

### `rounding_mode`

- **Type**: `string`
- **Default**: `up`
- **Valid Values**: `up`, `nearest`
- **Description**: How to round time durations to 0.5-hour blocks.
- **Behavior**:
  - `up`: Always round up to the next 0.5h block (e.g., 0:20 → 0:30, 0:35 → 1:00)
  - `nearest`: Round to the nearest 0.5h block (e.g., 0:20 → 0:30, 0:35 → 0:30, 0:50 → 1:00)
- **Recommendation**: Use `up` to avoid under-counting work hours.

### `group_same_activities`

- **Type**: `boolean`
- **Default**: `false`
- **Description**: Whether to group identical activities in the same day into one entry.
- **Behavior**:
  - `true`: Multiple coding sessions from WakaTime on same day → one entry with combined duration
  - `false`: Each coding session appears as separate entry
- **Example**: Three 1-hour coding sessions → one 3-hour entry (if `true`) vs. three 1-hour entries (if `false`)

### `fill_up_topic_mode`

- **Type**: `string`
- **Default**: `manual`
- **Valid Values**: `manual`, `auto`, `generic`
- **Description**: How to determine the topic/work package for auto-filled hours.
- **Behavior**:
  - `manual`: User manually sets topic (requires user input)
  - `auto`: Use most frequently occurring topic from the week
  - `generic`: Use `fill_up_default_topic` for all auto-filled hours
- **Recommendation**: Use `generic` for simplicity.

### `fill_up_default_topic`

- **Type**: `string`
- **Default**: `General`
- **Max Length**: 100 characters
- **Description**: The default topic/work package to use for auto-filled hours when `fill_up_topic_mode` is `generic`.
- **Example**: `Development`, `General`, `Administrative`, `Project Work`

### `fill_up_distribution`

- **Type**: `string`
- **Default**: `end_of_week`
- **Valid Values**: `end_of_week`, `distributed`, `empty_slots`
- **Description**: How to distribute auto-filled hours across the work week.
- **Behavior**:
  - `end_of_week`: Add all auto-filled hours at the end of the week (Saturday 5-6 PM)
  - `distributed`: Spread auto-filled hours evenly across all days
  - `empty_slots`: Only fill time slots that have no activity
- **Recommendation**: Use `end_of_week` for simplicity.

### `overlap_handling`

- **Type**: `string`
- **Default**: `priority`
- **Valid Values**: `priority`, `show_both`, `combine`
- **Description**: How to handle overlapping time blocks from different sources.
- **Behavior**:
  - `priority`: Use only the highest priority source (WakaTime > Calendar > Gmail > GitHub)
  - `show_both`: Display both overlapping activities as separate entries
  - `combine`: Merge descriptions of overlapping activities into one entry
- **Recommendation**: Use `priority` to avoid double-counting hours.

### `max_carry_over_hours`

- **Type**: `number`
- **Default**: `2000`
- **Valid Range**: `0` to `10000`
- **Description**: Maximum number of hours that can accumulate as carry-over (hours tracked above `target_hours_per_week`).
- **Behavior**: When you track more than `target_hours_per_week`, excess hours accumulate up to this limit.
- **Example**: If you track 45 hours when target is 40, you gain 5 carry-over hours. These accumulate week after week up to `max_carry_over_hours`.

---

## Export Settings

Configuration for timesheet export formatting.

### `export_show_weekly_breakdown`

- **Type**: `boolean`
- **Default**: `false`
- **Description**: Whether to show weekly hour totals breakdown in monthly export files.
- **Behavior**:
  - `true`: Monthly export includes section with per-week totals (Week 1: 40h, Week 2: 38h, etc.)
  - `false`: Only show overall monthly total
- **Use Case**: Enable if you need to report weekly progress within monthly reports.

### `export_title_name`

- **Type**: `string`
- **Default**: `Koni`
- **Max Length**: 50 characters
- **Description**: Name to display in export title. Used in format: `Zeiterfassung - {name}` for German exports or `Timesheet - {name}` for English.
- **Example**: Change to your name or employee ID for personalized exports.

---

## Managing Settings

### Via PocketBase Admin UI

1. **Access Admin UI**: http://localhost:8090/_/
2. **Navigate to Settings**: Collections → settings
3. **Edit a Setting**:
   - Click on any setting row
   - Modify the `value` field
   - Click "Save"
4. **Changes Take Effect**: On next fetch/process cycle (within `fetch_interval_hours`)

### Via Python API

```python
from app.config import config
from pocketbase import PocketBase

# Initialize (done automatically by app)
pb = PocketBase("http://127.0.0.1:8090")
config.setup_pocketbase(pb)

# Get all settings
settings = config.settings.get_all()
print(settings.core.target_hours_per_week)  # 40
print(settings.processing.rounding_mode)    # "up"

# Get single setting
value = config.settings.get("target_hours_per_week")
print(value)  # 40

# Update single setting
config.settings.update("target_hours_per_week", 35)

# Update multiple settings
config.settings.update_many({
    "target_hours_per_week": 35,
    "fetch_interval_hours": 3,
    "auto_fill_enabled": False
})

# Force reload from database
settings = config.settings.reload()
```

### Validation

Settings are validated at three levels:

1. **PocketBase Level**: Basic type checking, required fields, max lengths
2. **Seed Script Level**: Validates against `validation_rules` JSON
3. **Application Level**: Pydantic models with custom validators

**Example Validations:**
- Days of week must be lowercase (`monday` not `Monday`)
- Times must be in 24-hour format `HH:MM` (e.g., `18:00` not `6:00 PM`)
- Email lists must be comma-separated with no spaces around commas
- Repository names must follow `owner/repo` format
- Numeric ranges are enforced (e.g., `target_hours_per_week` must be 1-168)

---

## Best Practices

### Work Week Configuration

**Recommendation**: Monday 6 PM → Saturday 6 PM (default)
- Gives you 4.5 work days (Monday evening through Saturday afternoon)
- Auto-fill runs Monday at 6 PM to finalize previous week
- Aligns with typical work week patterns

**Alternative**: Monday 9 AM → Friday 5 PM (traditional 5-day week)
```
work_week_start_day: monday
work_week_start_time: 09:00
work_week_end_day: friday
work_week_end_time: 17:00
target_hours_per_week: 40
```

### Data Source Configuration

**Recommended Priority**:
1. Enable WakaTime (`wakatime_enabled: true`) - Most accurate coding time
2. Enable Calendar (`calendar_enabled: true`) - Track meetings
3. Enable Gmail (`gmail_enabled: true`) - Track client communication
4. Enable GitHub (`github_enabled: true`) - Track commits (but be aware of overlap with WakaTime)
5. Enable Cloud Events (`cloud_events_enabled: true`) - Manual entries for other activities

**Avoid Double-Counting**:
- If using WakaTime, consider disabling `github_track_commits` to avoid counting same coding time twice
- Use `overlap_handling: priority` to let higher-priority sources win

### Processing Configuration

**For Most Users**:
```
rounding_mode: up
group_same_activities: false
fill_up_topic_mode: generic
fill_up_default_topic: Development
fill_up_distribution: end_of_week
overlap_handling: priority
```

**For Detailed Tracking**:
```
rounding_mode: nearest
group_same_activities: false
fill_up_topic_mode: auto
overlap_handling: show_both
```

---

## Troubleshooting

### Settings Not Taking Effect

**Problem**: Changed a setting but it's not reflected in processing.

**Solutions**:
1. Check if setting was saved successfully in PocketBase admin UI
2. Wait for next fetch cycle (up to `fetch_interval_hours`)
3. Manually trigger fetch: `curl -X POST http://localhost:8000/process/manual`
4. Check logs for errors: `tail -f logs/app.log`
5. Reload settings in Python: `config.settings.reload()`

### Invalid Setting Value

**Problem**: Setting validation error when updating.

**Solutions**:
1. Check valid values in this documentation
2. Ensure correct format (e.g., time as `18:00` not `6:00 PM`)
3. Check range constraints (e.g., `target_hours_per_week` must be 1-168)
4. For email/repo lists, ensure comma-separated with no spaces

### Settings Not Loading

**Problem**: Error "Settings collection not found" or "Expected 28 settings, but found X".

**Solutions**:
1. Run migration: `cd pocketbase && ./pocketbase migrate`
2. Run seed script: `python scripts/seed_settings.py`
3. Check PocketBase is running: `http://localhost:8090/_/`
4. Verify all 28 settings exist in admin UI

---

## Related Documentation

- **README.md**: Quick start guide and overview
- **MASTER_PLAN.md**: Complete implementation plan
- **API Documentation**: http://localhost:8000/docs (when running)

---

**Version**: 1.0.0
**Last Updated**: 2026-01-07
