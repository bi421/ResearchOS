# Phase 4.5 — STEP 2 Baseline Report (Release)

> READ-ONLY step. No C++ source, header, binding, CMake flag, or algorithm was
> modified. This report records the pre-optimization baseline only.

## 1. Environment

| Item | Value |
|---|---|
| OS | Windows (win32), x86-64 |
| CPU | 13th Gen Intel(R) Core(TM) i5-13420H (8P+4E / 12 logical, 4.6 GHz boost) |
| CPU features | AVX2 / AVX / SSE4.2 / FMA (available on this microarchitecture) |
| Compiler | MSVC 14.44.35207 (Microsoft (R) C/C++ Optimizing Compiler Version 19.44.13.6706), MSBuild 17.14.51+25f168cee |
| CMake | 4.4.0 |
| Python | CPython 3.14.6 (cp314 ABI) |
| Compiled module | cpp_quant_engine/python/cpp_quant_engine/cpp_quant_backend.cp314-win_amd64.pyd, ENGINE_VERSION '1.0.0' |
| Build dir | cpp_quant_engine/build (multi-config) |

## 2. Compiler flags (Release, as configured before optimization)

From cpp_quant_engine/build/CMakeCache.txt:

| Variable | Value |
|---|---|
| CMAKE_CXX_FLAGS (base) | /DWIN32 /D_WINDOWS /EHsc |
| CMAKE_CXX_FLAGS_RELEASE | /O2 /Ob2 /DNDEBUG |
| CMAKE_CXX_FLAGS_DEBUG | /Zi /Ob0 /Od /RTC1 (NOT used for baseline) |
| Architecture / SIMD | none (/arch not set) |
| Link-time code generation | none (/GL, /LTCG not set) |
| Floating point | default (/fp:precise, no /fp:fast) |
| OpenMP | disabled (/openmp not set) |
| C++ standard | C++20 (cxx_std_20) |

Note: 'quant_engine' is a STATIC library; the .pyd and the .exe link it in.
LTCG is available (HAS_MSVC_GL_LTCG present in cache) but unused in the
baseline.

## 3. Build command (Release)

```
cmake --build cpp_quant_engine/build --config Release --parallel --target quant_engine_bench cpp_quant_backend quant_engine_tests
```

- Result: EXIT=0. Produced
  cpp_quant_engine/build/benchmarks/Release/quant_engine_bench.exe,
  cpp_quant_engine/python/cpp_quant_engine/cpp_quant_backend.cp314-win_amd64.pyd (Release),
  cpp_quant_engine/build/tests/Release/quant_engine_tests.exe.
- The pre-existing build dir was Debug-only; this fresh Release build is the
  baseline for every measurement below.

## 4. Benchmark commands

- Native (C++ kernels): cpp_quant_engine/build/benchmarks/Release/quant_engine_bench.exe
  (existing harness at benchmarks/benchmark_main.cpp; CSV format:
  benchmark,count,seconds,peak_mem_mib).
- Python->C++ shim (quant ops): a read-only throwaway script written to the
  Temp dir (Temp/opencode/step2_baseline.py) that imports CppQuantBackend from
  the freshly built Release .pyd. Per op: min of 3 runs via
  time.perf_counter; deterministic price series [100 + 30*((i%17)/17) + 0.5*(i%7)].
- Correctness gate: Release test suite quant_engine_tests.exe ->
  475 tests PASSED, 0 failed (no regressions vs the audited Debug build).

## 5. Raw baseline results

### 5.1 Native C++ kernels (build/benchmarks/Release/quant_engine_bench.exe)

```
benchmark,count,seconds,peak_mem_mib
research.grid.1000x10y,87600,29.360996,80.74
research.grid.1000x10y.auto,87600,6.606411,84.77     # 12-thread auto parallel
research.seeded.250x10y,87660,8.172825,86.74
research.random.250x10y,87660,8.112052,89.79
ingest.append,100000,0.010484,89.79
marketdata.load,100000,0.001814,89.79
replay.candle,100000,0.002971,89.79
backtest.run,100000,0.042663,89.79
analyzer.analyze,100000,0.065812,89.79
strategy.kernel.run,100000,0.018365,89.79
ingest.append,1000000,0.080270,191.90
marketdata.load,1000000,0.021510,191.90
replay.candle,1000000,0.025889,191.90
backtest.run,1000000,0.230765,357.45
analyzer.analyze,1000000,0.687715,457.58
strategy.kernel.run,1000000,0.225073,457.58
strategy.kernel.signals_1m,1000000,0.435804,496.64
strategy.kernel.trades_1m,1000000,0.449850,496.64
ingest.append,10000000,0.939601,1919.58
marketdata.load,10000000,0.243172,1919.58
replay.candle,10000000,0.280054,1919.58
backtest.run,10000000,3.038398,3565.82
analyzer.analyze,10000000,13.535931,4194.71
strategy.kernel.run,10000000,6.601443,4194.71
# peak process memory overall: 4194.71 MiB
```

