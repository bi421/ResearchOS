"""
Financial metrics for the Quant Computation Engine.

Implements standard performance metrics used in quantitative research.
All metrics are RESEARCH METRICS ONLY — NOT trading signals.

Formulas (CALCULATION_V1):
    - Sharpe Ratio: (mean(R) - R_f) / std(R) * sqrt(periods_per_year)
    - Sortino Ratio: (mean(R) - R_f) / downside_deviation(R) * sqrt(periods_per_year)
    - Calmar Ratio: mean(R) / |max_drawdown|
    - Profit Factor: sum(wins) / |sum(losses)|
    - Information Ratio: (mean(R) - mean(B)) / std(R - B)

Assumptions:
    - All returns are periodic (daily, hourly, etc.)
    - periods_per_year converts to annualised metrics (252 for daily, 52 for weekly, 12 for monthly)
    - Risk-free rate is provided as a decimal (e.g., 0.05 for 5% annual)

Based on Article XVII: Object Model — Quant Engine Layer.
"""

from __future__ import annotations

import math

from researchos.engines.quant.models import CalculationVersion
from researchos.engines.quant.statistics import (
    _validate_returns,
    mean,
    standard_deviation,
)


def downside_deviation(returns: list[float], ddof: int = 1) -> float:
    """
    Calculate the downside deviation — standard deviation of negative returns only.

    Only returns below zero are considered "risk" in this calculation.

    Args:
        returns: List of periodic returns.
        ddof: Delta degrees of freedom.

    Returns:
        Downside deviation value.

    Raises:
        ValueError: If returns is empty.
    """
    _validate_returns(returns, min_samples=1)

    negative_returns = [r for r in returns if r < 0]

    if len(negative_returns) < 2:
        return 0.0

    return standard_deviation(negative_returns, ddof=ddof)


def max_drawdown(equity_curve: list[float]) -> dict[str, float]:
    """
    Calculate the maximum drawdown and related metrics from an equity curve.

    Drawdown at point t = (equity[t] / peak_up_to_t) - 1
    Max drawdown = minimum of all drawdown values

    Args:
        equity_curve: Ordered list of equity values.

    Returns:
        Dict with keys:
            - max_drawdown: Maximum drawdown as decimal (e.g., -0.25).
            - max_drawdown_pct: Maximum drawdown as percentage.
            - recovery_period: Number of periods to recover from max drawdown (0 if not recovered).

    Raises:
        ValueError: If equity_curve has fewer than 2 elements.
    """
    if len(equity_curve) < 2:
        raise ValueError(f"Need at least 2 equity values, got {len(equity_curve)}")

    peak = equity_curve[0]
    max_dd = 0.0
    max_dd_end_idx = 0
    max_dd_peak_idx = 0

    for i, value in enumerate(equity_curve):
        if value > peak:
            peak = value
            max_dd_peak_idx = i

        dd = (value - peak) / peak if peak != 0 else 0.0
        if dd < max_dd:
            max_dd = dd
            max_dd_end_idx = i

    # Calculate recovery period
    recovery_period = 0
    if max_dd < 0:
        peak_before_dd = equity_curve[max_dd_peak_idx]
        for i in range(max_dd_end_idx, len(equity_curve)):
            if equity_curve[i] >= peak_before_dd:
                recovery_period = i - max_dd_end_idx
                break

    return {
        "max_drawdown": max_dd,
        "max_drawdown_pct": max_dd * 100,
        "recovery_period": recovery_period,
    }


def sharpe_ratio(
    returns: list[float],
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
    calculation_version: CalculationVersion = CalculationVersion.CALCULATION_V1,
) -> float:
    """
    Calculate the Sharpe ratio.

    Sharpe = (mean(R) - R_f) / std(R) * sqrt(periods_per_year)

    Higher values indicate better risk-adjusted returns.

    Args:
        returns: List of periodic returns.
        risk_free_rate: Annual risk-free rate (decimal, e.g., 0.05 for 5%).
        periods_per_year: Number of periods in a year (252 daily, 52 weekly, 12 monthly).
        calculation_version: Calculation methodology version.

    Returns:
        Sharpe ratio. Returns 0.0 if std(R) is zero.

    Raises:
        ValueError: If returns is empty.
    """
    _validate_returns(returns)

    if calculation_version != CalculationVersion.CALCULATION_V1:
        raise ValueError(f"Unsupported calculation version: {calculation_version}")

    std = standard_deviation(returns)
    if std == 0.0:
        return 0.0

    # Convert annual risk-free rate to periodic rate
    periodic_rf = risk_free_rate / periods_per_year
    excess_returns = mean(returns) - periodic_rf

    return excess_returns / std * math.sqrt(periods_per_year)


