"""Repository layer for ResearchOS — storage and retrieval of objects."""

from researchos.repository.interface import RepositoryInterface
from researchos.repository.memory import MemoryRepository

__all__ = [
    "RepositoryInterface",
    "MemoryRepository",
]
