"""
Unit Tests for Time Utilities

Tests for time calculations, week boundaries, and 30-minute block rounding.
"""

import pytest
from datetime import datetime, timedelta
from app.utils.time_utils import (
    get_work_week_start,
    get_work_week_end,
    is_within_work_week,
    round_to_half_hour,
    minutes_to_hours,
    duration_to_minutes,
    duration_to_hours,
    generate_time_blocks,
    align_to_block_boundary,
    get_week_range,
    format_duration,
    parse_time,
    calculate_weekly_hours,
    hours_to_blocks,
    blocks_to_hours,
    RoundingMode,
)


class TestWorkWeekCalculations:
    """Test work week boundary calculations"""

    def test_get_work_week_start_monday_evening(self):
        """Test work week start calculation for Monday evening work week"""
        # Thursday Jan 8, 2026 at 10:00 AM
        ref_date = datetime(2026, 1, 8, 10, 0)
        week_start = get_work_week_start(ref_date, "monday", "18:00")

        # Should return Monday Jan 5, 2026 at 18:00
        assert week_start == datetime(2026, 1, 5, 18, 0)

    def test_get_work_week_start_on_start_day_before_time(self):
        """Test when reference is on start day but before start time"""
        # Monday Jan 5, 2026 at 10:00 AM (before 18:00)
        ref_date = datetime(2026, 1, 5, 10, 0)
        week_start = get_work_week_start(ref_date, "monday", "18:00")

        # Should go back to previous Monday (Dec 29, 2025)
        assert week_start == datetime(2025, 12, 29, 18, 0)

    def test_get_work_week_start_on_start_day_after_time(self):
        """Test when reference is on start day after start time"""
        # Monday Jan 5, 2026 at 20:00 (after 18:00)
        ref_date = datetime(2026, 1, 5, 20, 0)
        week_start = get_work_week_start(ref_date, "monday", "18:00")

        # Should return same Monday
        assert week_start == datetime(2026, 1, 5, 18, 0)

    def test_get_work_week_start_traditional_week(self):
        """Test traditional Monday 9 AM work week"""
        # Thursday Jan 8, 2026 at 14:00
        ref_date = datetime(2026, 1, 8, 14, 0)
        week_start = get_work_week_start(ref_date, "monday", "09:00")

        # Should return Monday Jan 5, 2026 at 09:00
        assert week_start == datetime(2026, 1, 5, 9, 0)

    def test_get_work_week_end(self):
        """Test work week end calculation"""
        # Monday Jan 5, 2026 at 18:00
        week_start = datetime(2026, 1, 5, 18, 0)
        week_end = get_work_week_end(week_start, "saturday", "18:00")

        # Should return Saturday Jan 10, 2026 at 18:00
        assert week_end == datetime(2026, 1, 10, 18, 0)

    def test_get_work_week_end_traditional(self):
        """Test traditional Friday 5 PM end"""
        week_start = datetime(2026, 1, 5, 9, 0)  # Monday 9 AM
        week_end = get_work_week_end(week_start, "friday", "17:00")

        # Should return Friday at 17:00
        assert week_end == datetime(2026, 1, 9, 17, 0)

    def test_is_within_work_week(self):
        """Test checking if timestamp is within work week"""
        week_start = datetime(2026, 1, 6, 18, 0)
        week_end = datetime(2026, 1, 11, 18, 0)

        # Within week
        assert is_within_work_week(datetime(2026, 1, 8, 10, 0), week_start, week_end)

        # Before week
        assert not is_within_work_week(datetime(2026, 1, 5, 10, 0), week_start, week_end)

        # After week
        assert not is_within_work_week(datetime(2026, 1, 12, 10, 0), week_start, week_end)

        # Exactly at boundaries
        assert is_within_work_week(week_start, week_start, week_end)
        assert is_within_work_week(week_end, week_start, week_end)

    def test_get_week_range(self):
        """Test getting week range in one call"""
        ref_date = datetime(2026, 1, 8, 10, 0)
        week_start, week_end = get_week_range(ref_date, "monday", "18:00", "saturday", "18:00")

        assert week_start == datetime(2026, 1, 5, 18, 0)
        assert week_end == datetime(2026, 1, 10, 18, 0)


class TestTimeRounding:
    """Test time rounding functions"""

    def test_round_up_basic(self):
        """Test rounding up to 0.5h"""
        assert round_to_half_hour(10, RoundingMode.UP) == 0.5
        assert round_to_half_hour(30, RoundingMode.UP) == 0.5
        assert round_to_half_hour(35, RoundingMode.UP) == 1.0
        assert round_to_half_hour(60, RoundingMode.UP) == 1.0
        assert round_to_half_hour(65, RoundingMode.UP) == 1.5

    def test_round_nearest_basic(self):
        """Test rounding to nearest 0.5h"""
        assert round_to_half_hour(10, RoundingMode.NEAREST) == 0.0
        assert round_to_half_hour(20, RoundingMode.NEAREST) == 0.5
        assert round_to_half_hour(35, RoundingMode.NEAREST) == 0.5
        assert round_to_half_hour(45, RoundingMode.NEAREST) == 1.0
        assert round_to_half_hour(50, RoundingMode.NEAREST) == 1.0

    def test_minutes_to_hours(self):
        """Test minutes to hours conversion"""
        assert minutes_to_hours(30, RoundingMode.UP) == 0.5
        assert minutes_to_hours(60, RoundingMode.UP) == 1.0
        assert minutes_to_hours(90, RoundingMode.UP) == 1.5


