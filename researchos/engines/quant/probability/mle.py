"""
Probability & Statistics Engine — Maximum Likelihood Estimation.

Closed-form MLE for common distributions plus grid-search-based MLE
for distributions without closed-form solutions. Deterministic.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence

from researchos.engines.quant.probability.contracts import DistributionFit, DistributionType


def mle_normal(samples: Sequence[float]) -> DistributionFit:
    n = len(samples)
    if n == 0:
        raise ValueError("samples must be non-empty")
    mu = sum(samples) / n
    sigma2 = sum((s - mu) ** 2 for s in samples) / n
    return DistributionFit(
        distribution=DistributionType.NORMAL,
        parameters={"mean": mu, "std": math.sqrt(sigma2)},
        log_likelihood=-0.5 * n * math.log(2.0 * math.pi * sigma2) - n / 2.0,
        sample_size=n,
    )


def mle_log_normal(samples: Sequence[float]) -> DistributionFit:
    n = len(samples)
    if n == 0:
        raise ValueError("samples must be non-empty")
    if any(s <= 0 for s in samples):
        raise ValueError("log-normal MLE requires strictly positive samples")
    logs = [math.log(s) for s in samples]
    mu = sum(logs) / n
    sigma2 = sum((lg - mu) ** 2 for lg in logs) / n
    if sigma2 <= 0:
        sigma2 = 1e-12
    return DistributionFit(
        distribution=DistributionType.LOG_NORMAL,
        parameters={"mu": mu, "sigma": math.sqrt(sigma2)},
        log_likelihood=-0.5 * n * math.log(2.0 * math.pi * sigma2) - sum(logs) - n / 2.0,
        sample_size=n,
    )


def _student_t_ll(df: float, samples: Sequence[float], mu: float, sigma: float) -> float:
    return sum(math.log(math.gamma((df + 1.0) / 2.0) / (math.sqrt(df * math.pi) * math.gamma(df / 2.0)) * (1.0 + ((s - mu) / sigma) ** 2 / df) ** (-(df + 1.0) / 2.0)) / sigma for s in samples)


def mle_student_t(
    samples: Sequence[float],
    df_grid: Sequence[float] = (3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 15.0, 20.0, 30.0),
) -> DistributionFit:
    """Grid-search MLE for Student-t degrees of freedom."""
    n = len(samples)
    if n == 0:
        raise ValueError("samples must be non-empty")
    mu = sum(samples) / n
    var = sum((s - mu) ** 2 for s in samples) / n
    best_df = df_grid[0]
    best_ll = float("-inf")
    for df in df_grid:
        sigma = math.sqrt(var * (df - 2.0) / df) if df > 2 else math.sqrt(var)
        if sigma <= 0:
            sigma = 1e-12
        ll = _student_t_ll(df, samples, mu, sigma)
        if ll > best_ll:
            best_ll = ll
            best_df = df
    sigma = math.sqrt(var * (best_df - 2.0) / best_df) if best_df > 2 else math.sqrt(var)
    return DistributionFit(
        distribution=DistributionType.STUDENT_T,
        parameters={"df": float(best_df), "loc": mu, "scale": sigma},
        log_likelihood=best_ll,
        sample_size=n,
    )


def generic_grid_mle(
    samples: Sequence[float],
    log_likelihood_fn: Callable[[dict[str, float]], float],
    param_grid: dict[str, Sequence[float]],
) -> dict[str, float]:
    """
    Generic grid-search MLE.

    Args:
        samples: Ignored for likelihood; kept for signature symmetry.
        log_likelihood_fn: Function from param dict → log-likelihood.
        param_grid: Mapping of param name → candidate values.

    Returns:
        Best parameter dict under the grid.
    """
    if not param_grid:
        raise ValueError("param_grid must be non-empty")

    keys = list(param_grid.keys())
    best_params: dict[str, float] = {}
    best_ll = float("-inf")

    def _search(prefix: dict[str, float], idx: int) -> None:
        nonlocal best_params, best_ll
        if idx == len(keys):
            ll = log_likelihood_fn(dict(prefix))
            if ll > best_ll:
                best_ll = ll
                best_params = dict(prefix)
            return
        key = keys[idx]
        for value in param_grid[key]:
            prefix[key] = value
            _search(prefix, idx + 1)

    _search({}, 0)
    if not best_params:
        raise ValueError("MLE grid search failed")
    return best_params
