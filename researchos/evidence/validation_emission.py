"""
Validation Evidence Emission — connect the existing ValidationResult contract to the evidence store.

Phase 5.3b.5 — Validation Evidence Emission only.

This module bridges the existing ``ValidationResult`` contract (from
``researchos.quant_engine.validation.contracts``) to the append-only
``EvidenceRepository`` by building a scheme-2 ``EvidenceEnvelope``
(``HASH_SCHEME_VERSION = "2"``) of artifact type ``"Validation"``.

Scope (strictly additive):
    - Build a Validation evidence artifact from an existing ``ValidationResult``.
    - Capture validation identity/hash, validation method/version, linked
      result_hash, linked run_hash (when available), metrics, statistics,
      validation parameters, and evaluation configuration.
    - EXCLUDE timestamps, runtime telemetry, and execution duration from all
      identity fields.
    - Preserve existing ValidationResult behavior (no mutation).
    - Do NOT emit Model yet.
    - No execution changes.
    - No model registry.

Design:
    - The envelope payload is a deterministic, primitives-only projection of
      the validation's content.  Observational telemetry (execution duration,
      created timestamps) is excluded from every hash.
    - ``build_validation_envelope`` returns an immutable ``EvidenceEnvelope``
      whose ``artifact_hash`` is canonical (scheme 2).
    - ``emit_validation`` appends the envelope to an ``EvidenceRepository``
      and records the Result → Validation lineage edge (relation
      ``"validates"``) when a result parent hash is supplied.
    - ``attach_result_parent(envelope, result_hash)`` returns a new envelope
      carrying the result artifact hash as a parent (lineage).

This is a certification/trust layer only — it computes no trading decisions.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Sequence

from researchos.evidence.envelope import (
    HASH_SCHEME_VERSION,
    EvidenceEnvelope,
    build_envelope,
)
from researchos.evidence.repository import EvidenceRepository

#: The evidence artifact_type emitted for validation artifacts.
VALIDATION_ARTIFACT_TYPE = "Validation"

#: Default methodology version for the validation evidence surface.
VALIDATION_EVIDENCE_VERSION = "1.0.0"

#: Canonical lineage relation label for Result → Validation.
RESULT_TO_VALIDATION_RELATION = "validates"


def _to_primitives(value: Any) -> Any:
    """Recursively convert a value to a primitives-only representation.

    Mappings keep str keys; sequences become lists.  Non-primitive leaf values
    are preserved as-is and the envelope's strict payload validation will
    reject them if unsupported.
    """
    if isinstance(value, Mapping):
        return {str(k): _to_primitives(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_primitives(v) for v in value]
    return value


def validation_hash(validation: Any) -> str:
    """Compute a deterministic content hash for a ``ValidationResult``.

    The hash is derived from the validation's canonical ``to_dict()``
    serialization (which excludes any runtime telemetry by construction), so
    identical validations always produce identical identities.
    """
    from researchos.core.identity import deterministic_hash

    data = validation.to_dict()
    return deterministic_hash(_to_primitives(data))


def _fold_statistics(fold_results: Any) -> Dict[str, Any]:
    """Project per-fold results into a statistics mapping (primitives)."""
    folds = [dict(getattr(f, "to_dict", lambda: {})()) for f in (fold_results or ())]
    return {"fold_count": len(folds), "folds": folds}


def validation_payload(
    validation: Any,
    result_hash: str = "",
    run_hash: str = "",
    experiment_hash: str = "",
    method: str = "",
    evaluation_config: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a deterministic, primitives-only payload from a ``ValidationResult``.

    The payload captures the validation's CONTENT identity only.  Observational
    telemetry (timestamps, runtime execution duration) is intentionally
    excluded so identical logical validations always hash identically.

    Args:
        validation: A ``ValidationResult`` (any object exposing the expected
            attributes / ``to_dict()``).
        result_hash: The linked result's deterministic hash (reference).
        run_hash: The linked run's deterministic hash (reference), when
            available.
        experiment_hash: The linked experiment's deterministic reference hash.
        method: The validation method name (e.g. ``"walk_forward"``).
        evaluation_config: Optional evaluation configuration mapping.

    Returns:
        A primitives-only payload ready for hashing.
    """
    vh = str(validation_hash(validation))
    metrics = dict(getattr(validation, "metrics", {}) or {})
    metadata = dict(getattr(validation, "metadata", {}) or {})
    fold_results = getattr(validation, "fold_results", ()) or ()

    # Validation parameters derived from the ValidationResult contract.
    parameters: Dict[str, Any] = {
        "train_size": int(getattr(validation, "train_size", 0)),
        "validation_size": int(getattr(validation, "validation_size", 0)),
        "test_size": int(getattr(validation, "test_size", 0)),
        "fold_count": int(getattr(validation, "fold_count", 0)),
    }

    version = str(
        getattr(validation, "version", "")
        or metadata.get("validation_version", VALIDATION_EVIDENCE_VERSION)
        or VALIDATION_EVIDENCE_VERSION
    )

    payload: Dict[str, Any] = {
        "validation_hash": vh,
        "method": method,
        "version": version,
        "result_hash": result_hash,
        "run_hash": run_hash,
        "experiment_hash": experiment_hash,
        "metrics": _to_primitives(metrics),
        "statistics": _fold_statistics(fold_results),
        "parameters": parameters,
        "metadata": _to_primitives(metadata),
    }
    if evaluation_config is not None:
        payload["evaluation_config"] = _to_primitives(dict(evaluation_config))
    return payload


