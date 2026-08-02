# C++ ↔ Python Integration Bridge Report

**Project:** ResearchOS — `cpp_quant_engine`
**Date:** 2026-07-31
**Scope:** `C:\Users\User\Desktop\ResearchOS\cpp_quant_engine` (C++ engine + bindings + Python package + report only; no changes to the ResearchOS Python architecture, Decision Engine, MT5, or TradingView).

---

## 1. Executive Summary

A production-grade **Python/C++ integration contract** now exposes the entire
C++ quant engine to the future ResearchOS Python layer through a pybind11
bridge. The bridge wraps five engine operations — **MarketData**, **Statistics**,
**Risk**, **Simulation**, and **BacktestEngine / PerformanceReport** — behind a
stable, typed API.

The contract is defensively engineered around three guarantees:

1. **Stable numeric error codes** shared byte-for-byte between C++, pybind11,
   and the Python exception hierarchy.
2. **Canonical SHA-256 input/result hashes** computed identically in C++ and
   Python, giving every call an audit-verifiable fingerprint.
3. **A backward-compatible legacy shim** (`CppQuantBackend`) that preserves the
   old `quant_engine` API surface so existing ResearchOS code keeps working.

Verification: **275/275 C++ tests** and **96/96 Python tests** pass (Debug
build). Per the task constraints, the bridge transports signals but implements
**no trading logic, no broker connections, and no AI components**.

## 2. Deliverables & Status

| # | Deliverable | Status |
|---|-------------|--------|
| 1 | Bridge contract headers (`bridge_interface.h`, `bridge_models.h`, `bridge_validation.h`) | Done |
| 2 | `BridgeBackend` implementation (`src/bridge/bridge.cpp`, `src/bridge/validation.cpp`) | Done |
| 3 | pybind11 module `cpp_quant_backend` (`Backend` + legacy `CppQuantBackend`) | Done |
| 4 | Python package (`cpp_quant_engine`): typed models, exceptions, backend facade | Done |
| 5 | Canonical SHA-256 hash contract mirrored byte-for-byte across languages | Done |
| 6 | Backtest engine fix: trade recording + drawdown curve | Done |
| 7 | Tests: 51 new C++ (GTest) + 96 Python (pytest) | Done — all green |
| 8 | Report | Done |

## 3. Scope Boundaries (Explicitly NOT Changed)

- ❌ No trading signals / strategy logic in the bridge (signal is transported as a callable; `signal_reference` is audit metadata only).
- ❌ No broker/execution connections.
- ❌ No AI/ML components.
- ❌ No changes to `researchos.*`, Decision Engine, MT5, or TradingView files.
- ✅ Only: engine exposure via a stable Python contract, marshalling, validation, error mapping, canonical hashing, backward-compat shim, tests.

## 4. Architecture Overview

```
 ┌────────────────────────────────────────────────────────────────────┐
 │  Python 3.14 (ResearchOS layer)                                   │
 │  cpp_quant_engine.{models,exceptions,backend}  (pure Python)      │
 │   │  typed objects ↔ plain-dict BaseObjects; hash verification    │
 │   ▼                                                                │
 │  cpp_quant_engine.cpp_quant_backend  (pybind11 .pyd, 3.3 MB)      │
 │   │  dict ↔ C++ bridge models; Python signal → quant::SignalFn    │
 │   │  exception translator → typed Python errors by numeric code    │
 └───┼────────────────────────────────────────────────────────────────┘
     ▼
 ┌────────────────────────────────────────────────────────────────────┐
 │  C++20  cpp_quant_engine  (quant_engine.lib)                      │
 │  IBridgeBackend → BridgeBackend                                   │
 │   ├─ MarketData (load/validate/index)                             │
 │   ├─ DescriptiveStats (mean/var/quantiles/…)                      │
 │   ├─ RiskMetrics (VaR/CVaR/drawdown/Sharpe/Sortino)               │
 │   ├─ HistoricalSimulation (deterministic)                         │
 │   ├─ BacktestEngine (fill-at-close, TradeBook, drawdown curve)    │
 │   └─ PerformanceReport / PerformanceAnalyzer (calendar, downside) │
 └────────────────────────────────────────────────────────────────────┘
```

The numerical work always happens in C++; the Python layer only marshals data,
validates types, maps errors, and verifies hashes — it never re-implements
computations.

## 5. Component Details

### 5.1 Contract Headers — `python/`

