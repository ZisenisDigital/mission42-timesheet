"""
Unit Tests for Priority System

Tests for source priorities and overlap resolution.
"""

import pytest
from datetime import datetime, timedelta
from app.utils.priority import (
    SourcePriority,
    get_source_priority,
    get_highest_priority_source,
    times_overlap,
    TimeBlock,
    resolve_overlaps,
    merge_blocks,
    filter_by_priority,
    group_by_source,
    calculate_priority_stats,
    SOURCE_WAKATIME,
    SOURCE_CALENDAR,
    SOURCE_GMAIL,
    SOURCE_GITHUB,
    SOURCE_CLOUD_EVENTS,
    SOURCE_AUTO_FILL,
)


class TestSourcePriorities:
    """Test source priority values"""

    def test_priority_values(self):
        """Test that priority values are correct"""
        assert SourcePriority.WAKATIME == 100
        assert SourcePriority.CALENDAR == 80
        assert SourcePriority.GMAIL == 60
        assert SourcePriority.GITHUB == 40
        assert SourcePriority.CLOUD_EVENTS == 40
        assert SourcePriority.AUTO_FILL == 0

    def test_priority_ordering(self):
        """Test that priorities are ordered correctly"""
        assert SourcePriority.WAKATIME > SourcePriority.CALENDAR
        assert SourcePriority.CALENDAR > SourcePriority.GMAIL
        assert SourcePriority.GMAIL > SourcePriority.GITHUB
        assert SourcePriority.GITHUB > SourcePriority.AUTO_FILL

    def test_get_source_priority(self):
        """Test getting priority by source name"""
        assert get_source_priority(SOURCE_WAKATIME) == 100
        assert get_source_priority(SOURCE_CALENDAR) == 80
        assert get_source_priority(SOURCE_GMAIL) == 60
        assert get_source_priority(SOURCE_GITHUB) == 40
        assert get_source_priority(SOURCE_AUTO_FILL) == 0

    def test_get_source_priority_invalid(self):
        """Test getting priority for invalid source"""
        with pytest.raises(ValueError):
            get_source_priority("invalid_source")

    def test_get_highest_priority_source(self):
        """Test finding highest priority source from list"""
        sources = [SOURCE_GITHUB, SOURCE_WAKATIME, SOURCE_GMAIL]
        assert get_highest_priority_source(sources) == SOURCE_WAKATIME

        sources = [SOURCE_CALENDAR, SOURCE_GMAIL]
        assert get_highest_priority_source(sources) == SOURCE_CALENDAR

    def test_get_highest_priority_source_empty(self):
        """Test with empty sources list"""
        with pytest.raises(ValueError):
            get_highest_priority_source([])


class TestTimeOverlaps:
    """Test time overlap detection"""

    def test_times_overlap_complete(self):
        """Test complete overlap"""
        start1 = datetime(2026, 1, 6, 10, 0)
        end1 = datetime(2026, 1, 6, 11, 0)
        start2 = datetime(2026, 1, 6, 10, 0)
        end2 = datetime(2026, 1, 6, 11, 0)

        assert times_overlap(start1, end1, start2, end2)

    def test_times_overlap_partial(self):
        """Test partial overlap"""
        start1 = datetime(2026, 1, 6, 10, 0)
        end1 = datetime(2026, 1, 6, 11, 0)
        start2 = datetime(2026, 1, 6, 10, 30)
        end2 = datetime(2026, 1, 6, 11, 30)

        assert times_overlap(start1, end1, start2, end2)

    def test_times_no_overlap(self):
        """Test no overlap"""
        start1 = datetime(2026, 1, 6, 10, 0)
        end1 = datetime(2026, 1, 6, 11, 0)
        start2 = datetime(2026, 1, 6, 11, 0)
        end2 = datetime(2026, 1, 6, 12, 0)

        assert not times_overlap(start1, end1, start2, end2)

    def test_times_adjacent(self):
        """Test adjacent time blocks (touching but not overlapping)"""
        start1 = datetime(2026, 1, 6, 10, 0)
        end1 = datetime(2026, 1, 6, 10, 30)
        start2 = datetime(2026, 1, 6, 10, 30)
        end2 = datetime(2026, 1, 6, 11, 0)

        # Adjacent blocks should not overlap (end1 == start2 is not overlap)
        assert not times_overlap(start1, end1, start2, end2)


