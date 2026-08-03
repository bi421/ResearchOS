# ResearchOS Architecture Invariants

**Version:** 1.0 (Architecture Freeze)
**Effective Date:** 2026-08-03
**Status:** LOCKED — Permanent Rules

---

These invariants are **permanent rules** that govern the ResearchOS core
architecture. They are enforced by architecture guard tests (see
`researchos/tests/test_architecture_boundary_experiment_quant.py`) and must
not be violated by any future change to the frozen core or any extension
layer.

A violation of any invariant constitutes a **freeze-breaking regression** and
must be resolved before any release.

---

## INVARIANT-CORE-001: ResearchOS Core Must Remain Asset-Class Independent

**Rule:** The ResearchOS core computation and experiment layers must not
contain any logic specific to a particular asset class (e.g., FX, equities,
futures, crypto, options). All asset-class-specific logic must live in
extension modules that sit outside the frozen core.

**Rationale:** Asset-class independence allows the same deterministic
computation pipeline to be reused across XAU/USD, EUR/USD, GBP/USD, USD/JPY,
and any future instrument without modifying the core. The core operates on
generic price series (`List[float]`) and generic dataset contracts, never on
asset-class-specific data structures.

**Enforced by:**
- `test_runner_has_no_data_engine_import` — runner.py must not import
  `researchos.data_engine` symbols.
- `test_runner_executable_source_has_no_ohlcv_field_access` — runner.py
  must not reference `.open`, `.high`, `.low`, `.close`, `.volume`, `OHLCV`,
  `HistoricalDataset`, or `Candle` in executable source.
- Backend `_extract_prices()` normalizes dataset contracts generically:
  `List[float]`, `List[Candle]`, `List[dict]`, `HistoricalDataset`, or `None`.
  No asset-class-specific branches exist.

**Allowed in core:** Generic price series processing, generic dataset
contract normalization, deterministic return/volatility/metric computation.

**Prohibited in core:** Symbol-specific logic, exchange-specific parsing,
asset-class-specific fee models, instrument-type branching.

---

## INVARIANT-CORE-002: Instrument-Specific Logic Must Exist Outside Core Modules

**Rule:** Any logic specific to a trading instrument, symbol, exchange, or
market data format (e.g., MT5, TradingView, Bloomberg, AlphaStream) must be
implemented in extension modules outside the ResearchOS core. Core modules
must never know about broker APIs, exchange protocols, or vendor data formats.

**Rationale:** The core computation pipeline must remain portable and
testable with synthetic data. Instrument-specific concerns are injected via
the Dataset Contract at the Data Layer boundary.

**Enforced by:**
- AST-based source guards in
  `test_architecture_boundary_experiment_quant.py` verify that `runner.py`
  contains no references to `MT5`, `TradingView`, `CSV`, `OHLCV`, or any
  format-specific parsing.
- `QuantComputationInterface` docstring states: "This is NOT a trading
  engine. This is NOT execution logic. This is a NUMERICAL COMPUTATION LAYER
  for research analytics."

**Allowed in core:** Generic dataset contract normalization (duck-typing for
`close` attribute, `"close"` dict key, `records` attribute).

**Prohibited in core:** CSV parsing, MT5/TradingView format knowledge,
exchange protocol awareness, broker API integration.

---

## INVARIANT-CORE-003: ExperimentRunner Never Performs Computation

**Rule:** `ExperimentRunner` (`BaseExperimentRunner`) is orchestration-only.
It must never perform financial calculation logic (returns, volatility,
drawdown, metrics, statistics, performance analytics). All computation is
delegated to the `QuantComputationInterface` (i.e., `PythonQuantBackend`).

**Rationale:** Separation of concerns between orchestration (what to run,
how to track runs, how to package results) and computation (what formulas
to apply). The runner builds a `SimulationRequest`, forwards the dataset
contract to the backend, and packages the `SimulationResult` into an
`ExperimentResult`. It never computes metrics itself.

**Enforced by:**
- `test_runner_executable_source_has_no_ohlcv_field_access` — runner
  cannot access price/OHLCV fields.
- `test_runner_has_no_price_extraction_helper` — runner must not have any
  method with "price" or "extract" in the name.
- `test_runner_forwards_raw_dataset_contract` — the dataset contract is
  forwarded to the backend unchanged (`captured["dataset"] is contract`).
- Runner source explicitly documents: "The Experiment Framework NEVER:
  loads CSV files directly, parses OHLCV data, knows MT5/TradingView
  formats, contains financial calculation logic."

**Allowed in runner:** Experiment lifecycle management, run creation and
tracking, result packaging with provenance, walk-forward window estimation.

**Prohibited in runner:** Returns calculation, volatility calculation,
drawdown calculation, metric computation, price extraction, OHLCV parsing.

---

## INVARIANT-CORE-004: QuantBackend Is the Computation Authority

**Rule:** `PythonQuantBackend` (implementing `QuantComputationInterface`) is
the sole authority for all numerical computation in the ResearchOS core.
It owns: returns calculation, volatility calculation, drawdown calculation,
statistics computation, metrics computation, performance analytics
computation, and dataset-contract normalization.

