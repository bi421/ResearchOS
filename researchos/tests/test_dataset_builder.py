"""
Tests: Dataset Builder Engine.

Covers contracts, the builder, alignment / trimming, validation, export,
determinism, edge cases, and market regimes.  All data generation is
deterministic (no randomness).
"""

from __future__ import annotations

import csv
import io
import json
import math
import unittest
from dataclasses import FrozenInstanceError

from researchos.quant_engine.machine_learning.dataset_builder import DatasetBuilder
from researchos.quant_engine.machine_learning.dataset_contracts import (
    BUILDER_VERSION,
    DATASET_VERSION,
    ResearchDataset,
)
from researchos.quant_engine.machine_learning.dataset_export import (
    to_csv,
    to_dict,
    to_json,
)
from researchos.quant_engine.machine_learning.dataset_validation import (
    validate_alignment,
    validate_dataset,
    validate_feature_count,
    validate_no_nan,
    validate_no_none,
    validate_shapes,
)
from researchos.quant_engine.machine_learning.label_builder import LabelBuilder

# ---------------------------------------------------------------------------
# deterministic data generators
# ---------------------------------------------------------------------------


def close_up(n: int = 120, start: float = 100.0, step: float = 0.5):
    """Strictly increasing close series."""
    return [start + i * step for i in range(n)]


def close_down(n: int = 120, start: float = 200.0, step: float = -0.5):
    """Strictly decreasing close series."""
    return [start + i * step for i in range(n)]


def close_flat(n: int = 120, value: float = 100.0):
    """Constant close series."""
    return [value] * n


def close_volatile(n: int = 120, base: float = 100.0, amp: float = 2.0):
    """Deterministic zig-zag series (non-zero volatility)."""
    out = []
    for i in range(n):
        phase = i % 20
        if phase < 10:
            out.append(base - amp + phase * (2 * amp / 9.0))
        else:
            out.append(base - amp + (20 - phase) * (2 * amp / 9.0))
    return out


def ohlcv(close, vol_base: float = 1000.0, vol_step: float = 10.0):
    """Derive high / low / volume from a close series."""
    high = [c + 1.0 for c in close]
    low = [c - 1.0 for c in close]
    volume = [vol_base + i * vol_step for i in range(len(close))]
    return high, low, close, volume


# Maximum feature warmup across all FeatureBuilder columns (vol_regime 20/60).
WARMUP = 60


def dataset(n=120, series=close_up, horizon=1):
    """Shortcut: build a future-return dataset."""
    close = series(n)
    high, low, cl, vol = ohlcv(close)
    return DatasetBuilder(cl, high, low, vol).build_with_future_return(horizon)


# ---------------------------------------------------------------------------
# contracts
# ---------------------------------------------------------------------------


class TestResearchDatasetContract(unittest.TestCase):
    def test_is_frozen(self):
        fs = dataset()
        with self.assertRaises(FrozenInstanceError):
            fs.sample_count = 99  # type: ignore[misc]

    def test_has_all_fields(self):
        fs = dataset()
        for attr in (
            "feature_names",
            "features",
            "labels",
            "metadata",
            "sample_count",
            "feature_count",
            "label_name",
            "created_at",
            "version",
        ):
            self.assertTrue(hasattr(fs, attr), attr)

    def test_default_created_at_none(self):
        fs = dataset()
        self.assertIsNone(fs.created_at)

    def test_default_version_is_dataset_version(self):
        fs = dataset()
        self.assertEqual(fs.version, DATASET_VERSION)

    def test_version_is_str(self):
        self.assertIsInstance(dataset().version, str)

    def test_features_is_tuple(self):
        fs = dataset()
        self.assertIsInstance(fs.features, tuple)

    def test_labels_is_tuple(self):
        fs = dataset()
        self.assertIsInstance(fs.labels, tuple)

    def test_feature_names_is_tuple(self):
        fs = dataset()
        self.assertIsInstance(fs.feature_names, tuple)

    def test_metadata_immutable(self):
        fs = ResearchDataset(feature_names=(), features=(), labels=(), metadata={})
        with self.assertRaises(TypeError):
            fs.metadata["x"] = 1  # type: ignore[index]

    def test_deep_equality(self):
        a = dataset()
        b = dataset()
        self.assertEqual(a, b)

    def test_hashable(self):
        hash(dataset())


