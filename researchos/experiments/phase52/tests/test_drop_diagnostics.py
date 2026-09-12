"""Regression tests for deterministic Phase 5.2 dataset-drop diagnostics."""

from __future__ import annotations

from researchos.experiments.phase52.drop_diagnostics import diagnose_dataset_drops


def test_diagnose_dataset_drops_exposes_label_tail_and_feature_warmup():
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

    report = diagnose_dataset_drops(
        close, high, low, volume, macro, horizon=5, threshold=0.0
    )

    assert report["input_rows"] == n
    assert report["dropped_rows"] > 0
    assert report["label_missing_rows"] == 5
    assert report["feature_missing_rows"] > 0
    assert report["feature_missing_counts"]["vol_regime"] > 0
    assert report["macro_symbols_missing"] == []
    assert report["first_retained_index"] == 60
    assert report["last_retained_index"] == n - 6


def test_diagnose_dataset_drops_reports_missing_macro_features_without_repair():
    n = 80
    close = [2000.0 + float(i) for i in range(n)]
    high = [x + 1.0 for x in close]
    low = [x - 1.0 for x in close]
    volume = [100.0] * n
    macro = {
        "DXY": [100.0 + i * 0.1 for i in range(n)],
        "US10Y": [4.0 + i * 0.01 for i in range(n)],
    }

    report = diagnose_dataset_drops(
        close, high, low, volume, macro, horizon=5, threshold=0.0
    )

    assert "VIX" in report["macro_symbols_missing"]
    assert report["feature_missing_counts"]["macro_VIX_return_1"] == n
    assert report["retained_rows"] == 0
