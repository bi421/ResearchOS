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

# Phase 6 — Institutional Research Platform Design Audit

**Status:** DESIGN AUDIT ONLY — no implementation
**Classification:** Internal — Senior Architecture Board
**Audience:** Chief Systems Architect, Engineering Leads
**Base:** ResearchOS V1 Freeze (`3f4510f`) + Phase 5.1–5.3c verified stack
**Current verification:** 2540 tests passing; evidence chain
Dataset → Experiment → Run → Result → Validation deterministic, content-addressed,
append-only, tamper-verified, and reproducible.

---

## 0. Executive Summary

ResearchOS has validated a **trustworthy scientific core**: deterministic
hashing, immutable experiment/run/result contracts, certified computation
router, and an append-only, tamper-verified evidence repository with full
lineage and reproduction. This is the correct foundation for an
institutional-grade quantitative research operating system.

What is **absent** is the layer that turns a *correct* core into a *usable and
scalable* research platform: research workflow composition, knowledge
management, search/query, visualization, report generation, model/metadata
registries, experiment ranking, meta-analysis, and the institutional plumbing
(performance, storage scale, deployment).

This document audits every major subsystem, classifies each missing capability,
and proposes a Phase 6 / Phase 7 / later roadmap. It is architecture-only and
contains no code.

---

## 1. Current maturity assessment

| Layer | Maturity | Evidence |
|-------|----------|----------|
| Deterministic hashing / identity | **Production** | `backend_hash.py`, Hash Scheme v2, provenance chaining |
| Immutable Experiment/Run/Result contracts | **Production** | `experiments/result.py`, MappingProxyType protection |
| Dataset provenance | **Production** | `data_engine/hashing.py`, runner dataset-provenance hash |
| Certified computation router | **Production** | `BackendRouter`, `NumericalComparator`, capabilities, scheduler |
| Evidence repository (append-only) | **Production** | `evidence/repository.py`, tamper detection |
| Evidence envelope (Hash Scheme v2) | **Production** | `evidence/envelope.py`, `HASH_SCHEME_VERSION=2` |
| Dataset/Experiment/Run/Result/Validation emission | **Production** | `evidence/*_emission.py` |
| Lineage query engine | **Production** | `evidence/lineage.py` |
| Reproduction engine / deterministic replay | **Production** | `evidence/reproduction.py` |
| Analytical engines (technical, probability, portfolio, historical, fundamental, econometrics) | **Core math present; integration partial** | `quant_engine/*/`, certified surface exists but not the full institutional surface |
| Research workflow composition | **Immature / absent** | No single `ResearchWorkflow`; pieces exist (`orchestration/`, `pipeline/`) |
| Knowledge management / ontology | **Foundation only** | `intelligence/`, `objects/knowledge.py`, `objects/ontology` partial |
| Search & query | **Absent** | No cross-artifact search/index |
| Visualization & reporting | **Absent** | No dashboard/report renderer (static `static/index.html` only) |
| Model / artifact / experiment registries | **Partial** | `machine_learning/models/registry.py`, `training/repository.py` exist but not unified |
| Experiment ranking & meta-analysis | **Absent** | No comparative analytics |
| Storage scalability / distribution | **Single-node SQLite** | `storage/repository.py` in-memory/SQLite |
| C++ acceleration | **Certified, narrow** | Regression + rolling stats only |
| GPU / distributed / cloud | **Absent** | — |

**Overall maturity: a strong, verified scientific kernel (Phase 1–5) with an
incomplete institutional shell (the "research operating system" layer).**

---

## 2. Capability gap analysis

For every missing capability:

- **Name**
- **Purpose**
- **Importance** (Critical / High / Medium / Low)
- **Dependencies**
- **Implementation difficulty** (Low / Medium / High)
- **Risk**
- **Estimated work package**
- **Estimated number of files**
- **Estimated tests**
- **Phase assignment** (Phase 6 / Phase 7 / later)

### 2.1 Research workflow

