"""
ResearchOS Macro Intelligence Layer - Regime-Conditional Relationships

Calculates correlations between series conditioned on macro regimes.
Pure, deterministic, stateless.
"""

from __future__ import annotations

from macro_intelligence.relationships.correlation import classify_relationship, pearson_correlation
from macro_intelligence.relationships.models import (
    ALGORITHM_VERSION,
    RegimeRelationship,
)


def compute_regime_correlation(
    series_a: list[float],
    series_b: list[float],
    regime_labels: list[str],
    target_regime: str,
) -> RegimeRelationship | None:
    """
    Compute correlation between two series, conditioned on a specific regime.

    Args:
        series_a: Values for series A
        series_b: Values for series B
        regime_labels: Regime label for each time period
        target_regime: Regime to condition on

    Returns:
        RegimeRelationship or None if insufficient data
    """
    if len(series_a) != len(series_b) or len(series_a) != len(regime_labels):
        return None

    # Filter to target regime
    a_values = []
    b_values = []
    for i in range(len(regime_labels)):
        if regime_labels[i] == target_regime:
            a_values.append(series_a[i])
            b_values.append(series_b[i])

    if len(a_values) < 4:
        return None

    correlation = pearson_correlation(a_values, b_values)
    if correlation is None:
        return None

    rel_type, rel_strength = classify_relationship(correlation)
    confidence = min(1.0, len(a_values) / 20.0) * abs(correlation)

    return RegimeRelationship(
        series_a="",
        series_b="",
        regime=target_regime,
        correlation=correlation,
        sample_size=len(a_values),
        confidence=round(confidence, 4),
        algorithm_version=ALGORITHM_VERSION,
    )


def compute_all_regime_correlations(
    series_a: list[float],
    series_b: list[float],
    regime_labels: list[str],
    all_regimes: list[str] | None = None,
) -> list[RegimeRelationship]:
    """
    Compute correlations for all regimes.

    Args:
        series_a: Values for series A
        series_b: Values for series B
        regime_labels: Regime label for each time period
        all_regimes: List of all possible regimes (uses unique labels if None)

    Returns:
        List of RegimeRelationship for each regime with sufficient data
    """
    if all_regimes is None:
        all_regimes = sorted(set(regime_labels))

    results = []
    for regime in all_regimes:
        rel = compute_regime_correlation(series_a, series_b, regime_labels, regime)
        if rel is not None:
            results.append(rel)

    return results
