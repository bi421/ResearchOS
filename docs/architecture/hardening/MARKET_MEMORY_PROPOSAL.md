# MARKET_MEMORY_PROPOSAL.md

**Date:** 2026-08-17 — AUDIT ONLY. No implementation.

---

## CURRENT STATE

Two subsystems, zero imports between them (verified both directions):

| | `researchos/memory/` + `objects/market_memory.py` | `researchos/market_memory/` |
|---|---|---|
| Grain | **Event-level operational memory**: `MarketStructure` (BOS/CHOCH), `LiquidityEvent`, `MarketSession`, `VolatilityState`, `NewsReference`, `MarketOutcome` — BaseObjects with confirm()/resolve() lifecycle, audit-trailed | **Snapshot-level analytical memory**: `MarketSnapshot`, `MarketRegime`, `HistoricalScenario` — features → similarity → scenario matcher → outcome statistics |
| Engine | `MarketMemoryEngine` (CRUD service over injected `RepositoryInterface`; writes `AuditEntry` per action) | `MarketMemoryIntegrator` (adapter hooks; all 7 optional callables) + `ScenarioMatcher`, `OutcomeAnalysis`, `MarketMemoryReport` |
| Persistence | Injected repo (tests use `MemoryRepository`; objects round-trip `ResearchRepository` SQLite via `OBJECT_REGISTRY` — proven `test_market_memory.py:511-553`) | Own `MarketMemoryRepository`: always in-memory (4× `MemoryRepository`) + optional own SQLite mirror table; independent of `researchos.db` |
| Tests | `researchos/tests/test_market_memory.py` (94% cov engine) | `market_memory/tests/` + `researchos/tests/test_market_memory_q5.py` (96–100% cov) |
| Runtime wiring | **None** (instantiated only in tests) | **None** (`MarketMemoryIntegrator` instantiated only in `test_market_memory_q5.py:905-975`) |

## PROBLEM

1. **Two name collisions with divergent semantics (verified field-by-field):**
   - `MarketEvent`: `objects/market_memory.py:23` = *price-structure event* (`event_type, asset, timeframe, direction, price_level...`, seed `MarketEvent|{type}|{asset}|{tf}|{ts}|{price}`) vs `market_memory/events.py:21` = *calendar/macro data release* (`impact, actual/expected/previous_value, source`, different seed). Share only `event_type/timestamp/asset/description`.
   - `MacroState`: `objects/observation.py:248` (regime/inflation/growth/policy_stance/risk_factors) vs `market_memory/models.py:243` (dxy/real_yield/cpi/fed_event/nfp). Share only `timestamp/geography/confidence`.
2. **`OBJECT_REGISTRY` rehydration trap:** registry maps `"MarketEvent" → objects` variant and `"MacroState" → observation` variant (`storage/repository.py:63,90-96`). If a market_memory variant were ever saved through `ResearchRepository.save_object`, rehydration would construct the **wrong class** (fields don't match). Cannot happen today (different DB paths) — a trap for any future consolidation.
3. Conceptual overlap without collision: `VolatilityState` (objects, event) vs `volatility` scalars (snapshots); `MarketOutcome.MFE/MAE` vs `HistoricalScenario` MFE/MAE fields — same concepts at different grain, not duplicated logic.

## EVIDENCE

- No duplicated *logic* exists between the subsystems — different grain (event vs snapshot), different access patterns (audited single-object CRUD vs bulk similarity scans), disjoint model modules, disjoint repositories, disjoint test files.
- `MarketMemoryIntegrator` without adapters returns `{"status": "standalone"}` everywhere (`integration.py:61` et al.) — it was designed as the future bridge point and never connected.
- `decision_engine.contracts.EvidenceSource.MARKET_MEMORY` — the decision layer already expects a market-memory evidence producer (pre-declared, unwired, same pattern as MACRO_INTELLIGENCE).

## TARGET STATE

**Classification: (B) remain separate — intentionally layered. Do not merge.**

```
objects/market_memory.py      domain events (structure/liquidity/session/news/outcome)   [canonical event vocabulary]
researchos/memory/            operational recording service (audit-trailed CRUD)         [write side]
researchos/market_memory/     analytical similarity/outcome subsystem                    [read/analysis side]
future bridge                 MarketMemoryIntegrator adapters + decision_engine MARKET_MEMORY evidence
```

Minimal hardening:

- **M1 — Resolve the name collisions (REQUIRES REVIEW, do before any cross-wiring):**
  - `market_memory/events.MarketEvent` → rename to `MacroMarketEvent` (or `CalendarEvent`); it models data releases, not structure events. Alias first, remove later.
  - `market_memory/models.MacroState` → rename to `MacroContextSnapshot` (it *is* a snapshot of macro context: dxy/real_yield/cpi...). Prevents the registry trap permanently.
- **M2 — Document the layering** (events → recorder → analytics) in architecture docs so nobody "unifies" them.
- **M3 — IF persistence consolidation is ever wanted** (optional, later): make `MarketMemoryRepository` consume `RepositoryInterface`/`ResearchRepository` instead of its own SQLite file — it already embeds four `MemoryRepository` instances; this grants the audit chain and main DB for free while leaving analytical modules untouched. Separate branch.

## MIGRATION RISK

| Step | Risk | Notes |
|------|------|-------|
| M1 renames | Low | market_memory + its 2 test files only; alias keeps compatibility |
| M2 docs | None | — |
| M3 persistence consolidation | Medium | touches market_memory storage; must preserve in-memory-first semantics tests rely on |
| Merging the subsystems | **NOT PROPOSED** | would force one persistence model onto two access patterns; no duplicated logic to eliminate |

## REQUIRED TESTS (if M1/M3 proceed)

- Full suite (3,475), ruff, coverage ≥ 86%.
- M1: alias smoke test; negative test that `OBJECT_REGISTRY` rehydration of a renamed market_memory type raises/never silently constructs the objects-layer class.
- M3: round-trip test through `ResearchRepository` SQLite replacing the mirror-table test; identical query results.

## DO NOT CHANGE

- `ScenarioMatcher.DEFAULT_FEATURE_WEIGHTS` (sum to 1.0 — analytical constants).
- Feature computation determinism (`features.compute_features` — feeds similarity hashing).
- `MarketMemoryEngine` audit-entry-per-action invariant.
- confirm()/resolve() lifecycle state machines in `objects/market_memory.py`.
