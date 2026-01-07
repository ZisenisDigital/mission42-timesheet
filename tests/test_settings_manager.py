"""
Integration Tests for SettingsManager

Tests for SettingsManager integration with PocketBase.
These tests require a running PocketBase instance with seeded data.

Run with: pytest tests/test_settings_manager.py -v
"""

import os
import pytest
from unittest.mock import Mock, MagicMock
from app.config import SettingsManager, Config
from app.models.settings import Settings


class MockRecord:
    """Mock PocketBase record"""

    def __init__(self, key: str, value: str, record_type: str):
        self.key = key
        self.value = value
        self.type = record_type
        self.id = f"record_{key}"


class TestSettingsManager:
    """Test SettingsManager functionality"""

    @pytest.fixture
    def mock_pb_client(self):
        """Create mock PocketBase client"""
        pb = Mock()
        collection = Mock()
        pb.collection.return_value = collection
        return pb, collection

    @pytest.fixture
    def settings_manager(self, mock_pb_client):
        """Create SettingsManager with mock client"""
        pb, _ = mock_pb_client
        return SettingsManager(pb)

    def test_parse_value_string(self, settings_manager):
        """Test parsing string values"""
        assert settings_manager._parse_value("hello", "string") == "hello"
        assert settings_manager._parse_value("123", "string") == "123"

    def test_parse_value_number(self, settings_manager):
        """Test parsing number values"""
        assert settings_manager._parse_value("42", "number") == 42
        assert settings_manager._parse_value("3.14", "number") == 3.14

    def test_parse_value_boolean(self, settings_manager):
        """Test parsing boolean values"""
        assert settings_manager._parse_value("true", "boolean") is True
        assert settings_manager._parse_value("True", "boolean") is True
        assert settings_manager._parse_value("1", "boolean") is True
        assert settings_manager._parse_value("yes", "boolean") is True
        assert settings_manager._parse_value("on", "boolean") is True

        assert settings_manager._parse_value("false", "boolean") is False
        assert settings_manager._parse_value("False", "boolean") is False
        assert settings_manager._parse_value("0", "boolean") is False
        assert settings_manager._parse_value("no", "boolean") is False

    def test_value_to_string(self, settings_manager):
        """Test converting values to string"""
        assert settings_manager._value_to_string("hello") == "hello"
        assert settings_manager._value_to_string(42) == "42"
        assert settings_manager._value_to_string(3.14) == "3.14"
        assert settings_manager._value_to_string(True) == "true"
        assert settings_manager._value_to_string(False) == "false"

    def test_get_all_success(self, mock_pb_client, settings_manager):
        """Test getting all settings successfully"""
        pb, collection = mock_pb_client

        # Mock 31 settings records (10+1+2+3+5+1+7+2)
        mock_records = [
            # Core (10)
            MockRecord("work_week_start_day", "monday", "string"),
            MockRecord("work_week_start_time", "18:00", "string"),
            MockRecord("work_week_end_day", "saturday", "string"),
            MockRecord("work_week_end_time", "18:00", "string"),
            MockRecord("target_hours_per_week", "40", "number"),
            MockRecord("fetch_interval_hours", "5", "number"),
            MockRecord("time_block_size_minutes", "30", "number"),
            MockRecord("auto_fill_enabled", "true", "boolean"),
            MockRecord("auto_fill_day", "monday", "string"),
            MockRecord("default_location", "Remote", "string"),
            # WakaTime (1)
            MockRecord("wakatime_enabled", "true", "boolean"),
            # Calendar (2)
            MockRecord("calendar_enabled", "true", "boolean"),
            MockRecord("calendar_monitored_emails", "", "string"),
            # Gmail (3)
            MockRecord("gmail_enabled", "true", "boolean"),
            MockRecord("gmail_monitored_recipients", "", "string"),
            MockRecord("gmail_default_duration_minutes", "30", "number"),
            # GitHub (5)
            MockRecord("github_enabled", "true", "boolean"),
            MockRecord("github_repositories", "", "string"),
            MockRecord("github_track_commits", "true", "boolean"),
            MockRecord("github_track_issues", "true", "boolean"),
            MockRecord("github_track_prs", "false", "boolean"),
            # Cloud Events (1)
            MockRecord("cloud_events_enabled", "true", "boolean"),
            # Processing (7)
            MockRecord("rounding_mode", "up", "string"),
            MockRecord("group_same_activities", "false", "boolean"),
            MockRecord("fill_up_topic_mode", "manual", "string"),
            MockRecord("fill_up_default_topic", "General", "string"),
            MockRecord("fill_up_distribution", "end_of_week", "string"),
            MockRecord("overlap_handling", "priority", "string"),
            MockRecord("max_carry_over_hours", "2000", "number"),
            # Export (2)
            MockRecord("export_show_weekly_breakdown", "false", "boolean"),
            MockRecord("export_title_name", "Koni", "string"),
        ]

        collection.get_full_list.return_value = mock_records

        # Get all settings
        settings = settings_manager.get_all()

        # Verify it's a Settings object
        assert isinstance(settings, Settings)

        # Verify some values
        assert settings.core.target_hours_per_week == 40
        assert settings.core.work_week_start_day.value == "monday"
        assert settings.wakatime.wakatime_enabled is True
        assert settings.processing.rounding_mode.value == "up"
        assert settings.export.export_title_name == "Koni"

        # Verify caching
        settings2 = settings_manager.get_all()
        assert settings2 is settings  # Same object (cached)

    def test_get_all_wrong_count(self, mock_pb_client, settings_manager):
        """Test error when wrong number of settings"""
        pb, collection = mock_pb_client

        # Only return 10 settings instead of 31
        mock_records = [
            MockRecord("work_week_start_day", "monday", "string"),
            MockRecord("target_hours_per_week", "40", "number"),
        ]

        collection.get_full_list.return_value = mock_records

        # Should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            settings_manager.get_all()

        assert "Expected 31 settings" in str(exc_info.value)

    def test_get_single_setting(self, mock_pb_client, settings_manager):
        """Test getting a single setting"""
        pb, collection = mock_pb_client

        mock_record = MockRecord("target_hours_per_week", "40", "number")
        collection.get_first_list_item.return_value = mock_record

        value = settings_manager.get("target_hours_per_week")
        assert value == 40

        # Verify correct filter was used
        collection.get_first_list_item.assert_called_once_with('key="target_hours_per_week"')

    def test_get_nonexistent_setting(self, mock_pb_client, settings_manager):
        """Test getting non-existent setting raises KeyError"""
        pb, collection = mock_pb_client

        from pocketbase.client import ClientResponseError

        # Mock 404 error
        error = ClientResponseError(
            url="http://test",
            status=404,
            data={},
            response=Mock(status_code=404),
            originalError=None,
        )
        collection.get_first_list_item.side_effect = error

        with pytest.raises(KeyError) as exc_info:
            settings_manager.get("nonexistent_key")

        assert "nonexistent_key" in str(exc_info.value)

    def test_update_setting(self, mock_pb_client, settings_manager):
        """Test updating a setting"""
        pb, collection = mock_pb_client

        mock_record = MockRecord("target_hours_per_week", "40", "number")
        collection.get_first_list_item.return_value = mock_record

        # Update value
        settings_manager.update("target_hours_per_week", 35)

        # Verify update was called
        collection.update.assert_called_once_with("record_target_hours_per_week", {"value": "35"})

        # Verify cache was cleared
        assert settings_manager._cache is None

    def test_update_many_settings(self, mock_pb_client, settings_manager):
        """Test updating multiple settings"""
        pb, collection = mock_pb_client

        def mock_get_first(filter_str):
            key = filter_str.split('"')[1]
            return MockRecord(key, "old_value", "string")

        collection.get_first_list_item.side_effect = mock_get_first

        # Update multiple
        settings_manager.update_many(
            {"work_week_start_day": "tuesday", "default_location": "Office"}
        )

        # Verify two updates
        assert collection.update.call_count == 2

    def test_force_reload(self, mock_pb_client, settings_manager):
        """Test force reload bypasses cache"""
        pb, collection = mock_pb_client

        # Mock 31 settings
        mock_records = [MockRecord(f"key_{i}", f"value_{i}", "string") for i in range(31)]
        collection.get_full_list.return_value = mock_records

        # First call
        try:
            settings1 = settings_manager.get_all()
        except Exception:
            pass  # May fail validation, that's OK for this test

        # Should have been called once
        assert collection.get_full_list.call_count == 1

        # Call again (should use cache)
        try:
            settings2 = settings_manager.get_all()
        except Exception:
            pass

        # Still only one call (cache hit)
        assert collection.get_full_list.call_count == 1

        # Force reload
        try:
            settings3 = settings_manager.reload()
        except Exception:
            pass

        # Now two calls (cache bypassed)
        assert collection.get_full_list.call_count == 2

    def test_clear_cache(self, mock_pb_client, settings_manager):
        """Test clearing cache"""
        pb, collection = mock_pb_client

        # Set cache
        settings_manager._cache = Mock()
        assert settings_manager._cache is not None

        # Clear
        settings_manager.clear_cache()
        assert settings_manager._cache is None


