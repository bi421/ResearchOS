"""
Model Training Framework — deterministic training repository.

The repository stores ``TrainingResult`` objects (which embed trained
``ModelContract`` models).  It never trains models and never mutates stored
results.  All operations are deterministic and free of global state.
"""

from __future__ import annotations

from typing import Dict, Tuple

from .contracts import ModelContract
from .training_result import TrainingResult

TRAINING_REPOSITORY_VERSION = "1.0.0"


class TrainingRepositoryError(Exception):
    """Base class for all training repository errors."""


class DuplicateModelError(TrainingRepositoryError):
    """Raised when saving a model_id that already exists."""

    def __init__(self, model_id: str) -> None:
        super().__init__(f"model already stored: {model_id!r}")
        self.model_id = model_id


class TrainingResultNotFoundError(TrainingRepositoryError):
    """Raised when a requested model_id is not stored."""

    def __init__(self, model_id: str) -> None:
        super().__init__(f"model not found: {model_id!r}")
        self.model_id = model_id


class TrainingRepository:
    """Deterministic, in-memory store of ``TrainingResult`` objects.

    Every instance is fully independent (no global state).  ``list_results``
    returns results ordered deterministically by ``model_id``.
    """

    def __init__(self) -> None:
        self._results: Dict[str, TrainingResult] = {}

    def save(self, result: TrainingResult) -> None:
        """Store a training result.

        Raises:
            TypeError: If ``result`` is not a ``TrainingResult``.
            DuplicateModelError: If the model_id is already stored.
        """
        if not isinstance(result, TrainingResult):
            raise TypeError("save() expects a TrainingResult")
        model_id = result.model.model_id
        if model_id in self._results:
            raise DuplicateModelError(model_id)
        self._results[model_id] = result

    def get(self, model_id: str) -> TrainingResult:
        """Return the stored training result for ``model_id``.

        Raises:
            TrainingResultNotFoundError: If ``model_id`` is not stored.
        """
        try:
            return self._results[model_id]
        except KeyError:
            raise TrainingResultNotFoundError(model_id) from None

    def get_model(self, model_id: str) -> ModelContract:
        """Return the trained model contract stored under ``model_id``."""
        return self.get(model_id).model

    def list_results(self) -> Tuple[TrainingResult, ...]:
        """Return all stored results in deterministic (sorted) order."""
        return tuple(self._results[mid] for mid in sorted(self._results))

    def remove(self, model_id: str) -> None:
        """Remove the stored result under ``model_id``.

        Raises:
            TrainingResultNotFoundError: If ``model_id`` is not stored.
        """
        if model_id not in self._results:
            raise TrainingResultNotFoundError(model_id)
        del self._results[model_id]

    def clear(self) -> None:
        """Remove all stored results."""
        self._results.clear()

    def count(self) -> int:
        """Return the number of stored results."""
        return len(self._results)

    def exists(self, model_id: str) -> bool:
        """Return whether ``model_id`` is currently stored."""
        return model_id in self._results

    def to_dict(self) -> dict:
        """Serialize the repository to a JSON-compatible mapping."""
        return {
            "version": TRAINING_REPOSITORY_VERSION,
            "results": [r.to_dict() for r in self.list_results()],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TrainingRepository":
        """Reconstruct a repository from a ``to_dict()`` mapping."""
        repository = cls()
        for item in data.get("results", []):
            repository.save(TrainingResult.from_dict(item))
        return repository


__all__ = [
    "TRAINING_REPOSITORY_VERSION",
    "DuplicateModelError",
    "TrainingRepository",
    "TrainingRepositoryError",
    "TrainingResultNotFoundError",
]

