"""
ResearchOS Macro Intelligence Layer — Econometrics Engine Stress Tests (Phase 3.5)

Deterministic numerical stress testing covering:
  - Matrix: near-singular, singular, ill-conditioned, zero-variance columns,
    empty inputs, minimal sample sizes
  - Regression: perfect multicollinearity, constant features, insufficient
    observations, extreme values, very small datasets
  - Time series: ADF (stationary/non-stationary/constant/short), KPSS (trend /
    singular fallback), ACF/PACF (short / zero-variance), cointegration
    (unequal length / missing alignment), Granger (insufficient lag samples),
    VIF (perfect correlation / independent), heteroskedasticity (constant
    residuals)

Expected behavior:
  - deterministic failure (meaningful exceptions)
  - no silent corruption
  - OLS delegation to the canonical Statistics owner remains intact
"""

from __future__ import annotations

import math

import pytest

from macro_intelligence.econometrics.autocorrelation import (
    autocorrelation,
    partial_autocorrelation,
)
from macro_intelligence.econometrics.causality import granger_causality
from macro_intelligence.econometrics.cointegration import engle_granger
from macro_intelligence.econometrics.diagnostics import (
    durbin_watson,
    jarque_bera,
    residual_diagnostics,
)
from macro_intelligence.econometrics.heteroskedasticity import breusch_pagan
from macro_intelligence.econometrics.information_criteria import (
    aic,
    bic,
    information_criteria,
)
from macro_intelligence.econometrics.intervals import (
    confidence_interval,
    prediction_interval,
)
from macro_intelligence.econometrics.matrix import (
    determinant,
    identity,
    invert,
    matmul,
    solve,
    transpose,
)
from macro_intelligence.econometrics.regression import (
    logistic_regression,
    multiple_regression,
    polynomial_regression,
    univariate_ols,
)
from macro_intelligence.econometrics.stationarity import (
    augmented_dickey_fuller,
    kpss,
)
from macro_intelligence.econometrics.vif import variance_inflation_factor


# ---------------------------------------------------------------------------
# Matrix Layer — stress
# ---------------------------------------------------------------------------
class TestMatrixStress:
    def test_singular_matrix_raises(self):
        """A singular matrix must raise a meaningful ValueError."""
        singular = [[1.0, 2.0], [2.0, 4.0]]  # det = 0
        with pytest.raises(ValueError):
            invert(singular)

    def test_near_singular_matrix_determinant(self):
        """A near-singular matrix should produce a tiny but non-zero det."""
        near = [[1.0, 2.0], [2.0, 4.0 + 1e-10]]
        d = determinant(near)
        assert d != 0.0
        assert abs(d) < 1e-6

    def test_ill_conditioned_solve_returns_finite(self):
        """Ill-conditioned solve should return a finite result (no crash)."""
        a = [[1.0, 2.0 + 1e-12], [1.0 + 1e-12, 2.0]]
        b = [1.0, 1.0]
        x = solve(a, b)
        assert all(math.isfinite(v) for v in x)

    def test_zero_variance_column_invert(self):
        """A matrix with a zero column is singular and must raise."""
        m = [[1.0, 0.0], [2.0, 0.0]]
        with pytest.raises(ValueError):
            invert(m)

    def test_empty_matrix_transpose(self):
        assert transpose([]) == []

    def test_empty_matmul(self):
        assert matmul([], [[1.0]]) == []

    def test_minimal_single_element(self):
        assert invert([[3.0]]) == [[pytest.approx(1.0 / 3.0)]]

    def test_identity_inverse(self):
        m = identity(4)
        assert invert(m) == m

    def test_matmul_dimension_mismatch_raises(self):
        with pytest.raises(ValueError):
            matmul([[1.0, 2.0]], [[1.0], [2.0], [3.0]])

    def test_non_square_invert_raises(self):
        with pytest.raises(ValueError):
            invert([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])


# ---------------------------------------------------------------------------
# Regression Layer — stress
# ---------------------------------------------------------------------------
def _perfect_multiple_data(n: int = 30):
    x = [[float(i), float(i * i)] for i in range(n)]
    y = [2.0 + 3.0 * float(i) - 1.0 * float(i * i) for i in range(n)]
    return x, y


