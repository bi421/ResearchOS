"""
Tests: Model Training Framework (Q13).

Deterministic research-model training: contracts, trainer, metrics,
repository, and training results.  No ML, no randomness, no stochastic
algorithms.

Coverage:
    * immutability          frozen dataclasses, MappingProxyType
    * serialization         to_dict / from_dict roundtrip
    * hash & equality       identical objects produce identical hashes
    * repository            save / get / list / remove / clear / errors
    * trainer               train / predict / convenience methods
    * metrics               accuracy / precision / recall / f1 / mae / mse / rmse
    * edge cases            empty dataset, invalid dataset, duplicates
    * determinism           same input → same output always
    * large dataset         1000+ rows
    * public API            from researchos.quant_engine.training import *
"""

from __future__ import annotations

import hashlib
import json
import math
import unittest
from dataclasses import FrozenInstanceError

from researchos.quant_engine.machine_learning.dataset_contracts import (
    ResearchDataset,
)
from researchos.quant_engine.training import (
    MODEL_CONTRACT_VERSION,
    TRAINING_REPOSITORY_VERSION,
    TRAINING_VERSION,
    DuplicateModelError,
    InvalidDatasetError,
    InvalidModelError,
    ModelContract,
    ModelType,
    TrainConfig,
    Trainer,
    TrainingError,
    TrainingRepository,
    TrainingRepositoryError,
    TrainingResult,
    TrainingResultNotFoundError,
    accuracy,
    compute_metrics,
    dataset_hash,
    directional_accuracy,
    f1_score,
    mae,
    mse,
    precision,
    recall,
    rmse,
    validate_dataset,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _make_dataset(
    n: int = 100,
    n_features: int = 3,
    pos_ratio: float = 0.5,
    seed: int = 42,
) -> ResearchDataset:
    """Create a deterministic dataset for testing.

    Linear separability: label = 1 if feature[0] > 0.0, else 0.
    """
    rng = _Rng(seed)
    features = []
    labels = []
    for _ in range(n):
        row = tuple(rng.uniform(-1.0, 1.0) for _ in range(n_features))
        label = 1.0 if row[0] > 0.0 else 0.0
        # shuffle some labels based on pos_ratio
        if rng.uniform(0.0, 1.0) > pos_ratio:
            label = 1.0 - label
        features.append(row)
        labels.append(label)
    return ResearchDataset(
        feature_names=tuple(f"f{i}" for i in range(n_features)),
        features=tuple(features),
        labels=tuple(labels),
        sample_count=n,
        feature_count=n_features,
        label_name="target",
    )


class _Rng:
    """Minimal deterministic PRNG (not random module)."""

    def __init__(self, seed: int = 42) -> None:
        self._state = seed

    def _next(self) -> int:
        self._state = (self._state * 1103515245 + 12345) & 0x7FFFFFFF
        return self._state

    def uniform(self, lo: float, hi: float) -> float:
        return lo + (hi - lo) * (self._next() / 0x7FFFFFFF)


def _make_contract(
    model_id: str = "test_model_v1",
    model_type: ModelType = ModelType.FEATURE_WEIGHT,
    training_hash: str = "abc123",
    parameters: Any = None,
    metadata: Any = None,
) -> ModelContract:
    return ModelContract(
        model_id=model_id,
        name="Test Model",
        version="1.0.0",
        model_type=model_type,
        feature_names=("f0", "f1", "f2"),
        label_name="target",
        parameters={"weights": [0.5, 0.3, 0.2]} if parameters is None else parameters,
        metadata={"author": "test"} if metadata is None else metadata,
        created_at="2024-01-01T00:00:00Z",
        training_hash=training_hash,
    )


def _make_result(
    model_id: str = "test_model_v1",
    model_type: ModelType = ModelType.FEATURE_WEIGHT,
    dataset_hash_str: str = "hash123",
) -> TrainingResult:
    model = _make_contract(model_id, model_type, dataset_hash_str)
    return TrainingResult(
        model=model,
        metrics={"accuracy": 0.85, "f1_score": 0.82},
        dataset_hash=dataset_hash_str,
        n_samples=100,
        n_features=3,
        predictions=(1.0, 0.0, 1.0),
        metadata={"trainer_version": "1.0.0"},
    )


# ===================================================================
# ModelContract Tests
# ===================================================================


class TestModelContract(unittest.TestCase):
    def test_constructs_with_required_fields(self):
        c = _make_contract()
        self.assertEqual(c.model_id, "test_model_v1")
        self.assertEqual(c.model_type, ModelType.FEATURE_WEIGHT)
        self.assertEqual(c.parameters["weights"], [0.5, 0.3, 0.2])

    def test_constructs_with_all_model_types(self):
        for mt in ModelType:
            c = _make_contract(model_type=mt)
            self.assertEqual(c.model_type, mt)

    def test_immutability_frozen(self):
        c = _make_contract()
        with self.assertRaises(FrozenInstanceError):
            c.name = "Mutated"  # type: ignore[misc]

    def test_immutability_parameters_proxy(self):
        c = _make_contract()
        with self.assertRaises(TypeError):
            c.parameters["new"] = 1  # type: ignore[index]

    def test_immutability_metadata_proxy(self):
        c = _make_contract()
        with self.assertRaises(TypeError):
            c.metadata["x"] = 1  # type: ignore[index]

    def test_immutability_parameters_setitem(self):
        c = _make_contract()
        self.assertFalse(hasattr(c.parameters, "__setitem__"))

    def test_hashable(self):
        a = _make_contract()
        b = _make_contract()
        self.assertEqual(hash(a), hash(b))
        self.assertEqual(len({a, b}), 1)

    def test_equality(self):
        a = _make_contract()
        b = _make_contract()
        self.assertEqual(a, b)

    def test_inequality_different_id(self):
        a = _make_contract("a")
        b = _make_contract("b")
        self.assertNotEqual(a, b)

    def test_inequality_different_type(self):
        a = _make_contract(model_type=ModelType.FEATURE_WEIGHT)
        b = _make_contract(model_type=ModelType.THRESHOLD)
        self.assertNotEqual(a, b)

    def test_to_dict_roundtrip(self):
        a = _make_contract()
        b = ModelContract.from_dict(a.to_dict())
        self.assertEqual(a, b)
        self.assertEqual(hash(a), hash(b))

    def test_to_dict_structure(self):
        d = _make_contract().to_dict()
        self.assertIn("model_id", d)
        self.assertIn("model_type", d)
        self.assertIn("feature_names", d)
        self.assertIn("parameters", d)
        self.assertIn("metadata", d)

    def test_content_hash_deterministic(self):
        c = _make_contract()
        self.assertEqual(c.content_hash(), c.content_hash())

    def test_content_hash_different_parameters(self):
        a = _make_contract()
        b = _make_contract(
            parameters={"weights": [0.1, 0.2, 0.7]}
        )
        self.assertNotEqual(a.content_hash(), b.content_hash())

    def test_content_hash_length(self):
        c = _make_contract()
        self.assertEqual(len(c.content_hash()), 64)  # SHA-256 hex

    def test_invalid_model_id_empty(self):
        with self.assertRaises(InvalidModelError):
            _make_contract(model_id="")

    def test_invalid_model_id_bad_chars(self):
        with self.assertRaises(InvalidModelError):
            _make_contract(model_id="bad id!")

    def test_invalid_version_not_semver(self):
        with self.assertRaises(InvalidModelError):
            _make_contract().from_dict({
                "model_id": "ok",
                "name": "x",
                "version": "bad",
                "model_type": "rule_based",
                "feature_names": ["a"],
                "label_name": "y",
                "parameters": {},
                "metadata": {},
                "created_at": "now",
                "training_hash": "h",
            })

    def test_invalid_name_empty(self):
        with self.assertRaises(InvalidModelError):
            ModelContract(
                model_id="ok", name="", version="1.0.0",
                model_type=ModelType.RULE_BASED,
                feature_names=("a",), label_name="y",
            )

    def test_invalid_label_name_empty(self):
        with self.assertRaises(InvalidModelError):
            ModelContract(
                model_id="ok", name="x", version="1.0.0",
                model_type=ModelType.RULE_BASED,
                feature_names=("a",), label_name="",
            )

    def test_invalid_model_type_not_enum(self):
        with self.assertRaises(InvalidModelError):
            ModelContract(
                model_id="ok", name="x", version="1.0.0",
                model_type="invalid",  # type: ignore[arg-type]
                feature_names=("a",), label_name="y",
            )

    def test_feature_names_empty_string(self):
        with self.assertRaises(InvalidModelError):
            ModelContract(
                model_id="ok", name="x", version="1.0.0",
                model_type=ModelType.RULE_BASED,
                feature_names=("",), label_name="y",
            )

    def test_parameters_mappingproxy(self):
        c = _make_contract()
        from collections.abc import Mapping
        self.assertIsInstance(c.parameters, Mapping)

    def test_metadata_mappingproxy(self):
        c = _make_contract()
        from collections.abc import Mapping
        self.assertIsInstance(c.metadata, Mapping)

    def test_metadata_immutable_after_construction(self):
        md = {"author": "test"}
        c = ModelContract(
            model_id="ok", name="x", version="1.0.0",
            model_type=ModelType.RULE_BASED,
            feature_names=("a",), label_name="y",
            metadata=md,
        )
        with self.assertRaises(TypeError):
            c.metadata["author"] = "changed"  # type: ignore[index]

    def test_version_constant(self):
        self.assertEqual(MODEL_CONTRACT_VERSION, "1.0.0")

    def test_training_version_constant(self):
        self.assertEqual(TRAINING_VERSION, "1.0.0")

    def test_model_type_enum_values(self):
        self.assertEqual(ModelType.RULE_BASED.value, "rule_based")
        self.assertEqual(ModelType.LINEAR_FORMULA.value, "linear_formula")
        self.assertEqual(ModelType.THRESHOLD.value, "threshold")
        self.assertEqual(ModelType.FEATURE_WEIGHT.value, "feature_weight")

    def test_model_type_from_value(self):
        self.assertEqual(
            ModelType.from_value("rule_based"), ModelType.RULE_BASED
        )

    def test_model_type_from_value_invalid(self):
        with self.assertRaises(ValueError):
            ModelType.from_value("nonexistent")

    def test_feature_names_normalized_to_tuple(self):
        c = ModelContract(
            model_id="ok", name="x", version="1.0.0",
            model_type=ModelType.RULE_BASED,
            feature_names=["a", "b"], label_name="y",
        )
        self.assertIsInstance(c.feature_names, tuple)

    def test_to_dict_contains_all_keys(self):
        c = _make_contract()
        d = c.to_dict()
        expected_keys = {
            "model_id", "name", "version", "model_type",
            "feature_names", "label_name", "parameters",
            "metadata", "created_at", "training_hash",
        }
        self.assertEqual(set(d.keys()), expected_keys)

    def test_from_dict_with_missing_optional_fields(self):
        c = ModelContract.from_dict({
            "model_id": "m1",
            "name": "x",
            "version": "1.0.0",
            "model_type": "rule_based",
            "feature_names": ["a"],
            "label_name": "y",
            "parameters": {},
            "metadata": {},
            "created_at": "",
            "training_hash": "",
        })
        self.assertEqual(c.model_id, "m1")

    def test_serialization_deterministic(self):
        c = _make_contract()
        self.assertEqual(c.to_dict(), c.to_dict())

    def test_hash_different_metadata(self):
        a = _make_contract(metadata={"x": 1})
        b = _make_contract(metadata={"x": 2})
        self.assertNotEqual(hash(a), hash(b))

    def test_hash_different_training_hash(self):
        a = _make_contract(training_hash="abc")
        b = _make_contract(training_hash="def")
        self.assertNotEqual(hash(a), hash(b))

    def test_parameters_frozen_via_mappingproxy(self):
        c = _make_contract()
        # The mappingproxy itself has no __setitem__
        self.assertFalse(hasattr(c.parameters, "__setitem__"))
        # Assigning a key on the mappingproxy raises TypeError
        with self.assertRaises(TypeError):
            c.parameters["new_key"] = 1.0  # type: ignore[index]

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(InvalidModelError, TrainingError))
        self.assertTrue(issubclass(InvalidDatasetError, TrainingError))