- `bridge_interface.h` — `BridgeMeta`, `kBridgeName` / `kBridgeVersion` (`"1.0.0"`) / `kBridgeProtocolVersion` (1), `supported_calculation_versions()` (`CALCULATION_V1`), `BridgeErrorCode` enum, `BridgeError` (carries stable numeric `code()`), `BridgeSignalFn` (alias of `quant::SignalResult`), pure-virtual `IBridgeBackend` with the five operations, and `create_backend()` factory.
- `bridge_models.h` — all value models (`CandleModel`, `MarketDataRequest/Result`, `StatisticsRequest/Result`, `RiskRequest/Result`, `SimulationRequest/Result`, `BacktestRequest/Result`, `PerformanceRequest/Result`), each with `compute_input_hash()` / `compute_result_hash()`, plus canonical primitives: `canonical_float` (`{:.10f}`), `canonical_object` (sorted keys, JSON-escaped), `canonical_float_array`, `canonical_double_map`, `sha256_hex`, `iso8601_now`.
- `bridge_validation.h` — per-request validators and `require_*` guards; `timeframe_from_string` parser (M1…W1).

### 5.2 BridgeBackend — `src/bridge/`

- Self-contained SHA-256 (verified against FIPS 180-4 vectors) and canonical JSON serialization — no external hashing dependency.
- All five operations delegate to the existing engine modules (`DescriptiveStats`, `RiskMetrics`, `MarketData`, `BacktestEngine`, `PerformanceAnalyzer`/`PerformanceReport`).
- `performance_analyze` seeds `quant::BacktestResult.max_drawdown_pct` from `RiskMetrics::max_drawdown` before `PerformanceReport::compute` so the report's drawdown figures are consistent.

### 5.3 Backtest Engine Fix — `src/backtest/backtest_engine.cpp`

- `execute_signal` now records trades into `TradeBook` (open/closed buy/sell/close-short entries) and the run closes any open position at the end (`book.close_trade`).
- `BacktestResult::drawdown_curve` is now populated (running-peak positive percentage).
- Removed the `uint64_t& trade_id` parameter; signature updated in `include/quant/backtest/backtest_engine.h`.

### 5.4 pybind11 Module — `bindings/python_bindings.cpp`

- Dict ⇄ C++ model converters with strict `None` handling: a `None` value where a list is required now raises `InvalidType` (102) instead of silently becoming an empty list.
- `Backend` class — the stable contract. All inputs/outputs are plain `py::dict` (BaseObjects).
- Python signal callable → `quant::SignalFn` via `py::gil_scoped_acquire` (safe re-entry from C++).
- Exception translation via `py::register_exception_translator`: every C++ `BridgeError` is raised as the typed Python exception class selected by its numeric code (module imports `cpp_quant_engine.exceptions.error_from_code`).
- Module exports: `Backend`, `CppQuantBackend` (legacy), `version()`, `bridge_version()`, `protocol_version()`, `supported_calculation_versions()`, `error_codes()`.

### 5.5 Legacy Shim — `CppQuantBackend`

Preserves the old `QuantComputationInterface` surface for existing ResearchOS code: `calculate_returns` (percentage/absolute/log), `calculate_volatility`, `calculate_drawdown`, `calculate_statistics`, `calculate_metrics`, `calculate_performance_analytics`, `run_simulation`, `get_version`, `mean`, `std_dev`, `variance`, `z_score`.

### 5.6 Python Package — `python/cpp_quant_engine/`

- `models.py` — full dataclass mirror of `bridge_models.h`, `to_base_object` / `from_base_object`, and byte-identical `compute_input_hash` / `compute_result_hash`; `PerformanceReport` aliased to `PerformanceResult`.
- `exceptions.py` — `BridgeError` base + 11 typed subclasses with stable codes; `error_from_code` / `error_from_native`.
- `backend.py` — `CppQuantEngineBackend` typed facade with hash verification (`HashMismatchError` on mismatch); `_native_call` normalizes pybind11 cast failures to `InvalidTypeError` while letting typed `BridgeError`s through; facades `Statistics`, `Risk`, `Simulation`, `BacktestEngine`; `default_backend()`.
- `__init__.py` — stable public API re-exports; optional legacy `CppQuantBackendWrapper` imported only when the ResearchOS tree is present.

### 5.7 Error Codes

