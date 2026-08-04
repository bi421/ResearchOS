"""
ResearchOS Macro Intelligence Layer - Econometrics Intervals
Version: ecm/interval/v1
Status: FROZEN

Canonical owner of confidence and prediction intervals.

MIL-ECM-013: Econometrics owns confidence/prediction intervals.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from math import sqrt

from macro_intelligence.statistics.distributions import t_distribution_p_value
from macro_intelligence.statistics.provenance import StatisticalProvenance
from macro_intelligence.econometrics.models import IntervalResult

CONFIDENCE_VERSION = "ecm/ci/v1"
PREDICTION_VERSION = "ecm/pi/v1"

# Approximate two-tailed t critical values for common levels at large df.
_T_CRIT = {
    0.90: 1.645,
    0.95: 1.960,
    0.99: 2.576,
}


def _t_critical(level: float, df: int) -> float:
    """Approximate two-tailed t critical value for a confidence level."""
    # Use normal approximation for df >= 30; interpolate for smaller df.
    if df >= 30:
        if level == 0.90:
            return 1.645
        if level == 0.95:
            return 1.960
        if level == 0.99:
            return 2.576
        # Fallback: linear interpolation on the normal quantile.
        if level < 0.9:
            return 1.28 + (level - 0.8) / 0.1 * (1.645 - 1.28)
        if level < 0.95:
            return 1.645 + (level - 0.9) / 0.05 * (1.960 - 1.645)
        return 1.960 + (level - 0.95) / 0.04 * (2.576 - 1.960)
    # Small df: inflate a bit (conservative approximation).
    base = _t_critical(level, 30)
    return base * (1.0 + (30 - df) / 30.0 * 0.5)


def _standard_error_of_residuals(residuals: List[float], n_parameters: int) -> float:
    """Standard error of the estimate (residual standard error)."""
    n = len(residuals)
    rss = sum(r * r for r in residuals)
    df = n - n_parameters
    if df <= 0:
        df = 1
    return sqrt(rss / df)


def confidence_interval(
    estimate: float,
    standard_error: float,
    sample_size: int,
    n_parameters: int = 1,
    level: float = 0.95,
    dataset_id: Optional[str] = None,
    dataset_version: Optional[str] = None,
    dataset_hash: Optional[str] = None,
) -> IntervalResult:
    """
    Confidence interval for a parameter estimate.

    CI = estimate ± t_crit * standard_error

    Args:
        estimate: Point estimate.
        standard_error: Standard error of the estimate.
        sample_size: Number of observations.
        n_parameters: Number of estimated parameters.
        level: Confidence level (e.g., 0.95).

    Returns:
        Immutable IntervalResult.
    """
    if not (0.0 < level < 1.0):
        raise ValueError("level must be between 0 and 1")
    df = sample_size - n_parameters
    if df < 1:
        df = 1
    t_crit = _t_critical(level, df)
    margin = t_crit * standard_error
    prov = StatisticalProvenance(
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        dataset_hash=dataset_hash,
        computation_method="confidence_interval",
        method_version=CONFIDENCE_VERSION,
        parameters={"level": level, "sample_size": sample_size, "n_parameters": n_parameters},
    )
    return IntervalResult(
        level=level,
        lower=estimate - margin,
        upper=estimate + margin,
        kind="confidence",
        provenance=prov,
    )


def prediction_interval(
    prediction: float,
    residuals: List[float],
    n_parameters: int = 1,
    level: float = 0.95,
    dataset_id: Optional[str] = None,
    dataset_version: Optional[str] = None,
    dataset_hash: Optional[str] = None,
) -> IntervalResult:
    """
    Prediction interval for a new observation.

    PI = prediction ± t_crit * residual_standard_error * sqrt(1 + 1/n)

    Args:
        prediction: Model prediction for the new point.
        residuals: Residuals from the model fit.
        n_parameters: Number of estimated parameters.
        level: Confidence level (e.g., 0.95).

    Returns:
        Immutable IntervalResult.
    """
    if not (0.0 < level < 1.0):
        raise ValueError("level must be between 0 and 1")
    n = len(residuals)
    if n < 2:
        raise ValueError("Need at least 2 residuals for a prediction interval")
    s = _standard_error_of_residuals(residuals, n_parameters)
    df = n - n_parameters
    if df < 1:
        df = 1
    t_crit = _t_critical(level, df)
    margin = t_crit * s * sqrt(1.0 + 1.0 / n)
    prov = StatisticalProvenance(
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        dataset_hash=dataset_hash,
        computation_method="prediction_interval",
        method_version=PREDICTION_VERSION,
        parameters={"level": level, "n_observations": n, "n_parameters": n_parameters},
    )
    return IntervalResult(
        level=level,
        lower=prediction - margin,
        upper=prediction + margin,
        kind="prediction",
        provenance=prov,
    )


__all__ = ["confidence_interval", "prediction_interval", "CONFIDENCE_VERSION", "PREDICTION_VERSION"]
