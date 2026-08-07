# ResearchOS — Architecture Freeze v2

**Status:** FROZEN (design only — no implementation)
**Classification:** Internal — Constitutional Reference for all future development
**Supersedes:** ResearchOS V1 Architecture Freeze (3f4510f) + Phase 5.1–5.3c verified stack
**Assumed complete & verified (treated as frozen):** deterministic core, immutable
contracts, certified BaseExperimentRunner, evidence repository, lineage graph,
reproduction engine, Hash Scheme v2, 2500+ passing tests.
**Authority:** Chief Architect. This document governs every future implementation.

---

# SECTION 1 — Frozen Core

Every subsystem below is **permanently frozen**. Purpose, owner, public
responsibility, explicit non-responsibilities, allowed extensions, and forbidden
modifications are fixed.

| Subsystem | Purpose | Owner | Public responsibility | Explicit non-responsibilities | Allowed future extensions | Forbidden modifications |
|-----------|---------|-------|------------------------|-------------------------------|---------------------------|-------------------------|
| Deterministic core | Identity, hashing, canonicalization, lifecycle | Core Infrastructure | Deterministic identity + hash derivation; immutable lifecycle | No computation policy; no trading | Additive hash-scheme versions (v3+) | Changing hash v2 semantics, re-hashing history |
| Immutable contracts | Experiment/Run/Result value objects | Experiment Framework | Immutable, versioned, hash-bearing result containers | No numeric computation | Add fields (defaults); additive subclasses | Removing fields, mutating existing hashes |
| Certified BaseExperimentRunner | Orchestration-only experiment execution | Experiment Framework | Build request, delegate compute, package result | No price extraction, no CSV, no math, no trading | Subclassing for new orchestration patterns | Altering `_execute_simulation` core |
| BackendRouter + NumericalComparator | Trust boundary + certified parity | Compute | Select/validate/fail-over candidates; parity gate | No trading, no ML inference | New candidate backends (additive) | Weakening parity, bypassing reference |
| Evidence Repository | Append-only artifact store | Evidence | Append-only stores, tamper verification, dedup | No mutation, no delete, no lineage computation | New artifact types (additive schema) | In-place update/delete; changing hash v2 |
| Lineage Graph | Provenance traversal | Evidence | Authoritative parent/child edges; ancestors/descendants | No storage ownership, no selection/query | New edge kinds (additive) | Reassigning provenance authority |
| Reproduction Engine | Deterministic re-execution | Evidence | resolve chain, verify, reconstruct, re-run, compare hash | No new algorithms; no model execution | New artifact resolvers (additive) | Changing result-hash comparison |
| Hash Scheme v2 | Canonical content addressing | Core Infrastructure | Stable, versioned, deterministic artifact hashes | No semantic meaning in hashes | v3 additive scheme | Mutating v2 outputs in place |
| PythonQuantBackend | Reference computation truth | Compute | Source-of-truth math for all 7 quant ops | No trading, no ML, no stochastic | Additive ops (new interface) | Changing existing op semantics |
| Analytical engines (technical, probability, portfolio, historical, fundamental, econometrics) | Deterministic research math | Compute | Deterministic formulas; certified surface | No trading, no broker, no signal | Additive indicators/models (certified) | Changing existing formula output |

---

# SECTION 2 — Layer Definition

Official layers (top → bottom). Each layer: purpose, inputs, outputs, dependencies,
**forbidden dependencies**.

| Layer | Purpose | Inputs | Outputs | Dependencies | Forbidden dependencies |
|-------|---------|--------|---------|--------------|------------------------|
| **Presentation** | Human/API surface | Queried, ranked results | Reports, dashboards, notebooks, API responses | Research Workflow, Knowledge, Query | **Never** Compute, Evidence raw, Storage |
| **Research Workflow** | Compose scientific studies | Dataset, config, methodology | Workflow runs, experiment requests | Knowledge, Evidence, Configuration | **Never** computes statistics/metrics; **never** touches Storage directly |
| **Knowledge** | Ontology, graph, meta-analysis synthesis | Evidence, Query, Statistics | Conclusions, graph edges, explainability | Evidence, Statistics, Configuration | **Never** computes raw math; **never** owns raw artifacts |
| **Evidence** | Append-only artifacts, lineage, reproduction | Any frozen artifact | Hashed envelopes, lineage, verified repro | Storage, Configuration, Identity | **Never** derives scientific conclusions |
| **Execution** | Orchestrate compute (certified runner) | Experiment request, dataset | Run/Result | Compute, Evidence, Configuration | **Never** computes math; **never** owns metrics |
| **Compute** | Own all numeric math | Dataset contract, request | SimulationResult, analytical output | Configuration, Identity | **Never** stores; **never** formats for presentation |
| **Storage** | Backend-independent persistence | Artifacts, blobs | Persisted records | Infrastructure | **Never** owns lineage/identity policy |
| **Infrastructure** | Scheduler, task queue, concurrency | Operation requests | Scheduled execution | Configuration | **Never** owns scientific logic |
| **Configuration** | Versioned methodology/param authority | Definition requests | Version-locked config snapshots | Identity | **Never** owns computation |

