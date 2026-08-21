"""
Dataset Evidence Emission — connect existing dataset objects to the evidence store.

Phase 5.3b.1 — Dataset Evidence Emission only.

This module bridges the existing frozen ``ResearchDataset`` contract (from
``researchos.quant_engine.machine_learning.dataset_contracts``) to the
append-only ``EvidenceRepository`` by building a scheme-2 ``EvidenceEnvelope``
(``HASH_SCHEME_VERSION = "2"``) of artifact type ``"Dataset"``.

Scope (strictly additive):
    - Build a Dataset evidence artifact from an existing ``ResearchDataset``.
    - Preserve existing dataset behavior (no mutation of the dataset contract).
    - No Experiment / Run / Result emission yet.
    - No model registry.
    - No execution changes.

Design:
    - The envelope payload is a deterministic, primitives-only projection of
      the dataset (feature names, feature matrix, labels, metadata, counts,
      label name, version).  ``created_at`` is telemetry and excluded from
      every hash.
    - ``build_dataset_envelope`` returns an immutable ``EvidenceEnvelope``
      whose ``artifact_hash`` is canonical (type + version + payload, scheme 2).
    - ``emit_dataset`` appends the envelope to an ``EvidenceRepository`` and
      returns the stored envelope.
    - Lineage metadata (parent artifact hashes) is supported when available
      via the ``parent_hashes`` argument.

This is a certification/trust layer only — it computes no trading decisions.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Sequence

from researchos.engines.scenario.envelope import (
    HASH_SCHEME_VERSION,
    EvidenceEnvelope,
    build_envelope,
)
from researchos.engines.scenario.repository import EvidenceRepository

#: The evidence artifact_type emitted for datasets.
DATASET_ARTIFACT_TYPE = "Dataset"

#: Default methodology version for the dataset evidence surface.
DATASET_EVIDENCE_VERSION = "1.0.0"


def _metadata_to_primitives(metadata: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    """Recursively convert dataset metadata to a primitives-only mapping.

    Mappings and sequences are flattened to plain ``dict`` / ``list`` of
    primitives.  Any non-primitive leaf value is preserved as-is and the
    envelope's strict payload validation will reject it (so the caller learns
    of an unsupportable dataset rather than silently coercing it).
    """
    if not metadata:
        return {}
    out: Dict[str, Any] = {}

    def _convert(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {str(k): _convert(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [_convert(v) for v in value]
        return value

    for key, value in metadata.items():
        out[str(key)] = _convert(value)
    return out


def research_dataset_payload(dataset: Any) -> Dict[str, Any]:
    """Build a deterministic, primitives-only payload from a ``ResearchDataset``.

    Uses the frozen ``ResearchDataset`` attributes without mutating them.
    ``created_at`` is intentionally NOT included in the payload (telemetry).

    Raises:
        TypeError: If ``dataset`` does not expose the expected attributes.
    """
    feature_names = list(getattr(dataset, "feature_names", ()))
    features = [list(row) for row in getattr(dataset, "features", ())]
    labels = list(getattr(dataset, "labels", ()))
    metadata = _metadata_to_primitives(getattr(dataset, "metadata", {}))

    return {
        "feature_names": [str(n) for n in feature_names],
        "features": [[float(v) for v in row] for row in features],
        "labels": [float(v) for v in labels],
        "metadata": metadata,
        "sample_count": int(getattr(dataset, "sample_count", len(labels))),
        "feature_count": int(getattr(dataset, "feature_count", len(feature_names))),
        "label_name": str(getattr(dataset, "label_name", "")),
        "version": str(getattr(dataset, "version", "1.0.0")),
    }


def build_dataset_envelope(
    dataset: Any,
    version: str = DATASET_EVIDENCE_VERSION,
    created_at: str = "",
    parent_hashes: Optional[Sequence[str]] = None,
) -> EvidenceEnvelope:
    """Build a scheme-2 ``EvidenceEnvelope`` for a ``ResearchDataset``.

    The envelope binds ``artifact_type="Dataset"`` + ``version`` + ``payload``
    into the ``artifact_hash`` (scheme 2), so:

        - the same dataset always produces the same ``artifact_hash``, and
        - a changed dataset produces a different ``artifact_hash``.

    Args:
        dataset: A ``ResearchDataset`` (or any object exposing the dataset
            attributes used by ``research_dataset_payload``).
        version: Methodology version for the dataset evidence surface.
        created_at: Observational telemetry (never hashed).
        parent_hashes: Optional input artifact hashes (lineage metadata).

    Returns:
        An immutable ``EvidenceEnvelope`` ready for persistence.
    """
    payload = research_dataset_payload(dataset)
    return build_envelope(
        artifact_type=DATASET_ARTIFACT_TYPE,
        payload=payload,
        version=version,
        created_at=created_at,
        parent_hashes=parent_hashes,
    )


def make_dataset_envelope_from_payload(
    payload: Mapping[str, Any],
    version: str = DATASET_EVIDENCE_VERSION,
    created_at: str = "",
    parent_hashes: Optional[Sequence[str]] = None,
) -> EvidenceEnvelope:
    """Build a Dataset envelope directly from a primitives-only payload.

    Useful for callers that already hold a serialized dataset payload.
    """
    return build_envelope(
        artifact_type=DATASET_ARTIFACT_TYPE,
        payload=dict(payload),
        version=version,
        created_at=created_at,
        parent_hashes=parent_hashes,
    )


def emit_dataset(
    envelope: EvidenceEnvelope,
    repository: Optional[EvidenceRepository] = None,
) -> EvidenceEnvelope:
    """Persist a Dataset envelope to an ``EvidenceRepository`` (append-only).

    Args:
        envelope: A Dataset ``EvidenceEnvelope`` (from ``build_dataset_envelope``).
        repository: An ``EvidenceRepository``; defaults to an in-memory one.

    Returns:
        The stored envelope.

    Raises:
        ValueError: If the envelope is not a Dataset artifact or fails verify().
    """
    if envelope.artifact_type != DATASET_ARTIFACT_TYPE:
        raise ValueError(
            f"emit_dataset() expects artifact_type='Dataset', got '{envelope.artifact_type}'"
        )
    if not envelope.verify():
        raise ValueError(f"Dataset evidence lineage mismatch for {envelope.artifact_hash}")
    repo = repository or EvidenceRepository()
    return repo.append_artifact(envelope)


__all__ = [
    "DATASET_ARTIFACT_TYPE",
    "DATASET_EVIDENCE_VERSION",
    "HASH_SCHEME_VERSION",
    "build_dataset_envelope",
    "emit_dataset",
    "make_dataset_envelope_from_payload",
    "research_dataset_payload",
]
