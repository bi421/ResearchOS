"""Deterministic diagnostics for Phase 5.2 dataset row loss.

This module does not repair, fill, interpolate, resample, or otherwise alter
scientific inputs. It explains exactly why rows are excluded by the existing
Phase 5.2 dataset contract.
"""
from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence

from researchos.quant_engine.machine_learning.features import FeatureBuilder
from researchos.quant_engine.machine_learning.labels import multiclass_label

from .macro_features import MacroFeatureBuilder


def diagnose_dataset_drops(
    close: Sequence[float],
    high: Sequence[float],
    low: Sequence[float],
    volume: Sequence[float],
    macro_factor_series: dict[str, Sequence[float | None]],
    horizon: int,
    threshold: float,
) -> dict[str, object]:
    """Explain every excluded source row without changing dataset semantics.

    A row is classified using the same final conditions as
    ``build_macro_augmented_dataset``: missing/NaN label, or missing/NaN
    feature. Multiple feature failures on one row are all reported.
    """
    close = list(close)
    high = list(high)
    low = list(low)
    volume = list(volume)
    n = len(close)

    price = FeatureBuilder(close, high, low, volume).build(drop_na=False)
    macro = MacroFeatureBuilder(n, macro_factor_series).build()
    labels = multiclass_label(close, horizon, threshold)
    names = tuple(price.feature_names) + tuple(macro.feature_names)

    dropped_indices: list[int] = []
    label_missing: list[int] = []
    feature_missing: list[int] = []
    feature_counts: Counter[str] = Counter()

    for i in range(n):
        label = labels[i] if i < len(labels) else None
        label_bad = label is None or (isinstance(label, float) and math.isnan(label))
        row = tuple(price.data[i]) + tuple(macro.data[i])
        bad_features = [
            name
            for name, value in zip(names, row)
            if value is None or (isinstance(value, float) and math.isnan(value))
        ]
        if label_bad:
            label_missing.append(i)
        if bad_features:
            feature_missing.append(i)
            feature_counts.update(bad_features)
        if label_bad or bad_features:
            dropped_indices.append(i)

    retained = n - len(dropped_indices)
    return {
        "input_rows": n,
        "retained_rows": retained,
        "dropped_rows": len(dropped_indices),
        "dropped_indices": dropped_indices,
        "label_missing_rows": len(label_missing),
        "label_missing_indices": label_missing,
        "feature_missing_rows": len(feature_missing),
        "feature_missing_indices": feature_missing,
        "feature_missing_counts": dict(sorted(feature_counts.items())),
        "first_retained_index": next((i for i in range(n) if i not in set(dropped_indices)), None),
        "last_retained_index": next((i for i in range(n - 1, -1, -1) if i not in set(dropped_indices)), None),
        "price_feature_count": len(price.feature_names),
        "macro_feature_count": len(macro.feature_names),
        "macro_symbols_present": list(macro.symbols_present),
        "macro_symbols_missing": list(macro.symbols_missing),
    }


__all__ = ["diagnose_dataset_drops"]
