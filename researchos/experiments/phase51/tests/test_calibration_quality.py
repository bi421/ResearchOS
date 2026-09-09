from __future__ import annotations

import pytest

from researchos.experiments.phase51.calibration import (
    CALIBRATION_STATUS_NEEDS_ADJUSTMENT,
    CALIBRATION_STATUS_POORLY_CALIBRATED,
    CALIBRATION_STATUS_WELL_CALIBRATED,
    evaluate_calibration,
)


def test_calibration_quality_is_evidence_derived():
    probs = [{1: 0.9, 0: 0.05, -1: 0.05}] * 20
    actuals = [1] * 20
    result = evaluate_calibration(probs, actuals, num_bins=5)

    assert result.reliability_table["calibration_error"] == pytest.approx(0.1)
    assert result.reliability_table["calibration_status"] == CALIBRATION_STATUS_POORLY_CALIBRATED


def test_calibration_quality_accepts_error_below_constitutional_threshold():
    probs = [{1: 0.9, 0: 0.05, -1: 0.05}] * 20
    actuals = [1] * 18 + [0] * 2
    result = evaluate_calibration(probs, actuals, num_bins=5)

    assert result.reliability_table["calibration_error"] == pytest.approx(0.0)
    assert result.reliability_table["calibration_status"] == CALIBRATION_STATUS_WELL_CALIBRATED


def test_calibration_quality_does_not_claim_calibration_without_observations():
    result = evaluate_calibration([], [], num_bins=5)

    assert result.reliability_table["calibration_error"] is None
    assert result.reliability_table["calibration_status"] == CALIBRATION_STATUS_NEEDS_ADJUSTMENT


def test_calibration_rejects_invalid_bin_count():
    with pytest.raises(ValueError, match="num_bins must be positive"):
        evaluate_calibration([{1: 0.5}], [1], num_bins=0)