# ===================================================================
# TrainingResult Tests
# ===================================================================


class TestTrainingResult(unittest.TestCase):
    def test_constructs_with_required_fields(self):
        r = _make_result()
        self.assertEqual(r.model.model_id, "test_model_v1")
        self.assertEqual(r.metrics["accuracy"], 0.85)

    def test_immutability_frozen(self):
        r = _make_result()
        with self.assertRaises(FrozenInstanceError):
            r.n_samples = 999  # type: ignore[misc]

    def test_immutability_metrics_proxy(self):
        r = _make_result()
        with self.assertRaises(TypeError):
            r.metrics["new"] = 0.5  # type: ignore[index]

    def test_immutability_metadata_proxy(self):
        r = _make_result()
        with self.assertRaises(TypeError):
            r.metadata["x"] = 1  # type: ignore[index]

    def test_hashable(self):
        a = _make_result()
        b = _make_result()
        self.assertEqual(hash(a), hash(b))

    def test_equality(self):
        a = _make_result()
        b = _make_result()
        self.assertEqual(a, b)

    def test_to_dict_roundtrip(self):
        a = _make_result()
        b = TrainingResult.from_dict(a.to_dict())
        self.assertEqual(a, b)
        self.assertEqual(hash(a), hash(b))

    def test_to_dict_structure(self):
        d = _make_result().to_dict()
        self.assertIn("model", d)
        self.assertIn("metrics", d)
        self.assertIn("dataset_hash", d)
        self.assertIn("predictions", d)

    def test_content_hash_deterministic(self):
        r = _make_result()
        self.assertEqual(r.content_hash(), r.content_hash())

    def test_content_hash_length(self):
        r = _make_result()
        self.assertEqual(len(r.content_hash()), 64)

    def test_content_hash_differs_for_different_models(self):
        a = _make_result("model_a")
        b = _make_result("model_b")
        self.assertNotEqual(a.content_hash(), b.content_hash())

    def test_invalid_model_type(self):
        with self.assertRaises(TypeError):
            TrainingResult(
                model="not a model",  # type: ignore[arg-type]
                metrics={},
                dataset_hash="h",
                n_samples=0,
                n_features=0,
            )

    def test_invalid_metrics_type(self):
        with self.assertRaises(TypeError):
            TrainingResult(
                model=_make_contract(),
                metrics="not a mapping",  # type: ignore[arg-type]
                dataset_hash="h",
                n_samples=0,
                n_features=0,
            )

    def test_empty_dataset_hash_raises(self):
        with self.assertRaises(ValueError):
            _make_result(dataset_hash_str="")

    def test_negative_n_samples_raises(self):
        with self.assertRaises(ValueError):
            TrainingResult(
                model=_make_contract(),
                metrics={},
                dataset_hash="h",
                n_samples=-1,
                n_features=0,
            )

    def test_negative_n_features_raises(self):
        with self.assertRaises(ValueError):
            TrainingResult(
                model=_make_contract(),
                metrics={},
                dataset_hash="h",
                n_samples=0,
                n_features=-1,
            )

    def test_predictions_normalized_to_tuple(self):
        r = TrainingResult(
            model=_make_contract(),
            metrics={},
            dataset_hash="h",
            n_samples=0,
            n_features=0,
            predictions=[1.0, 0.0],
        )
        self.assertIsInstance(r.predictions, tuple)

    def test_serialization_deterministic(self):
        r = _make_result()
        self.assertEqual(r.to_dict(), r.to_dict())


