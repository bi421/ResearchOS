"""
Tests: Walk-Forward Validation Engine (Q9).

Covers contracts, metrics, chronological splitting, leakage protection,
determinism, and the end-to-end validator over a real ``ResearchDataset``.
All data generation is deterministic (no randomness).
"""

from __future__ import annotations

import unittest

from researchos.quant_engine.machine_learning.dataset_builder import DatasetBuilder
from researchos.quant_engine.machine_learning.dataset_contracts import ResearchDataset
from researchos.quant_engine.validation import (
    VALIDATION_VERSION,
    Fold,
    FoldResult,
    ValidationError,
    ValidationResult,
    WalkForwardSplitter,
    WalkForwardValidator,
    accuracy,
    compute_metrics,
    directional_accuracy,
    f1_score,
    mae,
    mean_error,
    precision,
    recall,
)

# ---------------------------------------------------------------------------
# deterministic data generators
# ---------------------------------------------------------------------------


def close_series(n: int = 300, start: float = 100.0, step: float = 0.5):
    """Strictly increasing close series."""
    return [start + i * step for i in range(n)]


def _ohlcv(close):
    high = [c + 1.0 for c in close]
    low = [c - 1.0 for c in close]
    volume = [1000.0 + i * 10.0 for i in range(len(close))]
    return high, low, close, volume


def make_dataset(n: int = 300, horizon: int = 1) -> ResearchDataset:
    close = close_series(n)
    high, low, cl, vol = _ohlcv(close)
    return DatasetBuilder(cl, high, low, vol).build_with_future_return(horizon)


# ---------------------------------------------------------------------------
# contracts
# ---------------------------------------------------------------------------


class TestContracts(unittest.TestCase):
    def test_validation_version(self):
        self.assertIsInstance(VALIDATION_VERSION, str)
        self.assertEqual(VALIDATION_VERSION, "1.0.0")

    def test_validation_error_is_exception(self):
        self.assertTrue(issubclass(ValidationError, Exception))

    def test_fold_result_is_frozen(self):
        fr = FoldResult(
            fold_id=1,
            train_range=(0, 9),
            validation_range=(10, 19),
            metrics={"accuracy": 0.5},
            sample_count=10,
        )
        with self.assertRaises(Exception):
            fr.fold_id = 2  # type: ignore[misc]

    def test_fold_result_hashable(self):
        fr1 = FoldResult(1, (0, 9), (10, 19), {"accuracy": 0.5}, 10)
        fr2 = FoldResult(1, (0, 9), (10, 19), {"accuracy": 0.5}, 10)
        self.assertEqual(hash(fr1), hash(fr2))

    def test_fold_result_to_dict(self):
        fr = FoldResult(1, (0, 9), (10, 19), {"accuracy": 0.5}, 10)
        d = fr.to_dict()
        for key in ("fold_id", "train_range", "validation_range", "metrics", "sample_count"):
            self.assertIn(key, d)
        self.assertEqual(d["metrics"], {"accuracy": 0.5})

    def test_validation_result_frozen(self):
        vr = ValidationResult(
            train_size=10,
            validation_size=5,
            test_size=3,
            fold_count=1,
            fold_results=(),
            metrics={},
        )
        with self.assertRaises(Exception):
            vr.train_size = 99  # type: ignore[misc]

    def test_validation_result_to_dict(self):
        fr = FoldResult(1, (0, 9), (10, 14), {"accuracy": 0.6}, 5)
        vr = ValidationResult(
            train_size=10,
            validation_size=5,
            test_size=3,
            fold_count=1,
            fold_results=(fr,),
            metrics={"accuracy": 0.6},
        )
        d = vr.to_dict()
        self.assertEqual(d["fold_count"], 1)
        self.assertEqual(d["metrics"], {"accuracy": 0.6})
        self.assertEqual(len(d["fold_results"]), 1)


# ---------------------------------------------------------------------------
# metrics
# ---------------------------------------------------------------------------


