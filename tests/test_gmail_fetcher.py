"""
Unit Tests for Gmail Fetcher

Tests for Gmail API integration and sent email fetching.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

from app.services.fetchers.gmail_fetcher import GmailAPI, GmailFetcher
from app.services.fetchers.base import FetchResult
from app.pocketbase_client import PocketBaseClient
from app.utils.oauth import OAuthToken, SecureTokenStorage, TokenManager


class TestGmailAPI:
    """Test Gmail API wrapper"""

    @pytest.fixture
    def credentials(self):
        """Create mock credentials"""
        return Mock(spec=Credentials)

    @pytest.fixture
    def api(self, credentials):
        """Create Gmail API instance"""
        with patch("app.services.fetchers.gmail_fetcher.build") as mock_build:
            mock_service = MagicMock()
            mock_build.return_value = mock_service
            api = GmailAPI(credentials)
            api.service = mock_service
            return api

    def test_initialization(self, credentials):
        """Test API initialization"""
        with patch("app.services.fetchers.gmail_fetcher.build") as mock_build:
            api = GmailAPI(credentials)
            mock_build.assert_called_once_with("gmail", "v1", credentials=credentials)
            assert api.credentials == credentials

    def test_list_sent_messages_success(self, api):
        """Test successful sent messages fetch"""
        # Mock list response
        mock_list_response = {
            "messages": [
                {"id": "msg1"},
                {"id": "msg2"},
            ]
        }

        # Mock get responses
        mock_msg1 = {
            "id": "msg1",
            "internalDate": "1704672000000",
            "payload": {
                "headers": [
                    {"name": "To", "value": "test@example.com"},
                    {"name": "Subject", "value": "Test Email"},
                    {"name": "Date", "value": "Mon, 08 Jan 2024 10:00:00 +0000"},
                ]
            },
        }

        mock_msg2 = {
            "id": "msg2",
            "internalDate": "1704675600000",
            "payload": {
                "headers": [
                    {"name": "To", "value": "another@example.com"},
                    {"name": "Subject", "value": "Another Email"},
                    {"name": "Date", "value": "Mon, 08 Jan 2024 11:00:00 +0000"},
                ]
            },
        }

        # Setup mock chain
        api.service.users().messages().list().execute.return_value = mock_list_response
        api.service.users().messages().get().execute.side_effect = [mock_msg1, mock_msg2]

        after_date = datetime(2024, 1, 8)
        messages = api.list_sent_messages(after_date=after_date)

        assert len(messages) == 2
        assert messages[0]["id"] == "msg1"
        assert messages[1]["id"] == "msg2"

    def test_list_sent_messages_no_results(self, api):
        """Test list with no messages"""
        mock_response = {"messages": []}
        api.service.users().messages().list().execute.return_value = mock_response

        messages = api.list_sent_messages()

        assert len(messages) == 0

    def test_list_sent_messages_with_date_filter(self, api):
        """Test date filtering in query"""
        mock_response = {"messages": []}
        api.service.users().messages().list().execute.return_value = mock_response

        after_date = datetime(2024, 1, 7)
        api.list_sent_messages(after_date=after_date)

        # Check that the query includes the date
        call_kwargs = api.service.users().messages().list.call_args[1]
        assert "after:2024/01/07" in call_kwargs["q"]

    def test_get_message_details(self, api):
        """Test getting message details"""
        mock_message = {
            "id": "msg123",
            "payload": {"headers": []},
        }
        api.service.users().messages().get().execute.return_value = mock_message

        result = api.get_message_details("msg123")

        assert result["id"] == "msg123"
        # Verify get was called (may be called multiple times due to chaining)
        assert api.service.users().messages().get.called

    def test_test_connection_success(self, api):
        """Test successful connection test"""
        api.service.users().getProfile().execute.return_value = {"emailAddress": "test@example.com"}

        assert api.test_connection() is True

    def test_test_connection_failure(self, api):
        """Test failed connection test"""
        api.service.users().getProfile().execute.side_effect = Exception("Connection failed")

        assert api.test_connection() is False


class TestGmailFetcher:
    """Test Gmail Fetcher"""

    @pytest.fixture
    def mock_pb_client(self):
        """Create mock PocketBase client"""
        client = Mock(spec=PocketBaseClient)
        client.COLLECTION_RAW_EVENTS = "raw_events"
        return client

    @pytest.fixture
    def mock_credentials(self):
        """Create mock credentials"""
        creds = Mock(spec=Credentials)
        creds.token = "access_token_123"
        creds.refresh_token = "refresh_token_456"
        creds.expired = False
        return creds

    @pytest.fixture
    def fetcher(self, mock_pb_client, mock_credentials):
        """Create Gmail fetcher instance"""
        with patch("app.services.fetchers.gmail_fetcher.GmailAPI"):
            fetcher = GmailFetcher(
                pb_client=mock_pb_client,
                account_email="test@example.com",
                credentials=mock_credentials,
            )
            fetcher.api = Mock(spec=GmailAPI)
            return fetcher

    def test_initialization(self, mock_pb_client, mock_credentials):
        """Test fetcher initialization"""
        fetcher = GmailFetcher(
            pb_client=mock_pb_client,
            account_email="test@example.com",
            credentials=mock_credentials,
        )

        assert fetcher.source_name == "gmail"
        assert fetcher.priority == 60
        assert fetcher.account_email == "test@example.com"
        assert fetcher.credentials == mock_credentials

    def test_validate_configuration_success(self, fetcher):
        """Test successful configuration validation"""
        fetcher.api.test_connection.return_value = True

        with patch.dict("os.environ", {"GOOGLE_CLIENT_ID": "test_id", "GOOGLE_CLIENT_SECRET": "test_secret"}):
            is_valid, error = fetcher.validate_configuration()

        assert is_valid is True
        assert error is None

    def test_validate_configuration_no_credentials(self, mock_pb_client):
        """Test validation with no credentials"""
        fetcher = GmailFetcher(
            pb_client=mock_pb_client,
            account_email="test@example.com",
            credentials=None,
        )

        is_valid, error = fetcher.validate_configuration()

        assert is_valid is False
        assert "credentials not configured" in error.lower()

    def test_validate_configuration_missing_client_id(self, fetcher):
        """Test validation with missing client ID"""
        with patch.dict("os.environ", {"GOOGLE_CLIENT_SECRET": "test_secret"}, clear=True):
            is_valid, error = fetcher.validate_configuration()

        assert is_valid is False
        assert "GOOGLE_CLIENT_ID" in error

    def test_get_monitored_recipients(self, fetcher, mock_pb_client):
        """Test getting monitored recipients from settings"""
        mock_pb_client.get_setting.return_value = "user1@example.com, user2@example.com, user3@example.com"

        recipients = fetcher._get_monitored_recipients()

        assert len(recipients) == 3
        assert "user1@example.com" in recipients
        assert "user2@example.com" in recipients
        assert "user3@example.com" in recipients

    def test_get_monitored_recipients_empty(self, fetcher, mock_pb_client):
        """Test with no monitored recipients"""
        mock_pb_client.get_setting.return_value = ""

        recipients = fetcher._get_monitored_recipients()

        assert len(recipients) == 0

    def test_get_default_duration(self, fetcher, mock_pb_client):
        """Test getting default duration"""
        mock_pb_client.get_setting.return_value = "45"

        duration = fetcher._get_default_duration()

        assert duration == 45

    def test_get_default_duration_fallback(self, fetcher, mock_pb_client):
        """Test default duration fallback"""
        mock_pb_client.get_setting.side_effect = Exception("Setting not found")

        duration = fetcher._get_default_duration()

        assert duration == 30  # Default value

    def test_parse_message_headers(self, fetcher):
        """Test parsing message headers"""
        message = {
            "payload": {
                "headers": [
                    {"name": "To", "value": "recipient@example.com"},
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "Date", "value": "Mon, 08 Jan 2024 10:00:00 +0000"},
                    {"name": "From", "value": "sender@example.com"},
                ]
            }
        }

        headers = fetcher._parse_message_headers(message)

        assert headers["to"] == "recipient@example.com"
        assert headers["subject"] == "Test Subject"
        assert headers["date"] == "Mon, 08 Jan 2024 10:00:00 +0000"

    def test_extract_email_addresses(self, fetcher):
        """Test extracting email addresses from To field"""
        to_field = "John Doe <john@example.com>, Jane Smith <jane@example.com>, bob@example.com"

        emails = fetcher._extract_email_addresses(to_field)

        assert len(emails) == 3
        assert "john@example.com" in emails
        assert "jane@example.com" in emails
        assert "bob@example.com" in emails

    def test_extract_email_addresses_simple(self, fetcher):
        """Test extracting simple email address"""
        to_field = "simple@example.com"

        emails = fetcher._extract_email_addresses(to_field)

        assert len(emails) == 1
        assert emails[0] == "simple@example.com"

    def test_matches_monitored_recipients_match(self, fetcher):
        """Test matching monitored recipients"""
        to_addresses = ["user1@example.com", "other@example.com"]
        monitored = ["user1@example.com", "user2@example.com"]

        matches = fetcher._matches_monitored_recipients(to_addresses, monitored)

        assert matches is True

    def test_matches_monitored_recipients_no_match(self, fetcher):
        """Test non-matching monitored recipients"""
        to_addresses = ["other@example.com", "another@example.com"]
        monitored = ["user1@example.com", "user2@example.com"]

        matches = fetcher._matches_monitored_recipients(to_addresses, monitored)

        assert matches is False

    def test_matches_monitored_recipients_empty_list(self, fetcher):
        """Test with empty monitored list (should match all)"""
        to_addresses = ["anyone@example.com"]
        monitored = []

        matches = fetcher._matches_monitored_recipients(to_addresses, monitored)

        assert matches is True

    def test_fetch_disabled(self, fetcher):
        """Test fetch when fetcher is disabled"""
        fetcher.is_enabled = Mock(return_value=False)

        result = fetcher.fetch()

        assert result.success is False
        assert "disabled" in result.error.lower()

    def test_fetch_invalid_config(self, fetcher):
        """Test fetch with invalid configuration"""
        fetcher.is_enabled = Mock(return_value=True)
        fetcher.validate_configuration = Mock(return_value=(False, "Invalid config"))

        result = fetcher.fetch()

        assert result.success is False
        assert result.error == "Invalid config"

    def test_fetch_success(self, fetcher, mock_pb_client):
        """Test successful fetch"""
        # Setup
        fetcher.is_enabled = Mock(return_value=True)
        fetcher.validate_configuration = Mock(return_value=(True, None))

        def mock_get_setting(key):
            settings = {
                "gmail_monitored_recipients": "client@example.com",
                "gmail_default_duration_minutes": "30",
            }
            return settings.get(key, "")

        mock_pb_client.get_setting = Mock(side_effect=mock_get_setting)

        # Mock messages
        mock_messages = [
            {
                "id": "msg1",
                "internalDate": str(int(datetime(2024, 1, 8, 10, 0).timestamp() * 1000)),
                "threadId": "thread1",
                "payload": {
                    "headers": [
                        {"name": "To", "value": "client@example.com"},
                        {"name": "Subject", "value": "Project Update"},
                        {"name": "Date", "value": "Mon, 08 Jan 2024 10:00:00 +0000"},
                    ]
                },
            }
        ]

        fetcher.api.list_sent_messages.return_value = mock_messages
        fetcher.event_exists = Mock(return_value=False)
        fetcher.create_raw_event = Mock()
        fetcher.get_default_date_range = Mock(return_value=(
            datetime(2024, 1, 1),
            datetime(2024, 1, 8, 23, 59, 59),  # End of day
        ))

        # Execute
        result = fetcher.fetch()

        # Verify
        assert result.success is True
        assert result.events_fetched == 1
        assert result.events_created == 1
        fetcher.create_raw_event.assert_called_once()

    def test_fetch_filters_by_recipients(self, fetcher, mock_pb_client):
        """Test that fetch filters by monitored recipients"""
        # Setup
        fetcher.is_enabled = Mock(return_value=True)
        fetcher.validate_configuration = Mock(return_value=(True, None))

        def mock_get_setting(key):
            settings = {
                "gmail_monitored_recipients": "client@example.com",
                "gmail_default_duration_minutes": "30",
            }
            return settings.get(key, "")

        mock_pb_client.get_setting = Mock(side_effect=mock_get_setting)

        # Mock messages - one matching, one not
        mock_messages = [
            {
                "id": "msg1",
                "internalDate": str(int(datetime(2024, 1, 8, 10, 0).timestamp() * 1000)),
                "threadId": "thread1",
                "payload": {
                    "headers": [
                        {"name": "To", "value": "client@example.com"},
                        {"name": "Subject", "value": "Project Update"},
                    ]
                },
            },
            {
                "id": "msg2",
                "internalDate": str(int(datetime(2024, 1, 8, 11, 0).timestamp() * 1000)),
                "threadId": "thread2",
                "payload": {
                    "headers": [
                        {"name": "To", "value": "other@example.com"},
                        {"name": "Subject", "value": "Other Email"},
                    ]
                },
            },
        ]

        fetcher.api.list_sent_messages.return_value = mock_messages
        fetcher.event_exists = Mock(return_value=False)
        fetcher.create_raw_event = Mock()
        fetcher.get_default_date_range = Mock(return_value=(
            datetime(2024, 1, 1),
            datetime(2024, 1, 8, 23, 59, 59),  # End of day
        ))

        # Execute
        result = fetcher.fetch()

        # Verify - only one email should be created (the matching one)
        assert result.success is True
        assert result.events_fetched == 1
        assert result.events_created == 1
        assert result.metadata["events_filtered"] == 1

    def test_fetch_skips_existing_events(self, fetcher, mock_pb_client):
        """Test that fetch skips existing events"""
        # Setup
        fetcher.is_enabled = Mock(return_value=True)
        fetcher.validate_configuration = Mock(return_value=(True, None))

        def mock_get_setting(key):
            return ""

        mock_pb_client.get_setting = Mock(side_effect=mock_get_setting)

        mock_messages = [
            {
                "id": "msg1",
                "internalDate": str(int(datetime(2024, 1, 8, 10, 0).timestamp() * 1000)),
                "threadId": "thread1",
                "payload": {
                    "headers": [
                        {"name": "To", "value": "test@example.com"},
                        {"name": "Subject", "value": "Test"},
                    ]
                },
            }
        ]

        fetcher.api.list_sent_messages.return_value = mock_messages
        fetcher.event_exists = Mock(return_value=True)  # Event already exists
        fetcher.create_raw_event = Mock()
        fetcher.get_default_date_range = Mock(return_value=(
            datetime(2024, 1, 1),
            datetime(2024, 1, 8, 23, 59, 59),  # End of day
        ))

        # Execute
        result = fetcher.fetch()

        # Verify - event fetched but not created
        assert result.success is True
        assert result.events_fetched == 1
        assert result.events_created == 0
        fetcher.create_raw_event.assert_not_called()

    def test_fetch_api_error(self, fetcher):
        """Test fetch with API error"""
        fetcher.is_enabled = Mock(return_value=True)
        fetcher.validate_configuration = Mock(return_value=(True, None))
        fetcher.api.list_sent_messages.side_effect = Exception("API Error")
        fetcher.get_default_date_range = Mock(return_value=(
            datetime(2024, 1, 1),
            datetime(2024, 1, 8),
        ))

        result = fetcher.fetch()

        assert result.success is False
        assert "Unexpected error" in result.error
