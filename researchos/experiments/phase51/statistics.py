"""Phase 5.1 deterministic statistical significance utilities."""

from __future__ import annotations

import math
from collections.abc import Sequence

from researchos.quant_engine.probability.statistics import confidence_interval_mean

from .contracts import SignificanceResult


def _binomial_tail_ge(n: int, k: int, p: float) -> float:
    if n <= 0 or p <= 0.0 or p >= 1.0:
        return 0.0
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    log_fact = _log_factorials(n)
    total = 0.0
    for c in range(k, n + 1):
        log_pmf = log_fact[n] - log_fact[c] - log_fact[n - c] + c * math.log(p) + (n - c) * math.log1p(-p)
        total += math.exp(log_pmf)
    return min(1.0, max(0.0, total))


def _log_factorials(n: int) -> list[float]:
    log_fact = [0.0] * (n + 1)
    for i in range(1, n + 1):
        log_fact[i] = log_fact[i - 1] + math.log(i)
    return log_fact


def _paired_sign_test(model_pred: Sequence[int], base_pred: Sequence[int], actuals: Sequence[float]):
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
        k = max(n_model_better, n_base_better)
        p_value = min(1.0, 2.0 * _binomial_tail_ge(n_discordant, k, 0.5))
    return n_discordant, n_model_better, n_base_better, p_value


def evaluate_significance(
    model_predictions: Sequence[int],
    baseline_predictions: Sequence[int],
    actuals: Sequence[float],
    significance_level: float = 0.05,
    observation_stride: int = 1,
) -> SignificanceResult:
    """Compare paired correctness; stride can decorrelate overlapping labels.

    For a forward label horizon H, passing ``observation_stride=H`` evaluates
    only non-overlapping observations. This avoids treating overlapping
    forward-return labels as independent Bernoulli trials.
    """
    if observation_stride <= 0:
        raise ValueError("observation_stride must be positive")
    model = model_predictions[::observation_stride]
    baseline = baseline_predictions[::observation_stride]
    observed = actuals[::observation_stride]
    n_disc, n_mb, n_bb, p_value = _paired_sign_test(model, baseline, observed)
    hu = sum(1 for a in observed if int(a) == 1)
    hd = sum(1 for a in observed if int(a) == -1)
    hn = sum(1 for a in observed if int(a) == 0)
    return SignificanceResult(
        n_up=hu,
        n_down=hd,
        n_neutral=hn,
        model_better_count=n_mb,
        baseline_better_count=n_bb,
        tie_count=n_disc - n_mb - n_bb,
        p_value=p_value,
        significant=p_value < significance_level,
        method=f"paired_sign_test_nonoverlap_stride_{observation_stride}",
    )


def confidence_interval_diff(new_perf: Sequence[float], base_perf: Sequence[float], confidence_level: float = 0.95) -> tuple[float, float]:
    diffs = [float(n) - float(b) for n, b in zip(new_perf, base_perf)]
    if not diffs:
        return (0.0, 0.0)
    ci = confidence_interval_mean(diffs, confidence_level=confidence_level)
    return ci.lower, ci.upper


__all__ = ["evaluate_significance", "confidence_interval_diff", "_paired_sign_test", "_binomial_tail_ge"]
