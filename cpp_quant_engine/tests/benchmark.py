"""
Performance benchmark: Python backend vs C++ backend.

Compares execution time for 100,000 calculations across all operations.

Usage:
    python -m cpp_quant_engine.tests.benchmark

Requires:
    - C++ backend compiled and importable
    - pytest (for reliable timing)
"""

import time
import random
import sys
import math
from typing import List, Callable, Tuple


def generate_prices(n: int = 1000) -> List[float]:
    """Generate random price series for benchmarking."""
    random.seed(42)
    price = 100.0
    prices = [price]
    for _ in range(n - 1):
        price *= (1.0 + random.gauss(0.0, 0.01))
        prices.append(price)
    return prices


def generate_returns(n: int = 1000) -> List[float]:
    """Generate random return series for benchmarking."""
    random.seed(42)
    return [random.gauss(0.001, 0.02) for _ in range(n)]


def generate_equity_curve(returns: List[float], initial: float = 100000.0) -> List[float]:
    """Generate equity curve from returns."""
    equity = [initial]
    for r in returns:
        equity.append(equity[-1] * (1.0 + r))
    return equity


def benchmark_op(
    name: str,
    py_fn: Callable,
    cpp_fn: Callable,
    iterations: int = 10000,
) -> Tuple[float, float, float]:
    """
    Benchmark a single operation.

    Returns:
        (py_time, cpp_time, speedup)
    """
    # Warmup
    for _ in range(100):
        try:
            py_fn()
        except Exception:
            pass
        try:
            cpp_fn()
        except Exception:
            pass

    # Python timing
    py_start = time.perf_counter()
    for _ in range(iterations):
        py_fn()
    py_end = time.perf_counter()
    py_time = py_end - py_start

    # C++ timing
    cpp_start = time.perf_counter()
    for _ in range(iterations):
        cpp_fn()
    cpp_end = time.perf_counter()
    cpp_time = cpp_end - cpp_start

    speedup = py_time / cpp_time if cpp_time > 0 else float("inf")

    return py_time, cpp_time, speedup


