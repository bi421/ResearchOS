"""
Phase 5.2 — macro-augmented dataset assembly.

Merges the existing price/technical ``FeatureBuilder`` output (the same 19
features Phase 5.1 uses, untouched) with the new macro factor features from
``MacroFeatureBuilder`` (DXY / US10Y / VIX), then aligns everything with
multiclass direction labels exactly the way ``DatasetBuilder`` does for
Phase 5.1 — trimming any row where a feature or label is undefined.

This module does not modify ``quant_engine.machine_learning.dataset_builder``
or anything under ``experiments/phase51`` (which is frozen); it composes
those pieces from the outside.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from researchos.quant_engine.machine_learning.dataset_contracts import (
    BUILDER_VERSION,
    DATASET_VERSION,
    ResearchDataset,
)
from researchos.quant_engine.machine_learning.features import FeatureBuilder
from researchos.quant_engine.machine_learning.labels import multiclass_label

from .macro_features import MacroFeatureBuilder, MacroFeatureSet

PHASE52_DATASET_VERSION = "1.0.0"


def build_macro_augmented_dataset(
    close: Sequence[float],
    high: Sequence[float],
    low: Sequence[float],
    volume: Sequence[float],
    macro_factor_series: dict[str, Sequence[float | None]],
    horizon: int,
    threshold: float,
) -> tuple[ResearchDataset, MacroFeatureSet]:
    """Build a price+macro aligned ``ResearchDataset`` plus macro diagnostics.

    ``macro_factor_series`` must already be aligned bar-for-bar with
    ``close``/``high``/``low``/``volume`` (same length, same order). Missing
    factors are represented as an absent key, not a placeholder series.
    """
    close = list(close)
    n = len(close)
    if not (len(high) == n and len(low) == n and len(volume) == n):
        raise ValueError("close, high, low and volume must have equal length")

    price_builder = FeatureBuilder(close, high, low, volume)
    price_feature_set = price_builder.build(drop_na=False)
    price_names = list(price_feature_set.feature_names)
    price_rows = price_feature_set.data

    macro_builder = MacroFeatureBuilder(aligned_length=n, factor_series=macro_factor_series)
    macro_feature_set = macro_builder.build()

    combined_names = tuple(price_names) + macro_feature_set.feature_names
    labels = multiclass_label(close, horizon, threshold)

    aligned_features: list[tuple[float, ...]] = []
    aligned_labels: list[float] = []
    for i in range(n):
        label = labels[i] if i < len(labels) else None
        if label is None or (isinstance(label, float) and math.isnan(label)):
            continue
        price_row = price_rows[i]
        macro_row = macro_feature_set.data[i]
        full_row = tuple(price_row) + tuple(macro_row)
        if any(v is None or (isinstance(v, float) and math.isnan(v)) for v in full_row):
            continue
        aligned_features.append(full_row)  # type: ignore[arg-type]
        aligned_labels.append(float(label))

    feature_count = len(combined_names)
    sample_count = len(aligned_features)
    metadata = {
        "dataset_version": DATASET_VERSION,
        "builder_version": BUILDER_VERSION,
        "phase52_dataset_version": PHASE52_DATASET_VERSION,
        "feature_count": feature_count,
        "sample_count": sample_count,
        "label_name": "multiclass",
        "feature_names": list(combined_names),
        "horizon": horizon,
        "threshold": threshold,
        "price_feature_count": len(price_names),
        "macro_feature_count": len(macro_feature_set.feature_names),
        "macro_symbols_present": list(macro_feature_set.symbols_present),
        "macro_symbols_missing": list(macro_feature_set.symbols_missing),
    }

    dataset = ResearchDataset(
        feature_names=combined_names,
        features=tuple(aligned_features),
        labels=tuple(aligned_labels),
        metadata=metadata,
        sample_count=sample_count,
        feature_count=feature_count,
        label_name="multiclass",
        created_at=None,
        version=DATASET_VERSION,
    )
    return dataset, macro_feature_set


__all__ = ["build_macro_augmented_dataset", "PHASE52_DATASET_VERSION"]
