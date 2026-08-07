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

# Phase 5.1 — Certified Analytical Compute Surface

**Status:** IN PROGRESS
**Scope:** WP-1 (certified analytical surface) + WP-4 (analytical test coverage) from
`docs/PHASE5_ARCHITECTURE_PLAN.md`. Additive only. No frozen-interface modification.
No commits. No Phase 5.2+.

## Architecture constraints (approved)
- Do NOT modify `QuantComputationInterface`, `BackendRouter`, `NumericalComparator`,
  `backend_hash`, existing certified regression/rolling API, scheduler, bridge contracts,
  hashing, deterministic policies.
- `ResearchComputationInterface` is a separate abstraction (additive subclass of the frozen
  interface so research backends remain registerable with the existing `BackendRouter`).
- No new algorithms — only expose existing deterministic submodule computations.
- Python reference = scientific source of truth; C++ = optional candidate (existing certified
  capability only; deterministic Python fallback for non-C++ analytical functions).
- Benchmark = scaffolding only, gated by `RESEARCHOS_PERF=1`, no performance assertions.
- No Phase 5.2 (workflow facade), model registry, evidence repository, C++ optimization,
  architecture redesign, or commits.

## Steps
- [x] 1. Create `research_interface.py` — `ResearchComputationInterface` + `RESEARCH_OPERATIONS`
      + `ResearchResult` (deterministic hashes via backend_hash).
- [x] 2. Create `research_engine.py` — `PythonResearchBackend` (reference, delegates to existing
      deterministic submodules) + `ResearchEngine` facade.
- [x] 3. Create `research_cpp_backend.py` — `ResearchCppBackend` (candidate; C++ capability where
      available, deterministic Python fallback otherwise).
- [x] 4. Create `research_registry.py` — `create_research_router()` / `register_research_backend()`
      / `create_research_engine()` (additive registration with existing BackendRouter).
- [x] 5. Update `researchos/quant_engine/__init__.py` — additive exports.
- [ ] 6. Tests: `test_quant_probability.py`, `test_quant_historical.py`, `test_quant_validation.py`
      (WP-4 direct coverage).
- [ ] 7. Tests: `test_research_engine_certification.py` (capability, determinism, parity, NaN/Inf
      rejection, edge cases, error propagation, provenance chaining).
- [ ] 8. Tests: `test_research_router_integration.py` (router registration, validation status,
      fallback, metadata).
- [ ] 9. Benchmark scaffolding: `benchmarks/benchmark_research_engine.py` (RESEARCHOS_PERF=1 gate,
      no assertions).
- [ ] 10. Run full ResearchOS suite; confirm existing Phase 4 tests stay green.
- [ ] 11. Evidence report: `docs/PHASE_5_1_CERTIFIED_ANALYTICAL_SURFACE_REPORT.md` + GO/NO-GO.

