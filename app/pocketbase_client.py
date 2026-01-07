"""
PocketBase Client Wrapper

Provides high-level CRUD operations and utilities for interacting with PocketBase collections.
"""

import os
from typing import Any, Dict, List, Optional, TypeVar
from datetime import datetime
from pocketbase import PocketBase
from pocketbase.client import ClientResponseError
from pocketbase.models import Record


T = TypeVar("T", bound=Record)


class PocketBaseClient:
    """
    High-level wrapper around PocketBase SDK.

    Provides convenient methods for CRUD operations across all collections
    with error handling, authentication, and type hints.
    """

    # Collection names
    COLLECTION_SETTINGS = "settings"
    COLLECTION_EMAIL_ACCOUNTS = "email_accounts"
    COLLECTION_CALENDAR_ACCOUNTS = "calendar_accounts"
    COLLECTION_WORK_PACKAGES = "work_packages"
    COLLECTION_PROJECT_SPECS = "project_specs"
    COLLECTION_RAW_EVENTS = "raw_events"
    COLLECTION_TIME_BLOCKS = "time_blocks"
    COLLECTION_WEEK_SUMMARIES = "week_summaries"
    COLLECTION_CLOUD_EVENTS = "cloud_events"

    def __init__(self, url: Optional[str] = None, auto_auth: bool = True):
        """
        Initialize PocketBase client.

        Args:
            url: PocketBase URL (defaults to POCKETBASE_URL env var)
            auto_auth: Automatically authenticate as admin on init
        """
        self.url = url or os.getenv("POCKETBASE_URL", "http://127.0.0.1:8090")
        self.client = PocketBase(self.url)
        self._admin_email = os.getenv("PB_ADMIN_EMAIL")
        self._admin_password = os.getenv("PB_ADMIN_PASSWORD")

        if auto_auth and self._admin_email and self._admin_password:
            self.authenticate_admin()

    def authenticate_admin(self) -> None:
        """Authenticate as admin user"""
        if not self._admin_email or not self._admin_password:
            raise ValueError("PB_ADMIN_EMAIL and PB_ADMIN_PASSWORD must be set")

        try:
            self.client.admins.auth_with_password(self._admin_email, self._admin_password)
        except ClientResponseError as e:
            raise RuntimeError(f"Failed to authenticate as admin: {e}")

    def health_check(self) -> bool:
        """
        Check if PocketBase is running and accessible.

        Returns:
            True if healthy, False otherwise
        """
        try:
            self.client.health.check()
            return True
        except Exception:
            return False

    # Generic CRUD operations

    def create(self, collection: str, data: Dict[str, Any]) -> Record:
        """
        Create a new record in a collection.

        Args:
            collection: Collection name
            data: Record data

        Returns:
            Created record

        Raises:
            ClientResponseError: If creation fails
        """
        return self.client.collection(collection).create(data)

    def get(self, collection: str, record_id: str) -> Record:
        """
        Get a record by ID.

        Args:
            collection: Collection name
            record_id: Record ID

        Returns:
            Record object

        Raises:
            ClientResponseError: If record not found
        """
        return self.client.collection(collection).get_one(record_id)

    def get_list(
        self,
        collection: str,
        page: int = 1,
        per_page: int = 50,
        filter: Optional[str] = None,
        sort: Optional[str] = None,
    ) -> List[Record]:
        """
        Get paginated list of records.

        Args:
            collection: Collection name
            page: Page number (1-indexed)
            per_page: Records per page
            filter: PocketBase filter expression
            sort: Sort expression (e.g., "-created", "+name")

        Returns:
            List of records
        """
        result = self.client.collection(collection).get_list(
            page=page, per_page=per_page, query_params={"filter": filter, "sort": sort}
        )
        return list(result.items)

    def get_full_list(
        self, collection: str, filter: Optional[str] = None, sort: Optional[str] = None
    ) -> List[Record]:
        """
        Get all records from a collection (auto-paginated).

        Args:
            collection: Collection name
            filter: PocketBase filter expression
            sort: Sort expression

        Returns:
            List of all records
        """
        return self.client.collection(collection).get_full_list(
            query_params={"filter": filter, "sort": sort}
        )

    def get_first_list_item(
        self, collection: str, filter: str, sort: Optional[str] = None
    ) -> Record:
        """
        Get first record matching filter.

        Args:
            collection: Collection name
            filter: PocketBase filter expression
            sort: Sort expression

        Returns:
            First matching record

        Raises:
            ClientResponseError: If no records match
        """
        return self.client.collection(collection).get_first_list_item(
            filter, query_params={"sort": sort}
        )

    def update(self, collection: str, record_id: str, data: Dict[str, Any]) -> Record:
        """
        Update a record.

        Args:
            collection: Collection name
            record_id: Record ID
            data: Fields to update

        Returns:
            Updated record

        Raises:
            ClientResponseError: If update fails
        """
        return self.client.collection(collection).update(record_id, data)

    def delete(self, collection: str, record_id: str) -> bool:
        """
        Delete a record.

        Args:
            collection: Collection name
            record_id: Record ID

        Returns:
            True if deleted

        Raises:
            ClientResponseError: If deletion fails
        """
        return self.client.collection(collection).delete(record_id)

    # Utility methods

    def exists(self, collection: str, filter: str) -> bool:
        """
        Check if any record matches filter.

        Args:
            collection: Collection name
            filter: PocketBase filter expression

        Returns:
            True if at least one record matches
        """
        try:
            self.get_first_list_item(collection, filter)
            return True
        except ClientResponseError as e:
            if e.status == 404:
                return False
            raise

    def count(self, collection: str, filter: Optional[str] = None) -> int:
        """
        Count records in collection.

        Args:
            collection: Collection name
            filter: Optional filter expression

        Returns:
            Number of records
        """
        result = self.client.collection(collection).get_list(
            page=1, per_page=1, query_params={"filter": filter}
        )
        return result.total_items

    # Collection-specific helpers

    def get_setting(self, key: str) -> Any:
        """
        Get a setting value by key.

        Args:
            key: Setting key

        Returns:
            Setting value (parsed based on type)

        Raises:
            ClientResponseError: If setting not found
        """
        record = self.get_first_list_item(self.COLLECTION_SETTINGS, f'key="{key}"')
        value = record.value
        type_str = record.type

        # Parse based on type
        if type_str == "number":
            try:
                return int(value)
            except ValueError:
                return float(value)
        elif type_str == "boolean":
            return value.lower() in ("true", "1", "yes", "on")
        else:
            return value

    def update_setting(self, key: str, value: Any) -> Record:
        """
        Update a setting value.

        Args:
            key: Setting key
            value: New value

        Returns:
            Updated setting record
        """
        record = self.get_first_list_item(self.COLLECTION_SETTINGS, f'key="{key}"')
        return self.update(self.COLLECTION_SETTINGS, record.id, {"value": str(value)})

    def create_raw_event(
        self,
        source: str,
        source_id: str,
        timestamp: datetime,
        duration_minutes: int,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Record:
        """
        Create a raw event record.

        Args:
            source: Source name (wakatime, calendar, gmail, github, cloud_events)
            source_id: Unique ID from source
            timestamp: Event timestamp
            duration_minutes: Duration in minutes
            description: Event description
            metadata: Additional metadata as JSON

        Returns:
            Created raw_events record
        """
        return self.create(
            self.COLLECTION_RAW_EVENTS,
            {
                "source": source,
                "source_id": source_id,
                "timestamp": timestamp.isoformat(),
                "duration_minutes": duration_minutes,
                "description": description,
                "metadata": metadata or {},
            },
        )

    def get_raw_events_by_source(
        self, source: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Record]:
        """
        Get raw events from a specific source within date range.

        Args:
            source: Source name
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of raw event records
        """
        filters = [f'source="{source}"']

        if start_date:
            filters.append(f'timestamp>="{start_date.isoformat()}"')
        if end_date:
            filters.append(f'timestamp<="{end_date.isoformat()}"')

        filter_str = " && ".join(filters)
        return self.get_full_list(self.COLLECTION_RAW_EVENTS, filter=filter_str, sort="+timestamp")

    def get_raw_events_for_week(
        self, week_start: datetime, week_end: datetime
    ) -> List[Record]:
        """
        Get all raw events for a work week.

        Args:
            week_start: Start of work week
            week_end: End of work week

        Returns:
            List of raw event records
        """
        filter_str = f'timestamp>="{week_start.isoformat()}" && timestamp<="{week_end.isoformat()}"'
        return self.get_full_list(self.COLLECTION_RAW_EVENTS, filter=filter_str, sort="+timestamp")

    def create_time_block(
        self,
        week_start: datetime,
        block_start: datetime,
        block_end: datetime,
        source: str,
        description: str,
        duration_hours: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Record:
        """
        Create a time block record.

        Args:
            week_start: Start of the work week
            block_start: Start of time block
            block_end: End of time block
            source: Source name
            description: Block description
            duration_hours: Duration in hours
            metadata: Additional metadata as JSON

        Returns:
            Created time_blocks record
        """
        return self.create(
            self.COLLECTION_TIME_BLOCKS,
            {
                "week_start": week_start.isoformat(),
                "block_start": block_start.isoformat(),
                "block_end": block_end.isoformat(),
                "source": source,
                "description": description,
                "duration_hours": duration_hours,
                "metadata": metadata or {},
            },
        )

    def get_time_blocks_for_week(self, week_start: datetime) -> List[Record]:
        """
        Get all time blocks for a specific week.

        Args:
            week_start: Start of the work week

        Returns:
            List of time block records sorted by block_start
        """
        filter_str = f'week_start="{week_start.isoformat()}"'
        return self.get_full_list(
            self.COLLECTION_TIME_BLOCKS, filter=filter_str, sort="+block_start"
        )

    def get_or_create_week_summary(
        self,
        week_start: datetime,
        total_hours: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Record:
        """
        Get or create week summary record.

        Args:
            week_start: Start of the work week
            total_hours: Total hours for the week
            metadata: Additional metadata as JSON

        Returns:
            Week summary record
        """
        filter_str = f'week_start="{week_start.isoformat()}"'

        try:
            record = self.get_first_list_item(self.COLLECTION_WEEK_SUMMARIES, filter_str)
            # Update existing record
            return self.update(
                self.COLLECTION_WEEK_SUMMARIES,
                record.id,
                {
                    "total_hours": total_hours,
                    "metadata": metadata or {},
                },
            )
        except ClientResponseError as e:
            if e.status == 404:
                # Create new summary
                return self.create(
                    self.COLLECTION_WEEK_SUMMARIES,
                    {
                        "week_start": week_start.isoformat(),
                        "total_hours": total_hours,
                        "metadata": metadata or {},
                    },
                )
            raise

