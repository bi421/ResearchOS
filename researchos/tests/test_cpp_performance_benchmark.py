"""
Phase 4.5 — benchmark suite for the Regression & Rolling C++ integration.

These tests are observational: they measure wall-clock execution time and
report the speedup, but never assert on absolute timings (environment noise is
too variable).  They exist to:

    1. Prove the C++ adapter is genuinely invoked (not silently falling back).
    2. Exercise every newly-integrated operation at scale.
    3. Produce the numbers recorded in the Phase 4.5 evidence report.

Gated behind ``RESEARCHOS_PERF=1`` so normal CI runs stay fast.
"""

from __future__ import annotations

import os

import pytest

from researchos.benchmarks.benchmark_cpp_performance_integration import (
    DATASET_SIZES,
    make_series,
    run_benchmark,
)
from researchos.quant_engine.cpp_backend import has_cpp_engine

_RUN_PERF = os.environ.get("RESEARCHOS_PERF") == "1"

pytestmark = [
    pytest.mark.skipif(not _RUN_PERF, reason="set RESEARCHOS_PERF=1 to run perf suite"),
    pytest.mark.skipif(
        not has_cpp_engine(), reason="compiled C++ quant engine not available"
    ),
]


def test_benchmark_reports_all_operations():
    results = run_benchmark()
    ops = {row["operation"] for row in results["rows"]}
    expected = {
        "regression_slope",
        "regression_intercept",
        "regression_correlation",
        "regression_r_squared",
        "regression_standard_error",
        "rolling_mean",
        "rolling_volatility",
    }
    assert ops == expected
    assert results["sizes"] == list(DATASET_SIZES)


def test_cpp_backend_is_actually_invoked():
    results = run_benchmark()
    assert results["cpp_backend"] == "CppQuantAdapter"


def test_benchmark_data_helpers_deterministic():
    a = make_series(100)
    b = make_series(100)
    assert a == b

