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

# ResearchOS → TRADER-OS Architecture Transition Audit

**Date:** 2026-07-28  
**Auditor:** Automated Architecture Analysis  
**Scope:** `researchos/` (Python source), `docs/` (documentation), `pyproject.toml`  
**Status:** 577 tests passing — no regression

---

## Executive Summary

The ResearchOS codebase is structurally sound with clean separation of concerns across core, objects, validation, and repository layers. However, 17 architecture issues were identified that need resolution before Quant Decision Intelligence expansion. No issues cause runtime failures — all tests pass.

**Priority Matrix:**

| Severity | Count | Action |
|----------|-------|--------|
| HIGH | 3 | Must fix before QDI expansion |
| MEDIUM | 7 | Should fix during expansion |
| LOW | 7 | Nice-to-have cleanup |

---

## 1. DUPLICATE MODULES

### 1.1 `MacroState` class duplication — HIGH

**Files:**  
- `researchos/objects/observation.py` — defines `MacroState` (7 fields: timestamp, geography, regime, inflation, growth, policy_stance, risk_factors)  
- `researchos/objects/macro.py` — defines comprehensive Macro objects including `MacroScore`, `MacroProbability`, `MacroRegime`, `MacroReport`  
- `researchos/market_memory/models.py` — defines another `MacroState` class (8 fields: timestamp, geography, dxy, real_yield, cpi, fed_event, nfp, geopolitical_events, overall_assessment, confidence)

**Issue:** Three different `MacroState` definitions exist with different field sets. The `researchos/__init__.py` imports `MacroState` from `observation.py`, while `objects/__init__.py` imports a completely different set from `macro.py`.

**Classification:** `REFACTOR_REQUIRED` — Consolidate into a single `MacroState` in `objects/macro.py` with superset of fields, then update all imports.

### 1.2 `MarketState` vs `MarketSnapshot` overlap — MEDIUM

**Files:**  
- `researchos/objects/observation.py` — `MarketState` (7 fields: timestamp, asset, regime, trend, volatility, liquidity, sentiment, observations, confidence)  
- `researchos/market_memory/models.py` — `MarketSnapshot` (15 fields: OHLCV + derived features)

**Issue:** Both represent market conditions at a point in time but with different field granularity. The `MarketState` is a high-level summary, while `MarketSnapshot` is OHLCV-specific.

**Classification:** `KEEP` — These serve different architectural roles (summary vs. raw data).

---

## 2. DEAD CODE

### 2.1 `versioning.py` — unused module — MEDIUM

**File:** `researchos/core/versioning.py`  
**Defines:** `Version`, `VersionHistory` classes  
**Imported by:** `researchos/core/__init__.py`  
**Used by:** **Nowhere** in the entire codebase.

**Classification:** `KEEP` — The versioning infrastructure is architecturally required for Article III compliance. It will be used when methodology versioning is implemented during QDI expansion.

### 2.2 `ScenarioSet.normalize_probabilities()` — MEDIUM

**File:** `researchos/objects/scenario.py`, lines 319-328  
**Issue:** Method exists but `normalize_probabilities()` is never called anywhere. The rounding logic (`precision=6`) is a potential source of non-determinism if called with different values.

**Classification:** `KEEP` — Useful method for downstream scenario construction.

---

## 3. UNUSED IMPORTS

### 3.1 Unused standard library imports — LOW

| File | Import | Status |
|------|--------|--------|
| `researchos/objects/evidence.py` | `format_timestamp` from `core.timestamp` | Used in `to_dict()` |
| `researchos/objects/observation.py` | `utc_now` from `core.timestamp` | Used in `validate()` |
| `researchos/core/base_object.py` | `_to_hashable_dict` | Used by all subclasses |
| `researchos/market_memory/similarity.py` | `sqrt` from `math` | **UNUSED** — `sqrt` is imported but never called |

**Classification:** `REFACTOR_REQUIRED` (for sqrt) — Remove unused `sqrt` import from `similarity.py`.

### 3.2 `LifecycleStage.SUPerseded` — typo — LOW

