# MACRO_OWNERSHIP_PROPOSAL.md

**Date:** 2026-08-17 — AUDIT ONLY. No implementation. HIGH-RISK DOMAIN — no merge proposed.

---

## CURRENT STATE

Two macro systems, **zero import connectivity** (AST-verified: 0 cross-package edges in 317 files).

### A. `researchos/macro/` — XAUUSD interpretation engine (LIVE)

- One file: `engine.py` (1,386 lines, no `__init__.py`, works via namespace packages). Coverage 86%.
- `MacroAnalysisEngine`: gold-specific 10-driver heuristic scoring (real yields, dollar strength, Fed policy, inflation, labor, growth, safe-haven, CB demand, physical demand, positioning).
- Regime labels (strings): Crisis, Risk_Off, Stagflation, Fed_Pivot, Inflation_Scare, Goldilocks, Risk_On, Range_Bound — via hardcoded `REGIME_SCORE_MAP` thresholds.
- Probability engine (directional) + report generation.
- Objects: `researchos/objects/macro.py` — 11 mutable `BaseObject` output types (62.8 KB).
- Wired into runtime via `researchos/engines/__init__.py` re-export. Only importers: `engines/__init__.py` + `researchos/tests/test_macro.py`.

### B. `macro_intelligence/` — generic macro domain library (TESTED, RUNTIME-DEAD)

- 90 files, 13 subpackages: contracts (frozen dataclasses, MIL invariant codes), econometrics (ADF/KPSS/Engle-Granger/Granger/VIF/Breusch-Pagan/DW/JB/AIC/BIC), statistics (13 modules), regime (detection with 6 specialized detectors → classification with taxonomy+rules → transition with probability matrices), relationships (correlation, lag, break detection, regime-conditional), time (calendar/normalizer/schedule/timeline), knowledge, features, revision, provenance, audit, storage, interfaces.
- Zero dependencies on `researchos.*`. Own test suite (`tests/unit/test_macro_intelligence/`, 15+ files). ~86% covered; `interfaces/` and `exceptions.py` at 0% (unwired).
- NOT in `pyproject.toml` packages — not installable, imports work only from repo root.

### Collisions

| Name | researchos side | macro_intelligence side |
|------|-----------------|-------------------------|
| `MacroRegime` | `objects.macro.MacroRegime` (mutable BaseObject) | `regime.contracts.MacroRegime` (frozen dataclass) AND `regime.classification.taxonomy.MacroRegime` (Enum, 6 values) |
| Inflation taxonomy | inline strings in engine.py (6 labels) | `contracts.enums.InflationRegime` (4), `regime.enums.InflationState` (6, incl. typo `DEFATION`) |
| Growth/Monetary/Employment/Risk | inline in engine.py | dedicated detectors + enums |

## PROBLEM

1. **Split-brain:** two regime classifiers, two object models, two audit paths — one heuristic and gold-specific (live), one scientific and generic (dead).
2. **Ownership ambiguity:** nobody can answer "where does a new macro capability go?" without archaeology.
3. **The live one is the unscientific one:** `researchos/macro` has no stationarity checks, no confidence intervals, no revision tracking — it cannot support the evidence-first pipeline the rest of the platform enforces.
4. **The scientific one has no consumer:** `macro_intelligence` emits frozen contracts nothing reads.

## EVIDENCE

- AST graph: 0 cross edges (DEPENDENCY_GRAPH.md §1).
- `researchos/macro/engine.py` imports only `researchos.objects.macro` + `researchos.core.*`.
- The only bridge stub in the repo: `researchos/market_memory/integration.py` (`macro_intelligence_adapter: Optional[Callable] = None`) — never wired.
- `decision_engine.contracts.EvidenceSource.MACRO_INTELLIGENCE = "MacroIntelligence"` — the decision layer already **expects** a macro-intelligence evidence producer that does not exist yet. This is the intended integration point, pre-declared in a frozen contract.

## TARGET STATE (conceptual — NOT permission to build)

