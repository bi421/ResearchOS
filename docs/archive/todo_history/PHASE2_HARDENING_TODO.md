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

# Phase 2 — Institutional Hardening: Step Tracker

## P1 — Content-derived persistent identifiers
- [x] `regime/classification/classifier.py:225` — classification_id → content-derived hash
- [x] `regime/transition/detector.py:109` — transition_id → content-derived hash
- [x] `regime/transition/detector.py:168` — analysis_id → content-derived hash

## P2 — datetime.utcnow() → datetime.now(timezone.utc)
- [x] `macro_intelligence/contracts/event.py`
- [x] `macro_intelligence/contracts/evidence.py`
- [x] `macro_intelligence/contracts/knowledge.py`
- [x] `macro_intelligence/contracts/reaction.py`
- [x] `macro_intelligence/contracts/series.py`
- [x] `macro_intelligence/knowledge/models.py`
- [x] `macro_intelligence/regime/classification/classifier.py`
- [x] `macro_intelligence/regime/detection/detector.py`
- [x] `macro_intelligence/regime/transition/detector.py`
- [x] `macro_intelligence/regime/transition/models.py`
- [x] `macro_intelligence/relationships/models.py`
- [x] `researchos/intelligence/rag_contracts.py`
- [x] `researchos/intelligence/rag_retriever.py`

## P3 — Standardize provenance envelope
- [x] `statistics/provenance.py` — add `method_name` read-only alias property
- [ ] `regime/detection/models.py` — add `provenance` field
- [ ] `regime/classification/models.py` — add `provenance` field
- [ ] `regime/transition/models.py` — add `provenance` field
- [ ] `regime/detection/detector.py` — populate provenance
- [ ] `regime/classification/classifier.py` — populate provenance
- [ ] `regime/transition/detector.py` — populate provenance
- [ ] `relationships/engine.py` — verify consistency

## P4 — Performance cleanup
- [x] `regime/transition/detector.py` — O(n²) → O(n) in `_get_historical_avg_persistence`

## P5 — Architecture guards (CI)
- [x] Create `macro_intelligence/audit/guards.py`
- [x] Create `tests/unit/test_macro_intelligence/test_architecture_guards.py`

## P5.5 — Future-proof determinism guard
- [x] Include persistent-ID determinism check in guards.py

## Verification
- [x] Run MIL tests (516 → green)
- [x] Run V1 tests (1897 → green)
- [x] Run audit_mil.py — clean
- [x] Generate Phase 2 report
