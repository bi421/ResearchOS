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

# Phase 6 — Adversarial Architecture Audit (Independent Review)

**Author role:** Independent Principal Software Architect / Quant Research Platform Auditor
**Disposition:** Skeptical. The proposed roadmap is treated as **guilty until proven correct**.
**Method:** Attempt to falsify every dependency, sequencing, and ownership claim.
**Status:** Audited against the verified ResearchOS kernel (2540+ tests, evidence chain,
append-only repository, lineage, reproduction, hash v2, architecture freeze).

---

## 0. Executive dissent

The proposed roadmap is **buildable but mis-sequenced and partially redundant.** Its
most serious defects:

1. **Ranking and Comparison are placed in Tier 1, but they cannot operate without a
   cross-artifact query/index (placed in Tier 2).** The proposed order is a direct
   dependency inversion.
2. **Meta-Analysis is placed in Tier 2 ahead of the Query Engine and behind the
   Knowledge Graph, when in fact Meta-Analysis is a *prerequisite* of a meaningful
   Knowledge Graph, not a consumer of it.** The direction of the dependency is wrong.
3. **"Statistical Research Engine" is largely a duplicate of existing statistics
   modules** (`quant_engine/statistics.py`, `probability/statistics.py`, `metrics.py`,
   `performance.py`, `data_engine/statistics.py`). It should be a thin certified facade,
   not a new engine — otherwise it creates a second, competing statistics authority.
4. **The roadmap names zero foundational blockers** (identity consistency, schema
   evolution, registry ownership, configuration service). These are not "implementation
   details"; they gate everything above.
5. **Risk Analytics is falsely implied to depend on Feature Registry.** It operates on
   returns/portfolio/regime data and is independent of features. Wiring them together
   creates a needless coupling.

The kernel is genuinely strong. The *institutional operating-system layer* is where the
plan is weak. This audit separates the two and grades them differently.

---

## 1. Missing dependencies (proven, not assumed)

For each proposed capability, the true prerequisite set (what MUST exist first):

| Capability | True prerequisites | Why it cannot come first |
|------------|--------------------|--------------------------|
| **Experiment Ranking** | Query Engine/Index, Metric Registry, validated evidence set | Ranking is a *selection over a corpus*. Without a way to enumerate experiments and a standard metric, ranking is arbitrary. **Cannot precede Query.** |
| **Experiment Comparison** | Metric Registry, Query Engine, standardized result schema | Comparison needs comparable, queryable result sets and agreed metrics. |
| **Meta-Analysis** | Evidence Repository, Statistics surface, Metric Registry, Ranking | Meta-analysis pools effect sizes across studies; it needs a statistics authority and a queryable evidence corpus. |
| **Knowledge Graph** | Ontology, Query Engine, Meta-Analysis, identity consistency | A graph is only as good as its nodes/edges being queryable and stable. Feeding it raw artifacts without meta-analysis produces a structure, not knowledge. |
| **Research Memory** | Knowledge Graph, Meta-Analysis, Retrieval | Memory is a *retrieval consumer*; it depends on the graph/synthesis, not the reverse. |
| **Statistical Research Engine** | Existing statistics modules (already present) | It is a facade over existing math; no new dependency is required, so it should be staged as a *certification wrapper*, not a foundation. |
| **Risk Analytics** | Portfolio/metrics analytics, regime data | **Independent of Feature Registry.** False coupling in the proposed plan. |
| **Knowledge Graph → Ontology** | A shared vocabulary must precede a graph | Otherwise edges are drawn between incompatible concept identifiers. |
| **Query Engine → Artifact Catalog + Index** | You cannot query what is not inventoried and indexed | Index is a prerequisite of query; catalog is a prerequisite of index. |
| **Feature/Label Registry → Feature/Label computation** | Emission must be defined before the registry stores it | The registry is a *consumer* of computed, hashed features. |
| **Report/Dashboard/Visualization** | Query Engine, Metric Registry, result schema | Presentation consumes queried, standardized results. |
| **Archive** | Evidence Repository (it is archival of the same store) | Archive is a retention policy on the repository, not a separate capability with new dependencies. |
| **Distributed/GPU/Cloud** | Storage scale, determinism/parity gate, scheduler | Cannot parallelize before determinism and storage are proven at scale. |

