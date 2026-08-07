"""
ResearchOS Macro Intelligence Layer - Distribution Analysis
Version: stat/dist/v1
Status: FROZEN

MIL-STAT-001: Same input must always produce identical output.
MIL-STAT-002: Statistical functions are pure.
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any
from math import sqrt, exp, lgamma, log
from macro_intelligence.statistics.descriptive import (
    mean,
    std,
    percentile,
    skewness,
    kurtosis,
)


def empirical_distribution(values: List[float]) -> Dict[str, Any]:
    """
    Calculate empirical distribution statistics.
    
    Args:
        values: List of numeric values
        
    Returns:
        Dictionary with empirical distribution metrics
    """
    if not values:
        return {
            "count": 0,
            "min": None,
            "max": None,
            "mean": None,
            "std": None,
            "skewness": None,
            "kurtosis": None,
            "percentiles": {},
        }
    
    return {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "mean": mean(values),
        "std": std(values),
        "skewness": skewness(values) if len(values) >= 3 else None,
        "kurtosis": kurtosis(values) if len(values) >= 4 else None,
        "percentiles": {
            "p10": percentile(values, 10),
            "p25": percentile(values, 25),
            "p50": percentile(values, 50),
            "p75": percentile(values, 75),
            "p90": percentile(values, 90),
        },
    }


def quantiles(
    values: List[float],
    probabilities: List[float] = None,
) -> Dict[float, float]:
    """
    Calculate quantiles.
    
    Args:
        values: List of numeric values
        probabilities: List of probability values (0-1)
        
    Returns:
        Dictionary mapping probability to quantile value
    """
    if probabilities is None:
        probabilities = [0.1, 0.25, 0.5, 0.75, 0.9]
    
    result = {}
    for p in probabilities:
        percentile_value = percentile(values, p * 100)
        result[p] = percentile_value
    
    return result


def distribution_analysis(
    values: List[float],
) -> Dict[str, Any]:
    """
    Complete distribution analysis.
    
    Args:
        values: List of numeric values
        
    Returns:
        Dictionary with complete distribution metrics
    """
    if not values:
        return {"error": "Empty values"}
    
    n = len(values)
    
    # Basic statistics
    m = mean(values)
    s = std(values)
    
    # Skewness and kurtosis
    skew = skewness(values) if n >= 3 else None
    kurt = kurtosis(values) if n >= 4 else None
    
    # Normality tests (simple)
    is_normal = False
    if skew is not None and kurt is not None:
        # Simple normality check
        if abs(skew) < 1 and abs(kurt) < 3:
            is_normal = True
    
    # Fit to normal distribution
    normal_params = {
        "mu": m,
        "sigma": s,
    }
    
    # Calculate empirical CDF at key points
    sorted_values = sorted(values)
    cdf_points = {}
    for i, p in enumerate([0.1, 0.25, 0.5, 0.75, 0.9]):
        idx = int(p * n)
        cdf_points[p] = sorted_values[min(idx, n - 1)]
    
    return {
        "count": n,
        "mean": m,
        "std": s,
        "skewness": skew,
        "kurtosis": kurt,
        "is_normal": is_normal,
        "normal_params": normal_params,
        "percentiles": {
            "p10": percentile(values, 10),
            "p25": percentile(values, 25),
            "p50": percentile(values, 50),
            "p75": percentile(values, 75),
            "p90": percentile(values, 90),
        },
        "cdf_points": cdf_points,
    }


def z_score_from_distribution(
    value: float,
    distribution_params: Dict[str, float],
) -> float:
    """
    Calculate z-score from distribution parameters.
    
    Args:
        value: Value to standardize
        distribution_params: Dictionary with 'mu' and 'sigma'
        
    Returns:
        Z-score
    """
    mu = distribution_params.get("mu", 0)
    sigma = distribution_params.get("sigma", 1)
    
    if sigma == 0:
        return 0.0
    
    return (value - mu) / sigma


def probability_from_z_score(z: float) -> float:
    """
    Approximate cumulative probability from z-score.
    
    Uses the error function approximation.
    
    Args:
        z: Z-score
        
    Returns:
        Cumulative probability (0 to 1)
    """
    # Approximation of the error function
    # This is a simplified version
    return 0.5 * (1 + _erf(z / sqrt(2)))


def _erf(x: float) -> float:
    """
    Approximate error function.
    
    Args:
        x: Input value
        
    Returns:
        Error function value
    """
    # Abramowitz and Stegun approximation
    a1 = 0.254829592
    a2 = -0.284496736
    a3 = 1.421413741
    a4 = -1.453152027
    a5 = 1.061405429
    p = 0.3275911
    
    sign = 1 if x >= 0 else -1
    x = abs(x)
    
    t = 1.0 / (1.0 + p * x)
    y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * exp(-x * x)
    
    return sign * y


def normal_cdf(x: float) -> float:
    """
    Approximate standard normal cumulative distribution function.

    Uses the Abramowitz & Stegun error function approximation.

    Args:
        x: Standard normal value

    Returns:
        Cumulative probability (0 to 1)
    """
    if x < -8:
        return 0.0
    if x > 8:
        return 1.0
    return 0.5 * (1.0 + _erf(x / sqrt(2)))


def incomplete_beta(a: float, b: float, x: float) -> float:
    """
    Approximate regularized incomplete beta function I_x(a, b).

    Args:
        a: First shape parameter
        b: Second shape parameter
        x: Integration upper limit (0 <= x <= 1)

    Returns:
        Regularized incomplete beta value (0 to 1)
    """
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0

    # Series expansion of the regularized incomplete beta function
    ln_beta = lgamma(a) + lgamma(b) - lgamma(a + b)
    front = exp(a * log(x) + b * log(1 - x) - ln_beta) / a

    result = front
    term = front
    for n in range(1, 20):
        term *= x * (a + n - 1) * (a + b + n - 1) / (n * (a + n))
        result += term
        if abs(term) < abs(result) * 1e-10:
            break

    return min(1.0, max(0.0, result))


def t_distribution_p_value(t: float, df: int) -> float:
    """
    Approximate two-tailed p-value for a t-distribution.

    Args:
        t: Observed t-statistic (absolute value)
        df: Degrees of freedom

    Returns:
        Two-tailed p-value (0 to 1)
    """
    x = df / (df + t * t)
    p = incomplete_beta(df / 2.0, 0.5, x)
    return max(0.0, min(1.0, p))


def p_value_from_correlation(correlation: float, n: int) -> Optional[float]:
    """
    Approximate two-tailed p-value for a Pearson correlation.

    Uses t = r * sqrt((n-2)/(1-r^2)) and the t-distribution with n-2 degrees
    of freedom. For large df, a normal approximation is used.

    Args:
        correlation: Pearson correlation coefficient
        n: Sample size

    Returns:
        Two-tailed p-value (0 to 1), or None if inputs are invalid
    """
    if n < 3 or abs(correlation) >= 1.0:
        return None

    r2 = correlation ** 2
    t_stat = abs(correlation) * ((n - 2) / (1 - r2)) ** 0.5
    df = n - 2

    if df >= 30:
        p_value = 2 * normal_cdf(-abs(t_stat))
    else:
        p_value = t_distribution_p_value(t_stat, df)

    return max(0.0, min(1.0, p_value))
