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

# Phase 6 — RED TEAM Architecture Audit

**Author role:** Independent Principal Research Architect (Red Team)
**Mandate:** DISPROVE. Attack everything above the verified kernel.
**Assumption (granted, not verified):** deterministic architecture, immutable contracts,
certified runner, deterministic hashing, reproducible experiments, append-only evidence
repository, lineage graph, reproduction engine, 2500+ tests.
**Horizon:** world-class institutional quantitative research operating system, 10 years.
**Scope:** long-term architecture only. No code review. No implementation details.
**Disposition:** every claim below is treated as guilty until proven correct.

---

## PART 1 — Challenge the overall roadmap

For every proposed Phase 6 work package, classify as **FOUNDATIONAL / DERIVED / OPTIONAL /
PREMATURE** and explain.

| Work package (proposed) | Classification | Why |
|-------------------------|----------------|-----|
| Workflow Engine | **FOUNDATIONAL** | Composition facade everything hangs on. But must be a *definition/execution* contract, not a third orchestrator. |
| Feature Registry | **FOUNDATIONAL** | Derived artifacts need a versioned home before cross-study work. But merge with Label into a Transformation Registry. |
| Label Registry | **DERIVED** | Same mechanics as Feature Registry; split is unjustified. Merge. |
| Statistical Research Engine | **DERIVED** | The math already exists as libraries. This is a certification facade, not a new engine. Frame as DERIVED of existing stats. |
| Risk Analytics | **DERIVED** | Builds on portfolio/metrics/regime analytics that exist. Not foundational. |
| Experiment Ranking | **DERIVED** | Requires Query/Index + Metric Registry. Premature if scheduled before those. |
| Experiment Comparison | **DERIVED** | Same dependency as Ranking. Premature if scheduled before Query/Metrics. |
| Knowledge Graph | **DERIVED** | Requires Ontology + Meta-Analysis + Query. Premature in Tier 2 if Meta-Analysis not done first. |
| Query Engine | **FOUNDATIONAL** | Nothing above (ranking, comparison, meta-analysis, graph, reporting) works without enumerating/selecting the corpus. |
| Meta Analysis | **FOUNDATIONAL-to-DERIVED** | Requires Statistics + Query + Metric Registry. It is a *prerequisite of a meaningful Knowledge Graph*, so it must precede the graph. |
| Research Memory | **DERIVED** | A retrieval consumer of the Knowledge Graph. If the graph is absent, memory is premature. |
| Notebook | **OPTIONAL** | Persistence/UX. Not required for the platform to function. |
| Report Generator | **DERIVED** | Consumes Query + Metrics. Presentation. |
| Dashboard | **OPTIONAL** | Presentation; not required. |
| Visualization | **OPTIONAL** | Presentation; not required. |
| Archive | **DERIVED** | Retention policy on the Evidence Repository; not a new store. |
| Distributed execution | **PREMATURE** | Requires storage scale + determinism/parity + scheduler. |
| GPU | **PREMATURE** | Requires order-stable reduction + parity gate. High risk to hash stability. |
| Cloud | **PREMATURE** | Requires platform API, auth, multi-tenancy — all absent. |
| Search Index | **DERIVED-to-OPTIONAL** | UX over Query. Semantic search threatens determinism. |

**Verdict on the roadmap:** the Tier 1/2/3/4 bucketing is **architecturally wrong**.
FOUNDATIONAL items (Query, Identity/Config, Catalog/Index) are buried in Tier 2;
DERIVED items (Ranking, Comparison) are prematurely in Tier 1.

---

## PART 2 — Dependency graph (the REAL one)

Use `A -> B` meaning "A depends on B" (B must exist first).

```
Identity/Config        -> (nothing)
Artifact Catalog       -> Identity/Config
Index                  -> Artifact Catalog
Query Engine           -> Index, Artifact Catalog
Data Version Registry  -> Identity/Config, Artifact Catalog
Transformation Store   -> Emissions, Data Version Registry, Query
Metric Registry        -> Query, Statistics facade
Statistics facade      -> existing statistics libraries
Experiment Ranking     -> Query, Metric Registry, validated evidence
Experiment Comparison  -> Query, Metric Registry, standardized schema
Meta Analysis          -> Query, Metric Registry, Statistics facade, Ranking
Ontology               -> Identity/Config, Artifact Catalog
Knowledge Graph        -> Ontology, Meta Analysis, Query
Research Memory        -> Knowledge Graph, Query
Report Generator       -> Query, Metric Registry
Dashboard/Viz          -> Query, Report Generator
Archive                -> Evidence Repository (retention)
Search Index           -> Index, Query
Distributed/GPU/Cloud  -> Determinism gate, storage scale, scheduler
```

