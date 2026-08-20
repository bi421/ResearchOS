"""
Model Registry — deterministic, in-memory model lifecycle registry.

The registry stores model identity, metadata, configuration, and validation
history only.  It never trains models, never executes trading, and never
mutates registered contracts.  All operations are deterministic and free of
global state.

Performance:
    register / get / exists / remove / count are O(1) dict operations.
    list_models returns a deterministic tuple ordered by ``model_id``.
"""

from __future__ import annotations

from typing import Dict, Tuple

from .contracts import ModelContract

MODEL_REGISTRY_VERSION = "1.0.0"


class ModelRegistryError(Exception):
    """Base class for all ModelRegistry errors."""


class ModelAlreadyExistsError(ModelRegistryError):
    """Raised when registering a ``model_id`` that already exists."""

    def __init__(self, model_id: str) -> None:
        super().__init__(f"model already registered: {model_id!r}")
        self.model_id = model_id


class ModelNotFoundError(ModelRegistryError):
    """Raised when a requested ``model_id`` is not registered."""

    def __init__(self, model_id: str) -> None:
        super().__init__(f"model not found: {model_id!r}")
        self.model_id = model_id


class ModelRegistry:
    """Deterministic model lifecycle registry.

    The registry is intentionally free of global state: every instance is
    fully independent and safe to construct in tests and experiments.
    """

    def __init__(self) -> None:
        self._models: Dict[str, ModelContract] = {}

    def register(self, model: ModelContract) -> None:
        """Register a model contract.

        Raises:
            TypeError: If ``model`` is not a ``ModelContract``.
            ModelAlreadyExistsError: If ``model.model_id`` is registered.
        """
        if not isinstance(model, ModelContract):
            raise TypeError("register() expects a ModelContract")
        if model.model_id in self._models:
            raise ModelAlreadyExistsError(model.model_id)
        self._models[model.model_id] = model

    def get(self, model_id: str) -> ModelContract:
        """Return the registered contract for ``model_id``.

        Raises:
            ModelNotFoundError: If ``model_id`` is not registered.
        """
        try:
            return self._models[model_id]
        except KeyError:
            raise ModelNotFoundError(model_id) from None

    def list_models(self) -> Tuple[ModelContract, ...]:
        """Return all registered contracts in deterministic order.

        The ordering is stable: contracts are sorted by ``model_id``.
        """
        return tuple(self._models[mid] for mid in sorted(self._models))

    def remove(self, model_id: str) -> None:
        """Remove the contract registered under ``model_id``.

        Raises:
            ModelNotFoundError: If ``model_id`` is not registered.
        """
        if model_id not in self._models:
            raise ModelNotFoundError(model_id)
        del self._models[model_id]

    def clear(self) -> None:
        """Remove all registered contracts."""
        self._models.clear()

    def count(self) -> int:
        """Return the number of registered contracts."""
        return len(self._models)

    def exists(self, model_id: str) -> bool:
        """Return whether ``model_id`` is currently registered."""
        return model_id in self._models

    def to_dict(self) -> dict:
        """Serialize the registry to a JSON-compatible mapping."""
        return {
            "version": MODEL_REGISTRY_VERSION,
            "models": [model.to_dict() for model in self.list_models()],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ModelRegistry":
        """Reconstruct a registry from a ``to_dict()`` mapping."""
        registry = cls()
        for item in data.get("models", []):
            registry.register(ModelContract.from_dict(item))
        return registry


__all__ = [
    "MODEL_REGISTRY_VERSION",
    "ModelAlreadyExistsError",
    "ModelNotFoundError",
    "ModelRegistry",
    "ModelRegistryError",
]
