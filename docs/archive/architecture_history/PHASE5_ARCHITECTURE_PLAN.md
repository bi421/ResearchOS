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

# Phase 5 Architecture & Migration Plan

**Status:** PLANNING (architecture only — no implementation)
**Scope:** All of Phase 5 — downstream integration of the Phase 4 compute
baseline into the research engine layer, with deterministic acceleration,
unified evidence storage, and scientific workflow completion.
**Base:** Phase 4 frozen compute baseline (`2020f90` + release audit `a897845`)
**Classification:** Internal — Architecture & Migration Plan

---

## 1. Executive Summary

Phase 4 delivered a certified, deterministic compute baseline: a trust-boundary
`BackendRouter`, a scheduler, the Python reference backend
(`PythonQuantBackend`), the C++ acceleration adapter (`CppQuantAdapter`), and a
production Python/C++ bridge (`cpp_quant_backend`) with Regression and
RollingWindow acceleration (up to ~17×).

Phase 5 is the **research-engine integration layer**: it connects the Phase 4
compute baseline to the analytical engines that exist in `researchos/quant_engine`
(technical, probability, portfolio, historical, fundamental, econometrics,
machine_learning/training, validation) and completes the institutional
scientific workflow. Phase 5 must:

1. **Unify** the analytical engines behind a single
   `ResearchEngine`/`ResearchComputationInterface` facade registered with the
   Phase 4 router.
2. **Preserve determinism** — every new surface is a pure function of its
   inputs; no stochastic models, no wall-clock dependence in hashes.
3. **Preserve the frozen compute interface** — `QuantComputationInterface`,
   `BackendRouter`, `PythonQuantBackend`, and `CppQuantAdapter` are extended
   only by **additive** capabilities, never modified.
4. **Close evidence integrity** — an immutable experiment-evidence repository
   (audit-trail-backed) for research artifacts.
5. **Fix coverage gaps** — add the missing unit tests for the analytical
   submodules that have implementations but no direct test coverage.
6. **Optional acceleration** — identify the analytical kernels most suitable
   for C++ acceleration (following the Phase 4.5 certified pattern), with the
   Python reference remaining the source of truth.

This is a **planning document only**. No production code is written, no modules
are modified, no commits are created, and no architecture is changed.

---

## 2. Current Baseline (After Phase 4)

### 2.1 Frozen Compute Layer (Phase 4)

| Component | File(s) | Status |
|-----------|---------|--------|
| `QuantComputationInterface` | `researchos/quant_engine/interface.py` | **Frozen** — 7 ops |
| `PythonQuantBackend` | `researchos/quant_engine/backend.py` | Certified source of truth |
| `BackendRouter` | `researchos/quant_engine/router.py` | Certification/trust-boundary |
| `BackendScheduler` | `researchos/quant_engine/scheduler.py` | Deterministic selection |
| `NumericalComparator` | `researchos/quant_engine/numerical_validation.py` | atol=1e-12 / rtol=1e-10 |
| `Capabilities` | `researchos/quant_engine/capabilities.py` | Trust-boundary contract |
| `CppQuantAdapter` | `researchos/quant_engine/cpp_backend.py` | C++ acceleration delegate |
| C++ bridge + engine | `cpp_quant_engine/` | Regression + RollingWindow |
| Performance integration | `researchos/benchmarks/benchmark_cpp_performance_integration.py` | Benchmarks |

Verified: 475/475 C++ (CTest), 30/30 Phase 4.5 integration, 3/3 benchmark,
1912+ existing ResearchOS tests, 131 Phase 4.1 backend tests, 96 bridge tests.

### 2.2 Existing Analytical Engines (implemented, partially integrated)

