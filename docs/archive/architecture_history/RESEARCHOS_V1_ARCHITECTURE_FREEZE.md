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

# ResearchOS Version 1 — Architecture Freeze Specification

**Version:** 1.0.0 (Architecture Freeze)
**Baseline Commit:** `ad50c06` (pre-freeze) → `3f4510f` (freeze commit)
**Effective Date:** 2026-08-03
**Status:** FROZEN
**Classification:** Internal — Senior Architecture Board

---

## 1. System Purpose

ResearchOS is a **deterministic, explainable, scientific market research
platform** that produces institutional-quality research for human traders.
It is **NOT** an automated trading system — it never executes trades, sends
orders, or makes final trading decisions.

The platform applies the scientific method to market research: hypotheses are
formulated, tested against historical data through deterministic experiment
runs, and results are validated, evaluated, and tracked through a closed
feedback loop. Every output carries full provenance and can be reproduced
from identical inputs.

---

## 2. Layer Architecture (Version 1)

The frozen V1 core is organised into eight layers. Each layer depends only
on the layers below it (or on the shared Core Infrastructure). Cross-layer
dependencies must not skip adjacent layers.

```
┌─────────────────────────────────────────────────────────────────────┐
│  Orchestration Layer                                                │
│  (researchos/orchestration/, researchos/core/)                      │
├─────────────────────────────────────────────────────────────────────┤
│  Intelligence Layer                                                │
│  (researchos/intelligence/)                                         │
├─────────────────────────────────────────────────────────────────────┤
│  Evaluation Layer                                                │
│  (researchos/evaluation/)                                           │
├─────────────────────────────────────────────────────────────────────┤
│  Validation Layer                                                │
│  (researchos/experiments/validation.py,                           │
│   researchos/validation/)                                           │
├─────────────────────────────────────────────────────────────────────┤
│  Experiment Framework Layer                                         │
│  (researchos/experiments/)                                          │
│       │                   │             │              │           │
│  contracts.py  experiment.py  runner.py  result.py  hypothesis.py  │
├─────────────────────────────────────────────────────────────────────┤
│  Quant Engine Layer                                                │
│  (researchos/quant_engine/)                                         │
│       │                     │           │          │              │
│  interface.py  backend.py  models.py  statistics.py  metrics.py   │
├─────────────────────────────────────────────────────────────────────┤
│  Dataset Contract Layer                                             │
│  (researchos/data_engine/contracts.py,                             │
│   researchos/experiments/contracts.py)                             │
├─────────────────────────────────────────────────────────────────────┤
│  Data Layer                                                         │
│  (researchos/data_engine/)                                          │
│       │                  │           │       │       │           │
│  dataset.py  candle.py  loader.py  query.py  tick.py  validator.py  │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.1 Verified Computation Flow (Frozen Core)

The Experiment ↔ Quant Backend boundary that was validated for freeze is:

```
Data Layer
    ↓
Dataset / Historical Data Contract
    ↓
SimulationRequest  (models.py)
    ↓
QuantComputationInterface  (interface.py)
    ↓
PythonQuantBackend  (backend.py)
    ↓
SimulationResult  (models.py)
    ↓
ExperimentRunner  (runner.py)
    ↓
