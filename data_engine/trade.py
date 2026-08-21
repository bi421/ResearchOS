"""
Trade model — individual trade/transaction record.

Based on Article XVII: Object Model — Data Layer.

A Trade represents a single executed transaction in the market,
including price, volume, and optional trade metadata.

Guarantees:
    - Deterministic: Same inputs → same ID and hash
    - Serializable: Supports to_dict/from_dict
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id
from researchos.core.lifecycle import LifecycleStage
from researchos.core.timestamp import parse_timestamp


class Trade(BaseObject):
    """
    A single executed trade/transaction in the market.

    Attributes:
        symbol: The trading symbol.
        timestamp: UTC timestamp of the trade.
        price: Execution price.
        volume: Executed volume.
        side: Trade side (buy, sell, unknown).
        exchange: Optional exchange identifier.
        conditions: Optional list of trade condition flags.
        trade_id: Optional exchange-assigned trade ID.
        is_block_trade: Whether this is a large block trade.
    """

    def __init__(
        self,
        symbol: str,
        timestamp: datetime,
        price: float,
        volume: float,
        side: str = "unknown",
        exchange: str = "",
        conditions: list[str] | None = None,
        trade_id: str = "",
        is_block_trade: bool = False,
        ontology_tags: list[str] | None = None,
        id: str | None = None,
    ):
        if id is None:
            ts_str = timestamp.isoformat() if hasattr(timestamp, "isoformat") else str(timestamp)
            seed = f"Trade|{symbol}|{ts_str}|{price}|{volume}|{side}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.symbol = symbol
        self.timestamp = timestamp
        self.price = price
        self.volume = volume
        self.side = side
        self.exchange = exchange
        self.conditions: list[str] = conditions or []
        self.trade_id = trade_id
        self.is_block_trade = is_block_trade

        self.lifecycle.transition(
            LifecycleStage.CREATED,
            reason=f"Trade created: {symbol} @ {timestamp}",
        )

    @property
    def notional(self) -> float:
        """Notional value of the trade (price × volume)."""
        return self.price * self.volume

    @property
    def is_buy(self) -> bool:
        """Whether this is a buy trade."""
        return self.side == "buy"

    @property
    def is_sell(self) -> bool:
        """Whether this is a sell trade."""
        return self.side == "sell"

    def _to_hashable_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "price": round(self.price, 10),
            "volume": round(self.volume, 10),
            "side": self.side,
            "exchange": self.exchange,
            "conditions": sorted(self.conditions),
            "trade_id": self.trade_id,
            "is_block_trade": self.is_block_trade,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict[str, Any]:
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
                "trade_id": self.trade_id,
                "is_block_trade": self.is_block_trade,
                "notional": self.notional,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Trade:
        obj = super().from_dict(data)
        obj.symbol = data["symbol"]
        obj.timestamp = parse_timestamp(data["timestamp"])
        obj.price = float(data["price"])
        obj.volume = float(data["volume"])
        obj.side = data.get("side", "unknown")
        obj.exchange = data.get("exchange", "")
        obj.conditions = list(data.get("conditions", []))
        obj.trade_id = data.get("trade_id", "")
        obj.is_block_trade = bool(data.get("is_block_trade", False))
        return obj

    def __repr__(self) -> str:
        return (
            f"Trade({self.symbol}, {self.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')}, "
            f"P={self.price:.4f} V={self.volume:.0f} {self.side})"
        )
