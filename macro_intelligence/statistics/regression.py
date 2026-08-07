"""
ResearchOS Macro Intelligence Layer - Regression Statistics
Version: stat/reg/v1
Status: FROZEN

MIL-STAT-001: Same input must always produce identical output.
MIL-STAT-002: Statistical functions are pure.
"""

from __future__ import annotations

from typing import List, Optional, NamedTuple
from math import sqrt
from macro_intelligence.statistics.descriptive import mean


class RegressionResult(NamedTuple):
    """Result of linear regression."""
    slope: float
    intercept: float
    r_squared: float
    standard_error: float


def slope(x: List[float], y: List[float]) -> float:
    """
    Calculate slope of linear regression.
    
    Args:
        x: Independent variable
        y: Dependent variable
        
    Returns:
        Slope coefficient
    """
    n = len(x)
    if n < 2:
        raise ValueError("Need at least 2 data points")
    
    x_mean = mean(x)
    y_mean = mean(y)
    
    numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
    denominator = sum((xi - x_mean) ** 2 for xi in x)
    
    if denominator == 0:
        return 0.0
    
    return numerator / denominator


def intercept(x: List[float], y: List[float]) -> float:
    """
    Calculate intercept of linear regression.
    
    Args:
        x: Independent variable
        y: Dependent variable
        
    Returns:
        Intercept coefficient
    """
    n = len(x)
    if n < 2:
        raise ValueError("Need at least 2 data points")
    
    x_mean = mean(x)
    y_mean = mean(y)
    slope_coef = slope(x, y)
    
    return y_mean - slope_coef * x_mean


def r_squared(x: List[float], y: List[float]) -> float:
    """
    Calculate R-squared (coefficient of determination).
    
    Args:
        x: Independent variable
        y: Dependent variable
        
    Returns:
        R-squared value (0 to 1)
    """
    n = len(x)
    if n < 2:
        raise ValueError("Need at least 2 data points")
    
    y_mean = mean(y)
    slope_coef = slope(x, y)
    intercept_coef = intercept(x, y)
    
    # Total sum of squares
    ss_tot = sum((yi - y_mean) ** 2 for yi in y)
    
    # Residual sum of squares
    ss_res = sum(
        (yi - (slope_coef * xi + intercept_coef)) ** 2
        for xi, yi in zip(x, y)
    )
    
    if ss_tot == 0:
        return 1.0 if ss_res == 0 else 0.0
    
    return 1.0 - (ss_res / ss_tot)


def linear_regression(
    x: List[float],
    y: List[float],
) -> RegressionResult:
    """
    Perform linear regression.
    
    Args:
        x: Independent variable
        y: Dependent variable
        
    Returns:
        RegressionResult with slope, intercept, R², and standard error
    """
    n = len(x)
    if n < 2:
        raise ValueError("Need at least 2 data points")
    
    slope_coef = slope(x, y)
    intercept_coef = intercept(x, y)
    r2 = r_squared(x, y)
    
    # Calculate standard error
    y_mean = mean(y)
    ss_tot = sum((yi - y_mean) ** 2 for yi in y)
    ss_res = sum(
        (yi - (slope_coef * xi + intercept_coef)) ** 2
        for xi, yi in zip(x, y)
    )
    
    if n > 2 and ss_tot > 0:
        std_error = sqrt(ss_res / (n - 2))
    else:
        std_error = 0.0
    
    return RegressionResult(
        slope=slope_coef,
        intercept=intercept_coef,
        r_squared=r2,
        standard_error=std_error,
    )


def predict(
    x: List[float],
    slope: float,
    intercept: float,
) -> List[float]:
    """
    Predict y values from linear regression.
    
    Args:
        x: Independent variable values
        slope: Slope coefficient
        intercept: Intercept coefficient
        
    Returns:
        Predicted y values
    """
    return [slope * xi + intercept for xi in x]


def residual_sum_of_squares(
    x: List[float],
    y: List[float],
    slope: Optional[float] = None,
    intercept: Optional[float] = None,
) -> float:
    """
    Calculate residual sum of squares.
    
    Args:
        x: Independent variable
        y: Dependent variable
        slope: Optional slope coefficient
        intercept: Optional intercept coefficient
        
    Returns:
        Residual sum of squares
    """
    if slope is None or intercept is None:
        reg = linear_regression(x, y)
        slope = reg.slope
        intercept = reg.intercept
    
    return sum(
        (yi - (slope * xi + intercept)) ** 2
        for xi, yi in zip(x, y)
    )


def standard_error_of_estimate(
    x: List[float],
    y: List[float],
) -> float:
    """
    Calculate standard error of estimate.
    
    Args:
        x: Independent variable
        y: Dependent variable
        
    Returns:
        Standard error
    """
    n = len(x)
    if n < 3:
        raise ValueError("Need at least 3 data points for standard error")
    
    reg = linear_regression(x, y)
    rss = residual_sum_of_squares(x, y, reg.slope, reg.intercept)
    
    return sqrt(rss / (n - 2))
