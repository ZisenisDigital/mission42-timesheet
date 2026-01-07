"""
Gmail Data Fetcher

Fetches sent emails from Gmail API (priority: 60).
Tracks emails sent to monitored recipients.
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.services.fetchers.base import BaseFetcher, FetchResult
from app.pocketbase_client import PocketBaseClient
from app.utils.priority import SOURCE_GMAIL
from app.utils.oauth import OAuthToken, SecureTokenStorage, TokenManager


class GmailAPI:
    """
    Wrapper for Gmail API.

    API Documentation: https://developers.google.com/gmail/api
    """

    def __init__(self, credentials: Credentials):
        """
        Initialize Gmail API client.

        Args:
            credentials: Google OAuth credentials
        """
        self.credentials = credentials
        self.service = build("gmail", "v1", credentials=credentials)

    def list_sent_messages(
        self, after_date: Optional[datetime] = None, max_results: int = 500
    ) -> List[Dict[str, Any]]:
        """
        List sent messages from Gmail.

        Args:
            after_date: Only fetch messages sent after this date
            max_results: Maximum number of messages to fetch

        Returns:
            List of message metadata dictionaries

        Raises:
            HttpError: If API request fails
        """
        messages = []

        # Build query
        query_parts = ["in:sent"]
        if after_date:
            # Gmail uses format YYYY/MM/DD
            date_str = after_date.strftime("%Y/%m/%d")
            query_parts.append(f"after:{date_str}")

        query = " ".join(query_parts)

        try:
            # List messages
            results = (
                self.service.users()
                .messages()
                .list(userId="me", q=query, maxResults=max_results)
                .execute()
            )

            message_ids = results.get("messages", [])

            # Fetch full message details for each
            for msg_ref in message_ids:
                msg_id = msg_ref["id"]
                message = (
                    self.service.users()
                    .messages()
                    .get(userId="me", id=msg_id, format="metadata", metadataHeaders=["To", "Subject", "Date"])
                    .execute()
                )
                messages.append(message)

            return messages

        except HttpError as error:
            raise

    def get_message_details(self, message_id: str) -> Dict[str, Any]:
        """
        Get full details of a specific message.

        Args:
            message_id: Gmail message ID

        Returns:
            Message details dictionary

        Raises:
            HttpError: If API request fails
        """
        try:
            message = (
                self.service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )
            return message
        except HttpError as error:
            raise

    def test_connection(self) -> bool:
        """
        Test API connection and authentication.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to get profile (lightweight request)
            self.service.users().getProfile(userId="me").execute()
            return True
        except Exception:
            return False