| Engine | Files | Implementation | Router-integrated | Direct tests |
|--------|-------|----------------|-------------------|--------------|
| Technical | `quant_engine/technical/` | Deterministic indicator framework (23 of 26 indicators) | ✗ | ✗ directly |
| Probability | `quant_engine/probability/` | 14 models, seeded/deterministic | ✗ | ✗ directly |
| Portfolio | `quant_engine/portfolio/` | 12 of 13 analytics | ✗ | ✗ directly |
| Historical | `quant_engine/historical/` | 12/12 analytics | ✗ | ✗ directly |
| Fundamental | `quant_engine/fundamental/` | 12/14 analytics | ✗ | ✗ directly |
| Econometrics | `quant_engine/econometrics/` | 6/13 models | ✗ | ✗ directly |
| Feature building | `quant_engine/machine_learning/` | Deterministic features, labels, dataset builder | ✗ | ✓ partial |
| Training (deterministic) | `quant_engine/training/` | Rule-based / linear / threshold / feature-weight | ✗ | ✓ partial |
| Validation split | `quant_engine/validation/` | Splitter, walk-forward | ✗ | ✗ directly |

### 2.3 Storage & Provenance

| Component | File(s) | Status |
|-----------|---------|--------|
| In-memory repository | `researchos/repository/` | Memory-backed |
| SQLite storage | `researchos/storage/repository.py` | Exists |
| Pipeline repository | `researchos/pipeline_repository/` | Exists |
| Audio/evidence trail | `researchos/intelligence/`, `market_memory/` | Partial |
| Experiment evidence | `researchos/experiments/result.py` | Immutable result hashes |

---

## 3. Remaining Gaps (After Phase 4)

### 3.1 Critical

**G-C1. Analytical engines are not behind the certified compute boundary.**
The technical/probability/portfolio/historical/fundamental/econometrics engines
implement deterministic math but are **not** exposed through the Phase 4 router,
so their outputs are not certified (no capability check, no `NumericalComparator`,
no canonical `result_hash`, no fallback). Any consumer trusting these outputs
bypasses the trust boundary.

**G-C2. No unified research-engine facade.**
There is no single `ResearchEngine` entry point that composes the analytical
engines, the Phase 4 compute backend, feature/label building, and validation
into one deterministic research pipeline. Consumers must call each submodule
directly, which prevents provenance chaining (input hash → output hash) and
breaks reproducibility at the workflow level.

**G-C3. Machine Learning surface is only "architecture".**
The `training/` trainer explicitly supports only rule-based / linear / threshold
/ feature-weight "architecture only, not ML" models. The `machine_learning/`
subpackage builds features/labels/datasets but there is no deterministic model
**registry**, no walk-forward **evaluation contract**, and no certified
**prediction** surface through the router.

### 3.2 High

**G-H1. Direct test coverage missing for analytical submodules.**
The Phase 4.1 audit (`QUANT_ENGINE_AUDIT_REPORT.md`) confirmed: technical,
probability, portfolio, historical, fundamental, econometrics submodules have
implementations but **no direct unit/integration test files**. The new engines
are exercised only indirectly (or not at all).

**G-H2. Immutable experiment-evidence storage is not unified.**
`SimulationResult`/`ExperimentResult` hashes are deterministic, but there is no
single append-only evidence repository that stores, versions, and audits all
research artifacts (datasets, features, labels, models, predictions, validated
outcomes) with a uniform lineage envelope.

**G-H3. Walk-forward validation is disconnected from the compute backend.**
`quant_engine/validation/walk_forward.py` exists, but the deterministic walk
forward is not integrated with the router (each fold should be a certified
computation) nor with the experiment framework for evidence capture.

**G-H4. C++ acceleration surface is narrow.**
Only regression + rolling statistics are accelerated. Analytical kernels that are
O(n) pure-Python loops (e.g., technical indicators, portfolio covariance /
efficient-frontier math, econometric filters) remain Python-bound and are prime
candidates for the Phase 4.5 certified pattern (Python reference + C++ candidate
+ `NumericalComparator` validation).

### 3.3 Medium

**G-M1. Performance benchmark coverage is not continuous.**
Phase 4.5 benchmarks are observational and gated behind `RESEARCHOS_PERF=1`.
There is no certified performance-profile pipeline feeding the scheduler from
the full analytical suite.

**G-M2. Machine_learning model/registry metadata is fragmented.**
`machine_learning/models/registry.py` and `training/repository.py` exist, but
model metadata is not uniformly versioned/hashed into the evidence store.

