# CLEANUP_PLAN.md — Staged Change Plan

**Date:** 2026-08-17. Execution requires explicit approval. High-risk phases use dedicated branches. Verification contract below applies to every phase.

---

## Verification Contract (every phase)

Full Python suite (baseline 3,475 passed / 58 skipped) · Ruff clean · Coverage ≥ 86% (no material decrease) · Import smoke test · `pip install -e .` succeeds · C++ build+ctest if affected · Determinism tests · Git diff inspection. High-risk phases additionally: baseline test-count/coverage/API/dependency-graph comparison and scientific-output byte-comparison. **STOP on any unexplained regression.**

---

## PHASE A — Zero-Risk Hygiene (`cleanup-safe` branch or direct)

| ID | Action | Evidence |
|----|--------|----------|
| A1 | Fix C++ CI: remove `\|\| echo` so `ctest` failures fail CI; build Release explicitly; drop unused boost install | DEPENDENCY §7 |
| A2 | Add package-local test roots to CI pytest invocation (`researchos/data_engine/tests researchos/market_memory/tests researchos/experiments/phase51/tests`) | DEPENDENCY §7 |
| A3 | Extend CI coverage to `--cov=macro_intelligence` (report-only, no gate yet) | DEPENDENCY §7 |
| A4 | Write ownership docs: evidence-concept map (H2), repository taxonomy (R3), market-memory layering (M2), macro boundary rule (T2), MacroEvent-canonical note (E1) | all proposals |
| A5 | Add `researchos/macro/__init__.py` (package hygiene; no behavior change) | MACRO |

**SAFE TO EXECUTE NOW** (after approval): all of Phase A.

## PHASE B — Repository Structure (`cleanup-safe`)

| ID | Action | Risk |
|----|--------|------|
| B1 | Alias-rename `intelligence.EvidenceRepository` → `EvidenceGraphStore` (R2) | Low |
| B2 | Alias-rename `decision_engine.EvidenceItem` → `DecisionEvidenceItem`; `reasoning_engine.EvidenceItem` → `ReasoningEvidence` (H1) | Low |
| B3 | Alias-rename `market_memory/events.MarketEvent` → `MacroMarketEvent`; `market_memory/models.MacroState` → `MacroContextSnapshot` (M1) + negative rehydration test for the OBJECT_REGISTRY trap (F6) | Low |

All renames: new name canonical, old name = deprecated alias; tests updated mechanically; no field/formula changes. **SAFE TO EXECUTE NOW** with Phase A.

## PHASE C — Memory Architecture (`memory-consolidation` branch)

- C1: (optional, recommended-defer) M3 — `MarketMemoryRepository` persistence over `RepositoryInterface`/`ResearchRepository` instead of own SQLite file. Only if/when market-memory needs the audit chain. **REQUIRES REVIEW.**

## PHASE D — Evidence Architecture (`evidence-consolidation` branch)

- D1: **R1 — wire ONE emission hook**: experiment runner deposits Run/Result envelopes post-run via existing emission modules. Additive-only; existing outputs byte-identical; new integration test asserts ledger contents + lineage. **REQUIRES REVIEW** (touches experiment runtime; scientific-integrity-positive). Highest-value change in this plan.
- D2: H3 — wire `reasoning_engine` as the envelope→reasoning bridge (`content_hash` fields already align) or formally park it as reserved foundation. **REQUIRES REVIEW.**

## PHASE E — Macro Architecture (`macro-consolidation` branch)

- E-1: adapter emitting `EvidenceSource.MACRO_INTELLIGENCE` decision evidence (no deletions).
- E-2: regime mapping table (researchos labels ↔ MIL enums) as data + round-trip tests.
- E-3: parity experiment (MIL detection vs heuristic engine on same inputs) with artifacts in the evidence store; migration decided **by that evidence**.
- E-4 (only after E-3): retire heuristic regime classification; keep gold-driver scoring as XAUUSD asset knowledge; dedupe `EventCategory` enums (S4).
**HIGH RISK / SEPARATE BRANCH. Never combined with other phases.**

## PHASE F — Cross-Asset (`cross-asset-expansion` branch, when DXY work starts)

- F1: T3 instrument-metadata contract (symbol → tick, calendar id, currency, annualization, session ids).
- F2: T1 annualization parameterization (explicit per-request value first; default change never without approval).
- F3: S3 FX session calendar as data (session definitions + boundary resolver; no hardcoded city logic in engine).
- F4: V1/V2 cosmetic-default cleanups (compatibility.py label, fundamental US/USD defaults → explicit args).

## PHASE G — News/Event Intelligence (explicit request only)

- G1: E2 reaction-aggregation read-only layer. G2: E3 entity layer + taxonomy consolidation (me/v2). **DEFER until requested.**

## PHASE H — Dashboard Evolution (DEFER)

Static emitter only today; nothing to evolve until a live research interface is requested. Boundary rule already documented in Phase A docs.

## Scientific-Integrity-Gated Items (approval = scientific change, not cleanup)

| Item | Why gated |
|------|-----------|
| S1 timezone silent-UTC fix (raise on unknown / zoneinfo) | Dataset hashes of mis-normalized loads would change; verify curated XAUUSD loader hashes unchanged |
| D1 emission wiring | Touches experiment runtime (additive by design) |
| T1 annualization | Metrics semantics |

## Decision Summary

- **SAFE TO EXECUTE NOW (on approval):** Phase A (A1–A5) + Phase B (B1–B3).
- **REQUIRES REVIEW:** C1, D1, D2, S1, T1.
- **HIGH RISK / SEPARATE BRANCH:** Phase E (macro-consolidation); F2 default changes.
- **DEFER:** G (event intelligence), H (dashboard), S2 (UTC-stack unification), S4 (enum dedupe → rides with E-4), C1 unless needed.
