"""
DatasetStatistics — descriptive statistics for market datasets.

Based on Article XVII: Object Model — Data Layer.

Computes deterministic, auditable statistics over a HistoricalDataset:

    - record count
    - missing percentage
    - duplicate count
    - gap count
    - average spread
    - average volume
    - first/last timestamp
    - daily coverage
    - trading days
    - completeness

Guarantees:
    - Deterministic: Same dataset -> same statistics
    - Serializable: DatasetStatistics supports to_dict/from_dict
    - Pure: No mutation of the input dataset
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from researchos.data_engine.candle import Candle
from researchos.data_engine.contracts import Timeframe
from researchos.data_engine.dataset import HistoricalDataset
from researchos.data_engine.orderbook import OrderBook
from researchos.data_engine.quote import Quote
from researchos.data_engine.tick import Tick
from researchos.data_engine.trade import Trade
from researchos.data_engine.validator import DuplicateDetector

DataRecord = Any


@dataclass
class DatasetStatistics:
    """
    Descriptive statistics computed from a HistoricalDataset.

    Attributes:
        record_count: Number of records in the dataset.
        missing_percentage: Percentage of expected candles missing from the
            covered span (0.0 for non-candle or tick data).
        duplicate_count: Number of records with duplicated timestamps.
        gap_count: Number of discontinuities exceeding the expected interval.
        average_spread: Mean bid-ask spread (points) across records.
        average_volume: Mean volume across records.
        first_timestamp: ISO timestamp of the first record.
        last_timestamp: ISO timestamp of the last record.
        daily_coverage: Fraction of calendar days in the span that contain data.
        trading_days: Number of unique calendar days with records.
        completeness: Overall completeness score in [0.0, 1.0].
    """

    record_count: int = 0
    missing_percentage: float = 0.0
    duplicate_count: int = 0
    gap_count: int = 0
    average_spread: float = 0.0
    average_volume: float = 0.0
    first_timestamp: str | None = None
    last_timestamp: str | None = None
    daily_coverage: float = 0.0
    trading_days: int = 0
    completeness: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize statistics to a dict (deterministic rounding)."""
        return {
            "record_count": self.record_count,
            "missing_percentage": round(self.missing_percentage, 4),
            "duplicate_count": self.duplicate_count,
            "gap_count": self.gap_count,
            "average_spread": round(self.average_spread, 6),
            "average_volume": round(self.average_volume, 2),
            "first_timestamp": self.first_timestamp,
            "last_timestamp": self.last_timestamp,
            "daily_coverage": round(self.daily_coverage, 4),
            "trading_days": self.trading_days,
            "completeness": round(self.completeness, 4),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DatasetStatistics:
        """Restore statistics from a dict."""
        return cls(
            record_count=int(data.get("record_count", 0)),
            missing_percentage=float(data.get("missing_percentage", 0.0)),
            duplicate_count=int(data.get("duplicate_count", 0)),
            gap_count=int(data.get("gap_count", 0)),
            average_spread=float(data.get("average_spread", 0.0)),
            average_volume=float(data.get("average_volume", 0.0)),
            first_timestamp=data.get("first_timestamp"),
            last_timestamp=data.get("last_timestamp"),
            daily_coverage=float(data.get("daily_coverage", 0.0)),
            trading_days=int(data.get("trading_days", 0)),
            completeness=float(data.get("completeness", 0.0)),
        )

    def __repr__(self) -> str:
        return f"DatasetStatistics({self.record_count} records, missing={self.missing_percentage:.2f}%, gaps={self.gap_count}, dups={self.duplicate_count}, coverage={self.daily_coverage:.2f})"


def _record_timestamp(record: DataRecord) -> datetime | None:
    """Extract a record timestamp, if present."""
    return record.timestamp if hasattr(record, "timestamp") else None


def _record_spread(record: DataRecord) -> float | None:
    """Extract a numeric spread from a record, if available."""
    if isinstance(record, (Quote, OrderBook)):
        spread = record.spread
        return float(spread) if spread is not None else None
    if isinstance(record, Tick):
        if record.bid is not None and record.ask is not None:
            return float(record.ask - record.bid)
        return None
    if isinstance(record, Candle):
        if record.spread is not None:
            return float(record.spread)
        return None
    return None


def _record_volume(record: DataRecord) -> float:
    """Extract a numeric volume from a record, if available."""
    if isinstance(record, Candle):
        return float(record.volume) if record.volume is not None else 0.0
    if isinstance(record, Tick):
        return float(record.volume) if record.volume is not None else 0.0
    if isinstance(record, Trade):
        return float(record.volume) if record.volume is not None else 0.0
    return 0.0


def compute_dataset_statistics(
    dataset: HistoricalDataset,
    gap_tolerance_factor: float = 1.0,
) -> DatasetStatistics:
    """
    Compute deterministic statistics for a dataset.

    Args:
        dataset: The dataset to analyze.
        gap_tolerance_factor: Multiplier above the expected interval that
            qualifies a discontinuity as a gap. 1.0 means any missed interval
            counts.

    Returns:
        DatasetStatistics with all computed metrics.

    Raises:
        ValueError: If the gap tolerance factor is not positive.
    """
    if gap_tolerance_factor <= 0:
        raise ValueError(f"gap_tolerance_factor must be positive, got {gap_tolerance_factor}")

    stats = DatasetStatistics()
    records = dataset._records
    stats.record_count = len(records)

    if not records:
        return stats

    sorted_records = sorted(
        records,
        key=lambda r: _record_timestamp(r) or datetime.min.replace(tzinfo=timezone.utc),
    )

    first = _record_timestamp(sorted_records[0])
    last = _record_timestamp(sorted_records[-1])

    if first is not None:
        stats.first_timestamp = first.isoformat()
    if last is not None:
        stats.last_timestamp = last.isoformat()

    # Expected interval for candle-like time series
    expected_seconds = 0
    try:
        expected_seconds = Timeframe.from_string(dataset.timeframe).to_seconds()
    except ValueError:
        expected_seconds = 0

    # Duplicates
    stats.duplicate_count = len(DuplicateDetector().detect(sorted_records))

    # Missing / gaps for known-interval time series
    missing_count = 0
    expected_total = stats.record_count
    if expected_seconds > 0 and first is not None and last is not None:
        span = (last - first).total_seconds()
        if span > 0:
            expected_total = int(span // expected_seconds) + 1
        gap_count = 0
        for i in range(1, len(sorted_records)):
            prev = _record_timestamp(sorted_records[i - 1])
            curr = _record_timestamp(sorted_records[i])
            if prev is None or curr is None:
                continue
            delta = (curr - prev).total_seconds()
            if delta > expected_seconds * gap_tolerance_factor:
                gap_count += 1
        stats.gap_count = gap_count
        missing_count = max(0, expected_total - stats.record_count)
        if expected_total > 0:
            stats.missing_percentage = min(100.0, 100.0 * missing_count / expected_total)

    # Average spread
    spreads: list[float] = []
    for record in sorted_records:
        spread = _record_spread(record)
        if spread is not None:
            spreads.append(spread)
    if spreads:
        stats.average_spread = sum(spreads) / len(spreads)

    # Average volume
    volumes: list[float] = []
    for record in sorted_records:
        volumes.append(_record_volume(record))
    if volumes:
        stats.average_volume = sum(volumes) / len(volumes)

    # Daily coverage and trading days
    dates = set()
    for record in sorted_records:
        ts = _record_timestamp(record)
        if ts is None:
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        dates.add(ts.date())
    stats.trading_days = len(dates)
    if dates and first is not None and last is not None:
        first_date = first.date() if first.tzinfo else first.replace(tzinfo=timezone.utc).date()
        last_date = last.date() if last.tzinfo else last.replace(tzinfo=timezone.utc).date()
        day_span = (last_date - first_date).days + 1
        if day_span > 0:
            stats.daily_coverage = min(1.0, len(dates) / day_span)

    # Completeness in [0, 1]
    if expected_total > 0:
        completeness = 1.0 - (missing_count + stats.duplicate_count) / expected_total
        stats.completeness = max(0.0, min(1.0, completeness))

    return stats
