"""Pure validation helpers for MT5 XAUUSD M1 acquisition.

The MT5 terminal is deliberately not imported here.  This keeps validation
portable and testable in CI while the acquisition adapter remains an external
Python 3.12 boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import math
from typing import Iterable, Mapping


REQUIRED_FIELDS = (
    "time",
    "open",
    "high",
    "low",
    "close",
    "tick_volume",
    "spread",
    "real_volume",
)


@dataclass(frozen=True)
class ValidationReport:
    rows: int
    unique_timestamps: int
    duplicate_timestamps: int
    out_of_range_rows: int
    invalid_ohlc_rows: int
    invalid_volume_flags: int
    negative_spread_rows: int
    max_gap_seconds: int
    gap_count_over_60s: int

    @property
    def passed_integrity(self) -> bool:
        return all(
            value == 0
            for value in (
                self.duplicate_timestamps,
                self.out_of_range_rows,
                self.invalid_ohlc_rows,
                self.invalid_volume_flags,
                self.negative_spread_rows,
            )
        )


def _finite(value: object) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _epoch_seconds(value: object) -> int:
    if isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    return int(value)


def validate_m1_rows(
    rows: Iterable[Mapping[str, object]],
    *,
    start_epoch: int,
    end_epoch: int,
) -> ValidationReport:
    """Validate broker rows without imposing a false 24/7 continuity rule."""
    materialized = list(rows)
    timestamps = [_epoch_seconds(row["time"]) for row in materialized]
    unique = set(timestamps)

    duplicate_count = len(timestamps) - len(unique)
    out_of_range = sum(
        not (start_epoch <= ts <= end_epoch) for ts in timestamps
    )

    invalid_ohlc = 0
    invalid_volume_flags = 0
    negative_spread = 0
    for row in materialized:
        values = [row[name] for name in ("open", "high", "low", "close")]
        if not all(_finite(value) for value in values):
            invalid_ohlc += 1
        else:
            open_, high, low, close = map(float, values)
            if (
                open_ <= 0
                or high <= 0
                or low <= 0
                or close <= 0
                or high < max(open_, close)
                or low > min(open_, close)
                or high < low
            ):
                invalid_ohlc += 1

        if not _finite(row["tick_volume"]) or float(row["tick_volume"]) < 0:
            invalid_volume_flags += 1
        if not _finite(row["real_volume"]) or float(row["real_volume"]) < 0:
            invalid_volume_flags += 1
        if not _finite(row["spread"]) or float(row["spread"]) < 0:
            negative_spread += 1

    ordered = sorted(unique)
    gaps = [b - a for a, b in zip(ordered, ordered[1:]) if b - a > 60]

    return ValidationReport(
        rows=len(materialized),
        unique_timestamps=len(unique),
        duplicate_timestamps=duplicate_count,
        out_of_range_rows=out_of_range,
        invalid_ohlc_rows=invalid_ohlc,
        invalid_volume_flags=invalid_volume_flags,
        negative_spread_rows=negative_spread,
        max_gap_seconds=max((b - a for a, b in zip(ordered, ordered[1:])), default=0),
        gap_count_over_60s=len(gaps),
    )