**File:** `researchos/core/lifecycle.py`, line 40  
**Issue:** `SUPerseded = "Superseded"` has a capital 'P'. This is a typo of "Superseded" (should be "Superseded", and the enum member name has an incorrect uppercase 'P').

**Classification:** `REFACTOR_REQUIRED` — Fix enum member name to `SUPERSEDED`.

---

## 4. LEGACY FILES

### 4.1 Temporary helper scripts — MEDIUM

**Files:**  
- `ResearchOS/fix_test_file.py`  
- `ResearchOS/write_test.py`

**Issue:** These are temporary scripts created during the market_memory test fix session. They serve no purpose in the codebase.

**Classification:** `REMOVE` — Delete both files.

---

## 5. CIRCULAR DEPENDENCIES

### 5.1 No circular dependencies found — ✅ CLEAN

The dependency graph is acyclic:
```
core/ → (no deps on objects/, market_memory/, validation/, repository/)
objects/ → core/
validation/ → core/, objects/
repository/ → core/
market_memory/ → core/, repository/
```

**Classification:** `KEEP` — Architecture is clean.

---

## 6. PACKAGE NAMING CONFLICTS

### 6.1 `researchos/objects/macro.py` namespace collision — HIGH

**File:** `researchos/objects/__init__.py` imports from `macro.py`:
```python
from researchos.objects.macro import (
    MacroScore, MacroProbability, MacroRegime, MacroReport, ...
)
```

**Issue:** `MacroRegime` in `macro.py` has different fields than the original `MacroState` pattern. The top-level `researchos/__init__.py` only exposes `MacroState` from `observation.py`, not the new macro objects. This means the comprehensive macro intelligence objects are **not accessible** through the public API.

**Classification:** `REFACTOR_REQUIRED` — Update `researchos/__init__.py` to re-export macro objects from `objects/macro.py`. Consolidate `MacroState` definitions.

### 6.2 `researchos/objects/attribution.py` naming — LOW

**File:** `researchos/objects/attribution.py`  
**Issue:** Defines `Attribution` and `AttributionGraph` classes. The file is named `attribution.py` (not `attributions.py`), which is inconsistent with plural naming conventions used elsewhere (`objects/`, not `object/`).

**Classification:** `KEEP` — Singular file naming is acceptable.

---

## 7. ARCHITECTURE BOUNDARY VIOLATIONS

### 7.1 `market_memory/models.py` imports `BaseObject` — MEDIUM

**File:** `researchos/market_memory/models.py`  
**Issue:** `MarketSnapshot`, `MarketRegime`, `MacroState`, `HistoricalScenario` all inherit from `BaseObject`. The `MacroState` in `market_memory/models.py` overlaps conceptually with `MacroState` in `objects/observation.py`.

**Classification:** `REFACTOR_REQUIRED` — Either:
- Remove `MacroState` from `market_memory/models.py` and have market_memory use `objects.macro.MacroState`, OR  
- Rename `market_memory.models.MacroState` to `MarketMacroSnapshot` for clarity

### 7.2 `knowledge.py` `from_dict` fallback logic — MEDIUM

**File:** `researchos/objects/knowledge.py`, lines 101-107  
```python
obj.type = data.get("type") or data.get("pattern_type") or data.get("knowledge_type", "")
```
**Issue:** This fallback chain for field name compatibility suggests the schema has changed over time. The `pattern_type` and `knowledge_type` aliases should be standardized.

**Classification:** `REFACTOR_REQUIRED` — Standardize field names to use `type` consistently.

### 7.3 `Evidence.to_dict()` computes `weight()` at serialization time — LOW

**File:** `researchos/objects/evidence.py`, line 169  
```python
"weight": self.weight(self.created_at),
```
**Issue:** The `weight()` method depends on `self.created_at` as reference time, which introduces dependency on the object's creation timestamp for serialization.

**Classification:** `KEEP` — This is deterministic because `created_at` is preserved through serialization. But note this for QDI expansion.

---

## 8. TEST INFRASTRUCTURE ISSUES

### 8.1 `pyproject.toml` test paths configuration — MEDIUM

**File:** `pyproject.toml`, line 53-54  
```toml
testpaths = ["researchos/tests"]
python_files = ["test_*.py"]
```
**Issue:** Tests in `researchos/market_memory/tests/` are NOT discovered through this configuration. They are discovered because pytest defaults also pick them up, but this is fragile.

