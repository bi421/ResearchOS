# Phase 7.2 — Evidence Aggregation Layer

## Files to CREATE:
- [ ] `researchos/decision_engine/evidence.py` — Canonical EvidenceItem (BaseObject), EvidenceSource, EvidenceCollection, EvidenceAggregator, EvidenceValidator
- [ ] `researchos/tests/test_evidence.py` — Comprehensive test suite

## Files to UPDATE:
- [ ] `researchos/decision_engine/contracts.py` — Re-export EvidenceItem and EvidenceSource from evidence.py
- [ ] `researchos/decision_engine/score.py` — Update enum refs: MACRO_INTELLIGENCE→MACRO, RESEARCH_OBJECTS→RESEARCH
- [ ] `researchos/decision_engine/reasoner.py` — Update enum refs: MACRO_INTELLIGENCE→MACRO, RESEARCH_OBJECTS→RESEARCH
- [ ] `researchos/decision_engine/__init__.py` — Add evidence class exports

## Validation:
- [ ] Run existing tests: `python -m pytest researchos/tests/test_decision_engine.py -v` (52 must pass)
- [ ] Run evidence tests: `python -m pytest researchos/tests/test_evidence.py -v` (all must pass)
