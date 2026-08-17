"""
Result Evidence Emission — connect the existing ExperimentResult contract to the evidence store.

Phase 5.3b.4 — ExperimentResult Evidence Emission only.

This module bridges the existing ``ExperimentResult`` contract (from
``researchos.experiments.result``) to the append-only ``EvidenceRepository`` by
building a scheme-2 ``EvidenceEnvelope`` (``HASH_SCHEME_VERSION = "2"``) of
artifact type ``"Result"``.

Scope (strictly additive):
    - Build a Result evidence artifact from an existing ``ExperimentResult``.
    - Capture result_hash, run_id, run_hash reference, experiment reference,
      metrics, statistics, performance metadata (deterministic fields only),
      result metadata, and backend identity metadata.
    - EXCLUDE timestamps, runtime telemetry, and execution timing from all
      identity fields.
    - Preserve existing ExperimentResult behavior (no mutation).
    - Do NOT emit Validation / Model yet.
    - No execution changes.
    - No model registry.

Design:
    - The envelope payload is a deterministic, primitives-only projection of
      the result's content.  Observational telemetry (execution time,
      execution timestamp) is excluded from every hash.
    - ``build_result_envelope`` returns an immutable ``EvidenceEnvelope``
      whose ``artifact_hash`` is canonical (scheme 2).
    - ``emit_result`` appends the envelope to an ``EvidenceRepository`` and
      records the Run → Result lineage edge (relation ``"produces"``) when a
      run parent hash is supplied.
    - ``attach_run_parent(envelope, run_hash)`` returns a new envelope
      carrying the run artifact hash as a parent (lineage).

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

#: The evidence artifact_type emitted for results.
RESULT_ARTIFACT_TYPE = "Result"

#: Default methodology version for the result evidence surface.
RESULT_EVIDENCE_VERSION = "1.0.0"

#: Canonical lineage relation label for Run → Result.
RUN_TO_RESULT_RELATION = "produces"


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


def result_payload(
    result: Any,
    run_hash: str = "",
    experiment_hash: str = "",
    backend_identity: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a deterministic, primitives-only payload from an ``ExperimentResult``.

    The payload captures the result's CONTENT identity only.  Observational
    telemetry (``backend_execution_time_ms``, ``backend_execution_timestamp``)
    is intentionally excluded so identical logical results always hash
    identically.

    Args:
        result: An ``ExperimentResult`` (or any object exposing the expected
            attributes).
        run_hash: The run's deterministic hash (reference).
        experiment_hash: The experiment's deterministic reference hash.
        backend_identity: Optional backend identity metadata (name, version,
            etc.).

    Returns:
        A primitives-only payload ready for hashing.
    """
    metrics = dict(getattr(result, "metrics", {}) or {})
    statistics = dict(getattr(result, "statistics", {}) or {})
    performance = dict(getattr(result, "performance", {}) or {})
    metadata = dict(getattr(result, "metadata", {}) or {})
    trace = str(getattr(result, "trace", ""))
    ontology_tags = sorted(getattr(result, "ontology_tags", []) or [])

    payload: Dict[str, Any] = {
        "result_hash": str(getattr(result, "result_hash", "")),
        "run_id": str(getattr(result, "run_id", "")),
        "run_hash": run_hash,
        "experiment_hash": experiment_hash,
        "metrics": _to_primitives(metrics),
        "statistics": _to_primitives(statistics),
        "performance": _to_primitives(performance),
        "metadata": _to_primitives(metadata),
        "trace": trace,
        "ontology_tags": ontology_tags,
    }
    if backend_identity is not None:
        payload["backend_identity"] = _to_primitives(dict(backend_identity))
    return payload


