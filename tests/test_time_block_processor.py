"""
Unit Tests for Time Block Processor

Tests for processing raw events into 30-minute time blocks.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch

from app.services.time_block_processor import TimeBlockProcessor, ProcessingResult
from app.pocketbase_client import PocketBaseClient
from app.config import Config
from app.models.settings import (
    Settings,
    RoundingMode,
    FillUpTopicMode,
    FillUpDistribution,
    OverlapHandling,
)
from app.utils.priority import TimeBlock, SourcePriority


class TestTimeBlockProcessor:
    """Test Time Block Processor"""

    @pytest.fixture
    def mock_pb_client(self):
        """Create mock PocketBase client"""
        # Use MagicMock without spec to allow arbitrary attributes
        return MagicMock()

    @pytest.fixture
    def mock_config(self):
        """Create mock Config with settings"""
        config = Mock(spec=Config)
        config.settings = Settings()  # Use default settings
        return config

    @pytest.fixture
    def processor(self, mock_pb_client, mock_config):
        """Create TimeBlockProcessor instance"""
        return TimeBlockProcessor(mock_pb_client, mock_config)

    def test_initialization(self, processor, mock_pb_client, mock_config):
        """Test processor initialization"""
        assert processor.pb_client == mock_pb_client
        assert processor.config == mock_config

    def test_fetch_raw_events_for_week(self, processor, mock_pb_client):
        """Test fetching raw events for a week"""
        week_start = datetime(2026, 1, 6, 18, 0)
        week_end = datetime(2026, 1, 11, 18, 0)

        # Mock raw events
        mock_event = Mock()
        mock_event.id = "evt_123"
        mock_event.source = "wakatime"
        mock_event.timestamp = "2026-01-07T10:00:00Z"
        mock_event.duration_minutes = 60
        mock_event.description = "Coding"

        mock_pb_client.get_raw_events_for_week.return_value = [mock_event]

        events = processor.fetch_raw_events_for_week(week_start, week_end)

        assert len(events) == 1
        assert events[0]["source"] == "wakatime"
        mock_pb_client.get_raw_events_for_week.assert_called_once_with(
            week_start, week_end
        )

    def test_convert_to_time_blocks(self, processor, mock_config):
        """Test converting raw events to time blocks"""
        raw_events = [
            {
                "source": "wakatime",
                "timestamp": datetime(2026, 1, 7, 10, 0),
                "duration_minutes": 65,  # Should round to 1.5h
                "description": "Coding: Project X",
                "metadata": {"project": "X"},
            }
        ]

        blocks = processor.convert_to_time_blocks(raw_events, mock_config.settings)

        assert len(blocks) == 1
        assert blocks[0].source == "wakatime"
        assert blocks[0].description == "Coding: Project X"
        assert blocks[0].priority == 100  # WakaTime priority
        # 65 minutes rounds up to 1.5h
        assert (blocks[0].end - blocks[0].start).total_seconds() / 3600 == 1.5

    def test_convert_to_time_blocks_rounding_up(self, processor, mock_config):
        """Test rounding mode UP"""
        mock_config.settings.processing.rounding_mode = RoundingMode.UP

        raw_events = [
            {
                "source": "calendar",
                "timestamp": datetime(2026, 1, 7, 10, 0),
                "duration_minutes": 35,  # Should round up to 1.0h
                "description": "Meeting",
                "metadata": {},
            }
        ]

        blocks = processor.convert_to_time_blocks(raw_events, mock_config.settings)

        assert len(blocks) == 1
        # 35 minutes rounds up to 1.0h
        assert (blocks[0].end - blocks[0].start).total_seconds() / 3600 == 1.0

    def test_convert_to_time_blocks_rounding_nearest(self, processor, mock_config):
        """Test rounding mode NEAREST"""
        mock_config.settings.processing.rounding_mode = RoundingMode.NEAREST

        raw_events = [
            {
                "source": "calendar",
                "timestamp": datetime(2026, 1, 7, 10, 0),
                "duration_minutes": 35,  # Should round to nearest 0.5h
                "description": "Meeting",
                "metadata": {},
            }
        ]

        blocks = processor.convert_to_time_blocks(raw_events, mock_config.settings)

        assert len(blocks) == 1
        # 35 minutes rounds to 0.5h (nearest)
        assert (blocks[0].end - blocks[0].start).total_seconds() / 3600 == 0.5

    def test_convert_to_time_blocks_skips_invalid(self, processor, mock_config):
        """Test that invalid events are skipped"""
        raw_events = [
            {
                "source": "test",
                "timestamp": "invalid-date",
                "duration_minutes": 60,
                "description": "Test",
                "metadata": {},
            },
            {
                "source": "test",
                "timestamp": datetime(2026, 1, 7, 10, 0),
                "duration_minutes": 0,  # Zero duration
                "description": "Test",
                "metadata": {},
            },
        ]

        blocks = processor.convert_to_time_blocks(raw_events, mock_config.settings)

        assert len(blocks) == 0  # Both events should be skipped

    def test_resolve_overlapping_blocks_priority(self, processor, mock_config):
        """Test overlap resolution with PRIORITY strategy"""
        mock_config.settings.processing.overlap_handling = OverlapHandling.PRIORITY

        # Create overlapping blocks
        blocks = [
            TimeBlock(
                start=datetime(2026, 1, 7, 10, 0),
                end=datetime(2026, 1, 7, 11, 0),
                source="calendar",
                description="Meeting",
                
                metadata={},
            ),
            TimeBlock(
                start=datetime(2026, 1, 7, 10, 30),
                end=datetime(2026, 1, 7, 11, 30),
                source="wakatime",
                description="Coding",
                
                metadata={},
            ),
        ]

        resolved = processor.resolve_overlapping_blocks(blocks, mock_config.settings)

        # Should keep WakaTime (higher priority)
        assert len(resolved) == 1
        assert resolved[0].source == "wakatime"

    def test_group_activities_disabled(self, processor, mock_config):
        """Test grouping when disabled"""
        mock_config.settings.processing.group_same_activities = False

        blocks = [
            TimeBlock(
                start=datetime(2026, 1, 7, 10, 0),
                end=datetime(2026, 1, 7, 12, 0),
                source="wakatime",
                description="Coding: Project X",
                
                metadata={},
            ),
            TimeBlock(
                start=datetime(2026, 1, 7, 14, 0),
                end=datetime(2026, 1, 7, 17, 0),
                source="wakatime",
                description="Coding: Project X",
                
                metadata={},
            ),
        ]

        grouped = processor.group_activities(blocks, mock_config.settings)

        assert len(grouped) == 2  # Should remain separate

    def test_group_activities_enabled(self, processor, mock_config):
        """Test grouping when enabled"""
        mock_config.settings.processing.group_same_activities = True

        blocks = [
            TimeBlock(
                start=datetime(2026, 1, 7, 10, 0),
                end=datetime(2026, 1, 7, 12, 0),
                source="wakatime",
                description="Coding: Project X",
                
                metadata={},
            ),
            TimeBlock(
                start=datetime(2026, 1, 7, 14, 0),
                end=datetime(2026, 1, 7, 17, 0),
                source="wakatime",
                description="Coding: Project X",
                
                metadata={},
            ),
        ]

        grouped = processor.group_activities(blocks, mock_config.settings)

        assert len(grouped) == 1  # Should be merged
        # Total duration: 2h + 3h = 5h
        assert (grouped[0].end - grouped[0].start).total_seconds() / 3600 == 5.0

    def test_calculate_week_hours(self, processor):
        """Test calculating total week hours"""
        blocks = [
            TimeBlock(
                start=datetime(2026, 1, 7, 10, 0),
                end=datetime(2026, 1, 7, 12, 0),  # 2 hours
                source="wakatime",
                description="Coding",
                
                metadata={},
            ),
            TimeBlock(
                start=datetime(2026, 1, 7, 14, 0),
                end=datetime(2026, 1, 7, 16, 30),  # 2.5 hours
                source="calendar",
                description="Meeting",
                
                metadata={},
            ),
        ]

        total_hours = processor.calculate_week_hours(blocks)

        assert total_hours == 4.5

    def test_auto_fill_disabled(self, processor, mock_config):
        """Test auto-fill when disabled"""
        mock_config.settings.core.auto_fill_enabled = False

        blocks = [
            TimeBlock(
                start=datetime(2026, 1, 7, 10, 0),
                end=datetime(2026, 1, 7, 12, 0),
                source="wakatime",
                description="Coding",
                
                metadata={},
            )
        ]

        week_start = datetime(2026, 1, 6, 18, 0)
        week_end = datetime(2026, 1, 11, 18, 0)

        updated_blocks, hours_filled = processor.auto_fill_to_target(
            blocks, week_start, week_end, mock_config.settings
        )

        assert len(updated_blocks) == 1  # No fill blocks added
        assert hours_filled == 0.0

    def test_auto_fill_already_at_target(self, processor, mock_config):
        """Test auto-fill when already at target hours"""
        mock_config.settings.core.auto_fill_enabled = True
        mock_config.settings.core.target_hours_per_week = 40

        # Create 40 hours of blocks
        blocks = [
            TimeBlock(
                start=datetime(2026, 1, 7, 0, 0),
                end=datetime(2026, 1, 7, 0, 0) + timedelta(hours=40),
                source="wakatime",
                description="Coding",
                
                metadata={},
            )
        ]

        week_start = datetime(2026, 1, 6, 18, 0)
        week_end = datetime(2026, 1, 11, 18, 0)

        updated_blocks, hours_filled = processor.auto_fill_to_target(
            blocks, week_start, week_end, mock_config.settings
        )

        assert len(updated_blocks) == 1  # No fill needed
        assert hours_filled == 0.0

    def test_auto_fill_to_target(self, processor, mock_config):
        """Test auto-fill adds hours to reach target"""
        mock_config.settings.core.auto_fill_enabled = True
        mock_config.settings.core.target_hours_per_week = 40
        mock_config.settings.processing.fill_up_distribution = (
            FillUpDistribution.END_OF_WEEK
        )

        # Create 35 hours of blocks
        blocks = [
            TimeBlock(
                start=datetime(2026, 1, 7, 0, 0),
                end=datetime(2026, 1, 7, 0, 0) + timedelta(hours=35),
                source="wakatime",
                description="Coding",
                
                metadata={},
            )
        ]

        week_start = datetime(2026, 1, 6, 18, 0)
        week_end = datetime(2026, 1, 11, 18, 0)

        updated_blocks, hours_filled = processor.auto_fill_to_target(
            blocks, week_start, week_end, mock_config.settings
        )

        assert len(updated_blocks) == 2  # Original + fill block
        assert hours_filled == 5.0  # 40 - 35
        assert updated_blocks[1].source == "auto_fill"

    def test_determine_fill_up_topic_manual(self, processor, mock_config):
        """Test fill-up topic determination with MANUAL mode"""
        mock_config.settings.processing.fill_up_topic_mode = FillUpTopicMode.MANUAL
        mock_config.settings.processing.fill_up_default_topic = "General"

        blocks = []
        topic = processor._determine_fill_up_topic(blocks, mock_config.settings)

        assert topic == "General"

    def test_determine_fill_up_topic_auto(self, processor, mock_config):
        """Test fill-up topic determination with AUTO mode"""
        mock_config.settings.processing.fill_up_topic_mode = FillUpTopicMode.AUTO

        blocks = [
            TimeBlock(
                start=datetime(2026, 1, 7, 10, 0),
                end=datetime(2026, 1, 7, 15, 0),  # 5 hours
                source="wakatime",
                description="Coding: Project X",
                
                metadata={},
            ),
            TimeBlock(
                start=datetime(2026, 1, 7, 16, 0),
                end=datetime(2026, 1, 7, 18, 0),  # 2 hours
                source="calendar",
                description="Meeting: Team Sync",
                
                metadata={},
            ),
        ]

        topic = processor._determine_fill_up_topic(blocks, mock_config.settings)

        # Should use "Coding: Project X" (most hours)
        assert topic == "Coding: Project X"

    def test_determine_fill_up_topic_generic(self, processor, mock_config):
        """Test fill-up topic determination with GENERIC mode"""
        mock_config.settings.processing.fill_up_topic_mode = FillUpTopicMode.GENERIC
        mock_config.settings.processing.fill_up_default_topic = "Development"

        blocks = []
        topic = processor._determine_fill_up_topic(blocks, mock_config.settings)

        assert topic == "Development"

    def test_create_fill_up_blocks_end_of_week(self, processor, mock_config):
        """Test fill-up block creation with END_OF_WEEK strategy"""
        mock_config.settings.processing.fill_up_distribution = (
            FillUpDistribution.END_OF_WEEK
        )

        week_start = datetime(2026, 1, 6, 18, 0)
        week_end = datetime(2026, 1, 11, 18, 0)

        fill_blocks = processor._create_fill_up_blocks(
            5.0, week_start, week_end, [], "General", mock_config.settings
        )

        assert len(fill_blocks) == 1
        assert fill_blocks[0].source == "auto_fill"
        assert fill_blocks[0].description == "Development: General"
        # Duration should be 5 hours
        duration = (fill_blocks[0].end - fill_blocks[0].start).total_seconds() / 3600
        assert duration == 5.0

    def test_create_fill_up_blocks_distributed(self, processor, mock_config):
        """Test fill-up block creation with DISTRIBUTED strategy"""
        mock_config.settings.processing.fill_up_distribution = (
            FillUpDistribution.DISTRIBUTED
        )

        week_start = datetime(2026, 1, 6, 18, 0)  # Monday 6 PM
        week_end = datetime(2026, 1, 11, 18, 0)  # Saturday 6 PM (5 days)

        fill_blocks = processor._create_fill_up_blocks(
            5.0, week_start, week_end, [], "General", mock_config.settings
        )

        assert len(fill_blocks) == 5  # One block per day
        # Each block should have 1 hour (5 hours / 5 days)
        for block in fill_blocks:
            duration = (block.end - block.start).total_seconds() / 3600
            assert duration == 1.0

    def test_save_time_blocks(self, processor, mock_pb_client):
        """Test saving time blocks to PocketBase"""
        blocks = [
            TimeBlock(
                start=datetime(2026, 1, 7, 10, 0),
                end=datetime(2026, 1, 7, 12, 0),
                source="wakatime",
                description="Coding",
                
                metadata={"project": "X"},
            )
        ]

        week_start = datetime(2026, 1, 6, 18, 0)

        count = processor.save_time_blocks(blocks, week_start)

        assert count == 1
        mock_pb_client.create_time_block.assert_called_once()

    def test_update_week_summary(self, processor, mock_pb_client):
        """Test updating week summary"""
        week_start = datetime(2026, 1, 6, 18, 0)
        week_end = datetime(2026, 1, 11, 18, 0)

        processor.update_week_summary(week_start, week_end, 42.5, 2.5)

        mock_pb_client.get_or_create_week_summary.assert_called_once()
        call_args = mock_pb_client.get_or_create_week_summary.call_args
        assert call_args[1]["total_hours"] == 42.5

    @patch.object(TimeBlockProcessor, "fetch_raw_events_for_week")
    @patch.object(TimeBlockProcessor, "save_time_blocks")
    @patch.object(TimeBlockProcessor, "update_week_summary")
    def test_process_week_success(
        self,
        mock_update_summary,
        mock_save_blocks,
        mock_fetch,
        processor,
        mock_config,
    ):
        """Test successful week processing"""
        # Mock raw events
        mock_fetch.return_value = [
            {
                "source": "wakatime",
                "timestamp": datetime(2026, 1, 7, 10, 0),
                "duration_minutes": 120,
                "description": "Coding",
                "metadata": {},
            }
        ]

        # Mock save returns count
        mock_save_blocks.return_value = 1

        result = processor.process_week(datetime(2026, 1, 7))

        assert result.success is True
        assert result.raw_events_count == 1
        assert result.time_blocks_created == 1
        assert result.total_hours > 0

    @patch.object(TimeBlockProcessor, "fetch_raw_events_for_week")
    def test_process_week_error(self, mock_fetch, processor):
        """Test week processing with error"""
        mock_fetch.side_effect = Exception("Database error")

        result = processor.process_week(datetime(2026, 1, 7))

        assert result.success is False
        assert "Database error" in result.error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