| Code | Name | Python class |
|------|------|--------------|
| 100 | `InvalidArgument` | `InvalidArgumentError` |
| 101 | `InvalidParameter` | `InvalidParameterError` |
| 102 | `InvalidType` | `InvalidTypeError` |
| 200 | `InsufficientData` | `InsufficientDataError` |
| 201 | `EmptyData` | `EmptyDataError` |
| 202 | `MalformedData` | `MalformedDataError` |
| 203 | `OutOfBounds` | `OutOfBoundsError` |
| 300 | `UnsupportedVersion` | `UnsupportedVersionError` |
| 301 | `ValidationFailed` | `ValidationFailedError` |
| 302 | `HashMismatch` | `HashMismatchError` |
| 500 | `InternalError` | `InternalError` |

### 5.8 Canonical Hash Contract

- Algorithm: SHA-256 over the canonical JSON of the request/result.
- Canonical JSON: keys sorted alphabetically; numbers formatted `{:.10f}` (fixed-point, 10 decimals); strings JSON-escaped; timestamps ISO-8601 (UTC-naive, second precision).
- `input_hash` covers every input field; `result_hash` covers the full result plus `input_hash`, `engine_version`, `bridge_version`, `calculation_version`, and `execution_timestamp` (for simulation/backtest).
- The Python mirror produces **identical digests** (verified by tests over statistics, risk, simulation, market data, backtest, and performance cases, including 100k-element datasets).

## 6. Test Results

### 6.1 C++ (GTest via ctest, Debug)

**275/275 passed** — the pre-existing 224 plus **51 new bridge tests**:

| File | Coverage | Tests |
|------|----------|-------|
| `test_bridge_core.cpp` | canonical serialization, SHA-256 known vectors, model hashes | ~10 |
| `test_bridge_validation.cpp` | validator rejections, code mapping | ~15 |
| `test_bridge_engine.cpp` | five operations end-to-end, hashes, determinism | ~26 |

### 6.2 Python (pytest, CPython 3.14.6)

**96/96 passed** (`python/tests/test_bridge.py`): metadata/versions, error-code
mapping, canonical serialization, dict round-trips, hash consistency across
languages, statistics/risk/simulation/market-data/backtest/performance behavior,
type conversion and `InvalidType` handling, typed exceptions with `.code`,
large datasets (100k candles, prices, equity points), the legacy shim, and
determinism/audit fields.

### 6.3 Build

- `cpp_quant_backend.cp314-win_amd64.pyd` (≈3.3 MB) built (MSVC 17.14.51, pybind11 3.0.4, Python 3.14.6) directly into `python/cpp_quant_engine/`.
- `quant_engine.lib` Debug build verified; smoke test confirms engine 0.1.0, bridge 1.0.0, protocol 1.

## 7. Notable Build-System Changes

- Root `CMakeLists.txt`: added `python/` to the `quant_engine` target include dirs; `BUILD_PYTHON_BINDINGS` branch configures `find_package(pybind11 CONFIG)` (with `python -m pybind11 --cmakedir` fallback) and `find_package(Python3 COMPONENTS Development)` before `pybind11_add_module` (required for `python3_add_library`); target `cpp_quant_backend` links `quant_engine`; `LIBRARY_OUTPUT_DIRECTORY` / `_DEBUG` / `_RELEASE` set so the `.pyd` lands directly in `python/cpp_quant_engine/`.
- `bindings/CMakeLists.txt` rewritten as a standalone verification doc (fatal if `quant_engine` is not a target; not intended for `add_subdirectory`).
- pybind11 3.x note: `exception<T>` no longer exposes `def_property_readonly`; errors are translated with `register_exception_translator` instead.

## 8. Known Limitations & Future Work

- Backtest fills remain simplified fill-at-close (existing behavior); the bridge does not add execution modeling.
- `BacktestEngine` signal is transported as a Python callable; strategy registration and audit plumbing (`signal_reference`) exist but a ResearchOS-side strategy registry is future work.
- Period (monthly/yearly) performance bucketing requires D1-or-better bar timestamps; without them period returns are empty (documented behavior).
- The bridge is built/verified for Debug (MSVC). A Release build with `-DBUILD_PYTHON_BINDINGS=ON` is a direct next step (C++ Release tests already green).
- Performance of the Python layer is marshalling-bound; large datasets (100k) already complete in well under a second, but a C++-side batched/streaming API is a natural follow-up for 1M+ candles.
