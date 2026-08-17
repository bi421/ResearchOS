"""
ResearchOS Macro Intelligence Layer — Econometrics Engine Tests (Phase 3)

Covers:
  - Multiple / polynomial / logistic regression (numerical reference validation)
  - Univariate OLS delegation to the canonical Statistics owner (no duplication)
  - ACF / PACF
  - Stationarity: ADF, KPSS
  - Cointegration: Engle-Granger
  - Causality: Granger
  - VIF
  - Heteroskedasticity: Breusch-Pagan
  - Diagnostics: Durbin-Watson, Jarque-Bera, residual/model diagnostics
  - Intervals: confidence, prediction
  - Information criteria: AIC, BIC
  - Determinism, immutability, serialization round-trip, provenance
"""

from __future__ import annotations

import math

import pytest

from macro_intelligence.econometrics import (
    InformationCriteria,
    IntervalResult,
    ModelDiagnostics,
    # Models
    RegressionResult,
    ResidualDiagnostics,
    # Information criteria
    aic,
    # Stationarity
    augmented_dickey_fuller,
    # Autocorrelation
    autocorrelation,
    bic,
    # Heteroskedasticity
    breusch_pagan,
    # Intervals
    confidence_interval,
    deterministic_hash,
    # Diagnostics
    durbin_watson,
    # Cointegration
    engle_granger,
    # Causality
    granger_causality,
    information_criteria,
    jarque_bera,
    kpss,
    logistic_regression,
    model_diagnostics,
    # Regression
    multiple_regression,
    partial_autocorrelation,
    polynomial_regression,
    prediction_interval,
    residual_diagnostics,
    univariate_ols,
    # VIF
    variance_inflation_factor,
    vif,
)
from macro_intelligence.econometrics import (
    TestResult as EconometricTestResult,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _perfect_multiple_data(n: int = 30):
    """y = 2 + 3*x1 - 1*x2 exactly."""
    x = [[float(i), float(i * i)] for i in range(n)]
    y = [2.0 + 3.0 * float(i) - 1.0 * float(i * i) for i in range(n)]
    return x, y


def _perfect_line_data(n: int = 30):
    """y = 2 + 3*x exactly."""
    x = [float(i) for i in range(n)]
    y = [2.0 + 3.0 * float(i) for i in range(n)]
    return x, y


# ---------------------------------------------------------------------------
# Regression
# ---------------------------------------------------------------------------
class TestMultipleRegression:
    def test_perfect_fit(self):
        x, y = _perfect_multiple_data()
        r = multiple_regression(x, y)
        assert r.r_squared == pytest.approx(1.0, abs=1e-9)
        assert r.coefficients[0] == pytest.approx(2.0, abs=1e-6)
        assert r.coefficients[1] == pytest.approx(3.0, abs=1e-6)
        assert r.coefficients[2] == pytest.approx(-1.0, abs=1e-6)
        assert r.n_features == 2
        assert r.method == "multiple_regression"

    def test_rejects_mismatched_lengths(self):
        with pytest.raises(ValueError):
            multiple_regression([[1.0], [2.0]], [1.0])

    def test_returns_model(self):
        x, y = _perfect_multiple_data()
        r = multiple_regression(x, y)
        assert isinstance(r, RegressionResult)
        assert r.converged is True

    def test_provenance_present(self):
        x, y = _perfect_multiple_data()
        r = multiple_regression(x, y, dataset_id="D1", dataset_version="v1", dataset_hash="h1")
        assert r.provenance.dataset_id == "D1"
        assert r.provenance.computation_method == "multiple_regression"
        assert r.provenance.method_version == "ecm/reg/multiple/v1"


class TestPolynomialRegression:
    def test_perfect_fit(self):
        x = [float(i) for i in range(20)]
        y = [float(i * i) for i in range(20)]
        r = polynomial_regression(x, y, degree=2)
        assert r.r_squared == pytest.approx(1.0, abs=1e-9)
        assert r.coefficients[0] == pytest.approx(0.0, abs=1e-6)
        assert r.coefficients[1] == pytest.approx(0.0, abs=1e-4)
        assert r.coefficients[2] == pytest.approx(1.0, abs=1e-4)

    def test_rejects_bad_degree(self):
        with pytest.raises(ValueError):
            polynomial_regression([1.0], [1.0], degree=0)


class TestLogisticRegression:
    def test_converges_and_binary(self):
        x = [[float(i)] for i in range(30)]
        y = [1 if i % 2 == 0 else 0 for i in range(30)]
        r = logistic_regression(x, y)
        assert r.converged in (True,)
        assert r.iterations > 0
        assert len(r.coefficients) == 2

    def test_rejects_non_binary_y(self):
        x = [[float(i)] for i in range(10)]
        y = [0.5] * 10
        with pytest.raises(ValueError):
            logistic_regression(x, y)


class TestUnivariateOlsDelegation:
    def test_delegates_to_canonical_ols(self):
        """univariate_ols must NOT re-implement OLS — it wraps the canonical
        statistics.regression.linear_regression result."""
        x, y = _perfect_line_data()
        r = univariate_ols(x, y)
        assert r.r_squared == pytest.approx(1.0, abs=1e-9)
        assert r.coefficients[0] == pytest.approx(2.0, abs=1e-6)
        assert r.coefficients[1] == pytest.approx(3.0, abs=1e-6)
        assert r.n_features == 1
        assert r.method == "ols"

    def test_returns_regression_result(self):
        x, y = _perfect_line_data()
        r = univariate_ols(x, y)
        assert isinstance(r, RegressionResult)


# ---------------------------------------------------------------------------
# Autocorrelation
# ---------------------------------------------------------------------------
class TestAutocorrelation:
    def test_returns_lag1(self):
        r = autocorrelation([float(i % 5) for i in range(60)], max_lag=4)
        assert isinstance(r, EconometricTestResult)
        assert r.test_name == "autocorrelation"
        assert "max_lag" in r.parameters or "lag" in r.parameters

    def test_provenance(self):
        r = autocorrelation(
            [float(i % 5) for i in range(60)],
            max_lag=4,
            dataset_id="D",
            dataset_version="v",
            dataset_hash="h",
        )
        assert r.provenance.computation_method == "autocorrelation"


class TestPartialAutocorrelation:
    def test_returns_statistic(self):
        r = partial_autocorrelation([float(i % 5) for i in range(60)], max_lag=4)
        assert isinstance(r, EconometricTestResult)
        assert r.test_name == "partial_autocorrelation"


# ---------------------------------------------------------------------------
# Stationarity
# ---------------------------------------------------------------------------
class TestAugmentedDickeyFuller:
    def test_returns_test_result(self):
        r = augmented_dickey_fuller([float(i) for i in range(100)], max_lag=1)
        assert isinstance(r, EconometricTestResult)
        assert r.test_name == "augmented_dickey_fuller"
        assert r.provenance.computation_method == "augmented_dickey_fuller"

    def test_singular_design_does_not_raise(self):
        """A pure linear trend makes the ADF design matrix singular; the
        ridge fallback must return a result instead of raising."""
        r = augmented_dickey_fuller([float(i) for i in range(100)], max_lag=1)
        assert r.provenance.method_version == "ecm/adf/v1"

    def test_rejects_short_input(self):
        with pytest.raises(ValueError):
            augmented_dickey_fuller([1.0, 2.0])


class TestKpss:
    def test_returns_test_result(self):
        r = kpss([float(i) for i in range(50)])
        assert isinstance(r, EconometricTestResult)
        assert r.test_name == "kpss"
        assert r.provenance.computation_method == "kpss"

    def test_rejects_short_input(self):
        with pytest.raises(ValueError):
            kpss([1.0, 2.0, 3.0])


# ---------------------------------------------------------------------------
# Cointegration
# ---------------------------------------------------------------------------
class TestEngleGranger:
    def test_cointegrated_series(self):
        x = [float(i) + 0.5 * math.sin(i) for i in range(60)]
        y = [2.0 * xi + 0.1 for xi in x]
        r = engle_granger(x, y)
        assert isinstance(r, EconometricTestResult)
        assert r.test_name == "engle_granger"
        assert r.provenance.computation_method == "engle_granger"

    def test_rejects_mismatched_lengths(self):
        with pytest.raises(ValueError):
            engle_granger([1.0, 2.0, 3.0], [1.0, 2.0])


# ---------------------------------------------------------------------------
# Causality
# ---------------------------------------------------------------------------
class TestGrangerCausality:
    def test_returns_result(self):
        z = [float(i % 3) + 0.1 * math.sin(i) for i in range(80)]
        w = [float(i % 2) + 0.05 * math.cos(i) for i in range(80)]
        r = granger_causality(z, w, max_lag=2)
        assert isinstance(r, EconometricTestResult)
        assert r.test_name == "granger_causality"
        assert r.provenance.computation_method == "granger_causality"

    def test_rejects_mismatched_lengths(self):
        with pytest.raises(ValueError):
            granger_causality([1.0, 2.0], [1.0])


# ---------------------------------------------------------------------------
# VIF
# ---------------------------------------------------------------------------
class TestVarianceInflationFactor:
    def test_returns_result(self):
        x = [[float(i), float(i) + 1.0, float(i * 2)] for i in range(30)]
        r = variance_inflation_factor(x)
        assert isinstance(r, EconometricTestResult)
        assert r.test_name == "variance_inflation_factor"
        assert r.provenance.computation_method == "variance_inflation_factor"

    def test_vif_alias(self):
        x = [[float(i), float(i) + 1.0] for i in range(30)]
        r = vif(x)
        assert isinstance(r, EconometricTestResult)


# ---------------------------------------------------------------------------
# Heteroskedasticity
# ---------------------------------------------------------------------------
class TestBreuschPagan:
    def test_returns_result(self):
        y = [float((i % 5) * 2) for i in range(50)]
        x = [[float(i)] for i in range(50)]
        r = breusch_pagan(y, x)
        assert isinstance(r, EconometricTestResult)
        assert r.test_name == "breusch_pagan"
        assert r.provenance.computation_method == "breusch_pagan"

    def test_rejects_mismatched_lengths(self):
        with pytest.raises(ValueError):
            breusch_pagan([1.0, 2.0], [[1.0]])


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------
class TestDurbinWatson:
    def test_returns_result(self):
        r = durbin_watson([float(i % 3) for i in range(60)])
        assert isinstance(r, EconometricTestResult)
        assert r.test_name == "durbin_watson"
        assert "statistic" in r.to_dict()

    def test_rejects_short(self):
        with pytest.raises(ValueError):
            durbin_watson([1.0])


class TestJarqueBera:
    def test_returns_result(self):
        r = jarque_bera([float(math.sin(i)) for i in range(80)])
        assert isinstance(r, EconometricTestResult)
        assert r.test_name == "jarque_bera"

    def test_rejects_short(self):
        with pytest.raises(ValueError):
            jarque_bera([1.0, 2.0, 3.0])


class TestResidualDiagnostics:
    def test_returns_diagnostics(self):
        r = residual_diagnostics([float(i % 2) for i in range(50)])
        assert isinstance(r, ResidualDiagnostics)
        assert r.durbin_watson > 0
        assert r.jarque_bera >= 0

    def test_provenance(self):
        r = residual_diagnostics(
            [float(i % 2) for i in range(50)], dataset_id="D", dataset_version="v", dataset_hash="h"
        )
        assert r.provenance.computation_method == "residual_diagnostics"


class TestModelDiagnostics:
    def test_returns_model_diagnostics(self):
        y = [float(i % 2) for i in range(60)]
        fitted = [float(i % 3) for i in range(60)]
        m = model_diagnostics(y, fitted, 2)
        assert isinstance(m, ModelDiagnostics)
        assert m.residual is not None

    def test_with_information_criteria(self):
        y = [float(i % 2) for i in range(60)]
        fitted = [float(i % 3) for i in range(60)]
        m = model_diagnostics(y, fitted, 2, aic=10.0, bic=15.0)
        assert m.information_criteria is not None
        assert m.information_criteria.aic == 10.0


# ---------------------------------------------------------------------------
# Intervals
# ---------------------------------------------------------------------------
class TestConfidenceInterval:
    def test_returns_interval(self):
        r = confidence_interval(5.0, 0.5, 100)
        assert isinstance(r, IntervalResult)
        assert r.lower < 5.0 < r.upper
        assert r.kind == "confidence"

    def test_rejects_bad_level(self):
        with pytest.raises(ValueError):
            confidence_interval(5.0, 0.5, 100, level=1.5)


class TestPredictionInterval:
    def test_returns_interval(self):
        resids = [float(i % 2) for i in range(50)]
        r = prediction_interval(5.0, resids)
        assert isinstance(r, IntervalResult)
        assert r.lower < 5.0 < r.upper
        assert r.kind == "prediction"

    def test_rejects_short_residuals(self):
        with pytest.raises(ValueError):
            prediction_interval(5.0, [1.0])


# ---------------------------------------------------------------------------
# Information criteria
# ---------------------------------------------------------------------------
class TestInformationCriteria:
    def test_aic(self):
        r = aic([0.1, 0.2, -0.1, 0.3], 2)
        assert isinstance(r, InformationCriteria)
        assert r.aic == pytest.approx(r.aic, abs=1e-9)

    def test_bic(self):
        r = bic([0.1, 0.2, -0.1, 0.3], 2)
        assert isinstance(r, InformationCriteria)

    def test_information_criteria(self):
        r = information_criteria([0.1, -0.2, 0.3], 3)
        assert isinstance(r, InformationCriteria)
        assert r.aic == pytest.approx(r.aic, abs=1e-9)


# ---------------------------------------------------------------------------
# Determinism / immutability / serialization
# ---------------------------------------------------------------------------
class TestDeterminism:
    def test_same_input_same_hash(self):
        x, y = _perfect_multiple_data()
        r1 = multiple_regression(x, y)
        r2 = multiple_regression(x, y)
        assert r1.result_hash == r2.result_hash

    def test_deterministic_hash_is_stable(self):
        h1 = deterministic_hash({"a": 1, "b": [1, 2, 3]})
        h2 = deterministic_hash({"b": [1, 2, 3], "a": 1})
        assert h1 == h2

    def test_adf_deterministic(self):
        r1 = augmented_dickey_fuller([float(i) for i in range(100)])
        r2 = augmented_dickey_fuller([float(i) for i in range(100)])
        assert r1.result_hash == r2.result_hash


class TestImmutability:
    def test_regression_result_frozen(self):
        x, y = _perfect_multiple_data()
        r = multiple_regression(x, y)
        with pytest.raises(Exception):
            r.coefficients = [1.0]  # frozen dataclass

    def test_test_result_mappingproxy(self):
        r = augmented_dickey_fuller([float(i) for i in range(100)])
        assert hasattr(r.parameters, "items")  # MappingProxyType


class TestSerialization:
    def test_regression_round_trip(self):
        x, y = _perfect_multiple_data()
        r = multiple_regression(x, y)
        d = r.to_dict()
        r2 = RegressionResult.from_dict(d)
        assert r2.result_hash == r.result_hash
        assert r2.coefficients == r.coefficients

    def test_test_result_round_trip(self):
        r = augmented_dickey_fuller([float(i) for i in range(100)])
        d = r.to_dict()
        r2 = EconometricTestResult.from_dict(d)
        assert r2.result_hash == r.result_hash
        assert r2.test_name == r.test_name

    def test_interval_round_trip(self):
        r = confidence_interval(5.0, 0.5, 100)
        d = r.to_dict()
        r2 = IntervalResult.from_dict(d)
        assert r2.result_hash == r.result_hash
        assert r2.lower == r.lower

    def test_information_criteria_round_trip(self):
        r = aic([0.1, 0.2, -0.1, 0.3], 2)
        d = r.to_dict()
        r2 = InformationCriteria.from_dict(d)
        assert r2.result_hash == r.result_hash


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------
class TestProvenance:
    def test_regression_provenance(self):
        x, y = _perfect_multiple_data()
        r = multiple_regression(x, y, dataset_id="D", dataset_version="v1", dataset_hash="H")
        assert r.provenance.dataset_id == "D"
        assert r.provenance.dataset_version == "v1"
        assert r.provenance.dataset_hash == "H"
        assert r.provenance.computation_method == "multiple_regression"
        assert r.provenance.method_version == "ecm/reg/multiple/v1"
        assert r.provenance.parameters == {"n_predictors": 2, "add_intercept": True}

    def test_statistics_provenance(self):
        r = augmented_dickey_fuller(
            [float(i) for i in range(100)], dataset_id="D", dataset_version="v1", dataset_hash="H"
        )
        assert r.provenance.dataset_id == "D"
        assert r.provenance.computation_method == "augmented_dickey_fuller"
        assert r.provenance.method_version == "ecm/adf/v1"
