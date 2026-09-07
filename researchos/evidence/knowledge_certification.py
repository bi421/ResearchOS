"""Validated Finding -> Knowledge Memory certification boundary.

This module is a trust boundary, not a knowledge generator. It permits an
existing ``Knowledge`` object to enter the durable ResearchRepository only
when its upstream Finding is a certified, VALIDATED evidence artifact.

The semantic fields of ``Knowledge`` remain caller-owned; this layer only
binds provenance by adding the Finding hash to ``source_references``.
"""

from __future__ import annotations

from dataclasses import dataclass

from researchos.evidence.repository import EvidenceRepository
from researchos.objects.knowledge import Knowledge
from researchos.storage.repository import ResearchRepository

FINDING_ARTIFACT_TYPE = "Finding"
KNOWLEDGE_ARTIFACT_TYPE = "Knowledge"
VALIDATED_STATUS = "VALIDATED"


@dataclass(frozen=True)
class KnowledgeCertification:
    """Durable Knowledge object certified from a validated Finding."""

    finding_hash: str
    knowledge: Knowledge

    @property
    def knowledge_id(self) -> str:
        return self.knowledge.id

    def verify(
        self,
        evidence_repository: EvidenceRepository,
        research_repository: ResearchRepository,
    ) -> bool:
        """Verify the upstream Finding and persisted Knowledge provenance."""
        finding = evidence_repository.get_artifact(self.finding_hash)
        if finding is None:
            return False
        if finding.artifact_type != FINDING_ARTIFACT_TYPE:
            return False
        if finding.payload.get("status") != VALIDATED_STATUS:
            return False
        stored = research_repository.load_by_id(self.knowledge.id)
        if stored is None:
            return False
        return self.finding_hash in stored.get("source_references", [])


def certify_knowledge(
    finding_hash: str,
    knowledge: Knowledge,
    evidence_repository: EvidenceRepository,
    research_repository: ResearchRepository,
) -> KnowledgeCertification:
    """Promote a validated Finding into durable Knowledge Memory.

    No semantic transformation or inference is performed here. The supplied
    Knowledge fields are preserved and the certified Finding hash is bound to
    ``source_references`` before persistence.
    """
    finding = evidence_repository.get_artifact(finding_hash)
    if finding is None:
        raise ValueError(f"Finding artifact not found: {finding_hash}")
    if finding.artifact_type != FINDING_ARTIFACT_TYPE:
        raise ValueError(
            f"Knowledge source must be a Finding artifact, got {finding.artifact_type!r}"
        )
    if finding.payload.get("status") != VALIDATED_STATUS:
        raise ValueError("Only VALIDATED findings may enter Knowledge Memory")

    source_references = list(knowledge.source_references)
    if finding_hash not in source_references:
        source_references.append(finding_hash)

    bound_knowledge = Knowledge(
        type=knowledge.type,
        subject=knowledge.subject,
        predicate=knowledge.predicate,
        object=knowledge.object,
        confidence=knowledge.confidence,
        evidence_count=max(knowledge.evidence_count, len(source_references)),
        source_references=source_references,
        knowledge_trace=knowledge.knowledge_trace,
        ontology_tags=list(knowledge.ontology_tags),
        id=knowledge.id,
    )
    research_repository.save_object(bound_knowledge)

    certification = KnowledgeCertification(
        finding_hash=finding_hash,
        knowledge=bound_knowledge,
    )
    if not certification.verify(evidence_repository, research_repository):
        raise RuntimeError("Knowledge certification failed after persistence")
    return certification
