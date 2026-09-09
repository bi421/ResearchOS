"""Runtime certification for the Experiment -> Run -> Result evidence chain.

This module is a trust-layer adapter. It does not execute research or change
trading logic. Given already-computed Experiment, Run and Result objects, it
certifies immutable evidence envelopes in dependency order and verifies the
resulting lineage chain.
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


_SYNTHETIC_SOURCES = frozenset({"synthetic", "demo", "mock", "fixture", "test"})


def _dataset_metadata(experiment: Any) -> Mapping[str, Any]:
    dataset_config = getattr(experiment, "dataset_config", None)
    if dataset_config is None:
        return {}
    to_dict = getattr(dataset_config, "to_dict", None)
    if callable(to_dict):
        value = to_dict()
        return value if isinstance(value, Mapping) else {}
    return {}


def _is_synthetic_experiment(experiment: Any) -> bool:
    """Return whether an experiment is explicitly backed by synthetic data."""
    dataset_config = getattr(experiment, "dataset_config", None)
    source = getattr(dataset_config, "source", "") if dataset_config is not None else ""
    metadata = _dataset_metadata(experiment)
    if not source:
        source = metadata.get("source", "")
    if isinstance(source, str) and source.strip().lower() in _SYNTHETIC_SOURCES:
        return True

    parameters = getattr(dataset_config, "parameters", {}) if dataset_config is not None else {}
    if not isinstance(parameters, Mapping):
        parameters = metadata.get("parameters", {})
    if isinstance(parameters, Mapping):
        classification = parameters.get("data_classification", "")
        if isinstance(classification, str) and classification.strip().lower() == "synthetic":
            return True
    classification = metadata.get("data_classification", "")
    return isinstance(classification, str) and classification.strip().lower() == "synthetic"


def _assert_evidence_eligible(experiment: Any) -> None:
    """Reject synthetic/demo/mock/fixture inputs at certification boundary."""
    if _is_synthetic_experiment(experiment):
        raise ValueError(
            "Synthetic, demo, mock, fixture, and test datasets cannot be certified "
            "as research evidence; use a validated real-market dataset."
        )


@dataclass(frozen=True)
class RuntimeCertification:
    """Immutable record of one certified Experiment -> Run -> Result chain."""

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
        stored = tuple(repository.get_artifact(h) for h in (self.experiment_hash, self.run_hash, self.result_hash))
        if stored != (self.experiment, self.run, self.result):
            return False
        return (
            self.run_hash in repository.get_children(self.experiment_hash)
            and self.experiment_hash in repository.get_parents(self.run_hash)
            and self.result_hash in repository.get_children(self.run_hash)
            and self.run_hash in repository.get_parents(self.result_hash)
        )


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
    """Certify an already-computed Experiment -> Run -> Result chain."""
    if not isinstance(repository, EvidenceRepository):
        raise TypeError("repository must be an EvidenceRepository")
    _assert_evidence_eligible(experiment)

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

    certification = RuntimeCertification(experiment_envelope, run_envelope, result_envelope)
    if not certification.verify(repository):
        raise RuntimeError("runtime evidence certification verification failed")
    return certification


__all__ = ["RuntimeCertification", "certify_runtime"]
