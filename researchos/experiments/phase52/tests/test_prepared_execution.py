from __future__ import annotations

import pytest

from researchos.experiments.phase52 import Phase52Config
from researchos.experiments.phase52.comparison import run_phase52_comparison_optimized
from researchos.experiments.phase52.prepared import Phase52PreparedData


def _inputs(n: int = 1300):
    close = [100.0 + i * 0.01 for i in range(n)]
    high = [value + 1.0 for value in close]
    low = [value - 1.0 for value in close]
    volume = [1000.0 + i for i in range(n)]
    timestamps = list(range(n))
    macro = {symbol: [float(i) for i in range(n)] for symbol in ("DXY", "US10Y", "VIX")}
    macro_timestamps = {symbol: list(timestamps) for symbol in macro}
    return close, high, low, volume, timestamps, macro_timestamps, macro


def test_prepared_data_validates_identity_contract():
    inputs = _inputs()
    prepared = Phase52PreparedData.build(
        *inputs[:4], inputs[4], inputs[5], inputs[6], horizon=5, threshold=0.0
    )
    prepared.validate(("DXY", "US10Y", "VIX"))
    assert len(prepared.source_indices) == prepared.sample_count
    assert prepared.source_indices == tuple(sorted(set(prepared.source_indices)))
    assert prepared.input_provenance["combined_input_hash"]


def test_prepared_data_rejects_exact_timestamp_mismatch():
    inputs = _inputs()
    macro_timestamps = {symbol: list(values) for symbol, values in inputs[5].items()}
    macro_timestamps["VIX"][17] += 1
    with pytest.raises(ValueError, match="VIX"):
        Phase52PreparedData.build(
            *inputs[:4],
            inputs[4],
            macro_timestamps,
            inputs[6],
            horizon=5,
            threshold=0.0,
        )


def test_comparison_returns_all_feature_sets_from_one_prepared_dataset():
    inputs = _inputs()
    config = Phase52Config(train_size=1000, validation_size=200, step_size=200)
    results = run_phase52_comparison_optimized(
        *inputs[:4],
        inputs[6],
        config=config,
        timestamps=inputs[4],
        macro_timestamps=inputs[5],
    )
    assert set(results) == {
        "PRICE_ONLY",
        "PRICE + DXY",
        "PRICE + US10Y",
        "PRICE + VIX",
        "PRICE + ALL",
    }
    assert all(
        result.metadata.get("prepared_dataset_contract")
        == "single_materialized_dataset_shared_across_feature_sets"
        for result in results.values()
    )
    assert len({result.num_folds for result in results.values()}) == 1


def test_comparison_fails_closed_without_explicit_timestamps():
    inputs = _inputs()
    with pytest.raises(ValueError, match="timestamps"):
        run_phase52_comparison_optimized(*inputs[:4], inputs[6])
