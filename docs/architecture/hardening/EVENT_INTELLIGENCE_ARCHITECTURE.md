# EVENT_INTELLIGENCE_ARCHITECTURE.md

**Date:** 2026-08-17 — AUDIT ONLY. No implementation. No news engine is proposed now.

---

## CURRENT STATE

At least **four unlinked event models** exist:

| Model | Location | Strengths | Gaps |
|-------|----------|-----------|------|
| `MacroEvent` (frozen, me/v1) | `macro_intelligence/contracts/event.py` | **Strongest**: `event_type: EventCategory`, `importance`, `market_relevance.affected_instruments: list[str]` + quantified volatility/liquidity/correlation/historical-similarity impact, `full_text`, `source_urls`, deterministic `compute_hash()` excluding runtime metadata | `classification` is **free text**; affected *entities* only as `related_series` IDs — no country/institution/CB object |
| `MarketReaction` (mr/v1) | `macro_intelligence/contracts/reaction.py` | Keyed `(event_id, instrument)`; `window_before/after` specs; `ReactionMetrics` (return_bps, vol/volume/spread deltas, drawdown, spike, significance); `StatisticalSupport` (n, p-value, CI, effect size, method, limitations) — statistically honest | No event→reactions collection; **no aggregation by event class** ("historically, this class of event moved these assets like this" is inexpressible) |
| `MarketEvent` | `researchos/market_memory/events.py` | Simple, used by market-memory scenarios | Free-string `event_type`; **single `asset`** (no list); string impact; scalar actual/expected; single source string |
| `CalendarEvent` / `EconomicCalendarEvent` / `NewsEvent` | `macro_intelligence/time/timeline.py` / `quant_engine/fundamental/contracts.py` | Calendar integration | US/USD defaults; no reaction linkage |

Supporting: `KnowledgeObject` (ko/v1, series-scoped evidence patterns with `StatisticalAnalysis`).

### News → trading signal? **No path exists — by design and by guard.**
Verified: `metrics.py:5` and `performance.py:4` "RESEARCH METRICS ONLY — NOT trading signals"; `router.py:57-58` "makes no trading, signalling, or prediction decisions"; `phase51/cost.py:21-22` "Never makes a live-trading claim"; `macro_intelligence/audit/guards.py:22-26` **architecturally forbids MIL importing quant/experiment layers** — events cannot reach the computation layer directly. MIL "signals" (InflationSignal, GrowthSignal) are regime-state classifications, not orders. The nearest signal-adjacent text is positioning commentary in `researchos/macro/engine.py:873-874` — analytical, not executable.

## PROBLEM

Compared to the target chain `GLOBAL EVENT → CLASSIFICATION → AFFECTED ENTITIES → AFFECTED ASSETS → HISTORICAL REACTION → EVIDENCE → PROBABILISTIC CONTEXT`:

1. **Classification** — free text on the strongest model; two divergent `EventCategory` enums.
2. **Affected entities** — absent everywhere (no first-class country/institution objects shared across events).
3. **Affected assets** — inconsistent cardinality (list in MacroEvent, single string in MarketEvent); no instrument registry to bind against.
4. **Historical reaction** — well-formed primitives, no aggregation layer.
5. **Evidence chain** — patches exist (`source_urls`, `evidence_refs`, `StatisticalSupport`) but nothing connects event → reaction → evidence end-to-end.

## EVIDENCE

The primitives to build the target chain **already exist in `macro_intelligence/contracts/`** — the gap is topology (linking/aggregation) and the entity layer, not modeling from scratch. The decision layer is pre-declared as the consumer: `decision_engine.contracts.EvidenceSource.MACRO_INTELLIGENCE`.

## TARGET STATE (conceptual — build only when explicitly requested)

```
MacroEvent (canonical, classification → enum taxonomy)
   ├─ affected_entities (new: country/institution objects, shared, hashable)
   ├─ affected_instruments (bind via instrument registry — see CROSS_ASSET_READINESS T3)
   └─ MarketReaction[] aggregated by event classification
           → KnowledgeObject / decision_engine MACRO_INTELLIGENCE evidence
                     → probabilistic context  (NEVER direct signals)
```

- **E1 (SAFE NOW):** Document MacroEvent as the canonical event model; market_memory's `MarketEvent` gets renamed as part of M1 (MARKET_MEMORY_PROPOSAL.md) — this also resolves event-model fragmentation names.
- **E2 (cross-asset branch):** reaction-aggregation query ("reactions of class X on instruments Y over window W") as a read-only layer over stored MacroEvent/MarketReaction pairs — mirroring `LineageQueryEngine`'s read-only pattern.
- **E3 (event-intelligence phase, explicitly requested only):** entity layer + classification taxonomy consolidation.
- **Never:** news → BUY/SELL. The existing guard (`audit/guards.py`) plus decision-engine evidence flow is the correct topology; preserve it.

## MIGRATION RISK

| Step | Risk |
|------|------|
| E1 docs | None |
| E2 | Low-medium — read-only additive layer over frozen contracts |
| E3 | Medium — new domain objects; frozen-contract versioning (me/v2) required |

## REQUIRED TESTS

- E2: aggregation determinism tests (sorted output), StatisticalSupport propagation (never aggregate away the p-values/limitations — "never manufacture confidence").
- E3: entity identity determinism (same institution → same hash across events).

## DO NOT CHANGE

- `MacroEvent.compute_hash()` exclusion rules and `me/v1` contract.
- `MarketReaction`/`StatisticalSupport` semantics — these encode the "uncertainty remains explicit" principle.
- The MIL architectural guard forbidding event → computation-layer imports.