#### RW-1 — Unified Research Workflow Engine
- **Purpose:** Compose hypothesis → dataset → features/labels → compute →
  validation → evidence → report into one deterministic, hashable, resumable
  workflow object (the Phase 5.2 facade, formalized).
- **Importance:** Critical
- **Dependencies:** ResearchEngine (exists), evidence emissions (exist), validation
- **Difficulty:** High
- **Risk:** Medium (non-determinism / hidden state)
- **Work package:** WP6-1
- **Files:** ~8
- **Tests:** ~40
- **Phase:** Phase 6

#### RW-2 — Research Notebook / Project Model
- **Purpose:** Persistent, versioned research projects tying hypotheses, datasets,
  experiments, notes, and reports together.
- **Importance:** High
- **Dependencies:** RW-1, evidence repository
- **Difficulty:** Medium
- **Risk:** Low
- **Work package:** WP6-2
- **Files:** ~6
- **Tests:** ~25
- **Phase:** Phase 6

#### RW-3 — Institutional Reproducibility Bundle
- **Purpose:** Export a self-contained "repro package" (inputs + params +
  methodology + code pointer + evidence lineage) for independent re-execution
  and audit sign-off.
- **Importance:** Critical
- **Dependencies:** ReproductionEngine (exists), RW-1
- **Difficulty:** Medium
- **Risk:** Low
- **Work package:** WP6-3
- **Files:** ~5
- **Tests:** ~30
- **Phase:** Phase 6

### 2.2 Knowledge management

#### KM-1 — Structured Research Ontology Service
- **Purpose:** Formalize market concepts, relationships, and methodology taxonomies
  so all artifacts share a uniform vocabulary (currently fragmented).
- **Importance:** High
- **Dependencies:** `objects/knowledge.py`, `intelligence/`
- **Difficulty:** Medium
- **Risk:** Low
- **Work package:** WP6-4
- **Files:** ~6
- **Tests:** ~30
- **Phase:** Phase 6

#### KM-2 — Knowledge / Insights Graph
- **Purpose:** Directed graph of findings, hypotheses, evidence, and outcomes
  enabling cross-study inference and contradiction detection at scale.
- **Importance:** High
- **Dependencies:** KM-1, evidence lineage
- **Difficulty:** High
- **Risk:** Medium
- **Work package:** WP6-5
- **Files:** ~8
- **Tests:** ~35
- **Phase:** Phase 6

#### KM-3 — Meta-Analysis Engine
- **Purpose:** Aggregate multiple experiments/studies statistically (effect-size
  pooling, heterogeneity, publication-bias heuristics) to rank the strength of a
  research conclusion.
- **Importance:** High
- **Dependencies:** evidence repository, statistics, experiment ranking (ER-1)
- **Difficulty:** High
- **Risk:** Medium (statistical rigor)
- **Work package:** WP6-6
- **Files:** ~7
- **Tests:** ~40
- **Phase:** Phase 6

#### KM-4 — Historical Market-Memory Retrieval
- **Purpose:** Structured retrieval over market-memory scenarios/outcomes for
  pattern-backed research (extends `market_memory/`).
- **Importance:** Medium
- **Dependencies:** `market_memory/`, evidence lineage
- **Difficulty:** Medium
- **Risk:** Low
- **Work package:** WP6-7
- **Files:** ~5
- **Tests:** ~25
- **Phase:** Phase 6

### 2.3 Evidence & lifecycle

#### EV-1 — Feature & Label Evidence Emission
- **Purpose:** Emit features/labels/datasets (not just results) as first-class
  evidence artifacts with lineage — closes a Phase 5.2/5.3 gap.
- **Importance:** High
- **Dependencies:** evidence envelope/repository (exist)
- **Difficulty:** Medium
- **Risk:** Low
- **Work package:** WP6-8
- **Files:** ~4
- **Tests:** ~25
- **Phase:** Phase 6

#### EV-2 — Model Evidence Emission + Model Registry Unification
- **Purpose:** Uniformly version/hash/store deterministic model contracts and
  their metadata into the evidence store (Phase 5.3 G-M2 closure).
