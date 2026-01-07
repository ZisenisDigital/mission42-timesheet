"""
Background Scheduler Service

Automates data fetching and processing with APScheduler.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from threading import Lock

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from app.pocketbase_client import PocketBaseClient
from app.config import Config
from app.services.time_block_processor import TimeBlockProcessor
from app.services.fetchers.wakatime_fetcher import WakaTimeFetcher
from app.services.fetchers.calendar_fetcher import CalendarFetcher
from app.services.fetchers.claude_code_fetcher import ClaudeCodeFetcher

logger = logging.getLogger(__name__)


class JobLock:
    """Thread-safe lock for preventing job overlaps"""

    def __init__(self):
        self._locks: Dict[str, Lock] = {}

    def acquire(self, job_name: str) -> bool:
        """
        Try to acquire lock for a job.

        Args:
            job_name: Name of the job

        Returns:
            True if lock acquired, False if already locked
        """
        if job_name not in self._locks:
            self._locks[job_name] = Lock()

        return self._locks[job_name].acquire(blocking=False)

    def release(self, job_name: str):
        """
        Release lock for a job.

        Args:
            job_name: Name of the job
        """
        if job_name in self._locks:
            try:
                self._locks[job_name].release()
            except RuntimeError:
                # Lock was not acquired, ignore
                pass


class SchedulerService:
    """
    Background scheduler for automated data fetching and processing.

    Jobs:
    - Every N hours: Fetch all sources + process current week
    - Monday at work_week_start_time: Process previous week with fill-up
    """

    def __init__(self, pb_client: PocketBaseClient, config: Config):
        """
        Initialize scheduler service.

        Args:
            pb_client: PocketBase client instance
            config: Application configuration
        """
        self.pb_client = pb_client
        self.config = config
        self.scheduler = AsyncIOScheduler()
        self.job_lock = JobLock()
        self._running = False

    def start(self):
        """Start the scheduler and register jobs"""
        if self._running:
            logger.warning("Scheduler is already running")
            return

        settings = self.config.settings

        # Get fetch interval from settings
        fetch_interval = settings.core.fetch_interval_hours

        # Job 1: Every N hours - Fetch and process
        self.scheduler.add_job(
            self._fetch_and_process_job,
            trigger=IntervalTrigger(hours=fetch_interval),
            id="fetch_and_process",
            name="Fetch All Sources and Process Week",
            replace_existing=True,
        )

        # Job 2: Monday at work_week_start_time - Weekly fill-up
        work_week_start_day = settings.core.work_week_start_day.value
        work_week_start_time = settings.core.work_week_start_time
        hour, minute = map(int, work_week_start_time.split(":"))

        # Map day names to cron day numbers (0=Monday, 6=Sunday)
        day_map = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }
        day_of_week = day_map.get(work_week_start_day, 0)

        self.scheduler.add_job(
            self._monday_fillup_job,
            trigger=CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute),
            id="monday_fillup",
            name="Monday Weekly Fill-up",
            replace_existing=True,
        )

        self.scheduler.start()
        self._running = True
        logger.info("Scheduler started successfully")

    def stop(self):
        """Stop the scheduler"""
        if not self._running:
            return

        self.scheduler.shutdown()
        self._running = False
        logger.info("Scheduler stopped")

    async def _fetch_and_process_job(self):
        """
        Scheduled job: Fetch all sources and process current week.

        Runs every N hours (configured in settings).
        """
        job_name = "fetch_and_process"

        # Prevent overlapping executions
        if not self.job_lock.acquire(job_name):
            logger.warning(f"Job {job_name} is already running, skipping")
            return

        try:
            logger.info(f"Starting job: {job_name}")
            start_time = datetime.now()

            # Log job start
            job_log = self._log_job_start(job_name)

            # Fetch all sources
            fetch_results = await self._fetch_all_sources()

            # Process current week
            processor = TimeBlockProcessor(self.pb_client, self.config)
            process_result = processor.process_week()

            # Log job completion
            duration = (datetime.now() - start_time).total_seconds()
            self._log_job_complete(
                job_log,
                success=process_result.success,
                duration=duration,
                metadata={
                    "fetch_results": fetch_results,
                    "process_result": {
                        "raw_events_count": process_result.raw_events_count,
                        "time_blocks_created": process_result.time_blocks_created,
                        "total_hours": process_result.total_hours,
                        "hours_filled": process_result.hours_filled,
                    },
                },
            )

            logger.info(f"Job {job_name} completed successfully in {duration:.2f}s")

        except Exception as e:
            logger.error(f"Job {job_name} failed: {str(e)}", exc_info=True)
            self._log_job_error(job_log, str(e))
        finally:
            self.job_lock.release(job_name)

    async def _monday_fillup_job(self):
        """
        Scheduled job: Process previous week with fill-up.

        Runs every Monday at work_week_start_time (e.g., Monday 6 PM).
        Ensures the completed week has minimum 40 hours.
        """
        job_name = "monday_fillup"

        # Prevent overlapping executions
        if not self.job_lock.acquire(job_name):
            logger.warning(f"Job {job_name} is already running, skipping")
            return

        try:
            logger.info(f"Starting job: {job_name}")
            start_time = datetime.now()

            # Log job start
            job_log = self._log_job_start(job_name)

            # Process current week (which is actually the previous work week)
            # The work week just ended, so process it
            processor = TimeBlockProcessor(self.pb_client, self.config)
            process_result = processor.process_week()

            # Log job completion
            duration = (datetime.now() - start_time).total_seconds()
            self._log_job_complete(
                job_log,
                success=process_result.success,
                duration=duration,
                metadata={
                    "raw_events_count": process_result.raw_events_count,
                    "time_blocks_created": process_result.time_blocks_created,
                    "total_hours": process_result.total_hours,
                    "hours_filled": process_result.hours_filled,
                    "week_start": process_result.week_start.isoformat()
                    if process_result.week_start
                    else None,
                    "week_end": process_result.week_end.isoformat()
                    if process_result.week_end
                    else None,
                },
            )

            logger.info(f"Job {job_name} completed successfully in {duration:.2f}s")

        except Exception as e:
            logger.error(f"Job {job_name} failed: {str(e)}", exc_info=True)
            self._log_job_error(job_log, str(e))
        finally:
            self.job_lock.release(job_name)

    async def _fetch_all_sources(self) -> Dict[str, Any]:
        """
        Fetch data from all enabled sources.

        Returns:
            Dictionary with fetch results from each source
        """
        results = {}

        # WakaTime
        if self.config.settings.wakatime.wakatime_enabled:
            try:
                fetcher = WakaTimeFetcher(self.pb_client)
                result = fetcher.fetch()
                results["wakatime"] = {
                    "success": result.success,
                    "events_fetched": result.events_fetched,
                    "events_created": result.events_created,
                    "error": result.error,
                }
                logger.info(
                    f"WakaTime: {result.events_fetched} fetched, {result.events_created} created"
                )
            except Exception as e:
                results["wakatime"] = {"success": False, "error": str(e)}
                logger.error(f"WakaTime fetch failed: {str(e)}")

        # Google Calendar
        if self.config.settings.calendar.calendar_enabled:
            try:
                fetcher = CalendarFetcher(self.pb_client)
                result = fetcher.fetch()
                results["calendar"] = {
                    "success": result.success,
                    "events_fetched": result.events_fetched,
                    "events_created": result.events_created,
                    "error": result.error,
                }
                logger.info(
                    f"Calendar: {result.events_fetched} fetched, {result.events_created} created"
                )
            except Exception as e:
                results["calendar"] = {"success": False, "error": str(e)}
                logger.error(f"Calendar fetch failed: {str(e)}")

        # Claude Code (Cloud Events)
        if self.config.settings.cloud_events.cloud_events_enabled:
            try:
                fetcher = ClaudeCodeFetcher(self.pb_client)
                result = fetcher.fetch()
                results["claude_code"] = {
                    "success": result.success,
                    "events_fetched": result.events_fetched,
                    "events_created": result.events_created,
                    "error": result.error,
                }
                logger.info(
                    f"Claude Code: {result.events_fetched} fetched, {result.events_created} created"
                )
            except Exception as e:
                results["claude_code"] = {"success": False, "error": str(e)}
                logger.error(f"Claude Code fetch failed: {str(e)}")

        # Gmail and GitHub would be added here if they were in the codebase
        # For now, they're implemented elsewhere according to the user

        return results

    def _log_job_start(self, job_name: str) -> Optional[str]:
        """
        Log job start to PocketBase.

        Args:
            job_name: Name of the job

        Returns:
            Job log record ID
        """
        try:
            # Create job log record
            # Note: This requires a job_logs collection in PocketBase
            # For now, just log to Python logger
            logger.info(f"Job started: {job_name}")
            return f"{job_name}_{datetime.now().isoformat()}"
        except Exception as e:
            logger.error(f"Failed to log job start: {str(e)}")
            return None

    def _log_job_complete(
        self,
        job_log_id: Optional[str],
        success: bool,
        duration: float,
        metadata: Dict[str, Any],
    ):
        """
        Log job completion to PocketBase.

        Args:
            job_log_id: Job log record ID
            success: Whether job succeeded
            duration: Job duration in seconds
            metadata: Job metadata
        """
        try:
            logger.info(
                f"Job completed: {job_log_id}, success={success}, duration={duration:.2f}s"
            )
            logger.debug(f"Job metadata: {metadata}")
        except Exception as e:
            logger.error(f"Failed to log job completion: {str(e)}")

    def _log_job_error(self, job_log_id: Optional[str], error: str):
        """
        Log job error to PocketBase.

        Args:
            job_log_id: Job log record ID
            error: Error message
        """
        try:
            logger.error(f"Job error: {job_log_id}, error={error}")
        except Exception as e:
            logger.error(f"Failed to log job error: {str(e)}")

    async def manual_fetch_and_process(self) -> Dict[str, Any]:
        """
        Manually trigger fetch and process job.

        Returns:
            Dictionary with job results
        """
        logger.info("Manual trigger: fetch_and_process")

        try:
            # Fetch all sources
            fetch_results = await self._fetch_all_sources()

            # Process current week
            processor = TimeBlockProcessor(self.pb_client, self.config)
            process_result = processor.process_week()

            return {
                "success": True,
                "fetch_results": fetch_results,
                "process_result": {
                    "raw_events_count": process_result.raw_events_count,
                    "time_blocks_created": process_result.time_blocks_created,
                    "total_hours": process_result.total_hours,
                    "hours_filled": process_result.hours_filled,
                },
            }

        except Exception as e:
            logger.error(f"Manual fetch_and_process failed: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def manual_process_week(
        self, reference_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Manually trigger week processing.

        Args:
            reference_date: Date within the week to process (defaults to now)

        Returns:
            Dictionary with processing results
        """
        logger.info(f"Manual trigger: process_week for {reference_date}")

        try:
            processor = TimeBlockProcessor(self.pb_client, self.config)
            process_result = processor.process_week(reference_date)

            return {
                "success": process_result.success,
                "raw_events_count": process_result.raw_events_count,
                "time_blocks_created": process_result.time_blocks_created,
                "total_hours": process_result.total_hours,
                "hours_filled": process_result.hours_filled,
                "week_start": process_result.week_start.isoformat()
                if process_result.week_start
                else None,
                "week_end": process_result.week_end.isoformat()
                if process_result.week_end
                else None,
                "error": process_result.error,
            }

        except Exception as e:
            logger.error(f"Manual process_week failed: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    def get_job_status(self) -> Dict[str, Any]:
        """
        Get status of all scheduled jobs.

        Returns:
            Dictionary with job status information
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat()
                    if job.next_run_time
                    else None,
                    "trigger": str(job.trigger),
                }
            )

        return {"running": self._running, "jobs": jobs}
