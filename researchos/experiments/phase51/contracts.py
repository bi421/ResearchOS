"""Phase 5.1 deterministic result contract."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

PHASE51_VERSION = "1.1.0"
HASH_ALGORITHM = "sha256"


class Outcome(str):
    PASS = "PASS"
    FAIL = "FAIL"
    UNCERTAIN = "UNCERTAIN"
    BLOCKED = "BLOCKED"


def _canonical(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=str)}
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if math.isnan(value):
            return "NaN"
        if math.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"
        if value == 0.0:
            return "0.0"
        return repr(value)
    if value is None or isinstance(value, str):
        return value
    return str(value)


def reproducibility_hash(content: Any) -> str:
    payload = _canonical(content)
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


@dataclass(frozen=True)
class BaselineResult:
    accuracy: float
    precision_up: float
    precision_down: float
    recall_up: float
    recall_down: float
    brier_score: float
    class_frequencies: dict[str, float]
    sample_count: int
    def to_dict(self) -> dict[str, Any]:
        return {"accuracy": self.accuracy, "precision_up": self.precision_up, "precision_down": self.precision_down, "recall_up": self.recall_up, "recall_down": self.recall_down, "brier_score": self.brier_score, "class_frequencies": dict(self.class_frequencies), "sample_count": self.sample_count}


@dataclass(frozen=True)
class ModelResult:
    accuracy: float
    precision_up: float
    precision_down: float
    recall_up: float
    recall_down: float
    brier_score: float
    sample_count: int
    def to_dict(self) -> dict[str, Any]:
        return {"accuracy": self.accuracy, "precision_up": self.precision_up, "precision_down": self.precision_down, "recall_up": self.recall_up, "recall_down": self.recall_down, "brier_score": self.brier_score, "sample_count": self.sample_count}


@dataclass(frozen=True)
class CostResult:
    cost_model: str
    spread_cost_per_bar: float
    slippage_cost_per_bar: float
    commission_cost_per_bar: float
    gross_accuracy: float
    net_accuracy_up: float
    net_accuracy_down: float
    net_accuracy_all: float
    cost_applied: bool
    def to_dict(self) -> dict[str, Any]:
        return {"cost_model": self.cost_model, "spread_cost_per_bar": self.spread_cost_per_bar, "slippage_cost_per_bar": self.slippage_cost_per_bar, "commission_cost_per_bar": self.commission_cost_per_bar, "gross_accuracy": self.gross_accuracy, "net_accuracy_up": self.net_accuracy_up, "net_accuracy_down": self.net_accuracy_down, "net_accuracy_all": self.net_accuracy_all, "cost_applied": self.cost_applied}


@dataclass(frozen=True)
class CalibrationResult:
    num_bins: int
    reliability_table: Mapping[str, Any]
    brier_score: float
    avg_confidence: float
    avg_accuracy: float
    def to_dict(self) -> dict[str, Any]:
        return {"num_bins": self.num_bins, "reliability_table": dict(self.reliability_table), "brier_score": self.brier_score, "avg_confidence": self.avg_confidence, "avg_accuracy": self.avg_accuracy}


@dataclass(frozen=True)
class SignificanceResult:
    n_up: int
    n_down: int
    n_neutral: int
    model_better_count: int
    baseline_better_count: int
    tie_count: int
    p_value: float
    significant: bool
    method: str
    def to_dict(self) -> dict[str, Any]:
        return {"n_up": self.n_up, "n_down": self.n_down, "n_neutral": self.n_neutral, "model_better_count": self.model_better_count, "baseline_better_count": self.baseline_better_count, "tie_count": self.tie_count, "p_value": self.p_value, "significant": self.significant, "method": self.method}


@dataclass(frozen=True)
class ValidationFlags:
    data_valid: bool
    leakage_check: bool
    out_of_sample: bool
    cost_adjusted: bool
    reproducible: bool
    outcome: str
    reasons: tuple[str, ...] = field(default_factory=tuple)
    def to_dict(self) -> dict[str, Any]:
        return {"data_valid": self.data_valid, "leakage_check": self.leakage_check, "out_of_sample": self.out_of_sample, "cost_adjusted": self.cost_adjusted, "reproducible": self.reproducible, "outcome": self.outcome, "reasons": list(self.reasons)}


@dataclass(frozen=True)
class Phase51Result:
    outcome: str
    symbol: str
    timeframe: str
    horizon: int
    threshold: float
    train_size: int
    validation_size: int
    step_size: int
    num_folds: int
    baseline: BaselineResult | None
    model: ModelResult | None
    cost: CostResult | None
    calibration: CalibrationResult | None
    significance: SignificanceResult | None
    validation: ValidationFlags
    metadata: Mapping[str, Any]
    reproducibility_hash: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "reproducibility_hash", reproducibility_hash(self._hashable_content()))

    def _hashable_content(self) -> dict[str, Any]:
        return {"outcome": self.outcome, "symbol": self.symbol, "timeframe": self.timeframe, "horizon": self.horizon, "threshold": self.threshold, "train_size": self.train_size, "validation_size": self.validation_size, "step_size": self.step_size, "num_folds": self.num_folds, "baseline": self.baseline.to_dict() if self.baseline else None, "model": self.model.to_dict() if self.model else None, "cost": self.cost.to_dict() if self.cost else None, "calibration": self.calibration.to_dict() if self.calibration else None, "significance": self.significance.to_dict() if self.significance else None, "validation": self.validation.to_dict(), "metadata": dict(self.metadata)}

    def to_dict(self) -> dict[str, Any]:
        result = self._hashable_content()
        result["reproducibility_hash"] = self.reproducibility_hash
        return result

    @classmethod
    def blocked(cls, symbol: str = "XAUUSD", timeframe: str = "1d", reason: str = "REAL XAUUSD DATA REQUIRED") -> "Phase51Result":
        validation = ValidationFlags(False, False, False, False, True, Outcome.BLOCKED, (reason,))
        return cls(Outcome.BLOCKED, symbol, timeframe, 0, 0.0, 0, 0, 0, 0, None, None, None, None, None, validation, {"blocked_reason": reason})


__all__ = ["PHASE51_VERSION", "HASH_ALGORITHM", "Outcome", "BaselineResult", "ModelResult", "CostResult", "CalibrationResult", "SignificanceResult", "ValidationFlags", "Phase51Result", "reproducibility_hash"]
