"""
Tick model â€” individual market tick representation.

Based on Article XVII: Object Model â€” Data Layer.

A Tick represents a single price update in the market. Ticks are the
finest granularity of market data.

Guarantees:
    - Deterministic: Same inputs â†’ same ID and hash
    - Auditable: Full lifecycle tracking
    - Serializable: Supports to_dict/from_dict
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id
from researchos.core.lifecycle import LifecycleStage
from researchos.core.timestamp import parse_timestamp


class Tick(BaseObject):
    """
    A single market tick â€” the finest granularity of market data.

    Attributes:
        symbol: The trading symbol.
        timestamp: UTC timestamp of the tick.
        price: Trade price.
        volume: Trade volume.
        side: Trade side ('buy', 'sell', or 'unknown').
        exchange: Optional exchange identifier.
        conditions: Optional list of trade condition flags.
        bid: Optional bid price at time of tick.
        ask: Optional ask price at time of tick.
    """

    def __init__(
        self,
        symbol: str,
        timestamp: datetime,
        price: float = 0.0,
        volume: float = 0.0,
        side: str = "unknown",
        exchange: str = "",
        conditions: Optional[List[str]] = None,
        bid: Optional[float] = None,
        ask: Optional[float] = None,
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            ts_str = timestamp.isoformat() if hasattr(timestamp, "isoformat") else str(timestamp)
            seed = f"Tick|{symbol}|{ts_str}|{price}|{volume}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.symbol = symbol
        self.timestamp = timestamp
        self.price = price
        self.volume = volume
        self.side = side
        self.exchange = exchange
        self.conditions: List[str] = conditions or []
        self.bid = bid
        self.ask = ask

        self.lifecycle.transition(
            LifecycleStage.CREATED,
            reason=f"Tick created: {symbol} @ {timestamp}",
        )

    @property
    def spread(self) -> Optional[float]:
        """Bid-ask spread at time of tick, if available."""
        if self.bid is not None and self.ask is not None:
            return self.ask - self.bid
        return None

    @property
    def mid_price(self) -> Optional[float]:
        """Mid price at time of tick, if bid/ask available."""
        if self.bid is not None and self.ask is not None:
            return (self.bid + self.ask) / 2.0
        return None

    def _to_hashable_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "price": round(self.price, 10),
            "volume": round(self.volume, 10),
            "side": self.side,
            "exchange": self.exchange,
            "conditions": sorted(self.conditions),
            "bid": round(self.bid, 10) if self.bid is not None else None,
            "ask": round(self.ask, 10) if self.ask is not None else None,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "symbol": self.symbol,
                "timestamp": self.timestamp.isoformat(),
                "price": self.price,
                "volume": self.volume,
                "side": self.side,
                "exchange": self.exchange,
                "conditions": self.conditions,
                "bid": self.bid,
                "ask": self.ask,
                "spread": self.spread,
                "mid_price": self.mid_price,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Tick":
        obj = super().from_dict(data)
        obj.symbol = data["symbol"]
        obj.timestamp = parse_timestamp(data["timestamp"])
        obj.price = float(data.get("price", 0.0))
        obj.volume = float(data.get("volume", 0.0))
        obj.side = data.get("side", "unknown")
        obj.exchange = data.get("exchange", "")
        obj.conditions = list(data.get("conditions", []))
        obj.bid = float(data["bid"]) if data.get("bid") is not None else None
        obj.ask = float(data["ask"]) if data.get("ask") is not None else None
        return obj

    def __repr__(self) -> str:
        return (
            f"Tick({self.symbol}, {self.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')}, "
            f"P={self.price:.4f} V={self.volume:.0f} {self.side})"
        )
