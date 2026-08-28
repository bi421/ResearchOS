"""
Purged K-Fold Cross-Validation and Walk-Forward with Embargo.

Implements:
    - Purged K-Fold: removes training samples within a gap (purge) of the validation set
    - Embargo: removes a buffer period after each validation fold
    - Expanding window walk-forward: train on all past, test on future
    - Combinatorial purged K-Fold for multiple test sets
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Fold:
    fold_id: int
    train_indices: np.ndarray
    test_indices: np.ndarray
    train_start: int
    train_end: int
    test_start: int
    test_end: int


def purged_k_fold(
    n_samples: int,
    n_splits: int = 5,
    purge_gap: int = 0,
    embargo_gap: int = 0,
    rng: np.random.Generator | None = None,
) -> list[Fold]:
    """Purged K-Fold with embargo.

    Args:
        n_samples: Total number of samples.
        n_splits: Number of folds.
        purge_gap: Number of samples to remove from training set before test set.
        embargo_gap: Number of samples to remove from training set after test set.
        rng: Random number generator.

    Returns:
        List of Fold objects with purged train/test indices.
    """
    if rng is None:
        rng = np.random.default_rng(42)

    indices = np.arange(n_samples)
    fold_size = n_samples // n_splits
    folds = []

    for fold_id in range(n_splits):
        test_start = fold_id * fold_size
        test_end = n_samples if fold_id == n_splits - 1 else (fold_id + 1) * fold_size
        test_indices = indices[test_start:test_end]

        purge_start = max(0, test_start - purge_gap)
        embargo_end = min(n_samples, test_end + embargo_gap)

        train_mask = np.ones(n_samples, dtype=bool)
        train_mask[purge_start:embargo_end] = False
        train_mask[test_start:test_end] = False
        train_indices = indices[train_mask]

        folds.append(
            Fold(
                fold_id=fold_id,
                train_indices=train_indices,
                test_indices=test_indices,
                train_start=train_indices[0] if len(train_indices) > 0 else 0,
                train_end=train_indices[-1] if len(train_indices) > 0 else 0,
                test_start=test_start,
                test_end=test_end - 1,
            )
        )

    return folds


def expanding_window_folds(
    n_samples: int,
    initial_train_size: int,
    test_size: int,
    step_size: int | None = None,
) -> list[Fold]:
    """Expanding window walk-forward folds.

    Each fold trains on all data up to train_end, tests on [test_start, test_end].
    Training window expands by step_size each iteration.
    """
    if step_size is None:
        step_size = test_size

    folds = []
    fold_id = 0
    train_end = initial_train_size - 1
    test_start = initial_train_size
    test_end = test_start + test_size - 1

    while test_end < n_samples:
        train_indices = np.arange(0, train_end + 1)
        test_indices = np.arange(test_start, test_end + 1)
        folds.append(
            Fold(
                fold_id=fold_id,
                train_indices=train_indices,
                test_indices=test_indices,
                train_start=0,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
            )
        )
        fold_id += 1
        train_end += step_size
        test_start = train_end + 1
        test_end = test_start + test_size - 1

    return folds


def walk_forward_with_embargo(
    n_samples: int,
    train_size: int,
    test_size: int,
    embargo_size: int = 0,
    step_size: int | None = None,
) -> list[Fold]:
    """Walk-forward with embargo period between train and test."""
    if step_size is None:
        step_size = test_size

    folds = []
    fold_id = 0
    train_end = train_size - 1
    test_start = train_end + 1 + embargo_size
    test_end = test_start + test_size - 1

    while test_end < n_samples:
        train_indices = np.arange(0, train_end + 1)
        test_indices = np.arange(test_start, test_end + 1)
        folds.append(
            Fold(
                fold_id=fold_id,
                train_indices=train_indices,
                test_indices=test_indices,
                train_start=0,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
            )
        )
        fold_id += 1
        train_end += step_size
        test_start = train_end + 1 + embargo_size
        test_end = test_start + test_size - 1

    return folds


@dataclass
class CVResult:
    fold_id: int
    train_indices: np.ndarray
    test_indices: np.ndarray
    train_metrics: dict[str, float]
    test_metrics: dict[str, float]
    predictions: np.ndarray | None = None
    uncertainties: np.ndarray | None = None


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    """Compute regression metrics."""
    mse = float(np.mean((y_pred - y_true) ** 2))
    mae = float(np.mean(np.abs(y_pred - y_true)))
    rmse = math.sqrt(mse)
    direction_acc = float(np.mean((y_pred > 0) == (y_true > 0)))
    sharpe = 0.0
    if len(y_true) > 1:
        returns = y_pred
        if returns.std() > 1e-9:
            sharpe = math.sqrt(252) * (returns.mean() / returns.std())
    return {
        "mse": mse,
        "mae": mae,
        "rmse": rmse,
        "directional_accuracy": direction_acc,
        "sharpe_ratio": sharpe,
        "mean_prediction": float(np.mean(y_pred)),
        "std_prediction": float(np.std(y_pred)),
    }


def compute_classification_metrics(y_true: np.ndarray, y_pred_proba: np.ndarray, threshold: float = 0.5) -> dict[str, float]:
    """Compute classification metrics."""
    y_pred = (y_pred_proba > threshold).astype(int)
    accuracy = float(np.mean(y_pred == y_true))
    if len(np.unique(y_true)) > 1:
        from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score

        precision = float(precision_score(y_true, y_pred, zero_division=0))
        recall = float(recall_score(y_true, y_pred, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, zero_division=0))
        auc = float(roc_auc_score(y_true, y_pred_proba))
    else:
        precision = recall = f1 = auc = 0.0
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "auc": auc,
    }


def compute_classification_metrics_numpy(y_true: np.ndarray, y_pred_proba: np.ndarray, threshold: float = 0.5) -> dict[str, float]:
    """Compute classification metrics using only numpy."""
    y_pred = (y_pred_proba > threshold).astype(int)
    tp = np.sum((y_pred == 1) & (y_true == 1))
    fp = np.sum((y_pred == 1) & (y_true == 0))
    fn = np.sum((y_pred == 0) & (y_true == 1))
    tn = np.sum((y_pred == 0) & (y_true == 0))

    accuracy = float((tp + tn) / max(len(y_true), 1))
    precision = float(tp / max(tp + fp, 1))
    recall = float(tp / max(tp + fn, 1))
    f1 = float(2 * precision * recall / max(precision + recall, 1e-9))

    # AUC approximation
    if len(np.unique(y_true)) > 1:
        sorted_idx = np.argsort(y_pred_proba)
        y_true_sorted = y_true[sorted_idx]
        n_pos = np.sum(y_true == 1)
        n_neg = np.sum(y_true == 0)
        if n_pos > 0 and n_neg > 0:
            rank_sum = np.sum(np.arange(1, len(y_true_sorted) + 1) * y_true_sorted)
            auc = float((rank_sum - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))
        else:
            auc = 0.0
    else:
        auc = 0.0

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "auc": auc,
    }


__all__ = [
    "Fold",
    "CVResult",
    "purged_k_fold",
    "expanding_window_folds",
    "walk_forward_with_embargo",
    "compute_metrics",
    "compute_classification_metrics",
    "compute_classification_metrics_numpy",
]