### Hard dependencies (cannot be skipped)
- Ranking -> Query+Metrics
- Comparison -> Query+Metrics
- Meta Analysis -> Query+Statistics+Metrics
- Knowledge Graph -> Ontology+Meta Analysis+Query
- Research Memory -> Knowledge Graph

### Soft dependencies (can partially proceed in parallel)
- Risk Analytics -> portfolio analytics (no feature dependency — the proposal's coupling is **false**)
- Statistics facade -> existing libs (independent)
- Report/Dashboard/Viz -> Query (soft; mockable)

### Circular dependencies detected
- **Feature construction vs Feature Store:** to register a feature you must compute it; to compute it reproducibly you need its parameters versioned by the Config Service, which the Store helps audit. Resolve by making the Store append-only and the Config Service the version authority — no cycle if Config precedes Store.
- **Meta Analysis vs Knowledge Graph:** if the graph is built before meta-analysis, it stores raw artifacts; then meta-analysis must rebuild the graph. Avoid by making Meta-Analysis produce the graph edges (single source of synthesized truth).

### Dependency inversions (in the proposed plan)
1. **Ranking (Tier 1) before Query (Tier 2) — INVERSION.** Ranking is a selection over an enumerable corpus.
2. **Knowledge Graph before Meta-Analysis — INVERSION.** The graph should *consume* meta-analysis, not feed it.
3. **Risk Analytics coupled to Feature Registry — FALSE INVERSION.** They are independent; coupling is arbitrary.
4. **Statistical Research Engine as a foundation — INVERSION.** It is a facade over existing math; it should be DERIVED.

---

## PART 3 — Single source of truth audit

| Subsystem | Who owns it today | Duplicated? | Verdict |
|-----------|-------------------|-------------|---------|
| statistics | `quant_engine/statistics.py`, `probability/statistics.py`, `data_engine/statistics.py`, `metrics.py`, `performance.py` | **CRITICAL — 5 owners** | A single certified Statistical authority must own the math; the rest must delegate. |
| metrics | `quant_engine/metrics.py`, `performance.py`, `evaluation/` | **CRITICAL — 3 owners** | One Metric Registry as the authority; evaluation consumes it. |
| features | `machine_learning/features.py`, `machine_learning/builder.py`, `dataset_builder.py` | **HIGH — 3 owners** | One Transformation Store. |
| labels | `machine_learning/label_builder.py`, `labels.py`, `label_contracts.py` | **HIGH — 3 owners** | Merge into Transformation Store. |
| datasets | `data_engine/`, `evidence/dataset_emission.py`, `quant_engine/dataset_contracts.py` | **HIGH — 3 owners** | One Data Version Registry + a single dataset contract. |
| models | `machine_learning/models/registry.py`, `training/repository.py`, `training/trainer.py` | **CRITICAL — 3 owners** | One Model Registry; training writers, registry is authority. |
| lineage | `evidence/lineage.py`, `evidence/repository.py`, `pipeline_repository/` | **HIGH — 3 owners** | One lineage service; repository asks it, not the reverse. |
| workflow | `orchestration/`, `pipeline/`, `experiments/runner.py`, proposed Workflow Engine | **CRITICAL — 4 owners** | ONE orchestrator; the rest are drivers. |
| config | Named in V1 but **UNIMPLEMENTED** | — | **CRITICAL — no owner.** Must be created before any derived-artifact versioning. |
| risk | `portfolio/`, `econometrics/`, scattered | **MEDIUM** | One Risk Analytics module. |
| ontology | `intelligence/`, `objects/knowledge.py`, fragmented | **HIGH** | One Ontology Service. |
| knowledge | `intelligence/`, `objects/`, Knowledge Graph proposal | **HIGH** | One Knowledge Graph as the synthesized truth. |
| memory | `market_memory/`, Research Memory proposal | **HIGH** | One retrieval layer; market_memory is the scenario store. |

**Critical owners with no single authority:** statistics, metrics, models, workflow, config.
These are the highest-risk duplication points.

---

## PART 4 — Architecture layer violations

Layers: Presentation / Research / Execution / Evidence / Storage / Infrastructure /
Compute / Knowledge / Configuration.

| Violation | What leaks | Why it is a violation | Future bugs | How institutional systems avoid it |
|-----------|-----------|----------------------|-------------|-------------------------------------|
| Statistics modules spread across Compute, Data, and Evaluate layers | math in multiple layers | Violates single-responsibility; two layers can disagree on a formula | Divergent results; silent reproducibility breaks | One Compute owner; all layers delegate |
| Metric definitions in both Evaluation and Performance layers | evaluation criteria | Two authorities for "what is a good result" | Ranking/validation disagree | One Metric Registry |
| Workflow logic in orchestration, pipeline, and runner | control flow in 3 places | Competing orchestrators | Non-deterministic run order | One workflow definition/execution contract |
| Config ownership absent | parameter versioning | No layer owns methodology versioning | Derived artifacts unversioned; repro claims void | Dedicated Configuration layer |
| Knowledge representation in intelligence, objects, and memory | knowledge in 3 layers | Ambiguous truth | Contradictory conclusions | One Knowledge layer |
| Storage concerns in evidence, repository, storage, pipeline_repository | persistence in 4 modules | No single storage boundary | Migration/backup diverges | One Storage abstraction |
| Search/embedding in Knowledge layer (Tier 4) | non-deterministic UX into knowledge | Semantic search is non-deterministic | Hash/lineage instability | Keep search out of the certified path |

Institutional systems enforce these via **interface boundaries + a single owner per
concern**, typically enforced by architecture tests (which ResearchOS already uses for
its frozen boundaries — the same discipline must extend to the new layers).

---

## PART 5 — Registry audit

| Registry | Verdict | Rationale |
|----------|---------|-----------|
| Dataset Registry | **KEEP** | Required for pinned data versions. |
| Feature Registry | **MERGE → Transformation Registry** | Same mechanics as labels/transforms. |
| Transformation Registry | **KEEP (merged)** | Owns features/labels/transforms. |
| Metric Registry | **KEEP** | Versioned evaluation authority. |
| Model Registry | **KEEP** | Owns deterministic model contracts. |
| Artifact Registry | **MERGE as the umbrella** | One content-addressed artifact catalog; the others are typed views over it. |
| Configuration Registry | **KEEP** | Methodology/parameter version authority (currently absent). |
| Pipeline Registry | **MERGE → Workflow** | Pipeline definitions belong to the Workflow Engine. |
| Validation Registry | **MERGE → Evidence/Artifact** | Validation results are evidence artifacts. |
| Risk Registry | **KEEP (new)** | Risk analytics outputs and their lineage. |
| Experiment Registry | **MERGE → Artifact Catalog** | Experiments are artifacts; ranking is a query over them. |
| Ontology Registry | **KEEP** | Concept definitions/relationships. |
| Knowledge Registry | **MERGE → Knowledge Graph** | Knowledge is a graph, not a flat registry. |
| Workflow Registry | **KEEP (merged with Pipeline)** | Workflow definitions. |

**Net:** 14 proposed registries collapse to ~8 distinct stores: Artifact Catalog (umbrella),
Transformation, Metric, Model, Configuration, Risk, Ontology, Workflow. The rest are
typed views or folds into the Evidence/Knowledge layers.

---

## PART 6 — Scalability audit

Assumption: 100 datasets, 10M experiments, 50M results, 20 TB evidence, 100 researchers.

| Component | Failure mode | Where it breaks |
|-----------|--------------|-----------------|
| SQLite evidence store | **Writes serialize; 50M rows exceed comfortable SQLite** | every emission is an append; 50M-result scale degrades |
| In-memory repository | **Does not persist** | only tests/dev |
| Lineage traversal | **BFS over 50M-edge graph in SQLite** | `resolve_full_chain` and `ancestors` become slow without an index/query layer |
| Hash computation | **Hashing every feature/label artifact doubles cost** | feature/label emission at scale |
| Append-only with no compaction | **20 TB with no retention tier** | Archive/retention absent |
| Query | **No index; per-hash lookups only** | ranking/comparison/meta-analysis impossible at scale |
| Concurrent researchers | **No task queue / scheduler at scale** | 100 researchers collide on writes |
| Metadata vs blobs | **Artifacts stored inline with metadata** | 20 TB blobs must be content-addressed objects, not SQLite BLOBs |

### Abstraction layers that MUST exist TODAY to avoid rewrites
1. **A Storage abstraction** (repository interface) so SQLite → object store is a swap, not a rewrite.
2. **A Query/Index abstraction** so lineage traversal and corpus selection share one index.
3. **A Content-addressed blob boundary** separate from metadata (metadata in SQL, blobs in object store).
4. **A Scheduler/task interface** so single-node → distributed is an implementation swap.
5. **A Config/Identity boundary** so versioning is stable across storage migrations.

If these boundaries are not drawn now, Phase 7+ will be a rewrite, not an extension.

---

## PART 7 — Determinism audit (threats)

| Future capability | Threat | Probability | Impact | Mitigation |
|-------------------|--------|-------------|--------|------------|
| Semantic Search (embeddings) | Non-deterministic inference in hash path | **High** | High | Keep out of certified path; deterministic bucketing; no embeddings in hashes |
| GPU acceleration | Order-dependent reductions break hash parity | **Medium** | Critical | Only order-stable reductions; NumericalComparator gate; scalar reference |
| Distributed execution | Partition order changes lineage/repro | **Medium** | Critical | Deterministic partition keys; mergeable evidence |
| Feature/Label emission | New artifact types change result hashes | **High** | High | Additive schema v3; parity gate; never re-hash history |
| Model registry | Metadata drift breaks hash stability | **Medium** | High | Content-hash model contracts; append-only metadata |
| Meta-analysis | Choosing studies changes pooled result | **High** (if opaque) | Medium | Deterministic selection criteria; versioned study set |
| Archive/compaction | Compaction loses lineage if not careful | **Medium** | High | Append-only compaction; lineage preserved in index |
| Config service | Parameter version drift breaks repro | **High** | Critical | Version-locked config per artifact |
| Report generation | Non-deterministic ordering | **Low** | Medium | Deterministic template ordering |

**Highest-risk threats:** GPU parity, distributed partition determinism, and config
version drift. Each must carry a hard gate before adoption.

---

## PART 8 — Research workflow audit

A researcher's required flow: create dataset → generate features → run experiments →
compare → rank → validate → publish → reproduce → search → discover → reuse.

| Step | Architectural friction | Where it's awkward |
|------|------------------------|--------------------|
| create dataset | No unified Data Version Registry; dataset provenance exists but no catalog | discovery of existing datasets |
| generate features | Feature/Label stores fragmented; no transformation store | reuse of features across studies |
| run experiments | Runner certified, but no unified workflow model | orchestrating multi-step runs |
| compare experiments | **No Query Engine / Metric Registry** | comparison is manual per-hash |
| rank experiments | **No Query/Index** | ranking impossible at scale |
| validate | Validation exists | OK |
| publish | No notebook/report/repro bundle | deliverable is ad hoc |
| reproduce | ReproductionEngine exists | OK — the strongest step |
| search | **No index/query** | discovery dead |
| discover | **No knowledge graph / memory** | no cross-study discovery |
| reuse | **No artifact catalog / transformation store** | features/labels/models not reusable |

**The workflow is broken at every composition step** (compare/rank/search/discover/reuse)
because the enumeration layer (query/index/catalog) is missing. The proposed roadmap puts
ranking (Tier 1) before this enumeration layer (Tier 2) — the exact awkwardness this audit
flags.

---

## PART 9 — Institutional comparison (missing architectural ideas, not copying)

| System | Architectural idea ResearchOS is missing |
|--------|-------------------------------------------|
| MLflow | A **unified experiment tracking + metric authority** with a standard run schema. ResearchOS has per-artifact hashes but no cross-run metric comparisons. |
| Weights & Biases | A **living experiment dashboard + live comparison** layer; ResearchOS has no presentation over its evidence. |
| Metaflow | **Data versioning + step-level cache + DAG execution** for workflows; ResearchOS has no workflow DAG or step cache. |
| DVC / LakeFS | **Content-addressed data versioning on object storage with zero-copy branch/tag**; ResearchOS stores inline in SQLite. |
| Apache Atlas / DataHub | **An enterprise metadata catalog + governed glossary**; ResearchOS has no central catalog or glossary. |
| OpenLineage | **A standardized lineage event model with a dedicated lineage service**; lineage is embedded in ResearchOS's repository, not a standalone, queryable service. |
| Neo4j | **A purpose-built graph store** for the knowledge graph; ResearchOS would put it in a relational/in-memory structure. |
| Kubeflow | **A pipeline SDK + component registry + orchestration contract**; ResearchOS lacks a workflow definition contract. |

**Missing architectural ideas (not tools):** (1) a **governed metadata catalog** as the
single entry point to all artifacts; (2) a **standardized lineage event model** decoupled
from storage; (3) a **workflow DAG execution + step cache** abstraction; (4) a **content-
addressed data versioning** boundary on object storage; (5) a **purpose-built graph store**
for knowledge; (6) a **presentation/UX layer over evidence** (dashboarding).

---

## PART 10 — Capability criticality (0–100, for research platform, not trading)

| Capability | Score | Rationale |
|-----------|-------|-----------|
| Identity & Configuration Service | 100 | Without it, nothing above is reproducible or groupable. |
| Artifact Catalog + Index | 95 | The entry point to all research. |
| Query Engine | 95 | Enables ranking/comparison/meta-analysis/graph/reporting. |
| Data Version Registry | 95 | Reproducibility is void without pinned data. |
| Evidence Repository (append-only) | 100 | Already the trust anchor. |
| Lineage | 95 | Already strong; needs to be a standalone service. |
| Reproduction Engine | 95 | Already strong. |
| Metric Registry | 90 | Authority for evaluation/ranking. |
| Transformation (Feature/Label) Store | 90 | Cross-study composability. |
| Statistical Research facade | 90 | Certifies the math authority. |
| Experiment Ranking | 85 | High research value. |
| Experiment Comparison | 85 | High research value. |
| Meta Analysis | 88 | Synthesis of conclusions. |
| Ontology | 80 | Shared vocabulary. |
| Knowledge Graph | 78 | Cross-study inference. |
| Research Memory | 72 | Retrieval over knowledge. |
| Risk Analytics | 80 | Institutional risk posture. |
| Workflow Engine | 90 | Composition facade. |
| Notebook | 65 | Persistence/UX. |
| Report Generator | 70 | Deliverable. |
| Dashboard / Visualization | 55 | Presentation. |
| Archive | 68 | Retention. |
| Search (semantic) | 50 | UX, determinism risk. |
| Distributed / GPU / Cloud | 40 | Infrastructure, late. |

---

## PART 11 — Future rewrite risk (within 5 years)

| Subsystem | Rewrite risk | Why |
|-----------|--------------|-----|
| Storage (SQLite inline) | **HIGH** | 50M results / 20 TB will force object-store-backed content addressing. If no storage abstraction is drawn now, this is a rewrite. |
| Lineage store | **HIGH** | Embedded in repository; at scale it needs a standalone, indexed, queryable lineage service. |
| Workflow (if built as a third orchestrator) | **HIGH** | Competing orchestrators (orchestration/pipeline/runner) will need unification. |
| Statistics (if left as 5 owners) | **HIGH** | Divergence forces a reconciliation rewrite. |
| Knowledge/memory (if duplicated) | **MEDIUM-HIGH** | Three overlapping stores will need consolidation. |
| Query (if built per-artifact) | **HIGH** | Without a shared index, each feature (ranking, comparison, search) builds its own — a rewrite risk. |
| Semantic search | **MEDIUM** | Non-determinism will force a rework to a certified, hashed-out-of-path design. |
| Config (if created late) | **HIGH** | Retro-fitting versioned config to existing artifacts is a migration nightmare. |

**The single highest rewrite risk is storage+lineage**, if the abstraction boundaries in
Part 6 are not drawn during Phase 6.

---

## PART 12 — Architecture completeness (weighted, not averaged)

Weights reflect architectural importance to an institutional research OS.

| Domain | Weight | Completion | Justification |
|--------|--------|-----------|---------------|
| Scientific Kernel | 25% | 85% | Determinism, router, C++ mature; C++ surface narrow (-5%), some math gaps. |
| Evidence Layer | 20% | 80% | Append-only, lineage, reproduction verified; feature/label/model emission missing (-20%). |
| Research Workflow | 12% | 10% | No unified, versioned workflow definition. |
| Knowledge Layer | 8% | 5% | No ontology/graph/meta-analysis. |
| Experiment Lifecycle | 10% | 70% | Run/result/validation strong; ranking/comparison absent. |
| Institutional Tooling | 8% | 5% | No registries unified, no catalog. |
| Visualization | 4% | 5% | Barely begun. |
| Infrastructure | 5% | 10% | Single-node; no storage abstraction. |
| Scalability | 4% | 5% | SQLite-bound. |
| Configuration | 4% | 0% | Named but unimplemented. |
| Research UX | 0% | 0% | No notebook/report/search. |

**Weighted total:** (0.25×85) + (0.20×80) + (0.12×10) + (0.08×5) + (0.10×70) +
(0.08×5) + (0.04×5) + (0.05×10) + (0.04×5) + (0.04×0) + (0×0)
= 21.25 + 16.0 + 1.2 + 0.4 + 7.0 + 0.4 + 0.2 + 0.5 + 0.2 + 0 + 0
**= ~47.15%**

Applying a discount for the missing foundational blockers (config, catalog, storage
abstraction) that will force rework, **realistic overall ≈ 40–45%**. The kernel is strong,
but the operating-system surface is the bulk of the remaining 55–60% and carries the risk.

---

## PART 13 — Unknown unknowns (blind spots)

1. **Multi-tenancy & access control.** 100 researchers implies per-researcher, per-team
   isolation, permissions, and audit of who read/wrote what. Entirely absent from the
   roadmap.
2. **Config as a first-class artifact.** The V1 spec names a Configuration Service but it
   was never built. Its absence undermines every derived-artifact versioning claim.
3. **Retention & legal/compliance.** Append-only forever is a liability; no retention
   tiers, data-hold policies, or legal-hold. Not discussed.
4. **Data quality lifecycle.** Datasets are pinned, but there is no "this dataset is
   deprecated/corrected" concept that preserves old hashes while flagging new ones.
5. **Concurrency semantics.** 100 researchers writing to one append-only store — the
   merge/conflict model is undefined.
6. **The "derived truth" problem.** When meta-analysis and the knowledge graph disagree
   with a raw artifact hash, which is authoritative? The graph/derived truth lifecycle is
   undefined.
7. **Gradual correctness drift.** Deterministic hashing certifies *identical re-execution*,
   not *correctness*. Over 10 years, methodology improvements will change results; there
   is no "superseded-by" semantic that preserves the audit trail while deprecating methods.
8. **Cost/operational model.** 20 TB evidence, 100 researchers, GPU/cloud — no cost model,
   no performance budget, no observability.
9. **The narcotic of determinism.** Determinism guarantees *reproducibility of the same
   inputs*, but a researcher can still feed bad inputs. Scientific validity is not
   guaranteed by determinism — a cognitive blind spot the roadmap does not address.

---

## PART 14 — Final verdict

### MAJOR REDESIGN REQUIRED

**Not** because the kernel is weak — it is strong. **Because the roadmap above the kernel
is architecturally inverted and foundationally incomplete.**

Reasons:
1. **Dependency inversion is structural, not cosmetic.** Ranking/Comparison (Tier 1) cannot
   precede Query/Index + Metric Registry (Tier 2); Meta-Analysis must precede the Knowledge
   Graph. The roadmap's ordering is wrong at the architectural level, not just the schedule.
2. **Single sources of truth are fragmented.** Statistics (5 owners), metrics (3), models
   (3), workflow (4), config (0). Without consolidation, the system will diverge and
   reproducibility will silently break.
3. **Foundational blockers are unnamed.** Identity/Config, Artifact Catalog, storage
   abstraction, and schema evolution gate the entire stack and are absent from the plan.
   Building Tier 1 on these gaps is building on sand.
4. **Scalability boundary is not drawn.** SQLite-inline storage and embedded lineage will
   force a rewrite at the stated scale (50M results / 20 TB). The abstraction must exist
   today.
5. **Determinism threats are unmanaged.** Semantic search, GPU, and distributed execution
   all threaten hash/lineage stability; none carry a hard parity gate in the roadmap.
6. **The research workflow is broken at every composition step** (compare/rank/search/
   discover/reuse) precisely because the enumeration layer is missing.

**What would change the verdict:**
- Re-sequence: Identity/Config → Catalog/Index → Query → Transformation Store → Metric
  Registry → Statistical facade → Ranking/Comparison → Ontology → Meta-Analysis →
  Knowledge Graph → Memory → Presentation → Archive (early) → Search → Scale.
- Consolidate owners: 5 statistics owners → 1; 3 metrics → 1; 3 models → 1; 4 workflow →
  1; create the Config Service.
- Draw the storage, query, scheduler, and config abstraction boundaries NOW.
- Add a determinism/parity gate to every future capability, and keep search/ML/GPU out of
  the certified hash path.
- Define the derived-truth lifecycle (superseded-by, deprecation, data-quality correction).

**Bottom line:** the verified kernel is a genuine institutional asset and the right
foundation, but the Phase 6 roadmap as proposed is **not approvable**. It requires major
architectural revision — re-sequencing, consolidation of ownership, and a mandatory
foundation layer — before it can responsibly proceed. Realistic near-term completion is
~40–45%, and the remaining 55–60% is where the value and the risk both live.

---

*Phase 6 RED TEAM Architecture Audit — Independent Review*
*Classification: Internal — Architecture Review (no implementation)*
