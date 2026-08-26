"""
Timestamp utilities for ResearchOS.

All timestamps in ResearchOS are UTC and ISO 8601 formatted.
Based on Article XVII: Object Model — every object has a timestamp.
"""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    """
    Get the current UTC timestamp.

    Returns:
        Current datetime in UTC timezone.
    """
    return datetime.now(timezone.utc)


def parse_timestamp(ts: str) -> datetime:
    """
    Parse an ISO 8601 timestamp string into a datetime object.

    Args:
        ts: ISO 8601 formatted timestamp string.

    Returns:
        Datetime object in UTC.
    """
    dt = _parse_iso_compat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _parse_iso_compat(value: str) -> datetime:
    """Parse an ISO 8601 string, normalizing trailing Z to +00:00 for Python 3.10 compatibility."""
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def format_timestamp(dt: datetime) -> str:
    """
    Format a datetime as an ISO 8601 string.

    Args:
        dt: Datetime object.

    Returns:
        ISO 8601 formatted string.
    """
    return dt.isoformat()


def days_between(start: datetime, end: datetime) -> int:
    """
    Calculate the number of days between two timestamps.

    Args:
        start: Start datetime.
        end: End datetime.

    Returns:
        Number of days (integer).
    """
    delta = end - start
    return delta.days