class TestConfig:
    """Test Config class"""

    def test_config_initialization(self):
        """Test Config loads from environment"""
        config = Config()
        assert config.pocketbase_url == os.getenv("POCKETBASE_URL", "http://127.0.0.1:8090")
        assert config.fastapi_port == int(os.getenv("FASTAPI_PORT", "8000"))

    def test_setup_pocketbase(self):
        """Test setting up PocketBase client"""
        config = Config()
        mock_pb = Mock()

        config.setup_pocketbase(mock_pb)

        assert config._pb_client is mock_pb
        assert config._settings_manager is not None
        assert isinstance(config._settings_manager, SettingsManager)

    def test_settings_property_before_setup(self):
        """Test accessing settings before setup raises error"""
        config = Config()

        with pytest.raises(RuntimeError) as exc_info:
            _ = config.settings

        assert "not initialized" in str(exc_info.value)

    def test_settings_property_after_setup(self):
        """Test accessing settings after setup works"""
        config = Config()
        mock_pb = Mock()
        config.setup_pocketbase(mock_pb)

        settings_manager = config.settings
        assert isinstance(settings_manager, SettingsManager)

    def test_config_validate_missing_required(self, monkeypatch):
        """Test validation catches missing required fields"""
        # Clear required env vars
        monkeypatch.delenv("PB_ADMIN_EMAIL", raising=False)
        monkeypatch.delenv("PB_ADMIN_PASSWORD", raising=False)
        monkeypatch.delenv("ENCRYPTION_KEY", raising=False)

        config = Config()
        errors = config.validate()

        # Should have errors for missing required fields
        assert len(errors) > 0
        assert any("PB_ADMIN_EMAIL" in error for error in errors)
        assert any("ENCRYPTION_KEY" in error for error in errors)

    def test_config_validate_missing_optional(self, monkeypatch):
        """Test validation warns about missing optional fields"""
        # Set required fields
        monkeypatch.setenv("PB_ADMIN_EMAIL", "admin@test.com")
        monkeypatch.setenv("PB_ADMIN_PASSWORD", "password123")
        monkeypatch.setenv("ENCRYPTION_KEY", "test-key-123")

        # Clear optional fields
        monkeypatch.delenv("WAKATIME_API_KEY", raising=False)
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)

        config = Config()
        errors = config.validate()

        # Should have warnings (not errors) for optional fields
        assert any("Warning" in error and "WAKATIME_API_KEY" in error for error in errors)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
