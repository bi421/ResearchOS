"""
ResearchOS Macro Intelligence Layer - MacroEvent Contract
Version: me/v1
Status: FROZEN
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from macro_intelligence.contracts.enums import (
    EventCategory,
    ImportanceLevel,
)


@dataclass(frozen=True)
class MarketRelevance:
    """Quantified market relevance metrics for an event."""

    volatility_impact: float
    liquidity_impact: float
    affected_instruments: list[str]
    correlation_score: float
    historical_similarity: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "volatility_impact": self.volatility_impact,
            "liquidity_impact": self.liquidity_impact,
            "affected_instruments": self.affected_instruments,
            "correlation_score": self.correlation_score,
            "historical_similarity": self.historical_similarity,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MarketRelevance:
        return cls(
            volatility_impact=data["volatility_impact"],
            liquidity_impact=data["liquidity_impact"],
            affected_instruments=data.get("affected_instruments", []),
            correlation_score=data["correlation_score"],
            historical_similarity=data.get("historical_similarity"),
        )


@dataclass(frozen=True)
class MacroEvent:
    """
    Immutable event object for macroeconomic events.

    Version: me/v1
    Immutable: Yes (frozen=True)

    Supports:
    - FOMC decisions
    - Fed speeches
    - Data releases
    - Geopolitical events
    - Sanctions
    - Major announcements
    """

    # Identity
    event_id: str

    # Event details
    event_type: EventCategory
    timestamp: datetime
    source: str
    description: str

    # Classification
    classification: str
    importance: ImportanceLevel

    # Market impact
    related_series: list[str]
    market_relevance: MarketRelevance

    # Metadata
    full_text: str | None = None
    source_urls: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    # Generated fields
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = "me/v1"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary with deterministic ordering."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "description": self.description,
            "classification": self.classification,
            "importance": self.importance.value,
            "related_series": self.related_series,
            "market_relevance": self.market_relevance.to_dict(),
            "full_text": self.full_text,
            "source_urls": self.source_urls,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MacroEvent:
        """Deserialize from dictionary."""
        market_relevance = MarketRelevance.from_dict(data.get("market_relevance", {}))

        return cls(
            event_id=data["event_id"],
            event_type=EventCategory(data["event_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            source=data["source"],
            description=data["description"],
            classification=data["classification"],
            importance=ImportanceLevel(data["importance"]),
            related_series=data.get("related_series", []),
            market_relevance=market_relevance,
            full_text=data.get("full_text"),
            source_urls=data.get("source_urls", []),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(
                data.get("created_at", datetime.now(timezone.utc).isoformat())
            ),
            version=data.get("version", "me/v1"),
        )

    def to_json(self) -> str:
        """Serialize to JSON with deterministic ordering."""
        import json

        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, json_str: str) -> MacroEvent:
        """Deserialize from JSON."""
        import json

        data = json.loads(json_str)
        return cls.from_dict(data)

    def compute_hash(self) -> str:
        """
        Compute deterministic hash for the event.

        MIL-DET-001: Hash depends ONLY on semantic data, never on runtime metadata.

        Allowed hash fields:
        - event_id, event_type, timestamp
        - source, description, classification
        - importance, related_series
        - volatility_impact, correlation_score

        Forbidden hash fields:
        - created_at (runtime metadata)
        - version (schema version, not semantic)
        """
        import hashlib
        import json

        # Create hash-specific dict excluding runtime metadata
        hash_data = {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "description": self.description,
            "classification": self.classification,
            "importance": self.importance.value,
            "related_series": sorted(self.related_series),
            "volatility_impact": self.market_relevance.volatility_impact,
            "liquidity_impact": self.market_relevance.liquidity_impact,
            "correlation_score": self.market_relevance.correlation_score,
        }
        canonical = json.dumps(hash_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate the event object.

        Returns:
            (is_valid, list_of_errors)
        """
        errors = []

        # Validate event_id format
        if not self.event_id.startswith("EVNT_"):
            errors.append("event_id must start with 'EVNT_'")

        # Validate description
        if not self.description or len(self.description) > 1024:
            errors.append("description must be non-empty and max 1024 chars")

        # Validate importance
        if self.importance not in ImportanceLevel:
            errors.append("invalid importance level")

        # Validate related_series
        if not self.related_series:
            errors.append("related_series cannot be empty")

        return (len(errors) == 0, errors)
