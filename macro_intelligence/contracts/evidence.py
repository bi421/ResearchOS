"""
ResearchOS Macro Intelligence Layer - Evidence Object Contract
Version: ev/v1
Status: FROZEN
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class RevisionRef:
    """Reference to a revision in the revision chain."""
    revision_id: str
    original_evidence_id: str
    revision_number: int
    revision_time: datetime
    revision_reason: str
    superseded: bool = False
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "revision_id": self.revision_id,
            "original_evidence_id": self.original_evidence_id,
            "revision_number": self.revision_number,
            "revision_time": self.revision_time.isoformat(),
            "revision_reason": self.revision_reason,
            "superseded": self.superseded,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RevisionRef:
        return cls(
            revision_id=data["revision_id"],
            original_evidence_id=data["original_evidence_id"],
            revision_number=data["revision_number"],
            revision_time=datetime.fromisoformat(data["revision_time"]),
            revision_reason=data["revision_reason"],
            superseded=data.get("superseded", False),
        )


@dataclass(frozen=True)
class Transformation:
    """Record of a data transformation."""
    timestamp: datetime
    operation: str
    input_value: float | None
    output_value: float | None
    input_unit: str | None
    output_unit: str | None
    parameters: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "operation": self.operation,
            "input_value": self.input_value,
            "output_value": self.output_value,
            "input_unit": self.input_unit,
            "output_unit": self.output_unit,
            "parameters": self.parameters,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Transformation:
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            operation=data["operation"],
            input_value=data.get("input_value"),
            output_value=data.get("output_value"),
            input_unit=data.get("input_unit"),
            output_unit=data.get("output_unit"),
            parameters=data.get("parameters", {}),
        )


@dataclass(frozen=True)
class CheckResult:
    """Result of a verification check."""
    check_name: str
    result: str
    timestamp: datetime
    details: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "check_name": self.check_name,
            "result": self.result,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CheckResult:
        return cls(
            check_name=data["check_name"],
            result=data["result"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            details=data.get("details"),
        )


@dataclass(frozen=True)
class ProvenanceChain:
    """Full provenance trail for evidence."""
    original_source: str
    ingestion_pipeline: list[str]
    transformation_log: list[Transformation]
    verification_checks: list[CheckResult]
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "original_source": self.original_source,
            "ingestion_pipeline": self.ingestion_pipeline,
            "transformation_log": [t.to_dict() for t in self.transformation_log],
            "verification_checks": [c.to_dict() for c in self.verification_checks],
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProvenanceChain:
        transformations = [
            Transformation.from_dict(t) for t in data.get("transformation_log", [])
        ]
        checks = [
            CheckResult.from_dict(c) for c in data.get("verification_checks", [])
        ]
        return cls(
            original_source=data["original_source"],
            ingestion_pipeline=data.get("ingestion_pipeline", []),
            transformation_log=transformations,
            verification_checks=checks,
        )


@dataclass(frozen=True)
class EvidenceObject:
    """
    Immutable evidence object representing a single macroeconomic observation.
    
    Version: ev/v1
    Immutable: Yes (frozen=True)
    Every piece of data becomes an EvidenceObject.
    Evidence is never modified - revisions create new EvidenceObjects.
    """
    
    # Identity
    evidence_id: str
    
    # Source information
    source: str
    source_quality_score: float
    
    # Series reference
    series_reference: str
    
    # Time dimensions
    observation_time: datetime
    release_time: datetime | None
    available_time: datetime
    
    # Data values
    value: float | None
    forecast: float | None
    previous: float | None
    revision: RevisionRef | None
    
    # Quality metrics
    confidence: float
    quality_score: float
    
    # Provenance
    provenance: ProvenanceChain
    
    # Metadata
    metadata: dict = field(default_factory=dict)
    
    # Generated fields
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = "ev/v1"
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary with deterministic ordering."""
        return {
            "evidence_id": self.evidence_id,
            "source": self.source,
            "source_quality_score": self.source_quality_score,
            "series_reference": self.series_reference,
            "observation_time": self.observation_time.isoformat(),
            "release_time": self.release_time.isoformat() if self.release_time else None,
            "available_time": self.available_time.isoformat(),
            "value": self.value,
            "forecast": self.forecast,
            "previous": self.previous,
            "revision": self.revision.to_dict() if self.revision else None,
            "confidence": self.confidence,
            "quality_score": self.quality_score,
            "provenance": self.provenance.to_dict(),
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "version": self.version,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvidenceObject:
        """Deserialize from dictionary."""
        revision = None
        if data.get("revision"):
            revision = RevisionRef.from_dict(data["revision"])
        
        provenance = ProvenanceChain.from_dict(data.get("provenance", {}))
        
        return cls(
            evidence_id=data["evidence_id"],
            source=data["source"],
            source_quality_score=data["source_quality_score"],
            series_reference=data["series_reference"],
            observation_time=datetime.fromisoformat(data["observation_time"]),
            release_time=datetime.fromisoformat(data["release_time"]) if data.get("release_time") else None,
            available_time=datetime.fromisoformat(data["available_time"]),
            value=data.get("value"),
            forecast=data.get("forecast"),
            previous=data.get("previous"),
            revision=revision,
            confidence=data["confidence"],
            quality_score=data["quality_score"],
            provenance=provenance,
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now(timezone.utc).isoformat())),
            version=data.get("version", "ev/v1"),
        )
    
    def to_json(self) -> str:
        """Serialize to JSON with deterministic ordering."""
        import json
        return json.dumps(self.to_dict(), sort_keys=True, separators=(',', ':'))
    
    @classmethod
    def from_json(cls, json_str: str) -> EvidenceObject:
        """Deserialize from JSON."""
        import json
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def compute_hash(self) -> str:
        """
        Compute deterministic hash for the evidence object.
        
        MIL-DET-001: Hash depends ONLY on semantic data, never on runtime metadata.
        
        Allowed hash fields:
        - evidence_id, source, series_reference
        - observation_time, release_time, available_time
        - value, forecast, previous
        - confidence, quality_score
        - revision_id, revision_number
        
        Forbidden hash fields:
        - created_at (runtime metadata)
        - version (schema version, not semantic)
        """
        import hashlib
        import json
        # Create hash-specific dict excluding runtime metadata
        hash_data = {
            "evidence_id": self.evidence_id,
            "source": self.source,
            "source_quality_score": self.source_quality_score,
            "series_reference": self.series_reference,
            "observation_time": self.observation_time.isoformat(),
            "release_time": self.release_time.isoformat() if self.release_time else None,
            "available_time": self.available_time.isoformat(),
            "value": self.value,
            "forecast": self.forecast,
            "previous": self.previous,
            "revision_id": self.revision.revision_id if self.revision else None,
            "revision_number": self.revision.revision_number if self.revision else 0,
            "confidence": self.confidence,
            "quality_score": self.quality_score,
            "original_source": self.provenance.original_source,
        }
        canonical = json.dumps(hash_data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
    
    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate the evidence object.
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate evidence_id format
        if not self.evidence_id.startswith("EV_"):
            errors.append("evidence_id must start with 'EV_'")
        
        # Validate scores
        if not (0.0 <= self.source_quality_score <= 1.0):
            errors.append("source_quality_score must be between 0.0 and 1.0")
        if not (0.0 <= self.confidence <= 1.0):
            errors.append("confidence must be between 0.0 and 1.0")
        if not (0.0 <= self.quality_score <= 1.0):
            errors.append("quality_score must be between 0.0 and 1.0")
        
        # Validate provenance
        if not self.provenance.original_source:
            errors.append("provenance.original_source is required")
        if not self.provenance.ingestion_pipeline:
            errors.append("provenance.ingestion_pipeline is required")
        
        return (len(errors) == 0, errors)
