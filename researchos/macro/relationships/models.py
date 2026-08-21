"""
ResearchOS Macro Intelligence Layer - Relationship Engine Models

Defines the data structures used by the historical relationship analysis engine.
All models are frozen (immutable) dataclasses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from researchos.macro.statistics.provenance import StatisticalProvenance

ALGORITHM_VERSION = "rel-eng/v5.0.0"


class RelationshipType(Enum):
    """Types of statistical relationships."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    NO_DATA = "no_data"


class RelationshipStrength(Enum):
    """Strength of a statistical relationship."""

    VERY_STRONG = "very_strong"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    NEGLIGIBLE = "negligible"


class LagType(Enum):
    """Types of lag relationships."""

    LEADING = "leading"
    LAGGING = "lagging"
    SIMULTANEOUS = "simultaneous"
    UNKNOWN = "unknown"


class BreakType(Enum):
    """Types of structural breaks."""

    STRENGTH_CHANGE = "strength_change"
    DIRECTION_CHANGE = "direction_change"
    SIGNIFICANCE_LOSS = "significance_loss"
    SIGNIFICANCE_GAIN = "significance_gain"


@dataclass(frozen=True)
class CorrelationResult:
    """Result of a correlation analysis between two series."""

    series_a: str
    series_b: str
    correlation: float
    p_value: float | None = None
    sample_size: int = 0
    method: str = "pearson"
    relationship_type: str = RelationshipType.NEUTRAL.value
    relationship_strength: str = RelationshipStrength.NEGLIGIBLE.value
    observation_start: str = ""
    observation_end: str = ""
    algorithm_version: str = ALGORITHM_VERSION
    evidence_refs: list[str] = field(default_factory=list)
    provenance: Optional[StatisticalProvenance] = None

    def to_dict(self) -> dict[str, Any]:
        d = {
            "series_a": self.series_a,
            "series_b": self.series_b,
            "correlation": round(self.correlation, 6),
            "p_value": round(self.p_value, 6) if self.p_value is not None else None,
            "sample_size": self.sample_size,
            "method": self.method,
            "relationship_type": self.relationship_type,
            "relationship_strength": self.relationship_strength,
            "observation_start": self.observation_start,
            "observation_end": self.observation_end,
            "algorithm_version": self.algorithm_version,
            "evidence_refs": sorted(self.evidence_refs),
        }
        if self.provenance is not None:
            d["provenance"] = self.provenance.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CorrelationResult:
        prov = None
        if data.get("provenance"):
            prov = StatisticalProvenance.from_dict(data["provenance"])
        return cls(
            series_a=data["series_a"],
            series_b=data["series_b"],
            correlation=data["correlation"],
            p_value=data.get("p_value"),
            sample_size=data.get("sample_size", 0),
            method=data.get("method", "pearson"),
            relationship_type=data.get("relationship_type", RelationshipType.NEUTRAL.value),
            relationship_strength=data.get(
                "relationship_strength", RelationshipStrength.NEGLIGIBLE.value
            ),
            observation_start=data.get("observation_start", ""),
            observation_end=data.get("observation_end", ""),
            algorithm_version=data.get("algorithm_version", ALGORITHM_VERSION),
            evidence_refs=data.get("evidence_refs", []),
            provenance=prov,
        )

    def to_json(self) -> str:
        import json

        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, json_str: str) -> CorrelationResult:
        import json

        return cls.from_dict(json.loads(json_str))

    def compute_hash(self) -> str:
        import hashlib
        import json

        h = {
            "series_a": self.series_a,
            "series_b": self.series_b,
            "correlation": self.correlation,
            "method": self.method,
        }
        return hashlib.sha256(
            json.dumps(h, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


@dataclass(frozen=True)
class RollingCorrelationResult:
    """Rolling correlation result for a time window."""

    series_a: str
    series_b: str
    window_size: int
    correlations: list[float] = field(default_factory=list)
    timestamps: list[str] = field(default_factory=list)
    stability: float = 0.0  # Standard deviation of correlations
    algorithm_version: str = ALGORITHM_VERSION
    provenance: Optional[StatisticalProvenance] = None

    def to_dict(self) -> dict[str, Any]:
        d = {
            "series_a": self.series_a,
            "series_b": self.series_b,
            "window_size": self.window_size,
            "correlations": [round(c, 6) for c in self.correlations],
            "timestamps": self.timestamps,
            "stability": round(self.stability, 6),
            "algorithm_version": self.algorithm_version,
        }
        if self.provenance is not None:
            d["provenance"] = self.provenance.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RollingCorrelationResult:
        prov = None
        if data.get("provenance"):
            prov = StatisticalProvenance.from_dict(data["provenance"])
        return cls(
            series_a=data["series_a"],
            series_b=data["series_b"],
            window_size=data["window_size"],
            correlations=data.get("correlations", []),
            timestamps=data.get("timestamps", []),
            stability=data.get("stability", 0.0),
            algorithm_version=data.get("algorithm_version", ALGORITHM_VERSION),
            provenance=prov,
        )

    def compute_hash(self) -> str:
        import hashlib
        import json

        h = {
            "series_a": self.series_a,
            "series_b": self.series_b,
            "window_size": self.window_size,
            "stability": self.stability,
        }
        return hashlib.sha256(
            json.dumps(h, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


@dataclass(frozen=True)
class LagRelationship:
    """Lag relationship between two series."""

    series_a: str
    series_b: str
    optimal_lag: int  # Positive = a leads b, Negative = b leads a
    lag_correlation: float
    lag_type: str = LagType.UNKNOWN.value
    confidence: float = 0.0
    algorithm_version: str = ALGORITHM_VERSION
    evidence_refs: list[str] = field(default_factory=list)
    provenance: Optional[StatisticalProvenance] = None

    def to_dict(self) -> dict[str, Any]:
        d = {
            "series_a": self.series_a,
            "series_b": self.series_b,
            "optimal_lag": self.optimal_lag,
            "lag_correlation": round(self.lag_correlation, 6),
            "lag_type": self.lag_type,
            "confidence": round(self.confidence, 4),
            "algorithm_version": self.algorithm_version,
            "evidence_refs": sorted(self.evidence_refs),
        }
        if self.provenance is not None:
            d["provenance"] = self.provenance.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LagRelationship:
        prov = None
        if data.get("provenance"):
            prov = StatisticalProvenance.from_dict(data["provenance"])
        return cls(
            series_a=data["series_a"],
            series_b=data["series_b"],
            optimal_lag=data["optimal_lag"],
            lag_correlation=data["lag_correlation"],
            lag_type=data.get("lag_type", LagType.UNKNOWN.value),
            confidence=data.get("confidence", 0.0),
            algorithm_version=data.get("algorithm_version", ALGORITHM_VERSION),
            evidence_refs=data.get("evidence_refs", []),
            provenance=prov,
        )

    def compute_hash(self) -> str:
        import hashlib
        import json

        h = {
            "series_a": self.series_a,
            "series_b": self.series_b,
            "optimal_lag": self.optimal_lag,
            "lag_correlation": self.lag_correlation,
        }
        return hashlib.sha256(
            json.dumps(h, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


@dataclass(frozen=True)
class RegimeRelationship:
    """Relationship between two series conditioned on regime."""

    series_a: str
    series_b: str
    regime: str
    correlation: float
    sample_size: int = 0
    confidence: float = 0.0
    algorithm_version: str = ALGORITHM_VERSION
    provenance: Optional[StatisticalProvenance] = None

    def to_dict(self) -> dict[str, Any]:
        d = {
            "series_a": self.series_a,
            "series_b": self.series_b,
            "regime": self.regime,
            "correlation": round(self.correlation, 6),
            "sample_size": self.sample_size,
            "confidence": round(self.confidence, 4),
            "algorithm_version": self.algorithm_version,
        }
        if self.provenance is not None:
            d["provenance"] = self.provenance.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RegimeRelationship:
        prov = None
        if data.get("provenance"):
            prov = StatisticalProvenance.from_dict(data["provenance"])
        return cls(
            series_a=data["series_a"],
            series_b=data["series_b"],
            regime=data["regime"],
            correlation=data["correlation"],
            sample_size=data.get("sample_size", 0),
            confidence=data.get("confidence", 0.0),
            algorithm_version=data.get("algorithm_version", ALGORITHM_VERSION),
            provenance=prov,
        )

    def compute_hash(self) -> str:
        import hashlib
        import json

        h = {
            "series_a": self.series_a,
            "series_b": self.series_b,
            "regime": self.regime,
            "correlation": self.correlation,
        }
        return hashlib.sha256(
            json.dumps(h, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


@dataclass(frozen=True)
class StructuralBreak:
    """Detected structural break in a relationship."""

    series_a: str
    series_b: str
    break_point: str  # ISO datetime
    break_type: str  # One of BreakType values
    correlation_before: float
    correlation_after: float
    confidence: float = 0.0
    algorithm_version: str = ALGORITHM_VERSION
    provenance: Optional[StatisticalProvenance] = None

    def to_dict(self) -> dict[str, Any]:
        d = {
            "series_a": self.series_a,
            "series_b": self.series_b,
            "break_point": self.break_point,
            "break_type": self.break_type,
            "correlation_before": round(self.correlation_before, 6),
            "correlation_after": round(self.correlation_after, 6),
            "confidence": round(self.confidence, 4),
            "algorithm_version": self.algorithm_version,
        }
        if self.provenance is not None:
            d["provenance"] = self.provenance.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StructuralBreak:
        prov = None
        if data.get("provenance"):
            prov = StatisticalProvenance.from_dict(data["provenance"])
        return cls(
            series_a=data["series_a"],
            series_b=data["series_b"],
            break_point=data["break_point"],
            break_type=data["break_type"],
            correlation_before=data["correlation_before"],
            correlation_after=data["correlation_after"],
            confidence=data.get("confidence", 0.0),
            algorithm_version=data.get("algorithm_version", ALGORITHM_VERSION),
            provenance=prov,
        )

    def compute_hash(self) -> str:
        import hashlib
        import json

        h = {
            "series_a": self.series_a,
            "series_b": self.series_b,
            "break_point": self.break_point,
            "break_type": self.break_type,
        }
        return hashlib.sha256(
            json.dumps(h, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


@dataclass(frozen=True)
class RelationshipResult:
    """Complete relationship analysis result for a pair of series."""

    series_a: str
    series_b: str
    overall_correlation: CorrelationResult | None = None
    rolling_correlation: RollingCorrelationResult | None = None
    lag_relationship: LagRelationship | None = None
    regime_relationships: list[RegimeRelationship] = field(default_factory=list)
    structural_breaks: list[StructuralBreak] = field(default_factory=list)
    algorithm_version: str = ALGORITHM_VERSION
    analysis_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    evidence_refs: list[str] = field(default_factory=list)
    provenance: Optional[StatisticalProvenance] = None

    def to_dict(self) -> dict[str, Any]:
        result = {
            "series_a": self.series_a,
            "series_b": self.series_b,
            "algorithm_version": self.algorithm_version,
            "analysis_time": self.analysis_time.isoformat(),
            "evidence_refs": sorted(self.evidence_refs),
        }
        if self.provenance is not None:
            result["provenance"] = self.provenance.to_dict()
        if self.overall_correlation:
            result["overall_correlation"] = self.overall_correlation.to_dict()
        if self.rolling_correlation:
            result["rolling_correlation"] = self.rolling_correlation.to_dict()
        if self.lag_relationship:
            result["lag_relationship"] = self.lag_relationship.to_dict()
        if self.regime_relationships:
            result["regime_relationships"] = [r.to_dict() for r in self.regime_relationships]
        if self.structural_breaks:
            result["structural_breaks"] = [b.to_dict() for b in self.structural_breaks]
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RelationshipResult:
        overall = (
            CorrelationResult.from_dict(data["overall_correlation"])
            if data.get("overall_correlation")
            else None
        )
        rolling = (
            RollingCorrelationResult.from_dict(data["rolling_correlation"])
            if data.get("rolling_correlation")
            else None
        )
        lag = (
            LagRelationship.from_dict(data["lag_relationship"])
            if data.get("lag_relationship")
            else None
        )
        regime_rels = [
            RegimeRelationship.from_dict(r) for r in data.get("regime_relationships", [])
        ]
        breaks = [StructuralBreak.from_dict(b) for b in data.get("structural_breaks", [])]
        prov = None
        if data.get("provenance"):
            prov = StatisticalProvenance.from_dict(data["provenance"])
        return cls(
            series_a=data["series_a"],
            series_b=data["series_b"],
            overall_correlation=overall,
            rolling_correlation=rolling,
            lag_relationship=lag,
            regime_relationships=regime_rels,
            structural_breaks=breaks,
            algorithm_version=data.get("algorithm_version", ALGORITHM_VERSION),
            analysis_time=datetime.fromisoformat(data["analysis_time"]),
            evidence_refs=data.get("evidence_refs", []),
            provenance=prov,
        )

    def to_json(self) -> str:
        import json

        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, json_str: str) -> RelationshipResult:
        import json

        return cls.from_dict(json.loads(json_str))

    def compute_hash(self) -> str:
        import hashlib
        import json

        h = {
            "series_a": self.series_a,
            "series_b": self.series_b,
            "algorithm_version": self.algorithm_version,
            "overall_corr_hash": (
                self.overall_correlation.compute_hash() if self.overall_correlation else None
            ),
            "lag_hash": self.lag_relationship.compute_hash() if self.lag_relationship else None,
        }
        return hashlib.sha256(
            json.dumps(h, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