**G-M3. Hyperparameters/config are not centrally versioned for the analytical
engines.**
Each engine carries its own parameters; there is no unified configuration
service (per the Phase 0 architecture) tying methodology versions to computed
outputs at the research-engine level.

**G-M4. Explainability traces are not uniformly emitted.**
Some engines produce reasoning/parameter traces, but there is no common output
envelope that guarantees every research result exposes the "inputs + parameters
+ methodology version" explainability contract.

### 3.4 Low

**G-L1. API exports are incomplete.**
`researchos/quant_engine/__init__.py` does not re-export the analytical
submodules (technical, probability, portfolio, historical, fundamental,
econometrics, machine_learning, training, validation). Direct subpackage imports
are required; a stable public surface is absent.

**G-L2. Legacy duplicate helpers.**
A few duplicate convenience functions exist across submodules (e.g., rolling
stats in `machine_learning/features.py` vs `quant_engine/statistics.py`).
Consolidation should be additive-only and audited.

---

## 4. Proposed Work Packages

### WP-1 — Certified Analytical Compute Surface (G-C1, G-L1)

**Purpose:** Expose the existing analytical engines behind a single
`ResearchComputationInterface` registered with the Phase 4 router, so every
analytical computation gets capability checks, numerical validation, canonical
hashing, and Python-fallback certification.

**Affected modules:**
- `researchos/quant_engine/interface.py` (additive: new abstract interface,
  NOT modifying `QuantComputationInterface`)
- `researchos/quant_engine/research_engine.py` (new facade)
- `researchos/quant_engine/technical/`, `probability/`, `portfolio/`,
  `historical/`, `fundamental/`, `econometrics/`
- `researchos/quant_engine/router.py` (register new candidates; no behavior change)
- `researchos/quant_engine/__init__.py` (public exports)

**Expected benefits:**
- Every analytical output is certified and auditable.
- Provenance chaining (input hash → output hash) for all research analytics.
- Single public API for consumers.

**Risks:** Medium — wrapping existing submodules requires care not to alter
their numeric behavior; certification adds validation overhead.

**Implementation complexity:** Medium-High.

**Dependencies:** Phase 4.1-4.5 certification layer (complete). Each analytical
engine must expose a `capabilities()` and `get_version()`.

**Acceptance criteria:**
- All analytical ops routed through `BackendRouter` with candidate + reference.
- Every output has deterministic `input_hash` / `result_hash`.
- Python reference equivalence for every op within atol/rtol.
- Existing submodule math unchanged (regression suite green).

---

### WP-2 — Research Engine Facade & Scientific Workflow (G-C2, G-M3, G-M4)

**Purpose:** Provide a single deterministic `ResearchEngine` that composes
dataset → features/labels → compute → validation → evidence into one auditable
scientific workflow with a uniform explainability envelope.

**Affected modules:**
- `researchos/quant_engine/research_engine.py` (new)
- `researchos/experiments/` (runner glue)
- `researchos/quant_engine/machine_learning/` (feature/label/dataset builder)
- `researchos/quant_engine/validation/` (splitter/walk-forward)
- `researchos/quant_engine/models/` (unified config/metadata)
- `researchos/repository/`, `researchos/storage/` (evidence store interface)

**Expected benefits:**
- Research reproducibility at the workflow level: one hashable pipeline.
- Uniform methodology-version and parameter provenance.
- Every result carries the explainability contract (inputs + params + version).

**Risks:** Medium — workflow composition must not introduce hidden state or
non-determinism; careful ordering of folds/features.

**Implementation complexity:** High.

**Dependencies:** WP-1 (certified surface), existing experiment framework,
feature/label/dataset builders.

**Acceptance criteria:**
- `ResearchEngine.run(config, dataset)` → immutable `ResearchResult` with
  full provenance hash.
- Deterministic: identical config+dataset → identical hash/result.
- Walk-forward and feature building are certified sub-steps.
- Explainability envelope present on every artifact.

---

### WP-3 — Immutable Evidence Repository (G-H2, G-M2)

