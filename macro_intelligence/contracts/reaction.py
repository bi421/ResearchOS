"""
ResearchOS Macro Intelligence Layer - MarketReaction Contract
Version: mr/v1
Status: FROZEN
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any


@dataclass(frozen=True)
class WindowSpec:
    """Window specification for market reaction analysis."""
    start_offset: timedelta
    end_offset: timedelta
    start_price: float | None = None
    end_price: float | None = None
    start_volatility: float | None = None
    end_volatility: float | None = None
    start_liquidity: float | None = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "start_offset_seconds": self.start_offset.total_seconds(),
            "end_offset_seconds": self.end_offset.total_seconds(),
            "start_price": self.start_price,
            "end_price": self.end_price,
            "start_volatility": self.start_volatility,
            "end_volatility": self.end_volatility,
            "start_liquidity": self.start_liquidity,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WindowSpec:
        return cls(
            start_offset=timedelta(seconds=data.get("start_offset_seconds", -24*3600)),
            end_offset=timedelta(seconds=data.get("end_offset_seconds", 24*3600)),
            start_price=data.get("start_price"),
            end_price=data.get("end_price"),
            start_volatility=data.get("start_volatility"),
            end_volatility=data.get("end_volatility"),
            start_liquidity=data.get("start_liquidity"),
        )


@dataclass(frozen=True)
class ReactionMetrics:
    """Quantified reaction metrics."""
    return_bps: float
    volatility_change_bps: float
    volume_change_pct: float
    bid_ask_widen_bps: float
    max_drawdown_bps: float
    max_spike_bps: float
    reaction_significance: float
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "return_bps": self.return_bps,
            "volatility_change_bps": self.volatility_change_bps,
            "volume_change_pct": self.volume_change_pct,
            "bid_ask_widen_bps": self.bid_ask_widen_bps,
            "max_drawdown_bps": self.max_drawdown_bps,
            "max_spike_bps": self.max_spike_bps,
            "reaction_significance": self.reaction_significance,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReactionMetrics:
        return cls(
            return_bps=data["return_bps"],
            volatility_change_bps=data["volatility_change_bps"],
            volume_change_pct=data["volume_change_pct"],
            bid_ask_widen_bps=data["bid_ask_widen_bps"],
            max_drawdown_bps=data["max_drawdown_bps"],
            max_spike_bps=data["max_spike_bps"],
            reaction_significance=data["reaction_significance"],
        )


@dataclass(frozen=True)
class MarketReaction:
    """
    Immutable market reaction object.
    
    Version: mr/v1
    Immutable: Yes (frozen=True)
    
    Captures pre/post event market state and reactions.
    """
    
    # Identity
    event_id: str
    instrument: str
    
    # Windows
    window_before: WindowSpec
    window_after: WindowSpec
    
    # Metrics
    reaction_metrics: ReactionMetrics
    
    # Metadata
    calculation_version: str = "mr/v1.0.0"
    metadata: dict = field(default_factory=dict)
    
    # Generated
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = "mr/v1"
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "event_id": self.event_id,
            "instrument": self.instrument,
            "window_before": self.window_before.to_dict(),
            "window_after": self.window_after.to_dict(),
            "reaction_metrics": self.reaction_metrics.to_dict(),
            "calculation_version": self.calculation_version,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "version": self.version,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MarketReaction:
        """Deserialize from dictionary."""
        return cls(
            event_id=data["event_id"],
            instrument=data["instrument"],
            window_before=WindowSpec.from_dict(data["window_before"]),
            window_after=WindowSpec.from_dict(data["window_after"]),
            reaction_metrics=ReactionMetrics.from_dict(data["reaction_metrics"]),
            calculation_version=data.get("calculation_version", "mr/v1.0.0"),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now(timezone.utc).isoformat())),
            version=data.get("version", "mr/v1"),
        )
    
    def to_json(self) -> str:
        """Serialize to JSON with deterministic ordering."""
        import json
        return json.dumps(self.to_dict(), sort_keys=True, separators=(',', ':'))
    
    @classmethod
    def from_json(cls, json_str: str) -> MarketReaction:
        """Deserialize from JSON."""
        import json
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def compute_hash(self) -> str:
        """
        Compute deterministic hash for the market reaction.
        
        MIL-DET-001: Hash depends ONLY on semantic data, never on runtime metadata.
        
        Allowed hash fields:
        - event_id, instrument
        - window specs, reaction metrics
        
        Forbidden hash fields:
        - created_at (runtime metadata)
        - version (schema version, not semantic)
        """
        import hashlib
        import json
        # Create hash-specific dict excluding runtime metadata
        hash_data = {
            "event_id": self.event_id,
            "instrument": self.instrument,
            "window_before": self.window_before.to_dict(),
            "window_after": self.window_after.to_dict(),
            "reaction_metrics": self.reaction_metrics.to_dict(),
            "calculation_version": self.calculation_version,
        }
        canonical = json.dumps(hash_data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class StatisticalSupport:
    """Statistical backing for knowledge claims."""
    sample_size: int
    p_value: float
    confidence_interval: tuple[float, float]
    effect_size: float
    test_method: str
    assumptions_valid: bool
    limitations: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "sample_size": self.sample_size,
            "p_value": self.p_value,
            "confidence_interval": list(self.confidence_interval),
            "effect_size": self.effect_size,
            "test_method": self.test_method,
            "assumptions_valid": self.assumptions_valid,
            "limitations": self.limitations,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StatisticalSupport:
        return cls(
            sample_size=data["sample_size"],
            p_value=data["p_value"],
            confidence_interval=tuple(data["confidence_interval"]),
            effect_size=data["effect_size"],
            test_method=data["test_method"],
            assumptions_valid=data["assumptions_valid"],
            limitations=data.get("limitations", []),
        )
