"""Benchmark the callback-free C++ hot path against an equivalent Python loop.

Usage from cpp_quant_engine/:
    python benchmarks/bench_fast_numeric.py --rows 1000000 --repeat 5

This benchmark measures compute + Python/C++ vector marshalling for the C++ path.
It deliberately does not claim a speedup until the benchmark is actually run on the
same machine and build configuration.
"""

from __future__ import annotations

import argparse
import random
import statistics
import time

from cpp_quant_engine import cpp_quant_fast_backend as fast


def make_data(n: int):
    rng = random.Random(42)
    close = [2000.0]
    for _ in range(n - 1):
        close.append(close[-1] * (1.0 + rng.uniform(-0.0005, 0.0005)))
    open_ = close[:]
    signal = [0] * n
    quantity = [1.0] * n
    for i in range(0, n, 37):
        signal[i] = 1 if (i // 37) % 2 == 0 else -1
    return open_, close, signal, quantity


def python_backtest(open_, close, signal, quantity):
    cash = 100000.0
    position = 0.0
    entry = 0.0
    trades = 0
    for i in range(1, len(open_)):
        s = signal[i - 1]
        q = quantity[i - 1]
        if s > 0 and position <= 0.0:
            if position < 0.0:
                cash -= (entry - open_[i]) * (-position)
                trades += 1
                position = 0.0
            if cash >= q * open_[i]:
                cash -= q * open_[i]
                position = q
                entry = open_[i]
        elif s < 0 and position >= 0.0:
            if position > 0.0:
                cash += position * open_[i]
                trades += 1
                position = 0.0
            position = -q
            cash += q * open_[i]
            entry = open_[i]
    if position > 0:
        cash += position * close[-1]
        trades += 1
    elif position < 0:
        cash -= (-position) * close[-1]
        trades += 1
    return cash, trades


def timed(fn, repeat):
    samples = []
    result = None
    for _ in range(repeat):
        t0 = time.perf_counter()
        result = fn()
        samples.append(time.perf_counter() - t0)
    return result, statistics.median(samples), samples


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=1_000_000)
    ap.add_argument("--repeat", type=int, default=5)
    args = ap.parse_args()

    open_, close, signal, quantity = make_data(args.rows)

    py_result, py_sec, _ = timed(
        lambda: python_backtest(open_, close, signal, quantity), args.repeat
    )
    cpp_result, cpp_sec, _ = timed(
        lambda: fast.backtest_next_open(
            open_, close, signal, quantity, 100000.0, 0.0, 0.0, True
        ),
        args.repeat,
    )

    speedup = py_sec / cpp_sec if cpp_sec else float("inf")
    print("C++ FAST NUMERIC BENCHMARK")
    print(f"rows              : {args.rows:,}")
    print(f"repeat            : {args.repeat}")
    print(f"python median sec : {py_sec:.6f}")
    print(f"c++ median sec    : {cpp_sec:.6f}")
    print(f"speedup           : {speedup:.2f}x")
    print(f"python final      : {py_result[0]:.6f}")
    print(f"c++ final         : {cpp_result.final_equity:.6f}")
    print(f"python trades     : {py_result[1]}")
    print(f"c++ trades        : {cpp_result.trades}")
    print("result match      :", abs(py_result[0] - cpp_result.final_equity) < 1e-9 and py_result[1] == cpp_result.trades)


if __name__ == "__main__":
    main()
