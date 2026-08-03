"""
Walk-Forward Validation Engine — Q9.

Deterministic, chronological validation of ``ResearchDataset`` objects with
leakage protection and serializable reports.
"""

from .contracts import (
    FoldResult,
    VALIDATION_VERSION,
    ValidationError,
    ValidationResult,
)
from .metrics import (
    accuracy,
    compute_metrics,
    directional_accuracy,
    f1_score,
    mae,
    mean_error,
    precision,
    recall,
)
from .splitter import Fold, WalkForwardSplitter
from .walk_forward import WalkForwardValidator

__all__ = [
    "Fold",
    "FoldResult",
    "VALIDATION_VERSION",
    "ValidationError",
    "ValidationResult",
    "WalkForwardSplitter",
    "WalkForwardValidator",
    "accuracy",
    "compute_metrics",
    "directional_accuracy",
    "f1_score",
    "mae",
    "mean_error",
    "precision",
    "recall",
]

