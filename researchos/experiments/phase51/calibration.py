"""
Phase 5.1 — probability calibration assessment.

Evaluates whether the model's predicted probabilities are well-calibrated.
Reuses ``researchos.quant_engine.probability.statistics.probability_calibration``
for the reliability table and computes a deterministic multiclass Brier score.

Calibration quality is evidence-derived: the constitutional methodology defines
calibration error as the mean absolute difference between bin midpoint and
observed frequency, with error below 0.05 considered well-calibrated.

Guarantees:
    * Deterministic.
    * Composes existing ``researchos`` infrastructure rather than duplicating it.
    * Never labels an empty/insufficient calibration sample as calibrated.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from researchos.quant_engine.probability.statistics import probability_calibration

from .contracts import BaselineResult, CalibrationResult

CALIBRATION_ERROR_THRESHOLD = 0.05
CALIBRATION_STATUS_WELL_CALIBRATED = "Well-Calibrated"
CALIBRATION_STATUS_NEEDS_ADJUSTMENT = "Needs Adjustment"
CALIBRATION_STATUS_POORLY_CALIBRATED = "Poorly Calibrated"


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
    """Return the mean per-class multiclass Brier score."""
    if not actuals:
        return 0.0
    return _brier_multiclass(probs, actuals) / 3.0


def _average_confidence(probs: Sequence[Mapping[int, float]]) -> float:
    if not probs:
        return 0.0
    return sum(max(p.values()) for p in probs) / len(probs)


def _calibration_error(reliability: Mapping[str, Any], num_bins: int) -> float | None:
    """Compute mean absolute bin-midpoint vs observed-frequency error.

    ``probability_calibration`` returns the integer index of each populated
    bin. The constitutional metric is based on that bin's midpoint, not the
    sample-average predicted probability inside the bin.
    """
    labels = reliability.get("bin_labels", [])
    observed = reliability.get("observed_frequencies", [])
    if not labels or len(labels) != len(observed) or num_bins <= 0:
        return None

    midpoints = [(int(label) + 0.5) / num_bins for label in labels]
    return sum(abs(midpoint - float(actual)) for midpoint, actual in zip(midpoints, observed)) / len(observed)


def _calibration_status(error: float | None) -> str:
    """Classify calibration without claiming quality when evidence is absent."""
    if error is None:
        return CALIBRATION_STATUS_NEEDS_ADJUSTMENT
    if error < CALIBRATION_ERROR_THRESHOLD:
        return CALIBRATION_STATUS_WELL_CALIBRATED
    return CALIBRATION_STATUS_POORLY_CALIBRATED


def evaluate_calibration(
    probs: Sequence[Mapping[int, float]],
    actuals: Sequence[float],
    num_bins: int = 10,
    model_brier: float | None = None,
    baseline_brier: float | None = None,
    baseline: BaselineResult | None = None,
) -> CalibrationResult:
    """Assess calibration of predicted probabilities.

    Args:
        probs: Per-observation predicted probability dicts {class: prob}.
        actuals: True labels (1/0/−1).
        num_bins: Number of reliability bins.
        model_brier: Optional precomputed model Brier score.
        baseline_brier: Optional precomputed baseline Brier score.
        baseline: Optional baseline comparison context.
    """
    if num_bins <= 0:
        raise ValueError("num_bins must be positive")
    if len(probs) != len(actuals):
        raise ValueError("probs and actuals must be equal-length")

    up_probs = [float(p.get(1, 0.0)) for p in probs]
    up_actual = [1 if a == 1 else 0 for a in actuals]
    try:
        reliability = probability_calibration(up_probs, up_actual, num_bins=num_bins)
    except ValueError:
        reliability = {"bin_labels": [], "predicted_probabilities": [], "observed_frequencies": []}

    calibration_error = _calibration_error(reliability, num_bins)
    status = _calibration_status(calibration_error)

    if model_brier is None:
        model_brier = _brier_from_proba(probs, actuals)
    if baseline_brier is None:
        baseline_brier = 0.0

    avg_conf = _average_confidence(probs)
    predictions: list[int] = []
    for p in probs:
        predictions.append(max(p, key=lambda k: p[k]) if p else 0)
    avg_acc = sum(1 for p, a in zip(predictions, actuals) if int(p) == int(a)) / len(actuals) if actuals else 0.0

    table: Mapping[str, Any] = {
        "model_brier": model_brier,
        "baseline_brier": baseline_brier,
        "brier_delta": model_brier - baseline_brier,
        "reliability_up": reliability,
        "calibration_error": calibration_error,
        "calibration_status": status,
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
    "CALIBRATION_ERROR_THRESHOLD",
    "CALIBRATION_STATUS_WELL_CALIBRATED",
    "CALIBRATION_STATUS_NEEDS_ADJUSTMENT",
    "CALIBRATION_STATUS_POORLY_CALIBRATED",
    "evaluate_calibration",
    "_brier_multiclass",
    "_brier_from_proba",
    "_average_confidence",
    "_calibration_error",
    "_calibration_status",
]
