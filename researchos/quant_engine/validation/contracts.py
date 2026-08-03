"""
Walk-Forward Validation — contracts.

Frozen, deterministic data structures produced by the validation layer.
The validation layer is responsible for realistic chronological evaluation
of ``ResearchDataset`` objects while preventing overfitting and future
leakage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Tuple

VALIDATION_VERSION = "1.0.0"


def _freeze(value: Any) -> Any:
    """Recursively convert a mapping/list value into a hashable form."""
    if isinstance(value, Mapping):
        return tuple(sorted((k, _freeze(v)) for k, v in value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    return value


class ValidationError(Exception):
    """Raised when a walk-forward configuration or fold violates the
    leak-free chronological constraints."""


@dataclass(frozen=True)
class FoldResult:
    """Outcome of a single walk-forward fold.

    Attributes:
        fold_id: 1-based chronological fold identifier.
        train_range: Inclusive ``(start, end)`` range of training indices.
        validation_range: Inclusive ``(start, end)`` range of validation indices.
        metrics: Deterministic metric-name -> value mapping for the fold.
        sample_count: Number of validation samples in the fold.
    """

    fold_id: int
    train_range: Tuple[int, int]
    validation_range: Tuple[int, int]
    metrics: Mapping[str, float]
    sample_count: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "metrics", MappingProxyType(dict(self.metrics)))

    def __hash__(self) -> int:
        return hash(
            (
                self.fold_id,
                self.train_range,
                self.validation_range,
                _freeze(self.metrics),
                self.sample_count,
            )
        )

    def to_dict(self) -> dict:
        return {
            "fold_id": int(self.fold_id),
            "train_range": [int(self.train_range[0]), int(self.train_range[1])],
            "validation_range": [
                int(self.validation_range[0]),
                int(self.validation_range[1]),
            ],
            "metrics": dict(self.metrics),
            "sample_count": int(self.sample_count),
        }


@dataclass(frozen=True)
class ValidationResult:
    """Aggregated result of a walk-forward validation run.

    Attributes:
        train_size: Number of samples in each training window.
        validation_size: Number of samples in each validation window.
        test_size: Number of untouched samples after the final validation
            window (truly unseen tail).
        fold_count: Total number of folds evaluated.
        fold_results: Tuple of per-fold ``FoldResult`` objects.
        metrics: Aggregate (mean) metrics across all folds.
        metadata: Deterministic metadata describing the validation run.
    """

    train_size: int
    validation_size: int
    test_size: int
    fold_count: int
    fold_results: Tuple[FoldResult, ...]
    metrics: Mapping[str, float]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metrics", MappingProxyType(dict(self.metrics)))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def __hash__(self) -> int:
        return hash(
            (
                self.train_size,
                self.validation_size,
                self.test_size,
                self.fold_count,
                self.fold_results,
                _freeze(self.metrics),
                _freeze(self.metadata),
            )
        )

    def to_dict(self) -> dict:
        return {
            "train_size": int(self.train_size),
            "validation_size": int(self.validation_size),
            "test_size": int(self.test_size),
            "fold_count": int(self.fold_count),
            "fold_results": [fr.to_dict() for fr in self.fold_results],
            "metrics": dict(self.metrics),
            "metadata": dict(self.metadata),
        }


__all__ = [
    "FoldResult",
    "VALIDATION_VERSION",
    "ValidationError",
    "ValidationResult",
]

