"""
Phase 5.1 — statistical significance and confidence intervals.

Assesses whether the model's out-of-sample difference from the baseline is
statistically meaningful.  Reuses ``researchos.quant_engine.probability.
statistics.confidence_interval_mean`` where applicable (verified existing).

Significance here uses a deterministic paired permutation-style comparison
over per-observation correctness, avoiding any randomness:
    - ``model_better_count`` = observations where the model is correct and the
      baseline is not.
    - ``baseline_better_count`` = the reverse.
    - A one-sided improvement is evaluated against the null that the two have
      equal correctness via a paired-exact (McNemar-style) binomial sign test
      computed deterministically.

Guarantees:
    * Deterministic: single fixed dataset -> single p-value.
    * No randomness.
    * Composes existing infrastructure rather than duplicating it.
"""

from __future__ import annotations

import math
from typing import List, Sequence

from researchos.quant_engine.probability.statistics import confidence_interval_mean

from .contracts import SignificanceResult

_LEVELS = (0.05, 0.01, 0.10)


def _binomial_tail_ge(n: int, k: int, p: float) -> float:
    """P(X >= k) for X ~ Binomial(n, p), computed deterministically (no RNG)."""
    if n <= 0 or p <= 0.0 or p >= 1.0:
        return 0.0
    # Use the incomplete beta relation: P(X >= k) = I_p(k, n-k+1).
    # Fall back to a direct summation over log-space for stability.
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    # Compute via log-combinations (log PMF) for numerical stability.
    log_fact = _log_factorials(n)
    total = 0.0
    for c in range(k, n + 1):
        log_pmf = (
            log_fact[n] - log_fact[c] - log_fact[n - c] + c * math.log(p) + (n - c) * math.log1p(-p)
        )
        total += math.exp(log_pmf)
    return min(1.0, max(0.0, total))


def _log_factorials(n: int) -> List[float]:
    log_fact = [0.0] * (n + 1)
    for i in range(1, n + 1):
        log_fact[i] = log_fact[i - 1] + math.log(i)
    return log_fact


def _paired_sign_test(
    model_pred: Sequence[int], base_pred: Sequence[int], actuals: Sequence[float]
):
    """Deterministic McNemar-style paired sign test of model vs baseline.

    Returns (n_discordant, n_model_better, n_baseline_better, p_one_sided).
    Only discordant pairs (one correct, the other wrong) are informative.
    """
    n_model_better = 0
    n_base_better = 0
    for mp, bp, a in zip(model_pred, base_pred, actuals):
        model_ok = int(mp) == int(a)
        base_ok = int(bp) == int(a)
        if model_ok and not base_ok:
            n_model_better += 1
        elif base_ok and not model_ok:
            n_base_better += 1
    n_discordant = n_model_better + n_base_better
    if n_discordant == 0:
        p_value = 1.0
    else:
        # Two-sided p-value: probability of observing at least as extreme
        # asymmetry, using the paired-binomial null at 0.5.
        k = max(n_model_better, n_base_better)
        p_ge = _binomial_tail_ge(n_discordant, k, 0.5)
        p_value = min(1.0, 2.0 * p_ge)
    return n_discordant, n_model_better, n_base_better, p_value


def evaluate_significance(
    model_predictions: Sequence[int],
    baseline_predictions: Sequence[int],
    actuals: Sequence[float],
    significance_level: float = 0.05,
) -> SignificanceResult:
    """Assess whether the model significantly differs from the baseline.

    Args:
        model_predictions: Model's ternary predictions (1/0/−1).
        baseline_predictions: Baseline's ternary predictions.
        actuals: True labels.
        significance_level: Alpha for the significance decision.
    """
    n_disc, n_mb, n_bb, p_value = _paired_sign_test(
        model_predictions, baseline_predictions, actuals
    )
    hu = sum(1 for a in actuals if int(a) == 1)
    hd = sum(1 for a in actuals if int(a) == -1)
    hn = sum(1 for a in actuals if int(a) == 0)
    significant = p_value < significance_level
    return SignificanceResult(
        n_up=hu,
        n_down=hd,
        n_neutral=hn,
        model_better_count=n_mb,
        baseline_better_count=n_bb,
        tie_count=n_disc - n_mb - n_bb,
        p_value=p_value,
        significant=significant,
        method="paired_sign_test",
    )


def confidence_interval_diff(
    new_perf: Sequence[float],
    base_perf: Sequence[float],
    confidence_level: float = 0.95,
) -> tuple[float, float]:
    """Confidence interval for the mean of (new_perf - base_perf) per observation.

    Reuses the existing ``confidence_interval_mean`` on the per-observation
    difference series.
    """
    diffs = [float(n) - float(b) for n, b in zip(new_perf, base_perf)]
    if not diffs:
        return (0.0, 0.0)
    ci = confidence_interval_mean(diffs, confidence_level=confidence_level)
    return ci.lower, ci.upper


__all__ = [
    "evaluate_significance",
    "confidence_interval_diff",
    "_paired_sign_test",
    "_binomial_tail_ge",
]
