"""
Benchmark scaffolding for the Certified Analytical Compute Surface (Phase 5.1).

Phase 5.1 — Certified Analytical Compute Surface (WP-1).
This is scaffolding ONLY: it measures wall-clock timings of the research
analytical backend and the C++ candidate (when available).  It is gated behind
``RESEARCHOS_PERF=1`` and makes NO performance assertions — it is observational
and must never affect scheduling or validation.

Run:
    RESEARCHOS_PERF=1 python -m researchos.benchmarks.benchmark_research_engine

The Python reference backend remains the scientific source of truth.  Timing
is observational and never part of any result hash.
"""

from __future__ import annotations

import os
import time
from typing import Any, Callable, Dict, List

from researchos.quant_engine.research_cpp_backend import ResearchCppBackend
from researchos.quant_engine.research_engine import PythonResearchBackend
from researchos.quant_engine.technical.contracts import Bars, IndicatorSpec


def _bars(length: int = 500) -> Bars:
    open_prices = [100.0 + (i * 0.5) for i in range(length)]
    high_prices = [o + 1.5 for o in open_prices]
    low_prices = [o - 1.0 for o in open_prices]
    close_prices = [o + 0.5 for o in open_prices]
    volumes = [1000.0 + i * 10.0 for i in range(length)]
    return Bars(
        open=open_prices,
        high=high_prices,
        low=low_prices,
        close=close_prices,
        volume=volumes,
    )


def _returns(length: int = 500) -> list:
    return [0.001 if i % 2 == 0 else -0.0008 for i in range(length)]


def _timeit(fn: Callable[[], Any], repeats: int = 1) -> float:
    start = time.perf_counter()
    for _ in range(repeats):
        fn()
    return (time.perf_counter() - start) * 1000.0


def _benchmark_op(name: str, python_fn: Callable[[], Any], cpp_fn: Callable[[], Any]) -> Dict[str, Any]:
    py_ms = _timeit(python_fn)
    cpp_ms = _timeit(cpp_fn)
    return {"operation": name, "python_ms": py_ms, "cpp_ms": cpp_ms}


def main() -> None:
    if os.environ.get("RESEARCHOS_PERF") != "1":
        print("Benchmark gated behind RESEARCHOS_PERF=1; skipping.")
        return

    python = PythonResearchBackend()
    cpp = ResearchCppBackend()
    print(f"C++ research engine available: {cpp.is_cpp}")

    bars = _bars(500)
    returns = _returns(500)
    specs = [IndicatorSpec(name="SMA", params={"period": 20})]

    rows: List[Dict[str, float]] = []

    rows.append(
        _benchmark_op(
            "research_technical",
            lambda: python.research_technical(bars, specs),
            lambda: cpp.research_technical(bars, specs),
        )
    )
    rows.append(
        _benchmark_op(
            "research_probabilistic_fit",
            lambda: python.research_probabilistic_fit(returns, "normal"),
            lambda: cpp.research_probabilistic_fit(returns, "normal"),
        )
    )
    rows.append(
        _benchmark_op(
            "research_historical",
            lambda: python.research_historical(returns, "features"),
            lambda: cpp.research_historical(returns, "features"),
        )
    )
    rows.append(
        _benchmark_op(
            "research_econometric_analysis",
            lambda: python.research_econometric_analysis(returns[:120], "arima"),
            lambda: cpp.research_econometric_analysis(returns[:120], "arima"),
        )
    )

    print(f"{'operation':<35}{'python_ms':>12}{'cpp_ms':>12}")
    for row in rows:
        print(
            f"{row['operation']:<35}{row['python_ms']:>12.3f}{row['cpp_ms']:>12.3f}"
        )

    # Observational only — no assertions, no hash changes.


if __name__ == "__main__":
    main()
