"""
Unit Tests for Settings Models

Tests for Pydantic settings models with validation.
"""

import pytest
from pydantic import ValidationError
from app.models.settings import (
    CoreSettings,
    WakaTimeSettings,
    CalendarSettings,
    GmailSettings,
    GitHubSettings,
    CloudEventsSettings,
    ProcessingSettings,
    ExportSettings,
    Settings,
    DayOfWeek,
    RoundingMode,
    FillUpTopicMode,
    FillUpDistribution,
    OverlapHandling,
)


class TestCoreSettings:
    """Test CoreSettings validation"""

    def test_valid_core_settings_default(self):
        """Test default values are valid"""
        settings = CoreSettings()
        assert settings.work_week_start_day == DayOfWeek.MONDAY
        assert settings.work_week_start_time == "18:00"
        assert settings.target_hours_per_week == 40
        assert settings.time_block_size_minutes == 30

    def test_valid_core_settings_custom(self):
        """Test custom valid values"""
        settings = CoreSettings(
            work_week_start_day=DayOfWeek.TUESDAY,
            work_week_start_time="09:00",
            work_week_end_day=DayOfWeek.FRIDAY,
            work_week_end_time="17:00",
            target_hours_per_week=35,
        )
        assert settings.work_week_start_day == DayOfWeek.TUESDAY
        assert settings.work_week_start_time == "09:00"
        assert settings.target_hours_per_week == 35

    def test_invalid_time_format(self):
        """Test invalid time format raises error"""
        with pytest.raises(ValidationError) as exc_info:
            CoreSettings(work_week_start_time="25:00")
        assert "String should match pattern" in str(exc_info.value)

        with pytest.raises(ValidationError):
            CoreSettings(work_week_start_time="6:00 PM")

        with pytest.raises(ValidationError):
            CoreSettings(work_week_start_time="18:60")

    def test_invalid_target_hours_range(self):
        """Test target hours must be in valid range"""
        with pytest.raises(ValidationError):
            CoreSettings(target_hours_per_week=0)

        with pytest.raises(ValidationError):
            CoreSettings(target_hours_per_week=200)

    def test_invalid_time_block_size(self):
        """Test time block size must be 30"""
        with pytest.raises(ValidationError) as exc_info:
            CoreSettings(time_block_size_minutes=15)
        assert "time_block_size_minutes must be 30" in str(exc_info.value)

    def test_week_validation(self):
        """Test work week end must come after start"""
        # Valid: Monday -> Saturday
        settings = CoreSettings(
            work_week_start_day=DayOfWeek.MONDAY, work_week_end_day=DayOfWeek.SATURDAY
        )
        assert settings.work_week_start_day == DayOfWeek.MONDAY

        # Invalid: Saturday -> Monday
        with pytest.raises(ValidationError) as exc_info:
            CoreSettings(
                work_week_start_day=DayOfWeek.SATURDAY, work_week_end_day=DayOfWeek.MONDAY
            )
        assert "must come after" in str(exc_info.value)

        # Invalid: Same day
        with pytest.raises(ValidationError):
            CoreSettings(
                work_week_start_day=DayOfWeek.MONDAY, work_week_end_day=DayOfWeek.MONDAY
            )


class TestCalendarSettings:
    """Test CalendarSettings validation"""

    def test_valid_calendar_settings(self):
        """Test valid calendar settings"""
        settings = CalendarSettings(calendar_enabled=True, calendar_monitored_emails="")
        assert settings.calendar_enabled is True
        assert settings.calendar_monitored_emails == ""

    def test_valid_email_list(self):
        """Test valid email lists"""
        settings = CalendarSettings(
            calendar_monitored_emails="test@example.com,user@domain.org"
        )
        assert settings.calendar_monitored_emails == "test@example.com,user@domain.org"

        emails = settings.get_monitored_emails_list()
        assert len(emails) == 2
        assert "test@example.com" in emails
        assert "user@domain.org" in emails

    def test_invalid_email_format(self):
        """Test invalid email format raises error"""
        with pytest.raises(ValidationError) as exc_info:
            CalendarSettings(calendar_monitored_emails="invalid-email")
        assert "Invalid email address" in str(exc_info.value)

        with pytest.raises(ValidationError):
            CalendarSettings(calendar_monitored_emails="good@example.com,bad-email")

    def test_empty_email_list(self):
        """Test empty email list is valid"""
        settings = CalendarSettings(calendar_monitored_emails="")
        emails = settings.get_monitored_emails_list()
        assert emails == []


