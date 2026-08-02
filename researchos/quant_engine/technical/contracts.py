"""
Technical Analysis Engine — contracts, enums, and dataclass models.

Based on Article XVII: Object Model — Quant Engine Layer.

This engine provides a deterministic, vectorized indicator framework.
Indicators are pure computations over OHLCV bar series. No trading logic,
no signals, no broker execution — research only.

Determinism guarantees:
    - Same OHLCV input + same indicator params → identical outputs
    - No RNG, no hidden state, no wall-clock dependence
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class IndicatorCategory(str, Enum):
    """High-level category of an indicator."""

    TREND = "trend"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    VOLUME = "volume"
    TREND_STRENGTH = "trend_strength"
    MACD = "macd"


class IndicatorFamily(str, Enum):
    """The concrete family of an indicator."""

    SMA = "SMA"
    EMA = "EMA"
    WMA = "WMA"
    HMA = "HMA"
    VWMA = "VWMA"
    RSI = "RSI"
    STOCHASTIC = "Stochastic"
    CCI = "CCI"
    ROC = "ROC"
    MOMENTUM = "Momentum"
    ATR = "ATR"
    BOLLINGER = "Bollinger"
    KELTNER = "Keltner"
    DONCHIAN = "Donchian"
    OBV = "OBV"
    VWAP = "VWAP"
    MFI = "MFI"
    CMF = "CMF"
    ACCUMULATION_DISTRIBUTION = "A/D"
    ADX = "ADX"
    DMI = "DMI"
    MACD = "MACD"
    SUPERTREND = "SuperTrend"
    ICHIMOKU = "Ichimoku"
    PSAR = "PSAR"


@dataclass(frozen=True)
class Bars:
    """
    Immutable OHLCV bar series.

    All lists must have equal length. The dataclass is frozen so the
    series cannot be mutated after construction — guaranteeing that
    deterministic computations cannot be corrupted by aliasing.
    """

    open: List[float] = field(default_factory=list)
    high: List[float] = field(default_factory=list)
    low: List[float] = field(default_factory=list)
    close: List[float] = field(default_factory=list)
    volume: List[float] = field(default_factory=list)

    @property
    def length(self) -> int:
        return len(self.close)

    def validate(self) -> None:
        """Validate that all series have equal length."""
        lengths = {len(self.open), len(self.high), len(self.low),
                   len(self.close), len(self.volume)}
        if len(lengths) > 1:
            raise ValueError(
                f"All OHLCV series must have equal length, got {lengths}"
            )


@dataclass(frozen=True)
class IndicatorSpec:
    """
    A request to compute a single indicator.

    Attributes:
        name: Indicator family name (registry key, e.g. "SMA", "RSI", "MACD").
        params: Indicator parameters (e.g. {"period": 14}).
        category: Optional category override (for reporting only).
    """

    name: str
    params: Dict[str, Any] = field(default_factory=dict)
    category: Optional[IndicatorCategory] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "params": dict(sorted(self.params.items())),
            "category": self.category.value if self.category else None,
        }


@dataclass(frozen=True)
class IndicatorOutput:
    """
    The computed output of a single indicator.

    Attributes:
        name: Indicator name.
        values: Main output series (aligned to input length, None-warm-up padded).
        aux: Optional auxiliary series (e.g. signal line, histogram, channels).
        category: Indicator category.
        params: Parameters used.
    """

    name: str
    values: List[Optional[float]]
    aux: Dict[str, List[Optional[float]]] = field(default_factory=dict)
    category: Optional[IndicatorCategory] = None
    params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "values": self.values,
            "aux": self.aux,
            "category": self.category.value if self.category else None,
            "params": dict(sorted(self.params.items())),
        }


@dataclass(frozen=True)
class IndicatorBatch:
    """
    The result of computing a batch of indicators.

    Attributes:
        outputs: Mapping of indicator name → IndicatorOutput.
        bar_count: Number of bars in the input series.
        computation_version: Version of the computation methodology.
    """

    outputs: Dict[str, IndicatorOutput] = field(default_factory=dict)
    bar_count: int = 0
    computation_version: str = "TECHNICAL_V1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "outputs": {k: v.to_dict() for k, v in self.outputs.items()},
            "bar_count": self.bar_count,
            "computation_version": self.computation_version,
        }

