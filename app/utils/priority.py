"""
Priority System

Defines priorities for different data sources and provides utilities for
conflict resolution when time blocks overlap.
"""

from enum import IntEnum
from typing import List, Tuple
from datetime import datetime


class SourcePriority(IntEnum):
    """
    Priority levels for different data sources.

    Higher values = higher priority.
    When time blocks overlap, the highest priority source wins.
    """

    # Highest priority: WakaTime (ground truth for coding time)
    WAKATIME = 100

    # High priority: Calendar meetings (scheduled commitments)
    CALENDAR = 80

    # Medium-high priority: Gmail sent emails (client communication)
    GMAIL = 60

    # Lower priority: GitHub activity (may overlap with WakaTime)
    GITHUB = 40

    # Lower priority: Cloud events (user-defined events)
    CLOUD_EVENTS = 40

    # Lowest priority: Auto-filled hours
    AUTO_FILL = 0


# Source name mappings
SOURCE_WAKATIME = "wakatime"
SOURCE_CALENDAR = "calendar"
SOURCE_GMAIL = "gmail"
SOURCE_GITHUB = "github"
SOURCE_CLOUD_EVENTS = "cloud_events"
SOURCE_AUTO_FILL = "auto_fill"

# Map source names to priorities
SOURCE_PRIORITIES = {
    SOURCE_WAKATIME: SourcePriority.WAKATIME,
    SOURCE_CALENDAR: SourcePriority.CALENDAR,
    SOURCE_GMAIL: SourcePriority.GMAIL,
    SOURCE_GITHUB: SourcePriority.GITHUB,
    SOURCE_CLOUD_EVENTS: SourcePriority.CLOUD_EVENTS,
    SOURCE_AUTO_FILL: SourcePriority.AUTO_FILL,
}


def get_source_priority(source: str) -> int:
    """
    Get priority value for a data source.

    Args:
        source: Source name (wakatime, calendar, gmail, github, cloud_events, auto_fill)

    Returns:
        Priority value (0-100)

    Raises:
        ValueError: If source is unknown
    """
    if source not in SOURCE_PRIORITIES:
        raise ValueError(f"Unknown source: {source}")

    return SOURCE_PRIORITIES[source]


def get_highest_priority_source(sources: List[str]) -> str:
    """
    Get the highest priority source from a list.

    Args:
        sources: List of source names

    Returns:
        Highest priority source name

    Raises:
        ValueError: If sources list is empty or contains unknown sources
    """
    if not sources:
        raise ValueError("Sources list cannot be empty")

    return max(sources, key=get_source_priority)


def times_overlap(
    start1: datetime, end1: datetime, start2: datetime, end2: datetime
) -> bool:
    """
    Check if two time ranges overlap.

    Args:
        start1: Start of first range
        end1: End of first range
        start2: Start of second range
        end2: End of second range

    Returns:
        True if ranges overlap

    Examples:
        >>> from datetime import datetime
        >>> start1 = datetime(2026, 1, 6, 10, 0)
        >>> end1 = datetime(2026, 1, 6, 11, 0)
        >>> start2 = datetime(2026, 1, 6, 10, 30)
        >>> end2 = datetime(2026, 1, 6, 11, 30)
        >>> times_overlap(start1, end1, start2, end2)
        True
    """
    return start1 < end2 and start2 < end1


class TimeBlock:
    """Represents a time block with source and priority"""

    def __init__(
        self,
        start: datetime,
        end: datetime,
        source: str,
        description: str,
        metadata: dict = None,
    ):
        self.start = start
        self.end = end
        self.source = source
        self.description = description
        self.priority = get_source_priority(source)
        self.metadata = metadata or {}

    def overlaps_with(self, other: "TimeBlock") -> bool:
        """Check if this block overlaps with another"""
        return times_overlap(self.start, self.end, other.start, other.end)

    def duration_minutes(self) -> float:
        """Get duration in minutes"""
        return (self.end - self.start).total_seconds() / 60

    def __repr__(self) -> str:
        return (
            f"TimeBlock(start={self.start.isoformat()}, end={self.end.isoformat()}, "
            f"source={self.source}, priority={self.priority})"
        )


