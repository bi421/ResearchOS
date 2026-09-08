"""
Phase 5.2 — deterministic result contract (macro-augmented XAUUSD experiment).

Reuses ``BaselineResult``, ``ModelResult``, ``CostResult``,
``CalibrationResult``, ``SignificanceResult``, ``ValidationFlags``,
``Outcome`` and ``reproducibility_hash`` from the frozen Phase 5.1 contracts
unmodified — those primitives are generic (baseline/cost/calibration math
does not depend on which features were used) and importing them keeps the
scientific bookkeeping (PASS/FAIL/UNCERTAIN/BLOCKED semantics, hash scheme)
identical across phases so results are directly comparable.

``Phase52Result`` adds one thing Phase 5.1 does not need: a record of which
macro symbols (DXY/US10Y/VIX) were actually available and used, since a
macro-conditioned result is only meaningful if the macro data was real and
present for every bar in the sample.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from researchos.experiments.phase51.contracts import (
    BaselineResult,
    CalibrationResult,
    CostResult,
    ModelResult,
    Outcome,
    SignificanceResult,
    ValidationFlags,
    reproducibility_hash,
)

PHASE52_VERSION = "1.0.0"


@dataclass(frozen=True)
class Phase52Result:
    """Immutable, deterministic result of a Phase 5.2 macro-augmented experiment."""

    outcome: str
    symbol: str
    timeframe: str
    horizon: int
    threshold: float
    train_size: int
    validation_size: int
    step_size: int
    num_folds: int
    macro_symbols_present: tuple[str, ...]
    macro_symbols_missing: tuple[str, ...]
    estimator_feature_name: str
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
            "macro_symbols_present": list(self.macro_symbols_present),
            "macro_symbols_missing": list(self.macro_symbols_missing),
            "estimator_feature_name": self.estimator_feature_name,
            "baseline": self.baseline.to_dict() if self.baseline else None,
            "model": self.model.to_dict() if self.model else None,
            "cost": self.cost.to_dict() if self.cost else None,
            "calibration": self.calibration.to_dict() if self.calibration else None,
            "significance": self.significance.to_dict() if self.significance else None,
            "validation": self.validation.to_dict(),
            "metadata": dict(self.metadata),
        }

    def to_dict(self) -> dict[str, Any]:
        d = self._hashable_content()
        d["reproducibility_hash"] = self.reproducibility_hash
        return d

    @classmethod
    def blocked(
        cls,
        symbol: str = "XAUUSD",
        timeframe: str = "1d",
        reason: str = "REAL XAUUSD + MACRO DATA REQUIRED",
        macro_symbols_present: tuple[str, ...] = (),
        macro_symbols_missing: tuple[str, ...] = (),
    ) -> Phase52Result:
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
            macro_symbols_present=macro_symbols_present,
            macro_symbols_missing=macro_symbols_missing,
            estimator_feature_name="",
            baseline=None,
            model=None,
            cost=None,
            calibration=None,
            significance=None,
            validation=validation,
            metadata={"blocked_reason": reason},
        )


__all__ = [
    "PHASE52_VERSION",
    "Outcome",
    "BaselineResult",
    "ModelResult",
    "CostResult",
    "CalibrationResult",
    "SignificanceResult",
    "ValidationFlags",
    "Phase52Result",
    "reproducibility_hash",
]
