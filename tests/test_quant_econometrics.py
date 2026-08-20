"""
Unit tests for Econometrics Engine missing models:
- ARIMA
- SARIMA
- VAR
- Cointegration (Engle-Granger)
- Johansen Test
- EGARCH
- TGARCH
- Determinism verification
"""

import math

from researchos.quant_engine.econometrics import (
    CointegrationTestResult,
    JohansenTestResult,
    ModelFamily,
    engle_granger_cointegration,
    fit_arima,
    fit_egarch,
    fit_sarima,
    fit_tgarch,
    fit_var,
    johansen_test,
)


def _sine_series(length: int = 50) -> list:
    return [10.0 + math.sin(i * 0.2) * 2.0 + (i * 0.1) for i in range(length)]


def _returns_series(length: int = 60) -> list:
    return [0.01 if i % 2 == 0 else -0.008 for i in range(length)]


class TestARIMA:
    def test_fit_arima(self):
        series = _sine_series(40)
        model = fit_arima(series, p=1, d=1, q=1)
        assert model.family == ModelFamily.ARIMA
        assert model.metadata["p_order"] == 1
        assert model.metadata["d_order"] == 1
        assert model.metadata["q_order"] == 1
        assert isinstance(model.aic, float)

    def test_arima_determinism(self):
        series = _sine_series(40)
        m1 = fit_arima(series, p=1, d=1, q=1)
        m2 = fit_arima(series, p=1, d=1, q=1)
        assert m1.coefficients == m2.coefficients
        assert m1.aic == m2.aic


class TestSARIMA:
    def test_fit_sarima(self):
        series = _sine_series(50)
        model = fit_sarima(series, p=1, d=1, q=1, P=1, D=1, Q=1, s=4)
        assert model.family == ModelFamily.SARIMA
        assert model.metadata["seasonal_period"] == 4

    def test_sarima_determinism(self):
        series = _sine_series(50)
        m1 = fit_sarima(series, p=1, d=1, q=1, P=1, D=1, Q=1, s=4)
        m2 = fit_sarima(series, p=1, d=1, q=1, P=1, D=1, Q=1, s=4)
        assert m1.coefficients == m2.coefficients


class TestVAR:
    def test_fit_var(self):
        s1 = [10.0 + i * 0.1 for i in range(30)]
        s2 = [5.0 + i * 0.2 for i in range(30)]
        model = fit_var([s1, s2], p=1)
        assert model.family == ModelFamily.VAR
        assert model.metadata["k_vars"] == 2
        assert "var_0_const" in model.coefficients
        assert "var_1_const" in model.coefficients

    def test_var_determinism(self):
        s1 = [10.0 + i * 0.1 for i in range(30)]
        s2 = [5.0 + i * 0.2 for i in range(30)]
        m1 = fit_var([s1, s2], p=1)
        m2 = fit_var([s1, s2], p=1)
        assert m1.coefficients == m2.coefficients


class TestCointegration:
    def test_engle_granger(self):
        x = [10.0 + i * 0.5 for i in range(40)]
        # y is strongly cointegrated with x (y = 2*x + 1 + noise)
        y = [2.0 * x_i + 1.0 + (0.01 if i % 2 == 0 else -0.01) for i, x_i in enumerate(x)]
        res = engle_granger_cointegration(y, x)
        assert isinstance(res, CointegrationTestResult)
        assert abs(res.beta - 2.0) < 0.1
        assert res.is_cointegrated is True

    def test_engle_granger_determinism(self):
        x = [10.0 + i * 0.5 for i in range(40)]
        y = [2.0 * x_i + 1.0 for x_i in x]
        r1 = engle_granger_cointegration(y, x)
        r2 = engle_granger_cointegration(y, x)
        assert r1.alpha == r2.alpha
        assert r1.beta == r2.beta
        assert r1.adf_statistic == r2.adf_statistic

    def test_johansen_test(self):
        s1 = [10.0 + i * 0.5 for i in range(40)]
        s2 = [2.0 * s1[i] + 1.0 for i in range(40)]
        res = johansen_test([s1, s2])
        assert isinstance(res, JohansenTestResult)
        assert len(res.trace_statistics) == 2
        assert res.cointegration_rank >= 1
        assert res.is_cointegrated is True

    def test_johansen_determinism(self):
        s1 = [10.0 + i * 0.5 for i in range(40)]
        s2 = [2.0 * s1[i] + 1.0 for i in range(40)]
        r1 = johansen_test([s1, s2])
        r2 = johansen_test([s1, s2])
        assert r1.trace_statistics == r2.trace_statistics
        assert r1.eigenvalues == r2.eigenvalues


class TestVolatilityModels:
    def test_egarch(self):
        returns = _returns_series(40)
        res = fit_egarch(returns)
        assert res.family == ModelFamily.EGARCH
        assert len(res.conditional_volatility) == 40
        assert len(res.forecast_volatility) == 1

    def test_egarch_determinism(self):
        returns = _returns_series(40)
        r1 = fit_egarch(returns)
        r2 = fit_egarch(returns)
        assert r1.conditional_volatility == r2.conditional_volatility

    def test_tgarch(self):
        returns = _returns_series(40)
        res = fit_tgarch(returns)
        assert res.family == ModelFamily.TGARCH
        assert len(res.conditional_volatility) == 40
        assert len(res.forecast_volatility) == 1

    def test_tgarch_determinism(self):
        returns = _returns_series(40)
        r1 = fit_tgarch(returns)
        r2 = fit_tgarch(returns)
        assert r1.conditional_volatility == r2.conditional_volatility
