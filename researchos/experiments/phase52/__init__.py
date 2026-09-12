"""
Phase 5.2 — macro-augmented (DXY / US10Y / VIX) XAUUSD predictive-value
experiment.

Builds on the frozen Phase 5.1 scientific primitives without modifying them.
Feature-set comparisons are explicit and deterministic.
"""

from .contracts import Phase52Result
from .experiment import FEATURE_SET_NAMES, Phase52Config, run_phase52, run_phase52_comparison
from .macro_features import MACRO_SYMBOLS, MacroFeatureBuilder, MacroFeatureSet
from .multivariate import MultivariateEmpiricalProbabilityEstimator
from .oos_calibration import CalibrationComparison, apply_temperature, calibrate_oos, fit_temperature

__all__ = [
    "FEATURE_SET_NAMES",
    "Phase52Config",
    "Phase52Result",
    "run_phase52",
    "run_phase52_comparison",
    "MACRO_SYMBOLS",
    "MacroFeatureBuilder",
    "MacroFeatureSet",
    "MultivariateEmpiricalProbabilityEstimator",
    "CalibrationComparison",
    "apply_temperature",
    "calibrate_oos",
    "fit_temperature",
]
