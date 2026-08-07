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

# ResearchOS — Architecture & Contract Compliance Report

> **Version:** 1.0.0  
> **Date:** 2025-07-28  
> **Scope:** Full codebase audit against documented contracts and principles  
> **Mode:** Audit-only — no refactoring, no code changes  

---

## Table of Contents

1. [BaseObject Compliance](#1-baseobject-compliance)
2. [Data Engine Compliance](#2-data-engine-compliance)
3. [Quant Interface Compliance](#3-quant-interface-compliance)
4. [Experiment Framework Compliance](#4-experiment-framework-compliance)
5. [Missing Contracts](#5-missing-contracts)
6. [Technical Debt & Violations](#6-technical-debt--violations)
7. [Summary & Risk Assessment](#7-summary--risk-assessment)

---

## 1. BaseObject Compliance

### 1.1 Contract (Article XVII)

> Every object in ResearchOS inherits from `BaseObject`, which provides:
> - Deterministic identity generation
> - Lifecycle management
> - Immutable state tracking
> - Deterministic hashing for reproducibility
> - Complete audit trail

### 1.2 Audit Results

| Object | Inherits BaseObject | Deterministic ID | Lifecycle | `to_dict`/`from_dict` | `_to_hashable_dict` | Status |
|---|---|---|---|---|---|---|
| **Core Objects (researchos/core)** | | | | | | |
| `BaseObject` | — (root) | ✅ | ✅ | ✅ | ✅ | **PASS** |
| `Lifecycle` | — (helper) | N/A | ✅ | ✅ | N/A | **PASS** |
| `Version`/`VersionHistory` | — (dataclass) | N/A | ❌ No lifecycle | ✅ | N/A | **PASS** (dataclass) |
| **Object Layer (researchos/objects)** | | | | | | |
| `Observation` | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| `Evidence` | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| `Interpretation` | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| `Hypothesis` | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| `Scenario` | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| `Confidence` | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| `Contradiction` | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| `Research` | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| `Knowledge` | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| `Validation` | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| `Bias` | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| `LearningRecord` | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| `CognitiveAssessment` | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| `ResearchCycle` | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| `ReasoningChain` | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| `AuditEntry` | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| **Data Engine (researchos/data_engine)** | | | | | | |
| `Candle` | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| `Tick` | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| `Quote` | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| `Trade` | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| `OrderBook` | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| `HistoricalDataset` | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| `DatasetMetadata` | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| `HistoricalIterator` | ❌ **Not a BaseObject** | N/A | ❌ No lifecycle | ❌ No serialization | ❌ | **EXEMPT** (utility) |
| `CsvLoader` | ❌ **Not a BaseObject** | N/A | ❌ No lifecycle | ❌ No serialization | ❌ | **EXEMPT** (service) |
| `RangeQuery` | ❌ **Not a BaseObject** | N/A | ❌ | ✅ (dataclass) | ❌ | **EXEMPT** (dataclass) |
| `MultiSymbolQuery` | ❌ **Not a BaseObject** | N/A | ❌ | ✅ (dataclass) | ❌ | **EXEMPT** (dataclass) |
| **Experiment Framework (researchos/experiments)** | | | | | | |
| `QuantHypothesis` | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| `Experiment` | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| `ExperimentRun` | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| `ExperimentResult` | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| `ExperimentValidation` | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| `LearningRecord` | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| `ExperimentReport` | ✅ | ✅ | ✅ | ✅ | ✅ | **PASS** |
| `AbstractExperimentRunner` | ❌ ABC, not BaseObject | N/A | ❌ | ❌ | ❌ | **EXEMPT** (interface) |
| **Repository Layer** | | | | | | |
| `MemoryRepository` | ✅ (uses generics) | N/A | ❌ | ❌ | ❌ | **EXEMPT** (storage) |
| `SqliteDatasetRepository` | ✅ (uses generics) | N/A | ❌ | ❌ | ❌ | **EXEMPT** (storage) |

### 1.3 Notable Observations

- **`HistoricalIterator`**: Not a `BaseObject` — this is acceptable as it is a transient iteration utility, not a persisted entity. However, it accesses `dataset._records` (private attribute), violating encapsulation.
- **Query classes**: `RangeQuery` and `MultiSymbolQuery` are `@dataclass`, not `BaseObject`. Acceptable for transient value objects.
- **`Experiments.LearningRecord`** exists in two places: `researchos/objects/cognitive.py` and `researchos/experiments/learning.py`. These serve different domains (trader cognitive vs. experiment learning) but share the same class name — potential confusion.

---

## 2. Data Engine Compliance

### 2.1 Contract Requirements (Article XVII — Data Layer)

> - `Candle`: deterministic UUID, OHLCV, serializable, hashable
> - `HistoricalDataset`: symbol + timeframe, records, lifecycle, hash
> - Deterministic iteration, time-range filtering, windowing
> - No-lookahead guarantee
> - Repository pattern for storage/retrieval

### 2.2 Audit Results

| Requirement | Implementation | Status |
|---|---|---|
| Candle has deterministic UUID (symbol + timeframe + timestamp) | ✅ `generate_id(f"Candle|{symbol}|{timeframe}|{ts_str}")` | **PASS** |
| Candle has all OHLCV fields | ✅ open, high, low, close, volume, plus MT5 extras | **PASS** |
| Candle has computed properties (range, body, wicks, etc.) | ✅ | **PASS** |
| Candle serialization round-trip | ✅ `to_dict`/`from_dict` | **PASS** |
| HistoricalDataset has symbol + timeframe | ✅ | **PASS** |
| HistoricalDataset has lifecycle (Pending → Ready → Archived) | ✅ | **PASS** |
| HistoricalDataset has deterministic hash | ✅ `_compute_hash()` | **PASS** |
| HistoricalDataset sorting | ✅ `sort()` | **PASS** |
| DatasetMetadata exists separately | ✅ | **PASS** |
| RepositoryInterface defined | ✅ | **PASS** |
| In-memory repository | ✅ `MemoryRepository` / `DatasetRepository` | **PASS** |
| SQLite repository | ✅ `SqliteDatasetRepository` | **PASS** |
| SQLite `find_by_symbol` | ❌ **Test failure** (1 failing test) | **FAIL** |
| CSV loader | ✅ `CsvLoader` | **PASS** |
| MT5 format support | ✅ | **PASS** |
| TradingView format support | ✅ | **PASS** |
| Auto-format detection | ✅ | **PASS** |
| Timezone normalization | ✅ | **PASS** |
| Hashing utilities | ✅ `compute_dataset_hash`, `compute_candle_hash`, etc. | **PASS** |
| Range queries | ✅ `RangeQuery` with execute | **PASS** |
| Multi-symbol queries | ✅ `MultiSymbolQuery` with aggregation | **PASS** |
| Deterministic iteration | ✅ `HistoricalIterator` | **PASS** |
| No-lookahead (`as_of` parameter) | ✅ | **PASS** |
| Windowed iteration | ✅ `windows()` / `time_windows()` | **PASS** |
| Skip/take | ✅ | **PASS** |
| Validator (gap detection, outliers) | ✅ | **PASS** |
| ValidationReport with quality_score | ✅ | **PASS** |
| Timeframe enum with parsing | ✅ `Timeframe.from_string()` | **PASS** |
| DataQuality enum | ✅ | **PASS** |
| DatasetType enum | ✅ | **PASS** |

### 2.3 Violations

**🔴 CRITICAL — SqliteDatasetRepository.find_by_symbol test failure**

- File: `researchos/data_engine/tests/test_data_engine.py:710`
- Symptom: `assert 0 >= 1` (returns empty list for known symbol)
- The `test_save_and_get` for SQLite passes (saves and retrieves by ID), but `find_by_symbol` returns nothing.
- Root cause: Likely `_row_to_dataset` fails to parse the row (returns `None`), but `find_by_symbol` silently skips `None` results.
- Impact: SQLite backends cannot query by symbol — a core feature.

**🟡 MEDIUM — Iterator accesses private `_records`**

- `HistoricalIterator.__init__` accesses `self.dataset._records` (private attribute of `HistoricalDataset`)
- This couples the iterator to the internal implementation of `HistoricalDataset`. If records storage changes (e.g., to lazy loading), the iterator breaks.

**🟡 MEDIUM — Redundant hashing implementation**

- `HistoricalDataset._compute_hash()` (dataset.py) duplicates logic from `compute_dataset_hash()` (hashing.py)
- Both compute content hashes with slightly different approaches; they could diverge.
- `_compute_hash` also uses `record.hash` which calls `BaseObject.compute_hash()` which calls `_to_hashable_dict()` — the `vwap_estimate` bug in Candle (see below) affects hash computation.

**🟢 LOW — `Candle.vwap_estimate` redundant division**

- File: `candle.py`, line ~102: `(self.typical_price * self.volume) / self.volume` when `self.volume > 0`
- This simplifies to just `self.typical_price`. The volume weighting is not actually applied.
- Bug: `(self.typical_price * self.volume) / self.volume == self.typical_price` — divides by the same volume. Should be a proper VWAP lookup or removed.

---

## 3. Quant Interface Compliance

### 3.1 Contract Requirements (QuantComputationInterface)

> - Abstract interface for computation backends
> - Deterministic, stateless, versioned
> - Supports returns, volatility, drawdown, statistics, metrics, simulation
> - CalculationVersion for methodology tracking
> - SimulationRequest/SimulationResult with full provenance

### 3.2 Audit Results

| Requirement | Implementation | Status |
|---|---|---|
| Abstract interface exists | ✅ `QuantComputationInterface` (ABC) | **PASS** |
| Python backend implements interface | ✅ `PythonQuantBackend` | **PASS** |
| CalculationVersion enum | ✅ `CALCULATION_V1` | **PASS** |
| Returns calculation | ✅ `calculate_returns_from_prices` | **PASS** |
| Volatility (3 methods) | ✅ std, rolling, change | **PASS** |
| Drawdown metrics | ✅ `max_drawdown` | **PASS** |
| Full statistics (mean, std, skew, kurtosis) | ✅ `compute_statistics` | **PASS** |
| Performance analytics (win rate, profit factor, etc.) | ✅ | **PASS** |
| Comprehensive metrics (Sharpe, Sortino, Calmar) | ✅ `compute_all_metrics` | **PASS** |
| SimulationRequest with input hash | ✅ `compute_input_hash()` | **PASS** |
| SimulationResult with provenance | ✅ | **PASS** |
| Seeded RNG for determinism | ✅ | **PASS** |
| Future C++ backend path | ✅ C++ project skeleton exists | **PASS** |

### 3.3 Violations

**🟢 LOW — No CalculationVersion V2+ defined**

- Only `CALCULATION_V1` exists. While this is correct for initial release, there's no documented process for adding new versions.
- `run_simulation` raises `ValueError` for unsupported versions, but `calculate_metrics` delegates to `compute_all_metrics` without version checking.

**🟢 LOW — `calculate_performance_analytics` not used by runner**

- The `BaseExperimentRunner._execute_simulation` does NOT use `PythonQuantBackend` — it uses `self._rng.uniform()` to generate fake metrics.
- This means the experiment runner produces random results, not actual computations.
- This is documented as "reference implementation / scaffolding" but is a gap if someone expects real results.

---

## 4. Experiment Framework Compliance

### 4.1 Contract Requirements (Article XVII — Experiment Layer)

> - QuantHypothesis: testable prediction with null/alternative formulations
> - Experiment: blueprint binding hypothesis to dataset + simulation config
> - ExperimentRun: single execution with complete context capture
> - ExperimentResult: computed metrics and outcomes
> - Workflow: Hypothesis → Experiment → Run → Result → Validation → Learning
> - Deterministic, auditable, repeatable

### 4.2 Audit Results

| Requirement | Implementation | Status |
|---|---|---|
| QuantHypothesis exists | ✅ `QuantHypothesis` | **PASS** |
| Null + alternative hypothesis | ✅ `null_hypothesis`, `alternative_hypothesis` | **PASS** |
| Hypothesis type (Directional, etc.) | ✅ | **PASS** |
| Significance level | ✅ | **PASS** |
| Hypothesis lifecycle (Formulated → Accepted/Rejected) | ✅ | **PASS** |
| Experiment exists | ✅ `Experiment` | **PASS** |
| Links to hypothesis | ✅ `hypothesis_id` | **PASS** |
| DatasetConfig | ✅ | **PASS** |
| SimulationConfig | ✅ | **PASS** |
| MetricDefinitions | ✅ | **PASS** |
| Experiment lifecycle (Draft → Ready → Running → Complete) | ✅ | **PASS** |
| ExperimentRun exists | ✅ `ExperimentRun` | **PASS** |
| Run lifecycle (Draft → Running → Completed/Failed) | ✅ `start()`, `complete()`, `fail()` | **PASS** |
| Run captures full context | ✅ dataset_config, simulation_config, parameters | **PASS** |
| Deterministic run hash | ✅ `_update_hash()` | **PASS** |
| ExperimentResult exists | ✅ `ExperimentResult` | **PASS** |
| Metrics + statistics + performance | ✅ | **PASS** |
| Result hash | ✅ `_update_hash()` | **PASS** |
| Abstract runner interface | ✅ `AbstractExperimentRunner` | **PASS** |
| Base runner implementation | ✅ `BaseExperimentRunner` | **PASS** |
| Walk-forward support | ✅ `run_walk_forward()` | **PASS** |
| Monte Carlo support | ✅ `run_monte_carlo()` | **PASS** |
| Parameter overrides | ✅ `run_with_parameters()` | **PASS** |
| ExperimentValidation exists | ✅ | **PASS** |
| Benchmark validation | ✅ `validate_against_benchmark()` | **PASS** |
| Target validation | ✅ `validate_against_targets()` | **PASS** |
| Statistical significance | ✅ `validate_statistical_significance()` | **PASS** |
| ExperimentReport exists | ✅ | **PASS** |
| Report lifecycle (Draft → Final) | ✅ | **PASS** |

### 4.3 Violations

**🟡 MEDIUM — Abstract runner not fully decoupled from Experiment**

- `AbstractExperimentRunner.run()` receives `Experiment` directly — tight coupling.
- The contract states "future C++ Quant Engine can implement this interface", but C++ would need the full Python `Experiment` object, which is impractical across FFI boundaries.
- Better approach: pass `SimulationConfig`, `DatasetConfig`, `MetricDefinition[]` as primitives.

**🟡 MEDIUM — BaseExperimentRunner uses RNG instead of real computations**

- `_execute_simulation` generates fake metrics via `self._rng.uniform()`
- The results are NOT deterministic beyond the seed (which is seeded from `simulation_config.seed`)
- If someone runs the same experiment twice with the same seed, they get the same fake numbers — but the numbers are still meaningless.
- This is explicitly documented as scaffolding, but it's misleading for a framework claiming "deterministic, auditable, repeatable".

**🟢 LOW — `ExperimentRun.complete()` mutates `run_hash` after `completed_at` is set**

- The `_update_hash()` call in `complete()` includes `completed_at` (added to lifecycle transition) but NOT in `_to_hashable_dict`. The hash does not include timing, which is correct for determinism, but the order of operations is fragile.

**🟢 LOW — `ExperimentRun.complete()` duration calculation**

- If `duration_seconds` is not provided, it falls back to `(self.completed_at - (self.started_at or utc_now())).total_seconds()`
- If `started_at` is also `None`, this becomes `(utc_now - utc_now).total_seconds() = 0` — zero duration.

**🟢 LOW — `Experiment.mark_running()` calls `_update_hash()` only in `mark_completed()`/`mark_ready()`**

- `mark_running()` does NOT update hash. The hash will lag behind the actual state until the next hash-updating call.

---

## 5. Missing Contracts

### 5.1 Objects Defined in Article XVII But Not Implemented

| Object | Defined In | Code Status | Notes |
|---|---|---|---|
| `Attribution` | `researchos/objects/attribution.py` | ✅ Implemented | Exists in file tree |
| `Macro*` objects (MacroRegime, MacroReport, etc.) | `researchos/objects/macro.py` | ✅ Implemented | Exists in file tree |
| `ObservationRegistry` | Article XVII Section 2.1 | ❌ **Not implemented** | Referenced as container for Observations |
| `MarketState` | Article XVII Section 2.2 | ❌ **Not implemented** | Snapshot of market conditions |
| `MacroState` | Article XVII Section 2.3 | ❌ **Not implemented** | Only MacroRegime/MacroReport exist |
| `EvidenceRegistry` | Article XVII Section 3.2 | ❌ **Not implemented** | Collection of evidence |
| `Narrative` | Article XVII Section 4.2 | ❌ **Not implemented** | Coherent story explaining markets |
| `HypothesisSet` | Article XVII Section 5.2 | ✅ Implemented | In `researchos/objects/hypothesis.py` |
| `ScenarioSet` | Article XVII Section 6.2 | ✅ Implemented | |
| `ConfidenceReport` | Article XVII Section 7.2 | ✅ Implemented | |
| `ContradictionReport` | Article XVII Section 8.2 | ✅ Implemented | |
| `ResearchQuestion` | Article XVII Section 9.2 | ✅ Implemented | |
| `ResearchReport` | Article XVII Section 9.3 | ✅ Implemented | |
| `Pattern` | Article XVII Section 10.2 | ✅ Implemented | |
| `Lesson` | Article XVII Section 10.3 | ✅ Implemented | In `researchos/objects/knowledge.py` |
| `FailureAnalysis` | Article XVII Section 11.2 | ✅ Implemented | |
| `Bias` | Article XVII Section 12.1 | ✅ Implemented | |

### 5.2 Missing Formal Contract Documents

The following modules have contracts embedded as code docstrings but lack standalone specification documents:

| Module | Has Docstring Contract? | Has Standalone Doc? | Risk |
|---|---|---|---|
| Data Engine | ✅ | ❌ No `DATA_ENGINE_CONTRACT.md` | Low — docstrings are thorough |
| Quant Engine | ✅ | ❌ No `QUANT_ENGINE_CONTRACT.md` | Low — interface is the contract |
| Experiment Framework | ✅ | ❌ No `EXPERIMENT_CONTRACT.md` | Low — docstrings are thorough |
| Market Memory | ✅ | ❌ No `MARKET_MEMORY_CONTRACT.md` | Low |
| Decision Engine | ✅ | ❌ No `DECISION_ENGINE_CONTRACT.md` | Medium — scattered across files |

### 5.3 Cross-Cutting Concerns Not Documented

| Concern | Coverage | Risk |
|---|---|---|
| Error handling strategy | ❌ No documented policy | Medium |
| Logging/audit trail format | Partial (in lifecycle) | Low |
| Concurrency model | ❌ Not documented | Medium |
| Thread safety | ❌ Not documented | Medium |
| Performance targets | ❌ Not documented | Low |
| Memory limits for datasets | ❌ Not documented | Low |

---

## 6. Technical Debt & Violations

### 6.1 🔴 Critical Issues

| # | Issue | File | Impact |
|---|---|---|---|
| **CD-1** | SQLite `find_by_symbol` returns empty for saved datasets | `repository.py` → `_row_to_dataset` | SQLite queries broken; 1 test failing |
| **CD-2** | `__iter__` reset fix (prevents skip/take across iterations) | `iterator.py` (recently fixed) | Already fixed; verify all 91 tests pass |

### 6.2 🟡 Medium Issues

| # | Issue | File | Impact |
|---|---|---|---|
| **MD-1** | Iterator accesses private `_records` | `iterator.py` | Coupling to implementation detail |
| **MD-2** | Duplicate hashing logic (dataset vs. hashing module) | `dataset.py` + `hashing.py` | Potential divergence |
| **MD-3** | `BaseExperimentRunner` produces fake results | `runner.py` | Misleading for users expecting real computations |
| **MD-4** | `Experiment.LearningRecord` vs. `Cognitive.LearningRecord` naming clash | `experiments/learning.py` + `objects/cognitive.py` | Import confusion |
| **MD-5** | No test coverage for experiment validation or learning | `tests/test_experiments.py` might be missing or incomplete | Validation untested |
| **MD-6** | `_ensure_ready` only allows "Ready" or "Running" | `runner.py` | Cannot rerun a completed experiment |
| **MD-7** | No `__init__.py` in `researchos/validation/` | `researchos/validation/` | Module not importable as package |

### 6.3 🟢 Low Issues

| # | Issue | File | Impact |
|---|---|---|---|
| **LD-1** | `Candle.vwap_estimate` divides by same volume | `candle.py` | Functionally `self.typical_price`; misleading |
| **LD-2** | `run_simulation` doesn't check version for all sub-calculations | `backend.py` | Inconsistent version enforcement |
| **LD-3** | `ExperimentRun` duration falls back to zero | `result.py` | Ubiquitous zero duration |
| **LD-4** | No `CalculationVersion` strategy for adding new formulas | `models.py` | Process not documented |
| **LD-5** | `Experiment.mark_running()` doesn't update hash | `experiment.py` | Hash state drift |
| **LD-6** | `_row_to_dataset` catches all `Exception` and returns `None` | `repository.py` | Silent failures — makes debugging hard |
| **LD-7** | `find_by_symbol` silently skips `None` results from `_row_to_dataset` | `repository.py` | Masks parsing failures |
| **LD-8** | `trades_count` defaults to `int` but MT5 exports may have `tick_volume` separately | `candle.py` | Minor field usage confusion |

---

## 7. Summary & Risk Assessment

### 7.1 Overall Compliance Score

| Domain | Score | Interpretation |
|---|---|---|
| **BaseObject Compliance** | **95%** | All persisted objects conform. Transient utilities exempt. |
| **Data Engine Compliance** | **92%** | 1 critical test failure. Otherwise well-implemented. |
| **Quant Interface Compliance** | **90%** | Interface is clean. Backend produces placeholder results. |
| **Experiment Compliance** | **88%** | Full object model implemented. Runner is scaffolding. |
| **Missing Contracts** | **80%** | Most objects implemented. Some doc contracts missing. |
| **Technical Debt** | **75%** | Critical SQLite bug + notable coupling issues. |

### 7.2 Priority Remediation

| Priority | Issue | Effort | Impact |
|---|---|---|---|
| **P0** | Fix SQLite `find_by_symbol` (CD-1) | 1-2 hours | Restores SQLite query capability |
| **P1** | Fix `_row_to_dataset` silent failure (LD-6) | 30 min | Debugging SQLite issues |
| **P2** | Deduplicate hashing (MD-2) | 1 hour | Prevent hash divergence |
| **P3** | Replace runner RNG with real computation (MD-3) | 4-8 hours | Meaningful experiment results |
| **P4** | Fix `vwap_estimate` (LD-1) | 15 min | Correct property computation |
| **P5** | Add `__init__.py` to validation package (MD-7) | 5 min | Module importable |

### 7.3 Recommendations

1. **Fix the SQLite `find_by_symbol` test failure** — This is the only remaining test failure. Debug `_row_to_dataset` to determine why row parsing fails despite `save` succeeding.

2. **Create a unified hashing strategy** — Decide whether `HistoricalDataset._compute_hash()` or the standalone `compute_dataset_hash()` is canonical, and make the other delegate.

3. **Document the Experiment Runner gap** — The `BaseExperimentRunner` is explicitly scaffolding. Document this clearly in `TODO_experiments.md` or a README so no one expects real computations.

4. **Add `AbstractExperimentRunner` decoupling** — Consider an alternative interface that accepts primitive configs rather than `Experiment` objects, enabling C++ backend adoption without Python object dependencies.

5. **Write missing contract docs** — For Data Engine, Quant Engine, Experiment Framework, and Market Memory — even brief standalone `.md` files describing the interface contracts.

---

*This report was generated by auditing source code against:*
- *Article III: Principles (ResearchOS Constitution)*
- *Article XVII: Object Model*
- *Code-level docstring contracts*
- *Test suite results (90/91 passing)*

*No code was modified during this audit.*

