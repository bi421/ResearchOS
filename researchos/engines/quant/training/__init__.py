"""
Model Training Framework (Q13) — deterministic research-model training.

This package provides architecture-only, deterministic model training:
immutable contracts, a deterministic trainer, evaluation metrics, and a
training-result repository.  It does NOT perform machine learning.

Public API (``from researchos.engines.quant.training import *``)::

    ModelContract            immutable trained-model contract
    ModelType                deterministic model families
    TrainingResult           immutable training outcome
    TrainConfig              immutable training configuration
    Trainer                  deterministic trainer
    TrainingRepository       deterministic result repository
    accuracy / precision / recall / f1_score / mae / mse / rmse / ...
    dataset_hash             deterministic dataset fingerprint
    validate_dataset         dataset structural validation
"""

from .contracts import (
    MODEL_CONTRACT_VERSION,
    TRAINING_VERSION,
    InvalidDatasetError,
    InvalidModelError,
    ModelContract,
    ModelType,
    TrainingError,
)
from .metrics import (
    accuracy,
    compute_metrics,
    directional_accuracy,
    f1_score,
    mae,
    mse,
    precision,
    recall,
    rmse,
)
from .repository import (
    TRAINING_REPOSITORY_VERSION,
    DuplicateModelError,
    TrainingRepository,
    TrainingRepositoryError,
    TrainingResultNotFoundError,
)
from .trainer import (
    TrainConfig,
    Trainer,
    dataset_hash,
    validate_dataset,
)
from .training_result import TrainingResult

__all__ = [
    # version constants
    "MODEL_CONTRACT_VERSION",
    "TRAINING_REPOSITORY_VERSION",
    "TRAINING_VERSION",
    # errors
    "TrainingError",
    "InvalidDatasetError",
    "InvalidModelError",
    "TrainingRepositoryError",
    "DuplicateModelError",
    "TrainingResultNotFoundError",
    # contracts
    "ModelContract",
    "ModelType",
    "TrainingResult",
    "TrainConfig",
    "Trainer",
    "TrainingRepository",
    # metrics
    "accuracy",
    "compute_metrics",
    "directional_accuracy",
    "f1_score",
    "mae",
    "mse",
    "precision",
    "recall",
    "rmse",
    # helpers
    "dataset_hash",
    "validate_dataset",
]