- **Importance:** High
- **Dependencies:** `models/registry.py`, `training/repository.py`, evidence
- **Difficulty:** Medium
- **Risk:** Medium (must not creep to stochastic ML)
- **Work package:** WP6-9
- **Files:** ~6
- **Tests:** ~30
- **Phase:** Phase 6

#### EV-3 — Artifact Indexing & Cross-Artifact Query
- **Purpose:** Index all evidence artifacts by type, methodology, params, hash,
  and lineage for fast programmatic query.
- **Importance:** High
- **Dependencies:** evidence repository, lineage
- **Difficulty:** Medium
- **Risk:** Low
- **Work package:** WP6-10
- **Files:** ~6
- **Tests:** ~35
- **Phase:** Phase 6

#### EV-4 — Append-Only Retention / Archival Policy
- **Purpose:** Cold-storage archival, compaction, and retention policy for the
  append-only store without breaking lineage.
- **Importance:** Medium
- **Dependencies:** storage, evidence
- **Difficulty:** Medium
- **Risk:** Medium (lineage preservation)
- **Work package:** WP6-11
- **Files:** ~4
- **Tests:** ~20
- **Phase:** Phase 7

### 2.4 Experiment lifecycle

#### EL-1 — Experiment Ranking & Portfolio of Experiments
- **Purpose:** Rank experiments by significance, robustness, evidence quality —
  a research "leaderboard".
- **Importance:** High
- **Dependencies:** evidence, statistics, validation
- **Difficulty:** Medium
- **Risk:** Low
- **Work package:** WP6-12
- **Files:** ~5
- **Tests:** ~30
- **Phase:** Phase 6

#### EL-2 — Strategy Comparison & Attribution
- **Purpose:** Compare multiple strategies/research variants head-to-head with
  rigorous attribution (extend `engines/attribution.py`).
- **Importance:** High
- **Dependencies:** EL-1, evidence, portfolio analytics
- **Difficulty:** Medium
- **Risk:** Low
- **Work package:** WP6-13
- **Files:** ~6
- **Tests:** ~35
- **Phase:** Phase 6

### 2.5 Statistical & mathematical research

#### SR-1 — Certified Statistical Inference Surface
- **Purpose:** Router-certified hypothesis tests, estimators, confidence
  intervals, and calibration (formalize `probability/`, `econometrics/`).
- **Importance:** High
- **Dependencies:** ResearchEngine (exists), numerical validation
- **Difficulty:** Medium
- **Risk:** Low
- **Work package:** WP6-14
- **Files:** ~6
- **Tests:** ~40
- **Phase:** Phase 6

#### SR-2 — Pattern Discovery & Regime Classification Engine
- **Purpose:** Deterministic pattern/regime discovery over historical data with
  evidence-backed validation (extend `market_memory/`, `technical/`).
- **Importance:** Medium
- **Dependencies:** KM-4, technical/historical analytics
- **Difficulty:** High
- **Risk:** High (must stay deterministic, avoid overfitting)
- **Work package:** WP6-15
- **Files:** ~8
- **Tests:** ~40
- **Phase:** Phase 7

### 2.6 Risk analytics

#### RS-1 — Research Risk Analytics Module
- **Purpose:** Quantify model/regime risk, parameter sensitivity, and stress
  behavior of research findings (extend `portfolio/`, `econometrics/`).
- **Importance:** High
- **Dependencies:** portfolio/econometrics analytics, evidence
- **Difficulty:** Medium
- **Risk:** Medium
- **Work package:** WP6-16
- **Files:** ~6
- **Tests:** ~35
- **Phase:** Phase 6

### 2.7 Interface & presentation

#### IF-1 — Research Query Engine (SQL-like cross-artifact)
- **Purpose:** Declarative query across experiments, results, models, datasets,
  and lineage.
- **Importance:** High
- **Dependencies:** EV-3 (indexing)
- **Difficulty:** Medium
- **Risk:** Low
- **Work package:** WP6-17
- **Files:** ~6
- **Tests:** ~35
- **Phase:** Phase 6