# ---------------------------------------------------------------------------
# basic builder behavior
# ---------------------------------------------------------------------------


class TestDatasetBuilderBasic(unittest.TestCase):
    def test_constructor_accepts_ohlcv(self):
        close = close_up()
        high, low, cl, vol = ohlcv(close)
        db = DatasetBuilder(cl, high, low, vol)
        self.assertIsInstance(db, DatasetBuilder)

    def test_constructor_requires_equal_lengths(self):
        with self.assertRaises(ValueError):
            DatasetBuilder([1.0, 2.0], [1.0], [1.0, 2.0], [1.0, 2.0])

    def test_constructor_accepts_tuples(self):
        close = close_up(80)
        high, low, cl, vol = ohlcv(close)
        db = DatasetBuilder(tuple(cl), tuple(high), tuple(low), tuple(vol))
        fs = db.build()
        self.assertGreater(fs.sample_count, 0)

    def test_build_returns_research_dataset(self):
        fs = dataset()
        self.assertIsInstance(fs, ResearchDataset)

    def test_build_default_horizon_is_one(self):
        close = close_up()
        high, low, cl, vol = ohlcv(close)
        fs = DatasetBuilder(cl, high, low, vol).build()
        self.assertEqual(fs.label_name, "future_return")
        self.assertEqual(fs.metadata.get("horizon"), 1)

    def test_build_with_future_return_label_name(self):
        fs = dataset()
        self.assertEqual(fs.label_name, "future_return")

    def test_build_feature_count_positive(self):
        fs = dataset()
        self.assertGreater(fs.feature_count, 0)

    def test_build_sample_count_expected(self):
        fs = dataset(n=120, horizon=1)
        self.assertEqual(fs.sample_count, 120 - WARMUP - 1)

    def test_build_no_none_values(self):
        fs = dataset()
        for row in fs.features:
            for v in row:
                self.assertIsNotNone(v)
        for v in fs.labels:
            self.assertIsNotNone(v)

    def test_build_no_nan_values(self):
        fs = dataset()
        for row in fs.features:
            for v in row:
                self.assertFalse(isinstance(v, float) and math.isnan(v))
        for v in fs.labels:
            self.assertFalse(isinstance(v, float) and math.isnan(v))

    def test_build_metadata_dataset_version(self):
        fs = dataset()
        self.assertEqual(fs.metadata["dataset_version"], DATASET_VERSION)

    def test_build_metadata_builder_version(self):
        fs = dataset()
        self.assertEqual(fs.metadata["builder_version"], BUILDER_VERSION)


# ---------------------------------------------------------------------------
# binary labels
# ---------------------------------------------------------------------------


class TestBinaryLabels(unittest.TestCase):
    def test_binary_label_name(self):
        close = close_up()
        high, low, cl, vol = ohlcv(close)
        fs = DatasetBuilder(cl, high, low, vol).build_with_binary_labels(1)
        self.assertEqual(fs.label_name, "binary")

    def test_binary_values_in_set(self):
        fs = dataset()
        high, low, cl, vol = ohlcv(close_up())
        fs = DatasetBuilder(cl, high, low, vol).build_with_binary_labels(1)
        for v in fs.labels:
            self.assertIn(v, (0.0, 1.0))

    def test_binary_uptrend_ones(self):
        close = close_up()
        high, low, cl, vol = ohlcv(close)
        fs = DatasetBuilder(cl, high, low, vol).build_with_binary_labels(1)
        for v in fs.labels:
            self.assertEqual(v, 1.0)

    def test_binary_downtrend_zeros(self):
        close = close_down()
        high, low, cl, vol = ohlcv(close)
        fs = DatasetBuilder(cl, high, low, vol).build_with_binary_labels(1)
        for v in fs.labels:
            self.assertEqual(v, 0.0)

    def test_binary_sample_count_expected(self):
        high, low, cl, vol = ohlcv(close_up())
        fs = DatasetBuilder(cl, high, low, vol).build_with_binary_labels(1)
        self.assertEqual(fs.sample_count, 120 - WARMUP - 1)

    def test_binary_horizon_metadata(self):
        high, low, cl, vol = ohlcv(close_up())
        fs = DatasetBuilder(cl, high, low, vol).build_with_binary_labels(5)
        self.assertEqual(fs.metadata["horizon"], 5)

    def test_binary_horizon_effect(self):
        high, low, cl, vol = ohlcv(close_up())
        fs = DatasetBuilder(cl, high, low, vol).build_with_binary_labels(10)
        # labels valid for i in 0..109, feature rows valid from 60
        self.assertEqual(fs.sample_count, 120 - WARMUP - 10)

    def test_binary_determinism(self):
        high, low, cl, vol = ohlcv(close_up())
        a = DatasetBuilder(cl, high, low, vol).build_with_binary_labels(1)
        b = DatasetBuilder(cl, high, low, vol).build_with_binary_labels(1)
        self.assertEqual(a.labels, b.labels)

    def test_binary_alignment(self):
        high, low, cl, vol = ohlcv(close_up())
        fs = DatasetBuilder(cl, high, low, vol).build_with_binary_labels(1)
        validate_alignment(fs)