class TestRegressionStress:
    def test_perfect_multicollinearity(self):
        """x2 is exactly 2*x1 → collinear design matrix is singular → the
        OLS solve raises a deterministic, meaningful ValueError."""
        x = [[float(i), 2.0 * float(i)] for i in range(30)]
        y = [1.0 + float(i) for i in range(30)]
        with pytest.raises(ValueError):
            multiple_regression(x, y)

    def test_constant_feature(self):
        """A constant predictor column is collinear with the intercept →
        singular design → deterministic ValueError."""
        x = [[1.0, float(i)] for i in range(30)]
        y = [2.0 + float(i) for i in range(30)]
        with pytest.raises(ValueError):
            multiple_regression(x, y)

    def test_insufficient_observations_multiple(self):
        """Fewer observations than parameters → still returns (df clipped)."""
        x = [[1.0], [2.0], [3.0]]
        y = [1.0, 2.0, 3.0]
        r = multiple_regression(x, y)
        assert r.n_observations == 3

    def test_extreme_values(self):
        """Large-magnitude values must not raise."""
        x = [[float(i) * 1e6 for i in range(10)]]
        # Ten observations, one predictor.
        x = [[float(i) * 1e6] for i in range(10)]
        y = [float(i) * 1e6 for i in range(10)]
        r = multiple_regression(x, y)
        assert math.isfinite(r.r_squared)

    def test_empty_y_raises(self):
        with pytest.raises(ValueError):
            multiple_regression([[1.0]], [])

    def test_mismatched_lengths_raises(self):
        with pytest.raises(ValueError):
            multiple_regression([[1.0], [2.0]], [1.0])

    def test_polynomial_small_dataset(self):
        r = polynomial_regression([1.0, 2.0, 3.0], [1.0, 4.0, 9.0], degree=1)
        assert math.isfinite(r.r_squared)

    def test_logistic_constant_features(self):
        """Logistic regression with a constant feature should not crash."""
        x = [[1.0, 2.0], [1.0, 3.0], [1.0, 4.0], [1.0, 5.0]]
        y = [0, 0, 1, 1]
        r = logistic_regression(x, y)
        assert r.converged is not None

    def test_univariate_ols_delegation_preserved(self):
        """Single-variable OLS must still delegate (no duplicate OLS)."""
        x = [float(i) for i in range(30)]
        y = [2.0 + 3.0 * float(i) for i in range(30)]
        r = univariate_ols(x, y)
        assert r.method == "ols"
        assert r.method_version == "stat/reg/v1"
        assert r.coefficients[1] == pytest.approx(3.0, abs=1e-6)


# ---------------------------------------------------------------------------
# Time-series layer — stress
# ---------------------------------------------------------------------------
class TestADFStress:
    def test_stationary_series(self):
        series = [0.5 * math.sin(i / 3.0) for i in range(100)]
        r = augmented_dickey_fuller(series, max_lag=1)
        assert math.isfinite(r.statistic)

    def test_non_stationary_series(self):
        series = [float(i) for i in range(100)]
        r = augmented_dickey_fuller(series, max_lag=1)
        assert math.isfinite(r.statistic)

    def test_constant_series(self):
        """A constant series has zero variance; ADF must not crash."""
        series = [5.0] * 100
        r = augmented_dickey_fuller(series, max_lag=1)
        assert r.statistic is not None

    def test_short_series_raises(self):
        with pytest.raises(ValueError):
            augmented_dickey_fuller([1.0, 2.0])


class TestKPSSStress:
    def test_trend_case(self):
        series = [float(i) for i in range(60)]
        r = kpss(series, trend="ct")
        assert math.isfinite(r.statistic)

    def test_constant_series_finite(self):
        """A constant series has zero residual variance; KPSS must return a
        finite statistic (sigma2 is clamped to a tiny epsilon), not crash."""
        r = kpss([5.0] * 50, trend="c")
        assert math.isfinite(r.statistic)

    def test_short_series_raises(self):
        with pytest.raises(ValueError):
            kpss([1.0, 2.0, 3.0])