def sortino_ratio(
    returns: list[float],
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
    calculation_version: CalculationVersion = CalculationVersion.CALCULATION_V1,
) -> float:
    """
    Calculate the Sortino ratio.

    Sortino = (mean(R) - R_f) / downside_deviation(R) * sqrt(periods_per_year)

    Unlike Sharpe, Sortino only penalises negative volatility (downside deviation).

    Args:
        returns: List of periodic returns.
        risk_free_rate: Annual risk-free rate (decimal).
        periods_per_year: Number of periods in a year.
        calculation_version: Calculation methodology version.

    Returns:
        Sortino ratio. Returns 0.0 if downside deviation is zero.

    Raises:
        ValueError: If returns is empty.
    """
    _validate_returns(returns)

    if calculation_version != CalculationVersion.CALCULATION_V1:
        raise ValueError(f"Unsupported calculation version: {calculation_version}")

    dd = downside_deviation(returns)
    if dd == 0.0:
        return 0.0

    periodic_rf = risk_free_rate / periods_per_year
    excess_returns = mean(returns) - periodic_rf

    return excess_returns / dd * math.sqrt(periods_per_year)


def calmar_ratio(
    returns: list[float],
    equity_curve: list[float],
    periods_per_year: int = 252,
    calculation_version: CalculationVersion = CalculationVersion.CALCULATION_V1,
) -> float:
    """
    Calculate the Calmar ratio.

    Calmar = mean(R) * periods_per_year / |max_drawdown|

    Higher values indicate better return relative to maximum drawdown.

    Args:
        returns: List of periodic returns.
        equity_curve: List of equity values.
        periods_per_year: Number of periods in a year.
        calculation_version: Calculation methodology version.

    Returns:
        Calmar ratio. Returns 0.0 if max_drawdown is 0.

    Raises:
        ValueError: If returns is empty or equity_curve has < 2 elements.
    """
    _validate_returns(returns)

    if calculation_version != CalculationVersion.CALCULATION_V1:
        raise ValueError(f"Unsupported calculation version: {calculation_version}")

    dd_info = max_drawdown(equity_curve)
    max_dd = dd_info["max_drawdown"]

    if max_dd == 0.0:
        return 0.0

    annual_return = mean(returns) * periods_per_year
    return annual_return / abs(max_dd)


def profit_factor_metric(returns: list[float]) -> float:
    """
    Calculate the profit factor.

    Profit_Factor = sum(positive_returns) / |sum(negative_returns)|

    A value > 1.0 indicates gross profit exceeds gross loss.

    Args:
        returns: List of periodic returns.

    Returns:
        Profit factor. Returns float('inf') if no losses with wins.
        Returns 0.0 if no wins.
    """
    total_wins = sum(r for r in returns if r > 0)
    total_losses = abs(sum(r for r in returns if r < 0))

    if total_losses == 0.0:
        if total_wins > 0.0:
            return float("inf")
        return 0.0

    return total_wins / total_losses


def compute_all_metrics(
    returns: list[float],
    equity_curve: list[float],
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
    calculation_version: CalculationVersion = CalculationVersion.CALCULATION_V1,
) -> dict[str, float]:
    """
    Compute a comprehensive set of performance metrics.

    Args:
        returns: List of periodic returns.
        equity_curve: List of equity values.
        risk_free_rate: Annual risk-free rate (decimal).
        periods_per_year: Number of periods in a year.
        calculation_version: Calculation methodology version.

    Returns:
        Dict of metric_name -> computed_value.

    Raises:
        ValueError: If returns is empty or equity_curve has < 2 elements.
    """
    _validate_returns(returns)

    if calculation_version != CalculationVersion.CALCULATION_V1:
        raise ValueError(f"Unsupported calculation version: {calculation_version}")

    dd_info = max_drawdown(equity_curve)

    metrics: dict[str, float] = {
        "total_return": sum(returns),
        "mean_return": mean(returns),
        "std_return": standard_deviation(returns),
        "downside_deviation": downside_deviation(returns),
        "max_drawdown": dd_info["max_drawdown"],
        "sharpe_ratio": sharpe_ratio(returns, risk_free_rate, periods_per_year),
        "sortino_ratio": sortino_ratio(returns, risk_free_rate, periods_per_year),
        "calmar_ratio": calmar_ratio(returns, equity_curve, periods_per_year),
        "profit_factor": profit_factor_metric(returns),
        "win_rate": sum(1 for r in returns if r > 0) / max(len(returns), 1),
    }

    # Add annualised metrics
    metrics["annualised_return"] = mean(returns) * periods_per_year
    metrics["annualised_volatility"] = standard_deviation(returns) * math.sqrt(periods_per_year)

    return metrics
