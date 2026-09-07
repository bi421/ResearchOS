# ResearchOS Architecture

## Data Flow (Canonical)

DATA
  ↓
VALIDATION
  ↓
STRUCTURED DATA
  ↓
MARKET MEMORY
  ↓
QUANTITATIVE ANALYSIS
  ↓
MARKET CONTEXT
  ↓
RESEARCH
  ↓
EXPERIMENT
  ↓
EVALUATION
  ↓
EVIDENCE
  ↓
INTELLIGENCE
  ↓
FUTURE LEARNING
  ↓
PROBABILITY

## Implementation Status (2026-09-07)

| Component | Status | Evidence |
|-----------|--------|----------|
| Data Engine | ✅ CURRENT | `researchos/data_engine/` — validation, dataset contracts, SQLite |
| Market Memory | ⚠️ TRANSITIONAL | `researchos/market_memory/` — event, outcome, conditioning, matching and evidence primitives exist |
| Quant Engine | ✅ CURRENT | Python reference backend + certified C++ acceleration path |
| Decision Engine | ✅ CURRENT | evidence scoring, probability assessment and decision contracts |
| Macro Intelligence | ✅ CURRENT | macro analysis and regime components |
| Intelligence | ✅ CURRENT | EvidenceGraph and reasoning components |
| Evidence / Lineage | ⚠️ RUNTIME WIRING | Dataset/Experiment/Run/Result/Validation emission primitives exist; core experiment runtime is not yet automatically persisted to the evidence repository |
| Future Learning | ❌ FUTURE | Not implemented intentionally |

## Verified Capabilities

| Capability | Status |
|------------|--------|
| Deterministic research execution boundary | ✅ |
| Dataset provenance/content hashing | ✅ |
| Experiment → execution → evidence lineage primitives | ✅ |
| Evidence envelope hash scheme 2 | ✅ |
| Run → Result lineage | ✅ |
| Object registry collision protection | ✅ |
| Timezone resolution with explicit failure | ✅ |
| Python/C++ certified backend routing | ✅ |
| Package-local market-memory/data-engine/Phase 5.1 tests in CI | ✅ |
| C++ test failures propagate to CI | ✅ |
| Calibrated probability | ❌ |
| Autonomous trading / broker execution | ❌ by design |

## Critical Invariants

- ✅ NO PREDICTIVE INTELLIGENCE WITHOUT VALIDATED HISTORICAL EVIDENCE
- ✅ DETERMINISTIC: Same inputs → same outputs
- ✅ IMMUTABLE: Completed experiments cannot be mutated
- ⚠️ PROBABILITY: Current score is heuristic, not calibrated probability
- ✅ NO BROKER EXECUTION

## Architecture Guards

- ✅ `quant_engine` must not depend on `decision_engine`
- ✅ `core` must not depend on high-level intelligence
- ✅ experiments must not mutate configurations
- ✅ evidence envelopes preserve deterministic lineage
- ✅ learning remains future/unimplemented
- ✅ broker execution does not exist
- ⚠️ synthetic-data gates require continued strengthening

## Next Implementation Milestone

### Runtime Evidence Certification

Wire the existing evidence emission layer into the production experiment path without changing scientific calculation semantics:

```text
Experiment
   ↓
Run
   ↓
Result
   ↓
EvidenceRepository
```

Required properties:

1. deterministic artifact identity
2. explicit parent/child lineage
3. append-only persistence
4. no timestamp/runtime telemetry in identity hashes
5. evidence emission failure must not silently produce an uncertified result when certification is explicitly enabled
6. existing experiment/result hashes and quantitative semantics remain unchanged

## Following Milestones

1. Complete runtime evidence certification.
2. Strengthen synthetic-data gates.
3. Complete Market Memory → Research integration.
4. Build the XAUUSD event → outcome probability pipeline.
5. Add calibration and baseline comparison.
6. Only after validated evidence, expose higher-level decision intelligence.

## Protected Scientific Surfaces

Do not modify without a demonstrated scientific defect and explicit architectural review:

- execution hash scheme
- decision methodology / `DECISION_V1`
- walk-forward arithmetic and leakage checks
- cost-model semantics
- backend certification/routing behavior
- C++ numerical implementation
- matcher feature weights
- broker execution boundary