# ===================================================================
# Metrics Tests
# ===================================================================


class TestMetrics(unittest.TestCase):
    def test_accuracy_perfect(self):
        self.assertEqual(accuracy([1, 0, 1], [1, 0, 1]), 1.0)

    def test_accuracy_half(self):
        self.assertEqual(accuracy([1, 0, 1], [0, 0, 1]), 2.0 / 3.0)

    def test_accuracy_empty(self):
        self.assertEqual(accuracy([], []), 0.0)

    def test_accuracy_mismatched_length(self):
        self.assertEqual(accuracy([1], [1, 0]), 0.0)

    def test_precision_perfect(self):
        self.assertEqual(precision([1, 0], [1, 0]), 1.0)

    def test_precision_imbalanced(self):
        self.assertAlmostEqual(precision([1, 0, 1], [1, 1, 0]), 0.5)

    def test_precision_no_positives(self):
        self.assertEqual(precision([0, 0], [0, 0]), 0.0)

    def test_precision_empty(self):
        self.assertEqual(precision([], []), 0.0)

    def test_recall_perfect(self):
        self.assertEqual(recall([1, 0], [1, 0]), 1.0)

    def test_recall_partial(self):
        self.assertAlmostEqual(recall([1, 1, 0], [1, 0, 0]), 0.5)

    def test_recall_no_positives(self):
        self.assertEqual(recall([0, 0], [0, 0]), 0.0)

    def test_recall_empty(self):
        self.assertEqual(recall([], []), 0.0)

    def test_f1_score_perfect(self):
        self.assertEqual(f1_score([1, 0], [1, 0]), 1.0)

    def test_f1_score_zero(self):
        self.assertEqual(f1_score([0, 0], [1, 1]), 0.0)

    def test_f1_score_empty(self):
        self.assertEqual(f1_score([], []), 0.0)

    def test_mae_zero(self):
        self.assertEqual(mae([1, 0], [1, 0]), 0.0)

    def test_mae_nonzero(self):
        self.assertAlmostEqual(mae([1, 0], [0, 1]), 1.0)

    def test_mae_empty(self):
        self.assertEqual(mae([], []), 0.0)

    def test_mse_zero(self):
        self.assertEqual(mse([1, 0], [1, 0]), 0.0)

    def test_mse_nonzero(self):
        self.assertAlmostEqual(mse([1, 0], [0, 1]), 1.0)

    def test_mse_empty(self):
        self.assertEqual(mse([], []), 0.0)

    def test_rmse_zero(self):
        self.assertEqual(rmse([1, 0], [1, 0]), 0.0)

    def test_rmse_nonzero(self):
        self.assertAlmostEqual(rmse([1, 0], [0, 1]), 1.0)

    def test_rmse_empty(self):
        self.assertEqual(rmse([], []), 0.0)

    def test_directional_accuracy(self):
        self.assertEqual(
            directional_accuracy([1, -1, 0], [1, -1, 0]), 1.0
        )

    def test_directional_accuracy_opposite(self):
        self.assertEqual(
            directional_accuracy([1, -1], [-1, 1]), 0.0
        )

    def test_directional_accuracy_empty(self):
        self.assertEqual(directional_accuracy([], []), 0.0)

    def test_compute_metrics_keys(self):
        d = compute_metrics([1, 0, 1], [1, 0, 1])
        self.assertIn("accuracy", d)
        self.assertIn("precision", d)
        self.assertIn("recall", d)
        self.assertIn("f1_score", d)
        self.assertIn("mae", d)
        self.assertIn("mse", d)
        self.assertIn("rmse", d)
        self.assertIn("directional_accuracy", d)

    def test_compute_metrics_deterministic(self):
        d1 = compute_metrics([1, 0, 1], [1, 0, 1])
        d2 = compute_metrics([1, 0, 1], [1, 0, 1])
        self.assertEqual(d1, d2)

    def test_compute_metrics_empty(self):
        d = compute_metrics([], [])
        self.assertEqual(d["accuracy"], 0.0)

    def test_accuracy_float_precision(self):
        self.assertAlmostEqual(
            accuracy([1.0, 0.0], [1.0, 0.0]), 1.0
        )

    def test_precision_with_custom_positive(self):
        self.assertEqual(
            precision([1, 0, 1], [1, 1, 0], positive=1.0), 0.5
        )

    def test_metrics_all_deterministic(self):
        y_true = [1.0, 0.0, 1.0, 0.0, 1.0]
        y_pred = [1.0, 0.0, 0.0, 0.0, 1.0]
        results = compute_metrics(y_true, y_pred)
        # verify same call twice
        self.assertEqual(results, compute_metrics(y_true, y_pred))


