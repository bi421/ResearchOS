"""
Dataset Builder — contracts.

Frozen data structures produced by the Dataset Builder subsystem.

The Dataset Builder is the only component allowed to merge raw OHLCV,
the feature matrix, labels, and metadata into a deterministic
``ResearchDataset``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

DATASET_VERSION = "1.0.0"
BUILDER_VERSION = "1.0.0"


def _freeze(value: Any) -> Any:
    """Recursively convert a metadata value into a hashable form."""
    if isinstance(value, Mapping):
        return tuple(sorted((k, _freeze(v)) for k, v in value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    return value


def _metadata_repr(value: Any) -> Any:
    """Recursively convert a metadata value into a plain dict / primitive."""
    if isinstance(value, Mapping):
        return {k: _metadata_repr(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_metadata_repr(v) for v in value]
    return value


@dataclass(frozen=True)
class ResearchDataset:
    """A deterministic, aligned research dataset.

    Feature row ``features[i]`` corresponds to ``labels[i]``.  Warmup and
    tail rows (containing ``None``) have already been removed, so the final
    dataset contains no ``None`` / NaN values.

    Attributes:
        feature_names: Names of the columns, aligned with each feature row.
        features: Aligned feature matrix (immutable tuples of floats).
        labels: Aligned label vector (immutable tuple).
        metadata: Descriptive metadata (deterministic; no timestamps).
        sample_count: Number of aligned observations.
        feature_count: Number of feature columns.
        label_name: Identifier of the label series.
        created_at: Optional deterministic timestamp (default ``None``).
        version: Dataset version string.
    """

    feature_names: tuple[str, ...]
    features: tuple[tuple[float, ...], ...]
    labels: tuple[float, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)
    sample_count: int = 0
    feature_count: int = 0
    label_name: str = ""
    created_at: str | None = None
    version: str = DATASET_VERSION

    def __post_init__(self) -> None:
        """Freeze the metadata mapping so the dataset is safe to hash."""
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def __hash__(self) -> int:
        return hash(
            (
                self.feature_names,
                self.features,
                self.labels,
                _freeze(self.metadata),
                self.sample_count,
                self.feature_count,
                self.label_name,
                self.created_at,
                self.version,
            )
        )

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> ResearchDataset:
        """Reconstruct a ``ResearchDataset`` from a dataset evidence payload.

        This is the deterministic inverse of the Dataset evidence emission
        projection (``researchos.evidence.dataset_emission.research_dataset_payload``),
        enabling exact reproduction of a dataset from its immutable evidence
        record.  It is strictly additive and never mutates the input payload.

        The payload must be a primitives-only mapping carrying the keys:

            - ``feature_names`` (list of str)
            - ``features`` (list of list of float)
            - ``labels`` (list of float)
            - ``metadata`` (dict)
            - ``sample_count`` (int)
            - ``feature_count`` (int)
            - ``label_name`` (str)
            - ``version`` (str)

        Note: the payload does not carry ``created_at`` (excluded from the
        emission identity), so the reconstructed dataset has ``created_at=None``.

        Args:
            payload: A primitives-only dataset evidence payload.

        Returns:
            A frozen ``ResearchDataset`` reconstructed from the payload.

        Raises:
            ValueError: If the payload is missing required keys or has
                inconsistent feature/label dimensions.
            TypeError: If the payload is not a mapping.
        """
        if not isinstance(payload, Mapping):
            raise TypeError(f"payload must be a mapping, got {type(payload).__name__}")
        required = (
            "feature_names",
            "features",
            "labels",
            "sample_count",
            "feature_count",
            "label_name",
            "version",
        )
        missing = [k for k in required if k not in payload]
        if missing:
            raise ValueError(f"payload missing required key(s): {', '.join(missing)}")

        feature_names = tuple(str(n) for n in payload["feature_names"])
        features = tuple(tuple(float(v) for v in row) for row in payload["features"])
        labels = tuple(float(v) for v in payload["labels"])
        metadata = dict(payload.get("metadata", {}) or {})

        sample_count = int(payload["sample_count"])
        feature_count = int(payload["feature_count"])
        label_name = str(payload["label_name"])
        version = str(payload["version"])

        if sample_count != len(labels):
            raise ValueError(f"payload sample_count={sample_count} does not match len(labels)={len(labels)}")
        if feature_count != len(feature_names):
            raise ValueError(
                f"payload feature_count={feature_count} does not match len(feature_names)={len(feature_names)}"
            )
        if features and any(len(row) != feature_count for row in features):
            row_lengths = {len(row) for row in features}
            raise ValueError(f"payload feature rows have inconsistent widths {row_lengths}, expected {feature_count}")

        return cls(
            feature_names=feature_names,
            features=features,
            labels=labels,
            metadata=metadata,
            sample_count=sample_count,
            feature_count=feature_count,
            label_name=label_name,
            created_at=None,
            version=version,
        )


__all__ = ["BUILDER_VERSION", "DATASET_VERSION", "ResearchDataset"]
