"""
Label Generation Engine — builder facade.

``LabelBuilder`` is the single entry point for producing supervised-learning
targets from a close-price series.  It is deterministic and independent from
FeatureBuilder, model training, dataset construction, and the decision engine.
"""

from __future__ import annotations

from typing import Dict, List

from .label_contracts import LabelResult
from .labels import (
    binary_label,
    future_return,
    multiclass_label,
    regression_target,
    triple_barrier,
)


class LabelBuilder:
    """Builds supervised-learning label series from a close-price series."""

    def __init__(self, close) -> None:
        self.close = list(close)

    def build_future_return(self, horizon: int = 1) -> LabelResult:
        """Forward-return label series."""
        return LabelResult(
            name="future_return",
            values=future_return(self.close, horizon),
            metadata={"horizon": horizon},
            horizon=horizon,
        )

    def build_binary(self, horizon: int = 1) -> LabelResult:
        """Binary direction label series (1 up / 0 down)."""
        return LabelResult(
            name="binary",
            values=binary_label(self.close, horizon),
            metadata={"horizon": horizon},
            horizon=horizon,
        )

    def build_multiclass(self, horizon: int = 1, threshold: float = 0.0) -> LabelResult:
        """Multi-class direction label series (-1 / 0 / 1)."""
        return LabelResult(
            name="multiclass",
            values=multiclass_label(self.close, horizon, threshold),
            metadata={"horizon": horizon, "threshold": threshold},
            horizon=horizon,
        )

    def build_triple_barrier(
        self,
        take_profit: float = 0.02,
        stop_loss: float = 0.02,
        max_horizon: int = 10,
    ) -> LabelResult:
        """Simplified deterministic triple-barrier label series."""
        return LabelResult(
            name="triple_barrier",
            values=triple_barrier(self.close, take_profit, stop_loss, max_horizon),
            metadata={
                "take_profit": take_profit,
                "stop_loss": stop_loss,
                "max_horizon": max_horizon,
            },
            horizon=max_horizon,
        )

    def build_regression(self, horizon: int = 1) -> LabelResult:
        """Regression target label series (alias of future return)."""
        return LabelResult(
            name="regression",
            values=regression_target(self.close, horizon),
            metadata={"horizon": horizon},
            horizon=horizon,
        )

    def build_all(
        self,
        horizon: int = 1,
        threshold: float = 0.0,
        take_profit: float = 0.02,
        stop_loss: float = 0.02,
        max_horizon: int = 10,
    ) -> Dict[str, LabelResult]:
        """Build every label type and return them keyed by name."""
        return {
            "future_return": self.build_future_return(horizon),
            "binary": self.build_binary(horizon),
            "multiclass": self.build_multiclass(horizon, threshold),
            "triple_barrier": self.build_triple_barrier(take_profit, stop_loss, max_horizon),
            "regression": self.build_regression(horizon),
        }


__all__ = ["LabelBuilder"]

