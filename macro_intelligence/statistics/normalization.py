"""
ResearchOS Macro Intelligence Layer - Normalization
Version: stat/norm/v1
Status: FROZEN

MIL-STAT-001: Same input must always produce identical output.
MIL-STAT-002: Statistical functions are pure.
"""

from __future__ import annotations

from macro_intelligence.statistics.descriptive import mean, percentile, std


def min_max_normalize(
    values: list[float],
    new_min: float = 0.0,
    new_max: float = 1.0,
) -> list[float]:
    """
    Normalize values to [new_min, new_max] range.

    Args:
        values: List of numeric values
        new_min: New minimum value
        new_max: New maximum value

    Returns:
        Normalized values

    Raises:
        ValueError: If all values are identical
    """
    if not values:
        raise ValueError("Cannot normalize empty list")

    old_min = min(values)
    old_max = max(values)

    if old_max == old_min:
        return [new_min] * len(values)

    return [new_min + (v - old_min) * (new_max - new_min) / (old_max - old_min) for v in values]


def zscore_normalize(values: list[float]) -> list[float]:
    """
    Normalize values using z-score standardization.

    Args:
        values: List of numeric values

    Returns:
        Z-score normalized values

    Raises:
        ValueError: If all values are identical
    """
    if not values:
        raise ValueError("Cannot normalize empty list")

    m = mean(values)
    s = std(values)

    if s == 0:
        return [0.0] * len(values)

    return [(v - m) / s for v in values]


def robust_scale(
    values: list[float],
    center: bool = True,
    scale: bool = True,
) -> list[float]:
    """
    Normalize values using robust scaling (median and IQR).

    Args:
        values: List of numeric values
        center: Whether to center (subtract median)
        scale: Whether to scale (divide by IQR)

    Returns:
        Robustly scaled values
    """
    if not values:
        raise ValueError("Cannot normalize empty list")

    median_val = percentile(values, 50)
    q1 = percentile(values, 25)
    q3 = percentile(values, 75)
    iqr = q3 - q1

    if center and not scale:
        return [v - median_val for v in values]
    elif not center and scale:
        if iqr == 0:
            return [0.0] * len(values)
        return [v / iqr for v in values]
    elif center and scale:
        if iqr == 0:
            return [0.0] * len(values)
        return [(v - median_val) / iqr for v in values]
    else:
        return list(values)


def normalize(
    values: list[float],
    method: str = "zscore",
    **kwargs,
) -> list[float]:
    """
    Normalize values using specified method.

    Args:
        values: List of numeric values
        method: Normalization method ('minmax', 'zscore', 'robust')
        **kwargs: Additional parameters

    Returns:
        Normalized values

    Raises:
        ValueError: If method is not supported
    """
    if method == "minmax":
        new_min = kwargs.get("new_min", 0.0)
        new_max = kwargs.get("new_max", 1.0)
        return min_max_normalize(values, new_min, new_max)
    elif method == "zscore":
        return zscore_normalize(values)
    elif method == "robust":
        return robust_scale(values)
    else:
        raise ValueError(f"Unsupported normalization method: {method}")


def batch_normalize(
    data: list[list[float]],
    method: str = "zscore",
    fit_on_first: bool = True,
) -> list[list[float]]:
    """
    Normalize multiple time series consistently.

    Args:
        data: List of time series
        method: Normalization method
        fit_on_first: If True, use first series for fit parameters

    Returns:
        List of normalized time series
    """
    if not data:
        return []

    if fit_on_first:
        # Fit on first series
        first_series = data[0]
        if method == "zscore":
            m = mean(first_series)
            s = std(first_series)
            if s == 0:
                return [[0.0] * len(series) for series in data]
            return [[(v - m) / s for v in series] for series in data]
        elif method == "minmax":
            old_min = min(first_series)
            old_max = max(first_series)
            if old_max == old_min:
                return [[0.0] * len(series) for series in data]
            return [[(v - old_min) / (old_max - old_min) for v in series] for series in data]

    # Fit each series individually
    return [normalize(series, method) for series in data]
