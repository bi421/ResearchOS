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

# Phase 5.3a — Evidence & Lineage Storage Foundation (Hash-Contract Hardened)

**Status:** COMPLETE
**Scope:** Additive evidence repository + lineage graph foundation for the
ResearchOS scientific record (Phase 5.3a of `docs/PHASE5_ARCHITECTURE_PLAN.md`),
plus the hash-contract hardening pass addressing the audit findings.

**Architecture base:** Phase 5.2 determinism closure (immutable experiment
artifacts, deterministic run hashes).

---

## 1. Summary

Implemented the append-only, content-addressed evidence repository and lineage
graph foundation on top of the existing `ResearchRepository`, then hardened the
hash contract in response to the Phase 5.3a audit.

Design is strictly **additive and compatibility-preserving**:
- No frozen interface modified.
- No existing experiment flow altered.
- No artifact emission hooks added yet.
- No Model Registry implementation yet.
- No replay execution.

---

## 2. Files Changed

| File | Reason |
|------|--------|
| `researchos/evidence/envelope.py` | **New / hardened** — `EvidenceEnvelope` immutable artifact envelope; hardened `artifact_hash` / `lineage_hash`; strict payload validation; `HASH_SCHEME_VERSION` marker; `legacy_verify()`. |
| `researchos/evidence/repository.py` | **New / hardened** — `EvidenceRepository` append-only facade; `verify_evidence()` updated to the hardened lineage scheme. |
| `researchos/evidence/__init__.py` | Public exports (added `HASH_SCHEME_VERSION`, `compute_artifact_hash`). |
| `researchos/storage/repository.py` | **Schema migration** `SCHEMA_VERSION` 2 → 3; creates `evidence` + `lineage` tables (unchanged from the foundation). |
| `researchos/tests/test_evidence_repository.py` | **New / expanded** — 37 deterministic tests: envelope, repository, migration, and hardening regressions. |

---

## 3. Hash Contract Hardening (Audit Fixes)

### 3.1 artifact_hash identity (Finding #1)
**Before:** `hash({payload, version})` — a Dataset and a Feature with identical
payload collided on the same `artifact_hash` (the SQLite PK).

**After:** `hash({scheme, artifact_type, version, payload})`.

Requirement met (verified by test):
- Dataset and Feature with identical payload → **different** `artifact_hash`.
- Deterministic behavior preserved.

### 3.2 lineage_hash integrity (Finding #2)
**Before:** `hash({payload, sorted parents})` — version/type tampering passed
`verify()`.

**After:** `hash({scheme, artifact_type, version, payload, sorted parents})`.

Requirements met (verified by tests):
- Parent order remains irrelevant (sorted edge set).
- Version/type tampering **fails** verification.

### 3.3 Payload contract (Finding #3)
**Before:** `deterministic_hash` used `json.dumps(..., default=str)`, which
coerced unsupported objects via `str()` — a determinism ambiguity.

**After:** Strict `_validate_payload()` rejects any value that is not a
deterministic JSON-compatible primitive:

```
dict | list | str | int | float | bool | None
```

- Non-string dict keys rejected.
- Nested unsupported objects rejected.
- Primitive-only serialization (no `default=str`).

### 3.4 Hash versioning (Finding #4)
Introduced `HASH_SCHEME_VERSION = "2"` embedded in the canonical envelope.
`verify()` uses the scheme-2 lineage hash. `legacy_verify()` recomputes the
pre-hardening scheme-1 hash so records created before the hardening remain
verifiable (backward compatibility).

---

## 4. Migration Impact

- **No destructive migration.** `SCHEMA_VERSION` remained at `3`; the
  `evidence`/`lineage` tables are unchanged (columns are the same).
- **Hash values change** for newly built envelopes (scheme-2). Any record
  persisted before hardening carries a scheme-1 `lineage_hash`; such records
  fail `verify()` but pass `legacy_verify()`.
- **Re-append semantics:** re-appending an identical content hash remains a
  no-op; distinct artifact types no longer collide (the hardening fix).

---

## 5. Backward Compatibility

