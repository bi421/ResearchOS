"""
Bootstrap Engine — deterministic bootstrap uncertainty quantification.

Provides:
  - Bootstrap confidence intervals
  - Bootstrap stability checks
  - Deterministic resampling with fixed seeds
"""

from __future__ import annotations

import math
from typing import Any, Sequence

from researchos.market_memory.event_schema import BootstrapResult


def bootstrap_mean_ci(
    values: Sequence[float],
    num_resamples: int = 1000,
    seed: int = 42,
    confidence_level: float = 0.95,
) -> BootstrapResult:
    """
    Compute bootstrap confidence interval for the mean.

    Args:
        values: Sample values
        num_resamples: Number of bootstrap resamples
        seed: Random seed for reproducibility
        confidence_level: Confidence level (e.g., 0.95 for 95% CI)

    Returns:
        BootstrapResult with point estimate and CI
    """
    import random

    if not values:
        raise ValueError("values cannot be empty")

    rng = random.Random(seed)
    n = len(values)
    point_estimate = sum(values) / n

    resample_means = []
    for _ in range(num_resamples):
        resample = [rng.choice(values) for _ in range(n)]
        resample_means.append(sum(resample) / n)

    resample_means.sort()
    bootstrap_mean_val = sum(resample_means) / len(resample_means)
    bootstrap_std = math.sqrt(sum((x - bootstrap_mean_val) ** 2 for x in resample_means) / len(resample_means))

    alpha = 1.0 - confidence_level
    lower_idx = int(math.floor(alpha / 2.0 * num_resamples))
    upper_idx = int(math.floor((1.0 - alpha / 2.0) * num_resamples))
    lower_idx = max(0, min(lower_idx, num_resamples - 1))
    upper_idx = max(0, min(upper_idx, num_resamples - 1))

    return BootstrapResult(
        point_estimate=point_estimate,
        bootstrap_mean=bootstrap_mean_val,
        bootstrap_std=bootstrap_std,
        confidence_interval=(resample_means[lower_idx], resample_means[upper_idx]),
        confidence_level=confidence_level,
        num_resamples=num_resamples,
        seed=seed,
        method="percentile_bootstrap",
    )


def bootstrap_stability_check(
    values: Sequence[float],
    num_resamples: int = 1000,
    seed: int = 42,
    threshold: float = 0.1,
) -> dict[str, Any]:
    """
    Check if bootstrap CI is stable (narrow relative to point estimate).

    Returns:
        Dict with stability metrics
    """
    result = bootstrap_mean_ci(values, num_resamples, seed)
    ci_width = result.confidence_interval[1] - result.confidence_interval[0]
    relative_width = ci_width / abs(result.point_estimate) if result.point_estimate != 0 else float("inf")

    return {
        "point_estimate": result.point_estimate,
        "ci_width": ci_width,
        "relative_width": relative_width,
        "is_stable": relative_width < threshold,
        "threshold": threshold,
    }
