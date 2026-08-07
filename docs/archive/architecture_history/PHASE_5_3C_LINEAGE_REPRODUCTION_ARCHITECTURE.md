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

# Phase 5.3c — Lineage Query & Reproduction Engine (Design)

**Status:** DESIGN ONLY — no code changes.
**Scope:** Make the existing evidence chain queryable (Lineage Query Engine) and
deterministically replayable (Reproduction Engine).
**Architecture base:** Phase 5.3a (Evidence & Lineage foundation) + Phase 5.3b.1–5.3b.5
(Dataset / Experiment / Run / Result / Validation emission).

---

## 1. Objective

Provide the institutional ability to **explain** and **reproduce** any certified
research artifact from its immutable evidence record:

```
Dataset ─feeds→ Experiment ─executes→ Run ─produces→ Result ─validates→ Validation
```

### 1.1 Query capability (`explain`)
Given any `artifact_hash`, return the complete upstream (ancestors) and downstream
(descendants) provenance as a typed, ordered graph.

### 1.2 Reproduction capability (`reproduce`)
Given a `result_hash`, deterministically:
1. locate the Result evidence,
2. resolve its parent Run,
3. resolve the Run's parent Experiment,
4. resolve the Experiment's parent Dataset,
5. recover exact parameters / configuration snapshots,
6. re-execute through the certified execution boundary,
7. generate a new Result,
8. compare hashes and report any difference.

---

## 2. Current Capabilities (Verified)

| Capability | Module | Present |
|-----------|--------|---------|
| Immutable scheme-2 `EvidenceEnvelope` | `researchos/evidence/envelope.py` | ✅ |
| Append-only `EvidenceRepository` (`evidence` + `lineage` tables) | `researchos/evidence/repository.py` | ✅ |
| `get_artifact(hash)` (by primary key) | `EvidenceRepository` | ✅ |
| `get_children(hash)` (edge parent→child) | `EvidenceRepository` | ✅ |
| `get_parents(hash)` (edge child→parent) | `EvidenceRepository` | ✅ |
| `verify_evidence()` (whole-store integrity) | `EvidenceRepository` | ✅ |
| `HASH_SCHEME_VERSION="2"` content-addressed hashing | `envelope.py` | ✅ |
| Dataset emission (`emit_dataset`) | `dataset_emission.py` | ✅ |
| Experiment emission (`emit_experiment`, `emit_experiment_with_dataset`) | `experiment_emission.py` | ✅ |
| Run emission (`emit_run`, `emit_run_for_experiment`) | `run_emission.py` | ✅ |
| Result emission (`emit_result`, `emit_result_for_run`) | `result_emission.py` | ✅ |
| Validation emission (`emit_validation`, `emit_validation_for_result`) | `validation_emission.py` | ✅ |
| Tamper verification (`envelope.verify()`) | `envelope.py` | ✅ |
| Contract immutability (params, config snapshots) | `experiments/result.py` (3.x) | ✅ |
| Deterministic run/result hashes (no wall-clock) | `experiments/result.py` | ✅ |
| Real dataset content-hash provenance in runner | `experiments/runner.py` | ✅ |

---

## 3. Architecture Diagram

```
                        ┌─────────────────────────────────────────────┐
                        │            EvidenceRepository (SQLite)      │
                        │  ┌──────────────┐    ┌──────────────────┐   │
                        │  │ evidence      │    │ lineage          │   │
    emit_*  ───────────▶│  │ artifact_hash │    │ parent_hash      │   │
   (phase 5.3b)         │  │ artifact_type │    │ child_hash       │   │
                        │  │ version       │    │ relation         │   │
                        │  │ payload       │    └──────────────────┘   │
                        │  │ parent_hashes │                           │
                        │  │ lineage_hash  │  (parent→child edges)     │
                        │  └──────────────┘                           │
                        └─────────────────────────────────────────────┘
                                        ▲
                                        │ get_artifact/get_parents/get_children
 ┌──────────────────────────────────────┴───────────────────────┐
 │                 Phase 5.3c (NEW, additive)                   │
 │  ┌──────────────────────────┐   ┌──────────────────────────┐ │
 │  │ LineageQueryEngine        │   │ ReproductionEngine       │ │
 │  │  - explain()              │   │  - reproduce(result_hash)│ │
 │  │  - ancestors()            │   │  - resolves chain        │ │
 │  │  - descendants()          │   │  - rebuilds configs      │ │
 │  │  - lineage_tree()         │   │  - re-executes certified │ │
 │  │  - resolve_reference()    │   │  - compares hashes       │ │
 │  └──────────────────────────┘   └──────────────────────────┘ │
 └──────────────────────────────────────────────────────────────┘
          │ upstream discovery                 │ replay boundary
          ▼                                    ▼
   immutable traversal (BFS/DFS)      CertifiedExecutionBoundary
   no mutation, no side writes       (QuantComputationInterface / Router)
```