class TestMetrics(unittest.TestCase):
    def test_accuracy_perfect(self):
        self.assertAlmostEqual(accuracy([1.0, 1.0, 0.0], [1.0, 1.0, 0.0]), 1.0)

    def test_accuracy_half(self):
        self.assertAlmostEqual(accuracy([1.0, 0.0], [1.0, 1.0]), 0.5)

    def test_accuracy_empty(self):
        self.assertEqual(accuracy([], []), 0.0)

    def test_accuracy_mismatched_length(self):
        self.assertEqual(accuracy([1.0], [1.0, 2.0]), 0.0)

    def test_precision(self):
        self.assertAlmostEqual(precision([1.0, 1.0, 0.0], [1.0, 0.0, 1.0]), 0.5)

    def test_precision_no_predicted(self):
        self.assertEqual(precision([1.0, 0.0], [0.0, 0.0]), 0.0)

    def test_recall(self):
        self.assertAlmostEqual(recall([1.0, 1.0, 0.0], [1.0, 0.0, 1.0]), 0.5)

    def test_recall_no_actual(self):
        self.assertEqual(recall([0.0, 0.0], [1.0, 1.0]), 0.0)

    def test_f1(self):
        # p = 0.5, r = 0.5 -> f1 = 0.5
        self.assertAlmostEqual(f1_score([1.0, 1.0, 0.0], [1.0, 0.0, 1.0]), 0.5)

    def test_f1_zero(self):
        self.assertEqual(f1_score([0.0, 0.0], [1.0, 1.0]), 0.0)

    def test_mae(self):
        self.assertAlmostEqual(mae([1.0, 2.0, 3.0], [2.0, 2.0, 3.0]), 1.0 / 3.0)

    def test_mean_error(self):
        # (1 + 0 + 0)/3 = 1/3 bias
        self.assertAlmostEqual(mean_error([1.0, 2.0, 3.0], [2.0, 2.0, 3.0]), 1.0 / 3.0)

    def test_directional_accuracy(self):
        self.assertAlmostEqual(directional_accuracy([1.0, -1.0, 0.5], [1.0, -1.0, -0.5]), 2.0 / 3.0)

    def test_compute_metrics_keys(self):
        m = compute_metrics([1.0, 1.0, 0.0], [1.0, 0.0, 0.0])
        for key in (
            "accuracy",
            "precision",
            "recall",
            "f1_score",
            "mean_error",
            "mae",
            "directional_accuracy",
        ):
            self.assertIn(key, m)

    def test_compute_metrics_deterministic(self):
        a = compute_metrics([1.0, 0.0, 1.0], [1.0, 1.0, 0.0])
        b = compute_metrics([1.0, 0.0, 1.0], [1.0, 1.0, 0.0])
        self.assertEqual(a, b)


# ---------------------------------------------------------------------------
# splitter
# ---------------------------------------------------------------------------


