"""
Time Block Processor

Processes raw events into 30-minute time blocks with priority-based overlap resolution.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from app.pocketbase_client import PocketBaseClient
from app.config import Config
from app.models.settings import Settings, RoundingMode, FillUpTopicMode, FillUpDistribution, OverlapHandling
from app.utils.time_utils import (
    get_work_week_start,
    get_work_week_end,
    is_within_work_week,
    round_to_half_hour,
    generate_time_blocks,
)
from app.utils.priority import (
    TimeBlock,
    resolve_overlaps,
    get_source_priority,
)


class ProcessingResult:
    """Result of week processing"""

    def __init__(
        self,
        success: bool,
        week_start: Optional[datetime] = None,
        week_end: Optional[datetime] = None,
        raw_events_count: int = 0,
        time_blocks_created: int = 0,
        total_hours: float = 0.0,
        hours_filled: float = 0.0,
        error: Optional[str] = None,
    ):
        self.success = success
        self.week_start = week_start
        self.week_end = week_end
        self.raw_events_count = raw_events_count
        self.time_blocks_created = time_blocks_created
        self.total_hours = total_hours
        self.hours_filled = hours_filled
        self.error = error


class TimeBlockProcessor:
    """
    Processes raw events into 30-minute time blocks.

    Handles:
    - Fetching raw events for a work week
    - Converting events to 30-minute blocks
    - Priority-based overlap resolution
    - Rounding to 0.5h increments
    - Auto-fill to target hours (40h minimum)
    - Saving to PocketBase
    """

    def __init__(self, pb_client: PocketBaseClient, config: Config):
        """
        Initialize Time Block Processor.

        Args:
            pb_client: PocketBase client instance
            config: Application configuration with settings
        """
        self.pb_client = pb_client
        self.config = config

    def fetch_raw_events_for_week(
        self, week_start: datetime, week_end: datetime
    ) -> List[Dict[str, Any]]:
        """
        Fetch all raw events for a work week.

        Args:
            week_start: Start of work week
            week_end: End of work week

        Returns:
            List of raw event records
        """
        # Fetch raw events from PocketBase
        raw_events = self.pb_client.get_raw_events_for_week(week_start, week_end)

        # Convert Record objects to dicts
        events_list = []
        for event in raw_events:
            if hasattr(event, "__dict__"):
                event_dict = {
                    k: v
                    for k, v in event.__dict__.items()
                    if not k.startswith("_")
                }
            else:
                event_dict = dict(event)
            events_list.append(event_dict)

        return events_list

    def convert_to_time_blocks(
        self, raw_events: List[Dict[str, Any]], settings: Settings
    ) -> List[TimeBlock]:
        """
        Convert raw events to time blocks with rounding.

        Args:
            raw_events: List of raw event records
            settings: Application settings

        Returns:
            List of TimeBlock objects
        """
        time_blocks = []

        for event in raw_events:
            # Get event data
            source = event.get("source", "unknown")
            timestamp = event.get("timestamp")
            duration_minutes = event.get("duration_minutes", 0)
            description = event.get("description", "")
            metadata = event.get("metadata", {})

            # Parse timestamp
            if isinstance(timestamp, str):
                try:
                    if "T" in timestamp:
                        timestamp = datetime.fromisoformat(
                            timestamp.replace("Z", "+00:00")
                        )
                    else:
                        timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                except (ValueError, AttributeError):
                    continue
            elif not isinstance(timestamp, datetime):
                continue

            # Skip events with no duration
            if duration_minutes <= 0:
                continue

            # Round duration to 0.5h increments
            rounding_mode = settings.processing.rounding_mode
            if rounding_mode == RoundingMode.UP:
                from app.utils.time_utils import RoundingMode as TimeUtilsRoundingMode

                rounded_hours = round_to_half_hour(
                    duration_minutes, TimeUtilsRoundingMode.UP
                )
            else:  # NEAREST
                from app.utils.time_utils import RoundingMode as TimeUtilsRoundingMode

                rounded_hours = round_to_half_hour(
                    duration_minutes, TimeUtilsRoundingMode.NEAREST
                )

            # Calculate end time
            end_time = timestamp + timedelta(hours=rounded_hours)

            # Create TimeBlock (priority is auto-determined from source)
            block = TimeBlock(
                start=timestamp,
                end=end_time,
                source=source,
                description=description,
                metadata=metadata,
            )

            time_blocks.append(block)

        return time_blocks

    def resolve_overlapping_blocks(
        self, time_blocks: List[TimeBlock], settings: Settings
    ) -> List[TimeBlock]:
        """
        Resolve overlapping time blocks using priority system.

        Args:
            time_blocks: List of TimeBlock objects
            settings: Application settings

        Returns:
            List of resolved TimeBlock objects
        """
        overlap_strategy = settings.processing.overlap_handling

        # Map settings enum to priority.py strategy strings
        if overlap_strategy == OverlapHandling.PRIORITY:
            strategy = "priority"
        elif overlap_strategy == OverlapHandling.SHOW_BOTH:
            strategy = "show_both"
        elif overlap_strategy == OverlapHandling.COMBINE:
            strategy = "combine"
        else:
            strategy = "priority"  # Default

        return resolve_overlaps(time_blocks, strategy=strategy)

    def group_activities(
        self, time_blocks: List[TimeBlock], settings: Settings
    ) -> List[TimeBlock]:
        """
        Group same activities on the same day if enabled.

        Args:
            time_blocks: List of TimeBlock objects
            settings: Application settings

        Returns:
            List of TimeBlock objects (grouped if enabled)
        """
        if not settings.processing.group_same_activities:
            return time_blocks

        # Group by date, source, and description
        grouped: Dict[Tuple[str, str, str], List[TimeBlock]] = defaultdict(list)

        for block in time_blocks:
            date_key = block.start.date().isoformat()
            group_key = (date_key, block.source, block.description)
            grouped[group_key].append(block)

        # Merge grouped blocks
        merged_blocks = []
        for blocks in grouped.values():
            if len(blocks) == 1:
                merged_blocks.append(blocks[0])
            else:
                # Merge multiple blocks into one
                first_block = blocks[0]
                total_duration = sum(
                    (b.end - b.start).total_seconds() / 3600 for b in blocks
                )

                # Use earliest start time
                earliest_start = min(b.start for b in blocks)
                merged_end = earliest_start + timedelta(hours=total_duration)

                # Merge metadata
                merged_metadata = {}
                for block in blocks:
                    merged_metadata.update(block.metadata)

                merged_block = TimeBlock(
                    start=earliest_start,
                    end=merged_end,
                    source=first_block.source,
                    description=first_block.description,
                    metadata=merged_metadata,
                )
                merged_blocks.append(merged_block)

        return sorted(merged_blocks, key=lambda b: b.start)

    def calculate_week_hours(self, time_blocks: List[TimeBlock]) -> float:
        """
        Calculate total hours from time blocks.

        Args:
            time_blocks: List of TimeBlock objects

        Returns:
            Total hours (float)
        """
        total_hours = 0.0
        for block in time_blocks:
            duration_hours = (block.end - block.start).total_seconds() / 3600
            total_hours += duration_hours

        return total_hours

    def auto_fill_to_target(
        self,
        time_blocks: List[TimeBlock],
        week_start: datetime,
        week_end: datetime,
        settings: Settings,
    ) -> Tuple[List[TimeBlock], float]:
        """
        Auto-fill to target hours (40h minimum).

        Args:
            time_blocks: List of existing TimeBlock objects
            week_start: Start of work week
            week_end: End of work week
            settings: Application settings

        Returns:
            Tuple of (updated time blocks, hours filled)
        """
        # Check if auto-fill is enabled
        if not settings.core.auto_fill_enabled:
            return time_blocks, 0.0

        # Calculate current hours
        current_hours = self.calculate_week_hours(time_blocks)
        target_hours = settings.core.target_hours_per_week

        # If already at or above target, no fill needed
        if current_hours >= target_hours:
            return time_blocks, 0.0

        # Calculate hours to fill
        hours_to_fill = target_hours - current_hours

        # Determine fill-up topic
        fill_up_topic = self._determine_fill_up_topic(time_blocks, settings)

        # Create fill-up blocks based on distribution strategy
        fill_blocks = self._create_fill_up_blocks(
            hours_to_fill,
            week_start,
            week_end,
            time_blocks,
            fill_up_topic,
            settings,
        )

        # Add fill blocks to existing blocks
        updated_blocks = time_blocks + fill_blocks

        return updated_blocks, hours_to_fill

    def _determine_fill_up_topic(
        self, time_blocks: List[TimeBlock], settings: Settings
    ) -> str:
        """
        Determine the topic for auto-fill blocks.

        Args:
            time_blocks: List of existing TimeBlock objects
            settings: Application settings

        Returns:
            Topic string
        """
        fill_up_mode = settings.processing.fill_up_topic_mode

        if fill_up_mode == FillUpTopicMode.MANUAL:
            # Use manually configured topic
            return settings.processing.fill_up_default_topic

        elif fill_up_mode == FillUpTopicMode.AUTO:
            # Auto-detect from most frequent description
            if not time_blocks:
                return settings.processing.fill_up_default_topic

            # Count description frequencies
            description_counts: Dict[str, float] = defaultdict(float)
            for block in time_blocks:
                duration_hours = (block.end - block.start).total_seconds() / 3600
                description_counts[block.description] += duration_hours

            # Get most frequent
            if description_counts:
                most_frequent = max(description_counts.items(), key=lambda x: x[1])
                return most_frequent[0]
            else:
                return settings.processing.fill_up_default_topic

        else:  # GENERIC
            return settings.processing.fill_up_default_topic

    def _create_fill_up_blocks(
        self,
        hours_to_fill: float,
        week_start: datetime,
        week_end: datetime,
        existing_blocks: List[TimeBlock],
        topic: str,
        settings: Settings,
    ) -> List[TimeBlock]:
        """
        Create fill-up blocks based on distribution strategy.

        Args:
            hours_to_fill: Number of hours to fill
            week_start: Start of work week
            week_end: End of work week
            existing_blocks: List of existing TimeBlock objects
            topic: Topic for fill-up blocks
            settings: Application settings

        Returns:
            List of fill-up TimeBlock objects
        """
        distribution = settings.processing.fill_up_distribution
        fill_blocks = []

        if distribution == FillUpDistribution.END_OF_WEEK:
            # Add all hours at end of week (Saturday afternoon)
            # Place at Saturday 12:00 PM
            saturday = week_end - timedelta(hours=6)  # 6 hours before week end (6 PM)
            fill_start = saturday.replace(hour=12, minute=0, second=0)
            fill_end = fill_start + timedelta(hours=hours_to_fill)

            fill_block = TimeBlock(
                start=fill_start,
                end=fill_end,
                source="auto_fill",
                description=f"Development: {topic}",
                metadata={"auto_generated": True, "fill_hours": hours_to_fill},
            )
            fill_blocks.append(fill_block)

        elif distribution == FillUpDistribution.DISTRIBUTED:
            # Distribute evenly across work days
            work_days = []
            current_day = week_start
            while current_day < week_end:
                work_days.append(current_day)
                current_day += timedelta(days=1)

            hours_per_day = hours_to_fill / len(work_days)

            for day in work_days:
                # Place at 5 PM each day
                fill_start = day.replace(hour=17, minute=0, second=0)
                fill_end = fill_start + timedelta(hours=hours_per_day)

                fill_block = TimeBlock(
                    start=fill_start,
                    end=fill_end,
                    source="auto_fill",
                    description=f"Development: {topic}",
                    metadata={
                        "auto_generated": True,
                        "fill_hours": hours_per_day,
                        "distributed": True,
                    },
                )
                fill_blocks.append(fill_block)

        else:  # EMPTY_SLOTS
            # Fill in empty time slots during work hours (9 AM - 5 PM)
            # This is more complex - for now, use end_of_week strategy
            # TODO: Implement proper empty slot detection
            fill_start = week_end - timedelta(hours=hours_to_fill)
            fill_end = week_end

            fill_block = TimeBlock(
                start=fill_start,
                end=fill_end,
                source="auto_fill",
                description=f"Development: {topic}",
                metadata={"auto_generated": True, "fill_hours": hours_to_fill},
            )
            fill_blocks.append(fill_block)

        return fill_blocks

    def save_time_blocks(
        self, time_blocks: List[TimeBlock], week_start: datetime
    ) -> int:
        """
        Save time blocks to PocketBase.

        Args:
            time_blocks: List of TimeBlock objects
            week_start: Start of work week

        Returns:
            Number of blocks saved
        """
        saved_count = 0

        for block in time_blocks:
            # Create time block record
            self.pb_client.create_time_block(
                week_start=week_start,
                block_start=block.start,
                block_end=block.end,
                source=block.source,
                description=block.description,
                duration_hours=(block.end - block.start).total_seconds() / 3600,
                metadata=block.metadata,
            )
            saved_count += 1

        return saved_count

    def update_week_summary(
        self,
        week_start: datetime,
        week_end: datetime,
        total_hours: float,
        hours_filled: float,
    ) -> None:
        """
        Create or update week summary.

        Args:
            week_start: Start of work week
            week_end: End of work week
            total_hours: Total hours for the week
            hours_filled: Hours filled by auto-fill
        """
        metadata = {
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "hours_filled": hours_filled,
        }

        self.pb_client.get_or_create_week_summary(
            week_start=week_start,
            total_hours=total_hours,
            metadata=metadata,
        )

    def process_week(
        self, reference_date: Optional[datetime] = None
    ) -> ProcessingResult:
        """
        Process raw events for a week into time blocks.

        Main orchestration method that:
        1. Fetches raw events for the week
        2. Converts to time blocks
        3. Resolves overlaps
        4. Groups activities (if enabled)
        5. Calculates hours and auto-fills to target
        6. Saves to PocketBase
        7. Updates week summary

        Args:
            reference_date: Date within the week to process (defaults to now)

        Returns:
            ProcessingResult with success status and statistics
        """
        try:
            # Use current time if no reference date provided
            if reference_date is None:
                reference_date = datetime.now()

            # Get settings
            settings = self.config.settings

            # Calculate work week boundaries
            week_start = get_work_week_start(
                reference_date,
                settings.core.work_week_start_day.value,
                settings.core.work_week_start_time,
            )
            week_end = get_work_week_end(
                week_start,
                settings.core.work_week_end_day.value,
                settings.core.work_week_end_time,
            )

            # 1. Fetch raw events
            raw_events = self.fetch_raw_events_for_week(week_start, week_end)

            # 2. Convert to time blocks
            time_blocks = self.convert_to_time_blocks(raw_events, settings)

            # 3. Resolve overlaps
            time_blocks = self.resolve_overlapping_blocks(time_blocks, settings)

            # 4. Group activities (if enabled)
            time_blocks = self.group_activities(time_blocks, settings)

            # 5. Calculate hours and auto-fill
            time_blocks, hours_filled = self.auto_fill_to_target(
                time_blocks, week_start, week_end, settings
            )

            # Calculate total hours
            total_hours = self.calculate_week_hours(time_blocks)

            # 6. Save time blocks
            blocks_saved = self.save_time_blocks(time_blocks, week_start)

            # 7. Update week summary
            self.update_week_summary(week_start, week_end, total_hours, hours_filled)

            return ProcessingResult(
                success=True,
                week_start=week_start,
                week_end=week_end,
                raw_events_count=len(raw_events),
                time_blocks_created=blocks_saved,
                total_hours=total_hours,
                hours_filled=hours_filled,
            )

        except Exception as e:
            return ProcessingResult(success=False, error=str(e))
