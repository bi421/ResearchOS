from __future__ import annotations

import pandas as pd

from researchos.experiments.phase52.provenance import build_input_provenance, hash_series


def _inputs():
    timestamps = pd.date_range("2024-01-01", periods=4, freq="h", tz="UTC").tolist()
    close = [1.0, 2.0, 3.0, 4.0]
    high = [1.1, 2.1, 3.1, 4.1]
    low = [0.9, 1.9, 2.9, 3.9]
    volume = [10, 20, 30, 40]
    macro = {"DXY": [100.0, 101.0, 99.0, 100.5], "US10Y": [4.0, 4.1, 4.2, 4.3], "VIX": [15.0, 16.0, 17.0, 18.0]}
    macro_timestamps = {symbol: list(timestamps) for symbol in macro}
    return timestamps, close, high, low, volume, macro_timestamps, macro


def test_series_hash_is_deterministic():
    timestamps, close, *_ = _inputs()
    assert hash_series(timestamps, close) == hash_series(timestamps, close)


def test_value_change_changes_hash():
    timestamps, close, *_ = _inputs()
    changed = list(close)
    changed[1] += 0.001
    assert hash_series(timestamps, close) != hash_series(timestamps, changed)


def test_timestamp_change_changes_hash():
    timestamps, close, *_ = _inputs()
    changed = list(timestamps)
    changed[1] = changed[1] + pd.Timedelta(minutes=1)
    assert hash_series(timestamps, close) != hash_series(changed, close)


def test_order_change_changes_hash():
    timestamps, close, *_ = _inputs()
    assert hash_series(timestamps, close) != hash_series(list(reversed(timestamps)), list(reversed(close)))


def test_provenance_contains_price_macro_and_combined_identity():
    args = _inputs()
    provenance = build_input_provenance(*args, required_macro_symbols=("DXY", "US10Y", "VIX"))
    assert provenance["hash_algorithm"] == "sha256"
    assert len(provenance["price_input_hash"]) == 64
    assert set(provenance["macro_input_hashes"]) == {"DXY", "US10Y", "VIX"}
    assert len(provenance["combined_input_hash"]) == 64


def test_macro_factor_identity_is_distinct():
    args = _inputs()
    provenance = build_input_provenance(*args, required_macro_symbols=("DXY", "US10Y", "VIX"))
    assert len(set(provenance["macro_input_hashes"].values())) == 3