---

## 4. Lineage Query Engine — API Proposal

New additive module `researchos/evidence/query_engine.py`.

### 4.1 Core queries

```
class LineageQueryEngine:
    def __init__(self, repository: Optional[EvidenceRepository] = None) -> None

    def explain(self, artifact_hash: str) -> LineageExplanation
        # Full upstream+downstream provenance as a typed graph.

    def ancestors(self, artifact_hash: str, *, depth: Optional[int] = None) -> List[EvidenceEnvelope]
        # Walk parents (BFS/DFS), return artifacts; order = canonical (e.g. BFS by type).

    def descendants(self, artifact_hash: str, *, depth: Optional[int] = None) -> List[EvidenceEnvelope]
        # Walk children, return artifacts.

    def lineage_tree(self, artifact_hash: str) -> LineageTreeNode
        # Nested (parent→[children]) recursive structure with envelopes + relation.
```

### 4.2 Supporting / enrichment helpers

```
def resolve_reference(self, artifact_hash_field: str, payload: Mapping[str, Any]) ->
        Optional[EvidenceEnvelope]
    # Given a payload and a reference key (e.g. "run_hash", "experiment_hash",
    # "result_hash"), fetch the referenced envelope when present.

def path(self, source_hash: str, target_hash: str) -> List[EvidenceEnvelope]
    # Deterministic path between two artifacts (BFS shortest), or [] if none.

def resolve_full_chain(self, result_hash: str) -> ReproducibleChain
    # Dataset → Experiment → Run → Result (+ optional Validation) resolution
    # via both the lineage edges AND the payload reference fields (redundant).
```

### 4.3 Result structures (immutable)

```
@dataclass(frozen=True)
class LineageExplanation:
    artifact: EvidenceEnvelope
    ancestors: Tuple[EvidenceEnvelope, ...]      # ordered upstream
    descendants: Tuple[EvidenceEnvelope, ...]    # ordered downstream
    relations: Tuple[LineageRelation, ...]       # parent, child, relation label
    verified: bool                               # envelope.verify() of all nodes

@dataclass(frozen=True)
class LineageTreeNode:
    artifact: EvidenceEnvelope
    relation: str            # relation by which this node is reached
    parents: Tuple["LineageTreeNode", ...]
    children: Tuple["LineageTreeNode", ...]

@dataclass(frozen=True)
class LineageRelation:
    parent_hash: str
    child_hash: str
    relation: str            # feeds / executes / produces / validates / trains
```

### 4.4 Determinism & safety guarantees
- Pure read-only: traversal performs **no writes**, no mutation of the repository.
- Deterministic ordering: children/parents are ordered by sorted `artifact_hash`; BFS levels are stable.
- Cycle-safe: the lineage table is a strict DAG by construction (append-only
  content-addressed parents cannot form cycles because a parent must exist before
  a child), but traversal still tracks a visited set defensively.
- Every returned envelope is passed through `envelope.verify()`; a tampered node
  surfaces as `verified=False` rather than being silently trusted.

---

## 5. Reproduction Engine — API Proposal

New additive module `researchos/evidence/reproduction.py`.

### 5.1 Public entry point

```
class ReproductionEngine:
    def __init__(
        self,
        repository: Optional[EvidenceRepository] = None,
        execution_boundary: Optional[Callable] = None,   # certified executor
    ) -> None

    def reproduce(self, result_hash: str) -> ReproductionReport:
        # Resolve chain, rebuild inputs, re-execute, compare hashes.
```

### 5.2 Resolution & rebuild pipeline

