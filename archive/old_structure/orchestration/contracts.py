"""
Research Orchestration Layer (Q14) — immutable contracts.

The orchestration layer is a PURE COORDINATOR.  It never persists, never
writes to repositories or registries, and never constructs or mutates
graphs.  It wires the locked modules (Dataset Builder, Walk-Forward
Validation, Training Framework) into a single deterministic research
pipeline and returns an immutable, hashable, serializable
``PipelineReport``.

The report carries the produced registry-style ``ModelContract`` plus
evidence node/edge *descriptors* so that downstream layers (Model Registry,
Intelligence Layer) can persist and graph-connect later, on their own.

Design rules:
    - stdlib only; deterministic; no randomness.
    - No persistence, no side effects.
    - No circular imports: this package only consumes public APIs of the
      locked modules and never imports them back.
"""

from __future__ import annotations

import enum
import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from researchos.quant_engine.models.contracts import (  # noqa: E402
    ModelContract as RegistryModelContract,
)
from researchos.quant_engine.training.training_result import (  # noqa: E402
    TrainingResult,
)
from researchos.quant_engine.validation.contracts import (  # noqa: E402
    FoldResult,
    ValidationResult,
)

ORCHESTRATION_VERSION = "1.0.0"


class OrchestrationError(Exception):
    """Base class for all orchestration-layer errors."""


class PipelineStage(str, enum.Enum):
    """The ordered stages of a research pipeline."""

    DATASET = "dataset"
    VALIDATION = "validation"
    TRAINING = "training"
    COMPLETE = "complete"


