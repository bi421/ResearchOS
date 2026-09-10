"""Regression tests for Phase 5.2 source-row identity preservation."""

from __future__ import annotations

from researchos.experiments.phase52.dataset import build_macro_augmented_dataset


def test_macro_dataset_records_retained_source_indices():
    close = [100.0 + i for i in range(30)]
    high = [c + 1.0 for c in close]
    low = [c - 1.0 for c in close]
    volume = [1000.0] * len(close)
    macro = {
        "DXY": [100.0 + i for i in range(30)],
        "US10Y": [4.0 + i * 0.01 for i in range(30)],
        "VIX": [18.0 + i * 0.1 for i in range(30)],
    }

    dataset, _ = build_macro_augmented_dataset(
        close, high, low, volume, macro, horizon=5, threshold=0.0
    )

    retained = dataset.metadata["source_indices"]
    assert retained == list(range(len(dataset.features)))
    assert len(retained) == dataset.sample_count


def test_macro_dataset_source_indices_track_dropped_feature_rows():
    close = [100.0 + i for i in range(30)]
    high = [c + 1.0 for c in close]
    low = [c - 1.0 for c in close]
    volume = [1000.0] * len(close)
    macro = {
        "DXY": [None] + [100.0 + i for i in range(1, 30)],
        "US10Y": [4.0 + i * 0.01 for i in range(30)],
        "VIX": [18.0 + i * 0.1 for i in range(30)],
    }

    dataset, _ = build_macro_augmented_dataset(
        close, high, low, volume, macro, horizon=5, threshold=0.0
    )

    retained = dataset.metadata["source_indices"]
    assert retained[0] > 0
    assert len(retained) == dataset.sample_count
    assert all(0 <= i < len(close) for i in retained)
    assert all(dataset.labels[j] is not None for j in range(dataset.sample_count))
