"""
Performance analytics for the Quant Computation Engine.

These are RESEARCH METRICS ONLY — NOT trading signals or decisions.

All calculations are:
    - Deterministic: Same inputs → same outputs
    - Versioned: CalculationVersion controls formula selection
    - Safe: Handles empty datasets, insufficient samples, edge cases

Based on Article XVII: Object Model — Quant Engine Layer.
"""

from __future__ import annotations

from typing import Any, Dict, List

from researchos.quant_engine.models import CalculationVersion
from researchos.quant_engine.statistics import (
    _validate_returns,
    mean,
    standard_deviation,
)


def win_rate(returns: List[float]) -> float:
    """
    Calculate the percentage of positive returns.

    Win_Rate = (Number of winning periods) / (Total periods)

    Args:
        returns: List of periodic returns.

    Returns:
        Win rate as a decimal (0.0 to 1.0).

    Raises:
        ValueError: If returns is empty.
    """
    _validate_returns(returns, min_samples=1)
    wins = sum(1 for r in returns if r > 0)
    return wins / len(returns)


def loss_rate(returns: List[float]) -> float:
    """
    Calculate the percentage of negative returns.

    Loss_Rate = (Number of losing periods) / (Total periods)

    Args:
        returns: List of periodic returns.

    Returns:
        Loss rate as a decimal (0.0 to 1.0).

    Raises:
        ValueError: If returns is empty.
    """
    _validate_returns(returns, min_samples=1)
    losses = sum(1 for r in returns if r < 0)
    return losses / len(returns)


def average_win(returns: List[float]) -> float:
    """
    Calculate the average positive return.

    Args:
        returns: List of periodic returns.

    Returns:
        Average positive return. Returns 0.0 if no winning periods.
    """
    wins = [r for r in returns if r > 0]
    if not wins:
        return 0.0
    return sum(wins) / len(wins)


def average_loss(returns: List[float]) -> float:
    """
    Calculate the average negative return.

    Args:
        returns: List of periodic returns.

    Returns:
        Average negative return (negative value). Returns 0.0 if no losing periods.
    """
    losses = [r for r in returns if r < 0]
    if not losses:
        return 0.0
    return sum(losses) / len(losses)


def win_loss_ratio(returns: List[float]) -> float:
    """
    Calculate the win/loss ratio.

    W/L Ratio = |Average Win / Average Loss|

    A ratio > 1.0 means wins are larger than losses on average.

    Args:
        returns: List of periodic returns.

    Returns:
        Win/loss ratio. Returns 0.0 if no wins or no losses.
    """
    avg_w = average_win(returns)
    avg_l = average_loss(returns)

    if avg_l == 0.0:
        return 0.0

    return abs(avg_w / avg_l)


def profit_factor(returns: List[float]) -> float:
    """
    Calculate the profit factor.

    Profit_Factor = Sum(Wins) / |Sum(Losses)|

    A profit factor > 1.0 means gross profit exceeds gross loss.

    Args:
        returns: List of periodic returns.

    Returns:
        Profit factor. Returns 0.0 if no losses (infinite profit factor).
        Returns float('inf') if no losses and there are wins.
    """
    total_wins = sum(r for r in returns if r > 0)
    total_losses = abs(sum(r for r in returns if r < 0))

    if total_losses == 0.0:
        if total_wins > 0.0:
            return float("inf")
        return 0.0

    return total_wins / total_losses


def consistency(returns: List[float]) -> float:
    """
    Calculate the consistency score.

    Consistency = (Positive periods) / (Total periods)

    This is the same as win_rate, but includes zero returns as neutral.
    Higher consistency indicates more predictable performance.

    Args:
        returns: List of periodic returns.

    Returns:
        Consistency as a decimal (0.0 to 1.0).

    Raises:
        ValueError: If returns is empty.
    """
    _validate_returns(returns, min_samples=1)
    return win_rate(returns)


