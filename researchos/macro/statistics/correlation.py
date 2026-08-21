"""
ResearchOS Macro Intelligence Layer - Correlation Statistics
Version: stat/corr/v1
Status: FROZEN

MIL-STAT-001: Same input must always produce identical output.
MIL-STAT-002: Statistical functions are pure.
"""

from __future__ import annotations

from math import sqrt

from researchos.macro.statistics.descriptive import mean


def pearson_correlation(x: list[float], y: list[float]) -> float | None:
    """
    Calculate Pearson correlation coefficient.

    Args:
        x: First list of numeric values
        y: Second list of numeric values

    Returns:
        Pearson correlation coefficient (-1 to 1)

    Raises:
        ValueError: If lists have different lengths or insufficient data
    """
    if len(x) != len(y):
        raise ValueError("Lists must have same length")

    n = len(x)
    if n < 2:
        raise ValueError("Need at least 2 data points")

    x_mean = mean(x)
    y_mean = mean(y)

    # Calculate covariance and standard deviations
    cov_xy = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
    std_x = sqrt(sum((xi - x_mean) ** 2 for xi in x))
    std_y = sqrt(sum((yi - y_mean) ** 2 for yi in y))

    if std_x == 0 or std_y == 0:
        return None

    return cov_xy / (std_x * std_y)


def spearman_correlation(x: list[float], y: list[float]) -> float | None:
    """
    Calculate Spearman rank correlation coefficient.

    Args:
        x: First list of numeric values
        y: Second list of numeric values

    Returns:
        Spearman correlation coefficient (-1 to 1)
    """
    # Rank the values
    x_ranked = _rank_values(x)
    y_ranked = _rank_values(y)

    # Calculate Pearson correlation on ranks
    return pearson_correlation(x_ranked, y_ranked)


def _rank_values(values: list[float]) -> list[float]:
    """
    Convert values to ranks.

    Args:
        values: List of numeric values

    Returns:
        List of ranks
    """
    # Create (value, original_index) pairs
    paired = [(v, i) for i, v in enumerate(values)]
    # Sort by value
    paired.sort(key=lambda x: x[0])

    # Assign ranks
    ranks = [0.0] * len(values)
    i = 0
    while i < len(paired):
        # Find all values with same value (ties)
        j = i
        while j < len(paired) and paired[j][0] == paired[i][0]:
            j += 1

        # Assign average rank to ties
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[paired[k][1]] = avg_rank

        i = j

    return ranks


def rolling_correlation(
    x: list[float],
    y: list[float],
    window: int,
    min_periods: int | None = None,
) -> list[float | None]:
    """
    Calculate rolling Pearson correlation.

    Args:
        x: First list of numeric values
        y: Second list of numeric values
        window: Rolling window size
        min_periods: Minimum number of observations required

    Returns:
        List of rolling correlations (None if insufficient data)
    """
    if min_periods is None:
        min_periods = window

    if len(x) != len(y):
        raise ValueError("Lists must have same length")

    result = []
    for i in range(len(x)):
        if i < window - 1:
            result.append(None)
        else:
            x_window = x[i - window + 1 : i + 1]
            y_window = y[i - window + 1 : i + 1]

            if len(x_window) >= min_periods:
                result.append(pearson_correlation(x_window, y_window))
            else:
                result.append(None)

    return result


def correlation_matrix(data: list[list[float]]) -> list[list[float | None]]:
    """
    Calculate correlation matrix.

    Args:
        data: List of lists, where each inner list is a time series

    Returns:
        Correlation matrix
    """
    n = len(data)
    matrix = [[None] * n for _ in range(n)]

    for i in range(n):
        for j in range(n):
            if i == j:
                matrix[i][j] = 1.0
            elif j > i:
                corr = pearson_correlation(data[i], data[j])
                matrix[i][j] = corr
                matrix[j][i] = corr

    return matrix