def build_validation_envelope(
    validation: Any,
    result_hash: str = "",
    run_hash: str = "",
    experiment_hash: str = "",
    method: str = "",
    evaluation_config: Optional[Mapping[str, Any]] = None,
    version: str = VALIDATION_EVIDENCE_VERSION,
    created_at: str = "",
    parent_hashes: Optional[Sequence[str]] = None,
) -> EvidenceEnvelope:
    """Build a scheme-2 ``EvidenceEnvelope`` for a ``ValidationResult``.

    The envelope binds ``artifact_type="Validation"`` + ``version`` + payload
    into the ``artifact_hash`` (scheme 2), so:

        - identical validations (same content) → identical ``artifact_hash``,
          and
        - a changed metric / configuration / parameter → a different
          ``artifact_hash``.

    Runtime timing / telemetry never affects the hash.

    Args:
        validation: A ``ValidationResult``.
        result_hash: The linked result's deterministic hash (reference).
        run_hash: The linked run's deterministic hash (reference), when
            available.
        experiment_hash: The linked experiment's deterministic reference hash.
        method: The validation method name (e.g. ``"walk_forward"``).
        evaluation_config: Optional evaluation configuration mapping.
        version: Methodology version for the validation evidence surface.
        created_at: Observational telemetry (never hashed).
        parent_hashes: Optional input artifact hashes (e.g. the Result hash).

    Returns:
        An immutable ``EvidenceEnvelope`` ready for persistence.
    """
    payload = validation_payload(
        validation,
        result_hash=result_hash,
        run_hash=run_hash,
        experiment_hash=experiment_hash,
        method=method,
        evaluation_config=evaluation_config,
    )
    return build_envelope(
        artifact_type=VALIDATION_ARTIFACT_TYPE,
        payload=payload,
        version=version,
        created_at=created_at,
        parent_hashes=parent_hashes,
    )


def attach_result_parent(
    envelope: EvidenceEnvelope,
    result_hash: str,
) -> EvidenceEnvelope:
    """Return a new Validation envelope carrying a result parent (lineage).

    The returned envelope records ``result_hash`` as a parent so the
    EvidenceRepository writes a Result → Validation lineage edge (relation
    ``"validates"``) on append.  The original envelope is unchanged
    (immutable).
    """
    parents = list(envelope.parent_hashes)
    if result_hash not in parents:
        parents.append(result_hash)
    return build_envelope(
        artifact_type=VALIDATION_ARTIFACT_TYPE,
        payload=envelope.payload,
        version=envelope.version,
        created_at=envelope.created_at,
        parent_hashes=parents,
    )


def emit_validation(
    envelope: EvidenceEnvelope,
    repository: Optional[EvidenceRepository] = None,
) -> EvidenceEnvelope:
    """Persist a Validation envelope to an ``EvidenceRepository`` (append-only).

    Args:
        envelope: A Validation ``EvidenceEnvelope`` (from
            ``build_validation_envelope``).
        repository: An ``EvidenceRepository``; defaults to an in-memory one.

    Returns:
        The stored envelope.

    Raises:
        ValueError: If the envelope is not a Validation artifact, fails
            verification, or contains an invalid payload.
    """
    if envelope.artifact_type != VALIDATION_ARTIFACT_TYPE:
        raise ValueError(
            f"emit_validation() expects artifact_type='Validation', got "
            f"'{envelope.artifact_type}'"
        )
    if not envelope.verify():
        raise ValueError(
            f"Validation evidence lineage mismatch for {envelope.artifact_hash}"
        )
    repo = repository or EvidenceRepository()
    return repo.append_artifact(envelope)


def emit_validation_for_result(
    validation: Any,
    result_hash: str,
    repository: Optional[EvidenceRepository] = None,
    run_hash: str = "",
    experiment_hash: str = "",
    method: str = "",
    evaluation_config: Optional[Mapping[str, Any]] = None,
    version: str = VALIDATION_EVIDENCE_VERSION,
    created_at: str = "",
) -> EvidenceEnvelope:
    """Convenience: build a Validation envelope, link it to a Result, and emit.

    This records the Result → Validation lineage edge (relation
    ``"validates"``) atomically on append.

    Returns:
        The stored Validation envelope.
    """
    base = build_validation_envelope(
        validation,
        result_hash=result_hash,
        run_hash=run_hash,
        experiment_hash=experiment_hash,
        method=method,
        evaluation_config=evaluation_config,
        version=version,
        created_at=created_at,
    )
    linked = attach_result_parent(base, result_hash)
    return emit_validation(linked, repository)


__all__ = [
    "HASH_SCHEME_VERSION",
    "VALIDATION_ARTIFACT_TYPE",
    "VALIDATION_EVIDENCE_VERSION",
    "RESULT_TO_VALIDATION_RELATION",
    "attach_result_parent",
    "build_validation_envelope",
    "emit_validation",
    "emit_validation_for_result",
    "validation_hash",
    "validation_payload",
]