class TestTimeBlock:
    """Test TimeBlock class"""

    def test_timeblock_creation(self):
        """Test creating a TimeBlock"""
        start = datetime(2026, 1, 6, 10, 0)
        end = datetime(2026, 1, 6, 11, 0)

        block = TimeBlock(start, end, SOURCE_WAKATIME, "Coding: project")

        assert block.start == start
        assert block.end == end
        assert block.source == SOURCE_WAKATIME
        assert block.priority == 100
        assert block.description == "Coding: project"

    def test_timeblock_overlaps_with(self):
        """Test checking overlap between TimeBlocks"""
        block1 = TimeBlock(
            datetime(2026, 1, 6, 10, 0),
            datetime(2026, 1, 6, 11, 0),
            SOURCE_WAKATIME,
            "Coding",
        )

        block2 = TimeBlock(
            datetime(2026, 1, 6, 10, 30),
            datetime(2026, 1, 6, 11, 30),
            SOURCE_CALENDAR,
            "Meeting",
        )

        assert block1.overlaps_with(block2)
        assert block2.overlaps_with(block1)

    def test_timeblock_duration(self):
        """Test calculating block duration"""
        block = TimeBlock(
            datetime(2026, 1, 6, 10, 0),
            datetime(2026, 1, 6, 11, 0),
            SOURCE_WAKATIME,
            "Coding",
        )

        assert block.duration_minutes() == 60.0


class TestOverlapResolution:
    """Test overlap resolution strategies"""

    def test_resolve_overlaps_priority_strategy(self):
        """Test priority strategy: keep highest priority"""
        blocks = [
            TimeBlock(
                datetime(2026, 1, 6, 10, 0),
                datetime(2026, 1, 6, 11, 0),
                SOURCE_WAKATIME,  # Priority 100
                "Coding",
            ),
            TimeBlock(
                datetime(2026, 1, 6, 10, 30),
                datetime(2026, 1, 6, 11, 30),
                SOURCE_CALENDAR,  # Priority 80
                "Meeting",
            ),
        ]

        result = resolve_overlaps(blocks, strategy="priority")

        # Should keep only WakaTime (higher priority)
        assert len(result) == 1
        assert result[0].source == SOURCE_WAKATIME

    def test_resolve_overlaps_show_both_strategy(self):
        """Test show_both strategy: keep all blocks"""
        blocks = [
            TimeBlock(
                datetime(2026, 1, 6, 10, 0),
                datetime(2026, 1, 6, 11, 0),
                SOURCE_WAKATIME,
                "Coding",
            ),
            TimeBlock(
                datetime(2026, 1, 6, 10, 30),
                datetime(2026, 1, 6, 11, 30),
                SOURCE_CALENDAR,
                "Meeting",
            ),
        ]

        result = resolve_overlaps(blocks, strategy="show_both")

        # Should keep both blocks
        assert len(result) == 2

    def test_resolve_overlaps_combine_strategy(self):
        """Test combine strategy: merge overlapping blocks"""
        blocks = [
            TimeBlock(
                datetime(2026, 1, 6, 10, 0),
                datetime(2026, 1, 6, 11, 0),
                SOURCE_WAKATIME,
                "Coding",
            ),
            TimeBlock(
                datetime(2026, 1, 6, 10, 30),
                datetime(2026, 1, 6, 11, 30),
                SOURCE_CALENDAR,
                "Meeting",
            ),
        ]

        result = resolve_overlaps(blocks, strategy="combine")

        # Should have one merged block
        assert len(result) == 1
        assert result[0].start == datetime(2026, 1, 6, 10, 0)
        assert result[0].end == datetime(2026, 1, 6, 11, 30)
        assert "wakatime: Coding" in result[0].description
        assert "calendar: Meeting" in result[0].description

    def test_resolve_overlaps_no_overlap(self):
        """Test resolution when blocks don't overlap"""
        blocks = [
            TimeBlock(
                datetime(2026, 1, 6, 10, 0),
                datetime(2026, 1, 6, 11, 0),
                SOURCE_WAKATIME,
                "Coding",
            ),
            TimeBlock(
                datetime(2026, 1, 6, 14, 0),
                datetime(2026, 1, 6, 15, 0),
                SOURCE_CALENDAR,
                "Meeting",
            ),
        ]

        result = resolve_overlaps(blocks, strategy="priority")

        # Should keep both since they don't overlap
        assert len(result) == 2

    def test_resolve_overlaps_empty_list(self):
        """Test with empty list"""
        result = resolve_overlaps([], strategy="priority")
        assert result == []

    def test_resolve_overlaps_invalid_strategy(self):
        """Test with invalid strategy"""
        blocks = [
            TimeBlock(
                datetime(2026, 1, 6, 10, 0),
                datetime(2026, 1, 6, 11, 0),
                SOURCE_WAKATIME,
                "Coding",
            )
        ]

        with pytest.raises(ValueError):
            resolve_overlaps(blocks, strategy="invalid")