class TestGmailSettings:
    """Test GmailSettings validation"""

    def test_valid_gmail_settings(self):
        """Test valid Gmail settings"""
        settings = GmailSettings(
            gmail_enabled=True,
            gmail_monitored_recipients="client@example.com",
            gmail_default_duration_minutes=30,
        )
        assert settings.gmail_enabled is True
        assert settings.gmail_default_duration_minutes == 30

    def test_invalid_duration_range(self):
        """Test duration must be in valid range"""
        with pytest.raises(ValidationError):
            GmailSettings(gmail_default_duration_minutes=3)

        with pytest.raises(ValidationError):
            GmailSettings(gmail_default_duration_minutes=300)

    def test_get_recipients_list(self):
        """Test parsing recipients list"""
        settings = GmailSettings(
            gmail_monitored_recipients="client1@example.com,client2@example.org"
        )
        recipients = settings.get_monitored_recipients_list()
        assert len(recipients) == 2
        assert "client1@example.com" in recipients


class TestGitHubSettings:
    """Test GitHubSettings validation"""

    def test_valid_github_settings(self):
        """Test valid GitHub settings"""
        settings = GitHubSettings(
            github_enabled=True,
            github_repositories="user/repo1,org/repo2",
            github_track_commits=True,
            github_track_issues=True,
            github_track_prs=False,
        )
        assert settings.github_enabled is True
        assert settings.github_track_commits is True

    def test_valid_repository_format(self):
        """Test valid repository formats"""
        settings = GitHubSettings(github_repositories="user/repo")
        repos = settings.get_repositories_list()
        assert repos == ["user/repo"]

        settings = GitHubSettings(
            github_repositories="user/repo1,org-name/repo-2,user123/repo_test"
        )
        repos = settings.get_repositories_list()
        assert len(repos) == 3

    def test_invalid_repository_format(self):
        """Test invalid repository format raises error"""
        with pytest.raises(ValidationError) as exc_info:
            GitHubSettings(github_repositories="invalid-repo")
        assert "Invalid repository format" in str(exc_info.value)

        with pytest.raises(ValidationError):
            GitHubSettings(github_repositories="user/repo,invalid")


class TestProcessingSettings:
    """Test ProcessingSettings validation"""

    def test_valid_processing_settings(self):
        """Test valid processing settings"""
        settings = ProcessingSettings(
            rounding_mode=RoundingMode.UP,
            group_same_activities=False,
            fill_up_topic_mode=FillUpTopicMode.GENERIC,
            fill_up_default_topic="Development",
            fill_up_distribution=FillUpDistribution.END_OF_WEEK,
            overlap_handling=OverlapHandling.PRIORITY,
            max_carry_over_hours=2000,
        )
        assert settings.rounding_mode == RoundingMode.UP
        assert settings.max_carry_over_hours == 2000

    def test_invalid_carry_over_range(self):
        """Test carry over hours must be in valid range"""
        with pytest.raises(ValidationError):
            ProcessingSettings(max_carry_over_hours=-1)

        with pytest.raises(ValidationError):
            ProcessingSettings(max_carry_over_hours=20000)


class TestExportSettings:
    """Test ExportSettings validation"""

    def test_valid_export_settings(self):
        """Test valid export settings"""
        settings = ExportSettings(
            export_show_weekly_breakdown=True, export_title_name="John Doe"
        )
        assert settings.export_show_weekly_breakdown is True
        assert settings.export_title_name == "John Doe"

    def test_title_max_length(self):
        """Test title name has max length"""
        # Valid: 50 chars
        settings = ExportSettings(export_title_name="A" * 50)
        assert len(settings.export_title_name) == 50

        # Invalid: 51 chars
        with pytest.raises(ValidationError):
            ExportSettings(export_title_name="A" * 51)


