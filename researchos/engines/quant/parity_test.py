"""
Parity test: proves C++ and Python backtest engines produce identical results.

This test is MANDATORY. It will FAIL (not skip) if the C++ engine is not
available, because a silent fallback to Python violates the determinism
principle of ResearchOS.

For floating-point comparison we use bit-exact equality via struct.pack.
If the C++ engine ever produces a different bit pattern for the same input,
this test will catch it.
"""

import math
import struct

import pytest

# ---------------------------------------------------------------------------
# Python reference implementation of run_ml_backtest_cpp
# This is a line-by-line translation of cpp_quant/src/backtest.cpp
# ---------------------------------------------------------------------------


def _python_run_ml_backtest(
    prices: list[float],
    probabilities: list[float],
    threshold: float,
    initial_capital: float = 100000.0,
    commission: float = 0.001,
    slippage: float = 0.0005,
) -> tuple[float, float, float, float, int]:
    """
    Pure-Python reference implementation of the C++ run_ml_backtest_cpp.

    Line-by-line translation of cpp_quant/src/backtest.cpp :: run_ml_backtest_cpp()
    """
    capital = initial_capital
    position = 0.0
    entry_price = 0.0
    trades = 0
    wins = 0
    equity_curve: list[float] = [initial_capital]

    n = min(len(prices), len(probabilities))

    for i in range(n):
        price = prices[i]
        prob = probabilities[i]

        if prob > threshold and position == 0.0:
            cost_per_unit = price * (1.0 + commission + slippage)
            size = capital / cost_per_unit
            if size > 0.0:
                capital -= size * cost_per_unit
                position = size
                entry_price = price
        elif prob < (1.0 - threshold) and position > 0.0:
            revenue_per_unit = price * (1.0 - commission - slippage)
            revenue = position * revenue_per_unit
            pnl = revenue - position * entry_price
            capital += revenue
            if pnl > 0:
                wins += 1
            trades += 1
            position = 0.0
            entry_price = 0.0

        equity = capital + position * price
        equity_curve.append(equity)

    if position > 0.0 and prices:
        closing_price = prices[-1]
        revenue_per_unit = closing_price * (1.0 - commission - slippage)
        revenue = position * revenue_per_unit
        pnl = revenue - position * entry_price
        capital += revenue
        if pnl > 0:
            wins += 1
        trades += 1

    total_return = (capital - initial_capital) / initial_capital

    sharpe = 0.0
    if len(equity_curve) > 1:
        returns: list[float] = []
        for i in range(1, len(equity_curve)):
            ret = (equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1]
            returns.append(ret)

        mean = sum(returns) / len(returns)
        stddev = math.sqrt(sum((r - mean) ** 2 for r in returns) / len(returns))

        if stddev > 1e-8:
            sharpe = (mean / stddev) * math.sqrt(252.0)

    max_drawdown = 0.0
    peak = equity_curve[0]
    for e in equity_curve:
        if e > peak:
            peak = e
        dd = (peak - e) / peak
        if dd > max_drawdown:
            max_drawdown = dd
    max_drawdown = -max_drawdown

    win_rate = (wins / trades) if trades > 0 else 0.0

    return (total_return, sharpe, max_drawdown, win_rate, trades)


# ---------------------------------------------------------------------------
# Bit-exact float comparison helper
# ---------------------------------------------------------------------------


def _float_to_hex(value: float) -> str:
    """Return the IEEE-754 bit representation of a float as a hex string."""
    return struct.pack(">d", value).hex()


def _assert_floats_bit_exact(name: str, python_val: float, cpp_val: float) -> None:
    """
    Assert two floats are bit-exactly equal.

    Uses struct.pack to compare the raw IEEE-754 representation.
    This catches differences in:
        - Calculation order (e.g. Kahan summation vs naive)
        - FMA (fused multiply-add) vs separate multiply+add
        - Extended precision (x87 80-bit) vs SSE2 64-bit
        - Compiler optimization reordering
    """
    py_bytes = struct.pack(">d", python_val)
    cpp_bytes = struct.pack(">d", cpp_val)

    if py_bytes != cpp_bytes:
        pytest.fail(
            f"BIT EXACT MISMATCH in {name}: "
            f"Python={python_val!r} (hex={_float_to_hex(python_val)}) vs "
            f"C++={cpp_val!r} (hex={_float_to_hex(cpp_val)})"
        )


# ---------------------------------------------------------------------------
# C++ engine import gate
# ---------------------------------------------------------------------------


def _require_cpp_engine():
    """
    Import the C++ engine function directly from the compiled .pyd module.

    This function will FAIL the test (not skip) if the C++ engine is not
    available. A silent fallback to Python is a determinism violation and
    must not be tolerated.
    """
    # The compiled module lives at researchos/engines/quant/cpp_quant.pyd
    # It exports run_ml_backtest_cpp directly.
    try:
        from researchos.engines.quant.cpp_quant import run_ml_backtest_cpp  # noqa: F401
    except (ImportError, ModuleNotFoundError, OSError) as exc:
        pytest.fail(
            "C++ engine not available — this is a CRITICAL failure. "
            "Build the C++ engine before deploying.\n"
            f"Import error: {exc}"
        )

    # Verify the module is actually the C++ engine, not a Python stub
    from researchos.engines.quant import cpp_quant

    if not hasattr(cpp_quant, "run_ml_backtest_cpp"):
        pytest.fail(
            "C++ engine module loaded but missing run_ml_backtest_cpp. This is a CRITICAL determinism violation."
        )

    return cpp_quant.run_ml_backtest_cpp


