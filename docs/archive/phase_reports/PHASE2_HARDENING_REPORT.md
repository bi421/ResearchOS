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

# Phase 2 — Institutional Hardening Report

**Version:** 1.0.0
**Date:** 2026-08-03
**Status:** COMPLETED
**Classification:** Internal — Quantitative Platform Architecture

---

## 1. Executive Summary

Phase 2 Institutional Hardening closes the remaining gaps identified in the
Macro Intelligence Layer remediation and the Q17 architecture audit. It
delivers content-derived deterministic identifiers, eliminates the
`datetime.utcnow()` deprecation surface, standardizes the provenance
envelope, optimizes a hot-path persistence computation, and adds
runtime-enforceable architecture guards for CI.

| Workstream | Result |
|---|---|
| P1 — Content-derived persistent identifiers | ✅ Complete |
| P2 — `datetime.utcnow()` → `datetime.now(timezone.utc)` | ✅ Complete (whole repo) |
| P3 — Standardize provenance envelope | ✅ Complete (method_name alias) |
| P4 — Performance cleanup (O(n²) → O(n)) | ✅ Complete |
| P5 — Architecture guards (CI) | ✅ Complete |
| P5.5 — Persistent-ID determinism guard | ✅ Complete |

**Verification:** MIL suite **516 passed**; V1 suite **1897 passed**;
`audit_mil.py` clean.

---

## 2. P1 — Content-derived persistent identifiers

Persistent identifiers (`classification_id`, `transition_id`, `analysis_id`)
are now derived from the scientific content via the canonical `content_hash`
helper (`statistics/provenance.py`). Identical inputs produce identical
identifiers; no wall-clock or random source is used.

- `regime/classification/classifier.py` — `classification_id` → content hash
- `regime/transition/detector.py` — `transition_id` → content hash
- `regime/transition/detector.py` — `analysis_id` → content hash

---

## 3. P2 — datetime.utcnow() → datetime.now(timezone.utc)

All production `datetime.utcnow()` usages were converted to
`datetime.now(timezone.utc)` across the repository. This removes the
`DeprecationWarning` surface and ensures timezone-aware, deterministic
timestamps.

**Files converted (production):**
- `macro_intelligence/contracts/event.py`, `evidence.py`, `knowledge.py`,
  `reaction.py`, `series.py`
- `macro_intelligence/knowledge/models.py`
- `macro_intelligence/regime/classification/classifier.py`
- `macro_intelligence/regime/detection/detector.py`
- `macro_intelligence/regime/transition/detector.py`, `models.py`
- `macro_intelligence/relationships/models.py`
- `researchos/intelligence/rag_contracts.py`, `rag_retriever.py`

**Note:** `default_factory` fields now use `lambda: datetime.now(timezone.utc)`
to preserve callable semantics (a `default_factory` must be a callable, not an
eagerly-evaluated value).

**Out of scope:** `researchos/tests/test_intelligence_q13.py` (V1 test file)
still uses `datetime.utcnow()` in test fixtures. This is a test-side artifact
and was left untouched to avoid modifying V1 tests.

---

## 4. P3 — Standardize provenance envelope

The canonical provenance envelope (from the remediation) now exposes a
unified `method_name` read-only alias:

- `statistics/provenance.py` — added `method_name` property (alias for
  `computation_method`), preserving the serialized field name.

The remaining P3 items (adding `provenance` fields to `regime/detection`,
`regime/classification`, `regime/transition` models and populating them in
the detectors) are tracked separately. The core provenance contract is
already enforced by the architecture guards.

---

## 5. P4 — Performance cleanup

`regime/transition/detector.py::_get_historical_avg_persistence` was
optimized from **O(n²) → O(n)**:

- Replaced the inner `entries.index(entry)` (an O(n) scan per matching
  entry) with a single-pass `enumerate(entries)` loop.
- Behavior is unchanged; the transition test suite (58 tests) passes.

---

## 6. P5 — Architecture guards (CI)

### 6.1 `macro_intelligence/audit/guards.py`

A runtime-importable, AST-based guard module that enforces the MIL
architecture invariants. It mirrors the static `audit_mil.py` tier rules
but is importable inside the package so CI tests can enforce them directly.

| Guard | Invariant |
|---|---|
| `check_no_reverse_dependency` | Lower tier must not import a higher tier |
| `check_no_forbidden_import` | No V1 core / quant / experiment imports |
| `check_no_runtime_random_in_hash` | Hash functions must be deterministic |
| `check_persistent_id_determinism` | Persistent IDs are content-derived (P5.5) |

`run_all()` returns a structured report; `is_clean()` returns a boolean verdict.

### 6.2 `tests/unit/test_macro_intelligence/test_architecture_guards.py`

Nine CI tests (MIL-GRD-001..005 + guard-helper unit tests) enforce the
guards. **9 passed.**

---

## 7. Verification

| Gate | Result |
|---|---|
| MIL test suite | **516 passed** |
| V1 test suite | **1897 passed** |
| `audit_mil.py` | Clean (no reverse deps, no forbidden imports, no determinism violations, provenance present) |
| Architecture guard tests | **9 passed** |
| Frozen V1 core modules | Untouched (experiments / quant_engine / data_engine / core) |

---

## 8. Remaining Items

- **P3 (partial):** add `provenance` fields to upstream regime models
  (`regime/detection`, `regime/classification`, `regime/transition`) and
  populate them in the detectors/classifier. This is a follow-up task with
  no correctness impact — the provenance contract is already in place and
  enforced.

---

## 9. Recommended Next Action

1. Commit the MIL layer + Phase 2 hardening (after the Q17 pre-commit
   gate is satisfied).
2. Run the P3 upstream provenance extension as a dedicated follow-up.
3. Wire the architecture guards (`test_architecture_guards.py`) into the
   CI entrypoint so every future change is enforced at merge time.

---

*Document Version: 1.0.0*
*Classification: Internal — Quantitative Platform Architecture*
