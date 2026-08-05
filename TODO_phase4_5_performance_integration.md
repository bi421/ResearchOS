# Phase 4.5 — C++ Performance Integration (TODO)

## Objectives
- Audit current Python numerical bottlenecks in ResearchOS.
- Identify statistics/performance calculations suitable for C++ acceleration.
- Connect existing C++ statistics modules through cpp_quant_backend.
- Maintain architecture rules (deterministic, no trading logic, no broker, no ML, no signal-gen changes).
- Add integration tests proving Python ↔ C++ numerical equivalence.
- Add benchmarks comparing Python vs C++ execution.
- Produce evidence report.

## Steps
- [x] 1. Inspect architecture (backend, router, numerical_validation, cpp_backend, bindings, C++ modules)
- [x] 2. Plan approved by user

### Implementation
- [x] 3. C++ binding: expose Regression + RollingWindow via CppQuantBackend shim
- [x] 4. Python adapter: add regression/rolling delegation methods in cpp_backend.py
- [x] 5. Python reference: add pure-Python reference implementations in statistics.py (validation only)
- [x] 6. Integration tests: Python ↔ C++ numerical equivalence
- [x] 7. Benchmarks: Python vs C++ execution comparison
- [x] 8. Evidence report: PHASE_4_5_PERFORMANCE_INTEGRATION_REPORT.md

### Verification
- [x] 9. Rebuild cpp_quant_backend (Release .pyd)
- [x] 10. Run C++ tests (all pass; 475 registered in this build)
- [x] 11. Run ResearchOS existing tests (no regressions; 1982 passed)
- [x] 12. Run new Phase 4.5 integration tests (25/25 passed)
- [x] 13. Run benchmarks
- [x] 14. Git commit with clear Phase 4.5 completion message
