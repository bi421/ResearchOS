"""
Portfolio & Risk Analytics Engine — contracts and dataclass models.

Deterministic portfolio analysis. Research-only. No position execution,
no broker logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Portfolio:
    """
    Immutable portfolio definition.

    Attributes:
        weights: Asset weights (must sum to ~1 for fully-invested portfolios).
        asset_returns: List of return series, one per asset (same length).
        risk_free_rate: Annual risk-free rate (decimal).
        initial_capital: Optional notional for sizing analytics.
    """

    weights: List[float]
    asset_returns: List[List[float]] = field(default_factory=list)
    risk_free_rate: float = 0.0
    initial_capital: float = 100_000.0

    def validate(self) -> None:
        if len(self.weights) == 0:
            raise ValueError("portfolio must have at least one asset")
        if abs(sum(self.weights) - 1.0) > 1e-6:
            raise ValueError(f"weights must sum to 1.0, got {sum(self.weights)}")
        if len(self.asset_returns) > 0 and len(self.asset_returns) != len(self.weights):
            raise ValueError("asset_returns must align with weights")

    @property
    def num_assets(self) -> int:
        return len(self.weights)


@dataclass(frozen=True)
class PortfolioMetrics:
    """Aggregate portfolio performance and risk metrics."""

    annualised_return: float = 0.0
    annualised_volatility: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    max_drawdown: float = 0.0
    beta: float = 0.0
    alpha: float = 0.0
    treynor_ratio: float = 0.0
    information_ratio: float = 0.0
    value_at_risk_95: float = 0.0
    conditional_var_95: float = 0.0
    omega_ratio: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "annualised_return": self.annualised_return,
            "annualised_volatility": self.annualised_volatility,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "calmar_ratio": self.calmar_ratio,
            "max_drawdown": self.max_drawdown,
            "beta": self.beta,
            "alpha": self.alpha,
            "treynor_ratio": self.treynor_ratio,
            "information_ratio": self.information_ratio,
            "value_at_risk_95": self.value_at_risk_95,
            "conditional_var_95": self.conditional_var_95,
            "omega_ratio": self.omega_ratio,
        }


@dataclass(frozen=True)
class RiskContribution:
    """Per-asset risk contribution to the portfolio."""

    asset_index: int
    weight: float
    marginal_contribution: float = 0.0
    contribution: float = 0.0
    percent_contribution: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_index": self.asset_index,
            "weight": self.weight,
            "marginal_contribution": self.marginal_contribution,
            "contribution": self.contribution,
            "percent_contribution": self.percent_contribution,
        }


@dataclass(frozen=True)
class AllocationResult:
    """Capital allocation / position sizing analytics."""

    capital_per_asset: List[float] = field(default_factory=list)
    risk_budget_per_asset: List[float] = field(default_factory=list)
    kelly_fraction: float = 0.0
    total_capital: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "capital_per_asset": self.capital_per_asset,
            "risk_budget_per_asset": self.risk_budget_per_asset,
            "kelly_fraction": self.kelly_fraction,
            "total_capital": self.total_capital,
        }


@dataclass(frozen=True)
class EfficientFrontierPoint:
    """A single portfolio point on the Efficient Frontier."""

    weights: List[float]
    expected_return: float = 0.0
    volatility: float = 0.0
    sharpe_ratio: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "weights": self.weights,
            "expected_return": self.expected_return,
            "volatility": self.volatility,
            "sharpe_ratio": self.sharpe_ratio,
        }


@dataclass(frozen=True)
class EfficientFrontierResult:
    """The result of an Efficient Frontier calculation."""

    frontier_points: List[EfficientFrontierPoint] = field(default_factory=list)
    min_variance_portfolio: Optional[EfficientFrontierPoint] = None
    max_sharpe_portfolio: Optional[EfficientFrontierPoint] = None
    covariance_matrix: List[List[float]] = field(default_factory=list)
    expected_returns: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frontier_points": [p.to_dict() for p in self.frontier_points],
            "min_variance_portfolio": (
                self.min_variance_portfolio.to_dict() if self.min_variance_portfolio else None
            ),
            "max_sharpe_portfolio": (
                self.max_sharpe_portfolio.to_dict() if self.max_sharpe_portfolio else None
            ),
            "covariance_matrix": self.covariance_matrix,
            "expected_returns": self.expected_returns,
        }