# ===================================================================
# Trainer Tests
# ===================================================================


class TestTrainer(unittest.TestCase):
    def setUp(self):
        self.trainer = Trainer()
        self.dataset = _make_dataset(100, 3)
        self.config = TrainConfig(
            model_id="test_model",
            name="Test",
            model_type=ModelType.FEATURE_WEIGHT,
            label_name="target",
            metadata={"trial": "1"},
        )

    def test_train_feature_weight(self):
        result = self.trainer.train(self.dataset, self.config)
        self.assertIsInstance(result, TrainingResult)
        self.assertEqual(result.model.model_type, ModelType.FEATURE_WEIGHT)

    def test_train_rule_based(self):
        config = TrainConfig(
            model_id="rule_model", name="Rule",
            model_type=ModelType.RULE_BASED, label_name="target",
        )
        result = self.trainer.train(self.dataset, config)
        self.assertEqual(result.model.model_type, ModelType.RULE_BASED)

    def test_train_linear_formula(self):
        config = TrainConfig(
            model_id="linear_model", name="Linear",
            model_type=ModelType.LINEAR_FORMULA, label_name="target",
        )
        result = self.trainer.train(self.dataset, config)
        self.assertEqual(result.model.model_type, ModelType.LINEAR_FORMULA)

    def test_train_threshold(self):
        config = TrainConfig(
            model_id="thresh_model", name="Threshold",
            model_type=ModelType.THRESHOLD, label_name="target",
        )
        result = self.trainer.train(self.dataset, config)
        self.assertEqual(result.model.model_type, ModelType.THRESHOLD)

    def test_train_determinism(self):
        r1 = self.trainer.train(self.dataset, self.config)
        r2 = self.trainer.train(self.dataset, self.config)
        self.assertEqual(r1.model, r2.model)
        self.assertEqual(r1.metrics, r2.metrics)
        self.assertEqual(r1.predictions, r2.predictions)
        self.assertEqual(r1.content_hash(), r2.content_hash())

    def test_train_sets_model_id(self):
        result = self.trainer.train(self.dataset, self.config)
        self.assertEqual(result.model.model_id, "test_model")

    def test_train_sets_label_name(self):
        result = self.trainer.train(self.dataset, self.config)
        self.assertEqual(result.model.label_name, "target")

    def test_train_sets_feature_names(self):
        result = self.trainer.train(self.dataset, self.config)
        self.assertEqual(
            result.model.feature_names, self.dataset.feature_names
        )

    def test_train_sets_training_hash(self):
        result = self.trainer.train(self.dataset, self.config)
        self.assertEqual(
            result.model.training_hash, result.dataset_hash
        )

    def test_train_sets_metadata(self):
        result = self.trainer.train(self.dataset, self.config)
        self.assertEqual(result.model.metadata["trial"], "1")

    def test_train_returns_metrics(self):
        result = self.trainer.train(self.dataset, self.config)
        self.assertIn("accuracy", result.metrics)

    def test_train_n_samples(self):
        result = self.trainer.train(self.dataset, self.config)
        self.assertEqual(result.n_samples, 100)

    def test_train_n_features(self):
        result = self.trainer.train(self.dataset, self.config)
        self.assertEqual(result.n_features, 3)

    def test_predict_after_train(self):
        result = self.trainer.train(self.dataset, self.config)
        preds = self.trainer.predict(result.model, self.dataset)
        self.assertEqual(len(preds), 100)
        self.assertEqual(preds, list(result.predictions))

    def test_predict_determinism(self):
        result = self.trainer.train(self.dataset, self.config)
        p1 = self.trainer.predict(result.model, self.dataset)
        p2 = self.trainer.predict(result.model, self.dataset)
        self.assertEqual(p1, p2)

    def test_predict_invalid_model(self):
        with self.assertRaises(TypeError):
            self.trainer.predict("not a model", self.dataset)  # type: ignore[arg-type]

    def test_predict_invalid_dataset(self):
        with self.assertRaises(InvalidDatasetError):
            self.trainer.predict(
                _make_contract(), "not a dataset"  # type: ignore[arg-type]
            )

    def test_train_invalid_config_type(self):
        with self.assertRaises(TypeError):
            self.trainer.train(self.dataset, "not a config")  # type: ignore[arg-type]

    def test_train_invalid_dataset_missing_features(self):
        ds = ResearchDataset(
            feature_names=(),
            features=(),
            labels=(),
            sample_count=0,
            feature_count=0,
            label_name="x",
        )
        with self.assertRaises(InvalidDatasetError):
            self.trainer.train(ds, self.config)

    def test_train_invalid_dataset_feature_mismatch(self):
        features = ((1.0, 2.0), (3.0,))
        labels = (1.0, 0.0)
        ds = ResearchDataset(
            feature_names=("a", "b"),
            features=features,
            labels=labels,
            sample_count=2,
            feature_count=2,
            label_name="x",
        )
        with self.assertRaises(InvalidDatasetError):
            self.trainer.train(ds, self.config)

    def test_train_invalid_dataset_none_feature(self):
        features = ((1.0, None),)
        labels = (1.0,)
        ds = ResearchDataset(
            feature_names=("a", "b"),
            features=features,
            labels=labels,
            sample_count=1,
            feature_count=2,
            label_name="x",
        )
        with self.assertRaises(InvalidDatasetError):
            self.trainer.train(ds, self.config)

    def test_train_invalid_dataset_nan_feature(self):
        features = ((1.0, float("nan")),)
        labels = (1.0,)
        ds = ResearchDataset(
            feature_names=("a", "b"),
            features=features,
            labels=labels,
            sample_count=1,
            feature_count=2,
            label_name="x",
        )
        with self.assertRaises(InvalidDatasetError):
            self.trainer.train(ds, self.config)

    def test_train_invalid_dataset_count_mismatch(self):
        features = ((1.0, 2.0),)
        labels = (1.0, 0.0)
        ds = ResearchDataset(
            feature_names=("a", "b"),
            features=features,
            labels=labels,
            sample_count=1,
            feature_count=2,
            label_name="x",
        )
        with self.assertRaises(InvalidDatasetError):
            self.trainer.train(ds, self.config)

    def test_train_invalid_dataset_non_label(self):
        features = ((1.0, 2.0),)
        labels = (None,)
        ds = ResearchDataset(
            feature_names=("a", "b"),
            features=features,
            labels=labels,
            sample_count=1,
            feature_count=2,
            label_name="x",
        )
        with self.assertRaises(InvalidDatasetError):
            self.trainer.train(ds, self.config)

    def test_convenience_train_feature_weight(self):
        result = self.trainer.train_feature_weight(
            self.dataset, "fw_model"
        )
        self.assertEqual(result.model.model_type, ModelType.FEATURE_WEIGHT)

    def test_convenience_train_rule_based(self):
        result = self.trainer.train_rule_based(
            self.dataset, "rule_model"
        )
        self.assertEqual(result.model.model_type, ModelType.RULE_BASED)

    def test_convenience_train_linear_formula(self):
        result = self.trainer.train_linear_formula(
            self.dataset, "linear_model"
        )
        self.assertEqual(result.model.model_type, ModelType.LINEAR_FORMULA)

    def test_convenience_train_threshold(self):
        result = self.trainer.train_threshold(
            self.dataset, "thresh_model"
        )
        self.assertEqual(result.model.model_type, ModelType.THRESHOLD)

    def test_convenience_determinism(self):
        r1 = self.trainer.train_feature_weight(
            self.dataset, "fw_model"
        )
        r2 = self.trainer.train_feature_weight(
            self.dataset, "fw_model"
        )
        self.assertEqual(r1.content_hash(), r2.content_hash())

    def test_dataset_hash_deterministic(self):
        h1 = dataset_hash(self.dataset)
        h2 = dataset_hash(self.dataset)
        self.assertEqual(h1, h2)

    def test_dataset_hash_different_data(self):
        ds1 = _make_dataset(100, 3)
        ds2 = _make_dataset(100, 3, seed=99)
        self.assertNotEqual(dataset_hash(ds1), dataset_hash(ds2))

    def test_dataset_hash_length(self):
        h = dataset_hash(self.dataset)
        self.assertEqual(len(h), 64)

    def test_large_dataset(self):
        large = _make_dataset(1000, 10)
        config = TrainConfig(
            model_id="large", name="Large",
            model_type=ModelType.FEATURE_WEIGHT, label_name="target",
        )
        result = self.trainer.train(large, config)
        self.assertEqual(result.n_samples, 1000)
        self.assertEqual(result.n_features, 10)

    def test_large_dataset_determinism(self):
        large = _make_dataset(1000, 10)
        config = TrainConfig(
            model_id="large", name="Large",
            model_type=ModelType.FEATURE_WEIGHT, label_name="target",
        )
        r1 = self.trainer.train(large, config)
        r2 = self.trainer.train(large, config)
        self.assertEqual(r1.content_hash(), r2.content_hash())

    def test_train_config_invalid_id(self):
        with self.assertRaises(InvalidModelError):
            TrainConfig(model_id="", name="x")

    def test_train_config_invalid_name(self):
        with self.assertRaises(InvalidModelError):
            TrainConfig(model_id="ok", name="")

    def test_train_config_invalid_type(self):
        with self.assertRaises(InvalidModelError):
            TrainConfig(
                model_id="ok", name="x",
                model_type="invalid",  # type: ignore[arg-type]
            )

    def test_train_config_parameters_frozen(self):
        cfg = TrainConfig(
            model_id="ok", name="x",
            parameters={"a": 1},
        )
        with self.assertRaises(TypeError):
            cfg.parameters["a"] = 2  # type: ignore[index]

    def test_train_config_metadata_frozen(self):
        cfg = TrainConfig(
            model_id="ok", name="x",
            metadata={"a": 1},
        )
        with self.assertRaises(TypeError):
            cfg.metadata["a"] = 2  # type: ignore[index]

    def test_train_with_different_model_types_produce_different_models(self):
        fw = self.trainer.train_feature_weight(self.dataset, "fw")
        rb = self.trainer.train_rule_based(self.dataset, "rb")
        self.assertNotEqual(fw.model, rb.model)

    def test_train_with_all_model_types_produce_valid_results(self):
        for mt, fn in [
            (ModelType.FEATURE_WEIGHT, self.trainer.train_feature_weight),
            (ModelType.RULE_BASED, self.trainer.train_rule_based),
            (ModelType.LINEAR_FORMULA, self.trainer.train_linear_formula),
            (ModelType.THRESHOLD, self.trainer.train_threshold),
        ]:
            result = fn(self.dataset, f"model_{mt.value}")
            self.assertEqual(result.model.model_type, mt)
            self.assertGreater(result.n_samples, 0)

    def test_validate_dataset_valid(self):
        # Should not raise
        validate_dataset(self.dataset)

    def test_validate_dataset_not_research_dataset(self):
        with self.assertRaises(InvalidDatasetError):
            validate_dataset("not a dataset")  # type: ignore[arg-type]

    def test_validate_dataset_empty_features(self):
        ds = ResearchDataset(
            feature_names=("a",),
            features=(),
            labels=(),
            sample_count=0,
            feature_count=1,
            label_name="x",
        )
        with self.assertRaises(InvalidDatasetError):
            validate_dataset(ds)

    def test_validate_dataset_no_feature_names(self):
        ds = ResearchDataset(
            feature_names=(),
            features=((1.0,), (2.0,)),
            labels=(1.0, 0.0),
            sample_count=2,
            feature_count=0,
            label_name="x",
        )
        with self.assertRaises(InvalidDatasetError):
            validate_dataset(ds)

    def test_validate_dataset_nan_feature(self):
        features = ((1.0, float("nan")),)
        labels = (1.0,)
        ds = ResearchDataset(
            feature_names=("a", "b"),
            features=features,
            labels=labels,
            sample_count=1,
            feature_count=2,
            label_name="x",
        )
        with self.assertRaises(InvalidDatasetError):
            validate_dataset(ds)

    def test_validate_dataset_inf_feature(self):
        features = ((1.0, float("inf")),)
        labels = (1.0,)
        ds = ResearchDataset(
            feature_names=("a", "b"),
            features=features,
            labels=labels,
            sample_count=1,
            feature_count=2,
            label_name="x",
        )
        with self.assertRaises(InvalidDatasetError):
            validate_dataset(ds)


