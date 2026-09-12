"""Canonical prepared-input contract for Phase 5.2 execution.

The preparation stage is intentionally separate from model execution so the
same immutable dataset, labels, source indices and macro diagnostics are used
by every feature-set comparison and by the canonical report.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from .alignment import validate_exact_timestamp_alignment
from .contracts import Phase52Result
from .dataset import build_macro_augmented_dataset
from .macro_features import MacroFeatureSet
from .provenance import build_input_provenance


@dataclass(frozen=True)
class Phase52PreparedData:
    """Single materialized Phase 5.2 input shared by all feature sets."""

    close: tuple[float, ...]
    high: tuple[float, ...]
    low: tuple[float, ...]
    volume: tuple[float, ...]
    timestamps: tuple[Any, ...]
    macro_timestamps: dict[str, tuple[Any, ...]]
    macro_factor_series: dict[str, tuple[float | None, ...]]
    dataset: Any
    macro_diagnostics: MacroFeatureSet
    input_provenance: dict[str, Any]

    @classmethod
    def build(
        cls,
        close: Sequence[Any],
        high: Sequence[Any],
        low: Sequence[Any],
        volume: Sequence[Any],
        timestamps: Sequence[Any],
        macro_timestamps: dict[str, Sequence[Any]],
        macro_factor_series: dict[str, Sequence[float | None]],
        *,
        horizon: int,
        threshold: float,
        required_macro_symbols: Sequence[str] = ("DXY", "US10Y", "VIX"),
    ) -> "Phase52PreparedData":
        close_t = tuple(float(v) for v in close)
        high_t = tuple(float(v) for v in high)
        low_t = tuple(float(v) for v in low)
        volume_t = tuple(float(v) for v in volume)
        timestamp_t = tuple(timestamps)
        if not (len(high_t) == len(low_t) == len(volume_t) == len(timestamp_t) == len(close_t)):
            raise ValueError("Prepared price data and timestamps must have equal length")

        macro_ts_t = {str(k): tuple(v) for k, v in macro_timestamps.items()}
        macro_series_t = {str(k): tuple(v) for k, v in macro_factor_series.items()}
        for symbol in required_macro_symbols:
            if symbol not in macro_ts_t or symbol not in macro_series_t:
                raise ValueError(f"Prepared inputs missing required macro symbol: {symbol}")
            if len(macro_ts_t[symbol]) != len(timestamp_t):
                raise ValueError(f"Prepared macro timestamps misaligned: {symbol}")
            if len(macro_series_t[symbol]) != len(timestamp_t):
                raise ValueError(f"Prepared macro series misaligned: {symbol}")
            validate_exact_timestamp_alignment(timestamp_t, macro_ts_t[symbol], symbol)

        input_provenance = build_input_provenance(
            timestamp_t,
            close_t,
            high_t,
            low_t,
            volume_t,
            macro_ts_t,
            macro_series_t,
            required_macro_symbols,
        )
        dataset, macro_diag = build_macro_augmented_dataset(
            close_t,
            high_t,
            low_t,
            volume_t,
            macro_series_t,
            horizon,
            threshold,
        )
        return cls(
            close=close_t,
            high=high_t,
            low=low_t,
            volume=volume_t,
            timestamps=timestamp_t,
            macro_timestamps=macro_ts_t,
            macro_factor_series=macro_series_t,
            dataset=dataset,
            macro_diagnostics=macro_diag,
            input_provenance=input_provenance,
        )

    @property
    def sample_count(self) -> int:
        return int(self.dataset.sample_count)

    @property
    def source_indices(self) -> tuple[int, ...]:
        return tuple(self.dataset.metadata["source_indices"])

    @property
    def feature_names(self) -> tuple[str, ...]:
        return tuple(self.dataset.feature_names)

    def validate(self, required_macro_symbols: tuple[str, ...]) -> None:
        """Fail closed if the prepared object violates its identity contract."""
        n = len(self.close)
        if not (len(self.high) == len(self.low) == len(self.volume) == len(self.timestamps) == n):
            raise ValueError("Prepared price data and timestamps must have equal length")
        for symbol in required_macro_symbols:
            if symbol not in self.macro_timestamps:
                raise ValueError(f"Prepared macro timestamps missing: {symbol}")
            if symbol not in self.macro_factor_series:
                raise ValueError(f"Prepared macro series missing: {symbol}")
            if len(self.macro_timestamps[symbol]) != n:
                raise ValueError(f"Prepared macro timestamps misaligned: {symbol}")
            if len(self.macro_factor_series[symbol]) != n:
                raise ValueError(f"Prepared macro series misaligned: {symbol}")
            validate_exact_timestamp_alignment(self.timestamps, self.macro_timestamps[symbol], symbol)
        if len(self.source_indices) != self.sample_count:
            raise ValueError("Dataset source_indices length does not equal sample_count")
        if tuple(sorted(self.source_indices)) != self.source_indices:
            raise ValueError("Dataset source_indices must be monotonic")
        if len(set(self.source_indices)) != len(self.source_indices):
            raise ValueError("Dataset source_indices must be unique")
        if any(i < 0 or i >= n for i in self.source_indices):
            raise ValueError("Dataset source_indices contain out-of-range rows")
        if not self.input_provenance.get("combined_input_hash"):
            raise ValueError("Prepared input provenance is missing combined_input_hash")

    def blocked_if_insufficient(
        self, train_size: int, validation_size: int
    ) -> Phase52Result | None:
        required = train_size + validation_size
        if self.sample_count < required:
            return Phase52Result.blocked(
                reason="REAL XAUUSD + MACRO DATA REQUIRED (insufficient aligned samples after merge)",
                macro_symbols_present=self.macro_diagnostics.symbols_present,
                macro_symbols_missing=self.macro_diagnostics.symbols_missing,
            )
        return None


__all__ = ["Phase52PreparedData"]
