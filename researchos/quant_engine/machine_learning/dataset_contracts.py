"""
Dataset Builder — contracts.

Frozen data structures produced by the Dataset Builder subsystem.

The Dataset Builder is the only component allowed to merge raw OHLCV,
the feature matrix, labels, and metadata into a deterministic
``ResearchDataset``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional, Tuple

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

    feature_names: Tuple[str, ...]
    features: Tuple[Tuple[float, ...], ...]
    labels: Tuple[float, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)
    sample_count: int = 0
    feature_count: int = 0
    label_name: str = ""
    created_at: Optional[str] = None
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


__all__ = ["BUILDER_VERSION", "DATASET_VERSION", "ResearchDataset"]