# ---------------------------------------------------------------------------
# future return labels
# ---------------------------------------------------------------------------


class TestFutureReturn(unittest.TestCase):
    def test_future_return_name(self):
        fs = dataset()
        self.assertEqual(fs.label_name, "future_return")

    def test_future_return_positive_series(self):
        fs = dataset(series=close_up)
        for v in fs.labels:
            self.assertGreater(v, 0.0)

    def test_future_return_negative_series(self):
        fs = dataset(series=close_down)
        for v in fs.labels:
            self.assertLess(v, 0.0)

    def test_future_return_values_match_formula(self):
        close = close_up()
        high, low, cl, vol = ohlcv(close)
        fs = DatasetBuilder(cl, high, low, vol).build_with_future_return(1)
        for i, label in enumerate(fs.labels):
            idx = WARMUP + i
            expected = (close[idx + 1] - close[idx]) / close[idx]
            self.assertAlmostEqual(label, expected, places=10)

    def test_future_return_horizon_metadata(self):
        high, low, cl, vol = ohlcv(close_up())
        fs = DatasetBuilder(cl, high, low, vol).build_with_future_return(7)
        self.assertEqual(fs.metadata["horizon"], 7)

    def test_future_return_horizon_larger(self):
        high, low, cl, vol = ohlcv(close_up())
        fs10 = DatasetBuilder(cl, high, low, vol).build_with_future_return(10)
        fs1 = DatasetBuilder(cl, high, low, vol).build_with_future_return(1)
        self.assertLess(fs10.sample_count, fs1.sample_count)

    def test_future_return_tail_trimming(self):
        close = close_up()
        high, low, cl, vol = ohlcv(close)
        n = len(close)
        fs = DatasetBuilder(cl, high, low, vol).build_with_future_return(1)
        # last aligned label corresponds to original index n-2
        last_index = WARMUP + fs.sample_count - 1
        self.assertEqual(last_index, n - 2)

    def test_future_return_determinism(self):
        a = dataset()
        b = dataset()
        self.assertEqual(a.labels, b.labels)
        self.assertEqual(a.features, b.features)


# ---------------------------------------------------------------------------
# multiclass labels
# ---------------------------------------------------------------------------


class TestMulticlass(unittest.TestCase):
    def test_multiclass_name(self):
        high, low, cl, vol = ohlcv(close_up())
        fs = DatasetBuilder(cl, high, low, vol).build_with_multiclass(1, 0.0)
        self.assertEqual(fs.label_name, "multiclass")

    def test_multiclass_values_in_set(self):
        high, low, cl, vol = ohlcv(close_volatile())
        fs = DatasetBuilder(cl, high, low, vol).build_with_multiclass(1, 0.0)
        for v in fs.labels:
            self.assertIn(v, (-1.0, 0.0, 1.0))

    def test_multiclass_uptrend_ones(self):
        high, low, cl, vol = ohlcv(close_up())
        fs = DatasetBuilder(cl, high, low, vol).build_with_multiclass(1, 0.0)
        for v in fs.labels:
            self.assertEqual(v, 1.0)

    def test_multiclass_downtrend_negatives(self):
        high, low, cl, vol = ohlcv(close_down())
        fs = DatasetBuilder(cl, high, low, vol).build_with_multiclass(1, 0.0)
        for v in fs.labels:
            self.assertEqual(v, -1.0)

    def test_multiclass_threshold_metadata(self):
        high, low, cl, vol = ohlcv(close_up())
        fs = DatasetBuilder(cl, high, low, vol).build_with_multiclass(1, 0.01)
        self.assertEqual(fs.metadata["threshold"], 0.01)

    def test_multiclass_threshold_changes_labels(self):
        # tiny step series: relative move is small; a large threshold maps
        # everything to neutral/non-positive
        close = close_up(n=200, step=0.01)
        high, low, cl, vol = ohlcv(close)
        fs_small = DatasetBuilder(cl, high, low, vol).build_with_multiclass(1, 0.0001)
        self.assertTrue(all(v <= 0.0 for v in fs_small.labels))

    def test_multiclass_alignment(self):
        high, low, cl, vol = ohlcv(close_volatile())
        fs = DatasetBuilder(cl, high, low, vol).build_with_multiclass(1)
        self.assertEqual(len(fs.features), len(fs.labels))

    def test_multiclass_determinism(self):
        high, low, cl, vol = ohlcv(close_volatile())
        a = DatasetBuilder(cl, high, low, vol).build_with_multiclass(1)
        b = DatasetBuilder(cl, high, low, vol).build_with_multiclass(1)
        self.assertEqual(a.labels, b.labels)