class PipelineStatus(str, enum.Enum):
    """Lifecycle status of a ``PipelineReport``."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


def _freeze(value: Any) -> Any:
    """Recursively convert mapping/list values into a hashable form."""
    if isinstance(value, Mapping):
        return tuple(sorted((k, _freeze(v)) for k, v in value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    return value


def _as_immutable_mapping(
    value: Any,
    error: type = OrchestrationError,
) -> MappingProxyType:
    """Normalise a mapping-like value to an immutable ``MappingProxyType``."""
    if isinstance(value, Mapping):
        return MappingProxyType(dict(value))
    raise error(f"expected a mapping, got {type(value).__name__}")


def _validate_identifier(
    value: Any,
    name: str,
    error: type = OrchestrationError,
) -> str:
    """Ensure a required identifier is a non-empty string."""
    if not isinstance(value, str) or not value.strip():
        raise error(f"{name} must be a non-empty string")
    return value.strip()


# ---------------------------------------------------------------------------
# evidence descriptors
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EvidenceNodeDescriptor:
    """Immutable node descriptor emitted for the Intelligence Layer.

    The orchestration layer does NOT construct evidence graphs; it only
    emits pure descriptors so the Intelligence Layer can build and own the
    graph later.
    """

    node_id: str
    node_type: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_id", _validate_identifier(self.node_id, "node_id"))
        object.__setattr__(self, "node_type", _validate_identifier(self.node_type, "node_type"))
        object.__setattr__(self, "metadata", _as_immutable_mapping(self.metadata))

    def __hash__(self) -> int:
        return hash((self.node_id, self.node_type, _freeze(self.metadata)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> EvidenceNodeDescriptor:
        return cls(
            node_id=str(data["node_id"]),
            node_type=str(data["node_type"]),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True)
class EvidenceEdgeDescriptor:
    """Immutable edge descriptor emitted for the Intelligence Layer.

    ``relationship`` is a plain descriptive string (e.g. ``uses_dataset``,
    ``validated_by``); the Intelligence Layer maps it onto its own
    ``Relationship`` vocabulary when constructing the graph.
    """

    edge_id: str
    source_id: str
    target_id: str
    relationship: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "edge_id", _validate_identifier(self.edge_id, "edge_id"))
        object.__setattr__(self, "source_id", _validate_identifier(self.source_id, "source_id"))
        object.__setattr__(self, "target_id", _validate_identifier(self.target_id, "target_id"))
        object.__setattr__(
            self,
            "relationship",
            _validate_identifier(self.relationship, "relationship"),
        )
        object.__setattr__(self, "metadata", _as_immutable_mapping(self.metadata))

    def __hash__(self) -> int:
        return hash(
            (
                self.edge_id,
                self.source_id,
                self.target_id,
                self.relationship,
                _freeze(self.metadata),
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relationship": self.relationship,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> EvidenceEdgeDescriptor:
        return cls(
            edge_id=str(data["edge_id"]),
            source_id=str(data["source_id"]),
            target_id=str(data["target_id"]),
            relationship=str(data["relationship"]),
            metadata=dict(data.get("metadata", {})),
        )


# ---------------------------------------------------------------------------
# validation reconstruction helpers (locked ValidationResult has no from_dict)
# ---------------------------------------------------------------------------


def _fold_result_from_dict(data: Mapping[str, Any]) -> FoldResult:
    return FoldResult(
        fold_id=int(data["fold_id"]),
        train_range=(int(data["train_range"][0]), int(data["train_range"][1])),
        validation_range=(
            int(data["validation_range"][0]),
            int(data["validation_range"][1]),
        ),
        metrics=dict(data.get("metrics", {})),
        sample_count=int(data.get("sample_count", 0)),
    )


def _validation_result_from_dict(data: Mapping[str, Any]) -> ValidationResult:
    return ValidationResult(
        train_size=int(data["train_size"]),
        validation_size=int(data["validation_size"]),
        test_size=int(data.get("test_size", 0)),
        fold_count=int(data["fold_count"]),
        fold_results=tuple(_fold_result_from_dict(fr) for fr in data.get("fold_results", [])),
        metrics=dict(data.get("metrics", {})),
        metadata=dict(data.get("metadata", {})),
    )


# ---------------------------------------------------------------------------
# pipeline report
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PipelineReport:
    """Immutable, hashable, serializable outcome of a research pipeline.

    The report aggregates the outputs of every locked stage and carries the
    produced registry-style ``ModelContract`` plus evidence descriptors.
    It is deliberately free of persistence handles: registries, repositories
    and graphs are owned by their respective layers.
    """

    pipeline_id: str
    status: PipelineStatus
    dataset_hash: str
    feature_names: tuple[str, ...]
    label_name: str
    sample_count: int
    feature_count: int
    validation: ValidationResult
    training: TrainingResult
    model_contract: RegistryModelContract
    nodes: tuple[EvidenceNodeDescriptor, ...] = ()
    edges: tuple[EvidenceEdgeDescriptor, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "pipeline_id",
            _validate_identifier(self.pipeline_id, "pipeline_id"),
        )
        if not isinstance(self.status, PipelineStatus):
            raise OrchestrationError("status must be a PipelineStatus")
        if not isinstance(self.dataset_hash, str) or not self.dataset_hash:
            raise OrchestrationError("dataset_hash must be a non-empty string")
        object.__setattr__(self, "feature_names", tuple(self.feature_names))
        if not isinstance(self.label_name, str) or not self.label_name:
            raise OrchestrationError("label_name must be a non-empty string")
        if not isinstance(self.sample_count, int) or self.sample_count < 0:
            raise OrchestrationError("sample_count must be a non-negative integer")
        if not isinstance(self.feature_count, int) or self.feature_count < 0:
            raise OrchestrationError("feature_count must be a non-negative integer")
        if not isinstance(self.validation, ValidationResult):
            raise OrchestrationError("validation must be a ValidationResult")
        if not isinstance(self.training, TrainingResult):
            raise OrchestrationError("training must be a TrainingResult")
        if not isinstance(self.model_contract, RegistryModelContract):
            raise OrchestrationError("model_contract must be a RegistryModelContract")
        object.__setattr__(self, "nodes", tuple(self.nodes))
        object.__setattr__(self, "edges", tuple(self.edges))
        object.__setattr__(self, "metadata", _as_immutable_mapping(self.metadata))
        object.__setattr__(self, "created_at", str(self.created_at))

    def __hash__(self) -> int:
        return hash(
            (
                self.pipeline_id,
                self.status.value,
                self.dataset_hash,
                self.feature_names,
                self.label_name,
                self.sample_count,
                self.feature_count,
                hash(self.validation),
                hash(self.training),
                hash(self.model_contract),
                self.nodes,
                self.edges,
                _freeze(self.metadata),
                self.created_at,
            )
        )

    def content_hash(self) -> str:
        """Deterministic SHA-256 content hash of this pipeline report."""
        payload = {
            "pipeline_id": self.pipeline_id,
            "status": self.status.value,
            "dataset_hash": self.dataset_hash,
            "feature_names": list(self.feature_names),
            "label_name": self.label_name,
            "sample_count": self.sample_count,
            "feature_count": self.feature_count,
            "validation": self.validation.to_dict(),
            "training": self.training.to_dict(),
            "model_contract": self.model_contract.to_dict(),
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic, JSON-compatible dictionary."""
        return {
            "pipeline_id": self.pipeline_id,
            "status": self.status.value,
            "dataset_hash": self.dataset_hash,
            "feature_names": list(self.feature_names),
            "label_name": self.label_name,
            "sample_count": self.sample_count,
            "feature_count": self.feature_count,
            "validation": self.validation.to_dict(),
            "training": self.training.to_dict(),
            "model_contract": self.model_contract.to_dict(),
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PipelineReport:
        """Reconstruct a ``PipelineReport`` from a ``to_dict()`` mapping."""
        return cls(
            pipeline_id=str(data["pipeline_id"]),
            status=PipelineStatus(str(data["status"])),
            dataset_hash=str(data["dataset_hash"]),
            feature_names=tuple(data.get("feature_names", ())),
            label_name=str(data["label_name"]),
            sample_count=int(data["sample_count"]),
            feature_count=int(data["feature_count"]),
            validation=_validation_result_from_dict(data["validation"]),
            training=TrainingResult.from_dict(data["training"]),
            model_contract=RegistryModelContract.from_dict(data["model_contract"]),
            nodes=tuple(EvidenceNodeDescriptor.from_dict(n) for n in data.get("nodes", [])),
            edges=tuple(EvidenceEdgeDescriptor.from_dict(e) for e in data.get("edges", [])),
            metadata=dict(data.get("metadata", {})),
            created_at=str(data.get("created_at", "")),
        )


__all__ = [
    "ORCHESTRATION_VERSION",
    "OrchestrationError",
    "PipelineStage",
    "PipelineStatus",
    "EvidenceNodeDescriptor",
    "EvidenceEdgeDescriptor",
    "PipelineReport",
]
