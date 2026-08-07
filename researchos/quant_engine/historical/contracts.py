"""
Historical Analytics Engine — contracts, enums, and dataclass models.

Research modules for historical pattern mining, market regime statistics,
seasonality, session statistics, volatility clustering, trend persistence,
drawdown/recovery statistics, market state transitions, probability tables,
and historical feature extraction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class MarketState(str, Enum):
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"


@dataclass(frozen=True)
class ReturnSeries:
    """Immutable daily return series for analysis."""

    returns: List[float] = field(default_factory=list)

    @property
    def length(self) -> int:
        return len(self.returns)

    def validate(self) -> None:
        if self.length == 0:
            raise ValueError("return series must be non-empty")


@dataclass(frozen=True)
class RegimeStatistics:
    """Statistics of a single detected market regime window."""

    state: MarketState
    start_index: int = 0
    end_index: int = 0
    mean_return: float = 0.0
    volatility: float = 0.0
    cumulative_return: float = 0.0
    num_periods: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state.value,
            "start_index": self.start_index,
            "end_index": self.end_index,
            "mean_return": self.mean_return,
            "volatility": self.volatility,
            "cumulative_return": self.cumulative_return,
            "num_periods": self.num_periods,
        }


@dataclass(frozen=True)
class SeasonalityProfile:
    """Seasonality statistics grouped by key."""

    group_key: str = ""
    periods: Dict[str, Dict[str, float]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "group_key": self.group_key,
            "periods": {k: dict(v) for k, v in self.periods.items()},
        }


@dataclass(frozen=True)
class DrawdownStatistics:
    """Drawdown and recovery statistics for a return series."""

    max_drawdown: float = 0.0
    avg_drawdown: float = 0.0
    longest_drawdown_periods: int = 0
    avg_drawdown_periods: float = 0.0
    recovery_periods: List[int] = field(default_factory=list)
    num_drawdowns: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_drawdown": self.max_drawdown,
            "avg_drawdown": self.avg_drawdown,
            "longest_drawdown_periods": self.longest_drawdown_periods,
            "avg_drawdown_periods": self.avg_drawdown_periods,
            "recovery_periods": self.recovery_periods,
            "num_drawdowns": self.num_drawdowns,
        }


@dataclass(frozen=True)
class StateTransitionTable:
    """Market state transition probabilities (probability table)."""

    states: List[str] = field(default_factory=list)
    transition_matrix: List[List[float]] = field(default_factory=list)
    state_counts: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "states": self.states,
            "transition_matrix": self.transition_matrix,
            "state_counts": dict(self.state_counts),
        }


@dataclass(frozen=True)
class FeatureExtraction:
    """Extracted historical features (flat dict of scalars)."""

    features: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return dict(sorted(self.features.items()))

