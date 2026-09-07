"""Deterministic Knowledge Memory retrieval with provenance traversal.

This layer reads certified Knowledge Memory and follows its Finding
source references upstream through the immutable evidence graph. It does not
infer, rank semantically, embed, or mutate knowledge.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from researchos.evidence.repository import EvidenceRepository
from researchos.objects.knowledge import Knowledge
from researchos.storage.repository import ResearchRepository

FINDING_ARTIFACT_TYPE = "Finding"
VALIDATED_STATUS = "VALIDATED"


@dataclass(frozen=True)
class KnowledgeQuery:
    """Exact deterministic filters for Knowledge Memory."""

    subject: str | None = None
    predicate: str | None = None
    object: str | None = None
    type: str | None = None
    min_confidence: float | None = None

    def __post_init__(self) -> None:
        if self.min_confidence is not None and not 0.0 <= self.min_confidence <= 1.0:
            raise ValueError("min_confidence must be between 0.0 and 1.0")

    def matches(self, knowledge: Knowledge) -> bool:
        return all(
            (
                self.subject is None or knowledge.subject == self.subject,
                self.predicate is None or knowledge.predicate == self.predicate,
                self.object is None or knowledge.object == self.object,
                self.type is None or knowledge.type == self.type,
                self.min_confidence is None
                or knowledge.confidence >= self.min_confidence,
            )
        )


@dataclass(frozen=True)
class ProvenanceNode:
    """One evidence artifact reached while traversing Knowledge provenance."""

    artifact_hash: str
    artifact_type: str
    depth: int


@dataclass(frozen=True)
class KnowledgeRetrievalResult:
    """Knowledge plus its complete upstream evidence provenance."""

    knowledge: Knowledge
    provenance: tuple[ProvenanceNode, ...]


class KnowledgeRetrieval:
    """Read-only query and provenance traversal facade for Knowledge Memory."""

    def __init__(
        self,
        research_repository: ResearchRepository,
        evidence_repository: EvidenceRepository,
    ) -> None:
        self._research = research_repository
        self._evidence = evidence_repository

    def query(self, query: KnowledgeQuery | None = None) -> list[Knowledge]:
        """Return only Knowledge records with validated Finding provenance.

        Results are sorted by stable semantic fields and ID. No repository
        state is modified and no semantic ranking is performed.
        """
        query = query or KnowledgeQuery()
        records: list[Knowledge] = []
        for data in self._research.load_by_type("Knowledge"):
            knowledge = Knowledge.from_dict(data)
            if query.matches(knowledge) and self._has_validated_provenance(knowledge):
                records.append(knowledge)
        return sorted(
            records,
            key=lambda item: (
                item.subject,
                item.predicate,
                item.object,
                item.type,
                item.id,
            ),
        )

    def retrieve(self, query: KnowledgeQuery | None = None) -> list[KnowledgeRetrievalResult]:
        """Query Knowledge and attach deterministic upstream provenance."""
        return [
            KnowledgeRetrievalResult(
                knowledge=knowledge,
                provenance=self.traverse(knowledge.id),
            )
            for knowledge in self.query(query)
        ]

    def traverse(self, knowledge_id: str) -> tuple[ProvenanceNode, ...]:
        """Traverse all Knowledge source references upstream to root evidence.

        Traversal follows Finding ``parent_hashes`` recursively. Each artifact
        is visited once, and siblings are processed in lexicographic hash order
        so the result is stable across runs. A path-local ancestor set detects
        real cycles without rejecting valid converging DAG paths.
        """
        data = self._research.load_by_id(knowledge_id)
        if data is None or data.get("object_type") != "Knowledge":
            raise ValueError(f"Knowledge not found: {knowledge_id}")
        knowledge = Knowledge.from_dict(data)
        if not self._has_validated_provenance(knowledge):
            raise ValueError(
                f"Knowledge {knowledge_id} has no validated Finding provenance"
            )

        queue: deque[tuple[str, int, frozenset[str]]] = deque(
            (finding_hash, 0, frozenset())
            for finding_hash in sorted(set(knowledge.source_references))
        )
        visited: set[str] = set()
        result: list[ProvenanceNode] = []

        while queue:
            artifact_hash, depth, ancestors = queue.popleft()
            if artifact_hash in ancestors:
                raise ValueError(
                    f"Cycle detected in provenance traversal at {artifact_hash}"
                )
            if artifact_hash in visited:
                continue
            visited.add(artifact_hash)
            artifact = self._evidence.get_artifact(artifact_hash)
            if artifact is None:
                raise ValueError(
                    f"Knowledge {knowledge_id} references missing evidence {artifact_hash}"
                )
            result.append(
                ProvenanceNode(
                    artifact_hash=artifact.artifact_hash,
                    artifact_type=artifact.artifact_type,
                    depth=depth,
                )
            )
            next_ancestors = ancestors | {artifact_hash}
            for parent_hash in sorted(set(artifact.parent_hashes)):
                queue.append((parent_hash, depth + 1, next_ancestors))

        return tuple(result)

    def _has_validated_provenance(self, knowledge: Knowledge) -> bool:
        if not knowledge.source_references:
            return False
        for finding_hash in sorted(set(knowledge.source_references)):
            finding = self._evidence.get_artifact(finding_hash)
            if finding is None:
                return False
            if finding.artifact_type != FINDING_ARTIFACT_TYPE:
                return False
            if finding.payload.get("status") != VALIDATED_STATUS:
                return False
        return True


__all__ = [
    "KnowledgeQuery",
    "KnowledgeRetrieval",
    "KnowledgeRetrievalResult",
    "ProvenanceNode",
]