**Forbidden dependency directions (global):**
- Any layer may never depend **upward** (Presentation → none; Workflow → none; etc.).
- No layer may bypass its adjacent layer to reach a lower one (e.g., Presentation → Storage).
- Compute and Evidence are **mutually segregated**: Compute never writes evidence directly;
  the Runner/Workflow bridges them.

---

# SECTION 3 — Single Source of Truth

One owner per concept. Conflicts are resolved below.

| Concept | Sole owner | Conflict to resolve | Resolution |
|---------|-----------|---------------------|------------|
| Dataset | Data Version Registry (Data layer) | data_engine, dataset_emission, dataset_contracts | Registry is the authority; all others delegate |
| Feature | Transformation Store | features.py, builder.py, dataset_builder.py | One Transformation Store |
| Transformation | Transformation Store | features.py, label_builder.py | Unified under Transformation Store |
| Metric | Metric Registry | metrics.py, performance.py, evaluation/ | Metric Registry is the authority |
| Statistics | Statistical authority (facade) | statistics.py ×5 modules | One certified statistical facade; all others delegate |
| Experiment | Experiment Framework | experiments/ | Framework owns lifecycle |
| Run | Experiment Framework | runner.py | Framework owns run lifecycle |
| Result | Experiment Framework | result.py | Framework owns immutable result |
| Validation | Validation layer | experiments/validation, validation/ | One validation authority |
| Model | Model Registry | models/registry, training/repository | Model Registry is authority; training writes |
| Workflow | Workflow Engine | orchestration, pipeline, runner | ONE orchestrator; the rest are drivers |
| Configuration | Configuration Service | (unimplemented → must be created) | Single version authority |
| Evidence | Evidence Repository | evidence/, repository/, storage/ | Evidence owns append-only |
| Lineage | Lineage service | lineage.py, repository, pipeline_repository | Lineage is the ONLY provenance authority |
| Ontology | Ontology Service | intelligence/, objects/knowledge | One ontology |
| Knowledge | Knowledge Graph | intelligence/, objects/, memory | Graph is synthesized truth |
| Memory | Knowledge retrieval layer | market_memory (scenario store), memory/ | One retrieval layer |
| Risk | Risk Analytics module | portfolio, econometrics fragments | One risk module |
| Artifact | Artifact Catalog | all registries | Catalog is the umbrella; registries are views |

**Resolved conflicts:** statistics (5→1), metrics (3→1), models (3→1), workflow (4→1),
config (0→1, must be created). All others delegate to a single authority.

---

# SECTION 4 — Registry Architecture

Final registry map. Where merged, delete the separate concepts. Where "never exist,"
do not create.

| Registry | Purpose | Owner | Relationships | Lifecycle |
|----------|---------|-------|---------------|-----------|
| **Artifact Catalog** (umbrella) | Content-addressed inventory of all artifacts | Evidence | Parent of all typed views; feeds Index | Append-only; immutable records |
| **Configuration Registry** | Versioned methodology/parameter authority | Configuration | Consumed by every compute/emission | Append-only; version-locked snapshots |
| **Data Version Registry** | Pinned dataset versions | Data layer | Parent of derived artifacts | Immutable; superseded-by flags |
| **Transformation Store** (merges Feature + Label) | Owns features/labels/transforms | Compute | Child of Data; consumed by ML interface | Immutable; certified on emission |
| **Metric Registry** | Versioned evaluation metrics | Statistical authority | Consumed by Ranking/Comparison/Validation | Append-only |
| **Model Registry** | Deterministic model contracts + metadata | Compute | Child of Transformation; consumed by Evidence | Immutable; content-hashed |
| **Risk Registry** | Risk analytics outputs + lineage | Risk module | Child of Evidence | Append-only |
| **Ontology** | Concept definitions/relationships | Knowledge | Feeds Knowledge Graph | Append-only; versioned |
| **Workflow Registry** (merges Pipeline) | Workflow definitions | Workflow Engine | Consumed by Runner | Versioned; draft→frozen |

