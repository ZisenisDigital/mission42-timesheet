"""
Google Calendar Data Fetcher

Fetches meeting events from Google Calendar API (high priority source: 80).
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
from app.utils.priority import SOURCE_CALENDAR
from app.utils.oauth import TokenManager, OAuthToken


class GoogleCalendarAPI:
    """
    Wrapper for Google Calendar API.

    API Documentation: https://developers.google.com/calendar/api
    """

    SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

    def __init__(self, credentials: Credentials):
        """
        Initialize Google Calendar API client.

        Args:
            credentials: Google OAuth2 credentials
        """
        self.credentials = credentials
        self.service = build("calendar", "v3", credentials=credentials)

    def list_calendars(self) -> List[Dict[str, Any]]:
        """
        List all calendars accessible to the user.

        Returns:
            List of calendar objects

        Raises:
            HttpError: If API request fails
        """
        try:
            calendar_list = self.service.calendarList().list().execute()
            return calendar_list.get("items", [])
        except HttpError as error:
            raise error

    def get_events(
        self,
        calendar_id: str,
        start_date: datetime,
        end_date: datetime,
        single_events: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get calendar events for a date range.

        Args:
            calendar_id: Calendar ID (email address or "primary")
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            single_events: Expand recurring events into individual instances

        Returns:
            List of event objects

        Raises:
            HttpError: If API request fails
        """
        try:
            # Format dates as RFC3339 timestamp
            time_min = start_date.isoformat() + "Z"
            time_max = end_date.isoformat() + "Z"

            events_result = (
                self.service.events()
                .list(
                    calendarId=calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=single_events,
                    orderBy="startTime" if single_events else None,
                )
                .execute()
            )

            return events_result.get("items", [])
        except HttpError as error:
            raise error

    def test_connection(self) -> bool:
        """
        Test API connection and authentication.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.service.calendarList().list(maxResults=1).execute()
            return True
        except Exception:
            return False


class CalendarFetcher(BaseFetcher):
    """
    Fetches meeting events from Google Calendar API.

    Calendar is a high priority data source (80) for tracking meetings
    and scheduled work time.
    """

    def __init__(
        self,
        pb_client: PocketBaseClient,
        credentials: Optional[Credentials] = None,
        token_manager: Optional[TokenManager] = None,
    ):
        """
        Initialize Calendar fetcher.

        Args:
            pb_client: PocketBase client instance
            credentials: Google OAuth2 credentials (optional)
            token_manager: Token manager for OAuth token storage (optional)
        """
        super().__init__(
            pb_client=pb_client,
            source_name=SOURCE_CALENDAR,
            enabled_setting_key="calendar_enabled",
        )

        self.credentials = credentials
        self.token_manager = token_manager or TokenManager()
        self.api = GoogleCalendarAPI(credentials) if credentials else None

    def _load_credentials(self) -> Optional[Credentials]:
        """
        Load OAuth credentials from token storage.

        Returns:
            Credentials object or None if not available
        """
        try:
            # Get stored token from PocketBase or token manager
            # This is a placeholder - actual implementation would fetch from storage
            token_data = self.token_manager.load_token(
                "google_calendar", self.pb_client
            )

            if not token_data:
                return None

            creds = Credentials.from_authorized_user_info(token_data, self.SCOPES)

            # Refresh token if expired
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # Save refreshed token
                self.token_manager.save_token(
                    "google_calendar",
                    OAuthToken.from_credentials(creds),
                    self.pb_client,
                )

            return creds
        except Exception:
            return None

    def validate_configuration(self) -> tuple[bool, Optional[str]]:
        """
        Validate Calendar configuration.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Try to load credentials if not provided
        if not self.credentials:
            self.credentials = self._load_credentials()

        if not self.credentials:
            return (
                False,
                "Google Calendar credentials not found. Please authenticate first.",
            )

        # Initialize API if needed
        if not self.api:
            self.api = GoogleCalendarAPI(self.credentials)

        # Test API connection
        try:
            if not self.api.test_connection():
                return (False, "Failed to connect to Google Calendar API")
        except Exception as e:
            return (False, f"Google Calendar API connection error: {str(e)}")

        return (True, None)

    def _should_include_event(
        self, event: Dict[str, Any], user_email: str, monitored_emails: List[str]
    ) -> bool:
        """
        Determine if an event should be included based on filtering rules.

        Rules:
        1. Event is created by the user
        2. User is invited by one of the monitored emails
        3. User invited one of the monitored emails

        Args:
            event: Calendar event object
            user_email: User's email address
            monitored_emails: List of monitored email addresses

        Returns:
            True if event should be included
        """
        # Get organizer email
        organizer = event.get("organizer", {})
        organizer_email = organizer.get("email", "").lower()

        # Get attendees
        attendees = event.get("attendees", [])
        attendee_emails = [a.get("email", "").lower() for a in attendees]

        # Rule 1: Event created by user
        if organizer_email == user_email.lower():
            return True

        # Rule 2: User invited by monitored email
        if user_email.lower() in attendee_emails and any(
            email.lower() in [organizer_email] for email in monitored_emails
        ):
            return True

        # Rule 3: User invited monitored email
        if organizer_email == user_email.lower() and any(
            email.lower() in attendee_emails for email in monitored_emails
        ):
            return True

        return False

    def _process_event(
        self, event: Dict[str, Any], calendar_email: str
    ) -> Optional[Dict[str, Any]]:
        """
        Process a calendar event into a raw event dictionary.

        Args:
            event: Calendar event from Google Calendar API
            calendar_email: Email of the calendar this event is from

        Returns:
            Event dictionary ready for PocketBase, or None if event should be skipped
        """
        # Get event start and end times
        start = event.get("start", {})
        end = event.get("end", {})

        # Parse datetime (handle both dateTime and date fields)
        try:
            if "dateTime" in start:
                start_time = datetime.fromisoformat(
                    start["dateTime"].replace("Z", "+00:00")
                )
                end_time = datetime.fromisoformat(end["dateTime"].replace("Z", "+00:00"))
            elif "date" in start:
                # All-day event - skip for now
                return None
            else:
                return None
        except (ValueError, KeyError):
            return None

        # Calculate duration in minutes
        duration = (end_time - start_time).total_seconds() / 60

        # Skip very short events (< 5 minutes)
        if duration < 5:
            return None

        # Get event title
        title = event.get("summary", "Untitled Meeting")

        # Get attendees for description
        attendees = event.get("attendees", [])
        attendee_names = [
            a.get("displayName") or a.get("email", "").split("@")[0]
            for a in attendees
            if a.get("email") != calendar_email
        ]

        # Build description
        if attendee_names:
            participant_str = ", ".join(attendee_names[:3])  # Limit to 3 names
            if len(attendee_names) > 3:
                participant_str += f" +{len(attendee_names) - 3} more"
            description = f"Meeting: {title} with {participant_str}"
        else:
            description = f"Meeting: {title}"

        # Create unique source ID
        event_id = event.get("id", "")
        source_id = f"calendar_{calendar_email}_{event_id}"

        # Extract metadata
        metadata = {
            "calendar": calendar_email,
            "event_id": event_id,
            "title": title,
            "organizer": event.get("organizer", {}).get("email"),
            "attendees": [a.get("email") for a in attendees],
            "location": event.get("location", ""),
            "conference_data": event.get("conferenceData", {}),
        }

        return {
            "source_id": source_id,
            "timestamp": start_time,
            "duration_minutes": duration,
            "description": description,
            "metadata": metadata,
        }

    def fetch(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> FetchResult:
        """
        Fetch calendar events and save to PocketBase.

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
                error="Calendar fetcher is disabled in settings",
            )

        # Validate configuration
        is_valid, error_msg = self.validate_configuration()
        if not is_valid:
            return FetchResult(success=False, error=error_msg)

        # Get date range
        if not start_date or not end_date:
            start_date, end_date = self.get_default_date_range(days_back=7)

        try:
            # Get monitored emails from settings
            monitored_emails = self.pb_client.get_setting("calendar_monitored_emails")
            if isinstance(monitored_emails, str):
                monitored_emails = [
                    e.strip() for e in monitored_emails.split(",") if e.strip()
                ]
            else:
                monitored_emails = []

            # Get list of calendars
            calendars = self.api.list_calendars()

            events_fetched = 0
            events_created = 0

            # Process each calendar
            for calendar in calendars:
                calendar_id = calendar.get("id")
                calendar_email = calendar.get("id")  # Calendar ID is usually the email

                # Fetch events from this calendar
                events = self.api.get_events(calendar_id, start_date, end_date)

                # Get user email (primary calendar)
                user_email = calendar_email if calendar.get("primary") else None
                if not user_email:
                    # Try to get from first primary calendar
                    for cal in calendars:
                        if cal.get("primary"):
                            user_email = cal.get("id")
                            break

                # Process each event
                for event in events:
                    # Apply filtering rules
                    if not self._should_include_event(
                        event, user_email or calendar_email, monitored_emails
                    ):
                        continue

                    event_data = self._process_event(event, calendar_email)

                    if not event_data:
                        continue

                    events_fetched += 1

                    # Check if event already exists
                    source_id = event_data["source_id"]
                    if not self.event_exists(source_id):
                        self.create_raw_event(**event_data)
                        events_created += 1

            result = FetchResult(
                success=True,
                events_fetched=events_fetched,
                events_created=events_created,
                metadata={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "calendars_processed": len(calendars),
                    "monitored_emails": monitored_emails,
                },
            )

            self.log_fetch_result(result)
            return result

        except HttpError as e:
            error_msg = f"Google Calendar API HTTP error: {e.resp.status}"
            return FetchResult(success=False, error=error_msg)

        except Exception as e:
            return FetchResult(
                success=False, error=f"Unexpected error: {str(e)}"
            )
