"""
Quote model — bid/ask quote representation.

Based on Article XVII: Object Model — Data Layer.

A Quote represents a snapshot of the best bid and ask prices at a
point in time. Quotes are used for market microstructure analysis.

Guarantees:
    - Deterministic: Same inputs → same ID and hash
    - Serializable: Supports to_dict/from_dict
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id
from researchos.core.lifecycle import LifecycleStage
from researchos.core.timestamp import parse_timestamp, utc_now
from researchos.data_engine.contracts import QuoteSide


class Quote(BaseObject):
    """
    A snapshot of bid and ask prices at a point in time.

    Attributes:
        symbol: The trading symbol.
        timestamp: UTC timestamp of the quote.
        bid: Best bid price.
        ask: Best ask price.
        bid_size: Best bid size/volume.
        ask_size: Best ask size/volume.
        exchange: Optional exchange identifier.
        condition: Optional quote condition flag.
    """

    def __init__(
        self,
        symbol: str,
        timestamp: datetime,
        bid: float,
        ask: float,
        bid_size: float = 0.0,
        ask_size: float = 0.0,
        exchange: str = "",
        condition: str = "",
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            ts_str = timestamp.isoformat() if hasattr(timestamp, "isoformat") else str(timestamp)
            seed = f"Quote|{symbol}|{ts_str}|{bid}|{ask}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.symbol = symbol
        self.timestamp = timestamp
        self.bid = bid
        self.ask = ask
        self.bid_size = bid_size
        self.ask_size = ask_size
        self.exchange = exchange
        self.condition = condition

        self.lifecycle.transition(
            LifecycleStage.CREATED,
            reason=f"Quote created: {symbol} @ {timestamp}",
        )

    @property
    def mid(self) -> float:
        """Mid price."""
        return (self.bid + self.ask) / 2.0

    @property
    def spread(self) -> float:
        """Bid-ask spread."""
        return self.ask - self.bid

    @property
    def spread_bps(self) -> float:
        """Spread in basis points of mid price."""
        if self.mid == 0:
            return 0.0
        return (self.spread / self.mid) * 10000.0

    def _to_hashable_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "bid": round(self.bid, 10),
            "ask": round(self.ask, 10),
            "bid_size": round(self.bid_size, 10),
            "ask_size": round(self.ask_size, 10),
            "exchange": self.exchange,
            "condition": self.condition,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "bid": self.bid,
            "ask": self.ask,
            "bid_size": self.bid_size,
            "ask_size": self.ask_size,
            "exchange": self.exchange,
            "condition": self.condition,
            "mid": self.mid,
            "spread": self.spread,
            "spread_bps": round(self.spread_bps, 4),
        })
        return base

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Quote":
        obj = super().from_dict(data)
        obj.symbol = data["symbol"]
        obj.timestamp = parse_timestamp(data["timestamp"])
        obj.bid = float(data["bid"])
        obj.ask = float(data["ask"])
        obj.bid_size = float(data.get("bid_size", 0.0))
        obj.ask_size = float(data.get("ask_size", 0.0))
        obj.exchange = data.get("exchange", "")
        obj.condition = data.get("condition", "")
        return obj

    def __repr__(self) -> str:
        return (
            f"Quote({self.symbol}, {self.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')}, "
            f"B={self.bid:.4f}×{self.bid_size:.0f} "
            f"A={self.ask:.4f}×{self.ask_size:.0f})"
        )

