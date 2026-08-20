"""
Phase 5.1 — probability calibration assessment.

Evaluates whether the model's predicted probabilities are well-calibrated.
Reuses ``researchos.quant_engine.probability.statistics.probability_calibration``
(verified existing infrastructure) for the reliability/recalibration table,
and computes a multi-class Brier score for the model and the baseline.

Guarantees:
    * Deterministic.
    * Composes existing ``researchos`` infrastructure rather than duplicating it.
"""

from __future__ import annotations

from typing import Any, List, Mapping, Optional, Sequence

from researchos.quant_engine.probability.statistics import probability_calibration

from .contracts import BaselineResult, CalibrationResult


def _brier_multiclass(probs: Sequence[Mapping[int, float]], actuals: Sequence[float]) -> float:
    """Multi-class Brier score from per-row probability dicts and true labels."""
    if not actuals:
        return 0.0
    total = 0.0
    for p, a in zip(probs, actuals):
        target = [0.0, 0.0, 0.0]
        target[int(a) + 1] = 1.0
        pred = [p.get(-1, 0.0), p.get(0, 0.0), p.get(1, 0.0)]
        total += sum((pi - ti) ** 2 for pi, ti in zip(pred, target))
    return total / len(actuals)


def _brier_from_proba(
    probs: Sequence[Mapping[int, float]],
    actuals: Sequence[float],
) -> float:
    """Alias for :func:`_brier_multiclass` (scaled to per-sample mean over 3 classes)."""
    if not actuals:
        return 0.0
    return _brier_multiclass(probs, actuals) / 3.0


def _average_confidence(
    probs: Sequence[Mapping[int, float]],
) -> float:
    if not probs:
        return 0.0
    return sum(max(p.values()) for p in probs) / len(probs)


def evaluate_calibration(
    probs: Sequence[Mapping[int, float]],
    actuals: Sequence[float],
    num_bins: int = 10,
    model_brier: Optional[float] = None,
    baseline_brier: Optional[float] = None,
    baseline: Optional[BaselineResult] = None,
) -> CalibrationResult:
    """Assess calibration of predicted probabilities.

    Args:
        probs: Per-observation predicted probability dicts {class: prob}.
        actuals: True labels (1/0/−1).
        num_bins: Number of reliability bins (reused by the existing helper).
        model_brier: Optional precomputed model Brier score.
        baseline_brier: Optional precomputed baseline Brier score.
        baseline: Optional :class:`BaselineResult` for comparison context.
    """
    # Reuse the existing reliability-table generator (prefers positive-class
    # "up" probability = proba[1]).
    up_probs = [float(p.get(1, 0.0)) for p in probs]
    up_actual = [1 if a == 1 else 0 for a in actuals]
    try:
        reliability = probability_calibration(up_probs, up_actual, num_bins=num_bins)
    except ValueError:
        reliability = {"bin_labels": [], "predicted_probabilities": [], "observed_frequencies": []}

    if model_brier is None:
        model_brier = _brier_from_proba(probs, actuals)
    if baseline_brier is None:
        baseline_brier = 0.0

    avg_conf = _average_confidence(probs)
    # Mean accuracy of the argmax prediction.
    predictions: List[int] = []
    for p in probs:
        if p:
            predictions.append(max(p, key=lambda k: p[k]))
        else:
            predictions.append(0)
    avg_acc = (
        sum(1 for p, a in zip(predictions, actuals) if int(p) == int(a)) / len(actuals)
        if actuals
        else 0.0
    )

    table: Mapping[str, Any] = {
        "model_brier": model_brier,
        "baseline_brier": baseline_brier,
        "brier_delta": model_brier - baseline_brier,
        "reliability_up": reliability,
        "n_actual": len(actuals),
        **({} if baseline is None else {"baseline_accuracy": baseline.accuracy}),
    }
    return CalibrationResult(
        num_bins=num_bins,
        reliability_table=table,
        brier_score=model_brier,
        avg_confidence=avg_conf,
        avg_accuracy=avg_acc,
    )


__all__ = [
    "evaluate_calibration",
    "_brier_multiclass",
    "_brier_from_proba",
    "_average_confidence",
]
