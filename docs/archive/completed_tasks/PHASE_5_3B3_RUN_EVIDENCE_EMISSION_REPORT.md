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

# Phase 5.3b.3 — ExperimentRun Evidence Emission

**Status:** COMPLETE
**Scope:** Connect the existing `ExperimentRun` contract to the `EvidenceRepository`
by emitting Run evidence artifacts (scheme-2 hashes).
**Architecture base:** Phase 5.3a evidence & lineage foundation +
Phase 5.3b.1 Dataset evidence + Phase 5.3b.2 Experiment evidence.

---

## 1. Summary

Implemented Run evidence emission only: a Run artifact builder that projects
the existing `ExperimentRun` contract into a scheme-2 `EvidenceEnvelope`
(artifact type `"Run"`) and persists it to the append-only
`EvidenceRepository`, including Experiment → Run lineage wiring (relation
`"executes"`).

Strictly **additive and compatibility-preserving**:
- Preserves existing `ExperimentRun` behavior (no mutation of the source run).
- Does NOT emit Result, Validation, or Model yet.
- No execution changes.
- No model registry.

---

## 2. Files Changed

| File | Reason |
|------|--------|
| `researchos/evidence/run_emission.py` | **New** — Run artifact builder (`run_payload`, `build_run_envelope`, `attach_experiment_parent`, `emit_run`, `emit_run_for_experiment`). |
| `researchos/evidence/__init__.py` | **Updated** — exported the new Run emission API. |
| `researchos/tests/test_run_evidence_emission.py` | **New** — 28 deterministic tests. |
| `docs/PHASE_5_3B3_RUN_EVIDENCE_EMISSION_REPORT.md` | **New** — this evidence report. |

---

## 3. Design

### 3.1 Run payload projection
`run_payload(run, experiment_hash, backend_identity)` produces a deterministic,
primitives-only mapping capturing the run's LOGICAL identity:

- `run_hash` — the run's deterministic identity
- `experiment_id` — the owning experiment id
- `experiment_hash` — the experiment's deterministic reference hash
- `run_number`
- `dataset_config` — snapshot via `to_dict()`
- `simulation_config` — snapshot via `to_dict()`
- `parameters` — snapshot
- `status`, `trace`, `tags`, `ontology_tags`
- `backend_identity` — optional backend identity metadata (name/version)

**Excluded** from the payload (identity): `started_at`, `completed_at`,
`duration_seconds`, and `created_at` (all wall-clock / runtime telemetry).
The projection never mutates the source `ExperimentRun`.

### 3.2 Run envelope
`build_run_envelope(run, ...)` builds a scheme-2 `EvidenceEnvelope` with
`artifact_type="Run"`:

- `artifact_hash = hash(scheme, "Run", version, payload)` — binds type +
  version + payload, so:
  - identical runs → identical `artifact_hash`, and
  - changed logical input (params / dataset / simulation / experiment hash) →
    different `artifact_hash`, and
  - runtime timing NEVER affects the hash.
- `lineage_hash` — binds type + version + payload + sorted parents (order
  irrelevant; tampering fails verification).

### 3.3 Experiment → Run lineage
`attach_experiment_parent(envelope, experiment_hash)` returns a new Run
envelope carrying the experiment artifact hash as a parent. On append,
`EvidenceRepository` writes an `Experiment → Run` lineage edge (relation
`"executes"`). `emit_run_for_experiment` combines build + link + emit
atomically.

### 3.4 Persistence
`emit_run(envelope, repository)` appends the envelope to an
`EvidenceRepository` (append-only). It rejects non-Run envelopes and tampered
envelopes (verify failure).

---

## 4. Tests Executed

| Command | Result |
|---------|--------|
| `pytest researchos/tests/test_run_evidence_emission.py -q` | **28 passed** |
| `pytest researchos/tests/test_run_evidence_emission.py researchos/tests/test_experiment_evidence_emission.py researchos/tests/test_dataset_evidence_emission.py researchos/tests/test_evidence_repository.py -q` | **113 passed** |
| `pytest researchos/ -q` (full suite) | **2399 passed, 58 skipped, 2 failed** |
| `python -m ruff check researchos/evidence/ researchos/tests/test_run_evidence_emission.py` | **All checks passed** |

### Verification output (acceptance criteria)
- **identical runs → identical artifact_hash** — ✅ `test_acceptance_identical_runs_identical_hash`, `test_same_run_same_artifact_hash`
- **changed logical input → different artifact_hash** — ✅ `test_acceptance_changed_logical_input_diff_hash`, `test_changed_params_different_artifact_hash`, `test_changed_dataset_config_different_artifact_hash`, `test_changed_experiment_hash_different_artifact_hash`
- **runtime timing does NOT affect hash** — ✅ `test_acceptance_runtime_timing_no_effect`, `test_runtime_timing_does_not_affect_hash`
- **Experiment -> Run lineage works** — ✅ `test_acceptance_experiment_to_run_lineage`, `test_lineage_edge_experiment_to_run`, `test_emit_run_for_experiment_links_lineage`
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
| Run evidence artifacts created from existing ExperimentRun contract | ✅ |
| `artifact_type="Run"` | ✅ |
| Uses `HASH_SCHEME_VERSION = 2` | ✅ |
| Includes run_hash | ✅ |
| Includes experiment_id | ✅ |
| Includes experiment_hash reference | ✅ |
| Includes parameters snapshot | ✅ |
| Includes dataset_config snapshot | ✅ |
| Includes simulation_config snapshot | ✅ |
| Includes backend identity metadata | ✅ |
| Includes deterministic run metadata | ✅ |
| Excludes wall-clock telemetry / execution timestamps / runtime duration from identity | ✅ |
| Experiment -> Run lineage (relation "executes") | ✅ |
| No Result emission | ✅ |
| No Validation | ✅ |
| No Model Registry | ✅ |
| No execution changes | ✅ |
| Deterministic tests added | ✅ |
| Full ResearchOS suite stays green (no new regressions) | ✅ |

---

## 6. Constraints Honored

- ✅ **Determinism** — canonical scheme-2 hashes; time/duration excluded.
- ✅ **Immutability** — frozen envelopes; append-only store.
- ✅ **Additive-only** — no existing module changed destructively.
- ✅ **No trading logic** — certification/trust layer only.

---

*Phase 5.3b.3 ExperimentRun Evidence Emission — Report*
*Classification: Internal — Implementation Evidence*
