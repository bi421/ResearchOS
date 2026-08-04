"""
ResearchOS Macro Intelligence Layer - Z-Score Analysis
Version: stat/zscore/v1
Status: FROZEN

MIL-STAT-001: Same input must always produce identical output.
MIL-STAT-002: Statistical functions are pure.
"""

from __future__ import annotations

from typing import List, Optional, Tuple
from macro_intelligence.statistics.descriptive import mean, std


def zscore(
    value: float,
    mean_val: float,
    std_val: float,
) -> float:
    """
    Calculate z-score for a single value.
    
    Args:
        value: Value to standardize
        mean_val: Mean of distribution
        std_val: Standard deviation of distribution
        
    Returns:
        Z-score
    """
    if std_val == 0:
        return 0.0
    
    return (value - mean_val) / std_val


def zscores(
    values: List[float],
    mean_val: Optional[float] = None,
    std_val: Optional[float] = None,
) -> List[float]:
    """
    Calculate z-scores for a list of values.
    
    Args:
        values: List of numeric values
        mean_val: Optional pre-calculated mean
        std_val: Optional pre-calculated standard deviation
        
    Returns:
        List of z-scores
    """
    if not values:
        return []
    
    if mean_val is None:
        mean_val = mean(values)
    
    if std_val is None:
        std_val = std(values)
    
    return [zscore(v, mean_val, std_val) for v in values]


def rolling_zscore(
    values: List[float],
    window: int,
    min_periods: Optional[int] = None,
) -> List[Tuple[float, float, float]]:
    """
    Calculate rolling z-scores with mean and std.
    
    Args:
        values: List of numeric values
        window: Rolling window size
        min_periods: Minimum number of observations required
        
    Returns:
        List of (value, zscore, std) tuples
    """
    if min_periods is None:
        min_periods = window
    
    result = []
    for i in range(len(values)):
        if i < window - 1:
            result.append((values[i], None, None))
        else:
            window_values = values[i - window + 1:i + 1]
            if len(window_values) >= min_periods:
                m = mean(window_values)
                s = std(window_values)
                z = zscore(values[i], m, s)
                result.append((values[i], z, s))
            else:
                result.append((values[i], None, None))
    
    return result


def interpret_zscore(zscore: float) -> str:
    """
    Interpret z-score magnitude.
    
    Args:
        zscore: Z-score value
        
    Returns:
        Interpretation string
    """
    abs_z = abs(zscore)
    
    if abs_z < 0.5:
        return "normal"
    elif abs_z < 1:
        return "mild"
    elif abs_z < 2:
        return "moderate"
    elif abs_z < 3:
        return "strong"
    else:
        return "extreme"


def zscore_threshold(
    values: List[float],
    threshold: float = 2.0,
) -> List[bool]:
    """
    Check which values exceed z-score threshold.
    
    Args:
        values: List of numeric values
        threshold: Z-score threshold
        
    Returns:
        List of booleans indicating threshold exceedance
    """
    m = mean(values)
    s = std(values)
    
    if s == 0:
        return [False] * len(values)
    
    return [abs((v - m) / s) > threshold for v in values]
