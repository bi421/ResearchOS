"""Regression tests for Phase 5.2 source-row identity preservation."""
from __future__ import annotations

from researchos.experiments.phase52.dataset import build_macro_augmented_dataset


EXPECTED_WARMUP = 60


def _inputs():
    close = [100.0 + i for i in range(150)]
    high = [c + 1.0 for c in close]
    low = [c - 1.0 for c in close]
    volume = [1000.0] * len(close)
    macro = {
        "DXY": [100.0 + i for i in range(150)],
        "US10Y": [4.0 + i * 0.01 for i in range(150)],
        "VIX": [18.0 + i * 0.1 for i in range(150)],
    }
    return close, high, low, volume, macro


def test_source_indices_match_retained_rows():
    inputs = _inputs()
    dataset, _ = build_macro_augmented_dataset(*inputs, horizon=5, threshold=0.0)
    retained = dataset.metadata["source_indices"]
    assert len(retained) == dataset.sample_count
    assert all(0 <= i < len(inputs[0]) for i in retained)
    assert retained == sorted(retained)


def test_source_indices_reveal_dropped_warmup_and_tail_rows():
    inputs = _inputs()
    dataset, _ = build_macro_augmented_dataset(*inputs, horizon=5, threshold=0.0)
    retained = dataset.metadata["source_indices"]
    assert retained
    assert retained[0] > 0
    assert retained[-1] < len(inputs[0]) - 1


def test_source_indices_exact_contiguous_retention_contract():
    inputs = _inputs()
    horizon = 5

    dataset, _ = build_macro_augmented_dataset(
        *inputs,
        horizon=horizon,
        threshold=0.0,
    )

    retained = dataset.metadata["source_indices"]
    expected = list(range(EXPECTED_WARMUP, len(inputs[0]) - horizon))

    assert retained == expected
    assert retained[0] == EXPECTED_WARMUP
    assert retained[-1] == len(inputs[0]) - horizon - 1
    assert len(retained) == len(inputs[0]) - EXPECTED_WARMUP - horizon


def test_source_index_maps_dataset_position_to_original_close():
    inputs = _inputs()
    close = inputs[0]
    dataset, _ = build_macro_augmented_dataset(*inputs, horizon=5, threshold=0.0)
    retained = dataset.metadata["source_indices"]

    for dataset_pos, source_pos in enumerate(retained):
        assert source_pos == EXPECTED_WARMUP + dataset_pos
        assert close[source_pos] == close[EXPECTED_WARMUP + dataset_pos]