class GmailFetcher(BaseFetcher):
    """
    Fetches sent emails from Gmail API.

    Gmail is a medium-high priority source (60) for tracking communication time.
    """

    def __init__(
        self,
        pb_client: PocketBaseClient,
        account_email: str,
        credentials: Optional[Credentials] = None,
        token_storage: Optional[SecureTokenStorage] = None,
    ):
        """
        Initialize Gmail fetcher.

        Args:
            pb_client: PocketBase client instance
            account_email: Gmail account email address
            credentials: Google OAuth credentials (optional if using token_storage)
            token_storage: Secure token storage for retrieving credentials
        """
        super().__init__(
            pb_client=pb_client,
            source_name=SOURCE_GMAIL,
            enabled_setting_key="gmail_enabled",
        )

        self.account_email = account_email
        self.credentials = credentials
        self.token_storage = token_storage
        self.api = None

        # Initialize API if credentials provided
        if self.credentials:
            self.api = GmailAPI(self.credentials)

    def _load_credentials_from_storage(self) -> bool:
        """
        Load credentials from token storage.

        Returns:
            True if credentials loaded successfully, False otherwise
        """
        if not self.token_storage:
            return False

        # Get encrypted token from PocketBase
        try:
            # Get email account record
            filter_str = f'email="{self.account_email}"'
            records = self.pb_client.get_list(
                collection="email_accounts",
                page=1,
                per_page=1,
                filter=filter_str,
            )

            if not records:
                return False

            record = records[0]

            # Check if active
            if not record.active:
                return False

            # Get encrypted token
            encrypted_token = record.oauth_token
            if not encrypted_token:
                return False

            # Decrypt and create credentials
            oauth_token = self.token_storage.retrieve_token(
                key=self.account_email, encrypted_data=encrypted_token
            )

            if not oauth_token:
                return False

            # Create Google credentials
            self.credentials = Credentials(
                token=oauth_token.access_token,
                refresh_token=oauth_token.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=os.getenv("GOOGLE_CLIENT_ID"),
                client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
                scopes=["https://www.googleapis.com/auth/gmail.readonly"],
            )

            # Refresh if expired
            if self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())

                # Update stored token
                updated_token = OAuthToken(
                    access_token=self.credentials.token,
                    refresh_token=self.credentials.refresh_token,
                    expires_at=datetime.utcnow() + timedelta(seconds=3600),
                )
                encrypted_updated = self.token_storage.store_token(
                    key=self.account_email, token=updated_token
                )

                # Update PocketBase
                self.pb_client.update(
                    collection="email_accounts",
                    record_id=record.id,
                    data={"oauth_token": encrypted_updated},
                )

            self.api = GmailAPI(self.credentials)
            return True

        except Exception as e:
            print(f"Error loading Gmail credentials: {e}")
            return False

    def validate_configuration(self) -> tuple[bool, Optional[str]]:
        """
        Validate Gmail configuration.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Try to load credentials if not already loaded
        if not self.credentials and self.token_storage:
            if not self._load_credentials_from_storage():
                return (False, "Failed to load Gmail credentials from storage")

        if not self.credentials:
            return (False, "Gmail OAuth credentials not configured")

        if not self.api:
            return (False, "Gmail API client not initialized")

        # Check for required Google OAuth settings
        if not os.getenv("GOOGLE_CLIENT_ID"):
            return (False, "GOOGLE_CLIENT_ID not set in environment")

        if not os.getenv("GOOGLE_CLIENT_SECRET"):
            return (False, "GOOGLE_CLIENT_SECRET not set in environment")

        # Test API connection
        try:
            if not self.api.test_connection():
                return (False, "Failed to connect to Gmail API (invalid credentials?)")
        except Exception as e:
            return (False, f"Gmail API connection error: {str(e)}")

        return (True, None)

    def _get_monitored_recipients(self) -> List[str]:
        """
        Get list of monitored email recipients from settings.

        Returns:
            List of email addresses to monitor
        """
        try:
            recipients_str = self.pb_client.get_setting("gmail_monitored_recipients")
            if not recipients_str:
                return []

            # Parse comma-separated list
            recipients = [email.strip() for email in recipients_str.split(",")]
            return [r for r in recipients if r]  # Filter empty strings

        except Exception:
            return []

    def _get_default_duration(self) -> int:
        """
        Get default email duration from settings.

        Returns:
            Duration in minutes (defaults to 30)
        """
        try:
            duration_str = self.pb_client.get_setting("gmail_default_duration_minutes")
            if duration_str:
                return int(duration_str)
        except Exception:
            pass

        return 30  # Default

    def _parse_message_headers(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse message headers to extract relevant information.

        Args:
            message: Gmail message dictionary

        Returns:
            Dictionary with parsed header information
        """
        headers = {}
        payload = message.get("payload", {})
        header_list = payload.get("headers", [])

        for header in header_list:
            name = header.get("name", "").lower()
            value = header.get("value", "")

            if name == "to":
                headers["to"] = value
            elif name == "subject":
                headers["subject"] = value
            elif name == "date":
                headers["date"] = value

        return headers

    def _extract_email_addresses(self, to_field: str) -> List[str]:
        """
        Extract email addresses from To field.

        Args:
            to_field: Value of To header (e.g., "John Doe <john@example.com>, jane@example.com")

        Returns:
            List of email addresses
        """
        import re

        # Extract email addresses using regex
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, to_field)

        return [email.lower() for email in emails]

    def _matches_monitored_recipients(self, to_addresses: List[str], monitored: List[str]) -> bool:
        """
        Check if any recipient matches monitored list.

        Args:
            to_addresses: List of recipient email addresses
            monitored: List of monitored email addresses

        Returns:
            True if any recipient is in monitored list
        """
        if not monitored:
            # If no monitored recipients configured, track all emails
            return True

        monitored_lower = [email.lower() for email in monitored]

        for address in to_addresses:
            if address in monitored_lower:
                return True

        return False

    def fetch(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> FetchResult:
        """
        Fetch sent emails from Gmail and save to PocketBase.

        Args:
            start_date: Optional start date (defaults to last fetch or 7 days ago)
            end_date: Optional end date (defaults to now)

        Returns:
            FetchResult with success status and statistics
        """
        # Check if enabled
        if not self.is_enabled():
            return FetchResult(
                success=False,
                error="Gmail fetcher is disabled in settings",
            )

        # Validate configuration
        is_valid, error_msg = self.validate_configuration()
        if not is_valid:
            return FetchResult(success=False, error=error_msg)

        # Get monitored recipients
        monitored_recipients = self._get_monitored_recipients()
        default_duration = self._get_default_duration()

        # Get date range
        if not start_date or not end_date:
            start_date, end_date = self.get_default_date_range(days_back=7)

        try:
            # Fetch sent messages
            messages = self.api.list_sent_messages(after_date=start_date)

            events_fetched = 0
            events_created = 0
            events_filtered = 0

            for message in messages:
                # Parse headers
                headers = self._parse_message_headers(message)

                # Get message timestamp (in milliseconds)
                internal_date_ms = int(message.get("internalDate", 0))
                if internal_date_ms == 0:
                    continue

                message_date = datetime.fromtimestamp(internal_date_ms / 1000.0)

                # Check if within date range
                if message_date < start_date or message_date > end_date:
                    continue

                # Extract recipient addresses
                to_field = headers.get("to", "")
                to_addresses = self._extract_email_addresses(to_field)

                # Filter by monitored recipients
                if not self._matches_monitored_recipients(to_addresses, monitored_recipients):
                    events_filtered += 1
                    continue

                events_fetched += 1

                # Get subject
                subject = headers.get("subject", "(No Subject)")

                # Create description
                recipient_names = ", ".join(to_addresses[:3])  # Limit to first 3
                if len(to_addresses) > 3:
                    recipient_names += f" (+{len(to_addresses) - 3} more)"

                description = f"Email to {recipient_names}: {subject}"

                # Create unique source ID
                message_id = message.get("id")
                source_id = f"gmail_{self.account_email}_{message_id}"

                # Check if already exists
                if self.event_exists(source_id):
                    continue

                # Create metadata
                metadata = {
                    "account": self.account_email,
                    "recipients": to_addresses,
                    "subject": subject,
                    "message_id": message_id,
                    "thread_id": message.get("threadId"),
                }

                # Create raw event
                self.create_raw_event(
                    source_id=source_id,
                    timestamp=message_date,
                    duration_minutes=default_duration,
                    description=description,
                    metadata=metadata,
                )

                events_created += 1

            result = FetchResult(
                success=True,
                events_fetched=events_fetched,
                events_created=events_created,
                metadata={
                    "account": self.account_email,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "total_messages": len(messages),
                    "events_filtered": events_filtered,
                    "monitored_recipients": monitored_recipients,
                },
            )

            self.log_fetch_result(result)
            return result

        except HttpError as e:
            error_msg = f"Gmail API HTTP error: {e.resp.status}"
            return FetchResult(success=False, error=error_msg)

        except Exception as e:
            return FetchResult(success=False, error=f"Unexpected error: {str(e)}")