class TestMergeBlocks:
    """Test merging blocks"""

    def test_merge_two_blocks(self):
        """Test merging two blocks"""
        blocks = [
            TimeBlock(
                datetime(2026, 1, 6, 10, 0),
                datetime(2026, 1, 6, 11, 0),
                SOURCE_WAKATIME,
                "Coding",
            ),
            TimeBlock(
                datetime(2026, 1, 6, 10, 30),
                datetime(2026, 1, 6, 11, 30),
                SOURCE_CALENDAR,
                "Meeting",
            ),
        ]

        merged = merge_blocks(blocks)

        assert merged.start == datetime(2026, 1, 6, 10, 0)
        assert merged.end == datetime(2026, 1, 6, 11, 30)
        assert merged.source == SOURCE_WAKATIME  # Highest priority
        assert "wakatime" in merged.description.lower()
        assert "calendar" in merged.description.lower()

    def test_merge_single_block(self):
        """Test merging single block"""
        blocks = [
            TimeBlock(
                datetime(2026, 1, 6, 10, 0),
                datetime(2026, 1, 6, 11, 0),
                SOURCE_WAKATIME,
                "Coding",
            )
        ]

        merged = merge_blocks(blocks)

        # Should return same block
        assert merged.start == blocks[0].start
        assert merged.end == blocks[0].end

    def test_merge_empty_list(self):
        """Test merging empty list"""
        with pytest.raises(ValueError):
            merge_blocks([])


class TestFilterAndGroup:
    """Test filtering and grouping functions"""

    def test_filter_by_priority(self):
        """Test filtering blocks by minimum priority"""
        blocks = [
            TimeBlock(
                datetime(2026, 1, 6, 10, 0),
                datetime(2026, 1, 6, 11, 0),
                SOURCE_WAKATIME,  # 100
                "Coding",
            ),
            TimeBlock(
                datetime(2026, 1, 6, 11, 0),
                datetime(2026, 1, 6, 12, 0),
                SOURCE_CALENDAR,  # 80
                "Meeting",
            ),
            TimeBlock(
                datetime(2026, 1, 6, 12, 0),
                datetime(2026, 1, 6, 13, 0),
                SOURCE_GITHUB,  # 40
                "Commit",
            ),
        ]

        # Filter for priority >= 60
        result = filter_by_priority(blocks, min_priority=60)

        assert len(result) == 2
        assert result[0].source == SOURCE_WAKATIME
        assert result[1].source == SOURCE_CALENDAR

    def test_group_by_source(self):
        """Test grouping blocks by source"""
        blocks = [
            TimeBlock(
                datetime(2026, 1, 6, 10, 0),
                datetime(2026, 1, 6, 11, 0),
                SOURCE_WAKATIME,
                "Coding 1",
            ),
            TimeBlock(
                datetime(2026, 1, 6, 11, 0),
                datetime(2026, 1, 6, 12, 0),
                SOURCE_CALENDAR,
                "Meeting",
            ),
            TimeBlock(
                datetime(2026, 1, 6, 14, 0),
                datetime(2026, 1, 6, 15, 0),
                SOURCE_WAKATIME,
                "Coding 2",
            ),
        ]

        groups = group_by_source(blocks)

        assert len(groups) == 2
        assert len(groups[SOURCE_WAKATIME]) == 2
        assert len(groups[SOURCE_CALENDAR]) == 1

    def test_calculate_priority_stats(self):
        """Test calculating hours by source"""
        blocks = [
            TimeBlock(
                datetime(2026, 1, 6, 10, 0),
                datetime(2026, 1, 6, 11, 0),
                SOURCE_WAKATIME,
                "Coding 1",
            ),  # 1 hour
            TimeBlock(
                datetime(2026, 1, 6, 11, 0),
                datetime(2026, 1, 6, 12, 30),
                SOURCE_CALENDAR,
                "Meeting",
            ),  # 1.5 hours
            TimeBlock(
                datetime(2026, 1, 6, 14, 0),
                datetime(2026, 1, 6, 15, 30),
                SOURCE_WAKATIME,
                "Coding 2",
            ),  # 1.5 hours
        ]

        stats = calculate_priority_stats(blocks)

        assert stats[SOURCE_WAKATIME] == 2.5  # 1 + 1.5
        assert stats[SOURCE_CALENDAR] == 1.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