**Merged (never separate):** Feature+Label → Transformation Store; Pipeline → Workflow;
Experiment → view over Artifact Catalog; Validation → evidence artifact; Knowledge → graph.
**Never exist:** a separate "Artifact Registry" beyond the Catalog umbrella; a separate
"Knowledge Registry" (knowledge is a graph).

---

# SECTION 5 — Dependency DAG (canonical, direct only)

```
Configuration -> (root; depends on Identity)
Identity      -> (root)
Artifact Catalog    -> Identity, Configuration
Index               -> Artifact Catalog
Query Engine        -> Index, Artifact Catalog
Data Version Reg    -> Identity, Configuration
Transformation Store-> Data Version Reg, Configuration, Query
Metric Registry     -> Statistical authority, Query
Statistical facade  -> (existing frozen statistics libs)
Experiment Ranking  -> Query, Metric Registry
Experiment Comparison -> Query, Metric Registry
Meta Analysis       -> Query, Metric Registry, Statistical facade, Ranking
Ontology            -> Identity, Configuration
Knowledge Graph     -> Ontology, Meta Analysis, Query
Research Memory     -> Knowledge Graph, Query
Report Generator    -> Query, Metric Registry
Dashboard/Viz       -> Query, Report Generator
Archive             -> Evidence Repository (retention)
Search Index        -> Index, Query
Distributed/GPU/Cloud -> determinism gate, storage scale, scheduler
```

**Forbidden dependency directions:**
- Nothing may depend on Presentation.
- Knowledge may not depend on Compute (only on Statistics facade + Evidence).
- Workflow may not depend on Storage directly.
- Storage may not depend on Lineage/Identity policy.
- Semantic Search may never feed into the certified hash/lineage path.

**Inversion risks to guard:** (R1) Ranking before Query; (R2) Knowledge Graph before
Meta-Analysis; (R3) any compute/evidence leak. These are forbidden by the DAG.

---

# SECTION 6 — Artifact Lifecycle

States: Created → Immutable → Referenced → Certified → Archived → Superseded.
**Never mutated.**

| Artifact | Created | Immutable | Referenced | Certified | Archived | Superseded | Never mutated |
|----------|---------|-----------|------------|-----------|----------|------------|---------------|
| Dataset | Data load + hash | after load | by features/experiments | data-quality gate | retention tier | superseded-by new version | yes |
| Feature | transformation emission | after emission | by models/experiments | router parity gate | tier | superseded-by new transform | yes |
| Experiment | framework definition | after definition | by runs | runner certification | tier | superseded-by new experiment | yes |
| Run | runner start | after start | by results | runner certification | tier | n/a | yes |
| Result | compute completion | after completion | by validation/evidence | backend parity | tier | superseded-by corrected method | yes |
| Validation | validation completion | after completion | by evidence | validation authority | tier | superseded-by new criteria | yes |
| Model | training/registry write | after write | by prediction/eval | model registry | tier | superseded-by new model | yes |
| Artifact (generic) | catalog write | after write | by lineage | type-specific gate | tier | superseded-by flag (never delete) | yes |

Rules:
- **Created** = first content-addressed write.
- **Immutable** = immediately after creation; hash fixed.
- **Referenced** = becomes a parent in lineage.
- **Certified** = passed its type-specific gate.
- **Archived** = moved to retention tier; hash and lineage preserved.
- **Superseded** = linked via a "superseded-by" edge; the old record is never deleted/mutated.
- **Never mutated** = true for every artifact, forever.

---

# SECTION 7 — Identity Policy

**Which hashes exist:**
- **artifact_hash** — content-addressed; identifies artifact content + type + version.
- **result_hash** — the deterministic execution hash (operation + backend + version +
  input_hash + output).
- **input_hash** — the operation inputs + parameters.
- **lineage_hash** — parent-order-independent hash of lineage edges.
- **methodology_hash** — version-locked config snapshot hash.

**What enters each hash:**
- artifact_hash: artifact_type, content, HASH_SCHEME_VERSION.
- result_hash: operation, backend, version, input_hash, output.
- input_hash: operation, parameters.
- lineage_hash: sorted parent hashes (order-independent).
- methodology_hash: canonicalized config snapshot.

**What never enters a hash:**
- wall-clock timestamps, random seeds (unless explicitly part of methodology), runtime
  telemetry, in-memory object identity, non-deterministic model output, semantic embeddings.

