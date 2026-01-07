"""
WakaTime Data Fetcher

Fetches coding activity from WakaTime API (highest priority source: 100).
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import requests
from requests.exceptions import RequestException, HTTPError, Timeout

from app.services.fetchers.base import BaseFetcher, FetchResult
from app.pocketbase_client import PocketBaseClient
from app.utils.priority import SOURCE_WAKATIME


class WakaTimeAPI:
    """
    Wrapper for WakaTime API.

    API Documentation: https://wakatime.com/developers
    """

    BASE_URL = "https://wakatime.com/api/v1"

    def __init__(self, api_key: str):
        """
        Initialize WakaTime API client.

        Args:
            api_key: WakaTime API key (from https://wakatime.com/settings/api-key)
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def get_summaries(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get coding activity summaries for a date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            API response with daily summaries

        Raises:
            HTTPError: If API request fails
            Timeout: If request times out
        """
        # Format dates as YYYY-MM-DD
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        url = f"{self.BASE_URL}/users/current/summaries"
        params = {"start": start_str, "end": end_str}

        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()

        return response.json()

    def get_heartbeats(self, date: datetime) -> Dict[str, Any]:
        """
        Get raw heartbeats for a specific date.

        Args:
            date: Date to fetch heartbeats for

        Returns:
            API response with heartbeat data

        Raises:
            HTTPError: If API request fails
        """
        date_str = date.strftime("%Y-%m-%d")
        url = f"{self.BASE_URL}/users/current/heartbeats"
        params = {"date": date_str}

        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()

        return response.json()

    def test_connection(self) -> bool:
        """
        Test API connection and authentication.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            url = f"{self.BASE_URL}/users/current"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return True
        except Exception:
            return False


class WakaTimeFetcher(BaseFetcher):
    """
    Fetches coding activity from WakaTime API.

    WakaTime is the highest priority data source (100) as it provides
    ground truth for actual coding time.
    """

    def __init__(self, pb_client: PocketBaseClient, api_key: Optional[str] = None):
        """
        Initialize WakaTime fetcher.

        Args:
            pb_client: PocketBase client instance
            api_key: WakaTime API key (defaults to WAKATIME_API_KEY env var)
        """
        super().__init__(
            pb_client=pb_client,
            source_name=SOURCE_WAKATIME,
            enabled_setting_key="wakatime_enabled",
        )

        self.api_key = api_key or os.getenv("WAKATIME_API_KEY")
        self.api = WakaTimeAPI(self.api_key) if self.api_key else None

    def validate_configuration(self) -> tuple[bool, Optional[str]]:
        """
        Validate WakaTime configuration.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.api_key:
            return (False, "WAKATIME_API_KEY not set in environment")

        if not self.api:
            return (False, "WAKATIME_API_KEY not set in environment")

        # Test API connection
        try:
            if not self.api.test_connection():
                return (False, "Failed to connect to WakaTime API (invalid API key?)")
        except Exception as e:
            return (False, f"WakaTime API connection error: {str(e)}")

        return (True, None)

    def fetch(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> FetchResult:
        """
        Fetch coding activity from WakaTime and save to PocketBase.

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
                error="WakaTime fetcher is disabled in settings",
            )

        # Validate configuration
        is_valid, error_msg = self.validate_configuration()
        if not is_valid:
            return FetchResult(success=False, error=error_msg)

        # Get date range
        if not start_date or not end_date:
            start_date, end_date = self.get_default_date_range(days_back=7)

        try:
            # Fetch summaries from WakaTime
            summaries_data = self.api.get_summaries(start_date, end_date)

            events_fetched = 0
            events_created = 0

            # Process each day's summary
            for day_summary in summaries_data.get("data", []):
                day_events = self._process_day_summary(day_summary)
                events_fetched += len(day_events)

                # Save events to PocketBase
                for event_data in day_events:
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
                    "days_processed": len(summaries_data.get("data", [])),
                },
            )

            self.log_fetch_result(result)
            return result

        except HTTPError as e:
            error_msg = f"WakaTime API HTTP error: {e.response.status_code}"
            return FetchResult(success=False, error=error_msg)

        except Timeout:
            return FetchResult(success=False, error="WakaTime API request timed out")

        except RequestException as e:
            return FetchResult(success=False, error=f"WakaTime API request failed: {str(e)}")

        except Exception as e:
            return FetchResult(success=False, error=f"Unexpected error: {str(e)}")

    def _process_day_summary(self, day_summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process a single day's summary into raw events.

        Args:
            day_summary: Day summary from WakaTime API

        Returns:
            List of event dictionaries ready for PocketBase
        """
        events = []

        # Get the date for this summary
        date_str = day_summary.get("range", {}).get("date")
        if not date_str:
            return events

        # Parse date
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return events

        # Get grand total (total coding time for the day)
        grand_total_seconds = day_summary.get("grand_total", {}).get("total_seconds", 0)

        if grand_total_seconds == 0:
            return events

        # Process projects
        projects = day_summary.get("projects", [])

        for project in projects:
            project_name = project.get("name", "Unknown Project")
            project_seconds = project.get("total_seconds", 0)

            if project_seconds == 0:
                continue

            # Get primary language for this project
            languages = project.get("languages", [])
            primary_language = languages[0].get("name") if languages else None

            # Create event
            # Use project start time if available, otherwise use date at 12:00
            timestamp = date.replace(hour=12, minute=0, second=0)

            # Build description
            if primary_language:
                description = f"Coding: {project_name} - {primary_language}"
            else:
                description = f"Coding: {project_name}"

            # Create unique source ID (date + project)
            source_id = f"wakatime_{date_str}_{project_name}"

            # Metadata
            metadata = {
                "project": project_name,
                "total_seconds": project_seconds,
                "languages": [lang.get("name") for lang in languages],
                "editors": [
                    editor.get("name") for editor in project.get("editors", [])
                ],
            }

            event = {
                "source_id": source_id,
                "timestamp": timestamp,
                "duration_minutes": project_seconds / 60,
                "description": description,
                "metadata": metadata,
            }

            events.append(event)

        # If no projects but there's total time, create a generic coding event
        if not events and grand_total_seconds > 0:
            timestamp = date.replace(hour=12, minute=0, second=0)
            source_id = f"wakatime_{date_str}_total"

            event = {
                "source_id": source_id,
                "timestamp": timestamp,
                "duration_minutes": grand_total_seconds / 60,
                "description": "Coding: General",
                "metadata": {
                    "total_seconds": grand_total_seconds,
                    "note": "No specific project data available",
                },
            }

            events.append(event)

        return events
