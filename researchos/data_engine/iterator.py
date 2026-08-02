"""
HistoricalIterator — iterate through historical market data chronologically.

Based on Article XVII: Object Model — Data Layer.

The HistoricalIterator provides efficient, deterministic iteration over
historical data records with support for windowing, batching, and
time-range filtering.

Guarantees:
    - Deterministic: Same dataset → same iteration order
    - Chronological: Always iterates in time-ascending order
    - Memory-efficient: Supports windowed iteration without loading all data
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Callable, Iterator, List, Optional, TypeVar

from researchos.data_engine.candle import Candle
from researchos.data_engine.dataset import HistoricalDataset
from researchos.data_engine.contracts import Timeframe

T = TypeVar("T")


class HistoricalIterator:
    """
    Iterate through historical data records chronologically.

    Supports:
        - Full dataset iteration
        - Time-range bounded iteration
        - Windowed iteration (rolling windows)
        - Batch iteration
        - Record transformation

    Usage:
        iterator = HistoricalIterator(dataset)
        for candle in iterator:
            process(candle)

        # With windowing
        for window in iterator.windows(window_size=20):
            process_window(window)

        # No-lookahead: never expose data after a cutoff
        iterator = HistoricalIterator(dataset, as_of=as_of_datetime)

    No-lookahead guarantee:
        - When `as_of` is provided, no record with a timestamp later than
          `as_of` is ever exposed, including inside windows and batches.
        - Windows are emitted chronologically; each window contains only
          records up to its final timestamp.
    """

    def __init__(
        self,
        dataset: HistoricalDataset,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        reverse: bool = False,
        as_of: Optional[datetime] = None,
    ):
        """
        Args:
            dataset: The dataset to iterate over.
            start_time: Only include records at or after this time.
            end_time: Only include records at or before this time.
            reverse: Iterate in reverse chronological order.
            as_of: No-lookahead cutoff. Only records with timestamp at or
                before this time are visible. Future data is never exposed.
        """
        self.dataset = dataset
        self.start_time = start_time
        self.end_time = end_time
        self.reverse = reverse
        self.as_of = as_of
        self._index = 0
        self._indices = self._build_index()

    def _build_index(self) -> List[int]:
        """Build a list of indices matching the time filters."""
        indices = []
        for i, record in enumerate(self.dataset._records):
            ts = record.timestamp if hasattr(record, "timestamp") else None
            if ts is None:
                continue
            if self.start_time and ts < self.start_time:
                continue
            if self.end_time and ts > self.end_time:
                continue
            if self.as_of is not None and ts > self.as_of:
                continue
            indices.append(i)
        if self.reverse:
            indices.reverse()
        return indices

    def __iter__(self) -> Iterator[Any]:
        return self

    def __next__(self) -> Any:
        if self._index >= len(self._indices):
            raise StopIteration
        idx = self._indices[self._index]
        self._index += 1
        return self.dataset._records[idx]

    def __len__(self) -> int:
        return len(self._indices)

    def reset(self) -> None:
        self._index = 0

    def take(self, count: int) -> List[Any]:
        records = []
        for _ in range(count):
            try:
                records.append(next(self))
            except StopIteration:
                break
        return records

    def skip(self, count: int) -> int:
        before = self._index
        self._index = min(self._index + count, len(self._indices))
        return self._index - before

    def windows(self, window_size: int, step: int = 1) -> Iterator[List[Any]]:
        i = 0
        while i + window_size <= len(self._indices):
            window = [
                self.dataset._records[self._indices[j]]
                for j in range(i, i + window_size)
            ]
            yield window
            i += step

    def time_windows(
        self,
        window_duration: timedelta,
        step: Optional[timedelta] = None,
    ) -> Iterator[List[Any]]:
        if not self._indices:
            return
        step = step or window_duration
        current_start = self.dataset._records[self._indices[0]].timestamp
        while current_start <= self.dataset._records[self._indices[-1]].timestamp:
            window_end = current_start + window_duration
            window = []
            for idx in self._indices:
                ts = self.dataset._records[idx].timestamp
                if current_start <= ts < window_end:
                    window.append(self.dataset._records[idx])
            if window:
                yield window
            current_start += step

    def map(self, func: Callable[[Any], T]) -> Iterator[T]:
        for record in self:
            yield func(record)

    def filter(self, predicate: Callable[[Any], bool]) -> Iterator[Any]:
        for record in self:
            if predicate(record):
                yield record

    def to_list(self) -> List[Any]:
        return list(self)

    @property
    def is_exhausted(self) -> bool:
        return self._index >= len(self._indices)

    @property
    def progress(self) -> float:
        if not self._indices:
            return 1.0
        return min(1.0, self._index / len(self._indices))

