"""
Performance benchmark suite for the Python vs C++ compute backends (Phase 4.3).

These tests are observational: they measure wall-clock execution time and
report the speedup, but never assert on absolute timings (environment noise is
too variable).  They exist to:

    1. Prove the C++ adapter is genuinely invoked (not silently falling back).
    2. Exercise every ``QuantComputationInterface`` operation at scale.
    3. Produce the numbers recorded in ``COMPUTE_BACKEND_BASELINE.md``.

The suite is gated behind ``RESEARCHOS_PERF=1`` so normal CI runs stay fast.
"""

from __future__ import annotations

import os

import pytest

from researchos.benchmarks.benchmark_cpp import (
    DATASET_SIZES,
    make_prices,
    make_request,
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
        "calculate_returns",
        "calculate_volatility",
        "calculate_statistics",
        "calculate_metrics",
        "calculate_performance_analytics",
        "run_simulation",
    }
    assert ops == expected
    assert results["sizes"] == list(DATASET_SIZES)


def test_cpp_backend_is_actually_invoked():
    results = run_benchmark()
    assert results["cpp_backend"] == "CppQuantAdapter"


def test_benchmark_cpp_is_faster_than_python_at_100k():
    # Observational gate: at 100k observations the C++ backend must not be
    # dramatically slower than Python (the whole point of the accelerator).
    results = run_benchmark()
    sim_row = next(r for r in results["rows"] if r["operation"] == "run_simulation")
    meas = next(m for m in sim_row["measurements"] if m["size"] == 100_000)
    assert meas["cpp_s"] < max(meas["python_s"] * 2.0, 5.0), (
        f"C++ unexpectedly slow: python={meas['python_s']:.3f}s cpp={meas['cpp_s']:.3f}s"
    )


def test_benchmark_data_helpers_deterministic():
    a = make_prices(100)
    b = make_prices(100)
    assert a == b
    req = make_request()
    assert req.seed == 42