**Hash version policy:** additive only. v2 is frozen. v3+ introduces new schemes that
must not alter v2 outputs.

**Migration policy:** new scheme applies to new artifacts only; historical v2 hashes are
never recomputed. A migration is a mapping, never a re-hash.

**Collision policy:** SHA-256 with domain separation (type + version prefix). On collision
(astronomically unlikely), the artifact is rejected, not overwritten.

**Future compatibility policy:** a hash is a stable identifier forever; it may gain
"superseded-by" pointers but its value never changes.

---

# SECTION 8 — Configuration Policy

Configuration Service:
- **Ownership:** sole authority for methodology/parameter versioning.
- **Versioning:** every config is immutable and version-locked; a change creates a new
  version, never mutates the old.
- **Snapshots:** a methodology_hash is a canonicalized snapshot of a config version.
- **Determinism:** identical config version → identical methodology_hash; config is pure data.
- **Backward compatibility:** old config versions remain readable and re-producible forever.
- **Mutation rules:** no in-place mutation; append-only sequence of versions; a running
  artifact is bound to the exact version it used.

---

# SECTION 9 — Storage Policy

- **Storage abstraction:** a single backend-independent interface. All layers depend on
  the interface, never on a concrete backend.
- **SQLite responsibilities:** metadata, indices, lineage edges, small typed records.
- **Blob storage responsibilities:** large content-addressed blobs (datasets, features,
  models, results) referenced by hash; never inline BLOBs in SQLite.
- **Evidence storage:** metadata in structured store + content-addressed blobs; envelope
  hash binds them.
- **Future distributed boundary:** the interface must allow a swap to object store /
  distributed sharding without touching upper layers.
- **MUST remain backend-independent forever:** artifact hash→location mapping, lineage
  edges, query/index, and the evidence envelope schema. These abstractions are contract.

---

# SECTION 10 — Workflow Policy

- **Orchestration owns:** sequencing, DAG of steps, scheduling, resumability, workflow
  definition registry.
- **Runner owns:** the certified single experiment execution (build request → delegate →
  package result). It never composes workflows.
- **Workflow never owns:** statistics, metrics, modeling, storage, or evidence writing
  directly.
- **Workflow ↔ evidence:** the workflow emits each completed step as an evidence artifact
  through the Evidence layer; the workflow itself is a versioned definition artifact.
- **Invariant:** one orchestrator. pipeline/ and orchestration/ are drivers of the
  Workflow Engine, not competitors.

---

# SECTION 11 — Knowledge Policy

- **Ontology:** single versioned concept/relationship authority; feeds the graph.
- **Knowledge Graph:** synthesized truth derived from Evidence + Meta-Analysis + Ontology;
  edges are evidence-backed; it is a DERIVED view, never a source of raw artifacts.
- **Research Memory:** a retrieval layer over the Knowledge Graph; never a second store.
- **Semantic Search:** presentation/UX only; **never** in the certified hash/lineage path.
  If used, it must be deterministic bucketing with embeddings excluded from hashes.
- **Explainability:** every knowledge/graph/meta-analytic output carries inputs +
  parameters + methodology version + supporting evidence lineage.
- **Boundaries:** Knowledge never computes raw math; Compute never forms conclusions.
- **Determinism constraints:** graph construction and meta-analysis must be deterministic
  functions of their (versioned) inputs; no stochastic edge formation.

---

# SECTION 12 — Statistical Authority

- **Statistics:** ONE certified Statistical authority (a facade over the frozen statistics
  libraries). All other modules delegate.
- **Metrics:** Metric Registry is the only authority for evaluation metrics.
- **Risk:** Risk Analytics module is the only risk authority.
- **Comparison:** Query + Metric Registry (comparison is a query over standardized metrics).
- **Ranking:** Query + Metric Registry (ranking is a query over standardized metrics).
- **Validation:** Validation layer is the only validation authority.
- **Meta-analysis:** Meta-analysis module is the only synthesis authority, consuming
  Statistics + Query + Metrics.
- **Facades identified:** Statistical Research Engine = a **facade** over frozen
  statistics (never a second authority). ResearchEngine = a facade composing certified
  compute. These facades delegate; they do not own the math.

---

# SECTION 13 — Future Compatibility

Achievable **without changing the frozen kernel** (via additive Data-layer loaders and
certified backends, per V1 Extension Rules):

- **Multiple asset classes:** new Data-layer loaders produce the same dataset contract.
- **Forex / Stocks / Crypto / Futures / Options:** asset-generic dataset contract; no
  core change; options need additive analytics, not core changes.
