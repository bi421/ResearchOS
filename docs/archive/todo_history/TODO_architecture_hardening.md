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

# Architecture Hardening — Confirmed Issues #3, #4, #5

**Status:** COMPLETE
**Scope:** Minimal, contract-preserving fixes for the three confirmed
architectural issues. Issues #1/#2 are already fixed (verified empirically).
Issues #6/#7 are explicitly out of scope.

## Steps
- [x] 1. `contracts.py` — add `snapshot()` to `DatasetConfig` and `SimulationConfig`.
- [x] 2. `experiments/result.py` — freeze `ExperimentRun` parameters + config snapshots (Issue #4).
- [x] 3. `experiments/result.py` — immutable `ExperimentResult` containers (Issue #3).
- [x] 4. `experiments/runner.py` — real dataset provenance instead of hardcoded version (Issue #5).
- [x] 5. Add `tests/test_architecture_immutability.py` — coverage for #3/#4/#5.
- [x] 6. Run full pytest suite; confirm zero regressions. **2044 passed, 56 skipped, 0 failed.**
- [x] 7. Run `ruff check`.
- [x] 8. Report evidence.

## Verification
- Full suite: `2044 passed, 56 skipped, 20 warnings` (0 failures).
- New immutability tests: `15 passed` in `test_architecture_immutability.py`.
- Updated legacy provenance assertions (Issue #5) in:
  - `test_architecture_boundary_experiment_quant.py`
  - `test_experiment_backend_integration.py`

---

# Determinism Closure — Issues A & B (follow-up)

**Status:** COMPLETE
**Scope:** Determinism closure only. Evidence Repository / Lineage Graph /
Model Registry / C++ backend are untouched (deferred).

## Steps
- [x] Issue A — `ExperimentRun.complete()` hash nondeterminism fixed in
      `researchos/experiments/result.py` (wall-clock removed from hash when
      `started_at` is None; deterministic `0.0` default; API preserved;
      telemetry stays outside hash).
- [x] Issue B — `ExperimentResult.from_dict` integrity verification added in
      `researchos/experiments/result.py` (recompute canonical hash; raise
      `ValueError` on mismatch with stored non-empty hash; backward-compatible
      recompute for legacy empty-hash payloads; added `verify_result_hash()`).
- [x] New tests: `researchos/tests/test_determinism_closure.py` (13 tests).
- [x] Full pytest suite green: **2055 passed, 56 skipped, 0 failed**.
- [x] `ruff check` clean.
- [x] Evidence captured in `docs/DETERMINISM_CLOSURE_REPORT.md`.

## Verification
- Determinism closure + immutability: `26 passed`.
- Experiment suite: `188 passed`.
- Full suite: `2055 passed, 56 skipped, 0 failed`.
- `ruff check`: All checks passed.
- Hash determinism evidence: identical logical runs → identical `run_hash`
  (`fda5d3...` == `fda5d3...`); tamper detection raises `ValueError`.

---

# W1 Determinism Closure — run_hash logical identity (runner flow)

**Status:** COMPLETE
**Scope:** W1 only. Evidence Repository / Lineage Graph / Model Registry /
Experiment config snapshotting / C++ backend are untouched (deferred).

## Problem
`BaseExperimentRunner.run()` creates started runs (`run.start()` sets
`started_at`). `ExperimentRun.complete()` derived `duration_seconds` from wall
clock when `duration_seconds <= 0` and `started_at` existed, leaking execution
timing into `run_hash` — two identical logical runs hashed differently.

## Fix
`researchos/experiments/result.py` — `ExperimentRun.complete()` now keeps the
deterministic `0.0` default unless an explicit positive `duration_seconds` is
supplied. Never derives `duration_seconds` from wall clock. `completed_at` and
execution timing remain observational telemetry outside the hash. Public API
unchanged.

## Tests added
`researchos/tests/test_run_hash_runner_determinism.py` (5 tests):
1. Two identical `BaseExperimentRunner` runs produce identical `run_hash`.
2. Changing logical parameters changes `run_hash`.
3. Runtime duration does not affect `run_hash`.
4. Existing `result_hash` determinism remains unchanged.
5. `run_hash` links result identity (`run.result_hash == result.result_hash`).

## Verification
- W1 + determinism closure + immutability: `31 passed`.
- Experiment suite: `188 passed`.
- Full suite: **2060 passed, 56 skipped, 0 failed**.
- `ruff check`: All checks passed.
- Empirical hash evidence: identical logical runs → identical `run_hash`
  (`13fd0ba4...` == `13fd0ba4...`); different logical parameters → different
  `run_hash` (`13fd0ba4...` != `0e2fddb3...`); `duration_seconds == 0.0`.
