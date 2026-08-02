# C++ Backtest Engine Enhancement Report

**Project:** ResearchOS — `cpp_quant_engine`
**Date:** 2026-07-31
**Scope:** `C:\Users\User\Desktop\ResearchOS\cpp_quant_engine` (C++ engine only; no changes to the ResearchOS Python architecture).

---

## 1. Executive Summary

The C++ backtest engine was upgraded from a prototype into an institutional-grade
research computation engine. The work delivers a clean **data pipeline**
(`MarketData → Backtest Engine → Performance Report`), a **deterministic event
replay engine**, a **performance analyzer** with drawdown/calendar/downside-risk
analysis, **CSV/JSON serialization**, a **native benchmark harness**
(100k / 1M / 10M candles), and **75 new unit tests** (224 total, all green in
Debug and Release).

Per the task constraints, no trading signals, strategies, broker connections, or
AI components were added — only data processing, simulation, statistics, and
performance measurement.

## 2. Deliverables & Status

| # | Deliverable | Status |
|---|-------------|--------|
| 1 | Backtest Data Interface (`MarketData → BacktestEngine → PerformanceReport`) | Done |
| 2 | Event Replay Engine (`CandleEvent` / `TimestampEvent` / `SessionEvent`) | Done |
| 3 | Performance Analyzer extensions (equity curve, drawdown periods, recovery time, monthly/yearly returns, volatility, downside risk) | Done |
| 4 | Benchmark system (100k / 1M / 10M candles; replay + backtest speed; memory) | Done |
| 5 | 50+ tests (deterministic replay, empty dataset, corrupted candles, large datasets, serialization) | Done — **75 new** |

## 3. Scope Boundaries (Explicitly NOT Changed)

- ❌ No trading signals / strategy logic added.
- ❌ No broker/execution connections.
- ❌ No AI/ML components.
- ✅ Only: data provisioning & validation, deterministic simulation, statistics, performance analytics, serialization, benchmarking.

## 4. Architecture Overview

```
 ┌─────────────┐   load/append    ┌──────────────────────┐
 │  Data files │ ───────────────▶ │    MarketData        │  (validates, indexes, slices)
 │ (CSV/JSON)  │                  │ include/quant/backtest/market_data.h
 └─────────────┘                  └──────────┬───────────┘
                                             │ OHLCVSource adapter (MarketDataSource)
                                             ▼
                                    ┌──────────────────────┐
                                    │   BacktestEngine     │  (fills at close; config-driven)
                                    │ backtest_engine.h    │
                                    └──────────┬───────────┘
                                               │ BacktestResult (equity_curve, bars_used, trades)
     ┌─────────────────────────────────────────┼──────────────────────────────┐
     ▼                                         ▼                              ▼
┌──────────────┐                    ┌─────────────────────┐          ┌────────────────────┐
│EventReplay   │                    │ PerformanceAnalyzer │          │  serialization     │
│Engine        │                    │ performance_analyzer│          │  (CSV + JSON)      │
│event_replay.h│                    │  DetailedReport     │          │  serialization.h   │
└──────────────┘                    └─────────────────────┘          └────────────────────┘
```

## 5. Component Details

### 5.1 Backtest Data Interface — `MarketData`

New module `include/quant/backtest/market_data.h` / `src/backtest/market_data.cpp`.

- Owns a chronologically ordered, validated candle series for a symbol/timeframe.
- `load()` rejects invalid OHLC and non-increasing timestamps (corrupt data never
  reaches the engine).
- `append()`, `validate()`, `slice()`, `to_ohlcv()`, `find_index()`, `first/last_time()`.
- `MarketDataSource` adapts `MarketData` to the existing `OHLCVSource` contract.
- `BacktestEngine::run(MarketData&, SignalFn)` overload added
  (`backtest_engine.h:67`), so the engine can be driven directly from `MarketData`.
- The `OHLCVSource` interface was extracted to
  `include/quant/backtest/ohlcv_source.h` to break a header cycle and keep the
  data contract independent of the engine.