class TestCompleteSettings:
    """Test complete Settings model"""

    def test_default_settings(self):
        """Test Settings with all defaults"""
        settings = Settings()
        assert settings.core.target_hours_per_week == 40
        assert settings.wakatime.wakatime_enabled is True
        assert settings.calendar.calendar_enabled is True
        assert settings.gmail.gmail_enabled is True
        assert settings.github.github_enabled is True
        assert settings.cloud_events.cloud_events_enabled is True
        assert settings.processing.rounding_mode == RoundingMode.UP
        assert settings.export.export_title_name == "Koni"

    def test_to_flat_dict(self):
        """Test converting Settings to flat dictionary"""
        settings = Settings()
        flat = settings.to_flat_dict()

        # Should have all 31 settings (10+1+2+3+5+1+7+2)
        assert len(flat) == 31

        # Check some key values
        assert flat["work_week_start_day"] == "monday"
        assert flat["target_hours_per_week"] == 40
        assert flat["wakatime_enabled"] is True
        assert flat["gmail_default_duration_minutes"] == 30
        assert flat["rounding_mode"] == "up"

    def test_from_flat_dict(self):
        """Test creating Settings from flat dictionary"""
        flat_dict = {
            # Core
            "work_week_start_day": "tuesday",
            "work_week_start_time": "09:00",
            "work_week_end_day": "friday",
            "work_week_end_time": "17:00",
            "target_hours_per_week": 35,
            "fetch_interval_hours": 3,
            "time_block_size_minutes": 30,
            "auto_fill_enabled": False,
            "auto_fill_day": "friday",
            "default_location": "Office",
            # WakaTime
            "wakatime_enabled": False,
            # Calendar
            "calendar_enabled": True,
            "calendar_monitored_emails": "work@example.com",
            # Gmail
            "gmail_enabled": True,
            "gmail_monitored_recipients": "",
            "gmail_default_duration_minutes": 45,
            # GitHub
            "github_enabled": True,
            "github_repositories": "user/repo",
            "github_track_commits": True,
            "github_track_issues": False,
            "github_track_prs": False,
            # Cloud Events
            "cloud_events_enabled": True,
            # Processing
            "rounding_mode": "nearest",
            "group_same_activities": True,
            "fill_up_topic_mode": "auto",
            "fill_up_default_topic": "Admin",
            "fill_up_distribution": "distributed",
            "overlap_handling": "show_both",
            "max_carry_over_hours": 1000,
            # Export
            "export_show_weekly_breakdown": True,
            "export_title_name": "Test User",
        }

        settings = Settings.from_flat_dict(flat_dict)

        # Verify core settings
        assert settings.core.work_week_start_day == DayOfWeek.TUESDAY
        assert settings.core.target_hours_per_week == 35
        assert settings.core.auto_fill_enabled is False

        # Verify data sources
        assert settings.wakatime.wakatime_enabled is False
        assert settings.gmail.gmail_default_duration_minutes == 45

        # Verify processing
        assert settings.processing.rounding_mode == RoundingMode.NEAREST
        assert settings.processing.max_carry_over_hours == 1000

        # Verify export
        assert settings.export.export_title_name == "Test User"

    def test_round_trip_conversion(self):
        """Test converting Settings to flat dict and back"""
        original = Settings()
        flat = original.to_flat_dict()
        restored = Settings.from_flat_dict(flat)

        # Should be identical
        assert original.core == restored.core
        assert original.wakatime == restored.wakatime
        assert original.calendar == restored.calendar
        assert original.gmail == restored.gmail
        assert original.github == restored.github
        assert original.cloud_events == restored.cloud_events
        assert original.processing == restored.processing
        assert original.export == restored.export


class TestEnums:
    """Test enum values"""

    def test_day_of_week_enum(self):
        """Test DayOfWeek enum has all days"""
        assert DayOfWeek.MONDAY.value == "monday"
        assert DayOfWeek.SUNDAY.value == "sunday"
        assert len(DayOfWeek) == 7

    def test_rounding_mode_enum(self):
        """Test RoundingMode enum"""
        assert RoundingMode.UP.value == "up"
        assert RoundingMode.NEAREST.value == "nearest"

    def test_fill_up_topic_mode_enum(self):
        """Test FillUpTopicMode enum"""
        assert FillUpTopicMode.MANUAL.value == "manual"
        assert FillUpTopicMode.AUTO.value == "auto"
        assert FillUpTopicMode.GENERIC.value == "generic"

    def test_overlap_handling_enum(self):
        """Test OverlapHandling enum"""
        assert OverlapHandling.PRIORITY.value == "priority"
        assert OverlapHandling.SHOW_BOTH.value == "show_both"
        assert OverlapHandling.COMBINE.value == "combine"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
