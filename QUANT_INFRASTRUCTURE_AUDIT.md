# QUANT_INFRASTRUCTURE_AUDIT.md

Phase 0 — Quant Infrastructure Audit of the ResearchOS quant stack.

**Scope boundary (architect ownership):** `researchos/experiments/`, `researchos/quant_engine/`, `researchos/market_memory/`, `researchos/core/`, `researchos/storage/`, `researchos/validation/`. The `researchos/decision_engine/` module is **out of scope** and is excluded from all recommendations below.

**Nature of this document:** Analysis only. No code was modified during this phase.

**Verification baseline (ran during audit):**
- Python test suite: **875 passed** (28.0s), 5 DeprecationWarnings (`datetime.utcnow()` in `market_memory/repository.py:96`).
- C++ engine: **175/175 tests passing** across 30 suites (per prior session runs).

---

## 1. Current Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RESEARCHOS (Python)                              │
│                                                                            │
│  interfaces/          api.py (FastAPI: /cycles/run, /cycles/{id},           │
│                       /audit/verify)   cli.py                              │
│                                                                            │
│  pipeline/            ResearchPipeline — 11-stage deterministic lifecycle   │
│                       start_research → observation → evidence →             │
│                       interpretation → narrative → hypothesis → scenario → │
│                       confidence → contradiction → report → validation →   │
│                       failure analysis → knowledge → lesson → cognitive     │
│                                                                            │
│  objects/             17 modules, ~50 object types, all extend BaseObject   │
│  validation/          rules.py (VALIDATION_RULES) + validators.py          │
│                       (VALIDATOR_REGISTRY, 14 validators)                  │
│  repository/          RepositoryInterface (ABC) + MemoryRepository          │
│  storage/             ResearchRepository (SQLite, OBJECT_REGISTRY)          │
│                                                                            │
│  ─── QUANT COMPUTATION LAYER (owned by this architecture) ──────────────  │
│                                                                            │
│  quant_engine/        QuantComputationInterface (ABC)                      │
│                          │                                                │
│                          ├── PythonQuantBackend  (CURRENT, pure Python)    │
│                          └── CppQuantBackend     (FUTURE, pybind11 seam)   │
│                       statistics/ metrics/ performance/ simulation          │
│                       (HistoricalSimulationEngine, set_backend() seam)     │
│                                                                            │
│  experiments/         QuantHypothesis → Experiment → ExperimentRun          │
│                       → ExperimentResult → ExperimentValidation            │
│                       → LearningRecord → ExperimentReport                  │
│                       AbstractExperimentRunner (ABC)                       │
│                          ├── BaseExperimentRunner (CURRENT, RNG-stubbed)   │
│                          └── CppExperimentRunner  (FUTURE, pybind11 seam)  │
│                                                                            │
│  market_memory/       MarketSnapshot / MarketRegime / MacroState /          │
│                       HistoricalScenario + MarketMemoryRepository           │
│                       (in-memory + optional SQLite)                         │
│                       ScenarioMatcher / OutcomeAnalysis / features /        │
│                       similarity / events / integration / report           │
│                                                                            │
│  core/                BaseObject (deterministic ID, lifecycle, hashing,     │
│                       audit) + identity/ lifecycle/ timestamp/ versioning  │
│                                                                            │
│  engines/             attribution.py   macro/engine.py   memory/engine.py  │
│  agents/              (out of core audit scope)                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          cpp_quant_engine (C++20)                          │
│                                                                            │
│  core/        Error, Result<T>, Logger, Config, QuantEngine                │
│  market/      types, OrderBook + MARKET DATA ENGINE:                       │
│               candle.h, time_index.h, ohlcv_container.h, data_loader.h,    │
│               timeframe_aggregator.h, historical_iterator.h,               │
│               market_data_engine.h                                         │
│  statistics/  descriptive, correlation, risk                               │
│  simulation/  RNG, GBM/OU/JumpDiff/Heston paths, Monte Carlo               │
│  backtest/    TradeBook, BacktestEngine, PerformanceReport                 │
│  tests/       30 suites, 175 tests passing                                 │
│  bindings/    pybind11 bindings (BUILD_BINDINGS=OFF by default)            │
│                                                                            │
│  PERF (measured): 100K candles append ~122ms, range query ~114ms,          │
│  H1 aggregation of 100K 5m candles ~95ms                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key observation:** The Python and C++ stacks are two parallel implementations with a **deliberate seam** (ABC interfaces + backend injection) but **zero connection between them today**. The C++ engine is complete and tested; Python never calls it.

