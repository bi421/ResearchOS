"""
ResearchOS Macro Intelligence Layer - Regime Transition Rules

Immutable, versioned rules for transition type classification.
All rules are defined as frozen ClassificationRule instances.
"""

from __future__ import annotations

from macro_intelligence.regime.classification.taxonomy import MacroRegime
from macro_intelligence.regime.transition.models import TransitionType

# =============================================================================
# Algorithm version
# =============================================================================

RULES_VERSION = "trans-rules/v4.0.0"

# =============================================================================
# Transition strength thresholds
# =============================================================================

# Confidence thresholds for transition type classification
_CONFIDENCE_HIGH = 0.80
_CONFIDENCE_MEDIUM = 0.60
_CONFIDENCE_LOW = 0.40

# Signal agreement thresholds
_SIGNALS_AGREE_THRESHOLD = 0.70  # Fraction of detectors agreeing
_SIGNALS_SPLIT_THRESHOLD = 0.40  # Fraction disagreeing

# Persistence thresholds (in periods)
_PERSISTENCE_SHORT = 3
_PERSISTENCE_MEDIUM = 8
_PERSISTENCE_LONG = 16

# Early warning thresholds
_EARLY_WARNING_MIN_CONFIDENCE = 0.50
_EARLY_WARNING_MIN_HORIZON = 2


# =============================================================================
# Transition type classification rules
# =============================================================================


def classify_transition_type(
    signal_strengths: list[float],
    signal_agreement: float,
    confidence: float,
    persistence_periods: int,
) -> str:
    """
    Classify transition type based on signal characteristics.

    Returns one of: TransitionType.STABLE, GRADUAL_SHIFT, ACCELERATED_SHIFT,
    REVERSAL, VOLATILE, UNKNOWN
    """
    if not signal_strengths:
        return TransitionType.UNKNOWN

    avg_strength = sum(signal_strengths) / len(signal_strengths)
    max(signal_strengths)
    min(signal_strengths)
    strength_variance = sum((s - avg_strength) ** 2 for s in signal_strengths) / len(signal_strengths)

    # STABLE: no significant signals
    if confidence < _CONFIDENCE_LOW and avg_strength < 0.3:
        return TransitionType.STABLE

    # VOLATILE: high variance in signals (detectors disagree strongly)
    if strength_variance > 0.15 and signal_agreement < _SIGNALS_SPLIT_THRESHOLD:
        return TransitionType.VOLATILE

    # REVERSAL: high confidence, high strength, short persistence
    if (
        confidence >= _CONFIDENCE_HIGH
        and avg_strength >= 0.7
        and persistence_periods < _PERSISTENCE_SHORT
    ):
        return TransitionType.REVERSAL

    # ACCELERATED_SHIFT: high confidence, moderate-high strength
    if confidence >= _CONFIDENCE_MEDIUM and avg_strength >= 0.5:
        return TransitionType.ACCELERATED_SHIFT

    # GRADUAL_SHIFT: moderate confidence, moderate strength
    if confidence >= _CONFIDENCE_LOW and avg_strength >= 0.3:
        return TransitionType.GRADUAL_SHIFT

    # Default
    return TransitionType.STABLE


# =============================================================================
# Early warning rules
# =============================================================================


def should_generate_early_warning(
    confidence: float,
    horizon_periods: int,
    signal_strengths: list[float],
) -> bool:
    """Determine if an early warning should be generated."""
    avg_strength = sum(signal_strengths) / len(signal_strengths) if signal_strengths else 0
    return (
        confidence >= _EARLY_WARNING_MIN_CONFIDENCE
        and horizon_periods >= _EARLY_WARNING_MIN_HORIZON
        and avg_strength >= 0.3
    )


def estimate_early_warning_horizon(
    signal_strengths: list[float],
    confidence: float,
) -> int:
    """
    Estimate the horizon (in periods) until a predicted transition.

    Higher signal strength and confidence → shorter horizon.
    """
    if not signal_strengths:
        return 0

    avg_strength = sum(signal_strengths) / len(signal_strengths)
    # Base horizon: 12 periods, reduced by signal strength and confidence
    base_horizon = 12
    reduction = avg_strength * 0.4 + confidence * 0.3
    horizon = max(2, int(base_horizon * (1 - reduction)))
    return horizon


# =============================================================================
# Persistence calculation rules
# =============================================================================


def calculate_continuation_probability(
    persistence_periods: int,
    avg_persistence: float,
    signal_strengths: list[float],
) -> float:
    """
    Calculate probability that current regime will continue.

    Returns a value between 0.0 and 1.0.
    """
    if avg_persistence <= 0:
        avg_persistence = 6.0  # Default assumption

    # Base probability from persistence ratio
    persistence_ratio = persistence_periods / avg_persistence
    base_prob = 1.0 / (1.0 + max(0, persistence_ratio - 1.0) * 0.3)

    # Adjust by signal strength (strong signals → lower continuation prob)
    avg_signal = sum(signal_strengths) / len(signal_strengths) if signal_strengths else 0
    signal_adjustment = -avg_signal * 0.3

    probability = max(0.0, min(1.0, base_prob + signal_adjustment))
    return round(probability, 2)


# =============================================================================
# Transition probability matrix rules
# =============================================================================

