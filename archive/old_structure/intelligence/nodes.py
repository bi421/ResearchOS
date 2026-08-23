"""
Evidence Graph — node contracts.

Defines ``NodeType`` and the immutable ``EvidenceNode``.

An ``EvidenceNode`` records a single research artifact (a dataset, feature
set, label set, model, validation, experiment, or result) referenced from
the surrounding ResearchOS subsystems.  Nodes never contain trading logic,
signals, or executable behavior — they are structured research knowledge.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any

from researchos.intelligence.contracts import EvidenceError


class NodeType(str, Enum):
    """The kind of research artifact an ``EvidenceNode`` references."""

    DATASET = "dataset"
    FEATURE_SET = "feature_set"
    LABEL_SET = "label_set"
    MODEL = "model"
    VALIDATION = "validation"
    EXPERIMENT = "experiment"
    RESULT = "result"

    @classmethod
    def from_string(cls, value: str) -> NodeType:
        """Parse a node type from a string, case-insensitive."""
        mapping = {
            "dataset": cls.DATASET,
            "feature_set": cls.FEATURE_SET,
            "featureset": cls.FEATURE_SET,
            "label_set": cls.LABEL_SET,
            "labelset": cls.LABEL_SET,
            "model": cls.MODEL,
            "validation": cls.VALIDATION,
            "experiment": cls.EXPERIMENT,
            "result": cls.RESULT,
        }
        normalized = str(value).lower().strip()
        if normalized not in mapping:
            raise ValueError(f"Unknown node type {value!r}. Valid options: {[t.value for t in cls]}")
        return mapping[normalized]

    def matches(self, node_type: str) -> bool:
        """Whether this type matches a string type label."""
        return self.value == str(node_type).lower().strip()


def _freeze(value: Any) -> Any:
    """Recursively convert a metadata value into a hashable form."""
    if isinstance(value, Mapping):
        return tuple(sorted((k, _freeze(v)) for k, v in value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    return value


def _as_immutable_mapping(value: Any) -> MappingProxyType:
    """Normalise the metadata field to an immutable mapping."""
    if isinstance(value, Mapping):
        return MappingProxyType(dict(value))
    raise EvidenceError("metadata must be a mapping")


def _validate_identifier(value: Any, field_name: str) -> str:
    """Ensure a required identifier is a non-empty string."""
    if not isinstance(value, str) or not value.strip():
        raise EvidenceError(f"{field_name} must be a non-empty string")
    return value.strip()


@dataclass(frozen=True)
class EvidenceNode:
    """Immutable, hashable, serializable node in the evidence graph.

    Attributes:
        node_id: Unique identifier within an ``EvidenceGraph``.
        node_type: The kind of artifact this node references.
        reference_id: Identifier of the artifact in the source subsystem
            (e.g. a ``ModelContract.model_id``, an ``Experiment`` id, or a
            dataset id).
        metadata: Immutable mapping of descriptive key/value pairs.
        created_at: Deterministic creation timestamp string (default "").
    """

    node_id: str
    node_type: NodeType
    reference_id: str
    metadata: Mapping[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def __post_init__(self) -> None:
        """Validate identifiers and freeze all container fields."""
        object.__setattr__(self, "node_id", _validate_identifier(self.node_id, "node_id"))
        if not isinstance(self.node_type, NodeType):
            raise EvidenceError("node_type must be a NodeType")
        object.__setattr__(self, "reference_id", _validate_identifier(self.reference_id, "reference_id"))
        object.__setattr__(self, "metadata", _as_immutable_mapping(self.metadata))
        object.__setattr__(self, "created_at", str(self.created_at))

    def __hash__(self) -> int:
        return hash(
            (
                self.node_id,
                self.node_type.value,
                self.reference_id,
                _freeze(self.metadata),
                self.created_at,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic, JSON-compatible dictionary."""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "reference_id": self.reference_id,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> EvidenceNode:
        """Reconstruct an ``EvidenceNode`` from a ``to_dict()`` mapping."""
        return cls(
            node_id=str(data["node_id"]),
            node_type=NodeType.from_string(str(data["node_type"])),
            reference_id=str(data["reference_id"]),
            metadata=dict(data.get("metadata", {})),
            created_at=str(data.get("created_at", "")),
        )


__all__ = [
    "NodeType",
    "EvidenceNode",
]
