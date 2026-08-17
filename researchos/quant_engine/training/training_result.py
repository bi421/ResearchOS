"""
Model Training Framework — training result contract.

Immutable, hashable outcome of a deterministic training run.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Dict, Mapping, Tuple

from .contracts import ModelContract, _freeze


def _as_frozen_mapping(value: Any) -> MappingProxyType:
    return MappingProxyType(dict(value))


@dataclass(frozen=True)
class TrainingResult:
    """Immutable outcome of a deterministic training run.

    Attributes:
        model: The trained ``ModelContract``.
        metrics: Immutable mapping of evaluation metrics.
        dataset_hash: Deterministic hash of the training dataset.
        n_samples: Number of training observations.
        n_features: Number of feature columns.
        predictions: Tuple of in-sample predictions.
        metadata: Immutable descriptive mapping.
    """

    model: ModelContract
    metrics: Mapping[str, float]
    dataset_hash: str
    n_samples: int
    n_features: int
    predictions: Tuple[float, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Freeze all container fields and validate scalars."""
        if not isinstance(self.model, ModelContract):
            raise TypeError("model must be a ModelContract")
        if not isinstance(self.metrics, Mapping):
            raise TypeError("metrics must be a mapping")
        object.__setattr__(self, "metrics", _as_frozen_mapping(self.metrics))
        object.__setattr__(self, "metadata", _as_frozen_mapping(self.metadata))
        object.__setattr__(self, "predictions", tuple(self.predictions))
        if not isinstance(self.dataset_hash, str) or not self.dataset_hash:
            raise ValueError("dataset_hash must be a non-empty string")
        if self.n_samples < 0:
            raise ValueError("n_samples must be non-negative")
        if self.n_features < 0:
            raise ValueError("n_features must be non-negative")

    def __hash__(self) -> int:
        return hash(
            (
                self.model,
                _freeze(self.metrics),
                self.dataset_hash,
                self.n_samples,
                self.n_features,
                self.predictions,
                _freeze(self.metadata),
            )
        )

    def content_hash(self) -> str:
        """Deterministic SHA-256 content hash of this training result."""
        payload = {
            "model": self.model.to_dict(),
            "metrics": dict(self.metrics),
            "dataset_hash": self.dataset_hash,
            "n_samples": self.n_samples,
            "n_features": self.n_features,
            "predictions": list(self.predictions),
            "metadata": dict(self.metadata),
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Return a deterministic, JSON-compatible dictionary."""
        return {
            "model": self.model.to_dict(),
            "metrics": dict(self.metrics),
            "dataset_hash": self.dataset_hash,
            "n_samples": self.n_samples,
            "n_features": self.n_features,
            "predictions": list(self.predictions),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "TrainingResult":
        """Reconstruct a training result from a ``to_dict()`` mapping."""
        return cls(
            model=ModelContract.from_dict(data["model"]),
            metrics=dict(data.get("metrics", {})),
            dataset_hash=str(data["dataset_hash"]),
            n_samples=int(data["n_samples"]),
            n_features=int(data["n_features"]),
            predictions=tuple(data.get("predictions", ())),
            metadata=dict(data.get("metadata", {})),
        )


__all__ = ["TrainingResult"]