# ---------------------------------------------------------------------------
# custom labels
# ---------------------------------------------------------------------------


class TestCustomLabels(unittest.TestCase):
    def test_custom_default_name(self):
        close = close_up()
        high, low, cl, vol = ohlcv(close)
        fs = DatasetBuilder(cl, high, low, vol).build_custom([1.0] * len(close))
        self.assertEqual(fs.label_name, "custom")

    def test_custom_custom_name(self):
        close = close_up()
        high, low, cl, vol = ohlcv(close)
        fs = DatasetBuilder(cl, high, low, vol).build_custom(
            [1.0] * len(close), label_name="my_target"
        )
        self.assertEqual(fs.label_name, "my_target")

    def test_custom_values_preserved(self):
        close = close_up()
        high, low, cl, vol = ohlcv(close)
        labels = [float(i) for i in range(len(close))]
        fs = DatasetBuilder(cl, high, low, vol).build_custom(labels)
        expected = [float(i) for i in range(WARMUP, len(close))]
        self.assertEqual(list(fs.labels), expected)

    def test_custom_alignment(self):
        close = close_up()
        high, low, cl, vol = ohlcv(close)
        labels = [1.0] * len(close)
        fs = DatasetBuilder(cl, high, low, vol).build_custom(labels)
        self.assertEqual(len(fs.features), len(fs.labels))
        self.assertEqual(len(fs.labels), len(close) - WARMUP)

    def test_custom_empty_label_name_raises(self):
        close = close_up()
        high, low, cl, vol = ohlcv(close)
        with self.assertRaises(ValueError):
            DatasetBuilder(cl, high, low, vol).build_custom(
                [1.0] * len(close), label_name=""
            )

    def test_custom_with_none_removes_rows(self):
        close = close_up()
        high, low, cl, vol = ohlcv(close)
        labels = [None] * 70 + [1.0] * (len(close) - 70)
        fs = DatasetBuilder(cl, high, low, vol).build_custom(labels)
        # overlap between valid feature rows [60, 119] and valid labels [70, 119]
        self.assertEqual(fs.sample_count, len(close) - 70)

    def test_custom_with_nan_removes_rows(self):
        close = close_up()
        high, low, cl, vol = ohlcv(close)
        labels = [float("nan")] * 70 + [1.0] * (len(close) - 70)
        fs = DatasetBuilder(cl, high, low, vol).build_custom(labels)
        self.assertEqual(fs.sample_count, len(close) - 70)

    def test_custom_determinism(self):
        close = close_up()
        high, low, cl, vol = ohlcv(close)
        labels = [float(i % 3) for i in range(len(close))]
        a = DatasetBuilder(cl, high, low, vol).build_custom(labels)
        b = DatasetBuilder(cl, high, low, vol).build_custom(labels)
        self.assertEqual(a, b)


# ---------------------------------------------------------------------------
# alignment
# ---------------------------------------------------------------------------


