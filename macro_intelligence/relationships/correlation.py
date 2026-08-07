"""
ResearchOS Macro Intelligence Layer - Correlation Engine

Relationship orchestration layer for correlation analysis.

Canonical rule:
- The Statistics Layer owns ALL statistical algorithms.
- The Relationships Layer is an orchestration layer only.
- It must NOT reimplement statistical mathematics.

Pearson and Spearman are provided by the canonical Statistics Layer
(macro_intelligence.statistics.correlation). This module delegates to
them, preserving the existing API contract of returning None for
invalid inputs (the canonical implementation raises ValueError).
"""

from __future__ import annotations


from macro_intelligence.statistics.correlation import (
    pearson_correlation as _canonical_pearson,
    spearman_correlation as _canonical_spearman,
)
from macro_intelligence.statistics.distributions import (
    p_value_from_correlation as _canonical_p_value,
)
from macro_intelligence.statistics.descriptive import (
    std as _canonical_std,
)


def pearson_correlation(x: list[float], y: list[float]) -> float | None:
    """
    Compute Pearson correlation coefficient between two series.

    Delegates to the canonical Statistics Layer implementation.
    Returns None if either series is invalid (empty, length mismatch,
    or zero variance) to preserve the existing API contract.
    """
    try:
        return _canonical_pearson(x, y)
    except ValueError:
        return None


def spearman_correlation(x: list[float], y: list[float]) -> float | None:
    """
    Compute Spearman rank correlation coefficient.

    Delegates to the canonical Statistics Layer implementation.
    Returns None if either series is invalid (empty, length mismatch,
    or zero variance) to preserve the existing API contract.
    """
    try:
        return _canonical_spearman(x, y)
    except ValueError:
        return None


def classify_relationship(correlation: float) -> tuple[str, str]:
    """
    Classify relationship type and strength based on correlation coefficient.
    
    Returns:
        (relationship_type, relationship_strength)
    """
    abs_corr = abs(correlation)
    
    # Type
    if correlation > 0.05:
        rel_type = "positive"
    elif correlation < -0.05:
        rel_type = "negative"
    else:
        rel_type = "neutral"
    
    # Strength
    if abs_corr >= 0.8:
        strength = "very_strong"
    elif abs_corr >= 0.6:
        strength = "strong"
    elif abs_corr >= 0.4:
        strength = "moderate"
    elif abs_corr >= 0.2:
        strength = "weak"
    else:
        strength = "negligible"
    
    return rel_type, strength


def compute_rolling_correlation(
    x: list[float],
    y: list[float],
    window: int,
) -> tuple[list[float], list[float], float]:
    """
    Compute rolling correlation with the given window size.
    
    Returns:
        (correlations, timestamps, stability)
        where stability is the standard deviation of correlations.
    """
    n = len(x)
    if n < window or window < 2:
        return [], [], 0.0
    
    correlations = []
    timestamps = list(range(window, n + 1))  # Use index positions as timestamps
    
    for i in range(window - 1, n):
        seg_x = x[i - window + 1: i + 1]
        seg_y = y[i - window + 1: i + 1]
        corr = pearson_correlation(seg_x, seg_y)
        if corr is not None:
            correlations.append(corr)
    
    if not correlations:
        return [], [], 0.0
    
    # Compute stability (std dev of correlations) — canonical Stats layer.
    stability = _canonical_std(correlations, sample=False)
    
    return correlations, timestamps, stability


def approximate_p_value(correlation: float, n: int) -> float | None:
    """
    Approximate two-tailed p-value for Pearson correlation using t-distribution.

    Delegates to the canonical Statistics Layer implementation.

    Args:
        correlation: Pearson correlation coefficient
        n: Sample size

    Returns:
        Two-tailed p-value (0 to 1), or None if inputs are invalid
    """
    return _canonical_p_value(correlation, n)