# Historical prior probabilities (seed values for the matrix)
# These are conservative starting points that get updated with observations
DEFAULT_TRANSITION_PROBS: dict[str, dict[str, float]] = {
    MacroRegime.GOLDILOCKS.value: {
        MacroRegime.GOLDILOCKS.value: 0.55,
        MacroRegime.INFLATIONARY_GROWTH.value: 0.15,
        MacroRegime.DISINFLATION.value: 0.15,
        MacroRegime.STAGFLATION.value: 0.05,
        MacroRegime.DEFLATIONARY_SLOWDOWN.value: 0.05,
        MacroRegime.RECESSION.value: 0.05,
    },
    MacroRegime.INFLATIONARY_GROWTH.value: {
        MacroRegime.INFLATIONARY_GROWTH.value: 0.40,
        MacroRegime.GOLDILOCKS.value: 0.10,
        MacroRegime.STAGFLATION.value: 0.25,
        MacroRegime.DISINFLATION.value: 0.10,
        MacroRegime.RECESSION.value: 0.10,
        MacroRegime.DEFLATIONARY_SLOWDOWN.value: 0.05,
    },
    MacroRegime.STAGFLATION.value: {
        MacroRegime.STAGFLATION.value: 0.35,
        MacroRegime.RECESSION.value: 0.25,
        MacroRegime.DISINFLATION.value: 0.15,
        MacroRegime.INFLATIONARY_GROWTH.value: 0.10,
        MacroRegime.DEFLATIONARY_SLOWDOWN.value: 0.10,
        MacroRegime.GOLDILOCKS.value: 0.05,
    },
    MacroRegime.DISINFLATION.value: {
        MacroRegime.DISINFLATION.value: 0.45,
        MacroRegime.GOLDILOCKS.value: 0.20,
        MacroRegime.DEFLATIONARY_SLOWDOWN.value: 0.15,
        MacroRegime.STAGFLATION.value: 0.10,
        MacroRegime.RECESSION.value: 0.05,
        MacroRegime.INFLATIONARY_GROWTH.value: 0.05,
    },
    MacroRegime.DEFLATIONARY_SLOWDOWN.value: {
        MacroRegime.DEFLATIONARY_SLOWDOWN.value: 0.40,
        MacroRegime.RECESSION.value: 0.25,
        MacroRegime.DISINFLATION.value: 0.15,
        MacroRegime.GOLDILOCKS.value: 0.10,
        MacroRegime.STAGFLATION.value: 0.05,
        MacroRegime.INFLATIONARY_GROWTH.value: 0.05,
    },
    MacroRegime.RECESSION.value: {
        MacroRegime.RECESSION.value: 0.35,
        MacroRegime.DEFLATIONARY_SLOWDOWN.value: 0.20,
        MacroRegime.DISINFLATION.value: 0.15,
        MacroRegime.GOLDILOCKS.value: 0.10,
        MacroRegime.STAGFLATION.value: 0.10,
        MacroRegime.INFLATIONARY_GROWTH.value: 0.10,
    },
}


def get_default_transition_probs() -> dict[str, dict[str, float]]:
    """Return a deep copy of the default transition probability matrix."""
    import copy
    return copy.deepcopy(DEFAULT_TRANSITION_PROBS)


def normalize_transition_probs(probs: dict[str, float]) -> dict[str, float]:
    """Normalize a probability distribution to sum to 1.0."""
    total = sum(probs.values())
    if total <= 0:
        # Uniform distribution
        n = len(probs)
        return {k: 1.0 / n for k in probs}
    return {k: v / total for k, v in probs.items()}


def update_transition_probs(
    current_probs: dict[str, dict[str, float]],
    observed_transitions: list[tuple[str, str]],
    alpha: float = 0.1,
) -> dict[str, dict[str, float]]:
    """
    Update transition probability matrix with new observations.

    Uses exponential moving average with smoothing factor alpha.

    Args:
        current_probs: Current probability matrix
        observed_transitions: List of (from_regime, to_regime) tuples
        alpha: Smoothing factor (0=ignore new data, 1=only new data)

    Returns:
        Updated probability matrix
    """
    import copy
    updated = copy.deepcopy(current_probs)

    # Count transitions
    counts: dict[str, dict[str, int]] = {}
    for from_r, to_r in observed_transitions:
        if from_r not in counts:
            counts[from_r] = {}
        if to_r not in counts[from_r]:
            counts[from_r][to_r] = 0
        counts[from_r][to_r] += 1

    # Update each source regime's probabilities
    for from_r, targets in counts.items():
        if from_r not in updated:
            updated[from_r] = {}
        total_count = sum(targets.values())
        for to_r, count in targets.items():
            observed_prob = count / total_count if total_count > 0 else 0
            current_prob = updated[from_r].get(to_r, 0.0)
            updated[from_r][to_r] = alpha * observed_prob + (1 - alpha) * current_prob

    # Normalize all rows
    for from_r in updated:
        updated[from_r] = normalize_transition_probs(updated[from_r])

    # Ensure all regimes have entries for all possible target regimes
    all_regimes = list(DEFAULT_TRANSITION_PROBS.keys())
    for from_r in all_regimes:
        if from_r not in updated:
            updated[from_r] = {}
        for to_r in all_regimes:
            if to_r not in updated[from_r]:
                updated[from_r][to_r] = DEFAULT_TRANSITION_PROBS[from_r].get(to_r, 0.0)
        updated[from_r] = normalize_transition_probs(updated[from_r])

    return updated
