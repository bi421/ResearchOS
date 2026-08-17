# Architecture Ownership — Canonical Reference

**Status:** canonical · **Detailed analysis:** `docs/architecture/hardening/` (10 documents, 2026-08-17 audit)

This document is the concise, binding answer to "who owns what." It exists so that no future change unifies, merges, or relocates these concepts based on name similarity.

---

## 1. Evidence Concept Ownership

There are **four evidence vocabularies. They are four lifecycle stages, NOT duplicates. Do not unify them.**

| Stage | Canonical type | Owner | Question it answers |
|-------|---------------|-------|---------------------|
| Certification envelope | `EvidenceEnvelope` | `researchos/evidence/` | *Which artifact, which hash, which parents?* (identity = content hash; append-only) |
| Reasoning evidence reference | `ReasoningEvidence` (alias `EvidenceItem`) | `researchos/reasoning_engine/` | *Which source, how reliable?* (frozen; `content_hash` aligns with envelope hashes) |
| Research interpretation | `Evidence` | `researchos/objects/evidence.py` | *What does this observation mean for a hypothesis?* (6-factor quality model, Articles XVI/XVII) |
| Decision evidence | `DecisionEvidenceItem` (alias `EvidenceItem`) | `researchos/decision_engine/` | *Which direction, how strong?* (versioned `DECISION_V1`; collectors never infer direction) |

Rule: new evidence-like concepts must declare which stage they belong to. Cross-stage movement happens through explicit adapters (collectors, emission modules), never by widening a schema.

## 2. Repository Taxonomy

Seven repositories = seven roles. **`RepositoryInterface` is load-bearing only for the research-object graph; do not force the others under it.**

| Role | Class | Store |
|------|-------|-------|
| Contract + default impl | `RepositoryInterface` / `MemoryRepository` | `researchos/repository/` |
| Central persistence + audit chain | `ResearchRepository` | `researchos/storage/` (SQLite `researchos.db`; sole runtime store) |
| Market-data bulk store | `DatasetRepository` / `SqliteDatasetRepository` | `researchos/data_engine/` |
| Pipeline state store | `PipelineRepository` | `researchos/pipeline_repository/` (deterministic JSON) |
| Graph projection | `EvidenceGraphStore` (alias `EvidenceRepository`) | `researchos/intelligence/` |
| Evidence ledger | `EvidenceRepository` | `researchos/evidence/` (append-only, content-addressed) |
| Market-memory store | `MarketMemoryRepository` | `researchos/market_memory/` |

Rule: new state gets a new role classification here, not silent membership in an existing store.

## 3. Market-Memory Layering

`researchos/memory/` and `researchos/market_memory/` are **layers, not duplicates — do not merge.**

- `objects/market_memory.py` — canonical **event vocabulary** (MarketStructure, LiquidityEvent, MarketSession, VolatilityState, NewsReference, MarketOutcome).
- `researchos/memory/` — **operational recorder** (audit-traited CRUD over injected `RepositoryInterface`).
- `researchos/market_memory/` — **analytical subsystem** (snapshots → features → similarity → scenario outcomes). Owns `MacroMarketEvent` (calendar/macro releases) and `MacroContextSnapshot` (DXY/yields/CPI snapshot) — renamed 2026-08-17 to end the name collisions with the objects layer.

## 4. Macro Architecture Boundary

`researchos/macro/` and `macro_intelligence/` are **separate systems with zero import connectivity** (AST-verified). Consolidation is gated behind a parity experiment on the `macro-consolidation` branch (adapter → mapping table → parity evidence → only then any retirement).

- `researchos/macro/` — **XAUUSD interpretation engine** (10 gold drivers, heuristic regime labels, wired into runtime via `engines/`). No new *generic* macro logic may be added here.
- `macro_intelligence/` — **generic macro domain library** (frozen contracts, econometrics, regime detection/classification/transition, relationships, time, events, knowledge). Asset-agnostic by invariant; asset-specific features do NOT belong here.
- Pre-declared integration point: `decision_engine.EvidenceSource.MACRO_INTELLIGENCE` (currently unwired).

## 5. Event Model Ownership

`macro_intelligence/contracts/event.py::MacroEvent` is the **canonical event model** (classification, affected instruments, market relevance, hashes). `market_memory` records scenario-level event context (`MacroMarketEvent`); calendar timing belongs to `macro_intelligence/time/` (`PlannedRelease` planned/actual times). Event → reaction → evidence → probabilistic context is the only sanctioned flow; **news → BUY/SELL paths are prohibited** (architecturally enforced by `macro_intelligence/audit/guards.py`).

## 6. Quant Engine Boundary

`researchos/quant_engine/` is **asset-agnostic scientific infrastructure** (Python reference; C++ acceleration via certified routing). Asset-specific code lives in: `data_engine/` loaders (per-asset), `experiments/` (per-asset experiments), and asset-context/macro-interpretation layers. No new asset-specific analytics may be added inside `quant_engine/`.
