"""Compatibility ReplayEngine with canonical next-bar-open execution semantics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from researchos.engines.data.dataset import HistoricalDataset
from researchos.engines.data.iterator import HistoricalIterator
from researchos.engines.quant.execution import ExecutionSimulationLayer
from researchos.engines.quant.models import OrderSide, Signal
from researchos.engines.quant.strategy import StrategyEvaluationInterface


@dataclass(frozen=True)
class ReplayBar:
    """Minimal deterministic bar used by the compatibility replay path."""

    close: float
    timestamp: datetime | None = None
    open: float | None = None


def _iso(dt: datetime | None) -> str:
    if dt is None:
        return ""
    return dt.isoformat()


def _open_price(bar: Any) -> float:
    value = getattr(bar, "open", None)
    if value is None:
        return float(getattr(bar, "close"))
    return float(value)


class ReplayEngine:
    """Sequential, no-lookahead compatibility replay engine."""

    def __init__(
        self,
        strategy: StrategyEvaluationInterface,
        execution: ExecutionSimulationLayer,
        as_of: datetime | None = None,
    ) -> None:
        self.strategy = strategy
        self.execution = execution
        self.as_of = as_of

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

    def run(self, dataset: Any) -> dict[str, Any]:
        """Run replay with signal-on-bar-i / fill-at-open-of-bar-i+1 semantics."""
        self.strategy.reset()
        bars = self._extract_bars(dataset)
        if len(bars) < 2:
            raise ValueError(f"Need at least 2 bars for replay, got {len(bars)}")

        history: list[Any] = []
        pending_signal: Signal | None = None

        for i, bar in enumerate(bars):
            ts = getattr(bar, "timestamp", None)

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

        # A final-bar signal has no next bar and is intentionally not filled.
        # Any already-open position is liquidated at the last known close.
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
