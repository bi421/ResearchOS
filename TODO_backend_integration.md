# Quant Backend Integration — TODO

## Steps

- [x] Plan approved
- [ ] 1. Modify `BaseExperimentRunner` to use `PythonQuantBackend` instead of RNG
- [ ] 2. Extract prices from dataset (support `List[float]`, `HistoricalDataset`)
- [ ] 3. Build `SimulationRequest` from experiment configs
- [ ] 4. Call `PythonQuantBackend.run_simulation()` for real computation
- [ ] 5. Map `SimulationResult` → `ExperimentResult`
- [ ] 6. Update tests (determinism, real computation verification)
- [ ] 7. Run full test suite — 0 regressions
- [ ] 8. Create `EXPERIMENT_QUANT_BACKEND_INTEGRATION_REPORT.md`

