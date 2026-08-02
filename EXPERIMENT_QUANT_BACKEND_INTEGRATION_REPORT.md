# Experiment ↔ Quant Backend Integration Report

**Status:** Completed
**Scope:** Replace `BaseExperimentRunner._execute_simulation()` RNG scaffolding with a deterministic `PythonQuantBackend` computation call, while preserving the strict architectural boundary between the Experiment Framework and raw price data.

---

## 1. Architectural Correction Applied

The Experiment Framework does **NOT** directly consume raw price data. The
approved computation flow is:

```
Data Engine
    ↓
Dataset / Historical Data Contract
    ↓
QuantComputationInterface
    ↓
PythonQuantBackend
    ↓
ExperimentRunner
    ↓
ExperimentResult
```

### 1.1 Old RNG Architecture Problem

The previous `BaseExperimentRunner._execute_simulation()`:

- Held its own `self._rng` (`random.Random`) and called `self._rng.uniform()`.
- Generated **fake metrics** (`num_trades`, `total_return`, etc.) inside the
  Experiment Framework.
- Contained OHLCV-parsing logic (`_extract_prices`) that knew about
  `Candle.close`, `HistoricalDataset.records`, dict `"close"` keys, etc.
- This broke the boundary rules:
  - Experiment Framework parsed OHLCV.
  - Experiment Framework contained financial calculation logic.
  - Results were not reproducible (RNG-driven `num_trades`).

### 1.2 New Computation Flow

`BaseExperimentRunner._execute_simulation()` now:

1. **Builds** a `SimulationRequest` from `experiment.simulation_config`,
   `experiment.dataset_config`, `run.parameters`, and `experiment.tags`.
2. **Forwards the dataset contract unchanged** to the Quant Engine:
   ```
   sim_result = self._backend.run_simulation(request, dataset, calculation_version)
   ```
   - The runner **does not** parse OHLCV, **does not** extract close prices,
     **does not** know MT5/TradingView formats.
   - The dataset contract (list of floats, list of dicts, `HistoricalDataset`,
     `Candle` list, `None` for synthetic demo) is normalized **inside the
     Quant Engine backend**.
3. **Maps** the deterministic `SimulationResult` → `ExperimentResult`:
   - metrics → `result.metrics`
   - statistics → `result.statistics`
   - performance → `result.statistics`
   - equity curve / returns → `result.metadata`
   - computation provenance → `result.statistics`
   - backtest artifacts → `result.trades`, `result.signals`,
     `result.metadata["positions"]`, `result.metadata["execution_stats"]`

### 1.3 Backtest Artifact Propagation

Mode B (bar-by-bar backtest) runs in the backend produce real execution
artifacts via `ReplayEngine` + `ExecutionSimulationLayer`:

```
dataset
  ↓
ReplayEngine (bar-by-bar, no-lookahead)
  ↓
StrategyEvaluationInterface → Signal
  ↓
ExecutionSimulationLayer (orders / fills / positions / trades)
  ↓
SimulationResult.trades / signals / positions / execution_stats
  ↓
ExperimentResult  (packaged verbatim by the runner)
```

The runner **packages only** — it copies the backend-produced lists/dicts into
`ExperimentResult` without parsing or recomputing any execution data:

```python
result.trades = list(sim_result.trades)
result.signals = list(sim_result.signals)
result.metadata["positions"] = list(sim_result.positions)
result.metadata["execution_stats"] = dict(sim_result.execution_stats)
```

These artifacts are included in `SimulationResult.compute_result_hash()`
(and thus in the ExperimentResult provenance), so identical dataset + config
reproduce identical trades/signals/positions/execution_stats.

---

## 2. Files Changed

