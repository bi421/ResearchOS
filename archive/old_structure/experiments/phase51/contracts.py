"""
Phase 5.1 — deterministic result contract.

Defines the frozen, deterministic output of a Phase 5.1 XAUUSD predictive
value experiment.  The result distinguishes four outcomes:

    * ``PASS``        — model beats the defensible baseline out-of-sample,
                        after costs, with the configured confidence criteria.
    * ``FAIL``        — model does NOT beat the baseline (or loses after costs).
    * ``UNCERTAIN``   — data/evaluation insufficient to conclude either way.
    * ``BLOCKED``     — real XAUUSD data is required but not supplied.

``BLOCKED`` is never interpreted as model success or failure.

Guarantees:
    * Deterministic: same inputs -> same ``reproducibility_hash``.
    * Additive: composes existing ``researchos`` infrastructure.
    * No empirical claim is made unless real XAUUSD data is supplied.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

PHASE51_VERSION = "1.0.0"
HASH_ALGORITHM = "sha256"


class Outcome(str):
    """Valid Phase 5.1 experiment outcomes."""

    PASS = "PASS"
    FAIL = "FAIL"
    UNCERTAIN = "UNCERTAIN"
    BLOCKED = "BLOCKED"


def _canonical(value: Any) -> Any:
    """Return a deterministic, JSON-serializable canonical form of ``value``."""
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
    """Deterministic SHA-256 digest of a canonicalizable result payload."""
    payload = _canonical(content)
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


@dataclass(frozen=True)
class BaselineResult:
    """Out-of-sample performance of the unconditional-frequency baseline."""

    accuracy: float
    precision_up: float
    precision_down: float
    recall_up: float
    recall_down: float
    brier_score: float
    class_frequencies: dict[str, float]
    sample_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "accuracy": self.accuracy,
            "precision_up": self.precision_up,
            "precision_down": self.precision_down,
            "recall_up": self.recall_up,
            "recall_down": self.recall_down,
            "brier_score": self.brier_score,
            "class_frequencies": dict(self.class_frequencies),
            "sample_count": self.sample_count,
        }


@dataclass(frozen=True)
class ModelResult:
    """Out-of-sample performance of the empirical probability estimator."""

    accuracy: float
    precision_up: float
    precision_down: float
    recall_up: float
    recall_down: float
    brier_score: float
    sample_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "accuracy": self.accuracy,
            "precision_up": self.precision_up,
            "precision_down": self.precision_down,
            "recall_up": self.recall_up,
            "recall_down": self.recall_down,
            "brier_score": self.brier_score,
            "sample_count": self.sample_count,
        }


@dataclass(frozen=True)
class CostResult:
    """Net-of-cost impact of spread/slippage/commission on direction accuracy."""

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
        return {
            "cost_model": self.cost_model,
            "spread_cost_per_bar": self.spread_cost_per_bar,
            "slippage_cost_per_bar": self.slippage_cost_per_bar,
            "commission_cost_per_bar": self.commission_cost_per_bar,
            "gross_accuracy": self.gross_accuracy,
            "net_accuracy_up": self.net_accuracy_up,
            "net_accuracy_down": self.net_accuracy_down,
            "net_accuracy_all": self.net_accuracy_all,
            "cost_applied": self.cost_applied,
        }


@dataclass(frozen=True)
class CalibrationResult:
    """Calibration (reliability) assessment of predicted probabilities."""

    num_bins: int
    reliability_table: Mapping[str, Any]
    brier_score: float
    avg_confidence: float
    avg_accuracy: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "num_bins": self.num_bins,
            "reliability_table": dict(self.reliability_table),
            "brier_score": self.brier_score,
            "avg_confidence": self.avg_confidence,
            "avg_accuracy": self.avg_accuracy,
        }


@dataclass(frozen=True)
class SignificanceResult:
    """Statistical significance of model-vs-baseline difference."""

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
        return {
            "n_up": self.n_up,
            "n_down": self.n_down,
            "n_neutral": self.n_neutral,
            "model_better_count": self.model_better_count,
            "baseline_better_count": self.baseline_better_count,
            "tie_count": self.tie_count,
            "p_value": self.p_value,
            "significant": self.significant,
            "method": self.method,
        }


@dataclass(frozen=True)
class ValidationFlags:
    """Self-validation flags and the aggregated outcome."""

    data_valid: bool
    leakage_check: bool
    out_of_sample: bool
    cost_adjusted: bool
    reproducible: bool
    outcome: str
    reasons: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "data_valid": self.data_valid,
            "leakage_check": self.leakage_check,
            "out_of_sample": self.out_of_sample,
            "cost_adjusted": self.cost_adjusted,
            "reproducible": self.reproducible,
            "outcome": self.outcome,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class Phase51Result:
    """
    Immutable, deterministic result of a Phase 5.1 experiment.

    The ``reproducibility_hash`` covers every deterministic field so identical
    inputs always produce an identical result.  Observational fields (e.g.
    ``execution_timestamp``) are excluded by design.
    """

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
        object.__setattr__(
            self,
            "reproducibility_hash",
            reproducibility_hash(self._hashable_content()),
        )

    def _hashable_content(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "horizon": self.horizon,
            "threshold": self.threshold,
            "train_size": self.train_size,
            "validation_size": self.validation_size,
            "step_size": self.step_size,
            "num_folds": self.num_folds,
            "baseline": self.baseline.to_dict() if self.baseline else None,
            "model": self.model.to_dict() if self.model else None,
            "cost": self.cost.to_dict() if self.cost else None,
            "calibration": self.calibration.to_dict() if self.calibration else None,
            "significance": self.significance.to_dict() if self.significance else None,
            "validation": self.validation.to_dict(),
            "metadata": dict(self.metadata),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "horizon": self.horizon,
            "threshold": self.threshold,
            "train_size": self.train_size,
            "validation_size": self.validation_size,
            "step_size": self.step_size,
            "num_folds": self.num_folds,
            "baseline": self.baseline.to_dict() if self.baseline else None,
            "model": self.model.to_dict() if self.model else None,
            "cost": self.cost.to_dict() if self.cost else None,
            "calibration": self.calibration.to_dict() if self.calibration else None,
            "significance": self.significance.to_dict() if self.significance else None,
            "validation": self.validation.to_dict(),
            "metadata": dict(self.metadata),
            "reproducibility_hash": self.reproducibility_hash,
        }

    @classmethod
    def blocked(
        cls,
        symbol: str = "XAUUSD",
        timeframe: str = "1d",
        reason: str = "REAL XAUUSD DATA REQUIRED",
    ) -> Phase51Result:
        """Construct a BLOCKED result — real data is gating, not a model outcome."""
        validation = ValidationFlags(
            data_valid=False,
            leakage_check=False,
            out_of_sample=False,
            cost_adjusted=False,
            reproducible=True,
            outcome=Outcome.BLOCKED,
            reasons=(reason,),
        )
        return cls(
            outcome=Outcome.BLOCKED,
            symbol=symbol,
            timeframe=timeframe,
            horizon=0,
            threshold=0.0,
            train_size=0,
            validation_size=0,
            step_size=0,
            num_folds=0,
            baseline=None,
            model=None,
            cost=None,
            calibration=None,
            significance=None,
            validation=validation,
            metadata={"blocked_reason": reason},
        )


__all__ = [
    "PHASE51_VERSION",
    "HASH_ALGORITHM",
    "Outcome",
    "BaselineResult",
    "ModelResult",
    "CostResult",
    "CalibrationResult",
    "SignificanceResult",
    "ValidationFlags",
    "Phase51Result",
    "reproducibility_hash",
]
