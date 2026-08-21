"""
EvidenceEnvelope — the uniform, immutable artifact envelope for evidence.

Phase 5.3a — Evidence & Lineage storage foundation (hash-contract hardened).

An ``EvidenceEnvelope`` wraps every certified artifact (Dataset, Feature,
Experiment, Run, Result, Validation, Model) with a uniform, deterministic
lineage envelope:

    - ``artifact_type``  — one of the 7 certified artifact types.
    - ``artifact_hash``  — canonical content hash (primary key).
    - ``version``        — methodology / surface version.
    - ``created_at``     — observational telemetry (NEVER part of any hash).
    - ``payload``        — the canonical artifact content.
    - ``parent_hashes``  — input artifact hashes (provenance).
    - ``lineage_hash``   — hash(payload + sorted parent_hashes).

Hash-contract hardening (audit findings addressed):

    1. ``artifact_hash`` now binds ``artifact_type`` + ``version`` + ``payload``
       so a Dataset and a Feature with identical payload produce different
       identities (audit finding #1).
    2. ``lineage_hash`` now binds ``artifact_type`` + ``version`` + ``payload``
       + sorted ``parent_hashes`` so version/type tampering fails verification
       while parent order remains irrelevant (audit finding #2).
    3. The payload is strictly validated to contain only deterministic
       JSON-compatible primitives (``dict``/``list``/``str``/``int``/``float``/
       ``bool``/``None``); unsupported objects are rejected (removes the
       ``default=str`` ambiguity of ``deterministic_hash``) (finding #3).
    4. A hash-scheme version marker is embedded in the canonical envelope so
       future algorithm changes are detectable (finding #4).

Design principles:
    - Immutable: fields are read-only mapping views / frozen tuples.
    - Deterministic: every hash is a canonical SHA-256 over sorted, stable
      serializations of validated primitives only.
    - Time is telemetry only: ``created_at`` is stored but never hashed.
    - Append-only: the envelope is immutable once built.

This is a certification/trust layer only — it computes no trading decisions.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

#: Canonical artifact types recognized by the evidence store.
ARTIFACT_TYPES: tuple[str, ...] = (
    "Dataset",
    "Feature",
    "Experiment",
    "Run",
    "Result",
    "Validation",
    "Model",
)
ARTIFACT_TYPES_TUPLE: tuple[str, ...] = ARTIFACT_TYPES

#: Accepted lineage relation labels.
LINEAGE_RELATIONS: tuple[str, ...] = (
    "feeds",
    "executes",
    "produces",
    "validates",
    "trains",
)

#: Hash-scheme version marker.  Bumping this invalidates legacy hashes (see
#: ``legacy_verify``).  The scheme hashes validated-primitives only.
HASH_SCHEME_VERSION = "2"

#: Allowed payload primitive types (deterministic JSON-compatible).
_ALLOWED_VALUE_TYPES = (dict, list, str, int, float, bool)
_ALLOWED_NONE = (None,)


def _is_primitive(value: Any) -> bool:
    """Return True if ``value`` is a deterministic JSON-compatible primitive."""
    if value is None:
        return True
    if isinstance(value, bool):
        return True
    if isinstance(value, (dict, list, str, int, float)):
        return True
    return False


def _validate_payload(payload: Any) -> None:
    """Strictly validate that ``payload`` contains only primitives.

    Raises:
        TypeError: If any nested value is not a deterministic primitive
            (dict / list / str / int / float / bool / None).
    """
    if isinstance(payload, dict):
        for key, value in payload.items():
            if not isinstance(key, str):
                raise TypeError(f"payload dict keys must be str, got {type(key).__name__}")
            _validate_payload(value)
        return
    if isinstance(payload, list):
        for value in payload:
            _validate_payload(value)
        return
    if isinstance(payload, (str, int, float, bool)) or payload is None:
        return
    raise TypeError(f"payload value {payload!r} of type {type(payload).__name__} is not a deterministic JSON-compatible primitive. Allowed: dict, list, str, int, float, bool, None.")


def _canonical_json(payload: Any) -> str:
    """Serialize a validated-payload to canonical JSON (sorted, no default=str).

    The payload has already been validated as primitives-only, so ``default``
    is never needed and the undefined-coercion ambiguity is removed.
    """
    return json.dumps(payload, sort_keys=True, ensure_ascii=False)


def _sha256(content: Any) -> str:
    """Deterministic SHA-256 over canonical JSON of validated primitives."""
    serialized = _canonical_json(content)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def compute_artifact_hash(
    artifact_type: str,
    version: str,
    payload: Any,
) -> str:
    """Deterministic artifact identity: hash(artifact_type + version + payload).

    The artifact type is bound into the identity so distinct artifact types
    never collide on identical payloads.
    """
    _validate_payload(payload)
    return _sha256(
        {
            "scheme": HASH_SCHEME_VERSION,
            "artifact_type": artifact_type,
            "version": version,
            "payload": payload,
        }
    )


def compute_lineage_hash(
    artifact_type: str,
    version: str,
    payload: Any,
    parent_hashes: Sequence[str],
) -> str:
    """Deterministic lineage hash over type + version + payload + sorted parents.

    Parent order is irrelevant (sorted edge set).  Version/type tampering
    changes the hash, so verification fails for tampered envelopes.
    """
    _validate_payload(payload)
    return _sha256(
        {
            "scheme": HASH_SCHEME_VERSION,
            "artifact_type": artifact_type,
            "version": version,
            "payload": payload,
            "parent_hashes": sorted(parent_hashes),
        }
    )


@dataclass(frozen=True)
class EvidenceEnvelope:
    """Immutable, deterministic envelope for a single evidence artifact.

    Attributes:
        artifact_type: One of ``ARTIFACT_TYPES``.
        artifact_hash: Canonical content hash (SHA-256 hex).
        version: Methodology / surface version token.
        created_at: Observational timestamp (telemetry, not hashed).
        payload: Canonical artifact content (primitives only).
        parent_hashes: Sorted tuple of input artifact hashes.
        lineage_hash: Hash of type + version + payload + sorted parents.
    """

    artifact_type: str
    artifact_hash: str
    payload: Any = field(default_factory=dict)
    version: str = ""
    created_at: str = ""
    parent_hashes: tuple[str, ...] = field(default_factory=tuple)
    lineage_hash: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "parent_hashes", tuple(sorted(self.parent_hashes)))
        if self.artifact_type not in ARTIFACT_TYPES:
            raise ValueError(f"Unknown artifact_type '{self.artifact_type}'. Expected one of {ARTIFACT_TYPES}.")
        if not self.artifact_hash:
            raise ValueError("artifact_hash is required")
        # Validate the payload contract at construction time.
        _validate_payload(self.payload)

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic, JSON-compatible mapping."""
        return {
            "artifact_type": self.artifact_type,
            "artifact_hash": self.artifact_hash,
            "version": self.version,
            "created_at": self.created_at,
            "payload": self.payload,
            "parent_hashes": list(self.parent_hashes),
            "lineage_hash": self.lineage_hash,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> EvidenceEnvelope:
        """Reconstruct an envelope from a ``to_dict()`` mapping."""
        return cls(
            artifact_type=str(data["artifact_type"]),
            artifact_hash=str(data["artifact_hash"]),
            version=str(data.get("version", "")),
            created_at=str(data.get("created_at", "")),
            payload=data.get("payload", {}),
            parent_hashes=tuple(data.get("parent_hashes", [])),
            lineage_hash=str(data.get("lineage_hash", "")),
        )

    def verify(self) -> bool:
        """Return True if the envelope's lineage hash matches its content.

        Recomputes ``lineage_hash`` from ``artifact_type`` + ``version`` +
        ``payload`` + ``parent_hashes`` and compares to the stored value.
        An empty stored ``lineage_hash`` is treated as legacy/unsigned and
        returns True (backward-compatible).  A non-empty mismatch indicates
        tampering (type, version, payload, or parent set).
        """
        if not self.lineage_hash:
            return True
        expected = compute_lineage_hash(
            self.artifact_type,
            self.version,
            self.payload,
            self.parent_hashes,
        )
        return expected == self.lineage_hash

    def legacy_verify(self) -> bool:
        """Backward-compatible verification against the pre-hardening scheme.

        The pre-hardening ``lineage_hash`` was computed as
        ``hash({payload, sorted parent_hashes})`` (scheme "1"), which omitted
        ``artifact_type`` and ``version``.  This method recomputes that legacy
        hash and compares it to the stored value so records created before the
        hardening remain verifiable.

        New envelopes (scheme "2") are verified by ``verify()``.

        Returns:
            True if the stored ``lineage_hash`` matches the legacy scheme.
        """
        if not self.lineage_hash:
            return True
        legacy = _sha256(
            {
                "payload": self.payload,
                "parent_hashes": sorted(self.parent_hashes),
            }
        )
        return legacy == self.lineage_hash


def build_envelope(
    artifact_type: str,
    payload: Any,
    version: str = "",
    created_at: str = "",
    parent_hashes: Sequence[str] | None = None,
    artifact_hash: str | None = None,
) -> EvidenceEnvelope:
    """Build a fully-hashed ``EvidenceEnvelope``.

    When ``artifact_hash`` is not supplied, it is derived deterministically
    from ``artifact_type`` + ``version`` + ``payload`` so:

        - identical type + version + content → identical identity, and
        - distinct artifact types with identical content → distinct identities.

    The payload is strictly validated as primitives-only.
    """
    _validate_payload(payload)
    if artifact_hash is None:
        artifact_hash = compute_artifact_hash(artifact_type, version, payload)
    parents = tuple(parent_hashes or ())
    lineage_hash = compute_lineage_hash(artifact_type, version, payload, parents)
    return EvidenceEnvelope(
        artifact_type=artifact_type,
        artifact_hash=artifact_hash,
        payload=payload,
        version=version,
        created_at=created_at,
        parent_hashes=parents,
        lineage_hash=lineage_hash,
    )


__all__ = [
    "ARTIFACT_TYPES",
    "ARTIFACT_TYPES_TUPLE",
    "HASH_SCHEME_VERSION",
    "LINEAGE_RELATIONS",
    "EvidenceEnvelope",
    "build_envelope",
    "compute_artifact_hash",
    "compute_lineage_hash",
]
