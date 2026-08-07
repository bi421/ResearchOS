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

# Macro Intelligence Remediation — Step Tracker

## WS1 — Restore Statistics as single computation owner
- [x] Add canonical `normal_cdf`, `t_distribution_p_value`, `incomplete_beta`, `p_value_from_correlation` to `statistics/distributions.py`
- [x] Make `relationships/correlation.py::approximate_p_value` delegate; remove duplicate math (`_normal_cdf`, `_t_distribution_p_value`, `_incomplete_beta`); delegate stability std to canonical
- [x] Make `relationships/rolling.py::analyze_relationship_stability` delegate to `statistics.descriptive.std` + `statistics.regression.slope`
- [x] Make `relationships/lag_analysis.py::detect_reaction_delay` delegate to `statistics.descriptive.mean/std` + `statistics.zscore.zscore`
- [x] Export new canonical statistics symbols from `statistics/__init__.py`

## WS2 — Resolve 12 failing MIL tests
- [x] Fix `regime/enums.py` — align `EmploymentState` member reference (test intent)
- [x] Fix `features/__init__.py` — import `FeatureCalculationResult` from correct owner
- [x] Fix `audit/log.py` — give `AuditLog.created_at` a default factory + `AuditEntry.details` a default
- [x] Fix `provenance/chain.py` — `compute_hash()` excludes runtime `created_at` (deterministic)

## WS3 — Resolve reverse dependency violations
- [x] `revision/record.py` — remove eager `provenance.chain` import; use lazy importlib in `from_dict` (annotation already string-deferred)
- [x] `revision_provenance/__init__.py` — replace eager `audit.*` imports with lazy module-level `__getattr__` via importlib

## WS4 — Complete provenance
- [x] Create `statistics/provenance.py` — `StatisticalProvenance` (dataset_id/version/hash, computation_method, method_version, parameters)
- [x] Attach optional `provenance` field to relationship result models (CorrelationResult, RollingCorrelationResult, LagRelationship, RegimeRelationship, StructuralBreak, RelationshipResult)
- [x] Wire provenance builder through `relationships/engine.py` methods

## WS5 — Repository hygiene
- [x] Remove stray `$null` file
- [x] Add `audit_mil_data.json` to `.gitignore`

## Verification
- [x] Run `pytest tests/unit/test_macro_intelligence/` — green (507 passed)
- [x] Run `python audit_mil.py` — zero duplicate ownership, zero reverse deps, zero boundary violations
- [x] Generate `MACRO_INTELLIGENCE_REMEDIATION_REPORT.md`
