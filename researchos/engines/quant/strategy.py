"""
Strategy Evaluation Interface — research-only strategy evaluation for backtesting.

Purpose:
    Define the abstract contract for strategy evaluation in the ResearchOS
    backtesting pipeline. Strategies are RESEARCH-ONLY: they produce Signals
    for evaluation, never broker orders, never execute trades, and never
    touch live systems.

Architecture:
    bar → StrategyEvaluationInterface.evaluate(...) → Signal
        ↓
    ExecutionSimulationLayer (fills, positions, PnL)
        ↓
    SimulationResult

Rules:
    - Research only: no broker execution, no live trading.
    - No decision_engine dependency: strategies are self-contained.
    - Deterministic: same bars + same history → same signals.
    - No-lookahead: strategies only ever see bars up to and including the
      current bar; ``history`` contains only strictly-prior bars.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from researchos.engines.quant.models import OrderSide, Signal


class StrategyEvaluationInterface(ABC):
    """
    Abstract contract for a strategy evaluation.

    Implementations produce deterministic Signals from a chronological
    stream of bars. They are pure evaluation logic — they do NOT:
        - place orders
        - simulate fills
        - interact with any broker or live execution system
        - depend on researchos.decision_engine

    A strategy must be deterministic: given the same ordered history it must
    always produce the same Signal.
    """

    #: Human-readable strategy identifier (used for provenance).
    identifier: str = "base"

    #: Semantic version of the strategy logic (used for provenance).
    version: str = "1.0.0"

    @abstractmethod
    def evaluate(
        self,
        bar: Any,
        history: list[Any],
        bar_index: int,
    ) -> Signal | None:
        """
        Evaluate the current bar and produce an optional Signal.

        Args:
            bar: The current bar (has ``close`` price; may have more OHLCV).
            history: All bars BEFORE the current bar, oldest to newest.
                     Never contains the current bar or any future bar.
            bar_index: Zero-based index of the current bar in the full series.

        Returns:
            A Signal to be routed to the execution layer, or None to skip.
        """
        ...

    def reset(self) -> None:
        """
        Reset any internal strategy state.

        Called before each replay so strategies can be reused
        deterministically across multiple runs.
        """
        pass


class BuyAndHoldStrategy(StrategyEvaluationInterface):
    """
    Baseline Buy & Hold strategy used to validate the backtesting pipeline.

    Emits a single BUY signal on the first bar. The ReplayEngine performs
    the end-of-data liquidation, so the strategy itself only needs to enter
    once. This provides a deterministic, trivially-verifiable baseline for
    commission, slippage, position accounting, and trade generation tests.
    """

    identifier = "buy_and_hold"
    version = "1.0.0"

    def evaluate(
        self,
        bar: Any,
        history: list[Any],
        bar_index: int,
    ) -> Signal | None:
        if bar_index == 0:
            return Signal(
                bar_index=0,
                timestamp=self._timestamp_of(bar),
                side=OrderSide.BUY,
                confidence=1.0,
                metadata={
                    "strategy": self.identifier,
                    "reason": "buy_and_hold_entry",
                },
            )
        return None

    @staticmethod
    def _timestamp_of(bar: Any) -> str:
        ts = getattr(bar, "timestamp", None)
        if ts is None:
            return ""
        if hasattr(ts, "isoformat"):
            return ts.isoformat()
        return str(ts)