def resolve_overlaps(blocks: List[TimeBlock], strategy: str = "priority") -> List[TimeBlock]:
    """
    Resolve overlapping time blocks according to strategy.

    Args:
        blocks: List of TimeBlock objects
        strategy: Resolution strategy:
            - "priority": Keep only highest priority block (default)
            - "show_both": Keep all overlapping blocks
            - "combine": Merge descriptions of overlapping blocks

    Returns:
        List of resolved TimeBlock objects

    Note:
        - "priority" strategy: When blocks overlap, only the highest priority survives
        - "show_both" strategy: All blocks are kept (may result in double-counting hours)
        - "combine" strategy: Overlapping blocks merged with combined descriptions
    """
    if not blocks:
        return []

    # Sort by start time, then by priority (highest first)
    sorted_blocks = sorted(blocks, key=lambda b: (b.start, -b.priority))

    if strategy == "show_both":
        # Keep all blocks
        return sorted_blocks

    elif strategy == "priority":
        # Keep only highest priority blocks, remove overlaps
        result = []

        for block in sorted_blocks:
            # Check if this block overlaps with any already in result
            overlaps = False
            for existing in result:
                if block.overlaps_with(existing):
                    # Keep the higher priority one
                    if block.priority > existing.priority:
                        # Replace existing with current
                        result.remove(existing)
                        result.append(block)
                    overlaps = True
                    break

            if not overlaps:
                result.append(block)

        return sorted(result, key=lambda b: b.start)

    elif strategy == "combine":
        # Combine overlapping blocks
        if not blocks:
            return []

        result = []
        current_group = [sorted_blocks[0]]

        for block in sorted_blocks[1:]:
            # Check if block overlaps with any in current group
            overlaps = any(block.overlaps_with(b) for b in current_group)

            if overlaps:
                current_group.append(block)
            else:
                # Process current group
                if len(current_group) == 1:
                    result.append(current_group[0])
                else:
                    # Merge group
                    merged = merge_blocks(current_group)
                    result.append(merged)

                # Start new group
                current_group = [block]

        # Process final group
        if len(current_group) == 1:
            result.append(current_group[0])
        else:
            merged = merge_blocks(current_group)
            result.append(merged)

        return result

    else:
        raise ValueError(f"Unknown strategy: {strategy}")


def merge_blocks(blocks: List[TimeBlock]) -> TimeBlock:
    """
    Merge multiple overlapping blocks into one.

    Takes the earliest start, latest end, highest priority, and combines descriptions.

    Args:
        blocks: List of TimeBlock objects to merge

    Returns:
        Merged TimeBlock
    """
    if not blocks:
        raise ValueError("Cannot merge empty list of blocks")

    if len(blocks) == 1:
        return blocks[0]

    # Get time range
    start = min(b.start for b in blocks)
    end = max(b.end for b in blocks)

    # Get highest priority block
    highest_priority_block = max(blocks, key=lambda b: b.priority)

    # Combine descriptions
    descriptions = [f"{b.source}: {b.description}" for b in blocks]
    combined_description = " | ".join(descriptions)

    return TimeBlock(
        start=start,
        end=end,
        source=highest_priority_block.source,
        description=combined_description,
        metadata={"merged_from": [b.source for b in blocks]},
    )


def filter_by_priority(blocks: List[TimeBlock], min_priority: int) -> List[TimeBlock]:
    """
    Filter blocks by minimum priority.

    Args:
        blocks: List of TimeBlock objects
        min_priority: Minimum priority threshold

    Returns:
        Filtered list of blocks
    """
    return [b for b in blocks if b.priority >= min_priority]


def group_by_source(blocks: List[TimeBlock]) -> dict[str, List[TimeBlock]]:
    """
    Group time blocks by source.

    Args:
        blocks: List of TimeBlock objects

    Returns:
        Dictionary mapping source names to lists of blocks
    """
    groups: dict[str, List[TimeBlock]] = {}

    for block in blocks:
        if block.source not in groups:
            groups[block.source] = []
        groups[block.source].append(block)

    return groups


def calculate_priority_stats(blocks: List[TimeBlock]) -> dict[str, float]:
    """
    Calculate hours contributed by each source.

    Args:
        blocks: List of TimeBlock objects

    Returns:
        Dictionary mapping source names to total hours
    """
    stats: dict[str, float] = {}

    for block in blocks:
        if block.source not in stats:
            stats[block.source] = 0.0
        stats[block.source] += block.duration_minutes() / 60.0

    return stats