```
def _resolve_chain(self, result_hash: str) -> ReproducibleChain:
    # 1. result = repository.get_artifact(result_hash)
    #    - if None → ReproductionFailure("result not found")
    # 2. run = resolve via lineage parent(s) of result matching type "Run"
    #    - fallback: payload["run_hash"] reference
    # 3. experiment = resolve via lineage parent(s) of run matching type "Experiment"
    #    - fallback: run payload["experiment_hash"]
    # 4. dataset = resolve via lineage parent(s) of experiment matching type "Dataset"
    #    - (the only producer feeding Experiment)

def _rebuild_dataset(self, dataset_envelope) -> Any:
    # Reconstruct a ResearchDataset from the Dataset payload:
    #   feature_names, features, labels, metadata, sample_count,
    #   feature_count, label_name, version.
    # The payload already stores the FULL content → byte-identical reconstruction.

def _rebuild_configs(self, run_envelope) -> Tuple[SimulationConfig, DatasetConfig, dict]:
    # Reconstruct SimulationConfig / DatasetConfig from the run payload
    # config snapshots (dataset_config / simulation_config to_dict()),
    # plus the run parameters mapping.
    # Requires a deterministic from_dict for each config contract (see gap C).
```

### 5.3 Execution & comparison

```
def reproduce(self, result_hash: str) -> ReproductionReport:
    chain = self._resolve_chain(result_hash)             # fail fast w/ reason
    dataset = self._rebuild_dataset(chain.dataset)
    configs = self._rebuild_configs(chain.run)
    new_run = execution_boundary(dataset, configs)       # certified executor
    new_result = ...                                     # produce new Result
    new_hash = new_result.result_hash
    return ReproductionReport(
        reproduction_success=(new_hash == original_result_hash),
        original_hash=result_hash,
        reproduced_hash=new_hash,
        differences=_diff(original_payload, new_result_payload),
        rebuilt_chain=chain,
        executed_after_retry=False,   # single deterministic attempt
    )
```

### 5.4 Output

```
@dataclass(frozen=True)
class ReproductionReport:
    reproduction_success: bool
    original_hash: str
    reproduced_hash: str
    differences: Mapping[str, Any]     # field-level diff when mismatch
    rebuilt_chain: ReproducibleChain
    failure_reason: str = ""

@dataclass(frozen=True)
class ReproductionFailure(Exception):   # typed failures, never silent
    reason: str
```

---

## 6. Data Flow

```
reproduce(result_hash)
    │
    ├─ result = get_artifact(result_hash)              (must be type "Result")
    ├─ run    = LineageQueryEngine.resolve_full_chain(result_hash).run
    ├─ exp    = .experiment
    ├─ ds     = .dataset
    │
    ├─ verify each envelope (tamper gate) ── fail → ReproductionFailure
    │
    ├─ rebuild ResearchDataset from ds.payload
    ├─ rebuild SimulationConfig / DatasetConfig / params from run.payload
    │
    ├─ execute through certified boundary (single attempt)
    │
    ├─ produce new ExperimentResult (deterministic)
    │
    └─ compare new result_hash vs original
         ├─ equal  → ReproductionReport(success=True)
         └─ differ → ReproductionReport(success=False, differences=diff)
```

---

## 7. Current Gaps Audit

### 7.1 Missing references / resolution weaknesses
| # | Gap | Severity | Notes |
|---|-----|----------|-------|
| R1 | References in payloads (`run_hash`, `experiment_hash`, `result_hash`) are **not** queryable as foreign-key lookups; only the `lineage` edges are traversable. | Medium | `resolve_reference()` must be added; payload fields are plain strings, not indexed. |
| R2 | Result→Run and Run→Experiment rely on **either** the `lineage` edge **or** the payload reference. The two can diverge after tampering. | Medium | Redundant cross-check required in `resolve_full_chain`; report discrepancies. |
| R3 | Dataset→Experiment is only present if `emit_experiment_with_dataset` (or `attach_dataset_parent`) was used; a bare `emit_experiment` stores **no** Dataset parent. | High | Reproduction of a Result whose Experiment lacks a Dataset parent **cannot** resolve the dataset → documented failure. |

### 7.2 Missing indexes
| # | Gap | Severity | Notes |
|---|-----|----------|-------|
| I1 | No index on `lineage.parent_hash` / `lineage.child_hash` beyond the default. | Low | For small stores SQLite scan is fine; add additive indexes only if queries profile hot. |
| I2 | No index on `evidence.artifact_type`. | Low | Needed only for type-filtered queries (explain/type scanning). |
| I3 | No composite index to resolve a payload reference field → artifact. | Medium | Functionally covered by `get_artifact(hash)` primary key; a reference index is an optimization, not required. |

