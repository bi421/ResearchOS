# ARCHITECTURE_FORENSIC_REPORT.md — Complete Architectural Hardening Audit

**Date:** 2026-08-17 · **Mode:** AUDIT ONLY (no source modified) · **Baseline:** `pre-cleanup-baseline` (6a1e428), verified 3,475 tests / 86% coverage / ruff clean / C++ 526-526.

**Companion documents (this directory):** DEPENDENCY_GRAPH.md, EVIDENCE_OWNERSHIP_PROPOSAL.md, REPOSITORY_OWNERSHIP_PROPOSAL.md, MARKET_MEMORY_PROPOSAL.md, MACRO_OWNERSHIP_PROPOSAL.md, CROSS_ASSET_READINESS.md, SESSION_TIME_ARCHITECTURE.md, EVENT_INTELLIGENCE_ARCHITECTURE.md, CLEANUP_PLAN.md.

---

## 1. Executive Summary

The platform's scientific core is **sound and unusually well-disciplined**: no circular dependencies (AST-verified, 317 files), no look-ahead by construction (index-based walk-forward with leakage checks), deterministic by design, C++ strictly subordinated to the Python reference via certified routing, and no news→signal path anywhere (guarded architecturally). The problems are **topological, not scientific**: four evidence vocabularies that are actually four *stages* (misread as duplication), seven repositories that are actually seven *roles* (misread as proliferation), two macro systems with zero connectivity, two market-memory grains, and — the single most consequential finding — **the evidence certification ledger has no production emitter** (verified: zero imports from the experiment runtime; the package's own docstring says "No artifact emission hooks yet").

**Headline findings (risk-ranked):**

| # | Finding | Severity | Doc |
|---|---------|----------|-----|
| F1 | Evidence ledger built + tested but **no runtime emission hooks** — evidence-first guarantee is enforced only in tests | HIGH (integrity gap) | REPOSITORY §P2 |
| F2 | `data_engine/timezone.py` **silently treats unknown/IANA zone names as UTC** (docstring claims IANA support) — latent data-semantics bug | HIGH (latent correctness) | SESSION_TIME §P1 |
| F3 | Macro split-brain, 0 cross-imports (AST proof); live side is the heuristic one; scientific side is runtime-dead | HIGH (structural) | MACRO |
| F4 | Chronology enforced by index only; `ResearchDataset` has **no timestamp column** — time-ordering of inputs is a docstring convention, not a runtime check | MEDIUM (integrity hardening) | §6 below |
| F5 | `quant_engine/models.py:49` tick annualization = US-equity 252×6.5h assumption in generic models | MEDIUM (future-asset correctness) | CROSS_ASSET V4 |
| F6 | Name collisions: `EvidenceItem` ×2, `EvidenceRepository` ×2, `MarketEvent` ×2, `MacroState` ×2, `MacroRegime` ×3 — plus **`OBJECT_REGISTRY` rehydration trap** (market_memory variants would rehydrate as the wrong class if ever routed through the main store) | MEDIUM | EVIDENCE/REPO/MEMORY |
| F7 | `macro_intelligence` + package-local test roots **not in CI**; C++ CI **masks test failures** (`ctest || echo`); coverage CI measures `researchos` only | MEDIUM (verification blind spots) | DEPENDENCY §7 |
| F8 | Packaging: `include=["researchos*"]` — macro_intelligence importable only from repo root (works by CWD accident) | LOW-MEDIUM | DEPENDENCY §6 |
| F9 | Two divergent `EventCategory` enums; two UTC normalization stacks; free-text event classification | LOW (defer with macro) | SESSION_TIME/EVENT |

## 2. Inventory (per-directory purpose/liveness — verified)

See DEPENDENCY_GRAPH.md §2–§5 for the full table (every `researchos` subpackage, external packages, test map, liveness-by-coverage). Key liveness corrections vs. earlier folklore: **all** contested modules (decision_engine 83–100%, evidence 83–100%, intelligence 92–100%, market_memory 96–100%, memory 94%, macro 86%, reasoning_engine 89–100%) are alive and tested; earlier "0% decision_engine" was an artifact of a partial test-root run.

## 3. Dependency Forensics

Machine-verified (AST, no filename inference): clean DAG, 0 researchos↔macro_intelligence edges, exactly one dynamic import boundary (compiled C++ backend with Python-reference fallback, `research_cpp_backend.py:73`). No string-import or config-driven module loading exists.

## 4. Evidence Architecture

Four concepts = four lifecycle stages, **not** duplication: certification envelope (hash identity) → reasoning evidence reference (content-hash + reliability) → research interpretation object (hypothesis-bound, quality-scored) → decision evidence (directional, versioned). Unification would be an error. Real issues: the `EvidenceItem` name collision and the unwired reasoning layer (whose `content_hash` field already matches the certification hash contract — the intended bridge is visible). → EVIDENCE_OWNERSHIP_PROPOSAL.md.

