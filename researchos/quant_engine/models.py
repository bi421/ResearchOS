"""
Models for the Quant Computation Engine.

Defines the data contracts used across the computation layer:
    SimulationRequest, SimulationResult, CalculationVersion.

All models are:
    - Deterministic: Same inputs → same outputs
    - Serializable: Support to_dict/from_dict
    - Versioned: CalculationVersion tracks methodology

Based on Article XVII: Object Model — Quant Engine Layer.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from researchos.core.identity import deterministic_hash
from researchos.core.timestamp import utc_now


class CalculationVersion(str, Enum):
    """
    Explicit version identifier for calculation methodology.

    Every calculation in the Quant Engine must reference a specific version.
    When formulas change, a new version is added — historical results remain
    reproducible under their original version.

    CALCULATION_V1: Initial release — standard return, volatility, drawdown,
                    Sharpe, Sortino, Calmar, Profit Factor formulas.
    """

    CALCULATION_V1 = "CALCULATION_V1"

    # Future versions:
    # CALCULATION_V2 = "CALCULATION_V2"


def periods_per_year_from_timeframe(timeframe: str) -> int:
    """
    Map a timeframe string to the number of periods per year.

    Used for annualising metrics (Sharpe, Sortino, etc.).
    """
    mapping = {
        "tick": 252 * 6.5 * 3600,  # ~6.5 hour session * 3600 ticks/hr
        "1m": 252 * 6.5 * 60,
        "5m": 252 * 6.5 * 12,
        "15m": 252 * 6.5 * 4,
        "30m": 252 * 13,
        "1h": 252 * 6.5,
        "4h": 252 * 1.625,
        "1d": 252,
        "1w": 52,
        "1mo": 12,
    }
    return mapping.get(timeframe, 252)


@dataclass
class SimulationRequest:
    """
    A request to run a historical simulation.

    Captures everything needed to reproduce a simulation:
    the dataset reference, time window, parameters, and calculation version.

    Attributes:
        dataset_reference: Identifier for the dataset (e.g., "XAU/USD:2020-2024").
        dataset_version: Version of the dataset used.
        calculation_version: Which calculation methodology to use.
        start_time: ISO 8601 start of the simulation window.
        end_time: ISO 8601 end of the simulation window.
        parameters: Simulation parameters (e.g., initial_capital, commission).
        seed: Deterministic random seed for reproducibility.
        tags: Optional tags for categorisation.
    """

    dataset_reference: str
    dataset_version: str = "1.0.0"
    calculation_version: CalculationVersion = CalculationVersion.CALCULATION_V1
    start_time: str = ""
    end_time: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    seed: int = 42
    tags: List[str] = field(default_factory=list)

    def compute_input_hash(self) -> str:
        """Compute a deterministic hash of all input parameters."""
        content = {
            "dataset_reference": self.dataset_reference,
            "dataset_version": self.dataset_version,
            "calculation_version": self.calculation_version.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "parameters": dict(sorted(self.parameters.items())),
            "seed": self.seed,
            "tags": sorted(self.tags),
        }
        return deterministic_hash(content)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_reference": self.dataset_reference,
            "dataset_version": self.dataset_version,
            "calculation_version": self.calculation_version.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "parameters": dict(self.parameters),
            "seed": self.seed,
            "tags": sorted(self.tags),
            "input_hash": self.compute_input_hash(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimulationRequest":
        return cls(
            dataset_reference=data["dataset_reference"],
            dataset_version=data.get("dataset_version", "1.0.0"),
            calculation_version=CalculationVersion(data.get("calculation_version", "CALCULATION_V1")),
            start_time=data.get("start_time", ""),
            end_time=data.get("end_time", ""),
            parameters=dict(data.get("parameters", {})),
            seed=int(data.get("seed", 42)),
            tags=list(data.get("tags", [])),
        )


# ──────────────────────────────────────────────
# Backtesting Execution Models
# ──────────────────────────────────────────────

class OrderSide(str, Enum):
    """Side of an order or position."""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    """Type of order."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderStatus(str, Enum):
    """Lifecycle status of an order."""
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class Signal:
    """
    A deterministic signal produced by a strategy evaluation.

    Immutable, hashable, serializable.

    Attributes:
        bar_index: Index of the bar that produced this signal.
        timestamp: ISO 8601 timestamp of the signal.
        side: BUY or SELL.
        confidence: Signal confidence in [0.0, 1.0].
        metadata: Optional signal metadata.
    """
    bar_index: int
    timestamp: str
    side: OrderSide
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bar_index": self.bar_index,
            "timestamp": self.timestamp,
            "side": self.side.value,
            "confidence": self.confidence,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Signal":
        return cls(
            bar_index=data["bar_index"],
            timestamp=data["timestamp"],
            side=OrderSide(data["side"]),
            confidence=float(data.get("confidence", 1.0)),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True)
