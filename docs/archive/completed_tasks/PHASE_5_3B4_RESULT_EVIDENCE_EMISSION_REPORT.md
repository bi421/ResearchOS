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

# Phase 5.3b.4 — ExperimentResult Evidence Emission

**Status:** COMPLETE
**Scope:** Connect the existing `ExperimentResult` contract to the `EvidenceRepository`
by emitting Result evidence artifacts (scheme-2 hashes).
**Architecture base:** Phase 5.3a evidence & lineage foundation +
Phase 5.3b.1 Dataset evidence + Phase 5.3b.2 Experiment evidence +
Phase 5.3b.3 Run evidence.

---

## 1. Summary

Implemented Result evidence emission only: a Result artifact builder that
projects the existing `ExperimentResult` contract into a scheme-2
`EvidenceEnvelope` (artifact type `"Result"`) and persists it to the
append-only `EvidenceRepository`, including Run → Result lineage wiring
(relation `"produces"`).

Strictly **additive and compatibility-preserving**:
- Preserves existing `ExperimentResult` behavior (no mutation of the source result).
- Does NOT emit Validation or Model.
- No execution changes.
- No model registry.

---

## 2. Files Changed

| File | Reason |
|------|--------|
| `researchos/evidence/result_emission.py` | **New** — Result artifact builder (`result_payload`, `build_result_envelope`, `attach_run_parent`, `emit_result`, `emit_result_for_run`). |
| `researchos/evidence/__init__.py` | **Updated** — exported the new Result emission API. |
| `researchos/tests/test_result_evidence_emission.py` | **New** — 29 deterministic tests. |
| `docs/PHASE_5_3B4_RESULT_EVIDENCE_EMISSION_REPORT.md` | **New** — this evidence report. |

---

## 3. Design

### 3.1 Result payload projection
`result_payload(result, run_hash, experiment_hash, backend_identity)` produces
a deterministic, primitives-only mapping capturing the result's CONTENT identity:

- `result_hash` — the result's deterministic content hash
- `run_id` — the owning run id
- `run_hash` — the run's deterministic hash (reference)
- `experiment_hash` — the experiment's deterministic reference hash
- `metrics` — the result's metric mapping
- `statistics` — the result's statistics mapping
- `performance` — the result's performance metadata (deterministic fields)
- `metadata` — the result's metadata mapping
- `trace`, `ontology_tags`
- `backend_identity` — optional backend identity metadata (name/version)

**Excluded** from the payload (identity): `backend_execution_time_ms`,
`backend_execution_timestamp`, and `created_at` (all runtime telemetry /
execution timing). The projection never mutates the source `ExperimentResult`.

### 3.2 Result envelope
`build_result_envelope(result, ...)` builds a scheme-2 `EvidenceEnvelope` with
`artifact_type="Result"`:

- `artifact_hash = hash(scheme, "Result", version, payload)` — binds type +
  version + payload, so:
  - identical results → identical `artifact_hash`,
  - a changed metric / statistic / metadata → different `artifact_hash`, and
  - telemetry NEVER affects the hash.
- `lineage_hash` — binds type + version + payload + sorted parents (order
  irrelevant; tampering fails verification).

### 3.3 Run → Result lineage
`attach_run_parent(envelope, run_hash)` returns a new Result envelope carrying
the run artifact hash as a parent. On append, `EvidenceRepository` writes a
`Run → Result` lineage edge (relation `"produces"`).
`emit_result_for_run` combines build + link + emit atomically.

### 3.4 Persistence
`emit_result(envelope, repository)` appends the envelope to an
`EvidenceRepository` (append-only). It rejects non-Result envelopes and
tampered envelopes (verify failure).

---

## 4. Tests Executed

| Command | Result |
|---------|--------|
| `pytest researchos/tests/test_result_evidence_emission.py -q` | **29 passed** |
| `pytest researchos/tests/test_result_evidence_emission.py researchos/tests/test_run_evidence_emission.py researchos/tests/test_experiment_evidence_emission.py researchos/tests/test_dataset_evidence_emission.py researchos/tests/test_evidence_repository.py -q` | **142 passed** |
| `pytest researchos/ -q` (full suite) | **2428 passed, 58 skipped, 2 failed** |
| `python -m ruff check researchos/evidence/ researchos/tests/test_result_evidence_emission.py` | **All checks passed** |

### Verification output (acceptance criteria)
- **identical result → identical artifact_hash** — ✅ `test_acceptance_identical_result_identical_hash`, `test_same_result_same_artifact_hash`
- **changed metric → different hash** — ✅ `test_acceptance_changed_metric_diff_hash`, `test_changed_metric_different_artifact_hash`
- **changed statistics → different hash** — ✅ `test_acceptance_changed_statistics_diff_hash`, `test_changed_statistics_different_artifact_hash`
- **telemetry does NOT affect hash** — ✅ `test_acceptance_telemetry_no_effect`, `test_telemetry_does_not_affect_hash`
- **Run -> Result lineage works** — ✅ `test_acceptance_run_to_result_lineage`, `test_lineage_edge_run_to_result`, `test_emit_result_for_run_links_lineage`
- **repository retrieval works** — ✅ `test_acceptance_repository_retrieval`, `test_emit_and_retrieve`

### Pre-existing failures (unrelated to this change)
The 2 failures are in `researchos/market_memory/` (untouched by this work):
1. `test_round_trip` — passes a non-existent `outcome_price_change` argument.
2. `test_doji_candle` — asserts a Doji (body=0.0) is `is_bullish`.

Identical failures existed before this change.

---

## 5. Acceptance Criteria

| Criterion | Status |
|-----------|--------|
| Result evidence artifacts created from existing ExperimentResult contract | ✅ |
| `artifact_type="Result"` | ✅ |
| Uses `HASH_SCHEME_VERSION = 2` | ✅ |
| Includes result_hash | ✅ |
| Includes run_id | ✅ |
| Includes run_hash reference | ✅ |
| Includes experiment reference | ✅ |
| Includes metrics | ✅ |
| Includes statistics | ✅ |
| Includes performance metadata (deterministic fields) | ✅ |
| Includes result metadata | ✅ |
| Includes backend identity metadata | ✅ |
| Excludes timestamps / runtime telemetry / execution timing from identity | ✅ |
| Run -> Result lineage (relation "produces") | ✅ |
| No Validation emission | ✅ |
| No Model Registry | ✅ |
| No execution changes | ✅ |
| Deterministic tests added | ✅ |
| Full ResearchOS suite stays green (no new regressions) | ✅ |

---

## 6. Constraints Honored

- ✅ **Determinism** — canonical scheme-2 hashes; telemetry/timing excluded.
- ✅ **Immutability** — frozen envelopes; append-only store.
- ✅ **Additive-only** — no existing module changed destructively.
- ✅ **No trading logic** — certification/trust layer only.

---

*Phase 5.3b.4 ExperimentResult Evidence Emission — Report*
*Classification: Internal — Implementation Evidence*
