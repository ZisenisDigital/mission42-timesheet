"""
Claude Code Data Fetcher

Fetches Claude Code AI assistant usage from claude_time_tracking collection.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from app.services.fetchers.base import BaseFetcher, FetchResult
from app.pocketbase_client import PocketBaseClient

logger = logging.getLogger(__name__)


class ClaudeCodeFetcher(BaseFetcher):
    """
    Fetches Claude Code AI assistant usage from claude_time_tracking collection.

    Converts tracking records to raw_events with smart description generation.
    """

    def __init__(self, pb_client: PocketBaseClient):
        """
        Initialize Claude Code fetcher.

        Args:
            pb_client: PocketBase client instance
        """
        super().__init__(pb_client)
        self.source_name = "cloud_events"

    def validate(self) -> bool:
        """
        Validate fetcher configuration.

        Returns:
            True if valid, False otherwise
        """
        # Check if claude_time_tracking collection is accessible
        try:
            self.pb_client.count("claude_time_tracking")
            return True
        except Exception as e:
            logger.error(f"Failed to access claude_time_tracking collection: {str(e)}")
            return False

    def fetch(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> FetchResult:
        """
        Fetch Claude Code tracking data.

        Args:
            start_date: Start date for fetch (defaults to 7 days ago)
            end_date: End date for fetch (defaults to now)

        Returns:
            FetchResult with statistics
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=7)
        if end_date is None:
            end_date = datetime.now()

        logger.info(
            f"Fetching Claude Code data from {start_date.isoformat()} to {end_date.isoformat()}"
        )

        try:
            # Fetch tracking records
            tracking_records = self._fetch_tracking_records(start_date, end_date)

            # Process and create raw events
            events_created = 0
            for record in tracking_records:
                event_data = self._process_tracking_record(record)
                if event_data:
                    created = self.create_or_update_raw_event(**event_data)
                    if created:
                        events_created += 1

            logger.info(
                f"Claude Code fetch complete: {len(tracking_records)} fetched, {events_created} created"
            )

            return FetchResult(
                success=True,
                events_fetched=len(tracking_records),
                events_created=events_created,
            )

        except Exception as e:
            logger.error(f"Claude Code fetch failed: {str(e)}", exc_info=True)
            return FetchResult(success=False, error=str(e))

    def _fetch_tracking_records(
        self, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Fetch tracking records from claude_time_tracking collection.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            List of tracking records as dicts
        """
        # Build filter for date range
        filter_str = f'started_at>="{start_date.isoformat()}" && started_at<="{end_date.isoformat()}"'

        # Fetch records
        records = self.pb_client.get_full_list(
            "claude_time_tracking", filter=filter_str, sort="+started_at"
        )

        # Convert Record objects to dicts
        records_list = []
        for record in records:
            if hasattr(record, "__dict__"):
                record_dict = {
                    k: v for k, v in record.__dict__.items() if not k.startswith("_")
                }
            else:
                record_dict = dict(record)
            records_list.append(record_dict)

        return records_list

    def _process_tracking_record(
        self, record: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Process a tracking record into raw event data.

        Args:
            record: Tracking record dict

        Returns:
            Event data dict or None if invalid
        """
        # Extract fields
        session_id = record.get("session_id") or record.get("id")
        tool_name = record.get("tool_name", "")
        description_raw = record.get("description", "")
        started_at = record.get("started_at")
        completed_at = record.get("completed_at")
        duration = record.get("duration")  # Duration in seconds
        status = record.get("status", "")
        topic = record.get("topic", "")
        project = record.get("project", "")

        # Parse timestamps
        if isinstance(started_at, str):
            try:
                started_at = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                logger.warning(f"Invalid started_at timestamp: {started_at}")
                return None
        elif not isinstance(started_at, datetime):
            logger.warning(f"Invalid started_at type: {type(started_at)}")
            return None

        if completed_at:
            if isinstance(completed_at, str):
                try:
                    completed_at = datetime.fromisoformat(
                        completed_at.replace("Z", "+00:00")
                    )
                except (ValueError, AttributeError):
                    completed_at = None

        # Calculate duration
        duration_minutes = 0
        if duration and duration > 0:
            # Duration is in seconds
            duration_minutes = duration / 60.0
        elif completed_at and isinstance(completed_at, datetime):
            # Calculate from timestamps
            duration_minutes = (completed_at - started_at).total_seconds() / 60.0
        else:
            # No duration or completion time - skip
            logger.debug(f"Skipping record {session_id}: no duration")
            return None

        # Skip if duration is too short (< 1 minute)
        if duration_minutes < 1:
            logger.debug(f"Skipping record {session_id}: duration too short")
            return None

        # Generate smart description
        description = self._generate_description(
            project, topic, tool_name, description_raw
        )

        # Create event data
        event_data = {
            "source_id": str(session_id),
            "timestamp": started_at,
            "duration_minutes": int(round(duration_minutes)),
            "description": description,
            "metadata": {
                "tool_name": tool_name,
                "topic": topic,
                "project": project,
                "status": status,
                "raw_description": description_raw,
            },
        }

        return event_data

    def _generate_description(
        self,
        project: str,
        topic: str,
        tool_name: str,
        description_raw: str,
    ) -> str:
        """
        Generate smart description from available fields.

        Args:
            project: Project name
            topic: Topic/task name
            tool_name: Tool used
            description_raw: Raw description

        Returns:
            Generated description
        """
        # Priority: project + topic > project > topic > tool_name > raw description
        if project and topic:
            return f"Claude Code: {project} - {topic}"
        elif project:
            return f"Claude Code: {project}"
        elif topic:
            return f"Claude Code: {topic}"
        elif tool_name:
            return f"Claude Code: {tool_name}"
        elif description_raw:
            # Truncate to first 100 chars
            truncated = description_raw[:100]
            if len(description_raw) > 100:
                truncated += "..."
            return f"Claude Code: {truncated}"
        else:
            return "Claude Code: AI Development"
