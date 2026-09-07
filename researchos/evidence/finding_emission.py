"""Research finding evidence emission.

Bridges the existing ``market_memory.EvidenceRecord`` contract into the
append-only evidence graph as a deterministic ``Finding`` artifact.

A finding may only be certified from an existing Validation artifact.  This
keeps the trust boundary explicit:

    Experiment -> Run -> Result -> Validation -> Finding

This module does not compute findings; it only records an already-produced
finding together with its provenance.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from researchos.evidence.envelope import EvidenceEnvelope, build_envelope
from researchos.evidence.repository import EvidenceRepository

FINDING_ARTIFACT_TYPE = "Finding"
FINDING_EVIDENCE_VERSION = "1.0.0"
VALIDATION_TO_FINDING_RELATION = "derives"


def _primitives(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _primitives(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_primitives(item) for item in value]
    return value


def finding_payload(finding: Any) -> dict[str, Any]:
    """Project an EvidenceRecord into a deterministic payload."""
    data = finding.to_dict()
    data.pop("created_at", None)
    return _primitives(data)


def finding_hash(finding: Any) -> str:
    """Return the deterministic content hash of a research finding."""
    from researchos.core.identity import deterministic_hash

    return deterministic_hash(finding_payload(finding))


def build_finding_envelope(
    finding: Any,
    *,
    validation_hash: str,
    version: str = FINDING_EVIDENCE_VERSION,
    created_at: str = "",
) -> EvidenceEnvelope:
    """Build a Finding envelope whose parent is the certified Validation."""
    if not validation_hash:
        raise ValueError("validation_hash is required to certify a finding")
    payload = finding_payload(finding)
    return build_envelope(
        artifact_type=FINDING_ARTIFACT_TYPE,
        payload=payload,
        version=version,
        created_at=created_at,
        parent_hashes=(validation_hash,),
    )


def emit_finding(
    envelope: EvidenceEnvelope,
    repository: EvidenceRepository | None = None,
) -> EvidenceEnvelope:
    """Append a validated Finding envelope to the evidence repository."""
    if envelope.artifact_type != FINDING_ARTIFACT_TYPE:
        raise ValueError(
            f"emit_finding() expects artifact_type='Finding', got '{envelope.artifact_type}'"
        )
    if not envelope.verify():
        raise ValueError(f"Finding evidence lineage mismatch for {envelope.artifact_hash}")
    return (repository or EvidenceRepository()).append_artifact(envelope)


def certify_finding(
    finding: Any,
    validation_hash: str,
    repository: EvidenceRepository,
    *,
    version: str = FINDING_EVIDENCE_VERSION,
    created_at: str = "",
) -> EvidenceEnvelope:
    """Certify an existing research finding against an existing Validation.

    The Validation must already exist in the evidence repository.  This is
    deliberate: a finding can never become durable knowledge without a
    verifiable validation predecessor.
    """
    if repository.get_artifact(validation_hash) is None:
        raise ValueError(f"Validation artifact '{validation_hash}' not found in repository")

    envelope = build_finding_envelope(
        finding,
        validation_hash=validation_hash,
        version=version,
        created_at=created_at,
    )
    return emit_finding(envelope, repository)


__all__ = [
    "FINDING_ARTIFACT_TYPE",
    "FINDING_EVIDENCE_VERSION",
    "VALIDATION_TO_FINDING_RELATION",
    "build_finding_envelope",
    "certify_finding",
    "emit_finding",
    "finding_hash",
    "finding_payload",
]