### 7.3 Missing APIs
| # | Gap | Severity | Notes |
|---|-----|----------|-------|
| A1 | No `explain`/`ancestors`/`descendants`/`lineage_tree` queries | High | Core of Phase 5.3c query engine. |
| A2 | No `resolve_reference` to turn a payload ref into an envelope | High | Needed for R1/R2. |
| A3 | No typed, ordered traversal (BFS-safe, cycle-safe) | Medium | `get_parents/get_children` are raw-hash only. |
| A4 | No `reproduce(result_hash)` entry point | High | Core of reproduction engine. |

### 7.4 Missing metadata required for reproduction
| # | Gap | Severity | Notes |
|---|-----|----------|-------|
| M1 | Config contracts lack a **deterministic `from_dict`** to reverse the recorded `to_dict()` snapshot into a live `SimulationConfig`/`DatasetConfig`. | **High** | Reproduction literally cannot rebuild exact configs without it. Additive `from_dict` classmethods required (Phase 5.3c impl). |
| M2 | The certified execution boundary is not explicitly referenced by any evidence artifact (no `executor_version` in the run/result payload). | Medium | Add an optional `backend_identity`/`executor_version` to Run insert (already a supported field) so replay pins the exact certified boundary. |
| M3 | No canonical `ResearchDataset.from_payload` to rebuild a dataset from a Dataset envelope payload. | Medium | Add a deterministic reconstruction (payload already carries full content). |
| M4 | Experiment payload stores `simulation_config`/`dataset_config` snapshots; these must round-trip exactly for hash parity. | Medium | Requires M1; timestamps already excluded. |

### 7.5 Determinism risks
| # | Risk | Severity | Mitigation |
|---|------|----------|-----------|
| D1 | Backend identity not pinned → replay may use a different (newer) certified backend with different numerics. | Medium | Record `backend_identity` at emission (M2); reproduction asserts same identity or flags mismatch. |
| D2 | Config snapshot ordering / dict insertion order could destabilize `from_dict` reconstruction. | Medium | Canonicalize via existing `_to_primitives` (sort keys) + strict `from_dict` that tolerates missing→default. |
| D3 | Any wall-clock / telemetry leaking into a rebuilt config would break parity. | High | Rebuild path must ONLY read the hashed payload, never `created_at`; reuse the run/result hash rules. |
| D4 | Dataset reconstruction float coercion (payload stores floats) must be bit-identical. | Low | Payload already stores `float` values; reuse the same parsing as emission (no re-rounding). |

---

## 8. Failure Handling

| Condition | Behaviour |
|-----------|-----------|
| `result_hash` not found | `ReproductionFailure("result not found")` |
| Result has no Run parent (lineage or ref) | `ReproductionFailure("run not resolved")` |
| Chain contains a tampered envelope (`verify()` False) | `ReproductionFailure("tampered artifact")` — never reproduce from untrusted input |
| Dataset parent missing (bare `emit_experiment`) | `ReproductionFailure("dataset not resolved")` |
| Config contract lacks `from_dict` | `ReproductionFailure("config from_dict unavailable")` |
| Re-execution raises | `ReproductionFailure("execution failed: <err>")` |
| Re-execution succeeds but hash differs | `ReproductionReport(success=False, differences=...)` — this is a legitimate scientific finding (not an exception) |
| Lineage cycle detected (defensive) | `lineage_tree`/reproduce aborts with `ReproductionFailure("cycle detected")` |

**Principle:** a failed or divergent reproduction is a **first-class result**, not an
exception. Only genuine errors (not found, tampered, missing resolver) raise typed
`ReproductionFailure`.

---

## 9. Security / Tamper Considerations

1. **Tamper gate before reproduction:** every envelope in the resolved chain is
   passed through `envelope.verify()` (recompute scheme-2 `lineage_hash`). Any
   mismatch aborts reproduction — a tampered prior artifact can never be silently
   replayed.
2. **Whole-store audit:** reuse `EvidenceRepository.verify_evidence()` as a pre-check
   gate and for the future audit surface.
3. **Append-only preservation:** query/reproduction are **read-only**; nothing is
   written. Reproduction does NOT re-emit the new result (unless a future explicit
   "reproduce-and-record" API is requested). This preserves the append-only philosophy.