---

## 2. Existing Components Assessment

### 2.1 Mature (production-quality, tested)

| Component | Location | Assessment |
|---|---|---|
| Deterministic object model | `core/base_object.py`, `core/identity.py` | Solid. UUID5 content-addressed IDs, SHA-256 hashing, immutable lifecycle, audit trail. Every object inherits this. |
| Object lifecycle | `core/lifecycle.py` | 24 stage enum, transition log, terminal-state guards. Well-designed. |
| Validation rules | `validation/rules.py` + `validators.py` | 14 typed validators, deterministic, registry-driven. Gap: only 4 rule functions fully implemented (observation/evidence/hypothesis/scenario); the rest are dict descriptions + validator classes. |
| Research object graph | `objects/` (17 modules) | ~50 object types, consistent to_dict/from_dict pattern. Heavy but coherent. |
| SQLite persistence | `storage/repository.py` | OBJECT_REGISTRY covers object-layer types; audit-chain verify endpoint exists. |
| Research pipeline | `pipeline/pipeline.py` | 975-line deterministic coordinator; every mutation writes an AuditEntry. Matches Article VII. |
| Statistics (Python) | `quant_engine/statistics.py` | mean/var/std/rolling vol/skew/kurtosis/z/returns calc. Version-gated (CALCULATION_V1). Pure Python, no numpy. |
| Metrics (Python) | `quant_engine/metrics.py` | Sharpe/Sortino/Calmar/profit factor/max drawdown/downside dev. Version-gated. |
| Performance analytics (Python) | `quant_engine/performance.py` | win rate, streaks, distribution analysis. Research-only (no signals). |
| C++ core engine | `cpp_quant_engine/core/`, `market/`, `statistics/`, `simulation/`, `backtest/` | 175 tests. Includes a complete backtest engine (TradeBook/BacktestEngine/PerformanceReport). |
| C++ Market Data Engine | `cpp_quant_engine/include/quant/market/*` | Candle/TimeIndex/OHLCVContainer/DataLoader/TimeframeAggregator/HistoricalIterator. Proven performance. |

### 2.2 Scaffolded / Stubbed (structural but not functional)

| Component | Location | Gap |
|---|---|---|
| Experiment runner | `experiments/runner.py` | `_execute_simulation()` returns **seeded random metrics** (runner.py:352-362). `run_walk_forward`/`run_monte_carlo` loop scaffolding only; windows do not slice a time series. |
| Experiment → data link | `experiments/contracts.py` DatasetConfig | `source` is an arbitrary string. No dataset registry, no loader, no schema. The runner ignores the dataset argument entirely. |
| Statistical significance | `experiments/validation.py` | Only a hardcoded z-critical map {0.01,0.05,0.10}; no t-test, no p-value from distributions, no confidence-interval validation. |
| Market memory matching | `market_memory/matcher.py`, `similarity.py` | Present and tested, but fed only by hand-constructed snapshots — no automated ingestion from market data. |
| API | `interfaces/api.py` | 3 endpoints; no experiment/quant endpoints. |
| C++ bindings | `cpp_quant_engine/bindings/` | CMakeLists present, `BUILD_BINDINGS` default OFF. Never built. |

### 2.3 Foundational but fragile

- `storage/repository.py` imports object-layer types only. **`experiments/` and `quant_engine/` objects are NOT in OBJECT_REGISTRY** — experiments cannot be persisted through the main repository. `market_memory` uses a separate, parallel SQLite table schema.
- `market_memory/repository.py:96` uses deprecated `datetime.utcnow()`.
- No type-checking config visible (no `py.typed`, no mypy/pyright config) despite heavy typing annotations.

---

## 3. Missing Components

