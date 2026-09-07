"""
ReplayEngine — chronological, no-lookahead backtest replay.

Purpose:
    Drive the research backtesting pipeline bar-by-bar:
        bar → StrategyEvaluationInterface → Signal → ExecutionSimulationLayer

Guarantees:
    - Chronological processing (oldest bar first).
    - No lookahead: strategies only ever receive the current bar plus history
      strictly before it.
    - Signals produced on bar i are filled at the OPEN of bar i+1.
    - Signals produced on the final bar are never filled.
    - Deterministic: identical dataset + config → identical result.
    - Integrates with HistoricalIterator / as_of for time-bounded replay.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from researchos.data_engine.dataset import HistoricalDataset
from researchos.data_engine.iterator import HistoricalIterator
from researchos.quant_engine.execution import ExecutionSimulationLayer
from researchos.quant_engine.models import OrderSide, Signal
from researchos.quant_engine.strategy import StrategyEvaluationInterface


@dataclass(frozen=True)
class ReplayBar:
    """
    Minimal deterministic bar used when source data has no Candle shape.

    Attributes:
        open: Opening price used for next-bar market fills.
        close: Closing price used for mark-to-market.
        timestamp: Optional datetime for the bar.
    """

    close: float
    timestamp: datetime | None = None
    open: float | None = None


def _iso(dt: datetime | None) -> str:
    if dt is None:
        return ""
    return dt.isoformat()


def _open_price(bar: Any) -> float:
    """Return the broker/source opening price required for next-bar fills."""
    value = getattr(bar, "open", None)
    if value is None:
        # Synthetic/close-only inputs have no distinct open. Preserve a
        # deterministic fallback rather than silently using a future close.
        return float(getattr(bar, "close"))
    return float(value)


class ReplayEngine:
    """
    Sequential, no-lookahead backtest engine.

    Usage:
        engine = ReplayEngine(strategy=BuyAndHoldStrategy(), execution=execution)
        output = engine.run(dataset)
    """

    def __init__(
        self,
        strategy: StrategyEvaluationInterface,
        execution: ExecutionSimulationLayer,
        as_of: datetime | None = None,
    ) -> None:
        self.strategy = strategy
        self.execution = execution
        self.as_of = as_of

    # ── bar extraction ────────────────────────────────────────────

    def _extract_bars(self, dataset: Any) -> list[Any]:
        """Return a chronologically-ordered list of bar-like objects."""
        if dataset is None:
            base = 100.0
            start = datetime(2020, 1, 1)
            return [
                ReplayBar(
                    close=base * (1.0 + 0.0001 * i),
                    open=base * (1.0 + 0.0001 * i),
                    timestamp=start + timedelta(days=i),
                )
                for i in range(252)
            ]

        if isinstance(dataset, HistoricalDataset):
            return list(HistoricalIterator(dataset, as_of=self.as_of))

        if hasattr(dataset, "records") and hasattr(dataset, "symbol"):
            return list(HistoricalIterator(dataset, as_of=self.as_of))

        if isinstance(dataset, list):
            if not dataset:
                return []
            first = dataset[0]
            if hasattr(first, "close") and hasattr(first, "timestamp"):
                return list(dataset)
            if hasattr(first, "close"):
                start = datetime(2020, 1, 1)
                return [
                    ReplayBar(
                        close=float(c.close),
                        open=float(getattr(c, "open", c.close)),
                        timestamp=start + timedelta(days=i),
                    )
                    for i, c in enumerate(dataset)
                ]
            if isinstance(first, (int, float)):
                start = datetime(2020, 1, 1)
                return [
                    ReplayBar(
                        close=float(p),
                        open=float(p),
                        timestamp=start + timedelta(days=i),
                    )
                    for i, p in enumerate(dataset)
                ]
            if isinstance(first, dict) and "close" in first:
                start = datetime(2020, 1, 1)
                bars = []
                for i, d in enumerate(dataset):
                    ts = d.get("timestamp")
                    dt = ts if isinstance(ts, datetime) else (start + timedelta(days=i))
                    bars.append(
                        ReplayBar(
                            close=float(d["close"]),
                            open=float(d.get("open", d["close"])),
                            timestamp=dt,
                        )
                    )
                return bars
            return []

        if hasattr(dataset, "__iter__"):
            items = list(dataset)
            if items and hasattr(items[0], "close"):
                return list(items)

        return []

    # ── replay ────────────────────────────────────────────────────

    def run(self, dataset: Any) -> dict[str, Any]:
        """
        Run the backtest replay over the dataset.

        Signals are evaluated using bar i information and queued until bar
        i+1, where market execution occurs at that bar's opening price.

        Raises:
            ValueError: If fewer than 2 bars are available.
        """
        self.strategy.reset()
        bars = self._extract_bars(dataset)
        if len(bars) < 2:
            raise ValueError(f"Need at least 2 bars for replay, got {len(bars)}")

        history: list[Any] = []
        pending_signal: Signal | None = None

        for i, bar in enumerate(bars):
            ts = getattr(bar, "timestamp", None)

            # A signal generated on bar i-1 is filled at the OPEN of bar i.
            if pending_signal is not None:
                self.execution.process_signal(
                    pending_signal,
                    _open_price(bar),
                    i,
                    _iso(ts),
                )
                pending_signal = None

            signal = self.strategy.evaluate(bar, list(history), i)
            if signal is not None:
                if signal.bar_index != i:
                    raise ValueError(
                        f"Strategy signal bar_index={signal.bar_index} does not match evaluation bar {i}"
                    )
                pending_signal = signal

            self.execution.mark_to_market(
                float(getattr(bar, "close")),
                i,
                _iso(ts),
            )
            history.append(bar)

        # A signal produced on the final bar has no next bar and is therefore
        # intentionally not filled. Any already-open position is liquidated at
        # the final known close for deterministic end-of-data accounting.
        if self.execution.position_qty != 0:
            last_bar = bars[-1]
            last_ts = getattr(last_bar, "timestamp", None)
            last_idx = len(bars) - 1
            close_side = OrderSide.SELL if self.execution.position_qty > 0 else OrderSide.BUY
            liquidation_signal = Signal(
                bar_index=last_idx,
                timestamp=_iso(last_ts),
                side=close_side,
                confidence=1.0,
                metadata={
                    "strategy": self.strategy.identifier,
                    "reason": "end_of_data_liquidation",
                },
            )
            self.execution.process_signal(
                liquidation_signal,
                float(getattr(last_bar, "close")),
                last_idx,
                _iso(last_ts),
            )

        stats = self.execution.execution_stats()
        stats["strategy"] = self.strategy.identifier
        stats["strategy_version"] = self.strategy.version
        stats["num_bars"] = len(bars)
        stats["signal_fill_timing"] = "next_bar_open"

        return {
            "signals": self.execution.signals,
            "trades": [t.to_dict() for t in self.execution.trades],
            "positions": [p.to_dict() for p in self.execution.position_snapshots],
            "equity_curve": self.execution.equity_curve,
            "execution_stats": stats,
            "num_bars": len(bars),
            "start_time": _iso(getattr(bars[0], "timestamp", None)),
            "end_time": _iso(getattr(bars[-1], "timestamp", None)),
        }
