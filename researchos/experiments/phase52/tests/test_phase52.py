"""Phase 5.2 scientific-boundary and deterministic regression tests."""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from researchos.experiments.phase52 import (
    MACRO_SYMBOLS,
    MacroFeatureBuilder,
    Phase52Config,
    Phase52Result,
    run_phase52,
)
from researchos.experiments.phase52.contracts import Outcome


def _synthetic_ohlcv(n: int = 3000, seed: int = 42):
    rng = random.Random(seed)
    close = [2000.0]
    for _ in range(n - 1):
        close.append(close[-1] * (1.0 + rng.gauss(0.0, 0.003)))
    high = [c * (1.0 + abs(rng.gauss(0, 0.001))) for c in close]
    low = [c * (1.0 - abs(rng.gauss(0, 0.001))) for c in close]
    volume = [float(rng.randint(100, 1000)) for _ in range(n)]
    return close, high, low, volume


def _synthetic_macro(n: int, seed: int = 7) -> dict[str, list[float]]:
    rng = random.Random(seed)
    out: dict[str, list[float]] = {}
    bases = {"DXY": 100.0, "US10Y": 4.0, "VIX": 18.0}
    for symbol, base in bases.items():
        series = [base]
        for _ in range(n - 1):
            series.append(max(0.01, series[-1] * (1.0 + rng.gauss(0.0, 0.004))))
        out[symbol] = series
    return out


def _timestamps(n: int) -> list[datetime]:
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return [start + timedelta(minutes=i) for i in range(n)]


def _run_inputs():
    close, high, low, volume = _synthetic_ohlcv()
    macro = _synthetic_macro(len(close))
    ts = _timestamps(len(close))
    macro_ts = {symbol: list(ts) for symbol in MACRO_SYMBOLS}
    return close, high, low, volume, macro, ts, macro_ts


def test_run_phase52_deterministic_hash():
    close, high, low, volume, macro, ts, macro_ts = _run_inputs()
    cfg = Phase52Config(train_size=400, validation_size=100, step_size=100)
    r1 = run_phase52(close, high, low, volume, macro, cfg, timestamps=ts, macro_timestamps=macro_ts)
    r2 = run_phase52(close, high, low, volume, macro, cfg, timestamps=ts, macro_timestamps=macro_ts)
    assert r1.reproducibility_hash == r2.reproducibility_hash
    assert r1.to_dict() == r2.to_dict()


def test_run_phase52_blocks_legacy_value_only_api():
    close, high, low, volume = _synthetic_ohlcv()
    macro = _synthetic_macro(len(close))
    r = run_phase52(close, high, low, volume, macro, Phase52Config(train_size=400, validation_size=100))
    assert r.outcome == Outcome.BLOCKED
    assert "TIMESTAMP ALIGNMENT" in r.validation.reasons[0]


def test_run_phase52_blocks_equal_length_shifted_macro_timestamps():
    close, high, low, volume, macro, ts, macro_ts = _run_inputs()
    macro_ts["DXY"] = [value + timedelta(minutes=1) for value in ts]
    r = run_phase52(close, high, low, volume, macro, Phase52Config(train_size=400, validation_size=100), timestamps=ts, macro_timestamps=macro_ts)
    assert r.outcome == Outcome.BLOCKED
    assert "DXY" in r.validation.reasons[0]
    assert "exact timestamp mismatch" in r.validation.reasons[0]


def test_run_phase52_blocks_missing_macro_timestamp_contract():
    close, high, low, volume, macro, ts, macro_ts = _run_inputs()
    del macro_ts["VIX"]
    r = run_phase52(close, high, low, volume, macro, Phase52Config(train_size=400, validation_size=100), timestamps=ts, macro_timestamps=macro_ts)
    assert r.outcome == Outcome.BLOCKED
    assert "VIX" in r.macro_symbols_missing


