"""
ResearchOS Macro Intelligence Layer - Knowledge Generation Models

Defines the core data structures for the Knowledge Generation Engine.

The Knowledge Layer is the final interpretation layer inside the Macro
Intelligence Layer. It converts previously computed information (evidence,
features, statistics, relationships, regime intelligence) into structured,
explainable, deterministic knowledge objects.

All models are frozen (immutable) dataclasses.

Architecture invariants:
- MIL-KNOW-001: Knowledge objects are immutable
- MIL-KNOW-002: Every knowledge object preserves complete provenance
- MIL-KNOW-003: Same inputs produce identical knowledge
- MIL-KNOW-004: Knowledge generation is deterministic
- MIL-KNOW-005: Algorithm versions are permanent
- MIL-KNOW-006: Source evidence and features are never mutated
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

# =============================================================================
# Algorithm version
# =============================================================================

ALGORITHM_VERSION = "know-eng/v1.0.0"


# =============================================================================
# Knowledge taxonomy
# =============================================================================


class KnowledgeType(Enum):
    """
    Knowledge classification taxonomy.

    These are knowledge classifications, NOT trading signals.
    Each type describes a deterministic finding about the macro environment.
    """

    REGIME_PERSISTENCE = "regime_persistence"
    REGIME_TRANSITION = "regime_transition"
    PERSISTENT_RELATIONSHIP = "persistent_relationship"
    CORRELATION_BREAK = "correlation_break"
    ANOMALY = "anomaly"
    REGIME_PATTERN = "regime_pattern"
    RISK_OFF_SAFE_HAVEN = "risk_off_safe_haven"
    TIGHTENING_VOLATILITY = "tightening_volatility"


# =============================================================================
# Provenance
# =============================================================================


@dataclass(frozen=True)
class KnowledgeProvenance:
    """
    Full provenance trail for a knowledge object.

    Every knowledge object must answer: "Why does this knowledge exist?"
    Provenance is therefore mandatory.

    References are recorded as stable identifiers (IDs) of the frozen
    upstream outputs that were consumed. The knowledge engine never mutates
    these upstream objects; it only records their identifiers.
    """

    # Upstream evidence references
    evidence_ids: tuple[str, ...] = field(default_factory=tuple)

    # Upstream feature vector references
    feature_vector_ids: tuple[str, ...] = field(default_factory=tuple)

    # Upstream relationship references
    relationship_ids: tuple[str, ...] = field(default_factory=tuple)

    # Upstream regime classification reference
    regime_classification_id: str = ""

    # Upstream regime transition reference
    transition_id: str = ""

    # Algorithm version used to generate this knowledge
    algorithm_version: str = ALGORITHM_VERSION

    # Rules version used to generate this knowledge
    rules_version: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_ids": sorted(self.evidence_ids),
            "feature_vector_ids": sorted(self.feature_vector_ids),
            "relationship_ids": sorted(self.relationship_ids),
            "regime_classification_id": self.regime_classification_id,
            "transition_id": self.transition_id,
            "algorithm_version": self.algorithm_version,
            "rules_version": self.rules_version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KnowledgeProvenance:
        return cls(
            evidence_ids=tuple(sorted(data.get("evidence_ids", []))),
            feature_vector_ids=tuple(sorted(data.get("feature_vector_ids", []))),
            relationship_ids=tuple(sorted(data.get("relationship_ids", []))),
            regime_classification_id=data.get("regime_classification_id", ""),
            transition_id=data.get("transition_id", ""),
            algorithm_version=data.get("algorithm_version", ALGORITHM_VERSION),
            rules_version=data.get("rules_version", ""),
        )

    def to_json(self) -> str:
        import json

        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, json_str: str) -> KnowledgeProvenance:
        import json

        return cls.from_dict(json.loads(json_str))

    def compute_hash(self) -> str:
        """Deterministic hash for provenance."""
        import hashlib
        import json

        hash_data = {
            "evidence_ids": sorted(self.evidence_ids),
            "feature_vector_ids": sorted(self.feature_vector_ids),
            "relationship_ids": sorted(self.relationship_ids),
            "regime_classification_id": self.regime_classification_id,
            "transition_id": self.transition_id,
            "algorithm_version": self.algorithm_version,
            "rules_version": self.rules_version,
        }
        canonical = json.dumps(hash_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def is_complete(self) -> bool:
        """
        Check whether provenance is complete.

        A knowledge object must reference at least one upstream artifact.
        Empty provenance is not allowed for valid knowledge objects.
        """
        return (
            bool(self.evidence_ids)
            or bool(self.feature_vector_ids)
            or bool(self.relationship_ids)
            or bool(self.regime_classification_id)
            or bool(self.transition_id)
        )


# =============================================================================
# Knowledge object
# =============================================================================


@dataclass(frozen=True)
class KnowledgeObject:
    """
    Immutable intelligence artifact.

    Represents: "What does the current macro environment tell us, based on
    validated evidence?"

    Knowledge is:
    - descriptive (not predictive)
    - statistical (derived from frozen statistics)
    - explainable (human-readable statement)
    - provenance-tracked (every artifact referenced)
    - deterministic (same inputs -> same output & hash)

    Hashing rules (MIL-DET-001):
    - Same inputs  -> same knowledge_hash
    - Different evidence -> different knowledge_hash
    - Runtime timestamps (created_timestamp) MUST NOT affect the hash
    """

    # Identity
    knowledge_id: str

    # Classification
    knowledge_type: KnowledgeType

    # Human-readable, explainable statement
    statement: str

    # Quality metrics
    confidence: float

    # Supporting frozen upstream outputs
    supporting_evidence: tuple[str, ...] = field(default_factory=tuple)
    supporting_features: tuple[str, ...] = field(default_factory=tuple)
    supporting_relationships: tuple[str, ...] = field(default_factory=tuple)

    # Regime context (frozen regime classification id)
    regime_context: str = ""

    # Versioning
    algorithm_version: str = ALGORITHM_VERSION

    # Provenance
    provenance: KnowledgeProvenance = field(default_factory=KnowledgeProvenance)

    # Runtime metadata (excluded from hash)
    created_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "knowledge_id": self.knowledge_id,
            "knowledge_type": self.knowledge_type.value,
            "statement": self.statement,
            "confidence": self.confidence,
            "supporting_evidence": sorted(self.supporting_evidence),
            "supporting_features": sorted(self.supporting_features),
            "supporting_relationships": sorted(self.supporting_relationships),
            "regime_context": self.regime_context,
            "algorithm_version": self.algorithm_version,
            "provenance": self.provenance.to_dict(),
            "created_timestamp": self.created_timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KnowledgeObject:
        provenance = KnowledgeProvenance.from_dict(data.get("provenance", {}))
        return cls(
            knowledge_id=data["knowledge_id"],
            knowledge_type=KnowledgeType(data["knowledge_type"]),
            statement=data["statement"],
            confidence=data["confidence"],
            supporting_evidence=tuple(sorted(data.get("supporting_evidence", []))),
            supporting_features=tuple(sorted(data.get("supporting_features", []))),
            supporting_relationships=tuple(sorted(data.get("supporting_relationships", []))),
            regime_context=data.get("regime_context", ""),
            algorithm_version=data.get("algorithm_version", ALGORITHM_VERSION),
            provenance=provenance,
            created_timestamp=datetime.fromisoformat(
                data.get("created_timestamp", datetime.now(timezone.utc).isoformat())
            ),
        )

    def to_json(self) -> str:
        """Serialize to JSON with deterministic ordering."""
        import json

        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, json_str: str) -> KnowledgeObject:
        import json

        return cls.from_dict(json.loads(json_str))

    def compute_hash(self) -> str:
        """
        Compute deterministic hash for the knowledge object.

        MIL-DET-001: Hash depends ONLY on semantic data, never on runtime
        metadata. Therefore `created_timestamp` is EXCLUDED from the hash.

        Different evidence (different provenance) -> different hash.
        """
        import hashlib
        import json

        hash_data = {
            "knowledge_type": self.knowledge_type.value,
            "statement": self.statement,
            "confidence": self.confidence,
            "supporting_evidence": sorted(self.supporting_evidence),
            "supporting_features": sorted(self.supporting_features),
            "supporting_relationships": sorted(self.supporting_relationships),
            "regime_context": self.regime_context,
            "algorithm_version": self.algorithm_version,
            "provenance_hash": self.provenance.compute_hash(),
        }
        canonical = json.dumps(hash_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def validate(self) -> tuple[bool, list[str]]:
        """Validate the knowledge object."""
        errors = []

        if not self.knowledge_id.startswith("KN_"):
            errors.append("knowledge_id must start with 'KN_'")

        if not self.statement:
            errors.append("statement must be non-empty")

        if not (0.0 <= self.confidence <= 1.0):
            errors.append("confidence must be between 0.0 and 1.0")

        if not self.provenance.is_complete():
            errors.append("provenance must reference at least one upstream artifact")

        return (len(errors) == 0, errors)


# =============================================================================
# Macro context aggregation model
# =============================================================================


@dataclass(frozen=True)
class MacroContext:
    """
    Aggregated macro context, composed of deterministic knowledge objects.

    This is a synthesis view: a collection of knowledge artifacts plus the
    regime context they describe. It is NOT a trading decision.
    """

    # Identity
    context_id: str

    # Regime context
    regime_context: str = ""

    # Knowledge objects
    knowledge_objects: tuple[KnowledgeObject, ...] = field(default_factory=tuple)

    # Algorithm version used to build the context
    algorithm_version: str = ALGORITHM_VERSION

    # Runtime metadata (excluded from hash)
    created_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_id": self.context_id,
            "regime_context": self.regime_context,
            "knowledge_count": len(self.knowledge_objects),
            "knowledge_objects": [k.to_dict() for k in self.knowledge_objects],
            "algorithm_version": self.algorithm_version,
            "created_timestamp": self.created_timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MacroContext:
        knowledge = tuple(KnowledgeObject.from_dict(k) for k in data.get("knowledge_objects", []))
        return cls(
            context_id=data["context_id"],
            regime_context=data.get("regime_context", ""),
            knowledge_objects=knowledge,
            algorithm_version=data.get("algorithm_version", ALGORITHM_VERSION),
            created_timestamp=datetime.fromisoformat(
                data.get("created_timestamp", datetime.now(timezone.utc).isoformat())
            ),
        )

    def to_json(self) -> str:
        import json

        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, json_str: str) -> MacroContext:
        import json

        return cls.from_dict(json.loads(json_str))

    def compute_hash(self) -> str:
        """
        Deterministic hash for the macro context.

        Excludes runtime timestamps.
        """
        import hashlib
        import json

        hash_data = {
            "context_id": self.context_id,
            "regime_context": self.regime_context,
            "knowledge_hashes": sorted(k.compute_hash() for k in self.knowledge_objects),
            "algorithm_version": self.algorithm_version,
        }
        canonical = json.dumps(hash_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
