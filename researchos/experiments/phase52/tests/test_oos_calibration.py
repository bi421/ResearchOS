from __future__ import annotations

import pytest

from researchos.experiments.phase52.oos_calibration import (
    apply_temperature,
    calibrate_oos,
    fit_temperature,
)


def _rows(count: int, *, confident: bool) -> tuple[list[dict[int, float]], list[int]]:
    probabilities: list[dict[int, float]] = []
    labels: list[int] = []
    for i in range(count):
        label = 1 if i % 2 == 0 else -1
        labels.append(label)
        if confident:
            probabilities.append({-1: 0.05 if label == 1 else 0.85, 0: 0.05, 1: 0.90 if label == 1 else 0.10})
        else:
            probabilities.append({-1: 0.20 if label == 1 else 0.60, 0: 0.20, 1: 0.60 if label == 1 else 0.20})
    return probabilities, labels


def test_temperature_is_deterministic_and_normalised() -> None:
    probs, labels = _rows(60, confident=True)
    first = fit_temperature(probs, labels)
    second = fit_temperature(probs, labels)
    assert first == second
    scaled = apply_temperature(probs, first)
    assert all(abs(sum(row.values()) - 1.0) < 1e-12 for row in scaled)


def test_oos_calibration_uses_disjoint_samples_and_reports_baseline() -> None:
    calibration_probs, calibration_labels = _rows(60, confident=True)
    evaluation_probs, evaluation_labels = _rows(80, confident=False)
    report = calibrate_oos(
        calibration_probs,
        calibration_labels,
        evaluation_probs,
        evaluation_labels,
    )
    assert report.method == "temperature_scaling"
    assert report.calibration_samples == 60
    assert report.evaluation_samples == 80
    assert report.temperature > 0.0
    assert report.raw_brier >= 0.0
    assert report.calibrated_brier >= 0.0


def test_calibration_rejects_insufficient_samples() -> None:
    probs, labels = _rows(20, confident=True)
    with pytest.raises(ValueError, match="at least 50 calibration samples"):
        fit_temperature(probs, labels)
