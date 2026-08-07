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

# Determinism Closure — Issues A & B

**Status:** COMPLETE
**Scope:** Determinism closure only. No Evidence Repository, no Lineage Graph,
no Model Registry, no C++ backend changes.

## Issue A — `ExperimentRun.complete()` hash nondeterminism

**Problem:** When `started_at` is None and no explicit `duration_seconds` was
supplied, `duration_seconds` was derived from wall clock (`completed_at -
utc_now()`), injecting microsecond noise into `_to_hashable_dict()` and thus
into `run_hash`. Identical logical runs produced different hashes.

**Fix (`researchos/experiments/result.py`):**
- Preserved the existing `complete()` API signature.
- `duration_seconds` is now set deterministically:
  - explicit `duration_seconds > 0` → used as given;
  - else if `started_at` is not None → derived from `started_at → completed_at`;
  - else → `0.0` (deterministic default, no wall clock).
- Observational telemetry (`completed_at`) remains outside the hash (it was
  never part of `_to_hashable_dict`).

**Evidence:**
```
run_hash r1: fda5d35c08cb0c917f6d84550f58c1d5430a6f483d56de4ab0332a27844e5799
run_hash r2: fda5d35c08cb0c917f6d84550f58c1d5430a6f483d56de4ab0332a27844e5799
duration r1: 0.0 | duration r2: 0.0
identical run_hash: True
```

## Issue B — `ExperimentResult.from_dict` integrity verification

**Problem:** `from_dict` set `result_hash` verbatim from the payload and never
recomputed or verified it. A corrupted/tampered stored hash was silently
accepted; legacy payloads without a stored hash stayed empty-hashed.

**Fix (`researchos/experiments/result.py`):**
- `from_dict` now recomputes the canonical `result_hash` from the deserialized
  content.
- If a stored non-empty hash exists and does not match the recomputed hash →
  raises `ValueError` (tamper/corruption detection).
- If no stored hash (legacy payload) → recomputes deterministically and stores
  it (backward compatible).
- Added public `verify_result_hash()` for live integrity checks.

**Evidence:**
```
round-trip hash preserved: True
verify_result_hash(): True
tamper detected: ValueError raised
verify_result_hash on corrupted: False
legacy recomputed hash non-empty: True
legacy verify_result_hash(): True
```

## Files changed
- `researchos/experiments/result.py` — Issue A `complete()` determinism;
  Issue B `from_dict` verification + `verify_result_hash()`.

## New tests
- `researchos/tests/test_determinism_closure.py` — 13 tests covering:
  - Issue A: identical logical runs → identical `run_hash`; deterministic
    `0.0` duration when not started; explicit duration; started-run duration;
    hash changes on logical input change; telemetry outside hash.
  - Issue B: round-trip hash preservation + verification; legacy payload
    backward compatibility; mismatched stored hash raises; live-object tamper
    detection; valid hash verification.

## Test results
- Determinism closure + immutability: `26 passed`.
- Experiment suite: `188 passed`.
- Full ResearchOS suite: **2055 passed, 56 skipped, 0 failed**.
- `ruff check`: **All checks passed!**

## Remaining risks (out of scope for this pass)
- Untouched: Evidence Repository (WP-3), Lineage Graph, Model Registry (WP-5),
  C++ backend (WP-6).
- `Experiment` config is still mutable (not snapshot-decoupled) — run-level
  snapshots are frozen, but the experiment-level config is not.
- `ExperimentResult.from_dict` raises on mismatch; callers must handle the
  `ValueError` to surface tamper alerts (no ambient logging).
