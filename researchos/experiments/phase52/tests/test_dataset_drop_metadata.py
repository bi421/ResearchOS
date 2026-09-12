"""Regression tests for dataset-level row-drop provenance."""

from __future__ import annotations

from researchos.experiments.phase52.dataset import build_macro_augmented_dataset


def test_dataset_metadata_records_label_and_feature_drops():
    n = 80
    close = [2000.0 + float(i) for i in range(n)]
    high = [x + 1.0 for x in close]
    low = [x - 1.0 for x in close]
    volume = [100.0] * n
    macro = {
        "DXY": [100.0 + i * 0.1 for i in range(n)],
        "US10Y": [4.0 + i * 0.01 for i in range(n)],
        "VIX": [18.0 + i * 0.05 for i in range(n)],
    }

    dataset, _ = build_macro_augmented_dataset(
        close, high, low, volume, macro, horizon=5, threshold=0.0
    )
    metadata = dataset.metadata

    assert metadata["sample_count"] == 15
    assert metadata["dropped_indices"] == list(range(60)) + list(range(75, 80))
    assert metadata["label_missing_indices"] == list(range(75, 80))
    assert metadata["feature_missing_indices"] == list(range(60))
    assert metadata["feature_missing_counts"]["vol_regime"] == 60
    assert len(metadata["source_indices"]) == dataset.sample_count