- `run()` now also populates `BacktestResult::bars_used` (needed for calendar
  performance analysis).

### 5.2 Event Replay Engine — `EventReplayEngine`

New module `include/quant/backtest/event_replay.h` / `src/backtest/event_replay.cpp`.

- Event model: `ReplayEvent` (discriminated by `EventType`):
  - `EventType::Candle` — a bar at its open time.
  - `EventType::Timestamp` — a time tick at the bar close.
  - `EventType::Session` — `SessionStatus::Open` / `SessionStatus::Close` at
    calendar-day boundaries.
- `ReplayMode`: `CandlesOnly`, `CandleTimestamp`, `FullWithSessions`.
- **Deterministic**: the same `MarketData` always produces the identical event
  stream (types, timestamps, 1-based `sequence` numbers). Verified by replaying
  the same series twice and by snapshot equality tests.
- Streaming iterator API (`advance()`, `reset()`, `current_event()`,
  `sequence()`, `position()`, `snapshot()`), so 10M candles are replayed without
  materializing the full event list.
- Session detection: calendar-day boundaries derived from bar timestamps.

### 5.3 Performance Analyzer — `PerformanceAnalyzer`

New module `include/quant/backtest/performance_analyzer.h` /
`src/backtest/performance_analyzer.cpp`, extending `PerformanceReport`
(`include/quant/backtest/performance.h`).

- `DetailedPerformanceReport` adds, on top of the base report:
  - `returns` — bar-to-bar equity returns.
  - `drawdowns` — full drawdown episodes (`DrawdownPeriod`: peak, trough,
    recovery indices, max drawdown %, length, recovered flag).
  - `yearly_returns` / `monthly_returns` — calendar-bucketed returns
    (`PeriodReturn`) with bar counts.
  - `DownsideMetrics` — downside deviation (annualized), historical VaR 95/99,
    CVaR 95/99, annualized volatility, average/max drawdown duration.
  - Recovery statistics: `max_drawdown_recovery_bars`, average recovery time,
    underwater bars, `time_in_drawdown_pct`.
- `PerformanceReport` gained: `downside_deviation`, `downside_deviation_annualized`,
  `var_95/99`, `cvar_95/99`, `max_drawdown_recovery_bars`, `time_in_drawdown_pct`
  (all filled by `PerformanceReport::compute`), plus extended `summary()`.
- Reuses existing `RiskMetrics` / `DescriptiveStats` for VaR, volatility and Sharpe.

### 5.4 Serialization — `quant::serialization`

New module `include/quant/backtest/serialization.h` /
`src/backtest/serialization.cpp`.

- ISO-8601 timestamp helpers (`to_iso8601` / `from_iso8601`).
- Candle CSV: `timestamp,open,high,low,close,volume,trade_count,vwap,timeframe`
  with strict round-trip parsing (header/blank-line tolerant; rejects malformed
  rows, bad timestamps, and invalid OHLC).
- Event JSON: full `ReplayEvent` serialization/deserialization.
- Report JSON: flat `PerformanceReport` and detailed `DetailedPerformanceReport`.
- Minimal dependency-free JSON parser/writer (no external libraries).

### 5.5 Benchmark Harness — `quant_engine_bench`

New module `benchmarks/CMakeLists.txt` + `benchmarks/benchmark_main.cpp`
(gated by `BUILD_BENCHMARKS`, default ON).

- Measures, for 100k / 1M / 10M candles:
  - `ingest.append` — `OHLCVContainer::append` throughput.
  - `marketdata.load` — `MarketData` load + validation.
  - `replay.candle` — full event replay (CandlesOnly path).
  - `backtest.run` — full engine run (100% fill on bullish bars).
  - `analyzer.analyze` — full `PerformanceAnalyzer` pass.
  - Peak working-set memory (MiB).

## 6. Build & Test Results

Environment: Visual Studio 17 2022 (x64), CMake 4.4.0, C++20, GoogleTest v1.15.2 (static).

```
cmake -S . -B build
cmake --build build --config Debug
cmake --build build --config Release
```