class TestAlignment(unittest.TestCase):
    def test_features_labels_same_length(self):
        fs = dataset()
        self.assertEqual(len(fs.features), len(fs.labels))

    def test_row_width_matches_feature_count(self):
        fs = dataset()
        for row in fs.features:
            self.assertEqual(len(row), fs.feature_count)

    def test_sample_count_matches_lengths(self):
        fs = dataset()
        self.assertEqual(fs.sample_count, len(fs.features))
        self.assertEqual(fs.sample_count, len(fs.labels))

    def test_feature_names_match_columns(self):
        fs = dataset()
        self.assertEqual(len(fs.feature_names), fs.feature_count)

    def test_alignment_validation_passes(self):
        fs = dataset()
        validate_alignment(fs)

    def test_first_label_maps_to_warmup_index(self):
        close = close_up()
        high, low, cl, vol = ohlcv(close)
        result = LabelBuilder(cl).build_future_return(1)
        fs = DatasetBuilder(cl, high, low, vol).build_with_future_return(1)
        self.assertEqual(fs.labels[0], result.values[WARMUP])

    def test_last_label_maps_to_trimmed_tail(self):
        close = close_up()
        high, low, cl, vol = ohlcv(close)
        result = LabelBuilder(cl).build_future_return(1)
        fs = DatasetBuilder(cl, high, low, vol).build_with_future_return(1)
        self.assertEqual(fs.labels[-1], result.values[len(close) - 2])

    def test_features_are_tuples(self):
        fs = dataset()
        for row in fs.features:
            self.assertIsInstance(row, tuple)

    def test_sparse_labels_aligned(self):
        close = close_up()
        high, low, cl, vol = ohlcv(close)
        labels = [None if i % 2 else 1.0 for i in range(len(close))]
        fs = DatasetBuilder(cl, high, low, vol).build_custom(labels)
        # valid labels every other index from max(warmup, first even) onward
        first_even = WARMUP if WARMUP % 2 == 0 else WARMUP + 1
        expected = (len(close) - first_even + 1) // 2
        self.assertEqual(fs.sample_count, expected)


# ---------------------------------------------------------------------------
# warmup / tail trimming
# ---------------------------------------------------------------------------


class TestWarmupTailTrimming(unittest.TestCase):
    def test_warmup_trimmed_deep_series(self):
        fs = dataset(n=500, horizon=1)
        self.assertEqual(fs.sample_count, 500 - WARMUP - 1)

    def test_tail_trimmed_horizon(self):
        fs = dataset(n=120, horizon=1)
        self.assertEqual(fs.sample_count, 120 - WARMUP - 1)

    def test_trim_increases_with_horizon(self):
        h1 = dataset(n=120, horizon=1)
        h20 = dataset(n=120, horizon=20)
        self.assertEqual(h20.sample_count, 120 - WARMUP - 20)
        self.assertLess(h20.sample_count, h1.sample_count)

    def test_no_na_in_final(self):
        fs = dataset(n=500, horizon=10)
        for row in fs.features:
            for v in row:
                self.assertIsNotNone(v)
                self.assertFalse(isinstance(v, float) and math.isnan(v))

    def test_short_series_zero_rows(self):
        fs = dataset(n=61, horizon=1)
        self.assertEqual(fs.sample_count, 0)

    def test_empty_series_zero_rows(self):
        close = []
        high, low, cl, vol = ohlcv(close)
        fs = DatasetBuilder(cl, high, low, vol).build()
        self.assertEqual(fs.sample_count, 0)

    def test_horizon_beyond_length_zero_rows(self):
        close = close_up(120)
        high, low, cl, vol = ohlcv(close)
        fs = DatasetBuilder(cl, high, low, vol).build_with_future_return(120)
        self.assertEqual(fs.sample_count, 0)

    def test_single_row_zero_rows(self):
        close = close_up(1)
        high, low, cl, vol = ohlcv(close)
        fs = DatasetBuilder(cl, high, low, vol).build()
        self.assertEqual(fs.sample_count, 0)


# ---------------------------------------------------------------------------
# validation
# ---------------------------------------------------------------------------


def _mk(features=(), labels=(), sample_count=0, feature_count=0, names=()):
    return ResearchDataset(
        feature_names=tuple(names),
        features=tuple(features),
        labels=tuple(labels),
        metadata={},
        sample_count=sample_count,
        feature_count=feature_count,
        label_name="x",
    )


