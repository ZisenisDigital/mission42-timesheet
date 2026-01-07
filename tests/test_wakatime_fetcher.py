"""
Unit Tests for WakaTime Fetcher

Tests for WakaTime API integration and data fetching.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from requests.exceptions import HTTPError, Timeout, RequestException

from app.services.fetchers.wakatime_fetcher import WakaTimeAPI, WakaTimeFetcher
from app.services.fetchers.base import FetchResult
from app.pocketbase_client import PocketBaseClient


class TestWakaTimeAPI:
    """Test WakaTime API wrapper"""

    @pytest.fixture
    def api(self):
        """Create WakaTime API instance"""
        return WakaTimeAPI(api_key="test_api_key_12345")

    def test_initialization(self, api):
        """Test API initialization"""
        assert api.api_key == "test_api_key_12345"
        assert "Authorization" in api.session.headers
        assert api.session.headers["Authorization"] == "Bearer test_api_key_12345"

    @patch("requests.Session.get")
    def test_get_summaries_success(self, mock_get, api):
        """Test successful summaries fetch"""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {
                    "range": {"date": "2026-01-07"},
                    "grand_total": {"total_seconds": 3600},
                    "projects": [{"name": "test-project", "total_seconds": 3600}],
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        start = datetime(2026, 1, 7)
        end = datetime(2026, 1, 7)

        result = api.get_summaries(start, end)

        assert "data" in result
        assert len(result["data"]) == 1
        mock_get.assert_called_once()

    @patch("requests.Session.get")
    def test_get_summaries_http_error(self, mock_get, api):
        """Test HTTP error handling"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        start = datetime(2026, 1, 7)
        end = datetime(2026, 1, 7)

        with pytest.raises(HTTPError):
            api.get_summaries(start, end)

    @patch("requests.Session.get")
    def test_get_heartbeats(self, mock_get, api):
        """Test heartbeats fetch"""
        mock_response = Mock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        date = datetime(2026, 1, 7)
        result = api.get_heartbeats(date)

        assert "data" in result
        mock_get.assert_called_once()

    @patch("requests.Session.get")
    def test_test_connection_success(self, mock_get, api):
        """Test successful connection test"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        assert api.test_connection() is True

    @patch("requests.Session.get")
    def test_test_connection_failure(self, mock_get, api):
        """Test failed connection test"""
        mock_get.side_effect = HTTPError("401 Unauthorized")

        assert api.test_connection() is False


class TestWakaTimeFetcher:
    """Test WakaTime Fetcher"""

    @pytest.fixture
    def mock_pb_client(self):
        """Create mock PocketBase client"""
        return Mock(spec=PocketBaseClient)

    @pytest.fixture
    def fetcher(self, mock_pb_client):
        """Create WakaTime fetcher with mock API"""
        fetcher = WakaTimeFetcher(mock_pb_client, api_key="test_key")
        return fetcher

    def test_initialization(self, fetcher):
        """Test fetcher initialization"""
        assert fetcher.source_name == "wakatime"
        assert fetcher.enabled_setting_key == "wakatime_enabled"
        assert fetcher.priority == 100
        assert fetcher.api_key == "test_key"

    def test_initialization_without_api_key(self, mock_pb_client, monkeypatch):
        """Test initialization without API key"""
        monkeypatch.delenv("WAKATIME_API_KEY", raising=False)

        fetcher = WakaTimeFetcher(mock_pb_client)
        assert fetcher.api_key is None
        assert fetcher.api is None

    def test_validate_configuration_no_api_key(self, mock_pb_client, monkeypatch):
        """Test validation fails without API key"""
        monkeypatch.delenv("WAKATIME_API_KEY", raising=False)

        fetcher = WakaTimeFetcher(mock_pb_client, api_key=None)

        is_valid, error = fetcher.validate_configuration()

        assert is_valid is False
        assert "WAKATIME_API_KEY" in error

    @patch.object(WakaTimeAPI, "test_connection")
    def test_validate_configuration_success(self, mock_test, fetcher):
        """Test successful validation"""
        mock_test.return_value = True

        is_valid, error = fetcher.validate_configuration()

        assert is_valid is True
        assert error is None

    @patch.object(WakaTimeAPI, "test_connection")
    def test_validate_configuration_connection_failure(self, mock_test, fetcher):
        """Test validation fails with connection error"""
        mock_test.return_value = False

        is_valid, error = fetcher.validate_configuration()

        assert is_valid is False
        assert "Failed to connect" in error

    def test_process_day_summary_with_projects(self, fetcher):
        """Test processing day summary with projects"""
        day_summary = {
            "range": {"date": "2026-01-07"},
            "grand_total": {"total_seconds": 7200},
            "projects": [
                {
                    "name": "mission42-timesheet",
                    "total_seconds": 5400,
                    "languages": [{"name": "Python"}, {"name": "JavaScript"}],
                    "editors": [{"name": "VS Code"}],
                },
                {
                    "name": "other-project",
                    "total_seconds": 1800,
                    "languages": [{"name": "TypeScript"}],
                    "editors": [{"name": "WebStorm"}],
                },
            ],
        }

        events = fetcher._process_day_summary(day_summary)

        assert len(events) == 2

        # First project
        assert events[0]["description"] == "Coding: mission42-timesheet - Python"
        assert events[0]["duration_minutes"] == 90.0  # 5400 / 60
        assert events[0]["source_id"] == "wakatime_2026-01-07_mission42-timesheet"
        assert events[0]["metadata"]["project"] == "mission42-timesheet"
        assert "Python" in events[0]["metadata"]["languages"]

        # Second project
        assert events[1]["description"] == "Coding: other-project - TypeScript"
        assert events[1]["duration_minutes"] == 30.0  # 1800 / 60

    def test_process_day_summary_no_projects(self, fetcher):
        """Test processing day summary without projects"""
        day_summary = {
            "range": {"date": "2026-01-07"},
            "grand_total": {"total_seconds": 3600},
            "projects": [],
        }

        events = fetcher._process_day_summary(day_summary)

        assert len(events) == 1
        assert events[0]["description"] == "Coding: General"
        assert events[0]["duration_minutes"] == 60.0
        assert events[0]["metadata"]["note"] == "No specific project data available"

    def test_process_day_summary_no_time(self, fetcher):
        """Test processing day summary with zero time"""
        day_summary = {
            "range": {"date": "2026-01-07"},
            "grand_total": {"total_seconds": 0},
            "projects": [],
        }

        events = fetcher._process_day_summary(day_summary)

        assert len(events) == 0

    def test_process_day_summary_invalid_date(self, fetcher):
        """Test processing summary with invalid date"""
        day_summary = {
            "range": {"date": "invalid-date"},
            "grand_total": {"total_seconds": 3600},
            "projects": [],
        }

        events = fetcher._process_day_summary(day_summary)

        assert len(events) == 0

    @patch.object(WakaTimeFetcher, "is_enabled")
    def test_fetch_disabled(self, mock_enabled, fetcher):
        """Test fetch when fetcher is disabled"""
        mock_enabled.return_value = False

        result = fetcher.fetch()

        assert result.success is False
        assert "disabled" in result.error

    @patch.object(WakaTimeFetcher, "is_enabled")
    @patch.object(WakaTimeFetcher, "validate_configuration")
    def test_fetch_invalid_configuration(self, mock_validate, mock_enabled, fetcher):
        """Test fetch with invalid configuration"""
        mock_enabled.return_value = True
        mock_validate.return_value = (False, "Invalid API key")

        result = fetcher.fetch()

        assert result.success is False
        assert result.error == "Invalid API key"

    @patch.object(WakaTimeFetcher, "is_enabled")
    @patch.object(WakaTimeFetcher, "validate_configuration")
    @patch.object(WakaTimeAPI, "get_summaries")
    @patch.object(WakaTimeFetcher, "event_exists")
    @patch.object(WakaTimeFetcher, "create_raw_event")
    def test_fetch_success(
        self,
        mock_create,
        mock_exists,
        mock_get_summaries,
        mock_validate,
        mock_enabled,
        fetcher,
    ):
        """Test successful fetch"""
        mock_enabled.return_value = True
        mock_validate.return_value = (True, None)

        # Mock API response
        mock_get_summaries.return_value = {
            "data": [
                {
                    "range": {"date": "2026-01-07"},
                    "grand_total": {"total_seconds": 3600},
                    "projects": [
                        {
                            "name": "test-project",
                            "total_seconds": 3600,
                            "languages": [{"name": "Python"}],
                            "editors": [],
                        }
                    ],
                }
            ]
        }

        # Mock event doesn't exist
        mock_exists.return_value = False

        # Mock create event
        mock_create.return_value = Mock()

        start = datetime(2026, 1, 7)
        end = datetime(2026, 1, 7)

        result = fetcher.fetch(start_date=start, end_date=end)

        assert result.success is True
        assert result.events_fetched == 1
        assert result.events_created == 1
        assert mock_create.call_count == 1

    @patch.object(WakaTimeFetcher, "is_enabled")
    @patch.object(WakaTimeFetcher, "validate_configuration")
    @patch.object(WakaTimeAPI, "get_summaries")
    def test_fetch_http_error(
        self, mock_get_summaries, mock_validate, mock_enabled, fetcher
    ):
        """Test fetch with HTTP error"""
        mock_enabled.return_value = True
        mock_validate.return_value = (True, None)

        # Mock HTTP error
        mock_response = Mock()
        mock_response.status_code = 401
        error = HTTPError("Unauthorized")
        error.response = mock_response
        mock_get_summaries.side_effect = error

        start = datetime(2026, 1, 7)
        end = datetime(2026, 1, 7)

        result = fetcher.fetch(start_date=start, end_date=end)

        assert result.success is False
        assert "HTTP error" in result.error
        assert "401" in result.error

    @patch.object(WakaTimeFetcher, "is_enabled")
    @patch.object(WakaTimeFetcher, "validate_configuration")
    @patch.object(WakaTimeAPI, "get_summaries")
    def test_fetch_timeout(self, mock_get_summaries, mock_validate, mock_enabled, fetcher):
        """Test fetch with timeout"""
        mock_enabled.return_value = True
        mock_validate.return_value = (True, None)
        mock_get_summaries.side_effect = Timeout()

        start = datetime(2026, 1, 7)
        end = datetime(2026, 1, 7)

        result = fetcher.fetch(start_date=start, end_date=end)

        assert result.success is False
        assert "timed out" in result.error

    @patch.object(WakaTimeFetcher, "is_enabled")
    @patch.object(WakaTimeFetcher, "validate_configuration")
    @patch.object(WakaTimeAPI, "get_summaries")
    @patch.object(WakaTimeFetcher, "event_exists")
    def test_fetch_skips_existing_events(
        self, mock_exists, mock_get_summaries, mock_validate, mock_enabled, fetcher
    ):
        """Test that fetch skips existing events"""
        mock_enabled.return_value = True
        mock_validate.return_value = (True, None)

        mock_get_summaries.return_value = {
            "data": [
                {
                    "range": {"date": "2026-01-07"},
                    "grand_total": {"total_seconds": 3600},
                    "projects": [
                        {
                            "name": "test-project",
                            "total_seconds": 3600,
                            "languages": [],
                            "editors": [],
                        }
                    ],
                }
            ]
        }

        # Event already exists
        mock_exists.return_value = True

        start = datetime(2026, 1, 7)
        end = datetime(2026, 1, 7)

        result = fetcher.fetch(start_date=start, end_date=end)

        assert result.success is True
        assert result.events_fetched == 1
        assert result.events_created == 0  # Should be 0 since event exists


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