Ordered by criticality for the master roadmap:

| # | Missing component | Why it blocks the roadmap |
|---|---|---|
| M1 | **Python market data layer (`researchos/data_engine/`)** — OHLCV candle model, timeframe model, CSV loader, validator, SQLite-backed repository, historical iterator | Nothing in Python can currently load, validate, or store actual price data. Every downstream phase (connectors, datasets, backtesting, experiments) consumes this. |
| M2 | **Dataset registry / versioning** — content-addressed dataset IDs, dataset_version, schema fingerprint | SimulationRequest/Experiment already reference `dataset_reference + dataset_version` but nothing implements them. ResearchOS determinism guarantees are void without immutable, hashed datasets. |
| M3 | **Real backtesting engine (Python)** — fill model, order/position book, commission/slippage/spread model, OHLCV bar iterator over a dataset | BaseExperimentRunner is random-number scaffolding. Phase 4 cannot begin. |
| M4 | **Strategy/indicator library** — deterministic technical/statistical indicator functions (Python) | Features for market memory exist (`features.py`) but no canonical, versioned indicator set for experiments. |
| M5 | **Connectors (MT5 / TradingView / CSV)** | Phase 2. Both are absent. |
| M6 | **Experiment & market-memory persistence in main repository** | Object lifecycle is defined but not storable through `storage/repository.py`. |
| M7 | **C++ ↔ Python bridge (pybind11, active)** | The seam exists on both sides (`set_backend()`, `AbstractExperimentRunner`) but no compiled module. Phase 8. |
| M8 | **Statistical test library** — t-test, p-value computation, bootstrap CI, walk-forward robustness tests | `ExperimentValidation` needs real statistical machinery for Phase 5/6. |
| M9 | **Concurrency** — parallel Monte Carlo / multi-window execution | Backtest and MC will be serial in Python otherwise. |

---

## 4. Recommended Implementation Order

Driven by dependency: nothing computes until data exists; nothing backtests until computation exists; nothing accelerates until both exist and are proven.

| Step | Deliverable | Depends on | Notes |
|---|---|---|---|
| 1 | `researchos/data_engine/` — candle/timeframe models, loader, validator, repository, iterator (mirror the proven C++ design) | — | Unblocks M1/M2. Reference: `cpp_quant_engine/include/quant/market/*`. |
| 2 | Dataset registry: content-addressed dataset ID, version hash, schema fingerprint | Step 1 | Wire `DatasetConfig` / `SimulationRequest.dataset_reference` to real dataset IDs. |
| 3 | Wire connectors: CSV first (guaranteed deterministic), MT5/TradingView second | Step 1 | CSV gives immediate deterministic test fixtures; live connectors come after. |
| 4 | Python backtest engine: bar iterator → order/position book → fills (OHLCV, slippage, commission) → equity curve | Steps 1-2 | Replace `BaseExperimentRunner._execute_simulation` RNG with real computation. |
| 5 | Experiment runner against real datasets: single run → walk-forward → Monte Carlo | Steps 2, 4 | Complete Phase 5. |
| 6 | Statistical test library + `ExperimentValidation` upgrade | Step 5 | Phase 6. |
| 7 | Persist experiments + market memory in main SQLite repository | Step 5 | Phase 7 unification. |
| 8 | Build C++ bindings; CppQuantBackend + CppExperimentRunner | Steps 4-5 | Phase 8. Keep Python as reference; add equivalence tests (Python vs C++ bit-identical results). |
| 9 | Real-time pipeline + production hardening | All | Phases 9-10. |

---

## 5. MT5 Integration Plan

**Constraint:** ingest historical data only. No orders, no execution — aligns with the "research only" constitution.

