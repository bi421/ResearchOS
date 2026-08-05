"""
Phase 4.5 — C++ performance integration equivalence tests.

Proves Python ↔ C++ numerical equivalence for the Regression and RollingWindow
statistics modules that Phase 4.4 shipped in C++ (520/520 tests passing) and
Phase 4.5 connects through ``cpp_quant_backend``.

Architecture rules (unchanged):
    - Deterministic: all operations are pure functions of their inputs.
    - No trading logic, no broker integration, no ML, no signal-generation
      changes.  Regression/rolling are pure numerical research analytics.
    - The frozen ``QuantComputationInterface`` is NOT modified; the C++
      delegates are extra adapter surface on ``CppQuantAdapter``.

Gated exactly like the Phase 4.1/4.3 parity suites: skipped when the compiled
C++ engine is unavailable.
"""

from __future__ import annotations

import math
from typing import List

import pytest

from researchos.quant_engine.cpp_backend import CppQuantAdapter, has_cpp_engine
from researchos.quant_engine.models import CalculationVersion
from researchos.quant_engine.numerical_validation import NumericalComparator
from researchos.quant_engine.statistics import (
    regression_correlation,
    regression_intercept,
    regression_r_squared,
    regression_slope,
    regression_standard_error,
    rolling_mean,
    rolling_volatility_incremental,
)

pytestmark = pytest.mark.skipif(
    not has_cpp_engine(), reason="compiled C++ quant engine not available"
)

_V1 = CalculationVersion.CALCULATION_V1


def make_series(n: int, base: float = 100.0) -> List[float]:
    """Deterministic series (no randomness)."""
    return [base + 30.0 * math.sin(i / 5.0) + 0.5 * (i % 7) for i in range(n)]


@pytest.fixture(scope="module")
def cpp() -> CppQuantAdapter:
    return CppQuantAdapter()


class TestRegressionSlopeIntercept:
    def test_slope_matches_reference(self, cpp):
        y = make_series(128)
        expected = regression_slope(y)
        actual = cpp.regression_slope(y)
        assert actual == pytest.approx(expected, rel=1e-12, abs=1e-12)

    def test_intercept_matches_reference(self, cpp):
        y = make_series(128)
        expected = regression_intercept(y)
        actual = cpp.regression_intercept(y)
        assert actual == pytest.approx(expected, rel=1e-12, abs=1e-12)

    def test_trend_exact_for_linear(self, cpp):
        # A perfect linear series: slope must be exact, intercept exact.
        y = [3.0 * i + 7.0 for i in range(64)]
        assert cpp.regression_slope(y) == pytest.approx(3.0, rel=1e-12)
        assert cpp.regression_intercept(y) == pytest.approx(7.0, rel=1e-12)

    def test_slope_deterministic(self, cpp):
        y = make_series(64)
        assert cpp.regression_slope(y) == cpp.regression_slope(y)

    def test_short_series_raises(self, cpp):
        with pytest.raises(ValueError):
            cpp.regression_slope([1.0])
        with pytest.raises(ValueError):
            cpp.regression_intercept([1.0])


class TestRegressionPairwise:
    def test_correlation_matches_reference(self, cpp):
        x = make_series(128)
        y = [v * 2.0 + 1.0 + 0.05 * (i % 3) for i, v in enumerate(x)]
        expected = regression_correlation(x, y)
        actual = cpp.regression_correlation(x, y)
        assert actual == pytest.approx(expected, rel=1e-12, abs=1e-12)

    def test_r_squared_matches_reference(self, cpp):
        x = make_series(128)
        y = [v * 2.0 + 1.0 + 0.05 * (i % 3) for i, v in enumerate(x)]
        expected = regression_r_squared(x, y)
        actual = cpp.regression_r_squared(x, y)
        assert actual == pytest.approx(expected, rel=1e-12, abs=1e-12)

    def test_standard_error_matches_reference(self, cpp):
        x = make_series(128)
        y = [v * 2.0 + 1.0 + 0.05 * (i % 3) for i, v in enumerate(x)]
        expected = regression_standard_error(x, y)
        actual = cpp.regression_standard_error(x, y)
        assert actual == pytest.approx(expected, rel=1e-12, abs=1e-12)

    def test_perfect_correlation(self, cpp):
        x = make_series(64)
        y = [3.0 * v - 2.0 for v in x]
        assert cpp.regression_correlation(x, y) == pytest.approx(1.0, rel=1e-12)
        assert cpp.regression_r_squared(x, y) == pytest.approx(1.0, rel=1e-12)
        assert cpp.regression_standard_error(x, y) == pytest.approx(0.0, abs=1e-12)

    def test_validation_mismatch_raises(self, cpp):
        x = make_series(32)
        y = make_series(33)
        with pytest.raises(ValueError):
            cpp.regression_correlation(x, y)
        with pytest.raises(ValueError):
            cpp.regression_r_squared(x, y)
        with pytest.raises(ValueError):
            cpp.regression_standard_error(x, y)

    def test_zero_variance_raises(self, cpp):
        # Constant y -> Sxx/Syy = 0 -> C++ DivisionByZero -> adapter ValueError.
        x = [1.0, 2.0, 3.0, 4.0]
        y = [5.0, 5.0, 5.0, 5.0]
        with pytest.raises(ValueError):
            cpp.regression_correlation(x, y)
        with pytest.raises(ValueError):
            cpp.regression_r_squared(x, y)


