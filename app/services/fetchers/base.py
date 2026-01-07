"""
Base Fetcher Class

Abstract base class for all data source fetchers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from pocketbase.models import Record

from app.pocketbase_client import PocketBaseClient
from app.utils.priority import get_source_priority


class FetchResult:
    """Result from a fetch operation"""

    def __init__(
        self,
        success: bool,
        events_fetched: int = 0,
        events_created: int = 0,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.success = success
        self.events_fetched = events_fetched
        self.events_created = events_created
        self.error = error
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()

    def __repr__(self) -> str:
        if self.success:
            return (
                f"FetchResult(success=True, fetched={self.events_fetched}, "
                f"created={self.events_created})"
            )
        else:
            return f"FetchResult(success=False, error={self.error})"


class BaseFetcher(ABC):
    """
    Abstract base class for data source fetchers.

    All data source fetchers (WakaTime, Google Calendar, Gmail, GitHub, Cloud Events)
    should inherit from this class and implement the abstract methods.
    """

    def __init__(
        self,
        pb_client: PocketBaseClient,
        source_name: str,
        enabled_setting_key: str,
    ):
        """
        Initialize base fetcher.

        Args:
            pb_client: PocketBase client instance
            source_name: Name of data source (e.g., "wakatime", "calendar")
            enabled_setting_key: Settings key to check if fetcher is enabled
        """
        self.pb_client = pb_client
        self.source_name = source_name
        self.enabled_setting_key = enabled_setting_key
        self.priority = get_source_priority(source_name)

    @abstractmethod
    def fetch(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> FetchResult:
        """
        Fetch events from data source and store in PocketBase.

        Args:
            start_date: Optional start date for fetching (defaults to last fetch or 7 days ago)
            end_date: Optional end date for fetching (defaults to now)

        Returns:
            FetchResult with success status and statistics
        """
        pass

    def is_enabled(self) -> bool:
        """
        Check if this fetcher is enabled in settings.

        Returns:
            True if enabled, False otherwise
        """
        try:
            enabled = self.pb_client.get_setting(self.enabled_setting_key)
            return bool(enabled)
        except Exception:
            # If setting not found or error, assume disabled
            return False

    def get_last_fetch_time(self) -> Optional[datetime]:
        """
        Get timestamp of last successful fetch.

        Returns:
            Datetime of last fetch, or None if never fetched

        Implementation:
            Queries raw_events collection for most recent event from this source
        """
        try:
            records = self.pb_client.get_list(
                collection=PocketBaseClient.COLLECTION_RAW_EVENTS,
                page=1,
                per_page=1,
                filter=f'source="{self.source_name}"',
                sort="-timestamp",
            )

            if records:
                # Parse timestamp from record
                timestamp_str = records[0].timestamp
                return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

            return None
        except Exception:
            return None

    def create_raw_event(
        self,
        source_id: str,
        timestamp: datetime,
        duration_minutes: int,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Record:
        """
        Create a raw event record in PocketBase.

        Args:
            source_id: Unique ID from source system
            timestamp: Event timestamp
            duration_minutes: Duration in minutes
            description: Event description
            metadata: Additional metadata as JSON

        Returns:
            Created raw_events record
        """
        return self.pb_client.create_raw_event(
            source=self.source_name,
            source_id=source_id,
            timestamp=timestamp,
            duration_minutes=duration_minutes,
            description=description,
            metadata=metadata,
        )

    def event_exists(self, source_id: str) -> bool:
        """
        Check if an event with this source_id already exists.

        Args:
            source_id: Unique ID from source system

        Returns:
            True if event exists, False otherwise
        """
        filter_str = f'source="{self.source_name}" && source_id="{source_id}"'
        return self.pb_client.exists(PocketBaseClient.COLLECTION_RAW_EVENTS, filter_str)

    def get_default_date_range(
        self, days_back: int = 7
    ) -> tuple[datetime, datetime]:
        """
        Get default date range for fetching.

        Args:
            days_back: Number of days to look back if no last fetch time

        Returns:
            Tuple of (start_date, end_date)
        """
        end_date = datetime.utcnow()

        # Check last fetch time
        last_fetch = self.get_last_fetch_time()

        if last_fetch:
            # Fetch from last fetch time (with small overlap buffer)
            from datetime import timedelta

            start_date = last_fetch - timedelta(hours=1)
        else:
            # First fetch: go back N days
            from datetime import timedelta

            start_date = end_date - timedelta(days=days_back)

        return (start_date, end_date)

    def log_fetch_result(self, result: FetchResult) -> None:
        """
        Log fetch result (can be overridden for custom logging).

        Args:
            result: FetchResult to log
        """
        if result.success:
            print(
                f"[{self.source_name}] Fetched {result.events_fetched} events, "
                f"created {result.events_created} new records"
            )
        else:
            print(f"[{self.source_name}] Fetch failed: {result.error}")

    def validate_configuration(self) -> tuple[bool, Optional[str]]:
        """
        Validate fetcher configuration (API keys, credentials, etc.).

        Returns:
            Tuple of (is_valid, error_message)
            - (True, None) if configuration is valid
            - (False, "error message") if configuration is invalid

        Should be overridden by subclasses to implement specific validation.
        """
        return (True, None)

    def get_info(self) -> Dict[str, Any]:
        """
        Get fetcher information.

        Returns:
            Dictionary with fetcher metadata
        """
        return {
            "source_name": self.source_name,
            "priority": self.priority,
            "enabled": self.is_enabled(),
            "last_fetch": self.get_last_fetch_time(),
            "configuration_valid": self.validate_configuration()[0],
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(source={self.source_name}, priority={self.priority})"