#### IF-2 — Full-Text + Semantic Search
- **Purpose:** Search research reports, notes, hypotheses, and findings by text
  and embedding (deterministic, non-trading).
- **Importance:** Medium
- **Dependencies:** KM-1, indexing
- **Difficulty:** Medium
- **Risk:** Low
- **Work package:** WP6-18
- **Files:** ~6
- **Tests:** ~25
- **Phase:** Phase 7

#### IF-3 — Visualization Layer
- **Purpose:** Deterministic charts/dashboards for equity curves, drawdown,
  calibration, comparisons, and lineage trees.
- **Importance:** Medium
- **Dependencies:** IF-1, experiment results
- **Difficulty:** Medium
- **Risk:** Low
- **Work package:** WP6-19
- **Files:** ~8 (JS/HTML + Python)
- **Tests:** ~20
- **Phase:** Phase 7

#### IF-4 — Report Generation Service
- **Purpose:** Institutional report templates (Markdown/PDF/JSON) with the
  reproducibility + explainability envelope auto-included.
- **Importance:** High
- **Dependencies:** RW-3, IF-1
- **Difficulty:** Medium
- **Risk:** Low
- **Work package:** WP6-20
- **Files:** ~7
- **Tests:** ~25
- **Phase:** Phase 6

### 2.8 Performance & infrastructure

#### PF-1 — Certified Analytical Acceleration (C++ / Python-kernel)
- **Purpose:** Extend phase-4.5 certified acceleration to O(n) analytical loops
  (technical indicators, covariance, econometric filters) with Python reference
  parity. (Phase 5.4 WP-6 carry-forward.)
- **Importance:** Medium
- **Dependencies:** C++ build, NumericalComparator, benchmark harness
- **Difficulty:** High
- **Risk:** High (hash parity)
- **Work package:** WP6-21
- **Files:** ~10 (C++ + Python)
- **Tests:** ~50
- **Phase:** Phase 7

#### PF-2 — Performance Profile Pipeline
- **Purpose:** Feed certi evidence-backed op timings into the scheduler profile
  (Phase 5.5 WP-7 carry-forward).
- **Importance:** Medium
- **Dependencies:** PF-1, benchmark harness
- **Difficulty:** Medium
- **Risk:** Low-Medium
- **Work package:** WP6-22
- **Files:** ~4
- **Tests:** ~20
- **Phase:** Phase 7

#### PF-3 — GPU Acceleration (Research kernels)
- **Purpose:** Offload large matrix/statistical kernels to GPU where
  order-stable reductions allow, preserving parity.
- **Importance:** Low
- **Dependencies:** PF-1, NumericalComparator
- **Difficulty:** High
- **Risk:** High (parity / determinism)
- **Work package:** WP7-1
- **Files:** ~8
- **Tests:** ~40
- **Phase:** later

#### PF-4 — Distributed Execution
- **Purpose:** Shard independent experiment/feature/validation work across
  workers while keeping per-unit determinism and mergeable evidence.
- **Importance:** Low
- **Dependencies:** PF-2, storage scale
- **Difficulty:** High
- **Risk:** High (determinism + lineage merge)
- **Work package:** WP7-2
- **Files:** ~10
- **Tests:** ~40
- **Phase:** later

#### PF-5 — Scalable Storage / Object Store
- **Purpose:** Content-addressed artifact store (parquet/object store) with
  lineage index, replacing single-node SQLite for large corpora.
- **Importance:** Medium
- **Dependencies:** EV-3, evidence
- **Difficulty:** High
- **Risk:** Medium (migration without breaking lineage)
- **Work package:** WP7-3
- **Files:** ~8
- **Tests:** ~35
- **Phase:** later

#### PF-6 — Cloud Deployment & Platform APIs
- **Purpose:** Managed deployment, auth, multi-tenant isolation, REST/gRPC
  surface over the research kernel.
- **Importance:** Low
- **Dependencies:** most of Phase 6/7
- **Difficulty:** High
- **Risk:** Medium
- **Work package:** WP7-4
- **Files:** ~15
- **Tests:** ~40
- **Phase:** later