4. **Hash scheme pinning:** scheme-2 content addressing means a reproduced artifact
   only equals the original if the *entire* certified surface and inputs are identical.
5. **No bypass of the trust boundary:** execution goes through the certified executor
   (QuantComputationInterface/Router); the reproduction engine never shortcuts.

---

## 10. Migration Plan

`Phase 5.3c` is **strictly additive** — no existing contract, envelope, repository
schema (beyond optional indexes), or emission module is modified.

| Step | Change | Additive? |
|------|--------|-----------|
| 1 | Add `from_dict` to `SimulationConfig` / `DatasetConfig` contracts | ✅ (new classmethods) |
| 2 | Add `ResearchDataset.from_payload` reconstruction helper | ✅ (new) |
| 3 | Create `query_engine.py` (`LineageQueryEngine` + result structures) | ✅ (new) |
| 4 | Create `reproduction.py` (`ReproductionEngine` + `ReproductionReport`) | ✅ (new) |
| 5 | Export new classes from `researchos/evidence/__init__.py` | ✅ (additive) |
| 6 | **Optional** additive indexes on `lineage(parent_hash)`, `lineage(child_hash)`, `evidence(artifact_type)` | ✅ (additive schema bump, no data rewrite) |
| 7 | Add deterministic tests (`test_lineage_query_engine.py`, `test_reproduction_engine.py`) | ✅ (new) |
| 8 | Emit `backend_identity`/`executor_version` at Run/Result emission (adopt existing optional field) | ✅ (caller-side addition, no contract change) |
| 9 | Evidence report + GO/NO-GO | ✅ (doc) |

### Backward compatibility
- Existing stamped evidence remains valid; only new additive methods are introduced.
- Existing `get_artifact/get_parents/get_children` untouched.
- No schema migration that rewrites/deletes existing rows.

---

## 11. Implementation Steps (Recommended Order)

1. **Contract resolvers** — `SimulationConfig.from_dict`, `DatasetConfig.from_dict`,
   `ResearchDataset.from_payload` (unblocks reproduction).
2. **Lineage Query Engine** — `resolve_reference`, `ancestors`, `descendants`,
   `lineage_tree`, `explain`, `resolve_full_chain` (read-only, tested).
3. **Reproduction Engine** — `reproduce(result_hash)` with failure handling + diff
   (depends on 1 & 2).
4. **Reproduction test fixture** — emit a full chain (Dataset→Experiment→Run→Result→Validation),
   reproduce, assert identical hash; then tamper / mutate a link and assert failure.
5. **Optional indexes** — additive schema bump if hot-path profiling justifies.
6. **Backend pinning** — adopt optional `backend_identity` in Run/Result emission to
   harden determinism (D1).
7. **Evidence report** — `docs/PHASE_5_3C_LINEAGE_REPRODUCTION_REPORT.md` + GO/NO-GO.

---

## 12. Findings & Recommended Order (Executive Summary)

### Findings
- **Foundation is solid:** append-only content-addressed evidence, tamper
  verification, deterministic hashes, and full emission chain are already in place.
- **Query is low-risk additive:** a read-only `LineageQueryEngine` over the existing
  `get_parents/get_children` is straightforward; the only substantive gap is a
  `resolve_reference` helper to reconcile payload refs with lineage edges (R1/R2).
- **Reproduction has one critical blocker:** config contracts lack deterministic
  `from_dict` (M1), so the recorded `to_dict()` snapshots cannot yet be rebuilt into
  live configs. This must be added before reproduction works end-to-end.
- **Reproducibility edge:** a bare `emit_experiment` (no Dataset parent) makes a
  Result non-reproducible (R3) — worth a `resolve_full_chain` warning and a documented
  failure reason.
- **Determinism hardening:** pinning `backend_identity`/`executor_version` at
  emission (M2) is the highest-value next hardening beyond the interfaces.

### Recommended implementation order
1. Additive `from_dict` / `from_payload` resolvers (contracts).
2. `LineageQueryEngine` (read-only queries) + tests.
3. `ReproductionEngine` + full-chain reproduction tests.
4. Optional additive indexes.
5. Backend-identity pinning at emission.
6. Evidence report + GO/NO-GO.

No code changes made in this phase. This is a design document only.

---

*Phase 5.3c Lineage Query & Reproduction Engine — Design Document*
*Classification: Internal — Design Only (no implementation)*