## 5. Repository Architecture

Seven roles, one contract, and the contract is load-bearing exactly where it should be (pipeline/engines/memory consume `RepositoryInterface`; `ResearchRepository` is the sole runtime store). A god-interface would be a useless abstraction; append-only vs CRUD vs whole-graph vs bulk-dataset semantics are *correctly* different. → REPOSITORY_OWNERSHIP_PROPOSAL.md.

## 6. Backtesting / Experiments (scientific core — verified intact)

- **No look-ahead:** `data_engine/iterator.py` as_of guarantee; `validation/walk_forward.py:96-128` `_check_fold_leakage` rejects non-chronological, overlapping, gapped, future-referencing folds; phase51 walk-forward train 1200/valid 200/step 200, lookahead-safe features, net-of-cost self-validation (leakage_check AND out_of_sample AND cost_adjusted required to pass).
- **Costs:** spread/slippage/commission specs (`execution.py` generic `fixed:`/`pct:` parser); defaults documented; significance tested net-of-cost.
- **Determinism:** phase51 "no ML libraries, no randomness"; `simulation.py` RNG re-seeded deterministically from `request.seed + i` before every stochastic use (`:268,273`; scenario variants `:169,223`) — the unseeded constructor RNG at `:60` is dead-but-misleading (per-request determinism holds).
- **Gap F4:** `ResearchDataset` (`machine_learning/dataset_contracts.py:46-79`) carries no timestamps; chronology assumes caller-ordered inputs (phase51 docstring convention). The curated XAUUSD path satisfies this via the loader; a runtime order-assertion (cheap, additive) would close the assumption.
- **Timezone:** normalized upstream at load (loader `timezone` kwarg); phase51 correctly carries no timezone concept.
- **Publication- vs event-time:** modeled only in MIL `PlannedRelease` (planned/actual/estimated + delay) — correct owner; not needed in the backtest path.

## 7. Quant Engine / C++ Boundary (verified intact)

Python = scientific reference; C++ = acceleration; router certifies every candidate against the reference output and falls back on any capability/execution/numerical failure; `BackendExecutionMetadata` immutable with hash-excluded observational timing. Schema normalization (count→int, drawdown rounding, calmar recompute) preserves ResearchOS definitions. 526/526 C++ tests from a clean Release build (verified 2026-08-17). Asset-agnosticism: genuinely clean except the classified items in CROSS_ASSET_READINESS.md.

## 8. Market Memory, Macro, Time/Session, Events, Dashboard

→ MARKET_MEMORY_PROPOSAL.md (verdict: layered, not merged; fix names + registry trap), MACRO_OWNERSHIP_PROPOSAL.md (adapter-first migration on dedicated branch), SESSION_TIME_ARCHITECTURE.md (S1 silent-UTC bug is the priority), EVENT_INTELLIGENCE_ARCHITECTURE.md (right primitives, wrong topology; no news engine now).

**Dashboard:** `tools/build_dashboard.py` contains **zero** functions/classes and no numerical imports — a pure static-HTML emitter. Dashboard-as-visualization principle is already satisfied; no scientific logic in UI code exists to remove.

## 9. CI / Versioning / Packaging

- Versioning: 1.0.1 consistent (pyproject, version.py, __init__) — verified.
- CI gaps (F7): C++ `ctest || echo` can never fail; package-local test roots (`data_engine/tests`, `market_memory/tests`, `phase51/tests`) not in CI; `--cov=researchos` hides macro_intelligence coverage; CI matrix 3.10–3.12 vs local 3.14.6.
- Packaging (F8): `macro_intelligence` unimportable outside repo root (verified via `find_spec` from external CWD).

## 10. Scientific Integrity Gate — pre-classification of every proposed change

Changes that alter data semantics / methodology (→ require explicit approval, not cleanup):
- **S1 timezone error behavior** (dataset hashes of any mis-normalized load would change),
- **T1 annualization parameterization** (metrics semantics),
- **R1 evidence emission wiring** (touches experiment runtime — additive-only by design).

Pure architecture/hygiene (no semantic change): renames with aliases (H1/H4/M1/R2), documentation (H2/M2/T2/R3/E1), CI fixes (F7), packaging manifest.

## 11. DO NOT CHANGE (global list)

All frozen/versioned scientific surfaces: envelope hash scheme; decision methodology (`DECISION_V1`, scoring/probability); objects' quality/aging/tier constants (Articles XVI); walk-forward/splitter arithmetic; cost-model parser; router certification flow; MIL frozen contracts + tier guard; matcher feature weights; engine audit-per-action invariant; C++ numerical code absent a demonstrated parity flaw.