def max_consecutive_wins(returns: List[float]) -> int:
    """
    Calculate the maximum consecutive winning periods.

    Args:
        returns: List of periodic returns.

    Returns:
        Longest streak of consecutive positive returns.
    """
    max_streak = 0
    current_streak = 0

    for r in returns:
        if r > 0:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0

    return max_streak


def max_consecutive_losses(returns: List[float]) -> int:
    """
    Calculate the maximum consecutive losing periods.

    Args:
        returns: List of periodic returns.

    Returns:
        Longest streak of consecutive negative returns.
    """
    max_streak = 0
    current_streak = 0

    for r in returns:
        if r < 0:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0

    return max_streak


def distribution_analysis(returns: List[float], bins: int = 10) -> Dict[str, Any]:
    """
    Analyse the distribution of returns.

    Divides the return range into bins and counts observations per bin.
    This is a research-only analysis — NOT a trading signal.

    Args:
        returns: List of periodic returns.
        bins: Number of bins for the distribution histogram.

    Returns:
        Dict with keys:
            - min: Minimum return.
            - max: Maximum return.
            - bin_edges: List of bin boundaries.
            - bin_counts: List of counts per bin.
            - positive_pct: Percentage of positive returns.
            - negative_pct: Percentage of negative returns.
            - zero_pct: Percentage of zero returns.

    Raises:
        ValueError: If returns is empty.
    """
    _validate_returns(returns, min_samples=1)

    if bins < 2:
        bins = 10

    min_r = min(returns)
    max_r = max(returns)
    range_r = max_r - min_r

    if range_r == 0.0:
        # All returns are identical
        bin_edges = [min_r] * (bins + 1)
        bin_counts = [len(returns)] + [0] * (bins - 1)
    else:
        bin_width = range_r / bins
        bin_edges = [min_r + i * bin_width for i in range(bins + 1)]
        bin_counts = [0] * bins

        for r in returns:
            # Find which bin this return falls into
            idx = min(int((r - min_r) / bin_width), bins - 1)
            bin_counts[idx] += 1

    total = len(returns)
    positive_count = sum(1 for r in returns if r > 0)
    negative_count = sum(1 for r in returns if r < 0)
    zero_count = sum(1 for r in returns if r == 0)

    return {
        "min": min_r,
        "max": max_r,
        "range": range_r,
        "bin_edges": [round(e, 8) for e in bin_edges],
        "bin_counts": bin_counts,
        "positive_pct": positive_count / total,
        "negative_pct": negative_count / total,
        "zero_pct": zero_count / total,
    }


def compute_performance_analytics(
    returns: List[float],
    calculation_version: CalculationVersion = CalculationVersion.CALCULATION_V1,
) -> Dict[str, Any]:
    """
    Compute a comprehensive set of research performance analytics.

    This is research-only analysis — NOT trading signals or decisions.

    Args:
        returns: List of periodic returns.
        calculation_version: Calculation methodology version.

    Returns:
        Dict with keys:
            - win_rate
            - loss_rate
            - average_win
            - average_loss
            - win_loss_ratio
            - profit_factor
            - consistency
            - max_consecutive_wins
            - max_consecutive_losses
            - total_returns
            - net_return

    Raises:
        ValueError: If returns is empty.
    """
    _validate_returns(returns, min_samples=1)

    if calculation_version != CalculationVersion.CALCULATION_V1:
        raise ValueError(f"Unsupported calculation version: {calculation_version}")

    return {
        "win_rate": win_rate(returns),
        "loss_rate": loss_rate(returns),
        "average_win": average_win(returns),
        "average_loss": average_loss(returns),
        "win_loss_ratio": win_loss_ratio(returns),
        "profit_factor": profit_factor(returns),
        "consistency": consistency(returns),
        "max_consecutive_wins": max_consecutive_wins(returns),
        "max_consecutive_losses": max_consecutive_losses(returns),
        "total_returns": len(returns),
        "net_return": sum(returns),
    }