- **Custom datasets / Alternative data:** loaded via Data-layer adapters; hashed/versioned
  as any dataset; no core change.
- **Guarantee:** `QuantComputationInterface`, `BaseExperimentRunner`, evidence envelope,
  lineage, and reproduction are unchanged for all of the above.

---

# SECTION 14 — Phase 6 Readiness

| Prerequisite | Status |
|--------------|--------|
| Configuration Service exists | **BLOCKED** (must be created) |
| Identity/Config authority | **BLOCKED** (blocked by above) |
| Artifact Catalog (umbrella registry) | **BLOCKED** (needs Config + Identity) |
| Storage abstraction (backend-independent) | **BLOCKED** (needs decision) |
| Query/Index abstraction | **BLOCKED** (needs Catalog + Storage) |
| Single Statistical authority consolidation | **BLOCKED** (needs decision on 5→1 merge) |
| Single Metric Registry | **BLOCKED** (needs Statistical authority) |
| Single Model Registry | **BLOCKED** (needs decision on 3→1 merge) |
| Single Workflow authority | **BLOCKED** (needs decision on 4→1 merge) |
| Frozen core (deterministic, contracts, runner, evidence, lineage, reproduction, v2) | **READY** |
| Certifi ed analytical surface (Phase 5.1) | **READY** |
| Evidence emission (dataset→validation) | **READY** |
| Reproduction engine | **READY** |
| Schema-evolution contract (additive, v2-preserving) | **NEEDS DECISION** |
| "Superseded-by" lifecycle semantic | **NEEDS DECISION** |
| Multi-tenancy / access-control scope | **NEEDS DECISION** |
| Retention/archival policy scope | **NEEDS DECISION** |
| Semantic-search determinism boundary | **NEEDS DECISION** |

---

# SECTION 15 — Architecture Constitution

Immutable architectural laws (short, absolute, enforceable via architecture tests):

1. **Evidence is append-only.**
2. **Artifacts are immutable forever.**
3. **Every deterministic identity is hash-derived.**
4. **Presentation never owns scientific logic.**
5. **Workflow never computes statistics or metrics.**
6. **Lineage is the only provenance authority.**
7. **Configuration has exactly one owner.**
8. **Compute is the only owner of numeric math.**
9. **The Python reference remains the source of scientific truth.**
10. **No computation path bypasses the certified router.**
11. **Every future capability carries a determinism/parity gate.**
12. **Semantic search never enters the certified hash path.**
13. **No stochastic ML/DL in the certified core.**
14. **No trading, broker, or signal generation, ever.**
15. **SQLite never stores content-addressed blobs inline.**
16. **Storage is always accessed through the backend-independent interface.**
17. **A hash's value never changes; it may only gain superseded-by pointers.**
18. **Hash schemes are additive; v2 is frozen; historical hashes are never recomputed.**
19. **One owner per concept; all others delegate.**
20. **Registries are typed views over the Artifact Catalog, not separate duplications.**
21. **Knowledge is a derived, evidence-backed graph, never a raw-artifact store.**
22. **No layer depends upward.**
23. **Compute and Evidence are mutually segregated; the Runner/Workflow bridges them.**
24. **Every artifact carries inputs + parameters + methodology version + lineage.**
25. **Append-only retention tiers may archive, never mutate or delete.**
26. **The trust boundary (BackendRouter + NumericalComparator) is never weakened.**
27. **New asset classes/backends are additive; the frozen core is unchanged.**
28. **Explainability is mandatory on every research and knowledge output.**

---

# FINAL VERDICT

## READY WITH MINOR DECISIONS

**Reasoning:** The verified frozen core is sound and the layer/ownership/dependency/
identity/configuration/storage/workflow/knowledge/statistical authority policies are now
fully specified, eliminating the ambiguity that previously blocked Phase 6. The remaining
items are **decisions, not architecture gaps** — the Configuration Service, storage
abstraction, single-authority consolidations, and "superseded-by" semantics are all
*directed* by this Freeze and require only scoping/sequencing decisions before
implementation. No architectural redesign is pending.

**However, Phase 6 must not begin until the Configuration Service and the storage
abstraction are created** (the two BLOCKED prerequisites), because ranking, comparison,
query, and meta-analysis all depend on them. Once those decisions are made, the frozen
architecture is ready.

---

*ResearchOS Architecture Freeze v2 — Constitutional Reference*
*Owned by: Chief Architect*
*Classification: Internal — governing all future implementation*
