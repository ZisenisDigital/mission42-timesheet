"""
Data Fetchers

Base classes and utilities for fetching data from external sources.
"""

from app.services.fetchers.base import BaseFetcher, FetchResult
from app.services.fetchers.wakatime_fetcher import WakaTimeFetcher
from app.services.fetchers.calendar_fetcher import CalendarFetcher

__all__ = ["BaseFetcher", "FetchResult", "WakaTimeFetcher", "CalendarFetcher"]