class TestValidation(unittest.TestCase):
    def test_validate_dataset_ok(self):
        fs = dataset()
        validate_dataset(fs)

    def test_validate_wrong_type(self):
        with self.assertRaises(TypeError):
            validate_dataset({"a": 1})

    def test_validate_shapes_features_mismatch(self):
        ds = _mk(features=((1.0,),), labels=(1.0,), sample_count=2, feature_count=1, names=("a",))
        with self.assertRaises(ValueError):
            validate_shapes(ds)

    def test_validate_shapes_labels_mismatch(self):
        ds = _mk(features=((1.0,),), labels=(1.0, 2.0), sample_count=1, feature_count=1, names=("a",))
        with self.assertRaises(ValueError):
            validate_shapes(ds)

    def test_validate_feature_count_row(self):
        ds = _mk(
            features=((1.0, 2.0),),
            labels=(1.0,),
            sample_count=1,
            feature_count=1,
            names=("a",),
        )
        with self.assertRaises(ValueError):
            validate_feature_count(ds)

    def test_validate_feature_count_names(self):
        ds = _mk(
            features=((1.0,),),
            labels=(1.0,),
            sample_count=1,
            feature_count=1,
            names=("a", "b"),
        )
        with self.assertRaises(ValueError):
            validate_feature_count(ds)

    def test_validate_no_none_features(self):
        ds = _mk(features=((None,),), labels=(1.0,), sample_count=1, feature_count=1, names=("a",))
        with self.assertRaises(ValueError):
            validate_no_none(ds)

    def test_validate_no_none_labels(self):
        ds = _mk(features=((1.0,),), labels=(None,), sample_count=1, feature_count=1, names=("a",))
        with self.assertRaises(ValueError):
            validate_no_none(ds)

    def test_validate_no_nan_features(self):
        ds = _mk(
            features=((float("nan"),),),
            labels=(1.0,),
            sample_count=1,
            feature_count=1,
            names=("a",),
        )
        with self.assertRaises(ValueError):
            validate_no_nan(ds)

    def test_validate_no_nan_labels(self):
        ds = _mk(
            features=((1.0,),),
            labels=(float("nan"),),
            sample_count=1,
            feature_count=1,
            names=("a",),
        )
        with self.assertRaises(ValueError):
            validate_no_nan(ds)

    def test_validate_alignment_mismatch(self):
        ds = _mk(
            features=((1.0,), (2.0,)),
            labels=(1.0,),
            sample_count=1,
            feature_count=1,
            names=("a",),
        )
        with self.assertRaises(ValueError):
            validate_alignment(ds)

    def test_validate_descriptive_message(self):
        ds = _mk(features=((None,),), labels=(1.0,), sample_count=1, feature_count=1, names=("a",))
        with self.assertRaises(ValueError) as ctx:
            validate_no_none(ds)
        self.assertIn("None", str(ctx.exception))


# ---------------------------------------------------------------------------
# export
# ---------------------------------------------------------------------------


class TestExport(unittest.TestCase):
    def test_to_dict_keys(self):
        d = to_dict(dataset())
        for key in (
            "feature_names",
            "features",
            "labels",
            "metadata",
            "sample_count",
            "feature_count",
            "label_name",
            "created_at",
            "version",
        ):
            self.assertIn(key, d)

    def test_to_dict_values(self):
        fs = dataset()
        d = to_dict(fs)
        self.assertEqual(d["sample_count"], fs.sample_count)
        self.assertEqual(d["feature_count"], fs.feature_count)
        self.assertEqual(d["label_name"], fs.label_name)
        self.assertEqual(d["features"], [list(r) for r in fs.features])
        self.assertEqual(d["labels"], list(fs.labels))

    def test_to_dict_deterministic(self):
        self.assertEqual(to_dict(dataset()), to_dict(dataset()))

    def test_to_json_string(self):
        self.assertIsInstance(to_json(dataset()), str)

    def test_to_json_parse(self):
        parsed = json.loads(to_json(dataset()))
        self.assertIn("features", parsed)
        self.assertIn("labels", parsed)
        self.assertEqual(parsed["sample_count"], dataset().sample_count)

    def test_to_json_sort_keys_deterministic(self):
        self.assertEqual(to_json(dataset()), to_json(dataset()))

    def test_to_json_roundtrip(self):
        fs = dataset()
        parsed = json.loads(to_json(fs))
        self.assertEqual(parsed["features"], [list(r) for r in fs.features])

    def test_to_csv_header(self):
        fs = dataset()
        text = to_csv(fs)
        reader = csv.reader(io.StringIO(text))
        header = next(reader)
        self.assertEqual(header, list(fs.feature_names) + [fs.label_name])

    def test_to_csv_rows(self):
        fs = dataset()
        text = to_csv(fs)
        rows = list(csv.reader(io.StringIO(text)))
        self.assertEqual(len(rows), fs.sample_count + 1)
        self.assertEqual(len(rows[1]), fs.feature_count + 1)

    def test_to_csv_roundtrip(self):
        fs = dataset()
        rows = list(csv.reader(io.StringIO(to_csv(fs))))
        header = rows[0]
        self.assertEqual(header[-1], fs.label_name)
        for i, row in enumerate(rows[1:]):
            values = [float(v) for v in row]
            self.assertEqual(values[: fs.feature_count], list(fs.features[i]))
            self.assertEqual(values[-1], fs.labels[i])

    def test_to_csv_empty_dataset(self):
        close = []
        high, low, cl, vol = ohlcv(close)
        fs = DatasetBuilder(cl, high, low, vol).build()
        rows = list(csv.reader(io.StringIO(to_csv(fs))))
        self.assertEqual(len(rows), 1)  # header only


