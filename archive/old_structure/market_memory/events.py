"""
Market events — discrete events that affect market conditions.

Tracks scheduled and unscheduled events that impact:
    - Central bank decisions (Fed, ECB, etc.)
    - Economic data releases (CPI, NFP, GDP, etc.)
    - Geopolitical events
    - Market structure events (liquidity sweeps, BOS, CHOCH)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id
from researchos.core.timestamp import parse_timestamp


class MacroMarketEvent(BaseObject):
    """
    A discrete event that affects market conditions.

    Renamed from ``MarketEvent`` (2026-08-17) to end the name collision with
    ``researchos.objects.market_memory.MarketEvent`` (the price-structure
    event object registered in the storage OBJECT_REGISTRY) — this class
    models calendar/macro releases instead.  Serialization is unchanged:
    the legacy ``object_type`` string and ID seed are pinned.
    See docs/architecture/OWNERSHIP.md.

    Attributes:
        event_type: Type of event ("Fed", "CPI", "NFP", "Geopolitical", etc.)
        timestamp: UTC timestamp of the event
        asset: Associated asset if applicable
        description: Human-readable description
        impact: Estimated impact level ("High", "Medium", "Low")
        actual_value: Actual released value (for data events)
        expected_value: Expected/forecast value
        previous_value: Previous period value
        source: Source of the event
    """

    def __init__(
        self,
        event_type: str,
        timestamp: datetime,
        asset: str = "",
        description: str = "",
        impact: str = "Medium",
        actual_value: float = 0.0,
        expected_value: float = 0.0,
        previous_value: float = 0.0,
        source: str = "",
        ontology_tags: list[str] | None = None,
        id: str | None = None,
    ):
        if id is None:
            seed = f"MarketEvent|{event_type}|{timestamp.isoformat()}|{description[:100]}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.event_type = event_type
        self.timestamp = timestamp
        self.asset = asset
        self.description = description
        self.impact = impact
        self.actual_value = actual_value
        self.expected_value = expected_value
        self.previous_value = previous_value
        self.source = source

    def _to_hashable_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "asset": self.asset,
            "description": self.description,
            "impact": self.impact,
            "actual_value": self.actual_value,
            "expected_value": self.expected_value,
            "previous_value": self.previous_value,
            "source": self.source,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        # Legacy serialization pin — object_type stays "MarketEvent" so that
        # renamed-class dicts remain byte-identical with stored data.
        base["object_type"] = "MarketEvent"
        base.update(
            {
                "event_type": self.event_type,
                "timestamp": self.timestamp.isoformat(),
                "asset": self.asset,
                "description": self.description,
                "impact": self.impact,
                "actual_value": self.actual_value,
                "expected_value": self.expected_value,
                "previous_value": self.previous_value,
                "source": self.source,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> MacroMarketEvent:
        obj = super().from_dict(data)
        obj.event_type = data["event_type"]
        obj.timestamp = parse_timestamp(data["timestamp"])
        obj.asset = data.get("asset", "")
        obj.description = data.get("description", "")
        obj.impact = data.get("impact", "Medium")
        obj.actual_value = data.get("actual_value", 0.0)
        obj.expected_value = data.get("expected_value", 0.0)
        obj.previous_value = data.get("previous_value", 0.0)
        obj.source = data.get("source", "")
        return obj


# Deprecated compatibility alias — canonical name is ``MacroMarketEvent``.
MarketEvent = MacroMarketEvent
