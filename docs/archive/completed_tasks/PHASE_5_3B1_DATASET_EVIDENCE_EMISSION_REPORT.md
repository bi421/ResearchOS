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

# Phase 5.3b.1 — Dataset Evidence Emission

**Status:** COMPLETE
**Scope:** Connect the existing `ResearchDataset` contract to the
`EvidenceRepository` by emitting Dataset evidence artifacts (scheme-2 hashes).
**Architecture base:** Phase 5.3a evidence & lineage foundation (hash-contract
hardened).

---

## 1. Summary

Implemented Dataset evidence emission only: a dataset artifact builder that
projects the frozen `ResearchDataset` contract into a scheme-2
`EvidenceEnvelope` (artifact type `"Dataset"`) and persists it to the
append-only `EvidenceRepository`.

Strictly **additive and compatibility-preserving**:
- Existing dataset behavior preserved (no mutation of the dataset contract).
- No Experiment / Run / Result emission yet.
- No model registry.
- No execution changes.

---

## 2. Files Changed

| File | Reason |
|------|--------|
| `researchos/evidence/dataset_emission.py` | **New** — dataset artifact builder (`build_dataset_envelope`, `emit_dataset`, `research_dataset_payload`, `make_dataset_envelope_from_payload`). |
| `researchos/evidence/__init__.py` | **Updated** — exported the new dataset emission API. |
| `researchos/tests/test_dataset_evidence_emission.py` | **New** — 22 deterministic tests for payload projection, envelope identity, persistence, lineage, and acceptance criteria. |
| `docs/PHASE_5_3B1_DATASET_EVIDENCE_EMISSION_REPORT.md` | **New** — this evidence report. |

---

## 3. Design

### 3.1 Dataset payload projection
`research_dataset_payload(dataset)` produces a deterministic, primitives-only
mapping from the frozen `ResearchDataset` attributes:

- `feature_names`, `features`, `labels`
- `metadata` (recursively flattened to primitives)
- `sample_count`, `feature_count`, `label_name`, `version`

`created_at` is **excluded** (observational telemetry, never hashed). The
projection does not mutate the source dataset.

### 3.2 Dataset envelope
`build_dataset_envelope(dataset, ...)` builds a scheme-2 `EvidenceEnvelope`
with `artifact_type="Dataset"`:

- `artifact_hash = hash(scheme, "Dataset", version, payload)` — binds type +
  version + payload, so:
  - same dataset → same `artifact_hash`, and
  - changed dataset → different `artifact_hash`.
- `lineage_hash = hash(scheme, "Dataset", version, payload, sorted parents)` —
  parent order irrelevant; version/type tampering fails verification.

### 3.3 Lineage metadata support
`parent_hashes` (input artifact hashes, when available) are carried on the
envelope and recorded as lineage edges by the repository on append.

### 3.4 Persistence
`emit_dataset(envelope, repository)` appends the envelope to an
`EvidenceRepository` (append-only, deduplicating). It rejects non-Dataset
envelopes and tampered envelopes (verify failure).

---

## 4. Tests Executed

| Command | Result |
|---------|--------|
| `pytest researchos/tests/test_dataset_evidence_emission.py -q` | **22 passed** |
| `pytest researchos/tests/test_dataset_evidence_emission.py researchos/tests/test_evidence_repository.py -q` | **59 passed** |
| `pytest researchos/ -q` (full suite) | **2345 passed, 58 skipped, 2 failed** |
| `ruff check researchos/evidence/ researchos/tests/test_dataset_evidence_emission.py researchos/tests/test_evidence_repository.py` | **All checks passed** |

### Verification output (acceptance criteria)
- **same dataset → same artifact_hash** — ✅ `test_same_dataset_same_artifact_hash`
- **changed dataset → different artifact_hash** — ✅ `test_changed_dataset_different_artifact_hash`, `test_changed_metadata_different_artifact_hash`
- **artifact retrievable from EvidenceRepository** — ✅ `test_emit_and_retrieve`, `test_acceptance_retrievable_from_repo`
- **existing tests remain stable** — ✅ full suite green (no new regressions)

### Pre-existing failures (unrelated to this change)
The 2 failures are in `researchos/market_memory/` (untouched by this work):
1. `test_round_trip` — passes a non-existent `outcome_price_change` argument.
2. `test_doji_candle` — asserts a Doji (body=0.0) is `is_bullish`.

Identical failures existed before this change.

---

## 5. Acceptance Criteria

| Criterion | Status |
|-----------|--------|
| Dataset evidence artifacts created from existing dataset contracts | ✅ |
| Uses `HASH_SCHEME_VERSION = 2` | ✅ |
| Existing dataset behavior preserved | ✅ |
| No Experiment/Run/Result emission | ✅ |
| No model registry | ✅ |
| No execution changes | ✅ |
| Dataset artifact builder added | ✅ |
| Lineage metadata support (parent hashes) | ✅ |
| Deterministic tests added | ✅ |
| Full ResearchOS suite stays green (no new regressions) | ✅ |

---

## 6. Constraints Honored

- ✅ **Determinism** — canonical scheme-2 hashes; time excluded.
- ✅ **Immutability** — frozen envelopes; append-only store.
- ✅ **Additive-only** — no existing module modified destructively.
- ✅ **No trading logic** — certification/trust layer only.

---

*Phase 5.3b.1 Dataset Evidence Emission — Report*
*Classification: Internal — Implementation Evidence*