class TestDurationCalculations:
    """Test duration calculation functions"""

    def test_duration_to_minutes(self):
        """Test calculating duration in minutes"""
        start = datetime(2026, 1, 6, 10, 0)
        end = datetime(2026, 1, 6, 11, 0)
        assert duration_to_minutes(start, end) == 60.0

        end = datetime(2026, 1, 6, 10, 30)
        assert duration_to_minutes(start, end) == 30.0

    def test_duration_to_hours(self):
        """Test calculating duration in hours with rounding"""
        start = datetime(2026, 1, 6, 10, 0)
        end = datetime(2026, 1, 6, 11, 0)
        assert duration_to_hours(start, end, RoundingMode.UP) == 1.0

        end = datetime(2026, 1, 6, 10, 35)
        assert duration_to_hours(start, end, RoundingMode.UP) == 1.0


class TestTimeBlocks:
    """Test time block generation"""

    def test_generate_time_blocks(self):
        """Test generating 30-minute blocks"""
        start = datetime(2026, 1, 6, 10, 0)
        end = datetime(2026, 1, 6, 11, 30)

        blocks = generate_time_blocks(start, end, block_size_minutes=30)

        assert len(blocks) == 3
        assert blocks[0] == (datetime(2026, 1, 6, 10, 0), datetime(2026, 1, 6, 10, 30))
        assert blocks[1] == (datetime(2026, 1, 6, 10, 30), datetime(2026, 1, 6, 11, 0))
        assert blocks[2] == (datetime(2026, 1, 6, 11, 0), datetime(2026, 1, 6, 11, 30))

    def test_generate_time_blocks_partial(self):
        """Test generating blocks with partial last block"""
        start = datetime(2026, 1, 6, 10, 0)
        end = datetime(2026, 1, 6, 10, 45)

        blocks = generate_time_blocks(start, end, block_size_minutes=30)

        assert len(blocks) == 2
        assert blocks[0] == (datetime(2026, 1, 6, 10, 0), datetime(2026, 1, 6, 10, 30))
        assert blocks[1] == (datetime(2026, 1, 6, 10, 30), datetime(2026, 1, 6, 10, 45))

    def test_align_to_block_boundary(self):
        """Test aligning timestamp to block boundary"""
        # 10:17 should align to 10:00
        dt = datetime(2026, 1, 6, 10, 17)
        aligned = align_to_block_boundary(dt, block_size_minutes=30)
        assert aligned == datetime(2026, 1, 6, 10, 0)

        # 10:35 should align to 10:30
        dt = datetime(2026, 1, 6, 10, 35)
        aligned = align_to_block_boundary(dt, block_size_minutes=30)
        assert aligned == datetime(2026, 1, 6, 10, 30)

        # 10:00 should stay 10:00
        dt = datetime(2026, 1, 6, 10, 0)
        aligned = align_to_block_boundary(dt, block_size_minutes=30)
        assert aligned == datetime(2026, 1, 6, 10, 0)


class TestUtilityFunctions:
    """Test misc utility functions"""

    def test_format_duration(self):
        """Test duration formatting"""
        assert format_duration(0.5) == "0.5h"
        assert format_duration(2.5) == "2.5h"
        assert format_duration(40.0) == "40.0h"

    def test_parse_time_valid(self):
        """Test parsing valid time strings"""
        assert parse_time("18:00") == (18, 0)
        assert parse_time("09:30") == (9, 30)
        assert parse_time("00:00") == (0, 0)
        assert parse_time("23:59") == (23, 59)

    def test_parse_time_invalid(self):
        """Test parsing invalid time strings"""
        with pytest.raises(ValueError):
            parse_time("25:00")  # Invalid hour

        with pytest.raises(ValueError):
            parse_time("10:60")  # Invalid minute

        with pytest.raises(ValueError):
            parse_time("10-30")  # Wrong format

        with pytest.raises(ValueError):
            parse_time("abc")  # Not a time

    def test_calculate_weekly_hours(self):
        """Test calculating total hours from blocks"""
        blocks = [
            (datetime(2026, 1, 6, 10, 0), datetime(2026, 1, 6, 11, 0)),  # 1 hour
            (datetime(2026, 1, 6, 14, 0), datetime(2026, 1, 6, 15, 30)),  # 1.5 hours
        ]

        total = calculate_weekly_hours(blocks)
        assert total == 2.5

    def test_hours_to_blocks(self):
        """Test converting hours to number of blocks"""
        assert hours_to_blocks(1.0) == 2  # 1 hour = 2 x 30-min blocks
        assert hours_to_blocks(0.5) == 1  # 0.5 hour = 1 x 30-min block
        assert hours_to_blocks(2.5) == 5  # 2.5 hours = 5 x 30-min blocks

    def test_blocks_to_hours(self):
        """Test converting blocks to hours"""
        assert blocks_to_hours(2) == 1.0  # 2 blocks = 1 hour
        assert blocks_to_hours(1) == 0.5  # 1 block = 0.5 hour
        assert blocks_to_hours(5) == 2.5  # 5 blocks = 2.5 hours


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_zero_duration(self):
        """Test zero duration"""
        start = datetime(2026, 1, 6, 10, 0)
        end = datetime(2026, 1, 6, 10, 0)

        assert duration_to_minutes(start, end) == 0.0
        assert duration_to_hours(start, end) == 0.0

    def test_empty_blocks_list(self):
        """Test empty blocks list"""
        assert calculate_weekly_hours([]) == 0.0

    def test_midnight_boundary(self):
        """Test calculations across midnight"""
        start = datetime(2026, 1, 6, 23, 30)
        end = datetime(2026, 1, 7, 0, 30)

        duration = duration_to_minutes(start, end)
        assert duration == 60.0

        blocks = generate_time_blocks(start, end, block_size_minutes=30)
        assert len(blocks) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
