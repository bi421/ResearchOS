"""
Phase 5.2 — tests.

Validates the deterministic, leak-free, macro-gating behavior of the Phase
5.2 macro-augmented experiment. Synthetic data is used ONLY for these unit
tests — it is never treated as empirical evidence, matching the Phase 5.1
testing discipline.
"""

from __future__ import annotations

import random

from researchos.experiments.phase52 import (
    MACRO_SYMBOLS,
    MacroFeatureBuilder,
    Phase52Config,
    Phase52Result,
    run_phase52,
)
from researchos.experiments.phase52.contracts import Outcome


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


def _synthetic_macro(n: int, seed: int = 7) -> dict[str, list[float]]:
    """Deterministic synthetic macro factor series (unit-test only)."""
    rng = random.Random(seed)
    out: dict[str, list[float]] = {}
    bases = {"DXY": 100.0, "US10Y": 4.0, "VIX": 18.0}
    for symbol, base in bases.items():
        series = [base]
        for _ in range(n - 1):
            series.append(max(0.01, series[-1] * (1.0 + rng.gauss(0.0, 0.004))))
        out[symbol] = series
    return out


# ── determinism ────────────────────────────────────────────────────────


def test_run_phase52_deterministic_hash():
    close, high, low, volume = _synthetic_ohlcv()
    macro = _synthetic_macro(len(close))
    cfg = Phase52Config(train_size=400, validation_size=100, step_size=100)
    r1 = run_phase52(close, high, low, volume, macro, cfg)
    r2 = run_phase52(close, high, low, volume, macro, cfg)
    assert r1.reproducibility_hash == r2.reproducibility_hash
    assert r1.to_dict() == r2.to_dict()


# ── macro gating (the core new behavior vs Phase 5.1) ───────────────────


def test_run_phase52_blocked_when_macro_missing():
    close, high, low, volume = _synthetic_ohlcv()
    macro = _synthetic_macro(len(close))
    del macro["VIX"]  # simulate one required factor unavailable
    cfg = Phase52Config(train_size=400, validation_size=100, step_size=100)
    r = run_phase52(close, high, low, volume, macro, cfg)
    assert r.outcome == Outcome.BLOCKED
    assert "VIX" in r.validation.reasons[0]
    assert "VIX" in r.macro_symbols_missing


def test_run_phase52_blocked_when_macro_misaligned_length():
    close, high, low, volume = _synthetic_ohlcv()
    macro = _synthetic_macro(len(close))
    macro["DXY"] = macro["DXY"][:-10]  # wrong length vs close
    cfg = Phase52Config(train_size=400, validation_size=100, step_size=100)
    r = run_phase52(close, high, low, volume, macro, cfg)
    assert r.outcome == Outcome.BLOCKED
    assert "DXY" in r.macro_symbols_missing


def test_run_phase52_blocked_when_insufficient_bars():
    close, high, low, volume = _synthetic_ohlcv(n=50)
    macro = _synthetic_macro(50)
    cfg = Phase52Config(train_size=400, validation_size=100)
    r = run_phase52(close, high, low, volume, macro, cfg)
    assert r.outcome == Outcome.BLOCKED
    assert "REAL XAUUSD DATA REQUIRED" in r.validation.reasons[0]


def test_run_phase52_all_macro_symbols_present_and_used_when_available():
    close, high, low, volume = _synthetic_ohlcv()
    macro = _synthetic_macro(len(close))
    cfg = Phase52Config(train_size=400, validation_size=100, step_size=100)
    r = run_phase52(close, high, low, volume, macro, cfg)
    assert set(r.macro_symbols_present) == set(MACRO_SYMBOLS)
    assert r.macro_symbols_missing == ()
    # Default feature resolution should have picked a macro feature, not a
    # pure price feature, since macro data was fully available.
    assert r.estimator_feature_name.startswith("macro_")


# ── walk-forward / leakage-safety ────────────────────────────────────────


def test_run_phase52_produces_multiple_folds():
    close, high, low, volume = _synthetic_ohlcv(n=2000)
    macro = _synthetic_macro(len(close))
    cfg = Phase52Config(train_size=400, validation_size=100, step_size=100)
    r = run_phase52(close, high, low, volume, macro, cfg)
    assert r.outcome != Outcome.BLOCKED
    assert r.num_folds > 1


def test_run_phase52_estimator_feature_explicit_override():
    close, high, low, volume = _synthetic_ohlcv()
    macro = _synthetic_macro(len(close))
    cfg = Phase52Config(train_size=400, validation_size=100, step_size=100, estimator_feature=0)
    r = run_phase52(close, high, low, volume, macro, cfg)
    assert r.outcome != Outcome.BLOCKED
    # Index 0 is always a price feature ("returns"), confirming override honored.
    assert not r.estimator_feature_name.startswith("macro_")


# ── macro feature builder ────────────────────────────────────────────────


def test_macro_feature_builder_marks_missing_symbols():
    series = {"DXY": [100.0 + i * 0.1 for i in range(50)]}
    builder = MacroFeatureBuilder(aligned_length=50, factor_series=series)
    fs = builder.build()
    assert fs.symbols_present == ("DXY",)
    assert set(fs.symbols_missing) == {"US10Y", "VIX"}
    assert len(fs.feature_names) == 9  # 3 factors * 3 features each
    # Missing-symbol columns are all None.
    us10y_idx = fs.feature_names.index("macro_US10Y_return_1")
    assert all(row[us10y_idx] is None for row in fs.data)


def test_macro_feature_builder_no_lookahead_on_first_bars():
    series = {"DXY": [100.0 + i * 0.1 for i in range(30)]}
    builder = MacroFeatureBuilder(aligned_length=30, factor_series=series)
    fs = builder.build()
    ret_idx = fs.feature_names.index("macro_DXY_return_1")
    assert fs.data[0][ret_idx] is None  # no prior bar to compute a return from


# ── result shape ──────────────────────────────────────────────────────


def test_phase52_result_is_phase52result_instance():
    close, high, low, volume = _synthetic_ohlcv()
    macro = _synthetic_macro(len(close))
    cfg = Phase52Config(train_size=400, validation_size=100, step_size=100)
    r = run_phase52(close, high, low, volume, macro, cfg)
    assert isinstance(r, Phase52Result)
    assert r.outcome in (Outcome.PASS, Outcome.FAIL, Outcome.UNCERTAIN, Outcome.BLOCKED)
