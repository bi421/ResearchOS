"""Certification helpers for the Result → Validation evidence boundary.

This module is a trust-layer adapter.  It does not execute validation logic;
it certifies an already-computed ``ValidationResult`` against an existing
Result evidence artifact and verifies the resulting lineage.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from researchos.evidence.envelope import EvidenceEnvelope
from researchos.evidence.repository import EvidenceRepository
from researchos.evidence.validation_emission import (
    build_validation_envelope,
    emit_validation,
    attach_result_parent,
)


@dataclass(frozen=True)
class ValidationCertification:
    """Immutable record of one certified Result → Validation edge."""

    result_hash: str
    validation: EvidenceEnvelope

    @property
    def validation_hash(self) -> str:
        return self.validation.artifact_hash

    def verify(self, repository: EvidenceRepository) -> bool:
        """Verify the stored Validation artifact and Result lineage edge."""
        if not repository.verify_evidence():
            return False
        stored = repository.get_artifact(self.validation_hash)
        if stored != self.validation:
            return False
        if self.validation_hash not in repository.get_children(self.result_hash):
            return False
        if self.result_hash not in repository.get_parents(self.validation_hash):
            return False
        return True


def certify_validation(
    validation: Any,
    result_hash: str,
    repository: EvidenceRepository,
    *,
    run_hash: str = "",
    experiment_hash: str = "",
    method: str = "",
    evaluation_config: Mapping[str, Any] | None = None,
    version: str = "1.0.0",
    created_at: str = "",
) -> ValidationCertification:
    """Certify an already-computed ValidationResult against an existing Result."""
    if not isinstance(repository, EvidenceRepository):
        raise TypeError("repository must be an EvidenceRepository")
    if repository.get_artifact(result_hash) is None:
        raise ValueError(f"result evidence artifact '{result_hash}' does not exist")

    envelope = build_validation_envelope(
        validation,
        result_hash=result_hash,
        run_hash=run_hash,
        experiment_hash=experiment_hash,
        method=method,
        evaluation_config=evaluation_config,
        version=version,
        created_at=created_at,
    )
    linked = attach_result_parent(envelope, result_hash)
    stored = emit_validation(linked, repository)
    certification = ValidationCertification(
        result_hash=result_hash,
        validation=stored,
    )
    if not certification.verify(repository):
        raise RuntimeError("validation evidence certification verification failed")
    return certification


__all__ = ["ValidationCertification", "certify_validation"]
