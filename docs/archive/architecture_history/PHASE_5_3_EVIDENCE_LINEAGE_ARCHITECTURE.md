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

# Phase 5.3 — Evidence & Lineage Architecture Design

**Status:** DESIGN ONLY (no implementation)
**Scope:** Evidence Repository architecture, Lineage Graph data model, artifact
types, hash & provenance strategy, storage strategy on the existing
`ResearchRepository`, and migration impact analysis.
**Base guarantees (already certified):**
- deterministic dataset identity (content hash)
- deterministic `experiment_hash`
- deterministic `run_hash` (logical identity, timing-excluded)
- deterministic `result_hash`
- immutable experiment artifacts (read-only mapping views)
- serialization integrity verification (`from_dict` + `verify_result_hash`)

**Constraints honored:**
- Preserve current contracts (no changes to `ExperimentRun`/`ExperimentResult`
  / router / submodules).
- No implementation in this document.
- No ML features (no model training, no stochastic fitting).
- No execution changes (no change to the certified compute path).

---

## Architecture Proposal

We layer a **read-mostly, append-only evidence store** and a **lineage graph**
on top of the existing `ResearchRepository`. The existing repository already
provides:
- a generic `objects` table (id, object_type, created_at, data JSON),
- an append-only, hash-chained `audit_logs` table with tamper detection,
- schema-versioned migrations, WAL mode, and a retry-capable transaction
  context.

The Phase 5.3 layer adds **two new tables** and a **thin facade** — it does not
modify any existing table or object contract. It treats every certified
artifact (Dataset, Feature, Experiment, Run, Result, Validation, Model) as an
**immutable, content-addressed record** whose identity key is its deterministic
hash, and records **parent→child edges** in a separate lineage table.

```
┌──────────────────────────────────────────────────────────────┐
│  Certified compute + workflow layer (unchanged)              │
│  Dataset → Feature → Experiment → Run → Result → Validation  │
│  (deterministic hashes; immutable; serialization-verified)   │
└───────────────────────────────┬──────────────────────────────┘
                                │ emit(artifact, parent_hashes)
                                ▼
┌──────────────────────────────────────────────────────────────┐
│  EvidenceRepository (new facade, thin)                       │
│  • append_artifact(artifact)  → immutable evidence record    │
│  • add_edge(parent_hash, child_hash, relation) → lineage     │
│  • query lineage / replay / verify                           │
└───────────────────────────────┬──────────────────────────────┘
                                │ uses existing tables + 2 new
                                ▼
┌──────────────────────────────────────────────────────────────┐
│  ResearchRepository (existing, unchanged)                    │
│  • objects        (payloads, content-addressed)              │
│  • audit_logs     (append-only tamper-evident chain)         │
│  • evidence       (NEW: artifact envelope + lineage hash)    │
│  • lineage        (NEW: parent→child edges)                  │
└──────────────────────────────────────────────────────────────┘
```

**Design principles**
1. **Append-only.** Records are inserted once; updates/removes are forbidden
   (mirrors the audit trail). A new artifact with a changed hash is a *new*
   record, never an in-place edit.
2. **Content-addressed.** The primary key of an artifact record is its
   deterministic content hash (canonical SHA-256 via the existing
   `deterministic_hash`/`backend_hash` machinery). This gives deduplication and
   reproducibility for free.
3. **Lineage is edges, not nesting.** A separate `lineage` table stores
   `(parent_hash, child_hash, relation)` so any graph traversal is possible
   without re-parsing JSON blobs.
4. **Uniform envelope.** Every artifact exposes the explainability contract:
   inputs + parameters + methodology version (already true of `ExperimentRun`
   and `ExperimentResult`; extended uniformly to Dataset/Feature/Validation/
   Model).
5. **Tamper-evident.** Each artifact record carries a lineage hash that binds
   its content hash to its parent hashes; the existing `audit_logs` chain
   records every append.

---

## Data Model

### Artifact types (7)

| Artifact | Source / identity | Fields (envelope) |
|----------|-------------------|--------------------|
| **Dataset** | Raw OHLCV / bars; `dataset_version` = content hash | `dataset_hash`, `schema`, `row_count`, `fingerprint`, `source` |
| **Feature** | `machine_learning/features` deterministic features | `feature_hash`, `feature_names`, `parameters`, `input_dataset_hash` |
| **Experiment** | `Experiment` definition | `experiment_hash`, `hypothesis_id`, `dataset_config`, `simulation_config`, `status` |
| **Run** | `ExperimentRun` | `run_hash`, `experiment_hash`, `parameters`, `config_snapshots`, `result_hash` |
| **Result** | `ExperimentResult` | `result_hash`, `run_hash`, `metrics`, `statistics`, metadata |
| **Validation** | `validation/walk_forward` | `validation_hash`, `result_hash`, `fold_count`, `metrics`, `params` |
| **Model** (research-only, deterministic) | deterministic model registry metadata | `model_hash`, `model_type`, `parameters`, `feature_hash`, `training_hash` |

