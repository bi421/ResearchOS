"""
ResearchOS Macro Intelligence Layer - Evidence Linking

The EvidenceLinker connects a KnowledgeObject to the frozen upstream
outputs it was derived from:

    KnowledgeObject
        -> EvidenceObject
        -> FeatureVector
        -> RelationshipResult
        -> RegimeClassification

Every knowledge object must answer: "Why does this knowledge exist?"
Therefore provenance is mandatory.

The linker only records stable identifiers and consumed metadata. It never
mutates the upstream objects (MIL-KNOW-006).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from macro_intelligence.knowledge.models import (
    ALGORITHM_VERSION,
    KnowledgeProvenance,
    KnowledgeObject,
)


@dataclass(frozen=True)
class EvidenceLink:
    """
    A single provenance link binding a knowledge object to upstream artifacts.

    Records the stable identifiers of every frozen upstream output that
    contributed to the knowledge object.
    """

    knowledge_id: str
    evidence_ids: tuple[str, ...] = field(default_factory=tuple)
    feature_vector_ids: tuple[str, ...] = field(default_factory=tuple)
    relationship_ids: tuple[str, ...] = field(default_factory=tuple)
    regime_classification_id: str = ""
    transition_id: str = ""
    algorithm_version: str = ALGORITHM_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "knowledge_id": self.knowledge_id,
            "evidence_ids": sorted(self.evidence_ids),
            "feature_vector_ids": sorted(self.feature_vector_ids),
            "relationship_ids": sorted(self.relationship_ids),
            "regime_classification_id": self.regime_classification_id,
            "transition_id": self.transition_id,
            "algorithm_version": self.algorithm_version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvidenceLink:
        return cls(
            knowledge_id=data["knowledge_id"],
            evidence_ids=tuple(sorted(data.get("evidence_ids", []))),
            feature_vector_ids=tuple(sorted(data.get("feature_vector_ids", []))),
            relationship_ids=tuple(sorted(data.get("relationship_ids", []))),
            regime_classification_id=data.get("regime_classification_id", ""),
            transition_id=data.get("transition_id", ""),
            algorithm_version=data.get("algorithm_version", ALGORITHM_VERSION),
        )

    def compute_hash(self) -> str:
        import hashlib
        import json
        hash_data = {
            "knowledge_id": self.knowledge_id,
            "evidence_ids": sorted(self.evidence_ids),
            "feature_vector_ids": sorted(self.feature_vector_ids),
            "relationship_ids": sorted(self.relationship_ids),
            "regime_classification_id": self.regime_classification_id,
            "transition_id": self.transition_id,
            "algorithm_version": self.algorithm_version,
        }
        canonical = json.dumps(hash_data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


class EvidenceLinker:
    """
    Builds provenance links connecting knowledge objects to upstream outputs.

    Stateless, deterministic, pure. It never mutates upstream objects.
    """

    def __init__(self) -> None:
        self._version = ALGORITHM_VERSION

    @property
    def version(self) -> str:
        return self._version

    def build_link(
        self,
        knowledge: KnowledgeObject,
        evidence_ids: list[str] | None = None,
        feature_vector_ids: list[str] | None = None,
        relationship_ids: list[str] | None = None,
        regime_classification_id: str = "",
        transition_id: str = "",
    ) -> EvidenceLink:
        """
        Build a provenance link for a knowledge object.

        Args:
            knowledge: The knowledge object being linked.
            evidence_ids: Stable IDs of contributing EvidenceObjects.
            feature_vector_ids: Stable IDs of contributing FeatureVectors.
            relationship_ids: Stable IDs of contributing RelationshipResults.
            regime_classification_id: RegimeClassification ID.
            transition_id: RegimeTransition ID.

        Returns:
            EvidenceLink with the full provenance record.
        """
        return EvidenceLink(
            knowledge_id=knowledge.knowledge_id,
            evidence_ids=tuple(sorted(evidence_ids or [])),
            feature_vector_ids=tuple(sorted(feature_vector_ids or [])),
            relationship_ids=tuple(sorted(relationship_ids or [])),
            regime_classification_id=regime_classification_id,
            transition_id=transition_id,
        )

    def build_provenance(
        self,
        evidence_ids: list[str] | None = None,
        feature_vector_ids: list[str] | None = None,
        relationship_ids: list[str] | None = None,
        regime_classification_id: str = "",
        transition_id: str = "",
        rules_version: str = "",
    ) -> KnowledgeProvenance:
        """
        Build a KnowledgeProvenance for a knowledge object.

        Returns:
            KnowledgeProvenance with the full provenance trail.
        """
        return KnowledgeProvenance(
            evidence_ids=tuple(sorted(evidence_ids or [])),
            feature_vector_ids=tuple(sorted(feature_vector_ids or [])),
            relationship_ids=tuple(sorted(relationship_ids or [])),
            regime_classification_id=regime_classification_id,
            transition_id=transition_id,
            rules_version=rules_version,
        )

    def resolve_provenance(self, knowledge: KnowledgeObject) -> KnowledgeProvenance:
        """
        Resolve the provenance of an existing knowledge object.

        Returns:
            The knowledge object's provenance.
        """
        return knowledge.provenance
