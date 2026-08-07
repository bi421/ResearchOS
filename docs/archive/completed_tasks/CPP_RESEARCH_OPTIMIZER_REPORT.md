# Document Status

Status:
ARCHIVED

Reason:
Historical record only

Superseded by:
See docs/ARCHITECTURE_FREEZE_V2.md (current constitution)

Original purpose:
See docs/DOCUMENTATION_INVENTORY_REPORT.md

---

# C++ Research Optimization Engine Report

**Project:** ResearchOS — `cpp_quant_engine`
**Date:** 2026-07-31
**Scope:** `C:\Users\User\Desktop\ResearchOS\cpp_quant_engine` (C++ engine only; no changes to the ResearchOS Python architecture).

---

## 1. Executive Summary

A deterministic, parallel, C++20-only **parameter research / optimization module** was
added on top of the existing `StrategyKernel`. It searches a `ParameterSpace` (grid,
random, or seeded) of strategy configurations, evaluates each combination through the
kernel, and ranks results across 11 research metrics — including a new **stability
score** (R² of a least-squares fit over the per-bar equity curve, scaled to `[0, 100]`).

The optimizer is **deterministic by construction**: the combo list is enumerated
deterministically, evaluations are spread across a worker pool via an atomic work
stealer, results are stored by combo index, and ranking is a stable sort tie-broken by
combo index — so a run is **byte-for-byte reproducible regardless of thread
scheduling**. Random search records its seed and can be replayed exactly through a
Seeded search (identical sampled combos and identical result hash).

Per the task constraints, **no Python, broker/execution, or trading-signal logic was
added** — only the deterministic research engine, metrics, hashing, and benchmarking.
The phase adds **110 unit tests (6 suites)**, taking the full suite to **475 tests /
45 suites, all green in Debug and Release**, plus a **1000-strategy × 10-year**
benchmark (hourly bars) in the existing CSV harness.

## 2. Deliverables & Status

| # | Deliverable | Status |
|---|-------------|--------|
| 1 | `ParameterSpace` / `ParamSet` (grid, range, int-range, log-scale, mixed-radix combo decoding, overflow cap) | Done |
| 2 | `Optimizer` with grid / random / seeded search + deterministic ranking | Done |
| 3 | Parallel evaluation with deterministic results irrespective of thread scheduling | Done |
| 4 | 11 ranking metrics incl. new equity-curve **stability score** (R², `[0,100]`) | Done |
| 5 | `OptimizationResult` with full-detail `StrategyEvaluation`, `top_n` retention, canonical result hash | Done |
| 6 | `ResearchRunner` high-level facade (`ResearchPlan`, convenience `run_grid`/`run_seeded`/`run_random`, summary) | Done |
| 7 | 110 new unit tests (475 total, Debug + Release green) | Done |
| 8 | 1000-strategy × 10-year benchmark rows in `quant_engine_bench` | Done |
| 9 | This report | Done |

## 3. Scope Boundaries (Explicitly NOT Changed)

- ❌ No Python or Python bindings enabled (`BUILD_PYTHON_BINDINGS=OFF`).
- ❌ No broker/execution connections.
- ❌ No trading-signal generation logic added (research consumes caller-supplied signals).
- ✅ Only: parameter spaces, deterministic search/optimization, metrics, ranking, hashing, benchmarking.

## 4. Architecture Overview

```
                 ParamSet / ParameterSpace (combo enumeration)
                                   │
                   OptimizerConfig (search type, seed, top_n, threads)
                                   ▼
                        ┌──────────────────────────┐
                        │        Optimizer         │
                        │  include/quant/research/ │
                        │  optimizer.h / .cpp      │
                        │                          │
                        │  combo_indices()         │  grid: exhaustive
                        │  ── grid/random/seeded   │  random: device seed, recorded
                        │  seeded: mt19937_64(seed)│  seeded: reproducible sample
                        │                          │
                        │  parallel worker pool    │  atomic work-stealing, per-slot
                        │  (atomic next, N threads)│  storage → scheduling-independent
                        │                          │
                        │  stable rank + tie-break │  rank metric ± MaxDrawdown(asc)
                        │  by combo index          │
                        └───────────┬──────────────┘
                                    │  top_n re-evaluation (full SimulationResult)
                                    ▼
                     ┌──────────────────────────────┐
                     │      OptimizationResult      │
                     │  optimization_result.h       │
                     │  ranked[] + compute_result_hash
                     └──────────────────────────────┘
```