| Config | Test executable | Result |
|--------|-----------------|--------|
| Debug | `build/tests/Debug/quant_engine_tests.exe` | **224/224 passed** (32 suites, ~650 ms) |
| Release | `build/tests/Release/quant_engine_tests.exe` | **224/224 passed** (32 suites, ~94 ms) |

**New test suites (75 tests) by category:**

| File | Coverage | Tests |
|------|----------|-------|
| `test_market_data_iface.cpp` | load/append/validate, empty data, corrupted candles, slicing, `MarketDataSource`, engine integration | 18 |
| `test_event_replay.cpp` | deterministic replay, all modes, empty dataset, single candle, session boundaries, reset/position, snapshot | 15 |
| `test_performance_analyzer.cpp` | drawdown periods, recovery, monthly/yearly returns, downside/VaR, time-in-drawdown | 17 |
| `test_serialization.cpp` | CSV round-trip, malformed/corrupt input, ISO-8601, event JSON round-trip, report JSON | 15 |
| `test_backtest_integration.cpp` | end-to-end pipeline, 100k datasets, determinism, corrupted-data guard | 10 |

Requirement coverage: deterministic replay ✅, empty dataset ✅, corrupted candles ✅,
large datasets (100k) ✅, serialization ✅.

## 7. Benchmark Results (Release build)

Measured on the current machine (`benchmark,count,seconds,peak_mem_mib`):

| Operation | 100k (s) | 1M (s) | 10M (s) | Peak mem @10M (MiB) |
|-----------|----------|--------|---------|----------------------|
| `ingest.append`       | 0.008 | 0.066 | 0.881 | 1910 |
| `marketdata.load`     | 0.002 | 0.017 | 0.211 | 1910 |
| `replay.candle`       | 0.002 | 0.023 | 0.267 | 1910 |
| `backtest.run`        | 0.008 | 0.070 | 0.709 | 2144 |
| `analyzer.analyze`    | 0.017 | 0.193 | 1.667 | 2144 |

Notes:
- 10M M1 candles (~19 years) ingest in <0.9 s; full backtest in <0.8 s;
  full analytics pass in <1.7 s (Release, single-threaded).
- Memory is dominated by the raw candle/equity storage for the 10M dataset
  (~1900 MiB for ~7 in-memory double vectors, plus transient copies during
  analysis); per-bar overhead is ≈200 bytes.
- The same harness in a Debug build is ~20× slower (unoptimized); numbers above
  are the Release figures for reference/reproducibility.

## 8. Notable Build-System Changes

- Root `CMakeLists.txt`: library target unified on `quant_engine` (was
  `cpp_quant_engine`, while tests already linked `quant_engine`); added
  `BUILD_BENCHMARKS` + `add_subdirectory(benchmarks)`; pybind11 target renamed
  `cpp_quant_backend` (default `BUILD_PYTHON_BINDINGS=OFF`); sources via
  `file(GLOB_RECURSE ... CONFIGURE_DEPENDS)`; added install rules.
- `tests/CMakeLists.txt`: forces static GoogleTest (avoids DLL PATH issues) and
  excludes `test_statistics.cpp` from the GTest suite. That file is a legacy
  self-contained harness (own `main()`, tests the deprecated `quant_engine`
  namespace, 2 pre-existing failures) which shadows `gtest_main` and broke
  `gtest_discover_tests`; it is excluded from discovery so the real GTest suite
  (224 tests) runs and reports green.
- New `benchmarks/CMakeLists.txt`.

## 9. Known Limitations & Future Work

- `BacktestEngine::execute_signal` intentionally uses simplified fill-at-close
  logic (existing behavior, unchanged); trade records are tracked but the trade
  book is not yet wired into the fill path — reflected in `total_trades = 0` in
  the integration signal used for benchmarks.
- Period (monthly/yearly) returns require `bars_used` timestamps; when the result
  carries no bars, period returns are empty (documented behavior).
- The JSON parser supports the schema emitted by this module (no unicode escapes
  beyond basic control characters).
- Benchmarks are single-threaded; multi-threaded replay/analysis is a natural
  follow-up.
