"""Experiment learning persistence boundary.

This module persists an ``ExperimentLearningRecord`` only when its upstream
Finding is already certified and VALIDATED.  It deliberately does not create
or certify Knowledge: durable semantic memory remains governed by
``knowledge_certification.certify_knowledge`` and the Finding evidence gate.

Boundary:
    Validation -> Finding -> ExperimentLearningRecord
                              \\-> Knowledge
"""

from __future__ import annotations

from dataclasses import dataclass

from researchos.evidence.repository import EvidenceRepository
from researchos.experiments.learning import ExperimentLearningRecord
from researchos.storage.repository import ResearchRepository

FINDING_ARTIFACT_TYPE = "Finding"
VALIDATED_STATUS = "VALIDATED"


@dataclass(frozen=True)
class ExperimentLearningCertification:
    """Persisted experiment learning bound to a validated Finding."""

    finding_hash: str
    learning: ExperimentLearningRecord

    @property
    def learning_id(self) -> str:
        return self.learning.id

    def verify(
        self,
        evidence_repository: EvidenceRepository,
        research_repository: ResearchRepository,
    ) -> bool:
        """Verify Finding provenance and the persisted learning record."""
        finding = evidence_repository.get_artifact(self.finding_hash)
        if finding is None or finding.artifact_type != FINDING_ARTIFACT_TYPE:
            return False
        if finding.payload.get("status") != VALIDATED_STATUS:
            return False
        stored = research_repository.load_by_id(self.learning.id)
        if stored is None:
            return False
        return (
            stored.get("object_type") == "ExperimentLearningRecord"
            and stored.get("validation_id") == self.learning.validation_id
            and stored.get("experiment_id") == self.learning.experiment_id
            and stored.get("hypothesis_id") == self.learning.hypothesis_id
        )


def _semantic_payload(learning: ExperimentLearningRecord) -> dict:
    """Return the stable learning representation used for immutability checks."""
    return learning._to_hashable_dict()


def certify_experiment_learning(
    learning: ExperimentLearningRecord,
    finding_hash: str,
    evidence_repository: EvidenceRepository,
    research_repository: ResearchRepository,
) -> ExperimentLearningCertification:
    """Persist learning only when its upstream Finding is VALIDATED.

    The learning record is stored as a normal research object. It is not an
    evidence artifact and it cannot bypass the Finding -> Knowledge gate.

    Once a Learning ID has been certified, an identical certification is
    idempotent while a changed semantic payload is rejected rather than
    overwriting durable research memory.
    """
    finding = evidence_repository.get_artifact(finding_hash)
    if finding is None:
        raise ValueError(f"Finding artifact not found: {finding_hash}")
    if finding.artifact_type != FINDING_ARTIFACT_TYPE:
        raise ValueError(
            f"Experiment learning source must be a Finding artifact, got {finding.artifact_type!r}"
        )
    if finding.payload.get("status") != VALIDATED_STATUS:
        raise ValueError("Only VALIDATED findings may certify experiment learning")
    if learning.validation_id != finding.payload.get("validation_id", learning.validation_id):
        # Findings created by older producers may not expose validation_id in
        # their payload. In that case the evidence graph remains authoritative.
        raise ValueError("Experiment learning validation_id does not match Finding provenance")

    existing = research_repository.load_by_id(learning.id)
    if existing is not None:
        if existing.get("object_type") != "ExperimentLearningRecord":
            raise ValueError(
                f"Experiment learning ID collision with {existing.get('object_type')!r}: {learning.id}"
            )
        existing_learning = ExperimentLearningRecord.from_dict(existing)
        if _semantic_payload(existing_learning) != _semantic_payload(learning):
            raise ValueError(
                "Certified ExperimentLearningRecord is immutable: existing semantic payload "
                "does not match the requested certification"
            )
        learning = existing_learning
    else:
        research_repository.save_object(learning)

    certification = ExperimentLearningCertification(
        finding_hash=finding_hash,
        learning=learning,
    )
    if not certification.verify(evidence_repository, research_repository):
        raise RuntimeError("Experiment learning certification failed after persistence")
    return certification


__all__ = ["ExperimentLearningCertification", "certify_experiment_learning"]