# ===================================================================
# TrainingRepository Tests
# ===================================================================


class TestTrainingRepository(unittest.TestCase):
    def setUp(self):
        self.repo = TrainingRepository()
        self.result = _make_result()

    def test_save_and_get(self):
        self.repo.save(self.result)
        got = self.repo.get("test_model_v1")
        self.assertEqual(got.model.model_id, "test_model_v1")
        self.assertEqual(self.repo.count(), 1)

    def test_save_duplicate_raises(self):
        self.repo.save(self.result)
        with self.assertRaises(DuplicateModelError):
            self.repo.save(self.result)

    def test_duplicate_error_message(self):
        self.repo.save(self.result)
        try:
            self.repo.save(self.result)
        except DuplicateModelError as e:
            self.assertIn("test_model_v1", str(e))

    def test_get_missing_raises(self):
        with self.assertRaises(TrainingResultNotFoundError):
            self.repo.get("nope")

    def test_get_missing_error_message(self):
        try:
            self.repo.get("missing")
        except TrainingResultNotFoundError as e:
            self.assertIn("missing", str(e))

    def test_get_model(self):
        self.repo.save(self.result)
        model = self.repo.get_model("test_model_v1")
        self.assertEqual(model.model_id, "test_model_v1")

    def test_remove(self):
        self.repo.save(self.result)
        self.repo.remove("test_model_v1")
        self.assertFalse(self.repo.exists("test_model_v1"))
        self.assertEqual(self.repo.count(), 0)

    def test_remove_missing_raises(self):
        with self.assertRaises(TrainingResultNotFoundError):
            self.repo.remove("nope")

    def test_clear(self):
        self.repo.save(self.result)
        self.repo.save(_make_result("other"))
        self.repo.clear()
        self.assertEqual(self.repo.count(), 0)

    def test_list_results_deterministic_order(self):
        self.repo.save(_make_result("zebra"))
        self.repo.save(_make_result("alpha"))
        self.repo.save(_make_result("middle"))
        ids = [r.model.model_id for r in self.repo.list_results()]
        self.assertEqual(ids, sorted(ids))

    def test_list_results_repeatable(self):
        self.repo.save(_make_result("zebra"))
        self.repo.save(_make_result("alpha"))
        self.repo.save(_make_result("middle"))
        self.assertEqual(
            self.repo.list_results(), self.repo.list_results()
        )

    def test_rejects_non_result(self):
        with self.assertRaises(TypeError):
            self.repo.save("not a result")  # type: ignore[arg-type]

    def test_exists_returns_true(self):
        self.repo.save(self.result)
        self.assertTrue(self.repo.exists("test_model_v1"))

    def test_exists_returns_false(self):
        self.assertFalse(self.repo.exists("nonexistent"))

    def test_count_empty(self):
        self.assertEqual(self.repo.count(), 0)

    def test_count_multiple(self):
        self.repo.save(_make_result("a"))
        self.repo.save(_make_result("b"))
        self.assertEqual(self.repo.count(), 2)

    def test_to_dict_roundtrip(self):
        self.repo.save(_make_result("a"))
        self.repo.save(_make_result("b"))
        r2 = TrainingRepository.from_dict(self.repo.to_dict())
        self.assertEqual(
            self.repo.list_results(), r2.list_results()
        )

    def test_to_dict_version(self):
        self.repo.save(self.result)
        d = self.repo.to_dict()
        self.assertEqual(d["version"], TRAINING_REPOSITORY_VERSION)

    def test_from_dict_empty(self):
        r = TrainingRepository.from_dict({"version": "1.0.0", "results": []})
        self.assertEqual(r.count(), 0)

    def test_error_hierarchy(self):
        self.assertTrue(
            issubclass(DuplicateModelError, TrainingRepositoryError)
        )
        self.assertTrue(
            issubclass(TrainingResultNotFoundError, TrainingRepositoryError)
        )

    def test_remove_nonexistent_after_clear(self):
        self.repo.save(self.result)
        self.repo.clear()
        with self.assertRaises(TrainingResultNotFoundError):
            self.repo.remove("test_model_v1")

    def test_save_twice_different_models(self):
        self.repo.save(_make_result("a"))
        self.repo.save(_make_result("b"))
        self.assertEqual(self.repo.count(), 2)

    def test_repository_independence(self):
        r1 = TrainingRepository()
        r2 = TrainingRepository()
        r1.save(_make_result("a"))
        self.assertEqual(r1.count(), 1)
        self.assertEqual(r2.count(), 0)