Derived throughput (native):
- backtest.run @10M = 3.29M bars/s
- strategy.kernel.run @10M = 1.51M bars/s
- analyzer.analyze @10M = 0.74M bars/s (slowest native kernel)
- research.grid.1000x10y.auto (parallel, 12 threads) @87660 bars x1000 combos = 6.61s
  vs single-thread grid = 29.36s (~4.4x parallel speedup)

Memory column is process-wide PEAK (GetProcessMemoryInfo PeakWorkingSetSize),
hence monotonically non-decreasing across rows. Treat inter-row deltas as
cumulative high-water marks, not per-op footprints. Peak process memory at
the 10M sweep was 4194.71 MiB.

### 5.2 Quant engine ops via the Python shim (min of 3, Release .pyd)

op = the operation; throughput_elem_per_s = n / seconds(min).

| op | size | seconds | throughput (elem/s) |
|---|---|---|---|
| calculate_returns | 10k | 0.000197 | 5.08e7 |
| calculate_returns | 100k | 0.002541 | 3.94e7 |
| calculate_returns | 1M | 0.045678 | 2.19e7 |
| calculate_returns | 10M | 1.040914 | 9.61e6 |
| calculate_statistics | 10k | 0.000184 | 5.45e7 |
| calculate_statistics | 100k | 0.002862 | 3.49e7 |
| calculate_statistics | 1M | 0.037980 | 2.63e7 |
| calculate_statistics | 10M | 0.847988 | 1.18e7 |
| calculate_volatility_rolling | 10k | 0.000628 | 1.59e7 |
| calculate_volatility_rolling | 100k | 0.010336 | 9.68e6 |
| calculate_volatility_rolling | 1M | 0.090730 | 1.10e7 |
| calculate_volatility_rolling | 10M | 3.116053 | 3.21e6 |
| calculate_metrics | 10k | 0.000324 | 3.09e7 |
| calculate_metrics | 100k | 0.004309 | 2.32e7 |
| calculate_metrics | 1M | 0.052550 | 1.90e7 |
| calculate_metrics | 10M | 1.277613 | 7.83e6 |

Notes:
- calculate_volatility_rolling uses the default window=21. At 10M it is
  3.12s and the single slowest quant op — consistent with the O(n*w)
  per-window allocation hotspot identified in STEP 1.
- These timings include pybind11 copy overhead (input list -> vector<double>
  + output dict construction). The pure-C++ cost is lower; STEP 6 will report
  the in-process native cost of each kernel after refactoring.
- calculate_rolling_mean is NOT an engine operation today; the only
  rolling-mean code path in the tree is the inline SMA crossover inside the
  research signal generator (benchmark_main.cpp lines ~200-248), already
  exercised via research.grid. Rolling-mean baseline is therefore N/A; it will
  be added only if/when the engine exposes a rolling_mean API (out of scope
  for the read-only baseline).

### 5.3 Risk metrics

calculate_metrics (Step 5.2) covers the risk-metrics aggregate: sharpe_ratio,
sortino_ratio, calmar_ratio, profit_factor, win_rate, max_drawdown, total/
mean/std return, annualised return/volatility. The standalone RiskMetrics
(path src/statistics/risk.cpp: VaR, CVaR, beta, alpha, information_ratio) is
not invoked by the certified adapter and so is not benchmarked here; it is a
candidate for STEP 4 if risk-metrics throughput is later requested.

## 6. Observations

1. Volatility (rolling) is the dominant outlier: O(n*w) per-window
   allocation. This is the single highest-leverage target.
2. statistics/metrics each perform several redundant full passes over the
   data (mean recomputed in variance, std, skewness, kurtosis, sharpe,
   sortino, calmar). At 10M these passes are visible in the 0.85s/1.28s.
3. pybind11 copy overhead caps small-op speedup; calculate_returns at 10M is
   1.04s despite trivial arithmetic (returns are n-1 subtractions/divisions)
   — the cost is marshalling 10M doubles across the language boundary each way.
4. analyzer.analyze @10M (13.5s native) is the slowest native kernel; it lives
   in the backtest/performance layer, still in-scope for C++ perf work.
5. The optimizer already parallelizes deterministically (4.4x @12 threads);
   no parallel-computation work is needed there.
6. Compiler flags are minimal Release /O2; no /arch, no LTCG, no /fp — a clear
   low-effort uplift remains on the table for STEP 6.

## 7. Next optimization target

Primary: replace the O(n*w) rolling_volatility_series
(src/quant_engine.cpp:87) with an O(n) sliding-window variance using running
sum / sum-of-squares of the window (one pass, no per-window allocation), then
fold the redundant passes in distribution_summary and compute_all_metrics.
Secondary: enable /arch:AVX2 + LTCG for the vectorizable element-wise passes.

All before/after must pass 475 C++ tests + Phase 4.3/4.4 Python gates with
identical FNV-1a result hashes.
