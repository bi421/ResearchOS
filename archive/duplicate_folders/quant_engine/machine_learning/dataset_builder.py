"""
Dataset Builder — canonical research dataset producer.

The Dataset Builder merges raw OHLCV into a feature matrix via
``FeatureBuilder`` and supervised-learning labels via ``LabelBuilder``,
then aligns them into a single deterministic ``ResearchDataset``.

Architecture rules:
    * May call FeatureBuilder and LabelBuilder.
    * FeatureBuilder and LabelBuilder must never know DatasetBuilder exists.
    * No circular imports.
    * Pure Python, deterministic, no randomness.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from .dataset_contracts import BUILDER_VERSION, DATASET_VERSION, ResearchDataset
from .features import FeatureBuilder
from .label_builder import LabelBuilder


class DatasetBuilder:
    """Builds aligned research datasets from OHLCV inputs.

    The builder internally constructs a ``FeatureBuilder`` and a
    ``LabelBuilder`` and trims warmup rows (features undefined) and tail
    rows (labels undefined) so features and labels align perfectly.
    """

    def __init__(self, close, high, low, volume) -> None:
        self.close = list(close)
        self.high = list(high)
        self.low = list(low)
        self.volume = list(volume)
        n = len(self.close)
        if not (len(self.high) == n and len(self.low) == n and len(self.volume) == n):
            raise ValueError("close, high, low and volume must have equal length")

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------

    def _feature_matrix(self):
        """Build the full feature matrix (with ``None`` warmup values)."""
        builder = FeatureBuilder(self.close, self.high, self.low, self.volume)
        feature_set = builder.build(drop_na=False)
        return list(feature_set.feature_names), feature_set.data

    def _assemble(
        self,
        label_values: Sequence[float | None],
        label_name: str,
        horizon: int | None = None,
        extra_metadata: dict | None = None,
    ) -> ResearchDataset:
        """Align feature rows and labels, trimming undefined entries."""
        feature_names, rows = self._feature_matrix()
        n = len(rows)
        if len(label_values) != n:
            raise ValueError(f"label length {len(label_values)} does not match feature row count {n}")

        aligned_features: list[tuple[float, ...]] = []
        aligned_labels: list[float] = []
        for i in range(n):
            label = label_values[i]
            if label is None:
                continue
            if isinstance(label, float) and math.isnan(label):
                continue
            row = rows[i]
            if any(v is None or (isinstance(v, float) and math.isnan(v)) for v in row):
                continue
            aligned_features.append(tuple(row))  # type: ignore[arg-type]
            aligned_labels.append(float(label))

        feature_count = len(feature_names)
        sample_count = len(aligned_features)
        metadata = {
            "dataset_version": DATASET_VERSION,
            "builder_version": BUILDER_VERSION,
            "feature_count": feature_count,
            "sample_count": sample_count,
            "label_name": label_name,
            "feature_names": list(feature_names),
        }
        if horizon is not None:
            metadata["horizon"] = horizon
        if extra_metadata:
            metadata.update(extra_metadata)

        return ResearchDataset(
            feature_names=tuple(feature_names),
            features=tuple(aligned_features),
            labels=tuple(aligned_labels),
            metadata=metadata,
            sample_count=sample_count,
            feature_count=feature_count,
            label_name=label_name,
            created_at=None,
            version=DATASET_VERSION,
        )

    # ------------------------------------------------------------------
    # public builders
    # ------------------------------------------------------------------

    def build(self, horizon: int = 1) -> ResearchDataset:
        """Build a dataset using future-return labels (default horizon)."""
        return self.build_with_future_return(horizon)

    def build_with_future_return(self, horizon: int = 1) -> ResearchDataset:
        """Build a dataset with future-return (regression) labels."""
        result = LabelBuilder(self.close).build_future_return(horizon)
        return self._assemble(result.values, result.name, horizon=horizon)

    def build_with_binary_labels(self, horizon: int = 1) -> ResearchDataset:
        """Build a dataset with binary direction labels (1 / 0)."""
        result = LabelBuilder(self.close).build_binary(horizon)
        return self._assemble(result.values, result.name, horizon=horizon)

    def build_with_multiclass(
        self,
        horizon: int = 1,
        threshold: float = 0.0,
    ) -> ResearchDataset:
        """Build a dataset with multi-class direction labels (-1 / 0 / 1)."""
        result = LabelBuilder(self.close).build_multiclass(horizon, threshold)
        return self._assemble(
            result.values,
            result.name,
            horizon=horizon,
            extra_metadata={"threshold": threshold},
        )

    def build_custom(
        self,
        labels: Sequence[float | None],
        label_name: str = "custom",
        horizon: int | None = None,
    ) -> ResearchDataset:
        """Build a dataset from an explicit label sequence.

        Rows where the label or any feature is undefined (``None`` / NaN)
        are removed so the final dataset contains only complete, aligned
        observations.
        """
        if not isinstance(label_name, str) or not label_name:
            raise ValueError("label_name must be a non-empty string")
        return self._assemble(list(labels), label_name, horizon=horizon)


__all__ = ["DatasetBuilder"]
