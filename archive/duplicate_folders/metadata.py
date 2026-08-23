"""
DatasetMetadata — comprehensive metadata for a historical dataset.

Based on Article XVII: Object Model — Data Layer.

DatasetMetadata captures all descriptive information about a dataset
including its source, coverage, quality, and statistics. It is separate
from the HistoricalDataset to allow metadata-only queries without
loading the full dataset into memory.

Guarantees:
    - Deterministic: Same dataset → same metadata
    - Serializable: Supports to_dict/from_dict
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id
from researchos.core.lifecycle import LifecycleStage
from researchos.core.timestamp import parse_timestamp
from researchos.data_engine.contracts import DataQuality, DatasetStatus


class DatasetMetadata(BaseObject):
    """
    Comprehensive metadata for a historical dataset.

    This object is designed to be lightweight so it can be stored
    and queried separately from the full dataset records.

    Attributes:
        dataset_id: Link to the HistoricalDataset.
        symbol: The trading symbol.
        timeframe: The data timeframe.
        data_type: Type of data (candle, tick, quote, trade, orderbook).
        source: Data source identifier.
        source_file: Original source file path.
        record_count: Total number of records.
        start_time: UTC timestamp of first record.
        end_time: UTC timestamp of last record.
        duration_days: Total days covered.
        timezone: Source timezone the data was recorded in.
        quality: Data quality grade.
        status: Dataset lifecycle status.
        dataset_hash: Content hash from HistoricalDataset.
        version: Dataset version.
        statistics: Dict of computed statistics.
        tags: Tags for categorisation.
        description: Human-readable description.
    """

    def __init__(
        self,
        dataset_id: str,
        symbol: str,
        timeframe: str,
        data_type: str = "candle",
        source: str = "",
        source_file: str = "",
        record_count: int = 0,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        timezone: str = "UTC",
        quality: str = "Raw",
        status: str = "Pending",
        dataset_hash: str = "",
        version: str = "1.0.0",
        statistics: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        description: str = "",
        ontology_tags: list[str] | None = None,
        id: str | None = None,
    ):
        if id is None:
            seed = f"DatasetMetadata|{dataset_id}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.dataset_id = dataset_id
        self.symbol = symbol
        self.timeframe = timeframe
        self.data_type = data_type
        self.source = source
        self.source_file = source_file
        self.record_count = record_count
        self.start_time = start_time
        self.end_time = end_time
        self.timezone = timezone
        self.quality = DataQuality(quality) if isinstance(quality, str) else quality
        self.status = DatasetStatus(status) if isinstance(status, str) else status
        self.dataset_hash = dataset_hash
        self.version = version
        self.statistics: dict[str, Any] = statistics or {}
        self.tags: list[str] = tags or []
        self.description = description

        self.lifecycle.transition(
            LifecycleStage.CREATED,
            reason=f"DatasetMetadata created: {symbol} {timeframe}",
        )

    @property
    def duration_days(self) -> float:
        """Total days covered by the dataset."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds() / 86400.0
        return 0.0

    @property
    def date_range(self) -> tuple[datetime, datetime] | None:
        """Covered date range as a (start, end) tuple, or None."""
        if self.start_time and self.end_time:
            return (self.start_time, self.end_time)
        return None

    @property
    def avg_records_per_day(self) -> float:
        """Average number of records per day."""
        days = self.duration_days
        if days > 0:
            return self.record_count / days
        return float(self.record_count)

    def _to_hashable_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "data_type": self.data_type,
            "source": self.source,
            "source_file": self.source_file,
            "record_count": self.record_count,
            "start_time": self.start_time.isoformat() if self.start_time else "",
            "end_time": self.end_time.isoformat() if self.end_time else "",
            "timezone": self.timezone,
            "quality": self.quality.value if isinstance(self.quality, DataQuality) else self.quality,
            "status": self.status.value if isinstance(self.status, DatasetStatus) else self.status,
            "dataset_hash": self.dataset_hash,
            "version": self.version,
            "statistics": dict(sorted(self.statistics.items())) if self.statistics else {},
            "tags": sorted(self.tags),
            "description": self.description,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "dataset_id": self.dataset_id,
                "symbol": self.symbol,
                "timeframe": self.timeframe,
                "data_type": self.data_type,
                "source": self.source,
                "source_file": self.source_file,
                "record_count": self.record_count,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "date_range": ([self.start_time.isoformat(), self.end_time.isoformat()] if self.start_time and self.end_time else None),
                "duration_days": round(self.duration_days, 4),
                "avg_records_per_day": round(self.avg_records_per_day, 2),
                "timezone": self.timezone,
                "quality": self.quality.value if isinstance(self.quality, DataQuality) else self.quality,
                "status": self.status.value if isinstance(self.status, DatasetStatus) else self.status,
                "dataset_hash": self.dataset_hash,
                "version": self.version,
                "statistics": self.statistics,
                "tags": self.tags,
                "description": self.description,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DatasetMetadata:
        obj = super().from_dict(data)
        obj.dataset_id = data["dataset_id"]
        obj.symbol = data["symbol"]
        obj.timeframe = data["timeframe"]
        obj.data_type = data.get("data_type", "candle")
        obj.source = data.get("source", "")
        obj.source_file = data.get("source_file", "")
        obj.record_count = int(data.get("record_count", 0))
        obj.start_time = parse_timestamp(data["start_time"]) if data.get("start_time") else None
        obj.end_time = parse_timestamp(data["end_time"]) if data.get("end_time") else None
        obj.timezone = data.get("timezone", "UTC")
        obj.quality = DataQuality(data.get("quality", "Raw"))
        obj.status = DatasetStatus(data.get("status", "Pending"))
        obj.dataset_hash = data.get("dataset_hash", "")
        obj.version = data.get("version", "1.0.0")
        obj.statistics = dict(data.get("statistics", {}))
        obj.tags = list(data.get("tags", []))
        obj.description = data.get("description", "")
        return obj

    def __repr__(self) -> str:
        return f"DatasetMetadata({self.symbol}, {self.timeframe}, {self.record_count} records, {self.quality.value})"