---

## 3. Recommended roadmap

### Phase 6 — "Institutional Research OS" (the shell)
Focus: make the verified scientific kernel **usable, composable, searchable,
comparable, and auditable** for a research desk.

Priority order (within Phase 6):
1. **RW-1 Unified Research Workflow Engine** — the single composition facade.
2. **EV-1 Feature & Label Emission** + **EV-2 Model Registry Unification** —
   first-class artifacts for every study.
3. **EL-1 Experiment Ranking** + **EL-2 Strategy Comparison** — value for the
   desk.
4. **SR-1 Certified Statistical Surface** + **RS-1 Research Risk Analytics** —
   rigorous analytics.
5. **EV-3 Artifact Indexing** + **IF-1 Query Engine** — retrieval.
6. **KM-1 Ontology** + **KM-2 Knowledge Graph** — shared vocabulary over
   artifacts.
7. **RW-2 Research Notebook** + **RW-3 Reproducibility Bundle** + **IF-4 Report
   Generation** — the institutional deliverable.
8. **KM-3 Meta-Analysis** + **KM-4 Market-Memory Retrieval** — synthesis.

### Phase 7 — "Scale & Accelerate"
- **EV-4** archival policy, **IF-2** semantic search, **IF-3** visualization,
  **PF-1** analytical acceleration, **PF-2** performance profile, **SR-2**
  pattern discovery.

### Later — "Distributed & Cloud"
- **PF-3 / PF-4 / PF-5 / PF-6** GPU, distributed execution, object-store scale,
  cloud platform.

---

## 4. Prioritized implementation order

| Priority | Capability | Phase | Rationale |
|----------|-----------|-------|-----------|
| 1 | RW-1 Unified Workflow Engine | 6 | Composition facade everything else hangs on |
| 2 | EV-1 Feature/Label emission | 6 | Completes artifact coverage |
| 3 | EV-2 Model registry unification | 6 | Closes G-M2, enables meta-analysis |
| 4 | EL-1 Experiment ranking | 6 | Direct institutional value |
| 5 | EL-2 Strategy comparison | 6 | Desk-facing |
| 6 | SR-1 Certified statistics | 6 | Rigor of all downstream analytics |
| 7 | RS-1 Research risk analytics | 6 | Institutional risk posture |
| 8 | EV-3 Artifact indexing | 6 | Enables query/search |
| 9 | IF-1 Query engine | 6 | Retrieval |
| 10 | KM-1 Ontology | 6 | Shared vocabulary |
| 11 | KM-2 Knowledge graph | 6 | Cross-study inference |
| 12 | RW-3 Reproducibility bundle | 6 | Audit sign-off |
| 13 | RW-2 Research notebook | 6 | Persistence model |
| 14 | IF-4 Report generation | 6 | Deliverable |
| 15 | KM-3 Meta-analysis | 6 | Synthesis |
| 16 | KM-4 Market-memory retrieval | 6 | Pattern-backed research |
| 17 | EV-4 Archival | 7 | Scale |
| 18 | IF-2 Semantic search | 7 | UX |
| 19 | IF-3 Visualization | 7 | UX |
| 20 | PF-1 C++ acceleration | 7 | Performance |
| 21 | PF-2 Perf profile | 7 | Scheduler |
| 22 | SR-2 Pattern discovery | 7 | Advanced research |
| 23 | PF-3/4/5/6 GPU/distributed/scale/cloud | later | Infrastructure |

---

## 5. Critical blockers

1. **No unified workflow facade (RW-1).** Reproducibility is proven per-artifact,
   but not yet per-research-workflow. This is the single most important blocker
   to institutional usability.
2. **Fragmented registries.** Model/artifact/experiment metadata is split across
   `models/registry.py`, `training/repository.py`, and evidence emission. Without
   unification (EV-2, EV-3), meta-analysis and ranking are impossible.
3. **No cross-artifact query/search.** Every lookup today is per-hash or
   per-lineage; there is no declarative query over the corpus (IF-1).
