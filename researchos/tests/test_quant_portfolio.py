"""
Unit tests for Portfolio Analytics missing components:
- Portfolio Variance
- Covariance Matrix
- Minimum Variance Portfolio
- Maximum Sharpe Ratio Portfolio
- Efficient Frontier curve generation
- Determinism verification
"""

import pytest

from researchos.quant_engine.portfolio.analytics import (
    covariance_matrix,
    efficient_frontier,
    maximum_sharpe_portfolio,
    minimum_variance_portfolio,
    portfolio_variance,
)
from researchos.quant_engine.portfolio.contracts import (
    EfficientFrontierPoint,
    EfficientFrontierResult,
    Portfolio,
)


def _asset_returns() -> list:
    # Asset 1: steady growth (mean return ~10% annualised)
    r1 = [0.001 * i for i in range(1, 51)]
    # Asset 2: volatile growth (mean return ~15% annualised, higher variance)
    r2 = [0.002 * i if i % 2 == 0 else -0.001 * i for i in range(1, 51)]
    # Asset 3: defensive asset (low return, low variance)
    r3 = [0.0005 * (i % 3) for i in range(1, 51)]
    return [r1, r2, r3]


class TestPortfolioMoments:
    def test_covariance_matrix(self):
        returns = _asset_returns()
        cov = covariance_matrix(returns)
        assert len(cov) == 3
        assert len(cov[0]) == 3
        assert cov[0][1] == cov[1][0]  # Symmetric
        assert cov[0][0] > 0
        assert cov[1][1] > 0

    def test_portfolio_variance(self):
        returns = _asset_returns()
        port = Portfolio(weights=[0.4, 0.4, 0.2], asset_returns=returns)
        p_var = portfolio_variance(port)
        assert p_var > 0.0


class TestEfficientFrontier:
    def test_minimum_variance_portfolio(self):
        returns = _asset_returns()
        mvp = minimum_variance_portfolio(returns, allow_short=False)
        assert isinstance(mvp, EfficientFrontierPoint)
        assert len(mvp.weights) == 3
        assert pytest.approx(sum(mvp.weights), abs=1e-4) == 1.0
        assert all(w >= -1e-5 for w in mvp.weights)  # Long only
        assert mvp.volatility > 0.0

    def test_maximum_sharpe_portfolio(self):
        returns = _asset_returns()
        msp = maximum_sharpe_portfolio(returns, risk_free_rate=0.01, allow_short=False)
        assert isinstance(msp, EfficientFrontierPoint)
        assert len(msp.weights) == 3
        assert pytest.approx(sum(msp.weights), abs=1e-4) == 1.0
        assert msp.sharpe_ratio >= 0.0

    def test_efficient_frontier_generation(self):
        returns = _asset_returns()
        ef_res = efficient_frontier(returns, num_portfolios=10, risk_free_rate=0.01)
        assert isinstance(ef_res, EfficientFrontierResult)
        assert len(ef_res.frontier_points) == 10
        assert ef_res.min_variance_portfolio is not None
        assert ef_res.max_sharpe_portfolio is not None

        # Check weights sum to 1 for all frontier points
        for pt in ef_res.frontier_points:
            assert pytest.approx(sum(pt.weights), abs=1e-4) == 1.0

    def test_efficient_frontier_determinism(self):
        returns = _asset_returns()
        res1 = efficient_frontier(returns, num_portfolios=10)
        res2 = efficient_frontier(returns, num_portfolios=10)
        assert res1.expected_returns == res2.expected_returns
        assert res1.min_variance_portfolio.weights == res2.min_variance_portfolio.weights
        assert res1.max_sharpe_portfolio.weights == res2.max_sharpe_portfolio.weights