class TestRollingMean:
    def test_matches_reference(self, cpp):
        data = make_series(256)
        for window in (5, 21, 60):
            expected = rolling_mean(data, window)
            actual = cpp.rolling_mean(data, window)
            assert len(actual) == len(data) - window + 1
            assert actual == pytest.approx(expected, rel=1e-12, abs=1e-12)

    def test_small_window_exact(self, cpp):
        data = [10.0, 20.0, 30.0, 40.0, 50.0]
        assert cpp.rolling_mean(data, 2) == pytest.approx([15.0, 25.0, 35.0, 45.0])
        assert cpp.rolling_mean(data, 3) == pytest.approx([20.0, 30.0, 40.0])

    def test_window_larger_than_data_raises(self, cpp):
        with pytest.raises(ValueError):
            cpp.rolling_mean([1.0, 2.0], 3)

    def test_zero_window_raises(self, cpp):
        with pytest.raises(ValueError):
            cpp.rolling_mean(make_series(16), 0)


class TestRollingVolatility:
    def test_matches_reference_ddof1(self, cpp):
        data = make_series(256)
        window = 21
        expected = rolling_volatility_incremental(data, window, ddof=1)
        actual = cpp.rolling_volatility_series(data, window, ddof=1)
        assert len(actual) == len(data) - window + 1
        assert actual == pytest.approx(expected, rel=1e-9, abs=1e-12)

    def test_matches_reference_ddof0(self, cpp):
        data = make_series(256)
        window = 21
        expected = rolling_volatility_incremental(data, window, ddof=0)
        actual = cpp.rolling_volatility_series(data, window, ddof=0)
        assert len(actual) == len(data) - window + 1
        assert actual == pytest.approx(expected, rel=1e-9, abs=1e-12)

    def test_constant_series_zero_volatility(self, cpp):
        data = [5.0] * 30
        assert list(cpp.rolling_volatility_series(data, 10)) == [0.0] * 21

    def test_invalid_ddof_raises(self, cpp):
        data = make_series(64)
        with pytest.raises(ValueError):
            cpp.rolling_volatility_series(data, 21, ddof=21)
        with pytest.raises(ValueError):
            cpp.rolling_volatility_series(data, 21, ddof=-1)


class TestComparatorCertification:
    """Route the new operations through the certification comparator."""

    def test_regression_slope_passes_numerical_comparator(self, cpp):
        y = make_series(256)
        comparator = NumericalComparator()
        result = comparator.compare(regression_slope(y), cpp.regression_slope(y))
        assert result.passed
        assert result.max_abs_error <= 1e-12

    def test_rolling_mean_passes_numerical_comparator(self, cpp):
        data = make_series(512)
        comparator = NumericalComparator()
        result = comparator.compare(
            rolling_mean(data, 21), cpp.rolling_mean(data, 21)
        )
        assert result.passed

    def test_rolling_volatility_passes_numerical_comparator(self, cpp):
        data = make_series(512)
        comparator = NumericalComparator()
        result = comparator.compare(
            rolling_volatility_incremental(data, 21, ddof=1),
            cpp.rolling_volatility_series(data, 21, ddof=1),
        )
        assert result.passed


class TestArchitectureBoundary:
    """Verify Phase 4.5 does not alter the frozen interface/architecture."""

    def test_quant_interface_unchanged(self):
        from researchos.quant_engine.interface import QuantComputationInterface

        methods = [m for m in dir(QuantComputationInterface) if not m.startswith("_")]
        # The frozen interface still only exposes the six certified operations.
        assert "regression_slope" not in methods
        assert "rolling_mean" not in methods

    def test_adapter_is_cpp(self, cpp):
        assert cpp.is_cpp is True

    def test_no_signal_or_trading_surface(self, cpp):
        # The adapter exposes no trading/broker/signal surface.
        for banned in ("place_order", "execute_trade", "generate_signal", "broker",
                       "connect_broker", "train", "fit", "predict"):
            assert not hasattr(cpp, banned), f"unexpected trading/ML surface {banned}"

