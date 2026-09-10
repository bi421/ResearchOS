"""
Phase 5.2 — macro-augmented dataset assembly.

Merges price/technical features with macro features and labels while
preserving the original source-row identity of every retained observation.
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

PHASE52_DATASET_VERSION = "1.1.0"


def build_macro_augmented_dataset(
    close: Sequence[float], high: Sequence[float], low: Sequence[float],
    volume: Sequence[float], macro_factor_series: dict[str, Sequence[float | None]],
    horizon: int, threshold: float,
) -> tuple[ResearchDataset, MacroFeatureSet]:
    """Build the Phase 5.2 dataset and retain source indices in metadata."""
    close = list(close)
    n = len(close)
    if not (len(high) == n and len(low) == n and len(volume) == n):
        raise ValueError("close, high, low and volume must have equal length")

    price_feature_set = FeatureBuilder(close, high, low, volume).build(drop_na=False)
    price_names = list(price_feature_set.feature_names)
    macro_feature_set = MacroFeatureBuilder(
        aligned_length=n, factor_series=macro_factor_series
    ).build()
    combined_names = tuple(price_names) + macro_feature_set.feature_names
    labels = multiclass_label(close, horizon, threshold)

    features: list[tuple[float, ...]] = []
    aligned_labels: list[float] = []
    source_indices: list[int] = []
    for i in range(n):
        label = labels[i] if i < len(labels) else None
        if label is None or (isinstance(label, float) and math.isnan(label)):
            continue
        row = tuple(price_feature_set.data[i]) + tuple(macro_feature_set.data[i])
        if any(v is None or (isinstance(v, float) and math.isnan(v)) for v in row):
            continue
        features.append(row)  # type: ignore[arg-type]
        aligned_labels.append(float(label))
        source_indices.append(i)

    sample_count = len(features)
    metadata = {
        "dataset_version": DATASET_VERSION,
        "builder_version": BUILDER_VERSION,
        "phase52_dataset_version": PHASE52_DATASET_VERSION,
        "feature_count": len(combined_names),
        "sample_count": sample_count,
        "label_name": "multiclass",
        "feature_names": list(combined_names),
        "horizon": horizon,
        "threshold": threshold,
        "price_feature_count": len(price_names),
        "macro_feature_count": len(macro_feature_set.feature_names),
        "macro_symbols_present": list(macro_feature_set.symbols_present),
        "macro_symbols_missing": list(macro_feature_set.symbols_missing),
        "source_indices": source_indices,
    }
    dataset = ResearchDataset(
        feature_names=combined_names,
        features=tuple(features),
        labels=tuple(aligned_labels),
        metadata=metadata,
        sample_count=sample_count,
        feature_count=len(combined_names),
        label_name="multiclass",
        created_at=None,
        version=DATASET_VERSION,
    )
    return dataset, macro_feature_set


__all__ = ["build_macro_augmented_dataset", "PHASE52_DATASET_VERSION"]