def test_run_phase52_blocks_when_macro_missing():
    close, high, low, volume, _, ts, macro_ts = _run_inputs()
    macro = _synthetic_macro(len(close))
    del macro["VIX"]
    r = run_phase52(close, high, low, volume, macro, Phase52Config(train_size=400, validation_size=100), timestamps=ts, macro_timestamps=macro_ts)
    assert r.outcome == Outcome.BLOCKED
    assert "VIX" in r.validation.reasons[0]


def test_run_phase52_blocks_when_macro_misaligned_length():
    close, high, low, volume, macro, ts, macro_ts = _run_inputs()
    macro["DXY"] = macro["DXY"][:-10]
    r = run_phase52(close, high, low, volume, macro, Phase52Config(train_size=400, validation_size=100), timestamps=ts, macro_timestamps=macro_ts)
    assert r.outcome == Outcome.BLOCKED
    assert "DXY" in r.macro_symbols_missing


def test_run_phase52_blocks_when_insufficient_bars():
    close, high, low, volume = _synthetic_ohlcv(n=50)
    macro = _synthetic_macro(50)
    ts = _timestamps(50)
    macro_ts = {symbol: list(ts) for symbol in MACRO_SYMBOLS}
    r = run_phase52(close, high, low, volume, macro, Phase52Config(train_size=400, validation_size=100), timestamps=ts, macro_timestamps=macro_ts)
    assert r.outcome == Outcome.BLOCKED
    assert "REAL XAUUSD DATA REQUIRED" in r.validation.reasons[0]


def test_run_phase52_all_macro_symbols_present_and_used_when_available():
    close, high, low, volume, macro, ts, macro_ts = _run_inputs()
    r = run_phase52(close, high, low, volume, macro, Phase52Config(train_size=400, validation_size=100, step_size=100), timestamps=ts, macro_timestamps=macro_ts)
    assert set(r.macro_symbols_present) == set(MACRO_SYMBOLS)
    assert r.macro_symbols_missing == ()
    assert r.estimator_feature_name.startswith("macro_")


def test_run_phase52_produces_multiple_folds():
    close, high, low, volume, macro, ts, macro_ts = _run_inputs()
    r = run_phase52(close, high, low, volume, macro, Phase52Config(train_size=400, validation_size=100, step_size=100), timestamps=ts, macro_timestamps=macro_ts)
    assert r.outcome != Outcome.BLOCKED
    assert r.num_folds > 1


def test_run_phase52_estimator_feature_explicit_override():
    close, high, low, volume, macro, ts, macro_ts = _run_inputs()
    r = run_phase52(close, high, low, volume, macro, Phase52Config(train_size=400, validation_size=100, step_size=100, estimator_feature=0), timestamps=ts, macro_timestamps=macro_ts)
    assert r.outcome != Outcome.BLOCKED
    assert not r.estimator_feature_name.startswith("macro_")


def test_macro_feature_builder_marks_missing_symbols():
    series = {"DXY": [100.0 + i * 0.1 for i in range(50)]}
    fs = MacroFeatureBuilder(aligned_length=50, factor_series=series).build()
    assert fs.symbols_present == ("DXY",)
    assert set(fs.symbols_missing) == {"US10Y", "VIX"}
    assert len(fs.feature_names) == 9
    us10y_idx = fs.feature_names.index("macro_US10Y_return_1")
    assert all(row[us10y_idx] is None for row in fs.data)


def test_macro_feature_builder_no_lookahead_on_first_bars():
    series = {"DXY": [100.0 + i * 0.1 for i in range(30)]}
    fs = MacroFeatureBuilder(aligned_length=30, factor_series=series).build()
    ret_idx = fs.feature_names.index("macro_DXY_return_1")
    assert fs.data[0][ret_idx] is None


def test_phase52_result_is_phase52result_instance():
    close, high, low, volume, macro, ts, macro_ts = _run_inputs()
    r = run_phase52(close, high, low, volume, macro, Phase52Config(train_size=400, validation_size=100, step_size=100), timestamps=ts, macro_timestamps=macro_ts)
    assert isinstance(r, Phase52Result)
    assert r.outcome in (Outcome.PASS, Outcome.FAIL, Outcome.UNCERTAIN, Outcome.BLOCKED)
