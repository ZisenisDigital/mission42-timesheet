"""
Unit Tests for Background Scheduler

Tests for automated data fetching and processing scheduler.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch, AsyncMock

from app.services.scheduler import SchedulerService, JobLock
from app.pocketbase_client import PocketBaseClient
from app.config import Config
from app.models.settings import Settings


class TestJobLock:
    """Test JobLock class"""

    def test_acquire_lock(self):
        """Test acquiring a lock"""
        lock = JobLock()
        assert lock.acquire("test_job") is True

    def test_acquire_locked(self):
        """Test acquiring an already locked job"""
        lock = JobLock()
        lock.acquire("test_job")
        # Try to acquire again - should fail
        assert lock.acquire("test_job") is False

    def test_release_lock(self):
        """Test releasing a lock"""
        lock = JobLock()
        lock.acquire("test_job")
        lock.release("test_job")
        # Should be able to acquire again
        assert lock.acquire("test_job") is True

    def test_release_unlocked(self):
        """Test releasing an unlocked job (should not error)"""
        lock = JobLock()
        lock.release("test_job")  # Should not raise error


class TestSchedulerService:
    """Test Scheduler Service"""

    @pytest.fixture
    def mock_pb_client(self):
        """Create mock PocketBase client"""
        return MagicMock()

    @pytest.fixture
    def mock_config(self):
        """Create mock Config with settings"""
        config = Mock(spec=Config)
        config.settings = Settings()  # Use default settings
        return config

    @pytest.fixture
    def scheduler(self, mock_pb_client, mock_config):
        """Create SchedulerService instance"""
        return SchedulerService(mock_pb_client, mock_config)

    def test_initialization(self, scheduler, mock_pb_client, mock_config):
        """Test scheduler initialization"""
        assert scheduler.pb_client == mock_pb_client
        assert scheduler.config == mock_config
        assert scheduler._running is False

    @pytest.mark.asyncio
    async def test_start_scheduler(self, scheduler):
        """Test starting the scheduler"""
        scheduler.start()

        assert scheduler._running is True
        assert len(scheduler.scheduler.get_jobs()) == 2  # fetch_and_process + monday_fillup

        # Clean up
        scheduler.stop()

    @pytest.mark.asyncio
    async def test_start_scheduler_twice(self, scheduler):
        """Test starting scheduler when already running"""
        scheduler.start()
        scheduler.start()  # Should log warning but not error

        assert scheduler._running is True

        # Clean up
        scheduler.stop()

    @pytest.mark.asyncio
    async def test_stop_scheduler(self, scheduler):
        """Test stopping the scheduler"""
        scheduler.start()
        scheduler.stop()

        assert scheduler._running is False

    def test_stop_scheduler_when_not_running(self, scheduler):
        """Test stopping scheduler when not running"""
        scheduler.stop()  # Should not error

    @pytest.mark.asyncio
    async def test_get_job_status_running(self, scheduler):
        """Test getting job status when running"""
        scheduler.start()

        status = scheduler.get_job_status()

        assert status["running"] is True
        assert len(status["jobs"]) == 2
        assert any(job["id"] == "fetch_and_process" for job in status["jobs"])
        assert any(job["id"] == "monday_fillup" for job in status["jobs"])

        # Clean up
        scheduler.stop()

    def test_get_job_status_not_running(self, scheduler):
        """Test getting job status when not running"""
        status = scheduler.get_job_status()

        assert status["running"] is False
        assert len(status["jobs"]) == 0

    @pytest.mark.asyncio
    @patch("app.services.scheduler.WakaTimeFetcher")
    @patch("app.services.scheduler.CalendarFetcher")
    @patch("app.services.scheduler.ClaudeCodeFetcher")
    async def test_fetch_all_sources(
        self,
        mock_claude_fetcher,
        mock_calendar_fetcher,
        mock_wakatime_fetcher,
        scheduler,
    ):
        """Test fetching from all sources"""
        # Mock fetcher results
        mock_result = Mock()
        mock_result.success = True
        mock_result.events_fetched = 5
        mock_result.events_created = 3
        mock_result.error = None

        mock_wakatime_fetcher.return_value.fetch.return_value = mock_result
        mock_calendar_fetcher.return_value.fetch.return_value = mock_result
        mock_claude_fetcher.return_value.fetch.return_value = mock_result

        results = await scheduler._fetch_all_sources()

        assert "wakatime" in results
        assert results["wakatime"]["success"] is True
        assert results["wakatime"]["events_fetched"] == 5

    @pytest.mark.asyncio
    @patch("app.services.scheduler.WakaTimeFetcher")
    async def test_fetch_all_sources_error(self, mock_wakatime_fetcher, scheduler):
        """Test fetching with error"""
        mock_wakatime_fetcher.return_value.fetch.side_effect = Exception(
            "Fetch failed"
        )

        results = await scheduler._fetch_all_sources()

        assert "wakatime" in results
        assert results["wakatime"]["success"] is False
        assert "Fetch failed" in results["wakatime"]["error"]

    @pytest.mark.asyncio
    @patch("app.services.scheduler.WakaTimeFetcher")
    @patch("app.services.scheduler.CalendarFetcher")
    @patch("app.services.scheduler.ClaudeCodeFetcher")
    @patch("app.services.scheduler.TimeBlockProcessor")
    async def test_fetch_and_process_job(
        self,
        mock_processor_class,
        mock_claude_fetcher,
        mock_calendar_fetcher,
        mock_wakatime_fetcher,
        scheduler,
    ):
        """Test fetch_and_process job execution"""
        # Mock fetcher results
        mock_result = Mock()
        mock_result.success = True
        mock_result.events_fetched = 5
        mock_result.events_created = 3
        mock_result.error = None

        mock_wakatime_fetcher.return_value.fetch.return_value = mock_result
        mock_calendar_fetcher.return_value.fetch.return_value = mock_result
        mock_claude_fetcher.return_value.fetch.return_value = mock_result

        # Mock processor
        mock_processor = Mock()
        mock_process_result = Mock()
        mock_process_result.success = True
        mock_process_result.raw_events_count = 15
        mock_process_result.time_blocks_created = 10
        mock_process_result.total_hours = 42.5
        mock_process_result.hours_filled = 2.5
        mock_processor.process_week.return_value = mock_process_result
        mock_processor_class.return_value = mock_processor

        await scheduler._fetch_and_process_job()

        # Verify processor was called
        mock_processor.process_week.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.scheduler.TimeBlockProcessor")
    async def test_monday_fillup_job(self, mock_processor_class, scheduler):
        """Test monday_fillup job execution"""
        # Mock processor
        mock_processor = Mock()
        mock_process_result = Mock()
        mock_process_result.success = True
        mock_process_result.raw_events_count = 15
        mock_process_result.time_blocks_created = 10
        mock_process_result.total_hours = 42.5
        mock_process_result.hours_filled = 2.5
        mock_process_result.week_start = datetime(2026, 1, 6, 18, 0)
        mock_process_result.week_end = datetime(2026, 1, 11, 18, 0)
        mock_processor.process_week.return_value = mock_process_result
        mock_processor_class.return_value = mock_processor

        await scheduler._monday_fillup_job()

        # Verify processor was called
        mock_processor.process_week.assert_called_once()

    @pytest.mark.asyncio
    async def test_job_overlap_prevention(self, scheduler):
        """Test that overlapping jobs are prevented"""
        # Acquire lock
        acquired = scheduler.job_lock.acquire("test_job")
        assert acquired is True

        # Mock job that checks for lock
        async def mock_job():
            if not scheduler.job_lock.acquire("test_job"):
                return "locked"
            scheduler.job_lock.release("test_job")
            return "executed"

        result = await mock_job()
        assert result == "locked"

        # Release lock
        scheduler.job_lock.release("test_job")

        # Now job should execute
        result = await mock_job()
        assert result == "executed"

    @pytest.mark.asyncio
    @patch("app.services.scheduler.WakaTimeFetcher")
    @patch("app.services.scheduler.CalendarFetcher")
    @patch("app.services.scheduler.ClaudeCodeFetcher")
    @patch("app.services.scheduler.TimeBlockProcessor")
    async def test_manual_fetch_and_process(
        self,
        mock_processor_class,
        mock_claude_fetcher,
        mock_calendar_fetcher,
        mock_wakatime_fetcher,
        scheduler,
    ):
        """Test manual fetch_and_process trigger"""
        # Mock fetcher results
        mock_result = Mock()
        mock_result.success = True
        mock_result.events_fetched = 5
        mock_result.events_created = 3
        mock_result.error = None

        mock_wakatime_fetcher.return_value.fetch.return_value = mock_result
        mock_calendar_fetcher.return_value.fetch.return_value = mock_result
        mock_claude_fetcher.return_value.fetch.return_value = mock_result

        # Mock processor
        mock_processor = Mock()
        mock_process_result = Mock()
        mock_process_result.success = True
        mock_process_result.raw_events_count = 15
        mock_process_result.time_blocks_created = 10
        mock_process_result.total_hours = 42.5
        mock_process_result.hours_filled = 2.5
        mock_processor.process_week.return_value = mock_process_result
        mock_processor_class.return_value = mock_processor

        result = await scheduler.manual_fetch_and_process()

        assert result["success"] is True
        assert "fetch_results" in result
        assert "process_result" in result

    @pytest.mark.asyncio
    @patch("app.services.scheduler.TimeBlockProcessor")
    async def test_manual_process_week(self, mock_processor_class, scheduler):
        """Test manual process_week trigger"""
        # Mock processor
        mock_processor = Mock()
        mock_process_result = Mock()
        mock_process_result.success = True
        mock_process_result.raw_events_count = 15
        mock_process_result.time_blocks_created = 10
        mock_process_result.total_hours = 42.5
        mock_process_result.hours_filled = 2.5
        mock_process_result.week_start = datetime(2026, 1, 6, 18, 0)
        mock_process_result.week_end = datetime(2026, 1, 11, 18, 0)
        mock_process_result.error = None
        mock_processor.process_week.return_value = mock_process_result
        mock_processor_class.return_value = mock_processor

        result = await scheduler.manual_process_week()

        assert result["success"] is True
        assert result["total_hours"] == 42.5
        assert result["hours_filled"] == 2.5

    @pytest.mark.asyncio
    @patch("app.services.scheduler.TimeBlockProcessor")
    async def test_manual_process_week_with_date(
        self, mock_processor_class, scheduler
    ):
        """Test manual process_week with specific date"""
        # Mock processor
        mock_processor = Mock()
        mock_process_result = Mock()
        mock_process_result.success = True
        mock_process_result.raw_events_count = 15
        mock_process_result.time_blocks_created = 10
        mock_process_result.total_hours = 42.5
        mock_process_result.hours_filled = 2.5
        mock_process_result.week_start = datetime(2026, 1, 6, 18, 0)
        mock_process_result.week_end = datetime(2026, 1, 11, 18, 0)
        mock_process_result.error = None
        mock_processor.process_week.return_value = mock_process_result
        mock_processor_class.return_value = mock_processor

        reference_date = datetime(2026, 1, 8)
        result = await scheduler.manual_process_week(reference_date)

        assert result["success"] is True
        mock_processor.process_week.assert_called_once_with(reference_date)

    @pytest.mark.asyncio
    @patch("app.services.scheduler.TimeBlockProcessor")
    async def test_manual_process_week_error(self, mock_processor_class, scheduler):
        """Test manual process_week with error"""
        mock_processor_class.side_effect = Exception("Processing failed")

        result = await scheduler.manual_process_week()

        assert result["success"] is False
        assert "Processing failed" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
