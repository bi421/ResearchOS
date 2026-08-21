"""
ExecutionSimulationLayer — deterministic fill simulation for backtesting.

Purpose:
    Simulate the lifecycle signal → order → fill → position → trade for a
    single symbol in a research backtest. This is a RESEARCH SIMULATION only:
        - No broker connectivity
        - No live execution
        - No randomness
        - Fully deterministic given the same inputs

Supported cost models:
    - commission: "fixed:10.0" (per fill) or "pct:0.001" (fraction of notional)
    - slippage:   "fixed:0.01" (price units) or "pct:0.0005" (fraction of price)

PnL accounting:
    - Realized PnL on close of a position (includes both commissions).
    - Unrealized PnL mark-to-market at each bar close.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from researchos.engines.quant.models import (
    Order,
    OrderFill,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
    Signal,
    Trade,
)


def parse_cost_spec(spec: Optional[str], default_value: float = 0.0) -> Tuple[str, float]:
    """
    Parse ``"fixed:X"`` or ``"pct:Y"`` into ``(kind, value)``.

    Args:
        spec: Cost specification string (e.g. ``"fixed:10.0"``, ``"pct:0.001"``).
        default_value: Value to use when spec is empty.

    Returns:
        Tuple of (kind, value) where kind is "fixed" or "pct".

    Raises:
        ValueError: If the spec is malformed.
    """
    if not spec:
        return "fixed", default_value
    if ":" not in spec:
        return "fixed", float(spec)
    kind, value = spec.split(":", 1)
    kind = kind.strip().lower()
    if kind not in ("fixed", "pct"):
        raise ValueError(f"Unsupported cost spec kind '{kind}'. Expected 'fixed' or 'pct'.")
    return kind, float(value)


class ExecutionSimulationLayer:
    """
    Deterministic execution simulator for a single symbol.

    The layer owns:
        - order creation from signals
        - fill simulation with commission + slippage
        - position tracking (quantity, entry price, realized/unrealized PnL)
        - trade generation (round-trip records)
        - a deterministic equity curve

    It is intentionally stateful across a replay (it accumulates fills,
    trades, and cash), but contains NO randomness: identical signal streams
    produce identical outcomes.
    """

    def __init__(
        self,
        initial_capital: float = 100_000.0,
        commission: str = "fixed:0.0",
        slippage: str = "fixed:0.0",
        symbol: str = "",
        position_size: float = 1.0,
    ) -> None:
        self.initial_capital = float(initial_capital)
        self.commission_spec = commission
        self.slippage_spec = slippage
        self.symbol = symbol
        self.position_size = float(position_size)

        self._commission_kind, self._commission_value = parse_cost_spec(commission)
        self._slippage_kind, self._slippage_value = parse_cost_spec(slippage)

        # Execution state (mutable during replay, deterministic).
        self.cash: float = float(initial_capital)
        self.position_qty: float = 0.0
        self.entry_price: float = 0.0
        self.entry_commission: float = 0.0
        self.entry_bar_index: Optional[int] = None
        self.entry_fill: Optional[OrderFill] = None
        self.realized_pnl: float = 0.0
        self.total_commission: float = 0.0
        self.total_slippage_cost: float = 0.0

        # Ledgers (deterministic order).
        self.signals: List[Dict[str, Any]] = []
        self.orders: List[Order] = []
        self.fills: List[OrderFill] = []
        self.trades: List[Trade] = []
        self.equity_curve: List[float] = []
        self.position_snapshots: List[Position] = []
        self._signal_counter = 0

    # ── cost helpers ──────────────────────────────────────────────

    def _commission_for(self, price: float, quantity: float) -> float:
        if self._commission_kind == "pct":
            return round(abs(price * quantity) * self._commission_value, 10)
        return round(self._commission_value, 10)

    def _slippage_offset(self, price: float) -> float:
        if self._slippage_kind == "pct":
            return price * self._slippage_value
        return self._slippage_value

    def _fill_price(self, price: float, side: OrderSide) -> float:
        offset = self._slippage_offset(price)
        if side == OrderSide.BUY:
            return round(price + offset, 10)
        return round(price - offset, 10)

    # ── signal → order → fill ─────────────────────────────────────

    def process_signal(
        self,
        signal: Signal,
        price: float,
        bar_index: int,
        timestamp: str = "",
    ) -> Optional[OrderFill]:
        """
        Process a Signal: create an order and (for market orders) fill it.

        Args:
            signal: The signal to process.
            price: The current bar close (reference price).
            bar_index: Bar index at which the signal was produced.
            timestamp: ISO 8601 timestamp of the bar.

        Returns:
            The OrderFill if an order was created and filled, else None.
        """
        self.signals.append(signal.to_dict())
        order_side = signal.side

        # Skip redundant signals (already positioned in the same direction).
        if order_side == OrderSide.BUY and self.position_qty > 0:
            return None
        if order_side == OrderSide.SELL and self.position_qty < 0:
            return None

        # Determine quantity to trade (full close if reducing a position).
        if order_side == OrderSide.BUY:
            quantity = abs(self.position_qty) if self.position_qty < 0 else self.position_size
        else:  # SELL
            quantity = abs(self.position_qty) if self.position_qty > 0 else self.position_size

        order = Order(
            signal_index=self._signal_counter,
            side=order_side,
            order_type=OrderType.MARKET,
            quantity=quantity,
            limit_price=None,
            status=OrderStatus.PENDING,
            bar_index=bar_index,
            timestamp=timestamp,
        )
        self._signal_counter += 1
        self.orders.append(order)

        # Market orders fill immediately at the adjusted price.
        return self._fill(order, price, bar_index, timestamp)

    def _fill(
        self,
        order: Order,
        price: float,
        bar_index: int,
        timestamp: str,
    ) -> OrderFill:
        fill_price = self._fill_price(price, order.side)
        commission = self._commission_for(fill_price, order.quantity)
        slippage_cost = abs(fill_price - price) * order.quantity

        fill = OrderFill(
            order=order,
            fill_price=fill_price,
            fill_quantity=order.quantity,
            commission=commission,
            slippage=abs(fill_price - price),
            bar_index=bar_index,
            timestamp=timestamp,
        )
        self.fills.append(fill)
        self.total_commission += commission
        self.total_slippage_cost += slippage_cost

        self._apply_fill(fill)
        return fill

    def _apply_fill(self, fill: OrderFill) -> None:
        side = fill.order.side
        qty = fill.fill_quantity
        price = fill.fill_price
        commission = fill.commission

        if side == OrderSide.BUY:
            if self.position_qty < 0:
                # Closing a short.
                self.cash -= price * qty + commission
                self.position_qty += qty
                self._record_trade_close(fill, qty=qty, closing_short=True)
            else:
                # Opening / adding to a long.
                self.cash -= price * qty + commission
                self.position_qty += qty
                self._set_entry(fill)
        else:  # SELL
            if self.position_qty > 0:
                # Closing a long.
                self.cash += price * qty - commission
                self.position_qty -= qty
                self._record_trade_close(fill, qty=qty, closing_short=False)
            else:
                # Opening a short.
                self.cash += price * qty - commission
                self.position_qty -= qty
                self._set_entry(fill)

    def _set_entry(self, fill: OrderFill) -> None:
        self.entry_price = fill.fill_price
        self.entry_commission = fill.commission
        self.entry_bar_index = fill.bar_index
        self.entry_fill = fill

    def _record_trade_close(self, fill: OrderFill, qty: float, closing_short: bool) -> None:
        entry_fill = self.entry_fill
        if entry_fill is None:
            return

        if closing_short:
            pnl = (
                (self.entry_price - fill.fill_price) * qty - entry_fill.commission - fill.commission
            )
        else:
            pnl = (
                (fill.fill_price - self.entry_price) * qty - entry_fill.commission - fill.commission
            )

        cost_basis = abs(self.entry_price * qty) + entry_fill.commission
        return_pct = (pnl / cost_basis) if cost_basis != 0 else 0.0

        trade = Trade(
            entry_fill=entry_fill,
            exit_fill=fill,
            pnl=round(pnl, 10),
            return_pct=round(return_pct, 10),
            bars_held=fill.bar_index - (entry_fill.bar_index or 0),
            entry_bar_index=entry_fill.bar_index or 0,
            exit_bar_index=fill.bar_index,
        )
        self.trades.append(trade)
        self.realized_pnl += trade.pnl

        # Position fully closed → clear entry state.
        if self.position_qty == 0:
            self.entry_price = 0.0
            self.entry_commission = 0.0
            self.entry_bar_index = None
            self.entry_fill = None

    # ── mark-to-market ────────────────────────────────────────────

    def mark_to_market(self, price: float, bar_index: int, timestamp: str = "") -> float:
        """
        Mark the portfolio to market at ``price``.

        Appends an equity value and a Position snapshot. Returns equity.

        Equity is computed as ``cash + quantity * current_price``, which is
        valid for both long (qty > 0) and short (qty < 0) positions.
        """
        equity = round(self.cash + self.position_qty * price, 10)
        self.equity_curve.append(equity)

        if self.position_qty == 0:
            unrealized = 0.0
            side = OrderSide.BUY
            avg_entry = 0.0
        else:
            avg_entry = self.entry_price
            if self.position_qty > 0:
                side = OrderSide.BUY
                unrealized = (price - avg_entry) * self.position_qty
            else:
                side = OrderSide.SELL
                unrealized = (avg_entry - price) * abs(self.position_qty)
            unrealized = round(unrealized - self.entry_commission, 10)

        snapshot = Position(
            symbol=self.symbol,
            side=side,
            quantity=abs(self.position_qty),
            entry_price=avg_entry,
            current_price=price,
            unrealized_pnl=unrealized,
            realized_pnl=round(self.realized_pnl, 10),
            bar_index=bar_index,
            timestamp=timestamp,
        )
        self.position_snapshots.append(snapshot)
        return equity

    @property
    def final_equity(self) -> float:
        return self.equity_curve[-1] if self.equity_curve else self.initial_capital

    def execution_stats(self) -> Dict[str, Any]:
        """Deterministic summary of the execution simulation."""
        net_return = (
            (self.final_equity / self.initial_capital - 1.0) if self.initial_capital else 0.0
        )
        wins = [t for t in self.trades if t.pnl > 0]
        losses = [t for t in self.trades if t.pnl < 0]
        return {
            "strategy": "",
            "strategy_version": "",
            "execution_model": "ExecutionSimulationLayer",
            "commission_spec": self.commission_spec,
            "slippage_spec": self.slippage_spec,
            "initial_capital": self.initial_capital,
            "final_equity": round(self.final_equity, 10),
            "total_return": round(net_return, 10),
            "total_commission": round(self.total_commission, 10),
            "total_slippage_cost": round(self.total_slippage_cost, 10),
            "realized_pnl": round(self.realized_pnl, 10),
            "num_signals": len(self.signals),
            "num_orders": len(self.orders),
            "num_fills": len(self.fills),
            "num_trades": len(self.trades),
            "num_winning_trades": len(wins),
            "num_losing_trades": len(losses),
        }
