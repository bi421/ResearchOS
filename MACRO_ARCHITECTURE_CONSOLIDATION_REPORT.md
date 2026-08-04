# Macro Intelligence Layer — Architecture Consolidation Report

**Version:** 1.0.0
**Date:** 2026-08-03
**Status:** COMPLETED
**Classification:** Internal — Quantitative Platform

---

## 1. Objective

Remove the single canonical-ownership violation discovered during the Macro
Intelligence Layer architecture audit.

**Canonical ownership rule:**

> The Statistics Layer owns ALL statistical algorithms.
> The Relationships Layer owns ONLY relationship analysis and orchestration.
> Relationship modules must NEVER contain independent implementations of
> statistical algorithms.

---

## 2. Files Changed

| File | Change |
|------|--------|
| `macro_intelligence/relationships/correlation.py` | Replaced duplicate `pearson_correlation` / `spearman_correlation` implementations with thin delegating wrappers around the canonical Statistics Layer implementations. |

No other files were modified.

---

## 3. Architectural Reason

The Macro Intelligence Layer requires **exactly one canonical implementation**
of each statistical algorithm. Two implementations of `pearson_correlation` and
`spearman_correlation` existed:

- `macro_intelligence/statistics/correlation.py` (canonical owner)
- `macro_intelligence/relationships/correlation.py` (duplicate)

The Relationships Layer is an orchestration layer. It must consume the
Statistics Layer — not re-implement statistical mathematics.

---

## 4. Ownership Before

| Algorithm | Statistics | Relationships | Duplicate? |
|-----------|-----------|---------------|------------|
| `pearson_correlation` | `statistics/correlation.py` | `relationships/correlation.py` | **YES** |
| `spearman_correlation` | `statistics/correlation.py` | `relationships/correlation.py` | **YES** |

---

## 5. Ownership After

| Algorithm | Canonical owner | Relationships |
|-----------|----------------|---------------|
| `pearson_correlation` | `statistics/correlation.py` | delegates (wrapper) |
| `spearman_correlation` | `statistics/correlation.py` | delegates (wrapper) |

The relationships wrappers preserve the existing public API contract:

- **Statistics implementation:** raises `ValueError` on invalid inputs.
- **Relationships public API:** returns `None` on invalid inputs.
- The wrapper converts `ValueError → None`, preserving backward compatibility.

---

## 6. Verification Results

### 6.1 Static Audit (`audit_mil.py`)

| Check | Result |
|-------|--------|
| `pearson` owners | **1** — `statistics.correlation.pearson_correlation` |
| `spearman` owners | **1** — `statistics.correlation.spearman_correlation` |
| Forbidden imports (V1/Quant/Experiment) | **NONE** |
| Non-frozen dataclasses | **NONE** |
| Mutable defaults | **NONE** |
| Determinism violations in hashes | **NONE** |
| Provenance (evidence + knowledge) | **PRESENT** |

The relationships module now imports from `statistics.correlation` (visible in
the import graph: `relationships.correlation → statistics.correlation`).

### 6.2 Test Suite

| Suite | Result |
|-------|--------|
| `tests/unit/test_macro_intelligence/statistics/` | **PASS** |
| `tests/unit/test_macro_intelligence/relationships/` | **PASS** |
| `tests/unit/test_macro_intelligence/` (full) | **495 passed, 12 pre-existing failures** |

The 12 failures are **pre-existing and unrelated** to this consolidation (see
Section 7). No new failures were introduced.

---

## 7. Remaining Known Pre-Existing Issues

These failures exist in modules **not modified** by this task and are already
documented as pre-existing:

| Module | Issue |
|--------|-------|
| `regime/test_regime.py` | `TestRegimeEnums::test_employment_states` — `EmploymentState` enum typo |
| `test_features.py` | `FeatureDefinition` / `FeatureRegistry` — `FeatureCalculationResult` mismatch |
| `test_revision_provenance.py` | `ProvenanceChain::test_provenance_hash_deterministic` / `AuditLog` — audit log API mismatch |

These are outside the scope of this consolidation and were left untouched.

---

## 8. Declaration

> No computation behavior changed. The elimination of duplicate ownership was
> achieved by delegation, not by modification of any algorithm. The Statistics
> Layer remains the single source of truth for all statistical computation.
> The Relationships Layer is now an orchestration layer only. No public API
> changed, no new dependencies were introduced, no architecture boundaries were
> violated, and no feature additions were made.

---

*Document Version: 1.0.0*
*Classification: Internal — Quantitative Platform Architecture*
