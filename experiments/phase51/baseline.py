"""
Phase 5.1 — unconditional-frequency baseline.

A defensible, simple baseline: predict the class with the highest empirical
frequency observed in the *training* window.  This is the "no-skill" reference
that the Phase 5.1 model must beat out-of-sample, after costs.

Guarantees:
    * Deterministic: same training labels -> same class-frequencies and
      same always-predict class.
    * Uses ONLY the training window (no lookahead).
    * Additive: composes existing ``researchos`` infrastructure.
"""

from __future__ import annotations

from collections.abc import Sequence

from .contracts import BaselineResult


def _class_frequencies(labels: Sequence[float]) -> dict[str, float]:
    """Return per-class frequency of labels in [−1, 0, 1]."""
    counts: dict[str, int] = {"-1": 0, "0": 0, "1": 0}
    for label in labels:
        if label is None:
            continue
        if label == -1:
            counts["-1"] += 1
        elif label == 0:
            counts["0"] += 1
        elif label == 1:
            counts["1"] += 1
    total = sum(counts.values())
    if total == 0:
        return {"-1": 0.0, "0": 0.0, "1": 0.0}
    return {k: v / total for k, v in counts.items()}


def majority_class_from_train(train_labels: Sequence[float]) -> str:
    """Return the most frequent class ('1' / '0' / '-1') in training labels."""
    freqs = _class_frequencies(train_labels)
    # Deterministic tie-break: prefer '1', then '0', then '-1'.
    for cls in ("1", "0", "-1"):
        if freqs[cls] == max(freqs.values()):
            return cls
    return "1"


def baseline_always_predict(
    train_labels: Sequence[float],
    validation_labels: Sequence[float],
) -> int:
    """Predict the training-majority class for every validation sample.

    Returns the integer prediction (1 / 0 / −1) used against validation labels.
    """
    return int(majority_class_from_train(train_labels))


def _accuracy(predictions: Sequence[int], actuals: Sequence[float]) -> float:
    if not actuals:
        return 0.0
    correct = sum(1 for p, a in zip(predictions, actuals) if int(p) == int(a))
    return correct / len(actuals)


def _brier(predictions: Sequence[int], actuals: Sequence[float], nclass: int) -> float:
    """Multi-class Brier score using one-hot targets."""
    if not actuals:
        return 0.0
    total = 0.0
    for p, a in zip(predictions, actuals):
        prob = [0.0] * 3
        prob[int(p) + 1] = 1.0
        target = [0.0] * 3
        target[int(a) + 1] = 1.0
        total += sum((pi - ti) ** 2 for pi, ti in zip(prob, target))
    return total / len(actuals) / nclass


def _precision_recall(
    predictions: Sequence[int],
    actuals: Sequence[float],
    cls: int,
) -> tuple[float, float]:
    tp = sum(1 for p, a in zip(predictions, actuals) if int(p) == cls and int(a) == cls)
    fp = sum(1 for p, a in zip(predictions, actuals) if int(p) == cls and int(a) != cls)
    fn = sum(1 for p, a in zip(predictions, actuals) if int(p) != cls and int(a) == cls)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    return precision, recall


def evaluate_baseline(
    train_labels: Sequence[float],
    validation_labels: Sequence[float],
) -> BaselineResult:
    """Evaluate the unconditional-frequency baseline out-of-sample.

    The baseline is fit on ``train_labels`` only and scored on
    ``validation_labels`` (never seen during fit).
    """
    pred = baseline_always_predict(train_labels, validation_labels)
    predictions = [pred] * len(validation_labels)
    acc = _accuracy(predictions, validation_labels)
    brier = _brier(predictions, validation_labels, 3)
    prec_up, rec_up = _precision_recall(predictions, validation_labels, 1)
    prec_down, rec_down = _precision_recall(predictions, validation_labels, -1)
    freqs = _class_frequencies(train_labels)
    return BaselineResult(
        accuracy=acc,
        precision_up=prec_up,
        precision_down=prec_down,
        recall_up=rec_up,
        recall_down=rec_down,
        brier_score=brier,
        class_frequencies=freqs,
        sample_count=len(validation_labels),
    )


__all__ = [
    "majority_class_from_train",
    "baseline_always_predict",
    "evaluate_baseline",
    "_class_frequencies",
    "_accuracy",
    "_brier",
    "_precision_recall",
]
