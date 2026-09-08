"""
Phase 5.2 — macro factor feature builder (DXY, US10Y, VIX).

Builds deterministic, lookahead-safe features from macro factor closing-price
series (DXY, US10Y, VIX), aligned index-for-index with the XAUUSD bar series
they will be merged against.

Design rules (mirrors ``quant_engine.machine_learning.features``):
    * Pure Python, no ML libraries, no randomness.
    * Every feature at index ``i`` uses only information available at or
      before bar ``i`` (no lookahead).
    * Missing/misaligned macro data yields ``None`` at that index rather than
      an interpolated or synthetic value — synthetic-data-as-evidence is
      never permitted per the Phase 5.x experiment constraints.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

MACRO_SYMBOLS: tuple[str, ...] = ("DXY", "US10Y", "VIX")

# 3 features per factor: 1-bar return, 5-bar rolling mean of returns,
# 20-bar rolling z-score of level. Kept small and explainable, matching the
# "smallest scientifically valid" principle used in Phase 5.1.
_FEATURES_PER_FACTOR: tuple[str, ...] = ("return_1", "roll_mean_return_5", "roll_zscore_20")


def _rolling_apply(values: list[float | None], period: int, fn) -> list[float | None]:
    n = len(values)
    out: list[float | None] = [None] * n
    for i in range(period - 1, n):
        window = values[i - period + 1 : i + 1]
        if any(v is None for v in window):
            continue
        out[i] = fn(window)
    return out


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs)


def _pstd(xs: list[float]) -> float:
    m = _mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs))


def _returns(values: list[float | None]) -> list[float | None]:
    out: list[float | None] = [None] * len(values)
    for i in range(1, len(values)):
        prev, cur = values[i - 1], values[i]
        if prev is None or cur is None or prev == 0:
            continue
        out[i] = (cur - prev) / prev
    return out


def _zscore_series(values: list[float | None], period: int) -> list[float | None]:
    def _z(window: list[float]) -> float:
        m = _mean(window)
        s = _pstd(window)
        last = window[-1]
        return 0.0 if s == 0 else (last - m) / s

    return _rolling_apply(values, period, _z)


@dataclass(frozen=True)
class MacroFeatureSet:
    """A deterministic macro feature matrix aligned to an external index."""

    feature_names: tuple[str, ...]
    data: tuple[tuple[float | None, ...], ...]
    symbols_present: tuple[str, ...]
    symbols_missing: tuple[str, ...]


class MacroFeatureBuilder:
    """Builds DXY / US10Y / VIX derived features aligned to a target index.

    ``factor_series`` maps a subset of ``MACRO_SYMBOLS`` to closing-price
    sequences already aligned (same length, same bar order) to the target
    XAUUSD series. Callers are responsible for the alignment/resampling step
    (e.g. forward-filling a lower-frequency series to daily bars) — this
    builder performs no interpolation of its own, only feature derivation.

    Any symbol absent from ``factor_series`` (or with fewer values than the
    aligned length) is recorded in ``symbols_missing`` and its 3 feature
    columns are filled with ``None`` at every row rather than silently
    dropped, so callers/experiments can see exactly what was unavailable.
    """

    def __init__(self, aligned_length: int, factor_series: dict[str, Sequence[float | None]]):
        self.aligned_length = int(aligned_length)
        self.factor_series = {k: list(v) for k, v in factor_series.items()}

    def build(self) -> MacroFeatureSet:
        names: list[str] = []
        columns: list[list[float | None]] = []
        present: list[str] = []
        missing: list[str] = []

        for symbol in MACRO_SYMBOLS:
            series = self.factor_series.get(symbol)
            if series is None or len(series) != self.aligned_length:
                missing.append(symbol)
                for feat in _FEATURES_PER_FACTOR:
                    names.append(f"macro_{symbol}_{feat}")
                    columns.append([None] * self.aligned_length)
                continue

            present.append(symbol)
            ret1 = _returns(series)
            roll_mean5 = _rolling_apply(ret1, 5, lambda w: _mean([x for x in w if x is not None]) if all(x is not None for x in w) else None)  # noqa: E501
            zscore20 = _zscore_series(series, 20)

            names.append(f"macro_{symbol}_return_1")
            columns.append(ret1)
            names.append(f"macro_{symbol}_roll_mean_return_5")
            columns.append(roll_mean5)
            names.append(f"macro_{symbol}_roll_zscore_20")
            columns.append(zscore20)

        rows: list[tuple[float | None, ...]] = [
            tuple(columns[c][i] for c in range(len(columns))) for i in range(self.aligned_length)
        ]
        return MacroFeatureSet(
            feature_names=tuple(names),
            data=tuple(rows),
            symbols_present=tuple(present),
            symbols_missing=tuple(missing),
        )


__all__ = ["MACRO_SYMBOLS", "MacroFeatureSet", "MacroFeatureBuilder"]