## 5. Component Details

### 5.1 `ParamSet` / `ParameterSpace` — `parameter_space.h/.cpp`

- `ParamSet`: ordered name→value map; `set/get/get_int` (banker's `llround`), `to_string()`
  (`"k=v k=v"`, `%.6g`), order-sensitive equality.
- `ParameterSpace`: `add_grid`, `add_range` (arithmetic or **log scale**), `add_int_range`
  (overflow-safe stepping).
- **Mixed-radix combo decoding** (`combo(index)`): first-added parameter varies fastest;
  `combo_count()` returns the exact product, capped at `SIZE_MAX` on overflow
  (an empty space yields 1 trivial combo).

### 5.2 `Optimizer` — `optimizer.h/.cpp`

- **Search types** (`optimization_result.h::SearchType`):
  - `Grid` — exhaustive enumeration in combo-index order.
  - `Random` — samples without replacement; seed drawn from `std::random_device` and
    **recorded in `OptimizationResult.seed`** so the run can be replayed.
  - `Seeded` — deterministic `std::mt19937_64(seed)` sample without replacement.
  - `random_samples ≥ combo_count` degrades to exhaustive enumeration.
- **Parallel evaluation**: `max_parallelism` workers (0 → `hardware_concurrency()`)
  pull slots from an `std::atomic<size_t>`; each slot writes a **lightweight `EvalRecord`
  (stats + metrics only — no equity curve)**, keeping sweeps memory-bounded.
- **Deterministic ranking**: `std::stable_sort` over successful records by the rank
  metric value (direction-aware; **MaxDrawdown ascending**, all others descending),
  tie-broken by ascending combo index — independent of thread scheduling.
- **`top_n` retention**: retained strategies are **re-evaluated to full detail**
  (equity/drawdown curves, trades, hashes via `evaluate_combo`); `top_n == 0` retains
  every evaluated strategy.
- **Result hash**: FNV-1a 64-bit over a canonical serialization (seed, requested/
  evaluated/failed counts, per-strategy combo index, params, rank value and 5 key
  metrics, final equity). The hash **excludes the search type**, so a Random run and its
  Seeded replay produce identical hashes.
- **Thread safety**: `optimize()`/`evaluate_combo()` are `const` and hold no mutable
  state; a single instance may be driven concurrently from multiple threads.

### 5.3 Metrics & stability — `optimization_result.h`, `optimizer.cpp`

`OptimizationMetrics` carries all 11 ranking metrics (NetProfit, Sharpe, Sortino, Calmar,
MaxDrawdown, ProfitFactor, WinRate, Expectancy, RecoveryFactor, TradeCount, Stability)
plus derived returns. `compute_optimization_metrics(stats, equity_curve)` maps kernel
`StrategyStats` onto the research view.

**Stability score** = coefficient of determination (R²) of the least-squares line through
the per-bar equity curve, scaled to `[0, 100]`. Flat or perfectly linear equity = 100;
a noisy, trendless curve approaches 0.

### 5.4 `ResearchRunner` — `research_runner.h/.cpp`

High-level facade: `ResearchPlan` (space, signal generator, config provider, base config,
optimizer config), `ResearchRunner::run(plan)`, single-combo `evaluate_combo`, and
convenience `run_grid` / `run_seeded` / `run_random`, plus `optimization_summary` that
renders a compact text summary of the ranked table.

## 6. Build & Test Results

Environment: Visual Studio 17 2022 (x64), CMake 4.4.0, C++20, GoogleTest v1.15.2 (static).

```
cmake -S . -B build
cmake --build build --config Debug
cmake --build build --config Release
```

| Config | Test executable | Result |
|--------|-----------------|--------|
| Debug | `build/tests/Debug/quant_engine_tests.exe` | **475/475 passed** (45 suites, ~38 s) |
| Release | `build/tests/Release/quant_engine_tests.exe` | **475/475 passed** (45 suites, ~1.5 s) |

**New tests (110) by suite** (`tests/test_research_optimizer.cpp`):

| Suite | Coverage | Tests |
|-------|----------|-------|
| `ParamSet` | accessors, fallbacks, int rounding, overwrite, equality, string form | 14 |
| `ParameterSpace` | combo counts, mixed-radix decoding, int/log ranges, overflow cap, invalid specs | 22 |
| `OptimizationMetrics` | metric mapping, stability (flat/perfectly-linear/monotonic/empty), rank direction | 10 |
| `Optimizer` | grid order, ranking direction per metric, tie-breaks, `top_n`, random/seeded sampling & reproducibility, parallel determinism, concurrency, providers, signal-generator param handoff, error handling, hashing | 45 |
| `ResearchRunner` | plans, rank metric, parallelism, convenience runs, summaries, reuse, concurrent calls | 17 |
| `Research` | search-type & metric name helpers | 2 |

Notable verified semantics (Debug + Release):
- Identical parallel vs single-threaded runs produce **identical result hashes**.
- Random search records its seed; a Seeded replay reproduces the same sampled combos
  and the same `compute_result_hash()`.
- Different seeds sample different combos (400-combo space, 20 samples).
- MaxDrawdown ranks ascending; every other metric ranks descending.
- All-combo ties are broken by ascending combo index.
- `top_n` bounds retained full-detail strategies; `top_n == 0` keeps every evaluation.
- Stability: flat and perfectly linear curves score 100; a gently noisy uptrend scores > 90;
  single-point/empty curves score 0; results always lie in `[0, 100]`.

## 7. Benchmark Results (Release build)

New rows added to `benchmarks/benchmark_main.cpp` (same CSV harness; measured on this
machine; **2 hardware threads**):

| Row | count | seconds | peak_mem MiB | notes |
|-----|-------|---------|--------------|-------|
| `research.grid.1000x10y` | 87,660 (10 y H1) | 64.86 | 80.51 | 1000 combos, single thread |
| `research.grid.1000x10y.auto` | 87,660 (10 y H1) | 33.89 | 84.33 | 1000 combos, auto threads (2) |
| `research.seeded.250x10y` | 87,660 (10 y H1) | 25.30 | 89.04 | 250 combos, seeded (seed 42), 1 thread |
| `research.random.250x10y` | 87,660 (10 y H1) | 20.04 | 89.40 | 250 combos, random (recorded seed), 1 thread |

Notes:
- The grid rows evaluate **1000 distinct strategies × 10 years of hourly candles**
  (87,660 bars each) = ~87.7M kernel bar-runs in ~65 s single-threaded (~1.35M bars/s
  per combo), or ~34 s with the machine's 2 auto threads (~2.6M bars/s aggregate).
- `top_n = 10` bounds full-detail retention; the sweep itself stores only lightweight
  per-combo stats, so the whole 1000-strategy research run peaks under **~90 MiB**.
- The pre-existing engine rows (`ingest`, `marketdata`, `replay`, `backtest`,
  `analyzer`, `strategy.kernel`) are unchanged and still pass; the 10M-candle peak
  (~4.2 GiB) reflects the large in-memory bar/equity datasets of those rows.

## 8. Notable Build-System Changes

- Sources under `src/research/*.cpp` and `include/quant/research/*.h` are picked up by
  the existing `file(GLOB ... CONFIGURE_DEPENDS)` rules; `tests/test_research_optimizer.cpp`
  is discovered automatically by `gtest_discover_tests`.
- The benchmark harness (`quant_engine_bench`) includes the research headers; no CMake
  targets were added or changed.

## 9. Known Limitations & Future Work

- Random/Seeded sampling uses rejection sampling with a try cap, then a deterministic
  fallback fill; this is exact for practical space sizes but a reservoir/Shuffle
  approach would be exact for pathological huge spaces.
- Stability is a global equity-curve R²; per-window/rolling stability (e.g. rolling
  12-month score) is a natural extension for walk-forward-style research.
- `top_n == 0` re-evaluates every strategy to full detail, which is correct but doubles
  signal-generation cost for full-retention runs; bounded `top_n` avoids this.
- Metric rank values that are NaN tie-break by combo index (no reliable ordering is
  possible); NaN handling could be surfaced as explicit "not ranked" markers.