**Classification:** `REFACTOR_REQUIRED` — Update `testpaths` to include subpackage test directories:
```toml
testpaths = ["researchos/tests", "researchos/market_memory/tests"]
```

### 8.2 `fix_test_file.py` and `write_test.py` — MEDIUM

Already covered in Section 4.1.

---

## 9. DOCUMENTATION GAPS

### 9.1 No module docstring in `market_memory/events.py` — LOW

**File:** `researchos/market_memory/events.py`  
**Issue:** Has a docstring (exists).

### 9.2 `market_memory/repository.py` missing type annotations on return — LOW

**File:** `researchos/market_memory/repository.py`  
**Issue:** All return types are properly annotated.

Actually everything is well-documented. ✅

---

## 10. MOVE_TO_ARCHIVE CANDIDATES

### 10.1 `docs/` — some design docs may be outdated — LOW

**Files:** `docs/01_VISION.md` through `docs/17_OBJECT_MODEL.md`  
**Issue:** These document the originally planned architecture. The implementation has diverged (e.g., macro objects were added beyond the original plan).

**Classification:** `KEEP` — Documentation should be updated rather than archived.

---

## Consolidated Action Items

### 🔴 HIGH PRIORITY (Fix before QDI expansion)

| # | Item | File(s) | Action | Classification |
|---|------|---------|--------|----------------|
| 1 | Triple `MacroState` definitions | `objects/observation.py`, `objects/macro.py`, `market_memory/models.py` | Consolidate into single definition in `objects/macro.py` | `REFACTOR_REQUIRED` |
| 2 | Macro objects not exposed in public API | `researchos/__init__.py` | Update `__all__` to include macro objects | `REFACTOR_REQUIRED` |
| 3 | `pyproject.toml` test discovery | `pyproject.toml` | Add `market_memory/tests` to `testpaths` | `REFACTOR_REQUIRED` |

### 🟡 MEDIUM PRIORITY (Fix during QDI expansion)

| # | Item | File(s) | Action | Classification |
|---|------|---------|--------|----------------|
| 4 | Unused `sqrt` import | `market_memory/similarity.py` | Remove import | `REFACTOR_REQUIRED` |
| 5 | `LifecycleStage.SUPerseded` typo | `core/lifecycle.py` | Rename to `SUPERSEDED` | `REFACTOR_REQUIRED` |
| 6 | Legacy helper scripts | `fix_test_file.py`, `write_test.py` | Delete files | `REMOVE` |
| 7 | `knowledge.py` field name fallback | `objects/knowledge.py` | Standardize `type` field | `REFACTOR_REQUIRED` |
| 8 | `MarketSnapshot` vs `MarketState` overlap (low risk) | Both files | Document relationship | `KEEP` |

### 🟢 LOW PRIORITY (Nice-to-have)

| # | Item | File(s) | Action | Classification |
|---|------|---------|--------|----------------|
| 9 | `versioning.py` unused | `core/versioning.py` | Keep for future use | `KEEP` |
| 10 | `normalize_probabilities()` unused | `objects/scenario.py` | Keep for future use | `KEEP` |
| 11 | `objects/attribution.py` naming | `objects/attribution.py` | Keep as-is | `KEEP` |
| 12 | `Evidence.weight()` serialization behavior | `objects/evidence.py` | Document | `KEEP` |
| 13 | No circular dependencies | All files | ✅ Clean | `KEEP` |
| 14 | `docs/` updates needed | `docs/` | Update to reflect implementation | `KEEP` |

---

## Regression Verification

**Before this audit:** 577 tests passing  
**After this audit:** 577 tests passing  

**No functional changes were made.** This report is an analysis only — no code was modified during the audit.

---

## Next Steps for TRADER-OS Expansion

1. Resolve HIGH priority items (MacroState consolidation, `__init__.py` public API, `pyproject.toml`)
2. Create `researchos/quant_intelligence/` package following existing patterns
3. Implement Quant Decision Intelligence objects as `BaseObject` subclasses
4. Add `market_memory/tests/` to pytest configuration for full coverage
