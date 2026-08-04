"""
ResearchOS Macro Intelligence Layer - Descriptive Statistics
Version: stat/desc/v1
Status: FROZEN

MIL-STAT-001: Same input must always produce identical output.
MIL-STAT-002: Statistical functions are pure.
MIL-STAT-004: All outputs preserve provenance.
"""

from __future__ import annotations

from typing import List, Optional, Tuple, Dict, Any
from math import sqrt, pow
from macro_intelligence.time.normalizer import TimeNormalizer


def _py_min(values: List[float]) -> float:
    """Internal min function using built-in min."""
    result = values[0]
    for v in values[1:]:
        if v < result:
            result = v
    return result


def _py_max(values: List[float]) -> float:
    """Internal max function using built-in max."""
    result = values[0]
    for v in values[1:]:
        if v > result:
            result = v
    return result


def mean(values: List[float]) -> float:
    """
    Calculate arithmetic mean.
    
    Args:
        values: List of numeric values
        
    Returns:
        Arithmetic mean
        
    Raises:
        ValueError: If values list is empty
    """
    if not values:
        raise ValueError("Cannot calculate mean of empty list")
    
    return sum(values) / len(values)


def median(values: List[float]) -> float:
    """
    Calculate median.
    
    Args:
        values: List of numeric values
        
    Returns:
        Median value
        
    Raises:
        ValueError: If values list is empty
    """
    if not values:
        raise ValueError("Cannot calculate median of empty list")
    
    sorted_values = sorted(values)
    n = len(sorted_values)
    
    if n % 2 == 0:
        # Even number of elements
        return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2.0
    else:
        # Odd number of elements
        return sorted_values[n // 2]


def variance(values: List[float], sample: bool = True) -> float:
    """
    Calculate variance.
    
    Args:
        values: List of numeric values
        sample: If True, calculate sample variance (N-1), else population variance (N)
        
    Returns:
        Variance
        
    Raises:
        ValueError: If values list has fewer than 2 elements (for sample variance)
    """
    if not values:
        raise ValueError("Cannot calculate variance of empty list")
    
    n = len(values)
    if n < 2 and sample:
        raise ValueError("Cannot calculate sample variance with fewer than 2 elements")
    
    m = mean(values)
    squared_diffs = [(x - m) ** 2 for x in values]
    
    if sample:
        return sum(squared_diffs) / (n - 1)
    else:
        return sum(squared_diffs) / n


def std(values: List[float], sample: bool = True) -> float:
    """
    Calculate standard deviation.
    
    Args:
        values: List of numeric values
        sample: If True, calculate sample std (N-1), else population std (N)
        
    Returns:
        Standard deviation
    """
    return sqrt(variance(values, sample))


def skewness(values: List[float]) -> float:
    """
    Calculate skewness (third standardized moment).
    
    Args:
        values: List of numeric values
        
    Returns:
        Skewness coefficient
        
    Raises:
        ValueError: If values list has fewer than 3 elements
    """
    if not values:
        raise ValueError("Cannot calculate skewness of empty list")
    
    n = len(values)
    if n < 3:
        raise ValueError("Cannot calculate skewness with fewer than 3 elements")
    
    m = mean(values)
    s = std(values, sample=False)
    
    if s == 0:
        return 0.0
    
    # Fisher-Pearson coefficient
    summed = sum(((x - m) / s) ** 3 for x in values)
    return (n / ((n - 1) * (n - 2))) * summed


def kurtosis(values: List[float]) -> float:
    """
    Calculate excess kurtosis (fourth standardized moment - 3).
    
    Args:
        values: List of numeric values
        
    Returns:
        Excess kurtosis coefficient
        
    Raises:
        ValueError: If values list has fewer than 4 elements
    """
    if not values:
        raise ValueError("Cannot calculate kurtosis of empty list")
    
    n = len(values)
    if n < 4:
        raise ValueError("Cannot calculate kurtosis with fewer than 4 elements")
    
    m = mean(values)
    s = std(values, sample=False)
    
    if s == 0:
        return 0.0
    
    # Excess kurtosis
    m4 = sum(((x - m) / s) ** 4 for x in values)
    return ((n * (n + 1)) / ((n - 1) * (n - 2) * (n - 3))) * m4 - (3 * (n - 1) ** 2) / ((n - 2) * (n - 3))


def min(values: List[float]) -> float:
    """
    Calculate minimum value.
    
    Args:
        values: List of numeric values
        
    Returns:
        Minimum value
        
    Raises:
        ValueError: If values list is empty
    """
    if not values:
        raise ValueError("Cannot calculate min of empty list")
    
    return _py_min(values)


def max(values: List[float]) -> float:
    """
    Calculate maximum value.
    
    Args:
        values: List of numeric values
        
    Returns:
        Maximum value
        
    Raises:
        ValueError: If values list is empty
    """
    if not values:
        raise ValueError("Cannot calculate max of empty list")
    
    return _py_max(values)


def percentile(values: List[float], p: float) -> float:
    """
    Calculate percentile.
    
    Args:
        values: List of numeric values
        p: Percentile (0-100)
        
    Returns:
        Percentile value
        
    Raises:
        ValueError: If values list is empty or p is out of range
    """
    if not values:
        raise ValueError("Cannot calculate percentile of empty list")
    
    if not (0 <= p <= 100):
        raise ValueError(f"Percentile must be between 0 and 100, got {p}")
    
    sorted_values = sorted(values)
    n = len(sorted_values)
    
    # Use linear interpolation
    k = (p / 100) * (n - 1)
    f = int(k)
    c = f + 1
    
    if c >= n:
        return sorted_values[-1]
    
    return sorted_values[f] + (k - f) * (sorted_values[c] - sorted_values[f])


def descriptive_statistics(
    values: List[float],
    include_skewness: bool = True,
    include_kurtosis: bool = True,
) -> Dict[str, float]:
    """
    Calculate complete descriptive statistics.
    
    MIL-STAT-001: Same input must always produce identical output.
    MIL-STAT-002: Statistical functions are pure.
    
    Args:
        values: List of numeric values
        include_skewness: Include skewness calculation
        include_kurtosis: Include kurtosis calculation
        
    Returns:
        Dictionary of statistics
        
    Raises:
        ValueError: If values list is empty
    """
    if not values:
        raise ValueError("Cannot calculate statistics of empty list")
    
    n = len(values)
    result = {
        "count": n,
        "mean": mean(values),
        "median": median(values),
        "std": std(values),
        "variance": variance(values),
        "min": _py_min(values),
        "max": _py_max(values),
        "range": max(values) - min(values),
        "percentile_25": percentile(values, 25),
        "percentile_75": percentile(values, 75),
        "iqr": percentile(values, 75) - percentile(values, 25),
    }
    
    if include_skewness:
        try:
            result["skewness"] = skewness(values)
        except ValueError:
            result["skewness"] = None
    
    if include_kurtosis:
        try:
            result["kurtosis"] = kurtosis(values)
        except ValueError:
            result["kurtosis"] = None
    
    return result


def five_number_summary(values: List[float]) -> Dict[str, float]:
    """
    Calculate five-number summary.
    
    Args:
        values: List of numeric values
        
    Returns:
        Dictionary with min, Q1, median, Q3, max
    """
    return {
        "min": min(values),
        "q1": percentile(values, 25),
        "median": median(values),
        "q3": percentile(values, 75),
        "max": max(values),
    }


def quartiles(values: List[float]) -> Tuple[float, float, float]:
    """
    Calculate quartiles.
    
    Args:
        values: List of numeric values
        
    Returns:
        (Q1, Median, Q3)
    """
    return (
        percentile(values, 25),
        median(values),
        percentile(values, 75),
    )


def interquartile_range(values: List[float]) -> float:
    """
    Calculate interquartile range.
    
    Args:
        values: List of numeric values
        
    Returns:
        IQR value
    """
    return percentile(values, 75) - percentile(values, 25)
