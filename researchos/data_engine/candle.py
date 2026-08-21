"""
Candle model — OHLCV representation for market data.

Based on Article XVII: Object Model — Data Layer.

A Candle represents a single OHLCV (Open, High, Low, Close, Volume) bar
for a specific symbol and timeframe at a specific timestamp.

Guarantees:
    - Deterministic: Same inputs → same ID and hash
    - Auditable: Full lifecycle tracking
    - Serializable: Supports to_dict/from_dict
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id
from researchos.core.lifecycle import LifecycleStage
from researchos.core.timestamp import parse_timestamp


class Candle(BaseObject):
    """
    A single OHLCV bar for a symbol at a specific timestamp.

    Attributes:
        symbol: The trading symbol (e.g., "XAU/USD", "AAPL").
        timeframe: The timeframe of this candle.
        timestamp: UTC timestamp of the candle open.
        open: Opening price.
        high: Highest price.
        low: Lowest price.
        close: Closing price.
        volume: Trading volume.
        quote_volume: Optional quote asset volume.
        trades_count: Optional number of trades.
        spread: Optional spread in points (MT5 export).
        tick_volume: Optional tick volume (MT5 export).
        real_volume: Optional real/contract volume (MT5 export).
        is_complete: Whether this candle is fully formed.
    """

    def __init__(
        self,
        symbol: str,
        timeframe: str,
        timestamp: datetime,
        open: float,
        high: float,
        low: float,
        close: float,
        volume: float = 0.0,
        quote_volume: float = 0.0,
        trades_count: int = 0,
        spread: float | None = None,
        tick_volume: float | None = None,
        real_volume: float | None = None,
        is_complete: bool = True,
        ontology_tags: list[str] | None = None,
        id: str | None = None,
    ):
        if id is None:
            ts_str = timestamp.isoformat() if hasattr(timestamp, "isoformat") else str(timestamp)
            seed = f"Candle|{symbol}|{timeframe}|{ts_str}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.symbol = symbol
        self.timeframe = timeframe
        self.timestamp = timestamp
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.quote_volume = quote_volume
        self.trades_count = trades_count
        self.spread = spread
        self.tick_volume = tick_volume
        self.real_volume = real_volume
        self.is_complete = is_complete

        self.lifecycle.transition(
            LifecycleStage.CREATED,
            reason=f"Candle created: {symbol} @ {timestamp}",
        )

    @property
    def range(self) -> float:
        """Price range (high - low)."""
        return self.high - self.low

    @property
    def body(self) -> float:
        """Candle body size (|close - open|)."""
        return abs(self.close - self.open)

    @property
    def is_bullish(self) -> bool:
        """Whether the candle is bullish (close > open)."""
        return self.close > self.open

    @property
    def is_bearish(self) -> bool:
        """Whether the candle is bearish (close < open)."""
        return self.close < self.open

    @property
    def upper_wick(self) -> float:
        """Upper wick size (high - max(open, close))."""
        return self.high - max(self.open, self.close)

    @property
    def lower_wick(self) -> float:
        """Lower wick size (min(open, close) - low)."""
        return min(self.open, self.close) - self.low

    @property
    def typical_price(self) -> float:
        """Typical price ((high + low + close) / 3)."""
        return (self.high + self.low + self.close) / 3.0

    @property
    def vwap_estimate(self) -> float:
        """Volume-weighted average price approximation."""
        if self.volume == 0:
            return self.typical_price
        return (self.typical_price * self.volume) / self.volume if self.volume > 0 else self.typical_price

    def _to_hashable_dict(self) -> dict[str, Any]:
        content = {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp.isoformat(),
            "open": round(self.open, 10),
            "high": round(self.high, 10),
            "low": round(self.low, 10),
            "close": round(self.close, 10),
            "volume": round(self.volume, 10),
            "quote_volume": round(self.quote_volume, 10),
            "trades_count": self.trades_count,
            "is_complete": self.is_complete,
            "ontology_tags": sorted(self.ontology_tags),
        }
        if self.spread is not None:
            content["spread"] = round(self.spread, 10)
        if self.tick_volume is not None:
            content["tick_volume"] = round(self.tick_volume, 10)
        if self.real_volume is not None:
            content["real_volume"] = round(self.real_volume, 10)
        return content

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "symbol": self.symbol,
                "timeframe": self.timeframe,
                "timestamp": self.timestamp.isoformat(),
                "open": self.open,
                "high": self.high,
                "low": self.low,
                "close": self.close,
                "volume": self.volume,
                "quote_volume": self.quote_volume,
                "trades_count": self.trades_count,
                "spread": self.spread,
                "tick_volume": self.tick_volume,
                "real_volume": self.real_volume,
                "is_complete": self.is_complete,
                "range": self.range,
                "body": self.body,
                "upper_wick": self.upper_wick,
                "lower_wick": self.lower_wick,
                "is_bullish": self.is_bullish,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Candle:
        obj = super().from_dict(data)
        obj.symbol = data["symbol"]
        obj.timeframe = data["timeframe"]
        obj.timestamp = parse_timestamp(data["timestamp"])
        obj.open = float(data["open"])
        obj.high = float(data["high"])
        obj.low = float(data["low"])
        obj.close = float(data["close"])
        obj.volume = float(data.get("volume", 0.0))
        obj.quote_volume = float(data.get("quote_volume", 0.0))
        obj.trades_count = int(data.get("trades_count", 0))
        spread = data.get("spread")
        obj.spread = float(spread) if spread is not None else None
        tick_volume = data.get("tick_volume")
        obj.tick_volume = float(tick_volume) if tick_volume is not None else None
        real_volume = data.get("real_volume")
        obj.real_volume = float(real_volume) if real_volume is not None else None
        obj.is_complete = bool(data.get("is_complete", True))
        return obj

    def __repr__(self) -> str:
        return (
            f"Candle({self.symbol}, {self.timeframe}, "
            f"{self.timestamp.strftime('%Y-%m-%d %H:%M')}, "
            f"O={self.open:.2f} H={self.high:.2f} "
            f"L={self.low:.2f} C={self.close:.2f} V={self.volume:.0f})"
        )