**Conclusion:** The proposed Tier 1 (Ranking, Comparison) violates a hard dependency on
Query/Index and Metric Registry. The proposed Tier 2 order (Knowledge Graph before
Meta-Analysis) reverses a dependency.

---

## 2. Duplicate responsibilities

| Pair | Verdict | Recommended action |
|------|---------|--------------------|
| **Statistics modules vs "Statistical Research Engine"** | **Duplicate.** `quant_engine/statistics.py`, `probability/statistics.py`, `metrics.py`, `performance.py`, `data_engine/statistics.py` already own the math. A new engine duplicates the authority. | **Merge:** make it a thin certified `StatisticalResearchBackend` behind the existing router that *delegates* to the existing modules. Do not create a second stats authority. |
| **Workflow Engine vs Experiment Manager (orchestration/, pipeline/, experiments/runner.py)** | **Overlap.** `orchestration/`, `pipeline/`, and `experiments/runner.py` already orchestrate. A third "Workflow Engine" risks a competing scheduler. | **Clarify ownership:** define Workflow Engine as the *composition facade* and demote `pipeline/`/`orchestration/` to its internal drivers. One orchestrator. |
| **Knowledge Graph vs Research Memory vs market_memory/** | **Overlap.** `market_memory/` is already a memory implementation; a new Research Memory and a new Knowledge Graph are three overlapping stores. | **Merge Research Memory into the Knowledge Graph retrieval layer**, and keep `market_memory/` as the scenario-specific store. One graph, one retrieval layer. |
| **Evidence Repository vs Archive** | **Duplicate as proposed as a separate capability.** Archive is retention on the same append-only store. | **Merge:** Archive = retention/compaction policy *inside* `evidence/repository.py`. Not a new store. |
| **Lineage vs Query Engine** | **Separate layers, must share an index.** Lineage is traversal; Query is selection. Not duplicate, **but** both must be built on the same artifact index or they diverge. | Keep separate but commit both to one index. |
| **Feature Registry vs Label Registry** | **Marginal.** Both are "derived artifact registries" with identical mechanics. | **Merge** into a single **Artifact/Transformation Registry** with a `kind` discriminator (feature/label/transform). Two registries is duplication. |
| **Model Registry vs Training Repository** | **Duplicate.** `machine_learning/models/registry.py` and `training/repository.py` already overlap. | **Merge** into the Artifact Registry; one metadata/versioning authority. |
| **Reproducibility Bundle vs Reproduction Engine** | Related but distinct. Bundle = export; Engine = re-execute. | Keep separate; define the bundle as a serialization of the engine's inputs. |

**Naming corrections:** "Feature Registry" and "Label Registry" are misleading — they are
derived-artifact registries, not separate domains. "Statistical Research Engine" is
misleading — it is a certification facade over existing statistics. "Research Memory" is
misleading — it is a retrieval view over the Knowledge Graph.

---

## 3. Hidden blockers (not in the proposed roadmap)

These gate the entire Tier 1–2 stack and are completely absent from the proposal:

1. **Identity consistency.** Ranking, comparison, meta-analysis, and the knowledge graph
   all require a *stable, cross-artifact identity* binding methodology version, dataset
   lineage, and parameters. Today identity is per-hash. Without a stable composite
   identity, two runs of the "same" study cannot be grouped for ranking. **Critical.**
2. **Schema evolution.** Evidence envelopes are append-only with **hash v2**. Adding new
   artifact types (feature, label, model, metric) requires an *additive schema versioning
   contract* so old envelopes still verify. Not specified. **Critical.**
3. **Version migration of the hash scheme.** Moving to v3 (e.g., to bind new artifact
   types) must be deterministic and must not re-hash/re-verify historical records
   inconsistently. **High.**
4. **Registry ownership.** There is no single owner of "what is a study / a metric / a
   model." The roadmap adds registries without resolving who owns the definitions. **High.**
5. **Configuration Service.** The V1 architecture names a Configuration Service for
   methodology versioning, but it is **not implemented.** Feature/label/statistical
   computations all depend on versioned parameters. Without it, reproducibility claims at
   the feature level are void. **Critical.**
6. **Artifact lifecycle.** The current model is fully immutable. Workflows need *draft →
   frozen* states for hypotheses/notebooks before they become immutable evidence. The
   roadmap does not define where mutability ends and immutability begins. **High.**
7. **Reproducibility risk.** Adding feature/label/model artifacts to the evidence chain
   must not change existing result hashes. The roadmap gives no parity gate. **High.**
8. **Backward compatibility of Query/Index.** As the schema evolves, the index and query
   engine must remain backward-compatible with v2 envelopes. **Medium.**
9. **Determinism risk in Semantic Search.** Embedding-based search (Tier 4) is
   non-deterministic and violates the determinism contract unless explicitly certified
   and kept out of the hash path. **High — hidden.**
10. **Performance at scale.** Hashing and indexing every feature/label artifact adds
    cost. The roadmap has no performance budget or benchmark gate for the emissions.
    **Medium.**

---

## 4. Wrong sequencing — the corrected order and why

The proposed Tier 1 order is **wrong**. Corrected sequence:

| Order | Capability | Why it must be here |
|-------|-----------|----------------------|
| 1 | **Identity & Configuration Service** | Foundational; gates grouping, versioning, reproducibility of every derived artifact. (Hidden blocker.) |
| 2 | **Artifact Catalog + Index** | Nothing above can enumerate the corpus without an inventory + index. |
| 3 | **Query Engine** | Ranking/comparison/meta-analysis/knowledge-graph all consume it. |
| 4 | **Feature/Label (Transformation) Emission + Registry** | Completes artifact coverage; feeds ML surface and statistical composability. |
| 5 | **Metric Registry** | Standard, versioned metrics are the basis of ranking and comparison. |
| 6 | **Statistical Research Engine (thin facade)** | Wraps existing math; no new dependency. |
| 7 | **Experiment Ranking + Comparison** | Now safe: query + metrics + validated evidence exist. |
| 8 | **Risk Analytics** | Independent; can run in parallel with 5–7. |
| 9 | **Ontology** | Shared vocabulary must precede the graph. |
| 10 | **Meta-Analysis** | Pools evidence; feeds the graph. **Before** knowledge graph. |
| 11 | **Knowledge Graph** | Consumes meta-analysis + ontology + query. |
| 12 | **Research Memory** | Retrieval consumer of the graph. |
| 13 | **Notebook / Report / Dashboard / Visualization** | Presentation over queried, ranked results. |
| 14 | **Archive** | Retention built into the evidence repository (do early, not as a Tier-4 afterthought). |
| 15 | **Search Index** | UX layer, after query + index stable. |
| 16 | **Distributed / GPU / Cloud** | Only after determinism, storage scale, and parity are proven. |

**Key corrections to the proposal:**
- Query/Index/Metric Registry move **up** (they are prerequisites of ranking).
- Meta-Analysis moves **before** the Knowledge Graph (dependency reversal).
- Feature/Label Registry moves **up** and **merges** into one Transformation Registry.
- Statistical Research Engine is de-ranked to a *facade*, not a foundation.
- Archive is collapsed into the Evidence Repository retention, not a Tier-4 item.
- Risk Analytics is **decoupled** from Feature Registry.

---

## 5. Missing capabilities (required vs optional)

| Capability | Required? | Assessment |
|-----------|-----------|------------|
| **Feature Store** | **Required** (for a research platform) | Deterministic computed-feature persistence + versioning. Merges with Feature/Label registry into a Transformation Store. |
| **Data Version Registry** | **Required** | Reproducibility is void without pinned, content-addressed data versions per run. |
| **Transformation Registry** | **Required (merged)** | Lineage of derived artifacts (features/labels/transforms). Merge with Feature/Label registry. |
| **Metric Registry** | **Required** | Standard, versioned evaluation metrics; prerequisite of ranking/comparison. |
| **Pipeline Registry** | **Required (merged)** | Merge into the Workflow Engine as its persisted definition store. |
| **Artifact Catalog** | **Required** | Cross-artifact inventory; prerequisite of index and query. |
| **Dependency Graph** | **Required (formalize)** | The lineage engine already provides this; expose it as a first-class service, not a new store. |
| **Cache Layer** | **Optional** | Performance optimization; must not affect determinism (only cache immutable, content-addressed results). |
| **Scheduler** | **Required (exists as BackendScheduler)** | A workflow scheduler is needed; extend the existing one, do not build a second. |
| **Task Queue** | Optional (later) | Only for distributed execution (Tier 4). |
| **Research API** | **Required** | Institutional integration surface (CLI exists; a stable programmatic API is needed). |
| **Plugin System** | **Optional / risky** | Risks determinism and frozen-contract integrity. Only if a strict certified-extension gate is enforced. |

---

## 6. Criticality ranking (can the system function without it?)

| Capability | Criticality | Justification |
|-----------|-------------|---------------|
| Identity & Config Service | **Critical** | Without it, no reliable grouping/versioning of derived work. |
| Artifact Catalog + Index | **Critical** | Without it, no way to enumerate the corpus. |
| Query Engine | **Critical** | Ranking, comparison, meta-analysis, graph, reporting all depend on it. |
| Data Version Registry | **Critical** | Reproducibility contract is broken without pinned data versions. |
| Transformation (Feature/Label) Store | **High** | Needed for cross-study composability and ML surface. |
| Metric Registry | **High** | Needed for ranking/comparison. |
| Statistical Research Engine (facade) | **High** | Certifies an authority that already exists as libraries. |
| Experiment Ranking | **High** | Desk value; not required for the platform to function. |
| Experiment Comparison | **High** | Desk value. |
| Risk Analytics | **High** | Institutional risk posture; not required for core function. |
| Ontology | **Primary-adjacent** (High) | Needed before Knowledge Graph, not for core. |
| Meta-Analysis | **High** | Synthesis; needs query + statistics. |
| Knowledge Graph | **Medium** | High value, not required to function. |
| Research Memory | **Medium** | Retrieval view; depends on graph. |
| Notebook | **Medium** | UX/persistence. |
| Report Generator | **Medium** | Deliverable. |
| Dashboard / Visualization | **Low** | Presentation; not required. |
| Archive | **Medium** | Retention; collapse into repository. |
| Search Index | **Low** | UX; later. |
| Distributed / GPU / Cloud | **Low** | Infrastructure; last. |

---

## 7. Trading impact

| Capability | Impact class |
|-----------|--------------|
| Risk Analytics | **Direct trading value** (informs risk posture for human traders) |
| Experiment Ranking / Comparison | **Indirect research value** (guides which research to trust) |
| Meta-Analysis | **Indirect research value** |
| Knowledge Graph / Research Memory | **Indirect research value** |
| Statistical Research Engine | **Indirect research value** |
| Transformation/Feature Store | **Indirect research value** |
| Ontology | **Infrastructure only** |
| Identity & Config Service | **Infrastructure only** |
| Artifact Catalog / Index / Query | **Infrastructure only** |
| Metric Registry | **Infrastructure only** |
| Notebook / Report / Dashboard / Viz | **Infrastructure only** (interface) |
| Archive / Search / Distributed / GPU / Cloud | **Infrastructure only** |

**Note:** None of the Tier 1–4 capabilities provide *direct trading value* except Risk
Analytics. This is consistent with the platform's mandate (research, not trading), but
it means the roadmap's ROI is institutional/indirect, and the freeze boundary must
remain absolute.

---

## 8. Revised completion percentage (non-optimistic)

Estimates are weighted by the target = "institutional quantitative research operating
system," not just "working kernel."

| Domain | Weight | Completion | Justification |
|--------|--------|-----------|---------------|
| Compute kernel (determinism, router, C++, math) | 25% | ~85% | Mature, verified; C++ surface narrow (-5%), some math gaps. |
| Evidence/lineage/repro/memory foundation | 20% | ~80% | Append-only, lineage, reproduction verified; feature/label/model emission missing (-20%). |
| Research workflow composition | 15% | ~10% | Facade exists but no unified, versioned workflow model. |
| Institutional registries (artifact/metric/data/transform) | 10% | ~5% | Fragmented, none unified. |
| Query / search / knowledge (index, graph, meta-analysis) | 10% | ~5% | Only per-hash lineage traversal; no corpus query. |
| Presentation (notebook/report/dashboard/viz) | 5% | ~5% | Barely begun. |
| Scale / deployment (storage, distributed, GPU, cloud, API) | 15% | ~5% | Single-node SQLite; no platform surface. |

**Weighted total ≈ 34%.** The kernel is near-complete, but the *operating-system surface*
is between 5–10% complete. A fair, non-optimistic overall architecture completion is
**~35%**, not higher. The strength is concentrated where the risk is lowest; the
remaining 65% is where the institutional value and the risk both live.

---

## 9. Final verdict

| Capability | Current status | Dependency | Priority | Required before Phase 7? | Can postpone? |
|-----------|----------------|-----------|----------|---------------------------|---------------|
| Identity & Config Service | **Absent** | — | **Critical (P0)** | Yes | **No** |
| Artifact Catalog + Index | **Absent** | Identity/Config | **Critical (P0)** | Yes | **No** |
| Query Engine | **Absent** | Catalog/Index | **Critical (P0)** | Yes | **No** |
| Data Version Registry | **Absent** | Identity | **Critical (P0)** | Yes | **No** |
| Transformation (Feature/Label) Store | **Fragmented** | Emissions, Identity | **High (P1)** | Yes | **No** |
| Metric Registry | **Absent** | Query | **High (P1)** | Yes | **No** |
| Statistical Research Engine | **Duplicate (libs exist)** | Existing stats | **High (P1)** — as facade | Yes | **No** |
| Experiment Ranking | **Absent** | Query, Metrics | **High (P1)** | Yes | **No** |
| Experiment Comparison | **Absent** | Query, Metrics | **High (P1)** | Yes | **No** |
| Risk Analytics | **Partial (portfolio)** | Portfolio analytics | **High (P1)** | Yes | **No** |
| Ontology | **Partial (fragmented)** | Config/Identity | **High (P1)** | Yes | **No** |
| Meta-Analysis | **Absent** | Stats, Query, Ranking | **High (P1)** | Yes | **No** |
| Knowledge Graph | **Absent** | Ontology, Meta-analysis, Query | **Medium (P2)** | Yes | **Yes** |
| Research Memory | **Partial (market_memory)** | Knowledge Graph | **Medium (P2)** | Yes | **Yes** |
| Notebook | **Absent** | Workflow | **Medium (P2)** | No | **Yes** |
| Report Generator | **Absent** | Query, Metrics | **Medium (P2)** | No | **Yes** |
| Dashboard / Visualization | **Absent** | Query, Reports | **Low (P3)** | No | **Yes** |
| Archive | **Absent (merge into repository)** | Evidence Repository | **Medium (P2)** | Yes | **Yes** |
| Search Index | **Absent** | Query, Index | **Low (P3)** | No | **Yes** |
| Distributed / GPU / Cloud | **Absent** | Parity, storage, scheduler | **Low (P3)** | No | **Yes** |

---

## 10. Bottom line

- **Do not proceed with the proposed Tier 1 order.** Ranking and Comparison cannot
  precede Query/Index and Metric Registry.
- **Do not build a separate "Statistical Research Engine."** Certify the existing
  statistics modules as a facade; a second authority is an architectural defect.
- **Reverse the Knowledge Graph / Meta-Analysis dependency.** Meta-analysis feeds the
  graph, not the reverse.
- **Merge** Feature/Label/Transformation/Model into one Artifact Registry; **merge**
  Archive into the Evidence Repository; **merge** Research Memory into the Knowledge
  Graph retrieval layer.
- **Resolve the hidden blockers first:** identity consistency, additive schema
  evolution, hash-version migration, registry ownership, and the unimplemented
  Configuration Service. These gate the entire Tier 1–2 stack.
- The frozen kernel is sound; the **institutional OS surface is ~35% complete** and is
  where the remaining risk and value concentrate. Proceed additively, keep the Python
  reference as source of truth, and never let search/ML/GPU break the determinism and
  immutability contract.

**Verdict: Revised / Conditional.** The roadmap is directionally correct but requires
re-sequencing, de-duplication, and a mandatory foundation layer (identity, config,
catalog/index/query) before any ranking, comparison, or knowledge capability.

---

*Phase 6 Adversarial Architecture Audit — Independent Review*
*Classification: Internal — Architecture Review (no implementation)*
