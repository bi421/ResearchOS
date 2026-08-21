"""
ResearchOS Macro Intelligence Layer - Shared Enums
"""

from enum import Enum


class ErrorType(Enum):
    """Error types for adapter operations."""

    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    AUTH_ERROR = "auth_error"
    NOT_FOUND = "not_found"
    SERVER_ERROR = "server_error"
    CLIENT_ERROR = "client_error"
    INVALID_RESPONSE = "invalid_response"
    NETWORK_ERROR = "network_error"


class HealthStatus(Enum):
    """Health status for sources."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class Severity(Enum):
    """Severity levels for alerts."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FrequencyEnum(Enum):
    """Data frequency enumeration."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    AD_HOC = "adhoc"


class SeriesType(Enum):
    """Type of series data."""

    LEVEL = "level"
    CHANGE = "change"
    YOY = "yoy"
    MOM = "mom"
    SURPRISE = "surprise"
    SPREAD = "spread"


class EventCategory(Enum):
    """Event category enumeration."""

    FOMC_MEETING = "fomc_meeting"
    FOMC_STATEMENT = "fomc_statement"
    FOMC_SUMMARY = "fomc_summary"
    FED_SPEECH = "fed_speech"
    FED_HEARING = "fed_hearing"
    DATA_RELEASE = "data_release"
    GEOPOLITICAL = "geopolitical"
    SANCTION = "sanction"
    MARKET_EVENT = "market_event"
    REGULATORY = "regulatory"


class ImportanceLevel(Enum):
    """Event importance levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(Enum):
    """Alert type enumeration."""

    WARNING = "warning"
    CRITICAL = "critical"
    SOURCE_OUTAGE = "source_outage"


class QuarantineStatus(Enum):
    """Quarantine status."""

    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    RELEASED = "released"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class PatternType(Enum):
    """Pattern type enumeration."""

    REGIME_SHIFT = "regime_shift"
    CORRELATION_BREAK = "correlation_break"
    VOLATILITY_CLUSTER = "volatility_cluster"
    TREND_ACCELERATION = "trend_acceleration"
    TREND_REVERSAL = "trend_reversal"
    INFLATION_PERSISTENCE = "inflation_persistence"
    RATE_PATH_SHIFT = "rate_path_shift"
    EVENT_SURPRISE = "event_surprise"
    MARKET_OVERREACTION = "market_overreaction"


class InflationRegime(Enum):
    """Inflation regime classification."""

    LOW = "low_inflation"
    TARGET = "target_inflation"
    ELEVATED = "elevated_inflation"
    HIGH = "high_inflation"


class GrowthRegime(Enum):
    """Growth regime classification."""

    RECOVERY = "recovery"
    EXPANSION = "expansion"
    SLOWDOWN = "slowdown"
    RECESSION = "recession"


class MonetaryRegime(Enum):
    """Monetary regime classification."""

    DOVISH_EASY = "dovish_easy"
    NEUTRAL = "neutral"
    TIGHTENING = "tightening"
    HAWKISH_RESTRICTIVE = "hawkish_restrictive"


class RiskRegime(Enum):
    """Risk regime classification."""

    RISK_ON = "risk_on"
    NEUTRAL = "neutral"
    RISK_OFF = "risk_off"
