"""
Model Training Framework — immutable contracts.

Deterministic research-model training contracts.  Pure Python, stdlib only.
No ML libraries, no stochastic algorithms, no randomness.

This layer DOES NOT train machine-learning models.  It stores deterministic
research models (rule-based, linear formula, threshold, feature-weight) and
their immutable contracts.
"""

from __future__ import annotations

import enum
import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

TRAINING_VERSION = "1.0.0"
MODEL_CONTRACT_VERSION = "1.0.0"

_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


class TrainingError(Exception):
    """Base class for all training-framework errors."""


class InvalidDatasetError(TrainingError):
    """Raised when a ResearchDataset is malformed or unusable."""


class InvalidModelError(TrainingError):
    """Raised when a model contract violates training-framework rules."""


class ModelType(enum.Enum):
    """Deterministic research model families.

    These are NOT machine-learning algorithms.  They are closed-form,
    deterministic research models computed directly from the dataset.
    """

    RULE_BASED = "rule_based"
    LINEAR_FORMULA = "linear_formula"
    THRESHOLD = "threshold"
    FEATURE_WEIGHT = "feature_weight"

    @classmethod
    def from_value(cls, value: str) -> ModelType:
        """Resolve a ``ModelType`` from its string value."""
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"unknown ModelType value: {value!r}")


def _canonical_json(obj: Any) -> str:
    """Serialize ``obj`` to a deterministic JSON string."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _freeze(value: Any) -> Any:
    """Recursively convert a value into a hashable form."""
    if isinstance(value, Mapping):
        return tuple(sorted((k, _freeze(v)) for k, v in value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    return value


def _as_frozen_mapping(value: Any, error: type) -> MappingProxyType:
    """Normalise a mapping-like value to an immutable ``MappingProxyType``."""
    if isinstance(value, Mapping):
        return MappingProxyType(dict(value))
    raise error(f"expected a mapping, got {type(value).__name__}")


def _validate_model_id(model_id: str) -> None:
    """Ensure a model id is a non-empty valid identifier."""
    if not isinstance(model_id, str) or not model_id:
        raise InvalidModelError("model_id must be a non-empty string")
    if _ID_PATTERN.fullmatch(model_id) is None:
        raise InvalidModelError("model_id may only contain letters, digits, '_', '.', '-' and must not start with a separator")


def _validate_version(version: str) -> None:
    """Ensure a version is a semantic ``major.minor.patch`` string."""
    if not isinstance(version, str) or not version:
        raise InvalidModelError("version must be a non-empty string")
    if _VERSION_PATTERN.fullmatch(version) is None:
        raise InvalidModelError("version must follow the semantic form 'major.minor.patch'")


@dataclass(frozen=True)
class ModelContract:
    """Immutable, hashable contract describing a trained research model.

    Attributes:
        model_id: Stable identifier, e.g. ``"xauusd_direction_v1"``.
        name: Human-readable model name.
        version: Semantic version string ``"major.minor.patch"``.
        model_type: Deterministic research model family.
        feature_names: Ordered tuple of feature column names.
        label_name: Target label column name.
        parameters: Immutable configuration mapping (frozen).
        metadata: Immutable descriptive mapping (frozen).
        created_at: Deterministic creation timestamp string (default ``""``).
        training_hash: Deterministic hash linking to the training dataset.
    """

    model_id: str
    name: str
    version: str
    model_type: ModelType
    feature_names: tuple[str, ...]
    label_name: str
    parameters: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    created_at: str = ""
    training_hash: str = ""

    def __post_init__(self) -> None:
        """Validate identity/version and freeze all container fields."""
        _validate_model_id(self.model_id)
        _validate_version(self.version)
        if not isinstance(self.name, str) or not self.name.strip():
            raise InvalidModelError("name must be a non-empty string")
        if not isinstance(self.model_type, ModelType):
            raise InvalidModelError("model_type must be a ModelType")
        object.__setattr__(self, "feature_names", tuple(self.feature_names))
        for name in self.feature_names:
            if not isinstance(name, str) or not name.strip():
                raise InvalidModelError("feature_names must contain only non-empty strings")
        if not isinstance(self.label_name, str) or not self.label_name.strip():
            raise InvalidModelError("label_name must be a non-empty string")
        object.__setattr__(
            self,
            "parameters",
            _as_frozen_mapping(self.parameters, InvalidModelError),
        )
        object.__setattr__(
            self,
            "metadata",
            _as_frozen_mapping(self.metadata, InvalidModelError),
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.model_id,
                self.name,
                self.version,
                self.model_type.value,
                self.feature_names,
                self.label_name,
                _freeze(self.parameters),
                _freeze(self.metadata),
                self.created_at,
                self.training_hash,
            )
        )

    def content_hash(self) -> str:
        """Deterministic SHA-256 content hash of this contract."""
        payload = {
            "model_id": self.model_id,
            "name": self.name,
            "version": self.version,
            "model_type": self.model_type.value,
            "feature_names": list(self.feature_names),
            "label_name": self.label_name,
            "parameters": dict(self.parameters),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "training_hash": self.training_hash,
        }
        return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic, JSON-compatible dictionary."""
        return {
            "model_id": self.model_id,
            "name": self.name,
            "version": self.version,
            "model_type": self.model_type.value,
            "feature_names": list(self.feature_names),
            "label_name": self.label_name,
            "parameters": dict(self.parameters),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "training_hash": self.training_hash,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ModelContract:
        """Reconstruct a contract from a ``to_dict()`` mapping."""
        return cls(
            model_id=str(data["model_id"]),
            name=str(data["name"]),
            version=str(data["version"]),
            model_type=ModelType.from_value(str(data["model_type"])),
            feature_names=tuple(data.get("feature_names", ())),
            label_name=str(data["label_name"]),
            parameters=dict(data.get("parameters", {})),
            metadata=dict(data.get("metadata", {})),
            created_at=str(data.get("created_at", "")),
            training_hash=str(data.get("training_hash", "")),
        )


__all__ = [
    "MODEL_CONTRACT_VERSION",
    "TRAINING_VERSION",
    "InvalidDatasetError",
    "InvalidModelError",
    "ModelContract",
    "ModelType",
    "TrainingError",
]
