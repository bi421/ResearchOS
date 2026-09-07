"""Runtime certification for the Experiment → Run → Result evidence chain.

This module is intentionally a trust-layer adapter.  It does not execute
research or change trading logic.  Given already-computed Experiment, Run and
Result objects, it certifies their immutable evidence envelopes in dependency
order and verifies the resulting lineage chain.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from researchos.evidence.envelope import EvidenceEnvelope
from researchos.evidence.experiment_emission import build_experiment_envelope
from researchos.evidence.repository import EvidenceRepository
from researchos.evidence.result_emission import build_result_envelope
from researchos.evidence.run_emission import build_run_envelope


@dataclass(frozen=True)
class RuntimeCertification:
    """Immutable record of one certified Experiment → Run → Result chain."""

    experiment: EvidenceEnvelope
    run: EvidenceEnvelope
    result: EvidenceEnvelope

    @property
    def experiment_hash(self) -> str:
        return self.experiment.artifact_hash

    @property
    def run_hash(self) -> str:
        return self.run.artifact_hash

    @property
    def result_hash(self) -> str:
        return self.result.artifact_hash

    def verify(self, repository: EvidenceRepository) -> bool:
        """Verify stored artifacts and all expected lineage edges."""
        if not repository.verify_evidence():
            return False
        stored_experiment = repository.get_artifact(self.experiment_hash)
        stored_run = repository.get_artifact(self.run_hash)
        stored_result = repository.get_artifact(self.result_hash)
        if (stored_experiment, stored_run, stored_result) != (
            self.experiment,
            self.run,
            self.result,
        ):
            return False
        if self.run_hash not in repository.get_children(self.experiment_hash):
            return False
        if self.experiment_hash not in repository.get_parents(self.run_hash):
            return False
        if self.result_hash not in repository.get_children(self.run_hash):
            return False
        if self.run_hash not in repository.get_parents(self.result_hash):
            return False
        return True


def certify_runtime(
    experiment: Any,
    run: Any,
    result: Any,
    repository: EvidenceRepository,
    *,
    dataset_hash: str = "",
    backend_identity: Mapping[str, Any] | None = None,
    version: str = "1.0.0",
    created_at: str = "",
) -> RuntimeCertification:
    """Certify an already-computed Experiment → Run → Result chain.

    ``dataset_hash`` is optional because the runner can receive dataset
    contracts whose evidence artifact is not available in the same repository.
    When supplied, the dataset artifact must already exist; this prevents a
    dangling Dataset → Experiment reference.

    The three artifacts are emitted in dependency order.  Existing identical
    artifacts are deduplicated by ``EvidenceRepository`` and are never updated.
    """
    if not isinstance(repository, EvidenceRepository):
        raise TypeError("repository must be an EvidenceRepository")

    if dataset_hash and repository.get_artifact(dataset_hash) is None:
        raise ValueError(f"dataset evidence artifact '{dataset_hash}' does not exist")

    experiment_envelope = build_experiment_envelope(
        experiment,
        version=version,
        created_at=created_at,
        parent_hashes=[dataset_hash] if dataset_hash else None,
    )
    repository.append_artifact(experiment_envelope)

    run_envelope = build_run_envelope(
        run,
        experiment_hash=experiment_envelope.artifact_hash,
        backend_identity=backend_identity,
        version=version,
        created_at=created_at,
        parent_hashes=[experiment_envelope.artifact_hash],
    )
    repository.append_artifact(run_envelope)

    result_envelope = build_result_envelope(
        result,
        run_hash=run_envelope.artifact_hash,
        experiment_hash=experiment_envelope.artifact_hash,
        backend_identity=backend_identity,
        version=version,
        created_at=created_at,
        parent_hashes=[run_envelope.artifact_hash],
    )
    repository.append_artifact(result_envelope)

    certification = RuntimeCertification(
        experiment=experiment_envelope,
        run=run_envelope,
        result=result_envelope,
    )
    if not certification.verify(repository):
        raise RuntimeError("runtime evidence certification verification failed")
    return certification


__all__ = ["RuntimeCertification", "certify_runtime"]