Ownership decomposition answering the 7 required questions:

| Capability | Canonical owner | Notes |
|-----------|----------------|-------|
| Generic macro intelligence (series, events, regimes, econometrics, statistics, time) | `macro_intelligence` | Already owns all of it scientifically |
| XAUUSD-specific interpretation (10-driver gold scoring, gold report) | `researchos/macro` — **renamed conceptually to "XAUUSD macro interpretation"** | Stays live until parity is proven; gold drivers are asset knowledge, not generic macro |
| Cross-asset relationships (DXY↔XAUUSD, rates↔FX…) | `macro_intelligence/relationships/` + future context layer | `relationships/engine.py` already models regime-conditional relations |
| Regime classification (generic) | `macro_intelligence/regime/` | 3-layer detection→classification→transition |
| Economic events (calendar, releases, reactions) | `macro_intelligence/contracts/event.py`, `time/` | See EVENT_INTELLIGENCE_ARCHITECTURE.md |
| Statistical/econometric infrastructure | `macro_intelligence/econometrics|statistics` + `researchos/quant_engine` (numerical backends) | Non-overlapping today: MIL = macro series methods; quant_engine = market computation |
| Asset-specific feature extraction | asset context packages (future), NOT macro_intelligence | Keeps MIL asset-agnostic |

Target flow (matches task diagram):

```
macro_intelligence (generic) ──► cross-asset relations ──► asset context (XAUUSD interp = researchos/macro)
                                        │                        │
                                        ▼                        ▼
                            decision_engine (MACRO_INTELLIGENCE evidence source)
                                                                 │
                                                                 ▼  (as evidence, never as signals)
                                                    quant_engine → backtesting → evidence/
```

Migration shape (eventual, on `macro-consolidation` branch only):

1. **Adapter first:** `researchos/macro` emits decision evidence (it likely already feeds `EvidenceSource.RESEARCH_OBJECTS`); add an adapter that maps `macro_intelligence` regime contracts → decision evidence under `MACRO_INTELLIGENCE`. No deletion.
2. **Own the name:** `researchos/macro` docstring/package doc repositions it as XAUUSD interpretation; generic regime code is never added there again.
3. **Parity experiment:** run `macro_intelligence` regime detection on the same inputs the heuristic engine uses; compare stability/confidence. Evidence-first: the migration decision itself must be an experiment with artifacts in the evidence store.
4. Only after parity evidence: retire the heuristic regime classification (keep gold-driver scoring — it is asset knowledge).

## MIGRATION RISK

**HIGH.** Reasons: incompatible object models (mutable BaseObject vs frozen dataclass); three `MacroRegime` types; differing taxonomies with no mapping table; the live engine feeds tested probability/report paths. A botched merge silently changes regime labels → decision evidence → probabilities.

Mitigations: dedicated branch; adapter-only first step; mapping table (`researchos` label ↔ MIL enum) shipped as data with tests; baseline comparison of decision-engine outputs before/after; STOP if any decision-engine test output changes unexplained.

## REQUIRED TESTS (when migration starts)

- All 3,475 Python tests + 526 C++ tests green; coverage ≥ 86%.
- New: regime mapping table round-trip tests.
- New: adapter emits `EvidenceSource.MACRO_INTELLIGENCE` items that pass `decision_engine` EvidenceCollection validation.
- Baseline diff: `test_decision_engine*`, `test_macro` outputs byte-identical before the switchover commit.

## DO NOT CHANGE

- `researchos/macro/engine.py` scoring thresholds/driver weights — they encode current XAUUSD research assumptions; changes are scientific changes requiring approval.
- Any `macro_intelligence` frozen contract (version-tagged "v1", "architectural_frozen"; MIL invariant tests enforce this).
- `decision_engine.EvidenceSource` enum values — decision contracts are versioned (`DECISION_V1`).
- Do NOT merge storage: `macro_intelligence/storage` is an abstract skeleton; `researchos/storage` is the SQLite production store. Different layers.
