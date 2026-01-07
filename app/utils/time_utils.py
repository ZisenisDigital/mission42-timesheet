"""
Time Utilities

Provides utilities for time calculations, week boundaries, and 30-minute block rounding.
"""

from datetime import datetime, timedelta
from typing import Tuple
from enum import Enum


class DayOfWeek(Enum):
    """Days of the week"""
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class RoundingMode(Enum):
    """Time rounding modes"""
    UP = "up"  # Always round up to next 0.5h
    NEAREST = "nearest"  # Round to nearest 0.5h


def get_work_week_start(
    reference_date: datetime,
    start_day: str = "monday",
    start_time: str = "18:00",
) -> datetime:
    """
    Calculate the start of the work week for a given reference date.

    Work week definition: Monday 6 PM → Saturday 6 PM (default)

    Args:
        reference_date: Any date/time within the week
        start_day: Day of week when work week starts (lowercase)
        start_time: Time when work week starts (HH:MM format)

    Returns:
        Datetime representing the start of the work week

    Examples:
        >>> # For a date on Wednesday Jan 8, 2026 at 10:00 AM
        >>> ref = datetime(2026, 1, 8, 10, 0)
        >>> start = get_work_week_start(ref)  # Returns Monday Jan 6, 2026 at 18:00
    """
    # Map day names to weekday numbers
    day_map = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }

    start_weekday = day_map[start_day.lower()]

    # Parse start time
    hour, minute = map(int, start_time.split(":"))

    # Get current weekday (0=Monday, 6=Sunday)
    current_weekday = reference_date.weekday()
    current_hour = reference_date.hour
    current_minute = reference_date.minute

    # Calculate days to subtract to get to start day
    if current_weekday >= start_weekday:
        days_back = current_weekday - start_weekday
    else:
        days_back = 7 - (start_weekday - current_weekday)

    # If we're on the start day but before start time, go back a week
    if days_back == 0:
        current_time_minutes = current_hour * 60 + current_minute
        start_time_minutes = hour * 60 + minute
        if current_time_minutes < start_time_minutes:
            days_back = 7

    # Calculate week start
    week_start = reference_date - timedelta(days=days_back)
    week_start = week_start.replace(hour=hour, minute=minute, second=0, microsecond=0)

    return week_start


def get_work_week_end(
    week_start: datetime,
    end_day: str = "saturday",
    end_time: str = "18:00",
) -> datetime:
    """
    Calculate the end of the work week from its start.

    Args:
        week_start: Start of the work week
        end_day: Day of week when work week ends (lowercase)
        end_time: Time when work week ends (HH:MM format)

    Returns:
        Datetime representing the end of the work week

    Examples:
        >>> start = datetime(2026, 1, 6, 18, 0)  # Monday 6 PM
        >>> end = get_work_week_end(start)  # Returns Saturday Jan 11, 2026 at 18:00
    """
    # Map day names to weekday numbers
    day_map = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }

    start_weekday = week_start.weekday()
    end_weekday = day_map[end_day.lower()]

    # Calculate days to add
    if end_weekday > start_weekday:
        days_forward = end_weekday - start_weekday
    else:
        # End day is earlier in the week, so it's in the next week
        days_forward = 7 - start_weekday + end_weekday

    # Parse end time
    hour, minute = map(int, end_time.split(":"))

    # Calculate week end
    week_end = week_start + timedelta(days=days_forward)
    week_end = week_end.replace(hour=hour, minute=minute, second=0, microsecond=0)

    return week_end


def is_within_work_week(
    timestamp: datetime,
    week_start: datetime,
    week_end: datetime,
) -> bool:
    """
    Check if a timestamp falls within the work week.

    Args:
        timestamp: Timestamp to check
        week_start: Start of work week
        week_end: End of work week

    Returns:
        True if timestamp is within work week (inclusive)
    """
    return week_start <= timestamp <= week_end


def round_to_half_hour(minutes: float, mode: RoundingMode = RoundingMode.UP) -> float:
    """
    Round minutes to 0.5 hour increments.

    Args:
        minutes: Duration in minutes
        mode: Rounding mode (UP or NEAREST)

    Returns:
        Duration in hours, rounded to 0.5h increments

    Examples:
        >>> round_to_half_hour(10, RoundingMode.UP)    # 0.5
        >>> round_to_half_hour(35, RoundingMode.UP)    # 1.0
        >>> round_to_half_hour(20, RoundingMode.NEAREST)  # 0.5
        >>> round_to_half_hour(35, RoundingMode.NEAREST)  # 0.5
    """
    hours = minutes / 60.0

    if mode == RoundingMode.UP:
        # Always round up to next 0.5h
        import math

        return math.ceil(hours * 2) / 2
    else:  # NEAREST
        # Round to nearest 0.5h
        return round(hours * 2) / 2


def minutes_to_hours(minutes: float, round_mode: RoundingMode = RoundingMode.UP) -> float:
    """
    Convert minutes to hours with rounding.

    Args:
        minutes: Duration in minutes
        round_mode: Rounding mode

    Returns:
        Duration in hours (rounded to 0.5h)
    """
    return round_to_half_hour(minutes, round_mode)


def duration_to_minutes(start: datetime, end: datetime) -> float:
    """
    Calculate duration in minutes between two timestamps.

    Args:
        start: Start timestamp
        end: End timestamp

    Returns:
        Duration in minutes
    """
    delta = end - start
    return delta.total_seconds() / 60


