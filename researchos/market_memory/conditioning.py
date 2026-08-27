"""
Conditional Analysis — deterministic conditional probability and statistics.

Given a set of market events, computes:
  - P(outcome | condition)
  - Conditional mean, std, confidence intervals
  - Multiple-testing audit trail

All analyses are deterministic and record the exact conditions tested.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from researchos.market_memory.event_schema import (
    ConditionalResult,
    ConditionSpec,
    EvidenceStatus,
    MarketEvent,
)

# =============================================================================
# Condition Evaluation
# =============================================================================


def evaluate_condition(event: MarketEvent, spec: ConditionSpec) -> bool:
    """
    Evaluate whether a single event matches a condition specification.

    Args:
        event: The market event to evaluate
        spec: The condition specification

    Returns:
        True if the event matches all conditions
    """
    if event.outcome is None:
        return False

    ctx = event.context
    for key, value in spec.conditions.items():
        if key == "direction":
            if ctx.market_regime.startswith("Trending"):
                pass
            if event.direction != value:
                return False
        elif key == "market_regime":
            if ctx.market_regime != value:
                return False
        elif key == "volatility_state":
            if ctx.volatility_state != value:
                return False
        elif key == "session":
            if ctx.session != value:
                return False
        elif key == "day_of_week":
            if ctx.day_of_week != value:
                return False
        elif key == "sma_fast_above_slow":
            if bool(ctx.sma_fast > ctx.sma_slow) != value:
                return False
        elif key == "atr_percentile":
            # Not implemented in V1
            return False
        else:
            # Unknown condition key
            return False
    return True


def filter_events(events: list[MarketEvent], spec: ConditionSpec) -> list[MarketEvent]:
    """
    Filter events that match a condition specification.
    """
    return [e for e in events if evaluate_condition(e, spec)]


# =============================================================================
# Conditional Statistics
# =============================================================================


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = _mean(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / len(values))


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return s[int(k)]
    return s[f] * (c - k) + s[c] * (k - f)


def compute_conditional_statistics(
    events: list[MarketEvent],
    spec: ConditionSpec,
    outcome_field: str = "return_1d",
    bootstrap_num_resamples: int = 1000,
    bootstrap_seed: int = 42,
    confidence_level: float = 0.95,
) -> ConditionalResult:
    """
    Compute conditional statistics for events matching a condition.

    Args:
        events: All market events
        spec: Condition specification
        outcome_field: Field name in EventOutcome to analyze
        bootstrap_num_resamples: Number of bootstrap resamples
        bootstrap_seed: Random seed for bootstrap
        confidence_level: Confidence level for CI

    Returns:
        ConditionalResult with computed statistics
    """
    matched = filter_events(events, spec)

    # Extract outcome values
    values = []
    for e in matched:
        val = getattr(e.outcome, outcome_field, None) if e.outcome else None
        if val is not None and isinstance(val, (int, float)):
            values.append(float(val))

    n = len(values)
    if n == 0:
        return ConditionalResult(
            condition_name=spec.name,
            condition_spec=spec,
            sample_size=0,
            raw_probability=0.0,
            mean_return=0.0,
            std_return=0.0,
            status="INCONCLUSIVE",
            notes="No events matched condition",
        )

    mean_val = _mean(values)
    std_val = _std(values)

    # Probability of positive return
    positive_count = sum(1 for v in values if v > 0)
    raw_prob = positive_count / n if n > 0 else 0.0

    # Bootstrap confidence interval for mean
    ci = _bootstrap_mean_ci(values, bootstrap_num_resamples, bootstrap_seed, confidence_level)

    # Status determination
    if n < 5:
        status = EvidenceStatus.EXPLORATORY.value
        notes = f"Small sample (n={n})"
    elif n < 20:
        status = EvidenceStatus.UNVALIDATED.value
        notes = f"Moderate sample (n={n}), needs OOS validation"
    else:
        status = EvidenceStatus.UNVALIDATED.value
        notes = f"Sample n={n}, awaiting temporal validation"

    return ConditionalResult(
        condition_name=spec.name,
        condition_spec=spec,
        sample_size=n,
        raw_probability=raw_prob,
        mean_return=mean_val,
        std_return=std_val,
        confidence_interval=ci,
        bootstrap_seed=bootstrap_seed,
        bootstrap_num_resamples=bootstrap_num_resamples,
        status=status,
        notes=notes,
    )


def _bootstrap_mean_ci(
    values: list[float],
    num_resamples: int,
    seed: int,
    confidence_level: float,
) -> tuple[float, float] | None:
    """
    Compute bootstrap confidence interval for the mean.
    """
    import random

    if len(values) < 2:
        return None

    rng = random.Random(seed)
    n = len(values)
    resample_means = []
    for _ in range(num_resamples):
        resample = [rng.choice(values) for _ in range(n)]
        resample_means.append(_mean(resample))

    resample_means.sort()
    alpha = 1.0 - confidence_level
    lower_idx = int(math.floor(alpha / 2.0 * num_resamples))
    upper_idx = int(math.floor((1.0 - alpha / 2.0) * num_resamples))
    lower_idx = max(0, min(lower_idx, num_resamples - 1))
    upper_idx = max(0, min(upper_idx, num_resamples - 1))
    return (resample_means[lower_idx], resample_means[upper_idx])


# =============================================================================
# Multiple Testing Audit
# =============================================================================


@dataclass
class MultipleTestingAudit:
    """
    Audit trail for multiple hypothesis testing.
    """

    total_hypotheses_tested: int = 0
    conditions_tested: list[str] = None
    selection_process: str = ""
    correction_applied: str = "None"
    limitations: str = ""

    def __post_init__(self):
        if self.conditions_tested is None:
            self.conditions_tested = []

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_hypotheses_tested": self.total_hypotheses_tested,
            "conditions_tested": self.conditions_tested,
            "selection_process": self.selection_process,
            "correction_applied": self.correction_applied,
            "limitations": self.limitations,
        }
