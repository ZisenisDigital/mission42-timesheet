"""
Settings Models

Pydantic models for all configuration settings with validation.
Settings are stored in PocketBase and loaded at runtime.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
import re


class DayOfWeek(str, Enum):
    """Valid days of the week"""
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class RoundingMode(str, Enum):
    """Time rounding modes for 0.5h blocks"""
    UP = "up"  # Always round up to next 0.5h
    NEAREST = "nearest"  # Round to nearest 0.5h


class FillUpTopicMode(str, Enum):
    """Mode for determining topic when auto-filling hours"""
    MANUAL = "manual"  # User manually sets topic
    AUTO = "auto"  # Use most frequent topic from week
    GENERIC = "generic"  # Use generic topic (e.g., "General")


class FillUpDistribution(str, Enum):
    """How to distribute auto-filled hours across the week"""
    END_OF_WEEK = "end_of_week"  # Add all hours at end of week
    DISTRIBUTED = "distributed"  # Spread evenly across week
    EMPTY_SLOTS = "empty_slots"  # Fill only empty time slots


class OverlapHandling(str, Enum):
    """How to handle overlapping time blocks from different sources"""
    PRIORITY = "priority"  # Use highest priority source only
    SHOW_BOTH = "show_both"  # Display both overlapping activities
    COMBINE = "combine"  # Merge descriptions of overlapping activities


# Core Settings (10 settings)
class CoreSettings(BaseModel):
    """Core work week and scheduling settings"""

    work_week_start_day: DayOfWeek = Field(
        default=DayOfWeek.MONDAY,
        description="Day of the week when work week starts"
    )

    work_week_start_time: str = Field(
        default="18:00",
        description="Time when work week starts (24-hour format HH:MM)",
        pattern=r"^([01]\d|2[0-3]):([0-5]\d)$"
    )

    work_week_end_day: DayOfWeek = Field(
        default=DayOfWeek.SATURDAY,
        description="Day of the week when work week ends"
    )

    work_week_end_time: str = Field(
        default="18:00",
        description="Time when work week ends (24-hour format HH:MM)",
        pattern=r"^([01]\d|2[0-3]):([0-5]\d)$"
    )

    target_hours_per_week: int = Field(
        default=40,
        ge=1,
        le=168,
        description="Target number of hours to track per week"
    )

    fetch_interval_hours: int = Field(
        default=5,
        ge=1,
        le=24,
        description="How often to fetch data from sources (in hours)"
    )

    time_block_size_minutes: int = Field(
        default=30,
        description="Size of time blocks in minutes (fixed at 30)"
    )

    auto_fill_enabled: bool = Field(
        default=True,
        description="Enable automatic filling to reach target hours"
    )

    auto_fill_day: DayOfWeek = Field(
        default=DayOfWeek.MONDAY,
        description="Day of week when auto-fill runs (at work_week_start_time)"
    )

    default_location: str = Field(
        default="Remote",
        max_length=100,
        description="Default location for time entries"
    )

    @field_validator("time_block_size_minutes")
    @classmethod
    def validate_block_size(cls, v: int) -> int:
        """Time block size must be 30 minutes"""
        if v != 30:
            raise ValueError("time_block_size_minutes must be 30")
        return v

    @model_validator(mode="after")
    def validate_week_logic(self) -> "CoreSettings":
        """Validate that week start comes before week end"""
        days_order = list(DayOfWeek)
        start_idx = days_order.index(self.work_week_start_day)
        end_idx = days_order.index(self.work_week_end_day)

        if start_idx >= end_idx:
            raise ValueError(
                f"work_week_end_day ({self.work_week_end_day}) must come after "
                f"work_week_start_day ({self.work_week_start_day})"
            )
        return self


# WakaTime Settings (1 setting)
class WakaTimeSettings(BaseModel):
    """WakaTime data source configuration"""

    wakatime_enabled: bool = Field(
        default=True,
        description="Enable WakaTime coding activity tracking"
    )


# Google Calendar Settings (2 settings)
class CalendarSettings(BaseModel):
    """Google Calendar data source configuration"""

    calendar_enabled: bool = Field(
        default=True,
        description="Enable Google Calendar meeting tracking"
    )

    calendar_monitored_emails: str = Field(
        default="",
        description="Comma-separated list of calendar email addresses to monitor"
    )

    @field_validator("calendar_monitored_emails")
    @classmethod
    def validate_email_list(cls, v: str) -> str:
        """Validate comma-separated email addresses"""
        if not v:
            return v

        emails = [e.strip() for e in v.split(",")]
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        for email in emails:
            if email and not re.match(email_pattern, email):
                raise ValueError(f"Invalid email address: {email}")

        return v

    def get_monitored_emails_list(self) -> List[str]:
        """Parse monitored emails into a list"""
        if not self.calendar_monitored_emails:
            return []
        return [e.strip() for e in self.calendar_monitored_emails.split(",") if e.strip()]


# Gmail Settings (3 settings)
class GmailSettings(BaseModel):
    """Gmail data source configuration"""

    gmail_enabled: bool = Field(
        default=True,
        description="Enable Gmail sent email tracking"
    )

    gmail_monitored_recipients: str = Field(
        default="",
        description="Comma-separated list of recipient emails to track sent emails to"
    )

    gmail_default_duration_minutes: int = Field(
        default=30,
        ge=5,
        le=240,
        description="Default duration in minutes for each sent email"
    )

    @field_validator("gmail_monitored_recipients")
    @classmethod
    def validate_email_list(cls, v: str) -> str:
        """Validate comma-separated email addresses"""
        if not v:
            return v

        emails = [e.strip() for e in v.split(",")]
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        for email in emails:
            if email and not re.match(email_pattern, email):
                raise ValueError(f"Invalid email address: {email}")

        return v

    def get_monitored_recipients_list(self) -> List[str]:
        """Parse monitored recipients into a list"""
        if not self.gmail_monitored_recipients:
            return []
        return [e.strip() for e in self.gmail_monitored_recipients.split(",") if e.strip()]


# GitHub Settings (5 settings)
class GitHubSettings(BaseModel):
    """GitHub data source configuration"""

    github_enabled: bool = Field(
        default=True,
        description="Enable GitHub activity tracking"
    )

    github_repositories: str = Field(
        default="",
        description="Comma-separated list of repositories to track (format: owner/repo)"
    )

    github_track_commits: bool = Field(
        default=True,
        description="Track commit activity"
    )

    github_track_issues: bool = Field(
        default=True,
        description="Track assigned issue activity"
    )

    github_track_prs: bool = Field(
        default=False,
        description="Track pull request review activity"
    )

    @field_validator("github_repositories")
    @classmethod
    def validate_repo_list(cls, v: str) -> str:
        """Validate comma-separated repository names"""
        if not v:
            return v

        repos = [r.strip() for r in v.split(",")]
        repo_pattern = r"^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$"

        for repo in repos:
            if repo and not re.match(repo_pattern, repo):
                raise ValueError(f"Invalid repository format: {repo} (expected: owner/repo)")

        return v

    def get_repositories_list(self) -> List[str]:
        """Parse repositories into a list"""
        if not self.github_repositories:
            return []
        return [r.strip() for r in self.github_repositories.split(",") if r.strip()]


# Cloud Events Settings (1 setting)
class CloudEventsSettings(BaseModel):
    """Cloud Events data source configuration"""

    cloud_events_enabled: bool = Field(
        default=True,
        description="Enable custom cloud events tracking"
    )


# Processing Settings (7 settings)
class ProcessingSettings(BaseModel):
    """Time block processing and auto-fill configuration"""

    rounding_mode: RoundingMode = Field(
        default=RoundingMode.UP,
        description="How to round time durations to 0.5h blocks"
    )

    group_same_activities: bool = Field(
        default=False,
        description="Group identical activities in the same day into one entry"
    )

    fill_up_topic_mode: FillUpTopicMode = Field(
        default=FillUpTopicMode.MANUAL,
        description="How to determine topic for auto-filled hours"
    )

    fill_up_default_topic: str = Field(
        default="General",
        max_length=100,
        description="Default topic to use when auto-filling hours"
    )

    fill_up_distribution: FillUpDistribution = Field(
        default=FillUpDistribution.END_OF_WEEK,
        description="How to distribute auto-filled hours across the week"
    )

    overlap_handling: OverlapHandling = Field(
        default=OverlapHandling.PRIORITY,
        description="How to handle overlapping time blocks from different sources"
    )

    max_carry_over_hours: int = Field(
        default=2000,
        ge=0,
        le=10000,
        description="Maximum hours that can accumulate as carry-over"
    )


# Export Settings (2 settings)
class ExportSettings(BaseModel):
    """Timesheet export configuration"""

    export_show_weekly_breakdown: bool = Field(
        default=False,
        description="Show weekly hour totals in monthly export"
    )

    export_title_name: str = Field(
        default="Koni",
        max_length=50,
        description="Name to display in export title (e.g., 'Zeiterfassung - {name}')"
    )


# Complete Settings Model
class Settings(BaseModel):
    """
    Complete application settings combining all categories.

    This model represents all 31 configuration settings across 8 categories:
    - Core: 10 settings (work week, scheduling, auto-fill)
    - WakaTime: 1 setting (enable/disable)
    - Calendar: 2 settings (enable, monitored emails)
    - Gmail: 3 settings (enable, monitored recipients, default duration)
    - GitHub: 5 settings (enable, repos, track commits/issues/PRs)
    - Cloud Events: 1 setting (enable/disable)
    - Processing: 7 settings (rounding, grouping, auto-fill logic, overlaps)
    - Export: 2 settings (weekly breakdown, title name)

    Total: 10 + 1 + 2 + 3 + 5 + 1 + 7 + 2 = 31 settings
    """

    core: CoreSettings = Field(default_factory=CoreSettings)
    wakatime: WakaTimeSettings = Field(default_factory=WakaTimeSettings)
    calendar: CalendarSettings = Field(default_factory=CalendarSettings)
    gmail: GmailSettings = Field(default_factory=GmailSettings)
    github: GitHubSettings = Field(default_factory=GitHubSettings)
    cloud_events: CloudEventsSettings = Field(default_factory=CloudEventsSettings)
    processing: ProcessingSettings = Field(default_factory=ProcessingSettings)
    export: ExportSettings = Field(default_factory=ExportSettings)

    def to_flat_dict(self) -> Dict[str, Any]:
        """
        Convert nested settings to flat key-value dict for PocketBase storage.

        Returns:
            Dict with keys like "work_week_start_day", "wakatime_enabled", etc.
        """
        flat = {}

        # Core settings (no prefix)
        for key, value in self.core.model_dump().items():
            flat[key] = value

        # Other categories (with prefix)
        for category in ["wakatime", "calendar", "gmail", "github", "cloud_events", "processing", "export"]:
            category_settings = getattr(self, category)
            for key, value in category_settings.model_dump().items():
                flat[key] = value

        return flat

    @classmethod
    def from_flat_dict(cls, flat_dict: Dict[str, Any]) -> "Settings":
        """
        Create Settings from flat key-value dict (from PocketBase).

        Args:
            flat_dict: Dictionary with keys like "work_week_start_day", etc.

        Returns:
            Settings object with nested structure
        """
        # Group settings by category
        core_keys = [
            "work_week_start_day", "work_week_start_time",
            "work_week_end_day", "work_week_end_time",
            "target_hours_per_week", "fetch_interval_hours",
            "time_block_size_minutes", "auto_fill_enabled",
            "auto_fill_day", "default_location"
        ]

        grouped = {
            "core": {k: flat_dict[k] for k in core_keys if k in flat_dict},
            "wakatime": {},
            "calendar": {},
            "gmail": {},
            "github": {},
            "cloud_events": {},
            "processing": {},
            "export": {}
        }

        # Categorize remaining keys by prefix
        for key, value in flat_dict.items():
            if key in core_keys:
                continue

            if key.startswith("wakatime_"):
                grouped["wakatime"][key] = value
            elif key.startswith("calendar_"):
                grouped["calendar"][key] = value
            elif key.startswith("gmail_"):
                grouped["gmail"][key] = value
            elif key.startswith("github_"):
                grouped["github"][key] = value
            elif key.startswith("cloud_events_"):
                grouped["cloud_events"][key] = value
            elif key.startswith("export_"):
                grouped["export"][key] = value
            else:
                # Processing settings don't have a common prefix
                grouped["processing"][key] = value

        return cls(**grouped)
