"""
Model Training Framework — deterministic trainer.

The trainer receives a ``ResearchDataset`` and returns a ``TrainingResult``.
It NEVER fits stochastic models.  Given the same dataset and the same
configuration, it always produces the same model, predictions, and metrics.

Supported deterministic model families (architecture only — NOT ML):
    * ``RULE_BASED``      — single-feature inequality rule.
    * ``LINEAR_FORMULA``  — closed-form linear score + bias.
    * ``THRESHOLD``       — single-feature threshold rule with direction.
    * ``FEATURE_WEIGHT``  — normalized feature-weight score.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Dict, List, Mapping, Tuple

from ..machine_learning.dataset_contracts import ResearchDataset
from .contracts import (
    TRAINING_VERSION,
    InvalidDatasetError,
    InvalidModelError,
    ModelContract,
    ModelType,
)
from .metrics import compute_metrics
from .training_result import TrainingResult


@dataclass(frozen=True)
class TrainConfig:
    """Immutable configuration for a deterministic training run."""

    model_id: str
    name: str
    version: str = "1.0.0"
    model_type: ModelType = ModelType.FEATURE_WEIGHT
    label_name: str = ""
    parameters: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def __post_init__(self) -> None:
        """Validate identity/type and freeze all container fields."""
        if not isinstance(self.model_id, str) or not self.model_id:
            raise InvalidModelError("model_id must be a non-empty string")
        if not isinstance(self.name, str) or not self.name:
            raise InvalidModelError("name must be a non-empty string")
        if not isinstance(self.model_type, ModelType):
            raise InvalidModelError("model_type must be a ModelType")
        object.__setattr__(self, "parameters", MappingProxyType(dict(self.parameters)))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


def dataset_hash(dataset: ResearchDataset) -> str:
    """Deterministic SHA-256 hash of a research dataset's content."""
    payload = {
        "feature_names": list(dataset.feature_names),
        "features": [list(row) for row in dataset.features],
        "labels": list(dataset.labels),
        "label_name": dataset.label_name,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


def validate_dataset(dataset: ResearchDataset) -> None:
    """Validate a dataset; raise ``InvalidDatasetError`` when unusable."""
    if not isinstance(dataset, ResearchDataset):
        raise InvalidDatasetError("expected a ResearchDataset")
    feature_names = tuple(dataset.feature_names)
    features = tuple(dataset.features)
    labels = tuple(dataset.labels)
    if not feature_names:
        raise InvalidDatasetError("dataset has no feature names")
    if not features:
        raise InvalidDatasetError("dataset has no feature rows")
    n_features = len(feature_names)
    for i, row in enumerate(features):
        if len(row) != n_features:
            raise InvalidDatasetError(
                f"feature row {i} has length {len(row)}; expected {n_features}"
            )
        for j, v in enumerate(row):
            if v is None or not isinstance(v, (int, float)):
                raise InvalidDatasetError(
                    f"feature row {i} column {j} is not a number"
                )
            if isinstance(v, float) and not math.isfinite(v):
                raise InvalidDatasetError(
                    f"feature row {i} column {j} is not finite"
                )
    if len(features) != len(labels):
        raise InvalidDatasetError(
            f"feature count {len(features)} != label count {len(labels)}"
        )
    for i, y in enumerate(labels):
        if y is None or not isinstance(y, (int, float)):
            raise InvalidDatasetError(f"label {i} is not a number")
        if isinstance(y, float) and not math.isfinite(y):
            raise InvalidDatasetError(f"label {i} is not finite")


# ---------------------------------------------------------------------------
# deterministic parameter derivation
# ---------------------------------------------------------------------------


def _class_means(
    features: Tuple[Tuple[float, ...], ...], labels: Tuple[float, ...]
) -> Tuple[List[float], List[float], int, int]:
    n_features = len(features[0])
    pos_cnt = sum(1 for y in labels if y == 1.0)
    neg_cnt = sum(1 for y in labels if y == 0.0)
    pos_sum = [0.0] * n_features
    neg_sum = [0.0] * n_features
    for row, y in zip(features, labels):
        if y == 1.0:
            for j in range(n_features):
                pos_sum[j] += float(row[j])
        elif y == 0.0:
            for j in range(n_features):
                neg_sum[j] += float(row[j])
    pos_mean = [s / pos_cnt if pos_cnt else 0.0 for s in pos_sum]
    neg_mean = [s / neg_cnt if neg_cnt else 0.0 for s in neg_sum]
    return pos_mean, neg_mean, pos_cnt, neg_cnt


def _feature_weights(
    features: Tuple[Tuple[float, ...], ...], labels: Tuple[float, ...]
) -> List[float]:
    pos_mean, neg_mean, _, _ = _class_means(features, labels)
    return [p - n for p, n in zip(pos_mean, neg_mean)]


def _l1_normalize(weights: List[float]) -> List[float]:
    total = sum(abs(w) for w in weights)
    if total == 0.0:
        return [0.0] * len(weights)
    return [w / total for w in weights]


def _best_separating_feature(
    features: Tuple[Tuple[float, ...], ...], labels: Tuple[float, ...]
) -> Tuple[int, float, float, float]:
    pos_mean, neg_mean, _, _ = _class_means(features, labels)
    diffs = [p - n for p, n in zip(pos_mean, neg_mean)]
    index = max(range(len(diffs)), key=lambda j: abs(diffs[j]))
    return index, diffs[index], pos_mean[index], neg_mean[index]


# ---------------------------------------------------------------------------
# deterministic predictors
# ---------------------------------------------------------------------------


def _predict_feature_weight(row, parameters: Mapping[str, Any]) -> float:
    weights = parameters["weights"]
    score = sum(w * float(x) for w, x in zip(weights, row))
    return 1.0 if score > 0.0 else 0.0


def _predict_linear_formula(row, parameters: Mapping[str, Any]) -> float:
    weights = parameters["weights"]
    bias = parameters["bias"]
    score = sum(w * float(x) for w, x in zip(weights, row)) + bias
    return 1.0 if score > 0.0 else 0.0


def _predict_threshold(row, parameters: Mapping[str, Any]) -> float:
    value = float(row[parameters["feature_index"]])
    threshold = parameters["threshold"]
    if parameters["direction"] == 1:
        return 1.0 if value > threshold else 0.0
    return 1.0 if value < threshold else 0.0


def _predict_rule_based(row, parameters: Mapping[str, Any]) -> float:
    value = float(row[parameters["feature_index"]])
    threshold = parameters["threshold"]
    if parameters["operator"] == "gt":
        return 1.0 if value > threshold else 0.0
    return 1.0 if value < threshold else 0.0


_PREDICTORS = {
    ModelType.FEATURE_WEIGHT: _predict_feature_weight,
    ModelType.LINEAR_FORMULA: _predict_linear_formula,
    ModelType.THRESHOLD: _predict_threshold,
    ModelType.RULE_BASED: _predict_rule_based,
}


class Trainer:
    """Deterministic research-model trainer (architecture only, not ML)."""

    def train(self, dataset: ResearchDataset, config: TrainConfig) -> TrainingResult:
        """Train a deterministic research model and return a ``TrainingResult``.

        The same dataset + config always produce the identical result.
        """
        validate_dataset(dataset)
        if not isinstance(config, TrainConfig):
            raise TypeError("config must be a TrainConfig")

        label_name = config.label_name or dataset.label_name
        parameters = self._derive_parameters(dataset, config.model_type)
        dhash = dataset_hash(dataset)
        model = ModelContract(
            model_id=config.model_id,
            name=config.name,
            version=config.version,
            model_type=config.model_type,
            feature_names=tuple(dataset.feature_names),
            label_name=label_name,
            parameters=parameters,
            metadata=dict(config.metadata),
            created_at=config.created_at,
            training_hash=dhash,
        )
        predictions = self.predict(model, dataset)
        metrics = compute_metrics(dataset.labels, predictions)
        return TrainingResult(
            model=model,
            metrics=metrics,
            dataset_hash=dhash,
            n_samples=len(dataset.features),
            n_features=len(dataset.feature_names),
            predictions=tuple(predictions),
            metadata={"trainer_version": TRAINING_VERSION},
        )

    def predict(self, model: ModelContract, dataset: ResearchDataset) -> List[float]:
        """Apply a trained model deterministically to a dataset."""
        validate_dataset(dataset)
        if not isinstance(model, ModelContract):
            raise TypeError("model must be a ModelContract")
        predictor = _PREDICTORS[model.model_type]
        parameters = dict(model.parameters)
        return [predictor(row, parameters) for row in dataset.features]

    def _derive_parameters(
        self, dataset: ResearchDataset, model_type: ModelType
    ) -> Dict[str, Any]:
        features = dataset.features
        labels = dataset.labels
        if model_type == ModelType.FEATURE_WEIGHT:
            weights = _l1_normalize(_feature_weights(features, labels))
            return {"weights": weights, "operator": "positive"}
        if model_type == ModelType.LINEAR_FORMULA:
            weights = _feature_weights(features, labels)
            scores = [
                sum(w * float(x) for w, x in zip(weights, row)) for row in features
            ]
            bias = -sum(scores) / len(scores)
            return {"weights": weights, "bias": bias, "operator": "positive"}
        if model_type == ModelType.THRESHOLD:
            index, diff, pos_mean, neg_mean = _best_separating_feature(
                features, labels
            )
            threshold = (pos_mean + neg_mean) / 2.0
            direction = 1 if diff >= 0 else -1
            return {
                "feature_index": index,
                "feature_name": dataset.feature_names[index],
                "threshold": threshold,
                "direction": direction,
            }
        if model_type == ModelType.RULE_BASED:
            index, diff, pos_mean, neg_mean = _best_separating_feature(
                features, labels
            )
            threshold = (pos_mean + neg_mean) / 2.0
            operator = "gt" if diff >= 0 else "lt"
            return {
                "feature_index": index,
                "feature_name": dataset.feature_names[index],
                "operator": operator,
                "threshold": threshold,
            }
        raise InvalidModelError(f"unsupported model type: {model_type}")

    # ------------------------------------------------------------------
    # convenience entry points
    # ------------------------------------------------------------------

    def train_rule_based(self, dataset, model_id, name="Rule Based", **kwargs):
        return self.train(
            dataset,
            TrainConfig(
                model_id=model_id, name=name, model_type=ModelType.RULE_BASED, **kwargs
            ),
        )

    def train_linear_formula(self, dataset, model_id, name="Linear Formula", **kwargs):
        return self.train(
            dataset,
            TrainConfig(
                model_id=model_id,
                name=name,
                model_type=ModelType.LINEAR_FORMULA,
                **kwargs,
            ),
        )

    def train_threshold(self, dataset, model_id, name="Threshold", **kwargs):
        return self.train(
            dataset,
            TrainConfig(
                model_id=model_id, name=name, model_type=ModelType.THRESHOLD, **kwargs
            ),
        )

    def train_feature_weight(self, dataset, model_id, name="Feature Weight", **kwargs):
        return self.train(
            dataset,
            TrainConfig(
                model_id=model_id,
                name=name,
                model_type=ModelType.FEATURE_WEIGHT,
                **kwargs,
            ),
        )


__all__ = ["TrainConfig", "Trainer", "dataset_hash", "validate_dataset"]