def run_benchmarks():
    """Run all benchmarks and print results."""
    print("=" * 80)
    print("C++ Quant Acceleration Engine — Performance Benchmark")
    print("=" * 80)
    print()

    # Load backends
    print("Loading backends...")

    from researchos.quant_engine.backend import PythonQuantBackend
    py_backend = PythonQuantBackend()

    try:
        from cpp_quant_engine.backend_wrapper import CppQuantBackendWrapper
        cpp_backend = CppQuantBackendWrapper()
        if not cpp_backend.is_cpp:
            print("  WARNING: C++ backend not available — using Python fallback")
            print("  Benchmarks will show C++ = Python (no acceleration)")
            cpp_backend = py_backend
    except ImportError as e:
        print(f"  WARNING: C++ backend not available: {e}")
        print("  Benchmarks will show C++ = Python (no acceleration)")
        cpp_backend = py_backend

    print(f"  Python backend: {type(py_backend).__name__}")
    print(f"  C++ backend:    {type(cpp_backend).__name__}")
    print()

    # Generate test data
    print("Generating test data...")
    n_prices = 1000
    n_returns = 1000
    prices = generate_prices(n_prices)
    returns = generate_returns(n_returns)
    equity_curve = generate_equity_curve(returns)
    print(f"  Prices: {len(prices)}")
    print(f"  Returns: {len(returns)}")
    print(f"  Equity curve: {len(equity_curve)}")
    print()

    ITERATIONS = 10000

    # ── Benchmark 1: Returns ────────────────────────────────────────────────
    print(f"[1] Calculate Returns (percentage) — {ITERATIONS} iterations")
    py_time, cpp_time, speedup = benchmark_op(
        "returns",
        lambda: py_backend.calculate_returns(prices, "percentage"),
        lambda: cpp_backend.calculate_returns(prices, "percentage"),
        ITERATIONS,
    )
    print(f"    Python: {py_time:.4f}s  C++: {cpp_time:.4f}s  Speedup: {speedup:.2f}x")
    all_results = [("Returns (percentage)", py_time, cpp_time, speedup)]

    # ── Benchmark 2: Statistics ─────────────────────────────────────────────
    print(f"[2] Calculate Statistics — {ITERATIONS} iterations")
    py_time, cpp_time, speedup = benchmark_op(
        "statistics",
        lambda: py_backend.calculate_statistics(returns),
        lambda: cpp_backend.calculate_statistics(returns),
        ITERATIONS,
    )
    print(f"    Python: {py_time:.4f}s  C++: {cpp_time:.4f}s  Speedup: {speedup:.2f}x")
    all_results.append(("Statistics", py_time, cpp_time, speedup))

    # ── Benchmark 3: Volatility ─────────────────────────────────────────────
    print(f"[3] Calculate Volatility (std) — {ITERATIONS} iterations")
    py_time, cpp_time, speedup = benchmark_op(
        "volatility",
        lambda: py_backend.calculate_volatility(returns, "standard_deviation"),
        lambda: cpp_backend.calculate_volatility(returns, "standard_deviation"),
        ITERATIONS,
    )
    print(f"    Python: {py_time:.4f}s  C++: {cpp_time:.4f}s  Speedup: {speedup:.2f}x")
    all_results.append(("Volatility", py_time, cpp_time, speedup))

    # ── Benchmark 4: Drawdown ───────────────────────────────────────────────
    print(f"[4] Calculate Drawdown — {ITERATIONS} iterations")
    py_time, cpp_time, speedup = benchmark_op(
        "drawdown",
        lambda: py_backend.calculate_drawdown(equity_curve),
        lambda: cpp_backend.calculate_drawdown(equity_curve),
        ITERATIONS,
    )
    print(f"    Python: {py_time:.4f}s  C++: {cpp_time:.4f}s  Speedup: {speedup:.2f}x")
    all_results.append(("Drawdown", py_time, cpp_time, speedup))

    # ── Benchmark 5: Metrics ────────────────────────────────────────────────
    print(f"[5] Calculate Metrics — {ITERATIONS} iterations")
    py_time, cpp_time, speedup = benchmark_op(
        "metrics",
        lambda: py_backend.calculate_metrics(returns, equity_curve, 0.0),
        lambda: cpp_backend.calculate_metrics(returns, equity_curve, 0.0),
        ITERATIONS,
    )
    print(f"    Python: {py_time:.4f}s  C++: {cpp_time:.4f}s  Speedup: {speedup:.2f}x")
    all_results.append(("Metrics", py_time, cpp_time, speedup))

    # ── Benchmark 6: Performance Analytics ──────────────────────────────────
    print(f"[6] Calculate Performance Analytics — {ITERATIONS} iterations")
    py_time, cpp_time, speedup = benchmark_op(
        "performance",
        lambda: py_backend.calculate_performance_analytics(returns),
        lambda: cpp_backend.calculate_performance_analytics(returns),
        ITERATIONS,
    )
    print(f"    Python: {py_time:.4f}s  C++: {cpp_time:.4f}s  Speedup: {speedup:.2f}x")
    all_results.append(("Performance Analytics", py_time, cpp_time, speedup))

    # ── Benchmark 7: Full Simulation ────────────────────────────────────────
    print(f"[7] Run Simulation — {ITERATIONS // 10} iterations")
    from researchos.quant_engine.models import SimulationRequest

    request = SimulationRequest(
        dataset_reference="BENCHMARK",
        parameters={"initial_capital": 100000.0, "risk_free_rate": 0.0},
        seed=42,
    )

    py_time, cpp_time, speedup = benchmark_op(
        "simulation",
        lambda: py_backend.run_simulation(request, prices),
        lambda: cpp_backend.run_simulation(request, prices),
        ITERATIONS // 10,
    )
    print(f"    Python: {py_time:.4f}s  C++: {cpp_time:.4f}s  Speedup: {speedup:.2f}x")
    all_results.append(("Simulation", py_time, cpp_time, speedup))

    # ── Summary ─────────────────────────────────────────────────────────────
    print()
    print("=" * 80)
    print("BENCHMARK SUMMARY")
    print("=" * 80)
    print(f"{'Operation':<30} {'Python (s)':<12} {'C++ (s)':<12} {'Speedup':<10}")
    print("-" * 64)
    for name, py_t, cpp_t, sp in all_results:
        print(f"{name:<30} {py_t:<12.4f} {cpp_t:<12.4f} {sp:<10.2f}x")

    # Overall
    total_py = sum(r[1] for r in all_results)
    total_cpp = sum(r[2] for r in all_results)
    total_speedup = total_py / total_cpp if total_cpp > 0 else float("inf")
    print("-" * 64)
    print(f"{'TOTAL':<30} {total_py:<12.4f} {total_cpp:<12.4f} {total_speedup:<10.2f}x")


if __name__ == "__main__":
    run_benchmarks()