def build_result_envelope(
    result: Any,
    run_hash: str = "",
    experiment_hash: str = "",
    backend_identity: Optional[Mapping[str, Any]] = None,
    version: str = RESULT_EVIDENCE_VERSION,
    created_at: str = "",
    parent_hashes: Optional[Sequence[str]] = None,
) -> EvidenceEnvelope:
    """Build a scheme-2 ``EvidenceEnvelope`` for an ``ExperimentResult``.

    The envelope binds ``artifact_type="Result"`` + ``version`` + payload into
    the ``artifact_hash`` (scheme 2), so:

        - identical results (same content) → identical ``artifact_hash``, and
        - a changed metric / statistic / metadata → a different
          ``artifact_hash``.

    Runtime timing / telemetry never affects the hash.

    Args:
        result: An ``ExperimentResult``.
        run_hash: The run's deterministic hash (reference).
        experiment_hash: The experiment's deterministic reference hash.
        backend_identity: Optional backend identity metadata.
        version: Methodology version for the result evidence surface.
        created_at: Observational telemetry (never hashed).
        parent_hashes: Optional input artifact hashes (e.g. the Run hash).

    Returns:
        An immutable ``EvidenceEnvelope`` ready for persistence.
    """
    payload = result_payload(
        result,
        run_hash=run_hash,
        experiment_hash=experiment_hash,
        backend_identity=backend_identity,
    )
    return build_envelope(
        artifact_type=RESULT_ARTIFACT_TYPE,
        payload=payload,
        version=version,
        created_at=created_at,
        parent_hashes=parent_hashes,
    )


def attach_run_parent(
    envelope: EvidenceEnvelope,
    run_hash: str,
) -> EvidenceEnvelope:
    """Return a new Result envelope carrying a run parent (lineage).

    The returned envelope records ``run_hash`` as a parent so the
    EvidenceRepository writes a Run → Result lineage edge (relation
    ``"produces"``) on append.  The original envelope is unchanged
    (immutable).
    """
    parents = list(envelope.parent_hashes)
    if run_hash not in parents:
        parents.append(run_hash)
    return build_envelope(
        artifact_type=RESULT_ARTIFACT_TYPE,
        payload=envelope.payload,
        version=envelope.version,
        created_at=envelope.created_at,
        parent_hashes=parents,
    )


def emit_result(
    envelope: EvidenceEnvelope,
    repository: Optional[EvidenceRepository] = None,
) -> EvidenceEnvelope:
    """Persist a Result envelope to an ``EvidenceRepository`` (append-only).

    Args:
        envelope: A Result ``EvidenceEnvelope`` (from ``build_result_envelope``).
        repository: An ``EvidenceRepository``; defaults to an in-memory one.

    Returns:
        The stored envelope.

    Raises:
        ValueError: If the envelope is not a Result artifact or fails
            verification.
    """
    if envelope.artifact_type != RESULT_ARTIFACT_TYPE:
        raise ValueError(
            f"emit_result() expects artifact_type='Result', got '{envelope.artifact_type}'"
        )
    if not envelope.verify():
        raise ValueError(f"Result evidence lineage mismatch for {envelope.artifact_hash}")
    repo = repository or EvidenceRepository()
    return repo.append_artifact(envelope)


def emit_result_for_run(
    result: Any,
    run_hash: str,
    repository: Optional[EvidenceRepository] = None,
    experiment_hash: str = "",
    backend_identity: Optional[Mapping[str, Any]] = None,
    version: str = RESULT_EVIDENCE_VERSION,
    created_at: str = "",
) -> EvidenceEnvelope:
    """Convenience: build a Result envelope, link it to a Run, and emit.

    This records the Run → Result lineage edge (relation ``"produces"``)
    atomically on append.

    Returns:
        The stored Result envelope.
    """
    base = build_result_envelope(
        result,
        run_hash=run_hash,
        experiment_hash=experiment_hash,
        backend_identity=backend_identity,
        version=version,
        created_at=created_at,
    )
    linked = attach_run_parent(base, run_hash)
    return emit_result(linked, repository)


__all__ = [
    "HASH_SCHEME_VERSION",
    "RESULT_ARTIFACT_TYPE",
    "RESULT_EVIDENCE_VERSION",
    "RUN_TO_RESULT_RELATION",
    "attach_run_parent",
    "build_result_envelope",
    "emit_result",
    "emit_result_for_run",
    "result_payload",
]
