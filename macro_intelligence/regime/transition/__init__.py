"""
ResearchOS Macro Intelligence Layer - Regime Transition Package

Provides deterministic regime transition analysis.

All transition detectors are:
- Pure functions (no mutable state)
- Deterministic (same input always produces same output)
- Stateless (no caches, no randomness)
- Provenance-preserving (output includes evidence references)

Architecture invariants:
- MIL-TRANS-001: Same input produces identical transition output
- MIL-TRANS-002: Transition objects are immutable
- MIL-TRANS-003: All transitions preserve provenance
- MIL-TRANS-004: Algorithms are versioned
- MIL-TRANS-005: No dependency on ResearchOS V1
"""

from __future__ import annotations

from macro_intelligence.regime.transition.models import (
    ALGORITHM_VERSION,
    TransitionType,
    TransitionSignal,
    RegimeTransition,
    TransitionHistoryEntry,
    TransitionProbabilityMatrix,
    RegimePersistence,
    EarlyWarningSignal,
    TransitionAnalysisResult,
)
from macro_intelligence.regime.transition.transitions import (
    RULES_VERSION,
    classify_transition_type,
    should_generate_early_warning,
    estimate_early_warning_horizon,
    calculate_continuation_probability,
    get_default_transition_probs,
    normalize_transition_probs,
    update_transition_probs,
)
from macro_intelligence.regime.transition.probability import TransitionProbabilityEngine
from macro_intelligence.regime.transition.history import TransitionHistory
from macro_intelligence.regime.transition.detector import RegimeTransitionDetector

__all__ = [
    # Models
    "ALGORITHM_VERSION",
    "TransitionType",
    "TransitionSignal",
    "RegimeTransition",
    "TransitionHistoryEntry",
    "TransitionProbabilityMatrix",
    "RegimePersistence",
    "EarlyWarningSignal",
    "TransitionAnalysisResult",
    # Rules
    "RULES_VERSION",
    "classify_transition_type",
    "should_generate_early_warning",
    "estimate_early_warning_horizon",
    "calculate_continuation_probability",
    "get_default_transition_probs",
    "normalize_transition_probs",
    "update_transition_probs",
    # Engine
    "TransitionProbabilityEngine",
    # History
    "TransitionHistory",
    # Detector
    "RegimeTransitionDetector",
]
