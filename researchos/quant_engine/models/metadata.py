"""
Model Registry — metadata contract.

Immutable, hashable modelling metadata stored on every ``ModelContract``.
Pure Python, deterministic, no external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Tuple

MODEL_METADATA_VERSION = "1.0.0"


@dataclass(frozen=True)
class ModelMetadata:
    """Immutable, hashable modelling metadata.

    Attributes:
        author: Creating analyst / system identifier.
        description: Free-form description of the model.
        created_at: Deterministic creation timestamp string.
        tags: Ordered tuple of categorical tags.
        framework: ML/statistical framework identifier (string only).
        notes: Additional deterministic notes.
    """

    author: str = ""
    description: str = ""
    created_at: str = ""
    tags: Tuple[str, ...] = ()
    framework: str = ""
    notes: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "tags", tuple(self.tags))

    def to_dict(self) -> Dict[str, Any]:
        """Return a deterministic, JSON-compatible dictionary."""
        return {
            "author": self.author,
            "description": self.description,
            "created_at": self.created_at,
            "tags": list(self.tags),
            "framework": self.framework,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ModelMetadata":
        """Reconstruct a ``ModelMetadata`` from a ``to_dict()`` mapping."""
        return cls(
            author=str(data.get("author", "")),
            description=str(data.get("description", "")),
            created_at=str(data.get("created_at", "")),
            tags=tuple(data.get("tags", ())),
            framework=str(data.get("framework", "")),
            notes=str(data.get("notes", "")),
        )


__all__ = ["MODEL_METADATA_VERSION", "ModelMetadata"]

