# ResearchOS Architecture Re-Audit — 2026-09-07

## Scope

Re-audit the canonical architecture after the CI Ruff regression fix. The audit focused on dependency boundaries, data/provenance flow, evidence lineage, deterministic execution, and CI enforcement.

## Verified Findings

### 1. CI baseline — PASS

- Ruff configuration is centralized in `pyproject.toml`.
- `pyproject.toml` selects `E`, `F`, `W` and intentionally ignores `E501`.
- CI invokes `ruff check --statistics`, so the workflow now respects the repository lint contract.
- Python Tests run completed successfully on commit `d6b4a6c7bdbc00e00f87ed4654ad48b39affd317`.
- CI run 89 completed successfully on the same commit.

### 2. Research execution boundary — PASS

`researchos/research_execution.py` enforces a validated-data boundary:

`ResearchInput → ValidatedDatasetRef → ResearchSeries → operation → ResearchExecutionResult`

The operation receives `ResearchSeries`, not `HistoricalDataset`. Execution identity binds research ID, dataset ID, dataset content hash, dataset hash, methodology version, and deterministic result content.

### 3. Evidence lineage — IMPLEMENTED FOUNDATION

The evidence package now contains deterministic emission surfaces for Dataset, Experiment, Run, Result, and Validation artifacts. Evidence envelopes are immutable and content-addressed under hash scheme 2. Run → Result and Experiment → Run lineage helpers are present.

The remaining architectural gap is **runtime certification wiring**: the generic experiment runner does not automatically persist these evidence artifacts into an injected evidence repository. The emission primitives exist, but certification remains opt-in/outside the core runner path.

### 4. Timezone integrity — PASS

`researchos/data_engine/timezone.py` now resolves IANA zones through `zoneinfo` and raises `TimezoneResolutionError` for unknown IANA-like names or invalid timezone values. There is no silent UTC fallback.

### 5. Object registry disambiguation — PASS

Registry tests pin the mapping of legacy serialized object types to the objects-layer classes and ensure renamed market-memory classes are not registered under colliding types.

### 6. Quant boundary — PASS

The experiment runner routes computation through `BackendRouter`. The Python backend remains the scientific reference and C++ is an acceleration path. The existing C++/Python parity and architecture guard suite remain protected.

### 7. Package-local test coverage in CI — PASS

The Python workflow currently includes the package-local data-engine, market-memory, and Phase 5.1 test roots in addition to the main integration/unit suites.

### 8. C++ test failure propagation — PASS

The current C++ workflow uses direct `ctest --output-on-failure` execution rather than masking failures with `|| echo`.

## Architecture Decision

Do **not** make further cosmetic refactors or manually shorten intentional dashboard/template lines. The current system has sufficient architectural boundaries to move to the next substantive milestone.

The next implementation milestone is:

**Runtime Evidence Certification**

Target flow:

`Experiment → Run → Result → EvidenceRepository`

with deterministic artifact hashes and explicit lineage, while preserving the existing scientific result hashes and computation semantics.

## Protected Scientific Surfaces

The following remain frozen unless a demonstrated scientific defect is found:

- execution hash scheme
- decision methodology and current heuristic score semantics
- walk-forward arithmetic and leakage checks
- cost-model semantics
- backend certification/routing behavior
- C++ numerical implementation
- matcher feature weights
- broker execution boundary

## Re-Audit Verdict

**Architecture foundation: READY FOR RUNTIME EVIDENCE CERTIFICATION.**

No new critical dependency-boundary defect was found during this re-audit. The highest-value remaining architectural gap is production wiring of the already-implemented evidence emission layer.