- `verify()` returns `True` for an empty `lineage_hash` (legacy/unsigned).
- `legacy_verify()` accepts pre-hardening scheme-1 hashes.
- `build_envelope()` public signature is unchanged.
- No existing callers of the evidence module were altered (it is additive);
  the experiments/storage layers are untouched.

---

## 6. Changed Contracts

| Contract | Before | After |
|----------|--------|-------|
| `compute_lineage_hash(payload, parents)` | (payload, parents) | `(artifact_type, version, payload, parents)` |
| `compute_artifact_hash` | — (implicit in build) | **new** public: `(artifact_type, version, payload)` |
| `EvidenceEnvelope.verify()` | payload+parents only | type+version+payload+parents (scheme-2) |
| `EvidenceEnvelope.legacy_verify()` | — | **new** scheme-1 backward-compat check |
| `build_envelope(payload)` | accepted any object (via `default=str`) | **rejects** non-primitive payloads (`TypeError`) |
| `HASH_SCHEME_VERSION` | — | **new** marker `"2"` |

---

## 7. Tests Executed

| Command | Result |
|---------|--------|
| `pytest researchos/tests/test_evidence_repository.py -q` | **37 passed** |
| `pytest researchos/ -q` (full suite) | **2323 passed, 58 skipped, 2 failed** |
| `ruff check researchos/evidence/ researchos/tests/test_evidence_repository.py` | **All checks passed** |

### New hardening tests added
- `test_same_payload_different_type_differs` — same payload, different
  `artifact_type` → different `artifact_hash` and `lineage_hash`.
- `test_version_change_affects_lineage` — version change alters lineage hash.
- `test_verify_detects_tampered_version` / `test_verify_detects_tampered_type`
  — tampering fails verification.
- `test_legacy_verify_accepts_pre_hardening_scheme` — scheme-1 records still
  verifiable via `legacy_verify()`.
- `TestPayloadContract` — unsupported payload objects rejected; primitives
  accepted; non-string dict keys rejected.
- `test_append_distinct_types_no_collision` — Dataset + Feature both stored.

### 7.1 Pre-existing failures (unrelated to this change)
The 2 failures are in `researchos/market_memory/` (untouched by this work):

1. `TestHistoricalScenarioSerialization::test_round_trip` — calls
   `HistoricalScenario(..., outcome_price_change=...)`, which is not a
   constructor parameter of the current `HistoricalScenario`.
2. `TestFeatureComputation::test_doji_candle` — a Doji candle (body = 0.0) is
   asserted `is_bullish is True`, but the feature classifier returns `False`.

Neither module was modified by this change (identical failures existed before).

---

## 8. Acceptance Criteria

| Criterion | Status |
|-----------|--------|
| Dataset/Feature with identical payload produce distinct `artifact_hash` | ✅ |
| Version/type tampering fails lineage verification | ✅ |
| Parent order remains irrelevant | ✅ |
| Unsupported payload types rejected | ✅ |
| Hash algorithm/version marker introduced | ✅ |
| Backward compatibility preserved (legacy verify) | ✅ |
| Append-only: no update/delete of existing records | ✅ |
| No modification of frozen compute interfaces | ✅ |
| No artifact emission hooks / Model Registry / replay added | ✅ |
| Full ResearchOS suite stays green (no new regressions) | ✅ |

---

## 9. Constraints Honored

- ✅ **Determinism** — all hashes canonical SHA-256 over sorted primitive-only
  serializations; time excluded; no `default=str` ambiguity.
- ✅ **Immutability** — envelopes are frozen dataclasses; append-only store.
- ✅ **Additive-only** — schema migration preserves prior tables.
- ✅ **No trading logic** — this is a certification/trust layer only.

---

## 10. Next Steps (Out of Scope)

- Artifact emission hooks from the experiment runner.
- Deterministic Model Registry (WP-5).
- Lineage graph traversal/query API beyond parent/child.
- Replay execution.

*Phase 5.3a Evidence & Lineage Storage Foundation — Report (hardened)*
*Classification: Internal — Implementation Evidence*
