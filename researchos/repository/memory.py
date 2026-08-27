"""
In-memory repository for ResearchOS.

Based on Article XVII: Object Model — Repository layer.

This is a simple in-memory implementation of the RepositoryInterface.
It is suitable for testing and development. Production deployments
should use a database-backed implementation.
"""

from __future__ import annotations

from typing import TypeVar

from researchos.core.base_object import BaseObject
from researchos.repository.interface import RepositoryInterface

T = TypeVar("T", bound=BaseObject)


class MemoryRepository(RepositoryInterface[T]):
    """
    In-memory repository for ResearchOS objects.

    Stores objects in a dictionary keyed by ID. This implementation
    is not persistent and is intended for testing and development.
    """

    def __init__(self):
        self._store: dict[str, T] = {}

    def save(self, obj: T) -> T:
        """Save an object to the repository."""
        self._store[obj.id] = obj
        return obj

    def get(self, id: str) -> T | None:
        """Retrieve an object by ID."""
        return self._store.get(id)

    def get_all(self) -> list[T]:
        """Retrieve all objects."""
        return list(self._store.values())

    def delete(self, id: str) -> bool:
        """Delete an object by ID."""
        if id in self._store:
            del self._store[id]
            return True
        return False

    def find_by_tag(self, tag: str) -> list[T]:
        """Find all objects with a specific ontology tag."""
        return [obj for obj in self._store.values() if tag in obj.ontology_tags]

    def count(self) -> int:
        """Count the number of objects."""
        return len(self._store)

    def clear(self) -> None:
        """Clear all objects from the repository."""
        self._store.clear()