All artifacts share the **EvidenceEnvelope**:

```
EvidenceEnvelope {
  artifact_type: str          # one of the 7
  artifact_hash: str          # canonical content hash (primary key)
  version: str                # methodology / surface version
  created_at: str             # observational telemetry (NOT hashed)
  payload: dict               # the canonical artifact content
  parent_hashes: list[str]    # input artifact hashes (provenance)
  lineage_hash: str           # hash(payload + sorted parent_hashes)
}
```

### Tables (new)

**Table `evidence`** (append-only, content-addressed):
```
evidence(
  artifact_type TEXT NOT NULL,
  artifact_hash TEXT PRIMARY KEY,     -- canonical content hash
  version TEXT NOT NULL,
  created_at TEXT NOT NULL,           -- observational, not hashed
  payload TEXT NOT NULL,              -- JSON of canonical content
  parent_hashes TEXT NOT NULL,        -- JSON list
  lineage_hash TEXT NOT NULL          -- hash(payload, sorted parents)
)
CREATE INDEX idx_evidence_type ON evidence(artifact_type)
```

**Table `lineage`** (append-only edges):
```
lineage(
  parent_hash TEXT NOT NULL,
  child_hash   TEXT NOT NULL,
  relation     TEXT NOT NULL,          -- 'feeds' | 'executes' | 'produces' | 'validates' | 'trains'
  created_at   TEXT NOT NULL,
  PRIMARY KEY (parent_hash, child_hash, relation)
)
CREATE INDEX idx_lineage_child ON lineage(child_hash)
```

Existing tables reused unchanged: `objects` (payload discoverability),
`audit_logs` (append/editing events), `_schema_version` (versioning).

---

## Lineage Flow

The canonical scientific workflow maps to lineage edges as follows:

```
 Dataset ──feeds──▶ Feature ──?──▶ Dataset(featured)
 Dataset ──feeds──▶ Experiment ──executes──▶ Run ──produces──▶ Result
 Result  ──validates──▶ Validation
 Feature ──trains──▶ Model    (deterministic research model only)
 Model   ──produces──▶ Prediction (validation/prediction surface)
```

Concrete chain for a single research cycle:

1. `append_artifact(Dataset)` → `artifact_hash = dataset_version`.
   - No parents (root node).
2. `append_artifact(Feature, parents=[dataset_hash])` →
   `add_edge(dataset_hash, feature_hash, "feeds")`.
3. `append_artifact(Experiment)` → `artifact_hash = experiment_hash`.
4. `append_artifact(Run, parents=[experiment_hash, dataset_hash])` →
   `add_edge(experiment_hash, run_hash, "executes")`,
   `add_edge(dataset_hash, run_hash, "feeds")`.
5. `append_artifact(Result, parents=[run_hash])` →
   `add_edge(run_hash, result_hash, "produces")`.
6. `append_artifact(Validation, parents=[result_hash])` →
   `add_edge(result_hash, validation_hash, "validates")`.
7. (Optional, deterministic research models) `append_artifact(Model, parents=[feature_hash])`.

**Traversal queries** (on `lineage`, not JSON):
- `ancestors(hash)` → repeated child→parent lookups.
- `descendants(hash)` → repeated parent→child lookups.
- `reproduce(result_hash)` → walk parents to recover exact Dataset + params +
  methodology version, then re-run the certified pipeline and confirm the
  recomputed `result_hash` matches the stored hash.

The `lineage_hash` on each evidence record binds the artifact to its parents,
so a tampered parent link is detectable by recomputation.

---

## Hash and Provenance Strategy

**Canonical hashing.** Reuse the existing deterministic machinery —
`researchos.core.identity.deterministic_hash` for experiments/runs/results and
the `backend_hash` canonicalizer for research analytical outputs. Every
artifact hash is a canonical SHA-256 over a sorted, stable serialization of its
content (no timestamps, no wall-clock, no randomness).

**Provenance chain.**
- `dataset_hash` = content hash of the dataset bytes.
- `feature_hash` = hash(features, params, dataset_hash).
- `experiment_hash` = hash(hypothesis_id, dataset_config, simulation_config).
- `run_hash` = hash(experiment_hash, run_number, params, config snapshots,
  result_hash) — logical identity only (W1 closure).
- `result_hash` = hash(run_id, metrics, statistics, performance, metadata).
- `validation_hash` = hash(result_hash, fold params, aggregate metrics).
- `model_hash` = hash(model_type, parameters, feature_hash).

**Dual-key integrity.** Each artifact has:
1. **content hash** (self-contained identity), and
2. **lineage hash** (binds content to parent hashes).

