"""Benchmark the callback-free C++ numeric path against Python.

Usage from cpp_quant_engine/:
    python benchmarks/bench_fast_numeric.py --rows 1000000 --repeat 5

The benchmark measures compute plus Python/C++ vector marshalling. A speedup is
reported only from an actual local run; this file never hard-codes a performance claim.
"""

from __future__ import annotations

import argparse
import random
import statistics
import time

from cpp_quant_engine import cpp_quant_fast_backend as fast


def make_close(n: int):
    rng = random.Random(42)
    close = [2000.0]
    for _ in range(n - 1):
        close.append(close[-1] * (1.0 + rng.uniform(-0.0005, 0.0005)))
    return close


def python_returns(close):
    return [close[i] / close[i - 1] - 1.0 for i in range(1, len(close))]


def timed(fn, repeat):
    samples = []
    result = None
    for _ in range(repeat):
        t0 = time.perf_counter()
        result = fn()
        samples.append(time.perf_counter() - t0)
    return result, statistics.median(samples)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=1_000_000)
    ap.add_argument("--repeat", type=int, default=5)
    args = ap.parse_args()

    close = make_close(args.rows)
    py_result, py_sec = timed(lambda: python_returns(close), args.repeat)
    cpp_result, cpp_sec = timed(lambda: fast.simple_returns(close), args.repeat)

    max_abs_error = max(
        (abs(a - b) for a, b in zip(py_result, cpp_result)), default=0.0
    )
    speedup = py_sec / cpp_sec if cpp_sec else float("inf")

    print("C++ FAST NUMERIC BENCHMARK")
    print(f"rows              : {args.rows:,}")
    print(f"repeat            : {args.repeat}")
    print(f"python median sec : {py_sec:.6f}")
    print(f"c++ median sec    : {cpp_sec:.6f}")
    print(f"speedup           : {speedup:.2f}x")
    print(f"max abs error     : {max_abs_error:.3e}")
    print("numerical match   :", max_abs_error < 1e-15)

    # Also exercise the callback-free backtest kernel so its native path is covered
    # by the same benchmark environment. Its result is printed, not compared to a
    # separate implementation with different accounting semantics.
    signal = [0] * args.rows
    quantity = [1.0] * args.rows
    for i in range(0, args.rows, 37):
        signal[i] = 1 if (i // 37) % 2 == 0 else -1
    backtest, bt_sec = timed(
        lambda: fast.backtest_next_open(
            close, close, signal, quantity, 100000.0, 0.0, 0.0, True
        ),
        args.repeat,
    )
    print(f"backtest median sec: {bt_sec:.6f}")
    print(f"backtest equity    : {backtest.final_equity:.6f}")
    print(f"backtest trades    : {backtest.trades}")


if __name__ == "__main__":
    main()
