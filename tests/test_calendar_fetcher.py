"""
Unit Tests for Google Calendar Fetcher

Tests for Google Calendar API integration and event fetching.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from googleapiclient.errors import HttpError

from app.services.fetchers.calendar_fetcher import GoogleCalendarAPI, CalendarFetcher
from app.services.fetchers.base import FetchResult
from app.pocketbase_client import PocketBaseClient


class TestGoogleCalendarAPI:
    """Test Google Calendar API wrapper"""

    @pytest.fixture
    def mock_credentials(self):
        """Create mock credentials"""
        creds = Mock()
        creds.expired = False
        creds.refresh_token = "test_refresh_token"
        return creds

    @pytest.fixture
    def api(self, mock_credentials):
        """Create Calendar API instance with mocked service"""
        with patch("app.services.fetchers.calendar_fetcher.build") as mock_build:
            mock_service = Mock()
            mock_build.return_value = mock_service
            api = GoogleCalendarAPI(mock_credentials)
            api.service = mock_service
            return api

    def test_initialization(self, mock_credentials):
        """Test API initialization"""
        with patch("app.services.fetchers.calendar_fetcher.build") as mock_build:
            api = GoogleCalendarAPI(mock_credentials)
            mock_build.assert_called_once_with(
                "calendar", "v3", credentials=mock_credentials
            )

    def test_list_calendars_success(self, api):
        """Test successful calendar list fetch"""
        # Mock response
        mock_result = {
            "items": [
                {"id": "user@example.com", "summary": "Primary", "primary": True},
                {"id": "calendar2@example.com", "summary": "Work Calendar"},
            ]
        }

        api.service.calendarList().list().execute.return_value = mock_result

        calendars = api.list_calendars()

        assert len(calendars) == 2
        assert calendars[0]["id"] == "user@example.com"
        assert calendars[0]["primary"] is True

    def test_list_calendars_http_error(self, api):
        """Test HTTP error handling in list_calendars"""
        api.service.calendarList().list().execute.side_effect = HttpError(
            Mock(status=401), b"Unauthorized"
        )

        with pytest.raises(HttpError):
            api.list_calendars()

    def test_get_events_success(self, api):
        """Test successful events fetch"""
        mock_result = {
            "items": [
                {
                    "id": "event1",
                    "summary": "Team Meeting",
                    "start": {"dateTime": "2026-01-07T10:00:00Z"},
                    "end": {"dateTime": "2026-01-07T11:00:00Z"},
                }
            ]
        }

        api.service.events().list().execute.return_value = mock_result

        start = datetime(2026, 1, 7, 0, 0)
        end = datetime(2026, 1, 8, 0, 0)

        events = api.get_events("user@example.com", start, end)

        assert len(events) == 1
        assert events[0]["summary"] == "Team Meeting"

    def test_get_events_with_parameters(self, api):
        """Test get_events with correct API parameters"""
        mock_result = {"items": []}

        # Create a fresh mock for the events chain
        mock_events = Mock()
        mock_list = Mock()
        mock_list.execute.return_value = mock_result
        mock_events.list.return_value = mock_list
        api.service.events.return_value = mock_events

        start = datetime(2026, 1, 7, 0, 0)
        end = datetime(2026, 1, 8, 0, 0)

        api.get_events("user@example.com", start, end, single_events=True)

        # Verify API was called with correct parameters
        mock_events.list.assert_called_once()
        call_kwargs = mock_events.list.call_args[1]
        assert call_kwargs["calendarId"] == "user@example.com"
        assert call_kwargs["singleEvents"] is True
        assert call_kwargs["orderBy"] == "startTime"

    def test_test_connection_success(self, api):
        """Test successful connection test"""
        api.service.calendarList().list().execute.return_value = {"items": []}

        assert api.test_connection() is True

    def test_test_connection_failure(self, api):
        """Test failed connection test"""
        api.service.calendarList().list().execute.side_effect = HttpError(
            Mock(status=401), b"Unauthorized"
        )

        assert api.test_connection() is False


class TestCalendarFetcher:
    """Test Calendar Fetcher"""

    @pytest.fixture
    def mock_pb_client(self):
        """Create mock PocketBase client"""
        return Mock(spec=PocketBaseClient)

    @pytest.fixture
    def mock_credentials(self):
        """Create mock credentials"""
        creds = Mock()
        creds.expired = False
        creds.refresh_token = "test_refresh_token"
        return creds

    @pytest.fixture
    def fetcher(self, mock_pb_client, mock_credentials):
        """Create Calendar fetcher with mock API"""
        with patch("app.services.fetchers.calendar_fetcher.build"):
            # Mock TokenManager to avoid ENCRYPTION_KEY requirement
            mock_token_manager = Mock()
            fetcher = CalendarFetcher(
                mock_pb_client,
                credentials=mock_credentials,
                token_manager=mock_token_manager,
            )
            return fetcher

    def test_initialization(self, fetcher):
        """Test fetcher initialization"""
        assert fetcher.source_name == "calendar"
        assert fetcher.enabled_setting_key == "calendar_enabled"
        assert fetcher.priority == 80

    def test_initialization_without_credentials(self, mock_pb_client):
        """Test initialization without credentials"""
        mock_token_manager = Mock()
        fetcher = CalendarFetcher(mock_pb_client, token_manager=mock_token_manager)
        assert fetcher.credentials is None
        assert fetcher.api is None

    def test_validate_configuration_no_credentials(self, mock_pb_client):
        """Test validation fails without credentials"""
        mock_token_manager = Mock()
        mock_token_manager.load_token.return_value = None
        fetcher = CalendarFetcher(
            mock_pb_client, credentials=None, token_manager=mock_token_manager
        )

        is_valid, error = fetcher.validate_configuration()

        assert is_valid is False
        assert "credentials not found" in error.lower()

    @patch.object(GoogleCalendarAPI, "test_connection")
    def test_validate_configuration_success(self, mock_test, fetcher):
        """Test successful validation"""
        mock_test.return_value = True

        is_valid, error = fetcher.validate_configuration()

        assert is_valid is True
        assert error is None

    @patch.object(GoogleCalendarAPI, "test_connection")
    def test_validate_configuration_connection_failure(self, mock_test, fetcher):
        """Test validation fails with connection error"""
        mock_test.return_value = False

        is_valid, error = fetcher.validate_configuration()

        assert is_valid is False
        assert "Failed to connect" in error

    def test_should_include_event_created_by_user(self, fetcher):
        """Test filtering: event created by user"""
        event = {
            "organizer": {"email": "user@example.com"},
            "attendees": [{"email": "colleague@example.com"}],
        }

        assert fetcher._should_include_event(event, "user@example.com", []) is True

    def test_should_include_event_invited_by_monitored(self, fetcher):
        """Test filtering: user invited by monitored email"""
        event = {
            "organizer": {"email": "boss@example.com"},
            "attendees": [
                {"email": "user@example.com"},
                {"email": "colleague@example.com"},
            ],
        }

        monitored = ["boss@example.com"]
        assert (
            fetcher._should_include_event(event, "user@example.com", monitored) is True
        )

    def test_should_include_event_user_invited_monitored(self, fetcher):
        """Test filtering: user invited monitored email"""
        event = {
            "organizer": {"email": "user@example.com"},
            "attendees": [
                {"email": "client@example.com"},
                {"email": "colleague@example.com"},
            ],
        }

        monitored = ["client@example.com"]
        assert (
            fetcher._should_include_event(event, "user@example.com", monitored) is True
        )

    def test_should_not_include_event_no_match(self, fetcher):
        """Test filtering: event does not match any rule"""
        event = {
            "organizer": {"email": "other@example.com"},
            "attendees": [{"email": "user@example.com"}],
        }

        monitored = ["client@example.com"]
        assert (
            fetcher._should_include_event(event, "user@example.com", monitored)
            is False
        )

    def test_process_event_success(self, fetcher):
        """Test processing event with all data"""
        event = {
            "id": "event123",
            "summary": "Project Planning",
            "start": {"dateTime": "2026-01-07T10:00:00Z"},
            "end": {"dateTime": "2026-01-07T11:30:00Z"},
            "organizer": {"email": "user@example.com"},
            "attendees": [
                {"email": "user@example.com", "displayName": "User"},
                {"email": "colleague@example.com", "displayName": "John Doe"},
            ],
            "location": "Conference Room A",
        }

        result = fetcher._process_event(event, "user@example.com")

        assert result is not None
        assert result["description"] == "Meeting: Project Planning with John Doe"
        assert result["duration_minutes"] == 90.0
        assert result["source_id"] == "calendar_user@example.com_event123"
        assert result["metadata"]["title"] == "Project Planning"
        assert result["metadata"]["location"] == "Conference Room A"

    def test_process_event_multiple_attendees(self, fetcher):
        """Test processing event with multiple attendees"""
        event = {
            "id": "event123",
            "summary": "Team Sync",
            "start": {"dateTime": "2026-01-07T10:00:00Z"},
            "end": {"dateTime": "2026-01-07T11:00:00Z"},
            "organizer": {"email": "user@example.com"},
            "attendees": [
                {"email": "user@example.com"},
                {"email": "alice@example.com", "displayName": "Alice"},
                {"email": "bob@example.com", "displayName": "Bob"},
                {"email": "charlie@example.com", "displayName": "Charlie"},
                {"email": "dave@example.com", "displayName": "Dave"},
            ],
        }

        result = fetcher._process_event(event, "user@example.com")

        assert result is not None
        # Should show first 3 + count
        assert "Alice, Bob, Charlie +1 more" in result["description"]

    def test_process_event_no_attendees(self, fetcher):
        """Test processing event without attendees"""
        event = {
            "id": "event123",
            "summary": "Focus Time",
            "start": {"dateTime": "2026-01-07T10:00:00Z"},
            "end": {"dateTime": "2026-01-07T11:00:00Z"},
            "organizer": {"email": "user@example.com"},
        }

        result = fetcher._process_event(event, "user@example.com")

        assert result is not None
        assert result["description"] == "Meeting: Focus Time"

    def test_process_event_all_day(self, fetcher):
        """Test processing all-day event (should be skipped)"""
        event = {
            "id": "event123",
            "summary": "Holiday",
            "start": {"date": "2026-01-07"},
            "end": {"date": "2026-01-08"},
        }

        result = fetcher._process_event(event, "user@example.com")

        assert result is None

    def test_process_event_short_duration(self, fetcher):
        """Test processing very short event (should be skipped)"""
        event = {
            "id": "event123",
            "summary": "Quick Chat",
            "start": {"dateTime": "2026-01-07T10:00:00Z"},
            "end": {"dateTime": "2026-01-07T10:03:00Z"},  # 3 minutes
            "organizer": {"email": "user@example.com"},
        }

        result = fetcher._process_event(event, "user@example.com")

        assert result is None

    @patch.object(CalendarFetcher, "is_enabled")
    def test_fetch_disabled(self, mock_enabled, fetcher):
        """Test fetch when fetcher is disabled"""
        mock_enabled.return_value = False

        result = fetcher.fetch()

        assert result.success is False
        assert "disabled" in result.error

    @patch.object(CalendarFetcher, "is_enabled")
    @patch.object(CalendarFetcher, "validate_configuration")
    def test_fetch_invalid_configuration(self, mock_validate, mock_enabled, fetcher):
        """Test fetch with invalid configuration"""
        mock_enabled.return_value = True
        mock_validate.return_value = (False, "Invalid credentials")

        result = fetcher.fetch()

        assert result.success is False
        assert result.error == "Invalid credentials"

    @patch.object(CalendarFetcher, "is_enabled")
    @patch.object(CalendarFetcher, "validate_configuration")
    @patch.object(GoogleCalendarAPI, "list_calendars")
    @patch.object(GoogleCalendarAPI, "get_events")
    @patch.object(CalendarFetcher, "event_exists")
    @patch.object(CalendarFetcher, "create_raw_event")
    def test_fetch_success(
        self,
        mock_create,
        mock_exists,
        mock_get_events,
        mock_list_calendars,
        mock_validate,
        mock_enabled,
        fetcher,
        mock_pb_client,
    ):
        """Test successful fetch"""
        mock_enabled.return_value = True
        mock_validate.return_value = (True, None)

        # Mock calendar list
        mock_list_calendars.return_value = [
            {"id": "user@example.com", "primary": True}
        ]

        # Mock events
        mock_get_events.return_value = [
            {
                "id": "event1",
                "summary": "Team Meeting",
                "start": {"dateTime": "2026-01-07T10:00:00Z"},
                "end": {"dateTime": "2026-01-07T11:00:00Z"},
                "organizer": {"email": "user@example.com"},
                "attendees": [{"email": "user@example.com"}],
            }
        ]

        # Mock settings
        mock_pb_client.get_setting.return_value = ""

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

    @patch.object(CalendarFetcher, "is_enabled")
    @patch.object(CalendarFetcher, "validate_configuration")
    @patch.object(GoogleCalendarAPI, "list_calendars")
    def test_fetch_http_error(
        self, mock_list_calendars, mock_validate, mock_enabled, fetcher
    ):
        """Test fetch with HTTP error"""
        mock_enabled.return_value = True
        mock_validate.return_value = (True, None)

        # Mock HTTP error
        mock_response = Mock()
        mock_response.status = 401
        error = HttpError(mock_response, b"Unauthorized")
        mock_list_calendars.side_effect = error

        start = datetime(2026, 1, 7)
        end = datetime(2026, 1, 7)

        result = fetcher.fetch(start_date=start, end_date=end)

        assert result.success is False
        assert "HTTP error" in result.error
        assert "401" in result.error

    @patch.object(CalendarFetcher, "is_enabled")
    @patch.object(CalendarFetcher, "validate_configuration")
    @patch.object(GoogleCalendarAPI, "list_calendars")
    @patch.object(GoogleCalendarAPI, "get_events")
    @patch.object(CalendarFetcher, "event_exists")
    def test_fetch_skips_existing_events(
        self,
        mock_exists,
        mock_get_events,
        mock_list_calendars,
        mock_validate,
        mock_enabled,
        fetcher,
        mock_pb_client,
    ):
        """Test that fetch skips existing events"""
        mock_enabled.return_value = True
        mock_validate.return_value = (True, None)

        mock_list_calendars.return_value = [
            {"id": "user@example.com", "primary": True}
        ]

        mock_get_events.return_value = [
            {
                "id": "event1",
                "summary": "Team Meeting",
                "start": {"dateTime": "2026-01-07T10:00:00Z"},
                "end": {"dateTime": "2026-01-07T11:00:00Z"},
                "organizer": {"email": "user@example.com"},
            }
        ]

        mock_pb_client.get_setting.return_value = ""

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
