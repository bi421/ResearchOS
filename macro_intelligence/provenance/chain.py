"""
ResearchOS Macro Intelligence Layer - Provenance Chain
Version: prov/v1
Status: FROZEN
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from macro_intelligence.revision.enums import ProvenanceSource


@dataclass(frozen=True)
class SourceRecord:
    """
    Record of a data source.

    Tracks the origin of data including:
    - Source identifier
    - Source version
    - Source quality
    - Timestamp of ingestion
    """

    source_id: str
    source_type: ProvenanceSource
    source_version: str
    source_quality_score: float
    ingestion_timestamp: datetime
    batch_id: str
    adapter_version: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "source_id": self.source_id,
            "source_type": self.source_type.value,
            "source_version": self.source_version,
            "source_quality_score": self.source_quality_score,
            "ingestion_timestamp": self.ingestion_timestamp.isoformat(),
            "batch_id": self.batch_id,
            "adapter_version": self.adapter_version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SourceRecord:
        """Deserialize from dictionary."""
        return cls(
            source_id=data["source_id"],
            source_type=ProvenanceSource(data["source_type"]),
            source_version=data["source_version"],
            source_quality_score=data["source_quality_score"],
            ingestion_timestamp=datetime.fromisoformat(data["ingestion_timestamp"]),
            batch_id=data["batch_id"],
            adapter_version=data["adapter_version"],
        )


@dataclass(frozen=True)
class ProcessingRecord:
    """
    Record of processing steps applied to data.

    Tracks:
    - Normalization version
    - Validation version
    - Transformation log
    - Quality scores at each step
    """

    normalization_version: str
    validation_version: str
    quality_score_before: float
    quality_score_after: float
    transformations_applied: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "normalization_version": self.normalization_version,
            "validation_version": self.validation_version,
            "quality_score_before": self.quality_score_before,
            "quality_score_after": self.quality_score_after,
            "transformations_applied": self.transformations_applied,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProcessingRecord:
        """Deserialize from dictionary."""
        return cls(
            normalization_version=data["normalization_version"],
            validation_version=data["validation_version"],
            quality_score_before=data["quality_score_before"],
            quality_score_after=data["quality_score_after"],
            transformations_applied=data.get("transformations_applied", []),
        )


@dataclass(frozen=True)
class EvidenceReference:
    """
    Reference to related evidence objects.

    Tracks:
    - Evidence IDs this object references
    - Evidence IDs that reference this object
    - Relationship type
    """

    evidence_id: str
    relationship_type: str  # "references", "referenced_by", "parent", "child"
    timestamp: datetime

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "evidence_id": self.evidence_id,
            "relationship_type": self.relationship_type,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvidenceReference:
        """Deserialize from dictionary."""
        return cls(
            evidence_id=data["evidence_id"],
            relationship_type=data["relationship_type"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


@dataclass(frozen=True)
class ProvenanceChain:
    """
    Complete provenance chain for an object.

    MIL-PROV-001: Every stored object must preserve complete provenance.

    Tracks the complete lifecycle of data from source to storage:
    1. Source information
    2. Processing steps
    3. Evidence relationships
    4. Schema version
    """

    # Source information
    source_record: SourceRecord

    # Processing information
    processing_record: ProcessingRecord

    # Schema information
    schema_version: str
    object_type: str

    # Evidence relationships
    evidence_references: list[EvidenceReference] = field(default_factory=list)

    # Metadata
    metadata: dict = field(default_factory=dict)

    # Generated
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = "prov/v1"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary with deterministic ordering."""
        return {
            "source_record": self.source_record.to_dict(),
            "processing_record": self.processing_record.to_dict(),
            "schema_version": self.schema_version,
            "object_type": self.object_type,
            "evidence_references": [ref.to_dict() for ref in self.evidence_references],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProvenanceChain:
        """Deserialize from dictionary."""
        evidence_refs = [
            EvidenceReference.from_dict(ref) for ref in data.get("evidence_references", [])
        ]

        return cls(
            source_record=SourceRecord.from_dict(data["source_record"]),
            processing_record=ProcessingRecord.from_dict(data["processing_record"]),
            schema_version=data["schema_version"],
            object_type=data["object_type"],
            evidence_references=evidence_refs,
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(
                data.get("created_at", datetime.now(timezone.utc).isoformat())
            ),
            version=data.get("version", "prov/v1"),
        )

    def to_json(self) -> str:
        """Serialize to JSON with deterministic ordering."""
        import json

        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, json_str: str) -> ProvenanceChain:
        """Deserialize from JSON."""
        import json

        data = json.loads(json_str)
        return cls.from_dict(data)

    def compute_hash(self) -> str:
        """
        Compute deterministic hash for the provenance chain.

        The runtime wall-clock ``created_at`` is excluded from the hashed
        content (like ``execution_timestamp`` in the V1 core) so that
        identical provenance inputs produce identical hashes regardless of
        when the instances were constructed. The timestamp remains present
        in ``to_dict``/``to_json`` for auditability.

        Returns:
            SHA-256 hex digest
        """
        import hashlib

        content = self.to_dict()
        content.pop("created_at", None)
        content.pop("metadata", None)
        # Serialize all associated records deterministically.
        content["source_record"] = self.source_record.to_dict()
        content["processing_record"] = self.processing_record.to_dict()
        content["evidence_references"] = [ref.to_dict() for ref in self.evidence_references]
        import json

        canonical = json.dumps(content, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate the provenance chain.

        Returns:
            (is_valid, list_of_errors)
        """
        errors = []

        # Validate source record
        if not self.source_record.source_id:
            errors.append("source_record.source_id is required")
        if not (0.0 <= self.source_record.source_quality_score <= 1.0):
            errors.append("source_quality_score must be between 0.0 and 1.0")

        # Validate processing record
        if self.processing_record.quality_score_after < 0.0:
            errors.append("quality_score_after cannot be negative")

        # Validate schema version
        if not self.schema_version:
            errors.append("schema_version is required")

        return (len(errors) == 0, errors)
