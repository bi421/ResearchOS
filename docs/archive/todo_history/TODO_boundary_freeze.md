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

# Experiment/Quant Engine Boundary Freeze — Task Tracker

## Steps

- [x] 1. Audit current implementation (runner.py / backend.py / interface.py / models.py)
- [ ] 2. Create `researchos/tests/test_architecture_boundary_experiment_quant.py` (6 TEST-xxx guard classes + AST guards)
- [ ] 3. Create `docs/ARCHITECTURE_BOUNDARY_EXPERIMENT_QUANT.md`
- [ ] 4. Create `docs/ARCHITECTURE_INVARIANTS.md`
- [ ] 5. Create `docs/EXPERIMENT_QUANT_BOUNDARY_FREEZE_REPORT.md`
- [ ] 6. Run `pytest` — verify new boundary tests + existing experiment/quant-engine tests pass
- [ ] 7. Final declaration in freeze report