def duration_to_hours(
    start: datetime, end: datetime, round_mode: RoundingMode = RoundingMode.UP
) -> float:
    """
    Calculate duration in hours between two timestamps with rounding.

    Args:
        start: Start timestamp
        end: End timestamp
        round_mode: Rounding mode

    Returns:
        Duration in hours (rounded to 0.5h)
    """
    minutes = duration_to_minutes(start, end)
    return round_to_half_hour(minutes, round_mode)


def generate_time_blocks(
    start: datetime, end: datetime, block_size_minutes: int = 30
) -> list[Tuple[datetime, datetime]]:
    """
    Generate 30-minute time blocks between start and end times.

    Args:
        start: Start timestamp
        end: End timestamp
        block_size_minutes: Size of each block in minutes (default: 30)

    Returns:
        List of (block_start, block_end) tuples

    Examples:
        >>> start = datetime(2026, 1, 6, 18, 0)
        >>> end = datetime(2026, 1, 6, 19, 30)
        >>> blocks = generate_time_blocks(start, end)
        >>> len(blocks)  # 3 blocks: 18:00-18:30, 18:30-19:00, 19:00-19:30
        3
    """
    blocks = []
    current = start
    block_delta = timedelta(minutes=block_size_minutes)

    while current < end:
        block_end = min(current + block_delta, end)
        blocks.append((current, block_end))
        current = block_end

    return blocks


def align_to_block_boundary(timestamp: datetime, block_size_minutes: int = 30) -> datetime:
    """
    Align a timestamp to the nearest block boundary (round down).

    Args:
        timestamp: Timestamp to align
        block_size_minutes: Block size in minutes (default: 30)

    Returns:
        Aligned timestamp

    Examples:
        >>> dt = datetime(2026, 1, 6, 18, 17)
        >>> align_to_block_boundary(dt)  # Returns 18:00
        datetime(2026, 1, 6, 18, 0)
    """
    # Round down to nearest block
    minutes_since_midnight = timestamp.hour * 60 + timestamp.minute
    aligned_minutes = (minutes_since_midnight // block_size_minutes) * block_size_minutes

    return timestamp.replace(
        hour=aligned_minutes // 60, minute=aligned_minutes % 60, second=0, microsecond=0
    )


def get_week_range(
    reference_date: datetime,
    start_day: str = "monday",
    start_time: str = "18:00",
    end_day: str = "saturday",
    end_time: str = "18:00",
) -> Tuple[datetime, datetime]:
    """
    Get the start and end of the work week for a reference date.

    Args:
        reference_date: Any date/time within the week
        start_day: Day of week when work week starts
        start_time: Time when work week starts (HH:MM)
        end_day: Day of week when work week ends
        end_time: Time when work week ends (HH:MM)

    Returns:
        Tuple of (week_start, week_end)
    """
    week_start = get_work_week_start(reference_date, start_day, start_time)
    week_end = get_work_week_end(week_start, end_day, end_time)
    return (week_start, week_end)


def format_duration(hours: float) -> str:
    """
    Format duration in hours to human-readable string.

    Args:
        hours: Duration in hours

    Returns:
        Formatted string

    Examples:
        >>> format_duration(0.5)
        '0.5h'
        >>> format_duration(2.5)
        '2.5h'
        >>> format_duration(40)
        '40.0h'
    """
    return f"{hours}h"


def parse_time(time_str: str) -> Tuple[int, int]:
    """
    Parse time string in HH:MM format.

    Args:
        time_str: Time string (e.g., "18:00")

    Returns:
        Tuple of (hour, minute)

    Raises:
        ValueError: If format is invalid
    """
    try:
        hour, minute = map(int, time_str.split(":"))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
        return (hour, minute)
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid time format: {time_str}. Expected HH:MM")


def get_current_week_start(
    start_day: str = "monday", start_time: str = "18:00"
) -> datetime:
    """
    Get the start of the current work week.

    Args:
        start_day: Day of week when work week starts
        start_time: Time when work week starts (HH:MM)

    Returns:
        Start of current work week
    """
    return get_work_week_start(datetime.now(), start_day, start_time)


def calculate_weekly_hours(time_blocks: list[Tuple[datetime, datetime]]) -> float:
    """
    Calculate total hours from a list of time blocks.

    Args:
        time_blocks: List of (start, end) tuples

    Returns:
        Total hours
    """
    total_minutes = sum(duration_to_minutes(start, end) for start, end in time_blocks)
    return total_minutes / 60.0


def hours_to_blocks(hours: float, block_size_minutes: int = 30) -> int:
    """
    Convert hours to number of time blocks.

    Args:
        hours: Duration in hours
        block_size_minutes: Block size in minutes

    Returns:
        Number of blocks

    Examples:
        >>> hours_to_blocks(1.0)  # 1 hour = 2 blocks of 30 min
        2
        >>> hours_to_blocks(0.5)  # 0.5 hour = 1 block of 30 min
        1
    """
    minutes = hours * 60
    return int(minutes / block_size_minutes)


def blocks_to_hours(blocks: int, block_size_minutes: int = 30) -> float:
    """
    Convert number of blocks to hours.

    Args:
        blocks: Number of time blocks
        block_size_minutes: Block size in minutes

    Returns:
        Duration in hours

    Examples:
        >>> blocks_to_hours(2)  # 2 blocks = 1.0 hour
        1.0
        >>> blocks_to_hours(1)  # 1 block = 0.5 hour
        0.5
    """
    minutes = blocks * block_size_minutes
    return minutes / 60.0
