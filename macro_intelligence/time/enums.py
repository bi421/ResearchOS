"""
ResearchOS Macro Intelligence Layer - Time & Calendar Enums
Version: time/enums/v1
Status: FROZEN
"""

from datetime import timedelta, timezone
from enum import Enum
from typing import Optional

UTC = timezone.utc


class TimezoneType(str, Enum):
    """
    Timezone classification for macro events.

    Types:
    - UTC: Coordinated Universal Time
    - US_EASTERN: US Eastern Time (ET)
    - US_CENTRAL: US Central Time (CT)
    - EUROPEAN: European Time (CET/CEST)
    - ASIAN: Asian Time (JST, etc.)
    - LOCAL: Local time of data source
    """

    UTC = "utc"
    US_EASTERN = "us_eastern"
    US_CENTRAL = "us_central"
    EUROPEAN = "european"
    ASIAN = "asian"
    LOCAL = "local"

    def to_offset(self) -> timezone:
        """Convert to timezone offset."""
        offsets = {
            TimezoneType.UTC: UTC,
            TimezoneType.US_EASTERN: timezone(timedelta(hours=-5)),
            TimezoneType.US_CENTRAL: timezone(timedelta(hours=-6)),
            TimezoneType.EUROPEAN: timezone(timedelta(hours=1)),
            TimezoneType.ASIAN: timezone(timedelta(hours=9)),
            TimezoneType.LOCAL: UTC,  # Default to UTC
        }
        return offsets.get(self, UTC)

    def is_utc(self) -> bool:
        """Check if this is UTC timezone."""
        return self == TimezoneType.UTC


class EventCategory(str, Enum):
    """
    Category of economic event.

    Categories:
    - DATA_RELEASE: Scheduled data release
    - CENTRAL_BANK: Central bank meeting/speech
    - POLICY: Policy announcement
    - GEOPOLITICAL: Geopolitical event
    - MARKET: Market event
    - HOLIDAY: Market holiday
    - UNSCHEDULED: Unscheduled event
    """

    DATA_RELEASE = "data_release"
    CENTRAL_BANK = "central_bank"
    POLICY = "policy"
    GEOPOLITICAL = "geopolitical"
    MARKET = "market"
    HOLIDAY = "holiday"
    UNSCHEDULED = "unscheduled"

    def is_scheduled(self) -> bool:
        """Check if event is scheduled."""
        return self in (
            EventCategory.DATA_RELEASE,
            EventCategory.CENTRAL_BANK,
            EventCategory.POLICY,
            EventCategory.HOLIDAY,
        )

    def is_unscheduled(self) -> bool:
        """Check if event is unscheduled."""
        return self in (
            EventCategory.GEOPOLITICAL,
            EventCategory.UNSCHEDULED,
        )


class ReleaseStatus(str, Enum):
    """
    Status of a data release.

    Statuses:
    - PLANNED: Scheduled but not yet released
    - ACTIVE: Currently being released
    - COMPLETED: Successfully released
    - DELAYED: Released later than planned
    - CANCELLED: Release cancelled
    - REVISED: Release was revised
    """

    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    DELAYED = "delayed"
    CANCELLED = "cancelled"
    REVISED = "revised"

    def is_final(self) -> bool:
        """Check if release is in final state."""
        return self in (
            ReleaseStatus.COMPLETED,
            ReleaseStatus.CANCELLED,
        )

    def is_terminal(self) -> bool:
        """Check if status is terminal."""
        return self in (
            ReleaseStatus.COMPLETED,
            ReleaseStatus.DELAYED,
            ReleaseStatus.CANCELLED,
            ReleaseStatus.REVISED,
        )

    def can_transition_to(self, target: "ReleaseStatus") -> bool:
        """Check if transition to target is allowed."""
        transitions = {
            ReleaseStatus.PLANNED: {
                ReleaseStatus.ACTIVE,
                ReleaseStatus.CANCELLED,
            },
            ReleaseStatus.ACTIVE: {
                ReleaseStatus.COMPLETED,
                ReleaseStatus.DELAYED,
                ReleaseStatus.CANCELLED,
            },
            ReleaseStatus.COMPLETED: {
                ReleaseStatus.REVISED,
            },
            ReleaseStatus.DELAYED: {
                ReleaseStatus.COMPLETED,
                ReleaseStatus.CANCELLED,
            },
            ReleaseStatus.CANCELLED: set(),
            ReleaseStatus.REVISED: set(),
        }
        return target in transitions.get(self, set())


class MarketSession(str, Enum):
    """
    Trading session classification.

    Sessions:
    - PRE_MARKET: Pre-market trading
    - REGULAR: Regular trading hours
    - AFTER_HOURS: After-hours trading
    - OVERNIGHT: Overnight trading
    - CLOSED: Market closed
    """

    PRE_MARKET = "pre_market"
    REGULAR = "regular"
    AFTER_HOURS = "after_hours"
    OVERNIGHT = "overnight"
    CLOSED = "closed"

    def is_trading_session(self) -> bool:
        """Check if this is a trading session."""
        return self in (
            MarketSession.PRE_MARKET,
            MarketSession.REGULAR,
            MarketSession.AFTER_HOURS,
        )


class WindowType(str, Enum):
    """
    Type of time window for market reaction analysis.

    Types:
    - PRE_EVENT: Window before event
    - POST_EVENT: Window after event
    - FULL_EVENT: Complete event window
    - CUSTOM: User-defined window
    """

    PRE_EVENT = "pre_event"
    POST_EVENT = "post_event"
    FULL_EVENT = "full_event"
    CUSTOM = "custom"


class Frequency(str, Enum):
    """
    Data frequency classification.

    Frequencies:
    - INTRADAILY: Multiple times per day
    - DAILY: Once per day
    - WEEKLY: Once per week
    - MONTHLY: Once per month
    - QUARTERLY: Once per quarter
    - ANNUAL: Once per year
    - IRREGULAR: No fixed schedule
    """

    INTRADAILY = "intradaily"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    IRREGULAR = "irregular"

    def get_expected_interval(self) -> Optional[timedelta]:
        """Get expected interval between releases."""
        intervals = {
            Frequency.INTRADAILY: timedelta(hours=1),
            Frequency.DAILY: timedelta(days=1),
            Frequency.WEEKLY: timedelta(weeks=1),
            Frequency.MONTHLY: timedelta(days=30),
            Frequency.QUARTERLY: timedelta(days=90),
            Frequency.ANNUAL: timedelta(days=365),
            Frequency.IRREGULAR: None,
        }
        return intervals.get(self)