1. **Interface:** `researchos/data_engine/connectors/base.py` — `DataSourceConnector` ABC with `fetch_candles(symbol, timeframe, start, end) -> List[Candle]`, `list_symbols()`, `schema_version()`.
2. **Adapter:** `MTAConnector` using the `MetaTrader5` Python package (`metatrader5` / `MetaTrader5.copy_rates_range`). Maps MT5 timeframe enums (`TIMEFRAME_M5`, `TIMEFRAME_H1`, …) to the canonical `data_engine` timeframe enum (which must match the C++ `Timeframe` enum values).
3. **Normalisation:** MT5 candles → canonical Candle (open/high/low/close/volume, UTC timestamps, asset string, dataset_source = `"mt5://SYMBOL/TIMEFRAME"`).
4. **Ingestion pipeline:** `fetch → validate (data_engine.validator) → save to SQLite dataset → register in DatasetRegistry with content hash`.
5. **Determinism guard:** each fetch records `dataset_version` = hash of (schema + source + range + retrieval params). Re-fetch of the same range with the same params must produce the identical dataset ID, else a new version.
6. **Testing:** no live MT5 in CI — fixture-based adapter tests using recorded CSV dumps of `copy_rates_range` output.
7. **Risk:** MT5 terminal must be running with an active account for live data; document that limitation in the connector docstring.

---

## 6. TradingView Integration Plan

**Constraint:** data ingestion only.

1. **Chosen channel (recommended): CSV/JSON export from TradingView charts + `TradingView Webhooks` only for future real-time alerts — no live streaming yet.** There is no official public candles REST API; scraping is fragile and violates ToS.
2. **Adapter A — File import:** `TradingViewCSVConnector` parses TradingView's "Export chart data" CSV into canonical candles (TradingView exports UTC timestamps, OHLCV). Reuses the same ingestion pipeline as MT5.
3. **Adapter B — Webhook ingestion (Phase 9 real-time):** FastAPI `/webhooks/tradingview` endpoint validates HMAC/secret, accepts alert payload, converts to a `MarketEvent`/candle append, routes to the real-time pipeline. Research-only recording, no trade actions.
4. **Unified dataset_source convention:** `"tv://SYMBOL/TIMEFRAME"` and `"mt5://SYMBOL/TIMEFRAME"` are distinct dataset sources, which `market_memory/repository.py` already tracks via `dataset_sources`.
5. **Testing:** fixture-based; golden CSV files checked into `tests/fixtures/`.

---

## 7. C++ Acceleration Plan

The seam is already designed. This plan activates it.

1. **Build the bindings:** enable `BUILD_BINDINGS=ON` in `cpp_quant_engine/bindings/CMakeLists.txt`. Module name `quant_engine_cpp`.
2. **Expose first:** `QuantEngine` + `MarketDataEngine` + statistics + backtest `PerformanceReport`. These map 1:1 to `QuantComputationInterface` methods.
3. **Python side:** implement `CppQuantBackend(QuantComputationInterface)` that calls the pybind11 module; inject via `HistoricalSimulationEngine.set_backend()` (simulation.py:68). Implement `CppExperimentRunner(AbstractExperimentRunner)` for the experiments layer.
4. **Equivalence contract (critical):** add a test matrix asserting **Python backend and C++ backend produce identical results** for identical inputs (same seeded RNG, same formulas, same rounding). The C++ engine must replicate Python's rounding and formula choices bit-for-bit, or the determinism guarantee is violated. CALCULATION_V1 must mean one thing in both languages.
5. **Hot paths to accelerate:** OHLCV loading + timeframe aggregation (already ~95ms for 100K 5m candles → H1), rolling volatility/skew/kurtosis over large windows, Monte Carlo path generation (GBM/OU/JumpDiff/Heston already implemented), walk-forward loops.
6. **Build/CI:** keep MSVC/CMake 4.4 pipeline used for the C++ engine; add a CI step that builds bindings + runs Python equivalence tests.
7. **Fallback:** keep `PythonQuantBackend` as the reference implementation forever — C++ is an accelerator, not a replacement.

---

## 8. Backtesting Engine Roadmap

C++ has `BacktestEngine`/`TradeBook`/`PerformanceReport` already (proven). The Python side is stubbed. Roadmap:

