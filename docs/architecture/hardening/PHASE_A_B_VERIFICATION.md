# PHASE A + B EXECUTION & VERIFICATION RECORD

**Date:** 2026-08-17 · **Branch:** master (working tree; nothing committed) · **Baseline:** `pre-cleanup-baseline` (6a1e428)

---

## Baseline (A0, recorded before any modification)

| Metric | Value |
|--------|-------|
| HEAD / tag | 6a1e428 / `pre-cleanup-baseline` |
| Python / C++ | 3.14.6 / C++20 · CMake 4.4.0 · MSVC 14.44 |
| Full suite | 3,475 passed / 58 skipped / 0 failed |
| Coverage | 86% (42,808 stmts / 6,122 miss) |
| Ruff | 0 errors |
| `pip install -e .` | OK |

## Phase A — Zero-Risk Hygiene (executed)

- **A1** `test-cpp.yml`: removed `ctest || echo` / `|| Write-Host` failure-masking on both Ubuntu and Windows jobs; Release now explicit (`-DCMAKE_BUILD_TYPE=Release` Ubuntu; `--config Release` Windows retained); removed `libboost-dev` (verified unused — zero Boost references outside vendored googletest comments in `build/`).
- **A2** `test-python.yml` + `pyproject.toml` testpaths: CI and local default now run all five roots (`researchos/tests`, `tests/unit`, `researchos/data_engine/tests`, `researchos/market_memory/tests`, `researchos/experiments/phase51/tests`).
- **A3** `coverage.yml` + test-python coverage step: `--cov=macro_intelligence` added (report-only; existing 70 gate unchanged, combined ≈86%).
- **A4** `docs/architecture/OWNERSHIP.md`: canonical concise ownership doc (evidence stages, repository taxonomy, market-memory layering, macro boundary, MacroEvent canonicality, quant-engine boundary).
- **A5** `researchos/macro/__init__.py`: added (explicit package; re-exports `MacroAnalysisEngine`, `ALL_DRIVERS`, `DRIVER_WEIGHTS`).

**Checkpoint A:** full suite via new testpaths → 3,475/58 identical; macro package smoke OK; ruff clean.

## Phase B — Safe Naming (executed; Rule 4 alias discipline)

- **B1** `intelligence.EvidenceRepository` → **`EvidenceGraphStore`**; old name = deprecated alias (module + package `__all__` + tests updated to canonical).
- **B2** `decision_engine.EvidenceItem` → **`DecisionEvidenceItem`**; `reasoning_engine.EvidenceItem` → **`ReasoningEvidence`**; both old names remain aliases (module + package exports). Schemas NOT merged — naming clarification only.
- **B3** `market_memory.MarketEvent` → **`MacroMarketEvent`**; `market_memory.MacroState` → **`MacroContextSnapshot`**; aliases kept. **Serialization pinned byte-identical:** legacy `object_type` strings ("MarketEvent"/"MacroState") and ID seeds unchanged (hazard found in pre-check: `BaseObject.to_dict` derives `object_type` from `__class__.__name__`); repository storage keys `"MacroState"` unchanged. New `researchos/tests/test_object_registry_disambiguation.py` (7 tests) pins the registry mapping and the wrong-class trap.

## Verification (after Phase B)

| Check | Baseline | After A+B | Verdict |
|-------|----------|-----------|---------|
| Full suite | 3,475 / 58 | **3,482 / 58** (+7 new registry tests) | ✅ no regression |
| Coverage | 86% (42,808/6,122) | **86% (42,849/6,123)** (+41 stmts: aliases/pins) | ✅ no material change |
| Ruff | 0 | **0** | ✅ |
| Import smoke | — | all canonical + alias names resolve | ✅ |
| `pip install -e .` | OK | **OK** | ✅ |
| Determinism tests | in suite | **passed** (test_determinism_closure, run-hash determinism) | ✅ |
| Serialization byte-identity | — | legacy assertions unchanged & passing (object_type pins) | ✅ |
| C++ | 526/526 | **not affected** (workflow YAML only; no source/CMake change) | ✅ n/a |
| Git diff | — | inspected: only the files listed above | ✅ |

## Not executed (per protocol)

Phases C (memory-consolidation), D (evidence-consolidation), E (macro-consolidation), F (cross-asset), G (event intelligence), H (dashboard) — all require explicit approval / dedicated branches / triggering milestones.