class Order:
    """
    A deterministic order created from a signal.

    Immutable, hashable, serializable.

    Attributes:
        signal_index: Index of the originating signal.
        side: BUY or SELL.
        order_type: MARKET or LIMIT.
        quantity: Number of units.
        limit_price: Limit price for LIMIT orders (None for MARKET).
        status: Current order status.
        bar_index: Bar index when the order was created.
        timestamp: ISO 8601 timestamp.
    """
    signal_index: int
    side: OrderSide
    order_type: OrderType
    quantity: float
    limit_price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    bar_index: int = 0
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_index": self.signal_index,
            "side": self.side.value,
            "order_type": self.order_type.value,
            "quantity": self.quantity,
            "limit_price": self.limit_price,
            "status": self.status.value,
            "bar_index": self.bar_index,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Order":
        return cls(
            signal_index=data["signal_index"],
            side=OrderSide(data["side"]),
            order_type=OrderType(data["order_type"]),
            quantity=float(data["quantity"]),
            limit_price=float(data["limit_price"]) if data.get("limit_price") is not None else None,
            status=OrderStatus(data.get("status", "PENDING")),
            bar_index=int(data.get("bar_index", 0)),
            timestamp=data.get("timestamp", ""),
        )


@dataclass(frozen=True)
class OrderFill:
    """
    A deterministic fill record for an executed order.

    Immutable, hashable, serializable.

    Attributes:
        order: The order that was filled.
        fill_price: The price at which the order was filled.
        fill_quantity: The quantity that was filled.
        commission: Commission paid for this fill.
        slippage: Slippage applied (difference from expected price).
        bar_index: Bar index when the fill occurred.
        timestamp: ISO 8601 timestamp.
    """
    order: Order
    fill_price: float
    fill_quantity: float
    commission: float = 0.0
    slippage: float = 0.0
    bar_index: int = 0
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order": self.order.to_dict(),
            "fill_price": self.fill_price,
            "fill_quantity": self.fill_quantity,
            "commission": self.commission,
            "slippage": self.slippage,
            "bar_index": self.bar_index,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrderFill":
        return cls(
            order=Order.from_dict(data["order"]),
            fill_price=float(data["fill_price"]),
            fill_quantity=float(data["fill_quantity"]),
            commission=float(data.get("commission", 0.0)),
            slippage=float(data.get("slippage", 0.0)),
            bar_index=int(data.get("bar_index", 0)),
            timestamp=data.get("timestamp", ""),
        )


@dataclass(frozen=True)
class Position:
    """
    A snapshot of a position at a given point in time.

    Immutable, hashable, serializable.

    Attributes:
        symbol: The trading symbol.
        side: BUY (long) or SELL (short).
        quantity: Number of units held.
        entry_price: Average entry price.
        current_price: Current market price.
        unrealized_pnl: Unrealised profit/loss.
        realized_pnl: Realised profit/loss (from closed portion).
        bar_index: Bar index of this snapshot.
        timestamp: ISO 8601 timestamp.
    """
    symbol: str
    side: OrderSide
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    bar_index: int = 0
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "side": self.side.value,
            "quantity": self.quantity,
            "entry_price": self.entry_price,
            "current_price": self.current_price,
            "unrealized_pnl": self.unrealized_pnl,
            "realized_pnl": self.realized_pnl,
            "bar_index": self.bar_index,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Position":
        return cls(
            symbol=data["symbol"],
            side=OrderSide(data["side"]),
            quantity=float(data["quantity"]),
            entry_price=float(data["entry_price"]),
            current_price=float(data["current_price"]),
            unrealized_pnl=float(data.get("unrealized_pnl", 0.0)),
            realized_pnl=float(data.get("realized_pnl", 0.0)),
            bar_index=int(data.get("bar_index", 0)),
            timestamp=data.get("timestamp", ""),
        )


@dataclass(frozen=True)
class Trade:
    """
    A completed trade — a round-trip (entry + exit).

    Immutable, hashable, serializable.

    Attributes:
        entry_fill: The fill at entry.
        exit_fill: The fill at exit.
        pnl: Net profit/loss (includes commissions).
        return_pct: Percentage return on the trade.
        bars_held: Number of bars the trade was held.
        entry_bar_index: Bar index of entry.
        exit_bar_index: Bar index of exit.
    """
    entry_fill: OrderFill
    exit_fill: OrderFill
    pnl: float = 0.0
    return_pct: float = 0.0
    bars_held: int = 0
    entry_bar_index: int = 0
    exit_bar_index: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_fill": self.entry_fill.to_dict(),
            "exit_fill": self.exit_fill.to_dict(),
            "pnl": self.pnl,
            "return_pct": self.return_pct,
            "bars_held": self.bars_held,
            "entry_bar_index": self.entry_bar_index,
            "exit_bar_index": self.exit_bar_index,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Trade":
        return cls(
            entry_fill=OrderFill.from_dict(data["entry_fill"]),
            exit_fill=OrderFill.from_dict(data["exit_fill"]),
            pnl=float(data.get("pnl", 0.0)),
            return_pct=float(data.get("return_pct", 0.0)),
            bars_held=int(data.get("bars_held", 0)),
            entry_bar_index=int(data.get("entry_bar_index", 0)),
            exit_bar_index=int(data.get("exit_bar_index", 0)),
        )


