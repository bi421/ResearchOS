"""
OrderBook model — L2 order book snapshot representation.

Based on Article XVII: Object Model — Data Layer.

An OrderBook represents a snapshot of the limit order book at a
point in time, including multiple price levels on bid and ask sides.

Guarantees:
    - Deterministic: Same inputs → same ID and hash
    - Serializable: Supports to_dict/from_dict
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id
from researchos.core.lifecycle import LifecycleStage
from researchos.core.timestamp import parse_timestamp, utc_now


@dataclass
class OrderBookLevel:
    """
    A single price level in the order book.

    Attributes:
        price: The price of this level.
        size: The available size at this price.
        order_count: Optional number of orders at this level.
    """

    price: float
    size: float
    order_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "price": self.price,
            "size": self.size,
            "order_count": self.order_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrderBookLevel":
        return cls(
            price=float(data["price"]),
            size=float(data.get("size", 0.0)),
            order_count=int(data.get("order_count", 0)),
        )


class OrderBook(BaseObject):
    """
    A snapshot of the limit order book.

    Contains multiple bid and ask levels with price, size, and
    order count information.

    Attributes:
        symbol: The trading symbol.
        timestamp: UTC timestamp of the snapshot.
        bids: List of bid levels (sorted descending by price).
        asks: List of ask levels (sorted ascending by price).
        exchange: Optional exchange identifier.
        is_snapshot: Whether this is a full snapshot or an update.
        sequence: Optional sequence number for ordering updates.
    """

    def __init__(
        self,
        symbol: str,
        timestamp: datetime,
        bids: Optional[List[OrderBookLevel]] = None,
        asks: Optional[List[OrderBookLevel]] = None,
        exchange: str = "",
        is_snapshot: bool = True,
        sequence: int = 0,
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            ts_str = timestamp.isoformat() if hasattr(timestamp, "isoformat") else str(timestamp)
            seed = f"OrderBook|{symbol}|{ts_str}|{sequence}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.symbol = symbol
        self.timestamp = timestamp
        self.bids: List[OrderBookLevel] = bids or []
        self.asks: List[OrderBookLevel] = asks or []
        self.exchange = exchange
        self.is_snapshot = is_snapshot
        self.sequence = sequence

        self.lifecycle.transition(
            LifecycleStage.CREATED,
            reason=f"OrderBook created: {symbol} @ {timestamp}",
        )

    @property
    def best_bid(self) -> Optional[float]:
        """Best bid price."""
        if self.bids:
            return max(b.price for b in self.bids)
        return None

    @property
    def best_ask(self) -> Optional[float]:
        """Best ask price."""
        if self.asks:
            return min(a.price for a in self.asks)
        return None

    @property
    def mid_price(self) -> Optional[float]:
        """Mid price from best bid/ask."""
        bb = self.best_bid
        ba = self.best_ask
        if bb is not None and ba is not None:
            return (bb + ba) / 2.0
        return None

    @property
    def spread(self) -> Optional[float]:
        """Bid-ask spread."""
        bb = self.best_bid
        ba = self.best_ask
        if bb is not None and ba is not None:
            return ba - bb
        return None

    @property
    def total_bid_size(self) -> float:
        """Total size available on bid side."""
        return sum(b.size for b in self.bids)

    @property
    def total_ask_size(self) -> float:
        """Total size available on ask side."""
        return sum(a.size for a in self.asks)

    def _to_hashable_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "bids": sorted(
                [b.to_dict() for b in self.bids],
                key=lambda x: x["price"],
            ),
            "asks": sorted(
                [a.to_dict() for a in self.asks],
                key=lambda x: x["price"],
            ),
            "exchange": self.exchange,
            "is_snapshot": self.is_snapshot,
            "sequence": self.sequence,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "bids": [b.to_dict() for b in self.bids],
            "asks": [a.to_dict() for a in self.asks],
            "exchange": self.exchange,
            "is_snapshot": self.is_snapshot,
            "sequence": self.sequence,
            "best_bid": self.best_bid,
            "best_ask": self.best_ask,
            "mid_price": self.mid_price,
            "spread": self.spread,
            "total_bid_size": self.total_bid_size,
            "total_ask_size": self.total_ask_size,
        })
        return base

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrderBook":
        obj = super().from_dict(data)
        obj.symbol = data["symbol"]
        obj.timestamp = parse_timestamp(data["timestamp"])
        obj.bids = [OrderBookLevel.from_dict(b) for b in data.get("bids", [])]
        obj.asks = [OrderBookLevel.from_dict(a) for a in data.get("asks", [])]
        obj.exchange = data.get("exchange", "")
        obj.is_snapshot = bool(data.get("is_snapshot", True))
        obj.sequence = int(data.get("sequence", 0))
        return obj

    def __repr__(self) -> str:
        return (
            f"OrderBook({self.symbol}, {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}, "
            f"{len(self.bids)} bids × {len(self.asks)} asks)"
        )

