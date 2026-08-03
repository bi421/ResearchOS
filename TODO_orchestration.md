# Research Orchestration Layer (Q14) — Task Tracking

Goal: deliver an isolated `researchos/orchestration/` module that coordinates
the locked modules (Dataset Builder, Walk-Forward Validation, Training
Framework) into a single deterministic research pipeline and returns an
immutable `PipelineReport`.

## Architectural constraints (approved)

- Pure coordinator only:
  `DatasetBuilder -> WalkForwardValidator -> Trainer -> PipelineReport`.
- NO persistence, NO repository writes, NO registry mutation, NO graph
  construction/mutation.
- Dependency injection only; no singletons; no global mutable state.
- stdlib only; deterministic; no randomness.
- NO modifications to any locked module.

## Steps

- [x] 0. Understand module interfaces (FeatureBuilder, DatasetBuilder,
      WalkForwardValidator, Trainer, TrainingResult, ModelContract,
      ValidationResult).
- [x] 1. Confirm final scope/signature with user (plan approved with
      purity adjustments).
- [ ] 2. Create `researchos/orchestration/contracts.py` (immutable
      contracts + serialization).
- [ ] 3. Create `researchos/orchestration/engine.py` (pure
      `ResearchOrchestrator` coordinator).
- [ ] 4. Create `researchos/orchestration/__init__.py` (public API).
- [ ] 5. Create `researchos/tests/test_orchestration_q14.py`
      (comprehensive unittest suite).
- [ ] 6. Verify: py_compile all new files.
- [ ] 7. Run new test suite (expect ALL PASS).
- [ ] 8. Run full repo suite (expect ALL PASS, no regressions).
- [ ] 9. Verify imports + determinism + forbidden-lib scan.
- [ ] 10. git diff / confirm NO locked module modified; report GREEN.

