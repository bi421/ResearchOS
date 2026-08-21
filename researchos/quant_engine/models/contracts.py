"""
Model Registry — immutable model contract.

A ``ModelContract`` stores model identity, metadata, configuration, and
validation history only.  The registry NEVER trains models and NEVER
executes trading.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from .metadata import ModelMetadata

MODEL_CONTRACT_VERSION = "1.0.0"

_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


class ModelContractError(Exception):
    """Raised when a ``ModelContract`` violates registry contract rules."""


def _freeze(value: Any) -> Any:
    """Recursively convert a mapping/list value into a hashable form."""
    if isinstance(value, Mapping):
        return tuple(sorted((k, _freeze(v)) for k, v in value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    return value


def _as_immutable_mapping(value: Any) -> MappingProxyType:
    """Normalise the metadata field to an immutable mapping."""
    if isinstance(value, ModelMetadata):
        value = value.to_dict()
    if isinstance(value, Mapping):
        return MappingProxyType(dict(value))
    raise ModelContractError("metadata must be a mapping or a ModelMetadata")


@dataclass(frozen=True)
class ModelContract:
    """Immutable, hashable, comparable model identity contract.

    Attributes:
        model_id: Stable identifier, e.g. ``"xauusd_direction_v1"``.
        name: Human-readable model name.
        version: Semantic version string ``"major.minor.patch"``.
        algorithm: Algorithm family / class name.
        feature_names: Ordered tuple of feature column names.
        label_name: Target label column name.
        dataset_hash: Deterministic hash linking to the research dataset.
        validation_hash: Deterministic hash linking to the validation result.
        parameters: Immutable configuration mapping.
        created_at: Deterministic creation timestamp string.
        metadata: Immutable mapping (or ``ModelMetadata``) of extra fields.
    """

    model_id: str
    name: str
    version: str
    algorithm: str
    feature_names: tuple[str, ...]
    label_name: str
    dataset_hash: str
    validation_hash: str
    parameters: Mapping[str, Any] = field(default_factory=dict)
    created_at: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate identity/version and freeze all container fields."""
        _validate_model_id(self.model_id)
        _validate_version(self.version)
        if not isinstance(self.name, str) or not self.name.strip():
            raise ModelContractError("name must be a non-empty string")
        if not isinstance(self.algorithm, str) or not self.algorithm.strip():
            raise ModelContractError("algorithm must be a non-empty string")
        object.__setattr__(self, "feature_names", tuple(self.feature_names))
        if not isinstance(self.label_name, str) or not self.label_name.strip():
            raise ModelContractError("label_name must be a non-empty string")
        if not isinstance(self.dataset_hash, str) or not self.dataset_hash.strip():
            raise ModelContractError("dataset_hash must be a non-empty string")
        if not isinstance(self.validation_hash, str) or not self.validation_hash.strip():
            raise ModelContractError("validation_hash must be a non-empty string")
        object.__setattr__(self, "parameters", MappingProxyType(dict(self.parameters)))
        object.__setattr__(self, "metadata", _as_immutable_mapping(self.metadata))

    def __hash__(self) -> int:
        return hash(
            (
                self.model_id,
                self.name,
                self.version,
                self.algorithm,
                self.feature_names,
                self.label_name,
                self.dataset_hash,
                self.validation_hash,
                _freeze(self.parameters),
                self.created_at,
                _freeze(self.metadata),
            )
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic, JSON-compatible dictionary."""
        return {
            "model_id": self.model_id,
            "name": self.name,
            "version": self.version,
            "algorithm": self.algorithm,
            "feature_names": list(self.feature_names),
            "label_name": self.label_name,
            "dataset_hash": self.dataset_hash,
            "validation_hash": self.validation_hash,
            "parameters": dict(self.parameters),
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ModelContract:
        """Reconstruct a ``ModelContract`` from a ``to_dict()`` mapping."""
        return cls(
            model_id=str(data["model_id"]),
            name=str(data["name"]),
            version=str(data["version"]),
            algorithm=str(data["algorithm"]),
            feature_names=tuple(data.get("feature_names", ())),
            label_name=str(data["label_name"]),
            dataset_hash=str(data["dataset_hash"]),
            validation_hash=str(data["validation_hash"]),
            parameters=dict(data.get("parameters", {})),
            created_at=str(data.get("created_at", "")),
            metadata=dict(data.get("metadata", {})),
        )


def _validate_model_id(model_id: str) -> None:
    """Ensure a model id is a non-empty valid identifier."""
    if not isinstance(model_id, str) or not model_id:
        raise ModelContractError("model_id must be a non-empty string")
    if _ID_PATTERN.fullmatch(model_id) is None:
        raise ModelContractError(
            "model_id may only contain letters, digits, '_', '.', '-' and must not start with a separator"
        )


def _validate_version(version: str) -> None:
    """Ensure a version is a semantic ``major.minor.patch`` string."""
    if not isinstance(version, str) or not version:
        raise ModelContractError("version must be a non-empty string")
    if _VERSION_PATTERN.fullmatch(version) is None:
        raise ModelContractError("version must follow the semantic form 'major.minor.patch'")


__all__ = [
    "MODEL_CONTRACT_VERSION",
    "ModelContract",
    "ModelContractError",
]
