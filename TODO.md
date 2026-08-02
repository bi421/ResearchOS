# Experiment ↔ Quant Backend Integration — Artifact Propagation

## Steps

- [x] 0. Audit current state (runner, backend, interface, tests, report, live verification)
- [x] 1. `researchos/experiments/runner.py`: propagate `trades`, `signals`, `positions`, `execution_stats` from `SimulationResult` into `ExperimentResult` (packaging only — no parsing/financial logic)
- [x] 2. `researchos/tests/test_experiment_backend_integration.py`: add tests for
      - ExperimentResult receives backtest artifacts from SimulationResult
      - Backtest artifact provenance deterministic across identical runs
- [x] 3. `EXPERIMENT_QUANT_BACKEND_INTEGRATION_REPORT.md`: document artifact propagation (architecture flow unchanged)
- [x] 4. Run full suite (`test_experiments.py`, `test_quant_engine.py`, `test_experiment_backend_integration.py`)
- [x] 5. Confirm acceptance criteria: existing tests pass, new tests pass, no RNG/boundary regressions

## Verification (2024-05-XX)

```
researchos/tests/test_experiments.py ................................... [ 38%]
researchos/tests/test_quant_engine.py .................................. [ 92%]
researchos/tests/test_experiment_backend_integration.py ................ [100%]

201 passed in 2.09s
```

- 78 existing experiment tests pass.
- 107 existing quant engine tests pass.
- 16 new integration tests pass (determinism, dataset sensitivity, RNG-free,
  provenance, dataset-contract boundary, Mode B backtest artifacts).

## Scope guardrails (approved)

- Do NOT change: strategy logic, execution simulation logic, backend calculations,
  decision_engine, evidence, probability, live execution modules.
- Propagation only — no dataset parsing added to Experiment Framework.

