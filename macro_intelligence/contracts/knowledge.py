"""
ResearchOS Macro Intelligence Layer - Knowledge Object Contract
Version: ko/v1
Status: FROZEN
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any
from macro_intelligence.contracts.reaction import StatisticalSupport
from macro_intelligence.contracts.enums import PatternType


@dataclass(frozen=True)
class Pattern:
    """Detected pattern in data."""
    type: PatternType
    description: str
    confidence: float
    evidence_refs: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type.value,
            "description": self.description,
            "confidence": self.confidence,
            "evidence_refs": self.evidence_refs,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Pattern:
        return cls(
            type=PatternType(data["type"]),
            description=data["description"],
            confidence=data["confidence"],
            evidence_refs=data.get("evidence_refs", []),
        )


@dataclass(frozen=True)
class StatisticalAnalysis:
    """Statistical analysis results."""
    series_id: str
    mean: float | None
    std: float | None
    trend: str | None  # "UPWARD", "DOWNWARD", "NEUTRAL"
    volatility: float | None
    observations: int
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "series_id": self.series_id,
            "mean": round(self.mean, 4) if self.mean else None,
            "std": round(self.std, 4) if self.std else None,
            "trend": self.trend,
            "volatility": round(self.volatility, 4) if self.volatility else None,
            "observations": self.observations,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StatisticalAnalysis:
        return cls(
            series_id=data["series_id"],
            mean=data.get("mean"),
            std=data.get("std"),
            trend=data.get("trend"),
            volatility=data.get("volatility"),
            observations=data.get("observations", 0),
        )


@dataclass(frozen=True)
class KnowledgeObject:
    """
    Generated knowledge object from evidence analysis.
    
    Version: ko/v1
    Immutable: Yes (frozen=True)
    
    Knowledge objects are deterministic outputs of the analysis pipeline.
    They are immutable and auditable.
    """
    
    # Identity
    knowledge_id: str
    version: str = "ko/v1"
    
    # Reference
    series_id: str = ""
    date: date = field(default_factory=lambda: date.today())
    
    # Evidence backing
    evidence_refs: list[str] = field(default_factory=list)
    patterns: list[Pattern] = field(default_factory=list)
    
    # Statistical summary
    statistics: StatisticalAnalysis | None = None
    
    # Quality metrics
    confidence: float = 0.0
    
    # Human-readable output
    explanation: str = ""
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    generation_pipeline: str = "deterministic"
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "knowledge_id": self.knowledge_id,
            "version": self.version,
            "series_id": self.series_id,
            "date": self.date.isoformat(),
            "evidence_refs": self.evidence_refs,
            "patterns": [p.to_dict() for p in self.patterns],
            "statistics": self.statistics.to_dict() if self.statistics else None,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "created_at": self.created_at.isoformat(),
            "generation_pipeline": self.generation_pipeline,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KnowledgeObject:
        """Deserialize from dictionary."""
        patterns = [Pattern.from_dict(p) for p in data.get("patterns", [])]
        statistics = StatisticalAnalysis.from_dict(data["statistics"]) if data.get("statistics") else None
        
        return cls(
            knowledge_id=data["knowledge_id"],
            version=data.get("version", "ko/v1"),
            series_id=data["series_id"],
            date=date.fromisoformat(data["date"]),
            evidence_refs=data.get("evidence_refs", []),
            patterns=patterns,
            statistics=statistics,
            confidence=data["confidence"],
            explanation=data["explanation"],
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now(timezone.utc).isoformat())),
            generation_pipeline=data.get("generation_pipeline", "deterministic"),
        )
    
    def to_json(self) -> str:
        """Serialize to JSON with deterministic ordering."""
        import json
        return json.dumps(self.to_dict(), sort_keys=True, separators=(',', ':'))
    
    @classmethod
    def from_json(cls, json_str: str) -> KnowledgeObject:
        """Deserialize from JSON."""
        import json
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def compute_hash(self) -> str:
        """
        Compute deterministic hash for the knowledge object.
        
        MIL-DET-001: Hash depends ONLY on semantic data, never on runtime metadata.
        
        Allowed hash fields:
        - knowledge_id, series_id, date
        - evidence_refs, patterns
        - statistics, confidence, explanation
        
        Forbidden hash fields:
        - created_at (runtime metadata)
        - version (schema version, not semantic)
        """
        import hashlib
        import json
        # Create hash-specific dict excluding runtime metadata
        hash_data = {
            "knowledge_id": self.knowledge_id,
            "series_id": self.series_id,
            "date": self.date.isoformat(),
            "evidence_refs": sorted(self.evidence_refs),
            "patterns": [p.to_dict() for p in sorted(self.patterns, key=lambda x: x.type.value)],
            "statistics": self.statistics.to_dict() if self.statistics else None,
            "confidence": self.confidence,
            "explanation": self.explanation,
        }
        canonical = json.dumps(hash_data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
    
    def validate(self) -> tuple[bool, list[str]]:
        """Validate the knowledge object."""
        errors = []
        
        if not self.knowledge_id.startswith("KN_"):
            errors.append("knowledge_id must start with 'KN_'")
        
        if not self.explanation or len(self.explanation) > 4096:
            errors.append("explanation must be non-empty and max 4096 chars")
        
        if not (0.0 <= self.confidence <= 1.0):
            errors.append("confidence must be between 0.0 and 1.0")
        
        return (len(errors) == 0, errors)