ExperimentResult  (experiments/result.py)
```

### 2.2 Layer Descriptions

#### Layer 1 — Data Layer
**Modules:** `researchos/data_engine/` (`dataset.py`, `candle.py`,
`loader.py`, `query.py`, `tick.py`, `quote.py`, `orderbook.py`,
`repository.py`, `validator.py`, `timezone.py`, `hashing.py`,
`iterator.py`, `metadata.py`, `statistics.py`, `trade.py`)

Provides raw historical market data and data-loading utilities. The Data
Layer produces `HistoricalDataset`, `Candle`, `Tick`, `Quote`, and `OrderBook`
objects. It has **no dependency** on the Quant Engine or Experiment Framework.

The Data Layer is the **only** layer that knows about file formats (CSV),
exchange protocols (MT5), and data-source specifics (Yahoo, Alpaca, Polygon).

**Entry point:** `DatasetConfig` from `experiments/contracts.py` specifies the
source, symbols, date range, and resolution. The Data Layer loads and
validates data into a contract that the Quant Layer normalizes.

#### Layer 2 — Dataset Contract Layer
**Modules:** `researchos/data_engine/contracts.py`,
`researchos/experiments/contracts.py`

Defines the shared vocabulary (enums, dataclasses) that flows between the
Data Layer and the Quant Layer:

- `DatasetConfig` — source, symbols, start/end dates, resolution, filters
- `SimulationConfig` — seed, initial_capital, commission, slippage,
  max_positions, parameters
- `Timeframe`, `DataSource`, `DataQuality`, `DatasetStatus`, `DatasetType`
- `CandleField`, `LoaderConfig`, `ValidationReport`

The contract is **asset-class generic** — `DatasetConfig.symbols` accepts
any list of symbol strings (e.g., `["XAU/USD"]`, `["EUR/USD", "GBP/USD"]`).

#### Layer 3 — Quant Engine Layer
**Modules:** `researchos/quant_engine/` (`backend.py`, `interface.py`,
`models.py`, `statistics.py`, `metrics.py`, `performance.py`,
`simulation.py`, `replay.py`, `execution.py`, `strategy.py`,
`econometrics/`, `technical/`, `fundamental/`, `portfolio/`, `probability/`,
`machine_learning/`, `models/`, `training/`, `validation/`)

**Owns all computation.** This is the sole authority for:
- Returns calculation (percentage, absolute, log)
- Volatility calculation (standard deviation, rolling, change)
- Drawdown calculation (max drawdown, recovery period, downside deviation)
- Statistics computation (mean, std, variance, skewness, kurtosis, etc.)
- Metrics computation (Sharpe, Sortino, Calmar, profit factor, etc.)
- Performance analytics (win rate, win/loss ratio, consecutive streaks)
- Dataset contract normalization (`PythonQuantBackend._extract_prices`)
- Backtest execution (ReplayEngine + ExecutionSimulationLayer)

**Key contracts:**
- `QuantComputationInterface` (`interface.py`) — abstract interface
  that all computation backends must implement
- `PythonQuantBackend` (`backend.py`) — reference implementation
  (pure Python, stdlib-only, stateless, deterministic)
- `SimulationRequest` / `SimulationResult` (`models.py`) — versioned
  computation request/response with deterministic hashing
- `CalculationVersion.CALCULATION_V1` — formula version identifier

**Future expansion:** A C++ backend (`cpp_quant_engine/`) can replace
`PythonQuantBackend` by implementing `QuantComputationInterface` without
any changes to upper layers.

#### Layer 4 — Experiment Framework Layer
**Modules:** `researchos/experiments/` (`runner.py`, `experiment.py`,
`result.py`, `contracts.py`, `hypothesis.py`, `learning.py`,
`reports.py`, `validation.py`)

Provides the orchestration framework for running experiments:

- `Experiment` — blueprint binding a hypothesis to a dataset and
  simulation configuration
- `ExperimentRunner` (`BaseExperimentRunner`) — orchestration-only; builds
  `SimulationRequest`, delegates computation to the Quant Engine, maps
  `SimulationResult` → `ExperimentResult`
- `ExperimentRun` — single execution with lifecycle tracking (Draft →
  Running → Completed/Failed)
- `ExperimentResult` — output container with metrics, statistics,
  performance, trades, signals, and provenance

**Critical boundary:** The Experiment Framework **NEVER**:
- Loads CSV files directly
- Parses OHLCV data
- Knows MT5/TradingView formats
- Contains financial calculation logic

The runner forwards the dataset contract **unchanged** to the Quant Engine
and packages the backend's output into `ExperimentResult`.

#### Layer 5 — Validation Layer
**Modules:** `researchos/experiments/validation.py`,
`researchos/validation/` (`validators.py`, `rules.py`, `prop_validator.py`)

Validates that experiment results meet quality thresholds and that the
research output is internally consistent. Validates data quality, experiment
configuration, and result integrity.

#### Layer 6 — Evaluation Layer
**Modules:** `researchos/evaluation/` (`engine.py`, `contracts.py`,
`__init__.py`)

Evaluates research outputs against criteria, produces evaluation scores,
and generates evaluation reports. This layer assesses the quality and
significance of research findings.

#### Layer 7 — Intelligence Layer
**Modules:** `researchos/intelligence/` (`graph.py`, `nodes.py`, `edges.py`,
`rag_contracts.py`, `rag_retriever.py`, `repository.py`, `contracts.py`,
`__init__.py`)

Handles knowledge representation, retrieval-augmented generation (RAG),
intelligence graph construction, and repository management for research
intelligence.

#### Layer 8 — Orchestration Layer
**Modules:** `researchos/orchestration/` (`engine.py`, `contracts.py`,
`__init__.py`), `researchos/core/` (`research_orchestrator.py`,
`pipeline.py`, `process_objects.py`, `identity.py`, `lifecycle.py`,
`timestamp.py`, `versioning.py`, `base_object.py`)

Coordinates across all layers. Manages the research pipeline lifecycle,
orchestrates multi-stage computations, and provides shared infrastructure
(deterministic identity generation, lifecycle management, pipeline execution).

#### Core Infrastructure
**Modules:** `researchos/core/`, `researchos/objects/`, `researchos/repository/`,
`researchos/storage/`, `researchos/market_memory/`, `researchos/interpreters/`,
`researchos/decision_engine/`, `researchos/agent/`, `researchos/agents/`,
`researchos/engines/`, `researchos/macro/`.

Shared services: Audit Trail (immutable logging), Ontology Service (concept
definitions), Data Catalog (source metadata), Configuration Service,
Storage Service, Identity Service (deterministic ID generation), Lifecycle
Service.

---

## 3. Responsibility Boundaries

### 3.1 Data Flow vs. Control Flow

**Data flows downward** (Data Layer → Quant Engine → Experiment Framework →
Validation → Evaluation → Intelligence → Orchestration). Each layer
consumes the output of the layer below.

**Control flows upward** (Orchestration → Intelligence → Evaluation →
Validation → Experiment Framework → Quant Engine → Data Layer). The
orchestration layer coordinates execution by calling into lower layers.

### 3.2 Computation Ownership

| Capability | Owner | NOT Owner |
|---|---|---|
| Returns calculation | Quant Engine | Experiment Framework |
| Volatility calculation | Quant Engine | Experiment Framework |
| Drawdown calculation | Quant Engine | Experiment Framework |
| Metrics (Sharpe, Sortino, etc.) | Quant Engine | Experiment Framework |
| Statistics | Quant Engine | Experiment Framework |
| Performance analytics | Quant Engine | Experiment Framework |
| Dataset normalization (OHLCV → prices) | Quant Engine (`_extract_prices`) | Experiment Framework |
| Backtest simulation | Quant Engine (ReplayEngine) | Experiment Framework |
| Experiment lifecycle | Experiment Framework | Quant Engine |
| Run tracking | Experiment Framework | Quant Engine |
| Result packaging + provenance | Experiment Framework | Quant Engine |
| Deterministic hashing | Core Infrastructure (`deterministic_hash`) | Quant Engine |

### 3.3 Data Ownership

| Data Artifact | Produced By | Consumed By |
|---|---|---|
| `HistoricalDataset`, `Candle` | Data Layer | Quant Engine (normalization) |
| `DatasetConfig`, `SimulationConfig` | Dataset Contract Layer | Data Layer (load), Quant Engine (execute), Experiment Framework (orchestrate) |
| `SimulationRequest` | Experiment Framework | Quant Engine |
| `SimulationResult` | Quant Engine | Experiment Framework |
| `ExperimentRun` | Experiment Framework | Experiment Framework, Validation |
| `ExperimentResult` | Experiment Framework | Validation, Evaluation, Orchestration |
| Research Reports | Evaluation, Intelligence | Orchestration |
| Audit Records | Core Infrastructure | All layers |

---

## 4. Protected Modules

The following modules are **LOCKED** for Version 1. They may not be modified
without a formal architecture-change review and re-validation.

### 4.1 Frozen Core Modules

| Module | File | Role |
|---|---|---|
| `BaseExperimentRunner` | `researchos/experiments/runner.py` | Orchestration-only experiment execution |
| `PythonQuantBackend` | `researchos/quant_engine/backend.py` | Reference computation backend |
| `QuantComputationInterface` | `researchos/quant_engine/interface.py` | Abstraction boundary for computation |
| `CalculationVersion` | `researchos/quant_engine/models.py` | Formula version control |
| `SimulationRequest` | `researchos/quant_engine/models.py` | Deterministic computation request |
| `SimulationResult` | `researchos/quant_engine/models.py` | Deterministic computation result |
| `ExperimentRun` | `researchos/experiments/result.py` | Run lifecycle + provenance |
| `ExperimentResult` | `researchos/experiments/result.py` | Result packaging |

### 4.2 Protected Architecture Areas

The following directories are **protected** and must not be modified during
the V1 freeze:

- `researchos/decision_engine/` — decision logic
- `researchos/evidence/` — evidence collection and weighting
- `researchos/probability/` — probability distributions and inference
- `researchos/execution/` — execution logic (NOT used by frozen core)
- `researchos/strategy/` — strategy logic (NOT used by frozen core)

### 4.3 Frozen Contracts

| Contract | Module | Description |
|---|---|---|
| `QuantComputationInterface` | `interface.py` | All computation backends must implement this |
| `Dataset Contract` | `data_engine/contracts.py` | Data formats, enums, configs |
| `Experiment Contract` | `experiments/contracts.py` | DatasetConfig, SimulationConfig |
| `SimulationRequest/Result` | `models.py` | Versioning, hashing, serialization |

---

## 5. Extension Rules

### 5.1 Future systems may extend ResearchOS through modules

**Future systems may extend ResearchOS through modules**, but **must not
violate core boundaries**.

Extensions must adhere to the following rules:

### 5.2 Extension Rule 1: Asset-Class Extensions

New asset classes (EUR/USD, GBP/USD, USD/JPY, stocks, crypto, etc.) can be
added by providing a new **Data Layer** data source that produces the same
dataset contract. The Quant Engine, Experiment Framework, and all upper
layers remain unchanged.

- ✅ Add a new loader in `researchos/data_engine/` for a new data format
- ✅ Pass the loaded data as a `List[Candle]`, `List[dict]`, or
  `HistoricalDataset` to the existing pipeline
- ✅ Set `DatasetConfig.symbols = ["EUR/USD", "GBP/USD", ...]`
- ❌ Do NOT add asset-class-specific logic to `backend.py` or `runner.py`
- ❌ Do NOT add asset-class-specific branches to `interface.py` or `models.py`

### 5.3 Extension Rule 2: Computation Backend Extensions

A future C++ Quant Engine (`cpp_quant_engine/`) can replace
`PythonQuantBackend` by implementing `QuantComputationInterface`.

- ✅ Implement all `@abstractmethod` methods in `QuantComputationInterface`
- ✅ Ensure deterministic outputs (same `SimulationResult` schema)
- ✅ Use `CalculationVersion.CALCULATION_V1` for formula parity
- ❌ Do NOT add new methods to `QuantComputationInterface` without version bump
- ❌ Do NOT change `SimulationRequest` / `SimulationResult` schema

### 5.4 Extension Rule 3: Experiment Framework Extensions

New experiment types (A/B testing, sensitivity analysis, custom workflows)
can be added as subclasses of `AbstractExperimentRunner` or through the
`run_*` methods on `BaseExperimentRunner`.

- ✅ Subclass `AbstractExperimentRunner` for new orchestration patterns
- ✅ Add new `ExperimentType` enum values as needed
- ❌ Do NOT modify `runner.py`'s core `_execute_simulation` method
- ❌ Do NOT add computation to the Experiment Framework

### 5.5 Extension Rule 4: Upper-Layer Extensions

Validation, Evaluation, Intelligence, and Orchestration layers can be extended
freely as long as they only consume the frozen contracts and do not push
computation downward.

- ✅ Add new validation rules in `researchos/validation/`
- ✅ Add new evaluation criteria in `researchos/evaluation/`
- ✅ Add new intelligence modules in `researchos/intelligence/`
- ✅ Add new orchestration patterns in `researchos/orchestration/`
- ❌ Do NOT push computation into the Experiment Framework
- ❌ Do NOT bypass the Quant Engine for any numerical calculation

### 5.6 Forward Compatibility Guarantees

The V1 frozen core guarantees:

1. **Interface stability:** `QuantComputationInterface` will not change its
   method signatures for V1. New methods will be additive.
2. **Schema stability:** `SimulationRequest` and `SimulationResult` will not
   lose fields. New fields will be optional with defaults.
3. **Hash stability:** `result_hash` computation will not change for
   `CALCULATION_V1`. Re-hashing historical results will produce the same
   hashes.
4. **Provenance stability:** All output objects will continue to carry
   full provenance fields.

---

## 6. Verified Architecture Properties

The following properties have been verified by architecture guard tests and
integration tests (see `EXPERIMENT_QUANT_BACKEND_INTEGRATION_REPORT.md`):

| Property | Verified | Test Reference |
|---|---|---|
| ExperimentRunner is orchestration-only | ✅ | `test_runner_has_no_price_extraction_helper`, `test_runner_forwards_raw_dataset_contract` |
| QuantBackend owns computation | ✅ | `test_backend_deterministic_result_hash`, `test_backend_stateless` |
| No RNG scaffolding | ✅ | `test_runner_has_no_random_import`, `test_backend_rng_free`, `test_experiment_execution_is_rng_free` |
| Deterministic results | ✅ | `test_same_dataset_same_config_identical_result`, `test_backend_deterministic_result_hash` |
| Provenance tracking | ✅ | `test_result_contains_all_provenance_fields`, `test_run_links_to_result_hash` |
| Architecture guard tests | ✅ | 17 boundary-freeze guard tests in `test_architecture_boundary_experiment_quant.py` |
| Integration tests | ✅ | 16 integration tests in `test_experiment_backend_integration.py` |

---

## 7. Version 1 Baseline

**Version:** 1.0.0
**Frozen at commit:** `3f4510f` (Architecture Freeze commit)
**Test count:** 1897 passing
**Test duration:** ~36s
**Warnings:** 59 (pre-existing `datetime.utcnow()` deprecation warnings,
noted in remaining limitations)

**Locked files:**
- `researchos/experiments/runner.py`
- `researchos/quant_engine/backend.py`
- `researchos/quant_engine/interface.py`
- `researchos/quant_engine/models.py`

**Protected directories:**
- `researchos/decision_engine/`
- `researchos/evidence/`
- `researchos/probability/`
- `researchos/execution/`
- `researchos/strategy/`

---

## 8. Future Expansion Compatibility

The frozen V1 architecture supports the addition of new FX pairs
(EUR/USD, GBP/USD, USD/JPY, and other currency pairs) without any
modification to the frozen core, Experiment layer, Quant layer, or core
contracts. See Section 5.2 (Extension Rule 1) and `TASK 5` verification
in the Freeze Report.

Future equity/stock research systems should remain separate platforms,
as they may require different data models, regulations, and execution
semantics. The V1 core is optimized for systematic market research on
liquid instruments with deterministic backtesting.

---

*This document, together with `ARCHITECTURE_INVARIANTS.md`, constitutes the
Version 1 Architecture Freeze specification for ResearchOS.*
