"""
Timezone normalization utilities for market data.

Based on Article XVII: Object Model — Data Layer.

All timestamps in ResearchOS are normalized to UTC on load.
This module provides utilities for converting timestamps from
various timezones to UTC.

Guarantees:
    - Deterministic: Same input timestamp → same UTC output
    - Safe: Handles naive and aware datetimes correctly
    - Standard: All timestamps are ISO 8601 compliant
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Dict


# Common timezone offsets (minutes from UTC)
_COMMON_OFFSETS: Dict[str, int] = {
    "UTC": 0,
    "GMT": 0,
    "EST": -300,
    "EDT": -240,
    "CST": -360,
    "CDT": -300,
    "MST": -420,
    "MDT": -360,
    "PST": -480,
    "PDT": -420,
    "CET": 60,
    "CEST": 120,
    "EET": 120,
    "EEST": 180,
    "BST": 60,
    "IST": 330,
    "JST": 540,
    "CST_ASIA": 480,
    "AEST": 600,
    "AEDT": 660,
}


def normalize_timestamp(
    dt: datetime,
    source_timezone: str = "UTC",
) -> datetime:
    """
    Normalize a timestamp to UTC.

    Args:
        dt: The datetime to normalize. Can be naive or timezone-aware.
        source_timezone: The source timezone (e.g., "America/New_York", "EST", "UTC").

    Returns:
        Timezone-aware datetime in UTC.

    Examples:
        >>> normalize_timestamp(datetime(2024, 1, 1, 12, 0, 0), "EST")
        datetime(2024, 1, 1, 17, 0, 0, tzinfo=timezone.utc)

        >>> normalize_timestamp(datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc))
        datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    """
    # If already timezone-aware, convert to UTC
    if dt.tzinfo is not None:
        offset = dt.tzinfo.utcoffset(dt)
        if offset == timedelta(0):
            return dt
        return dt.astimezone(timezone.utc)

    # Naive datetime: apply source timezone
    offset = _get_offset(source_timezone)
    if offset == 0:
        return dt.replace(tzinfo=timezone.utc)

    # Create timezone-aware datetime and convert to UTC
    tz = timezone(timedelta(minutes=offset))
    aware = dt.replace(tzinfo=tz)
    return aware.astimezone(timezone.utc)


def convert_timezone(
    dt: datetime,
    target_timezone: str,
) -> datetime:
    """
    Convert a UTC timestamp to a target timezone.

    Args:
        dt: UTC datetime to convert.
        target_timezone: Target timezone (e.g., "EST", "CET", "JST").

    Returns:
        Timezone-aware datetime in the target timezone.

    Raises:
        ValueError: If the datetime is not timezone-aware.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    offset = _get_offset(target_timezone)
    tz = timezone(timedelta(minutes=offset))
    return dt.astimezone(tz)


def format_iso(dt: datetime) -> str:
    """
    Format a datetime as ISO 8601 string with Z suffix for UTC.

    Args:
        dt: Datetime to format.

    Returns:
        ISO 8601 formatted string.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    if dt.tzinfo.utcoffset(dt) == timedelta(0):
        return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    return dt.isoformat()


def parse_iso(value: str) -> datetime:
    """
    Parse an ISO 8601 string, normalizing to UTC.

    Args:
        value: ISO 8601 formatted string.

    Returns:
        Timezone-aware datetime in UTC.
    """
    dt = datetime.fromisoformat(value)
    return normalize_timestamp(dt)


def _get_offset(timezone_name: str) -> int:
    """
    Get UTC offset in minutes for a timezone name.

    Args:
        timezone_name: Timezone name (e.g., "EST", "CET", "UTC").

    Returns:
        Offset in minutes from UTC (positive = east of UTC).
    """
    # Try common abbreviations
    upper = timezone_name.upper().strip()
    if upper in _COMMON_OFFSETS:
        return _COMMON_OFFSETS[upper]

    # Try to parse hours offset (e.g., "+05:30", "-05:00")
    try:
        if upper.startswith(("+", "-")) and ":" in upper:
            parts = upper.split(":")
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            if hours < 0:
                return hours * 60 - minutes
            return hours * 60 + minutes
    except (ValueError, IndexError):
        pass

    # Default to UTC
    return 0

