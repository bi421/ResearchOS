# REPOSITORY_OWNERSHIP_PROPOSAL.md

**Date:** 2026-08-17 — AUDIT ONLY. No implementation.

---

## CURRENT STATE — 7 repository implementations, classified by measured responsibility

| # | Class | Mechanism | Actual role (measured) | Runtime-wired? |
|---|-------|-----------|------------------------|----------------|
| 1 | `repository/memory.py::MemoryRepository` | dict | test/dev implementation **of** the canonical contract | Yes — composed by #7; injected in tests |
| 2 | `storage/repository.py::ResearchRepository` | SQLite (`researchos.db`), WAL, migrations, `OBJECT_REGISTRY` (~52 entity types), tamper-evident audit chain | **central persistence repository** (research ontology + cycles + audit) | **Yes — the only one**: `run_demo.py`, `agents/tools.py`, `interfaces/api.py`, `interfaces/cli.py` |
| 3 | `data_engine/repository.py::DatasetRepository` / `SqliteDatasetRepository` | dict / SQLite (`records_<id>` tables) | **market-data persistence repository** (bulk datasets + metadata) | No — package + own tests only |
| 4 | `pipeline_repository/repository.py::PipelineRepository` | dict + canonical JSON file, content-hash IDs | **pipeline state store** (immutable `PipelineReport` archive) | Only via `evaluation/engine.py` (itself test-wired) |
| 5 | `intelligence/repository.py::EvidenceRepository` | JSON file (single aggregate) | **graph repository** (persistence projection of in-memory `EvidenceGraph`) | No — own tests only |
| 6 | `evidence/repository.py::EvidenceRepository` | SQLite via facade **over** `ResearchRepository` (its `evidence`/`lineage` tables, migration v2→v3) | **evidence store** (append-only, content-addressed artifact ledger) | **No production emitter** — see PROBLEM #2 |
| 7 | `market_memory/repository.py::MarketMemoryRepository` | 4× composed `MemoryRepository` + optional own SQLite mirror table | **market-memory store** (snapshots/regimes/macro-states/scenarios) | No — tests only |

Contract: `repository/interface.py::RepositoryInterface` (6 methods: save/get/get_all/delete/find_by_tag/count, `T bound=BaseObject`). Verified runtime consumers of the *interface*: `pipeline/pipeline.py`, `engines/attribution.py`, `macro/engine.py`, `memory/engine.py`, `pipeline/references.py` + implementors #2, #3.

## PROBLEM

1. **Apparent proliferation — mostly justified.** Only #1/#2 share the load-bearing contract at runtime. #4–#7 deviate for defensible reasons (determinism, whole-graph persistence, append-only, multi-type facade). **A unified interface across all seven would be a useless abstraction** (append-only vs save/delete; whole-graph save/load vs single-object CRUD; datasets that are not ontology-tagged BaseObjects).
2. **The evidence store has no production emitter (verified).** `grep` proves zero imports of `researchos.evidence` from `experiments/`, `quant_engine/`, `orchestration/`, `pipeline/`. `evidence/__init__.py` states "No artifact emission hooks yet." The append-only ledger — the platform's reproducibility anchor — is 83–100% covered by tests that are its *only* writers.
3. **Two exported classes named `EvidenceRepository`** (`intelligence/` JSON graph vs `evidence/` SQLite ledger) — different contracts, same name in two `__all__`s.
4. **SQLite fragmentation (latent):** `researchos.db` (#2, hosts #6's tables), data_engine datasets DB (#3), market-memory mirror DB (#7), JSON files (#4, #5). Acceptable today (different lifecycles), but every new store invents its own persistence.

## EVIDENCE

- All classifications above are from file-level measurement (interfaces implemented, tables created, callers grepped) — see DEPENDENCY_GRAPH.md for method.
- #2 is the only repository constructed by any runtime entry point (verified in `run_demo.py:16-17`, `agents/tools.py:11-12`, `interfaces/api.py:7-8`, `interfaces/cli.py:16-17`).
- #6 dual-writes via a `_EnvelopeObject` shim into #2's object store (`evidence/repository.py:237-260`) — the intended convergence pattern already exists.

## TARGET STATE

**Keep seven roles; stop counting them as one problem.**

```
RepositoryInterface (contract, BaseObject-typed)
  ├─ ResearchRepository      central persistence + audit chain      [KEEP — production store]
  ├─ MemoryRepository        default in-memory impl                [KEEP]
DatasetRepository/Sqlite     market-data bulk store                [KEEP — domain-specific]
PipelineRepository           deterministic report archive          [KEEP — own contract by design]
intelligence.EvidenceRepository  graph projection (rename → EvidenceGraphStore)  [KEEP + RENAME]
evidence.EvidenceRepository  append-only artifact ledger           [KEEP + WIRE IT UP (R1)]
MarketMemoryRepository       market-memory store                   [KEEP — see MARKET_MEMORY_PROPOSAL.md]
```

Minimal hardening:

- **R1 — Wire ONE emission hook (REQUIRES REVIEW, scientific-integrity positive).** Make the experiment runner deposit Run/Result envelopes via the existing emission modules after each run. This is the single highest-value change in this document: it converts the evidence-first architecture from "tested in isolation" to "enforced in production." Must be additive-only (append after run; never alter experiment flow or hashes of existing outputs).
- **R2 — Rename `intelligence.EvidenceRepository` → `EvidenceGraphStore` (low risk, alias first).** Kills the second name collision of the audit.
- **R3 — Do NOT create a god-interface.** Document the taxonomy above in architecture docs as the official answer to "where does new state live?"

## MIGRATION RISK

| Step | Risk | Notes |
|------|------|-------|
| R2 rename | Low | Only intelligence package + 2 test files use it |
| R1 wiring | Medium | Touches experiment runtime; must be append-only and not change any existing hash/test expectation; new artifacts appear in stores used by tests that count rows |
| God-interface | — | NOT PROPOSED — would be a useless abstraction |

## REQUIRED TESTS (if R1/R2 proceed)

- Full suite (3,475), ruff, coverage ≥ 86%.
- R1: new integration test — run one phase51 experiment → assert Run/Result envelopes exist in a temp ledger with verifiable lineage; assert existing experiment outputs byte-identical.
- R2: alias smoke test; both names resolve during transition.

## DO NOT CHANGE

- `RepositoryInterface` method set (runtime load-bearing).
- `ResearchRepository` schema/migrations/audit-chain verification — tamper-evidence anchor.
- `PipelineRepository` determinism contract (content-hash IDs, canonical JSON).
- `evidence.EvidenceRepository` append-only semantics (no delete/update API — by design).