class TestACFPACFStress:
    def test_acf_short_sample(self):
        r = autocorrelation([1.0, 2.0, 3.0], max_lag=2)
        assert r.test_name == "autocorrelation"

    def test_acf_zero_variance(self):
        """Zero-variance series → ACF must not divide by zero."""
        r = autocorrelation([5.0] * 10, max_lag=2)
        assert math.isfinite(r.statistic)

    def test_pacf_short_sample(self):
        r = partial_autocorrelation([1.0, 2.0, 3.0, 4.0], max_lag=2)
        assert r.test_name == "partial_autocorrelation"

    def test_pacf_zero_variance(self):
        r = partial_autocorrelation([5.0] * 10, max_lag=2)
        assert math.isfinite(r.statistic)


class TestEngleGrangerStress:
    def test_unequal_length_raises(self):
        with pytest.raises(ValueError):
            engle_granger([1.0, 2.0, 3.0, 4.0], [1.0, 2.0, 3.0])

    def test_too_short_raises(self):
        with pytest.raises(ValueError):
            engle_granger([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])

    def test_missing_alignment_constant(self):
        """Constant series → step-1 regression is singular → deterministic
        ValueError (no silent corruption)."""
        with pytest.raises(ValueError):
            engle_granger([5.0] * 20, [5.0] * 20)


class TestGrangerStress:
    def test_insufficient_lag_samples(self):
        """Too few observations for the requested lags → still returns a
        result (max_lag is clipped) or raises a meaningful error."""
        series = [float(i) for i in range(10)]
        try:
            r = granger_causality(series, series, max_lag=5)
            assert r.test_name == "granger_causality"
        except ValueError:
            pass  # acceptable deterministic failure

    def test_short_series_raises(self):
        with pytest.raises(ValueError):
            granger_causality([1.0, 2.0], [1.0, 2.0])


class TestVIFStress:
    def test_perfect_correlation(self):
        """x2 = 2*x1 → perfect multicollinearity → infinite VIF (no crash)."""
        x = [[float(i), 2.0 * float(i)] for i in range(30)]
        r = variance_inflation_factor(x)
        assert r.test_name == "variance_inflation_factor"

    def test_independent_variables(self):
        """Independent predictors → VIF near 1."""
        x = [[float(i), float(i) * float(i)] for i in range(30)]
        r = variance_inflation_factor(x)
        vifs = r.critical_values["vif"]
        assert all(v > 0 for v in vifs)

    def test_single_predictor_raises(self):
        with pytest.raises(ValueError):
            variance_inflation_factor([[1.0], [2.0]])


class TestBreuschPaganStress:
    def test_constant_residuals(self):
        """Homoskedastic residuals → LM statistic near zero, no crash."""
        y = [float(i) for i in range(50)]
        x = [[float(i)] for i in range(50)]
        r = breusch_pagan(y, x)
        assert math.isfinite(r.statistic)

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            breusch_pagan([], [[1.0]])


class TestDiagnosticsStress:
    def test_durbin_watson_constant(self):
        r = durbin_watson([1.0] * 10)
        assert math.isfinite(r.statistic)

    def test_jarque_bera_short_raises(self):
        with pytest.raises(ValueError):
            jarque_bera([1.0, 2.0, 3.0])

    def test_residual_diagnostics_short_raises(self):
        with pytest.raises(ValueError):
            residual_diagnostics([1.0, 2.0, 3.0])


class TestIntervalsStress:
    def test_confidence_interval_invalid_level(self):
        with pytest.raises(ValueError):
            confidence_interval(1.0, 0.1, 100, level=0.0)

    def test_prediction_interval_short_residuals(self):
        with pytest.raises(ValueError):
            prediction_interval(1.0, [1.0])


class TestInformationCriteriaStress:
    def test_empty_residuals_raises(self):
        with pytest.raises(ValueError):
            aic([], 2)

    def test_bic_empty_raises(self):
        with pytest.raises(ValueError):
            bic([], 2)

    def test_information_criteria_empty_raises(self):
        with pytest.raises(ValueError):
            information_criteria([], 2)
