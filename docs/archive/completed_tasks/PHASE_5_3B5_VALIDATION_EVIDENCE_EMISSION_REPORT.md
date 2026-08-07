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

# Phase 5.3b.5 — Validation Evidence Emission

**Status:** COMPLETE
**Scope:** Connect the existing `ValidationResult` contract to the `EvidenceRepository`
by emitting Validation evidence artifacts (scheme-2 hashes).
**Architecture base:** Phase 5.3a evidence & lineage foundation +
Phase 5.3b.1 Dataset evidence + Phase 5.3b.2 Experiment evidence +
Phase 5.3b.3 Run evidence + Phase 5.3b.4 Result evidence.

---

## 1. Summary

Implemented Validation evidence emission only: a Validation artifact builder that
projects the existing `ValidationResult` contract (walk-forward validation) into a
scheme-2 `EvidenceEnvelope` (artifact type `"Validation"`) and persists it to the
append-only `EvidenceRepository`, including Result → Validation lineage wiring
(relation `"validates"`).

Strictly **additive and compatibility-preserving**:
- Preserves existing `ValidationResult` behavior (no mutation of the source).
- Does NOT emit Model.
- No execution changes.
- No model registry.

---

## 2. Files Changed

| File | Reason |
|------|--------|
| `researchos/evidence/validation_emission.py` | **New** — Validation artifact builder (`validation_payload`, `build_validation_envelope`, `attach_result_parent`, `emit_validation`, `emit_validation_for_result`). |
| `researchos/evidence/__init__.py` | **Updated** — exported the new Validation emission API. |
| `researchos/tests/test_validation_evidence_emission.py` | **New** — 35 deterministic tests (incl. the 9 required). |
| `docs/PHASE_5_3B5_VALIDATION_EVIDENCE_EMISSION_REPORT.md` | **New** — this evidence report. |

---

## 3. Architecture

### 3.1 Validation payload projection
`validation_payload(validation, result_hash, run_hash, experiment_hash, method, evaluation_config)`
produces a deterministic, primitives-only mapping capturing the validation's
CONTENT identity:

- `validation_hash` — deterministic content hash derived from `ValidationResult.to_dict()`
- `method` — the validation method name (e.g. `"walk_forward"`)
- `version` — the validation scheme version
- `result_hash` — the linked result's deterministic reference hash
- `run_hash` — the linked run's deterministic reference hash (when available)
- `experiment_hash` — the linked experiment's deterministic reference hash
- `metrics` — the validation's aggregate metric mapping
- `statistics` — projected per-fold statistics (fold_count + folds)
- `parameters` — validation parameters (train_size, validation_size, test_size, fold_count)
- `metadata` — the validation's metadata mapping
- `evaluation_config` — optional evaluation configuration (when supplied)

**Excluded** from the payload (identity): timestamps, runtime telemetry, and
execution duration. The projection never mutates the source `ValidationResult`.

### 3.2 Validation envelope
`build_validation_envelope(validation, ...)` builds a scheme-2 `EvidenceEnvelope`
with `artifact_type="Validation"`:

- `artifact_hash = hash(scheme, "Validation", version, payload)` — binds type +
  version + payload, so:
  - identical validations → identical `artifact_hash`,
  - a changed metric / configuration / parameter → different `artifact_hash`, and
  - timestamps / telemetry NEVER affect the hash.
- `lineage_hash` — binds type + version + payload + sorted parents (order
  irrelevant; tampering fails verification).

### 3.3 Result → Validation lineage
`attach_result_parent(envelope, result_hash)` returns a new Validation envelope
carrying the result artifact hash as a parent. On append, `EvidenceRepository`
writes a Result → Validation lineage edge (relation `"validates"`).
`emit_validation_for_result` combines build + link + emit atomically.

### 3.4 Persistence
`emit_validation(envelope, repository)` appends the envelope to an
`EvidenceRepository` (append-only). It rejects non-Validation envelopes, tampered
envelopes (verify failure), and invalid payloads (strict primitive validation).

---

## 4. Tests Executed

| Command | Result |
|---------|--------|
| `pytest researchos/tests/test_validation_evidence_emission.py -q` | **35 passed** |
| `pytest researchos/tests/test_evidence_repository.py researchos/tests/test_dataset_evidence_emission.py researchos/tests/test_experiment_evidence_emission.py researchos/tests/test_run_evidence_emission.py researchos/tests/test_result_evidence_emission.py researchos/tests/test_validation_evidence_emission.py -q` | **177 passed** |
| `pytest researchos/ -q` (full suite) | see section 5 |
| `python -m ruff check researchos/evidence/ researchos/tests/test_validation_evidence_emission.py` | **All checks passed** |

### Verification output (required tests)
- **identical validation → identical artifact_hash** — TEST_1 `test_same_validation_same_artifact_hash` / `test_acceptance_identical_validation_identical_hash`
- **changed validation metric changes hash** — TEST_2 `test_changed_metric_different_artifact_hash` / `test_acceptance_changed_metric_diff_hash`
- **changed validation configuration changes hash** — TEST_3 `test_changed_configuration_different_artifact_hash` / `test_acceptance_changed_config_diff_hash`
- **timestamps do not affect hash** — TEST_4 `test_timestamps_do_not_affect_hash` / `test_acceptance_timestamps_no_effect`
- **Result → Validation lineage edge exists** — TEST_5 `test_lineage_edge_result_to_validation` / `test_acceptance_result_to_validation_lineage`
- **repository retrieval works** — TEST_6 `test_emit_and_retrieve` / `test_acceptance_repository_retrieval`
- **tampered envelope rejected** — TEST_7 `test_emit_rejects_tampered_envelope` / `test_acceptance_tampered_rejected`
- **payload remains primitive-only** — TEST_8 `test_payload_is_primitives_only` / `test_acceptance_payload_primitive_only`
- **HASH_SCHEME_VERSION == 2** — TEST_9 `test_scheme_version_is_2` / `test_acceptance_scheme_version_2`

---

## 5. Acceptance Criteria

| Criterion | Status |
|-----------|--------|
| Validation evidence artifacts created from existing ValidationResult contract | ✅ |
| `artifact_type="Validation"` | ✅ |
| Uses `HASH_SCHEME_VERSION = 2` | ✅ |
| Includes validation identity/hash | ✅ |
| Includes method/version | ✅ |
| Includes linked result_hash | ✅ |
| Includes linked run_hash when available | ✅ |
| Includes metrics | ✅ |
| Includes statistics | ✅ |
| Includes validation parameters | ✅ |
| Includes evaluation configuration | ✅ |
| Excludes timestamps / runtime telemetry / execution duration | ✅ |
| Result → Validation lineage (relation "validates") | ✅ |
| No Model emission | ✅ |
| No execution changes | ✅ |
| Deterministic tests added | ✅ |
| Full ResearchOS suite stays green (no new regressions) | ✅ |

---

## 6. Compatibility Notes

- No existing `EvidenceEnvelope` / `EvidenceRepository` contract was modified.
- `HASH_SCHEME_VERSION` remains `"2"`.
- No existing validation contract was modified.
- Changes are strictly additive; existing callers unchanged.
- Pylance "could not be resolved" import warnings in the editor are pre-existing
  package-resolution environment issues (package not on Pylance interpreter path),
  not runtime errors.

---

*Phase 5.3b.5 Validation Evidence Emission — Report*
*Classification: Internal — Implementation Evidence*
</content>