# ---------------------------------------------------------------------------
# Test cases — KNOWN inputs and KNOWN expected outputs
# These values were produced by running the C++ engine and recording the
# exact outputs. They are the source of truth.
# ---------------------------------------------------------------------------

TEST_CASES = [
    pytest.param(
        [100.0, 101.0, 102.0, 103.0, 104.0, 105.0],
        [0.6, 0.7, 0.8, 0.9, 0.95, 0.96],
        0.55,
        (0.04685471792311568, 29.839466673666227, -0.0014977533699448394, 1.0, 1),
        id="upward_trend_high_confidence",
    ),
    pytest.param(
        [105.0, 104.0, 103.0, 102.0, 101.0, 100.0],
        [0.4, 0.3, 0.2, 0.1, 0.05, 0.04],
        0.55,
        (0.0, 0.0, -0.0, 0.0, 0),
        id="downward_trend_low_confidence",
    ),
    pytest.param(
        [100.0, 100.0, 100.0, 100.0, 100.0, 100.0],
        [0.5, 0.5, 0.5, 0.5, 0.5, 0.5],
        0.55,
        (0.0, 0.0, -0.0, 0.0, 0),
        id="flat_market_equal_prob",
    ),
    pytest.param(
        [100.0, 105.0, 102.0, 108.0, 104.0, 110.0],
        [0.8, 0.85, 0.9, 0.92, 0.94, 0.96],
        0.55,
        (0.09670494258612118, 6.497328767652983, -0.03703703703703714, 1.0, 1),
        id="volatile_uptrend_high_confidence",
    ),
    pytest.param(
        [100.0],
        [0.6],
        0.55,
        (-0.0029955067398898245, 0.0, -0.0014977533699448394, 0.0, 1),
        id="single_bar_edge_case",
    ),
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_cpp_engine_is_available():
    """The C++ engine must be importable and functional."""
    _require_cpp_engine()


@pytest.mark.parametrize("prices,probs,threshold,expected", TEST_CASES)
def test_ml_backtest_parity(prices, probs, threshold, expected):
    """
    Python and C++ backtest engines must produce BIT-EXACT identical results.

    This is not a tolerance test. Every bit of every float must match.
    """
    cpp_run = _require_cpp_engine()

    expected_total_return, expected_sharpe, expected_max_dd, expected_wr, expected_trades = expected

    # Run C++ engine
    cpp_result = cpp_run(prices, probs, threshold)
    cpp_total_return, cpp_sharpe, cpp_max_dd, cpp_wr, cpp_trades = cpp_result

    # Run Python reference
    py_result = _python_run_ml_backtest(prices, probs, threshold)
    py_total_return, py_sharpe, py_max_dd, py_wr, py_trades = py_result

    # Assert Python produces the expected values (sanity check)
    _assert_floats_bit_exact("python.total_return", py_total_return, expected_total_return)
    _assert_floats_bit_exact("python.sharpe", py_sharpe, expected_sharpe)
    _assert_floats_bit_exact("python.max_drawdown", py_max_dd, expected_max_dd)
    _assert_floats_bit_exact("python.win_rate", py_wr, expected_wr)
    assert py_trades == expected_trades, f"Python trades mismatch: {py_trades} != {expected_trades}"

    # Assert C++ matches Python bit-exactly
    _assert_floats_bit_exact("cpp.total_return", py_total_return, cpp_total_return)
    _assert_floats_bit_exact("cpp.sharpe", py_sharpe, cpp_sharpe)
    _assert_floats_bit_exact("cpp.max_drawdown", py_max_dd, cpp_max_dd)
    _assert_floats_bit_exact("cpp.win_rate", py_wr, cpp_wr)
    assert cpp_trades == expected_trades, f"C++ trades mismatch: {cpp_trades} != {expected_trades}"


def test_cpp_engine_does_not_silently_fallback():
    """
    If the C++ engine module is missing, the test must FAIL (not skip).

    A silent fallback to Python is a determinism violation and must not
    be tolerated.
    """
    _require_cpp_engine()


def test_float_comparison_method():
    """
    Verify that our bit-exact comparison works by testing known distinct values.

    This is a meta-test: it proves that the comparison method can actually
    detect differences when they exist.
    """
    # These are definitely different bit patterns
    from _pytest.outcomes import Failed

    with pytest.raises(Failed):
        _assert_floats_bit_exact("distinct_values", 0.1, 0.125)

    # These should be bit-exact
    _assert_floats_bit_exact("same_value", 0.1, 0.1)
