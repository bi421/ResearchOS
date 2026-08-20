"""
Unit tests for Fundamental Analytics missing models:
- Real Yield (linear proxy and exact Fisher equation)
- Bond Spread (spread series and yield spread metrics)
- Determinism verification
"""

import pytest

from researchos.quant_engine.fundamental.analytics import (
    bond_spread,
    bond_spread_series,
    fisher_real_yield,
    real_yield,
    real_yield_series,
    yield_spread_metrics,
)


class TestRealYield:
    def test_real_yield_linear(self):
        # 5.0% nominal yield - 2.0% inflation = 3.0% real yield
        ry = real_yield(5.0, 2.0)
        assert ry == 3.0

    def test_fisher_real_yield(self):
        # Exact Fisher: (1 + 0.05) / (1 + 0.02) - 1 = 0.0294117647...
        fry = fisher_real_yield(5.0, 2.0)
        assert abs(fry - 2.94117647) < 1e-5

    def test_real_yield_series(self):
        nominals = [4.0, 4.5, 5.0]
        inflations = [2.0, 2.5, 2.0]
        res = real_yield_series(nominals, inflations)
        assert res == [2.0, 2.0, 3.0]

    def test_real_yield_determinism(self):
        nominals = [4.0, 4.5, 5.0]
        inflations = [2.0, 2.5, 2.0]
        res1 = real_yield_series(nominals, inflations, exact_fisher=True)
        res2 = real_yield_series(nominals, inflations, exact_fisher=True)
        assert res1 == res2

    def test_mismatched_length_raises(self):
        with pytest.raises(ValueError):
            real_yield_series([4.0], [2.0, 2.5])


class TestBondSpread:
    def test_bond_spread_single(self):
        # 10Y Corporate (5.5%) - 10Y Treasury (4.0%) = 1.5%
        sp = bond_spread(5.5, 4.0)
        assert sp == 1.5

    def test_bond_spread_series(self):
        a = [5.0, 5.5, 6.0]
        b = [4.0, 4.2, 4.5]
        res = bond_spread_series(a, b)
        assert pytest.approx(res) == [1.0, 1.3, 1.5]

    def test_yield_spread_metrics(self):
        yields = {"3M": 5.2, "2Y": 4.5, "10Y": 4.2, "30Y": 4.4}
        metrics = yield_spread_metrics(yields)
        assert "10y_2y_spread" in metrics
        assert pytest.approx(metrics["10y_2y_spread"]) == -0.3
        assert "30y_10y_spread" in metrics
        assert pytest.approx(metrics["30y_10y_spread"]) == 0.2
        assert "10y_3m_spread" in metrics
        assert pytest.approx(metrics["10y_3m_spread"]) == -1.0

    def test_bond_spread_determinism(self):
        yields = {"3M": 5.2, "2Y": 4.5, "10Y": 4.2, "30Y": 4.4}
        res1 = yield_spread_metrics(yields)
        res2 = yield_spread_metrics(yields)
        assert res1 == res2
