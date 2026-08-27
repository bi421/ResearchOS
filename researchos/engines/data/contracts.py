"""
Contracts, enums, and data classes for the Data Engine.

Based on Article XVII: Object Model â€” Data Layer.

Defines the shared vocabulary used across all data engine objects.
All enums and configs are deterministic for repeatability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class Timeframe(str, Enum):
    """Standard market data timeframes."""

    TICK = "tick"
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"
    MN1 = "1mo"

    @classmethod
    def from_string(cls, value: str) -> "Timeframe":
        """Parse a timeframe from a string, case-insensitive."""
        mapping = {
            "tick": cls.TICK,
            "1m": cls.M1,
            "1min": cls.M1,
            "minute": cls.M1,
            "5m": cls.M5,
            "5min": cls.M5,
            "15m": cls.M15,
            "15min": cls.M15,
            "30m": cls.M30,
            "30min": cls.M30,
            "1h": cls.H1,
            "1hour": cls.H1,
            "hour": cls.H1,
            "4h": cls.H4,
            "4hour": cls.H4,
            "1d": cls.D1,
            "1day": cls.D1,
            "daily": cls.D1,
            "day": cls.D1,
            "1w": cls.W1,
            "1week": cls.W1,
            "weekly": cls.W1,
            "week": cls.W1,
            "1mo": cls.MN1,
            "1month": cls.MN1,
            "monthly": cls.MN1,
            "month": cls.MN1,
        }
        normalized = value.lower().strip()
        if normalized not in mapping:
            raise ValueError(f"Unknown timeframe '{value}'. Valid options: {list(mapping.keys())}")
        return mapping[normalized]

    def to_seconds(self) -> int:
        """Convert timeframe to seconds for calculations."""
        mapping = {
            self.TICK: 0,
            self.M1: 60,
            self.M5: 300,
            self.M15: 900,
            self.M30: 1800,
            self.H1: 3600,
            self.H4: 14400,
            self.D1: 86400,
            self.W1: 604800,
            self.MN1: 2592000,
        }
        return mapping[self]


class DataSource(str, Enum):
    """Supported data sources."""

    CSV = "csv"
    SQLITE = "sqlite"
    YAHOO = "yahoo"
    ALPACA = "alpaca"
    POLYGON = "polygon"
    CUSTOM = "custom"


class DataQuality(str, Enum):
    """Quality grade of a dataset."""

    RAW = "Raw"
    CLEANED = "Cleaned"
    NORMALIZED = "Normalized"
    VALIDATED = "Validated"
    CERTIFIED = "Certified"


class DatasetStatus(str, Enum):
    """Lifecycle status of a dataset."""

    PENDING = "Pending"
    LOADING = "Loading"
    READY = "Ready"
    VALIDATED = "Validated"
    ARCHIVED = "Archived"
    FAILED = "Failed"


class DatasetType(str, Enum):
    """Type of market data contained in a dataset."""

    CANDLE = "candle"
    TICK = "tick"
    QUOTE = "quote"
    TRADE = "trade"
    ORDERBOOK = "orderbook"

    @classmethod
    def from_string(cls, value: str) -> "DatasetType":
        """Parse a dataset type from a string, case-insensitive."""
        mapping = {
            "candle": cls.CANDLE,
            "candles": cls.CANDLE,
            "ohlc": cls.CANDLE,
            "ohlcv": cls.CANDLE,
            "bar": cls.CANDLE,
            "bars": cls.CANDLE,
            "tick": cls.TICK,
            "ticks": cls.TICK,
            "quote": cls.QUOTE,
            "quotes": cls.QUOTE,
            "trade": cls.TRADE,
            "trades": cls.TRADE,
            "orderbook": cls.ORDERBOOK,
            "order_book": cls.ORDERBOOK,
            "orderbooklevel": cls.ORDERBOOK,
        }
        normalized = value.lower().strip()
        if normalized not in mapping:
            raise ValueError(
                f"Unknown dataset type '{value}'. Valid options: {list(mapping.keys())}"
            )
        return mapping[normalized]

    def matches(self, data_type: str) -> bool:
        """Whether this type matches a string data_type label."""
        return self.value == str(data_type).lower().strip()


class QuoteSide(str, Enum):
    """Side of a quote."""

    BID = "bid"
    ASK = "ask"
    MID = "mid"


class TradeSide(str, Enum):
    """Side of a trade."""

    BUY = "buy"
    SELL = "sell"
    UNKNOWN = "unknown"


@dataclass
class CandleField:
    """Field mapping configuration for OHLCV data."""

    timestamp: str = "timestamp"
    open: str = "open"
    high: str = "high"
    low: str = "low"
    close: str = "close"
    volume: str = "volume"
    symbol: str = "symbol"

    def to_dict(self) -> Dict[str, str]:
        return {
            "timestamp": self.timestamp,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "symbol": self.symbol,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "CandleField":
        return cls(
            timestamp=data.get("timestamp", "timestamp"),
            open=data.get("open", "open"),
            high=data.get("high", "high"),
            low=data.get("low", "low"),
            close=data.get("close", "close"),
            volume=data.get("volume", "volume"),
            symbol=data.get("symbol", "symbol"),
        )


@dataclass
class LoaderConfig:
    """
    Configuration for data loading operations.

    Attributes:
        field_mapping: Custom field name mappings.
        date_format: Expected date format string (e.g., "%Y-%m-%d %H:%M:%S").
        timezone: Source timezone (e.g., "America/New_York").
        delimiter: CSV delimiter (default: ",").
        has_header: Whether the file has a header row.
        batch_size: Number of records to process per batch.
        max_records: Maximum records to load (0 = unlimited).
        skip_errors: Whether to skip malformed rows.
        normalize_timezone: Whether to normalize to UTC.
    """

    field_mapping: Optional[CandleField] = None
    date_format: str = "%Y-%m-%d %H:%M:%S"
    timezone: str = "UTC"
    delimiter: str = ","
    has_header: bool = True
    batch_size: int = 10000
    max_records: int = 0
    skip_errors: bool = False
    normalize_timezone: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_mapping": self.field_mapping.to_dict() if self.field_mapping else None,
            "date_format": self.date_format,
            "timezone": self.timezone,
            "delimiter": self.delimiter,
            "has_header": self.has_header,
            "batch_size": self.batch_size,
            "max_records": self.max_records,
            "skip_errors": self.skip_errors,
            "normalize_timezone": self.normalize_timezone,
            "parameters": dict(self.parameters),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LoaderConfig":
        fm = data.get("field_mapping")
        return cls(
            field_mapping=CandleField.from_dict(fm) if fm else None,
            date_format=data.get("date_format", "%Y-%m-%d %H:%M:%S"),
            timezone=data.get("timezone", "UTC"),
            delimiter=data.get("delimiter", ","),
            has_header=bool(data.get("has_header", True)),
            batch_size=int(data.get("batch_size", 10000)),
            max_records=int(data.get("max_records", 0)),
            skip_errors=bool(data.get("skip_errors", False)),
            normalize_timezone=bool(data.get("normalize_timezone", True)),
            parameters=dict(data.get("parameters", {})),
        )


@dataclass
class ValidationReport:
    """Report of dataset validation results."""

    total_records: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    gaps_found: int = 0
    missing_candles: int = 0
    duplicates_found: int = 0
    outlier_records: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def quality_score(self) -> float:
        """Compute a quality score between 0.0 and 1.0."""
        if self.total_records == 0:
            return 0.0
        valid_ratio = self.valid_records / self.total_records
        gap_penalty = min(self.gaps_found / max(self.total_records, 1) * 10, 0.3)
        dup_penalty = min(self.duplicates_found / max(self.total_records, 1) * 10, 0.2)
        return max(0.0, min(1.0, valid_ratio - gap_penalty - dup_penalty))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_records": self.total_records,
            "valid_records": self.valid_records,
            "invalid_records": self.invalid_records,
            "gaps_found": self.gaps_found,
            "missing_candles": self.missing_candles,
            "duplicates_found": self.duplicates_found,
            "outlier_records": self.outlier_records,
            "quality_score": round(self.quality_score, 4),
            "errors": self.errors,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ValidationReport":
        return cls(
            total_records=int(data.get("total_records", 0)),
            valid_records=int(data.get("valid_records", 0)),
            invalid_records=int(data.get("invalid_records", 0)),
            gaps_found=int(data.get("gaps_found", 0)),
            missing_candles=int(data.get("missing_candles", 0)),
            duplicates_found=int(data.get("duplicates_found", 0)),
            outlier_records=int(data.get("outlier_records", 0)),
            errors=list(data.get("errors", [])),
            warnings=list(data.get("warnings", [])),
        )
