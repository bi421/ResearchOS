"""
Evidence Graph — edge contracts.

Defines ``Relationship`` and the immutable ``EvidenceEdge``.

An ``EvidenceEdge`` connects two ``EvidenceNode`` objects to express how
research artifacts relate (e.g. a model ``USED_BY`` an experiment, or a
validation ``VALIDATED_BY`` an experiment).  Edges are pure structured
knowledge — never executable behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Dict, Mapping

from researchos.intelligence.contracts import EvidenceError


class Relationship(str, Enum):
    """The kind of relationship an ``EvidenceEdge`` represents."""

    USED_BY = "used_by"
    GENERATED_FROM = "generated_from"
    VALIDATED_BY = "validated_by"
    PRODUCED = "produced"
    DEPENDS_ON = "depends_on"

    @classmethod
    def from_string(cls, value: str) -> "Relationship":
        """Parse a relationship from a string, case-insensitive."""
        mapping = {
            "used_by": cls.USED_BY,
            "usedby": cls.USED_BY,
            "generated_from": cls.GENERATED_FROM,
            "generatedfrom": cls.GENERATED_FROM,
            "validated_by": cls.VALIDATED_BY,
            "validatedby": cls.VALIDATED_BY,
            "produced": cls.PRODUCED,
            "depends_on": cls.DEPENDS_ON,
            "dependson": cls.DEPENDS_ON,
        }
        normalized = str(value).lower().strip()
        if normalized not in mapping:
            raise ValueError(
                f"Unknown relationship {value!r}. "
                f"Valid options: {[r.value for r in cls]}"
            )
        return mapping[normalized]

    def matches(self, relationship: str) -> bool:
        """Whether this relationship matches a string label."""
        return self.value == str(relationship).lower().strip()


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
class EvidenceEdge:
    """Immutable, hashable, serializable directed edge.

    Attributes:
        edge_id: Unique identifier within an ``EvidenceGraph``.
        source_id: ``node_id`` of the source node.
        target_id: ``node_id`` of the target node.
        relationship: The relationship this edge expresses.
        metadata: Immutable mapping of descriptive key/value pairs.
        created_at: Deterministic creation timestamp string (default "").
    """

    edge_id: str
    source_id: str
    target_id: str
    relationship: Relationship
    metadata: Mapping[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def __post_init__(self) -> None:
        """Validate identifiers and freeze all container fields."""
        object.__setattr__(self, "edge_id", _validate_identifier(self.edge_id, "edge_id"))
        object.__setattr__(
            self, "source_id", _validate_identifier(self.source_id, "source_id")
        )
        object.__setattr__(
            self, "target_id", _validate_identifier(self.target_id, "target_id")
        )
        if not isinstance(self.relationship, Relationship):
            raise EvidenceError("relationship must be a Relationship")
        object.__setattr__(self, "metadata", _as_immutable_mapping(self.metadata))
        object.__setattr__(self, "created_at", str(self.created_at))

    def __hash__(self) -> int:
        return hash(
            (
                self.edge_id,
                self.source_id,
                self.target_id,
                self.relationship.value,
                _freeze(self.metadata),
                self.created_at,
            )
        )

    def to_dict(self) -> Dict[str, Any]:
        """Return a deterministic, JSON-compatible dictionary."""
        return {
            "edge_id": self.edge_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relationship": self.relationship.value,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "EvidenceEdge":
        """Reconstruct an ``EvidenceEdge`` from a ``to_dict()`` mapping."""
        return cls(
            edge_id=str(data["edge_id"]),
            source_id=str(data["source_id"]),
            target_id=str(data["target_id"]),
            relationship=Relationship.from_string(str(data["relationship"])),
            metadata=dict(data.get("metadata", {})),
            created_at=str(data.get("created_at", "")),
        )


__all__ = [
    "Relationship",
    "EvidenceEdge",
]