| File | Change |
|------|--------|
| `researchos/experiments/runner.py` | Replaced RNG/fake-metrics `_execute_simulation()` with a `PythonQuantBackend` computation call. Removed `self._rng`, `_extract_prices()` OHLCV parsing, and fake metric generation. The runner now forwards the dataset contract verbatim to the backend and packages Mode B backtest artifacts. |
| `researchos/quant_engine/backend.py` | (Only if required) — `PythonQuantBackend.run_simulation(request, dataset, ...)` already normalizes the dataset contract deterministically and produces Mode B execution artifacts. Confirmed no RNG state remains in the backend. |
| `researchos/tests/test_experiment_backend_integration.py` | **New** integration tests (16 tests) verifying determinism, dataset sensitivity, RNG-free execution, provenance, the dataset-contract boundary, and Mode B backtest-artifact propagation. |
| `researchos/quant_engine/interface.py` | Signature clarification: `run_simulation(self, request, dataset, calculation_version)` — the parameter is the **dataset contract**, not a pre-parsed price list. |

**Not modified** (as required): `decision_engine/`, `evidence/`, `probability/`,
`execution/`, `strategy/`.

---

## 3. Determinism Verification

The following guarantees are now enforced by tests:

### 3.1 Same dataset + same config = identical result

```python
runner.run(exp, _prices())   # run 1
runner.run(exp, _prices())   # run 2

assert result1.result_hash == result2.result_hash
assert result1.metrics == result2.metrics
```

Verified at three levels:
- **ExperimentRunner level** (`test_same_dataset_same_config_identical_result`)
- **Dataset contract level** (`test_same_dataset_historical_contract_identical`)
- **Backend level** (`test_backend_determinism_direct`)

### 3.2 Different dataset = different result

```python
_, result_up   = runner.run(exp, _prices(drift=+0.001))
_, result_down = runner.run(exp, _prices(drift=-0.001))

assert result_up.result_hash != result_down.result_hash
```

Also verified at the input-hash level:
`test_different_dataset_reference_changes_input_hash`.

### 3.3 No RNG dependency remains

`test_experiment_execution_is_rng_free` monkeypatches the entire `random`
module (`random`, `uniform`, `randint`, `choice`, `gauss`, `Random`) to raise,
and proves a full experiment run completes without touching any of them.

`test_backend_has_no_rng_state` asserts the backend instance has no RNG state
attribute.

### 3.4 ExperimentResult stores computation provenance

`test_result_stores_computation_provenance` asserts `ExperimentResult` carries:
- `computation_backend` = `"PythonQuantBackend"`
- `calculation_version` = `"CALCULATION_V1"`
- `input_hash`, `result_hash`, `simulation_id`
- `dataset_reference`, `dataset_version`, `seed`, `run_number`
- `metadata["equity_curve"]`, `metadata["returns"]`

`test_run_links_to_result_hash` asserts `ExperimentRun.result_hash ==
result.result_hash`.

---

## 4. Test Suite Results

```
researchos/tests/test_experiment_backend_integration.py ................ [  7%]
researchos/tests/test_experiments.py ................................... [ 46%]
researchos/tests/test_quant_engine.py .................................. [100%]
201 passed in 1.50s
```

- **78 existing experiment tests** remain passing.
- **107 existing quant engine tests** remain passing.
- **16 new integration tests** added and passing.
- **Total: 201 passed.**

---

## 5. Remaining Limitations

1. **Backend still accepts a `List[float]` convenience path.** The
   `QuantComputationInterface` contract is dataset-generic, and the backend
   normalizes a variety of dataset contracts. A future refinement could type
   the contract to a single `HistoricalDataset` (or a dedicated
   `DatasetContract` dataclass) to further formalize the boundary.

2. **Monte Carlo resampling lives in the Quant Engine** (`simulation.py`),
   not the Experiment Framework, and is already seeded. It remains the only
   intentionally stochastic simulation mode and is outside the scope of this
   integration (the runner delegates it to the backend with explicit seeds).

3. **The runner synthesizes a default dataset (`None`)** for demo/testing
   purposes only. In production, the Data Engine should always supply a
   validated `HistoricalDataset`. The default is explicit in the tests and
   never used for real research.

4. **Performance analytics are computed via the ResearchOS reference
   implementation** in both `PythonQuantBackend` and `CppQuantAdapter` to keep
   the `SimulationResult` schema identical. A pure C++ performance-analytics
   implementation is future work.

5. **`execution_timestamp` is intentionally non-deterministic** (wall-clock)
   and is **excluded from `result_hash`** (`compute_result_hash` does not
   include it), preserving deterministic hashing while retaining auditability.

