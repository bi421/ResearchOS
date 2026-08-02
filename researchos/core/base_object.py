"""
Base object for all ResearchOS entities.

Implements the foundational class that every ResearchOS object inherits from.
Based on Article XVII: Object Model.

All objects are:
    - Deterministic: Same inputs produce same outputs
    - Versioned: All changes are tracked
    - Traceable: Every action is recorded
    - Immutable: Once created, objects are never modified (only superseded)
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from researchos.core.identity import generate_id, deterministic_hash
from researchos.core.lifecycle import Lifecycle, LifecycleStage
from researchos.core.timestamp import utc_now, parse_timestamp


class BaseObject:
    """
    Foundational class for all ResearchOS objects.

    Every object in ResearchOS inherits from this class, which provides:
        - Deterministic identity generation
        - Lifecycle management
        - Immutable state tracking
        - Deterministic hashing for reproducibility
        - Complete audit trail
    """

    def __init__(
        self,
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        ontology_tags: Optional[List[str]] = None,
    ):
        """
        Initialize a ResearchOS object.

        Args:
            id: Deterministic UUID. If None, generated from content.
            created_at: UTC timestamp. If None, set to current time.
            ontology_tags: Ontology concept IDs for this object.
        """
        self.id = id
        self.created_at = created_at or utc_now()
        self.ontology_tags: List[str] = ontology_tags or []
        self.lifecycle = Lifecycle()
        self._hash: Optional[str] = None
        
        if self.id is None:
            tags_str = "|".join(sorted(self.ontology_tags)) if self.ontology_tags else "BaseObject"
            self.id = generate_id(tags_str)

    def compute_hash(self) -> str:
        """
        Compute a deterministic hash of this object's content.

        The hash is computed from all properties except id, created_at,
        and lifecycle (which are metadata, not content).

        Returns:
            Deterministic SHA-256 hash string.
        """
        content = self._to_hashable_dict()
        return deterministic_hash(content)

    def _to_hashable_dict(self) -> Dict[str, Any]:
        """
        Convert object to a hashable dictionary.

        Subclasses should override this to include their specific properties.
        """
        return {
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert object to a dictionary representation.

        This is the canonical serialization format for all ResearchOS objects.
        """
        return {
            "object_type": self.__class__.__name__,
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "ontology_tags": self.ontology_tags,
            "lifecycle": self.lifecycle.to_dict(),
            "hash": self.compute_hash(),
        }

    def to_json(self) -> str:
        """Serialize object to JSON string with sorted keys (deterministic)."""
        return json.dumps(self.to_dict(), indent=2, sort_keys=True, default=str)

    @classmethod
    def from_dict(cls, data: dict) -> "BaseObject":
        """
        Restore an object from saved state.

        Uses cls.__new__() instead of cls() to avoid __init__() side effects
        (timestamps, lifecycle, etc.). Subclasses must call super().from_dict()
        then restore their own fields directly.
        """
        obj = cls.__new__(cls)
        obj.id = data.get("id")
        obj.created_at = parse_timestamp(data["created_at"]) if data.get("created_at") else utc_now()
        obj.ontology_tags = data.get("ontology_tags", [])
        obj.lifecycle = Lifecycle.from_dict(data.get("lifecycle", {"transitions": []}))
        obj._hash = None
        return obj

    @property
    def hash(self) -> str:
        """Get the deterministic hash of this object."""
        if self._hash is None:
            self._hash = self.compute_hash()
        return self._hash

    def __eq__(self, other: object) -> bool:
        """Two objects are equal if they have the same hash."""
        if not isinstance(other, BaseObject):
            return False
        return self.hash == other.hash

    def __hash__(self) -> int:
        """Hash based on the object's deterministic ID."""
        return hash(self.id)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id[:8]}...)"
