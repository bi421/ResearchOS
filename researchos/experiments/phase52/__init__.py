"""
Phase 5.2 — macro-augmented (DXY / US10Y / VIX) XAUUSD predictive-value
experiment.

Builds on the frozen Phase 5.1 scientific primitives (walk-forward
validation, calibration, significance testing, cost adjustment,
self-validation flags) without modifying them, adding macro factor
conditioning as a new, separately-tracked experiment.

See ``researchos.experiments.phase51`` for the underlying, unmodified
scientific infrastructure this phase composes.
"""

from .contracts import Phase52Result
from .experiment import Phase52Config, run_phase52
from .macro_features import MACRO_SYMBOLS, MacroFeatureBuilder, MacroFeatureSet

__all__ = [
    "Phase52Config",
    "Phase52Result",
    "run_phase52",
    "MACRO_SYMBOLS",
    "MacroFeatureBuilder",
    "MacroFeatureSet",
]
