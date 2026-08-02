"""
Repository interface for ResearchOS.

Based on Article XVII: Object Model — all objects are stored and retrieved
through repositories.

The repository interface defines the contract for storing, retrieving,
and querying ResearchOS objects. Implementations can use in-memory
storage, databases, or distributed systems.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar

from researchos.core.base_object import BaseObject

T = TypeVar("T", bound=BaseObject)


class RepositoryInterface(ABC, Generic[T]):
    """
    Abstract base class for all ResearchOS repositories.

    All repositories must implement these methods to provide
    storage and retrieval of ResearchOS objects.
    """

    @abstractmethod
    def save(self, obj: T) -> T:
        """
        Save an object to the repository.

        Args:
            obj: The object to save.

        Returns:
            The saved object.
        """
        pass

    @abstractmethod
    def get(self, id: str) -> Optional[T]:
        """
        Retrieve an object by ID.

        Args:
            id: The object ID.

        Returns:
            The object, or None if not found.
        """
        pass

    @abstractmethod
    def get_all(self) -> List[T]:
        """
        Retrieve all objects from the repository.

        Returns:
            List of all objects.
        """
        pass

    @abstractmethod
    def delete(self, id: str) -> bool:
        """
        Delete an object by ID.

        Args:
            id: The object ID.

        Returns:
            True if the object was deleted, False if not found.
        """
        pass

    @abstractmethod
    def find_by_tag(self, tag: str) -> List[T]:
        """
        Find all objects with a specific ontology tag.

        Args:
            tag: The ontology tag to search for.

        Returns:
            List of matching objects.
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """
        Count the number of objects in the repository.

        Returns:
            The number of objects.
        """
        pass
