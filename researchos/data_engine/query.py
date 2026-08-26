"""
RangeQuery and MultiSymbolQuery — efficient data querying for market data.

Based on Article XVII: Object Model — Data Layer.

Provides structured query objects for filtering and aggregating
historical market data across time ranges and symbol combinations.

Guarantees:
    - Deterministic: Same query parameters → same results
    - Serializable: All queries support to_dict/from_dict
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from researchos.core.timestamp import _parse_iso_compat
from researchos.data_engine.candle import Candle
from researchos.data_engine.dataset import HistoricalDataset


@dataclass
class RangeQuery:
    """
    Query for filtering data within a specific time range.

    Attributes:
        symbol: Symbol to query.
        timeframe: Timeframe to query.
        start_time: Start of the time range (ISO 8601).
        end_time: End of the time range (ISO 8601).
        limit: Maximum number of records to return (0 = unlimited).
        offset: Number of records to skip.
        sort_order: Sort order ('asc' or 'desc').
        fields: Specific fields to return (empty = all fields).
    """

    symbol: str
    timeframe: str
    start_time: str = ""
    end_time: str = ""
    limit: int = 0
    offset: int = 0
    sort_order: str = "asc"
    fields: list[str] = field(default_factory=list)

    def execute(self, dataset: HistoricalDataset) -> list[Candle]:
        if dataset.symbol != self.symbol:
            return []
        if dataset.timeframe != self.timeframe:
            return []
        results: list[Candle] = []
        for record in dataset._records:
            if not isinstance(record, Candle):
                continue
            ts = record.timestamp
            if self.start_time:
                start_dt = _parse_iso_compat(self.start_time)
                if ts < start_dt:
                    continue
            if self.end_time:
                end_dt = _parse_iso_compat(self.end_time)
                if ts > end_dt:
                    continue
            results.append(record)
        if self.sort_order == "desc":
            results.sort(key=lambda r: r.timestamp, reverse=True)
        else:
            results.sort(key=lambda r: r.timestamp)
        if self.offset > 0:
            results = results[self.offset :]
        if self.limit > 0:
            results = results[: self.limit]
        return results

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "limit": self.limit,
            "offset": self.offset,
            "sort_order": self.sort_order,
            "fields": list(self.fields),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RangeQuery:
        return cls(
            symbol=data["symbol"],
            timeframe=data["timeframe"],
            start_time=data.get("start_time", ""),
            end_time=data.get("end_time", ""),
            limit=int(data.get("limit", 0)),
            offset=int(data.get("offset", 0)),
            sort_order=data.get("sort_order", "asc"),
            fields=list(data.get("fields", [])),
        )


@dataclass
class MultiSymbolQuery:
    """
    Query across multiple symbols.

    Attributes:
        symbols: List of symbols to query.
        timeframe: Timeframe to query.
        start_time: Start of the time range.
        end_time: End of the time range.
        aggregate: Aggregation function ('none', 'mean', 'sum', 'min', 'max').
        limit: Maximum records per symbol.
        sort_by: Field to sort by.
        sort_order: Sort order.
    """

    symbols: list[str] = field(default_factory=list)
    timeframe: str = ""
    start_time: str = ""
    end_time: str = ""
    aggregate: str = "none"
    limit: int = 0
    sort_by: str = "timestamp"
    sort_order: str = "asc"

    def execute(
        self,
        datasets: dict[str, HistoricalDataset],
    ) -> dict[str, list[Any]]:
        results: dict[str, list[Any]] = {}
        for symbol in self.symbols:
            dataset = datasets.get(symbol)
            if dataset is None:
                continue
            range_query = RangeQuery(
                symbol=symbol,
                timeframe=self.timeframe,
                start_time=self.start_time,
                end_time=self.end_time,
                limit=self.limit,
                sort_order=self.sort_order,
            )
            records = range_query.execute(dataset)
            if records:
                results[symbol] = records
        return results

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbols": self.symbols,
            "timeframe": self.timeframe,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "aggregate": self.aggregate,
            "limit": self.limit,
            "sort_by": self.sort_by,
            "sort_order": self.sort_order,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MultiSymbolQuery:
        return cls(
            symbols=list(data.get("symbols", [])),
            timeframe=data.get("timeframe", ""),
            start_time=data.get("start_time", ""),
            end_time=data.get("end_time", ""),
            aggregate=data.get("aggregate", "none"),
            limit=int(data.get("limit", 0)),
            sort_by=data.get("sort_by", "timestamp"),
            sort_order=data.get("sort_order", "asc"),
        )