# ===================================================================
# Determinism / Immutability Integration Tests
# ===================================================================


class TestDeterminismAndImmutability(unittest.TestCase):
    def test_full_training_pipeline_determinism(self):
        ds = _make_dataset(200, 5)
        trainer = Trainer()
        for mt in ModelType:
            config = TrainConfig(
                model_id=f"model_{mt.value}",
                name=f"Test {mt.value}",
                model_type=mt,
                label_name="target",
            )
            r1 = trainer.train(ds, config)
            r2 = trainer.train(ds, config)
            self.assertEqual(r1.content_hash(), r2.content_hash())
            self.assertEqual(r1.model.content_hash(), r2.model.content_hash())

    def test_metadata_immutability(self):
        c = _make_contract()
        with self.assertRaises(TypeError):
            c.metadata["author"] = "changed"  # type: ignore[index]
        with self.assertRaises(TypeError):
            c.parameters["weights"] = [1.0]  # type: ignore[index]

    def test_dataset_hash_immutability(self):
        ds = _make_dataset()
        h = dataset_hash(ds)
        # same dataset -> same hash
        self.assertEqual(h, dataset_hash(ds))

    def test_training_result_immutability(self):
        r = _make_result()
        with self.assertRaises(FrozenInstanceError):
            r.n_samples = 999  # type: ignore[misc]
        with self.assertRaises(TypeError):
            r.metrics["new"] = 0.5  # type: ignore[index]

    def test_repository_immutability_of_stored(self):
        repo = TrainingRepository()
        result = _make_result()
        repo.save(result)
        got = repo.get("test_model_v1")
        with self.assertRaises(FrozenInstanceError):
            got.model._name = "changed"  # type: ignore[attr-defined]

    def test_serialization_roundtrip_preserves_hash(self):
        c = _make_contract()
        c2 = ModelContract.from_dict(c.to_dict())
        self.assertEqual(hash(c), hash(c2))
        self.assertEqual(c.content_hash(), c2.content_hash())

    def test_model_contract_serialization_all_types(self):
        for mt in ModelType:
            c = _make_contract(model_type=mt)
            c2 = ModelContract.from_dict(c.to_dict())
            self.assertEqual(c, c2)
            self.assertEqual(c.content_hash(), c2.content_hash())