4. **Storage is single-node SQLite.** Content-addressed scale and archival (EV-4,
   PF-5) require a bulletproof, lineage-preserving migration — a high-risk item
   that must not be rushed.
5. **Determinism vs. statistical/ML dark side.** Any foray into pattern
   discovery, embeddings (IF-2), or GPU (PF-3) risks nondeterminism and
   overfitting. Each must carry certified parity and a strict
   determinism/explainability gate.
6. **Hash-parity risk in acceleration.** C++/GPU acceleration (PF-1, PF-3) can
   break the byte-level hash contract; must be order-stable and gated by
   `NumericalComparator`.

---

## 6. What should never be implemented

ResearchOS is a **scientific research operating system**, not a trading/broker
system. The following must remain **out of scope, forever**:

- ❌ **Live order execution / broker integration** — the frozen architecture
  explicitly excludes `execution/`, `strategy/` from the core.
- ❌ **Signal generation / trading recommendations** — reports must never
  produce buy/sell directives.
- ❌ **Stochastic ML/DL model families** — no gradient descent, random forests,
  neural nets, or any non-deterministic inference in the certified core. The
  existing whitelist (rule-based / linear / threshold / feature-weight) stays.
- ❌ **Non-deterministic any source** — no wall-clock dependence in hashes, no
  unseeded randomness, no hidden state in workflows.
- ❌ **In-place mutation of evidence** — append-only + tamper detection is
  non-negotiable.
- ❌ **Skipping the trust boundary** — no computation path that bypasses the
  certified router / Python reference.
- ❌ **Asset-class-specific logic leaking into the core** — extend via the Data
  Layer only (Extension Rule 1).
- ❌ **Subjectivity / "advisor" behavior** — no claims of certainty, no
  overriding human judgment, no financial advice.

---

## 7. Long-term architecture vision

```
┌──────────────────────────────────────────────────────────────────────┐
│  PRESENTATION / INSTITUTIONAL SURFACE (Phase 6–7)                    │
│  Research Notebook · Reports · Dashboards · Query · Search · Export  │
├──────────────────────────────────────────────────────────────────────┤
│  RESEARCH OPERATING SYSTEM LAYER (Phase 6)                           │
│  Workflow Engine · Ontology · Knowledge Graph · Meta-Analysis        │
│  Experiment Ranking · Strategy Comparison · Risk Analytics            │
├──────────────────────────────────────────────────────────────────────┤
│  RESEARCH KERNEL (VERIFIED — Phase 1–5) — FROZEN CONTRACTS           │
│  Evidence Repository · Lineage · Reproduction · Certified Router     │
│  Immutable Contracts · Deterministic Hashing · Feature/Label         │
│  Analytical Engines (technical/probability/portfolio/historical/     │
│  fundamental/econometrics) · Validation                              │
├──────────────────────────────────────────────────────────────────────┤
│  COMPUTE & STORAGE BACKENDS (Phase 7 / later — always candidates)    │
│  Python reference (source of truth) → C++ → GPU → distributed        │
│  SQLite → object store / parquet → cloud                            │
└──────────────────────────────────────────────────────────────────────┘
```

Guiding principles for all future work:
- **The scientific kernel stays frozen and additive.** New capabilities are
  additive subclasses/facades; the Python reference remains the only source of
  truth.
- **Every new surface is deterministic, explainable, and evidence-backed** —
  inputs + parameters + methodology version + lineage on every artifact.
- **Institutional trust is the product.** Reproducibility, append-only
  immutability, tamper detection, and audit sign-off are the competitive moat.
- **Never expand into trading/broker/ML-dark side.** The platform's identity is
  a scientific research operating system for human researchers.

**Phase 6 should begin with WP6-1 (Unified Research Workflow Engine) and
WP6-8/WP6-9 (Feature/Label + Model evidence emission), which unblock ranking,
query, meta-analysis, and institutional reproducibility.**

---

*Phase 6 Architecture Design Audit — Version 1.0.0*
*Classification: Internal — Design Audit (no implementation)*