**Purpose:** Build an append-only, SQLite-backed evidence repository that stores
and versions every research artifact (datasets, features, labels, models,
predictions, validated outcomes) with a uniform lineage envelope, extending the
existing storage layer.

**Affected modules:**
- `researchos/repository/` (new append-only evidence store)
- `researchos/storage/repository.py` (backing store)
- `researchos/pipeline_repository/` (hook)
- `researchos/experiments/result.py` (evidence capture)

**Expected benefits:**
- Immutable, auditable research history.
- Uniform lineage: artifact → parent hash → methodology version.
- Queryable evidence for validation and cognitive growth.

**Risks:** Medium — schema/version migration must be deterministic and additive;
no in-place mutation.

**Implementation complexity:** Medium-High.

**Dependencies:** WP-1 (certified artifacts), existing SQLite storage.

**Acceptance criteria:**
- Every stored artifact has a deterministic content hash + lineage.
- Append-only: no update/delete of existing records.
- Evidence store interfaces with `ResearchEngine` output.

---

### WP-4 — Analytical Unit Test Coverage (G-H1)

**Purpose:** Add direct deterministic unit and (where useful) integration tests
for technical, probability, portfolio, historical, fundamental, econometrics,
and validation submodules. Pure research-only tests; no trading logic.

**Affected modules:**
- `researchos/tests/test_quant_technical_*.py` (new)
- `researchos/tests/test_quant_probability_*.py` (new)
- `researchos/tests/test_quant_portfolio_*.py` (new)
- `researchos/tests/test_quant_historical_*.py` (new)
- `researchos/tests/test_quant_fundamental_*.py` (new)
- `researchos/tests/test_quant_econometrics_*.py` (new)
- `researchos/tests/test_quant_validation_*.py` (new)

**Expected benefits:**
- Certified correctness at the analytical-engine level.
- Determinism regressions caught early.
- Parity baseline for C++ acceleration (WP-6).

**Risks:** Low — tests are observation of existing deterministic behavior.

**Implementation complexity:** Medium.

**Dependencies:** None beyond the existing submodules.

**Acceptance criteria:**
- ≥ 200 new deterministic tests across the six engines.
- Every public function in the targeted submodules covered.
- Full suite stays green (no behavior change).

---

### WP-5 — Deterministic Model Registry & Evaluation (G-C3)

**Purpose:** Complete the deterministic research-model surface: a model
registry (metadata, versioning, hashing) and a certified prediction/evaluation
contract through the router, using only the existing deterministic model
families (rule-based, linear formula, threshold, feature-weight). Explicitly
NOT stochastic ML/DL.

**Affected modules:**
- `researchos/quant_engine/machine_learning/models/registry.py`
- `researchos/quant_engine/training/` (trainer, repository, metrics)
- `researchos/quant_engine/machine_learning/label_builder.py`
- `researchos/quant_engine/validation/walk_forward.py` (evaluation contract)
- `researchos/quant_engine/router.py` (certified prediction)

**Expected benefits:**
- Deterministic research models are first-class certified artifacts.
- Uniform model metadata + content hash → evidence store.
- Walk-forward evaluation becomes a certified, reproducible experiment.

**Risks:** Medium — must not creep toward stochastic ML; keep the model families
explicitly deterministic and explainable.

**Implementation complexity:** Medium.

**Dependencies:** WP-1, WP-3, WP-4 (baseline correctness).

**Acceptance criteria:**
- Model registry returns content-hashed `ModelContract` objects.
- Prediction/evaluation routed through the router with validation.
- Walk-forward folds produce deterministic certified results.
- No stochastic model families (no gradient descent, no random forests, etc.).

---

### WP-6 — C++ Acceleration of Analytical Kernels (G-H4)

**Purpose:** Extend the Phase 4.5 certified acceleration pattern to the highest-
value analytical kernels (technical rolling indicators, portfolio covariance/
efficient-frontier math, econometric single-pass filters) with the Python
reference remaining the source of truth.