# ===================================================================
# Public API Tests
# ===================================================================


class TestPublicAPI(unittest.TestCase):
    def test_import_star(self):
        # Verify that the public API is surface-stable
        from researchos.quant_engine.training import (
            ModelContract, ModelType, TrainingResult,
            TrainConfig, Trainer, TrainingRepository,
            accuracy, precision, recall, f1_score, mae, mse, rmse,
            directional_accuracy, compute_metrics,
            dataset_hash, validate_dataset,
            TrainingError, InvalidDatasetError, InvalidModelError,
            TrainingRepositoryError, DuplicateModelError,
            TrainingResultNotFoundError,
            TRAINING_VERSION, MODEL_CONTRACT_VERSION,
            TRAINING_REPOSITORY_VERSION,
        )
        self.assertIsNotNone(ModelContract)
        self.assertIsNotNone(ModelType)
        self.assertIsNotNone(TrainingResult)
        self.assertIsNotNone(Trainer)
        self.assertIsNotNone(TrainingRepository)
        self.assertIsNotNone(accuracy)
        self.assertIsNotNone(precision)

    def test_trainer_is_importable(self):
        from researchos.quant_engine.training import Trainer
        self.assertTrue(callable(Trainer))

    def test_model_type_enum_members(self):
        self.assertEqual(len(ModelType), 4)

    def test_version_constants(self):
        self.assertIsInstance(TRAINING_VERSION, str)
        self.assertIsInstance(MODEL_CONTRACT_VERSION, str)
        self.assertIsInstance(TRAINING_REPOSITORY_VERSION, str)