# ---------------------------------------------------------------------------
# determinism
# ---------------------------------------------------------------------------


class TestDeterminism(unittest.TestCase):
    def test_build_repeatable(self):
        a = dataset()
        b = dataset()
        self.assertEqual(a.features, b.features)
        self.assertEqual(a.labels, b.labels)

    def test_binary_repeatable(self):
        high, low, cl, vol = ohlcv(close_volatile())
        a = DatasetBuilder(cl, high, low, vol).build_with_binary_labels(3)
        b = DatasetBuilder(cl, high, low, vol).build_with_binary_labels(3)
        self.assertEqual(a, b)

    def test_multiclass_repeatable(self):
        high, low, cl, vol = ohlcv(close_volatile())
        a = DatasetBuilder(cl, high, low, vol).build_with_multiclass(3, 0.5)
        b = DatasetBuilder(cl, high, low, vol).build_with_multiclass(3, 0.5)
        self.assertEqual(a, b)

    def test_future_return_repeatable(self):
        a = dataset(n=300, series=close_volatile, horizon=5)
        b = dataset(n=300, series=close_volatile, horizon=5)
        self.assertEqual(a, b)

    def test_custom_repeatable(self):
        close = close_volatile()
        high, low, cl, vol = ohlcv(close)
        labels = [1.0 if i % 2 else -1.0 for i in range(len(close))]
        a = DatasetBuilder(cl, high, low, vol).build_custom(labels, "z")
        b = DatasetBuilder(cl, high, low, vol).build_custom(labels, "z")
        self.assertEqual(a, b)

    def test_feature_names_stable(self):
        self.assertEqual(dataset().feature_names, dataset().feature_names)

    def test_metadata_stable(self):
        self.assertEqual(dataset().metadata, dataset().metadata)

    def test_deep_equal_frozen(self):
        a = dataset()
        b = dataset()
        self.assertEqual(a, b)
        self.assertEqual(hash(a), hash(b))


# ---------------------------------------------------------------------------
# edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases(unittest.TestCase):
    def test_empty_inputs(self):
        close = []
        high, low, cl, vol = ohlcv(close)
        fs = DatasetBuilder(cl, high, low, vol).build()
        self.assertEqual(fs.sample_count, 0)

    def test_single_row(self):
        close = close_up(1)
        high, low, cl, vol = ohlcv(close)
        fs = DatasetBuilder(cl, high, low, vol).build()
        self.assertEqual(fs.sample_count, 0)

    def test_two_rows(self):
        close = close_up(2)
        high, low, cl, vol = ohlcv(close)
        fs = DatasetBuilder(cl, high, low, vol).build()
        self.assertEqual(fs.sample_count, 0)

    def test_small_n_65(self):
        fs = dataset(n=65, horizon=1)
        self.assertEqual(fs.sample_count, 4)

    def test_small_n_80(self):
        fs = dataset(n=80, horizon=1)
        self.assertEqual(fs.sample_count, 19)

    def test_large_n_500(self):
        fs = dataset(n=500, horizon=1)
        self.assertEqual(fs.sample_count, 439)
        self.assertEqual(fs.feature_count, 19)

    def test_constant_prices_empty(self):
        close = close_flat()
        high, low, cl, vol = ohlcv(close)
        fs = DatasetBuilder(cl, high, low, vol).build()
        # vol_ratio stays None for flat series -> all rows dropped
        self.assertEqual(fs.sample_count, 0)

    def test_constant_prices_deterministic(self):
        close = close_flat()
        high, low, cl, vol = ohlcv(close)
        a = DatasetBuilder(cl, high, low, vol).build()
        b = DatasetBuilder(cl, high, low, vol).build()
        self.assertEqual(a, b)

    def test_zero_volume_empty(self):
        close = close_up()
        high, low, cl, vol = ohlcv(close)
        vol = [0.0] * len(close)
        fs = DatasetBuilder(cl, high, low, vol).build()
        # vwap stays None for zero volume -> all rows dropped
        self.assertEqual(fs.sample_count, 0)

    def test_mismatched_lengths_raises(self):
        with self.assertRaises(ValueError):
            DatasetBuilder([1.0] * 10, [1.0] * 10, [1.0] * 10, [1.0] * 9)


