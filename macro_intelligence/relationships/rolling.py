"""
ResearchOS Macro Intelligence Layer - Rolling Correlation Module

Computes rolling/progressive correlation statistics.
Pure, deterministic, stateless.
"""

from __future__ import annotations

from typing import Any

from macro_intelligence.relationships.correlation import (
    pearson_correlation,
    classify_relationship,
    compute_rolling_correlation,
)
from macro_intelligence.relationships.models import (
    ALGORITHM_VERSION,
    RollingCorrelationResult,
)
from macro_intelligence.statistics.descriptive import (
    std as _canonical_std,
)
from macro_intelligence.statistics.regression import (
    slope as _canonical_slope,
)


def compute_rolling(
    series_a_values: list[float],
    series_b_values: list[float],
    window_size: int,
    timestamps: list[str] | None = None,
    evidence_refs: list[str] | None = None,
) -> RollingCorrelationResult:
    """
    Compute rolling correlation between two series.
    
    Args:
        series_a_values: Values for series A
        series_b_values: Values for series B
        window_size: Rolling window size
        timestamps: Optional timestamp strings (uses indices if None)
        evidence_refs: Optional evidence references
    
    Returns:
        RollingCorrelationResult
    """
    if timestamps is None:
        timestamps = [str(i) for i in range(len(series_a_values))]
    if evidence_refs is None:
        evidence_refs = []
    
    correlations, corr_timestamps, stability = compute_rolling_correlation(
        series_a_values, series_b_values, window_size
    )
    
    # Align timestamps
    if len(corr_timestamps) < len(timestamps):
        aligned_ts = [timestamps[t] for t in corr_timestamps]
    else:
        aligned_ts = [timestamps[t] for t in corr_timestamps[:len(correlations)]]
    
    return RollingCorrelationResult(
        series_a="",  # Set by caller
        series_b="",
        window_size=window_size,
        correlations=correlations,
        timestamps=aligned_ts,
        stability=stability,
        algorithm_version=ALGORITHM_VERSION,
    )


def analyze_relationship_stability(
    correlations: list[float],
) -> dict[str, Any]:
    """
    Analyze the stability of a correlation series.

    Statistical computations (std dev, regression slope) delegate to the
    canonical Statistics Layer. Relationships owns orchestration only.

    Returns stability metrics.
    """
    if len(correlations) < 2:
        return {"stable": True, "variability": 0.0, "trend": "insufficient_data"}
    
    # Compute variability (std dev) — canonical Statistics layer.
    # Preserve original population-std behavior (denominator = N).
    std_dev = _canonical_std(correlations, sample=False)
    
    # Detect trend (linear regression slope on indices) — canonical layer
    n = len(correlations)
    x_idx = [float(i) for i in range(n)]
    slope = _canonical_slope(x_idx, correlations)
    
    mean_c = sum(correlations) / len(correlations)
    
    # Classify stability
    if std_dev < 0.1:
        stable = True
        trend = "stable"
    elif std_dev < 0.2:
        stable = True
        trend = "slight_trend" if abs(slope) > 0.01 else "stable"
    else:
        stable = False
        trend = "trending" if abs(slope) > 0.02 else "volatile"
    
    return {
        "stable": stable,
        "variability": round(float(std_dev), 6),
        "trend": trend,
        "mean_correlation": round(mean_c, 6),
        "slope": round(float(slope), 6),
    }
