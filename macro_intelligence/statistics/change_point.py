"""
ResearchOS Macro Intelligence Layer - Change Point Detection
Version: stat/cp/v1
Status: FROZEN

MIL-STAT-001: Same input must always produce identical output.
MIL-STAT-002: Statistical functions are pure.
"""

from __future__ import annotations

from typing import List, Optional, Tuple
from math import sqrt
from macro_intelligence.statistics.descriptive import mean


def cusum(
    values: List[float],
    threshold: Optional[float] = None,
) -> List[Tuple[int, float]]:
    """
    CUSUM (Cumulative Sum) change point detection.
    
    Args:
        values: List of numeric values
        threshold: Detection threshold (auto-calculated if None)
        
    Returns:
        List of (index, cumulative_sum) tuples at change points
    """
    if not values:
        return []
    
    len(values)
    
    # Calculate threshold if not provided
    if threshold is None:
        # Auto-calculate based on standard deviation
        from macro_intelligence.statistics.descriptive import std
        s = std(values)
        threshold = 4 * s if s > 0 else 1.0
    
    # Calculate mean
    mu = mean(values)
    
    # Calculate CUSUM
    s_pos = 0.0
    s_neg = 0.0
    change_points = []
    
    for i, v in enumerate(values):
        # Positive CUSUM
        s_pos = max(0, s_pos + v - mu - 0.5 * threshold)
        # Negative CUSUM
        s_neg = max(0, s_neg - v + mu - 0.5 * threshold)
        
        # Check for change points
        if s_pos > threshold:
            change_points.append((i, s_pos))
            s_pos = 0
        elif s_neg > threshold:
            change_points.append((i, -s_neg))
            s_neg = 0
    
    return change_points


def detect_change_points(
    values: List[float],
    method: str = "cusum",
    **kwargs,
) -> List[int]:
    """
    Detect change points using specified method.
    
    Args:
        values: List of numeric values
        method: Detection method ('cusum', 'pearsong', 'binseg')
        **kwargs: Additional parameters
        
    Returns:
        List of change point indices
    """
    if method == "cusum":
        points = cusum(values, **kwargs)
        return [p[0] for p in points]
    else:
        raise ValueError(f"Unsupported change point detection method: {method}")


def structural_break_test(
    values: List[float],
    break_point: Optional[int] = None,
) -> Tuple[float, bool]:
    """
    Simple structural break test.
    
    Args:
        values: List of numeric values
        break_point: Proposed break point (auto-detected if None)
        
    Returns:
        (test_statistic, has_break)
    """
    if not values:
        return (0.0, False)
    
    n = len(values)
    
    if break_point is None:
        # Try to find optimal break point
        best_stat = 0.0
        best_point = n // 2
        
        for i in range(n // 4, 3 * n // 4):
            stat = _structural_break_stat(values, i)
            if stat > best_stat:
                best_stat = stat
                best_point = i
        
        break_point = best_point
    
    stat = _structural_break_stat(values, break_point)
    
    # Critical value approximation (simple rule of thumb)
    critical_value = 2.0
    
    return (stat, stat > critical_value)


def _structural_break_stat(
    values: List[float],
    break_point: int,
) -> float:
    """
    Calculate structural break test statistic.
    
    Args:
        values: List of numeric values
        break_point: Break point index
        
    Returns:
        Test statistic
    """
    if break_point <= 0 or break_point >= len(values):
        return 0.0
    
    first_half = values[:break_point]
    second_half = values[break_point:]
    
    mean1 = mean(first_half)
    mean2 = mean(second_half)
    
    # Pooled variance
    var1 = sum((x - mean1) ** 2 for x in first_half) / len(first_half)
    var2 = sum((x - mean2) ** 2 for x in second_half) / len(second_half)
    pooled_var = (var1 + var2) / 2
    
    if pooled_var == 0:
        return 0.0
    
    # T-statistic for difference in means
    se = sqrt(pooled_var * (1/len(first_half) + 1/len(second_half)))
    
    return abs(mean1 - mean2) / se
