"""Feature and label construction for the Phase 5.2 rebuild.

This module sits strictly downstream of the deterministic daily common-data
boundary.  It constructs the frozen ResearchOS price features and the Phase
5.2 macro features, then applies the existing forward-return label semantics.

Timing contract:
    A row for day ``t`` is evaluated after the UTC day has closed.  Therefore
    same-day end-of-day DXY/US10Y/VIX observations are observable features.
    No feature uses ``t+1`` or later market information.

The output deliberately keeps the five Phase 5.2 feature-set variants
separate so each experiment receives an isolated feature matrix.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from researchos.experiments.phase52.macro_features import MacroFeatureBuilder
from researchos.quant_engine.machine_learning.features import FeatureBuilder
from researchos.quant_engine.machine_learning.labels import multiclass_label

from .daily_dataset import DailyObservation
from .feature_contract import (
    FEATURE_SET_NAMES,
    MACRO_FEATURES_PER_SYMBOL,
    MACRO_SYMBOLS,
    Phase52FeatureContract,
    PRICE_FEATURE_NAMES,
)


@dataclass(frozen=True)
class FeatureDataset:
    """Immutable, deterministic feature/label dataset with source-day identity."""

    feature_set: str
    feature_names: tuple[str, ...]
    rows: tuple[tuple[float, ...], ...]
    labels: tuple[int, ...]
    source_days: tuple[str, ...]
    prediction_timestamps: tuple[str, ...]
    metadata: dict[str, object]

    @property
    def sample_count(self) -> int:
        return len(self.rows)

    @property
    def feature_count(self) -> int:
        return len(self.feature_names)


def _prediction_timestamp(day: str) -> str:
    dt = datetime.fromisoformat(day).replace(tzinfo=timezone.utc) + timedelta(days=1)
    return dt.isoformat().replace("+00:00", "Z")


def _selected_macro_columns(
    macro_data: tuple[tuple[float | None, ...], ...],
    macro_names: tuple[str, ...],
    feature_set: str,
) -> tuple[tuple[str, ...], tuple[tuple[float | None, ...], ...]]:
    selected_symbols = {
        "PRICE_DXY": ("DXY",),
        "PRICE_US10Y": ("US10Y",),
        "PRICE_VIX": ("VIX",),
        "PRICE_ALL": MACRO_SYMBOLS,
    }.get(feature_set, ())
    if not selected_symbols:
        return (), tuple(() for _ in macro_data)
    wanted = tuple(
        f"macro_{symbol}_{suffix}"
        for symbol in selected_symbols
        for suffix in MACRO_FEATURES_PER_SYMBOL
    )
    indices = [macro_names.index(name) for name in wanted]
    rows = tuple(tuple(row[i] for i in indices) for row in macro_data)
    return wanted, rows


def build_feature_dataset(
    observations: tuple[DailyObservation, ...],
    feature_set: str,
    contract: Phase52FeatureContract | None = None,
) -> FeatureDataset:
    """Build one Phase 5.2 feature-set variant from daily common observations."""
    contract = contract or Phase52FeatureContract()
    if feature_set not in FEATURE_SET_NAMES:
        raise ValueError(f"unsupported feature set: {feature_set}")
    if len(observations) < contract.minimum_samples:
        raise ValueError(
            f"common dataset has {len(observations)} rows; "
            f"minimum required is {contract.minimum_samples}"
        )

    close = [o.close for o in observations]
    high = [o.high for o in observations]
    low = [o.low for o in observations]
    volume = [o.tick_volume for o in observations]
    price_features = FeatureBuilder(close, high, low, volume).build(drop_na=False)

    price_names = tuple(price_features.feature_names)
    if price_names != PRICE_FEATURE_NAMES:
        raise AssertionError("frozen price feature contract changed unexpectedly")

    macro_factors = {
        "DXY": [o.dxy for o in observations],
        "US10Y": [o.us10y for o in observations],
        "VIX": [o.vix for o in observations],
    }
    macro_set = MacroFeatureBuilder(
        aligned_length=len(observations), factor_series=macro_factors
    ).build()
    macro_names, macro_rows = _selected_macro_columns(
        macro_set.data, macro_set.feature_names, feature_set
    )

    combined_names = price_names + macro_names
    labels = multiclass_label(close, contract.horizon, contract.threshold)

    rows: list[tuple[float, ...]] = []
    aligned_labels: list[int] = []
    source_days: list[str] = []
    prediction_timestamps: list[str] = []

    for i, observation in enumerate(observations):
        # The feature row at t is computed only from data through t.
        row = tuple(price_features.data[i]) + tuple(macro_rows[i])
        label = labels[i]
        if label is None:
            continue
        if any(v is None or (isinstance(v, float) and math.isnan(v)) for v in row):
            continue
        if i < contract.warmup:
            continue
        rows.append(tuple(float(v) for v in row))  # type: ignore[arg-type]
        aligned_labels.append(int(label))
        source_days.append(observation.day)
        prediction_timestamps.append(_prediction_timestamp(observation.day))

    expected_count = len(observations) - contract.warmup - contract.horizon
    if len(rows) != expected_count:
        raise AssertionError(
            f"feature/label accounting mismatch: expected {expected_count}, got {len(rows)}"
        )

    metadata: dict[str, object] = {
        "feature_set": feature_set,
        "feature_names": list(combined_names),
        "feature_count": len(combined_names),
        "common_rows": len(observations),
        "warmup_rows": contract.warmup,
        "label_horizon": contract.horizon,
        "final_usable_rows": len(rows),
        "minimum_required_rows": contract.minimum_samples,
        "train_size": contract.train_size,
        "validation_size": contract.validation_size,
        "threshold": contract.threshold,
        "prediction_timing": contract.prediction_timing,
        "label_definition": contract.label_definition,
        "final_sample_rule": contract.final_sample_rule,
        "macro_timing_contract": "same_day_eod_observation_consumed_after_day_close",
        "no_interpolation_or_forward_fill": True,
        "source_days": list(source_days),
        "prediction_timestamps": list(prediction_timestamps),
    }
    return FeatureDataset(
        feature_set=feature_set,
        feature_names=combined_names,
        rows=tuple(rows),
        labels=tuple(aligned_labels),
        source_days=tuple(source_days),
        prediction_timestamps=tuple(prediction_timestamps),
        metadata=metadata,
    )


def build_all_feature_datasets(
    observations: tuple[DailyObservation, ...],
    contract: Phase52FeatureContract | None = None,
) -> dict[str, FeatureDataset]:
    """Build all five isolated Phase 5.2 feature-set variants."""
    return {
        name: build_feature_dataset(observations, name, contract)
        for name in FEATURE_SET_NAMES
    }


__all__ = ["FeatureDataset", "build_feature_dataset", "build_all_feature_datasets"]
