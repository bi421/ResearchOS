"""Phase 5.1 unit tests for deterministic and temporal-valid research behavior."""

from __future__ import annotations

import math
import random

import pytest

from researchos.experiments.phase51 import (
    EmpiricalProbabilityEstimator,
    Outcome,
    Phase51Config,
    apply_costs,
    baseline_always_predict,
    evaluate_baseline,
    evaluate_calibration,
    evaluate_significance,
    run_phase51,
)


def _synthetic_ohlcv(n: int = 3000, seed: int = 42):
    rng = random.Random(seed)
    close = [2000.0]
    for _ in range(n - 1):
        close.append(close[-1] * (1.0 + rng.gauss(0.0, 0.003)))
    high = [c * (1.0 + abs(rng.gauss(0, 0.001))) for c in close]
    low = [c * (1.0 - abs(rng.gauss(0, 0.001))) for c in close]
    volume = [float(rng.randint(100, 1000)) for _ in range(n)]
    return close, high, low, volume


def test_run_phase51_deterministic_hash():
    close, high, low, volume = _synthetic_ohlcv()
    cfg = Phase51Config(train_size=400, validation_size=100, step_size=100)
    r1 = run_phase51(close, high, low, volume, cfg)
    r2 = run_phase51(close, high, low, volume, cfg)
    assert r1.reproducibility_hash == r2.reproducibility_hash
    assert r1.to_dict() == r2.to_dict()


def test_run_phase51_records_real_temporal_validation():
    close, high, low, volume = _synthetic_ohlcv()
    cfg = Phase51Config(train_size=400, validation_size=100, step_size=100, horizon=5)
    result = run_phase51(close, high, low, volume, cfg)
    assert result.validation.data_valid is True
    assert result.validation.leakage_check is True
    assert result.validation.out_of_sample is True
    assert result.metadata["purge_bars"] == 5
    assert result.metadata["expected_folds"] == result.num_folds


def test_run_phase51_blocks_non_finite_data():
    close, high, low, volume = _synthetic_ohlcv(n=1000)
    close[500] = math.nan
    result = run_phase51(close, high, low, volume, Phase51Config(train_size=400, validation_size=100))
    assert result.outcome == Outcome.BLOCKED
    assert "non-finite" in result.validation.reasons[0]


def test_run_phase51_blocks_invalid_temporal_configuration():
    close, high, low, volume = _synthetic_ohlcv(n=1000)
    result = run_phase51(close, high, low, volume, Phase51Config(train_size=400, validation_size=100, horizon=0))
    assert result.outcome == Outcome.BLOCKED


def test_run_phase51_blocked_when_insufficient_data():
    close, high, low, volume = _synthetic_ohlcv(n=50)
    cfg = Phase51Config(train_size=400, validation_size=100)
    r = run_phase51(close, high, low, volume, cfg)
    assert r.outcome == Outcome.BLOCKED
    assert "REAL XAUUSD DATA REQUIRED" in r.validation.reasons[0]


def test_baseline_uses_train_only():
    train = [1, 1, 1, 1, 0, 0, 0, 0, -1, -1]
    val = [1] * 10
    assert baseline_always_predict(train, val) == 1


def test_baseline_accuracy_equals_frequency_when_val_has_majority():
    train = [1, 1, 1, 1, 0, 0, 0, 0, -1, -1]
    val = [1, 1, 1, 1, 1, 1, 1, 1, 0, 0]
    assert evaluate_baseline(train, val).accuracy == pytest.approx(0.8)


def test_estimator_deterministic():
    feats = [[0.0, 1.0], [0.0, 1.0], [0.0, 1.0], [1.0, 0.0], [1.0, 0.0]]
    labs = [1, 1, 1, 0, 0]
    est = EmpiricalProbabilityEstimator(n_bins=2, feature_indices=[0]).fit(feats, labs)
    assert est.predict_proba([0.0, 1.0]) == est.predict_proba([0.0, 1.0])
    assert est.predict_class([0.0, 1.0]) == 1


def test_estimator_lookahead_fit_only():
    feats = [[0.0], [0.0], [0.0], [1.0], [1.0]]
    labs = [1, 1, 1, 0, 0]
    est = EmpiricalProbabilityEstimator(n_bins=2, feature_indices=[0]).fit(feats, labs)
    assert est.predict_class([0.1]) == 1


def test_cost_degrades_accuracy_with_large_spread():
    res = apply_costs([1] * 5, [1] * 5, [2000.0] * 5, threshold=0.001, spread_spec="fixed:10.0", slippage_spec="fixed:0.0", commission_spec="fixed:0.0", cost_applied=True)
    assert res.net_accuracy_all < res.gross_accuracy
    assert res.cost_applied


def test_cost_zero_spread_no_degredation():
    res = apply_costs([1] * 5, [1] * 5, [2000.0] * 5, threshold=0.001, spread_spec="fixed:0.0", slippage_spec="fixed:0.0", commission_spec="fixed:0.0", cost_applied=True)
    assert res.net_accuracy_all == pytest.approx(res.gross_accuracy)


def test_calibration_reliability_table():
    probs = [{1: 0.9, 0: 0.05, -1: 0.05}, {1: 0.9, 0: 0.05, -1: 0.05}]
    cal = evaluate_calibration(probs, [1, 1], num_bins=5)
    assert cal.num_bins == 5
    assert "reliability_up" in cal.reliability_table
    assert cal.avg_confidence == pytest.approx(0.9)


def test_significance_model_better_than_baseline():
    sig = evaluate_significance([1] * 10, [0] * 10, [1] * 10, 0.05)
    assert sig.model_better_count == 10
    assert sig.baseline_better_count == 0
    assert sig.significant is True


def test_outcome_pass_when_model_wins_net_and_significant():
    from researchos.experiments.phase51.self_validation import aggregate_outcome

    flags = aggregate_outcome(data_valid=True, leakage_check=True, out_of_sample=True, cost_adjusted=True, reproducible=True, model_accuracy=0.7, baseline_accuracy=0.5, net_accuracy_all=0.65, significant=True, min_sample_count=100, validation_sample_count=200)
    assert flags.outcome == Outcome.PASS


def test_outcome_fail_when_model_loses_net():
    from researchos.experiments.phase51.self_validation import aggregate_outcome

    flags = aggregate_outcome(data_valid=True, leakage_check=True, out_of_sample=True, cost_adjusted=True, reproducible=True, model_accuracy=0.6, baseline_accuracy=0.6, net_accuracy_all=0.55, significant=True, min_sample_count=100, validation_sample_count=200)
    assert flags.outcome == Outcome.FAIL


def test_outcome_blocked_without_data():
    from researchos.experiments.phase51.self_validation import aggregate_outcome

    flags = aggregate_outcome(data_valid=False, leakage_check=False, out_of_sample=False, cost_adjusted=False, reproducible=False, model_accuracy=0.0, baseline_accuracy=0.0, net_accuracy_all=0.0, significant=False, min_sample_count=100, validation_sample_count=0)
    assert flags.outcome == Outcome.BLOCKED