# ===================================================================
# Edge Cases
# ===================================================================


class TestEdgeCases(unittest.TestCase):
    def test_empty_dataset_fails_validation(self):
        ds = ResearchDataset(
            feature_names=("a",),
            features=(),
            labels=(),
            sample_count=0,
            feature_count=1,
            label_name="x",
        )
        with self.assertRaises(InvalidDatasetError):
            validate_dataset(ds)

    def test_single_sample_dataset(self):
        ds = ResearchDataset(
            feature_names=("f0", "f1"),
            features=((1.0, 2.0),),
            labels=(1.0,),
            sample_count=1,
            feature_count=2,
            label_name="target",
        )
        trainer = Trainer()
        config = TrainConfig(
            model_id="single", name="Single",
            model_type=ModelType.FEATURE_WEIGHT, label_name="target",
        )
        result = trainer.train(ds, config)
        self.assertEqual(result.n_samples, 1)
        self.assertEqual(len(result.predictions), 1)

    def test_two_class_balanced(self):
        features = ((1.0,), (-1.0,))
        labels = (1.0, 0.0)
        ds = ResearchDataset(
            feature_names=("f0",),
            features=features,
            labels=labels,
            sample_count=2,
            feature_count=1,
            label_name="target",
        )
        trainer = Trainer()
        config = TrainConfig(
            model_id="balanced", name="Balanced",
            model_type=ModelType.FEATURE_WEIGHT, label_name="target",
        )
        result = trainer.train(ds, config)
        self.assertEqual(result.n_samples, 2)

    def test_all_same_class(self):
        features = ((1.0,), (2.0,), (3.0,))
        labels = (1.0, 1.0, 1.0)
        ds = ResearchDataset(
            feature_names=("f0",),
            features=features,
            labels=labels,
            sample_count=3,
            feature_count=1,
            label_name="target",
        )
        trainer = Trainer()
        config = TrainConfig(
            model_id="same_class", name="Same",
            model_type=ModelType.FEATURE_WEIGHT, label_name="target",
        )
        # Should not raise -- deterministic even with single class
        result = trainer.train(ds, config)
        self.assertEqual(result.n_samples, 3)

    def test_dataset_hash_distinct_datasets(self):
        ds1 = _make_dataset(50, 3, seed=1)
        ds2 = _make_dataset(50, 3, seed=2)
        self.assertNotEqual(dataset_hash(ds1), dataset_hash(ds2))

    def test_dataset_hash_same_datasets(self):
        ds1 = _make_dataset(50, 3, seed=42)
        ds2 = _make_dataset(50, 3, seed=42)
        self.assertEqual(dataset_hash(ds1), dataset_hash(ds2))

    def test_model_contract_from_dict_all_types(self):
        for mt in ModelType:
            d = {
                "model_id": "m1",
                "name": "x",
                "version": "1.0.0",
                "model_type": mt.value,
                "feature_names": ["a", "b"],
                "label_name": "y",
                "parameters": {"p": 1.0},
                "metadata": {"m": "v"},
                "created_at": "now",
                "training_hash": "h",
            }
            c = ModelContract.from_dict(d)
            self.assertEqual(c.model_type, mt)

    def test_training_result_metrics_immutable(self):
        r = _make_result()
        with self.assertRaises(TypeError):
            r.metrics["accuracy"] = 0.99  # type: ignore[index]

    def test_training_result_predictions_immutable(self):
        r = _make_result()
        with self.assertRaises(TypeError):
            r.predictions[0] = 0.5  # type: ignore[index]

    def test_training_result_metadata_immutable(self):
        r = _make_result()
        with self.assertRaises(TypeError):
            r.metadata["trainer_version"] = "2.0.0"  # type: ignore[index]

    def test_model_contract_to_dict_deterministic(self):
        c = _make_contract()
        d1 = json.dumps(c.to_dict(), sort_keys=True)
        d2 = json.dumps(c.to_dict(), sort_keys=True)
        self.assertEqual(d1, d2)

    def test_training_result_to_dict_deterministic(self):
        r = _make_result()
        d1 = json.dumps(r.to_dict(), sort_keys=True)
        d2 = json.dumps(r.to_dict(), sort_keys=True)
        self.assertEqual(d1, d2)

    def test_repository_serialization_empty(self):
        r = TrainingRepository()
        d = r.to_dict()
        self.assertEqual(d["results"], [])
        r2 = TrainingRepository.from_dict(d)
        self.assertEqual(r2.count(), 0)

    def test_repository_serialization_preserves_content_hash(self):
        repo = TrainingRepository()
        repo.save(_make_result("a"))
        d = repo.to_dict()
        repo2 = TrainingRepository.from_dict(d)
        self.assertEqual(
            repo.get("a").content_hash(),
            repo2.get("a").content_hash(),
        )


if __name__ == "__main__":
    unittest.main()
