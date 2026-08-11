"""
Phase 5.1 — tests.

Validates the deterministic, leak-free, baseline/cost/calibration behavior of
the Phase 5.1 experiment.  Synthetic data is used ONLY for these unit tests —
it is never treated as empirical evidence.
"""

from __future__ import annotations

import random

import pytest

from researchos.experiments.phase51 import (
    baseline_always_predict,
    evaluate_baseline,
    apply_costs,
    evaluate_calibration,
    evaluate_significance,
    EmpiricalProbabilityEstimator,
    Phase51Config,
    run_phase51,
    Outcome,
)


def _synthetic_ohlcv(n: int = 3000, seed: int = 42):
    """Deterministic synthetic OHLCV (unit-test only, never empirical evidence)."""
    rng = random.Random(seed)
    close = [2000.0]
    for _ in range(n - 1):
        close.append(close[-1] * (1.0 + rng.gauss(0.0, 0.003)))
    high = [c * (1.0 + abs(rng.gauss(0, 0.001))) for c in close]
    low = [c * (1.0 - abs(rng.gauss(0, 0.001))) for c in close]
    volume = [float(rng.randint(100, 1000)) for _ in range(n)]
    return close, high, low, volume


# ── determinism ────────────────────────────────────────────────────────

def test_run_phase51_deterministic_hash():
    close, high, low, volume = _synthetic_ohlcv()
    cfg = Phase51Config(train_size=400, validation_size=100, step_size=100)
    r1 = run_phase51(close, high, low, volume, cfg)
    r2 = run_phase51(close, high, low, volume, cfg)
    assert r1.reproducibility_hash == r2.reproducibility_hash
    assert r1.to_dict() == r2.to_dict()


def test_run_phase51_blocked_when_insufficient_data():
    close, high, low, volume = _synthetic_ohlcv(n=50)
    cfg = Phase51Config(train_size=400, validation_size=100)
    r = run_phase51(close, high, low, volume, cfg)
    assert r.outcome == Outcome.BLOCKED
    assert "REAL XAUUSD DATA REQUIRED" in r.validation.reasons[0]


# ── baseline ───────────────────────────────────────────────────────────

def test_baseline_uses_train_only():
    train = [1, 1, 1, 1, 0, 0, 0, 0, -1, -1]  # majority 1
    val = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    pred = baseline_always_predict(train, val)
    assert pred == 1
    # Majority = 1 (4×1 vs 3×0 vs 3×-1)


def test_baseline_accuracy_equals_frequency_when_val_has_majority():
    train = [1, 1, 1, 1, 0, 0, 0, 0, -1, -1]
    val = [1, 1, 1, 1, 1, 1, 1, 1, 0, 0]
    res = evaluate_baseline(train, val)
    assert res.accuracy == pytest.approx(0.8)  # 8/10 correct


# ── probability estimator ──────────────────────────────────────────────

def test_estimator_deterministic():
    feats = [[0.0, 1.0], [0.0, 1.0], [0.0, 1.0], [1.0, 0.0], [1.0, 0.0]]
    labs = [1, 1, 1, 0, 0]
    est = EmpiricalProbabilityEstimator(n_bins=2, feature_indices=[0]).fit(feats, labs)
    p1 = est.predict_proba([0.0, 1.0])
    p2 = est.predict_proba([0.0, 1.0])
    assert p1 == p2
    assert est.predict_class([0.0, 1.0]) == 1


def test_estimator_lookahead_fit_only():
    # Feature near 0 predicts 1; feature near 1 predicts 0.
    feats = [[0.0], [0.0], [0.0], [1.0], [1.0]]
    labs = [1, 1, 1, 0, 0]
    est = EmpiricalProbabilityEstimator(n_bins=2, feature_indices=[0]).fit(feats, labs)
    # OOS: feature 0.1 (unseen) -> predicted 1 (from train bin 0)
    assert est.predict_class([0.1]) == 1


# ── cost ───────────────────────────────────────────────────────────────

def test_cost_degrades_accuracy_with_large_spread():
    preds = [1, 1, 1, 1, 1]
    actuals = [1, 1, 1, 1, 1]
    close = [2000.0] * 5
    # Huge spread in price units overwhelms the threshold.
    res = apply_costs(
        preds, actuals, close, threshold=0.001,
        spread_spec="fixed:10.0",  # $10 spread on $2000 gold
        slippage_spec="fixed:0.0",
        commission_spec="fixed:0.0",
        cost_applied=True,
    )
    assert res.net_accuracy_all < res.gross_accuracy
    assert res.cost_applied


def test_cost_zero_spread_no_degredation():
    preds = [1, 1, 1, 1, 1]
    actuals = [1, 1, 1, 1, 1]
    close = [2000.0] * 5
    res = apply_costs(
        preds, actuals, close, threshold=0.001,
        spread_spec="fixed:0.0",
        slippage_spec="fixed:0.0",
        commission_spec="fixed:0.0",
        cost_applied=True,
    )
    assert res.net_accuracy_all == pytest.approx(res.gross_accuracy)


# ── calibration ────────────────────────────────────────────────────────

def test_calibration_reliability_table():
    probs = [{1: 0.9, 0: 0.05, -1: 0.05}, {1: 0.9, 0: 0.05, -1: 0.05}]
    actuals = [1, 1]
    cal = evaluate_calibration(probs, actuals, num_bins=5)
    assert cal.num_bins == 5
    assert "reliability_up" in cal.reliability_table
    assert cal.avg_confidence == pytest.approx(0.9)


# ── significance ───────────────────────────────────────────────────────

def test_significance_model_better_than_baseline():
    model_pred = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    base_pred = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    actuals = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    sig = evaluate_significance(model_pred, base_pred, actuals, 0.05)
    assert sig.model_better_count == 10
    assert sig.baseline_better_count == 0
    assert sig.significant is True


# ── self-validation outcome ────────────────────────────────────────────

def test_outcome_pass_when_model_wins_net_and_significant():
    from researchos.experiments.phase51.self_validation import aggregate_outcome

    flags = aggregate_outcome(
        data_valid=True,
        leakage_check=True,
        out_of_sample=True,
        cost_adjusted=True,
        reproducible=True,
        model_accuracy=0.7,
        baseline_accuracy=0.5,
        net_accuracy_all=0.65,
        significant=True,
        min_sample_count=100,
        validation_sample_count=200,
    )
    assert flags.outcome == Outcome.PASS


def test_outcome_fail_when_model_loses_net():
    from researchos.experiments.phase51.self_validation import aggregate_outcome

    flags = aggregate_outcome(
        data_valid=True,
        leakage_check=True,
        out_of_sample=True,
        cost_adjusted=True,
        reproducible=True,
        model_accuracy=0.6,
        baseline_accuracy=0.6,
        net_accuracy_all=0.55,
        significant=True,
        min_sample_count=100,
        validation_sample_count=200,
    )
    assert flags.outcome == Outcome.FAIL


def test_outcome_blocked_without_data():
    from researchos.experiments.phase51.self_validation import aggregate_outcome

    flags = aggregate_outcome(
        data_valid=False,
        leakage_check=False,
        out_of_sample=False,
        cost_adjusted=False,
        reproducible=False,
        model_accuracy=0.0,
        baseline_accuracy=0.0,
        net_accuracy_all=0.0,
        significant=False,
        min_sample_count=100,
        validation_sample_count=0,
    )
    assert flags.outcome == Outcome.BLOCKED
