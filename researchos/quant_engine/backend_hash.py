"""
Backend result hashing — canonical, deterministic digests for certification.

Phase 4.1: backend certification and trust-boundary hardening.

``compute_backend_result_hash`` produces a SHA-256 digest over a canonical
serialization of a backend execution:

    - ``operation``: the operation name (e.g. ``"calculate_returns"``).
    - ``backend``: the backend identifier that produced the output.
    - ``version``: the backend version.
    - ``input_hash``: hash of the operation inputs (provenance).
    - ``output``: the (canonicalized) backend output.

Canonical serialization guarantees that identical logical values produce
identical digests regardless of container ordering.  Stable float formatting
guarantees the digest does not drift for identical float values.

This is a certification/trust layer only — it computes nothing and makes no
trading or prediction decisions.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Dict, Mapping

HASH_ALGORITHM = "sha256"
HASH_VERSION = "1.0.0"


def stable_float(value: float) -> str:
    """Format a float with a stable, canonical representation.

    ``repr`` produces the shortest decimal string that round-trips to the
    same IEEE-754 value, so identical floats always format identically.
    Non-finite values are encoded explicitly and deterministically.
    """
    if math.isnan(value):
        return "NaN"
    if math.isinf(value):
        return "Infinity" if value > 0 else "-Infinity"
    if value == 0.0:
        return "0.0"
    return repr(value)


def canonicalize(value: Any) -> Any:
    """Recursively produce a canonical, JSON-compatible representation.

    - dict keys are sorted
    - lists/tuples become lists
    - floats become stable strings (via ``stable_float``)
    - ints/bools/strings/None pass through
    - objects exposing ``to_dict()`` are reduced to their canonical dict
    """
    if isinstance(value, Mapping):
        return {str(k): canonicalize(v) for k, v in sorted(value.items(), key=str)}
    if isinstance(value, (list, tuple)):
        return [canonicalize(v) for v in value]
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return stable_float(value)
    if value is None or isinstance(value, str):
        return value
    if hasattr(value, "to_dict"):
        data = value.to_dict()
        if isinstance(data, dict):
            # Observational / derived fields are never part of a result hash.
            # Including them (e.g. ``SimulationResult.execution_timestamp`` /
            # ``result_hash``) would make identical executions hash differently.
            data = dict(data)
            data.pop("execution_timestamp", None)
            data.pop("result_hash", None)
        return canonicalize(data)
    return str(value)


def compute_input_hash(inputs: Any) -> str:
    """Deterministic SHA-256 digest of an operation's input payload."""
    payload = canonicalize({"inputs": inputs})
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()


def compute_backend_result_hash(
    operation: str,
    backend: str,
    version: str,
    input_hash: str,
    output: Any,
) -> str:
    """Compute the canonical SHA-256 digest of a backend execution.

    Args:
        operation: Operation name, e.g. ``"calculate_returns"``.
        backend: Backend identifier that produced ``output``.
        version: Backend version string.
        input_hash: Digest of the operation inputs (see ``compute_input_hash``).
        output: The backend output (any JSON-serializable / canonicalizable
            value).

    Returns:
        Hexadecimal SHA-256 digest string (64 chars).
    """
    content = {
        "hash_version": HASH_VERSION,
        "operation": str(operation),
        "backend": str(backend),
        "version": str(version),
        "input_hash": str(input_hash),
        "output": canonicalize(output),
    }
    serialized = json.dumps(content, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def canonical_dict(value: Any) -> Dict[str, Any]:
    """Return a canonical JSON-compatible dict of any value."""
    return {"canonical": canonicalize(value)}


__all__ = [
    "HASH_ALGORITHM",
    "HASH_VERSION",
    "canonicalize",
    "compute_backend_result_hash",
    "compute_input_hash",
    "stable_float",
]
