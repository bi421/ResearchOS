"""
Model Training Framework — deterministic evaluation metrics.

Pure-Python, stdlib-only metrics.  All functions are deterministic and safe
for empty / degenerate inputs (returning ``0.0`` when undefined).
"""

from __future__ import annotations

import math
from collections.abc import Sequence


def _as_floats(values: Sequence) -> list[float]:
    return [float(v) for v in values]


def _invalid(y_true: list[float], y_pred: list[float]) -> bool:
    return not y_true or len(y_true) != len(y_pred)


def accuracy(y_true: Sequence, y_pred: Sequence) -> float:
    """Fraction of exact matches. ``0.0`` for empty/mismatched input."""
    y_true = _as_floats(y_true)
    y_pred = _as_floats(y_pred)
    if _invalid(y_true, y_pred):
        return 0.0
    return sum(1.0 for t, p in zip(y_true, y_pred) if t == p) / len(y_true)


def precision(y_true: Sequence, y_pred: Sequence, positive: float = 1.0) -> float:
    """``TP / (TP + FP)`` for the binary positive class."""
    y_true = _as_floats(y_true)
    y_pred = _as_floats(y_pred)
    if _invalid(y_true, y_pred):
        return 0.0
    tp = 0.0
    fp = 0.0
    for t, p in zip(y_true, y_pred):
        if p == positive:
            if t == positive:
                tp += 1.0
            else:
                fp += 1.0
    if tp + fp == 0.0:
        return 0.0
    return tp / (tp + fp)


def recall(y_true: Sequence, y_pred: Sequence, positive: float = 1.0) -> float:
    """``TP / (TP + FN)`` for the binary positive class."""
    y_true = _as_floats(y_true)
    y_pred = _as_floats(y_pred)
    if _invalid(y_true, y_pred):
        return 0.0
    tp = 0.0
    fn = 0.0
    for t, p in zip(y_true, y_pred):
        if t == positive:
            if p == positive:
                tp += 1.0
            else:
                fn += 1.0
    if tp + fn == 0.0:
        return 0.0
    return tp / (tp + fn)


def f1_score(y_true: Sequence, y_pred: Sequence, positive: float = 1.0) -> float:
    """Harmonic mean of precision and recall. ``0.0`` if undefined."""
    p = precision(y_true, y_pred, positive)
    r = recall(y_true, y_pred, positive)
    if p + r == 0.0:
        return 0.0
    return 2.0 * p * r / (p + r)


def mae(y_true: Sequence, y_pred: Sequence) -> float:
    """Mean absolute error. ``0.0`` for empty/mismatched input."""
    y_true = _as_floats(y_true)
    y_pred = _as_floats(y_pred)
    if _invalid(y_true, y_pred):
        return 0.0
    return sum(abs(p - t) for t, p in zip(y_true, y_pred)) / len(y_true)


def mse(y_true: Sequence, y_pred: Sequence) -> float:
    """Mean squared error. ``0.0`` for empty/mismatched input."""
    y_true = _as_floats(y_true)
    y_pred = _as_floats(y_pred)
    if _invalid(y_true, y_pred):
        return 0.0
    return sum((p - t) ** 2 for t, p in zip(y_true, y_pred)) / len(y_true)


def rmse(y_true: Sequence, y_pred: Sequence) -> float:
    """Root mean squared error. ``0.0`` for empty/mismatched input."""
    return math.sqrt(mse(y_true, y_pred))


def directional_accuracy(y_true: Sequence, y_pred: Sequence) -> float:
    """Fraction of matching signs (including zero). ``0.0`` if undefined."""
    y_true = _as_floats(y_true)
    y_pred = _as_floats(y_pred)
    if _invalid(y_true, y_pred):
        return 0.0

    def _sign(v: float) -> float:
        if v > 0.0:
            return 1.0
        if v < 0.0:
            return -1.0
        return 0.0

    return sum(1.0 for t, p in zip(y_true, y_pred) if _sign(t) == _sign(p)) / len(y_true)


def compute_metrics(y_true: Sequence, y_pred: Sequence) -> dict:
    """Compute the canonical deterministic metric dictionary."""
    return {
        "accuracy": accuracy(y_true, y_pred),
        "precision": precision(y_true, y_pred),
        "recall": recall(y_true, y_pred),
        "f1_score": f1_score(y_true, y_pred),
        "mae": mae(y_true, y_pred),
        "mse": mse(y_true, y_pred),
        "rmse": rmse(y_true, y_pred),
        "directional_accuracy": directional_accuracy(y_true, y_pred),
    }


__all__ = [
    "accuracy",
    "compute_metrics",
    "directional_accuracy",
    "f1_score",
    "mae",
    "mse",
    "precision",
    "recall",
    "rmse",
]
