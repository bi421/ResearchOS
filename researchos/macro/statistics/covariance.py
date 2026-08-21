"""
ResearchOS Macro Intelligence Layer - Covariance
Version: stat/cov/v1
Status: FROZEN

MIL-STAT-001: Same input must always produce identical output.
MIL-STAT-002: Statistical functions are pure.
"""

from __future__ import annotations

from researchos.macro.statistics.descriptive import mean


def covariance(x: list[float], y: list[float], sample: bool = True) -> float:
    """
    Calculate covariance between two series.

    Args:
        x: First list of numeric values
        y: Second list of numeric values
        sample: If True, calculate sample covariance (N-1), else population (N)

    Returns:
        Covariance value

    Raises:
        ValueError: If lists have different lengths
    """
    if len(x) != len(y):
        raise ValueError("Lists must have same length")

    n = len(x)
    if n < 2:
        raise ValueError("Need at least 2 data points")

    x_mean = mean(x)
    y_mean = mean(y)

    cov = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))

    if sample:
        return cov / (n - 1)
    else:
        return cov / n


def rolling_covariance(
    x: list[float],
    y: list[float],
    window: int,
    min_periods: int | None = None,
) -> list[float | None]:
    """
    Calculate rolling covariance.

    Args:
        x: First list of numeric values
        y: Second list of numeric values
        window: Rolling window size
        min_periods: Minimum number of observations required

    Returns:
        List of rolling covariances (None if insufficient data)
    """
    if len(x) != len(y):
        raise ValueError("Lists must have same length")

    if min_periods is None:
        min_periods = window

    result = []
    for i in range(len(x)):
        if i < window - 1:
            result.append(None)
        else:
            x_window = x[i - window + 1 : i + 1]
            y_window = y[i - window + 1 : i + 1]

            if len(x_window) >= min_periods:
                result.append(covariance(x_window, y_window))
            else:
                result.append(None)

    return result


def correlation_from_covariance(
    cov_xy: float,
    std_x: float,
    std_y: float,
) -> float | None:
    """
    Calculate correlation from covariance and standard deviations.

    Args:
        cov_xy: Covariance between x and y
        std_x: Standard deviation of x
        std_y: Standard deviation of y

    Returns:
        Correlation coefficient (-1 to 1)
    """
    if std_x == 0 or std_y == 0:
        return None

    return cov_xy / (std_x * std_y)


def covariance_matrix(data: list[list[float]]) -> list[list[float]]:
    """
    Calculate covariance matrix.

    Args:
        data: List of lists, where each inner list is a time series

    Returns:
        Covariance matrix
    """
    n = len(data)
    matrix = [[0.0] * n for _ in range(n)]

    for i in range(n):
        for j in range(n):
            if i == j:
                # Variance (diagonal)
                from researchos.macro.statistics.descriptive import variance

                matrix[i][j] = variance(data[i])
            elif j > i:
                # Covariance (upper triangle)
                cov = covariance(data[i], data[j])
                matrix[i][j] = cov
                matrix[j][i] = cov  # Symmetric

    return matrix