**Affected modules:**
- `cpp_quant_engine/include/quant/analytics/*.h` (new C++ kernels)
- `cpp_quant_engine/bindings/python_bindings.cpp` (additive bindings)
- `researchos/quant_engine/cpp_backend.py` (delegations)
- `researchos/benchmarks/benchmark_cpp_analytics.py` (new)
- `researchos/tests/test_cpp_analytics_integration.py` (new)

**Expected benefits:**
- Meaningful speedups (~5–16×) on O(n) analytical loops.
- Certified parity via `NumericalComparator`.
- Scheduler profile enriched with analytical-op timings.

**Risks:** High — must preserve byte-level parity for the hash contract; only
order-independent (or order-stable) reductions may be SIMD/parallelized.

**Implementation complexity:** High.

**Dependencies:** WP-1 (certified analytical surface), Phase 4.5 C++ build,
`NumericalComparator`.

**Acceptance criteria:**
- Every accelerated op passes Python↔C++ equivalence within atol/rtol.
- Deterministic hashes unchanged for identical inputs.
- Benchmark harness reports per-op speedups.
- C++ gtest suite stays 475/475 (plus new kernel tests).

---

### WP-7 — Certified Performance Profile Pipeline (G-M1, G-M3)

**Purpose:** Continuously feed analytical-op timings from the benchmark harness
into the scheduler's certified performance profile, keeping the per-operation
adoption policy data-driven.

**Affected modules:**
- `researchos/quant_engine/scheduler.py` (profile ingestion API — additive)
- `researchos/benchmarks/` (CI hook)
- `researchos/quant_engine/router.py` (profile refresh — additive)

**Expected benefits:**
- Scheduler remains deterministic but adapts certified estimates.
- Performance regressions surface automatically.

**Risks:** Low-Medium — profile calibration must remain deterministic and
versioned.

**Implementation complexity:** Medium.

**Dependencies:** WP-6 benchmark harness.

**Acceptance criteria:**
- Profile is versioned and deterministically merged from observations.
- Router uses refreshed profile without behavior change.
- Gate: no schedule decision changes for identical inputs/profile version.

---

## 5. Risk Assessment

| # | Risk | Likelihood | Impact | Mitigation |
|----|------|-----------|--------|------------|
| R1 | Wrapping analytical engines changes numeric behavior | Medium | High | Reference-first tests (WP-4) before wrapping; only additive changes; parity gates |
| R2 | C++ acceleration breaks hash parity | Medium | High | Only order-stable reductions; byte-parity tests; `NumericalComparator` gate; scalar reference preserved |
| R3 | Workflow facade introduces non-determinism | Low | High | Pure functions; no hidden state; deterministic fold ordering; hash-based identity |
| R4 | Scope creep into stochastic ML | Medium | High | Explicit model-family whitelist; review gate; no gradient/forest/DL |
| R5 | Evidence store schema migration breaks lineage | Low | Medium | Additive-only schema versions; content-hash lineage; append-only |
| R6 | Test coverage effort large | Medium | Low | Incremental WP-4; prioritize high-value public functions |
| R7 | Scheduler profile drift | Low | Medium | Versioned, deterministic profile merge; identical-input gate |

---

## 6. Migration Strategy

Phase 5 is implemented as an **additive, compatibility-preserving** migration:

1. **Never modify** the frozen `QuantComputationInterface`, `BackendRouter`
   behavior, `PythonQuantBackend`, or the C++ bridge contract.
2. **New interfaces are additive** — `ResearchComputationInterface` extends the
   pattern without altering existing ops.
3. **Every new computation surface** is registered as a **candidate backend**
   with the Phase 4 router, validated against the Python reference, and given an
   automatic Python-fallback path — exactly the Phase 4.1 pattern.
4. **C++ acceleration** only ever appears as a candidate behind the router;
   the Python reference remains the source of truth.
5. **Evidence is append-only** — any new repository layer layers on top of the
   existing storage, never mutating prior records.
6. **Tests-first for every WP** — deterministic reference tests must exist
   before any wrapping/acceleration.

---

## 7. Acceptance Gates

Every Phase 5 work package must pass:

| Gate | Requirement |
|------|-------------|
| **G-Arch** | No modification to frozen compute interfaces; no trading/broker/ML/signal changes |
| **G-Determinism** | Identical inputs → identical outputs and hashes for every new surface |
| **G-Parity** | All candidate outputs match the Python reference within atol=1e-12 / rtol=1e-10 |
| **G-Repro** | Every result carries full provenance (inputs, parameters, methodology version) |
| **G-Immutable** | Evidence store is append-only; lineage preserved |
| **G-Explain** | Every research result exposes the explainability envelope |
| **G-Test** | New deterministic tests pass; full suite (ResearchOS + C++) stays green |
| **G-Perf** | Benchmarks report per-op speedups; C++ candidates never regress parity |
| **G-Compat** | Backward-compatible exports; existing callers unchanged |

---

## 8. Recommended Milestones

### Phase 5.1 — Certified Analytical Surface (WP-1 + WP-4)
- Register the six analytical engines behind the router; add direct test
  coverage (G-H1 + G-C1).
- **Justification:** Everything downstream needs certification and correctness
  first. This de-risks wrapping before acceleration and provides the parity
  baseline for all later WPs.

### Phase 5.2 — Research Engine Facade (WP-2)
- Compose the certified pipeline: dataset → features/labels → compute →
  validation → evidence, with an explainability envelope.
- **Justification:** The workflow-level reproducibility and provenance chaining
  are the central institutional value; requires WP-5.1 certified surface.

### Phase 5.3 — Immutable Evidence Repository (WP-3 + WP-5)
- Append-only evidence store; deterministic model registry + walk-forward
  evaluation.
- **Justification:** Hardens the scientific record and closes the model/evidence
  lifecycle; depends on WP-1/WP-2 output contracts.

### Phase 5.4 — C++ Analytical Acceleration (WP-6)
- Accelerate the highest-value analytical kernels with certified parity and a
  benchmark harness.
- **Justification:** Delivers the Phase-4.5-style performance wins on the
  research analytics, following the already-certified pattern.

### Phase 5.5 — Continuous Performance Profiling (WP-7)
- Feed analytical-op timings into the scheduler profile.
- **Justification:** Closes the loop so the accelerated backend is adopted
  per-operation in production, mechanically and deterministically.

---

## 9. Compatibility Confirmation

Every proposed Phase 5 task **explicitly preserves**:

- ✅ **Deterministic execution** — all new surfaces are pure functions; no
  stochastic models; order-stable reductions only.
- ✅ **Reproducibility** — identical inputs → identical hashes; provenance
  chaining everywhere.
- ✅ **Scientific workflow** — hypothesis → certified compute → validation →
  evidence → review, unchanged.
- ✅ **Immutable experiment evidence** — new evidence store is append-only;
  existing result hashes untouched.
- ✅ **Frozen compute interfaces** — `QuantComputationInterface`,
  `BackendRouter`, `PythonQuantBackend`, `CppQuantAdapter` are only extended
  additively, never modified.
- ✅ **Explainability** — every new artifact exposes inputs + parameters +
  methodology version.
- ✅ **Python reference backend** — remains the only scientific source of
  truth; candidates are always validated against it.
- ✅ **C++ certified acceleration model** — C++ only ever appears as a
  validated candidate behind the router; Python fallback always available.

---

## 10. Implementation Order (Summary)

| Order | Phase | Work Package | Primary Gaps |
|-------|-------|--------------|--------------|
| 1 | 5.1 | WP-1 Certified Analytical Surface | G-C1, G-L1 |
| 2 | 5.1 | WP-4 Analytical Test Coverage | G-H1 |
| 3 | 5.2 | WP-2 Research Engine Facade | G-C2, G-M3, G-M4 |
| 4 | 5.3 | WP-3 Immutable Evidence Repository | G-H2, G-M2 |
| 5 | 5.3 | WP-5 Model Registry & Evaluation | G-C3 |
| 6 | 5.4 | WP-6 C++ Analytical Acceleration | G-H4 |
| 7 | 5.5 | WP-7 Performance Profile Pipeline | G-M1 |

---

*Phase 5 Architecture & Migration Plan — Version 1.0.0*
*Classification: Internal — Planning Document (no implementation)*