@dataclass
class SimulationResult:
    """
    The complete output of a simulation run.

    Includes full provenance so the result can be audited and reproduced.

    Attributes:
        simulation_id: Unique identifier for this simulation.
        dataset_reference: Dataset identifier (from request).
        dataset_version: Dataset version used.
        calculation_version: Calculation methodology version used.
        parameters: Parameters used for the simulation.
        start_time: Start of simulation window.
        end_time: End of simulation window.
        input_hash: Hash of the SimulationRequest that produced this result.
        result_hash: Deterministic hash of this result's content.
        execution_timestamp: When the simulation was executed.
        returns: List of periodic returns (absolute, pct, or log).
        equity_curve: List of equity values over time.
        metrics: Dict of computed metrics (sharpe, sortino, etc.).
        statistics: Dict of statistical summaries.
        performance: Dict of performance analytics.
        trades: List of trade records (if applicable).
        signals: List of signal records produced by the strategy.
        positions: List of position snapshots over the replay.
        execution_stats: Dict of execution-model statistics.
        metadata: Additional metadata.
    """

    simulation_id: str
    dataset_reference: str
    dataset_version: str = "1.0.0"
    calculation_version: CalculationVersion = CalculationVersion.CALCULATION_V1
    parameters: Dict[str, Any] = field(default_factory=dict)
    start_time: str = ""
    end_time: str = ""
    input_hash: str = ""
    result_hash: str = ""
    execution_timestamp: str = ""
    returns: List[float] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    statistics: Dict[str, Any] = field(default_factory=dict)
    performance: Dict[str, Any] = field(default_factory=dict)
    trades: List[Dict[str, Any]] = field(default_factory=list)
    signals: List[Dict[str, Any]] = field(default_factory=list)
    positions: List[Dict[str, Any]] = field(default_factory=list)
    execution_stats: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def compute_result_hash(self) -> str:
        """Compute a deterministic hash of this result's content."""
        content = {
            "simulation_id": self.simulation_id,
            "dataset_reference": self.dataset_reference,
            "dataset_version": self.dataset_version,
            "calculation_version": self.calculation_version.value,
            "parameters": dict(sorted(self.parameters.items())),
            "start_time": self.start_time,
            "end_time": self.end_time,
            "input_hash": self.input_hash,
            "returns": [round(r, 10) for r in self.returns],
            "equity_curve": [round(e, 10) for e in self.equity_curve],
            "metrics": dict(sorted(self.metrics.items())),
            "statistics": dict(sorted(self.statistics.items())),
            "performance": dict(sorted(self.performance.items())),
            "trades": sorted(self.trades, key=lambda t: str(t)),
            "signals": sorted(self.signals, key=lambda s: str(s)),
            "positions": sorted(self.positions, key=lambda p: str(p)),
            "execution_stats": dict(sorted(self.execution_stats.items())),
            "metadata": dict(sorted(self.metadata.items())),
        }
        return deterministic_hash(content)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "simulation_id": self.simulation_id,
            "dataset_reference": self.dataset_reference,
            "dataset_version": self.dataset_version,
            "calculation_version": self.calculation_version.value,
            "parameters": dict(self.parameters),
            "start_time": self.start_time,
            "end_time": self.end_time,
            "input_hash": self.input_hash,
            "result_hash": self.result_hash or self.compute_result_hash(),
            "execution_timestamp": self.execution_timestamp,
            "returns": self.returns,
            "equity_curve": self.equity_curve,
            "metrics": self.metrics,
            "statistics": self.statistics,
            "performance": self.performance,
            "trades": self.trades,
            "signals": self.signals,
            "positions": self.positions,
            "execution_stats": self.execution_stats,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimulationResult":
        return cls(
            simulation_id=data["simulation_id"],
            dataset_reference=data.get("dataset_reference", ""),
            dataset_version=data.get("dataset_version", "1.0.0"),
            calculation_version=CalculationVersion(data.get("calculation_version", "CALCULATION_V1")),
            parameters=dict(data.get("parameters", {})),
            start_time=data.get("start_time", ""),
            end_time=data.get("end_time", ""),
            input_hash=data.get("input_hash", ""),
            result_hash=data.get("result_hash", ""),
            execution_timestamp=data.get("execution_timestamp", ""),
            returns=list(data.get("returns", [])),
            equity_curve=list(data.get("equity_curve", [])),
            metrics=dict(data.get("metrics", {})),
            statistics=dict(data.get("statistics", {})),
            performance=dict(data.get("performance", {})),
            trades=list(data.get("trades", [])),
            signals=list(data.get("signals", [])),
            positions=list(data.get("positions", [])),
            execution_stats=dict(data.get("execution_stats", {})),
            metadata=dict(data.get("metadata", {})),
        )