# ---------------------------------------------------------------------------
# market regimes
# ---------------------------------------------------------------------------


class TestMarketRegimes(unittest.TestCase):
    def test_uptrend_builds(self):
        fs = dataset(series=close_up)
        self.assertGreater(fs.sample_count, 0)

    def test_uptrend_sample_count(self):
        fs = dataset(series=close_up, n=120)
        self.assertEqual(fs.sample_count, 120 - WARMUP - 1)

    def test_downtrend_builds(self):
        fs = dataset(series=close_down)
        self.assertGreater(fs.sample_count, 0)

    def test_downtrend_sample_count(self):
        fs = dataset(series=close_down, n=120)
        self.assertEqual(fs.sample_count, 120 - WARMUP - 1)

    def test_volatile_builds(self):
        fs = dataset(series=close_volatile)
        self.assertGreater(fs.sample_count, 0)

    def test_volatile_sample_count(self):
        fs = dataset(series=close_volatile, n=120)
        self.assertEqual(fs.sample_count, 120 - WARMUP - 1)

    def test_uptrend_binary_labels_ones(self):
        high, low, cl, vol = ohlcv(close_up())
        fs = DatasetBuilder(cl, high, low, vol).build_with_binary_labels(1)
        self.assertTrue(all(v == 1.0 for v in fs.labels))

    def test_downtrend_binary_labels_zeros(self):
        high, low, cl, vol = ohlcv(close_down())
        fs = DatasetBuilder(cl, high, low, vol).build_with_binary_labels(1)
        self.assertTrue(all(v == 0.0 for v in fs.labels))

    def test_volatile_custom_labels_ok(self):
        close = close_volatile()
        high, low, cl, vol = ohlcv(close)
        labels = [1.0 if i % 2 else 0.0 for i in range(len(close))]
        fs = DatasetBuilder(cl, high, low, vol).build_custom(labels)
        self.assertGreater(fs.sample_count, 0)
        self.assertEqual(len(fs.features), len(fs.labels))

    def test_volatile_validate_full(self):
        fs = dataset(series=close_volatile)
        validate_dataset(fs)


# ---------------------------------------------------------------------------
# metadata
# ---------------------------------------------------------------------------


class TestMetadata(unittest.TestCase):
    def test_feature_count_metadata(self):
        fs = dataset()
        self.assertEqual(fs.metadata["feature_count"], fs.feature_count)

    def test_sample_count_metadata(self):
        fs = dataset()
        self.assertEqual(fs.metadata["sample_count"], fs.sample_count)

    def test_label_name_metadata(self):
        fs = dataset()
        self.assertEqual(fs.metadata["label_name"], fs.label_name)

    def test_feature_names_metadata(self):
        fs = dataset()
        self.assertEqual(fs.metadata["feature_names"], list(fs.feature_names))

    def test_horizon_metadata(self):
        fs = dataset(horizon=4)
        self.assertEqual(fs.metadata["horizon"], 4)

    def test_custom_horizon_metadata(self):
        close = close_up()
        high, low, cl, vol = ohlcv(close)
        fs = DatasetBuilder(cl, high, low, vol).build_custom(
            [1.0] * len(close), label_name="x", horizon=9
        )
        self.assertEqual(fs.metadata["horizon"], 9)


if __name__ == "__main__":
    unittest.main()