class TestSplitter(unittest.TestCase):
    def test_rejects_non_positive_train(self):
        with self.assertRaises(ValidationError):
            WalkForwardSplitter(0, 10, 10)

    def test_rejects_non_positive_validation(self):
        with self.assertRaises(ValidationError):
            WalkForwardSplitter(60, 0, 10)

    def test_rejects_non_positive_step(self):
        with self.assertRaises(ValidationError):
            WalkForwardSplitter(60, 10, 0)

    def test_rejects_negative_length(self):
        with self.assertRaises(ValidationError):
            WalkForwardSplitter(60, 10, 10).split(-5)

    def test_rejects_too_small(self):
        with self.assertRaises(ValidationError):
            WalkForwardSplitter(60, 10, 10).split(50)

    def test_fold_count(self):
        # length=239, train=80, val=20, step=20 -> 7 folds
        folds = WalkForwardSplitter(80, 20, 20).split(239)
        self.assertEqual(len(folds), 7)

    def test_fold_ids_start_at_one(self):
        folds = WalkForwardSplitter(80, 20, 20).split(239)
        self.assertEqual(folds[0].fold_id, 1)
        self.assertEqual([f.fold_id for f in folds], list(range(1, 8)))

    def test_fold_validation_size(self):
        folds = WalkForwardSplitter(80, 20, 20).split(239)
        for f in folds:
            self.assertEqual(f.validation_size, 20)

    def test_fold_train_size(self):
        folds = WalkForwardSplitter(80, 20, 20).split(239)
        for f in folds:
            self.assertEqual(f.train_size, 80)

    def test_fold_train_precedes_validation(self):
        folds = WalkForwardSplitter(80, 20, 20).split(239)
        for f in folds:
            self.assertLessEqual(f.train_end, f.validation_start)

    def test_folds_contiguous_non_overlapping(self):
        step = 20
        folds = WalkForwardSplitter(80, 20, step).split(239)
        # Validation windows are contiguous: each new validation window starts
        # exactly one index after the previous window's last index.
        for i in range(1, len(folds)):
            self.assertEqual(folds[i].validation_start, folds[i - 1].validation_end + 1)
            self.assertEqual(folds[i].train_start, folds[i - 1].train_start + step)

    def test_fold_ranges(self):
        folds = WalkForwardSplitter(80, 20, 20).split(239)
        f0 = folds[0]
        self.assertEqual(f0.train_range, (0, 79))
        self.assertEqual(f0.validation_range, (80, 99))
        f1 = folds[1]
        self.assertEqual(f1.train_range, (20, 99))
        self.assertEqual(f1.validation_range, (100, 119))

    def test_validate_length_non_int(self):
        with self.assertRaises(ValidationError):
            WalkForwardSplitter(60, 10, 10).split(60.5)

    def test_deterministic(self):
        s1 = WalkForwardSplitter(80, 20, 20).split(239)
        s2 = WalkForwardSplitter(80, 20, 20).split(239)
        self.assertEqual(
            [(f.train_range, f.validation_range) for f in s1],
            [(f.train_range, f.validation_range) for f in s2],
        )

    def test_fold_is_dataclass(self):
        f = Fold(1, 0, 79, 80, 99)
        self.assertEqual(f.train_size, 80)
        self.assertEqual(f.validation_size, 20)


# ---------------------------------------------------------------------------
# validator — constructor
# ---------------------------------------------------------------------------


class TestValidatorConstructor(unittest.TestCase):
    def test_requires_train_size(self):
        with self.assertRaises(ValidationError):
            WalkForwardValidator()

    def test_requires_validation_size(self):
        with self.assertRaises(ValidationError):
            WalkForwardValidator(train_size=60)

    def test_requires_step_size(self):
        with self.assertRaises(ValidationError):
            WalkForwardValidator(train_size=60, validation_size=10)

    def test_rejects_non_int_train(self):
        with self.assertRaises(ValidationError):
            WalkForwardValidator(train_size=60.0, validation_size=10, step_size=10)

    def test_rejects_negative_test_size(self):
        with self.assertRaises(ValidationError):
            WalkForwardValidator(
                train_size=60,
                validation_size=10,
                step_size=10,
                test_size=-1,
            )

    def test_accepts_valid(self):
        v = WalkForwardValidator(train_size=60, validation_size=10, step_size=10)
        self.assertEqual(v.train_size, 60)


# ---------------------------------------------------------------------------
# validator — end to end
# ---------------------------------------------------------------------------


