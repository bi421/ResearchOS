"""
ResearchOS Macro Intelligence Layer - Lag Analysis Module

Detects leading/lagging relationships between series using cross-correlation.
Pure, deterministic, stateless.
"""

from __future__ import annotations

from researchos.macro.relationships.correlation import pearson_correlation
from researchos.macro.relationships.models import (
    LagRelationship,
    LagType,
)
from researchos.macro.statistics.descriptive import mean, std
from researchos.macro.statistics.zscore import zscore


def find_optimal_lag(
    series_a: list[float],
    series_b: list[float],
    max_lag: int = 10,
) -> LagRelationship:
    """
    Find the optimal lag between two series using cross-correlation.

    Args:
        series_a: Primary series
        series_b: Secondary series
        max_lag: Maximum lag to test (positive and negative)

    Returns:
        LagRelationship with optimal lag and correlation
    """
    n = len(series_a)
    if n < 4 or n != len(series_b):
        return LagRelationship(
            series_a="",
            series_b="",
            optimal_lag=0,
            lag_correlation=0.0,
            lag_type=LagType.UNKNOWN.value,
            confidence=0.0,
        )

    best_lag = 0
    best_corr = 0.0
    correlations = {}

    # Test lags from -max_lag to +max_lag
    for lag in range(-max_lag, max_lag + 1):
        if lag > 0:
            # series_a leads series_b by `lag` periods
            # Correlate a[t+lag] with b[t]
            valid_len = n - lag
            corr = pearson_correlation(series_a[lag:], series_b[:valid_len])
        elif lag < 0:
            # series_b leads series_a by |lag| periods
            # Correlate a[t] with b[t+|lag|]
            abs_lag = -lag
            valid_len = n - abs_lag
            corr = pearson_correlation(series_a[:valid_len], series_b[abs_lag:])
        else:
            # Zero lag
            corr = pearson_correlation(series_a, series_b)

        if corr is not None:
            correlations[lag] = corr
            if abs(corr) > abs(best_corr):
                best_corr = corr
                best_lag = lag

    # Determine lag type
    if best_lag > 0:
        lag_type = LagType.LEADING.value
    elif best_lag < 0:
        lag_type = LagType.LAGGING.value
    else:
        lag_type = LagType.SIMULTANEOUS.value

    # Compute confidence based on correlation strength and sample size
    confidence = min(1.0, abs(best_corr) * (n / (n + 10)))

    return LagRelationship(
        series_a="",
        series_b="",
        optimal_lag=best_lag,
        lag_correlation=best_corr,
        lag_type=lag_type,
        confidence=round(confidence, 4),
        evidence_refs=[],
    )


def detect_reaction_delay(
    event_series: list[float],
    response_series: list[float],
    event_threshold: float = 2.0,
    max_search_lag: int = 20,
) -> LagRelationship:
    """
    Detect reaction delay: when does response_series react to event_series spikes?

    Finds the lag at which response series shows the strongest correlation
    after event series exceeds the threshold.

    Args:
        event_series: Series containing events (spikes)
        response_series: Series that may react to events
        event_threshold: Z-score threshold for identifying events
        max_search_lag: Maximum lag to search

    Returns:
        LagRelationship with reaction delay
    """
    n = len(event_series)
    if n < 4 or n != len(response_series):
        return LagRelationship(
            series_a="",
            series_b="",
            optimal_lag=0,
            lag_correlation=0.0,
            lag_type=LagType.UNKNOWN.value,
            confidence=0.0,
        )

    # Find event points (where event_series exceeds threshold).
    # Statistics delegated to canonical Stats layer; population std preserved.
    mean_e = mean(event_series)
    std_e = std(event_series, sample=False)
    if std_e == 0:
        return LagRelationship(
            series_a="",
            series_b="",
            optimal_lag=0,
            lag_correlation=0.0,
            lag_type=LagType.UNKNOWN.value,
            confidence=0.0,
        )

    events = []
    for i in range(n):
        z = zscore(event_series[i], mean_e, std_e)
        if abs(z) >= event_threshold:
            events.append((i, z))

    if len(events) < 2:
        return LagRelationship(
            series_a="",
            series_b="",
            optimal_lag=0,
            lag_correlation=0.0,
            lag_type=LagType.UNKNOWN.value,
            confidence=0.0,
        )

    # For each event, check response in subsequent periods
    best_lag = 0
    best_corr = 0.0

    for lag in range(0, min(max_search_lag, n // 2)):
        response_values = []
        for evt_idx, _ in events:
            resp_idx = evt_idx + lag
            if 0 <= resp_idx < n:
                response_values.append(response_series[resp_idx])

        if len(response_values) >= 3:
            # Check if response values deviate from mean.
            # Statistics delegated to canonical Stats layer; population std preserved.
            mean_r = mean(response_series)
            std_r = std(response_series, sample=False)
            if std_r > 0:
                resp_deviation = sum(abs(v - mean_r) / std_r for v in response_values) / len(response_values)
                # Higher deviation = stronger reaction
                if resp_deviation > abs(best_corr):
                    best_corr = resp_deviation * 0.5  # Scale to correlation-like range
                    best_lag = lag

    confidence = min(1.0, abs(best_corr) * len(events) / 10)

    return LagRelationship(
        series_a="",
        series_b="",
        optimal_lag=best_lag,
        lag_correlation=best_corr,
        lag_type=LagType.LAGGING.value if best_lag > 0 else LagType.SIMULTANEOUS.value,
        confidence=round(confidence, 4),
        evidence_refs=[],
    )
