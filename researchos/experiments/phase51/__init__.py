"""
Phase 5.1 — XAUUSD predictive-value experiment (additive).

Composes the verified existing ``researchos`` infrastructure to answer:
"Can ResearchOS estimate a defined future XAUUSD outcome better than a
defensible baseline, out-of-sample, after realistic spread/slippage?"

This is a *thin, additive* orchestration layer.  It does not modify protected
architecture and does not duplicate existing components; it reuses:
    * ``quant_engine.machine_learning.DatasetBuilder`` / ``FeatureBuilder`` /
      ``multiclass_label`` for the dataset + target.
    * ``quant_engine.probability.statistics.probability_calibration`` and
      ``confidence_interval_mean`` for calibration / intervals.
    * ``quant_engine.execution.ExecutionSimulationLayer`` / ``parse_cost_spec``
      for cost semantics.

Outcome contract: PASS / FAIL / UNCERTAIN / BLOCKED.  ``BLOCKED`` is the
required outcome when real XAUUSD data is not supplied; it is never an
interpretation of model success or failure.
"""

from .contracts import (
    PHASE51_VERSION,
    HASH_ALGORITHM,
    Outcome,
    BaselineResult,
    ModelResult,
    CostResult,
    CalibrationResult,
    SignificanceResult,
    ValidationFlags,
    Phase51Result,
)
from .baseline import (
    majority_class_from_train,
    baseline_always_predict,
    evaluate_baseline,
)
from .probability import EmpiricalProbabilityEstimator, FEATURE_NAMES
from .calibration import evaluate_calibration
from .statistics import evaluate_significance, confidence_interval_diff
from .cost import apply_costs
from .self_validation import aggregate_outcome
from .experiment import Phase51Config, run_phase51

__all__ = [
    # Contracts
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
    # Baseline
    "majority_class_from_train",
    "baseline_always_predict",
    "evaluate_baseline",
    # Probability
    "EmpiricalProbabilityEstimator",
    "FEATURE_NAMES",
    # Calibration / statistics / cost
    "evaluate_calibration",
    "evaluate_significance",
    "confidence_interval_diff",
    "apply_costs",
    # Self-validation
    "aggregate_outcome",
    # Entrypoint
    "Phase51Config",
    "run_phase51",
]