class TestValidatorEndToEnd(unittest.TestCase):
    def setUp(self):
        self.dataset = make_dataset(n=300)
        self.validator = WalkForwardValidator(train_size=80, validation_size=20, step_size=20)

    def test_returns_validation_result(self):
        result = self.validator.validate(self.dataset)
        self.assertIsInstance(result, ValidationResult)

    def test_fold_count_positive(self):
        result = self.validator.validate(self.dataset)
        self.assertGreater(result.fold_count, 0)

    def test_fold_results_type(self):
        result = self.validator.validate(self.dataset)
        for fr in result.fold_results:
            self.assertIsInstance(fr, FoldResult)

    def test_metrics_present(self):
        result = self.validator.validate(self.dataset)
        for key in ("accuracy", "precision", "recall", "f1_score", "mae"):
            self.assertIn(key, result.metrics)

    def test_metrics_bounded(self):
        result = self.validator.validate(self.dataset)
        for key in ("accuracy", "precision", "recall", "f1_score", "directional_accuracy"):
            self.assertGreaterEqual(result.metrics[key], 0.0)
            self.assertLessEqual(result.metrics[key], 1.0)

    def test_test_size_tail(self):
        result = self.validator.validate(self.dataset)
        # last validation window ends at index 219; tail is 239-220=19
        self.assertGreaterEqual(result.test_size, 1)

    def test_metadata(self):
        result = self.validator.validate(self.dataset)
        self.assertEqual(result.metadata["validation_version"], VALIDATION_VERSION)
        self.assertIn("label_name", result.metadata)
        self.assertIn("dataset_version", result.metadata)

    def test_determinism(self):
        r1 = self.validator.validate(self.dataset)
        r2 = self.validator.validate(self.dataset)
        self.assertEqual(r1.metrics, r2.metrics)
        self.assertEqual(r1.fold_results, r2.fold_results)

    def test_hash_of_result(self):
        r1 = self.validator.validate(self.dataset)
        r2 = self.validator.validate(self.dataset)
        self.assertEqual(hash(r1), hash(r2))

    def test_validate_folds_returns_tuple(self):
        folds = self.validator.validate_folds(self.dataset)
        self.assertIsInstance(folds, tuple)
        self.assertGreater(len(folds), 0)

    def test_generate_report_dict(self):
        report = self.validator.generate_report(self.dataset)
        for key in (
            "train_size",
            "validation_size",
            "test_size",
            "fold_count",
            "fold_results",
            "metrics",
            "metadata",
        ):
            self.assertIn(key, report)
        self.assertIn("feature_count", report["metadata"])
        self.assertIn("feature_names", report["metadata"])

    def test_report_serializable(self):
        report = self.validator.generate_report(self.dataset)
        import json

        json.dumps(report)  # must not raise

    def test_rejects_wrong_type(self):
        with self.assertRaises(TypeError):
            self.validator.validate({"not": "a dataset"})

    def test_rejects_too_small_dataset(self):
        small = make_dataset(n=61)
        with self.assertRaises(ValidationError):
            self.validator.validate(small)

    def test_label_alignment_in_fold(self):
        result = self.validator.validate(self.dataset)
        for fr in result.fold_results:
            self.assertGreater(fr.sample_count, 0)
            self.assertEqual(fr.sample_count, 20)


# ---------------------------------------------------------------------------
# architectural guarantee — validation does not import FeatureBuilder
# ---------------------------------------------------------------------------


class TestArchitecture(unittest.TestCase):
    def test_validation_import_graph_is_contracts_only(self):
        import ast
        import inspect

        import researchos.quant_engine.validation.walk_forward as wf

        # The validation layer must only depend on the dataset contract.  Use
        # AST to inspect actual import statements (ignoring docstring prose).
        tree = ast.parse(inspect.getsource(wf))
        imported_modules = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imported_modules.append(node.module or "")
            elif isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
        joined = "\n".join(imported_modules)
        self.assertIn("dataset_contracts", joined)
        self.assertNotIn("dataset_builder", joined)
        self.assertNotIn("label_builder", joined)
        self.assertNotIn("machine_learning.features", joined)

    def test_import_orders_no_circular(self):
        from researchos.quant_engine.machine_learning import FeatureBuilder
        from researchos.quant_engine.validation import WalkForwardValidator as V1

        self.assertIsNotNone(V1)
        self.assertIsNotNone(FeatureBuilder)


if __name__ == "__main__":
    unittest.main()