Both are stored; verification recomputes both and compares. This mirrors the
existing `verify_audit_chain()` / `detect_tampering()` pattern already present
in `ResearchRepository`.

**Time is telemetry only.** Timestamps (`created_at`, `completed_at`) are
stored but never fed into any hash, preserving determinism exactly as the
Phase 5.2 closure established.

---

## Storage Strategy (using existing ResearchRepository)

The Phase 5.3 layer is a **subclass or thin facade** over `ResearchRepository`
(no changes to the base class):

- **Reuse** the existing `_transaction()` retry context, WAL mode, foreign
  keys, `_schema_version` migration runner, and `_get_conn`/`_reconnect`.
- **Add** a migration `_migrate_v2_to_v3` creating the two new tables
  (`evidence`, `lineage`), following the exact `MIGRATIONS` dict pattern already
  in place (bump `SCHEMA_VERSION` 2 → 3, additive only).
- **Register** the new artifacts in `OBJECT_REGISTRY` so `load_object` /
  `load_by_type` can rehydrate them (additive entries only).
- **Still save** artifacts to the existing `objects` table for generic
  discoverability (matching how `save_audit_entry` dual-writes to both
  `audit_logs` and `objects`).
- **Reuse** `save_audit_entry` to record every append (append →
  `AuditEntry(action="evidence_append", object_id=artifact_hash)`), so the
  evidence store is both append-only and tamper-evident through the existing
  chain.

**RepositoryInterface compatibility.** The facade implements `save`, `get`,
`get_all`, `delete` (delete is a no-op/refused for evidence to preserve
append-only), `find_by_tag`, and `count` to remain a drop-in
`RepositoryInterface` implementation.

---

## Migration Plan

**Phase 5.3a — Schema & Facade (additive)**
1. Bump `SCHEMA_VERSION` 2 → 3; add `_migrate_v2_to_v3` creating `evidence`
   and `lineage` tables (IF NOT EXISTS).
2. Add `EvidenceEnvelope` + 7 `EvidenceRecord` subclasses (Dataset, Feature,
   Experiment, Run, Result, Validation, Model) with `to_dict`/`from_dict`.
3. Add `EvidenceRepository(ResearchRepository)` facade with
   `append_artifact`, `add_edge`, `ancestors`, `descendants`, `reproduce`,
   `verify_evidence`.
4. Register new artifact classes in `OBJECT_REGISTRY`.
5. Add append-only tests (no update/delete; lineage traversal; tamper
   detection; determinism).

**Phase 5.3b — Wiring (hook points only, no behavior change)**
6. Emit `Experiment`/`Run`/`Result` artifacts from the existing runner glue
   (read-only observation; no change to compute).
7. Emit `Dataset`/`Feature`/`Validation` artifacts from existing producers.
8. Backfill: re-index already-produced result hashes as evidence records
   (append-only snapshot).

**Phase 5.3c — Verification**
9. Deterministic replay test: recompute lineage from stored artifacts and
   confirm hashes match.
10. Full suite green; no contract changes; no execution changes.

**Rollback.** Schema migration is additive (`IF NOT EXISTS`); dropping the two
tables returns to Phase 5.2 state without touching any existing data.

---

## Risks

| # | Risk | Likelihood | Impact | Mitigation |
|----|------|-----------|--------|------------|
| R1 | Schema migration (v2→v3) breaks existing data | Low | High | Additive `IF NOT EXISTS` tables only; ordered migration runner already tested; rollback by dropping only new tables |
| R2 | Content-hash key collisions / non-canonical serialization | Low | High | Reuse existing canonicalizer + `deterministic_hash`; sort keys; add determinism tests; reject non-canonical payloads |
| R3 | Lineage graph becomes unbounded (fork/explosion) | Medium | Medium | Index on `child_hash`; enforce `parent_hashes` bounded; snapshot/compaction for old runs |
| R4 | `reproduce()` divergence (replay ≠ stored hash) | Medium | High | Hash must cover all inputs (W1-closed); versioned methodology token in envelope; replay gate before trust |
| R5 | Append-only enforcement bypassed | Medium | Medium | Facade refuses `delete`/update for `evidence`; audit hook on every write; `detect_tampering` on lineage |
| R6 | Scope creep into ML | Medium | High | Model artifact is metadata-only (deterministic families only); no training/prediction execution added; explicit whitelist |
| R7 | Dual-write (objects + evidence + audit) consistency | Medium | Medium | Reuse existing `_TransactionContext` for atomic multi-table writes; add `verify_dual_storage_consistency`-style check |
| R8 | Performance of ancestor/descendant traversal on large graphs | Low–Med | Medium | Indexed edges; batch lookups; optional materialized paths later (additive) |

---

*Phase 5.3 Evidence & Lineage Architecture — Design v1.0.0*
*Classification: Internal — Design Document (no implementation)*
