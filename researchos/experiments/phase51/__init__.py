"""Phase 5.1 — XAUUSD predictive-value experiment."""

from .baseline import baseline_always_predict, evaluate_baseline, majority_class_from_train
from .calibration import evaluate_calibration
from .contracts import HASH_ALGORITHM, PHASE51_VERSION, BaselineResult, CalibrationResult, CostResult, ModelResult, Outcome, Phase51Result, SignificanceResult, ValidationFlags
from .cost import apply_costs
from .experiment import Phase51Config, run_phase51, run_phase51_research
from .probability import FEATURE_NAMES, EmpiricalProbabilityEstimator
from .self_validation import aggregate_outcome
from .statistics import confidence_interval_diff, evaluate_significance

__all__ = [
    "PHASE51_VERSION", "HASH_ALGORITHM", "Outcome", "BaselineResult", "ModelResult",
    "CostResult", "CalibrationResult", "SignificanceResult", "ValidationFlags", "Phase51Result",
    "majority_class_from_train", "baseline_always_predict", "evaluate_baseline",
    "EmpiricalProbabilityEstimator", "FEATURE_NAMES", "evaluate_calibration", "evaluate_significance",
    "confidence_interval_diff", "apply_costs", "aggregate_outcome", "Phase51Config",
    "run_phase51", "run_phase51_research",
]