**Rationale:** Centralized computation ensures that formulas are versioned,
deterministic, and testable. A future C++ backend can replace the Python
backend by implementing the same `QuantComputationInterface` without any
changes to the upper layers (Experiment Framework, Validation, Evaluation,
Intelligence, Orchestration).

**Enforced by:**
- `QuantComputationInterface` is the sole abstraction boundary between
  upper layers and the computation backend.
- `test_backend_stateless` — backend instance holds no RNG or hidden mutable
  state.
- `test_backend_deterministic_result_hash` — identical inputs produce
  identical result hashes.
- `test_backend_rng_free` — backend simulation never calls `random`.
- `CalculationVersion.CALCULATION_V1` governs all formula selection; new
  versions are added without changing existing results.

**Allowed in backend:** Returns, volatility, drawdown, statistics, metrics,
performance analytics, dataset normalization, backtest simulation
(ReplayEngine + ExecutionSimulationLayer + StrategyEvaluationInterface).

**Prohibited in backend:** None — all computation flows here.

---

## INVARIANT-CORE-005: All Research Outputs Require Provenance

**Rule:** Every research output (`SimulationResult`, `ExperimentResult`,
`ExperimentRun`) must carry full provenance: computation backend identifier,
calculation version, input hash, result hash, simulation ID, dataset
reference, dataset version, seed, and run number. The `execution_timestamp`
is audit-only and must be excluded from all deterministic hash computations.

**Rationale:** Provenance ensures that every research result can be audited,
traced to its inputs, and reproduced. The deterministic hash (excluding
wall-clock timestamp) guarantees that identical inputs produce identical
output identifiers, enabling verification and regression detection.

**Enforced by:**
- `test_result_contains_all_provenance_fields` — verifies that
  `ExperimentResult.statistics` contains `computation_backend`,
  `calculation_version`, `input_hash`, `result_hash`, `simulation_id`,
  `dataset_reference`, `dataset_version`, `seed`, `run_number`.
- `test_run_links_to_result_hash` — `ExperimentRun.result_hash` equals
  `ExperimentResult.result_hash`.
- `SimulationResult.compute_result_hash()` excludes
  `execution_timestamp` from the hash content.
- `ExperimentResult._to_hashable_dict()` includes `run_id` and all
  statistics/metrics/performance, excluding wall-clock fields.

**Allowed in core:** Provenance metadata in all output objects.

**Prohibited in core:** Any output without a deterministic result hash.

---

## INVARIANT-CORE-006: Deterministic Inputs Must Produce Reproducible Outputs

**Rule:** The entire ResearchOS core computation pipeline must be fully
deterministic. Identical `SimulationRequest` + identical dataset contract
must produce identical `SimulationResult` (same `result_hash`, same metrics,
same statistics, same equity curve, same trades, same signals, same
positions). No `random.Random` instances, no unseeded RNG, no wall-clock
dependencies in computation.

**Rationale:** Deterministic outputs are the foundation of scientific
research. Without determinism, experiments cannot be reproduced, results
cannot be verified, and regressions cannot be detected. The entire
Experiment ↔ Quant boundary was refactored specifically to eliminate RNG
scaffolding that previously lived in the ExperimentRunner.

**Enforced by:**
- `test_experiment_execution_is_rng_free` — monkeypatches the entire `random`
  module to raise; a full experiment run completes without touching any
  random function.
- `test_backend_has_no_rng_state` — backend instance has no RNG state
  attribute.
- `test_same_dataset_same_config_identical_result` — identical dataset +
  config produce identical `result_hash` at both runner and backend levels.
- `test_different_input_hash_on_change` — different dataset reference
  produces different `input_hash` and `result_hash`.
- `SimulationRequest.compute_input_hash()` uses `deterministic_hash()`
  with sorted parameters.
- `SimulationResult.compute_result_hash()` uses `deterministic_hash()`
  with sorted content, rounded floats, and sorted lists.
- `PythonQuantBackend.__init__()` explicitly documents: "Stateless and
  deterministic: no RNG, no hidden mutable state."

**Allowed in core:** Seeded RNG (explicit `seed` parameter on
`SimulationRequest`, `SimulationConfig`), deterministic pseudo-random
generation.

**Prohibited in core:** Unseeded `random.Random`, `random.random()` without
seed, `numpy.random` without seed, wall-clock-dependent computation in
hashing.

---

## Invariant Registry

| ID | Invariant | Enforcement |
|---|---|---|
| INVARIANT-CORE-001 | Core is asset-class independent | AST guards, runtime tests |
| INVARIANT-CORE-002 | Instrument-specific logic outside core | AST guards, interface docstring |
| INVARIANT-CORE-003 | ExperimentRunner never computes | AST guards, source guards, runtime tests |
| INVARIANT-CORE-004 | QuantBackend is computation authority | Interface contract, runtime tests |
| INVARIANT-CORE-005 | All outputs require provenance | Runtime test: provenance fields |
| INVARIANT-CORE-006 | Deterministic inputs → reproducible outputs | RNG-free tests, hash determinism tests |
