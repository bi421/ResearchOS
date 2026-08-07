"""
ResearchOS Macro Intelligence Layer - Volatility Analysis
Version: stat/vol/v1
Status: FROZEN

MIL-STAT-001: Same input must always produce identical output.
MIL-STAT-002: Statistical functions are pure.
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any
from math import sqrt
from macro_intelligence.statistics.descriptive import std
from macro_intelligence.statistics.rolling import rolling_std


def rolling_volatility(
    values: List[float],
    window: int = 20,
    annualize: bool = False,
    periods_per_year: int = 252,
) -> List[Optional[float]]:
    """
    Calculate rolling volatility.
    
    Args:
        values: List of numeric values (returns or prices)
        window: Rolling window
        annualize: Whether to annualize
        periods_per_year: Number of periods per year
        
    Returns:
        List of rolling volatilities
    """
    result = rolling_std(values, window)
    
    if annualize:
        ann_factor = sqrt(periods_per_year)
        result = [
            v * ann_factor if v is not None else None
            for v in result
        ]
    
    return result


def realized_volatility(
    returns: List[float],
    window: int = 20,
    annualize: bool = True,
    periods_per_year: int = 252,
) -> Optional[float]:
    """
    Calculate realized volatility over a window.
    
    Args:
        returns: List of returns
        window: Realized volatility window
        annualize: Whether to annualize
        periods_per_year: Number of periods per year
        
    Returns:
        Realized volatility (None if insufficient data)
    """
    if len(returns) < window:
        return None
    
    recent = returns[-window:]
    vol = std(recent)
    
    if annualize:
        vol *= sqrt(periods_per_year)
    
    return vol


def volatility_analysis(
    values: List[float],
    window: int = 20,
    annualize: bool = True,
) -> Dict[str, Any]:
    """
    Complete volatility analysis.
    
    Args:
        values: List of numeric values
        window: Analysis window
        annualize: Whether to annualize
        
    Returns:
        Dictionary with volatility metrics
    """
    if len(values) < window:
        return {
            "volatility": None,
            "volatility_regime": "insufficient_data",
            "volatility_percentile": None,
        }
    
    # Calculate realized volatility
    vol = realized_volatility(values, window, annualize)
    
    # Calculate volatility percentile
    if len(values) >= window * 10:
        # Use historical volatility for percentile
        historical = []
        for i in range(window, len(values), window):
            hv = realized_volatility(values[:i], window, annualize=False)
            if hv is not None:
                historical.append(hv)
        
        if historical:
            historical.sort()
            current_index = historical.index(vol) if vol in historical else 0
            percentile = (current_index / len(historical)) * 100
        else:
            percentile = None
    else:
        percentile = None
    
    # Determine volatility regime
    if vol is None:
        regime = "insufficient_data"
    elif percentile is not None:
        if percentile > 75:
            regime = "high"
        elif percentile < 25:
            regime = "low"
        else:
            regime = "normal"
    else:
        regime = "normal"
    
    return {
        "volatility": vol,
        "volatility_regime": regime,
        "volatility_percentile": percentile,
        "annualized": annualize,
    }


def garch_simplified(
    returns: List[float],
    omega: float = 0.00001,
    alpha: float = 0.1,
    beta: float = 0.85,
    iterations: int = 100,
) -> List[float]:
    """
    Simplified GARCH(1,1) volatility estimation.
    
    Args:
        returns: List of returns
        omega: Constant term
        alpha: ARCH term coefficient
        beta: GARCH term coefficient
        iterations: Number of iterations
        
    Returns:
        List of estimated volatilities
    """
    if not returns:
        return []
    
    # Initialize
    sigma2 = [variance(returns)]
    
    for i in range(1, min(iterations, len(returns))):
        # GARCH(1,1) equation
        sigma2.append(
            omega + alpha * returns[i - 1] ** 2 + beta * sigma2[-1]
        )
    
    return [sqrt(s) for s in sigma2]


def variance(returns: List[float]) -> float:
    """
    Calculate variance of returns.
    
    Args:
        returns: List of returns
        
    Returns:
        Variance
    """
    from macro_intelligence.statistics.descriptive import variance as var_func
    return var_func(returns)