1. **Bar-level event loop (Python):** iterate a `data_engine` dataset via the historical iterator; emit `bar_open/bar_close` events.
2. **Order/position book:** deterministic orders (`market`, `limit`), fills against OHLCV (`open` for market, gap-safe limit logic), position sizing, partial fills.
3. **Cost model:** spread, commission (per-lot/per-value), slippage (fixed or volume-scaled) — all parameters versioned.
4. **Equity curve + metrics:** reuse `quant_engine/metrics.py` (already correct) and C++ `PerformanceReport` for cross-checking.
5. **Backtest container:** `BacktestResult` (trades, equity curve, metrics, per-bar ledger) as a `BaseObject` so it gains IDs, lifecycle, and hashing for free.
6. **Experiment runner rewrite:** `BaseExperimentRunner._execute_simulation` switches from RNG scaffolding to real backtest execution; `run_walk_forward` slices datasets correctly.
7. **Validation hooks:** `ExperimentValidation.validate_statistical_significance` gains bootstrap/t-test from Step 6 of §4.
8. **Determinism tests:** same experiment + same dataset ⇒ identical result_hash, across runs and across backends.

---

## 9. Risks and Architectural Warnings

1. **HIGH — RNG-based fake results are dangerous.** `BaseExperimentRunner` currently produces plausible-looking metrics from `random.uniform` (runner.py:352-362). If treated as real, this corrupts every downstream validation/learning object. It is scaffolding, but nothing in the codebase marks it as non-production except docstrings. **Mitigation:** runner must refuse to run against a non-registered dataset (dependency on §4 Step 2) and always record `computation_backend = "python_reference"` in statistics (already does).
2. **HIGH — Dual-language determinism drift.** Python and C++ implement the same formulas independently. Without an equivalence test matrix, CALCULATION_V1 will silently diverge. **Mitigation:** §7.4 equivalence contract before any C++ backend goes live.
3. **MEDIUM — Parallel persistence schemas.** `storage/repository.py` (object-layer), `market_memory/repository.py` (own SQLite table), and future `data_engine` repository are three separate storage worlds. **Mitigation:** unify in Phase 7 (§4 Step 7); define a single dataset_id convention now.
4. **MEDIUM — Dataset immutability not enforced.** Nothing stops code from mutating a loaded dataset and rerunning an experiment, breaking reproducibility. **Mitigation:** immutable candle storage + content-addressed dataset_version from day one.
5. **LOW — Deprecated `datetime.utcnow()`** in `market_memory/repository.py:96`; will break when Python removes it.
6. **LOW — Type-checking not enforced** despite full annotations; pyright/mypy would catch the `researchos/experiments/__init__.py:65` indentation anomaly (`"BaseExperimentRunner"` at wrong indent level) and latent type errors.
7. **CONSTRAINT — decision_engine/ is out of scope** for this architecture and must not be coupled into the quant computation layer. The quant layer must expose data/metrics only, never trade decisions.

---

## Executive Summary

- **Infrastructure maturity: ~35%.**
  - Foundation (object model, lifecycle, validation, research pipeline, SQLite object storage): **80%**.
  - Quant computation (Python statistics/metrics/performance + complete C++ engine): **60%**.
  - Experiment framework (objects complete, execution stubbed): **40%**.
  - Market data ingestion & dataset management: **0%**.
  - Backtesting (C++ engine exists; Python execution stubbed; no strategy/fill/cost layer): **25%**.
  - Connectors (MT5/TradingView): **0%**.
  - C++ acceleration bridge (seam designed, bindings never built): **10%**.
  - Real-time / production: **0%**.

- **Biggest bottleneck:** the **missing Python market data layer + dataset registry**. Every quant activity (experiments, backtesting, market memory, connectors) is currently disconnected from real data — the experiment runner computes against `random.uniform`, not against prices. Everything downstream is blocked by this single missing layer.

- **Recommended Phase 1 implementation:** build **`researchos/data_engine/`** in Python: `models.py` (Candle, Timeframe — mirroring the proven C++ `candle.h`/`time_index.h`), `contracts.py`, `validator.py`, `loader.py` (CSV), `repository.py` (SQLite, immutable, content-addressed), `historical_iterator.py`, `tests/`. This directly reuses the C++ market data engine as a design reference, unblocks the dataset registry (M2), gives the experiment runner real data (M3), and provides the foundation every remaining phase consumes.
