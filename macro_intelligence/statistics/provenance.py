"""
ResearchOS Macro Intelligence Layer - Statistical Provenance
Version: stat/prov/v1
Status: FROZEN

Defines the provenance envelope attached to every statistical output so that
each result can be traced back to its exact input lineage and the computation
that produced it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def content_hash(content: Any) -> str:
    """
    Deterministic SHA-256 content hash (canonical helper).

    Used to derive persistent identifiers from scientific content so that
    identical inputs produce identical identifiers. This is the single
    canonical hashing helper for the Macro Intelligence Layer.

    Never uses ``hash()``, ``uuid4``, ``random``, or wall-clock time.
    """
    import hashlib
    import json

    canonical = json.dumps(content, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class StatisticalProvenance:
    """
    Immutable provenance envelope for a statistical result.

    Every statistical output can be traced to:
    - the dataset it was computed from (dataset_id / version / hash)
    - the computation method and its version
    - the exact parameters used

    This envelope is metadata only; it does not alter statistical behaviour.
    """

    dataset_id: str | None = None
    dataset_version: str | None = None
    dataset_hash: str | None = None
    computation_method: str = ""
    method_version: str = ""
    parameters: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a dictionary (stable key ordering)."""
        return {
            "dataset_id": self.dataset_id,
            "dataset_version": self.dataset_version,
            "dataset_hash": self.dataset_hash,
            "computation_method": self.computation_method,
            "method_version": self.method_version,
            "parameters": dict(sorted(self.parameters.items())) if self.parameters else {},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StatisticalProvenance:
        """Deserialize from a dictionary."""
        return cls(
            dataset_id=data.get("dataset_id"),
            dataset_version=data.get("dataset_version"),
            dataset_hash=data.get("dataset_hash"),
            computation_method=data.get("computation_method", ""),
            method_version=data.get("method_version", ""),
            parameters=data.get("parameters", {}),
        )

    def to_json(self) -> str:
        """Serialize to JSON with deterministic ordering."""
        import json

        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, json_str: str) -> StatisticalProvenance:
        """Deserialize from JSON."""
        import json

        return cls.from_dict(json.loads(json_str))

    def compute_hash(self) -> str:
        """Compute a deterministic hash over the provenance envelope."""
        import hashlib

        canonical = __import__("json").dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @property
    def method_name(self) -> str:
        """
        Read-only alias for the canonical ``computation_method`` field.

        Exposes the unified provenance vocabulary (``method_name``) without
        duplicating state or altering the serialized field name.
        """
        return self.computation_method
